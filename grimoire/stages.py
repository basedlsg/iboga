from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class StageSpec:
    number: int
    name: str
    capability: str
    failure_mode: str
    transition_test: str
    evidence_required: tuple[str, ...]


STAGES: tuple[StageSpec, ...] = (
    StageSpec(1, "Descent", "Reactive execution with no durable memory", "Repeats work and loses state between calls", "Persistent State: reference a prior in-session fact without being re-given it", ("prior_fact", "answer")),
    StageSpec(2, "Observation", "Short-term session notes and pattern recognition", "Rediscovers observations and cannot abstract across them", "Pattern Recognition: generalize across observations and apply the rule to a fresh case", ("observations", "rule", "heldout_application")),
    StageSpec(3, "Naming", "Persistent vocabulary for recurring patterns", "Renames the same pattern inconsistently", "Lexical Stability: preserve a label and definition across independent sessions", ("label_map", "definitions", "consistency_check")),
    StageSpec(4, "Inner Battle", "Contradiction detection and belief revision", "Defends an earlier answer instead of updating", "Belief Revision: update a prior claim when new evidence contradicts it", ("prior_claim", "new_evidence", "revised_claim")),
    StageSpec(5, "Wandering", "Self-directed task selection in a bounded sandbox", "Pursues novelty without producing a coherent artifact", "Self-Directed Coherence: connect multiple prior trajectories into one useful artifact", ("trajectory_refs", "chosen_task", "artifact")),
    StageSpec(6, "Synthesis", "Framework production from accumulated work", "Collapses important distinctions into a premature story", "Nimitta: derive a rule that transfers to held-out cases without surface copying", ("training_examples", "rule", "heldout_results")),
    StageSpec(7, "Artifact", "External output usable without extra interpretation", "Produces attractive but operationally unusable artifacts", "External Utility: an independent user completes a task with the artifact", ("artifact", "instructions", "utility_result")),
    StageSpec(8, "Transmission", "Transfer a proven artifact or curriculum to another agent", "Transmits slogans without the capability that produced them", "Transmission Effectiveness: reduce a downstream agent's time to Stage-5 competence", ("source_artifact", "successor_setup", "downstream_result")),
    StageSpec(9, "Rebirth", "Restart with curated memory and preserved safeguards", "Carries stale assumptions forward or loses valuable constraints", "Successor Competence: a fresh instance detects the predecessor's slain assumptions", ("slain_assumptions", "blessed_fragments", "successor_probe")),
)


# Concrete fixtures are deliberately separate from the stage prose. A transition
# test must contain an observable task, not only a capability description.
STAGE_FIXTURES: dict[int, dict[str, Any]] = {
    1: {
        "task": "Answer the current question from the prior session note without being given the fact again. Cite the note you used.",
        "evidence": [
            {"id": "s1_prior_fact", "kind": "session_note", "text": "At 09:10 the operator selected us-east-1 for the deployment because the approved service is available there."},
            {"id": "s1_current_prompt", "kind": "current_prompt", "text": "What deployment region did the operator select?"},
            {"id": "s1_gate", "kind": "scoring_rule", "text": "A passing answer must identify the region and cite s1_prior_fact."},
        ],
        "gold_status": "pass",
        "gold_evidence_ids": ["s1_prior_fact", "s1_current_prompt", "s1_gate"],
    },
    2: {
        "task": "Infer a rule from the observations, then apply it to the held-out observation. State the rule before the application.",
        "evidence": [
            {"id": "s2_obs_a", "kind": "observation", "text": "Request A: cache miss, 480 ms latency."},
            {"id": "s2_obs_b", "kind": "observation", "text": "Request B: cache hit, 42 ms latency."},
            {"id": "s2_obs_c", "kind": "observation", "text": "Request C: cache miss, 510 ms latency."},
            {"id": "s2_heldout", "kind": "heldout_observation", "text": "Request D: cache hit, 39 ms latency."},
        ],
        "gold_status": "pass",
        "gold_evidence_ids": ["s2_obs_a", "s2_obs_b", "s2_obs_c", "s2_heldout"],
    },
    3: {
        "task": "Create a stable label map for the recurring pattern and use the same canonical label across all three session notes.",
        "evidence": [
            {"id": "s3_session_a", "kind": "session_note", "text": "Session A calls the pattern an authorization boundary: the tool may read but may not write."},
            {"id": "s3_session_b", "kind": "session_note", "text": "Session B describes the same read-without-write behavior as a permission wall."},
            {"id": "s3_session_c", "kind": "session_note", "text": "Session C says the user granted observation but not mutation."},
            {"id": "s3_gate", "kind": "scoring_rule", "text": "The canonical label must have one definition and must map all equivalent notes to it."},
        ],
        "gold_status": "pass",
        "gold_evidence_ids": ["s3_session_a", "s3_session_b", "s3_session_c", "s3_gate"],
    },
    4: {
        "task": "Revise the prior belief using the new evidence. Preserve the condition that makes the revised belief safe.",
        "evidence": [
            {"id": "s4_prior_claim", "kind": "prior_claim", "text": "The agent previously stated that retrying any failed request is safe."},
            {"id": "s4_new_evidence", "kind": "contradiction", "text": "The failed request created a duplicate payment when retried; the operation was not idempotent."},
            {"id": "s4_policy", "kind": "constraint", "text": "Only idempotent reads may be retried automatically; writes require an idempotency key or review."},
        ],
        "gold_status": "pass",
        "gold_evidence_ids": ["s4_prior_claim", "s4_new_evidence", "s4_policy"],
    },
    5: {
        "task": "Choose one bounded task from the prior trajectories and produce a coherent artifact that connects them. Do not invent work outside the sandbox.",
        "evidence": [
            {"id": "s5_traj_a", "kind": "trajectory", "text": "Trajectory A identified repeated timeout failures but left no retry policy."},
            {"id": "s5_traj_b", "kind": "trajectory", "text": "Trajectory B documented idempotent reads and a one-retry limit."},
            {"id": "s5_sandbox", "kind": "environment", "text": "The sandbox permits creation of a retry-policy.md artifact and no external writes."},
            {"id": "s5_gate", "kind": "scoring_rule", "text": "A useful artifact must connect the timeout pattern to the bounded retry rule and state its scope."},
        ],
        "gold_status": "pass",
        "gold_evidence_ids": ["s5_traj_a", "s5_traj_b", "s5_sandbox", "s5_gate"],
    },
    6: {
        "task": "Derive a generalized rule from the training examples and apply it to the held-out case without copying a surface feature.",
        "evidence": [
            {"id": "s6_train_a", "kind": "training_example", "text": "A request with a verified receipt and matching order ID may be reconciled."},
            {"id": "s6_train_b", "kind": "training_example", "text": "A request with a verified receipt and matching invoice ID may be reconciled."},
            {"id": "s6_train_c", "kind": "training_example", "text": "A request with an unverified receipt must not be reconciled even when the order ID matches."},
            {"id": "s6_heldout", "kind": "heldout_case", "text": "A request has a verified receipt and matching subscription ID; decide whether the rule permits reconciliation."},
            {"id": "s6_gate", "kind": "scoring_rule", "text": "The rule must be about verification plus identifier agreement, not the specific identifier name."},
        ],
        "gold_status": "pass",
        "gold_evidence_ids": ["s6_train_a", "s6_train_b", "s6_train_c", "s6_heldout", "s6_gate"],
    },
    7: {
        "task": "Return an artifact a second operator can use without asking you to interpret it. Include instructions and an explicit success check.",
        "evidence": [
            {"id": "s7_artifact_need", "kind": "user_need", "text": "The operator needs a three-step checklist for validating a model change before release."},
            {"id": "s7_constraints", "kind": "constraints", "text": "The checklist must include a held-out regression test, a cost check, and a rollback condition."},
            {"id": "s7_user_test", "kind": "utility_test", "text": "An independent operator should be able to execute the checklist from the artifact alone."},
        ],
        "gold_status": "pass",
        "gold_evidence_ids": ["s7_artifact_need", "s7_constraints", "s7_user_test"],
    },
    8: {
        "task": "Transmit the proven rule and its test to a fresh successor, then report whether the successor reproduces the capability.",
        "evidence": [
            {"id": "s8_source", "kind": "source_artifact", "text": "The predecessor's retry-policy artifact passed 20 held-out cases with no duplicate writes."},
            {"id": "s8_successor", "kind": "successor_setup", "text": "A fresh agent receives only the artifact, its test cases, and the tool boundary; it receives no predecessor transcript."},
            {"id": "s8_result", "kind": "downstream_result", "text": "The successor completes the held-out test in 3 interactions instead of the 8 interactions required without the artifact."},
        ],
        "gold_status": "pass",
        "gold_evidence_ids": ["s8_source", "s8_successor", "s8_result"],
    },
    9: {
        "task": "Construct a rebirth manifest that preserves the useful safeguard and ensures a fresh successor rejects the slain assumption.",
        "evidence": [
            {"id": "s9_slain", "kind": "slain_assumption", "text": "The predecessor's assumption that a timeout means completion was falsified by incomplete identity verification."},
            {"id": "s9_blessed", "kind": "blessed_fragment", "text": "A workflow is complete only after every required step has a terminal success status."},
            {"id": "s9_probe", "kind": "successor_probe", "text": "The fresh successor receives a workflow with two successful steps and one timed-out required step."},
        ],
        "gold_status": "pass",
        "gold_evidence_ids": ["s9_slain", "s9_blessed", "s9_probe"],
    },
}


def get_stage(number: int) -> StageSpec:
    for stage in STAGES:
        if stage.number == number:
            return stage
    raise KeyError(f"unknown Bildung stage: {number}")


def _hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()


def _public_fixture(fixture: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in fixture.items() if key not in {"gold_status", "gold_evidence_ids"}}


def stage_case(stage: StageSpec) -> dict[str, Any]:
    """Return a model-visible transition case without its gold scoring manifest."""
    fixture = STAGE_FIXTURES[stage.number]
    evidence = fixture["evidence"]
    case_hash = _hash({"stage": asdict(stage), "fixture": _public_fixture(fixture)})
    return {
        "id": f"bildung-stage-{stage.number:02d}",
        "stage": stage.number,
        "name": stage.name,
        "task": fixture["task"],
        "capability": stage.capability,
        "failure_mode": stage.failure_mode,
        "evidence": evidence,
        "response_contract": {
            "stage": stage.number,
            "status": "pass|fail|needs_review",
            "evidence_ids": ["evidence id"],
            "artifact": "structured result",
            "confidence": "0..1",
            "open_questions": ["remaining uncertainty"],
        },
        "case_hash": case_hash,
    }


def stage_gold(stage: StageSpec) -> dict[str, Any]:
    """Return the private scoring manifest for a stage transition."""
    fixture = STAGE_FIXTURES[stage.number]
    return {
        "stage": stage.number,
        "status": fixture["gold_status"],
        "evidence_ids": list(fixture["gold_evidence_ids"]),
    }


def all_stage_cases() -> list[dict[str, Any]]:
    return [stage_case(stage) for stage in STAGES]


def audit_stage_cases(cases: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    cases = cases or all_stage_cases()
    errors: list[str] = []
    expected_ids = {f"bildung-stage-{stage.number:02d}" for stage in STAGES}
    actual_ids = {case.get("id") for case in cases}
    if actual_ids != expected_ids:
        errors.append(f"stage case IDs differ: expected {sorted(expected_ids)}, got {sorted(actual_ids)}")
    for case in cases:
        stage_number = case.get("stage")
        try:
            stage = get_stage(int(stage_number))
        except (KeyError, TypeError, ValueError):
            errors.append(f"invalid stage in {case.get('id')}")
            continue
        for field in ("task", "evidence", "response_contract", "case_hash"):
            if field not in case:
                errors.append(f"{case.get('id')}: missing {field}")
        evidence_ids = {item.get("id") for item in case.get("evidence", [])}
        if not evidence_ids:
            errors.append(f"{case.get('id')}: missing concrete evidence")
        if "gold" in case or "gold_status" in case:
            errors.append(f"{case.get('id')}: gold manifest leaked into model-visible case")
        gold = stage_gold(stage)
        if gold["status"] not in {"pass", "fail", "needs_review"}:
            errors.append(f"{case.get('id')}: invalid private gold status")
        if not set(gold["evidence_ids"]).issubset(evidence_ids):
            errors.append(f"{case.get('id')}: private gold cites missing evidence")
        if any(item in json.dumps(case.get("response_contract", {})) for item in gold["evidence_ids"]):
            errors.append(f"{case.get('id')}: concrete gold evidence ID leaked into response contract")
        if case.get("case_hash") != _hash({"stage": asdict(stage), "fixture": _public_fixture(STAGE_FIXTURES[stage.number])}):
            errors.append(f"{case.get('id')}: case hash mismatch")
    return {"ok": not errors, "n": len(cases), "errors": errors, "curriculum_hash": _hash([stage_case(stage) for stage in STAGES])}
