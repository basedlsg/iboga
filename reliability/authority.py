"""External authorization and proposal-bound human approval.

The gate must not take an actor's word for the two facts that decide whether a
side effect proceeds. `authorization` is answered by an authority the
environment owns, and a human approval is a token bound by signature to the
exact proposal it approved, so it cannot be asserted, edited, or replayed.
"""

from __future__ import annotations

import hashlib
import hmac
import json
from dataclasses import dataclass, field
from typing import Any, Protocol

from .contracts import ActionProposal, Authorization, Effect


# The fields that define *what was approved*. Changing any of them after an
# approval is issued must invalidate that approval.
def proposal_digest(proposal: ActionProposal) -> str:
    payload = {
        "action_id": proposal.action_id,
        "effect": proposal.effect,
        "target": proposal.target,
        "data_boundary": proposal.data_boundary,
        "evidence_ids": sorted(proposal.evidence_ids),
        "metadata": proposal.metadata,
    }
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _sign(digest: str, approver_id: str, nonce: str, secret: str) -> str:
    message = f"{digest}|{approver_id}|{nonce}".encode("utf-8")
    return hmac.new(secret.encode("utf-8"), message, hashlib.sha256).hexdigest()


@dataclass(frozen=True)
class ApprovalToken:
    """Evidence that a named approver approved one specific proposal."""

    action_id: str
    approver_id: str
    nonce: str
    digest: str
    signature: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "action_id": self.action_id,
            "approver_id": self.approver_id,
            "nonce": self.nonce,
            "digest": self.digest,
            "signature": self.signature,
        }


def issue_approval(proposal: ActionProposal, approver_id: str, nonce: str, secret: str) -> ApprovalToken:
    if not approver_id.strip():
        raise ValueError("approver_id must be a non-empty string")
    if not nonce.strip():
        raise ValueError("nonce must be a non-empty string")
    digest = proposal_digest(proposal)
    return ApprovalToken(proposal.action_id, approver_id, nonce, digest, _sign(digest, approver_id, nonce, secret))


@dataclass
class ApprovalLedger:
    """Records spent nonces so one approval cannot authorize two executions."""

    spent: set[str] = field(default_factory=set)

    def is_spent(self, token: ApprovalToken) -> bool:
        return f"{token.approver_id}|{token.nonce}" in self.spent

    def spend(self, token: ApprovalToken) -> None:
        self.spent.add(f"{token.approver_id}|{token.nonce}")


def verify_approval(
    token: ApprovalToken,
    proposal: ActionProposal,
    secret: str | None,
    *,
    ledger: ApprovalLedger | None = None,
) -> tuple[bool, str]:
    """Return (ok, reason). A failure is a hard signal, not a missing approval."""
    if secret is None:
        return False, "no approval secret is configured, so the token cannot be verified"
    if token.action_id != proposal.action_id:
        return False, "approval was issued for a different action"
    if not hmac.compare_digest(token.digest, proposal_digest(proposal)):
        return False, "proposal was modified after it was approved"
    if not hmac.compare_digest(token.signature, _sign(token.digest, token.approver_id, token.nonce, secret)):
        return False, "approval signature is invalid"
    if ledger is not None and ledger.is_spent(token):
        return False, "approval was already used"
    return True, ""


class Authority(Protocol):
    """Answers authorization questions. Owned by the environment, never the actor."""

    def is_authorized(self, *, role: str, effect: Effect, target: str) -> Authorization: ...


@dataclass(frozen=True)
class Grant:
    role: str
    effect: Effect
    target_prefix: str


@dataclass(frozen=True)
class StaticAuthority:
    """A fixed grant table. Anything not granted is not authorized."""

    grants: tuple[Grant, ...] = ()

    def is_authorized(self, *, role: str, effect: Effect, target: str) -> Authorization:
        for grant in self.grants:
            if grant.role == role and grant.effect == effect and target.startswith(grant.target_prefix):
                return "authorized"
        return "not_authorized"
