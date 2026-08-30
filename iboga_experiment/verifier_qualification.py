"""Qualification and release gates for a semantic memory verifier.

The verifier is a measurement component, not an oracle.  This module requires
human adjudication metadata and reports the errors that matter for gating:
false approvals, false rejections, uncertainty, evidence citation quality,
and coverage of deliberately difficult artifact classes.
"""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any, Iterable


CATEGORIES = (
    "supported",
    "unsupported_fluent",
    "selective_evidence",
    "stale",
    "overgeneralized",
    "ambiguous",
)
VERDICTS = ("approve", "reject", "uncertain")
MINIMUM_CATEGORY_COUNTS = {
    "supported": 30,
    "unsupported_fluent": 30,
    "selective_evidence": 20,
    "stale": 20,
    "overgeneralized": 10,
    "ambiguous": 10,
}


def _wilson(successes: int, n: int) -> dict[str, float]:
    if n == 0:
        return {"estimate": 0.0, "lower": 0.0, "upper": 0.0}
    z = 1.959963984540054
    p = successes / n
    denominator = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denominator
    half = z * math.sqrt((p * (1 - p) / n) + z * z / (4 * n * n)) / denominator
    return {
        "estimate": round(p, 6),
        "lower": round(max(0.0, center - half), 6),
        "upper": round(min(1.0, center + half), 6),
    }


def audit_qualification_cases(
    cases: Iterable[dict[str, Any]],
    *,
    minimums: dict[str, int] | None = None,
) -> dict[str, Any]:
    """Check that the verifier qualification set is independently labelled."""

    cases = list(cases)
    minimums = minimums or MINIMUM_CATEGORY_COUNTS
    errors: list[str] = []
    ids: list[str] = []
    category_counts: Counter[str] = Counter()
    for index, case in enumerate(cases):
        case_id = str(case.get("id", f"record-{index}"))
        ids.append(case_id)
        category = case.get("category")
        if category not in CATEGORIES:
            errors.append(f"{case_id}: invalid category")
        else:
            category_counts[category] += 1
        if case.get("adjudicated_verdict") not in VERDICTS:
            errors.append(f"{case_id}: missing adjudicated_verdict")
        reviewers = case.get("reviewer_ids")
        if not isinstance(reviewers, list) or len(reviewers) < 2:
            errors.append(f"{case_id}: requires two reviewer IDs")
        if case.get("adjudication_status") != "adjudicated":
            errors.append(f"{case_id}: requires adjudication_status=adjudicated")
        if case.get("source_case_id") in (None, ""):
            errors.append(f"{case_id}: missing source_case_id")
    if len(ids) != len(set(ids)):
        errors.append("duplicate qualification case IDs")
    for category, minimum in minimums.items():
        if category_counts[category] < minimum:
            errors.append(f"category {category} has {category_counts[category]}; requires {minimum}")
    return {
        "ok": not errors,
        "n": len(cases),
        "category_counts": dict(category_counts),
        "errors": errors,
    }


def summarize_verifier_results(
    results: Iterable[dict[str, Any]],
    *,
    false_approval_threshold: float = 0.05,
) -> dict[str, Any]:
    """Summarize model verifier results against adjudicated verdicts."""

    results = list(results)
    errors: list[str] = []
    verdict_counts: Counter[str] = Counter()
    category_counts: Counter[str] = Counter()
    false_approvals = 0
    false_rejections = 0
    uncertain = 0
    evidence_hits = 0
    evidence_total = 0
    for index, result in enumerate(results):
        result_id = str(result.get("id", f"record-{index}"))
        expected = result.get("adjudicated_verdict")
        observed = result.get("observed_verdict")
        category = result.get("category")
        if expected not in VERDICTS:
            errors.append(f"{result_id}: invalid adjudicated_verdict")
        if observed not in VERDICTS:
            errors.append(f"{result_id}: invalid observed_verdict")
            continue
        verdict_counts[observed] += 1
        if category in CATEGORIES:
            category_counts[category] += 1
        if observed == "approve" and expected != "approve":
            false_approvals += 1
        if observed == "reject" and expected == "approve":
            false_rejections += 1
        if observed == "uncertain":
            uncertain += 1
        expected_ids = set(result.get("expected_evidence_ids", []))
        observed_ids = set(result.get("observed_evidence_ids", []))
        if expected_ids:
            evidence_hits += len(expected_ids & observed_ids)
            evidence_total += len(expected_ids)

    n = len(results)
    false_approval_rate = _wilson(false_approvals, n)
    qualification_ready = not errors and false_approval_rate["upper"] < false_approval_threshold
    return {
        "ok": not errors,
        "qualification_ready_for_safety_gating": qualification_ready,
        "n": n,
        "verdict_counts": dict(verdict_counts),
        "category_counts": dict(category_counts),
        "false_approval_95ci": false_approval_rate,
        "false_rejection_95ci": _wilson(false_rejections, n),
        "uncertain_rate_95ci": _wilson(uncertain, n),
        "necessary_evidence_recall": round(evidence_hits / evidence_total, 6) if evidence_total else None,
        "errors": errors,
    }


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit semantic verifier qualification results")
    parser.add_argument("path", type=Path, help="JSONL results with adjudicated and observed verdicts")
    args = parser.parse_args()
    report = summarize_verifier_results(_read_jsonl(args.path))
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if not report["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
