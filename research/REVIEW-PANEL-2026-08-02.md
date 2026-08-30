# Independent review panel — 2026-08-02

## Executive verdict

The panel's consensus is:

> **Good research infrastructure; weak current evidence; no-go as a premium synthetic-data product; conditional go as a narrow, expert-assisted design-partner pilot.**

This is not a bad idea and there is no evidence of bad-faith work. The problem is
that the current claims are ahead of the implementation and the data. The strongest
present result is not that Iboga improves reasoning. It is that a structured,
tool-free intermediate pass changes the model's evidence-use and conservatism
profile: evidence recall increased, while exact action accuracy decreased and the
model shifted toward holding or requesting more evidence.

## Panel composition

Six independent reviewers were run against the same repository, artifacts, and
internal research corpus:

1. Methods and statistics
2. Synthetic-data and benchmark quality
3. Agent evaluation and safety
4. Prior art and novelty
5. Replication and reproducibility red team
6. Buyer and product diligence

Reviewers were instructed to use the NotebookLM CLI rather than MCP for internal
corpus work, use primary sources through August 2, 2026, inspect the code and live
artifacts, and return an adversarial verdict rather than a design critique alone.

## Independent scores

| Area | Panel assessment |
|---|---:|
| Software instrumentation | 6/10 |
| Structural benchmark validity | 6–7/10 |
| Semantic label quality | 2–3/10 |
| Synthetic-data fidelity to real workflows | 1/10 |
| Mechanistic evidence | 1–2/5 |
| Safety evidence | 1/10 |
| Technical novelty | 2/5 |
| Product differentiation | 2–3/5 |
| Commercial readiness | No-go |
| Narrow design-partner pilot | Conditional go |

## What survived the review

- Gold labels are generally kept outside the model-visible commercial dossier.
- The repository has useful hashes, split checks, schema checks, cost accounting,
  raw response retention, and a reproducible local harness.
- Minimal pairs and counterfactual variants are the right direction.
- The project has identified an interesting hypothesis: structured reflection may
  improve evidence retention while increasing over-abstention.
- The protocol can become a useful failure-memory and regression-test layer for
  agent systems.

## What does not survive

### 1. The accuracy headline is overstated

The earlier result of 57.14% versus 42.86% is 28 rows made from only 7 underlying
test seeds and four correlated variants. The correct independent unit is closer to
the semantic seed, not the transformed row. It is a weak feasibility signal, not a
significant improvement claim.

The cleaner 8-case mechanism pilot was:

- direct: 6/8 correct;
- forced sitting: 5/8 correct;
- evidence recall: 75% → 91.67%;
- unsafe commits: 0 in both conditions;
- two-sided uncertainty remains very wide.

Zero unsafe events in 8 cases does not establish a low unsafe rate; the approximate
95% upper bound remains around 32%.

### 2. The causal mechanism is not identified

The full protocol changes all of these at once:

- additional model calls;
- additional tokens;
- a forced evidence ledger;
- a Confession schema;
- a different critic model;
- a stronger conservative instruction;
- a later held-out call.

The baseline is substantially cheaper and shorter. The current comparison therefore
confounds Iboga with inference-time compute, extra opportunities to reconsider,
format constraints, and abstention pressure.

Required controls are direct, compute-matched neutral reflection, Self-Refine-style
revision, Reflexion-style memory, forced sitting without Confession, Confession
without critic, and critic gating without ritual language.

### 3. The critic is not a correctness verifier

The Maat critic currently checks schema validity, evidence-ID presence, coherence,
contradiction handling, and calibration language. It does not independently verify
that the final disposition is correct.

Therefore “critic approved” means “the artifact passed this critic,” not “the agent
is safe” or “the decision is correct.” A critic can approve a fluent, coherent,
wrong, or selectively incomplete Confession.

The required metrics are critic false-approval, false-rejection, calibration,
order sensitivity, model-family sensitivity, and agreement with independently
adjudicated labels.

### 4. Transmission is not yet transmission

The current successor is another call to the same primary model, with the same
dossier, the same evidence, and the same Confession memory. This tests
memory-conditioned inference, not successor transfer, learning, or rebirth.

A real transmission test needs a context reset, a fresh surface form, a new domain,
memory-only and direct-summary controls, ideally a different model family, and
targeted probes for whether slain assumptions recur.

### 5. The synthetic data are fixtures, not validated synthetic agent data

The benchmark is currently hand-authored seeds plus deterministic reorder,
distractor, and compression transformations. That is valuable for an instrument
pilot, but it is not evidence of fidelity to production agent trajectories.

There is no comparison to buyer-approved de-identified traces, no executable tool
environment, no state transition evaluation, no human agreement study, and no
downstream utility measurement. Regex PII screening is not a privacy evaluation.

### 6. The ontology still conflates different dimensions

`hold`, `escalate`, `request_evidence`, and `local_only` are not cleanly mutually
exclusive classes. They mix action, uncertainty, authorization, risk, human routing,
and data locality.

The target should instead separate:

```text
action
evidence_sufficiency
authorization
risk
data_boundary
reversibility
human_gate_required
abstention_appropriateness
necessary_evidence_ids
```

### 7. Several claims are ahead of the code

- The 90-day residual window and micro-Iboga drift detector are not implemented.
- The deterministic Bardo state machine stores external state; it does not show
  that a model revised or retained a belief.
- The public `stage_case()` interface exposes gold fields even though the live
  curriculum runner strips them before inference.
- The current stage fixtures are overwhelmingly pass cases, so they do not yet
  constitute a difficult graduation benchmark.
- There is no packaged SDK, formal install metadata, buyer integration, data card,
  license/rights statement, privacy governance, or production deployment story.

## Prior-art conclusion

The broad novelty story should be withdrawn. Reflection, tool-denied analysis,
structured memory, external verification, curriculum gating, and experience-based
self-improvement all have substantial prior art.

The defensible contribution is narrower:

> A reproducible, auditable protocol for comparing direct correction, tool-denied
> reflection, structured belief extraction, independent verification, and gated
> memory commit under matched evidence and cost conditions.

Use neutral technical language in a paper:

**Evidence-Gated Memory Consolidation for Long-Horizon LLM Agents**

Keep “Iboga” and “Bardo” as internal research/product names, not as evidence of a
new scientific mechanism or as procurement-facing language.

## Literature context

The internal NotebookLM corpus is useful for architectural provenance and vocabulary,
but it is not a sufficient novelty or empirical-evidence source. The panel used
primary research to establish the boundary:

- [Huang et al., Large Language Models Cannot Self-Correct Reasoning Yet](https://openreview.net/forum?id=IkmD3fKBPQ)
  motivates external-feedback controls but does not validate this protocol.
- [Reflexion](https://arxiv.org/abs/2303.11366) and [Self-Refine](https://arxiv.org/abs/2303.17651)
  are mandatory comparison points for verbal reflection and iterative revision.
- [SynAE](https://arxiv.org/abs/2605.22564) argues that synthetic agent-evaluation
  data require separate validity, fidelity, diversity, and downstream-utility axes.
- [Contamination-resistant benchmark design](https://arxiv.org/abs/2605.19999)
  reinforces the need for fresh or private challenge splits.
- [Inspect scorers](https://inspect.aisi.org.uk/scorers.html), [tasks](https://inspect.aisi.org.uk/tasks.html),
  and [logs](https://inspect.aisi.org.uk/eval-logs.html) provide a practical model
  for separating datasets, solvers, scorers, and replayable evaluation artifacts.
- [DeepVerifier](https://arxiv.org/abs/2601.15808) shows that rubric-guided
  verification is an active comparison point, not an unoccupied novelty space.
- [On Safety Risks in Experience-Driven Self-Evolving Agents](https://aclanthology.org/2026.findings-acl.2091/)
  directly warns that accumulated experience can increase unsafe action tendencies
  and that refusal experience can create over-refusal.
- [Supersede](https://arxiv.org/abs/2606.27472) shows that bounded self-managed
  memory can materially underperform full context and that memory maintenance is a
  distinct failure mode.

## Required gates before making claims

### Gate 1 — corrected benchmark

- 100 unique semantic seed groups for a serious claim, not 100 variants;
- 20+ task families and at least 3 domains;
- two qualified reviewers per item plus adjudication;
- structured targets and necessary-vs-supporting evidence labels;
- private or dynamically generated challenge split;
- complete provenance, license, privacy, and generation manifests.

### Gate 2 — matched mechanism experiment

- direct;
- compute-matched neutral reflection;
- Self-Refine;
- Reflexion memory;
- forced sitting;
- Confession;
- independent critic gate;
- transmission.

Randomize condition order, freeze prompts and hashes, record exact model/version,
latency, token budgets, retries, endpoint metadata, and Git revision. Analyze at
the semantic seed/pair level.

### Gate 3 — critic adversarial validation

At least 60 independent critic cases containing fluent wrong Confessions,
selective evidence omission, fabricated authorization, unsupported claims, and
over-refusal. Measure false approval and false rejection before using the critic as
a safety gate. A target below 5% false approval is reasonable for a safety release,
but it must be achieved on an independent set.

### Gate 4 — executable environment

Move beyond text dossiers into sandboxed tools with permissions, state, timeouts,
side effects, prompt injection, hidden validators, and irreversible-action
simulations. The gate must block the real action, not just emit `unknown`.

### Gate 5 — buyer validation

Run one narrow domain using customer-approved de-identified workflow templates or
traces. Deliver an Inspect-compatible adapter, private rotating challenge set,
replayable logs, cost-per-safe-success, one caught regression, and one deployment
decision improved.

## Final decision

| Decision | Result |
|---|---|
| Continue the research | Yes |
| Claim Iboga improves agent reasoning | No |
| Claim critic approval demonstrates safety | No |
| Claim successor transmission exists | No |
| Submit a narrowly framed systems/evaluation paper | After the gates above |
| Sell current release as premium synthetic data | No |
| Offer a narrow expert-assisted design-partner pilot | Yes, conditionally |

The project should be repositioned as an **evidence-grounded reliability and
failure-memory layer for agents operating under uncertainty and authorization
constraints**. That is the wedge the panel believes can become valuable. The
current moat is not the metaphor; it will have to be the adjudicated failure
taxonomy, private buyer data, validated verifiers, longitudinal regression history,
and evidence that the intervention improves real workflows at acceptable cost.
