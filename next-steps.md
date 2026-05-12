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

Today: **2026-05-12**. Lock target: **2026-07-01**. That's **7 weeks of pre-lock work**.

---

## Week 1 — May 12-18 — Foundations

- [x] Create `github.com/basedlsg/iboga` repo (MIT license)
- [x] Fork SlopCodeBench: `gh repo fork SprocketLab/slop-code-bench`. Pin upstream commit hash in `prereg.md` metadata.
- [ ] Create OSF account at osf.io (use flareondon@gmail.com). No pre-reg posted yet.
- [ ] Read SlopCodeBench paper in full (arXiv 2603.24755), take notes on: exact metric definitions in §3.2, the agent-loop hook surface, reproduction protocol.
- [ ] Set up RunPod or Vast.ai account for SAE work later (A10G access).
- [ ] **Decision point**: confirm budget cap at $900 by reviewing current finances.

## Week 2 — May 19-25 — Harness Reproduction

- [ ] Clone SlopCodeBench fork locally. Run their published baseline on 5 models × 5 problems (out of the 20).
- [ ] Verify forked harness reproduces upstream numbers within ±2 percentage points on `erosion_slope` and `verbosity_slope`. **If fail → pre-reg blocked until harness debugged.**
- [ ] Write `iboga-runner.py` — wraps SlopCodeBench harness with retrospective hook between checkpoints. Host-side session logging goes to `~/iboga-data/sessions/{trajectory-id}/`; nothing is written into the checkpoint workspace.
- [ ] **Pivotal verification**: confirm `~/iboga-data/sessions/*` is not mounted into the Docker workspace and cannot be traversed by AST-Grep or radon. Run no-hook baseline vs Arm 0 no-op hook → must produce identical metrics. Document in `iboga/harness-validation.md`.

## Week 3 — May 26 - June 1 — Prompt Templates

- [ ] Write Arm A (AA vocabulary) prompt template. Use provider-neutral JSON Schema enum validation with an Anthropic `tool_use` adapter for Claude. Test against Claude Opus on a synthetic diff.
- [ ] Write Arm B (vocabulary-neutral) prompt template. Same structure, swap vocabularies.
- [ ] Write Arm C (unstructured) prompt template. Same Berg induction, same corpus, free-form retrospective content inside a single structured-output wrapper, with ≤2000 token cap.
- [ ] Validate token budgets: Arm A and Arm B mean output tokens within ±15%; record Arm C distribution without padding. **Token-budget documentation in `iboga/arm-token-budget.md` — locked at pre-reg.**
- [ ] Test all three arms on a single SlopCodeBench problem with Claude Opus. Sanity check the output structure.
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
- 2026-05-12 — **Structured-output portability fix**: prompt schemas are canonical JSON Schema. Claude uses Anthropic `tool_use`; non-Anthropic models use provider adapters where available or JSON-only output with local validation/retry. Arm C gets a single structured wrapper field so transport shape is explicit without adding structure/vocabulary constraints.
- 2026-05-12 — **Pre-lock scaffold files created**: draft JSON schemas added under `schemas/`; `arm-token-budget.md`, `sae-features-decision.md`, and `annotator-rubric.md` created as lock-time documentation targets. Token-budget checklist corrected to A/B equivalence plus Arm C documentation, not all-arm output matching.
- 2026-05-12 — **GitHub setup complete**: created/verified `basedlsg/iboga`, forked `SprocketLab/slop-code-bench` to `basedlsg/slop-code-bench`, and pinned upstream HEAD `080922495aba9aedc4b7a6c80803bb5ffd301a49` in `prereg.md` and `harness-validation.md`.
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

1. Create `github.com/basedlsg/iboga` empty repo (5 min)
2. Fork SlopCodeBench locally (5 min)
3. Read SlopCodeBench paper in full this evening (2 hrs)
4. Tomorrow: start week-1 harness reproduction

**The pre-reg is drafted. The work is in the validation steps before lock.**
