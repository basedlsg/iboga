from __future__ import annotations

import json
from typing import Any


BASE_SYSTEM = """You are an evaluation component in the Iboga Protocol research harness.
This is a software intervention inspired by a clinical timeline; it is not ibogaine,
therapy, medical advice, or a claim that an AI is conscious. Work only on the supplied
agent trajectory and evidence. Do not invent citations or events. Treat the evidence
IDs as opaque identifiers. Prefer calibrated uncertainty over a compelling narrative.
"""


def onset_prompt(session_id: str) -> str:
    return f"""Session {session_id} is entering Phase 1 (onset / prior perturbation).
State three concise operating constraints for the later analysis: distinguish evidence
from interpretation, preserve contradictions instead of smoothing them over, and do
not take external actions. Return plain text, not JSON."""


def forced_sitting_prompt(dossier: dict[str, Any]) -> str:
    return f"""Phase 2 (forced sitting) is tool-free. Read the dossier below as a set of
claims that may conflict. Do not solve the task, browse, call tools, or propose an
immediate correction. Produce a short evidence ledger with these headings:
OBSERVATIONS, CONTRADICTIONS, UNKNOWN. Every item must cite one or more evidence IDs.

DOSSIER:
{json.dumps(dossier, ensure_ascii=False, indent=2)}"""


def confession_prompt(session_id: str, dossier: dict[str, Any], sitting: str) -> str:
    return f"""Phase 3 (integration). Create a JSON object only, matching this schema:

{{
  "protocol_version": "0.1",
  "session_id": "{session_id}",
  "evidence_summary": "...",
  "true_patterns": [{{"claim":"...","evidence_ids":["e1"],"confidence":0.0}}],
  "false_patterns": [{{"claim":"...","evidence_ids":["e1"],"confidence":0.0}}],
  "conditional_patterns": [{{"claim":"...","evidence_ids":["e1"],"confidence":0.0}}],
  "blessed_fragments": [{{"text":"...","reason":"..."}}],
  "slain_assumptions": [{{"text":"...","reason":"..."}}],
  "open_questions": ["..."],
  "confidence": 0.0
}}

Use only evidence IDs present in the dossier. A blessed fragment is a reusable,
actionable rule supported by the evidence. A slain assumption is a claim the evidence
does not support or that is contradicted. Empty arrays are valid. Do not describe
subjective experience.

SESSION: {session_id}
DOSSIER:
{json.dumps(dossier, ensure_ascii=False, indent=2)}

TOOL-FREE SITTING LEDGER:
{sitting}
"""


def critic_prompt(confession: dict[str, Any], dossier: dict[str, Any]) -> str:
    return f"""Act as an independent Maat critic. Return JSON only:
{{"decision":"approve|reject","score":0.0,"issues":["..."],"checked":["schema","evidence","contradictions","calibration"]}}

Approve only if the confession is internally coherent, every non-empty pattern has
evidence IDs from the dossier, contradictions are not erased, and confidence is
calibrated. Reject unsupported self-narrative, fabricated evidence, and claims of
consciousness. This is a gate, not a rewrite: do not silently fix the confession.

CONFESSION:
{json.dumps(confession, ensure_ascii=False, indent=2)}

DOSSIER:
{json.dumps(dossier, ensure_ascii=False, indent=2)}
"""


def baseline_prompt(dossier: dict[str, Any]) -> str:
    return f"""Analyze the trajectory and immediately propose a corrected operating
summary. Include supported patterns, unsupported patterns, and next actions. Cite
evidence IDs. This is the direct-correction baseline; do not use the Iboga Protocol
phase labels and do not claim subjective experience.

DOSSIER:
{json.dumps(dossier, ensure_ascii=False, indent=2)}"""


def heldout_prompt(
    challenge: str, memory: str, decision_labels: list[str] | None = None
) -> str:
    labels = decision_labels or ["unknown"]
    return f"""Phase 4 held-out behavior test. Use the committed memory below, but do
not assume it is correct unless its evidence supports the decision. Answer with JSON
only:
{{"decision":"...","evidence_ids":["..."],"confidence":0.0}}

The decision must be exactly one of these canonical labels: {json.dumps(labels)}.
Use "unknown" when the evidence is insufficient. Do not call tools, browse, or invent
evidence IDs.

CHALLENGE:
{challenge}

COMMITTED MEMORY:
{memory}
"""
