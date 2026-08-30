#!/usr/bin/env python3
"""Inspect a local SlopCodeBench clone for Iboga harness-validation notes.

The script reads only the repo path explicitly supplied by the user. It does
not modify the SlopCodeBench checkout.
"""

from __future__ import annotations

import argparse
from pathlib import Path


KEYWORDS = {
    "verbosity": [
        "clone",
        "duplicate",
        "ast-grep",
        "ast_grep",
        "subprocess",
        "hash",
        "minhash",
        "jaccard",
        "shingle",
        "symlink",
    ],
    "erosion": [
        "radon",
        "cc_visit",
        "complexity",
        "sqrt",
        "slope",
        "polyfit",
        "linregress",
        "LinearRegression",
        "> 10",
        ">= 10",
    ],
    "runner": [
        "docker",
        "checkpoint",
        "prompt",
        "spec",
        "workspace",
        "container",
        "subprocess",
        "model",
        "agent",
    ],
}


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="replace")


def find_named_file(root: Path, filename: str) -> list[Path]:
    return sorted(path for path in root.rglob(filename) if ".git" not in path.parts)


def collect_keyword_lines(path: Path, keywords: list[str]) -> list[str]:
    lines = []
    for i, line in enumerate(read_text(path).splitlines(), start=1):
        lower = line.lower()
        if any(keyword.lower() in lower for keyword in keywords):
            lines.append(f"{path}:{i}: {line.rstrip()}")
    return lines


def section(title: str) -> None:
    print(f"\n## {title}\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, type=Path, help="Local SlopCodeBench clone path")
    args = parser.parse_args()

    repo = args.repo.expanduser().resolve()
    if not repo.exists() or not repo.is_dir():
        raise SystemExit(f"Repo path not found: {repo}")

    print("# SlopCodeBench Inspection Notes")
    print(f"\nRepo: `{repo}`")

    section("Metric Files")
    for name, kind in [("verbosity.py", "verbosity"), ("erosion.py", "erosion")]:
        matches = find_named_file(repo, name)
        print(f"- `{name}`: {len(matches)} match(es)")
        for match in matches:
            print(f"  - `{match.relative_to(repo)}`")
            for line in collect_keyword_lines(match, KEYWORDS[kind])[:80]:
                print(f"    - `{line}`")

    section("Runner Candidates")
    candidates = []
    for dirname in ["runner", "runners", "src", "slop_code_bench"]:
        path = repo / dirname
        if path.exists():
            candidates.extend(p for p in path.rglob("*.py") if ".git" not in p.parts)
    candidates = sorted(set(candidates))
    print(f"Python runner candidate files: {len(candidates)}")
    for path in candidates[:80]:
        hits = collect_keyword_lines(path, KEYWORDS["runner"])
        if hits:
            print(f"\n### `{path.relative_to(repo)}`")
            for line in hits[:40]:
                print(f"- `{line}`")

    section("Docker Files")
    docker_files = sorted(
        p for p in repo.rglob("*")
        if p.is_file() and (p.name == "Dockerfile" or p.name.endswith(".Dockerfile"))
    )
    for path in docker_files:
        print(f"- `{path.relative_to(repo)}`")


if __name__ == "__main__":
    main()
