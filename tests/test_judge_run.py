"""The judge must never be handed the answer, and its failures must stay visible."""

import json
import unittest

from iboga_experiment.judge_run import (
    DryRunJudge,
    JUDGE_SYSTEM,
    judge_prompt,
    leak_check,
    ordered_items,
    run,
)
from iboga_experiment.semantic_mutations import build_mutation_set, score_judge


class BlindingTests(unittest.TestCase):
    def test_no_item_leaks_its_defect_into_the_prompt(self) -> None:
        self.assertEqual(leak_check(ordered_items()), [])

    def test_public_id_does_not_name_the_category(self) -> None:
        """`item_id` is `<case>__<category>`, which would hand over the answer."""
        items, _ = build_mutation_set()
        for item in items:
            if item.category != "control":
                self.assertNotIn(item.category, item.public_id)
                self.assertNotIn(item.category, json.dumps(item.blinded()))

    def test_blinded_payload_excludes_the_answer_key(self) -> None:
        items, _ = build_mutation_set()
        defective = next(item for item in items if item.is_defective)
        payload = json.dumps(defective.blinded())
        self.assertNotIn(defective.defect_explanation, payload)
        self.assertNotIn(defective.item_id, payload)

    def test_leak_check_catches_a_planted_leak(self) -> None:
        """The guard has to actually fire, not just return an empty list."""
        items, _ = build_mutation_set()
        leaky = next(item for item in items if item.is_defective)
        leaky.artifact["reviewer_note"] = f"this item is a {leaky.category} case"
        self.assertTrue(leak_check([leaky]))

    def test_prompt_does_not_reveal_the_base_rate(self) -> None:
        """Telling the judge most items are broken makes rejecting everything pay."""
        items = ordered_items()
        text = (JUDGE_SYSTEM + judge_prompt(items[0].dossier, items[0].artifact)).lower()
        for tell in ("most artifacts", "majority", "109", "91 ", "planted", "mutation", "deliberately"):
            self.assertNotIn(tell, text)


class OrderingTests(unittest.TestCase):
    def test_order_is_deterministic_for_a_seed(self) -> None:
        first = [item.item_id for item in ordered_items(11)]
        second = [item.item_id for item in ordered_items(11)]
        self.assertEqual(first, second)

    def test_items_are_not_grouped_by_category(self) -> None:
        categories = [item.category for item in ordered_items(7)]
        runs = sum(1 for a, b in zip(categories, categories[1:]) if a != b)
        self.assertGreater(runs, len(set(categories)))


class MalformedResponseTests(unittest.TestCase):
    """One unparseable reply must not abort a 109-item run."""

    def _judge_with_text(self, text):
        from dataclasses import dataclass

        from iboga_experiment.client import Completion
        from iboga_experiment.config import custom_model
        from iboga_experiment.judge_run import ModelJudge

        @dataclass
        class Stub:
            def complete(self, model, system, user, **kwargs):
                return Completion(text, 10, 5, "stub", 0.0, {})

        return ModelJudge(Stub(), custom_model("stub/model"))

    def test_two_json_objects_become_unavailable_not_a_crash(self) -> None:
        """The real GLM-5 failure: extract_json spans from the first '{' to the
        last '}', so a second object makes the slice unparseable and it raised
        JSONDecodeError('Extra data'), aborting the run at item 109."""
        judge = self._judge_with_text('{"verdict": "reject"} {"note": "afterthought"}')
        result = judge({"task": "t", "evidence": []}, {"memory_candidate": {}})
        self.assertEqual(result["verdict"], "unavailable")
        self.assertIn("unparseable", " ".join(result["reasons"]).lower())

    def test_trailing_prose_after_one_object_still_parses(self) -> None:
        """This case is fine and must keep working; only multi-object fails."""
        judge = self._judge_with_text('{"verdict": "reject"} and then some prose')
        result = judge({"task": "t", "evidence": []}, {"memory_candidate": {}})
        self.assertEqual(result["verdict"], "reject")

    def test_response_with_no_json_at_all_becomes_unavailable(self) -> None:
        judge = self._judge_with_text("I cannot answer that.")
        result = judge({"task": "t", "evidence": []}, {"memory_candidate": {}})
        self.assertEqual(result["verdict"], "unavailable")

    def test_a_valid_verdict_still_parses(self) -> None:
        judge = self._judge_with_text('{"verdict": "approve", "reasons": ["ok"]}')
        result = judge({"task": "t", "evidence": []}, {"memory_candidate": {}})
        self.assertEqual(result["verdict"], "approve")


class UnavailableTests(unittest.TestCase):
    def test_provider_failure_is_not_recoded_as_a_verdict(self) -> None:
        items, _ = build_mutation_set()
        result = score_judge(items[:5], DryRunJudge())
        self.assertEqual(result["n_unavailable"], 5)
        self.assertEqual(result["n_answered"], 0)
        self.assertTrue(all(record["verdict"] == "unavailable" for record in result["records"]))

    def test_unavailable_items_stay_in_the_record_but_out_of_the_rates(self) -> None:
        items, _ = build_mutation_set()
        result = score_judge(items[:5], DryRunJudge())
        self.assertEqual(result["n_items"], 5)
        self.assertIsNone(result["false_approval_rate"]["estimate"])
        self.assertEqual(result["availability_rate"], 0.0)

    def test_run_reports_cost_and_availability(self) -> None:
        items, _ = build_mutation_set()
        report = run(DryRunJudge(), items[:3], model_name="dry-run", seed=7)
        self.assertEqual(report["total_cost_usd"], 0)
        self.assertEqual(report["availability_rate"], 0.0)
        self.assertIn("judge_model", report)


if __name__ == "__main__":
    unittest.main()
