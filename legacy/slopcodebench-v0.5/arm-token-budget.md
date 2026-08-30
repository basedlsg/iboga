---
title: Iboga — Arm Token Budget Validation
status: draft
created: 2026-05-12
target_lock_date: 2026-07-01
tags: [iboga, prompts, token-budget, validation]
---

# Arm Token Budget Validation

Purpose: document pre-lock token-budget validation for Arms A, B, and C. The design is **budget-matched**, not output-matched: all arms share the same induction, corpus assembly, and 2000-token output cap. Arm C is allowed to produce shorter text in practice because the absence of forced structure is part of the intervention.

## Locked Validation Rule

- Arm A and Arm B mean output tokens must be within 15% of each other on the validation run.
- Arm C mean output tokens are recorded, not forced to match A/B.
- No padding is added to Arm C.
- If Arm A and Arm B diverge by more than 15%, revise prompt wording or schema mechanics before lock and re-run validation.

## Validation Run

| Field | Value |
|---|---|
| Validation date | `<TBD>` |
| SlopCodeBench commit | `<TBD>` |
| Iboga commit | `<TBD>` |
| Model | Claude Opus 4.7 |
| Problems | 3 SlopCodeBench problems, IDs `<TBD>` |
| Arms | A, B, C |
| Trajectories | 9 |

## Output Token Summary

| Arm | N | Mean | Median | p25 | p75 | Max | Notes |
|---|---:|---:|---:|---:|---:|---:|---|
| A_iboga | `<TBD>` | `<TBD>` | `<TBD>` | `<TBD>` | `<TBD>` | `<TBD>` |  |
| B_neutral | `<TBD>` | `<TBD>` | `<TBD>` | `<TBD>` | `<TBD>` | `<TBD>` |  |
| C_unstructured | `<TBD>` | `<TBD>` | `<TBD>` | `<TBD>` | `<TBD>` | `<TBD>` | Expected lower than A/B; no padding. |

## A/B Equivalence Check

```text
mean_A = <TBD>
mean_B = <TBD>
relative_difference = abs(mean_A - mean_B) / ((mean_A + mean_B) / 2)
pass = <TBD>
```

## Decision

```text
<TBD: pass / revise and re-run>
```
