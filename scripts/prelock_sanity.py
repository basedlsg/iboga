#!/usr/bin/env python3
"""Cheap local sanity checks for Iboga pre-lock artifacts."""

from __future__ import annotations

import ast
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = [
    "CLAUDE.md",
    "README.md",
    "prereg.md",
    "next-steps.md",
    "week-1-runbook.md",
    "slopcodebench-study.md",
    "arm-templates.md",
    "arm-token-budget.md",
    "arm-assignment-spec.md",
    "failure-types.md",
    "annotator-rubric.md",
    "analysis-plan.R",
    "power-calc.R",
    "sae-features-decision.md",
    "sprocketlab-email.md",
    "harness-validation.md",
    "handoff-prompt.md",
    "schemas/README.md",
    "schemas/arm-a.json",
    "schemas/arm-b.json",
    "schemas/arm-c.json",
    "scripts/compare_metric_outputs.py",
    "scripts/generate_arm_assignment.py",
    "scripts/inspect_slopcodebench_repo.py",
    "scripts/prelock_sanity.py",
]

STALE_PHRASES = [
    "Token-match all three arms within",
    "free-form retrospective with <=2000 token cap",
    "single free-form turn",
    "no tool calls",
    "locked closed list",
    "top_decile_CC",
    "Power was computed via R",
    "Drop one model",
]


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    sys.exit(1)


def check_required_files() -> None:
    missing = [path for path in REQUIRED_FILES if not (ROOT / path).exists()]
    if missing:
        fail(f"Missing required files: {missing}")


def check_json() -> None:
    for rel in ["schemas/arm-a.json", "schemas/arm-b.json", "schemas/arm-c.json"]:
        path = ROOT / rel
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            fail(f"Invalid JSON in {rel}: {exc}")


def check_python_syntax() -> None:
    for rel in [
        "scripts/compare_metric_outputs.py",
        "scripts/generate_arm_assignment.py",
        "scripts/inspect_slopcodebench_repo.py",
        "scripts/prelock_sanity.py",
    ]:
        path = ROOT / rel
        try:
            ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError as exc:
            fail(f"Syntax error in {rel}: {exc}")


def check_stale_phrases() -> None:
    haystack = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in ROOT.rglob("*")
        if path.is_file()
        and path.name != "prelock_sanity.py"
        and ".git" not in path.parts
        and "__pycache__" not in path.parts
        and path.suffix in {".md", ".R", ".py", ".json"}
    )
    hits = [phrase for phrase in STALE_PHRASES if phrase in haystack]
    if hits:
        fail(f"Stale phrase(s) found: {hits}")


def main() -> None:
    check_required_files()
    check_json()
    check_python_syntax()
    check_stale_phrases()
    print("prelock sanity ok")


if __name__ == "__main__":
    main()
