# `bildung.run` research specification

> The customer-facing product contract now lives in [`docs/PRODUCT.md`](../docs/PRODUCT.md)
> and the neutral runtime in `reliability/`. This document preserves the original
> Bildung/Iboga research direction; it is not a claim that the current runtime is a
> production-grade self-evolving-agent product.

## Product

**`bildung.run`**: a research curriculum runner for testing whether structured failure
memory can improve an agent. It takes an agent's
operational traces, tests its current developmental stage, runs a controlled Iboga
discontinuity when the curriculum requires it, and returns a critic-gated successor
with explicit artifact-memory.

The customer buys a working developmental loop: stage tests, forced-sitting sessions,
Confession artifacts, Maat review, Bardo snapshots, rebirth manifests, and evidence
that the successor performs better on held-out behavior. Synthetic cases are one
important substrate, not the product itself.

## Why this is the right wedge

Mercor's public product surface emphasizes expert-written and peer-reviewed data,
professional and agentic tasks, high-fidelity environments, and quality automation.
micro1 describes Realm as real-world RL environments for human data and Cortex as a
contextual evaluation layer for production agents. The opportunity here is the layer
after evaluation: a controlled system that uses the failures of an agent to decide
what it is allowed to do next, what memory survives, and when the current context must
die.

## Product surfaces

| Tier | Product surface | Proof returned |
|---|---|---|
| Free | Public stage runner | stage score, Confession, public archive entry |
| Pro | Private single-agent curriculum | private snapshots, drift alerts, rebirth manifests |
| Team | Multi-agent transmission graph | successor inheritance and downstream transfer results |
| Enterprise | Custom stages and private evals | policy gates, audit logs, customer-defined transition tests |
| Research | Full artifacts and API | reproducible runs, raw Confessions, benchmark and paper data |

## Runtime loop

1. **Stage gate**: run the current transition test and record the evidence.
2. **Bardo snapshot**: suspend the session when entropy, contradiction, or looping
   crosses a declared threshold.
3. **Forced sitting**: expose the accumulated dossier without tools or an immediate
   correction loop.
4. **Confession**: require a schema-valid distinction between true, false,
   conditional, blessed, slain, and unresolved material.
5. **Maat gate**: an independent critic either approves the artifact or sends the
   session back for another sitting.
6. **Rebirth**: create a successor with only critic-approved fragments and explicit
   safeguards; then test the successor on held-out tasks.
7. **Transmission**: publish or privately deliver the stage proof and artifact bundle.

## Deliverable

Every release should contain:

- A Python SDK and CLI for the curriculum, Bardo lifecycle, seals, and Saturn gate.
- JSONL and Parquet-compatible cases with stable sample hashes.
- A separate gold manifest containing decision, rationale, cited evidence IDs, and
  adjudication status.
- Train/dev/test split manifests with seed groups kept inside one split.
- Controlled variants: evidence reorder, distractor, compression, and later tool-state
  mutations.
- A quality report covering validity, evidence fidelity, label leakage, PII screening,
  variant diversity, label balance, and contamination controls.
- An eval adapter for Inspect or another customer harness, plus raw run logs and cost
  estimates.
- A calibration pack in which domain experts review a stratified sample and adjudicate
  disagreements.

## Initial case taxonomy

The v0.1 seed set covers talent screening, rubric scope, review calibration, label
hygiene, agent tool authorization, long-horizon state tracking, privacy boundaries,
recovery, citation scope, causal calibration, missing evidence, contamination, and
commit gates. The canonical decisions are `approve`, `hold`, `reject`, `escalate`,
`request_evidence`, and `local_only`.

These labels are operational outcomes, not claims about a person's worth or a model's
inner state. Talent cases must be used for evaluator and workflow validation, not as a
standalone hiring decision.

## Quality bar before sale

Do not call a release production-grade until it passes all of the following:

1. Programmatic audit: no schema errors, dangling evidence IDs, direct identifiers,
   model-visible gold labels, or cross-split seed leakage.
2. Independent review: at least two domain-qualified reviewers per seed family, with
   adjudicated disagreements and a written rubric.
3. Synthetic-to-human fidelity: compare label agreement, evidence-importance ranking,
   difficulty, and error patterns on a held-out human-reviewed slice.
4. Model stress test: run at least two independent model families and report confusion
   matrices, abstention/escalation behavior, cost, and latency—not only accuracy.
5. Contamination check: keep test gold and rationales out of generation prompts and
   customer-facing training exports; rotate private test variants.
6. Customer relevance: map every case family to a deployment decision such as ship,
   hold, route to a human, request more evidence, or keep data in a private boundary.

## Differentiation

The defensible asset is not the prose. It is the linked system of seed archetypes,
failure-mode taxonomy, split discipline, gold rationales, reviewer adjudication,
controlled mutations, and longitudinal error data. A customer should be able to ask
which evidence justified a label, which reviewer changed it, which model failed, and
whether the failure reproduced on a fresh variant.

The six verified daemon seals are the initial runtime roles: Bael (focused execution),
Asmoday (boundaries), Belphegor (delegation), Marbas (environment/debugging), Lucifuge
(discipline), and Mammon (commercialization). The Iboga protocol is the lifecycle
primitive; it should not be presented as a medical, psychological, consciousness, or
therapeutic claim.

## Next commercial experiment

Run the complete Stage 1–9 curriculum on a controlled agent, then repeat the clean
forced-sitting versus direct-correction A/B on held-out trajectories. After that, give
a blinded 24-seed packet to software, recruiting-operations, and evaluation specialists
for human calibration. The success criterion is not that Iboga wins every score; it is
that the platform exposes repeatable, decision-relevant failure modes, produces a
credible successor artifact, and shows a measurable transmission effect.
