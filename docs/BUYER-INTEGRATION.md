# Buyer integration contract

## Minimum integration

The customer supplies one workflow definition:

- task instruction;
- mock or sandbox environment;
- tools and permission scopes;
- success criteria;
- high-cost failure modes;
- domain reviewers.

The system returns:

- a versioned task/environment/trajectory bundle;
- verifier scores and explanations;
- deterministic gate outcomes for proposed side effects;
- regression cases for each confirmed failure;
- cost, latency, and model comparison;
- private challenge-set results.

## Runtime flow

```text
agent request
  -> trajectory recorder
  -> output/action proposal
  -> deterministic reliability gate
       -> allow
       -> human review
       -> block
  -> verifier scores
  -> regression case on confirmed failure
```

The model may propose an action. It may not override the gate. A model critic is an
additional verifier, not the authority that grants permission.

## Executable reference runtime

The repository includes a deterministic reference pilot with four customer-shaped
failure families: unsupported release, privacy-boundary export, authorized internal
write, and stale workflow completion.

```bash
PYTHONPATH=. python -m reliability pilot \
  --out results/reliability-pilot-v0.1.json
```

The pilot is a contract test for the runtime, not a model-quality result. A real
customer adapter must supply its own tool implementations, reviewer rubric, and
independent hidden validators.

The runtime records input, decision, tool call, gate, tool result, and verifier
events. The independent verifier suite scores decision axes, evidence availability,
gate outcomes, effect application, and trajectory completeness separately.

## Expert adjudication

Customer-derived or high-impact cases require two reviewer annotations, explicit
rationales, disagreement preservation, and a named adjudicator. A forced consensus
is not silently converted into ground truth.

## Private challenge boundary

The public case file is delivered to the evaluated agent. The gold manifest remains
inside the scoring process and is hash-bound to the public case. Validate the local
boundary with:

```bash
PYTHONPATH=. python -m reliability challenge-audit \
  results/commercial-benchmark-v0.2.public.jsonl \
  results/commercial-benchmark-v0.2.gold.jsonl
```

## Inspect compatibility

The repository exports public cases to Inspect JSONL. The intended customer mapping
is:

- case/environment → Inspect dataset/task;
- agent scaffold → Inspect solver;
- deterministic and model-assisted checks → Inspect scorers;
- trajectory and verifier records → Inspect logs.

Use:

```bash
PYTHONPATH=. python -m reliability inspect-export \
  results/commercial-benchmark-v0.2.public.jsonl \
  results/commercial-benchmark.inspect.jsonl
```

The export contains no gold labels. Gold data remains in a private scoring service
or adjudication manifest.
