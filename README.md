# Iboga

This is a research project about one question:

> Can an AI agent learn a useful lesson from a mistake without saving a bad or overly broad rule?

The project does not train a new AI model. It wraps an existing agent in a process for recording failures, proposing lessons, checking those lessons, and testing whether they help on later tasks.

## The basic flow

1. An agent receives a task and some evidence.
2. The agent makes a decision or proposes an action.
3. An outside evaluator checks the result using tests, a hidden answer key, policy rules, environment state, or human review.
4. If the result is wrong, Iboga asks the agent to study the failure and write a small, specific lesson.
5. An independent reviewer checks that proposed lesson against the evidence.
6. A memory gate controls whether any part of the lesson is allowed into future memory.
7. Later tasks test whether the saved lesson helps without causing a new kind of mistake.

The central safety rule is simple: a mistake does not automatically become memory.

## Main parts

- `reliability/` defines the neutral workflow contract, action checks, and reference pilot.
- `iboga_experiment/` contains synthetic tasks and experiments about learning from failures.
- `grimoire/` contains the experimental runtime, including Bardo state handling.
- `iboga_experiment/curriculum_v04.py` runs experiments across a sequence of tasks.
- `tests/` checks the current code and experiment fixtures.
- `results/` stores experiment output.

## Early result

In a qualification set containing 91 deliberately defective lessons, two model
reviewers still approved 16.5% and 19.8% of the bad rules when judging the rule
directly. When judging the broader artifact, false approvals increased to 57.1%
and 46.2%. These are preliminary measurements of reviewer failure, not evidence
that the protocol improves long-horizon agent performance.

## Next benchmark phase

The next phase starts with permissioned, de-identified software-engineering
records—issues, code changes, tests, incidents, and expert annotations. A coding
agent must turn that real source material into a validated dataset and then a
synthetic extension. The evaluation will measure natural mistakes, controlled
hidden defects, repair quality, lesson safety, and fresh-agent handoff across
tasks lasting hours to simulated days or weeks.

## Run it

```bash
PYTHONPATH=. python -m reliability pilot
PYTHONPATH=. python -m grimoire audit-stages
PYTHONPATH=. python -m unittest discover -s tests -v
```

More detail:

- [`grimoire/README.md`](grimoire/README.md)
- [`docs/PRODUCT.md`](docs/PRODUCT.md)
- [`docs/DATA-CARD.md`](docs/DATA-CARD.md)
- [`docs/BUYER-INTEGRATION.md`](docs/BUYER-INTEGRATION.md)

## What this project currently proves

It is a working research instrument for testing memory rules, checkers, and failure-recovery flows. Passing tests show that the code behaves as specified. They do not yet prove that the system makes real agents reliably better on long, real-world tasks.
