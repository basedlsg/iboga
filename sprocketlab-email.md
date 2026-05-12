---
title: SprocketLab Coordination Email — Draft
status: draft
created: 2026-05-12
send_target: Week 7 (2026-06-23 — 2026-07-01)
recipients: SprocketLab PIs (SlopCodeBench authors, identify from arXiv 2603.24755 author list)
tags: [iboga, coordination, sprocketlab]
---

# Coordination Email to SprocketLab — Draft

**Purpose**: transparency, not collaboration. Inform the SlopCodeBench authors that we are running a pre-registered intervention experiment on top of their benchmark, opening with explicit acknowledgement of their declared future work.

**Why send it**: NeurIPS reviewer N2 + CMU chair both flagged competition risk — SprocketLab is the natural author of an "interventions on SlopCodeBench" follow-up paper. Sending this email is professional courtesy, de-risks a "you stole our follow-up" surprise, and may surface useful information about their plans.

**Tone**: respectful, brief, no ask. We're not requesting code review, collaboration, or comment. Just informing.

---

## Subject

`Pre-registered extension to SlopCodeBench: retrospective-protocol intervention layer`

## Body

```
Hi <Author Name>,

I'm pre-registering an empirical experiment that uses SlopCodeBench
as a substrate. I wanted to flag it before posting to OSF, in case
it's useful context for your group's own planning.

Your Conclusion explicitly notes that "interventions that enforce
structural discipline across checkpoints... remain untested." We
are pre-registering a 4-model × 3-arm test of exactly that: a
between-checkpoint retrospective protocol (with closed-vocabulary
structural constraint vs vocabulary-neutral vs unstructured), with
structural-erosion slope and solve-rate non-inferiority as paired
primary outcomes. 240 trajectories total, ICLR 2027 workshop target.

What we are NOT touching:
- Your metrics/ directory. Reproductions use your code unmodified.
- Your problem set. We use the 20 problems and 93 checkpoints as published.
- Your leaderboard. We run our own untreated-control arm rather than
  comparing against your published baselines.

What we add:
- A between-checkpoint hook in runner/ that lets a retrospective LLM
  call happen on the host between Docker checkpoint runs, with the
  retrospective text injected into the next checkpoint's agent prompt.
- Three retrospective vocabularies (treatment, neutral, none).
- Exploratory SAE analysis on Llama-3.1-8B using Goodfire's open SAEs.

We're not asking for anything — just letting you know in case any
of this overlaps with what your group is planning. The pre-reg will
be public on OSF (DOI included once registered, target 2026-07-01).
The code fork will be at github.com/basedlsg/iboga.

Submission target: ICLR 2027 workshop (Recursive Self-Improvement
or Lifelong Agents). Happy to share the pre-reg early if useful.

Thanks for SlopCodeBench — it's exactly the substrate this kind of
work has been missing.

Best,
Carlos
flareondon@gmail.com
```

---

## Notes for sending

- **Recipients**: identify from the arXiv 2603.24755 author list. Likely Andrew Pickett (first author) and the senior author. Cross-reference SprocketLab's website (sprocketlab.org or similar).
- **Send via**: personal email, not a form. Plain text, no signature block beyond name + email.
- **Don't include**:
  - Resumé / credentials (looks like job-seeking)
  - The full pre-reg PDF (overkill; link if asked)
  - Any AA / iboga framing (use neutral language)
  - Anthropic Fellowship mention (irrelevant)
- **Timing**: send during business hours US/East. Wednesday or Thursday best.
- **No follow-up if no response**: this is transparency, not a request. Silence = no objection.

---

## Possible responses and how to handle

| Response | Action |
|---|---|
| "Thanks, sounds interesting, good luck" | Reply once, briefly. Done. |
| "We're working on something similar — let's coordinate" | Real opportunity. Reply within 24h proposing 30-min call. **Do not promise collaboration** without thinking. |
| "Please don't use our benchmark for this" | Unusual for academic norms but possible. Reply asking for specific concerns. Most likely they want attribution / disclaimer language; offer to include. |
| "We'd like to collaborate as co-authors" | Real fork in the road. Solo decision was deliberate (per advisor). Decline politely, offer to acknowledge their feedback. |
| No response after 2 weeks | Send the OSF DOI when registered as a one-line update. Then drop it. |

---

## Don't send before:

- The pre-reg is fully drafted (yes — done 2026-05-12)
- The OSF account is created (Week 1)
- The fork repo exists publicly at github.com/basedlsg/iboga (Week 1)
- The harness reproduction has been validated (Week 2-3)
- You're confident in the timeline (i.e. you haven't slipped past Aug)

Sending too early risks confusion if plans change. Sending too late risks them publishing first.

**Right window**: between successful pilot and OSF post. That's Week 7, late June.
