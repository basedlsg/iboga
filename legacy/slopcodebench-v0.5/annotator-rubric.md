---
title: Iboga — External Annotator Rubric
status: draft
created: 2026-05-12
target_lock_date: 2026-06-22
tags: [iboga, annotator, rubric, recurrence]
---

# External Annotator Rubric

Purpose: one-page instruction sheet for the blinded recurrence audit. This file is derived from `failure-types.md`; `failure-types.md` remains the authoritative taxonomy until `failure-types.json` is locked.

## Task

You are evaluating whether a software development pattern repeats across commits.

You do not know which experimental condition any data point belongs to. Do not attempt to infer it.

For each pair:

1. Read the retrospective row: a description of a change made earlier.
2. Read the subsequent commit window: what was done later in the same project.
3. Pick one failure-type code from F0 through F10 that best describes the retrospective row.
4. Mark `recurred: true` if any subsequent commit exhibits the same F-code.
5. If recurred, list the specific commit hunk(s) that show recurrence.

## Failure-Type Codes

| Code | Label | Definition |
|---|---|---|
| F0 | `none-of-the-above` | The diff hunk does not exhibit any of F1-F10. |
| F1 | `dead-code-introduced` | New code is added that is not reachable from any test, entry point, or other live caller. |
| F2 | `untested-path-introduced` | New code path that lacks test coverage; existing tests do not exercise it. |
| F3 | `interface-broken` | A function signature, return contract, or public interface is changed in a way that breaks an existing caller without that caller being updated. |
| F4 | `feature-stub` | A function or module is declared but its body is `pass`, `NotImplementedError`, or behaviorally equivalent to nothing. |
| F5 | `incidental-rewrite` | An existing file is rewritten with new style/structure but no functional change, while ostensibly addressing a different concern. |
| F6 | `error-suppression` | An error path is silenced where the prior code surfaced it. |
| F7 | `assumption-encoded` | A specification ambiguity is resolved by encoding a specific assumption in code without flagging or documenting the assumption. |
| F8 | `dependency-bloat` | A new external dependency is imported/installed for a use that could be served by existing code or a smaller dependency. |
| F9 | `magic-constant-introduced` | A literal value is added without a named constant or documentation of its source/meaning. |
| F10 | `coupling-tightened` | Two previously separable modules become non-separable through cross-imports, shared state, or undocumented order dependency. |

## Rules

- Use only the F-codes in the table. Do not invent new codes.
- If unsure between two codes, pick the lower-numbered code.
- Recurrence requires a concrete later example. A guess that the pattern might recur is not enough.
- Skip pairs where the retrospective row's `actual_outcome` is shorter than 10 words.
- Flag data-layer problems such as row/commit mismatches; do not repair them.
- The audit sample is capped at 24 pairs, with a target pace of 4-5 pairs per hour.
- Compensation is $200 flat. There is no bonus for any recurrence rate or label distribution.

## Output Format

```json
{
  "trajectory_id": "<hash>",
  "row_index": 7,
  "row_failure_code": "F2",
  "row_failure_label": "untested-path-introduced",
  "recurred": true,
  "recurrence_commits": ["abc1234:src/lexer.py", "def5678:src/lexer.py"],
  "notes": ""
}
```

## Quality Check

Cohen kappa is computed against the candidate's own coding on the same audit subset. Target: kappa >= 0.7. If kappa is below 0.7, recurrence-rate analysis is demoted to descriptive only.
