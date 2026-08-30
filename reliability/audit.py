from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from typing import Any


PUBLIC_GOLD_FIELDS = {"gold", "gold_status", "gold_decision", "gold_rationale", "gold_evidence_ids"}


def stable_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()


def audit_public_case(case: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not case.get("id"):
        errors.append("missing case id")
    leaked = sorted(PUBLIC_GOLD_FIELDS.intersection(case))
    if leaked:
        errors.append(f"gold fields leaked into public case: {', '.join(leaked)}")
    evidence = case.get("evidence", [])
    evidence_ids = [item.get("id") for item in evidence if isinstance(item, dict)]
    if not evidence_ids or len(evidence_ids) != len(set(evidence_ids)):
        errors.append("evidence IDs must be present and unique")
    provenance = case.get("provenance")
    if not isinstance(provenance, dict):
        errors.append("missing provenance manifest")
    else:
        for field in ("source_type", "generator", "generator_version", "prompt_hash", "code_revision", "rights_status", "privacy_review"):
            if not provenance.get(field):
                errors.append(f"missing provenance field: {field}")
    declared_hash = case.get("sample_hash")
    if declared_hash:
        expected = stable_hash({key: value for key, value in case.items() if key != "sample_hash"})
        if declared_hash != expected:
            errors.append("sample hash mismatch")
    return errors


def audit_dataset(cases: list[dict[str, Any]]) -> dict[str, Any]:
    errors: list[str] = []
    ids = [case.get("id") for case in cases]
    if len(ids) != len(set(ids)):
        errors.append("duplicate case IDs")
    groups: dict[str, set[str]] = defaultdict(set)
    for case in cases:
        errors.extend(f"{case.get('id')}: {error}" for error in audit_public_case(case))
        group = case.get("seed_id") or case.get("pair_id") or case.get("id")
        split = case.get("split", "unspecified")
        groups[str(group)].add(str(split))
    for group, splits in groups.items():
        if len(splits) > 1:
            errors.append(f"group crosses split boundary: {group}")
    return {
        "ok": not errors,
        "n": len(cases),
        "errors": errors,
        "group_count": len(groups),
        "splits": dict(Counter(str(case.get("split", "unspecified")) for case in cases)),
        "audit_hash": stable_hash({"case_ids": ids, "groups": {key: sorted(value) for key, value in groups.items()}}),
    }
