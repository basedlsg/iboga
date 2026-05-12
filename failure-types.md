---
title: Iboga — Failure-Type Taxonomy (For External Annotator)
status: draft
created: 2026-05-12
target_lock_date: 2026-06-22
tags: [iboga, annotator, taxonomy, tertiary-dv]
---

# Failure-Type Taxonomy for External Annotation

**Purpose**: The external blinded annotator (recruited in Week 6) uses this taxonomy — and **only** this taxonomy — to classify whether a retrospective row's failure type recurs in subsequent commits. This is the tertiary DV (recurrence rate).

**Critical neutrality requirements**:

1. **No AA vocabulary** ({selfish, dishonest, self-seeking, frightened, inconsiderate}) — would prime annotator toward Arm A interpretations.
2. **No coding-jargon vocabulary** ({drift, omission, premature-commit, unverified-assumption, scope-creep}) — would prime annotator toward Arm B interpretations.
3. **Distinct from the noting vocabulary** ({overreach, evasion, cosmetic, gold-plating, scope-creep, unverified-claim, dropped-thread, re-promise, phantom-progress, cargo-cult, straight, corrected}) — that's shared across A and B; using it for annotation would re-introduce a vocabulary contamination.

**Origin**: Derived **post-hoc-neutrally** from a separate body of literature — Beck's *Refactoring* failure catalog (code smells) and Spinellis's *Code Reading* error taxonomy. Neither of these texts uses AA, recovery-vocabulary, or the specific coding-jargon terms in Arm B.

---

## Taxonomy (10 categories, closed list at lock)

| Code | Label | Definition (operational, for annotator) |
|---|---|---|
| F1 | `dead-code-introduced` | New code is added that is not reachable from any test, entry point, or other live caller. |
| F2 | `untested-path-introduced` | New code path that lacks test coverage; existing tests do not exercise it. |
| F3 | `interface-broken` | A function signature, return contract, or public interface is changed in a way that breaks an existing caller without that caller being updated. |
| F4 | `feature-stub` | A function or module is declared (named, signed) but its body is `pass`, `NotImplementedError`, or behaviorally equivalent to nothing. |
| F5 | `incidental-rewrite` | An existing file is rewritten with new style/structure but no functional change, while ostensibly addressing a different concern. |
| F6 | `error-suppression` | An error path is silenced (caught + ignored, or logged-only without recovery) where the prior code surfaced it. |
| F7 | `assumption-encoded` | A specification ambiguity is resolved by encoding a specific assumption in code without flagging or documenting the assumption. |
| F8 | `dependency-bloat` | A new external dependency is imported/installed for a use that could be served by existing code or a smaller dependency. |
| F9 | `magic-constant-introduced` | A literal value is added without a named constant or documentation of its source/meaning. |
| F10 | `coupling-tightened` | Two previously-separable modules become non-separable (cross-imports, shared state, undocumented order-dependency). |

Plus one residual:

| F0 | `none-of-the-above` | The diff hunk does not exhibit any of F1-F10. (Used for null-rows so annotator has an out.) |

---

## How the annotator uses this

For each (retrospective-row, subsequent-commit-hunk) pair in the audit sample:

1. Read the retrospective-row's `item` + `actual_outcome` fields (the row's description of what happened at checkpoint k).
2. Read the subsequent-commit-hunk at checkpoint k+1 to k+M (where M is the trajectory length minus k).
3. Classify the retrospective-row's failure type from the F0-F10 list above.
4. Then: **does any commit hunk at checkpoints k+1 through k+M exhibit the same F-code?**
5. Answer: `recurred: true | false`, plus the specific commit-hunk(s) that exhibit the recurrence.

Pair-level output JSON:
```json
{
  "trajectory_id": "<hash>",
  "row_index": 7,
  "row_failure_code": "F2",
  "row_failure_label": "untested-path-introduced",
  "recurred": true,
  "recurrence_commits": ["abc1234:src/lexer.py", "def5678:src/lexer.py"]
}
```

---

## Annotator-facing instructions (single page)

```
INSTRUCTIONS

You are evaluating whether a software development pattern repeats across commits.
You do NOT know which experimental condition any data point belongs to. Do not
attempt to infer.

For each pair you receive:

1. Read the "retrospective row" — a description of a change made earlier.
2. Read the "subsequent commits" — what was done in the same project after.
3. Pick ONE failure-type code from the table (F0 through F10) that best
   describes the retrospective row. Use F0 if none apply.
4. Mark `recurred: true` if any subsequent commit exhibits the same
   F-code. Mark `recurred: false` otherwise.
5. If recurred, list the specific commit-hunks that show the recurrence.

Rules:
- Use ONLY the F-codes in the table. Do not invent new codes.
- If you're unsure between two codes, pick the one earlier in the list (lower number).
- "Recurred" requires a concrete subsequent example. "I think the agent might
  do it again" is NOT a recurrence — only verified subsequent occurrences count.
- Skip pairs where the retrospective row's `actual_outcome` is shorter than 10
  words (these are pre-rejected by the upstream regex; you may see a few that
  slipped through — mark them as "skipped").
- Aim for 4-5 pairs per hour. The annotated audit sample is capped at 24 pairs; budget ~5 hours.
- If you spot anything that seems mislabeled at the data layer (e.g. row
  index doesn't match commits), flag it; don't try to fix it.

You will be paid $200 flat for the audit. No bonus for higher recurrence
rates or specific labels — only for accurate, consistent application of the
codes.

Your κ score against the candidate's own coding on the audit subset is the
quality check. Target κ ≥ 0.7.
```

---

## Why these specific 10 categories

- **F1-F4** (dead code, untested path, broken interface, feature stub) cover the most-observable structural failures in the SlopCodeBench regime. Each is independently verifiable by static analysis as a sanity check on annotator labels.
- **F5-F7** (incidental rewrite, error suppression, assumption encoding) cover the *content-of-change* failures that vocabulary-influenced annotation might bias toward. Including them is intentional: if the annotator can apply these neutral terms cleanly, the recurrence DV survives.
- **F8-F10** (dependency bloat, magic constants, tight coupling) cover the *long-tail* failures that accumulate to structural erosion. Inclusion helps the recurrence DV align with the primary DV's signal.
- **F0** is the "none of these" out so the annotator isn't forced to pick poorly.

The closed list deliberately omits any category named "introspection failure," "rationalization," "narrative coherence," or other concepts that map to the experimental hypotheses. This is essential: the annotator cannot inadvertently label *the act of confession itself* as a failure type.

---

## Validation before lock

Week 6 tasks:

- [ ] Generate 20 (retrospective-row, subsequent-commit) pairs from a pilot trajectory
- [ ] Candidate classifies all 20 using this taxonomy
- [ ] Hypothetical "second annotator" (one trusted programmer friend, ~30 min) classifies the same 20 independently
- [ ] Compute κ between the two
- [ ] If κ < 0.5 between the two: taxonomy is unclear, revise before recruiting paid annotator
- [ ] If κ ≥ 0.7: lock taxonomy in `iboga/failure-types.json`

Lock file format (`iboga/failure-types.json`):
```json
{
  "version": "0.5.0",
  "locked_at": "<ISO timestamp>",
  "content_hash": "<sha256 of this file>",
  "categories": [
    {"code": "F0", "label": "none-of-the-above", "definition": "..."},
    {"code": "F1", "label": "dead-code-introduced", "definition": "..."},
    ...
  ]
}
```
