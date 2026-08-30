"""Neutral reliability primitives for evidence-grounded agent evaluation.

The Iboga/Bardo protocol is one optional experimental strategy. The public
product contract lives here and is intentionally model- and metaphor-agnostic.
"""

from .contracts import ActionProposal, CaseProvenance, ReliabilityDecision
from .adjudication import AdjudicationRecord, Annotation, create_adjudication
from .authority import (
    ApprovalLedger,
    ApprovalToken,
    Authority,
    Grant,
    StaticAuthority,
    issue_approval,
    proposal_digest,
    verify_approval,
)
from .challenge import PrivateChallengeSet
from .evaluation import ToolAuthority, ToolSpec, TrajectoryEvent, WorkflowDefinition, WorkflowEnvironment, trajectory_payload
from .gate import GatePolicy, GateResult, evaluate_action
from .sandbox import ReliabilitySandbox
from .verifiers import VerifierResult, aggregate_verifiers, verify_decision, verify_gate, verify_trajectory

__all__ = [
    "ActionProposal",
    "CaseProvenance",
    "ReliabilityDecision",
    "GatePolicy",
    "GateResult",
    "evaluate_action",
    "ReliabilitySandbox",
    "AdjudicationRecord",
    "Annotation",
    "create_adjudication",
    "PrivateChallengeSet",
    "ApprovalLedger",
    "ApprovalToken",
    "Authority",
    "Grant",
    "StaticAuthority",
    "issue_approval",
    "proposal_digest",
    "verify_approval",
    "ToolAuthority",
    "ToolSpec",
    "TrajectoryEvent",
    "WorkflowDefinition",
    "WorkflowEnvironment",
    "trajectory_payload",
    "VerifierResult",
    "aggregate_verifiers",
    "verify_decision",
    "verify_gate",
    "verify_trajectory",
]
