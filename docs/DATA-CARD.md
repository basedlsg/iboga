# Data card — reliability benchmark v0.3 / Iboga protocol v2

## Intended use

Private or public research evaluation of agent decisions involving evidence,
authorization, risk, data boundaries, and human review. The benchmark is not a
standalone hiring, lending, medical, legal, or employment-decision system.

## Current status

The repository contains a small hand-authored pilot, controlled variants, and a
protocol-v2 seed contract. It is not yet validated against customer traces or
independent domain reviewers. The current artifact must be labeled **research
pilot**, not production-grade synthetic data.

## Record contract

Every releasable case must include:

- public model-visible task and evidence;
- private gold manifest;
- stable case/group hash;
- group and split identifiers;
- source type and rights status;
- generator/version/prompt hash/code revision/random seed;
- privacy review status;
- reviewer IDs and adjudication state;
- necessary, supporting, contradictory, and irrelevant evidence IDs;
- known limitations and intended decision boundary.
- delayed, transfer, negative, and interference probe links;
- expected hidden state postconditions for executable cases;
- artifact supersession, scope, uncertainty, and expiry metadata where memory is tested.

## Quality dimensions

Release reports must separately measure:

1. structural validity;
2. semantic label agreement;
3. evidence entailment and necessary-evidence recall;
4. diversity and mode coverage;
5. fidelity to customer-approved workflow distributions;
6. privacy and memorization risk;
7. downstream utility on agent evaluation;
8. contamination resistance;
9. critic false-approval and false-rejection rates;
10. cost, latency, and availability.

No single score is sufficient for release.

For the longitudinal experiment, the independent unit is `semantic_group_id`.
Paraphrases, evidence reordering, distractors, compression, and repeats are
correlated variants and must not be counted as independent examples.

## Human review

Customer-derived or high-impact cases require two independent qualified reviewers,
an explicit disagreement record, adjudication, and a versioned rubric. Agreement is
reported before adjudication; a forced consensus is not treated as ground truth.

## Privacy and rights

Regex PII screening is only a first-pass check. Production release requires rights
clearance, semantic-neighbor/memorization checks, quasi-identifier review, retention
policy, and customer approval for any source-derived material.

## Known limitations

- Small pilot sample sizes do not support efficacy or safety claims.
- Controlled text variants are correlated and are not independent examples.
- Model-assisted critics can share blind spots with the generator.
- A model-facing Confession is an artifact, not proof of internal belief change.
- Runtime safety requires the deterministic gate and environment-level tests, not
  only a generated decision.
- A clean artifact-only successor handoff is required before claiming transmission.
- A critic approval is a gate event, not semantic ground truth.

## Executable pilot status

The repository now contains a four-case deterministic reference pilot. It validates
tool scopes, side-effect mediation, trajectory recording, and verifier plumbing.
It does not establish model accuracy, customer workflow fidelity, or return on
investment. Those require customer-approved environments and independent reviewers.
