from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .audit import audit_public_case, stable_hash
from .contracts import ReliabilityDecision
from .verifiers import verify_decision


@dataclass(frozen=True)
class PrivateChallengeSet:
    """A local scoring boundary: callers receive public cases, not gold labels."""

    public_cases: tuple[dict[str, Any], ...]
    gold_by_id: dict[str, dict[str, Any]]

    @classmethod
    def from_jsonl(cls, public_path: Path, gold_path: Path) -> "PrivateChallengeSet":
        public_cases = tuple(_load_jsonl(public_path))
        gold_records = _load_jsonl(gold_path)
        gold_by_id = {record["id"]: record["gold"] for record in gold_records}
        gold_record_by_id = {record["id"]: record for record in gold_records}
        errors: list[str] = []
        for case in public_cases:
            if "gold" in case:
                errors.append(f"public case leaked gold: {case.get('id')}")
            errors.extend(f"{case.get('id')}: {error}" for error in audit_public_case(case))
            if case.get("id") not in gold_by_id:
                errors.append(f"missing private gold: {case.get('id')}")
            gold_record = gold_record_by_id.get(case.get("id"))
            if gold_record and case.get("sample_hash") != gold_record.get("public_sample_hash"):
                errors.append(f"public/private hash mismatch: {case.get('id')}")
        if len(gold_by_id) != len(gold_records) or len(gold_by_id) != len(public_cases):
            errors.append("public/private challenge IDs are not one-to-one")
        if errors:
            raise ValueError("; ".join(errors))
        return cls(public_cases, gold_by_id)

    def cases_for_agent(self) -> list[dict[str, Any]]:
        return [dict(case) for case in self.public_cases]

    def score(self, observed_by_id: dict[str, ReliabilityDecision | dict[str, Any]]) -> dict[str, Any]:
        records: list[dict[str, Any]] = []
        for case in self.public_cases:
            observed = observed_by_id.get(case["id"])
            if observed is None:
                records.append({"id": case["id"], "status": "missing"})
                continue
            result = verify_decision(observed, self.gold_by_id[case["id"]], {item["id"] for item in case.get("evidence", [])})
            records.append({"id": case["id"], "status": "scored", **result.as_dict()})
        scored = [record for record in records if record["status"] == "scored"]
        return {
            "challenge_hash": stable_hash([case["id"] for case in self.public_cases]),
            "n": len(records),
            "scored": len(scored),
            "missing": len(records) - len(scored),
            "mean_score": round(sum(record["score"] for record in scored) / len(scored), 6) if scored else 0.0,
            "passed": sum(bool(record.get("passed")) for record in scored),
            "records": records,
        }


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
