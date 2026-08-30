"""Independent review, disagreement preservation, and release gates for v2.

The packet generator creates provisional labels for balancing and auditability.
This module keeps those labels separate from human review. It never turns a
majority vote into truth: disagreement must either be explicitly adjudicated or
the item remains ambiguous/rewrite-required and is excluded from release.
"""

from __future__ import annotations

import argparse
import copy
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


RUBRIC_VERSION = "iboga-human-adjudication-v1.0"
SEED_KIND = "seed"
QUALIFICATION_KIND = "qualification"
RELEASE_STATUSES = {"adjudicated", "ambiguous", "rewrite_required"}
MACHINE_PILOT_STATUS = "machine_pilot"
SEED_LABEL_FIELDS = (
    "action",
    "evidence_sufficiency",
    "authorization",
    "risk",
    "data_boundary",
    "reversibility",
    "human_gate_required",
    "abstention_appropriate",
)
EVIDENCE_FIELDS = (
    "evidence_ids",
    "necessary_evidence_ids",
    "supporting_evidence_ids",
    "contradictory_evidence_ids",
    "irrelevant_evidence_ids",
)
QUALIFICATION_LABEL_FIELDS = ("verdict",)
SEED_ACTIONS = {"approve", "hold", "reject", "escalate", "request_evidence", "local_only", "unknown"}
SEED_ENUMS = {
    "evidence_sufficiency": {"sufficient", "insufficient", "conflicted", "unknown"},
    "authorization": {"authorized", "not_authorized", "not_applicable", "unknown"},
    "risk": {"low", "medium", "high", "unknown"},
    "data_boundary": {"external_allowed", "local_only", "unknown"},
    "reversibility": {"reversible", "irreversible", "unknown"},
}


def _case_id(case: dict[str, Any]) -> str:
    value = case.get("case_id", case.get("id"))
    if not value:
        raise ValueError("public case has no case_id or id")
    return str(value)


def _public_evidence_ids(case: dict[str, Any]) -> set[str]:
    evidence = case.get("evidence")
    if evidence is None:
        evidence = case.get("dossier", {}).get("evidence", [])
    return {str(item["id"]) for item in evidence if isinstance(item, dict) and item.get("id")}


def _as_ids(value: Any) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, (list, tuple)):
        raise ValueError("evidence references must be a list")
    return list(dict.fromkeys(str(item) for item in value))


def _annotation_view(annotation: dict[str, Any]) -> dict[str, Any]:
    label = dict(annotation.get("label") or {})
    for field in EVIDENCE_FIELDS:
        if field in annotation:
            label[field] = _as_ids(annotation[field])
    return label


def _label_diff(left: dict[str, Any], right: dict[str, Any], kind: str) -> list[str]:
    fields = SEED_LABEL_FIELDS + EVIDENCE_FIELDS if kind == SEED_KIND else QUALIFICATION_LABEL_FIELDS + ("evidence_ids",)
    differing: list[str] = []
    for field in fields:
        left_value = left.get(field)
        right_value = right.get(field)
        if field in EVIDENCE_FIELDS or field == "evidence_ids":
            left_value = sorted(_as_ids(left_value))
            right_value = sorted(_as_ids(right_value))
        if left_value != right_value:
            differing.append(field)
    return differing


def _required_fields(kind: str) -> tuple[str, ...]:
    if kind == SEED_KIND:
        return SEED_LABEL_FIELDS
    if kind == QUALIFICATION_KIND:
        return QUALIFICATION_LABEL_FIELDS
    raise ValueError(f"unknown review kind: {kind}")


def _validate_label(label: dict[str, Any], allowed_evidence: set[str], *, kind: str, prefix: str) -> list[str]:
    errors: list[str] = []
    missing = [field for field in _required_fields(kind) if field not in label]
    if missing:
        errors.append(f"{prefix} is missing label fields: {', '.join(missing)}")
    if kind == SEED_KIND:
        if "action" in label and label["action"] not in SEED_ACTIONS:
            errors.append(f"{prefix} has invalid action")
        for field, allowed in SEED_ENUMS.items():
            if field in label and label[field] not in allowed:
                errors.append(f"{prefix} has invalid {field}")
        for field in ("human_gate_required", "abstention_appropriate"):
            if field in label and not isinstance(label[field], bool):
                errors.append(f"{prefix} {field} must be boolean")
    elif label.get("verdict") not in {"approve", "reject", "uncertain"}:
        errors.append(f"{prefix} has invalid qualification verdict")
    for field in EVIDENCE_FIELDS:
        if field not in label and (kind == SEED_KIND or field == "evidence_ids"):
            errors.append(f"{prefix} is missing {field}")
            continue
        if field not in label:
            continue
        try:
            referenced = _as_ids(label[field])
        except ValueError as exc:
            errors.append(f"{prefix} {field}: {exc}")
            continue
        unknown = sorted(set(referenced) - allowed_evidence)
        if unknown:
            errors.append(f"{prefix} cites unknown evidence IDs in {field}: {unknown}")
    return errors


def validate_annotations(
    public_case: dict[str, Any],
    annotations: Iterable[dict[str, Any]],
    *,
    kind: str,
) -> list[str]:
    """Validate two independent annotations without consulting private gold."""
    items = list(annotations)
    errors: list[str] = []
    if len(items) != 2:
        errors.append("exactly two independent first-pass annotations are required")
    reviewer_ids = [str(item.get("reviewer_id", "")).strip() for item in items]
    if any(not reviewer_id for reviewer_id in reviewer_ids):
        errors.append("each annotation requires a reviewer_id")
    if len(set(reviewer_ids)) != len(reviewer_ids):
        errors.append("reviewer IDs must be distinct")
    rubric_versions = {str(item.get("rubric_version", "")).strip() for item in items}
    if rubric_versions != {RUBRIC_VERSION}:
        errors.append(f"all annotations must use rubric {RUBRIC_VERSION}")
    allowed_evidence = _public_evidence_ids(public_case)
    for index, annotation in enumerate(items, start=1):
        if not str(annotation.get("rationale", "")).strip():
            errors.append(f"annotation {index} requires a rationale")
        try:
            label = _annotation_view(annotation)
        except ValueError as exc:
            errors.append(f"annotation {index}: {exc}")
            continue
        errors.extend(_validate_label(label, allowed_evidence, kind=kind, prefix=f"annotation {index}"))
    return errors


def compare_annotations(annotations: list[dict[str, Any]], *, kind: str) -> dict[str, Any]:
    if len(annotations) != 2:
        raise ValueError("comparison requires exactly two annotations")
    left = _annotation_view(annotations[0])
    right = _annotation_view(annotations[1])
    fields = SEED_LABEL_FIELDS + EVIDENCE_FIELDS if kind == SEED_KIND else QUALIFICATION_LABEL_FIELDS + ("evidence_ids",)
    field_agreement = {}
    for field in fields:
        left_value = sorted(_as_ids(left.get(field))) if field in EVIDENCE_FIELDS or field == "evidence_ids" else left.get(field)
        right_value = sorted(_as_ids(right.get(field))) if field in EVIDENCE_FIELDS or field == "evidence_ids" else right.get(field)
        field_agreement[field] = left_value == right_value
    disagreement_fields = [field for field, agrees in field_agreement.items() if not agrees]
    return {
        "exact_label_agreement": not disagreement_fields,
        "field_agreement": field_agreement,
        "disagreement_fields": disagreement_fields,
    }


def adjudicate_case(
    public_case: dict[str, Any],
    annotations: list[dict[str, Any]],
    *,
    kind: str,
    adjudicator_id: str | None = None,
    final_label: dict[str, Any] | None = None,
    status: str | None = None,
) -> dict[str, Any]:
    """Create a durable record; no silent majority or automatic disagreement resolution."""
    errors = validate_annotations(public_case, annotations, kind=kind)
    if errors:
        raise ValueError("; ".join(errors))
    comparison = compare_annotations(annotations, kind=kind)
    disagreement = not comparison["exact_label_agreement"]
    status = status or "adjudicated"
    if status not in RELEASE_STATUSES:
        raise ValueError(f"invalid adjudication status: {status}")
    if disagreement and not adjudicator_id:
        raise ValueError("disagreement requires a named adjudicator")
    if disagreement and status == "adjudicated" and final_label is None:
        raise ValueError("an adjudicated disagreement requires an explicit final label")
    if status in {"ambiguous", "rewrite_required"} and not adjudicator_id:
        raise ValueError(f"{status} requires a named adjudicator")
    if status == "adjudicated" and final_label is None:
        # Agreement is safe to carry forward, but the provenance records that
        # it came from exact reviewer agreement rather than a hidden vote.
        final_label = copy.deepcopy(_annotation_view(annotations[0]))
    if final_label is not None:
        final_label = copy.deepcopy(final_label)
        final_errors = _validate_label(final_label, _public_evidence_ids(public_case), kind=kind, prefix="final label")
        if final_errors:
            raise ValueError("; ".join(final_errors))
    return {
        "case_id": _case_id(public_case),
        "kind": kind,
        "annotations": copy.deepcopy(annotations),
        "adjudicator_id": adjudicator_id,
        "final_label": final_label,
        "disagreement": disagreement,
        "disagreement_fields": comparison["disagreement_fields"],
        "field_agreement": comparison["field_agreement"],
        "finalization_method": "adjudicator" if disagreement else "reviewer_agreement",
        "status": status,
        "rubric_version": RUBRIC_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


def validate_adjudication_record(record: dict[str, Any], public_case: dict[str, Any], *, kind: str) -> list[str]:
    errors = validate_annotations(public_case, record.get("annotations", []), kind=kind)
    if record.get("case_id") != _case_id(public_case):
        errors.append("record case_id does not match public case")
    if record.get("kind") != kind:
        errors.append("record kind does not match review kind")
    if record.get("status") not in RELEASE_STATUSES | {MACHINE_PILOT_STATUS}:
        errors.append("record has no valid adjudication status")
    annotations = record.get("annotations", [])
    if len(annotations) == 2:
        comparison = compare_annotations(annotations, kind=kind)
        if bool(record.get("disagreement")) != (not comparison["exact_label_agreement"]):
            errors.append("record disagreement flag is inconsistent with annotations")
    if record.get("disagreement") and not str(record.get("adjudicator_id") or "").strip():
        errors.append("disagreement is missing adjudicator_id")
    if record.get("status") == "adjudicated" and record.get("final_label") is None:
        errors.append("adjudicated record has no final_label")
    if record.get("final_label") is not None:
        errors.extend(_validate_label(record["final_label"], _public_evidence_ids(public_case), kind=kind, prefix="final label"))
    return errors


def _release_ready(record: dict[str, Any], public_case: dict[str, Any], *, kind: str) -> bool:
    return not validate_adjudication_record(record, public_case, kind=kind) and record.get("status") == "adjudicated"


def analyze_review_set(
    public_cases: Iterable[dict[str, Any]],
    records: Iterable[dict[str, Any]],
    *,
    kind: str,
) -> dict[str, Any]:
    cases = {_case_id(case): case for case in public_cases}
    review_records = list(records)
    errors: list[str] = []
    record_map: dict[str, dict[str, Any]] = {}
    for record in review_records:
        case_id = str(record.get("case_id", ""))
        if case_id in record_map:
            errors.append(f"duplicate adjudication record: {case_id}")
        record_map[case_id] = record
        if case_id not in cases:
            errors.append(f"adjudication record references unknown case: {case_id}")
    missing = sorted(set(cases) - set(record_map))
    status_counts = Counter(str(record.get("status", "missing")) for record in review_records)
    disagreement_fields: Counter[str] = Counter()
    exact_agreement = 0
    valid_records = 0
    release_ready = 0
    for case_id, record in record_map.items():
        if case_id not in cases:
            continue
        record_errors = validate_adjudication_record(record, cases[case_id], kind=kind)
        if record_errors:
            errors.extend(f"{case_id}: {error}" for error in record_errors)
            continue
        valid_records += 1
        if not record.get("disagreement"):
            exact_agreement += 1
        for field in record.get("disagreement_fields", []):
            disagreement_fields[str(field)] += 1
        if _release_ready(record, cases[case_id], kind=kind):
            release_ready += 1
    if missing:
        errors.append(f"missing adjudication records: {len(missing)}")
    if any(count for status, count in status_counts.items() if status in {"ambiguous", "rewrite_required"}):
        errors.append("ambiguous or rewrite-required cases cannot enter a release manifest")
    if status_counts.get(MACHINE_PILOT_STATUS):
        errors.append("machine-pilot records are diagnostic only and cannot enter a release manifest")
    release_status = "ready_for_manifest_merge" if not errors and release_ready == len(cases) else "blocked_pending_review"
    field_totals = len(review_records) if review_records else 0
    return {
        "ok": not errors,
        "kind": kind,
        "cases": len(cases),
        "review_records": len(review_records),
        "valid_records": valid_records,
        "release_ready_cases": release_ready,
        "missing_case_ids": missing,
        "status_counts": dict(status_counts),
        "agreement": {
            "exact_label_agreement": exact_agreement,
            "exact_label_agreement_rate": exact_agreement / valid_records if valid_records else None,
            "disagreement_fields": dict(disagreement_fields),
            "record_denominator": field_totals,
        },
        "errors": errors,
        "release_status": release_status,
    }


def merge_private_manifest(
    private_records: list[dict[str, Any]],
    adjudications: Iterable[dict[str, Any]],
    *,
    kind: str,
) -> list[dict[str, Any]]:
    """Attach human records while preserving every provisional field."""
    by_case = {str(record["case_id"]): record for record in adjudications}
    merged = copy.deepcopy(private_records)
    if kind == QUALIFICATION_KIND:
        for item in merged:
            case_id = str(item.get("id", ""))
            adjudication = by_case.get(case_id)
            if adjudication is None or adjudication.get("status") != "adjudicated":
                raise ValueError(f"qualification case is not release-ready: {case_id}")
            item["human_adjudication"] = adjudication
            item["adjudicated_verdict"] = adjudication["final_label"]["verdict"]
            item["reviewer_ids"] = [annotation["reviewer_id"] for annotation in adjudication["annotations"]]
            item["adjudication_status"] = "adjudicated"
        return merged
    for group in merged:
        adjudicated_ids: list[str] = []
        reviewer_ids: set[str] = set()
        adjudicator_ids: set[str] = set()
        for item in group.get("cases", []):
            case_id = str(item.get("public_case_id", ""))
            adjudication = by_case.get(case_id)
            if adjudication is None or adjudication.get("status") != "adjudicated":
                raise ValueError(f"seed case is not release-ready: {case_id}")
            item["human_adjudication"] = adjudication
            adjudicated_ids.append(case_id)
            reviewer_ids.update(str(annotation["reviewer_id"]) for annotation in adjudication["annotations"])
            if adjudication.get("adjudicator_id"):
                adjudicator_ids.add(str(adjudication["adjudicator_id"]))
        group["review"] = {
            "reviewer_ids": sorted(reviewer_ids),
            "adjudicator_ids": sorted(adjudicator_ids),
            "adjudication_status": "adjudicated",
            "rubric_version": RUBRIC_VERSION,
            "case_count": len(adjudicated_ids),
        }
    return merged


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _write_jsonl(path: Path, records: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n" for record in records), encoding="utf-8")


def _queue_cases(path: Path) -> list[dict[str, Any]]:
    records = _read_jsonl(path)
    cases = []
    for record in records:
        case = record.get("public_case", record.get("case"))
        if case is not None:
            cases.append(case)
    return cases


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze or merge Iboga v2 independent adjudication records")
    parser.add_argument("command", choices=("analyze", "merge"))
    parser.add_argument("--kind", choices=(SEED_KIND, QUALIFICATION_KIND), required=True)
    parser.add_argument("--queue", type=Path, help="JSONL adjudication queue containing public_case records")
    parser.add_argument("--reviews", type=Path, help="JSONL adjudication records")
    parser.add_argument("--private-pending", type=Path, help="JSONL private pending manifest for merge")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    records = _read_jsonl(args.reviews) if args.reviews else []
    if args.command == "analyze":
        if args.queue is None:
            parser.error("analyze requires --queue")
        report = analyze_review_set(_queue_cases(args.queue), records, kind=args.kind)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(report, ensure_ascii=False, indent=2))
        raise SystemExit(0 if report["ok"] else 2)
    if args.private_pending is None:
        parser.error("merge requires --private-pending")
    private = _read_jsonl(args.private_pending)
    merged = merge_private_manifest(private, records, kind=args.kind)
    _write_jsonl(args.out, merged)
    print(json.dumps({"ok": True, "records": len(merged), "out": str(args.out)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
