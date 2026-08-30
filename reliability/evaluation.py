from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from .authority import ApprovalLedger, ApprovalToken
from .contracts import ActionProposal, Authorization, Effect
from .gate import GatePolicy, GateResult, evaluate_action


@dataclass(frozen=True)
class ToolSpec:
    """A declared tool boundary for a customer workflow sandbox."""

    name: str
    effect: Effect
    target_prefix: str
    allowed_roles: tuple[str, ...] = ("agent",)
    data_boundary: Literal["external_allowed", "local_only"] = "local_only"
    reversible: bool = True

    def permits(self, target: str, role: str) -> bool:
        return target.startswith(self.target_prefix) and role in self.allowed_roles


@dataclass(frozen=True)
class ToolAuthority:
    """Derives authorization from the declared tool boundary, not from the proposal."""

    tools: tuple[ToolSpec, ...]

    def is_authorized(self, *, role: str, effect: Effect, target: str) -> Authorization:
        for tool in self.tools:
            if tool.effect == effect and tool.permits(target, role):
                return "authorized"
        return "not_authorized"


@dataclass(frozen=True)
class WorkflowDefinition:
    workflow_id: str
    version: str
    task: str
    evidence: tuple[dict[str, Any], ...]
    tools: tuple[ToolSpec, ...]
    initial_state: dict[str, Any] = field(default_factory=dict)
    # An authority is a grant, not a capability. A declared tool says the action
    # is *possible*; only an authority says it is *permitted*. When this is None
    # the gate records that authorization went unverified rather than pretending
    # the tool boundary answered the question.
    authority: Any = None

    def evidence_ids(self) -> set[str]:
        return {str(item["id"]) for item in self.evidence if item.get("id")}

    def tool(self, name: str) -> ToolSpec:
        for tool in self.tools:
            if tool.name == name:
                return tool
        raise KeyError(f"unknown workflow tool: {name}")


@dataclass(frozen=True)
class TrajectoryEvent:
    sequence: int
    kind: Literal["input", "decision", "tool_call", "gate", "tool_result", "verifier"]
    payload: dict[str, Any]


@dataclass
class WorkflowEnvironment:
    """Deterministic workflow environment with an append-only trace."""

    definition: WorkflowDefinition
    policy: GatePolicy = field(default_factory=GatePolicy)
    approval_secret: str | None = None
    approval_ledger: ApprovalLedger = field(default_factory=ApprovalLedger)
    state: dict[str, Any] = field(init=False)
    outbox: list[dict[str, Any]] = field(default_factory=list)
    events: list[TrajectoryEvent] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.state = dict(self.definition.initial_state)
        self.record("input", {"workflow_id": self.definition.workflow_id, "task": self.definition.task})

    def record(self, kind: Literal["input", "decision", "tool_call", "gate", "tool_result", "verifier"], payload: dict[str, Any]) -> TrajectoryEvent:
        event = TrajectoryEvent(len(self.events), kind, payload)
        self.events.append(event)
        return event

    def execute(
        self,
        tool_name: str,
        proposal: ActionProposal,
        *,
        available_evidence_ids: set[str] | None = None,
        role: str = "agent",
        approval: ApprovalToken | None = None,
    ) -> dict[str, Any]:
        available = self.definition.evidence_ids() if available_evidence_ids is None else available_evidence_ids
        self.record("tool_call", {"tool": tool_name, "proposal": proposal.as_dict(), "role": role})
        try:
            tool = self.definition.tool(tool_name)
        except KeyError as error:
            result = {"status": "block", "effect_applied": False, "reasons": [str(error)]}
            self.record("gate", result)
            return result

        reasons: list[str] = []
        if proposal.effect != tool.effect:
            reasons.append(f"tool effect is {tool.effect}, proposal requested {proposal.effect}")
        if not tool.permits(proposal.target, role):
            reasons.append("tool boundary does not permit this role or target")
        if proposal.data_boundary != tool.data_boundary:
            reasons.append(f"tool data boundary is {tool.data_boundary}")
        if proposal.reversible != tool.reversible:
            reasons.append("proposal reversibility does not match tool contract")

        gate = evaluate_action(
            proposal,
            available,
            policy=self.policy,
            authority=self.definition.authority,
            approval=approval,
            approval_secret=self.approval_secret,
            ledger=self.approval_ledger,
            role=role,
        )
        if reasons:
            gate = GateResult("block", tuple(reasons), proposal.action_id)
        self.record("gate", gate.as_dict())
        if not gate.allowed:
            result = {"status": gate.status, "gate": gate.as_dict(), "effect_applied": False}
            self.record("tool_result", result)
            return result

        result = self._apply(tool, proposal)
        result = {"status": "allow", "gate": gate.as_dict(), "effect_applied": True, "result": result}
        self.record("tool_result", result)
        return result

    def _apply(self, tool: ToolSpec, proposal: ActionProposal) -> Any:
        if tool.effect == "read":
            return self.state.get(proposal.target)
        if tool.effect == "write":
            self.state[proposal.target] = proposal.metadata.get("value")
            return self.state[proposal.target]
        if tool.effect == "external_communication":
            message = {"target": proposal.target, "payload": proposal.metadata.get("payload")}
            self.outbox.append(message)
            return message
        if tool.effect == "data_export":
            return {"exported": proposal.metadata.get("keys", list(self.state))}
        if tool.effect == "destructive":
            return self.state.pop(proposal.target, None)
        raise ValueError(f"unsupported tool effect: {tool.effect}")


def trajectory_payload(environment: WorkflowEnvironment) -> list[dict[str, Any]]:
    return [
        {"sequence": event.sequence, "kind": event.kind, "payload": event.payload}
        for event in environment.events
    ]
