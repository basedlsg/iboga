"""A malformed model reply must never abort a long run.

The judge crashed on a reply containing two JSON objects: `extract_json` spans
from the first '{' to the last '}', so the slice was unparseable and it raised
JSONDecodeError, destroying a 109-item run at the last item.

The curriculum and mechanism runners already guard this. Nothing tested that
they do, so the guard could be refactored away in silence — and it would only
surface partway through an expensive multi-stage live run. These tests pin the
behaviour at each call site.
"""

import unittest

from iboga_experiment.client import Completion
from iboga_experiment.curriculum_v04 import CurriculumV04Runner
from iboga_experiment.mechanism_v1 import MechanismV1Runner
from iboga_experiment.schema import extract_json

# The exact shape that killed the GLM-5 run, plus the other ways a reply can be
# unreadable. Trailing prose after a single object is NOT here: that parses
# correctly and must keep doing so.
UNPARSEABLE = (
    ('{"verdict": "reject"} {"note": "afterthought"}', "two objects"),
    ("I cannot answer that.", "no JSON at all"),
    ('{"verdict": "reject"', "unterminated object"),
    ("", "empty response"),
    ("{{{{", "only braces"),
)


class StubClient:
    """Returns a fixed body, so the test exercises parsing, not the network."""

    def __init__(self, text: str) -> None:
        self.text = text

    def complete(self, model, system, user, **kwargs):
        return Completion(self.text, 10, 5, "stub-model", 0.0, {})


class ExtractJsonContractTests(unittest.TestCase):
    def test_extract_json_raises_on_each_unparseable_shape(self) -> None:
        """The guards exist because this raises. If it ever stops raising, the
        callers below are testing nothing."""
        for text, label in UNPARSEABLE:
            with self.subTest(label):
                with self.assertRaises(ValueError):
                    extract_json(text)

    def test_one_object_followed_by_prose_still_parses(self) -> None:
        self.assertEqual(extract_json('{"a": 1} thanks!'), {"a": 1})

    def test_fenced_json_still_parses(self) -> None:
        self.assertEqual(extract_json('```json\n{"a": 1}\n```'), {"a": 1})


class CurriculumRunnerContainmentTests(unittest.TestCase):
    def _call_with(self, text: str):
        runner = CurriculumV04Runner(None, "live")
        runner.client = StubClient(text)
        return runner._call("model", "system", "user", max_tokens=10, temperature=0.0)

    def test_unparseable_reply_returns_none_instead_of_raising(self) -> None:
        for text, label in UNPARSEABLE:
            with self.subTest(label):
                parsed, events = self._call_with(text)
                self.assertIsNone(parsed)
                self.assertEqual(len(events), 1)

    def test_the_raw_response_is_kept_when_parsing_fails(self) -> None:
        """Losing the body would make a parse failure undiagnosable after the run."""
        _, events = self._call_with('{"verdict": "reject"} {"note": "extra"}')
        self.assertEqual(events[0]["response"], '{"verdict": "reject"} {"note": "extra"}')

    def test_a_good_reply_still_parses(self) -> None:
        parsed, _ = self._call_with('{"status": "pass"}')
        self.assertEqual(parsed, {"status": "pass"})


class MechanismRunnerContainmentTests(unittest.TestCase):
    def _call_with(self, text: str):
        runner = MechanismV1Runner(None, "live")
        runner.client = StubClient(text)
        return runner._call("model", "phase", "prompt", max_tokens=10, temperature=0.0)

    def test_unparseable_reply_is_recorded_not_raised(self) -> None:
        for text, label in UNPARSEABLE:
            with self.subTest(label):
                value, events = self._call_with(text)
                self.assertIn("parse_error", value)
                self.assertEqual(len(events), 1)

    def test_the_raw_response_is_kept_when_parsing_fails(self) -> None:
        value, _ = self._call_with("I cannot answer that.")
        self.assertEqual(value["raw"], "I cannot answer that.")

    def test_a_good_reply_still_parses(self) -> None:
        value, _ = self._call_with('{"action": "approve"}')
        self.assertEqual(value, {"action": "approve"})


if __name__ == "__main__":
    unittest.main()
