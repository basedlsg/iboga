---
title: Iboga — Week 1 Runbook
status: draft
created: 2026-05-12
date_range: 2026-05-12 to 2026-05-18
tags: [iboga, runbook, week-1, prereg]
---

# Week 1 Runbook — 2026-05-12 to 2026-05-18

Purpose: make the Week 1 checklist executable without changing the experiment design. Do these in order. Do not run treatment trajectories before OSF lock.

## 1. Create Iboga Repo

From `projects/iboga/`:

```bash
gh repo create basedlsg/iboga \
  --public \
  --description "Pre-registered retrospective-protocol intervention study on SlopCodeBench" \
  --license MIT
```

Then initialize/push the local folder only if the repo is meant to track this project folder:

```bash
git init
git add .
git commit -m "Draft Iboga v0.5 preregistration artifacts"
git branch -M main
git remote add origin git@github.com:basedlsg/iboga.git
git push -u origin main
```

Validation:

```bash
gh repo view basedlsg/iboga --json nameWithOwner,url,visibility
```

Record result:

```text
repo_url = https://github.com/basedlsg/iboga
visibility = PUBLIC
created_or_verified = 2026-05-12
```

## 2. Fork SlopCodeBench And Pin Commit

Fork without cloning first:

```bash
gh repo fork SprocketLab/slop-code-bench --clone=false --remote=false
```

Pin upstream HEAD:

```bash
git ls-remote https://github.com/SprocketLab/slop-code-bench.git HEAD
```

Record:

```text
upstream_commit = 080922495aba9aedc4b7a6c80803bb5ffd301a49
fork_url = https://github.com/basedlsg/slop-code-bench
recorded = 2026-05-12
```

Then update:

- `prereg.md` frontmatter `substrate_repo_pin`
- `prereg.md` section 0 substrate harness row
- `harness-validation.md` upstream pin table

## 3. OSF Account

Create OSF account manually. Do not post the pre-reg yet.

Record:

```text
osf_account_created = <TBD>
account_email = <manual entry>
```

## 4. SlopCodeBench Paper Check

Current local notes are in `slopcodebench-study.md`. Before lock, verify against the paper/repo:

- Metrics equation references
- Docker/workspace persistence
- Agent-loop hook surface
- Reproduction protocol

Record any corrections in:

- `slopcodebench-study.md`
- `prereg.md`
- `next-steps.md` decision log

## 5. GPU Vendor Setup

Create RunPod or Vast.ai account manually. Do not rent GPU yet.

Record:

```text
gpu_vendor = <TBD>
account_ready = <TBD>
target_gpu = A10G or equivalent 24GB
```

## 6. Budget Confirmation

Before any paid run:

```text
budget_cap_confirmed = <TBD>
hard_cap = 900 USD
soft_tracking_threshold = 810 USD
```

If the budget cannot support the locked 4-model x 20-problem x 3-arm design, revise before OSF lock. After lock, any model-list or sample-size change is an OSF amendment.

## 7. Local Sanity Check

Run:

```bash
python3 scripts/prelock_sanity.py
```

Expected:

```text
prelock sanity ok
```

## End Of Week 1 Exit Criteria

- [x] `basedlsg/iboga` exists
- [x] `SprocketLab/slop-code-bench` fork exists
- [x] Upstream commit hash recorded locally
- [ ] OSF account exists but pre-reg remains unposted
- [ ] GPU vendor account exists but no GPU spend incurred
- [ ] Budget cap confirmed
- [ ] Local sanity check passes
