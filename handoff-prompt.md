---
title: Iboga — Continuation Prompt for New Chat
status: handoff
created: 2026-05-12
purpose: Self-contained prompt that picks up this research in a fresh Claude conversation
tags: [iboga, handoff, continuation]
---

# How to use this

Copy everything inside the `--- PROMPT BEGIN ---` / `--- PROMPT END ---` markers below into a new Claude conversation as the first message. The new chat will have full project context and the same discipline rules.

---

--- PROMPT BEGIN ---

I'm continuing a research project called **Iboga v0.5**. Read the project context below carefully, then read the actual artifacts in the project folder before proposing anything. **Do not expand scope. Do not re-litigate locked decisions. Do not suggest finding a collaborator (already declined).**

## Project location and scoping

All Iboga files live at `/Users/carlos/Brain/OBSIDIAN/projects/iboga/`.

**Hard scoping rule**: when working on Iboga, only read files in that folder. Do NOT read:
- `../life-compiler/`, `../nemo-compliance/`, `../innoxera-ksa/`, `../brain-itself/` (sibling projects)
- `../../inbox/`, `../../notes/`, `../../ideas/`, `../../archive/`, `../../daily-briefs/`, `../../weekly-syntheses/` (vault streams)

The only exception: at paper-writing time, the Nemo code repo at `/Users/carlos/NEMU-TEST-main/` may be read for the deployment-vignette chapter — but only when I explicitly invoke this.

Read `/Users/carlos/Brain/OBSIDIAN/projects/iboga/CLAUDE.md` first; it formalizes this scoping rule.

## What Iboga is

A pre-registered, 4-model × 3-arm controlled experiment characterizing how vocabulary choice and structural constraint on a between-checkpoint retrospective protocol mediates structural-erosion slope and solve rate in long-horizon coding agents, with exploratory SAE-based mechanistic analysis on Llama-3.1-8B.

**Substrate**: SlopCodeBench (arXiv:2603.24755, MIT-licensed, `github.com/SprocketLab/slop-code-bench`). 20 problems × 93 checkpoints × Python-only.

**Models** (4 families, 3 vendors) — locked OpenRouter slugs as of 2026-05-14:
1. `anthropic/claude-opus-4.7` (Anthropic, via OpenRouter; no direct Anthropic key)
2. `qwen/qwen3-32b` (Alibaba, via OpenRouter)
3. `meta-llama/llama-3.1-8b-instruct` (Meta, via OpenRouter; local for SAE work)
4. `deepseek/deepseek-chat-v3-0324` (DeepSeek V3 chat — the originally-named "DeepSeek-Coder-V3" does NOT exist on OpenRouter; verified 2026-05-14)

**Three arms** (all identical structure except where noted):
- **Arm A — Iboga**: AA Big Book vocabulary `{selfish, dishonest, self-seeking, frightened, inconsiderate}` as the "Where I was" closed-vocab field. Plus structured table, closed-vocab noting, Resentment inventory, past-tense panorama.
- **Arm B — Vocabulary-neutral**: identical structure, swaps AA vocab for `{drift, omission, premature-commit, unverified-assumption, scope-creep}` (coding-jargon attractor — explicitly NOT a null arm).
- **Arm C — Unstructured retrospective**: token-matched free-form retrospective, no closed vocab, no forced coverage.

**Primary outcomes** (Holm-Bonferroni protected, α=0.025 each):
- **H1a**: structural-erosion slope, AA < unstructured, one-tailed paired Wilcoxon
- **H1b**: solve rate non-inferiority, AA vs unstructured, TOST, margin Δ=−0.05

**Secondary** (α=0.05):
- **H2**: erosion slope AA vs neutral (two-tailed) — does vocabulary content matter?
- **H3**: verbosity slope AA < unstructured

**Exploratory mechanistic** (BH-FDR q<0.10):
- **H_M**: Goodfire l19 SAE features tagged with self-reference/deception/roleplay terms show LOWER activation in AA-arm vs neutral-arm during retrospective generation on Llama-3.1-8B (pre-registered direction).

**Budget**: $810 against $900 cap. **Timeline**: pre-reg lock 2026-07-01, main run Jul 1–Aug 23, submission ICLR 2027 workshop 2026-09-25 (Recursive Self-Improvement or Lifelong Agents). Fallback NeurIPS SafetyXAI October.

## How we got here (compressed history)

The project evolved through three versions in May 2026:

**v0.4** was rejected by all three rounds of academic review:
- CMU committee chair: approve-with-major-changes for thesis chapter only; reject Fellowship; reject main track
- Stanford CRFM chair: decline; workshop paper at best, weak end
- Hostile NeurIPS reviewer: 2/9 Reject

**Convergent v0.4 critiques** (every reviewer named the same flaws):
1. N=1×1×1×1 substrate (one project, one model, one operator, one domain) — case study, not science
2. Primary outcome (recurrence rate) was a textbook Goodhart target — same model writes confession AND subsequent commits
3. AA Big Book vocabulary is an *induction* (Common Crawl exposure), not a neutral measurement
4. No mechanistic component — naturalistic introspection is mostly confabulation in the 2026 consensus
5. Strategic mistake: abandoning silentvault's lineage (closed-vocabulary protocol design for self-report content)

**v0.5** was produced by a trusted-advisor agent that synthesized the critiques. Major changes:
- Substrate: SlopCodeBench instead of Nemo (Nemo demoted to deployment vignette)
- Models: 4 families instead of 1
- Three arms instead of two (vocabulary-neutral arm added)
- Primary outcome: structural-erosion slope (externally defined, static-analysis-measured, Goodhart-resistant) instead of recurrence rate
- Mechanism: exploratory SAE component on Llama-3.1-8B
- Verification: external blinded annotator with Cohen κ ≥ 0.7 audit + neutral failure-type taxonomy

**v0.5 re-evaluation** (third round, May 12):
- CMU chair: approve as thesis chapter with 2 minor conditions; would write strong Fellowship letter
- Stanford CRFM chair: workshop submission credible; conditional Fellowship support
- Hostile NeurIPS reviewer: 4/9 — borderline reject as written, accept-worthy for workshop with 8 specific fixes

**Solo execution decided 2026-05-12**: no SAE collaborator. H_M demoted from confirmatory to exploratory-with-pre-registered-direction. Llama-3.3-70B dropped from arms (compute), DeepSeek-Coder-V3 added to maintain 3-vendor diversity.

## Critical architectural correction (logged in decision log)

SlopCodeBench uses **fresh Docker containers per checkpoint**. Only the working directory persists; `/tmp/`, agent session data, shell history all reset. Therefore:

- Retrospective text **cannot** live in `/tmp/iboga-*` (would be wiped)
- Retrospective text **must not** live in the workspace (would contaminate AST-Grep verbosity metric)
- Retrospective lives on the **host** at `~/iboga-data/sessions/{trajectory-id}/{k}.json`
- At checkpoint k+1, retrospective is **injected into the agent's prompt**, never written to a file inside the container

This requires modifying SprocketLab's harness to expose a `--between-checkpoint-hook` flag. Repo inspection found the insertion target is `src/slop_code/agent_runner/runner.py` plus run CLI/config plumbing; **never touch metric computation** (reproducibility requirement).

## Current state (2026-05-13)

**Artifacts drafted** in `/Users/carlos/Brain/OBSIDIAN/projects/iboga/`:

| File | Purpose |
|---|---|
| `README.md` | Overview + isolation policy + status flags |
| `CLAUDE.md` | Hard scoping rule (read only this folder) |
| `prereg.md` | Full v0.5 pre-registration, 18 sections, OSF-ready |
| `next-steps.md` | Pre-lock checklist Week 1-7 + main-run calendar + decision log |
| `slopcodebench-study.md` | Verified metrics + harness architecture + risk flags from paper read |
| `arm-templates.md` | Arm A/B/C prompt templates with provider-neutral JSON Schema; Claude uses an Anthropic-compatible structured-output adapter through the selected route |
| `schemas/` | Draft provider-neutral JSON Schema files for Arms A/B/C |
| `arm-token-budget.md` | Token-budget validation scaffold |
| `arm-assignment-spec.md` | Deterministic `arm-assignment.json` format and validation rule |
| `scripts/generate_arm_assignment.py` | Standard-library generator for deterministic arm-assignment files |
| `scripts/prelock_sanity.py` | Local sanity checks for draft artifacts |
| `scripts/inspect_slopcodebench_repo.py` | Helper for later SlopCodeBench fork inspection |
| `scripts/compare_metric_outputs.py` | Helper for reproduction metric comparisons |
| `failure-types.md` | F0-F10 taxonomy for blinded annotator (neutral wrt both arms) |
| `annotator-rubric.md` | One-page blinded annotator instruction sheet draft |
| `analysis-plan.R` | Pre-registered statistical analysis script |
| `power-calc.R` | n=80 power validation across d=0.2-0.5 |
| `sae-features-decision.md` | SAE feature-catalog filter and lock decision scaffold |
| `sprocketlab-email.md` | Week 7 coordination email draft |
| `harness-validation.md` | Week 2 validation log for SlopCodeBench, `scb-check`, and runner-hook inspection |
| `provider-routing.md` | Non-Anthropic provider routing notes for OpenRouter, Gemini CLI OAuth, Meta Llama Developer API, and Jules |
| `handoff-prompt.md` | This file (also lives in the chat that produced it) |

**Decisions locked** (no silent revisions allowed):
- Substrate: SlopCodeBench
- Models: `anthropic/claude-opus-4.7` + `qwen/qwen3-32b` + `meta-llama/llama-3.1-8b-instruct` + `deepseek/deepseek-chat-v3-0324`
- 3 arms + Arm 0 (pilot sanity check only)
- H_M exploratory with pre-registered direction
- Annotator $200 retainer, F0-F10 taxonomy, κ ≥ 0.7 requirement
- Budget $810 / $900 cap
- Pre-reg lock target 2026-07-01
- ICLR 2027 workshop target 2026-09-25
- **Solo execution — no collaborator outreach**

**Pre-lock corrections already applied 2026-05-12**:
- Erosion equation in `prereg.md` aligned with repo inspection: high-complexity threshold `CC(f) > 10`, using SlopCodeBench's exported `erosion` field from `scb-check==0.1.3`.
- Verbosity operationalization corrected before lock: `scb-check==0.1.3` uses clone SLOC union ast-grep SLOC union trivial-wrapper SLOC divided by total SLOC.
- Recurrence annotation is now a capped exploratory audit: 120 candidate pairs, 20% annotated sample (target 24 pairs), 5-hour cap, $200.
- Mixed-effects sensitivity check uses raw `erosion_slope`, not `log(erosion_slope)`, because slopes can be zero or negative.
- Primary analysis requires raw H1a and H1b p-values to both pass α=0.025; Holm-adjusted p-values are still reported.
- Structured output is provider-neutral JSON Schema with local validation/retry. Arm C uses a single wrapper field so it remains unstructured in content but structured in transport.
- Local SlopCodeBench reproduction setup completed: `uv sync` succeeded in `projects/iboga/slop-code-bench/`; managed problem catalog installed under `projects/iboga/.scbench/`, catalog `v1.0` commit `4d38d300059667d57e43c31969bc455f5c338b52`.
- No-cost config smoke check completed: `configs/runs/lite_under20.yaml` resolves to `mvvault` and `xjq`, with default `claude_code@2.0.51`, `anthropic/sonnet-4.5`, `thinking=high`, and no Docker `extra_mounts`.
- Docker server `27.3.1` was started on 2026-05-12.
- Direct-Anthropic default route is stale for this project. Non-Anthropic route verified on 2026-05-13: `uv run slop-code run --config configs/runs/lite_under20.yaml --agent gemini --model gemini_auth/gemini-2.5-flash-lite --dry-run --no-live-progress` passes credential resolution and previews `mvvault` + `xjq`.
- OpenRouter route probe on 2026-05-13 stops only because `OPENROUTER_API_KEY` is not exported in the shell. Meta Llama Developer API needs authenticated portal details before local provider support can be added.
- **Tool-stack roles** (preserved from the original silentvault plan): OpenRouter is the trajectory-model route; Gemini CLI is the free validation route; Jules is the engineering coordinator (J6-J10 coding tasks: hook implementation, `iboga_runner.py`, SAE collection script, metric reproduction harness, DeepSeek slug resolution); HuggingFace Router + Together AI remain as fallbacks. Jules is in scope as engineering helper, not as a trajectory model. See `provider-routing.md` for the full table and Jules task list.
- Local SlopCodeBench fork configs were added for Opus 4.7 via OpenRouter, Qwen2.5-32B, and Llama-3.1-8B; all reach OpenRouter credential resolution. DeepSeek remains an exact-slug pre-lock issue because current docs expose DeepSeek V3 variants, not a confirmed `DeepSeek-Coder-V3` route.
- Gemini agent Docker image build passed after Docker Desktop disk cleanup: built `slop-code:python3.12` and `slop-code:gemini-0.41.2-python3.12`.
- Actual no-treatment Gemini validation on `xjq` partially passed: checkpoint 1 completed/evaluated with no infrastructure failure; checkpoint 2 hit Gemini Code Assist capacity errors (`429`, `MODEL_CAPACITY_EXHAUSTED`) and was stopped manually. Use OpenRouter for the next full no-treatment validation once `OPENROUTER_API_KEY` is exported.

**Pre-lock validation steps pending** (user-side, mostly mechanical):
1. Create OSF account; no pre-reg upload until all gates pass.
2. Export `OPENROUTER_API_KEY`; then run the full no-treatment validation on `configs/runs/lite_under20.yaml`.
3. Resolve exact DeepSeek slug before lock; do not silently substitute DeepSeek V3 for `DeepSeek-Coder-V3`.
4. Run upstream/fork baseline reproduction on 5 baseline models × 5 problems → verify reproduction within ±2 pp.
5. Build `--between-checkpoint-hook` around `src/slop_code/agent_runner/runner.py`.
6. Build "Arm 0" no-op-hook arm; run pilot; confirm no metric drift from no-hook baseline.
7. Verify `~/iboga-data/sessions/*` paths never enter Docker workspace or checkpoint `snapshot`.
8. Pull Goodfire l19 feature catalog. Apply label-filter against the 8 terms locked in `prereg.md` §4. Top-20 by match score → lock IDs in `iboga/sae-features.json`. If <5 features → demote H_M to exploratory-no-direction.
9. Commit power calc output to `iboga/power-calc-output.txt`.
10. Recruit one external annotator ($200, ~5 hours work, no AA familiarity) for the capped recurrence audit sample.
11. Run pilot (24 trajectories from Week 7 schedule).
12. Post to OSF, receive DOI, flip `prereg.md` frontmatter `status: draft` → `status: locked`.

## DO

- **Read `prereg.md`, `next-steps.md`, and `slopcodebench-study.md` first** when given any Iboga task.
- **Maintain solo-execution discipline.** No collaborator suggestions.
- **Push corrections back into the pre-reg + decision log** when new findings emerge. Update `next-steps.md` decision log.
- **Cite vault-relative paths** (drop the `/Users/carlos/Brain/OBSIDIAN/` prefix when referring to files inside Iboga).
- **Pre-register everything material** before lock; no silent design changes.
- **Convert relative dates to absolute** (today is in the system prompt).
- **Push back hard if I suggest scope creep** — the reviewers' 4/9 verdict assumed v0.5 as defined; expanding scope risks the timeline.
- **If a finding invalidates a locked decision**, flag it explicitly and propose an OSF amendment rather than silently revising.

## DON'T

- Don't suggest finding a co-author (already declined; SAE is solo + exploratory).
- Don't read sibling project folders or vault streams (CLAUDE.md scoping rule).
- Don't add new vocabularies, new arms, or new models without flagging it as a material deviation.
- Don't propose moving the substrate back to Nemo (Nemo is deployment vignette only).
- Don't romanticize the AA vocabulary in writing — it's an *instrument* whose effect is being characterized vs the neutral arm, not a load-bearing philosophical claim.
- Don't write the paper before the experiment runs. We're in pre-lock validation; the paper drafts in Sep 7-25.
- Don't quote the Berg 2025 induction prompt verbatim in any external document until copyright clearance is verified (`prereg.md` flags this).

## What I might ask you to do next

Likely first tasks in a fresh chat:

1. **"Read the pre-reg and flag anything I'd want to fix before lock."** → Read the Iboga folder artifacts, surface inconsistencies or risks.
2. **"Help me inspect the SlopCodeBench fork further."** → Continue from `harness-validation.md` and `provider-routing.md`; next blocker is either exporting `OPENROUTER_API_KEY` or running the no-treatment `lite_under20` route through Gemini CLI OAuth.
3. **"Build the harness-validation script."** → Concrete code: a Python or shell script that runs the upstream harness on 5×5 trajectories and compares my fork's output to upstream.
4. **"Pull the SAE feature catalog and apply the filter."** → A Python script using `huggingface_hub` + Goodfire's feature index format to filter top-20 features matching the locked terms.
5. **"Run the power calc."** → Execute `power-calc.R` and commit the output.
6. **"Walk me through what to do today."** → Look at `next-steps.md` and the current date; tell me the specific next physical action.

## Tone

The reviewers were harsh. I accepted it. Maintain that tone. **No sycophancy. No padding. Push back if my framing is off.** The pre-reg's discipline is the whole point — if it slips, the work fails.

## Today's date

It's in the system prompt. Use it. Don't guess. If the system date is past 2026-07-01 and `prereg.md` still has `status: draft`, the timeline has slipped — flag it.

--- PROMPT END ---

---

# Maintenance notes

- If pre-reg lock happens (status: locked, OSF DOI assigned), update this prompt's "Current state" section.
- If a material deviation is made post-lock, document it in `prereg.md §17` and reflect in this prompt.
- If the venue shifts (e.g., NeurIPS SafetyXAI fallback), update the timeline section.
- Refresh "What I might ask you to do next" when current state changes substantially.

This prompt is designed to be **self-contained**. A fresh chat with just the prompt + file access to `/Users/carlos/Brain/OBSIDIAN/projects/iboga/` should be able to continue the work without further onboarding.
