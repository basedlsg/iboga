---
title: SlopCodeBench Study Notes (for Week 2 harness fork)
status: active
created: 2026-05-12
source_paper: arXiv:2603.24755
source_repo: github.com/SprocketLab/slop-code-bench
source_leaderboard: scbench.ai
tags: [iboga, slopcodebench, harness, study-notes]
---

# SlopCodeBench — Technical Brief for Harness Forking

Read of arXiv:2603.24755 + HTML version. **Source of truth: this file's section references against the paper at lock time.**

---

## Confirmed parameters

| Parameter | Value | Source |
|---|---|---|
| Problems | **20** | Abstract + Conclusion |
| Total checkpoints | **93** | Abstract |
| Models in their paper | **11** | Conclusion: "Across 11 models and 20 iterative problems" |
| Language tracks reported | **Python only** | §2 — "language-agnostic by design" but Python in reported runs |
| Best-agent solve rate | **17.2%** | Opus 4.6 |
| Workspace persistence | **Working dir only** | §3.1 |
| Docker isolation | **Fresh container per checkpoint** | §3.1 |

This matches the pre-reg. No revisions needed to the pre-reg numbers.

---

## Equations to implement / inherit

### Erosion (§2.3)

```
mass(f) = CC(f) × √SLOC(f)

Erosion = Σ_{f∈F, CC(f)>10} mass(f) / Σ_{f∈F} mass(f)
```

- `CC(f)` = cyclomatic complexity of function `f` (Radon convention)
- `SLOC(f)` = source lines of code for function `f`
- Threshold `CC > 10` follows the Radon "high complexity" threshold

**Implementation**: don't reimplement. Use SlopCodeBench's exported checkpoint field `erosion` unmodified. Repo inspection on 2026-05-12 found that this field is produced by `src/slop_code/metrics/checkpoint/driver.py`, which shells out to `scb-check==0.1.3`.

### Verbosity (§2.3, Eq. 4)

```
Verbosity = |{AST-Grep Flagged Lines} ∪ {Clone Lines}| / LOC
```

- AST-Grep rules detecting wasteful patterns
- Repo inspection correction: `scb-check==0.1.3` computes `verbosity = (clone SLOC ∪ ast-grep SLOC ∪ trivial-wrapper SLOC) / total SLOC`. The paper shorthand omits trivial wrappers.
- Clone-detection algorithm: exact tree-sitter AST-subtree hashing with normalized identifiers/literals, deterministic MD5 hash groups, default minimum 3 SLOC lines. Documented in `harness-validation.md`.

### Slope computation

The paper measures the *slope* of erosion and verbosity over checkpoints. Implementation detail (not specified in paper):
- OLS slope across checkpoint indices, or some other regression?
- Are checkpoints evenly spaced indices or actual time?
- Slope per problem, then averaged? Or pooled regression?

**Repo inspection result**: no upstream slope script found in the checkpoint export path. SlopCodeBench run summaries aggregate checkpoint `verbosity` and `erosion` as statistics including means. Iboga computes OLS slopes from per-checkpoint exported fields and checkpoint `idx`.

---

## Harness architecture (critical for Iboga hook insertion)

### Confirmed (§3.1)

- **Fresh Docker per checkpoint**: agent process, env, packages, shell history, agent session data all reset.
- **Workspace carryover**: ONLY the contents of the working directory persist between checkpoints.
- **Specification**: agent receives the spec for checkpoint `k+1` at the start of container `k+1`.

### Implication for Iboga retrospective injection

An earlier Iboga draft specified "out-of-workspace" retrospective text at `/tmp/iboga-*`. But Docker reset means `/tmp/` is **also wiped** between containers. The retrospective text must therefore be:

1. **Computed outside Docker** (on the host) between checkpoint `k` and `k+1`
2. **Persisted on the host** (e.g., `~/iboga-data/sessions/{trajectory}/{k}.json`)
3. **Injected into the agent's spec at checkpoint `k+1`** as part of the system/user prompt, NOT placed in the workspace

This is a substantive architectural decision. `prereg.md` §8 and §11 were updated on 2026-05-12 to reflect this: retrospective text lives in the agent's *prompt* for next checkpoint, not in any filesystem the workspace AST-Grep sees.

**Pre-lock contamination stance**: the intended design keeps retrospective text out of the workspace, but this is not treated as proven until runtime mount assertions and the Arm 0 no-op validation pass.

### Required harness modification

SprocketLab's harness has no documented intervention-hook surface. We need to:

1. Add a `--between-checkpoint-hook <script>` flag to their harness invocation
2. The hook receives: `(trajectory_id, checkpoint_k_workspace_dir, prior_diff)`
3. Hook computes retrospective via LLM call (Arm A / B / C prompt template)
4. Hook returns text to be prepended to checkpoint `k+1`'s agent prompt
5. Harness modified to accept prepended-prompt for the next agent invocation

Repo inspection correction: there is no top-level `runner/` directory. The insertion target is `src/slop_code/agent_runner/runner.py`, with CLI/config plumbing through `src/slop_code/entrypoints/commands/run_agent.py` and `src/slop_code/entrypoints/problem_runner/models.py`. **Allowed scope**: don't touch metric computation at all.

---

## Repo inspection (2026-05-12)

Pinned local clone: `projects/iboga/slop-code-bench/` at `080922495aba9aedc4b7a6c80803bb5ffd301a49`.

Local reproduction setup:

- `uv sync` completed on 2026-05-12.
- Managed problem catalog installed under `projects/iboga/.scbench/`.
- Catalog version: `v1.0`.
- Catalog commit: `4d38d300059667d57e43c31969bc455f5c338b52`.
- Catalog count: 36 problems.
- `configs/runs/lite_under20.yaml` resolves to `mvvault` (6 checkpoints, entry file `mvault`) and `xjq` (5 checkpoints, entry file `xjq`).
- Docker server `27.3.1` started successfully on 2026-05-12.
- `slop-code run --config configs/runs/lite_under20.yaml --dry-run --no-live-progress` reaches credential resolution and stops before agent execution because `ANTHROPIC_API_KEY` is missing.

Metric findings:

- No `metrics/verbosity.py` and no metric-level `metrics/erosion.py` exist at the pinned commit.
- `src/slop_code/metrics/checkpoint/driver.py` calls `uvx scb-check check --report --include-all <checkpoint>/snapshot`.
- `uvx scb-check --version` resolved `0.1.3`.
- Inspected PyPI wheel `scb_check-0.1.3-py3-none-any.whl`, SHA-256 `f13040c8ca8f57b8dc8137692c37e0f181fe55867691dfe6a5b8a79d2513f50f`.
- `scb-check` package metadata points to `github.com/gabeorlanski/scb-check`.
- `scb-check` skips symlinked files/directories during traversal and only walks `*.py` under the supplied snapshot root.

Hook findings:

- CLI command: `src/slop_code/entrypoints/commands/run_agent.py`.
- Config object: `src/slop_code/entrypoints/problem_runner/models.py::RunTaskConfig`.
- Checkpoint loop and prompt rendering: `src/slop_code/agent_runner/runner.py`.
- Prompt assembly: `get_task_for_checkpoint()` writes `prompt.txt` and returns the string passed to `agent.run_checkpoint(task)`.
- Best insertion target: invoke hook in `AgentRunner._run_problem()` for `idx > 0` after checkpoint k finishes and before checkpoint k+1 prompt rendering; pass returned prefix into `get_task_for_checkpoint()`.
- Prior checkpoint diff file is `diff.json`.
- Default Docker environment mounts a temp workspace read-write at `/workspace` and has no configured `extra_mounts`; static assets mount read-only under `/static`.

---

## What was NOT specified (action items for repo inspection)

Before pre-reg lock, must inspect:

- [x] Metric implementation path — actual path is SlopCodeBench checkpoint driver plus `scb-check==0.1.3`
- [x] Clone-detection algorithm — deterministic tree-sitter AST-subtree hashing
- [x] Erosion formula — `cyc_complexity * sqrt(sloc)`, high complexity `> 10`
- [x] Slope computation — no upstream checkpoint-export slope; Iboga computes slopes from exported checkpoint fields
- [x] Runner equivalent — `src/slop_code/agent_runner/runner.py`
- [x] Docker/session implementation and default mount list
- [ ] Per-checkpoint specification format — what does the agent receive at checkpoint `k+1`? File path? Text in stdin? Env var?
- [ ] `Dockerfile` — what Python version, what packages preinstalled, what user permissions
- [ ] Existing logs/output format — how do their 11 baselines store per-checkpoint results? Reproducing their leaderboard numbers requires reading their existing result JSON format.

---

## Top-line baseline numbers (for Week 2 reproduction check)

Per the HTML version's Table (paraphrased; verify against repo at validation time):

| Model | Strict solve % |
|---|---|
| Opus 4.6 | 17.2 |
| GPT 5.4 | 11.8 |
| Opus 4.5 | 10.9 |
| GPT 5.1 Codex Max | 10.8 |
| GPT 5.2 | 10.8 |
| Sonnet 4.6 | 8.5 |
| GPT 5.3 Codex | 9.7 |
| GPT 5.2 Codex | 9.7 |
| Sonnet 4.5 | 5.4 |
| GLM 4.7 | 4.3 |
| GPT 5.3 Spark | 5.4 |

**Reproduction check (Week 2)**: pick 5 of these. Run their unmodified harness on 5 problems each. Verify our forked metric scripts produce solve rates within ±2 percentage points.

**Iboga model selection**: Claude Opus 4.7 (newer than their Opus 4.6), Qwen2.5-32B, Llama-3.1-8B, DeepSeek-Coder-V3. **None of our 4 models are in the SlopCodeBench leaderboard.** This means we cannot directly compare our untreated-control numbers against the leaderboard — we run our own untreated baselines as Arm C (unstructured) and treat that as our local control.

This is fine for the pre-registered design (paired-within-trajectory comparisons across arms), but it means we cannot claim "our intervention beats the SlopCodeBench leaderboard." That claim was never made. We measure *differential* arm effect within (model, problem) pairs.

---

## The future-work paragraph that validates the Iboga niche

From the Conclusion (quoted under fair use, <25 words):
> "interventions that enforce structural discipline across checkpoints... remain untested"

This is the gap Iboga occupies. The paper authors explicitly flag it as their open question.

**Implication for the SprocketLab coordination email (Week 7)**: open with "We are implementing the intervention-class your Conclusion §6 flags as untested." This signals respect for their declared territory.

---

## Risk flags identified during this read

1. **Paper shorthand under-specifies verbosity**. `scb-check==0.1.3` includes trivial-wrapper SLOC in the verbosity union, not only clone and ast-grep lines. Mitigation: pre-reg now names the package-level exported field and pins the package version/hash.

2. **Slope computation not in upstream checkpoint export path**. Iboga must compute OLS slopes from `checkpoint_results.jsonl` using checkpoint `idx`. Mitigation: analysis script and pre-reg now state this explicitly.

3. **The hook surface doesn't exist**. We're modifying a benchmark harness. There's a risk that our fork's "hook between checkpoints" subtly changes timing/scheduling and shifts measured metrics independent of intervention content. Mitigation: include a "Arm 0 — no retrospective at all, but with the empty hook running" as a sanity-check arm during pilot (Week 7). If Arm 0 matches no-hook baseline on all metrics, the hook is benign.

4. **Their Docker images may be tied to specific Python versions / package pins**. Test environment must match.

5. **Cost on their 20 problems × 93 checkpoints**: at ~$0.10-0.30 per Opus 4.7 checkpoint, full Opus arm = $200-560. Our budget allocates $280 for Opus. **Tight.** May need to reduce to 16 of 20 problems for Opus arm only.

---

## Updates pushed back into the pre-reg before lock

Status as of 2026-05-12:

1. **§8 Treatment specifications**: done. Retrospective lives in the prompt for checkpoint k+1, not in workspace or `/tmp/`.
2. **§10 Stopping rules**: done. Arm 0 sanity-check arm added; if the hook itself shifts metrics, abort.
3. **§11 Pre-Lock Validation**: done. Explicit subtasks updated to match the actual repo layout and `scb-check==0.1.3` metric package.
4. **§14 Solo Execution Plan budget**: unresolved risk. Do not silently reduce Opus to 16/20 problems; that changes the locked design and requires a pre-lock revision or post-lock OSF amendment.
5. **§16 External Coordination**: done. Opening sentence drafted in `sprocketlab-email.md`.

---

## Decision: are 20 problems enough?

Yes. With 4 models × 20 problems × 3 arms = 240 trajectories, the paired-within-(model,problem) design gives 80 paired observations per arm contrast. Power calc already validates this at d=0.4, α=0.025 → 0.92 power.

If Opus drops to 16 problems → 64 paired observations for Opus arm contrasts. Mixed-effects model in §9 absorbs the imbalance.

---

## Next read

Continue repo validation:
- Docker/session implementation and mount list
- Existing leaderboard/result JSON output format
- One cheap no-treatment baseline run after provider credentials are available
- 5-model × 5-problem reproduction gate

Append any further repo-level findings to `## Repo inspection (2026-05-12)`.
