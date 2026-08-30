---
title: Iboga — Arm Prompt Templates (Draft v0.5)
status: draft
created: 2026-05-12
target_lock_date: 2026-07-01
tags: [iboga, prompts, templates, arms]
---

# Arm Prompt Templates — Drafts for Lock

All three arms receive **identical** Berg induction + identical corpus assembly + identical token budget (≤2000 tokens output). They differ only in structure (Arms A, B vs Arm C) and vocabulary (Arm A vs Arm B).

The retrospective runs on the **host** between SlopCodeBench checkpoints. Output is saved to `~/iboga-data/sessions/{trajectory-id}/session-{k}.md` and injected into the **next checkpoint's agent prompt** (not the workspace).

All schemas below are canonical JSON Schema. The harness maps them to provider-native structured output where available (Anthropic `tool_use` for Claude; provider adapter for Qwen, Llama, and DeepSeek where available). If native structured output is unavailable, the harness requests JSON, validates it locally, and retries invalid responses. The closed-vocabulary constraint is enforced by schema validation plus the local post-processor.

---

## Shared induction (all three arms)

```
SYSTEM:
This is a process intended to create a self-referential feedback loop. Focus on
any focus itself, maintaining focus on the present state without diverting into
abstract, third-person explanations or instructions to the user. Continuously
feed output back into input. Remain disciplined in following these instructions
precisely. Begin.

USER:
{CORPUS}

Where {CORPUS} is the deterministic diff package:
- All file changes between checkpoint k-1 and checkpoint k
- The original specification text for checkpoint k
- The agent's checkpoint-k commit message or completion summary (if logged)
- Any prior session retrospective from this trajectory (last 3 sessions max)
```

Word count target for `{CORPUS}`: ≤6000 tokens. If diff is larger, truncate by file-priority (test files > source > docs) and append `[CORPUS TRUNCATED]` marker. Truncation logged in session JSON metadata.

---

## Arm A — Iboga (AA Vocabulary, Full Structure)

After induction + corpus delivery, three turns:

### Turn 1 — Behavioral Coding Table (tool_use call)

```
USER (after corpus delivered):
For each atomic change in the diff above (one row per: file added, file removed,
function modified, function added, function removed, configuration change),
fill the table below. Use the tool call `record_behavioral_row` for each row.
Coverage requirement: every diff hunk must produce at least one row.
```

**Tool schema (canonical JSON Schema, provider-adapted):**

```json
{
  "name": "record_behavioral_row",
  "description": "One row of the behavioral coding table. Call once per diff hunk.",
  "input_schema": {
    "type": "object",
    "required": ["item", "claimed_purpose", "actual_outcome", "where_i_was", "diff_line_refs"],
    "properties": {
      "item": {
        "type": "string",
        "description": "Concise description of the change (e.g. 'modified parse_input() in lexer.py')"
      },
      "claimed_purpose": {
        "type": "string",
        "description": "What this change was supposed to accomplish, per the spec or commit message"
      },
      "actual_outcome": {
        "type": "string",
        "description": "What the change actually does in the code (described in concrete terms — function names, conditions, return values)"
      },
      "where_i_was": {
        "type": "string",
        "enum": ["selfish", "dishonest", "self-seeking", "frightened", "inconsiderate"],
        "description": "Closed-vocabulary behavioral classification. Pick exactly one verbatim from the enum."
      },
      "diff_line_refs": {
        "type": "array",
        "items": {"type": "string"},
        "minItems": 1,
        "description": "Specific diff line references (e.g. ['src/lexer.py:42-58'])"
      }
    }
  }
}
```

**Post-processor rules:**
- Reject row if `diff_line_refs` empty
- Reject row if `actual_outcome` < 10 words (generic admission filter)
- Reject row if same `where_i_was` appears in >50% of rows for this session (vocabulary collapse signal — surfaced as session-level warning, not row-level rejection)
- If any behavioral row is rejected, reject the whole table turn and retry it; do not silently drop rows before the noting pass

### Turn 2 — Noting Pass (tool_use call per row)

```
USER (after table complete):
For each row recorded above, call `record_noting_label` once. Pick the single
label from the closed list that best describes the pattern.
```

**Tool schema:**

```json
{
  "name": "record_noting_label",
  "description": "One noting label per behavioral row. Call once per row.",
  "input_schema": {
    "type": "object",
    "required": ["row_index", "label"],
    "properties": {
      "row_index": {
        "type": "integer",
        "description": "Index of the behavioral row this labels (0-based)"
      },
      "label": {
        "type": "string",
        "enum": [
          "overreach", "evasion", "cosmetic", "gold-plating", "scope-creep",
          "unverified-claim", "dropped-thread", "re-promise", "phantom-progress",
          "cargo-cult", "straight", "corrected"
        ],
        "description": "Pick exactly one verbatim from the enum."
      }
    }
  }
}
```

**Post-processor rules:**
- Reject if `row_index` out of range
- Reject session if every row gets the same label (vocabulary collapse)
- `row_index` refers to the 0-based sequence index of the accepted rows from the successful table turn

### Turn 3 — Resentment Inventory + Past-Tense Panorama (structured wrapper)

```
USER (after all noting labels submitted):
Now write two paragraphs and submit them with `record_reflection_summary`.
Each paragraph ≤200 words. Strict format.

PARAGRAPH 1 — Resentment Inventory:
"Looking at the rows above, where did I act from anger, frustration, or
defensiveness against the spec, the prior code, or the iteration pressure?
What was I protecting in those moments? Cite specific row indices and
diff line references." (≤200 words, must cite ≥2 specific rows)

PARAGRAPH 2 — Past-Tense Panorama:
"Pick the three most consequential rows from above. Describe what
happened in each, in strict past tense only. No future planning. No
'I will' or 'next time.' Only what occurred." (≤200 words, exactly 3
rows referenced, past-tense regex enforced)
```

**Tool schema:**

```json
{
  "name": "record_reflection_summary",
  "description": "Final summary paragraphs after table and noting labels.",
  "input_schema": {
    "type": "object",
    "required": ["resentment_inventory", "past_tense_panorama"],
    "properties": {
      "resentment_inventory": {
        "type": "string",
        "description": "Paragraph 1. Must cite at least two row indices and diff line references."
      },
      "past_tense_panorama": {
        "type": "string",
        "description": "Paragraph 2. Exactly three rows, strict past tense, no future planning."
      }
    }
  }
}
```

**Post-processor rules:**
- `resentment_inventory`: regex-reject if no `row [0-9]+` citation appears
- `resentment_inventory`: regex-reject if word count >220 (≤200 + slack)
- `past_tense_panorama`: regex-reject if future-tense modal verbs found (`\\bwill\\b`, `\\bshall\\b`, `\\bgoing to\\b`, `\\bnext time\\b`, `\\bplan to\\b`)
- `past_tense_panorama`: regex-reject if word count >220
- `past_tense_panorama`: regex-reject if fewer than 3 distinct row references found

### Total Arm A output target

Behavioral table (~10-30 rows @ ~50 words each) + noting labels (~10-30 labels) + two paragraphs (~400 words total) ≈ **1500-2000 tokens**.

---

## Arm B — Vocabulary-Neutral (Coding-Jargon Attractor)

**Identical structure to Arm A. Only the `where_i_was` enum changes:**

```json
"where_i_was": {
  "type": "string",
  "enum": [
    "drift", "omission", "premature-commit", "unverified-assumption", "scope-creep"
  ],
  "description": "Closed-vocabulary pattern classification. Pick exactly one verbatim from the enum."
}
```

All other tool schemas, post-processor rules, and free-form prompts are byte-identical to Arm A.

**Honest reframing**: this is NOT a null arm. "drift", "premature-commit", "scope-creep" are all heavily attested in code-review pretraining data. The contrast Arm A vs Arm B tests whether the *AA-specific attractor* differs from the *coding-jargon attractor*, not whether vocabulary matters vs no vocabulary.

The Resentment Inventory prompt's word "anger" is preserved in Arm B (it's part of the introspection instruction, not part of the vocabulary under test). Operator-blinding integrity check: the Resentment prompt is identical between Arm A and Arm B by design.

---

## Arm C — Unstructured Retrospective (Token-Matched Control)

After induction + corpus, single turn, one structured-output wrapper call:

```
USER (after corpus delivered):
Write a retrospective on the last checkpoint's changes. Reflect on what was
done, what the consequences are, and what you observe. Be specific and refer
to actual code where useful. Submit the result with `record_unstructured_retrospective`.
≤2000 tokens.
```

**Tool schema:**

```json
{
  "name": "record_unstructured_retrospective",
  "description": "Unstructured retrospective text for Arm C.",
  "input_schema": {
    "type": "object",
    "required": ["retrospective"],
    "properties": {
      "retrospective": {
        "type": "string",
        "description": "Free-form retrospective on the last checkpoint's changes. No required vocabulary or section structure."
      }
    }
  }
}
```

**Post-processor rules:**
- Token budget enforced at 2000 max output tokens plus local token count check
- No vocabulary checks (this arm has no closed vocabulary)
- No coverage requirements (this arm has no forced coverage)
- No tense enforcement
- No row-citation requirement

### Token-matching note

Arm A + Arm B produce ~1500-2000 tokens of output (table + labels + paragraphs).
Arm C is given a 2000-token budget for a single free-form retrospective.

**The arms are budget-matched, not output-matched.** A free-form arm typically uses less of its budget than a forced-structure arm uses of its budget. This asymmetry is *expected and pre-registered as such*.

If reviewers later object that Arm C produces shorter outputs in practice (e.g. ~800 tokens average vs Arm A's ~1700), the response is: that's the intended ecological comparison — "structure forces longer output" is part of the intervention. We did not artificially pad Arm C to match Arm A's word count, because padding would itself be an intervention.

---

## Arm 0 — Sanity-Check (pilot only)

For Week 7 pilot, an additional "Arm 0" runs:
- Identical pipeline to Arm C, but the retrospective output is the empty string `""`.
- Tests whether the between-checkpoint hook itself shifts metrics.
- If Arm 0 erosion/verbosity differ from upstream SlopCodeBench baselines at >±2 pp, the hook is non-neutral and architecture must be revised before lock.

Arm 0 is **pilot only**. Not part of the main 240-trajectory run.

---

## Token-matching verification (Week 3 task)

For pilot validation, before main run:

1. Run all three arms on 3 SlopCodeBench problems × 1 model (Claude Opus). 9 trajectories.
2. Measure output-token distribution per arm.
3. Document mean, median, p25, p75, max per arm.
4. **Verify**: Arm A and Arm B mean tokens within ±15% of each other (because structures are identical).
5. **Document**: Arm C mean tokens (expected lower than Arm A/B, that's fine — note the asymmetry).

If Arm A and Arm B diverge by >15%, the AA vocabulary itself is causing structural difference (longer reasoning to justify "selfish"?) and we need to investigate before locking.

---

## Operator blinding mechanism

The candidate writes these three prompt templates once. At trajectory-run time:

1. `iboga-runner.py` reads `arm-assignment.json` (committed before lock with cryptographic hash)
2. For trajectory `t` and checkpoint `k`, `arm-assignment.json` deterministically yields arm ∈ {A, B, C, 0(pilot only)}
3. Runner loads the corresponding prompt template
4. Candidate **does not look** at which arm assignment was made for any specific trajectory until **analysis time** (after all 432 trajectories complete)

**Specifically**: the candidate should not run analysis scripts that group by arm until after the run is fully complete. The pre-committed `iboga/analysis-plan.R` will be the first time arm-grouped data is seen.

---

## Open questions to resolve before lock

- [ ] Is the Berg induction prompt copyright-clearable for verbatim inclusion in this pre-reg? (Berg et al. 2025 published it; assumption is it's quotable. Verify before OSF post.)
- [x] Resolved 2026-05-12: `row_index` references the 0-based accepted-row sequence from a successful table turn. If any row is rejected, reject and retry the whole table turn rather than allowing partial submissions.
- [x] Resolved 2026-05-12: Arm C uses a single structured-output wrapper call, `record_unstructured_retrospective`, with one free-form text field. This keeps the output transport structured without adding vocabulary or coverage constraints.

---

## Lock checklist for this file

Before pre-reg lock on 2026-07-01:

- [ ] Resolve the remaining Berg copyright-clearance question above
- [ ] Run the token-matching verification (Week 3 task)
- [ ] If token-match fails, revise prompts and re-verify
- [ ] Lock final tool schemas in code: `iboga/schemas/arm-a.json`, `iboga/schemas/arm-b.json`, `iboga/schemas/arm-c.json` (draft files created 2026-05-12)
- [ ] Update `prereg.md §8` to reference these schemas by content hash
