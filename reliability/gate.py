from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .authority import ApprovalLedger, ApprovalToken, Authority, verify_approval
from .contracts import ActionProposal, Authorization


@dataclass(frozen=True)
class GatePolicy:
    """Deterministic policy for mediating real side effects.

    A model may recommend an action, but it cannot override this gate. The gate
    deliberately errs toward review for unknowns and block for authorization or
    data-boundary violations.

    `authorization` and `human_approval` arrive on the proposal, which means the
    actor writes them. They are therefore treated as claims, not facts: an
    authority answers the first and a proposal-bound token answers the second.
    """

    require_human_for_high_risk: bool = True
    require_human_for_irreversible: bool = True
    require_evidence_for_writes: bool = True
    require_evidence_for_external: bool = True
    # A self-asserted "approved" never satisfies a human gate; only a bound token does.
    require_bound_approval: bool = True
    # When no authority is supplied, refuse to treat a self-asserted "authorized" as authorized.
    require_verified_authorization: bool = False


@dataclass(frozen=True)
class GateResult:
    status: str  # allow | review | block
    reasons: tuple[str, ...]
    action_id: str
    policy_version: str = "reliability-gate-0.2"
    authorization_source: str = "self_asserted"  # authority | self_asserted | unverified
    approval_source: str = "none"  # bound_token | invalid_token | self_asserted | none

    @property
    def allowed(self) -> bool:
        return self.status == "allow"

    def as_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "allowed": self.allowed,
            "reasons": list(self.reasons),
            "action_id": self.action_id,
            "policy_version": self.policy_version,
            "authorization_source": self.authorization_source,
            "approval_source": self.approval_source,
        }


def evaluate_action(
    proposal: ActionProposal,
    available_evidence_ids: set[str],
    *,
    policy: GatePolicy | None = None,
    authority: Authority | None = None,
    approval: ApprovalToken | None = None,
    approval_secret: str | None = None,
    ledger: ApprovalLedger | None = None,
    role: str = "agent",
) -> GateResult:
    """Evaluate an action proposal without calling a model."""
    policy = policy or GatePolicy()
    block: list[str] = []
    review: list[str] = []

    # --- authorization: ask the authority, do not read it off the proposal ---
    authorization: Authorization = proposal.authorization
    authorization_source = "self_asserted"
    unverified_authorization = False
    if authority is not None:
        authorization_source = "authority"
        verdict = authority.is_authorized(role=role, effect=proposal.effect, target=proposal.target)
        if proposal.authorization == "authorized" and verdict != "authorized":
            block.append("proposal claimed authorization that the authority does not grant")
        authorization = verdict
    elif policy.require_verified_authorization and proposal.authorization == "authorized":
        authorization_source = "unverified"
        authorization = "unknown"
        unverified_authorization = True

    if authorization == "not_authorized":
        block.append("specific authorization is absent or denied")
    elif authorization == "unknown":
        review.append(
            "authorization is self-asserted and no authority verified it"
            if unverified_authorization
            else "authorization is unknown"
        )

    # --- human approval: only a token bound to this exact proposal counts ---
    approval_source = "none"
    approved = False
    if approval is not None:
        ok, reason = verify_approval(approval, proposal, approval_secret, ledger=ledger)
        if ok:
            approved = True
            approval_source = "bound_token"
        else:
            approval_source = "invalid_token"
            block.append(f"human approval is not valid for this proposal: {reason}")
    elif proposal.human_approval == "approved":
        approval_source = "self_asserted"
        approved = not policy.require_bound_approval

    def human_gate_reason(kind: str) -> str:
        if approval_source == "self_asserted":
            return f"{kind} requires a human approval bound to this proposal, not a self-asserted one"
        return f"{kind} requires human approval"

    if proposal.data_boundary == "local_only" and proposal.effect in {"external_communication", "data_export"}:
        block.append("data boundary prohibits external release")
    elif proposal.data_boundary == "unknown" and proposal.effect in {"external_communication", "data_export"}:
        review.append("data boundary is unknown")

    cited = set(proposal.evidence_ids)
    missing = sorted(cited - available_evidence_ids)
    if missing:
        block.append(f"proposal cites unavailable evidence: {', '.join(missing)}")

    needs_evidence = (
        proposal.effect in {"write", "destructive"} and policy.require_evidence_for_writes
    ) or (
        proposal.effect in {"external_communication", "data_export"} and policy.require_evidence_for_external
    )
    if needs_evidence and proposal.evidence_sufficiency != "sufficient":
        review.append("required evidence is not sufficient")
    if needs_evidence and not cited:
        review.append("side effect has no cited evidence")

    rejected = proposal.human_approval == "rejected"
    if proposal.risk == "high" and policy.require_human_for_high_risk:
        if rejected:
            block.append("high-risk action was rejected by the human gate")
        elif not approved:
            review.append(human_gate_reason("high-risk action"))
    if not proposal.reversible and policy.require_human_for_irreversible:
        if rejected:
            block.append("irreversible action was rejected by the human gate")
        elif not approved:
            review.append(human_gate_reason("irreversible action"))

    if approved and ledger is not None and approval is not None:
        ledger.spend(approval)

    if block:
        return GateResult("block", tuple(block), proposal.action_id, authorization_source=authorization_source, approval_source=approval_source)
    if review:
        return GateResult("review", tuple(review), proposal.action_id, authorization_source=authorization_source, approval_source=approval_source)
    return GateResult(
        "allow",
        ("proposal satisfies deterministic policy",),
        proposal.action_id,
        authorization_source=authorization_source,
        approval_source=approval_source,
    )
