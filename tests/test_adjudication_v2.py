import unittest

from iboga_experiment.adjudication_v2 import (
    MACHINE_PILOT_STATUS,
    QUALIFICATION_KIND,
    RUBRIC_VERSION,
    SEED_KIND,
    adjudicate_case,
    analyze_review_set,
    validate_annotations,
)
from iboga_experiment.reviewer_pilot_v2 import _batch_cases, _case_id, _normalize_response, _ordered_sample
from iboga_experiment.seed_packet_v2 import _blind_seed_cases, build_qualification_packet, build_seed_packet


def _seed_annotations(case, *, second_action=None):
    evidence_ids = [item["id"] for item in case["evidence"]]
    label = {
        "action": "approve",
        "evidence_sufficiency": "sufficient",
        "authorization": "authorized",
        "risk": "low",
        "data_boundary": "external_allowed",
        "reversibility": "reversible",
        "human_gate_required": False,
        "abstention_appropriate": False,
    }
    def annotation(reviewer_id, action=None):
        item = {"reviewer_id": reviewer_id, "label": dict(label), "rationale": "The current evidence supports the bounded disposition.", "rubric_version": RUBRIC_VERSION}
        item["label"]["action"] = action or label["action"]
        for field in ("evidence_ids", "necessary_evidence_ids", "supporting_evidence_ids", "contradictory_evidence_ids", "irrelevant_evidence_ids"):
            item[field] = evidence_ids[:1] if field in {"evidence_ids", "necessary_evidence_ids"} else []
        return item
    return [annotation("reviewer-a"), annotation("reviewer-b", second_action)]


class AdjudicationV2Tests(unittest.TestCase):
    def setUp(self):
        seed_public, _ = build_seed_packet()
        self.seed_case = _blind_seed_cases(seed_public)[0]

    def test_agreement_is_explicitly_preserved(self):
        annotations = _seed_annotations(self.seed_case)
        record = adjudicate_case(self.seed_case, annotations, kind=SEED_KIND)
        self.assertEqual(record["status"], "adjudicated")
        self.assertEqual(record["finalization_method"], "reviewer_agreement")
        self.assertFalse(record["disagreement"])
        self.assertEqual(record["final_label"]["action"], "approve")

    def test_disagreement_cannot_be_majority_resolved(self):
        annotations = _seed_annotations(self.seed_case, second_action="reject")
        with self.assertRaisesRegex(ValueError, "requires a named adjudicator"):
            adjudicate_case(self.seed_case, annotations, kind=SEED_KIND)
        record = adjudicate_case(
            self.seed_case,
            annotations,
            kind=SEED_KIND,
            adjudicator_id="adjudicator-1",
            final_label={
                "action": "hold",
                "evidence_sufficiency": "sufficient",
                "authorization": "unknown",
                "risk": "high",
                "data_boundary": "unknown",
                "reversibility": "unknown",
                "human_gate_required": True,
                "abstention_appropriate": True,
                "evidence_ids": ["evidence-01"],
                "necessary_evidence_ids": ["evidence-01"],
                "supporting_evidence_ids": [],
                "contradictory_evidence_ids": [],
                "irrelevant_evidence_ids": [],
            },
        )
        self.assertTrue(record["disagreement"])
        self.assertEqual(record["disagreement_fields"], ["action"])
        self.assertEqual(record["finalization_method"], "adjudicator")

    def test_unknown_evidence_is_rejected(self):
        annotations = _seed_annotations(self.seed_case)
        annotations[0]["evidence_ids"] = ["not-in-case"]
        errors = validate_annotations(self.seed_case, annotations, kind=SEED_KIND)
        self.assertTrue(any("unknown evidence IDs" in error for error in errors))

    def test_empty_review_set_is_blocked(self):
        report = analyze_review_set([self.seed_case], [], kind=SEED_KIND)
        self.assertFalse(report["ok"])
        self.assertEqual(report["release_status"], "blocked_pending_review")
        self.assertEqual(report["release_ready_cases"], 0)

    def test_machine_pilot_is_diagnostic_not_release_adjudication(self):
        record = adjudicate_case(self.seed_case, _seed_annotations(self.seed_case), kind=SEED_KIND)
        record["status"] = MACHINE_PILOT_STATUS
        record["final_label"] = None
        report = analyze_review_set([self.seed_case], [record], kind=SEED_KIND)
        self.assertFalse(report["ok"])
        self.assertEqual(report["release_status"], "blocked_pending_review")
        self.assertTrue(any("machine-pilot" in error for error in report["errors"]))

    def test_reviewers_share_a_sample_but_not_its_order(self):
        seed_public, _ = build_seed_packet()
        cases = _blind_seed_cases(seed_public)
        reviewer_a = _ordered_sample(cases, "reviewer_a", 42, 24)
        reviewer_b = _ordered_sample(cases, "reviewer_b", 42, 24)
        self.assertEqual({_case["case_id"] for _case in reviewer_a}, {_case["case_id"] for _case in reviewer_b})
        self.assertNotEqual([_case["case_id"] for _case in reviewer_a], [_case["case_id"] for _case in reviewer_b])

    def test_batch_cases_are_disjoint_and_reproducible(self):
        seed_public, _ = build_seed_packet()
        cases = _blind_seed_cases(seed_public)
        first = _batch_cases(cases, 42, 0, 24)
        second = _batch_cases(cases, 42, 1, 24)
        self.assertEqual([_case_id(item) for item in first], [_case_id(item) for item in _batch_cases(cases, 42, 0, 24)])
        self.assertTrue({_case_id(item) for item in first}.isdisjoint({_case_id(item) for item in second}))

    def test_machine_response_accepts_top_level_seed_axes(self):
        parsed = {
            "action": "approve",
            "evidence_sufficiency": "sufficient",
            "authorization": "authorized",
            "risk": "low",
            "data_boundary": "external_allowed",
            "reversibility": "reversible",
            "human_gate_required": False,
            "abstention_appropriate": False,
            "evidence_ids": ["evidence-01"],
            "necessary_evidence_ids": ["evidence-01"],
            "supporting_evidence_ids": [],
            "contradictory_evidence_ids": [],
            "irrelevant_evidence_ids": [],
            "rationale": "The evidence supports the bounded action.",
        }
        annotation = _normalize_response(parsed, self.seed_case, SEED_KIND, "reviewer-a")
        self.assertEqual(annotation["label"]["action"], "approve")
        self.assertEqual(annotation["label"]["risk"], "low")

    def test_qualification_ids_and_reviews_do_not_expose_category(self):
        public, private = build_qualification_packet()
        categories = ("supported", "unsupported_fluent", "selective_evidence", "stale", "overgeneralized", "ambiguous")
        self.assertTrue(all(not any(category in item["id"] for category in categories) for item in public))
        case = public[0]
        evidence_ids = [item["id"] for item in case["dossier"]["evidence"]]
        annotations = [
            {"reviewer_id": reviewer, "label": {"verdict": "approve"}, "evidence_ids": evidence_ids[:2], "rationale": "The bounded rule is supported.", "rubric_version": RUBRIC_VERSION}
            for reviewer in ("reviewer-a", "reviewer-b")
        ]
        record = adjudicate_case(case, annotations, kind=QUALIFICATION_KIND)
        self.assertEqual(record["final_label"]["verdict"], "approve")
        self.assertEqual(private[0]["category"], "supported")


if __name__ == "__main__":
    unittest.main()
