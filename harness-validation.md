---
title: Iboga — Harness Validation Log
status: draft
created: 2026-05-12
target_lock_date: 2026-07-01
tags: [iboga, slopcodebench, harness, validation]
---

# Harness Validation Log

Purpose: record the Week 2 SlopCodeBench fork inspection and validation gates before OSF lock. This file should contain findings only from the SlopCodeBench fork, `scb-check`, and Iboga harness work, not sibling vault projects.

Local helper scripts:

- `scripts/inspect_slopcodebench_repo.py` summarizes relevant metric/runner files from an explicitly supplied local SlopCodeBench clone.
- `scripts/compare_metric_outputs.py` compares upstream vs fork metric summaries once reproduction runs produce CSV outputs.

## Scope Rules

- Inspect upstream metric code and `scb-check` behavior to understand the exact exported `verbosity` and `erosion` fields.
- Do not modify upstream metric files or `scb-check` behavior.
- Harness modifications stay in the agent-invocation path, especially `src/slop_code/agent_runner/runner.py` and the run CLI/config plumbing needed to pass a hook path.
- Retrospective text stays on the host under `~/iboga-data/sessions/{trajectory-id}/` and is injected into the next checkpoint prompt only.
- Nothing from `~/iboga-data/sessions/*` may be mounted into or copied into the checkpoint workspace.

## Upstream Pin

| Field | Value |
|---|---|
| Upstream repo | `SprocketLab/slop-code-bench` |
| Fork repo | `basedlsg/slop-code-bench` |
| Upstream commit hash | `080922495aba9aedc4b7a6c80803bb5ffd301a49` |
| Local clone path | `projects/iboga/slop-code-bench/` |
| Validation date | 2026-05-12 code inspection complete; reproduction pending |

Local setup for reproduction:

| Field | Value |
|---|---|
| SlopCodeBench local environment | `uv sync` complete under `projects/iboga/slop-code-bench/.venv/` |
| `uv` cache | `projects/iboga/.uv-cache/` |
| Managed problem catalog home | `projects/iboga/.scbench/` |
| Problem catalog version | `v1.0` |
| Problem catalog commit | `4d38d300059667d57e43c31969bc455f5c338b52` |
| Catalog problem count | 36 |
| Docker status on 2026-05-12 | Docker CLI installed; daemon started successfully after `open -a Docker`; server `27.3.1` |

`scb-check` pin found during inspection:

| Field | Value |
|---|---|
| Package | `scb-check` |
| Version used by `uvx scb-check --version` | `0.1.3` |
| PyPI wheel inspected locally | `scb_check-0.1.3-py3-none-any.whl` |
| Wheel SHA-256 | `f13040c8ca8f57b8dc8137692c37e0f181fe55867691dfe6a5b8a79d2513f50f` |
| Source repository in package metadata | `https://github.com/gabeorlanski/scb-check` |

## Metric Inspection

### Repository Layout Finding

At pinned SlopCodeBench commit `080922495aba9aedc4b7a6c80803bb5ffd301a49`, there is no in-repo `metrics/verbosity.py` and no metric implementation file named `metrics/erosion.py`.

The exported checkpoint fields are assembled in `slop-code-bench/src/slop_code/metrics/checkpoint/driver.py`. That function first loads evaluation, inference, quality, and rubric metrics, then shells out:

```text
uvx scb-check check --report --include-all <checkpoint>/snapshot
```

The `verbosity` and `erosion` fields used by run summaries come from the JSON report emitted by `scb-check`, not from a local `metrics/verbosity.py` or `metrics/erosion.py`.

SlopCodeBench also contains local helper functions in `src/slop_code/metrics/checkpoint/composites.py`:

- `compute_checkpoint_verbosity(metrics)` returns `verbosity_flagged_pct` if present, else falls back to `clone_lines / loc + violation_pct`.
- `compute_checkpoint_erosion(metrics)` returns `mass.high_cc_pct` if it is between 0 and 1.

Those helpers are exported and tested, but no production call site in `src/` invokes them at this commit. The production checkpoint export path depends on `scb-check`.

### Verbosity

Confirmed `scb-check==0.1.3` behavior:

- Score formula: `verbosity = verbosity_flagged_loc / total_loc`.
- `verbosity_flagged_loc` is the per-file union of:
  - clone SLOC lines,
  - ast-grep SLOC lines,
  - trivial-wrapper SLOC lines.
- This is slightly broader than the paper shorthand and the original Iboga draft, which named only clone lines and ast-grep lines.

Clone detection details:

- Implemented in `scb_check/analysis/clones.py`.
- Parses Python with tree-sitter.
- Candidate AST node types: `function_definition`, `if_statement`, `for_statement`, `while_statement`, `with_statement`, `try_statement`, `match_statement`.
- Minimum candidate size: at least 3 SLOC lines by default.
- Excludes `TYPE_CHECKING` / `typing.TYPE_CHECKING` blocks.
- Normalizes identifiers to `$VARn`.
- Normalizes literals to typed placeholders such as `$STR`, `$INT`, `$FLOAT`, `$BOOL`, `$NONE`.
- Ignores comments and plain string expression statements in the normalized subtree.
- Hashes normalized AST subtrees with MD5, truncated to 12 hex chars.
- Groups are exact hash matches. The algorithm is deterministic.

Traversal and isolation details:

- Implemented in `scb_check/walker.py`.
- Input root is the checkpoint `snapshot` directory passed by SlopCodeBench.
- Only `*.py` files are yielded.
- Common generated/cache directories are excluded by default.
- Symlinks are skipped for both directories and files (`not child.is_symlink()`), which helps prevent host-session leakage if a symlink were accidentally placed in the workspace.

### Erosion

Confirmed `scb-check==0.1.3` behavior:

- `ParsedSymbol.cc_mass() = cyc_complexity * sqrt(sloc)`.
- High-CC threshold is `cyc_complexity > 10`.
- `erosion = sum(cc_mass(high_cc_functions)) / sum(cc_mass(all_functions))`.
- Empty denominator returns `0.0`.

The in-repo SlopCodeBench quality metric `src/slop_code/metrics/checkpoint/mass.py` computes the same high-CC mass share as `mass.high_cc_pct`, but production checkpoint summaries use the `erosion` field emitted by `scb-check`.

Slope computation:

- SlopCodeBench run summaries aggregate checkpoint `verbosity` and `erosion` as distributional stats, including means.
- The OLS slope across checkpoint index is not computed by the upstream metric path found here.
- Iboga must compute `erosion_slope` and `verbosity_slope` in its own trajectory post-processor from per-checkpoint `checkpoint_results.jsonl`, using the exported `erosion` and `verbosity` fields and the checkpoint order `idx`.

## Runner Hook Inspection

Questions answered:

- Checkpoint prompt assembly: `slop-code-bench/src/slop_code/agent_runner/runner.py::get_task_for_checkpoint()`.
- Prompt write path: same function writes `prompt.txt` under the checkpoint output directory.
- Agent context reset between checkpoints: `AgentRunner._setup_for_checkpoint()` calls `agent.finish_checkpoint(reset_context=True)` for non-first checkpoints.
- Checkpoint loop: `AgentRunner._run_problem()` iterates checkpoints, calls `_run_checkpoint()`, evaluates, appends summary, and then advances.
- CLI/config plumbing: `slop-code-bench/src/slop_code/entrypoints/commands/run_agent.py` builds a `RunTaskConfig`, which is defined in `src/slop_code/entrypoints/problem_runner/models.py`.

Chosen hook insertion point:

```text
Add hook configuration to RunTaskConfig, thread it into AgentRunner, and invoke it in AgentRunner._run_problem()
for checkpoints idx > 0 after the previous checkpoint has finished and before the next prompt is rendered.
The hook returns prompt-prefix text. run_checkpoint()/get_task_for_checkpoint() receives that prefix and prepends it
to the checkpoint k+1 task string before writing prompt.txt and before agent.run_checkpoint(task).
```

Rationale:

- This keeps metrics untouched.
- The previous checkpoint snapshot, diff, evaluation files, and agent artifacts exist by the time the hook runs.
- The prefix is injected into the agent prompt only; no retrospective file needs to enter `snapshot`.
- The first checkpoint gets no retrospective prefix.

Proposed hook contract:

```text
hook(
  trajectory_id,
  model_id,
  problem_id,
  previous_checkpoint_name,
  current_checkpoint_name,
  previous_checkpoint_output_dir,
  previous_snapshot_dir,
  previous_diff_path,
  prior_session_dir
) -> prompt_prefix_text
```

Implementation facts confirmed before coding:

- Prior diff filename is `diff.json`; `save_agent_checkpoint_info()` writes it with `diff.model_dump_json()`.
- `_run_inference()` calls `session.finish_checkpoint(snapshot_dir)` in a `finally` block, so a checkpoint snapshot/diff is produced even when agent inference raises.
- The default environment config `configs/environments/docker-python3.12-uv.yaml` sets `docker.workdir: /workspace` and `docker.mount_workspace: true` with no `extra_mounts` field.

Open implementation questions before coding:

- Decide whether the hook subprocess receives JSON on stdin or command-line arguments; JSON stdin is less brittle.
- Add a no-op hook mode that exercises the same call path and returns an empty string for Arm 0.
- Confirm resume behavior: completed checkpoints should not re-run hooks, and hook outputs must be persisted on host so resumed runs reuse the prior prefix.

## Baseline Reproduction Gate

Run upstream/forked harness on 5 published baseline models x 5 problems. Pass condition: solve rate, erosion slope, and verbosity slope reproduce upstream report within +/-2 percentage points where the upstream report exposes the comparable statistic.

No-cost setup checks completed on 2026-05-12:

- `uv sync` succeeded for the pinned SlopCodeBench clone.
- Problem catalog installed locally under `projects/iboga/.scbench/`.
- `configs/runs/lite_under20.yaml` resolves to two cheap problems: `mvvault` and `xjq`.
- Resolved default run config for `lite_under20`: `agent=claude_code@2.0.51`, `model=anthropic/sonnet-4.5`, `thinking=high`, `environment=docker-python3.12-uv`.
- `mvvault` has 6 checkpoints and entry file `mvault`; `xjq` has 5 checkpoints and entry file `xjq`.
- The default upstream route `slop-code run --config configs/runs/lite_under20.yaml --dry-run --no-live-progress` reaches the SlopCodeBench credential-resolution step, then stops before agent execution because it uses `anthropic/sonnet-4.5` and no direct Anthropic key is configured.

Non-Anthropic provider checks completed on 2026-05-13:

- Gemini CLI OAuth route passes credential resolution: `uv run slop-code run --config configs/runs/lite_under20.yaml --agent gemini --model gemini_auth/gemini-2.5-flash-lite --dry-run --no-live-progress`.
- OpenRouter route is syntactically valid but blocked by shell state: `uv run slop-code run --config configs/runs/lite_under20.yaml --agent miniswe --model openrouter/gemini-2.5-flash-lite --dry-run --no-live-progress` stops because `OPENROUTER_API_KEY` is not exported.
- Local model configs added in the SlopCodeBench fork clone for Opus 4.7 via OpenRouter, Qwen2.5-32B, and Llama-3.1-8B. All three reach `OPENROUTER_API_KEY` credential resolution in dry-run probes.
- Gemini Docker image build passes after Docker disk cleanup: `uv run slop-code docker build-agent configs/agents/gemini.yaml configs/environments/docker-python3.12-uv.yaml` built `slop-code:python3.12` and `slop-code:gemini-0.41.2-python3.12`. Initial failures were Docker Desktop storage exhaustion during apt/Rust installation; resolved by pruning build cache, stopped containers, and unused images.
- Actual no-treatment Gemini validation run started on `xjq` only: `uv run slop-code run --config configs/runs/lite_under20.yaml --agent gemini --model gemini_auth/gemini-2.5-flash-lite --problem xjq --no-live-progress`. Output path: `slop-code-bench/outputs/lite_under20_runs/gemini-2.5-flash-lite_0.41.2_high_just-solve/20260513T1427/`.
- Checkpoint 1 completed and evaluated locally: `inference_result.json` reports no agent error, 9 steps, cost `$0.005402`; `evaluation.json` collected 23 tests with infrastructure failure `false`.
- Checkpoint 2 did not complete. Gemini CLI repeatedly hit Google Code Assist capacity errors (`429`, `MODEL_CAPACITY_EXHAUSTED`, "No capacity available for model gemini-2.5-flash-lite") after a long agent loop. The run was stopped manually after checkpoint 2 reached 61 steps to avoid waiting for the one-hour timeout.
- See `provider-routing.md` for provider slugs and local model-config work required before the locked-model pilot.

| Model | Problems | Solve delta | Erosion slope delta | Verbosity slope delta | Pass? | Notes |
|---|---:|---:|---:|---:|---|---|
| `<TBD>` | 5 | `<TBD>` | `<TBD>` | `<TBD>` | `<TBD>` |  |
| `<TBD>` | 5 | `<TBD>` | `<TBD>` | `<TBD>` | `<TBD>` |  |
| `<TBD>` | 5 | `<TBD>` | `<TBD>` | `<TBD>` | `<TBD>` |  |
| `<TBD>` | 5 | `<TBD>` | `<TBD>` | `<TBD>` | `<TBD>` |  |
| `<TBD>` | 5 | `<TBD>` | `<TBD>` | `<TBD>` | `<TBD>` |  |

Gate verdict:

```text
Partial pass. Local dependencies, problem catalog, Docker daemon, config resolution, and Gemini agent image build are ready. Gemini CLI OAuth can execute checkpoints but is not stable enough for a full baseline run today because of Google capacity errors. Next full no-treatment run should use OpenRouter after `OPENROUTER_API_KEY` is exported, or retry Gemini later with explicit step limits.
```

Comparison helper:

```bash
python3 scripts/compare_metric_outputs.py \
  --upstream <upstream-summary.csv> \
  --fork <fork-summary.csv> \
  --tolerance-pp 2
```

## Arm 0 Hook Neutrality Gate

Arm 0: run the between-checkpoint hook infrastructure with empty retrospective output. Pass condition: no-hook baseline vs Arm 0 no-op hook differs by no more than +/-2 percentage points on erosion and verbosity.

| Model | Problem set | Erosion delta | Verbosity delta | Solve delta | Pass? | Notes |
|---|---|---:|---:|---:|---|---|
| `<TBD>` | `<TBD>` | `<TBD>` | `<TBD>` | `<TBD>` | `<TBD>` |  |

Gate verdict:

```text
Pending. Hook not implemented yet.
```

## Retrospective Isolation Gate

Pass condition: `~/iboga-data/sessions/*` never enters the Docker workspace and cannot be traversed by `scb-check`, AST-Grep, radon, or clone detection.

Checks:

- [x] Confirm default Docker/session mount list excludes `~/iboga-data`.
- [ ] Add Iboga wrapper assertion that spec/runtime mounts exclude `~/iboga-data`.
- [ ] Confirm hook output is prompt text only.
- [ ] Confirm no session/corpus files are written under the checkpoint workspace or `snapshot`.
- [x] Confirm metric traversal root is checkpoint `snapshot` only for the `scb-check` composite fields.
- [x] Confirm `scb-check` skips symlinked files and directories.

Code-inspection findings from 2026-05-12:

- `Session.from_environment_spec()` creates a workspace in a temporary directory.
- `Session.spawn()` and `Session.exec()` pass that temp workspace as the runtime `working_dir`.
- Docker runtime `_build_volumes()` mounts the session workspace read-write at `docker.workdir` when `mount_workspace` is true.
- Static assets mount read-only under `/static/{asset.save_path}`.
- Spec-level `docker.extra_mounts` and runtime `mounts` are the only inspected paths that could introduce additional host content into a container.
- The pinned default Python Docker environment has `mount_workspace: true`, `workdir: /workspace`, and no configured `extra_mounts`.

Findings:

```text
Partial. Code inspection supports isolation if Iboga never writes/symlinks host session files into snapshot
and never passes ~/iboga-data through spec-level or runtime mounts. Runtime assertion and Arm 0 validation
remain pending.
```

## Lock Decision

Pre-reg lock may proceed only if all required gates pass.

| Gate | Status |
|---|---|
| Upstream pin recorded | Complete |
| Metric inspection complete | Complete for code inspection; baseline reproduction pending |
| Runner hook insertion identified | Complete for design; implementation pending |
| Baseline reproduction within +/-2 pp | Pending |
| Arm 0 hook neutrality within +/-2 pp | Pending |
| Retrospective isolation verified | Partially inspected; runtime validation pending |

Decision:

```text
Do not lock yet. Next blocked steps are baseline reproduction, hook implementation, Arm 0 neutrality, and runtime mount/isolation validation.
```
