#!/usr/bin/env python3
"""Generate deterministic Iboga arm assignments.

This script intentionally uses only the Python standard library. It does not
inspect SlopCodeBench; pass locked problem IDs in a local text file after the
fork is pinned.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_MODELS = [
    "opus-4.7",
    "qwen-2.5-32b",
    "llama-3.1-8b",
    "deepseek-coder-v3",
]

MAIN_ARMS = ["A_iboga", "B_neutral", "C_unstructured"]
PILOT_ARMS = ["A_iboga", "B_neutral", "C_unstructured", "arm0_noop"]

SCHEMA_BY_ARM = {
    "A_iboga": "schemas/arm-a.json",
    "B_neutral": "schemas/arm-b.json",
    "C_unstructured": "schemas/arm-c.json",
    "arm0_noop": "schemas/arm-c.json",
}


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def read_problem_ids(path: Path) -> list[str]:
    raw = path.read_text(encoding="utf-8").splitlines()
    problem_ids = []
    for line in raw:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        problem_ids.append(line)
    if not problem_ids:
        raise ValueError(f"No problem IDs found in {path}")
    if len(problem_ids) != len(set(problem_ids)):
        raise ValueError("Problem IDs must be unique")
    return problem_ids


def make_record(
    *,
    phase: str,
    model_id: str,
    problem_id: str,
    arm: str,
    assignment_seed: str,
) -> dict[str, str]:
    run_seed = sha256_text(
        f"iboga-v0.5|seed|{model_id}|{problem_id}|{arm}|{assignment_seed}"
    )
    trajectory_id = sha256_text(
        f"iboga-v0.5|{phase}|{model_id}|{problem_id}|{arm}|{run_seed}"
    )
    return {
        "trajectory_id": trajectory_id,
        "phase": phase,
        "model_id": model_id,
        "problem_id": problem_id,
        "arm": arm,
        "run_seed": run_seed,
        "schema_file": SCHEMA_BY_ARM[arm],
    }


def validate(records: list[dict[str, str]], *, models: list[str], problem_ids: list[str], phase: str) -> None:
    ids = [r["trajectory_id"] for r in records]
    if len(ids) != len(set(ids)):
        raise ValueError("trajectory_id values must be unique")

    expected_arms = PILOT_ARMS if phase == "pilot" else MAIN_ARMS
    if phase == "main" and any(r["arm"] == "arm0_noop" for r in records):
        raise ValueError("Arm 0 cannot appear in main phase")

    by_pair: dict[tuple[str, str], list[str]] = {}
    for record in records:
        key = (record["model_id"], record["problem_id"])
        by_pair.setdefault(key, []).append(record["arm"])
        schema_path = Path(record["schema_file"])
        if not schema_path.exists():
            raise ValueError(f"Schema file missing: {schema_path}")

    for model_id in models:
        for problem_id in problem_ids:
            arms = sorted(by_pair.get((model_id, problem_id), []))
            if arms != sorted(expected_arms):
                raise ValueError(
                    f"Expected {expected_arms} for {(model_id, problem_id)}, got {arms}"
                )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--problems-file", required=True, type=Path)
    parser.add_argument("--assignment-seed", required=True)
    parser.add_argument("--phase", choices=["main", "pilot"], default="main")
    parser.add_argument("--out", type=Path, default=Path("arm-assignment.json"))
    parser.add_argument("--models", nargs="+", default=DEFAULT_MODELS)
    args = parser.parse_args()

    problem_ids = read_problem_ids(args.problems_file)
    arms = PILOT_ARMS if args.phase == "pilot" else MAIN_ARMS

    records = [
        make_record(
            phase=args.phase,
            model_id=model_id,
            problem_id=problem_id,
            arm=arm,
            assignment_seed=args.assignment_seed,
        )
        for model_id in args.models
        for problem_id in problem_ids
        for arm in arms
    ]
    records.sort(key=lambda r: r["trajectory_id"])
    validate(records, models=args.models, problem_ids=problem_ids, phase=args.phase)

    payload = {
        "version": "0.5.0",
        "status": "draft",
        "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "assignment_seed": args.assignment_seed,
        "models": args.models,
        "problem_ids": problem_ids,
        "arms": MAIN_ARMS,
        "pilot_arms": PILOT_ARMS,
        "phase": args.phase,
        "records": records,
    }
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    digest = sha256_text(args.out.read_text(encoding="utf-8"))
    print(f"Wrote {args.out}")
    print(f"records={len(records)}")
    print(f"sha256={digest}")


if __name__ == "__main__":
    main()
