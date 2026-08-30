from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ModelSpec:
    name: str
    model_id: str
    input_usd_per_million: float
    output_usd_per_million: float
    context_tokens: int
    max_output_tokens: int
    role: str

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        return (input_tokens / 1_000_000) * self.input_usd_per_million + (
            output_tokens / 1_000_000
        ) * self.output_usd_per_million


MODELS: dict[str, ModelSpec] = {
    "deepseek-v3.2": ModelSpec(
        name="DeepSeek V3.2",
        model_id="deepseek.v3.2",
        input_usd_per_million=0.62,
        output_usd_per_million=1.85,
        context_tokens=164_000,
        max_output_tokens=8_000,
        role="primary-cost-efficient",
    ),
    "kimi-k2.5": ModelSpec(
        name="Kimi K2.5",
        model_id="moonshotai.kimi-k2.5",
        input_usd_per_million=0.60,
        output_usd_per_million=3.00,
        context_tokens=256_000,
        max_output_tokens=16_000,
        role="primary-long-context",
    ),
    "glm-4.7-flash": ModelSpec(
        name="GLM 4.7 Flash",
        model_id="zai.glm-4.7-flash",
        input_usd_per_million=0.07,
        output_usd_per_million=0.40,
        context_tokens=128_000,
        max_output_tokens=4_000,
        role="critic-low-cost",
    ),
    "glm-5": ModelSpec(
        name="GLM 5",
        model_id="zai.glm-5",
        input_usd_per_million=1.00,
        output_usd_per_million=3.20,
        context_tokens=200_000,
        max_output_tokens=128_000,
        role="critic-high-quality",
    ),
}


# OpenRouter speaks the same Chat Completions shape as Bedrock Mantle, so the
# existing client works against it unchanged apart from the base URL, the key
# variable, and the model slugs.
#
# Prices and limits below were read from https://openrouter.ai/api/v1/models on
# 2026-08-15 and are USD per million tokens. They can go stale, so the client
# also asks OpenRouter to report what it actually charged and prefers that;
# every record says which source it used. Refresh with:
#     python3 -m iboga_experiment.config --refresh-prices
OPENROUTER_PRICES_FETCHED = "2026-08-15"

OPENROUTER_MODELS: dict[str, ModelSpec] = {
    "gpt-5.6-luna": ModelSpec(
        name="OpenAI GPT-5.6 Luna (OpenRouter)",
        model_id="openai/gpt-5.6-luna",
        input_usd_per_million=0.10,
        output_usd_per_million=0.60,
        context_tokens=1_050_000,
        max_output_tokens=128_000,
        role="critic-low-cost",
    ),
    "gpt-5.6-luna-pro": ModelSpec(
        name="OpenAI GPT-5.6 Luna Pro (OpenRouter)",
        model_id="openai/gpt-5.6-luna-pro",
        input_usd_per_million=0.10,
        output_usd_per_million=0.60,
        context_tokens=1_050_000,
        max_output_tokens=128_000,
        role="critic-high-quality",
    ),
    "glm-4.6": ModelSpec(
        name="GLM 4.6 (OpenRouter)",
        model_id="z-ai/glm-4.6",
        input_usd_per_million=0.55,
        output_usd_per_million=2.20,
        context_tokens=204_800,
        max_output_tokens=131_072,
        role="critic-low-cost",
    ),
    "deepseek-chat": ModelSpec(
        name="DeepSeek Chat (OpenRouter)",
        model_id="deepseek/deepseek-chat",
        input_usd_per_million=0.2574,
        output_usd_per_million=1.0287,
        context_tokens=163_840,
        max_output_tokens=16_000,
        role="primary-cost-efficient",
    ),
    "claude-sonnet-4.5": ModelSpec(
        name="Claude Sonnet 4.5 (OpenRouter)",
        model_id="anthropic/claude-sonnet-4.5",
        input_usd_per_million=3.00,
        output_usd_per_million=15.00,
        context_tokens=1_000_000,
        max_output_tokens=64_000,
        role="critic-high-quality",
    ),
    "gpt-4.1-mini": ModelSpec(
        name="GPT-4.1 mini (OpenRouter)",
        model_id="openai/gpt-4.1-mini",
        input_usd_per_million=0.40,
        output_usd_per_million=1.60,
        context_tokens=1_047_576,
        max_output_tokens=32_768,
        role="critic-low-cost",
    ),
}


@dataclass(frozen=True)
class Provider:
    name: str
    base_url: str
    api_key_env: str
    models: dict[str, ModelSpec]
    default_primary: str
    default_critic: str
    extra_headers: tuple[tuple[str, str], ...] = ()


PROVIDERS: dict[str, Provider] = {
    "bedrock-mantle": Provider(
        name="Bedrock Mantle",
        base_url="",  # region-derived; resolved in from_env
        api_key_env="AWS_BEARER_TOKEN_BEDROCK",
        models=MODELS,
        default_primary="deepseek-v3.2",
        default_critic="glm-4.7-flash",
    ),
    "openrouter": Provider(
        name="OpenRouter",
        base_url="https://openrouter.ai/api/v1",
        api_key_env="OPENROUTER_API_KEY",
        models=OPENROUTER_MODELS,
        default_primary="gpt-5.6-luna",
        default_critic="gpt-5.6-luna",
        # Optional attribution headers OpenRouter documents for API clients.
        extra_headers=(
            ("HTTP-Referer", "https://github.com/basedlsg/claude_code_journaling"),
            ("X-Title", "evidence-grounded-reliability"),
        ),
    ),
}


def custom_model(model_id: str, *, input_price: float = 0.0, output_price: float = 0.0) -> ModelSpec:
    """Build a spec for any provider slug not in the catalog.

    OpenRouter accepts any `vendor/model` string, so the catalog is a
    convenience, not a limit. Prices default to zero, which reports the run as
    uncosted rather than reporting a number that was made up.
    """
    return ModelSpec(
        name=model_id,
        model_id=model_id,
        input_usd_per_million=input_price,
        output_usd_per_million=output_price,
        context_tokens=128_000,
        max_output_tokens=8_000,
        role="user-specified",
    )


@dataclass(frozen=True)
class Settings:
    region: str
    base_url: str
    api_key_env: str
    primary: ModelSpec
    critic: ModelSpec
    timeout_seconds: float
    max_retries: int
    api_mode: str = "mantle"
    provider: str = "bedrock-mantle"
    provider_name: str = "Bedrock Mantle"
    extra_headers: tuple[tuple[str, str], ...] = ()

    @classmethod
    def from_env(cls) -> "Settings":
        provider_key = os.getenv("IBOGA_PROVIDER", "bedrock-mantle")
        if provider_key not in PROVIDERS:
            raise ValueError(
                f"Unknown IBOGA_PROVIDER: {provider_key}. Available: {', '.join(sorted(PROVIDERS))}"
            )
        provider = PROVIDERS[provider_key]
        region = os.getenv("BEDROCK_REGION", os.getenv("AWS_REGION", "us-east-1"))
        default_base = provider.base_url or f"https://bedrock-mantle.{region}.api.aws/v1"
        base_url = os.getenv("IBOGA_BASE_URL", os.getenv("BEDROCK_MANTLE_BASE_URL", default_base)).rstrip("/")
        primary_name = os.getenv("IBOGA_PRIMARY_MODEL", provider.default_primary)
        critic_name = os.getenv("IBOGA_CRITIC_MODEL", provider.default_critic)
        if primary_name not in provider.models:
            raise ValueError(f"Unknown IBOGA_PRIMARY_MODEL for {provider_key}: {primary_name}")
        if critic_name not in provider.models:
            raise ValueError(f"Unknown IBOGA_CRITIC_MODEL for {provider_key}: {critic_name}")
        return cls(
            region=region,
            base_url=base_url,
            api_key_env=provider.api_key_env,
            primary=provider.models[primary_name],
            critic=provider.models[critic_name],
            timeout_seconds=float(os.getenv("IBOGA_TIMEOUT_SECONDS", "120")),
            max_retries=int(os.getenv("IBOGA_MAX_RETRIES", "2")),
            # OpenRouter has no Converse API; the Chat Completions path is the only one.
            api_mode="mantle" if provider_key == "openrouter" else os.getenv("IBOGA_BEDROCK_API", "mantle"),
            provider=provider_key,
            provider_name=provider.name,
            extra_headers=provider.extra_headers,
        )

    def require_api_key(self) -> str:
        value = os.getenv(self.api_key_env)
        if not value:
            raise RuntimeError(
                f"{self.api_key_env} is not set. Rotate the exposed key first, then "
                "export the replacement only in your shell or secret manager."
            )
        return value


def project_root() -> Path:
    return Path(__file__).resolve().parent


def check_openrouter_prices(timeout: float = 20.0) -> dict[str, Any]:
    """Compare the hardcoded catalog against the live OpenRouter listing.

    Needs no API key — the model listing is public. Reports drift rather than
    editing the file, so a price change is something a human sees.
    """
    import json
    import urllib.request

    request = urllib.request.Request(
        "https://openrouter.ai/api/v1/models", headers={"User-Agent": "iboga-config"}
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        listing = {item["id"]: item for item in json.loads(response.read().decode("utf-8"))["data"]}

    drift: list[dict[str, Any]] = []
    missing: list[str] = []
    for key, spec in OPENROUTER_MODELS.items():
        live = listing.get(spec.model_id)
        if live is None:
            missing.append(spec.model_id)
            continue
        pricing = live.get("pricing") or {}
        live_in = round(float(pricing.get("prompt", 0)) * 1e6, 6)
        live_out = round(float(pricing.get("completion", 0)) * 1e6, 6)
        if (live_in, live_out) != (
            round(spec.input_usd_per_million, 6),
            round(spec.output_usd_per_million, 6),
        ):
            drift.append(
                {
                    "key": key,
                    "model_id": spec.model_id,
                    "local": [spec.input_usd_per_million, spec.output_usd_per_million],
                    "live": [live_in, live_out],
                }
            )
    return {
        "ok": not drift and not missing,
        "fetched_on_record": OPENROUTER_PRICES_FETCHED,
        "catalog_size": len(listing),
        "drift": drift,
        "missing_from_catalog": missing,
    }


def main() -> None:
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Inspect provider configuration")
    parser.add_argument("--refresh-prices", action="store_true", help="check the catalog against live OpenRouter pricing")
    args = parser.parse_args()
    if args.refresh_prices:
        print(json.dumps(check_openrouter_prices(), indent=2))
        return
    for key, provider in sorted(PROVIDERS.items()):
        print(f"{key}: {provider.name} -> {provider.base_url or '<region-derived>'} ({provider.api_key_env})")
        for name, spec in sorted(provider.models.items()):
            print(f"    {name:<20} {spec.model_id}")


if __name__ == "__main__":
    main()
