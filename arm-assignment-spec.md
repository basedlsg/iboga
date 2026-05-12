---
title: Iboga — Arm Assignment Specification
status: draft
created: 2026-05-12
target_lock_date: 2026-07-01
tags: [iboga, assignment, blinding, prereg]
---

# Arm Assignment Specification

Purpose: define the deterministic `arm-assignment.json` format and generation rule before pre-reg lock.

## Design Constraint

Every `(model_id, problem_id)` pair must appear in all three main arms:

- `A_iboga`
- `B_neutral`
- `C_unstructured`

Arm 0 is pilot-only and never enters the main 240-trajectory run.

## Blinding Constraint

The candidate writes templates once. At runtime, the runner loads templates automatically from assignment metadata. The operator should monitor trajectory health, cost, and crashes, but should not inspect per-trajectory arm vocabulary or arm-grouped results until analysis.

Practical implementation:

- `arm-assignment.json` contains explicit arm labels because the runner needs them.
- The execution dashboard/log view should show only `trajectory_id`, model, problem, checkpoint, status, and cost.
- Prompt text and arm labels should be written to audit logs but not displayed in routine monitoring.
- The analysis script is the first arm-grouped view after the full run completes.

## Trajectory ID

For each main-run trajectory:

```text
trajectory_id = sha256("iboga-v0.5|main|{model_id}|{problem_id}|{arm}|{run_seed}")
```

For pilot trajectories:

```text
trajectory_id = sha256("iboga-v0.5|pilot|{model_id}|{problem_id}|{arm}|{run_seed}")
```

## Assignment File Format

```json
{
  "version": "0.5.0",
  "status": "draft",
  "created_at": "<ISO timestamp>",
  "assignment_seed": "<TBD>",
  "arms": ["A_iboga", "B_neutral", "C_unstructured"],
  "pilot_arms": ["A_iboga", "B_neutral", "C_unstructured", "arm0_noop"],
  "records": [
    {
      "trajectory_id": "<sha256>",
      "phase": "main",
      "model_id": "opus-4.7",
      "problem_id": "<problem-id>",
      "arm": "A_iboga",
      "run_seed": "<seed>",
      "schema_file": "schemas/arm-a.json"
    }
  ]
}
```

## Generation Rule

For each model and problem in the locked evaluation set:

1. Emit exactly one record for each of `A_iboga`, `B_neutral`, and `C_unstructured`.
2. Derive `run_seed` deterministically from:

```text
sha256("iboga-v0.5|seed|{model_id}|{problem_id}|{arm}|{assignment_seed}")
```

3. Sort records by `trajectory_id` before writing.
4. Generate with `scripts/generate_arm_assignment.py` after the locked problem IDs are available.
5. Write `arm-assignment.json`.
6. Compute and record SHA-256 of `arm-assignment.json` in `prereg.md` before OSF lock.

## Validation Checks

- [ ] Every locked model appears.
- [ ] Every locked problem appears.
- [ ] Every `(model_id, problem_id)` has exactly three main records.
- [ ] The three main records contain exactly one A, one B, and one C arm.
- [ ] No Arm 0 record appears in main phase.
- [ ] All `trajectory_id` values are unique.
- [ ] All `schema_file` paths exist.
- [ ] File hash recorded in `prereg.md`.
