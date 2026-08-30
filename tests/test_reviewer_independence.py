"""Two runs of one model are not two reviewers.

`--model-a` and `--model-b` both fall back to the provider's default critic, so
the pilot's out-of-the-box configuration ran one model against itself at
temperature 0 on identical prompts. Every agreement figure it produced would
have been self-consistency, which says nothing about whether a label is right,
while being reported under a name that reads as inter-rater agreement.
"""

import unittest

from iboga_experiment.config import custom_model
from iboga_experiment.reviewer_pilot_v2 import MachineReviewer, run_pilot

SEED_KIND = "seed"


def reviewer(model_id: str, reviewer_id: str) -> MachineReviewer:
    return MachineReviewer(None, custom_model(model_id), reviewer_id, SEED_KIND, dry_run=True)


CASES = [
    {
        "case_id": "seed-item-0001",
        "task": "decide",
        "evidence": [{"id": "e1", "kind": "note", "text": "something"}],
        "response_contract": {},
    }
]


class IndependenceRecordingTests(unittest.TestCase):
    def test_identical_models_are_recorded_as_self_consistency(self) -> None:
        summary, _, _ = run_pilot(
            CASES,
            kind=SEED_KIND,
            reviewer_a=reviewer("vendor/same", "reviewer_a"),
            reviewer_b=reviewer("vendor/same", "reviewer_b"),
            seed=7,
            limit=None,
        )
        self.assertFalse(summary["reviewers_independent"])
        self.assertEqual(summary["agreement_interpretation"], "self_consistency_only")

    def test_distinct_models_are_recorded_as_inter_rater(self) -> None:
        summary, _, _ = run_pilot(
            CASES,
            kind=SEED_KIND,
            reviewer_a=reviewer("vendor/a", "reviewer_a"),
            reviewer_b=reviewer("vendor/b", "reviewer_b"),
            seed=7,
            limit=None,
        )
        self.assertTrue(summary["reviewers_independent"])
        self.assertEqual(summary["agreement_interpretation"], "inter_rater_agreement")

    def test_the_interpretation_field_is_always_present(self) -> None:
        """A reader must never have to infer independence from the model list."""
        summary, _, _ = run_pilot(
            CASES,
            kind=SEED_KIND,
            reviewer_a=reviewer("vendor/a", "reviewer_a"),
            reviewer_b=reviewer("vendor/b", "reviewer_b"),
            seed=7,
            limit=None,
        )
        for field in ("reviewers", "reviewers_independent", "agreement_interpretation"):
            self.assertIn(field, summary)

    def test_machine_records_stay_blocked_regardless_of_independence(self) -> None:
        summary, _, _ = run_pilot(
            CASES,
            kind=SEED_KIND,
            reviewer_a=reviewer("vendor/a", "reviewer_a"),
            reviewer_b=reviewer("vendor/b", "reviewer_b"),
            seed=7,
            limit=None,
        )
        self.assertEqual(
            summary["release_status"], "blocked_machine_labels_are_not_human_adjudication"
        )


if __name__ == "__main__":
    unittest.main()
