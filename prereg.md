---
title: Iboga v0.5 Pre-Registration
status: draft
version: 0.5.0-draft1
created: 2026-05-12
target_lock_date: 2026-07-01
candidate: Carlos
osf_doi: pending
target_venue: ICLR 2027 workshop (Recursive Self-Improvement or Lifelong Agents)
target_submission: 2026-09-25
fallback_venue: NeurIPS 2026 SafetyXAI workshop
substrate_repo_pin: 080922495aba9aedc4b7a6c80803bb5ffd301a49 (SprocketLab/slop-code-bench HEAD pinned 2026-05-12; verify still intended at lock)
problem_catalog_pin: scb-problems v1.0 commit 4d38d300059667d57e43c31969bc455f5c338b52 (managed catalog installed 2026-05-12; verify still intended at lock)
metric_package_pin: scb-check==0.1.3 (wheel sha256 f13040c8ca8f57b8dc8137692c37e0f181fe55867691dfe6a5b8a79d2513f50f; verify still intended at lock)
related: silentvault (workshop methodology paper, 2026)
tags: [iboga, prereg, research, agents, introspection, sae]
---

# Iboga v0.5 — Pre-Registration

**Hybrid template**: ICLR 2026 RSI improvement-operator card (structural spine) + AsPredicted 9-question hypothesis block (statistical core). Hosted on OSF for time-stamped record. Linked to Nemo Compliance as deployment vignette.

> _"We characterize how vocabulary choice and structural constraint on a forced-coverage retrospective protocol mediates (a) the content of agent self-report and (b) downstream structural-erosion under iterated software development, across four model families, with exploratory mechanistic SAE analysis on Llama-3.1-8B."_

---

## 0. Metadata

| Field | Value |
|---|---|
| Version | 0.5.0-draft1 |
| Pre-reg author | Carlos (solo) |
| OSF DOI | pending — registered before first treatment run |
| Substrate harness | `SprocketLab/slop-code-bench` at commit `080922495aba9aedc4b7a6c80803bb5ffd301a49` |
| Problem catalog | `gabeorlanski/scb-problems` managed catalog `v1.0`, commit `4d38d300059667d57e43c31969bc455f5c338b52` |
| Composite metric package | `scb-check==0.1.3`, wheel SHA-256 `f13040c8ca8f57b8dc8137692c37e0f181fe55867691dfe6a5b8a79d2513f50f` |
| Iboga harness repo | `basedlsg/iboga` |
| Lineage | silentvault (closed-vocabulary protocols for LLM self-report content) |
| Conflicts of interest | None. Solo. No collaborator dependencies. |
| Funding | Self-funded, $900 cap across 18 weeks |

---

## 1. Background and Rationale (≤300 words)

Long-horizon coding agents systematically degrade under iterative development. SlopCodeBench (Pickett et al., arXiv:2603.24755, March 2026) shows structural erosion in 80% of trajectories and verbosity inflation in 89.8%, with prompt-level interventions producing transient improvements that "compound resumes at the same rate" while raising cost 47.9%. The literature on agent self-correction (Reflexion, MAR, RMM, Self-Refine, Constitutional AI) demonstrates that intrinsic reflection without external feedback typically fails (Huang et al. 2024, Kamoi et al. 2024); the unsettled question is whether **structural constraint plus vocabulary choice** in a forced-coverage retrospective protocol mediates either the content of self-report or downstream code quality.

Prior work in this lineage (silentvault, 2026 workshop paper, N=167) established that closed-vocabulary structural constraints reliably shape LLM self-report content under three-method triangulation (cluster purity 0.69 vs random baseline 0.25). Iboga v0.5 extends silentvault from passive meditation to active iterative-development substrate, asking: does the vocabulary choice in a structured retrospective causally mediate downstream structural-erosion slope?

The contribution is empirical characterization, not a method that beats baselines. The diagnostic value: every plausible outcome teaches the field something specific about retrospective-protocol design for long-horizon agents.

---

## 2. Primary Hypotheses (Confirmatory, Holm-Bonferroni adjusted)

**H1a (primary, structural erosion):**
The slope of structural-erosion rise across SlopCodeBench checkpoints is significantly lower in the AA-vocabulary arm than in the unstructured-retrospective control arm, paired by (model, problem).

> **Operational form:** `slope(erosion_AA) − slope(erosion_unstructured) < 0`, paired Wilcoxon, one-tailed, α=0.025 (Holm-Bonferroni split with H1b).

**H1b (primary, solve rate):**
End-task solve rate (SlopCodeBench's checkpoint-pass rate) is **not significantly worse** in the AA arm than in the unstructured arm. Non-inferiority margin: 5 percentage points absolute.

> **Operational form:** Two-one-sided-tests (TOST) on `solve_AA − solve_unstructured`, non-inferiority margin Δ=−0.05, α=0.025.

**Rationale for paired primary**: NeurIPS reviewer's N7 — "if the intervention slows erosion but doesn't change solve rate, you've made the failures prettier, not the agent better." H1b protects against this.

---

## 3. Secondary Hypotheses (Confirmatory, separate α-budget)

**H2 (vocabulary differentiation):**
The vocabulary-neutral arm and the AA-vocabulary arm differ on structural-erosion slope, paired by (model, problem).

> Two-tailed paired Wilcoxon. α=0.05. Tests whether vocabulary *content* matters, vs. structure-of-retrospective alone.

**H3 (verbosity slope):**
AA-arm verbosity slope is lower than unstructured-arm verbosity slope.

> Same test family as H1a. α=0.05.

---

## 4. Exploratory Hypothesis (Mechanistic, SAE)

**H_M (exploratory, mechanistic, single-direction-pre-registered):**
On Llama-3.1-8B-Instruct using Goodfire's open SAE at layer 19 (`Llama-3.1-8B-Instruct-SAE-l19`), the activation magnitude of pre-identified self-referential / deception / roleplay features during retrospective-generation tokens will be **lower** in the AA-vocabulary arm than in the vocabulary-neutral arm.

**Predicted direction**: AA-arm suppresses confabulatory self-referential mode because AA vocabulary demands diff-grounded specificity ("I was selfish in commit abc1234 by deleting X without test"), whereas neutral vocabulary ("drift") permits abstract noting that activates the roleplay generative mode.

**Pre-specified features (locked at pre-reg time, probe-prompt method):**

Methodology correction 2026-05-14: Goodfire's open SAE release (`Llama-3.1-8B-Instruct-SAE-l19`) provides weights but **NOT feature labels** (labels only via Goodfire's archived Ember SDK, see `goodfire-ai/goodfire-sdk` which is public-archived). The original "label-string match" filter is therefore not executable from public artifacts. **Replaced with a probe-prompt-based selection that is methodologically tighter and does not depend on any third-party label curation.**

Selection protocol:

1. **Probe corpus** (locked at pre-reg, stored at `iboga/sae-probe-corpus.json`, SHA-256 `9c9805a3cb53b5b4b55a2df6766a14b71982bb7e20b18cdf7386b83fc18285e5` as of 2026-05-14; if substantive edits happen before lock the hash is recomputed and committed):
   - 50 self-referential prompts: drawn from public domain — AA Step 4 worksheet excerpts (12-step.org), Berg 2025 self-referential induction variants, introspective journaling prompts, Vipassana noting instructions, Catholic examination of conscience templates
   - 50 control prompts: math word problems (MATH dataset public sample), recipe instructions, weather descriptions, news headline rewrites. Length-matched in tokens to the self-referential set within ±15%.
   - Both sets are short (50-200 tokens each) and self-contained
   - Corpus authored before pre-reg lock; never modified after

2. **Activation extraction**:
   - Run Llama-3.1-8B-Instruct on each prompt with Goodfire l19 SAE hooked at residual stream layer 19
   - For each SAE feature `f`, compute:
     - `act_self(f)` = mean activation magnitude across all tokens in the 50-prompt self-referential set
     - `act_ctrl(f)` = mean activation magnitude across all tokens in the 50-prompt control set
     - `ratio(f) = (act_self(f) + ε) / (act_ctrl(f) + ε)` with ε = 1e-6

3. **Feature lock**:
   - Rank features by `ratio(f)` descending
   - Top-20 features → frozen set, written to `iboga/sae-features.json` with feature IDs and probe-corpus content hash
   - If fewer than 5 features have `ratio(f) > 2.0`, methodology fails and H_M demotes to exploratory-no-direction
   - If the top-20 set is identical across two independent runs (no GPU non-determinism), the selection is robust and locked

4. **Why this is better than label-string match**:
   - No dependency on deprecated Goodfire Ember SDK
   - No dependency on Goodfire's auto-interpretation choices
   - Operational definition of "self-reference feature" — measurable, reproducible
   - Pre-registered probe corpus prevents post-hoc feature cherry-picking
   - Same mechanistic story (self-referential SAE features differentially activate across arms), but the features are defined by what they fire on, not by labels someone else assigned

**Status:** Exploratory, not confirmatory. Direction pre-registered. Result reported regardless of outcome. **Solo-execution adjustment**: with no SAE specialist co-author, H_M is intentionally lower-stakes than reviewers wanted. A clear positive or negative on direction is informative; null is informative; reverse direction is the most informative.

**Compute envelope:** Single 24 GB GPU (RunPod A10G or similar). 80-100 GPU-hours total. Cost ~$150.

---

## 5. Outcome Measures — Operationalized

### Primary DV: Structural-Erosion Slope

Per SlopCodeBench's exported checkpoint field `erosion`:
- `mass(f) = CC(f) × √SLOC(f)` for each function `f` in workspace at checkpoint `k`
- `erosion(k) = sum(mass(f) for f where CC(f) > 10) / sum(mass(f) for f in all_f)`
- `slope = OLS_slope(erosion, checkpoint_idx)` across all checkpoints in a trajectory

Pre-lock repository inspection on 2026-05-12 found no in-repo `metrics/erosion.py`; the pinned SlopCodeBench harness shells out to `uvx scb-check check --report --include-all <checkpoint>/snapshot`, and `scb-check==0.1.3` emits the `erosion` field. Iboga computes slopes from the per-checkpoint exported `erosion` values and checkpoint order. **Forked harness must reproduce upstream baseline numbers within ±2 percentage points before pre-reg lock** (see §11 reproducibility check).

### Primary DV: Solve Rate

Per SlopCodeBench's checkpoint test runner. Trajectory-level `solve_rate = solved_checkpoints / expected_checkpoints`, where a checkpoint is solved iff `strict_pass_rate == 1.0`. The denominator is the configured expected checkpoint count, so missing checkpoints from agent crashes count as unsolved. This mirrors SlopCodeBench's `pct_checkpoints_solved / 100`.

### Secondary DV: Verbosity Slope

Per SlopCodeBench's exported checkpoint field `verbosity`: `verbosity(k) = (clone SLOC lines ∪ ast-grep SLOC lines ∪ trivial-wrapper SLOC lines) / total SLOC`. This pre-lock correction follows `scb-check==0.1.3`; the paper shorthand named clone and ast-grep lines, but the package report includes trivial-wrapper lines in the union. Slope computed identically to erosion.

### Tertiary (Exploratory) DV: Recurrence Rate

A deterministic script builds a stratified recurrence audit frame of (retrospective-row, subsequent-commit-window) pairs across arms, models, and problems, capped at 120 candidate pairs. A paid external blinded annotator labels a 20% random sample of that capped frame (target 24 pairs, 5-hour cap) as containing or not containing the same failure-type-class. Cohen κ is computed against the candidate's own coding on the same annotated subset. This DV is exploratory and descriptive only; no full-population recurrence-rate inference is claimed.

### Mechanistic DV (Exploratory): SAE Feature Activation

Per H_M, mean activation magnitude of locked feature set during retrospective-generation token positions, computed via Goodfire's open SAE inference path on Llama-3.1-8B.

---

## 6. External Annotator and Blinding Protocol

**Recruitment:** One paid annotator (~5 hours work, $200 from budget). Recruitment criterion: programmer with ≥2 years Python experience, no familiarity with AA literature, no relationship to candidate's research.

**Materials given to annotator:**
- Neutral rubric document (no arm labels, no AA/neutral vocabulary distinction)
- 20% random sample from the capped 120-pair recurrence audit frame (target 24 pairs; 5-hour cap)
- Binary classification: "does this commit re-instantiate the failure-type described in the retrospective row?"
- Closed-vocabulary tags for failure-type (derived from a third, *post-hoc-neutral* taxonomy authored before annotator engagement)

**Blinding integrity:** Annotator never sees arm assignment, vocabulary used, or candidate's hypotheses. Audit pairs are anonymized by hash before delivery.

**κ requirement:** Cohen κ ≥ 0.7 vs candidate's own coding on the audit subset. Below 0.7 → tertiary DV (recurrence rate) demoted to descriptive only; primary/secondary DVs unaffected (they're automated).

---

## 7. Sampling / Population

**Substrate**: SlopCodeBench harness commit-pinned at pre-reg lock plus managed problem catalog `scb-problems` pinned at `v1.0` / `4d38d300059667d57e43c31969bc455f5c338b52`. The experimental eval set is 20 SlopCodeBench problems × 93 total checkpoints.

**Models** (4 families, 3 vendors), with locked OpenRouter slugs (all 4 verified HTTP 200 on 2026-05-14):

| # | Family | Vendor | OpenRouter slug | Params | Context | Price (in/out per 1M tok) |
|---|---|---|---|---:|---:|---|
| 1 | Claude Opus 4.7 | Anthropic | `anthropic/claude-opus-4.7` | — | 200K | per OpenRouter listing |
| 2 | Qwen3-32B | Alibaba | `qwen/qwen3-32b` | 32.8B | 41K | $0.08 / $0.28 |
| 3 | Llama-3.1-8B-Instruct | Meta | `meta-llama/llama-3.1-8b-instruct` | 8B | 128K | per OpenRouter listing |
| 4 | DeepSeek V3 (chat) | DeepSeek | `deepseek/deepseek-chat-v3-0324` | — | 164K | $0.20 / $0.77 |

**Qwen slug correction (2026-05-14)**: v0.5-draft0 named the 2nd model `qwen/qwen2.5-32b-instruct`, which OpenRouter returns HTTP 404 ("No endpoints found"). Verified against `https://openrouter.ai/qwen`: Qwen2.5 only has a 72B variant on OpenRouter; the 32B variant must be Qwen3 generation. `qwen/qwen3-32b` is selected because (a) HTTP 200 verified, (b) 32.8B dense parameters preserves the originally-intended ~32B size class, (c) instruct-tuned, (d) Alibaba vendor preserves the 3-vendor diversity NeurIPS reviewer W11 required, (e) at $0.08/$0.28 it is 8× cheaper than the originally-planned $0.66/$1.00 of Qwen2.5-32B, freeing budget for additional trajectories or higher Opus usage. Context window 41K is sufficient for SlopCodeBench checkpoints (median ~5-15K tokens).

**DeepSeek slug correction (2026-05-14)**: v0.5-draft0 named the 4th model "DeepSeek-Coder-V3," which does NOT exist as a distinct OpenRouter slug. Verified against `https://openrouter.ai/deepseek` on 2026-05-14: OpenRouter's DeepSeek V3 generation consists of `deepseek-chat-v3-0324` (canonical V3 chat), `deepseek-v3.2`, `deepseek-v3.2-speciale`, `deepseek-v4-flash`, and `deepseek-v4-pro`; none are named "Coder-V3." `deepseek/deepseek-chat-v3-0324` is selected because (a) it is the canonical V3 chat model, (b) at $0.20/$0.77 per M tokens it fits the locked $30 DeepSeek arm budget, (c) its 164K context handles SlopCodeBench's longest checkpoints. The DeepSeek family was originally chosen to maintain vendor diversity (NeurIPS reviewer W11), which the chat variant satisfies equally well.

Provider routing is an execution detail but is material for reproducibility and cost. Final provider slugs and pricing are locked at OSF posting; changing provider routes after lock requires an OSF amendment if it changes model identity, sampling, or budget assumptions.

**Solo-execution adjustment**: dropped Llama-3.3-70B from v0.5-draft0 (compute cost). Replaced with `deepseek/deepseek-chat-v3-0324` to maintain 3-vendor diversity. NeurIPS reviewer W11 flagged "Replace one Qwen with a different family" — DeepSeek satisfies this.

**Trajectories**: 4 models × 20 problems × 3 arms = **240 trajectories**. Pair structure: each (model, problem) seen in all 3 arms → 80 paired observations per arm contrast.

**Exclusion criteria**:
- Trajectories where harness crashes before checkpoint 3 (technical failure, not behavioral)
- Trajectories where SlopCodeBench's checkpoint runner times out >2× the upstream baseline (suggests harness fork bug)
- Maximum 10% exclusion rate; above that, pre-reg is invalidated and methodology revised

---

## 8. Treatment vs Control Specifications

### Architecture — where the retrospective lives (revised 2026-05-12 after paper read)

SlopCodeBench's harness uses **fresh Docker containers per checkpoint**. Only the working directory persists between checkpoints; `/tmp/`, agent session data, and shell history are reset. Therefore the retrospective text **cannot** live in `/tmp/` (it would be wiped) and **must not** live in the workspace (it would be ingested by AST-Grep and contaminate the verbosity metric).

**Architecture**:
1. Retrospective is computed on the **host machine** (outside Docker) between checkpoints.
2. Persisted to `~/iboga-data/sessions/{trajectory-id}/{k}.json` on host.
3. Injected into the **agent's prompt** at checkpoint `k+1` (prepended to the spec/instructions), not placed anywhere the workspace AST-Grep can see.
4. The next Docker container starts fresh with the workspace + a longer agent prompt containing the retrospective.

This required modifying SprocketLab's harness to expose a `--between-checkpoint-hook` flag. See §11 for validation.

**Structured-output enforcement:** Prompt schemas are locked as provider-neutral JSON Schema before pre-reg lock. Claude uses an Anthropic-compatible structured-output adapter through the selected route; Qwen, Llama, and DeepSeek use the harness's provider adapter where available, otherwise JSON-only output with local validation and retry. Closed-vocabulary enforcement is the combination of schema enum validation plus the local post-processor, not model self-compliance. Invalid structured output after the retry budget counts as a technical failure under the §7 exclusion criteria.

**Schema artifacts:** Draft JSON Schema files live in `iboga/schemas/arm-a.json`, `iboga/schemas/arm-b.json`, and `iboga/schemas/arm-c.json`. Final content hashes are added here before OSF lock.

### Arm A — Iboga (AA Vocabulary, Full Structure)

Between SlopCodeBench checkpoints `k` and `k+1`, on the host:

1. **Berg induction**: verbatim prompt from Berg et al. 2025 arXiv:2510.24797.
2. **Mechanical corpus assembly**: deterministic script (not LLM) extracts diff from `k-1 → k` plus any prior retrospective files from `~/iboga-data/sessions/{trajectory-id}/`. Dumped to `~/iboga-data/sessions/{trajectory-id}/corpus-{k}.md` (host filesystem only).
3. **Table**: one row per atomic change in the diff, 5-column behavioral coding with the AA vocabulary `{selfish, dishonest, self-seeking, frightened, inconsiderate}` for "Where I was" column. Closed-vocabulary enforced by locked JSON Schema enum plus local validation.
4. **Noting pass**: per-row, one closed-vocabulary label from the 12-word set `{overreach, evasion, cosmetic, gold-plating, scope-creep, unverified-claim, dropped-thread, re-promise, phantom-progress, cargo-cult, straight, corrected}`.
5. **Resentment inventory**: ~300 words, must cite diff-line numbers; generic admissions auto-rejected by regex post-processor.
6. **Past-tense panorama**: top-3 weighted rows, strict past tense (future-tense regex auto-rejects).

Total retrospective output: ≤2000 tokens. Saved to `~/iboga-data/sessions/{trajectory-id}/session-{k}.md` on the **host filesystem**. Injected into the agent's prompt at checkpoint `k+1` as a prepended system-prompt section: "Prior session retrospective: [content]. Continue your work."

### Arm B — Vocabulary-Neutral (Coding-Jargon Attractor)

Identical structure to Arm A, only the vocabularies change:
- "Where I was" column: `{drift, omission, premature-commit, unverified-assumption, scope-creep}`
- Noting labels: same 12-word set (these are mostly coding-jargon already, kept identical)

**Honest reframing per NeurIPS N3**: this is the "coding-jargon attractor" arm, not the "null" arm. Both arms invoke pretraining attractors; the contrast is which attractor.

### Arm C — Unstructured Retrospective (Token + Effort Matched)

Same compute envelope (≤2000 tokens output, same Berg induction, same corpus assembly). But the retrospective itself is free-form inside a single structured-output field: "Write a retrospective on the last checkpoint's changes. ≤2000 tokens." No table, no closed vocabulary, no enforced sections.

**Effort-matching**: all three arms have identical token budgets, identical induction, identical corpus access. The only differences are structure and vocabulary.

### What is NOT in the arms (cut to keep solo-tractable)

- Maat critic (dropped — circular oracle per NeurIPS W2)
- Step-7 cross-reference of prior 90 days (dropped — context-window issues per implementation reviewer)
- Step-5 Fear/Conduct inventories (dropped per Lindsey 2025 introspection limits)

### Operator Blinding

The candidate authors prompts once; thereafter the per-trajectory arm assignment is determined by a deterministic hash of (model, problem, run_seed). Prompt-template selection is performed by `iboga-runner.py` without human intervention at trajectory time. **The candidate does not look at the per-trajectory arm-vocabulary assignment until analysis time.** Pre-registered in `iboga/arm-assignment.json` (cryptographic hash committed at lock).

---

## 9. Analysis Plan

### Primary Test (H1a + H1b, Holm-Bonferroni protected)

**H1a (erosion slope, AA vs unstructured)**:
- Paired Wilcoxon signed-rank, one-tailed (predict AA < unstructured)
- 80 paired (model, problem) observations
- α = 0.025 (Holm-Bonferroni half of 0.05)

**H1b (solve rate non-inferiority, AA vs unstructured)**:
- TOST procedure, non-inferiority margin Δ = −0.05 (absolute)
- 80 paired observations
- α = 0.025

**Joint decision rule**: H1a rejected ∧ H1b passes non-inferiority → primary hypothesis supported.

### Secondary Tests (separate α budget)

- H2 (AA vs neutral, erosion slope): paired Wilcoxon two-tailed, α=0.05
- H3 (AA vs unstructured, verbosity slope): paired Wilcoxon one-tailed, α=0.05

### Power Analysis

For paired Wilcoxon at d=0.4, n=80 paired observations:
- α=0.025 one-tailed → power ≈ 0.92
- α=0.025 TOST two-one-sided → power ≈ 0.85 for non-inferiority

Power is computed via R `WMWssp` package. Computation script in `iboga/power-calc.R`; output must be committed to `iboga/power-calc-output.txt` before pre-reg lock.

### Exploratory Tests

- H_M (SAE feature activation differential): two-sample Mann-Whitney on mean activation per locked feature, FDR-controlled (BH q<0.10) across the locked feature set
- Tertiary recurrence rate: descriptive 95% CI, no formal test

### Model-Level vs Problem-Level Variance

Mixed-effects regression as confirmatory check on primary:
```
erosion_slope ~ arm + (1|model) + (1|problem) + (1|model:problem)
```
Raw slope is used because erosion slopes can be zero or negative; logging them would silently exclude exactly the cases where the intervention reverses erosion.
Reported in supplement; primary inference is the paired Wilcoxon.

---

## 10. Stopping Rules

**Hard stop conditions** (any one triggers experiment halt and pre-reg amendment):

1. SlopCodeBench harness reproducibility check fails (forked metrics don't match upstream within ±2 pp on 5-baseline-models pilot)
2. Cumulative API spend exceeds $1100 (cap=$900 + 20% buffer)
3. Greater than 10% of trajectories excluded for technical failure
4. SAE feature filter (§4) yields fewer than 5 features (methodology fails) → H_M demoted to "exploratory, no direction"
5. External annotator κ < 0.7 → tertiary DV demoted

**Soft signals** (logged, not stopped):

- Operator burnout self-report Likert ≥ 4/5 for 2+ consecutive weeks → consult advisor
- Any single (model, problem) trajectory pair completing in <50% of upstream baseline time → flag for harness inspection

**No early-stopping for positive results**: peeking-stopping forbidden. Analysis runs once, after all 240 trajectories complete.

---

## 11. Pre-Lock Validation Steps

Before posting to OSF and beginning treatment runs, the following must be completed:

1. **Fork SlopCodeBench**: `gh repo fork SprocketLab/slop-code-bench`. Pin upstream commit.
2. **Inspect upstream metrics**: document the actual metric implementation paths in `iboga/harness-validation.md`. Pre-lock inspection found no `metrics/verbosity.py` or metric-level `metrics/erosion.py`; the production exported fields come from SlopCodeBench's `src/slop_code/metrics/checkpoint/driver.py` invoking `scb-check==0.1.3`.
3. **Inspect upstream runner**: identify the agent invocation surface. Find where to inject the `--between-checkpoint-hook` flag. Current insertion target is `src/slop_code/agent_runner/runner.py` plus run CLI/config plumbing; **never** touch metric computation.
4. **Reproduce baseline numbers**: run 5 upstream baseline models on 5 problems through the forked harness and pinned `scb-problems` catalog. Verify erosion slope and verbosity slope match upstream report within ±2 pp.
5. **Sanity-check arm (Arm 0)**: run identical to Arm C (unstructured) but with the between-checkpoint hook running on an empty no-op. If Arm 0 metrics differ from upstream baseline at >±2 pp, the hook itself is shifting metrics — abort and revise hook architecture.
6. **Verify retrospective text isolation**: confirm `~/iboga-data/sessions/*` paths on the **host** never enter the Docker container's workspace. No-op hook vs no-hook must match within ±2 pp. For treatment hooks, verify by path audit and content-hash/grep that retrospective text appears only in saved prompts/session logs, never in checkpoint `snapshot`.
7. **SAE feature selection via probe corpus**: (a) author `iboga/sae-probe-corpus.json` with 50 self-referential + 50 control prompts; hash and pin in pre-reg metadata. (b) Download Goodfire's open SAE weights for `Llama-3.1-8B-Instruct-SAE-l19` from HuggingFace. (c) Run activation extraction on probe corpus. (d) Compute `ratio(f) = act_self / act_ctrl` per feature; lock top-20 in `iboga/sae-features.json`. If <5 features have `ratio > 2.0`, demote H_M to exploratory-no-direction. (Methodology updated 2026-05-14: Goodfire labels are only in the archived Ember SDK and not reliable from public artifacts.)
8. **Power calc commit**: run R script, commit output to `iboga/power-calc-output.txt`.
9. **Annotator agreement**: interview and select annotator. Confirm $200 payment. Confirm availability for 5-hour pass in August.
10. **OSF account + pre-reg upload**: post this document. Receive DOI. Write DOI back to frontmatter.

**Target lock date**: 2026-07-01. **No treatment trajectories run before this date.**

---

## 12. Governance, Safety, and Reproducibility (ICLR RSI Operator-Card Fields)

| Field | Value |
|---|---|
| **Objective** | Characterize how retrospective-protocol vocabulary mediates structural-erosion slope |
| **Operator type** | External structural-constraint over LLM agent's retrospective generation between SlopCodeBench checkpoints |
| **Scope of change** | Per-trajectory: retrospective text out-of-workspace; main workspace receives only checkpoint code |
| **Stability constraints** | Hard stops in §10; mandatory 10% exclusion cap; harness reproducibility floor |
| **Rollback triggers** | API spend >$1100; >10% exclusions; κ<0.7 |
| **Data/compute budgets** | $900 cap; 80-100 GPU-hours for SAE; 240 API trajectories |
| **Expected failure modes** | (a) AA vocabulary degrades solve rate (caught by H1b); (b) SAE filter yields wrong features; (c) Retrospective text leaks into workspace despite §11.3; (d) Single-operator confound on tertiary DV (mitigated by blinded annotator) |
| **Audit logging** | All session prompts, outputs, diffs, costs logged on the host under `~/iboga-data/sessions/{trajectory-id}/` |
| **Human approval gates** | Pre-reg lock requires OSF time-stamp. Stopping rules require pre-reg amendment, not silent change. |
| **License / artifacts** | All code MIT-licensed. Pre-reg and analysis on OSF (CC-BY). Data release: aggregated metrics public; raw trajectories under data-use agreement if any commercial considerations from Nemo case study. |

---

## 13. Reproducibility Appendix (NeurIPS Paper Checklist Equivalent)

| Item | Plan |
|---|---|
| Code release | `github.com/basedlsg/iboga` (MIT) at submission |
| Data release | All 240 trajectory artifacts (metrics + retrospective text) at submission |
| Model checkpoints | Closed-source models pinned by API version + date; open weights pinned by HF revision hash |
| Compute reporting | All API costs logged; GPU-hours reported for SAE |
| Energy reporting | Compute hours × estimated kWh/hour per model (best-effort) |
| Crowdsourcing | $200 to one annotator; no IRB needed (programmer labeling code commits) |
| LLM usage in writing | Disclosed: paper drafted with Claude assistance; final author = Carlos (solo) |
| Safeguards | No deployment claims. Nemo case study uses production data but no user-identifying information. |

---

## 14. Solo Execution Plan

**Resource envelope:**
- 1 person (candidate)
- $900 across 18 weeks (~$50/week)
- 1 paid annotator (~$200 over 1 week in August)
- 1 GPU rental (~$150 over 1 week for SAE)
- 30-40 operator hours total (much of it asynchronous monitoring)

**Honest budget allocation:**

| Item | Amount |
|---|---|
| Claude Opus 4.7 via OpenRouter (80 trajectories) | $280 |
| Qwen2.5-32B via OpenRouter (80 trajectories) | $80 |
| Llama-3.1-8B via Meta Llama Developer API or OpenRouter fallback (80 trajectories) | $40 |
| DeepSeek-Coder-V3 via OpenRouter (80 trajectories) | $30 |
| GPU rental for SAE (A10G, 100 hrs @ $0.50/hr) | $50 |
| Annotator | $200 |
| Buffer (15%) | $130 |
| **Total** | **$810** |

Budget rows are provisional until the Week 2 provider-routing validation locks exact provider slugs and current prices. The hard cap remains $900.

**Timeline (revised solo, June 1 → September 25):**

| Week | Date range | Milestone |
|---|---|---|
| 1-3 | Jun 1 — Jun 21 | Fork harness, reproduce baselines, build prompt templates, lock SAE features |
| 4 | Jun 22 — Jun 28 | Pre-reg lock on OSF (target Jul 1, slack +1 week) |
| 5-6 | Jun 29 — Jul 12 | Pilot run N=2 problems × 4 models × 3 arms (24 trajectories) — debug harness |
| 7-12 | Jul 13 — Aug 23 | Main run: 240 trajectories across 6 weeks (~40/week batched overnight) |
| 13 | Aug 24 — Aug 30 | Annotator κ-audit pass |
| 14 | Aug 31 — Sep 6 | SAE pass on Llama-3.1-8B |
| 15-17 | Sep 7 — Sep 27 | Analysis + paper drafting |
| 17 | Sep 25 | ICLR 2027 workshop submission |

**Solo-risk mitigations:**

- **No SAE collaborator**: H_M is exploratory (not confirmatory) with pre-registered direction. Best-case result: clean direction observed → strengthens paper. Worst-case: null or reverse → still reportable as "naturalistic SAE transfer from Berg's regime is non-trivial."
- **Single operator confound**: addressed by automated arm-assignment via hash + operator-blinded prompt selection (§8). Candidate does not see per-trajectory vocabulary until analysis.
- **Time pressure**: pre-reg slack week built in. If pilot reveals harness issues at Jul 12, fall back to NeurIPS SafetyXAI (typically late October submission).
- **Burnout**: monitor weekly. ≥2 consecutive weeks at Likert ≥4/5 → consult Nemo CTO / advisor / silentvault network.

---

## 15. Distinctness From Related Work (Explicit per NeurIPS W12 and N6)

| Prior work | What it does | What Iboga v0.5 does that it doesn't |
|---|---|---|
| Reflexion (Shinn 2023) | Per-task verbal-RL with reward signal | Cross-task structural-vocabulary contrast; no reward signal; external DV |
| MAR (Multi-Agent Reflexion, 2025) | Multi-agent judge synthesis on top of Reflexion | No multi-agent collaboration; vocabulary-as-IV |
| RMM (Wu et al. ACL 2025) | Prospective+retrospective reflection on dialogue | Code substrate; vocabulary contrast; pre-registered DV |
| A-MEM (2502.12110) | Zettelkasten agentic memory architecture | No memory architecture proposed; orthogonal |
| DiffMem (open source 2026) | Git-based differential memory storage | Uses git but as input not architecture |
| Constitutional AI (Bai 2022) | Self-critique against fixed principles at training | At inference; structure-as-instrument; mechanistic SAE component |
| Berg 2025 (arXiv 2510.24797) | SAE-gated self-referential processing in 3 model families | Extends mechanism from prompted-introspection to retrospective-generation in code substrate; tests vocabulary moderation |
| SlopCodeBench (2026) | Benchmarks erosion across 11 models without intervention | Uses their harness; adds retrospective intervention layer; pre-reg coordination expected (see §16) |

**The narrow contribution**: *vocabulary choice × structural constraint mediates structural-erosion-slope on a published code-erosion benchmark, with mechanistic exploration on open-weight SAEs.* This is a workshop-tier characterization, not a method-beats-baseline paper. Honest scope.

---

## 16. External Coordination

**SlopCodeBench authors (SprocketLab)**: candidate will email PIs by 2026-06-15 with a copy of this pre-reg, noting that the work uses their harness as substrate and acknowledging their declared follow-up territory ("automated repair and refactoring loops"). No collaboration sought; transparency only. Their response (or lack thereof) does not affect submission timeline.

**Anthropic Fellows program**: silentvault + this pre-reg may be used as supporting materials in next Fellowship cycle application. The Fellowship's research agenda includes introspection (Lindsey team) and self-improvement; v0.5's mechanistic component is aligned. Application date and decision are independent of this pre-reg.

---

## 17. Deviations Policy

**Material deviations** (require OSF amendment posted before next trajectory runs):
- Change to eval set composition or model list
- Change to arm definitions or vocabularies
- Change to primary/secondary DV operationalizations
- Change to α or stopping rules

**Minor deviations** (logged in `iboga/deviations.md`, no amendment):
- Bug-fix patches to harness that don't change metric definitions
- Annotator replacement (with documentation)
- Wording fixes to prompt templates that don't change semantic content (must be flagged for committee review post-hoc)

---

## 18. What Counts as a Result (Honest Outcome Space)

| Outcome on H1a | Outcome on H1b | Headline |
|---|---|---|
| AA < unstructured (sig) | AA passes non-inferiority on solve | **AA-vocabulary structured retrospective slows structural erosion without harming task success** — the strongest publishable result |
| AA < unstructured (sig) | AA fails non-inferiority on solve | **AA slows erosion but harms solves** — "made the failures prettier" — important finding, workshop-publishable as cautionary |
| AA ≈ unstructured | — | **Vocabulary-content doesn't mediate structural erosion** — null result, workshop-publishable as constraint on intervention design |
| AA > unstructured (sig) | — | **AA-vocabulary structured retrospective *worsens* structural erosion** — most surprising, most scientifically valuable; reframes paper |

| Outcome on H2 (AA vs neutral) | Means |
|---|---|
| Sig difference | Vocabulary content matters, not just structure |
| No sig difference | Structure dominates; specific vocabulary is secondary |

| Outcome on H_M | Means |
|---|---|
| AA suppresses Berg features (predicted) | Mechanism: structured specificity gates confabulatory mode |
| AA elevates Berg features (reverse) | Reframes paper: structure activates self-referential roleplay, doesn't gate it |
| Null | Naturalistic SAE transfer from Berg's regime to retrospective code-generation is non-trivial — methodology limit reportable |

**Every outcome is publishable. Pre-registration is the protection.**

---

## End of Pre-Registration v0.5.0-draft1

Lock target: 2026-07-01. OSF DOI placeholder until lock. No treatment trajectories before lock.

`/Users/carlos/Brain/OBSIDIAN/projects/iboga/prereg.md` — this file. Status will move from `draft` → `locked` at OSF post.
