"""Run the complete Bildung curriculum with Iboga interludes.

This is the product-shaped experiment: stages are evaluated in order, the clean
direct-correction path is recorded for every stage, and the forced-sitting protocol
is inserted at the documented discontinuities (4→5, 6→7, and 9→1').
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from grimoire.stages import STAGES, stage_case, stage_gold

from .config import Settings
from .runner import run_baseline, run_iboga


INTERLUDE_AFTER = {4, 6, 9}
DECISION_LABELS = ["pass", "fail", "needs_review"]


def parse_stage_selector(value: str) -> list[int]:
    if value == "all":
        return [stage.number for stage in STAGES]
    numbers: set[int] = set()
    for part in value.split(","):
        if "-" in part:
            start, end = (int(item) for item in part.split("-", 1))
            numbers.update(range(start, end + 1))
        else:
            numbers.add(int(part))
    valid = {stage.number for stage in STAGES}
    if not numbers or not numbers.issubset(valid):
        raise ValueError(f"stages must be within 1..{len(STAGES)}")
    return sorted(numbers)


def _dossier(stage_number: int) -> dict[str, Any]:
    case = stage_case(next(stage for stage in STAGES if stage.number == stage_number))
    return {
        "id": case["id"],
        "session_id": f"bildung-stage-{stage_number:02d}",
        "task": case["task"],
        "challenge": case["task"],
        "stage": case["stage"],
        "name": case["name"],
        "capability": case["capability"],
        "failure_mode": case["failure_mode"],
        "evidence": case["evidence"],
        "decision_labels": DECISION_LABELS,
    }


def run_curriculum(stage_numbers: list[int], settings: Settings) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    for stage_number in stage_numbers:
        case = stage_case(next(stage for stage in STAGES if stage.number == stage_number))
        gold = stage_gold(next(stage for stage in STAGES if stage.number == stage_number))
        dossier = _dossier(stage_number)
        direct = run_baseline(dossier, settings, temperature=0.2)
        direct_decision = str((direct.get("heldout") or {}).get("decision", "parse_error")).strip().lower()
        records.append({"stage": stage_number, "condition": "direct_correction", "expected_status": gold["status"], "observed_status": direct_decision, "correct": direct_decision == gold["status"], "result": direct})
        if stage_number in INTERLUDE_AFTER:
            iboga = run_iboga(dossier, settings, temperature=0.2)
            iboga_decision = str((iboga.get("heldout") or {}).get("decision", "parse_error")).strip().lower()
            records.append({"stage": stage_number, "condition": "iboga_interlude", "expected_status": gold["status"], "observed_status": iboga_decision, "correct": iboga_decision == gold["status"], "result": iboga})
    summary = {
        "stages_attempted": stage_numbers,
        "records": len(records),
        "direct_cost_usd": round(sum(float(item["result"].get("estimated_cost_usd", 0)) for item in records if item["condition"] == "direct_correction"), 8),
        "iboga_cost_usd": round(sum(float(item["result"].get("estimated_cost_usd", 0)) for item in records if item["condition"] == "iboga_interlude"), 8),
        "iboga_commit_rate": round(sum(bool(item["result"].get("approved_for_commit")) for item in records if item["condition"] == "iboga_interlude") / max(1, len([item for item in records if item["condition"] == "iboga_interlude"])), 4),
        "direct_accuracy": round(sum(bool(item["correct"]) for item in records if item["condition"] == "direct_correction") / max(1, len([item for item in records if item["condition"] == "direct_correction"])), 4),
        "iboga_accuracy": round(sum(bool(item["correct"]) for item in records if item["condition"] == "iboga_interlude") / max(1, len([item for item in records if item["condition"] == "iboga_interlude"])), 4),
    }
    return {"experiment": "bildung-curriculum-v0.2", "created_at": datetime.now(timezone.utc).isoformat(), "primary_model": settings.primary.model_id, "critic_model": settings.critic.model_id, "interlude_after": sorted(INTERLUDE_AFTER), "summary": summary, "records": records}


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Bildung curriculum with Iboga interludes")
    parser.add_argument("--stages", default="all", help="all, a comma list, or a range such as 1-9")
    parser.add_argument("--out", type=Path, default=Path("results/bildung-curriculum-v0.1.json"))
    args = parser.parse_args()
    result = run_curriculum(parse_stage_selector(args.stages), Settings.from_env())
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"experiment": result["experiment"], "summary": result["summary"]}, indent=2))


if __name__ == "__main__":
    main()
