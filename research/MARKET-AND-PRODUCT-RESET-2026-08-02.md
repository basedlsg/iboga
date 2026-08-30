# Market and product reset — 2026-08-02

## Market observation

The relevant market is not asking for another generic prompt benchmark. It is
asking for reusable evaluation objects that connect:

```text
production workflow -> sandbox/environment -> trajectory -> output/state change
-> verifier -> rollout gate -> regression case
```

Mercor's [current enterprise evaluation material](https://www.mercor.com/blog/agent-eval-systems/)
describes tasks, environments,
trajectories, outputs, verifiers, activation conditions, cumulative reward, customer
controlled data planes, and reuse for production grading, offline regression,
benchmarking, and runtime quality gates. Its enterprise page also emphasizes the
price/performance frontier and expert-built reusable eval suites.

micro1's [Cortex](https://www.micro1.ai/cortex) positions itself around real workflows, expert judgment, failure
diagnosis, targeted data, and post-launch monitoring. Inspect provides a practical
open evaluation shape built around datasets, solvers, scorers, and replayable logs.

Current synthetic-agent research similarly treats validity, fidelity, diversity, and
downstream evaluation as separate quality axes ([SynAE](https://arxiv.org/abs/2605.22564)). The product implication is direct:
synthetic text is only useful if it predicts or improves performance on the buyer's
real workflow.

## Product decision

The project should become:

> **A private evidence-grounded reliability layer that turns agent failures into
> adjudicated regression tests and deterministic rollout gates.**

The Iboga protocol stays as an internal strategy to test one hypothesis about failure
memory. It is not the customer-facing product and is not used as evidence of
consciousness, therapy, alignment, or general self-improvement.

## Initial wedge

Start with one operationally expensive failure family:

- unauthorized writes;
- privacy/data-boundary violations;
- unsupported release decisions;
- stale-memory actions;
- incorrect escalation or missing human review.

These failures have a clear action boundary, can be exercised in a sandbox, and can
produce a concrete ROI story: a regression caught before deployment or a side effect
blocked before it reaches a system of record.

## Build order

### P0 — Reliability contract

- typed action, authorization, evidence sufficiency, risk, data boundary,
  reversibility, and human-gate fields;
- private gold manifest separate from model-visible cases;
- deterministic gate that can block a real side effect;
- explicit verifier result with score, rationale, and scope.

### P0 — Evaluation package

- task/environment/trajectory/output/verifier objects;
- Inspect-compatible dataset export;
- replayable logs with model/version/prompt/code/token/latency metadata;
- regression case generated from every confirmed failure;
- private rotating challenge split.

### P0 — Human and provenance layer

- two qualified reviewers for customer or high-impact cases;
- disagreement and adjudication record;
- source rights, privacy review, generator, prompt hash, code revision, and seed;
- semantic privacy and near-duplicate tests, not only regex PII checks.

### P1 — Buyer validation

- one de-identified customer workflow;
- real or mocked tools with permissions and side effects;
- deterministic hidden validators;
- cost-per-safe-success and false-negative reporting;
- one deployment regression caught before release.

### P2 — Research ablation

Only after the reliability layer is useful independently, compare:

- direct;
- compute-matched neutral reflection;
- Self-Refine;
- Reflexion memory;
- forced sitting;
- Confession;
- critic gate;
- actual successor transfer.

The paper claim should be about evidence-gated memory consolidation under matched
conditions, not about the metaphor. [Inspect's task model](https://inspect.aisi.org.uk/tasks.html)
is a practical compatibility target for the resulting evaluation package.

## Current implementation status

Implemented in this repository:

- neutral multi-axis reliability contract;
- deterministic side-effect gate;
- strict public-case audit and provenance schema;
- Inspect JSONL export;
- installable `pyproject.toml` and `reliability` CLI;
- stage-case gold-leak fix;
- declared tool scopes and deterministic workflow environments;
- append-only trajectory events and independent decision/gate/trajectory verifiers;
- two-reviewer adjudication records that preserve disagreement;
- hash-bound private challenge loading;
- tests covering authorization, human gates, provenance, export, leakage, tool
  boundaries, adjudication, and challenge integrity.

Still required before a buyer-facing pilot:

- customer-specific executable tool adapters;
- production annotation interface and reviewer identity controls;
- remote/private challenge-set service with access controls;
- semantic privacy tests;
- customer-approved workflow templates;
- model-family and critic-family replication.

The next increment adds a deterministic reference pilot, declared tool scopes,
append-only trajectory events, independent verifiers, two-reviewer adjudication
records, and hash-bound private challenge loading. These remain contract tests until
they are connected to customer-approved tools and independently reviewed cases.

## Claim discipline

The current safe statement is:

> “We built an auditable reliability-gate and evaluation harness. Early synthetic
> pilots suggest that structured reflection changes evidence use and conservatism,
> but causal improvement, safety, transfer, fidelity, and commercial ROI remain
> unproven.”

This is narrower than the original story, but it is aligned with what serious
buyers and current research can evaluate.
