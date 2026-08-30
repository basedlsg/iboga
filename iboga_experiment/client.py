from __future__ import annotations

import json
import os
import signal
import time
import urllib.error
import urllib.parse
import urllib.request
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any

from .config import ModelSpec, Settings


class RequestDeadlineExceeded(TimeoutError):
    """The provider did not complete a response before the wall-clock deadline."""


@contextmanager
def _request_deadline(seconds: float):
    """Bound the whole blocking urllib call, including chunked response reads.

    urllib's timeout is an idle socket timeout, not a total request deadline.
    A provider can therefore keep a chunked response open indefinitely while
    periodically sending data. The experiment runner needs a hard upper bound
    so long queues cannot hang forever. The clients run synchronously on the
    main thread, which is the supported context for SIGALRM on Unix.
    """
    if seconds <= 0:
        yield
        return
    previous_handler = signal.getsignal(signal.SIGALRM)
    previous_timer = signal.setitimer(signal.ITIMER_REAL, 0)

    def _raise_deadline(_signum: int, _frame: Any) -> None:
        raise RequestDeadlineExceeded(f"request exceeded {seconds:g}s wall-clock deadline")

    signal.signal(signal.SIGALRM, _raise_deadline)
    signal.setitimer(signal.ITIMER_REAL, max(0.1, seconds))
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous_handler)
        if previous_timer[0] > 0:
            signal.setitimer(signal.ITIMER_REAL, previous_timer[0], previous_timer[1])


def _read_response_body(response: Any, seconds: float) -> bytes:
    """Read a response in bounded chunks with an absolute wall-clock deadline."""
    deadline = time.monotonic() + seconds
    chunks: list[bytes] = []
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise RequestDeadlineExceeded(f"response read exceeded {seconds:g}s wall-clock deadline")
        raw = getattr(getattr(response, "fp", None), "raw", None)
        sock = getattr(raw, "_sock", None)
        if sock is not None and hasattr(sock, "settimeout"):
            # HTTPResponse.read() can loop through an arbitrary number of
            # chunked reads without returning control here. read1 plus a
            # remaining-time socket timeout gives us an absolute bound.
            sock.settimeout(remaining)
        read_one = getattr(response, "read1", None)
        chunk = read_one(64 * 1024) if callable(read_one) else response.read()
        if not chunk:
            return b"".join(chunks)
        chunks.append(chunk)


@dataclass(frozen=True)
class Completion:
    text: str
    input_tokens: int
    output_tokens: int
    model_id: str
    cost_usd: float
    raw: dict[str, Any]
    # "provider_reported" when the API returned what it charged, otherwise
    # "local_estimate" from the price table, which may be stale.
    cost_source: str = "local_estimate"


def extract_chat_completion(raw: dict[str, Any], model_id: str) -> tuple[str, int, int]:
    """Extract a documented Chat Completions response or fail loudly.

    Bedrock can return an HTTP 200 envelope that is not the OpenAI-compatible
    Chat Completions shape. Treating that as a normal response would hide an
    endpoint, model, or authentication mismatch and could produce empty
    experiment records.
    """
    choices = raw.get("choices")
    if not isinstance(choices, list) or not choices:
        keys = ", ".join(sorted(str(key) for key in raw))
        raise RuntimeError(
            "Bedrock returned HTTP 200 but not a Chat Completions response for "
            f"{model_id}; top-level keys: {keys or '<none>'}."
        )
    try:
        message = choices[0]["message"]
        text = message["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError(
            f"Bedrock returned an invalid Chat Completions choice for {model_id}."
        ) from exc
    usage = raw.get("usage") or {}
    try:
        input_tokens = int(usage.get("prompt_tokens", 0))
        output_tokens = int(usage.get("completion_tokens", 0))
    except (AttributeError, TypeError, ValueError) as exc:
        raise RuntimeError(f"Bedrock returned invalid usage fields for {model_id}.") from exc
    if not isinstance(text, str):
        raise RuntimeError(f"Bedrock returned non-text message content for {model_id}.")
    return text, input_tokens, output_tokens


class BedrockMantleClient:
    """Minimal OpenAI-compatible Bedrock Mantle client.

    The key is read at call time and never included in logs or result artifacts.
    """

    def __init__(self, settings: Settings):
        self.settings = settings

    def complete(
        self,
        model: ModelSpec,
        system: str,
        user: str,
        *,
        max_tokens: int = 2_000,
        temperature: float = 0.2,
    ) -> Completion:
        estimated_input_tokens = (len(system) + len(user) + 3) // 4
        if estimated_input_tokens + max_tokens > model.context_tokens:
            raise ValueError(
                f"request exceeds {model.name} context budget: "
                f"estimated {estimated_input_tokens + max_tokens:,} > "
                f"{model.context_tokens:,} tokens"
            )
        api_key = self.settings.require_api_key()
        payload: dict[str, Any] = {
            "model": model.model_id,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "max_tokens": min(max_tokens, model.max_output_tokens),
            "temperature": temperature,
        }
        if self.settings.provider == "openrouter":
            # Ask OpenRouter to return what it actually charged, so cost is
            # reported rather than estimated from a hardcoded price table.
            payload["usage"] = {"include": True}
            reasoning_effort = os.getenv("IBOGA_REASONING_EFFORT")
            if reasoning_effort:
                # OpenRouter's reasoning object is model-agnostic. Excluding
                # reasoning keeps hidden chains out of experiment artifacts;
                # the model's final structured answer remains in content.
                payload["reasoning"] = {"effort": reasoning_effort, "exclude": True}
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        headers.update(dict(self.settings.extra_headers))
        request = urllib.request.Request(
            f"{self.settings.base_url}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        last_error: Exception | None = None
        for attempt in range(self.settings.max_retries + 1):
            try:
                with _request_deadline(self.settings.timeout_seconds):
                    with urllib.request.urlopen(
                        request, timeout=self.settings.timeout_seconds
                    ) as response:
                        raw = json.loads(
                            _read_response_body(response, self.settings.timeout_seconds).decode("utf-8")
                        )
                if not isinstance(raw, dict):
                    raise RuntimeError(
                        f"Bedrock returned a non-object response for {model.model_id}."
                    )
                text, input_tokens, output_tokens = extract_chat_completion(
                    raw, model.model_id
                )
                reported = (raw.get("usage") or {}).get("cost")
                cost_reported = isinstance(reported, (int, float)) and not isinstance(reported, bool)
                return Completion(
                    text=text,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    model_id=model.model_id,
                    cost_usd=float(reported) if cost_reported else model.estimate_cost(input_tokens, output_tokens),
                    cost_source="provider_reported" if cost_reported else "local_estimate",
                    raw=raw,
                )
            except urllib.error.HTTPError as exc:
                if exc.code == 401:
                    raise RuntimeError(
                        f"{self.settings.provider_name} rejected the bearer credential with "
                        f"HTTP 401. Check that {self.settings.api_key_env} holds a current key "
                        f"for {self.settings.base_url} and is passed through the same process "
                        "rather than copied between commands."
                    ) from exc
                last_error = exc
                if attempt < self.settings.max_retries:
                    time.sleep(2**attempt)
            except (urllib.error.URLError, KeyError, ValueError, TimeoutError) as exc:
                last_error = exc
                if attempt < self.settings.max_retries:
                    time.sleep(2**attempt)
        raise RuntimeError(f"{self.settings.provider_name} request failed after retries: {last_error}") from last_error


class BedrockConverseClient:
    """Amazon Bedrock Runtime Converse client using the bearer API key."""

    def __init__(self, settings: Settings):
        self.settings = settings

    def complete(
        self,
        model: ModelSpec,
        system: str,
        user: str,
        *,
        max_tokens: int = 2_000,
        temperature: float = 0.2,
    ) -> Completion:
        estimated_input_tokens = (len(system) + len(user) + 3) // 4
        if estimated_input_tokens + max_tokens > model.context_tokens:
            raise ValueError(
                f"request exceeds {model.name} context budget: "
                f"estimated {estimated_input_tokens + max_tokens:,} > "
                f"{model.context_tokens:,} tokens"
            )
        api_key = self.settings.require_api_key()
        payload: dict[str, Any] = {
            "messages": [{"role": "user", "content": [{"text": user}]}],
            "inferenceConfig": {
                "maxTokens": min(max_tokens, model.max_output_tokens),
                "temperature": temperature,
            },
        }
        if system:
            payload["system"] = [{"text": system}]
        encoded_model = urllib.parse.quote(model.model_id, safe=".:/-")
        request = urllib.request.Request(
            f"https://bedrock-runtime.{self.settings.region}.amazonaws.com/model/{encoded_model}/converse",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        last_error: Exception | None = None
        for attempt in range(self.settings.max_retries + 1):
            try:
                with _request_deadline(self.settings.timeout_seconds):
                    with urllib.request.urlopen(
                        request, timeout=self.settings.timeout_seconds
                    ) as response:
                        raw = json.loads(
                            _read_response_body(response, self.settings.timeout_seconds).decode("utf-8")
                        )
                if not isinstance(raw, dict):
                    raise RuntimeError(f"Bedrock Converse returned a non-object response for {model.model_id}.")
                output = raw.get("output")
                message = output.get("message") if isinstance(output, dict) else None
                content = message.get("content") if isinstance(message, dict) else None
                text_parts = [item.get("text") for item in content or [] if isinstance(item, dict) and isinstance(item.get("text"), str)]
                if not text_parts:
                    keys = ", ".join(sorted(str(key) for key in raw))
                    raise RuntimeError(
                        "Bedrock Converse returned HTTP 200 without text content for "
                        f"{model.model_id}; top-level keys: {keys or '<none>'}."
                    )
                usage = raw.get("usage") or {}
                input_tokens = int(usage.get("inputTokens", 0))
                output_tokens = int(usage.get("outputTokens", 0))
                text = "".join(text_parts)
                return Completion(
                    text=text,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    model_id=model.model_id,
                    cost_usd=model.estimate_cost(input_tokens, output_tokens),
                    raw=raw,
                )
            except urllib.error.HTTPError as exc:
                if exc.code == 401:
                    raise RuntimeError(
                        "Bedrock Runtime Converse rejected the bearer credential with HTTP 401."
                    ) from exc
                last_error = exc
                if attempt < self.settings.max_retries:
                    time.sleep(2**attempt)
            except (urllib.error.URLError, ValueError, KeyError, TypeError, TimeoutError) as exc:
                last_error = exc
                if attempt < self.settings.max_retries:
                    time.sleep(2**attempt)
        raise RuntimeError(f"Bedrock Converse request failed after retries: {last_error}") from last_error
