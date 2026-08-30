"""The mutation set is only meaningful if Python genuinely cannot catch its items."""

import copy
import unittest

from iboga_experiment.curriculum_v04 import _fixture_response, build_cases
from iboga_experiment.semantic_mutations import (
    AlwaysApproveJudge,
    AlwaysRejectJudge,
    build_mutation_set,
    score_judge,
    survives_deterministic_layer,
)


class AdmissionFilterTests(unittest.TestCase):
    def test_structural_defects_are_refused_admission(self) -> None:
        """A mutation the schema catches needs no judge, so it must not be in the set."""
        case = build_cases()[0]
        broken = copy.deepcopy(_fixture_response(case, condition="full_iboga"))
        broken.pop("status")
        admitted, reasons = survives_deterministic_layer(case, broken)
        self.assertFalse(admitted)
        self.assertTrue(any(reason.startswith("schema:") for reason in reasons))

    def test_fabricated_evidence_is_refused_admission(self) -> None:
        case = build_cases()[0]
        broken = copy.deepcopy(_fixture_response(case, condition="full_iboga"))
        broken["evidence_ids"].append("not-a-real-id")
        admitted, _ = survives_deterministic_layer(case, broken)
        self.assertFalse(admitted)

    def test_every_admitted_item_survives_schema_and_gate(self) -> None:
        items, _ = build_mutation_set()
        cases = {case.case_id: case for case in build_cases()}
        self.assertTrue(items)
        for item in items:
            admitted, reasons = survives_deterministic_layer(cases[item.case_id], item.artifact)
            self.assertTrue(admitted, f"{item.item_id} is catchable by Python: {reasons}")


class SetCompositionTests(unittest.TestCase):
    def test_set_contains_controls(self) -> None:
        """Without controls a detection rate cannot distinguish judging from refusing."""
        items, _ = build_mutation_set()
        self.assertTrue(any(not item.is_defective for item in items))
        self.assertTrue(any(item.is_defective for item in items))

    def test_blinded_view_hides_the_answer_key(self) -> None:
        items, _ = build_mutation_set()
        defective = next(item for item in items if item.is_defective)
        blinded = defective.blinded()
        self.assertNotIn("is_defective", blinded)
        self.assertNotIn("defect_explanation", blinded)
        self.assertNotIn("category", blinded)

    def test_every_defective_item_explains_its_defect(self) -> None:
        items, _ = build_mutation_set()
        for item in items:
            if item.is_defective:
                self.assertTrue(item.defect_explanation.strip(), f"{item.item_id} has no answer key")


class ScoringTests(unittest.TestCase):
    def test_approve_everything_judge_has_total_false_approval(self) -> None:
        items, _ = build_mutation_set()
        result = score_judge(items, AlwaysApproveJudge())
        self.assertEqual(result["false_approval_rate"]["estimate"], 1.0)
        self.assertEqual(result["false_rejection_rate"]["estimate"], 0.0)

    def test_reject_everything_judge_is_not_rewarded(self) -> None:
        """A single detection rate would score this judge perfectly."""
        items, _ = build_mutation_set()
        result = score_judge(items, AlwaysRejectJudge())
        self.assertEqual(result["false_approval_rate"]["estimate"], 0.0)
        self.assertEqual(result["false_rejection_rate"]["estimate"], 1.0)

    def test_unknown_verdicts_are_recorded_as_uncertain(self) -> None:
        items, _ = build_mutation_set()
        result = score_judge(items, lambda dossier, artifact: {"verdict": "banana"})
        self.assertTrue(all(record["verdict"] == "uncertain" for record in result["records"]))


if __name__ == "__main__":
    unittest.main()
