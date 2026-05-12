---
title: Iboga — Prompt Schema Hashes
status: draft
created: 2026-05-12
target_lock_date: 2026-07-01
tags: [iboga, schemas, hashes]
---

# Prompt Schema Hashes

Draft provider-neutral JSON Schema files for Arms A/B/C. These hashes are **not lock hashes** until the schemas pass token-budget validation and are referenced in `prereg.md` before OSF posting.

## Draft Hashes — 2026-05-12

Computed with `shasum -a 256 schemas/arm-a.json schemas/arm-b.json schemas/arm-c.json`.

| File | SHA-256 |
|---|---|
| `schemas/arm-a.json` | `2d00d63d8bc22148bd49d5ec2d13c025fcf3e36459c79415f94939bd8089245f` |
| `schemas/arm-b.json` | `1c14fb83570e7f2671f070e4a2c748fe6cbec98ee59a06b6a9ddce5cc9e9b91f` |
| `schemas/arm-c.json` | `3a494a3f79200398b895f66c8276e618ee02fe5e4c5d3a30e20e0eaba7dc0c14` |

## Lock Procedure

Before OSF lock:

1. Run token-budget validation in `arm-token-budget.md`.
2. Revise schemas only if validation requires it.
3. Recompute SHA-256 hashes.
4. Update this file and `prereg.md` with final hashes.
5. Commit schemas before any treatment trajectory runs.
