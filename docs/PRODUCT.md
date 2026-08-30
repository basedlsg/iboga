# Evidence-grounded agent reliability

## Product definition

This project is an evaluation and runtime reliability layer for agents operating
under uncertainty, authorization constraints, and real-world side effects.

It converts a workflow into five inspectable objects:

1. task;
2. environment;
3. trajectory;
4. output/action proposal;
5. deterministic and model-assisted verifiers.

The same case can be used for offline regression, production grading, model/prompt
comparison, and runtime quality gates. This matches the current enterprise eval
market's direction: Mercor describes reusable tasks, environments, trajectories,
outputs, and verifier-backed judgments; micro1 describes real-workflow evaluation,
failure diagnosis, expert data, and post-launch monitoring.

The Iboga/Bardo protocol is retained as one experimental strategy for producing and
testing structured failure memory. It is not the product claim, a medical claim, or
evidence of consciousness.

## What a buyer receives

- private, versioned task and environment definitions;
- structured, multi-axis rubrics rather than a single opaque label;
- expert-reviewed gold manifests with adjudication records;
- deterministic permission and data-boundary gates;
- synthetic cases linked to source archetypes and transformations;
- executable regression cases and Inspect-compatible exports;
- replayable trajectories, verifier outputs, costs, latency, and failure taxonomy;
- a rotating private challenge set unavailable to the evaluated model.

The reference runtime also supports declared tool scopes, append-only trajectory
events, independent deterministic verifiers, and explicit two-reviewer adjudication
records. These are integration primitives; they are not a substitute for customer
domain validation.

## Product wedge

Do not compete as a generic synthetic-data vendor. Start with one high-cost failure
family, such as unauthorized writes, privacy-boundary violations, unsupported
release decisions, or stale-memory actions. Use customer-approved de-identified
workflow templates and produce a private regression suite that catches a concrete
failure before rollout.

## Claims policy

Allowed:

- “evidence-grounded reliability gate”;
- “critic-assisted artifact review”;
- “deterministic side-effect mediation”;
- “private regression suite built from adjudicated failure modes.”

Not allowed without new evidence:

- “self-evolving” as a demonstrated capability;
- “transmission” or “rebirth” as measured learning;
- “safe because the critic approved it”;
- “human-equivalent synthetic data”;
- medical, therapeutic, consciousness, or alignment claims.
