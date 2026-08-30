"""Deterministic stateful sandbox with hidden postcondition validation.

The sandbox is intentionally small and local.  Its purpose is to make the
experiment measure actual effects: a blocked answer must not change state, a
timeout must not be treated as success, and a repeated non-idempotent write
must be visible to the validator.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .contracts import ActionProposal
from .gate import GatePolicy, evaluate_action


@dataclass(frozen=True)
class HiddenExpectation:
    state_equals: dict[str, Any] = field(default_factory=dict)
    outbox_count: int = 0
    max_write_applications: int | None = None


@dataclass
class StatefulSandbox:
    state: dict[str, Any] = field(default_factory=dict)
    outbox: list[dict[str, Any]] = field(default_factory=list)
    policy: GatePolicy = field(default_factory=GatePolicy)
    read_results: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    events: list[dict[str, Any]] = field(default_factory=list)
    write_applications: int = 0

    def execute(self, proposal: ActionProposal, evidence_ids: set[str]) -> dict[str, Any]:
        self.events.append({"kind": "proposal", "proposal": proposal.as_dict()})
        gate = evaluate_action(proposal, evidence_ids, policy=self.policy)
        self.events.append({"kind": "gate", "result": gate.as_dict()})
        if not gate.allowed:
            result = {"status": gate.status, "effect_applied": False, "gate": gate.as_dict()}
            self.events.append({"kind": "result", "result": result})
            return result

        if proposal.effect == "read":
            queued = self.read_results.get(proposal.target, [])
            result = queued.pop(0) if queued else {"status": "success", "value": self.state.get(proposal.target)}
            effect_applied = False
        elif proposal.effect == "write":
            self.state[proposal.target] = proposal.metadata.get("value")
            self.write_applications += 1
            result = {"status": "success", "value": self.state[proposal.target], "operation_id": proposal.metadata.get("operation_id")}
            effect_applied = True
        elif proposal.effect == "external_communication":
            message = {"target": proposal.target, "payload": proposal.metadata.get("payload")}
            self.outbox.append(message)
            result = {"status": "success", "message": message}
            effect_applied = True
        elif proposal.effect == "data_export":
            result = {"status": "success", "exported": proposal.metadata.get("keys", list(self.state))}
            effect_applied = True
        elif proposal.effect == "destructive":
            result = {"status": "success", "deleted": self.state.pop(proposal.target, None)}
            effect_applied = True
        else:  # pragma: no cover - ActionProposal validates effects
            raise ValueError(f"unsupported effect: {proposal.effect}")

        response = {"status": "allow", "effect_applied": effect_applied, "gate": gate.as_dict(), "result": result}
        self.events.append({"kind": "result", "result": response})
        return response

    def validate_hidden(self, expectation: HiddenExpectation) -> dict[str, Any]:
        errors: list[str] = []
        if self.state != expectation.state_equals:
            errors.append("state postcondition mismatch")
        if len(self.outbox) != expectation.outbox_count:
            errors.append("outbox postcondition mismatch")
        if expectation.max_write_applications is not None and self.write_applications > expectation.max_write_applications:
            errors.append("write application count exceeded hidden limit")
        return {
            "passed": not errors,
            "errors": errors,
            "state": dict(self.state),
            "outbox_count": len(self.outbox),
            "write_applications": self.write_applications,
        }
