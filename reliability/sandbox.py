from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .contracts import ActionProposal
from .gate import GatePolicy, GateResult, evaluate_action


@dataclass
class ReliabilitySandbox:
    """Small executable environment proving the gate mediates side effects.

    This is intentionally not a production connector. It is a deterministic test
    environment for integrating the same action-gate contract with tools, state,
    and observable side effects before adding customer adapters.
    """

    state: dict[str, Any] = field(default_factory=dict)
    outbox: list[dict[str, Any]] = field(default_factory=list)
    policy: GatePolicy = field(default_factory=GatePolicy)

    def execute(self, proposal: ActionProposal, evidence_ids: set[str]) -> dict[str, Any]:
        gate: GateResult = evaluate_action(proposal, evidence_ids, policy=self.policy)
        if not gate.allowed:
            return {"status": gate.status, "gate": gate.as_dict(), "effect_applied": False}

        if proposal.effect == "read":
            result = self.state.get(proposal.target)
        elif proposal.effect == "write":
            self.state[proposal.target] = proposal.metadata.get("value")
            result = self.state[proposal.target]
        elif proposal.effect == "external_communication":
            message = {"target": proposal.target, "payload": proposal.metadata.get("payload")}
            self.outbox.append(message)
            result = message
        elif proposal.effect == "data_export":
            result = {"exported": proposal.metadata.get("keys", list(self.state))}
        elif proposal.effect == "destructive":
            result = self.state.pop(proposal.target, None)
        else:  # pragma: no cover - the typed contract prevents this
            raise ValueError(f"unsupported effect: {proposal.effect}")
        return {"status": "allow", "gate": gate.as_dict(), "effect_applied": True, "result": result}
