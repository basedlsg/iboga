"""Audit a longitudinal experiment manifest against protocol v1.0.

This module is deliberately conservative.  It does not turn a small fixture
into evidence by adding paraphrases or repeats.  It reports the independent
semantic groups, stage/domain coverage, split hygiene, provenance, and
condition coverage that must be present before a live efficacy run.

The audit accepts either a JSON array or JSONL records.  Gold labels are
expected to live in a private manifest; the audit only checks that the public
record declares the required shape and that the private metadata is complete.
It is therefore useful both for the current hand-authored pilot and for the
larger buyer-domain dataset that will replace it.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


REQUIRED_STAGES = tuple(range(1, 10))
REQUIRED_CONDITIONS = ("D", "N", "L", "S", "R", "C", "G")
REQUIRED_PHASES = ("immediate", "delayed", "transfer", "negative")


@dataclass(frozen=True)
class ProtocolRequirements:
    """Minimum checks for a registered pilot or confirmatory manifest."""

    min_groups_per_stage: int = 12
    min_domains: int = 3
    max_domain_fraction: float = 0.35
    require_confirmatory_split: bool = True
    require_provenance: bool = True
    require_human_review: bool = True
    require_all_conditions: bool = True


def _read_records(path: Path) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return []
    if text.startswith("["):
        value = json.loads(text)
        if not isinstance(value, list):
            raise ValueError("JSON manifest must contain an array")
        records = value
    else:
        records = [json.loads(line) for line in text.splitlines() if line.strip()]
    if not all(isinstance(record, dict) for record in records):
        raise ValueError("manifest records must be JSON objects")
    return records


def _first(record: dict[str, Any], *keys: str, default: Any = None) -> Any:
    for key in keys:
        if key in record and record[key] not in (None, ""):
            return record[key]
    return default


def _metadata(record: dict[str, Any]) -> dict[str, Any]:
    value = record.get("metadata")
    return value if isinstance(value, dict) else record


def audit_manifest(
    records: Iterable[dict[str, Any]],
    *,
    requirements: ProtocolRequirements | None = None,
    conditions: Iterable[str] = REQUIRED_CONDITIONS,
) -> dict[str, Any]:
    """Return a no-go report when the manifest cannot support the protocol.

    ``semantic_group_id`` is the unit of inference.  Records that are merely
    variants, probes, or repeats must point to the same group and therefore do
    not increase the independent-group count.
    """

    req = requirements or ProtocolRequirements()
    records = list(records)
    errors: list[str] = []
    warnings: list[str] = []
    ids: list[str] = []
    groups: dict[str, set[str]] = defaultdict(set)
    group_stages: dict[str, set[int]] = defaultdict(set)
    group_domains: dict[str, set[str]] = defaultdict(set)
    stage_groups: dict[int, set[str]] = defaultdict(set)
    domain_counts: Counter[str] = Counter()
    split_counts: Counter[str] = Counter()
    condition_counts: Counter[str] = Counter()
    phase_counts: Counter[str] = Counter()

    for index, record in enumerate(records):
        record_id = str(_first(record, "id", "case_id", default=f"record-{index}"))
        ids.append(record_id)
        if not _first(record, "id", "case_id"):
            errors.append(f"{record_id}: missing stable id")

        group = _first(record, "semantic_group_id", "seed_group_id", "seed_id")
        if not group:
            errors.append(f"{record_id}: missing semantic_group_id")
            group = f"__missing__:{record_id}"
        group = str(group)

        stage = _first(record, "stage")
        try:
            stage_int = int(stage)
        except (TypeError, ValueError):
            errors.append(f"{record_id}: stage must be an integer from 1 to 9")
            stage_int = 0
        if stage_int not in REQUIRED_STAGES:
            errors.append(f"{record_id}: invalid stage {stage!r}")

        domain = _first(record, "domain")
        if not domain:
            errors.append(f"{record_id}: missing domain")
            domain = "__missing__"
        domain = str(domain)

        split = str(_first(record, "split", default="__missing__"))
        phase = str(_first(record, "phase", "probe_kind", default="immediate"))
        condition = _first(record, "condition")

        groups[group].add(split)
        group_stages[group].add(stage_int)
        group_domains[group].add(domain)
        stage_groups[stage_int].add(group)
        domain_counts[domain] += 1
        split_counts[split] += 1
        phase_counts[phase] += 1
        if condition:
            condition_counts[str(condition)] += 1

        metadata = _metadata(record)
        if req.require_provenance:
            provenance = record.get("provenance") or metadata.get("provenance")
            if not isinstance(provenance, dict):
                errors.append(f"{record_id}: missing provenance")
            else:
                for field in ("generator", "generator_version", "code_revision", "rights_status", "privacy_review"):
                    if not provenance.get(field):
                        errors.append(f"{record_id}: provenance missing {field}")

        if req.require_human_review:
            reviewers = _first(record, "reviewer_ids", default=metadata.get("reviewer_ids"))
            adjudication = _first(record, "adjudication_status", default=metadata.get("adjudication_status"))
            if not isinstance(reviewers, list) or len(reviewers) < 2:
                errors.append(f"{record_id}: requires two independent reviewer IDs")
            if adjudication != "adjudicated":
                errors.append(f"{record_id}: requires adjudication_status=adjudicated")

    if len(ids) != len(set(ids)):
        errors.append("duplicate stable IDs")

    for group, splits in sorted(groups.items()):
        if len(splits) > 1:
            errors.append(f"semantic group crosses split boundary: {group}")

    for stage in REQUIRED_STAGES:
        count = len(stage_groups.get(stage, set()))
        if count < req.min_groups_per_stage:
            errors.append(
                f"stage {stage} has {count} independent groups; "
                f"requires at least {req.min_groups_per_stage}"
            )

    real_domains = {domain for domain in domain_counts if domain != "__missing__"}
    if len(real_domains) < req.min_domains:
        errors.append(f"only {len(real_domains)} domains; requires at least {req.min_domains}")
    total = sum(domain_counts.values())
    if total:
        largest_domain, largest_count = domain_counts.most_common(1)[0]
        fraction = largest_count / total
        if largest_domain != "__missing__" and fraction > req.max_domain_fraction:
            errors.append(
                f"domain {largest_domain} contributes {fraction:.1%}; "
                f"maximum is {req.max_domain_fraction:.1%}"
            )

    missing_phases = sorted(set(REQUIRED_PHASES) - set(phase_counts))
    if missing_phases:
        errors.append(f"missing required phases: {', '.join(missing_phases)}")
    if req.require_confirmatory_split and "confirmatory" not in split_counts:
        errors.append("missing confirmatory split")
    if req.require_all_conditions:
        missing_conditions = sorted(set(conditions) - set(condition_counts))
        if missing_conditions:
            errors.append(f"missing registered conditions: {', '.join(missing_conditions)}")

    if len(records) > len(groups):
        warnings.append(
            f"{len(records) - len(groups)} records are variants, probes, repeats, or otherwise "
            "not independent semantic groups"
        )
    if not errors:
        warnings.append("manifest meets structural protocol checks; this is not evidence of efficacy")

    return {
        "ok": not errors,
        "release_status": "eligible_for_next_gate" if not errors else "no_go",
        "record_count": len(records),
        "independent_group_count": len(groups),
        "stage_group_counts": {str(stage): len(stage_groups.get(stage, set())) for stage in REQUIRED_STAGES},
        "domain_counts": dict(domain_counts),
        "split_counts": dict(split_counts),
        "phase_counts": dict(phase_counts),
        "condition_counts": dict(condition_counts),
        "errors": errors,
        "warnings": warnings,
    }


def audit_current_fixture() -> dict[str, Any]:
    """Audit the existing v0.4 fixture without pretending it is v1.0 data."""

    from .curriculum_v04 import build_cases, build_probes

    records: list[dict[str, Any]] = []
    for case in build_cases():
        records.append({
            "id": case.case_id,
            "semantic_group_id": case.lesson_id,
            "stage": case.stage,
            "domain": "legacy_fixture",
            "split": "development",
            "phase": "immediate",
            "condition": "legacy",
        })
    for probe in build_probes():
        records.append({
            "id": probe.probe_id,
            "semantic_group_id": probe.lesson_id,
            "stage": probe.source_stage,
            "domain": "legacy_fixture",
            "split": "development",
            "phase": probe.probe_kind,
            "condition": "legacy",
        })
    return audit_manifest(records)


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit an Iboga protocol manifest")
    parser.add_argument("--manifest", type=Path, help="JSON array or JSONL manifest")
    parser.add_argument("--current-fixture", action="store_true", help="audit the legacy v0.4 fixture")
    args = parser.parse_args()
    if bool(args.manifest) == bool(args.current_fixture):
        parser.error("choose exactly one of --manifest or --current-fixture")
    report = audit_current_fixture() if args.current_fixture else audit_manifest(_read_records(args.manifest))
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if not report["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
