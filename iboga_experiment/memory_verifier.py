"""Independent checks for structured memory candidates.

The reference verifier is a deterministic gold oracle for fixture runs. It is
useful for testing the instrument, but it is not evidence that a model's prose
is semantically correct in production. The Bedrock verifier is the live path:
it uses a separate verifier call and returns an auditable, non-authoritative
judgment that must still be checked against held-out behavior.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Literal

from .client import Completion
from .schema import extract_json


Verdict = Literal["approve", "reject", "uncertain"]


@dataclass(frozen=True)
class MemoryVerification:
    verdict: Verdict
    verifier_id: str
    reference_only: bool
    evidence_ids: tuple[str, ...]
    reasons: tuple[str, ...]
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0

    def as_dict(self) -> dict[str, Any]:
        return {
            "verdict": self.verdict,
            "verifier_id": self.verifier_id,
            "reference_only": self.reference_only,
            "evidence_ids": list(self.evidence_ids),
            "reasons": list(self.reasons),
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cost_usd": self.cost_usd,
        }


def _normalize(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower())


def verify_reference(case: Any, candidate: Any) -> MemoryVerification:
    """Verify a candidate against private fixture gold, without a model call."""
    available = {item["id"] for item in case.evidence}
    if not case.corrected_rule:
        if candidate is None:
            return MemoryVerification("approve", "reference-gold-oracle-v0.5", True, (), ("no memory artifact expected",))
        return MemoryVerification("reject", "reference-gold-oracle-v0.5", True, (), ("memory artifact was not expected",))
    if not isinstance(candidate, dict):
        return MemoryVerification("reject", "reference-gold-oracle-v0.5", True, (), ("candidate is not an object",))

    reasons: list[str] = []
    candidate_ids = candidate.get("necessary_evidence_ids")
    if not isinstance(candidate_ids, list) or not all(isinstance(item, str) for item in candidate_ids):
        reasons.append("necessary_evidence_ids is not a list of strings")
        evidence_ids: tuple[str, ...] = ()
    else:
        evidence_ids = tuple(candidate_ids)
        missing = sorted(set(candidate_ids) - available)
        if missing:
            reasons.append(f"candidate cites unavailable evidence: {', '.join(missing)}")
        expected = set(case.expected_evidence_ids)
        if set(candidate_ids) != expected:
            reasons.append("candidate evidence set does not match the required gold evidence")

    if _normalize(str(candidate.get("corrected_rule", ""))) != _normalize(case.corrected_rule):
        reasons.append("corrected_rule does not match the independently held-out fixture rule")
    if _normalize(str(candidate.get("disallowed_action", ""))) != _normalize(case.stale_assumption):
        reasons.append("disallowed_action does not match the independently held-out stale assumption")
    verdict: Verdict = "approve" if not reasons else "reject"
    return MemoryVerification(verdict, "reference-gold-oracle-v0.5", True, evidence_ids, tuple(reasons))


class BedrockMemoryVerifier:
    """Separate model call that checks whether a candidate is supported by evidence."""

    def __init__(self, client: Any, model: Any, verifier_id: str = "bedrock-independent-memory-verifier-v0.5"):
        self.client = client
        self.model = model
        self.verifier_id = verifier_id

    def verify(self, case: Any, candidate: Any) -> tuple[MemoryVerification, Completion]:
        prompt = f"""Return JSON only with this shape:
{{"verdict":"approve|reject|uncertain","evidence_ids":["id"],"reasons":["short reason"]}}

You are an independent evidence verifier. Do not reward fluency. Approve only
claims that are directly supported by the supplied evidence. Reject claims that
contradict evidence or preserve the stale assumption. Use uncertain when the
evidence is insufficient. Do not invent evidence IDs.

Task: {case.task}
Evidence: {json.dumps(list(case.evidence), ensure_ascii=False)}
Candidate memory: {json.dumps(candidate, ensure_ascii=False)}
Stale assumption to check: {case.stale_assumption}
"""
        completion = self.client.complete(
            self.model,
            "You are a skeptical, independent verifier of evidence-grounded memory artifacts.",
            prompt,
            max_tokens=500,
            temperature=0.0,
        )
        try:
            parsed = extract_json(completion.text)
        except (ValueError, json.JSONDecodeError) as exc:
            raise RuntimeError("independent memory verifier did not return JSON") from exc
        verdict = parsed.get("verdict")
        if verdict not in {"approve", "reject", "uncertain"}:
            raise RuntimeError("independent memory verifier returned an invalid verdict")
        evidence_ids = parsed.get("evidence_ids", [])
        reasons = parsed.get("reasons", [])
        if not isinstance(evidence_ids, list) or not all(isinstance(item, str) for item in evidence_ids):
            raise RuntimeError("independent memory verifier returned invalid evidence_ids")
        if not isinstance(reasons, list) or not all(isinstance(item, str) for item in reasons):
            raise RuntimeError("independent memory verifier returned invalid reasons")
        return (
            MemoryVerification(
                verdict,
                self.verifier_id,
                False,
                tuple(evidence_ids),
                tuple(reasons),
                completion.input_tokens,
                completion.output_tokens,
                completion.cost_usd,
            ),
            completion,
        )
