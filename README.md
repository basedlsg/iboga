---
title: Iboga — Research Program
status: active
created: 2026-05-12
parent: silentvault (workshop paper, 2026)
substrate: SlopCodeBench (arXiv 2603.24755)
deployment_vignette: Nemo Compliance (production at ying.gamechangerlabs.io)
target_venue: ICLR 2027 workshop (RSI or Lifelong Agents)
tags: [iboga, research, agents, introspection]
---

# Iboga — Research Program

**One-sentence framing**: Closed-vocabulary structural constraints as instruments for shaping and measuring LLM self-report content under iterated software development.

**Lineage**: silentvault (2026 workshop paper, N=167 meditations, 3-method triangulation → cluster purity 0.69 vs 0.25 random). Iboga extends silentvault from passive meditation to active iterative-development substrate.

## Files in this folder

| File | Purpose |
|---|---|
| `prereg.md` | The v0.5 pre-registration document. Lock target 2026-07-01. Hybrid ICLR RSI operator-card + AsPredicted hypothesis block. |
| `next-steps.md` | Pre-lock checklist with dates. What needs to happen between now and 2026-07-01. |
| `slopcodebench-study.md` | SlopCodeBench paper notes and harness-risk checklist. |
| `arm-templates.md` | Arm A/B/C prompt templates and structured-output schemas. |
| `schemas/` | Draft provider-neutral JSON Schema files for Arms A/B/C. |
| `arm-token-budget.md` | Token-budget validation scaffold for pre-lock prompt checks. |
| `arm-assignment-spec.md` | Deterministic `arm-assignment.json` format and validation rule. |
| `scripts/generate_arm_assignment.py` | Standard-library generator for deterministic arm-assignment files. |
| `scripts/prelock_sanity.py` | Local sanity checks for draft artifacts. |
| `scripts/inspect_slopcodebench_repo.py` | Helper for later SlopCodeBench fork inspection. |
| `scripts/compare_metric_outputs.py` | Helper for reproduction metric comparisons. |
| `failure-types.md` | Neutral F0-F10 taxonomy for recurrence annotation. |
| `annotator-rubric.md` | One-page blinded annotator instruction sheet draft. |
| `analysis-plan.R` | Pre-registered analysis script draft. |
| `power-calc.R` | Power-analysis script draft. |
| `sae-features-decision.md` | SAE feature-catalog filter and lock decision scaffold. |
| `sprocketlab-email.md` | SprocketLab transparency email draft. |
| `harness-validation.md` | Week 2 validation log for SlopCodeBench, `scb-check`, and runner-hook inspection. |
| `provider-routing.md` | Non-Anthropic provider routing notes for OpenRouter, Gemini CLI OAuth, Meta Llama Developer API, and Jules. |
| `jules-tasks.md` | Ready-to-dispatch Jules task prompts (J6-J9) for engineering coordination once `basedlsg/iboga` is public. |
| `handoff-prompt.md` | Self-contained continuation prompt for future chats. |
| `README.md` | This file. |

## Where Iboga sits in the broader project graph

```
silentvault (2026 workshop paper) ──── methodology lineage
                                        │
                                        ▼
                  Iboga v0.5 ── 4 models × 3 arms × SlopCodeBench
                                        │
                                        ├─ primary: structural erosion + solve rate
                                        ├─ secondary: vocabulary differentiation
                                        └─ exploratory: SAE mechanism (Llama-3.1-8B)
                                        
                  Nemo Compliance ───── deployment vignette (one chapter)
                  (Chinese energy/transport compliance Q&A, production)
```

## Research arc decisions (locked unless flagged)

- **Substrate**: SlopCodeBench, not Nemo. Nemo becomes deployment case study only.
- **Models** (locked OpenRouter slugs): `anthropic/claude-opus-4.7` + `qwen/qwen3-32b` + `meta-llama/llama-3.1-8b-instruct` + `deepseek/deepseek-chat-v3-0324`. Four families, three vendors.
- **Arms**: 3 — Iboga (AA vocabulary), Vocabulary-Neutral (coding-jargon), Unstructured.
- **Primary DV**: structural-erosion slope + solve-rate (co-primary, non-inferiority).
- **Mechanism**: SAE on Llama-3.1-8B via Goodfire's open weights at layer 19. Exploratory, with pre-registered direction.
- **Operator**: solo. Blinding via deterministic hash-based arm assignment.
- **Budget**: $810 across 18 weeks.
- **Submission window**: ICLR 2027 workshop, 2026-09-25. Fallback NeurIPS SafetyXAI October.

## Tool stack (original plan, preserved)

- **OpenRouter** — pre-registered route for the 4 trajectory models. Locked.
- **Gemini CLI** — free OAuth-backed validation route (proven on `xjq` checkpoint 1). Used for harness debugging, not as a trajectory model.
- **Jules** — engineering coordinator for J6-J10 coding tasks (hook implementation, `iboga_runner.py`, SAE collection script, metric reproduction harness, DeepSeek slug resolution). Same way silentvault used it for J1-J5. Not a trajectory model.
- **HuggingFace Router + Together AI** — fallbacks for Llama / Qwen if OpenRouter has issues.

See `provider-routing.md` for the full routing table and the Jules task list.

## Status flags

- 🟢 v0.5 pre-reg drafted (2026-05-12)
- 🟡 Pre-lock validation steps pending (see `next-steps.md`)
- ⚪ OSF account creation pending
- 🟢 SlopCodeBench fork created and upstream commit pinned (2026-05-12)
- 🟢 SlopCodeBench metric and hook insertion inspection documented (2026-05-12)
- 🟢 Local SlopCodeBench dependencies and managed problem catalog installed under this project folder (2026-05-12)
- 🟢 Non-Anthropic `lite_under20` dry-run route verified through Gemini CLI OAuth (`gemini_auth/gemini-2.5-flash-lite`) on 2026-05-13
- 🟢 Gemini SlopCodeBench Docker image built successfully on 2026-05-13 after Docker disk cleanup
- 🟡 Actual no-treatment `xjq` Gemini run partially validated the path: checkpoint 1 completed/evaluated; checkpoint 2 hit Google capacity errors and was stopped
- 🟡 OpenRouter route identified; `OPENROUTER_API_KEY` is not exported in this shell yet
- 🟡 Baseline reproduction and Arm 0 hook-neutrality gates pending
- ⚪ SAE feature catalog pull pending
- ⚪ External annotator recruitment pending
- ⚪ Pre-reg lock target 2026-07-01

## Scope (isolation policy)

**This project is self-contained.** When working on Iboga, Claude reads and writes only files under `/Users/carlos/Brain/OBSIDIAN/projects/iboga/`. No reads from other project folders, no reads from `inbox/`, `notes/`, `ideas/`, or `archive/`. See `CLAUDE.md` in this folder for the enforced scoping rule.

The only exception is **Nemo Compliance as deployment vignette** — at write-time of the final paper, ≤1 chapter draws on `/Users/carlos/NEMU-TEST-main/` (the actual code, not the vault folder). That happens late and is flagged explicitly.

Cross-project capture (silentvault learnings, Brain inbox material, etc.) is done by **manual copy into this folder**, never by Claude reading siblings.
