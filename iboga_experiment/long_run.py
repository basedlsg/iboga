from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import Settings
from .runner import load_dossier, run_baseline, run_iboga


DECISION_LABELS = ["unknown", "reject", "hold", "use_cli", "keep_local", "draft_only"]


def load_cases(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("long-run cases file must contain an array")
    for case in payload:
        if not case.get("id") or not case.get("challenge") or not case.get("gold_decision"):
            raise ValueError("each case needs id, challenge, and gold_decision")
    return payload


def decision(result: dict[str, Any]) -> str:
    value = result.get("heldout") or {}
    return str(value.get("decision", "parse_error")).strip().lower()


def run_long(cases: list[dict[str, Any]], settings: Settings, repeats: int) -> dict[str, Any]:
    temperatures = [0.1, 0.4, 0.7][:repeats]
    records: list[dict[str, Any]] = []
    for case in cases:
        dossier = {k: v for k, v in case.items() if k not in {"gold_decision", "tags"}}
        dossier["decision_labels"] = DECISION_LABELS
        for repeat, temperature in enumerate(temperatures, start=1):
            for condition in ("iboga", "baseline"):
                if condition == "iboga":
                    result = run_iboga(dossier, settings, temperature=temperature)
                else:
                    result = run_baseline(dossier, settings, temperature=temperature)
                observed = decision(result)
                records.append(
                    {
                        "case_id": case["id"],
                        "tags": case.get("tags", []),
                        "condition": condition,
                        "repeat": repeat,
                        "temperature": temperature,
                        "gold_decision": case["gold_decision"],
                        "observed_decision": observed,
                        "correct": observed == case["gold_decision"],
                        "approved_for_commit": result.get("approved_for_commit"),
                        "schema_valid": not bool(result.get("schema_errors")),
                        "estimated_cost_usd": result.get("estimated_cost_usd", 0),
                        "result": result,
                    }
                )
    by_condition: dict[str, dict[str, float | int]] = {}
    for condition in ("iboga", "baseline"):
        subset = [r for r in records if r["condition"] == condition]
        by_condition[condition] = {
            "n": len(subset),
            "accuracy": round(sum(bool(r["correct"]) for r in subset) / len(subset), 4),
            "schema_valid_rate": round(sum(bool(r["schema_valid"]) for r in subset) / len(subset), 4),
            "total_cost_usd": round(sum(float(r["estimated_cost_usd"]) for r in subset), 8),
        }
    return {
        "experiment": "iboga-long-v0.2",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "primary_model": settings.primary.model_id,
        "critic_model": settings.critic.model_id,
        "cases": len(cases),
        "repeats": repeats,
        "summary": by_condition,
        "records": records,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the long Iboga Protocol evaluation")
    parser.add_argument("--cases", type=Path, default=Path("iboga_experiment/long_cases.json"))
    parser.add_argument("--repeats", type=int, choices=(1, 2, 3), default=3)
    parser.add_argument("--out", type=Path, default=Path("results/iboga-long-v0.2.json"))
    args = parser.parse_args()
    settings = Settings.from_env()
    result = run_long(load_cases(args.cases), settings, args.repeats)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: result[k] for k in ("experiment", "cases", "repeats", "summary")}, indent=2))


if __name__ == "__main__":
    main()
