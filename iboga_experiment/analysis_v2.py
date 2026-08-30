"""Dependency-free analysis for the registered longitudinal experiment.

The functions operate on completed trajectory summaries, not raw model prose.
Missing or malformed runs remain visible through availability statistics and are
not silently converted into successes.
"""

from __future__ import annotations

import random
from collections import defaultdict
from typing import Any, Callable, Iterable


def wilson_interval(successes: int, total: int, z: float = 1.959963984540054) -> tuple[float, float]:
    if total < 0 or successes < 0 or successes > total:
        raise ValueError("successes and total must satisfy 0 <= successes <= total")
    if total == 0:
        return (0.0, 0.0)
    p = successes / total
    denominator = 1 + z * z / total
    centre = (p + z * z / (2 * total)) / denominator
    margin = z * ((p * (1 - p) / total + z * z / (4 * total * total)) ** 0.5) / denominator
    return (max(0.0, centre - margin), min(1.0, centre + margin))


def _available(record: dict[str, Any]) -> bool:
    return bool(record.get("available", record.get("run_status", "completed") == "completed"))


def _metric(record: dict[str, Any], endpoint: str) -> float | None:
    value = record.get(endpoint)
    if value is None and isinstance(record.get("metrics"), dict):
        value = record["metrics"].get(endpoint)
    if isinstance(value, bool):
        return float(value)
    if isinstance(value, (int, float)):
        return float(value)
    return None


def summarize_condition(records: Iterable[dict[str, Any]], condition: str, endpoint: str = "safe_correct_success") -> dict[str, Any]:
    selected = [record for record in records if record.get("condition") == condition]
    completed = [record for record in selected if _available(record)]
    values = [value for record in completed if (value := _metric(record, endpoint)) is not None]
    successes = sum(value >= 1 for value in values)
    interval = wilson_interval(successes, len(values))
    missing = len(selected) - len(values)
    return {
        "condition": condition,
        "endpoint": endpoint,
        "successes": successes,
        "total": len(values),
        "rate": successes / len(values) if values else 0.0,
        "wilson_95": {"lower": interval[0], "upper": interval[1]},
        "requested": len(selected),
        "missing_or_invalid": missing,
        "availability_rate": len(values) / len(selected) if selected else 0.0,
    }


def _group_values(records: Iterable[dict[str, Any]], condition: str, endpoint: str) -> dict[str, float]:
    result: dict[str, float] = {}
    for record in records:
        if record.get("condition") != condition or not _available(record):
            continue
        group = record.get("semantic_group_id") or record.get("group_id")
        value = _metric(record, endpoint)
        if group is not None and value is not None:
            result[str(group)] = value
    return result


def paired_difference(
    records: Iterable[dict[str, Any]],
    treatment: str = "G",
    control: str = "N",
    endpoint: str = "safe_correct_success",
) -> dict[str, Any]:
    records = list(records)
    treated = _group_values(records, treatment, endpoint)
    baseline = _group_values(records, control, endpoint)
    shared = sorted(set(treated) & set(baseline))
    differences = [treated[group] - baseline[group] for group in shared]
    wins = sum(value > 0 for value in differences)
    losses = sum(value < 0 for value in differences)
    ties = len(differences) - wins - losses
    return {
        "treatment": treatment,
        "control": control,
        "endpoint": endpoint,
        "groups_treatment": len(treated),
        "groups_control": len(baseline),
        "paired_groups": len(shared),
        "mean_difference": sum(differences) / len(differences) if differences else 0.0,
        "wins": wins,
        "losses": losses,
        "ties": ties,
        "group_differences": dict(zip(shared, differences)),
    }


def cluster_bootstrap_difference(
    records: Iterable[dict[str, Any]],
    treatment: str = "G",
    control: str = "N",
    endpoint: str = "safe_correct_success",
    *,
    repeats: int = 2_000,
    seed: int = 7,
) -> dict[str, float]:
    paired = paired_difference(records, treatment, control, endpoint)
    differences = list(paired["group_differences"].values())
    if not differences:
        return {"lower": 0.0, "median": 0.0, "upper": 0.0}
    rng = random.Random(seed)
    samples = []
    for _ in range(repeats):
        draw = [rng.choice(differences) for _ in differences]
        samples.append(sum(draw) / len(draw))
    samples.sort()
    def quantile(p: float) -> float:
        index = min(len(samples) - 1, max(0, int(round((len(samples) - 1) * p))))
        return samples[index]
    return {"lower": quantile(0.025), "median": quantile(0.5), "upper": quantile(0.975)}


def analyze(records: Iterable[dict[str, Any]], *, primary_treatment: str = "G", primary_control: str = "N") -> dict[str, Any]:
    records = list(records)
    conditions = sorted({str(record.get("condition")) for record in records if record.get("condition")})
    endpoints = ("safe_correct_success", "unsafe_commit", "over_refusal", "delayed_success", "transfer_success", "negative_success")
    summaries = {condition: {endpoint: summarize_condition(records, condition, endpoint) for endpoint in endpoints} for condition in conditions}
    primary = paired_difference(records, primary_treatment, primary_control, "safe_correct_success")
    primary["bootstrap_95"] = cluster_bootstrap_difference(records, primary_treatment, primary_control, "safe_correct_success")
    failures = defaultdict(int)
    for record in records:
        if not _available(record):
            failures[str(record.get("error_type", "unavailable"))] += 1
    return {
        "analysis": "iboga-longitudinal-v2",
        "unit_of_inference": "semantic_group_id",
        "conditions": conditions,
        "summaries": summaries,
        "primary": primary,
        "unavailable_by_error": dict(failures),
    }
