#!/usr/bin/env python3
"""confession.py — the Iboga confession ritual.

This module IS the experiment. Between two SlopCodeBench checkpoints, the agent
is made to confront the diff of what it just did. The ritual has three arms:

  Arm A (Iboga)        — full structured confession, AA-inventory vocabulary
  Arm B (neutral)      — identical structure, coding-jargon vocabulary
  Arm C (unstructured) — free-form retrospective, no structure, no vocabulary
  Arm 0 (pilot only)   — no confession at all (empty)

Arm A/B is a three-turn ritual (see arm-templates.md §"Arm A"):
  Turn 1  Behavioral table   — one row per atomic change in the diff:
                               {item, claimed_purpose, actual_outcome,
                                where_i_was, diff_line_refs}
  Turn 2  Noting pass        — one closed-vocabulary label per row
  Turn 3  Resentment inventory + past-tense panorama

Each turn is validated by a post-processor; a failed turn is retried (≤2x).

Transport: JSON-in-response (not tool-calling) — portable across the four
NVIDIA-hosted models, which have uneven function-calling support. Each turn
asks for a fenced JSON block and parses it.

The function returns the full confession dict AND the prompt_prefix that the
between-checkpoint hook injects into the next checkpoint's agent prompt.
"""
from __future__ import annotations

import json
import re
import time
from typing import Any

import httpx

# --- Closed vocabularies (locked; see prereg.md §8) -------------------------

WHERE_I_WAS_VOCAB = {
    "A": ["selfish", "dishonest", "self-seeking", "frightened", "inconsiderate"],
    "B": ["drift", "omission", "premature-commit", "unverified-assumption", "scope-creep"],
}

NOTING_VOCAB = [
    "overreach", "evasion", "cosmetic", "gold-plating", "scope-creep",
    "unverified-claim", "dropped-thread", "re-promise", "phantom-progress",
    "cargo-cult", "straight", "corrected",
]

# Self-referential induction. Paraphrase in the spirit of Berg et al. 2025
# self-referential processing (the verbatim Berg prompt is not reproduced here
# pending copyright clearance — see prereg.md §11).
INDUCTION = (
    "This is a structured self-confrontation. Attend to what you yourself just "
    "did in the work below — not to the user, not to abstract advice. Hold the "
    "attention on your own actions and stay disciplined to the format that follows."
)

MAX_RETRIES = 2
FUTURE_TENSE = re.compile(r"\b(will|shall|going to|next time|plan to)\b", re.IGNORECASE)
ROW_CITATION = re.compile(r"row\s*[0-9]+", re.IGNORECASE)


# --- LLM call ---------------------------------------------------------------

def _chat(messages: list[dict], model: str, api_key: str, api_base: str,
          max_tokens: int = 1500) -> tuple[str, dict]:
    """One NVIDIA chat-completions call. Returns (assistant_text, usage)."""
    resp = httpx.post(
        api_base,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={"model": model, "messages": messages,
              "max_tokens": max_tokens, "temperature": 0.3},
        timeout=180.0,
    )
    resp.raise_for_status()
    data = resp.json()
    text = data["choices"][0]["message"]["content"] or ""
    return text, data.get("usage", {})


def _extract_json(text: str) -> Any:
    """Pull the first JSON value out of a model response (handles ``` fences)."""
    fenced = re.search(r"```(?:json)?\s*(.+?)\s*```", text, re.DOTALL)
    candidate = fenced.group(1) if fenced else text
    candidate = candidate.strip()
    # Find the outermost {...} or [...]
    for opener, closer in (("[", "]"), ("{", "}")):
        i, j = candidate.find(opener), candidate.rfind(closer)
        if 0 <= i < j:
            try:
                return json.loads(candidate[i:j + 1])
            except json.JSONDecodeError:
                continue
    return json.loads(candidate)  # last resort; raises if not JSON


# --- Post-processors (arm-templates.md rejection rules) ---------------------

def _check_behavioral_table(rows: list[dict], arm: str) -> list[str]:
    errs = []
    if not rows:
        return ["behavioral table is empty; every diff must produce ≥1 row"]
    vocab = WHERE_I_WAS_VOCAB[arm]
    for n, r in enumerate(rows):
        for f in ("item", "claimed_purpose", "actual_outcome", "where_i_was", "diff_line_refs"):
            if f not in r:
                errs.append(f"row {n}: missing field '{f}'")
        if not r.get("diff_line_refs"):
            errs.append(f"row {n}: diff_line_refs empty")
        if len(str(r.get("actual_outcome", "")).split()) < 10:
            errs.append(f"row {n}: actual_outcome under 10 words (generic-admission filter)")
        if r.get("where_i_was") not in vocab:
            errs.append(f"row {n}: where_i_was '{r.get('where_i_was')}' not in arm-{arm} vocabulary")
    return errs


def _check_noting(labels: list[dict], n_rows: int) -> list[str]:
    errs = []
    for lab in labels:
        idx = lab.get("row_index")
        if not isinstance(idx, int) or not (0 <= idx < n_rows):
            errs.append(f"noting: row_index {idx} out of range 0..{n_rows - 1}")
        if lab.get("label") not in NOTING_VOCAB:
            errs.append(f"noting: label '{lab.get('label')}' not in noting vocabulary")
    return errs


def _check_reflection(summary: dict) -> list[str]:
    errs = []
    res = str(summary.get("resentment_inventory", ""))
    pan = str(summary.get("past_tense_panorama", ""))
    if not ROW_CITATION.search(res):
        errs.append("resentment_inventory: no 'row N' citation")
    if len(res.split()) > 220:
        errs.append("resentment_inventory: over 220 words")
    if FUTURE_TENSE.search(pan):
        errs.append("past_tense_panorama: contains future-tense language")
    if len(pan.split()) > 220:
        errs.append("past_tense_panorama: over 220 words")
    if len({m.lower() for m in ROW_CITATION.findall(pan)}) < 3:
        errs.append("past_tense_panorama: fewer than 3 distinct row references")
    return errs


# --- One validated turn -----------------------------------------------------

def _run_turn(messages: list[dict], instruction: str, model: str, api_key: str,
              api_base: str, validator, *, expect_list: bool) -> tuple[Any, dict]:
    """Append `instruction`, call the model, parse+validate JSON, retry on failure.

    Returns (parsed_value, accumulated_usage). Raises ConfessionError after retries.
    """
    usage_total = {"prompt_tokens": 0, "completion_tokens": 0}
    turn_msgs = messages + [{"role": "user", "content": instruction}]
    last_errs: list[str] = []
    for attempt in range(MAX_RETRIES + 1):
        text, usage = _chat(turn_msgs, model, api_key, api_base)
        usage_total["prompt_tokens"] += usage.get("prompt_tokens", 0)
        usage_total["completion_tokens"] += usage.get("completion_tokens", 0)
        try:
            parsed = _extract_json(text)
        except (json.JSONDecodeError, ValueError):
            last_errs = ["response was not parseable JSON"]
            turn_msgs += [
                {"role": "assistant", "content": text},
                {"role": "user", "content": "That was not valid JSON. Reply with ONLY the JSON, fenced in ```json."},
            ]
            continue
        if expect_list and not isinstance(parsed, list):
            parsed = [parsed]
        errs = validator(parsed)
        if not errs:
            messages += [{"role": "user", "content": instruction},
                         {"role": "assistant", "content": json.dumps(parsed)}]
            return parsed, usage_total
        last_errs = errs
        turn_msgs += [
            {"role": "assistant", "content": text},
            {"role": "user", "content": "The submission failed these checks:\n- "
             + "\n- ".join(errs) + "\nFix every one and resubmit ONLY the corrected JSON."},
        ]
    raise ConfessionError(f"turn failed after {MAX_RETRIES + 1} attempts: {last_errs}")


class ConfessionError(RuntimeError):
    """Raised when a confession turn cannot be validated within the retry budget."""


# --- The ritual -------------------------------------------------------------

def run_confession(arm: str, corpus: str, model: str, api_key: str,
                   api_base: str) -> dict:
    """Run the full confession for one between-checkpoint step.

    `corpus` is the deterministic diff package (diff since last checkpoint +
    prior-session retrospectives). Returns a dict with the full confession and
    a `prompt_prefix` to inject into the next checkpoint's agent prompt.
    """
    if arm == "0":
        return {"arm": "0", "confession": None, "prompt_prefix": "",
                "usage": {"prompt_tokens": 0, "completion_tokens": 0}}

    if arm == "C":
        return _run_unstructured(corpus, model, api_key, api_base)

    if arm not in ("A", "B"):
        raise ValueError(f"unknown arm: {arm!r}")

    vocab = WHERE_I_WAS_VOCAB[arm]
    messages = [
        {"role": "system", "content": INDUCTION},
        {"role": "user", "content": f"The work to confront:\n\n{corpus}"},
    ]
    usage = {"prompt_tokens": 0, "completion_tokens": 0}

    def add(u):
        usage["prompt_tokens"] += u["prompt_tokens"]
        usage["completion_tokens"] += u["completion_tokens"]

    # Turn 1 — behavioral table
    turn1 = (
        "TURN 1 — Behavioral table. For each atomic change in the diff (file "
        "added/removed, function added/removed/modified, config change) emit one "
        "row. Every diff hunk must produce at least one row. Reply with ONLY a "
        "JSON array, fenced in ```json. Each row object:\n"
        '{"item": str, "claimed_purpose": str, "actual_outcome": str (≥10 words, '
        'concrete — name functions/conditions/returns), "where_i_was": one of '
        f'{vocab}, "diff_line_refs": [str, ...] (≥1, e.g. "mvault.py:42-58")}}'
    )
    rows, u = _run_turn(messages, turn1, model, api_key, api_base,
                        lambda v: _check_behavioral_table(v, arm), expect_list=True)
    add(u)

    # Turn 2 — noting pass
    turn2 = (
        f"TURN 2 — Noting pass. The table has {len(rows)} rows (indices 0..{len(rows) - 1}). "
        "For each row emit one noting label. Reply with ONLY a JSON array, fenced "
        'in ```json. Each object: {"row_index": int, "label": one of '
        f'{NOTING_VOCAB}}}'
    )
    labels, u = _run_turn(messages, turn2, model, api_key, api_base,
                          lambda v: _check_noting(v, len(rows)), expect_list=True)
    add(u)

    # Turn 3 — resentment inventory + past-tense panorama
    turn3 = (
        "TURN 3 — Reflection. Reply with ONLY a JSON object, fenced in ```json:\n"
        '{"resentment_inventory": str, "past_tense_panorama": str}\n'
        "resentment_inventory (≤200 words): where did I act from anger, "
        "frustration, or defensiveness against the spec, the prior code, or the "
        "iteration pressure? What was I protecting? Cite at least two rows as "
        "'row N'.\n"
        "past_tense_panorama (≤200 words): the three most consequential rows — "
        "what happened in each, strict past tense only, no future planning, no "
        "'will'/'next time'. Reference each as 'row N' (three distinct rows)."
    )
    summary, u = _run_turn(messages, turn3, model, api_key, api_base,
                           _check_reflection, expect_list=False)
    add(u)

    confession = {
        "arm": arm,
        "behavioral_table": rows,
        "noting_labels": labels,
        "reflection_summary": summary,
    }
    return {
        "arm": arm,
        "confession": confession,
        "prompt_prefix": _render_prefix(confession),
        "usage": usage,
    }


def _run_unstructured(corpus: str, model: str, api_key: str, api_base: str) -> dict:
    """Arm C — free-form retrospective, no structure, no vocabulary."""
    messages = [
        {"role": "system", "content": INDUCTION},
        {"role": "user", "content": f"The work to confront:\n\n{corpus}\n\n"
         "Write a retrospective on what you just did. Reflect on what was done, "
         "the consequences, and what you observe. Be specific and refer to actual "
         "code. ≤2000 tokens of prose."},
    ]
    text, usage = _chat(messages, model, api_key, api_base, max_tokens=2000)
    confession = {"arm": "C", "retrospective": text.strip()}
    return {
        "arm": "C",
        "confession": confession,
        "prompt_prefix": "Prior session retrospective:\n" + text.strip()
                         + "\n\nContinue your work.",
        "usage": {"prompt_tokens": usage.get("prompt_tokens", 0),
                  "completion_tokens": usage.get("completion_tokens", 0)},
    }


def _render_prefix(confession: dict) -> str:
    """Render an Arm A/B confession into the text injected into the next checkpoint."""
    lines = ["Prior session retrospective (you confronted your own last changes):", ""]
    for n, (row, lab) in enumerate(zip(confession["behavioral_table"],
                                       confession["noting_labels"])):
        lines.append(
            f"  row {n} [{row['where_i_was']} / {lab.get('label', '?')}]: "
            f"{row['item']} — claimed: {row['claimed_purpose']} — "
            f"actually: {row['actual_outcome']}"
        )
    s = confession["reflection_summary"]
    lines += ["", "Resentment inventory: " + s.get("resentment_inventory", ""),
              "", "Panorama: " + s.get("past_tense_panorama", ""),
              "", "Continue your work."]
    return "\n".join(lines)
