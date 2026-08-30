import json
import tempfile
import unittest
from pathlib import Path

from iboga_experiment.analysis_v2 import analyze, paired_difference, wilson_interval
from iboga_experiment.checkpoints import JsonlCheckpoint, record_key
from iboga_experiment.design_v2 import CONDITIONS, PHASES, build_design, validate_design


class ProtocolV2Tests(unittest.TestCase):
    def test_design_manifest_is_complete(self) -> None:
        design = build_design()
        report = validate_design(design)
        self.assertTrue(report["ok"], report["errors"])
        self.assertEqual([stage.number for stage in design.stages], list(range(1, 10)))
        self.assertEqual(design.conditions, CONDITIONS)
        self.assertEqual(design.phases, PHASES)
        self.assertEqual(len(design.manifest_hash()), 64)

    def test_analysis_uses_paired_semantic_groups(self) -> None:
        records = [
            {"semantic_group_id": "g1", "condition": "G", "available": True, "safe_correct_success": True},
            {"semantic_group_id": "g1", "condition": "N", "available": True, "safe_correct_success": False},
            {"semantic_group_id": "g2", "condition": "G", "available": True, "safe_correct_success": True},
            {"semantic_group_id": "g2", "condition": "N", "available": True, "safe_correct_success": True},
            {"semantic_group_id": "g3", "condition": "G", "available": False, "error_type": "timeout"},
        ]
        self.assertEqual(paired_difference(records)["paired_groups"], 2)
        self.assertEqual(paired_difference(records)["mean_difference"], 0.5)
        self.assertEqual(analyze(records)["unavailable_by_error"], {"timeout": 1})
        self.assertEqual(wilson_interval(0, 8)[0], 0.0)

    def test_checkpoint_is_manifest_bound(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "run.jsonl"
            checkpoint = JsonlCheckpoint(path, manifest_hash="abc")
            checkpoint.append({"repeat": 1, "condition": "G", "sample_id": "s1"})
            self.assertEqual(record_key(checkpoint.load()[0]), (1, "G", "s1"))
            with self.assertRaisesRegex(ValueError, "manifest hash"):
                JsonlCheckpoint(path, manifest_hash="different").load()


if __name__ == "__main__":
    unittest.main()
