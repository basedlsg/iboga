"""OpenRouter wiring, verified without a key or a network call.

The Chat Completions client is provider-agnostic, so switching providers is a
matter of base URL, key variable, headers, and model slug. These tests capture
the outbound request and assert each of those, which is the part that would
otherwise only be discovered by spending money.
"""

import io
import json
import os
import time
import unittest
import urllib.error
from contextlib import contextmanager
from unittest import mock

from iboga_experiment.client import BedrockMantleClient
from iboga_experiment.config import PROVIDERS, Settings, custom_model


@contextmanager
def provider_env(**overrides):
    keys = ("IBOGA_PROVIDER", "OPENROUTER_API_KEY", "AWS_BEARER_TOKEN_BEDROCK", "IBOGA_BASE_URL")
    saved = {key: os.environ.get(key) for key in keys}
    try:
        for key in keys:
            os.environ.pop(key, None)
        os.environ.update(overrides)
        yield
    finally:
        for key in keys:
            os.environ.pop(key, None)
            if saved[key] is not None:
                os.environ[key] = saved[key]


def fake_response(payload: dict) -> io.BytesIO:
    stream = io.BytesIO(json.dumps(payload).encode("utf-8"))
    stream.__enter__ = lambda: stream  # type: ignore[method-assign]
    stream.__exit__ = lambda *args: None  # type: ignore[method-assign]
    return stream


OK_PAYLOAD = {
    "choices": [{"message": {"content": '{"verdict": "approve", "reasons": ["supported"]}'}}],
    "usage": {"prompt_tokens": 500, "completion_tokens": 40, "cost": 0.000123},
}


class ProviderSelectionTests(unittest.TestCase):
    def test_openrouter_resolves_endpoint_and_key_variable(self) -> None:
        with provider_env(IBOGA_PROVIDER="openrouter"):
            settings = Settings.from_env()
        self.assertEqual(settings.base_url, "https://openrouter.ai/api/v1")
        self.assertEqual(settings.api_key_env, "OPENROUTER_API_KEY")
        self.assertEqual(settings.provider, "openrouter")

    def test_bedrock_remains_the_default_so_existing_runs_are_unchanged(self) -> None:
        with provider_env():
            settings = Settings.from_env()
        self.assertEqual(settings.provider, "bedrock-mantle")
        self.assertEqual(settings.api_key_env, "AWS_BEARER_TOKEN_BEDROCK")
        self.assertIn("bedrock-mantle", settings.base_url)

    def test_unknown_provider_is_rejected(self) -> None:
        with provider_env(IBOGA_PROVIDER="nonesuch"):
            with self.assertRaises(ValueError):
                Settings.from_env()

    def test_openrouter_catalog_uses_vendor_prefixed_slugs(self) -> None:
        for key, spec in PROVIDERS["openrouter"].models.items():
            self.assertIn("/", spec.model_id, key)


class RequestShapeTests(unittest.TestCase):
    def _capture(self, model_id="z-ai/glm-4.6", payload=None):
        with provider_env(IBOGA_PROVIDER="openrouter", OPENROUTER_API_KEY="test-key"):
            settings = Settings.from_env()
            client = BedrockMantleClient(settings)
            captured = {}

            def fake_urlopen(request, timeout=None):
                captured["url"] = request.full_url
                captured["headers"] = dict(request.headers)
                captured["body"] = json.loads(request.data.decode("utf-8"))
                return fake_response(payload or OK_PAYLOAD)

            with mock.patch("urllib.request.urlopen", fake_urlopen):
                completion = client.complete(custom_model(model_id), "system", "user")
            return captured, completion

    def test_request_goes_to_openrouter_chat_completions(self) -> None:
        captured, _ = self._capture()
        self.assertEqual(captured["url"], "https://openrouter.ai/api/v1/chat/completions")

    def test_bearer_token_comes_from_the_openrouter_variable(self) -> None:
        captured, _ = self._capture()
        self.assertEqual(captured["headers"].get("Authorization"), "Bearer test-key")

    def test_attribution_headers_are_sent(self) -> None:
        captured, _ = self._capture()
        lowered = {key.lower(): value for key, value in captured["headers"].items()}
        self.assertIn("http-referer", lowered)
        self.assertIn("x-title", lowered)

    def test_model_slug_is_passed_through_verbatim(self) -> None:
        captured, _ = self._capture(model_id="anthropic/claude-sonnet-4.5")
        self.assertEqual(captured["body"]["model"], "anthropic/claude-sonnet-4.5")

    def test_provider_cost_is_requested(self) -> None:
        captured, _ = self._capture()
        self.assertEqual(captured["body"].get("usage"), {"include": True})

    def test_reasoning_effort_is_opt_in_and_excludes_hidden_reasoning(self) -> None:
        with provider_env(IBOGA_PROVIDER="openrouter", OPENROUTER_API_KEY="test-key"):
            with mock.patch.dict(os.environ, {"IBOGA_REASONING_EFFORT": "low"}):
                settings = Settings.from_env()
                client = BedrockMantleClient(settings)
                captured = {}

                def fake_urlopen(request, timeout=None):
                    captured["body"] = json.loads(request.data.decode("utf-8"))
                    return fake_response(OK_PAYLOAD)

                with mock.patch("urllib.request.urlopen", fake_urlopen):
                    client.complete(custom_model("stealth/ox-alpha"), "system", "user")
        self.assertEqual(captured["body"]["reasoning"], {"effort": "low", "exclude": True})


class CostAccountingTests(unittest.TestCase):
    def test_provider_reported_cost_beats_the_local_price_table(self) -> None:
        with provider_env(IBOGA_PROVIDER="openrouter", OPENROUTER_API_KEY="test-key"):
            settings = Settings.from_env()
            client = BedrockMantleClient(settings)
            with mock.patch("urllib.request.urlopen", lambda *a, **k: fake_response(OK_PAYLOAD)):
                completion = client.complete(
                    custom_model("z-ai/glm-4.6", input_price=999.0, output_price=999.0),
                    "system",
                    "user",
                )
        self.assertEqual(completion.cost_usd, 0.000123)
        self.assertEqual(completion.cost_source, "provider_reported")

    def test_missing_provider_cost_falls_back_and_says_so(self) -> None:
        payload = {
            "choices": [{"message": {"content": '{"verdict": "approve"}'}}],
            "usage": {"prompt_tokens": 1_000_000, "completion_tokens": 0},
        }
        with provider_env(IBOGA_PROVIDER="openrouter", OPENROUTER_API_KEY="test-key"):
            settings = Settings.from_env()
            client = BedrockMantleClient(settings)
            with mock.patch("urllib.request.urlopen", lambda *a, **k: fake_response(payload)):
                completion = client.complete(
                    custom_model("z-ai/glm-4.6", input_price=2.0, output_price=8.0), "system", "user"
                )
        self.assertEqual(completion.cost_usd, 2.0)
        self.assertEqual(completion.cost_source, "local_estimate")

    def test_unpriced_custom_model_reports_zero_rather_than_a_guess(self) -> None:
        spec = custom_model("some/new-model")
        self.assertEqual(spec.estimate_cost(1_000_000, 1_000_000), 0.0)


class ErrorMessageTests(unittest.TestCase):
    def test_total_request_deadline_catches_a_stalled_chunked_response(self) -> None:
        with provider_env(IBOGA_PROVIDER="openrouter", OPENROUTER_API_KEY="test-key"):
            with mock.patch.dict(os.environ, {"IBOGA_TIMEOUT_SECONDS": "0.05", "IBOGA_MAX_RETRIES": "0"}):
                settings = Settings.from_env()
                client = BedrockMantleClient(settings)

                class StalledResponse:
                    def __enter__(self):
                        return self

                    def __exit__(self, *args):
                        return None

                    def read(self):
                        time.sleep(0.25)
                        return b"{}"

                with mock.patch("urllib.request.urlopen", return_value=StalledResponse()):
                    with self.assertRaisesRegex(RuntimeError, "request exceeded 0.05s"):
                        client.complete(custom_model("z-ai/glm-4.6"), "system", "user")

    def test_401_names_the_right_provider_and_key_variable(self) -> None:
        with provider_env(IBOGA_PROVIDER="openrouter", OPENROUTER_API_KEY="bad-key"):
            settings = Settings.from_env()
            client = BedrockMantleClient(settings)

            def raise_401(*args, **kwargs):
                raise urllib.error.HTTPError("url", 401, "Unauthorized", {}, None)

            with mock.patch("urllib.request.urlopen", raise_401):
                with self.assertRaises(RuntimeError) as caught:
                    client.complete(custom_model("z-ai/glm-4.6"), "system", "user")
        message = str(caught.exception)
        self.assertIn("OpenRouter", message)
        self.assertIn("OPENROUTER_API_KEY", message)


if __name__ == "__main__":
    unittest.main()
