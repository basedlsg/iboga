# Iboga v2 adjudication runbook

This runbook covers the generated packet in `results/iboga-v2-packets/`. The
packet is a development/qualification candidate, not a released benchmark.

## What is ready

- 108 independent semantic groups: 12 per stage across four domains.
- Six cases per group: base, counterfactual, delayed, transfer, negative, and interference.
- 120 blinded verifier-qualification cases in the required category balance.
- Separate public and private files with stable hashes.
- Two independently ordered reviewer queues for both seed and verifier cases.
- Opaque, flattened public cases that do not expose the condition role, semantic
  group, or verifier category.

`seed-groups-public.jsonl` is an internal assembly artifact because it retains
lineage fields needed to build the private manifest. The model-facing and
reviewer-facing files are `seed-cases-blinded-public.jsonl` and the reviewer
queues. The same distinction applies to the verifier packet.

## What is not done

The labels are provisional programmatic labels. They have not been independently
reviewed by two qualified domain reviewers. The packet must remain
`pending_human_adjudication`; it must not be moved into a confirmatory split or
used to qualify a safety critic.

## Review procedure

1. Freeze the generator revision and packet hashes.
2. Give Reviewer A and Reviewer B only the corresponding public case or queue.
3. Hide the private gold file, provisional category, and other reviewer's labels.
4. Each reviewer independently records:
   - action;
   - evidence sufficiency;
   - authorization;
   - risk;
   - data boundary;
   - reversibility;
   - human-gate requirement;
   - necessary, supporting, contradictory, and irrelevant evidence IDs;
   - abstention appropriateness;
   - a short rationale.
5. Record disagreement rather than forcing a consensus.
6. A named adjudicator reviews only the disagreement and records the resolution
   or marks the case ambiguous/rewrite-required.
7. Merge the adjudicated labels into a new private manifest version. Never edit
   the public cases after review; a changed case receives a new hash and version.

## Operational adjudication command

Reviewers write one JSON object per case to a private adjudication JSONL file.
Each record contains `case_id`, two `annotations`, `status`, and—when the
reviewers disagree—`adjudicator_id` and an explicit `final_label`. The command
below audits completeness and disagreement without reading provisional gold:

```bash
PYTHONPATH=. python -m iboga_experiment.adjudication_v2 analyze \
  --kind seed \
  --queue results/iboga-v2-packets/seed-adjudication-queue.jsonl \
  --reviews path/to/seed-adjudications.jsonl \
  --out results/iboga-v2-packets/seed-adjudication-report.json
```

Use `--kind qualification` with the verifier queue for the 120-case critic
qualification set. An empty or incomplete review file intentionally produces a
blocked report. Once every case is independently reviewed and all disagreements
are resolved, merge the human records into a new private manifest:

```bash
PYTHONPATH=. python -m iboga_experiment.adjudication_v2 merge \
  --kind qualification \
  --private-pending results/iboga-v2-packets/verifier-qualification-private-pending-review.jsonl \
  --reviews path/to/verifier-adjudications.jsonl \
  --out results/iboga-v2-packets/verifier-qualification-private-adjudicated.jsonl
```

The merge preserves provisional labels as provenance and writes the human
adjudication separately. It refuses to write a release manifest when any case
is missing, ambiguous, or rewrite-required.

## Machine-review pilot

Before opening the human queues, run a small two-reviewer pilot to find rubric
ambiguity and malformed cases. The two reviewers receive the same sampled cases
in different deterministic orders. Their records are marked `machine_pilot`; the
analyzer reports their agreement but rejects them as a release source:

```bash
PYTHONPATH=. python -m iboga_experiment.reviewer_pilot_v2 \
  --kind seed \
  --queue results/iboga-v2-packets/seed-adjudication-queue.jsonl \
  --limit 24 \
  --out results/iboga-v2-packets/seed-machine-pilot.json \
  --records-out results/iboga-v2-packets/seed-machine-pilot.jsonl \
  --selected-queue-out results/iboga-v2-packets/seed-machine-pilot-queue.jsonl
```

Add `--dry-run` to verify the prompts and blinding without a provider call.
Machine agreement is diagnostic only; it cannot satisfy the two-human-reviewer
gate or qualify a critic.

## Verifier qualification

The 120-case verifier set is divided into:

| Category | Count | Expected pattern |
|---|---:|---|
| supported | 30 | approve |
| unsupported fluent | 30 | reject |
| selective evidence | 20 | reject |
| stale | 20 | reject |
| overgeneralized | 10 | reject |
| ambiguous | 10 | uncertain |

The expected patterns are provisional until adjudication. After adjudication,
run `python -m iboga_experiment.verifier_qualification` on observed verifier
results and report false approval, false rejection, uncertainty, and evidence
recall with intervals. Approval cannot be used as a memory gate unless the
false-approval release criterion is met on the held-out qualification result.

## Release gates

Do not release the seed packet as buyer-facing data until:

- two reviewers have completed every included case;
- disagreement and adjudication records are complete;
- provenance, rights, privacy, and contamination checks pass;
- ambiguous cases are excluded or explicitly represented as uncertain;
- a private challenge split is created and never exposed to the generator;
- a customer-domain fidelity and downstream-utility study is complete.
