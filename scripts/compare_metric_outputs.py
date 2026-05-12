#!/usr/bin/env python3
"""Compare SlopCodeBench reproduction metric summaries.

Expected CSV columns:
model,problem_id,solve_rate,erosion_slope,verbosity_slope

Rates may be in proportions or percentages; the script reports absolute deltas
in percentage points for all three metrics after coercing numeric values.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


KEYS = ["model", "problem_id"]
METRICS = ["solve_rate", "erosion_slope", "verbosity_slope"]


def load_csv(path: Path) -> dict[tuple[str, str], dict[str, float]]:
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        missing = [col for col in KEYS + METRICS if col not in (reader.fieldnames or [])]
        if missing:
            raise ValueError(f"{path} missing columns: {missing}")
        rows = {}
        for row in reader:
            key = tuple(row[col] for col in KEYS)
            rows[key] = {metric: float(row[metric]) for metric in METRICS}
        return rows


def to_pp_delta(a: float, b: float) -> float:
    # If both values look like proportions, convert to percentage points.
    if abs(a) <= 1.5 and abs(b) <= 1.5:
        return (a - b) * 100
    return a - b


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--upstream", required=True, type=Path)
    parser.add_argument("--fork", required=True, type=Path)
    parser.add_argument("--tolerance-pp", type=float, default=2.0)
    args = parser.parse_args()

    upstream = load_csv(args.upstream)
    fork = load_csv(args.fork)

    all_keys = sorted(set(upstream) | set(fork))
    failures = 0
    print("| Model | Problem | Metric | Upstream | Fork | Delta pp | Pass? |")
    print("|---|---|---|---:|---:|---:|---|")
    for key in all_keys:
        if key not in upstream or key not in fork:
            failures += 1
            print(f"| {key[0]} | {key[1]} | missing-row | NA | NA | NA | false |")
            continue
        for metric in METRICS:
            delta = to_pp_delta(fork[key][metric], upstream[key][metric])
            passed = abs(delta) <= args.tolerance_pp
            failures += 0 if passed else 1
            print(
                f"| {key[0]} | {key[1]} | {metric} | "
                f"{upstream[key][metric]:.6g} | {fork[key][metric]:.6g} | "
                f"{delta:.4f} | {str(passed).lower()} |"
            )

    if failures:
        raise SystemExit(f"Metric comparison failed: {failures} item(s) outside tolerance")
    print(f"\nAll compared metrics within ±{args.tolerance_pp} pp.")


if __name__ == "__main__":
    main()
