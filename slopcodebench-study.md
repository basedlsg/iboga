---
title: SlopCodeBench Study Notes (for Week 2 harness fork)
status: active
created: 2026-05-12
source_paper: arXiv:2603.24755
source_repo: github.com/SprocketLab/slop-code-bench
source_leaderboard: scbench.ai
tags: [iboga, slopcodebench, harness, study-notes]
---

# SlopCodeBench — Technical Brief for Harness Forking

Read of arXiv:2603.24755 + HTML version. **Source of truth: this file's section references against the paper at lock time.**

---

## Confirmed parameters

| Parameter | Value | Source |
|---|---|---|
| Problems | **20** | Abstract + Conclusion |
| Total checkpoints | **93** | Abstract |
| Models in their paper | **11** | Conclusion: "Across 11 models and 20 iterative problems" |
| Language tracks reported | **Python only** | §2 — "language-agnostic by design" but Python in reported runs |
| Best-agent solve rate | **17.2%** | Opus 4.6 |
| Workspace persistence | **Working dir only** | §3.1 |
| Docker isolation | **Fresh container per checkpoint** | §3.1 |

This matches the pre-reg. No revisions needed to the pre-reg numbers.

---

## Equations to implement / inherit

### Erosion (§2.3)

```
mass(f) = CC(f) × √SLOC(f)

Erosion = Σ_{f∈F, CC(f)>10} mass(f) / Σ_{f∈F} mass(f)
```

- `CC(f)` = cyclomatic complexity of function `f` (Radon convention)
- `SLOC(f)` = source lines of code for function `f`
- Threshold `CC > 10` follows the Radon "high complexity" threshold

**Implementation**: don't reimplement. Use SprocketLab's `metrics/erosion.py` unmodified. Their results in the leaderboard are reproducible by definition only if we use their exact code.

### Verbosity (§2.3, Eq. 4)

```
Verbosity = |{AST-Grep Flagged Lines} ∪ {Clone Lines}| / LOC
```

- 137 AST-Grep rules detecting wasteful patterns
- Clone-detection algorithm: **NOT SPECIFIED in paper**. Must inspect their `metrics/verbosity.py` to know whether they use token-shingle, AST-subtree, or threshold-based detection. **Add to Week 2 harness-validation checklist.**

### Slope computation

The paper measures the *slope* of erosion and verbosity over checkpoints. Implementation detail (not specified in paper):
- OLS slope across checkpoint indices, or some other regression?
- Are checkpoints evenly spaced indices or actual time?
- Slope per problem, then averaged? Or pooled regression?

**Action: read `metrics/slope.py` (or equivalent) in their fork before Week 2.**

---

## Harness architecture (critical for Iboga hook insertion)

### Confirmed (§3.1)

- **Fresh Docker per checkpoint**: agent process, env, packages, shell history, agent session data all reset.
- **Workspace carryover**: ONLY the contents of the working directory persist between checkpoints.
- **Specification**: agent receives the spec for checkpoint `k+1` at the start of container `k+1`.

### Implication for Iboga retrospective injection

An earlier Iboga draft specified "out-of-workspace" retrospective text at `/tmp/iboga-*`. But Docker reset means `/tmp/` is **also wiped** between containers. The retrospective text must therefore be:

1. **Computed outside Docker** (on the host) between checkpoint `k` and `k+1`
2. **Persisted on the host** (e.g., `~/iboga-data/sessions/{trajectory}/{k}.json`)
3. **Injected into the agent's spec at checkpoint `k+1`** as part of the system/user prompt, NOT placed in the workspace

This is a substantive architectural decision. `prereg.md` §8 and §11 were updated on 2026-05-12 to reflect this: retrospective text lives in the agent's *prompt* for next checkpoint, not in any filesystem the workspace AST-Grep sees.

**Confirmed: no contamination risk for verbosity/erosion metrics**, because the retrospective never enters the workspace.

### Required harness modification

SprocketLab's harness has no documented intervention-hook surface. We need to:

1. Add a `--between-checkpoint-hook <script>` flag to their harness invocation
2. The hook receives: `(trajectory_id, checkpoint_k_workspace_dir, prior_diff)`
3. Hook computes retrospective via LLM call (Arm A / B / C prompt template)
4. Hook returns text to be prepended to checkpoint `k+1`'s agent prompt
5. Harness modified to accept prepended-prompt for the next agent invocation

This is roughly 100-200 lines of Python in their existing `runner/` directory. **Allowed scope**: don't touch their `metrics/` directory at all (reproducibility requirement). Only modify `runner/`.

---

## What was NOT specified (action items for repo inspection)

Before pre-reg lock, must inspect:

- [ ] `metrics/verbosity.py` — clone-detection algorithm
- [ ] `metrics/erosion.py` — exact OLS slope vs per-problem averaging
- [ ] `runner/` or equivalent — agent invocation surface, where to add the hook
- [ ] Per-checkpoint specification format — what does the agent receive at checkpoint `k+1`? File path? Text in stdin? Env var?
- [ ] `Dockerfile` — what Python version, what packages preinstalled, what user permissions
- [ ] Existing logs/output format — how do their 11 baselines store per-checkpoint results? Reproducing their leaderboard numbers requires reading their existing result JSON format.

---

## Top-line baseline numbers (for Week 2 reproduction check)

Per the HTML version's Table (paraphrased; verify against repo at validation time):

| Model | Strict solve % |
|---|---|
| Opus 4.6 | 17.2 |
| GPT 5.4 | 11.8 |
| Opus 4.5 | 10.9 |
| GPT 5.1 Codex Max | 10.8 |
| GPT 5.2 | 10.8 |
| Sonnet 4.6 | 8.5 |
| GPT 5.3 Codex | 9.7 |
| GPT 5.2 Codex | 9.7 |
| Sonnet 4.5 | 5.4 |
| GLM 4.7 | 4.3 |
| GPT 5.3 Spark | 5.4 |

**Reproduction check (Week 2)**: pick 5 of these. Run their unmodified harness on 5 problems each. Verify our forked metric scripts produce solve rates within ±2 percentage points.

**Iboga model selection**: Claude Opus 4.7 (newer than their Opus 4.6), Qwen2.5-32B, Llama-3.1-8B, DeepSeek-Coder-V3. **None of our 4 models are in the SlopCodeBench leaderboard.** This means we cannot directly compare our untreated-control numbers against the leaderboard — we run our own untreated baselines as Arm C (unstructured) and treat that as our local control.

This is fine for the pre-registered design (paired-within-trajectory comparisons across arms), but it means we cannot claim "our intervention beats the SlopCodeBench leaderboard." That claim was never made. We measure *differential* arm effect within (model, problem) pairs.

---

## The future-work paragraph that validates the Iboga niche

From the Conclusion (quoted under fair use, <25 words):
> "interventions that enforce structural discipline across checkpoints... remain untested"

This is the gap Iboga occupies. The paper authors explicitly flag it as their open question.

**Implication for the SprocketLab coordination email (Week 7)**: open with "We are implementing the intervention-class your Conclusion §6 flags as untested." This signals respect for their declared territory.

---

## Risk flags identified during this read

1. **Clone-detection algorithm unspecified in paper**. If their `metrics/verbosity.py` uses a non-deterministic clone detector (e.g., random-projected MinHash), our reproductions may not be bit-exact. Mitigation: compare *distributions* across 5-problem reproductions, not point values. Tolerance ±2 pp matches the pre-reg.

2. **Slope computation unspecified in paper**. Same mitigation.

3. **The hook surface doesn't exist**. We're modifying a benchmark harness. There's a risk that our fork's "hook between checkpoints" subtly changes timing/scheduling and shifts measured metrics independent of intervention content. Mitigation: include a "Arm 0 — no retrospective at all, but with the empty hook running" as a sanity-check arm during pilot (Week 7). If Arm 0 matches Arm C on all metrics, the hook is benign.

4. **Their Docker images may be tied to specific Python versions / package pins**. Test environment must match.

5. **Cost on their 20 problems × 93 checkpoints**: at ~$0.10-0.30 per Opus 4.7 checkpoint, full Opus arm = $200-560. Our budget allocates $280 for Opus. **Tight.** May need to reduce to 16 of 20 problems for Opus arm only.

---

## Updates pushed back into the pre-reg before lock

Status as of 2026-05-12:

1. **§8 Treatment specifications**: done. Retrospective lives in the prompt for checkpoint k+1, not in workspace or `/tmp/`.
2. **§10 Stopping rules**: done. Arm 0 sanity-check arm added; if the hook itself shifts metrics, abort.
3. **§11 Pre-Lock Validation**: done. Explicit subtasks added for inspecting `metrics/verbosity.py` clone detection and `metrics/erosion.py` slope computation.
4. **§14 Solo Execution Plan budget**: unresolved risk. Do not silently reduce Opus to 16/20 problems; that changes the locked design and requires a pre-lock revision or post-lock OSF amendment.
5. **§16 External Coordination**: done. Opening sentence drafted in `sprocketlab-email.md`.

---

## Decision: are 20 problems enough?

Yes. With 4 models × 20 problems × 3 arms = 240 trajectories, the paired-within-(model,problem) design gives 80 paired observations per arm contrast. Power calc already validates this at d=0.4, α=0.025 → 0.92 power.

If Opus drops to 16 problems → 64 paired observations for Opus arm contrasts. Mixed-effects model in §9 absorbs the imbalance.

---

## Next read

Move from paper to repo. Week 1 task: `gh repo fork SprocketLab/slop-code-bench`, then inspect:
- `metrics/`
- `runner/` (or equivalent)
- `Dockerfile`
- Existing leaderboard JSON output format

Update this file with repo-level findings under `## Repo inspection (Week 2)`.
