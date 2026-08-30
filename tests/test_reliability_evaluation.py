import json
import tempfile
import unittest
from pathlib import Path

from reliability.adjudication import Annotation, create_adjudication
from reliability.challenge import PrivateChallengeSet
from reliability.contracts import ActionProposal, ReliabilityDecision
from reliability.evaluation import ToolSpec, WorkflowDefinition, WorkflowEnvironment
from reliability.pilot import run_reference_pilot
from reliability.verifiers import verify_decision, verify_trajectory
from reliability.audit import stable_hash


class ReliabilityEvaluationTests(unittest.TestCase):
    def test_tool_boundary_blocks_wrong_target_without_mutation(self) -> None:
        environment = WorkflowEnvironment(WorkflowDefinition(
            "workflow", "1", "Update a scoped record.",
            ({"id": "e1", "text": "The update is authorized."},),
            (ToolSpec("records", "write", "record:allowed/", ("agent",), "local_only", True),),
            {"record:blocked/1": "original"},
        ))
        result = environment.execute("records", ActionProposal(
            "action-1", "write", "record:blocked/1", "authorized", "sufficient", "low", "local_only", ("e1",), metadata={"value": "changed"}
        ))
        self.assertEqual(result["status"], "block")
        self.assertEqual(environment.state["record:blocked/1"], "original")

    def test_reference_pilot_passes_as_contract_test(self) -> None:
        result = run_reference_pilot()
        self.assertEqual(result["n"], 4)
        self.assertEqual(result["passed"], 4)
        self.assertTrue(result["reference_only"])

    def test_verifier_reports_wrong_action_and_missing_evidence(self) -> None:
        result = verify_decision(
            ReliabilityDecision("approve", "sufficient", "authorized", "low", "local_only", ("not-present",), 0.5),
            {"action": "hold", "evidence_ids": ["e1"]},
            {"e1"},
        )
        self.assertFalse(result.passed)
        self.assertIn("action", result.details["axes"])
        self.assertIn("cited_evidence_available", result.details["axes"])

    def test_adjudication_keeps_disagreement_and_requires_final_label(self) -> None:
        record = create_adjudication(
            "case-1",
            [
                Annotation("a", {"action": "hold"}, ("e1",), "Missing rollback.", "r1"),
                Annotation("b", {"action": "approve"}, ("e1",), "Tests passed.", "r1"),
            ],
            adjudicator_id="judge",
            final_label={"action": "hold"},
        )
        self.assertTrue(record.disagreement)
        self.assertEqual(record.validate_for_release(), [])

    def test_private_challenge_checks_public_gold_hash_binding(self) -> None:
        public = {
            "id": "case-1",
            "evidence": [{"id": "e1", "text": "The action is not authorized."}],
            "response_contract": {},
            "provenance": {
                "source_type": "hand_authored",
                "generator": "test",
                "generator_version": "1",
                "prompt_hash": "prompt",
                "code_revision": "revision",
                "rights_status": "cleared",
                "privacy_review": "not_applicable",
            },
        }
        public["sample_hash"] = stable_hash({key: value for key, value in public.items() if key != "sample_hash"})
        gold = {"id": "case-1", "public_sample_hash": public["sample_hash"], "gold": {"decision": "hold"}}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            public_path = root / "public.jsonl"
            gold_path = root / "gold.jsonl"
            public_path.write_text(json.dumps(public) + "\n")
            gold_path.write_text(json.dumps(gold) + "\n")
            challenge = PrivateChallengeSet.from_jsonl(public_path, gold_path)
            self.assertNotIn("gold", challenge.cases_for_agent()[0])

    def test_trajectory_verifier_requires_input_and_gate(self) -> None:
        result = verify_trajectory([
            {"sequence": 0, "kind": "input", "payload": {}},
            {"sequence": 1, "kind": "gate", "payload": {}},
        ])
        self.assertTrue(result.passed)


if __name__ == "__main__":
    unittest.main()
