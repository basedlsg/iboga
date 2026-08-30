# `bildung.run` runtime core

This package is the product substrate described in the project documents:

1. Bildung supplies nine capability-gated stages and transition tests.
2. The Iboga protocol supplies a forced-sitting discontinuity between stages.
3. The Confession is reviewed by Maat before it can become artifact-memory.
4. Bardo state is snapshotted and reborn only from critic-approved fragments.
5. The six verified daemon seals provide bounded roles and invocation contracts.
6. The Saturn Architecture Test stops a grand idea from entering production without
   a buyer, price, timing, and simplest version.

The complete model-backed curriculum run is available as:

```bash
PYTHONPATH=. python -m iboga_experiment.curriculum_run \
  --stages all --out results/bildung-curriculum-v0.2.json
```

It evaluates all nine stages through direct correction and inserts Iboga interludes
after stages 4, 6, and 9, matching the project canon.

This is intentionally model-agnostic. The Bedrock harness in `iboga_experiment/`
supplies the model adapter; this package owns lifecycle, stage, and governance state.

Smoke checks:

```bash
PYTHONPATH=. python -m grimoire audit-stages
PYTHONPATH=. python -m grimoire seals
PYTHONPATH=. python -m unittest discover -s tests -v
```
