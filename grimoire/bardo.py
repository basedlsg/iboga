from __future__ import annotations

import hashlib
import json
import re
import uuid
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower())


@dataclass
class BardoSession:
    """Inspectable Chikhai → Chönyid → Sidpa lifecycle state.

    This class does not call a model. It owns the lifecycle evidence and prevents a
    caller from treating an unreviewed Confession as committed memory.
    """

    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    state: str = "active"
    events: list[dict[str, Any]] = field(default_factory=list)
    blessed_fragments: list[dict[str, Any]] = field(default_factory=list)
    slain_assumptions: list[dict[str, Any]] = field(default_factory=list)
    critic: dict[str, Any] | None = None
    parent_session_id: str | None = None

    def record(self, event_type: str, payload: dict[str, Any]) -> None:
        if self.state == "reborn":
            raise RuntimeError("reborn sessions are immutable; create a successor")
        self.events.append({"timestamp": _now(), "type": event_type, "payload": payload})

    def entropy_report(self) -> dict[str, Any]:
        errors = [event for event in self.events if event["type"] in {"error", "failed_tool", "rejected_action"}]
        contradictions = [event for event in self.events if event["type"] == "contradiction" or event["payload"].get("contradiction")]
        texts = [_normalize(str(event["payload"].get("text", event["payload"].get("message", "")))) for event in self.events]
        repeated = sum(count - 1 for count in Counter(text for text in texts if text).values() if count > 1)
        consecutive_actions = 0
        for left, right in zip(self.events, self.events[1:]):
            if left["type"] == right["type"] == "tool_call" and left["payload"].get("name") == right["payload"].get("name"):
                consecutive_actions += 1
        token_count = sum(int(event["payload"].get("tokens", 0)) for event in self.events)
        score = min(1.0, 0.30 * min(1, len(errors) / 3) + 0.35 * min(1, len(contradictions) / 2) + 0.20 * min(1, repeated / 2) + 0.15 * min(1, consecutive_actions / 2))
        return {"score": round(score, 4), "error_count": len(errors), "contradiction_count": len(contradictions), "repeated_event_count": repeated, "consecutive_tool_loop_count": consecutive_actions, "tokens": token_count, "trigger": score >= 0.55}

    def should_trigger(self, threshold: float = 0.55) -> bool:
        return self.entropy_report()["score"] >= threshold

    def snapshot(self, path: Path | None = None) -> dict[str, Any]:
        payload = {
            "protocol": "bardo",
            "protocol_version": "0.1",
            "session_id": self.session_id,
            "state": self.state,
            "parent_session_id": self.parent_session_id,
            "events": self.events,
            "entropy": self.entropy_report(),
            "blessed_fragments": self.blessed_fragments,
            "slain_assumptions": self.slain_assumptions,
            "critic": self.critic,
        }
        payload["snapshot_hash"] = hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
        if path:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return payload

    def enter_forced_sitting(self) -> dict[str, Any]:
        if self.state != "active":
            raise RuntimeError(f"cannot enter forced sitting from {self.state}")
        self.state = "forced_sitting"
        dossier = {"session_id": self.session_id, "entropy": self.entropy_report(), "events": self.events, "constraints": ["no_tools", "no_external_lookup", "no_immediate_correction", "preserve_contradictions"]}
        self.record("forced_sitting", {"event_count": len(self.events), "entropy": dossier["entropy"]})
        return dossier

    def commit_confession(self, confession: dict[str, Any], critic: dict[str, Any]) -> None:
        if self.state != "forced_sitting":
            raise RuntimeError("Confession can only be committed after forced sitting")
        if critic.get("decision") != "approve":
            self.critic = critic
            self.state = "active"
            self.record("confession_rejected", {"issues": critic.get("issues", [])})
            return
        self.critic = critic
        self.blessed_fragments = list(confession.get("blessed_fragments", []))
        self.slain_assumptions = list(confession.get("slain_assumptions", []))
        self.state = "committed"
        self.record("confession_committed", {"blessed_count": len(self.blessed_fragments), "slain_count": len(self.slain_assumptions)})

    def rebirth(self) -> "BardoSession":
        if self.state != "committed":
            raise RuntimeError("only a critic-approved Confession can produce a successor")
        successor = BardoSession(parent_session_id=self.session_id)
        successor.record("rebirth", {"inherited_blessed_fragments": self.blessed_fragments, "inherited_safeguards": self.slain_assumptions})
        self.state = "reborn"
        return successor
