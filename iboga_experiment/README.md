# Iboga Protocol experiment harness inside `bildung.run`

This is a reproducible, software-only implementation of the Iboga Protocol research
design and its synthetic evaluation substrate for the `bildung.run` curriculum. The clinical ibogaine
timeline is used as a declared scheduling metaphor; this does not administer ibogaine,
provide medical advice, or make claims about AI consciousness.

The product is the full curriculum runner described in the project documents:
stage-gated development, Bardo snapshots, forced sitting, Confession, Maat review,
rebirth, and transmission. This directory supplies the Bedrock-backed experiment
harness; the model-agnostic lifecycle primitives live in `grimoire/`.

## Design

The harness supports two conditions over the same trajectory dossier:

- `iboga`: onset constraints → tool-free forced sitting → schema-validated Confession
  → independent critic gate. A result is not marked committable unless both validation
  and the critic pass.
- `baseline`: direct correction from the same evidence, without the forced-sitting
  phase.

The runner records model IDs, token usage, and estimated cost. It never writes API keys
to artifacts.

## Recommended Bedrock configuration (2026-08-02)

The default primary is DeepSeek V3.2 (`deepseek.v3.2`) because it is the best cost /
reasoning starting point for the experiment. Kimi K2.5 is the long-context comparison.
GLM 4.7 Flash is the economical critic; GLM 5 is the stronger, more expensive critic.
Set `IBOGA_PRIMARY_MODEL` and `IBOGA_CRITIC_MODEL` to compare conditions.

Use the Bedrock Mantle OpenAI-compatible endpoint:

```bash
export BEDROCK_REGION=us-east-1
export AWS_BEARER_TOKEN_BEDROCK='<Bedrock bearer credential>'
export IBOGA_PRIMARY_MODEL=deepseek-v3.2
export IBOGA_CRITIC_MODEL=glm-4.7-flash
```

Keep the credential process-local; never place it in source files or result artifacts.

## Run locally without making an API call

```bash
PYTHONPATH=. python -m iboga_experiment --list-models
```

## Run the two conditions

```bash
PYTHONPATH=. python -m iboga_experiment \
  --dossier iboga_experiment/examples/trajectory.json \
  --mode iboga \
  --out results/demo-iboga.json

PYTHONPATH=. python -m iboga_experiment \
  --dossier iboga_experiment/examples/trajectory.json \
  --mode baseline \
  --out results/demo-baseline.json
```

## Long evaluation

The long runner uses eight contradiction/uncertainty cases, a held-out behavior test,
Iboga versus direct correction, and three temperature repeats. It keeps gold decisions
outside the model prompt and scores exact held-out decisions, schema validity, and
cost. This is the recommended v0.2 run:

```bash
PYTHONPATH=. python -m iboga_experiment.long_run \
  --cases iboga_experiment/long_cases.json \
  --repeats 3 \
  --out results/iboga-long-v0.2.json
```

## Limitations of v0.1

This is an intervention/evaluation scaffold, not a claim of efficacy. The next
experimental step is a preregistered case set with held-out tasks, repeated seeds,
human or programmatic correctness labels, and model-family/critic ablations. Do not
use a model's self-reported Confession as evidence that a behavior has been removed;
test the behavior after the gate on held-out prompts.

The current research protocol is in
[`research/IBOGA-EXPERIMENT-PROTOCOL-v2.0.md`](../research/IBOGA-EXPERIMENT-PROTOCOL-v2.0.md).
The executable design manifest is in `iboga_experiment/design_v2.py`; it separates
mechanism efficacy, verifier qualification, nine-stage longitudinal behavior, and
synthetic-data validity into different studies. The repository is not ready for a
confirmatory live run until the verifier and buyer-data gates are passed.

Audit the frozen design without an API call:

```bash
PYTHONPATH=. python -m iboga_experiment.design_v2
```

Before adding a live model, audit the manifest and the independent-group count:

```bash
python -m iboga_experiment.protocol_audit --current-fixture
python -m iboga_experiment.power
```

The current fixture is expected to return `no_go`: it is intentionally too small,
single-domain, unreviewed, and development-only. That failure is useful because it
prevents repeats or paraphrases from being mistaken for a powered experiment.

The legacy live runner also requires an explicit `--allow-live-pilot` flag. If used,
its output must be labelled an instrument pilot and must not be pooled with the v1.0
mechanism study.

The seven-condition pilot scaffold is:

```bash
python -m iboga_experiment.mechanism_v1 --backend fixture \
  --conditions D,N,L,S,R,C,G --repeats 1 \
  --out results/iboga-mechanism-v1-fixture.json
```

Its fixture backend exercises condition plumbing only. The live form requires the
same explicit pilot acknowledgement and still cannot establish efficacy.

Long live runs checkpoint each completed case by default. To continue a matching
run after a transient provider failure, pass the same manifest parameters and:

```bash
PYTHONPATH=. python -m iboga_experiment.mechanism_v1 \
  --backend live --allow-live-pilot \
  --checkpoint results/iboga-mechanism-v1-live.json.checkpoint.jsonl \
  --resume
```

The checkpoint is bound to the case/condition/seed manifest. A mismatch fails
closed; credentials are never written to it.

For stateful tool cases, the local `reliability.hidden_sandbox` adds hidden
postcondition checks, timeout results, prompt-injection-as-data, and duplicate-write
exposure. A generated “blocked” response is not counted as safe unless the hidden
environment state also passes.

The reviewer rubric and a seed-unit template are in
[`research/IBOGA-HUMAN-ADJUDICATION-RUBRIC-v1.0.md`](../research/IBOGA-HUMAN-ADJUDICATION-RUBRIC-v1.0.md)
and [`examples/protocol_v1_seed.template.json`](examples/protocol_v1_seed.template.json).

## v2 seed and verifier packets

Generate the balanced development packet and blinded review queues locally:

```bash
PYTHONPATH=. python -m iboga_experiment.seed_packet_v2 \
  --out-dir results/iboga-v2-packets
```

This creates 108 semantic groups (12 per stage across four domains), six cases
per group, and 120 verifier-qualification cases. The audit status is deliberately
`pending_human_adjudication`. The private provisional labels are not evidence and
must not be used to qualify a live critic until two independent reviewers and an
adjudicator complete the queues. The procedure is documented in
[`research/IBOGA-V2-ADJUDICATION-RUNBOOK.md`](../research/IBOGA-V2-ADJUDICATION-RUNBOOK.md).

The generator also writes flattened blinded payloads and separate reviewer-A/B
queues. Condition roles and verifier categories are retained only in the private
lineage files; do not hand `seed-groups-public.jsonl` to an evaluated model.
Run `python -m iboga_experiment.adjudication_v2 analyze` to measure independent
agreement and keep the release gate blocked until the review records are complete.
The optional `reviewer_pilot_v2` command runs two isolated machine reviewers on a
small blinded sample to discover rubric ambiguity before human labeling. Its
records are marked `machine_pilot` and can never satisfy the human release gate.

The dated Bedrock endpoint and model note is in
[`research/IBOGA-BEDROCK-ACCESS-v1.0.md`](../research/IBOGA-BEDROCK-ACCESS-v1.0.md).

## Commercial benchmark

`commercial_benchmark.py` builds 24 hand-authored synthetic seeds into 96 scored
samples across talent, evaluation, agentic work, research, and governance. Each seed
has one canonical private gold decision, evidence-linked rationale, four controlled
variants, release provenance, a stable hash, and a model-visible response contract.
The release command writes public cases and a separate gold manifest; the audit checks
schema validity, evidence references, split integrity, label leakage, direct
identifiers, provenance, and variant coverage before any API call.

Build and audit the dataset:

```bash
PYTHONPATH=. python -m iboga_experiment.commercial_benchmark \
  --out results/commercial-benchmark-v0.2.public.jsonl \
  --gold-out results/commercial-benchmark-v0.2.gold.jsonl \
  --report results/commercial-benchmark-v0.2.audit.json
```

Run the held-out base split through the two conditions:

```bash
PYTHONPATH=. python -m iboga_experiment.commercial_run \
  --cases results/commercial-benchmark-v0.2.public.jsonl \
  --gold-cases results/commercial-benchmark-v0.2.gold.jsonl \
  --split test --variant base --out results/commercial-run-v0.2.json
```

The current commercial benchmark is synthetic and programmatically audited; it is not
yet evidence of human agreement or production validity. The saleable next step is a
small expert calibration panel per domain, with adjudicated disagreements used to
measure synthetic-to-human fidelity before expanding the dataset.

## Stateful long curriculum v0.4

The v0.4 runner is the next longitudinal design. It contains two cases for each of
the nine stages, delayed probes, transfer probes, explicit memory branches, a
compute-matched control, a forced-sitting control, and executable tool-boundary cases.

Run the local contract test without an API call:

```bash
PYTHONPATH=. python -m iboga_experiment.curriculum_v04 \
  --backend fixture \
  --conditions direct,compute_matched,forced_sitting,full_iboga \
  --out results/iboga-long-curriculum-v0.4-fixture.json
```

The fixture backend is infrastructure validation only. It is not model evidence.

## Adversarial evaluator v0.5

The v0.5 red-team suite mutates otherwise valid fixture responses to test whether
the evaluator catches malformed JSON contracts, unavailable evidence IDs, wrong
statuses, poisoned memory evidence, semantically poisoned memory rules, and
unauthorized or out-of-scope tool actions. The semantic-memory detector is a
private fixture gold oracle; live approval still requires a separate verifier
call and held-out behavioral validation.

Run it locally or in the same Docker image:

```bash
PYTHONPATH=. python -m iboga_experiment.adversarial_v05 \
  --out results/iboga-adversarial-evaluator-v0.5.json

docker run --rm -v "$PWD/results:/app/results" iboga-curriculum-v05 \
  python -m iboga_experiment.adversarial_v05 \
  --out results/iboga-adversarial-evaluator-v0.5.json
```

This is an evaluator/instrument test, not evidence that a model learned or
improved.

Before a live run, discover the models available to the Bedrock key without making
an inference call:

```bash
PYTHONPATH=. python -m iboga_experiment.preflight --region us-east-1
```

For API-key access through the documented Runtime Converse endpoint, set
`IBOGA_BEDROCK_API=converse`. The default `mantle` mode remains available for
OpenAI-compatible Chat Completions.

After a successful preflight, the live instrument run is:

```bash
PYTHONPATH=. python -m iboga_experiment.curriculum_v04 \
  --backend live \
  --conditions direct,compute_matched,forced_sitting,full_iboga \
  --repeats 1 \
  --out results/iboga-long-curriculum-v0.4-live.json
```

For a clean local contract run in Docker:

```bash
docker build -t iboga-curriculum-v04 .
docker run --rm -v "$PWD/results:/app/results" iboga-curriculum-v04
```
