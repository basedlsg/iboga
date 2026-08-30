from __future__ import annotations

import argparse
import json
from pathlib import Path

from .audit import audit_dataset
from .challenge import PrivateChallengeSet
from .contracts import ActionProposal
from .gate import evaluate_action
from .inspect_adapter import write_inspect_jsonl
from .pilot import write_reference_pilot


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(prog="reliability", description="Evidence-grounded agent reliability utilities")
    sub = parser.add_subparsers(dest="command", required=True)

    audit = sub.add_parser("audit", help="audit a public JSONL benchmark")
    audit.add_argument("cases", type=Path)

    export = sub.add_parser("inspect-export", help="export public cases to Inspect JSONL")
    export.add_argument("cases", type=Path)
    export.add_argument("out", type=Path)

    gate = sub.add_parser("gate", help="evaluate one action proposal without a model")
    gate.add_argument("proposal", type=Path)
    gate.add_argument("--evidence", nargs="*", default=[])

    pilot = sub.add_parser("pilot", help="run the deterministic reference workflow pilot")
    pilot.add_argument("--out", type=Path, default=Path("results/reliability-pilot-v0.1.json"))

    challenge = sub.add_parser("challenge-audit", help="validate a public/private challenge-set boundary")
    challenge.add_argument("public_cases", type=Path)
    challenge.add_argument("gold_cases", type=Path)

    args = parser.parse_args()
    if args.command == "audit":
        print(json.dumps(audit_dataset(load_jsonl(args.cases)), indent=2))
    elif args.command == "inspect-export":
        cases = load_jsonl(args.cases)
        write_inspect_jsonl(cases, args.out)
        print(json.dumps({"written": len(cases), "path": str(args.out)}, indent=2))
    elif args.command == "gate":
        proposal = ActionProposal.from_dict(json.loads(args.proposal.read_text(encoding="utf-8")))
        print(json.dumps(evaluate_action(proposal, set(args.evidence)).as_dict(), indent=2))
    elif args.command == "pilot":
        result = write_reference_pilot(args.out)
        print(json.dumps({"experiment": result["experiment"], "n": result["n"], "passed": result["passed"], "path": str(args.out)}, indent=2))
    elif args.command == "challenge-audit":
        challenge_set = PrivateChallengeSet.from_jsonl(args.public_cases, args.gold_cases)
        print(json.dumps({"ok": True, "n": len(challenge_set.public_cases), "gold_records": len(challenge_set.gold_by_id)}, indent=2))


if __name__ == "__main__":
    main()
