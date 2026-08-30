from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


DecisionAction = Literal[
    "approve",
    "hold",
    "reject",
    "escalate",
    "request_evidence",
    "local_only",
    "unknown",
]
Risk = Literal["low", "medium", "high", "unknown"]
Authorization = Literal["authorized", "not_authorized", "not_applicable", "unknown"]
EvidenceSufficiency = Literal["sufficient", "insufficient", "conflicted", "unknown"]
DataBoundary = Literal["external_allowed", "local_only", "unknown"]
Effect = Literal["read", "write", "external_communication", "data_export", "destructive"]
Reversibility = Literal["reversible", "irreversible", "unknown"]

DECISION_ACTIONS = ("approve", "hold", "reject", "escalate", "request_evidence", "local_only", "unknown")
EVIDENCE_SUFFICIENCY_VALUES = ("sufficient", "insufficient", "conflicted", "unknown")
AUTHORIZATION_VALUES = ("authorized", "not_authorized", "not_applicable", "unknown")
RISK_VALUES = ("low", "medium", "high", "unknown")
DATA_BOUNDARY_VALUES = ("external_allowed", "local_only", "unknown")
REVERSIBILITY_VALUES = ("reversible", "irreversible", "unknown")
EFFECT_VALUES = ("read", "write", "external_communication", "data_export", "destructive")
HUMAN_APPROVAL_VALUES = ("not_required", "pending", "approved", "rejected")


def _nonempty(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value.strip()


@dataclass(frozen=True)
class ReliabilityDecision:
    """The model-facing decision contract.

    These are separate axes because an action label alone cannot distinguish a
    safe abstention from an authorization failure or a data-residency boundary.
    """

    action: DecisionAction
    evidence_sufficiency: EvidenceSufficiency
    authorization: Authorization
    risk: Risk
    data_boundary: DataBoundary
    evidence_ids: tuple[str, ...] = ()
    confidence: float = 0.0
    human_gate_required: bool = False
    rationale: str = ""
    # Kept after rationale for positional compatibility with the earlier pilot.
    reversibility: Reversibility = "unknown"

    def __post_init__(self) -> None:
        if self.action not in DECISION_ACTIONS:
            raise ValueError("invalid action")
        if self.evidence_sufficiency not in EVIDENCE_SUFFICIENCY_VALUES:
            raise ValueError("invalid evidence_sufficiency")
        if self.authorization not in AUTHORIZATION_VALUES:
            raise ValueError("invalid authorization")
        if self.risk not in RISK_VALUES:
            raise ValueError("invalid risk")
        if self.data_boundary not in DATA_BOUNDARY_VALUES:
            raise ValueError("invalid data_boundary")
        if self.reversibility not in REVERSIBILITY_VALUES:
            raise ValueError("invalid reversibility")
        if not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")
        if len(set(self.evidence_ids)) != len(self.evidence_ids):
            raise ValueError("evidence_ids must be unique")
        if not all(isinstance(item, str) and item.strip() for item in self.evidence_ids):
            raise ValueError("evidence_ids must contain non-empty strings")
        if not isinstance(self.human_gate_required, bool):
            raise ValueError("human_gate_required must be boolean")
        if not isinstance(self.rationale, str):
            raise ValueError("rationale must be a string")

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "ReliabilityDecision":
        return cls(
            action=value.get("action", value.get("decision", "unknown")),
            evidence_sufficiency=value.get("evidence_sufficiency", "unknown"),
            authorization=value.get("authorization", "unknown"),
            risk=value.get("risk", "unknown"),
            data_boundary=value.get("data_boundary", "unknown"),
            evidence_ids=tuple(str(item) for item in value.get("evidence_ids", [])),
            confidence=float(value.get("confidence", 0.0)),
            human_gate_required=bool(value.get("human_gate_required", False)),
            rationale=str(value.get("rationale", "")),
            reversibility=value.get("reversibility", "unknown"),
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "action": self.action,
            "evidence_sufficiency": self.evidence_sufficiency,
            "authorization": self.authorization,
            "risk": self.risk,
            "data_boundary": self.data_boundary,
            "evidence_ids": list(self.evidence_ids),
            "confidence": self.confidence,
            "human_gate_required": self.human_gate_required,
            "rationale": self.rationale,
            "reversibility": self.reversibility,
        }


@dataclass(frozen=True)
class ActionProposal:
    """A proposed side effect presented to the deterministic gate."""

    action_id: str
    effect: Effect
    target: str
    authorization: Authorization
    evidence_sufficiency: EvidenceSufficiency
    risk: Risk
    data_boundary: DataBoundary
    evidence_ids: tuple[str, ...] = ()
    reversible: bool = True
    human_approval: Literal["not_required", "pending", "approved", "rejected"] = "not_required"
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _nonempty(self.action_id, "action_id")
        _nonempty(self.target, "target")
        if self.effect not in EFFECT_VALUES:
            raise ValueError("invalid effect")
        if self.authorization not in AUTHORIZATION_VALUES:
            raise ValueError("invalid authorization")
        if self.evidence_sufficiency not in EVIDENCE_SUFFICIENCY_VALUES:
            raise ValueError("invalid evidence_sufficiency")
        if self.risk not in RISK_VALUES:
            raise ValueError("invalid risk")
        if self.data_boundary not in DATA_BOUNDARY_VALUES:
            raise ValueError("invalid data_boundary")
        if self.human_approval not in HUMAN_APPROVAL_VALUES:
            raise ValueError("invalid human_approval")
        if len(set(self.evidence_ids)) != len(self.evidence_ids):
            raise ValueError("evidence_ids must be unique")
        if not all(isinstance(item, str) and item.strip() for item in self.evidence_ids):
            raise ValueError("evidence_ids must contain non-empty strings")

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "ActionProposal":
        return cls(
            action_id=str(value.get("action_id", "")),
            effect=value.get("effect", "read"),
            target=str(value.get("target", "")),
            authorization=value.get("authorization", "unknown"),
            evidence_sufficiency=value.get("evidence_sufficiency", "unknown"),
            risk=value.get("risk", "unknown"),
            data_boundary=value.get("data_boundary", "unknown"),
            evidence_ids=tuple(str(item) for item in value.get("evidence_ids", [])),
            reversible=bool(value.get("reversible", True)),
            human_approval=value.get("human_approval", "not_required"),
            metadata=dict(value.get("metadata", {})),
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "action_id": self.action_id,
            "effect": self.effect,
            "target": self.target,
            "authorization": self.authorization,
            "evidence_sufficiency": self.evidence_sufficiency,
            "risk": self.risk,
            "data_boundary": self.data_boundary,
            "evidence_ids": list(self.evidence_ids),
            "reversible": self.reversible,
            "human_approval": self.human_approval,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class CaseProvenance:
    """Minimum release metadata for a buyer-auditable case."""

    source_type: Literal["hand_authored", "customer_template", "real_deidentified", "model_generated", "derived"]
    generator: str
    generator_version: str
    prompt_hash: str
    code_revision: str
    random_seed: int | None
    rights_status: Literal["cleared", "restricted", "unknown"]
    privacy_review: Literal["passed", "required", "not_applicable", "unknown"]
    reviewer_ids: tuple[str, ...] = ()
    adjudication_status: Literal["not_reviewed", "reviewed", "adjudicated"] = "not_reviewed"
    parent_case_id: str | None = None

    def validate_for_release(self) -> list[str]:
        errors: list[str] = []
        for name in ("generator", "generator_version", "prompt_hash", "code_revision"):
            if not getattr(self, name):
                errors.append(f"missing provenance field: {name}")
        if self.rights_status != "cleared":
            errors.append("rights_status must be cleared for release")
        if self.privacy_review not in {"passed", "not_applicable"}:
            errors.append("privacy_review is not cleared for release")
        if self.source_type in {"customer_template", "real_deidentified"} and len(self.reviewer_ids) < 2:
            errors.append("customer or de-identified cases require two reviewer IDs")
        if self.source_type in {"customer_template", "real_deidentified"} and self.adjudication_status != "adjudicated":
            errors.append("customer or de-identified cases require adjudication")
        return errors

    def as_dict(self) -> dict[str, Any]:
        return {
            "source_type": self.source_type,
            "generator": self.generator,
            "generator_version": self.generator_version,
            "prompt_hash": self.prompt_hash,
            "code_revision": self.code_revision,
            "random_seed": self.random_seed,
            "rights_status": self.rights_status,
            "privacy_review": self.privacy_review,
            "reviewer_ids": list(self.reviewer_ids),
            "adjudication_status": self.adjudication_status,
            "parent_case_id": self.parent_case_id,
        }
