---
title: Iboga — Jules Task Prompts (J6-J9)
status: ready_to_dispatch
created: 2026-05-14
prerequisite: github.com/basedlsg/iboga must be public + connected to Jules
related: provider-routing.md, harness-validation.md
tags: [iboga, jules, engineering, dispatch]
---

# Jules Task Prompts — ALL COMPLETE (historical)

> **STATUS 2026-05-15: J6-J9 all dispatched, reviewed, and merged.** This file is now a historical record. The prompts below were the dispatch text; the actual dispatched versions differed in details (J6 targeted `basedlsg/slop-code-bench` not `basedlsg/iboga`; J8 was re-scoped after a failed first attempt; SAE work targets Llama-3.3-70B/l50 not Llama-3.1-8B/l19 after the NVIDIA transition). The merged, reviewed outcomes are the source of truth — see `next-steps.md` decision log. Do not re-dispatch these.

Each block below is the original dispatch prompt for `jules new`. Same pattern as silentvault J1-J5. After dispatch, pull patches with `jules remote pull --session <id>`. **Inspect every patch before applying.**

---

## J6 — Implement `--between-checkpoint-hook` in the SlopCodeBench fork

**Dispatch command:**

```bash
jules new --repo basedlsg/iboga "$(cat <<'EOF'
Add a `--between-checkpoint-hook` integration to our SlopCodeBench fork
at vendored path slop-code-bench/ (which mirrors SprocketLab/slop-code-bench
at commit 080922495aba9aedc4b7a6c80803bb5ffd301a49). Do NOT modify any
file under slop-code-bench/src/slop_code/metrics/ — those drive the
pre-registered DV and must remain bit-identical to upstream.

Where to add:
1. Extend src/slop_code/entrypoints/problem_runner/models.py RunTaskConfig
   with an optional field: between_checkpoint_hook: Optional[str] = None
   (path to an executable script).
2. Extend the CLI in src/slop_code/entrypoints/commands/run_agent.py to
   accept --between-checkpoint-hook <path>.
3. In src/slop_code/agent_runner/runner.py, after AgentRunner._run_checkpoint()
   finishes a non-first checkpoint and before the next checkpoint's
   get_task_for_checkpoint() is called, invoke the hook subprocess with
   the contract documented in projects/iboga/harness-validation.md
   "Proposed hook contract" block. Pass payload as JSON on stdin.
4. Capture the hook's stdout as prompt_prefix. If non-empty, modify
   get_task_for_checkpoint() to prepend prompt_prefix to the task string
   (separated by two newlines) before writing prompt.txt.
5. Add a no-op mode: if the hook script exits 0 with empty stdout, the
   prefix is empty and the checkpoint proceeds normally. This is "Arm 0"
   neutrality.

Contract for the hook subprocess (stdin JSON):
{
  "trajectory_id": "...",
  "model_id": "...",
  "problem_id": "...",
  "previous_checkpoint_name": "...",
  "current_checkpoint_name": "...",
  "previous_checkpoint_output_dir": "/abs/path",
  "previous_snapshot_dir": "/abs/path",
  "previous_diff_path": "/abs/path/diff.json",
  "prior_session_dir": "~/iboga-data/sessions/<trajectory-id>/"
}

The hook's stdout becomes the prompt prefix. Stderr is logged but not
forwarded into the agent.

Resume safety:
- If a checkpoint has already completed in a prior partial run, do NOT
  re-invoke the hook for that checkpoint. Use the existing resume
  machinery in AgentRunner.
- Persist hook outputs under the checkpoint output directory (e.g.
  hook_prefix.txt) so resumed runs reuse them deterministically.

Acceptance criteria:
1. Run with no --between-checkpoint-hook → behavior IDENTICAL to upstream
   on lite_under20 (mvvault + xjq). Reproduce upstream metrics within
   ±0.5 pp on a 1-problem smoke run.
2. Run with --between-checkpoint-hook=/usr/bin/true → identical to (1)
   (Arm 0 neutrality).
3. Run with a hook that echoes a fixed line → next checkpoint's
   prompt.txt contains that line as prefix.
4. Pass the existing test suite without modification.
5. ZERO changes under slop-code-bench/src/slop_code/metrics/.

Output: produce a patch against the vendored slop-code-bench/ tree. Open
a PR on basedlsg/iboga titled "J6: between-checkpoint hook for retrospective injection."
EOF
)"
```

**Estimated session time:** 30-60 min. **Estimated patch size:** ~150-250 lines.

---

## J7 — Write `scripts/iboga_runner.py` host-side wrapper

**Depends on:** J6 merged.

**Dispatch command:**

```bash
jules new --repo basedlsg/iboga "$(cat <<'EOF'
Write scripts/iboga_runner.py, the host-side launcher for an Iboga
trajectory. Reads from projects/iboga/prereg.md §7 and §8 for the
locked design; do not change anything in prereg.md.

CLI:
  python scripts/iboga_runner.py \
    --trajectory-id <hash> \
    --model <openrouter-slug> \
    --problem <slopcodebench-problem-id> \
    --arm A|B|C|0 \
    [--dry-run]

Behavior:
1. Resolve the assignment: arm A=Iboga AA, B=neutral, C=unstructured,
   0=hook-running-but-empty-output (pilot only). Reject anything else.
2. Look up the per-arm prompt template from projects/iboga/arm-templates.md.
   Templates are pinned by their content hash at projects/iboga/schemas/.
3. Create ~/iboga-data/sessions/<trajectory-id>/ if missing. This is
   the HOST persistence directory; it must NEVER be mounted into the
   SlopCodeBench Docker workspace. Add a guard: if the SlopCodeBench
   config's docker.extra_mounts contains anything under iboga-data,
   abort with a clear error.
4. Write a wrapper hook script at /tmp/iboga-hook-<trajectory-id>.sh
   that:
     a. Reads JSON from stdin per the J6 contract.
     b. Calls the OpenRouter API for the assigned model with the assigned
        arm's prompt template, passing the diff and corpus as input.
        Arms A/B use the locked JSON Schema with enum validation; if
        validation fails, retry up to 2x; if still failing, write an
        empty prefix and log a structured-output failure.
     c. Saves the full retrospective JSON to
        ~/iboga-data/sessions/<trajectory-id>/session-<checkpoint>.json
     d. Writes the prompt-prefix text to stdout (the next-checkpoint
        prefix). For Arm 0, stdout is always empty.
5. Invoke the SlopCodeBench fork's `slop-code run --between-checkpoint-hook
   /tmp/iboga-hook-<trajectory-id>.sh` with the assigned model and problem.
6. After completion, run scb-check on the final snapshot, save the
   verbosity/erosion/solve_rate to ~/iboga-data/sessions/<trajectory-id>/metrics.json.
7. With --dry-run, do everything except the actual LLM call — instead,
   call a stub that returns a fixed retrospective for inspection.

Requirements:
- Use OPENROUTER_API_KEY from environment. Fail early if unset.
- Cost accounting: write each OpenRouter response's usage block to
  ~/iboga-data/sessions/<trajectory-id>/cost-log.jsonl. Sum to
  ~/iboga-data/cost-total.json after each run.
- Hard kill if cumulative cost across all trajectories exceeds $900
  (the locked budget cap).
- Use stdlib + httpx + jsonschema. No new heavy dependencies.

Acceptance criteria:
1. Dry-run mode produces a session-N.json artifact with the stub content
   and emits a valid prompt-prefix for the hook.
2. Live mode (1 trajectory, 1 problem, mvvault, arm C) completes end to
   end and writes metrics.json with non-null verbosity/erosion/solve_rate.
3. Arm 0 mode runs the hook but writes empty stdout; metrics match a
   no-hook upstream baseline within ±2 pp.
4. iboga-data is never mounted into Docker; verify with a print of
   the resolved SlopCodeBench config's docker.extra_mounts.

Output: PR titled "J7: iboga_runner.py host-side wrapper" against basedlsg/iboga.
Include integration tests that run with --dry-run.
EOF
)"
```

**Estimated session time:** 90-120 min. **Estimated patch size:** ~300-450 lines.

---

## J8 — Write `scripts/collect_sae_activations.py` (Llama-3.1-8B + Goodfire SAE l19)

**Independent of J6/J7. Can run in parallel.**

**Dispatch command:**

```bash
jules new --repo basedlsg/iboga "$(cat <<'EOF'
Write scripts/collect_sae_activations.py for the exploratory mechanistic
arm of Iboga (see projects/iboga/prereg.md §4, H_M).

Purpose: take a trajectory's retrospective text(s), run them through
Llama-3.1-8B-Instruct, and capture the mean activation of a pre-locked
SAE feature set at layer 19 using Goodfire's open SAE.

Reference:
- Goodfire's open SAE on HuggingFace:
  Goodfire/Llama-3.1-8B-Instruct-SAE-l19
- Goodfire's inference docs:
  https://github.com/goodfire-ai/sparse-autoencoders
- Locked feature IDs: read from projects/iboga/sae-features.json
  (the file must exist; if missing or empty, fail with a clear error
  saying H_M needs to demote to exploratory-no-direction).

CLI:
  python scripts/collect_sae_activations.py \
    --trajectory-id <hash> \
    --retrospective-file ~/iboga-data/sessions/<trajectory-id>/session-K.json \
    [--gpu-id 0]

Behavior:
1. Load Llama-3.1-8B-Instruct locally (huggingface_hub; will require
   24+ GB VRAM or 4-bit quantization fallback).
2. Load Goodfire's SAE for layer 19 (Llama-3.1-8B-Instruct-SAE-l19).
3. Tokenize the retrospective text(s) from the session JSON.
4. Forward pass through the model, hooking layer 19's residual stream.
5. Pass the layer 19 activations through the SAE encoder.
6. For each pre-locked feature ID, compute the mean activation across
   all retrospective-generation tokens (excluding system/user prompt
   tokens; mark those positions in the input).
7. Save to ~/iboga-data/sae/<trajectory-id>/checkpoint-K.json with shape:
   {
     "trajectory_id": "...",
     "checkpoint": K,
     "model": "llama-3.1-8b-instruct",
     "sae_layer": 19,
     "n_tokens": ...,
     "features": [
       {"feature_id": 12345, "mean_activation": 0.42, "max_activation": 1.87},
       ...
     ]
   }
8. Add a --batch flag that processes all sessions for a given
   trajectory-id in one model load.

Requirements:
- Auto-fallback to 4-bit (bitsandbytes) if FP16 won't fit.
- Cache the SAE weights in ~/iboga-data/sae/.cache/ so repeat runs are fast.
- No edits to projects/iboga/sae-features.json (the locked feature list).
- No edits to anything under projects/iboga/slop-code-bench/.

Acceptance criteria:
1. Runs end-to-end on a single retrospective JSON.
2. Outputs a JSON file matching the schema above.
3. Re-runs use the cache, completing in <30s after first load.
4. Feature IDs in output match feature IDs in sae-features.json exactly.

Output: PR titled "J8: SAE activation collector for H_M" against basedlsg/iboga.
EOF
)"
```

**Estimated session time:** 90-120 min. **Estimated patch size:** ~200-300 lines.

**Note:** depends on `sae-features.json` being locked first (Week 4 task). Dispatch J8 ONLY after that file exists.

---

## J9 — Metric reproduction harness (5 baseline models × 5 problems × ±2 pp tolerance)

**Depends on:** J6 merged (needs the fork's hook infrastructure to not interfere with the no-hook reproduction).

**Dispatch command:**

```bash
jules new --repo basedlsg/iboga "$(cat <<'EOF'
Write scripts/reproduce_slopcodebench_baselines.py and the supporting
config to validate that our SlopCodeBench fork reproduces the upstream
published baseline numbers within ±2 percentage points. This is a
pre-lock gate per projects/iboga/harness-validation.md "Baseline
Reproduction Gate."

CLI:
  python scripts/reproduce_slopcodebench_baselines.py \
    --models <comma-separated OpenRouter slugs> \
    --problems <comma-separated problem IDs> \
    [--upstream-leaderboard <path-to-published-json>] \
    [--tolerance-pp 2.0]

Behavior:
1. For each (model, problem) pair, invoke the SlopCodeBench fork via
   `slop-code run` WITHOUT --between-checkpoint-hook. Use the upstream
   "just-solve" agent configuration with thinking=high.
2. Collect per-checkpoint metrics from the fork's outputs:
   solve_rate, erosion, verbosity. Compute slopes via OLS on (checkpoint_idx, value).
3. Pull published-baseline numbers from the upstream leaderboard (either
   from a local JSON dump of scbench.ai data, or scrape from
   scbench.ai/leaderboard.json if available; the upstream-leaderboard
   flag lets the user provide a path).
4. Compare fork-vs-upstream on each metric per (model, problem).
5. Output a markdown report at projects/iboga/harness-validation-results.md
   with a table:
   | model | problem | metric | upstream | fork | delta_pp | within_tol |
6. Exit code 0 if all (model, problem, metric) cells are within ±2 pp.
   Exit code 1 if any cell fails.

Default models (cheap subset for pre-lock gate):
- anthropic/claude-sonnet-4.5 (was in upstream paper)
- openai/gpt-5.2
- qwen/qwen3-32b
- meta-llama/llama-3.1-8b-instruct
- deepseek/deepseek-chat-v3-0324

Default problems:
- mvvault
- xjq
- (3 others from lite_under20 or its expansion)

Cost cap:
- Print estimated cost before running. Abort if estimate exceeds $50
  unless --confirm-spend is passed.
- Log actual cost to projects/iboga/harness-validation-cost.json.

Acceptance criteria:
1. The script runs to completion against at least one model × one problem.
2. The output report renders correctly in Obsidian.
3. The exit code matches the documented contract.
4. The cost log is written.

Output: PR titled "J9: baseline reproduction harness" against basedlsg/iboga.
EOF
)"
```

**Estimated session time:** 60-90 min. **Estimated patch size:** ~250-350 lines. **Estimated API cost:** ~$30-50 for a full 5×5 run.

---

## Dispatch order and gates

```
[basedlsg/iboga public]
        │
        ▼
   J6 (hook)  ────►  merge J6  ────►  J7 (runner)  ─────┐
        │                                                │
        │                                                ▼
        │                                            J9 (reproduction gate)
        │                                                │
        ▼                                                ▼
  sae-features.json locked (Week 4) ────►  J8 (SAE collector)
```

**Gate before J7/J9 dispatch:** J6 must merge AND pass acceptance criteria 1-3 (upstream behavior reproduced with no hook, Arm 0 neutral, fixed-prefix injection working).

**Gate before J8 dispatch:** `projects/iboga/sae-features.json` must be locked with a non-empty list of feature IDs.

---

## Manual review checklist for every Jules patch

Before applying any Jules patch with `jules remote pull --session <id> --apply`:

1. Read the full diff
2. Check NO file under `projects/iboga/slop-code-bench/src/slop_code/metrics/` is modified
3. Check NO file under `projects/iboga/prereg.md`, `arm-templates.md`, `failure-types.md`, `analysis-plan.R`, or `power-calc.R` is modified
4. Check the change is scoped to its task (J6 only touches hook plumbing; J7 only writes new scripts; etc.)
5. Run the acceptance-criteria smoke tests from the task prompt
6. Commit with `git commit -m "J<N>: <task summary> (Jules session <id>)"`
