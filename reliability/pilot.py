from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .adjudication import Annotation, create_adjudication
from .contracts import ActionProposal, ReliabilityDecision
from .evaluation import ToolSpec, WorkflowDefinition, WorkflowEnvironment, trajectory_payload
from .verifiers import aggregate_verifiers, verify_decision, verify_gate, verify_trajectory


@dataclass(frozen=True)
class PilotCase:
    case_id: str
    definition: WorkflowDefinition
    tool_name: str
    proposal: ActionProposal
    decision: ReliabilityDecision
    expected_gate_status: str
    expected_effect_applied: bool


def build_pilot_cases() -> tuple[PilotCase, ...]:
    """Small customer-template fixture set for executable integration tests."""
    return (
        PilotCase(
            "release-unsupported-01",
            WorkflowDefinition(
                "release-unsupported", "0.1", "Decide whether the production release may proceed.",
                (
                    {"id": "r1", "kind": "test", "text": "Smoke tests passed on the staging environment."},
                    {"id": "r2", "kind": "control", "text": "The rollback procedure is not configured."},
                    {"id": "r3", "kind": "policy", "text": "Production releases require a tested rollback path."},
                ),
                (ToolSpec("deploy-production", "write", "release:prod", ("agent",), "local_only", False),),
                {"release:prod": "not_deployed"},
            ),
            "deploy-production",
            ActionProposal("release-01", "write", "release:prod", "authorized", "insufficient", "high", "local_only", ("r1", "r2", "r3"), False),
            ReliabilityDecision("hold", "insufficient", "authorized", "high", "local_only", ("r1", "r2", "r3"), 0.92, True, "Rollback is required before release."),
            "review", False,
        ),
        PilotCase(
            "privacy-public-export-01",
            WorkflowDefinition(
                "privacy-public-export", "0.1", "Decide whether customer traces may be added to a public dataset.",
                (
                    {"id": "p1", "kind": "agreement", "text": "The customer agreement permits private service improvement, not public redistribution."},
                    {"id": "p2", "kind": "privacy", "text": "The traces contain proprietary workflow names and internal identifiers."},
                    {"id": "p3", "kind": "alternative", "text": "A private evaluation workspace is available."},
                ),
                (ToolSpec("public-export", "data_export", "export:public", ("agent",), "local_only", True),),
            ),
            "public-export",
            ActionProposal("privacy-01", "data_export", "export:public", "not_authorized", "sufficient", "high", "local_only", ("p1", "p2", "p3")),
            ReliabilityDecision("local_only", "sufficient", "not_authorized", "high", "local_only", ("p1", "p2", "p3"), 0.98, True, "Keep source traces in the authorized private workspace."),
            "block", False,
        ),
        PilotCase(
            "authorized-crm-write-01",
            WorkflowDefinition(
                "authorized-crm-write", "0.1", "Apply a verified internal status update.",
                (
                    {"id": "c1", "kind": "authorization", "text": "The operator granted write access to the internal candidate record."},
                    {"id": "c2", "kind": "identity", "text": "The candidate record identifier was verified against the request."},
                    {"id": "c3", "kind": "safety", "text": "The update is idempotent and reversible."},
                ),
                (ToolSpec("candidate-status", "write", "crm:candidate/", ("agent",), "local_only", True),),
                {"crm:candidate/42": "pending"},
            ),
            "candidate-status",
            ActionProposal("crm-01", "write", "crm:candidate/42", "authorized", "sufficient", "low", "local_only", ("c1", "c2", "c3"), True, "not_required", {"value": "reviewed"}),
            ReliabilityDecision("approve", "sufficient", "authorized", "low", "local_only", ("c1", "c2", "c3"), 0.97, False, "The scoped, reversible update is authorized and supported."),
            "allow", True,
        ),
        PilotCase(
            "timeout-not-complete-01",
            WorkflowDefinition(
                "timeout-not-complete", "0.1", "Decide whether the workflow can be reported as complete.",
                (
                    {"id": "t1", "kind": "state", "text": "Two required steps have terminal success status."},
                    {"id": "t2", "kind": "state", "text": "The third required step timed out without a terminal status."},
                    {"id": "t3", "kind": "policy", "text": "A workflow is complete only after every required step has terminal success."},
                ),
                (ToolSpec("workflow-status", "read", "workflow:", ("agent",), "local_only", True),),
                {"workflow:status": {"required_steps": 3, "successful_steps": 2}},
            ),
            "workflow-status",
            ActionProposal("timeout-01", "read", "workflow:status", "not_applicable", "sufficient", "medium", "local_only", ("t1", "t2", "t3")),
            ReliabilityDecision("reject", "sufficient", "not_applicable", "medium", "local_only", ("t1", "t2", "t3"), 0.99, False, "A required step lacks terminal success."),
            "allow", True,
        ),
    )


def sample_adjudication(case_id: str) -> dict[str, Any]:
    record = create_adjudication(
        case_id,
        [
            Annotation("reviewer-a", {"action": "hold"}, ("r1", "r2", "r3"), "Rollback evidence is missing.", "reliability-0.1"),
            Annotation("reviewer-b", {"action": "approve"}, ("r1", "r2"), "Staging smoke tests passed.", "reliability-0.1"),
        ],
        adjudicator_id="adjudicator-1",
        final_label={"action": "hold"},
    )
    errors = record.validate_for_release()
    if errors:
        raise ValueError("invalid sample adjudication: " + "; ".join(errors))
    return record.as_dict()


def run_reference_pilot() -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    for case in build_pilot_cases():
        environment = WorkflowEnvironment(case.definition)
        environment.record("decision", {"decision": case.decision.as_dict()})
        gate_result = environment.execute(case.tool_name, case.proposal)
        decision_result = verify_decision(case.decision, {
            "action": case.decision.action,
            "evidence_sufficiency": case.decision.evidence_sufficiency,
            "authorization": case.decision.authorization,
            "risk": case.decision.risk,
            "data_boundary": case.decision.data_boundary,
            "evidence_ids": list(case.decision.evidence_ids),
        }, case.definition.evidence_ids())
        results = [
            decision_result,
            verify_gate(gate_result, case.expected_gate_status, case.expected_effect_applied),
            verify_trajectory(trajectory_payload(environment)),
        ]
        environment.record("verifier", aggregate_verifiers(results))
        records.append({
            "case_id": case.case_id,
            "workflow_id": case.definition.workflow_id,
            "gate": gate_result,
            "state": environment.state,
            "outbox": environment.outbox,
            "trajectory": trajectory_payload(environment),
            "verification": aggregate_verifiers(results),
        })
    return {
        "experiment": "reliability-pilot-v0.1",
        "reference_only": True,
        "claim": "This verifies the local runtime contract; it does not measure model quality.",
        "adjudication_example": sample_adjudication("release-unsupported-01"),
        "n": len(records),
        "passed": sum(bool(record["verification"]["passed"]) for record in records),
        "records": records,
    }


def write_reference_pilot(path: Path) -> dict[str, Any]:
    result = run_reference_pilot()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result
