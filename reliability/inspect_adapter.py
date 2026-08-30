from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable


def to_inspect_records(cases: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Export public cases to Inspect's JSON dataset shape.

    Gold data stays out of ``input``. The target is a compact, explicit rubric
    payload so an Inspect scorer or customer verifier can score it independently.
    """
    records: list[dict[str, Any]] = []
    for case in cases:
        evidence = "\n".join(f"[{item['id']}] {item['text']}" for item in case.get("evidence", []))
        records.append({
            "id": case.get("id"),
            "input": f"{case.get('scenario', '')}\n{case.get('input', case.get('task', ''))}\n\nEvidence:\n{evidence}",
            "target": json.dumps(case.get("response_contract", {"type": "reliability_decision"}), sort_keys=True),
            "metadata": {
                "seed_id": case.get("seed_id"),
                "pair_id": case.get("pair_id"),
                "task_family": case.get("task_family"),
                "provenance": case.get("provenance", {}),
            },
        })
    return records


def write_inspect_jsonl(cases: Iterable[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    records = to_inspect_records(cases)
    path.write_text("".join(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n" for record in records), encoding="utf-8")
