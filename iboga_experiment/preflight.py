"""Safe Bedrock Mantle preflight; it lists models but performs no inference."""

from __future__ import annotations

import argparse
import json
import urllib.error
import urllib.request

from .config import MODELS, Settings


def run_preflight(settings: Settings) -> dict[str, object]:
    request = urllib.request.Request(
        f"{settings.base_url}/models",
        headers={"Authorization": f"Bearer {settings.require_api_key()}"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
        models = payload.get("data", [])
        model_ids = [item.get("id") for item in models if isinstance(item, dict) and item.get("id")]
        configured = {"primary": settings.primary.model_id, "critic": settings.critic.model_id}
        return {
            "ok": True,
            "status": 200,
            "base_url": settings.base_url,
            "model_count": len(model_ids),
            "configured_models": configured,
            "configured_models_available": {name: value in model_ids for name, value in configured.items()},
            "model_ids": model_ids,
        }
    except urllib.error.HTTPError as exc:
        return {"ok": False, "status": exc.code, "base_url": settings.base_url, "error": "Bedrock rejected the preflight request"}
    except (urllib.error.URLError, ValueError, KeyError) as exc:
        return {"ok": False, "base_url": settings.base_url, "error": type(exc).__name__}


def main() -> None:
    parser = argparse.ArgumentParser(description="List available Bedrock Mantle models without inference")
    parser.add_argument("--region", default=None)
    args = parser.parse_args()
    if args.region:
        import os
        os.environ["BEDROCK_REGION"] = args.region
    result = run_preflight(Settings.from_env())
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not result.get("ok"):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
