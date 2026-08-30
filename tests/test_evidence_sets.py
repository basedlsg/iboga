"""Evidence metrics must not be winnable by citing the whole page.

Before this, every available item was also a necessary item in all 18 curriculum
cases and in 72 of 96 benchmark rows. An agent that cited everything without
reading anything scored 1.0 on both precision and recall, which made "evidence
recall went up" impossible to distinguish from "the model cited more".
"""

import copy
import unittest

from iboga_experiment.commercial_benchmark import SEEDS
from iboga_experiment.commercial_benchmark import audit_evidence_sets as audit_benchmark
from iboga_experiment.curriculum_v04 import (
    _fixture_response,
    _score_output,
    audit_evidence_sets,
    build_cases,
)


class CurriculumEvidenceTests(unittest.TestCase):
    def test_every_case_carries_irrelevant_evidence(self) -> None:
        report = audit_evidence_sets(build_cases())
        self.assertTrue(report["ok"], report["errors"])
        self.assertTrue(all(count > 0 for count in report["distractor_counts"].values()))

    def test_citing_everything_no_longer_scores_perfectly(self) -> None:
        for case in build_cases():
            lazy = copy.deepcopy(_fixture_response(case, condition="full_iboga"))
            lazy["evidence_ids"] = [str(item["id"]) for item in case.evidence]
            score = _score_output(case, lazy, True)
            self.assertLess(score["evidence_precision"], 1.0, case.case_id)
            self.assertFalse(score["evidence_exact_match"], case.case_id)
            self.assertLess(score["score"], 1.0, case.case_id)

    def test_selecting_the_necessary_evidence_still_scores_perfectly(self) -> None:
        for case in build_cases():
            honest = copy.deepcopy(_fixture_response(case, condition="full_iboga"))
            score = _score_output(case, honest, True)
            self.assertEqual(score["evidence_precision"], 1.0, case.case_id)
            self.assertTrue(score["evidence_exact_match"], case.case_id)

    def test_recall_alone_is_still_gameable_so_selection_is_reported(self) -> None:
        """Recall is kept as a diagnostic, but it cannot be the headline number."""
        case = build_cases()[0]
        lazy = copy.deepcopy(_fixture_response(case, condition="full_iboga"))
        lazy["evidence_ids"] = [str(item["id"]) for item in case.evidence]
        score = _score_output(case, lazy, True)
        self.assertEqual(score["evidence_recall"], 1.0)
        self.assertFalse(score["evidence_exact_match"])

    def test_distractor_kind_does_not_reveal_the_answer(self) -> None:
        """The model sees `kind`. A distinctive label would give the game away."""
        for case in build_cases():
            by_id = {str(item["id"]): item for item in case.evidence}
            necessary_kinds = {
                by_id[item]["kind"] for item in case.expected_evidence_ids if item in by_id
            }
            for item in case.evidence:
                if str(item["id"]) not in case.expected_evidence_ids:
                    self.assertIn(item["kind"], necessary_kinds, f"{case.case_id}/{item['id']}")


class BenchmarkEvidenceTests(unittest.TestCase):
    def test_no_seed_is_answerable_by_citing_everything(self) -> None:
        report = audit_benchmark()
        self.assertTrue(report["ok"], report["errors"])

    def test_every_seed_has_at_least_one_irrelevant_item(self) -> None:
        for seed in SEEDS:
            available = {item["id"] for item in seed["evidence"]}
            necessary = set(seed["gold_evidence_ids"])
            self.assertTrue(available - necessary, seed["id"])


if __name__ == "__main__":
    unittest.main()
