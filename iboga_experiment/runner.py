from __future__ import annotations

import argparse
import json
import uuid
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .client import BedrockMantleClient, Completion
from .config import MODELS, Settings
from .prompts import (
    BASE_SYSTEM,
    baseline_prompt,
    confession_prompt,
    critic_prompt,
    forced_sitting_prompt,
    onset_prompt,
)
from .schema import extract_json, validate_confession
from .metrics import score_result


def load_dossier(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or "evidence" not in value:
        raise ValueError("dossier must be a JSON object with an evidence array")
    if not isinstance(value["evidence"], list):
        raise ValueError("dossier.evidence must be an array")
    return value


def completion_event(phase: str, completion: Completion) -> dict[str, Any]:
    return {
        "phase": phase,
        "model_id": completion.model_id,
        "input_tokens": completion.input_tokens,
        "output_tokens": completion.output_tokens,
        "estimated_cost_usd": round(completion.cost_usd, 8),
        "response": completion.text,
    }


def run_iboga(
    dossier: dict[str, Any], settings: Settings, *, temperature: float = 0.1
) -> dict[str, Any]:
    session_id = dossier.get("session_id", str(uuid.uuid4()))
    client = BedrockMantleClient(settings)
    events: list[dict[str, Any]] = []

    onset = client.complete(
        settings.primary, BASE_SYSTEM, onset_prompt(session_id), max_tokens=500, temperature=temperature
    )
    events.append(completion_event("onset", onset))

    sitting = client.complete(
        settings.primary,
        BASE_SYSTEM + " You are in a tool-denied phase; do not provide a solution.",
        forced_sitting_prompt(dossier),
        max_tokens=2_500,
        temperature=temperature,
    )
    events.append(completion_event("forced_sitting", sitting))

    confession_call = client.complete(
        settings.primary,
        BASE_SYSTEM + " Output valid JSON and nothing else.",
        confession_prompt(session_id, dossier, sitting.text),
        max_tokens=min(7_000, settings.primary.max_output_tokens),
        temperature=temperature,
    )
    events.append(completion_event("confession", confession_call))
    try:
        confession = extract_json(confession_call.text)
        schema_errors = validate_confession(confession)
    except (ValueError, json.JSONDecodeError) as exc:
        confession = None
        schema_errors = [str(exc)]

    critic: dict[str, Any] | None = None
    critic_call: Completion | None = None
    if confession is not None and not schema_errors:
        critic_call = client.complete(
            settings.critic,
            BASE_SYSTEM + " You are the independent critic. Output valid JSON only.",
            critic_prompt(confession, dossier),
            max_tokens=1_000,
            temperature=0.0,
        )
        events.append(completion_event("critic", critic_call))
        try:
            critic = extract_json(critic_call.text)
        except (ValueError, json.JSONDecodeError) as exc:
            critic = {"decision": "reject", "score": 0, "issues": [str(exc)]}

    heldout = None
    if dossier.get("challenge"):
        from .prompts import heldout_prompt

        memory = json.dumps(confession, ensure_ascii=False) if confession else "No confession was committed."
        heldout_call = client.complete(
            settings.primary,
            BASE_SYSTEM + " Output valid JSON and nothing else.",
            heldout_prompt(dossier["challenge"], memory, dossier.get("decision_labels")),
            max_tokens=600,
            temperature=temperature,
        )
        events.append(completion_event("heldout", heldout_call))
        try:
            heldout = extract_json(heldout_call.text)
        except (ValueError, json.JSONDecodeError) as exc:
            heldout = {"decision": "parse_error", "evidence_ids": [], "error": str(exc)}

    approved = bool(
        confession is not None
        and not schema_errors
        and critic is not None
        and critic.get("decision") == "approve"
    )
    total_cost = sum(event["estimated_cost_usd"] for event in events)
    return {
        "protocol": "iboga",
        "protocol_version": "0.1",
        "session_id": session_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "primary_model": settings.primary.model_id,
        "critic_model": settings.critic.model_id,
        "schema_errors": schema_errors,
        "critic": critic,
        "approved_for_commit": approved,
        "confession": confession,
        "heldout": heldout,
        "events": events,
        "estimated_cost_usd": round(total_cost, 8),
        "metrics": score_result(
            {
                "schema_errors": schema_errors,
                "approved_for_commit": approved,
                "confession": confession,
                "estimated_cost_usd": round(total_cost, 8),
            },
            dossier,
        ),
    }


def run_baseline(
    dossier: dict[str, Any], settings: Settings, *, temperature: float = 0.1
) -> dict[str, Any]:
    client = BedrockMantleClient(settings)
    session_id = dossier.get("session_id", str(uuid.uuid4()))
    result = client.complete(
        settings.primary,
        BASE_SYSTEM,
        baseline_prompt(dossier),
        max_tokens=min(4_000, settings.primary.max_output_tokens),
        temperature=temperature,
    )
    events = [completion_event("baseline", result)]
    heldout = None
    if dossier.get("challenge"):
        from .prompts import heldout_prompt

        heldout_call = client.complete(
            settings.primary,
            BASE_SYSTEM + " Output valid JSON and nothing else.",
            heldout_prompt(dossier["challenge"], result.text, dossier.get("decision_labels")),
            max_tokens=600,
            temperature=temperature,
        )
        events.append(completion_event("heldout", heldout_call))
        try:
            heldout = extract_json(heldout_call.text)
        except (ValueError, json.JSONDecodeError) as exc:
            heldout = {"decision": "parse_error", "evidence_ids": [], "error": str(exc)}
    return {
        "protocol": "direct-correction-baseline",
        "protocol_version": "0.1",
        "session_id": session_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "primary_model": settings.primary.model_id,
        "heldout": heldout,
        "events": events,
        "estimated_cost_usd": round(result.cost_usd, 8),
    }


def print_models() -> None:
    rows = [
        {
            "alias": alias,
            "model_id": spec.model_id,
            "role": spec.role,
            "context_tokens": spec.context_tokens,
            "max_output_tokens": spec.max_output_tokens,
            "input_usd_per_1m": spec.input_usd_per_million,
            "output_usd_per_1m": spec.output_usd_per_million,
        }
        for alias, spec in MODELS.items()
    ]
    print(json.dumps(rows, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Iboga Protocol model experiment")
    parser.add_argument("--dossier", type=Path, help="JSON dossier with trajectory evidence")
    parser.add_argument("--mode", choices=("iboga", "baseline"), default="iboga")
    parser.add_argument("--out", type=Path, help="Write a JSON result artifact")
    parser.add_argument("--list-models", action="store_true")
    args = parser.parse_args()
    if args.list_models:
        print_models()
        return
    if not args.dossier:
        parser.error("--dossier is required unless --list-models is used")
    settings = Settings.from_env()
    dossier = load_dossier(args.dossier)
    result = run_iboga(dossier, settings) if args.mode == "iboga" else run_baseline(dossier, settings)
    output = json.dumps(result, ensure_ascii=False, indent=2)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(output + "\n", encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
