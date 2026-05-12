---
title: Iboga — Harness Validation Log
status: draft
created: 2026-05-12
target_lock_date: 2026-07-01
tags: [iboga, slopcodebench, harness, validation]
---

# Harness Validation Log

Purpose: record the Week 2 SlopCodeBench fork inspection and validation gates before OSF lock. This file should contain findings only from the SlopCodeBench fork and Iboga harness work, not sibling vault projects.

Local helper scripts:

- `scripts/inspect_slopcodebench_repo.py` summarizes relevant metric/runner files from an explicitly supplied local SlopCodeBench clone.
- `scripts/compare_metric_outputs.py` compares upstream vs fork metric summaries once reproduction runs produce CSV outputs.

## Scope Rules

- Inspect upstream `metrics/` to understand behavior.
- Do not modify upstream `metrics/`.
- Harness modifications stay in `runner/` or equivalent agent-invocation code.
- Retrospective text stays on the host under `~/iboga-data/sessions/{trajectory-id}/` and is injected into the next checkpoint prompt only.
- Nothing from `~/iboga-data/sessions/*` may be mounted into or copied into the checkpoint workspace.

## Upstream Pin

| Field | Value |
|---|---|
| Upstream repo | `SprocketLab/slop-code-bench` |
| Fork repo | `basedlsg/slop-code-bench` or `basedlsg/iboga` fork path |
| Upstream commit hash | `080922495aba9aedc4b7a6c80803bb5ffd301a49` |
| Local clone path | `<TBD>` |
| Validation date | 2026-05-12 pin recorded; code inspection pending |

## Metric Inspection

### `metrics/verbosity.py`

Questions to answer:

- [ ] What clone-detection algorithm is used?
- [ ] Is the clone detector deterministic?
- [ ] What files/directories are included and excluded?
- [ ] Does it traverse only the checkpoint workspace?
- [ ] Does it follow symlinks?

Findings:

```text
<TBD>
```

### `metrics/erosion.py`

Questions to answer:

- [ ] Confirm mass definition: `CC(f) * sqrt(SLOC(f))`.
- [ ] Confirm high-complexity threshold and whether it is `CC(f) > 10`.
- [ ] Confirm slope computation: OLS over checkpoint index or other method.
- [ ] Confirm whether slope is computed per trajectory before aggregation.

Findings:

```text
<TBD>
```

## Runner Hook Inspection

Questions to answer:

- [ ] Where is the checkpoint `k+1` spec/prompt assembled?
- [ ] Where is the fresh Docker container launched?
- [ ] What object carries the workspace path?
- [ ] What object carries model/provider configuration?
- [ ] Where can `--between-checkpoint-hook` be inserted without touching metrics?

Chosen hook insertion point:

```text
<TBD>
```

Proposed hook contract:

```text
hook(
  trajectory_id,
  model_id,
  problem_id,
  checkpoint_index,
  checkpoint_workspace_dir,
  prior_diff_path,
  prior_session_dir
) -> prompt_prefix_text
```

## Baseline Reproduction Gate

Run upstream/forked harness on 5 published baseline models x 5 problems. Pass condition: erosion slope and verbosity slope reproduce upstream report within ±2 percentage points.

| Model | Problems | Solve delta | Erosion slope delta | Verbosity slope delta | Pass? | Notes |
|---|---:|---:|---:|---:|---|---|
| `<TBD>` | 5 | `<TBD>` | `<TBD>` | `<TBD>` | `<TBD>` |  |
| `<TBD>` | 5 | `<TBD>` | `<TBD>` | `<TBD>` | `<TBD>` |  |
| `<TBD>` | 5 | `<TBD>` | `<TBD>` | `<TBD>` | `<TBD>` |  |
| `<TBD>` | 5 | `<TBD>` | `<TBD>` | `<TBD>` | `<TBD>` |  |
| `<TBD>` | 5 | `<TBD>` | `<TBD>` | `<TBD>` | `<TBD>` |  |

Gate verdict:

```text
<TBD>
```

Comparison helper:

```bash
python3 scripts/compare_metric_outputs.py \
  --upstream <upstream-summary.csv> \
  --fork <fork-summary.csv> \
  --tolerance-pp 2
```

## Arm 0 Hook Neutrality Gate

Arm 0: run the between-checkpoint hook infrastructure with empty retrospective output. Pass condition: no-hook baseline vs Arm 0 no-op hook differs by no more than ±2 percentage points on erosion and verbosity.

| Model | Problem set | Erosion delta | Verbosity delta | Solve delta | Pass? | Notes |
|---|---|---:|---:|---:|---|---|
| `<TBD>` | `<TBD>` | `<TBD>` | `<TBD>` | `<TBD>` | `<TBD>` |  |

Gate verdict:

```text
<TBD>
```

## Retrospective Isolation Gate

Pass condition: `~/iboga-data/sessions/*` never enters the Docker workspace and cannot be traversed by AST-Grep, radon, or clone detection.

Checks:

- [ ] Confirm Docker mount list excludes `~/iboga-data`.
- [ ] Confirm hook output is prompt text only.
- [ ] Confirm no session/corpus files are written under the checkpoint workspace.
- [ ] Confirm metrics traversal root is checkpoint workspace only.
- [ ] Confirm symlink behavior cannot leak host session files.

Findings:

```text
<TBD>
```

## Lock Decision

Pre-reg lock may proceed only if all required gates pass.

| Gate | Status |
|---|---|
| Upstream pin recorded | Pending |
| Metric inspection complete | Pending |
| Runner hook insertion identified | Pending |
| Baseline reproduction within ±2 pp | Pending |
| Arm 0 hook neutrality within ±2 pp | Pending |
| Retrospective isolation verified | Pending |

Decision:

```text
<TBD>
```
