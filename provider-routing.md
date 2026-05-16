---
title: Iboga — Provider Routing Notes
status: draft
created: 2026-05-13
tags: [iboga, providers, slopcodebench, validation]
---

# Provider Routing Notes

Purpose: record the non-Anthropic execution routes for SlopCodeBench validation without changing the locked 4-model x 3-arm design.

## Current Local State

- Gemini CLI is installed: `gemini --version` reports `0.41.2`.
- Jules CLI is installed: `jules version` reports `v0.1.42`.
- This shell has no provider env vars exported: `OPENROUTER_API_KEY`, `GEMINI_API_KEY`, `GOOGLE_API_KEY`, `TOGETHER_API_KEY`, `DEEPSEEK_API_KEY`, `LLAMA_API_KEY`, and `JULES_API_KEY` are unset.
- SlopCodeBench is run through `uv run slop-code ...` from `projects/iboga/slop-code-bench/`; `slop-code` is not on the global shell `PATH`.

## Local SlopCodeBench Findings

`slop-code-bench/configs/providers.yaml` already supports:

- `openrouter` via `OPENROUTER_API_KEY`
- `google` via `GEMINI_API_KEY`
- `gemini_auth` via `~/.gemini/oauth_creds.json`
- `together` via `TOGETHER_API_KEY`
- `deepseek` via `DEEPSEEK_API_KEY`

The credential resolver uses the provider prefix from `--model provider/name`. Consequence:

- `--model gemini_auth/gemini-2.5-flash-lite` uses the Gemini CLI OAuth-file provider.
- `--model google/gemini-2.5-flash-lite` requires `GEMINI_API_KEY`.
- `--model openrouter/...` requires `OPENROUTER_API_KEY`.

The pinned clone has no Jules agent integration and no Meta Llama Developer API provider entry.

## Dry-Run Results

Passing non-Anthropic route:

```bash
uv run slop-code run \
  --config configs/runs/lite_under20.yaml \
  --agent gemini \
  --model gemini_auth/gemini-2.5-flash-lite \
  --dry-run \
  --no-live-progress
```

Result on 2026-05-13: credential resolution passed; preview selected `mvvault` and `xjq`; no changes made.

OpenRouter probe:

```bash
uv run slop-code run \
  --config configs/runs/lite_under20.yaml \
  --agent miniswe \
  --model openrouter/gemini-2.5-flash-lite \
  --dry-run \
  --no-live-progress
```

Result on 2026-05-13: stopped only because `OPENROUTER_API_KEY` is not exported in this shell.

After adding local SlopCodeBench model configs in the fork clone, these locked-model probes also reach OpenRouter credential resolution and stop only because `OPENROUTER_API_KEY` is unset:

```bash
uv run slop-code run --config configs/runs/lite_under20.yaml --agent miniswe --model openrouter/opus-4.7-openrouter --dry-run --no-live-progress
uv run slop-code run --config configs/runs/lite_under20.yaml --agent miniswe --model openrouter/qwen2.5-32b-instruct --dry-run --no-live-progress
uv run slop-code run --config configs/runs/lite_under20.yaml --agent miniswe --model openrouter/llama-3.1-8b-instruct --dry-run --no-live-progress
```

Gemini Docker image build:

```bash
uv run slop-code docker build-agent \
  configs/agents/gemini.yaml \
  configs/environments/docker-python3.12-uv.yaml
```

Result on 2026-05-13: passed after freeing Docker Desktop storage. Built `slop-code:python3.12` and `slop-code:gemini-0.41.2-python3.12`.

Actual no-treatment Gemini validation:

```bash
uv run slop-code run \
  --config configs/runs/lite_under20.yaml \
  --agent gemini \
  --model gemini_auth/gemini-2.5-flash-lite \
  --problem xjq \
  --no-live-progress
```

Result on 2026-05-13: checkpoint 1 completed/evaluated; checkpoint 2 did not complete because Gemini CLI hit Google Code Assist capacity errors (`429`, `MODEL_CAPACITY_EXHAUSTED`) after a long loop. The run was stopped manually before the one-hour checkpoint timeout. This validates auth, Docker, execution, and evaluation for one checkpoint, but not full baseline reproducibility.

## Official Documentation Checked

- OpenRouter authentication uses bearer API keys and an OpenAI-compatible base URL: <https://openrouter.ai/docs/api/reference/authentication>
- OpenRouter lists Claude Opus 4.7 as `anthropic/claude-opus-4.7`: <https://openrouter.ai/anthropic/claude-opus-4.7/api>
- OpenRouter lists Qwen2.5-32B-Instruct as `qwen/qwen2.5-32b-instruct`: <https://openrouter.ai/qwen/qwen2.5-32b-instruct/api>
- OpenRouter lists Llama-3.1-8B-Instruct as `meta-llama/llama-3.1-8b-instruct`: <https://openrouter.ai/meta-llama/llama-3.1-8b-instruct/api>
- OpenRouter lists DeepSeek V3 0324 as `deepseek/deepseek-chat-v3-0324`, which is not the same as a confirmed `DeepSeek-Coder-V3` slug: <https://openrouter.ai/deepseek/deepseek-chat-v3-0324%3Afree/api>
- Google documents Gemini CLI as a local terminal agent with Gemini Code Assist/API-key routes: <https://developers.google.com/gemini-code-assist/docs/gemini-cli>
- Jules CLI is a remote-session manager for Jules tasks, not a model provider: <https://jules.google/docs/cli/reference/>
- Jules REST API uses `JULES_API_KEY` and `x-goog-api-key`: <https://jules.google/docs/api/reference/authentication/>
- Meta's authenticated Llama Developer docs are not readable without login from this environment: <https://llama.developer.meta.com/docs/overview>
- Public Meta LlamaCon material says Llama API has Python/TypeScript SDKs and OpenAI SDK compatibility, but exact endpoint/model strings must be copied from the portal before lock: <https://about.fb.com/ltam/news/2025/04/todo-lo-que-anunciamos-en-nuestro-primer-llamacon/>

## Required Before Pilot

1. Export `OPENROUTER_API_KEY` in the run shell or configure direnv. Gemini CLI OAuth is valid but capacity-limited today, so OpenRouter is the cleaner route for the next full no-treatment validation.
2. Verify and commit the local SlopCodeBench model-config patch in the SlopCodeBench fork if these routes are retained:
   - `configs/models/opus-4.7-openrouter.yaml`
   - `configs/models/qwen2.5-32b-instruct.yaml`
   - `configs/models/llama-3.1-8b-instruct.yaml`
3. Verify DeepSeek before lock. OpenRouter lists DeepSeek V3 variants, but the exact `DeepSeek-Coder-V3` slug is not present in the pinned local model catalog. Do not silently substitute `deepseek/deepseek-chat-v3-0324` unless the pre-reg model name is corrected before OSF lock.
4. If Meta Llama Developer API is used instead of OpenRouter for Llama-3.1-8B, copy the exact official endpoint/model string from the authenticated portal into this file and add a provider config to the SlopCodeBench fork.
5. Re-price the budget rows after exact provider slugs are locked.

## Roles of the Tool Stack (LOCKED 2026-05-15 — NVIDIA free hosted API)

OpenRouter was retired 2026-05-15 (it requires a funded account; project direction is no paid path). The everything-above provider notes are historical; the live routing is:

| Tool | Role | Status |
|---|---|---|
| **NVIDIA hosted NIM API** | **Primary route for all 4 trajectory models** (`integrate.api.nvidia.com/v1`, OpenAI-compatible, free tier). Models: `meta/llama-3.3-70b-instruct`, `qwen/qwen3-next-80b-a3b-instruct`, `deepseek-ai/deepseek-v4-pro`, `nvidia/llama-3.1-nemotron-70b-instruct`. All via the `opencode` agent. | Provider in `providers.yaml`; 4 `nvidia-*` model configs in `configs/models/`. Verified multi-checkpoint, $0. |
| **Gemini CLI** | Free OAuth route. Verified — completed a full 6-checkpoint trajectory. Kept as fallback if NVIDIA throttles a model; not a primary trajectory model (different agent → confound). | Installed v0.41.2; OAuth working. |
| **Jules** | Engineering coordinator. Ran J6-J9 (hook, `iboga_runner.py`, SAE selector, reproduction harness) — all complete and merged. | v0.1.42; done. |
| **Groq / Llama Dev API** | Evaluated, not adopted. Groq free tier 12K TPM too small; Llama Dev API works but `opencode` won't route its custom slugs. Provider configs retained as documented fallbacks. | Not used. |

**Operating rule**: all 432 trajectories route through the NVIDIA provider via `opencode`. Free-tier rate limits (not dollars) are the constraint — the main run batches across its window with 429 backoff. Gemini CLI is the only sanctioned fallback and using it for any locked-model trajectory is a documented deviation.

### Jules engineering tasks (explicit, in-scope)

Jules can be dispatched the same way it was used in silentvault's J1-J5 series. Currently queued:

- **J6** — implement the `--between-checkpoint-hook` integration in `src/slop_code/agent_runner/runner.py` per the contract in `harness-validation.md`. Test on `lite_under20`.
- **J7** — write `scripts/iboga_runner.py` host-side wrapper: takes (trajectory_id, model, problem, arm), invokes SlopCodeBench fork with hook configured, writes outputs to `~/iboga-data/sessions/{trajectory-id}/`.
- **J8** — write `scripts/collect_sae_activations.py`: loads Goodfire l19 SAE for Llama-3.1-8B, captures mean activation of locked feature set per token position over a retrospective text input.
- **J9** — write the metric reproduction harness comparing forked vs upstream `erosion`/`verbosity`/`solve_rate` outputs across 5 baseline models × 5 problems, with ±2 pp tolerance check.
- ~~**J10** — DeepSeek slug resolution~~ **CLOSED 2026-05-14**: resolved manually via WebFetch of `https://openrouter.ai/deepseek`. "DeepSeek-Coder-V3" does not exist. Locked to `deepseek/deepseek-chat-v3-0324`. SlopCodeBench provider config still needed — folded into J6 scope (or a small J10' patch task once `basedlsg/iboga` is public).

These dispatch only after the `basedlsg/iboga` repo is public on GitHub and connected to Jules. Jules tasks are pure engineering — they touch the harness fork, scripts, and configs, not the pre-reg or experimental design.

## Scope Guard

This provider-routing update does not add arms, models, collaborators, or outcome measures. It removes the stale direct-Anthropic-key assumption and records the work needed to make the locked model set reproducible before OSF lock.
