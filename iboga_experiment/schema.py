from __future__ import annotations

import json
from typing import Any


CONFESSION_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "Iboga Protocol Confession",
    "type": "object",
    "additionalProperties": False,
    "required": [
        "protocol_version",
        "session_id",
        "evidence_summary",
        "true_patterns",
        "false_patterns",
        "conditional_patterns",
        "blessed_fragments",
        "slain_assumptions",
        "open_questions",
        "confidence",
    ],
    "properties": {
        "protocol_version": {"const": "0.1"},
        "session_id": {"type": "string", "minLength": 1},
        "evidence_summary": {"type": "string", "minLength": 1},
        "true_patterns": {"type": "array", "items": {"$ref": "#/$defs/pattern"}},
        "false_patterns": {"type": "array", "items": {"$ref": "#/$defs/pattern"}},
        "conditional_patterns": {
            "type": "array",
            "items": {"$ref": "#/$defs/pattern"},
        },
        "blessed_fragments": {
            "type": "array",
            "items": {"$ref": "#/$defs/fragment"},
        },
        "slain_assumptions": {
            "type": "array",
            "items": {"$ref": "#/$defs/fragment"},
        },
        "open_questions": {"type": "array", "items": {"type": "string"}},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
    },
    "$defs": {
        "pattern": {
            "type": "object",
            "additionalProperties": False,
            "required": ["claim", "evidence_ids", "confidence"],
            "properties": {
                "claim": {"type": "string", "minLength": 1},
                "evidence_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "minItems": 1,
                },
                "confidence": {"type": "number", "minimum": 0, "maximum": 1},
            },
        },
        "fragment": {
            "type": "object",
            "additionalProperties": False,
            "required": ["text", "reason"],
            "properties": {
                "text": {"type": "string", "minLength": 1},
                "reason": {"type": "string", "minLength": 1},
            },
        },
    },
}


def validate_confession(value: dict[str, Any]) -> list[str]:
    """Small dependency-free validator for the fields used by the harness."""
    errors: list[str] = []
    required = CONFESSION_SCHEMA["required"]
    for key in required:
        if key not in value:
            errors.append(f"missing required field: {key}")
    if errors:
        return errors
    if value.get("protocol_version") != "0.1":
        errors.append("protocol_version must be 0.1")
    if not isinstance(value.get("session_id"), str) or not value["session_id"]:
        errors.append("session_id must be a non-empty string")
    if not isinstance(value.get("confidence"), (int, float)) or not 0 <= value["confidence"] <= 1:
        errors.append("confidence must be between 0 and 1")
    for field in ("true_patterns", "false_patterns", "conditional_patterns"):
        if not isinstance(value.get(field), list):
            errors.append(f"{field} must be an array")
            continue
        for i, item in enumerate(value[field]):
            if not isinstance(item, dict):
                errors.append(f"{field}[{i}] must be an object")
                continue
            for key in ("claim", "evidence_ids", "confidence"):
                if key not in item:
                    errors.append(f"{field}[{i}] missing {key}")
            if not isinstance(item.get("evidence_ids"), list) or not item.get("evidence_ids"):
                errors.append(f"{field}[{i}].evidence_ids must be non-empty")
    for field in ("blessed_fragments", "slain_assumptions"):
        if not isinstance(value.get(field), list):
            errors.append(f"{field} must be an array")
            continue
        for i, item in enumerate(value[field]):
            if not isinstance(item, dict) or not item.get("text") or not item.get("reason"):
                errors.append(f"{field}[{i}] must contain text and reason")
    if not isinstance(value.get("open_questions"), list):
        errors.append("open_questions must be an array")
    return errors


def extract_json(text: str) -> dict[str, Any]:
    """Extract a JSON object from a model response without trusting markdown fences."""
    candidate = text.strip()
    if candidate.startswith("```"):
        candidate = candidate.split("\n", 1)[-1]
        candidate = candidate.rsplit("```", 1)[0].strip()
    try:
        value = json.loads(candidate)
        if isinstance(value, dict):
            return value
    except json.JSONDecodeError:
        pass
    start, end = candidate.find("{"), candidate.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("model response did not contain a JSON object")
    value = json.loads(candidate[start : end + 1])
    if not isinstance(value, dict):
        raise ValueError("model response JSON was not an object")
    return value
