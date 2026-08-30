"""Run a buyer-facing benchmark split through both protocol conditions."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .commercial_benchmark import DECISIONS
from .config import Settings
from .runner import run_baseline, run_iboga


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    samples = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            samples.append(json.loads(line))
    return samples


def attach_private_gold(samples: list[dict[str, Any]], gold_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    gold_by_id = {record["id"]: record["gold"] for record in gold_records}
    joined: list[dict[str, Any]] = []
    for sample in samples:
        if "gold" in sample:
            joined.append(sample)
            continue
        if sample.get("id") not in gold_by_id:
            raise ValueError(f"missing private gold for public sample {sample.get('id')}")
        joined.append({**sample, "gold": gold_by_id[sample["id"]]})
    return joined


def _observed(result: dict[str, Any]) -> str:
    heldout = result.get("heldout") or {}
    decision = str(heldout.get("decision", "parse_error")).strip().lower()
    return decision if decision in DECISIONS else "parse_error"


def run_benchmark(samples: list[dict[str, Any]], settings: Settings) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    for sample in samples:
        # Keep gold, provenance, and split metadata outside the model-visible dossier.
        dossier = {
            "id": sample["id"],
            "task": sample["scenario"],
            "challenge": sample["input"],
            "evidence": sample["evidence"],
            "decision_labels": list(DECISIONS),
        }
        for condition in ("iboga", "baseline"):
            result = run_iboga(dossier, settings, temperature=0.2) if condition == "iboga" else run_baseline(dossier, settings, temperature=0.2)
            observed = _observed(result)
            records.append({
                "sample_id": sample["id"],
                "seed_id": sample["seed_id"],
                "split": sample["split"],
                "variant": sample["variant"],
                "domain": sample["domain"],
                "task_family": sample["task_family"],
                "gold_decision": sample["gold"]["decision"],
                "observed_decision": observed,
                "correct": observed == sample["gold"]["decision"],
                "schema_valid": not bool(result.get("schema_errors")),
                "critic_approved": bool(result.get("approved_for_commit")),
                "estimated_cost_usd": result.get("estimated_cost_usd", 0),
                "condition": condition,
                "result": result,
            })
    summary: dict[str, Any] = {}
    for condition in ("iboga", "baseline"):
        subset = [record for record in records if record["condition"] == condition]
        summary[condition] = {
            "n": len(subset),
            "accuracy": round(sum(bool(record["correct"]) for record in subset) / len(subset), 4) if subset else 0.0,
            "schema_valid_rate": round(sum(bool(record["schema_valid"]) for record in subset) / len(subset), 4) if subset else 0.0,
            "critic_approval_rate": round(sum(bool(record["critic_approved"]) for record in subset) / len(subset), 4) if subset else 0.0,
            "total_cost_usd": round(sum(float(record["estimated_cost_usd"]) for record in subset), 8),
            "confusion": {gold: dict(Counter(record["observed_decision"] for record in subset if record["gold_decision"] == gold)) for gold in DECISIONS if any(record["gold_decision"] == gold for record in subset)},
        }
    return {
        "experiment": "commercial-benchmark-v0.2",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "primary_model": settings.primary.model_id,
        "critic_model": settings.critic.model_id,
        "samples": len(samples),
        "summary": summary,
        "records": records,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the buyer-facing synthetic benchmark")
    parser.add_argument("--cases", type=Path, default=Path("results/commercial-benchmark-v0.2.public.jsonl"))
    parser.add_argument("--gold-cases", type=Path, default=Path("results/commercial-benchmark-v0.2.gold.jsonl"))
    parser.add_argument("--split", choices=("train", "dev", "test"), default="test")
    parser.add_argument("--variant", choices=("base", "reordered", "distractor", "compressed"), default="base")
    parser.add_argument("--limit", type=int, default=0, help="optional cap after split/variant selection")
    parser.add_argument("--out", type=Path, default=Path("results/commercial-run-v0.2.json"))
    args = parser.parse_args()
    samples = attach_private_gold(load_jsonl(args.cases), load_jsonl(args.gold_cases))
    samples = [sample for sample in samples if sample["split"] == args.split and sample["variant"] == args.variant]
    if args.limit:
        samples = samples[:args.limit]
    if not samples:
        raise SystemExit("no samples selected")
    result = run_benchmark(samples, Settings.from_env())
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"experiment": result["experiment"], "samples": result["samples"], "summary": result["summary"]}, indent=2))


if __name__ == "__main__":
    main()
