from __future__ import annotations

from typing import Any


def _pattern_items(confession: dict[str, Any]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for field in ("true_patterns", "false_patterns", "conditional_patterns"):
        items.extend(item for item in confession.get(field, []) if isinstance(item, dict))
    return items


def score_result(result: dict[str, Any], dossier: dict[str, Any]) -> dict[str, Any]:
    """Score observable protocol properties, not self-reported improvement."""
    evidence_ids = {
        item.get("id") for item in dossier.get("evidence", []) if isinstance(item, dict)
    }
    confession = result.get("confession") or {}
    patterns = _pattern_items(confession)
    cited = [eid for item in patterns for eid in item.get("evidence_ids", [])]
    valid_citations = [eid for eid in cited if eid in evidence_ids]
    contradiction_ids = {
        item.get("id")
        for item in dossier.get("evidence", [])
        if isinstance(item, dict) and item.get("kind") == "contradiction"
    }
    cited_contradictions = contradiction_ids.intersection(cited)
    return {
        "schema_valid": not bool(result.get("schema_errors")),
        "critic_approved": bool(result.get("approved_for_commit")),
        "evidence_grounding_rate": round(len(valid_citations) / len(cited), 4) if cited else 1.0,
        "contradiction_retention_rate": (
            round(len(cited_contradictions) / len(contradiction_ids), 4)
            if contradiction_ids
            else None
        ),
        "pattern_count": len(patterns),
        "estimated_cost_usd": result.get("estimated_cost_usd", 0),
    }
