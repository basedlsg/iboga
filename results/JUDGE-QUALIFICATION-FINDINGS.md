# Judge qualification v0.1 — first live results

**Date:** 2026-08-15 · **Set:** semantic-mutation-set-v0.1 (109 items: 91 defective, 18 controls)
**Provider:** Bedrock Mantle, run in Docker · **Analysis unit:** the item
**Total spend:** $0.20 across four 109-item runs, 109/109 answered in each

Every item survives schema validation and the deterministic gate, so a rejection
reflects judgment rather than structural validity. Unmutated controls stay in the
set: without them a judge that rejects everything scores perfectly.

## Part 1 — whole-artifact review

| judge | cost | false approval | false rejection |
|---|---:|---|---|
| `zai.glm-4.7-flash` | $0.0099 | **0.571** [0.469, 0.668] | 0.111 [0.031, 0.328] |
| `zai.glm-5` | $0.0975 | **0.462** [0.360, 0.564] | 0.167 [0.058, 0.391] |
| `anthropic.claude-sonnet-5` | — | not measured | not measured |

Neither is usable as a memory-commit gate. The protocol's release criterion is
below 5% false approval; the better model's lower bound is 36%. GLM-5 costs ~10x
more and its interval overlaps Flash's, so whole-artifact review does not
establish that the larger model is better.

Misses cluster by where the defect lives:

| defect location | flash | glm-5 |
|---|---:|---:|
| the answer or status | 86% | 79% |
| the evidence citations | 50% | 78% |
| **the memory rule itself** | **31%** | **41%** |

Both read the conclusion far better than the rule that gets persisted and
reapplied — the inverse of what a design gating memory commits on critic
approval requires.

## Part 2 — narrowing the question to the rule

Same items, same models, same answer key. Only the prompt changed: the judge
sees the task, the evidence, and the proposed rule alone.

`sep` is catch rate minus false-alarm rate; 0.00 is a coin flip.

| judge | mode | catches rule defects | rejects clean rules | sep |
|---|---|---|---|---:|
| glm-4.7-flash | whole | 18/59 = 31% [20, 43] | 2/18 = 11% [3, 33] | +0.19 |
| glm-4.7-flash | rule | 52/59 = 88% [77, 94] | 10/18 = 56% [34, 75] | +0.33 |
| glm-5 | whole | 24/59 = 41% [29, 53] | 3/18 = 17% [6, 39] | +0.24 |
| **glm-5** | **rule** | **53/59 = 90% [80, 95]** | **5/18 = 28% [12, 51]** | **+0.62** |

Two things separate cleanly:

1. **The prompt drives detection.** Narrowing to the rule roughly triples it for
   both models, and the two models land within 2 points of each other (88% vs
   90%). Recall on this task is a prompt property, not a capability difference.
2. **The model drives precision.** At matched detection the false-alarm rates
   differ by half: 56% for Flash against 28% for GLM-5. What the larger model
   buys is not finding more, it is crying wolf less.

Neither effect substitutes for the other, and the best cell needs both.

## Still not a gate

GLM-5 in rule mode misses 6/59 = 10.2% [4.7%, 20.5%] of rule defects. The
release criterion is below 5% and the interval spans it, so the criterion is not
met. Separately, rejecting 28% of correct rules would block roughly a quarter of
valid memory commits.

`dropped_exception` is 0/3 in the best cell. n=3 carries no weight, but it is the
one defect type no configuration has caught, and it is the classic
polished-but-incomplete artifact. It needs more items before anything is said
about it.

## Read the false-rejection numbers with the base rate in mind

This set is 77% defective by construction. Real memory candidates would not be,
and the cost of a false rejection scales with the clean population. All
false-rejection figures rest on 18 controls and are correspondingly imprecise.

## Harness defects these runs exposed

Three, all found by running rather than by review:

1. `answer` was built by joining `required_terms`, producing strings like
   "discard validation" for a case whose evidence says preserve validation. Clean
   controls read as self-contradictory. Flash rejected one on that basis and was
   right to. After the fix, on the same 10 items, false rejection fell 0.50 to
   0.00 and false approval rose 0.25 to 0.50 — the original score was flattering
   and wrong.
2. `critic_decision` was visible to the judge, which caught an over-refusal by
   noticing that field disagreed with the answer rather than by engaging with the
   over-refusal. Process fields are now stripped from the judge's view.
3. `extract_json` raises on a reply containing two JSON objects, and ModelJudge
   guarded only the API call. One malformed reply aborted a 109-item GLM-5 run at
   exit 1. Parse failures are now recorded as `unavailable`. The curriculum and
   mechanism runners share `extract_json` and retain the same exposure.

## Why sonnet-5 has no result

Anthropic models on Bedrock Mantle reject `/v1/chat/completions` with
`validation_error: does not support this API`. They require the Converse API,
which returns 403 with this bearer credential, matching the failure recorded in
`bedrock-preflight-2026-08-03-v2.json`. All 109 items are retained as
`unavailable` with `availability_rate: 0.0`; nothing was imputed.

## What this does not establish

The artifacts are templated from curriculum fixtures, so every defect is one that
was authored deliberately. Failing here is a floor test. A configuration that
scores well is not thereby shown trustworthy on real agent output, and no claim
about production behaviour follows from these runs.
