from __future__ import annotations

import argparse
import json
from pathlib import Path

from .bardo import BardoSession
from .seals import VERIFIED_SEALS, saturn_test, validate_seal
from .stages import STAGES, audit_stage_cases


def main() -> None:
    parser = argparse.ArgumentParser(prog="grimoire", description="Bildung / Iboga agent lifecycle runtime")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("stages")
    sub.add_parser("audit-stages")
    seals = sub.add_parser("seals")
    seals.add_argument("--name")
    saturn = sub.add_parser("saturn-test")
    saturn.add_argument("proposal", type=Path)
    bardo = sub.add_parser("bardo-demo")
    bardo.add_argument("--out", type=Path)
    args = parser.parse_args()
    if args.command == "stages":
        print(json.dumps([stage.__dict__ for stage in STAGES], indent=2))
    elif args.command == "audit-stages":
        print(json.dumps(audit_stage_cases(), indent=2))
    elif args.command == "seals":
        if args.name:
            if args.name not in VERIFIED_SEALS:
                raise SystemExit(f"unknown seal: {args.name}")
            print(json.dumps(VERIFIED_SEALS[args.name], indent=2))
        else:
            print(json.dumps({name: {"errors": validate_seal(seal), "domain": seal["domain"]} for name, seal in VERIFIED_SEALS.items()}, indent=2))
    elif args.command == "saturn-test":
        print(json.dumps(saturn_test(json.loads(args.proposal.read_text(encoding="utf-8"))), indent=2))
    elif args.command == "bardo-demo":
        session = BardoSession()
        session.record("tool_call", {"name": "search", "text": "same query"})
        session.record("error", {"message": "timeout", "text": "timeout"})
        session.record("contradiction", {"text": "prior claim conflicts with new evidence", "contradiction": True})
        session.enter_forced_sitting()
        output = session.snapshot(args.out)
        print(json.dumps(output, indent=2))
