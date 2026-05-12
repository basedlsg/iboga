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

**Models** (4 families, 3 vendors):
1. Claude Opus 4.7 (closed, Anthropic API)
2. Qwen2.5-32B-Instruct (Together AI)
3. Llama-3.1-8B-Instruct (Together AI + local for SAE)
4. DeepSeek-Coder-V3 (OpenRouter free tier)

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

This required modifying SprocketLab's harness to expose a `--between-checkpoint-hook` flag. Modifications stay in `runner/` only; **never touch `metrics/`** (reproducibility requirement).

## Current state (2026-05-12, evening)

**Artifacts drafted** in `/Users/carlos/Brain/OBSIDIAN/projects/iboga/`:

| File | Purpose |
|---|---|
| `README.md` | Overview + isolation policy + status flags |
| `CLAUDE.md` | Hard scoping rule (read only this folder) |
| `prereg.md` | Full v0.5 pre-registration, 18 sections, OSF-ready |
| `next-steps.md` | Pre-lock checklist Week 1-7 + main-run calendar + decision log |
| `slopcodebench-study.md` | Verified metrics + harness architecture + risk flags from paper read |
| `arm-templates.md` | Arm A/B/C prompt templates with provider-neutral JSON Schema; Claude uses Anthropic `tool_use` adapter |
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
| `harness-validation.md` | Week 2 validation scaffold for upstream metric and runner inspection |
| `handoff-prompt.md` | This file (also lives in the chat that produced it) |

**Decisions locked** (no silent revisions allowed):
- Substrate: SlopCodeBench
- Models: Opus 4.7 + Qwen2.5-32B + Llama-3.1-8B + DeepSeek-Coder-V3
- 3 arms + Arm 0 (pilot sanity check only)
- H_M exploratory with pre-registered direction
- Annotator $200 retainer, F0-F10 taxonomy, κ ≥ 0.7 requirement
- Budget $810 / $900 cap
- Pre-reg lock target 2026-07-01
- ICLR 2027 workshop target 2026-09-25
- **Solo execution — no collaborator outreach**

**Pre-lock corrections already applied 2026-05-12**:
- Erosion equation in `prereg.md` aligned with `slopcodebench-study.md`: high-complexity threshold `CC(f) > 10`, with upstream `metrics/erosion.py` still authoritative after repo inspection.
- Recurrence annotation is now a capped exploratory audit: 120 candidate pairs, 20% annotated sample (target 24 pairs), 5-hour cap, $200.
- Mixed-effects sensitivity check uses raw `erosion_slope`, not `log(erosion_slope)`, because slopes can be zero or negative.
- Primary analysis requires raw H1a and H1b p-values to both pass α=0.025; Holm-adjusted p-values are still reported.
- Structured output is provider-neutral JSON Schema with local validation/retry. Arm C uses a single wrapper field so it remains unstructured in content but structured in transport.

**Pre-lock validation steps pending** (user-side, mostly mechanical):
1. Fork SlopCodeBench: `gh repo fork SprocketLab/slop-code-bench`. Pin commit.
2. Inspect upstream `metrics/verbosity.py` (clone-detection algorithm — not specified in paper). Inspect `metrics/erosion.py` (slope computation detail). Document findings in a new file `iboga/harness-validation.md`.
3. Inspect upstream `runner/` to identify where to insert `--between-checkpoint-hook`.
4. Run upstream harness on 5 baseline models × 5 problems → verify reproduction within ±2 pp.
5. Build "Arm 0" no-op-hook arm; run pilot; confirm no metric drift from upstream baseline.
6. Verify `~/iboga-data/sessions/*` paths never enter Docker workspace.
7. Pull Goodfire l19 feature catalog. Apply label-filter against the 8 terms locked in `prereg.md` §4. Top-20 by match score → lock IDs in `iboga/sae-features.json`. If <5 features → demote H_M to exploratory-no-direction.
8. Commit power calc output to `iboga/power-calc-output.txt`.
9. Recruit one external annotator ($200, ~5 hours work, no AA familiarity) for the capped recurrence audit sample.
10. Run pilot (24 trajectories from Week 7 schedule).
11. Post to OSF, receive DOI, flip `prereg.md` frontmatter `status: draft` → `status: locked`.

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
2. **"Help me inspect the SlopCodeBench fork."** → After I run `gh repo fork SprocketLab/slop-code-bench`, walk through their `metrics/` and `runner/` code with me to understand the hook insertion point.
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
