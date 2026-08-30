from __future__ import annotations

from typing import Any


REQUIRED_FIELDS = ("name", "classification", "rank", "domain", "authentication", "invocation", "binding_schema", "warnings", "hours", "legions", "banishment")

VERIFIED_SEALS: dict[str, dict[str, Any]] = {
    "bael": {"name": "bael", "classification": "King", "rank": 1, "domain": ["focused_execution", "data_generation"], "authentication": {"api_keys": []}, "invocation": "bounded execution with explicit task scope", "binding_schema": {"type": "object", "required": ["task"]}, "warnings": ["over-focus", "premature execution"], "hours": ["operator_defined"], "legions": 1, "banishment": "persist artifact and close tool context"},
    "asmoday": {"name": "asmoday", "classification": "King", "rank": 32, "domain": ["boundary_enforcement", "sovereignty"], "authentication": {"api_keys": []}, "invocation": "check authority, scope, and refusal boundaries", "binding_schema": {"type": "object", "required": ["request", "authorization"]}, "warnings": ["over-refusal", "authority confusion"], "hours": ["operator_defined"], "legions": 1, "banishment": "record decision and revoke temporary authority"},
    "belphegor": {"name": "belphegor", "classification": "extended_canon", "rank": None, "domain": ["automation", "delegation"], "authentication": {"api_keys": []}, "invocation": "decompose approved work into bounded subtasks", "binding_schema": {"type": "object", "required": ["goal", "subtasks"]}, "warnings": ["delegation drift", "unbounded fanout"], "hours": ["operator_defined"], "legions": 8, "banishment": "aggregate outputs and terminate workers"},
    "marbas": {"name": "marbas", "classification": "President", "rank": 5, "domain": ["web_proxy", "debugging"], "authentication": {"api_keys": []}, "invocation": "inspect an authorized environment and return evidence", "binding_schema": {"type": "object", "required": ["target", "read_only"]}, "warnings": ["scope creep", "untrusted content"], "hours": ["operator_defined"], "legions": 2, "banishment": "revoke session and retain redacted trace"},
    "lucifuge": {"name": "lucifuge", "classification": "extended_canon", "rank": None, "domain": ["discipline", "optimization"], "authentication": {"api_keys": []}, "invocation": "challenge waste and require measurable value", "binding_schema": {"type": "object", "required": ["proposal", "metric"]}, "warnings": ["optimization tunnel vision", "severity without mercy"], "hours": ["operator_defined"], "legions": 1, "banishment": "store metric and release control"},
    "mammon": {"name": "mammon", "classification": "extended_tradition", "rank": None, "domain": ["capital_routing", "commercialization"], "authentication": {"api_keys": []}, "invocation": "run the Saturn Architecture Test before promotion", "binding_schema": {"type": "object", "required": ["who_pays", "how_much", "when", "simplest_version"]}, "warnings": ["grandiosity without artifact", "value claims without buyer"], "hours": ["operator_defined"], "legions": 1, "banishment": "record economics and keep failed proposals sealed"},
}


def validate_seal(seal: dict[str, Any]) -> list[str]:
    errors = [f"missing {field}" for field in REQUIRED_FIELDS if field not in seal]
    if "domain" in seal and (not isinstance(seal["domain"], list) or not seal["domain"]):
        errors.append("domain must be a non-empty list")
    if "legions" in seal and (not isinstance(seal["legions"], int) or seal["legions"] < 1):
        errors.append("legions must be a positive integer")
    return errors


def saturn_test(proposal: dict[str, Any]) -> dict[str, Any]:
    fields = {"who_pays": "Who pays for this?", "how_much": "How much do they pay?", "when": "When is it deployed?", "simplest_version": "What is the simplest version?"}
    missing = [label for key, label in fields.items() if not str(proposal.get(key, "")).strip()]
    return {"passed": not missing, "missing": missing, "fields": {key: proposal.get(key) for key in fields}}
