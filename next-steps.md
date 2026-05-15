---
title: Iboga — Pre-Lock Checklist
status: active
created: 2026-05-12
lock_target: 2026-07-01
submission_target: 2026-09-25
tags: [iboga, prereg, checklist]
---

# Pre-Lock Checklist — Today → 2026-07-01

**Goal**: complete every item below before posting `prereg.md` to OSF. No treatment trajectories run before lock.

Today: **2026-05-13**. Lock target: **2026-07-01**. That's **7 weeks of pre-lock work**.

---

## Week 1 — May 12-18 — Foundations

- [x] Create `github.com/basedlsg/iboga` repo (MIT license)
- [x] Fork SlopCodeBench: `gh repo fork SprocketLab/slop-code-bench`. Pin upstream commit hash in `prereg.md` metadata.
- [x] Install pinned SlopCodeBench clone dependencies locally with `uv sync`; cache kept under `projects/iboga/.uv-cache/`.
- [x] Install managed problem catalog locally under `projects/iboga/.scbench/`; pinned catalog `v1.0` at `4d38d300059667d57e43c31969bc455f5c338b52`.
- [x] Start Docker Desktop / Docker daemon before any SlopCodeBench checkpoint run. Docker server `27.3.1` available after `open -a Docker` on 2026-05-12.
- [x] Verify a non-Anthropic dry-run route. `uv run slop-code run --config configs/runs/lite_under20.yaml --agent gemini --model gemini_auth/gemini-2.5-flash-lite --dry-run --no-live-progress` passes credential resolution and previews `mvvault` + `xjq` on 2026-05-13.
- [x] Build Gemini SlopCodeBench Docker image. After Docker Desktop disk cleanup, `slop-code:python3.12` and `slop-code:gemini-0.41.2-python3.12` built successfully on 2026-05-13.
- [x] Start actual no-treatment Gemini validation on `xjq`. Checkpoint 1 completed/evaluated; checkpoint 2 hit Gemini Code Assist capacity errors (`429`, `MODEL_CAPACITY_EXHAUSTED`) after a long loop and was stopped manually before the one-hour timeout.
- [ ] Export `OPENROUTER_API_KEY` in the run shell or direnv before OpenRouter-backed validation. Current shell has `OPENROUTER_API_KEY` unset.
- [x] Add/test local SlopCodeBench model configs for unambiguous OpenRouter routes: Opus 4.7, Qwen2.5-32B, and Llama-3.1-8B reach `OPENROUTER_API_KEY` credential resolution on 2026-05-13.
- [ ] Resolve the exact DeepSeek model slug before lock. Do not silently substitute DeepSeek V3 for `DeepSeek-Coder-V3` without a pre-lock correction.
- [ ] Create OSF account at osf.io (use flareondon@gmail.com). No pre-reg posted yet.
- [ ] Read SlopCodeBench paper in full (arXiv 2603.24755), take notes on: exact metric definitions in §3.2, the agent-loop hook surface, reproduction protocol.
- [ ] Set up RunPod or Vast.ai account for SAE work later (A10G access).
- [ ] **Decision point**: confirm budget cap at $900 by reviewing current finances.

## Week 2 — May 19-25 — Harness Reproduction

- [x] Clone SlopCodeBench fork locally under `projects/iboga/slop-code-bench/` and pin `080922495aba9aedc4b7a6c80803bb5ffd301a49`.
- [x] Inspect metric implementation paths. Finding: no `metrics/verbosity.py` or metric-level `metrics/erosion.py`; exported composites come from `src/slop_code/metrics/checkpoint/driver.py` invoking `scb-check==0.1.3`.
- [x] Inspect runner insertion surface. Finding: hook belongs in `src/slop_code/agent_runner/runner.py` plus run CLI/config plumbing, not a top-level `runner/` directory.
- [x] Inspect default Docker/session mount path. Finding: default environment mounts only a temporary workspace read-write at `/workspace` plus read-only static assets; Iboga still needs an explicit assertion against spec/runtime mounts that include `~/iboga-data`.
- [ ] Run their published baseline on 5 models × 5 problems (out of the 20).
- [ ] Complete a no-treatment run on `configs/runs/lite_under20.yaml` (`mvvault`, `xjq`) through OpenRouter after `OPENROUTER_API_KEY` is exported, or retry Gemini later with explicit step limits.
- [ ] Verify forked harness reproduces upstream numbers within ±2 percentage points on `erosion_slope` and `verbosity_slope`. **If fail → pre-reg blocked until harness debugged.**
- [ ] Write `iboga-runner.py` — wraps SlopCodeBench harness with retrospective hook between checkpoints. Host-side session logging goes to `~/iboga-data/sessions/{trajectory-id}/`; nothing is written into the checkpoint workspace.
- [ ] **Pivotal verification**: confirm `~/iboga-data/sessions/*` is not mounted into the Docker workspace and cannot be traversed by `scb-check`, AST-Grep, radon, or clone detection. Run no-hook baseline vs Arm 0 no-op hook → must produce identical metrics. Document in `iboga/harness-validation.md`.

## Week 3 — May 26 - June 1 — Prompt Templates

- [ ] Write Arm A (AA vocabulary) prompt template. Use provider-neutral JSON Schema enum validation; if Opus is routed through OpenRouter, use the Anthropic-compatible OpenRouter adapter rather than a direct Anthropic key. Test against the locked Opus 4.7 route on a synthetic diff.
- [ ] Write Arm B (vocabulary-neutral) prompt template. Same structure, swap vocabularies.
- [ ] Write Arm C (unstructured) prompt template. Same Berg induction, same corpus, free-form retrospective content inside a single structured-output wrapper, with ≤2000 token cap.
- [ ] Validate token budgets: Arm A and Arm B mean output tokens within ±15%; record Arm C distribution without padding. **Token-budget documentation in `iboga/arm-token-budget.md` — locked at pre-reg.**
- [ ] Test all three arms on a single SlopCodeBench problem with the locked Opus 4.7 route. Sanity check the output structure.
- [ ] Build `iboga/arm-assignment.json` from `iboga/arm-assignment-spec.md` — deterministic SHA256-based per-trajectory arm mapping. Commit cryptographic hash to git.

## Week 4 — June 2-8 — SAE Feature Catalog

- [ ] Download Goodfire's `Llama-3.1-8B-Instruct-SAE-l19` from HuggingFace.
- [ ] Pull full feature catalog. Filter by label-string match against `{deception, roleplay, identity, self-reference, first-person narrator, confession, apology, admission}`.
- [ ] Top-20 features by label-match score. Lock IDs in `iboga/sae-features.json`. **Check filter result count**: if <5 → demote H_M to exploratory-no-direction; if >50 → narrow filter further. Document decision in `iboga/sae-features-decision.md`.
- [ ] Write SAE activation collection script: takes a trajectory's retrospective text, runs Llama-3.1-8B-Instruct, captures mean activation of locked features per token position. Test on a single retrospective.

## Week 5 — June 9-15 — Power Analysis + Statistical Plan

- [ ] Install R + `WMWssp` package locally. `R`/`Rscript` were not on PATH in this shell on 2026-05-12.
- [ ] Compute power for: (a) paired Wilcoxon at α=0.025 one-tailed, d=0.3, 0.4, 0.5 across n=60, 70, 80, 90; (b) TOST non-inferiority at α=0.025, Δ=−0.05.
- [ ] Commit `iboga/power-calc.R` and `iboga/power-calc-output.txt`.
- [ ] Draft preliminary analysis script `iboga/analysis-plan.R`: ingests `metrics/*.json` from all 240 trajectories, applies Holm-Bonferroni, outputs the four hypothesis tests.
- [ ] **Pre-commit analysis script before pre-reg lock.** No data-driven analysis revisions allowed.

## Week 6 — June 16-22 — Annotator Recruitment

- [ ] Identify candidate annotator (programmer, ≥2 yrs Python, no AA literature familiarity, no relationship to candidate's research). Outreach via [Hacker News Who's Hiring / Upwork / personal network].
- [ ] Pay $200 retainer for ~5 hours work in August. Confirm availability for the capped recurrence audit sample (~24 pairs).
- [ ] Draft annotator rubric document (`iboga/annotator-rubric.md`): neutral failure-type taxonomy (not AA, not neutral arm vocab — third post-hoc taxonomy authored before annotator engagement).
- [ ] Lock failure-type taxonomy in `iboga/failure-types.json` (closed list, 8-12 categories).

## Week 7 — June 23 - July 1 — Final Lock

- [ ] **External coordination email**: send copy of pre-reg to SprocketLab PIs (SlopCodeBench authors). Subject: "Pre-registered extension to SlopCodeBench: retrospective-protocol intervention layer." No collaboration sought; transparency only.
- [ ] Run small-N pilot: 2 problems × 4 models × 3 arms = 24 trajectories. **Budget: $50.** Pure dry-run. Pilot data NOT counted in final results.
- [ ] If pilot reveals harness issues → fix and re-pilot. If pilot reveals SAE issues → demote H_M or fix.
- [ ] **Final pre-reg lock**: post `prereg.md` to OSF. Update `frontmatter.osf_doi` in this file and `prereg.md`. Change `status: draft` → `status: locked`.
- [ ] Commit final repo state, tag `v0.5-pre-reg-lock`.

---

## Main Run Phase — July 1 → August 23

8 weeks of main-experiment trajectories. ~30 trajectories per week, batched overnight.

| Week | Trajectories | Models |
|---|---|---|
| Jul 1-7 | 24 (1 model × 8 problems × 3 arms) | Claude Opus |
| Jul 8-14 | 24 | Qwen2.5-32B |
| Jul 15-21 | 24 | Llama-3.1-8B |
| Jul 22-28 | 24 | DeepSeek-Coder-V3 |
| Jul 29 - Aug 4 | 48 (second-half problems) | Claude Opus + Qwen |
| Aug 5-11 | 48 | Llama + DeepSeek |
| Aug 12-18 | 24 | replay / debugging buffer |
| Aug 19-23 | 24 | final clean runs |

**Operator role during main run**: monitor only. Arm assignment is automated. Check daily cost. No look at per-trajectory vocabulary until analysis time.

---

## Post-Run Phase — August 24 → September 25

| Week | Date range | Activity |
|---|---|---|
| Aug 24-30 | Annotator pass on 20% audit sample → κ check |
| Aug 31 - Sep 6 | SAE feature activation pass on all Llama-3.1-8B trajectories |
| Sep 7-13 | Run analysis script. Lock primary and secondary results. |
| Sep 14-20 | Paper drafting. Target 8-page workshop format. |
| Sep 21-25 | Final polish, submit. |

---

## Living Decision Log

When you hit a fork, log it here. **No silent decisions after pre-reg lock.**

- 2026-05-12 — Substrate decision locked: SlopCodeBench, not Nemo. (Reviewers converged.)
- 2026-05-12 — Models locked: Opus + Qwen2.5-32B + Llama-3.1-8B + DeepSeek-Coder-V3. Dropped Llama-3.3-70B from v0.5-draft0 (solo compute constraint).
- 2026-05-12 — H_M demoted to exploratory-with-direction (was confirmatory in v0.5-draft0). Reason: no SAE co-author per Carlos decision.
- 2026-05-12 — **Architecture revision after SlopCodeBench paper read** (`slopcodebench-study.md`): retrospective text moved from `/tmp/iboga-*` (Docker-wiped) to `~/iboga-data/sessions/{trajectory}/{k}.json` on host. Retrospective injects into next checkpoint's *agent prompt*, not workspace. Added "Arm 0" sanity-check arm to pilot to verify the hook itself doesn't shift metrics. Pre-reg §8, §11 updated.
- 2026-05-12 — **Confirmed niche**: SlopCodeBench Conclusion explicitly flags "interventions that enforce structural discipline across checkpoints remain untested" as open question. SprocketLab coordination email (Week 7) opens with this acknowledgement.
- 2026-05-12 — **Pre-lock consistency corrections**: Week 2 checklist updated to host-side `~/iboga-data/sessions/*` architecture; tertiary recurrence audit capped at 120 candidate pairs with 24 annotated pairs to match the $200 / ~5-hour annotator budget; mixed-effects sensitivity check changed from `log(erosion_slope)` to raw `erosion_slope` because slopes can be zero or negative; primary analysis script now requires raw H1a and H1b p-values to both pass α=0.025, while still reporting Holm-adjusted p-values.
- 2026-05-12 — **Structured-output portability fix**: prompt schemas are canonical JSON Schema. Claude uses an Anthropic-compatible structured-output adapter through the selected route; non-Anthropic models use provider adapters where available or JSON-only output with local validation/retry. Arm C gets a single structured wrapper field so transport shape is explicit without adding structure/vocabulary constraints.
- 2026-05-12 — **Pre-lock scaffold files created**: draft JSON schemas added under `schemas/`; `arm-token-budget.md`, `sae-features-decision.md`, and `annotator-rubric.md` created as lock-time documentation targets. Token-budget checklist corrected to A/B equivalence plus Arm C documentation, not all-arm output matching.
- 2026-05-12 — **GitHub setup complete**: created/verified `basedlsg/iboga`, forked `SprocketLab/slop-code-bench` to `basedlsg/slop-code-bench`, and pinned upstream HEAD `080922495aba9aedc4b7a6c80803bb5ffd301a49` in `prereg.md` and `harness-validation.md`.
- 2026-05-12 — **SlopCodeBench repo inspection correction**: pinned local clone at `projects/iboga/slop-code-bench/`. There is no `metrics/verbosity.py` or metric-level `metrics/erosion.py` at the pinned commit. Production checkpoint exports invoke `uvx scb-check check --report --include-all <snapshot>` from `src/slop_code/metrics/checkpoint/driver.py`; inspected `scb-check==0.1.3` and pinned wheel SHA-256 `f13040c8ca8f57b8dc8137692c37e0f181fe55867691dfe6a5b8a79d2513f50f`.
- 2026-05-12 — **DV operationalization correction before lock**: `verbosity` is the union of clone SLOC, ast-grep SLOC, and trivial-wrapper SLOC divided by total SLOC; `erosion` is high-CC mass share with `CC > 10`; slopes are computed by Iboga from per-checkpoint exports rather than by an upstream slope script. `solve_rate` is solved checkpoints divided by expected checkpoints, matching SlopCodeBench `pct_checkpoints_solved / 100`.
- 2026-05-12 — **Hook insertion target identified**: add hook config through `RunTaskConfig`; invoke in `AgentRunner._run_problem()` after checkpoint k finishes and before checkpoint k+1 prompt rendering; prepend returned text in `get_task_for_checkpoint()`. Metrics remain untouched.
- 2026-05-12 — **Runtime isolation inspection, code-level**: default SlopCodeBench Docker sessions use a temporary workspace mounted read-write at `/workspace`; default Python Docker config has no `extra_mounts`; static assets mount read-only under `/static`. Remaining lock gate is an Iboga-side assertion that neither spec-level nor runtime mounts include `~/iboga-data`, plus Arm 0 no-op validation.
- 2026-05-12 — **Local reproduction setup**: `uv sync` completed in the local SlopCodeBench clone; managed problem catalog installed at `projects/iboga/.scbench/`, catalog `v1.0` commit `4d38d300059667d57e43c31969bc455f5c338b52`; `lite_under20` resolves to `mvvault` and `xjq`; Docker started successfully; default upstream dry run reaches credential resolution and stops before agent execution because it uses `anthropic/sonnet-4.5` and no direct Anthropic key is configured. Superseded as current route by the 2026-05-13 provider-routing correction below.
- 2026-05-13 — **Provider-routing correction**: no Anthropic key will be used. SlopCodeBench already supports `openrouter` via `OPENROUTER_API_KEY` and `gemini_auth` via `~/.gemini/oauth_creds.json`. Gemini CLI OAuth dry-run passes with `--agent gemini --model gemini_auth/gemini-2.5-flash-lite`; OpenRouter dry-run is blocked only because `OPENROUTER_API_KEY` is not exported in this shell. Meta Llama Developer docs require authenticated portal access; provider support must be added and logged before lock if used for the Llama-3.1-8B trajectory route.
- 2026-05-14 — **Tool-stack role clarification (preserving original silentvault plan)**: OpenRouter is the trajectory-model route; Gemini CLI is the free validation route; Jules is the engineering coordinator for J6-J10 coding tasks (hook implementation, `iboga_runner.py`, SAE activation collector, metric reproduction harness, DeepSeek slug resolution) — same way silentvault used Jules for J1-J5. Jules is in scope as engineering helper, not as a trajectory provider; the prior "Jules out of scope" phrasing was too restrictive and is superseded. See `provider-routing.md` for the full task list. Jules dispatch starts once `basedlsg/iboga` is public on GitHub and connected to Jules.
- 2026-05-14 — **DeepSeek slug resolved**: verified against `https://openrouter.ai/deepseek` that "DeepSeek-Coder-V3" does NOT exist as an OpenRouter slug. Replaced with `deepseek/deepseek-chat-v3-0324` (canonical V3 chat, $0.20/$0.77 per M tokens, 164K context, fits $30 arm budget). Updated `prereg.md` §7, `README.md`, `handoff-prompt.md`. Vendor diversity preserved. J10 (DeepSeek slug resolution Jules task) is now CLOSED.
- 2026-05-14 — **All 4 OpenRouter slugs HTTP-200 verified**. Opus 4.7, Llama-3.1-8B-Instruct, DeepSeek chat v3-0324 all returned `OK` reply tokens against the live API. `qwen/qwen2.5-32b-instruct` returned HTTP 404 ("No endpoints found"). OpenRouter's Qwen2.5 only has the 72B variant; the 32B exists only in the Qwen3 generation. **Locked the 2nd model to `qwen/qwen3-32b`** (32.8B dense, instruct-tuned, $0.08/$0.28 per M tokens, 41K context). Decision rationale: preserves Alibaba vendor diversity (NeurIPS W11), preserves ~32B size class, 8× cheaper than the originally-planned 32B Qwen2.5 ($0.66/$1.00), context window comfortably handles SlopCodeBench checkpoints (median ~5-15K). Updated `prereg.md` §7, `README.md`, `handoff-prompt.md`, `jules-tasks.md`. **All 4 trajectory-model slugs now verified live**.
- 2026-05-14 — **J6 dispatched to Jules**: `jules new --repo basedlsg/slop-code-bench` (stdin-piped prompt from `jules-tasks.md` J6 with path adjustments for fork-root rather than vendored-path). Session: `https://jules.google.com/session/10172013158850380825`. Acceptance criteria locked: identical upstream behavior with no hook, Arm 0 neutrality with `/usr/bin/true` hook, fixed-prefix injection working, zero changes under `src/slop_code/metrics/`. Async; pull patch when complete.
- 2026-05-13 — **Local SlopCodeBench model-config patch**: added `opus-4.7-openrouter.yaml`, `qwen2.5-32b-instruct.yaml`, and `llama-3.1-8b-instruct.yaml` in the local SlopCodeBench fork clone. All three dry-run probes reach OpenRouter credential resolution. DeepSeek remains unresolved because current docs expose DeepSeek V3 variants, not an exact `DeepSeek-Coder-V3` slug.
- 2026-05-13 — **Gemini Docker build gate passed**: `uv run slop-code docker build-agent configs/agents/gemini.yaml configs/environments/docker-python3.12-uv.yaml` initially failed due Docker Desktop storage exhaustion during apt/Rust install. Pruned Docker build cache, stopped containers, and unused images; retry built `slop-code:python3.12` and `slop-code:gemini-0.41.2-python3.12`.
- 2026-05-13 — **Actual no-treatment Gemini validation partial**: started `xjq` only using Gemini CLI OAuth and stock `just-solve`. Checkpoint 1 completed/evaluated with no infrastructure failure and cost `$0.005402`; checkpoint 2 entered a long loop and then hit Google Code Assist capacity errors (`429`, `MODEL_CAPACITY_EXHAUSTED`). Stopped manually before the one-hour timeout. This validates the container/auth path but not full baseline reproducibility.
- _Add entries below as decisions accrue._

---

## What can derail this (and what to do)

| Failure mode | Fallback |
|---|---|
| SlopCodeBench harness fork fails to reproduce upstream baselines | Investigate; if structural, abandon SlopCodeBench → switch to METR HCAST subset (smaller, but reproducible) |
| SAE feature filter yields <5 features | H_M drops to exploratory-no-direction. Paper still ships. |
| Annotator κ < 0.7 | Tertiary DV (recurrence) → descriptive only. Primary/secondary unaffected. |
| API spend approaches $900 before main-run completion | Pause before the next batch. If before OSF lock, revise budget/design explicitly; if after lock, halt and file OSF amendment before any model-list or sample-size change. |
| Pilot reveals retrospective text contamination | Hard stop. Fix isolation. Re-pilot. Slip lock to mid-July; submit to NeurIPS SafetyXAI (October) instead of ICLR. |
| Carlos burnout (Likert ≥4/5 two weeks straight) | Pause for 1 week, reassess. Don't push through. |

---

## What to do TODAY

1. Export `OPENROUTER_API_KEY` in the shell that will launch SlopCodeBench; Gemini CLI OAuth is validated but capacity-limited today.
2. Create OSF account at osf.io using `flareondon@gmail.com`.
3. Start a no-treatment baseline reproduction run on `configs/runs/lite_under20.yaml`; do not use any treatment prompt.
4. Resolve the DeepSeek exact slug and either correct the pre-reg label before lock or add the matching local SlopCodeBench model config.
5. Once `basedlsg/iboga` is public on GitHub, dispatch **J6** to Jules: implement `--between-checkpoint-hook` per the contract in `harness-validation.md`. Jules tasks J6-J10 are listed in `provider-routing.md` under "Jules engineering tasks." Same pattern as silentvault J1-J5: write the prompt, send via `jules new --repo basedlsg/iboga "..."`, pull patch via `jules remote pull --session <id>`, review, apply.
5. Do not begin treatment trajectories before OSF lock.

**The pre-reg is drafted. The work is in the validation steps before lock.**
- 2026-05-14 — **H_M feature-selection methodology update**: Goodfire's open SAE release (`Llama-3.1-8B-Instruct-SAE-l19`) provides weights but NOT feature labels (Ember SDK that holds labels is archived; `goodfire-ai/goodfire-sdk` is public-archived). The pre-reg's original label-string-match filter was not executable from public artifacts. **Replaced with probe-prompt-based selection**: author 50 self-referential + 50 control prompts (locked + hashed at pre-reg), measure each SAE feature's activation ratio (self/control), lock top-20 by ratio. This is methodologically tighter (operational definition of "self-reference feature," no third-party label dependency) and removes the deprecated-service risk. Updated `prereg.md` §4 and §11.7. New pre-lock artifact: `iboga/sae-probe-corpus.json` (to be authored before lock). Decision rationale also added inline in prereg.
- 2026-05-14 — **Problem-set expanded 20 → 36, arm-assignment.json generated and hash-pinned**. SlopCodeBench's full v1.0 catalog has 36 well-formed problems (`cfgpipe` ... `xjq`); v0.5-draft0's plan of 20 was an underspecified subset never selected because the paper didn't enumerate which 20. Decision: use all 36. Implications: 4 × 36 × 3 = **432 trajectories** (was 240); **144 paired observations per arm contrast** (was 80); power at d=0.4 increases from 0.92 to ~0.99. Generated `arm-assignment.json` deterministically via `scripts/generate_arm_assignment.py --assignment-seed iboga-v0.5-lock-2026-07-01-placeholder`. SHA-256: `7adb28f7a74ea34e128351e2f62f47073f612d64c46ca6c3891c8c478d4f7dda`. Updated generator defaults to the locked OpenRouter slugs. Power calc and budget revision pending.
- 2026-05-14 — **Live baseline run launched**: `opencode + openrouter/llama-3.1-8b-instruct` on `mvvault`, no hook. Background. Validates the OpenRouter route end-to-end with the locked Llama-3.1-8B slug. Logs at `/tmp/iboga-baseline-llama.log`. Expected wall-clock 20-60 min, cost ~$0.10.
- 2026-05-14 — **Llama-3.1-8B + opencode baseline test: PARTIAL FAILURE**. `mvvault` checkpoint 1 succeeded ($0.0008, 165s, 2 steps). Checkpoint 2 errored at step 4 ("OpenCode error: unknown OpenCode error" — opencode's message parser rejected the model's output after 1314 generated tokens). 1/2 checkpoints solved. Full output dir: `slop-code-bench/outputs/lite_under20_runs/llama-3.1-8b-instruct_1.0.134_high_just-solve/20260514T1818/`. **Real risk**: Llama-3.1-8B may not be reliably trajectory-capable with opencode at the 4 steps × 60K-token-context scale. Possible mitigations: (a) accept higher exclusion rate and rely on the 10% cap; (b) switch trajectory model #3 to Llama-3.3-70B (more capable, ~2x cost ~$216/108 trajectories); (c) try a different agent (claude_code requires `claude` binary, gemini requires Gemini CLI — both not OpenRouter-routed, so neither fits); (d) try Qwen3-8B for trajectories + keep Llama-3.1-8B only for SAE work, adding a 5th model. Pre-lock decision pending Week 2 broader reproduction. SAE work is unaffected — Goodfire's open SAE for Llama-3.1-8B-Instruct can run on retrospective text from ANY trajectory model.
- 2026-05-14 — **J8 dispatched to Jules**: `https://jules.google.com/session/2376809178617050983`. Writes `scripts/select_sae_features.py` (probe-corpus-based feature selection, locks `sae-features.json`) and `scripts/collect_sae_activations.py` (per-trajectory activation collection using locked features). Both target basedlsg/iboga.
- 2026-05-15 — **J6 COMPLETED + merged**. Pulled Jules session 10172013158850380825 patch: 6 files (models.py, runner.py, run_agent.py, problem_runner/models.py, worker.py, new test). Reviewed: zero changes under `src/slop_code/metrics/` (reproducibility constraint holds). Hook logic correct — idx>0 only, JSON stdin, stdout→prompt-prefix, empty-stdout = Arm-0-neutral, prefix persisted to hook_prefix.txt. **One reviewer fix applied**: Jules wrote `previous_diff_path` as `diff.patch`; corrected to `diff.json` (the actual `common.DIFF_FILENAME`, verified in reporting.py:485). Test suite: 417 pass, J6's own hook test passes, 2 pre-existing `resume_integration_test.py` Docker-exec flakes unrelated to the hook. Merged `iboga/openrouter-model-configs` + `iboga/j6-between-checkpoint-hook` into basedlsg/slop-code-bench main (commit fee78b1).
- 2026-05-15 — **J8 (first dispatch) FAILED** — Jules produced no diff. Likely the two-script scope + Goodfire SAE loader (poorly documented) was unresolvable. **Re-dispatched as a tighter single-script task**: `scripts/select_sae_features.py` only, with a `--self-test` mode (synthetic SAE, CPU-only, <30s) so the aggregation/ranking/output pipeline is verifiable without a GPU, and an explicit sae_lens-first / Goodfire-safetensors-fallback loader strategy. Session 6901570842350401820. The activation-collection script becomes a separate later task.
- 2026-05-15 — **J7 dispatched**: `scripts/iboga_runner.py` host-side trajectory launcher. Session 2598946940364520975. Uses the merged J6 `--between-checkpoint-hook` contract. Includes CPU-only `--dry-run` mode for all 4 arms, the `~/iboga-data` mount-guard, and the $900 cost-cap hard-stop. Targets basedlsg/iboga.
- 2026-05-15 — **Probe corpus token-level length-match verified**. tiktoken cl100k_base BPE pass: self_referential mean 40.7 tok, control mean 46.0 tok, ratio 0.886 — within the pre-registered ±15% tolerance (11.4% gap), so no pruning required. Imbalance direction is conservative for H_M. Verification note added to `sae-probe-corpus.json`; new SHA-256 `0f62051574cac0bbaf9efbfa46a4dcf689842e2b174a9bb7b7020970b92d20c0` pinned in prereg.md §4 (supersedes the 2026-05-14 hash).
- 2026-05-15 — **J9 dispatched**: `scripts/reproduce_slopcodebench_baselines.py` — baseline reproduction harness with CPU-only `--dry-run`, OLS slope computation, upstream-leaderboard comparison, ±2pp tolerance gate, cost-estimate guard. Session 7879058108275412909. Three Jules sessions now running in parallel on basedlsg/iboga (J7 iboga_runner, J8 select_sae_features, J9 reproduce_baselines) — each adds a distinct scripts/ + tests/ file, no conflict risk.
