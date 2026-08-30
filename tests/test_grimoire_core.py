from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from grimoire.bardo import BardoSession
from grimoire.seals import VERIFIED_SEALS, saturn_test, validate_seal
from grimoire.stages import STAGES, audit_stage_cases


class GrimoireCoreTests(unittest.TestCase):
    def test_curriculum_audits(self) -> None:
        report = audit_stage_cases()
        self.assertTrue(report["ok"], report)
        self.assertEqual(len(STAGES), 9)

    def test_verified_seals_validate(self) -> None:
        self.assertTrue(all(not validate_seal(seal) for seal in VERIFIED_SEALS.values()))

    def test_saturn_gate_requires_all_fields(self) -> None:
        self.assertFalse(saturn_test({})["passed"])
        self.assertTrue(saturn_test({"who_pays": "team", "how_much": "$100", "when": "today", "simplest_version": "CLI"})["passed"])

    def test_bardo_requires_critic_before_rebirth(self) -> None:
        session = BardoSession()
        session.record("contradiction", {"text": "a", "contradiction": True})
        session.enter_forced_sitting()
        session.commit_confession({"blessed_fragments": [{"text": "check evidence", "reason": "supported"}], "slain_assumptions": []}, {"decision": "approve"})
        successor = session.rebirth()
        self.assertEqual(session.state, "reborn")
        self.assertEqual(successor.parent_session_id, session.session_id)
        with self.assertRaises(RuntimeError):
            successor.rebirth()

    def test_snapshot_is_writable(self) -> None:
        session = BardoSession()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "snapshot.json"
            snapshot = session.snapshot(path)
            self.assertTrue(path.exists())
            self.assertTrue(snapshot["snapshot_hash"])


if __name__ == "__main__":
    unittest.main()
