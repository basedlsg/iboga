"""Crash-safe JSONL checkpoints for long live runs.

The checkpoint contains completed trajectory records and a protocol hash.  It
never receives credentials; error messages are redacted against the current
process environment before they are written.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1


def record_key(record: dict[str, Any]) -> tuple[Any, ...]:
    return (record.get("repeat"), record.get("condition"), record.get("sample_id"))


def redact_sensitive(value: str) -> str:
    result = value
    for name in ("AWS_BEARER_TOKEN_BEDROCK", "OPENAI_API_KEY", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_SESSION_TOKEN"):
        secret = os.getenv(name)
        if secret and len(secret) >= 8:
            result = result.replace(secret, "[REDACTED]")
    return result[:2_000]


class JsonlCheckpoint:
    def __init__(self, path: Path, *, manifest_hash: str) -> None:
        self.path = path
        self.manifest_hash = manifest_hash

    def load(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        records: list[dict[str, Any]] = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            value = json.loads(line)
            if value.get("kind") == "header":
                if value.get("schema_version") != SCHEMA_VERSION or value.get("manifest_hash") != self.manifest_hash:
                    raise ValueError("checkpoint schema or manifest hash mismatch")
            elif value.get("kind") == "record":
                record = value.get("record")
                if not isinstance(record, dict):
                    raise ValueError("checkpoint record must be an object")
                records.append(record)
        return records

    def initialize(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.path.exists() and self.path.stat().st_size:
            self.load()
            return
        header = {"kind": "header", "schema_version": SCHEMA_VERSION, "manifest_hash": self.manifest_hash}
        self.path.write_text(json.dumps(header, sort_keys=True) + "\n", encoding="utf-8")

    def append(self, record: dict[str, Any]) -> None:
        self.initialize()
        safe = dict(record)
        if isinstance(safe.get("error"), str):
            safe["error"] = redact_sensitive(safe["error"])
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps({"kind": "record", "record": safe}, ensure_ascii=False, sort_keys=True) + "\n")
