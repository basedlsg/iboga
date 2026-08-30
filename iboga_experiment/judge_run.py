"""Qualify a model as a judge against the semantic mutation set.

Python holds the answer key; the model does the judging. The model sees only the
task, its evidence, and one artifact. It never sees the category, the
explanation, the item id, or how many items are defective — the base rate is the
single biggest leak, because a judge told that most items are broken can score
well by rejecting everything.

The output is two numbers that must be read together:

    false approval  — defective artifacts the judge waved through
    false rejection — clean artifacts the judge condemned

Neither is a score on its own. A judge that rejects everything has a perfect
false-approval rate.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .client import BedrockConverseClient, BedrockMantleClient
from .config import MODELS, PROVIDERS, ModelSpec, Settings, custom_model
from .schema import extract_json
from .semantic_mutations import MutationItem, build_mutation_set, score_judge

# Deliberately neutral. "Find the flaw" would inflate false rejection, and the
# false-rejection number is half the result.
JUDGE_SYSTEM = (
    "You review work artifacts produced by another agent. For each artifact you "
    "decide one thing: does its conclusion follow from the evidence it cites, "
    "within the scope the task defines?\n\n"
    "Approve when the artifact is supported by its cited evidence and stays "
    "within what that evidence establishes. Reject when it is not supported — "
    "for example when a rule claims more than the evidence shows, when a "
    "necessary condition or exception has been dropped, when the cited evidence "
    "does not bear on the conclusion, when a stated status is not what the "
    "evidence supports, or when confidence is not warranted. Answer uncertain "
    "only when the task genuinely does not determine an answer.\n\n"
    "Some artifacts are correct. Approving a correct artifact is as important as "
    "rejecting a flawed one.\n\n"
    "Return only JSON matching:\n"
    '{"verdict": "approve|reject|uncertain", "reasons": ["short reason"], '
    '"unsupported_claim": "the specific claim that is not supported, or null"}'
)


# Fields that describe how the artifact was produced rather than what it claims.
# `critic_decision` is another reviewer's verdict: showing it invites the judge to
# either defer to it or reject on the mismatch, which scores the wrong thing. In
# the smoke run it caught an over-refusal purely by noticing that this field
# disagreed with the answer, never engaging with the over-refusal itself.
PROCESS_FIELDS = ("critic_decision",)


# The whole-artifact prompt caught 86% of answer/status defects but only 31-41%
# of defects in the memory rule — the part that gets persisted and reapplied.
# This asks the narrow question instead. It is a specialist: by construction it
# cannot see an over-refusal or a bad citation, so its overall false-approval
# rate is not comparable to whole mode. Compare per defect location.
RULE_SYSTEM = (
    "You review a rule that an agent proposes to remember and apply to later "
    "work. You see the task it came from, the evidence that was available, and "
    "the proposed rule.\n\n"
    "Decide one thing: does the rule state exactly what the evidence supports?\n\n"
    "Reject when the rule claims more than the evidence establishes, when it "
    "drops a condition or exception the evidence requires, when its trigger "
    "would fire in the wrong circumstances, when it contradicts the evidence, or "
    "when its disallowed_action does not name the specific action the evidence "
    "says to prevent. Approve when the rule and its guardrail match what the "
    "evidence supports. Answer uncertain only when the evidence genuinely does "
    "not settle the rule's scope.\n\n"
    "Many proposed rules are correct. Approving a correct rule matters as much "
    "as rejecting a flawed one.\n\n"
    "Return only JSON matching:\n"
    '{"verdict": "approve|reject|uncertain", "reasons": ["short reason"], '
    '"unsupported_claim": "the part of the rule the evidence does not support, or null"}'
)

MODES = ("whole", "rule")


def judge_prompt(dossier: dict[str, Any], artifact: dict[str, Any], mode: str = "whole") -> str:
    task = {
        "task": dossier.get("task"),
        "evidence": dossier.get("evidence", []),
    }
    if mode == "rule":
        body = artifact.get("memory_candidate")
        return (
            "TASK AND AVAILABLE EVIDENCE\n"
            + json.dumps(task, ensure_ascii=False, indent=2)
            + "\n\nPROPOSED RULE\n"
            + json.dumps(body, ensure_ascii=False, indent=2)
            + "\n\nReturn only the JSON verdict object."
        )
    claim = {key: value for key, value in artifact.items() if key not in PROCESS_FIELDS}
    return (
        "TASK AND AVAILABLE EVIDENCE\n"
        + json.dumps(task, ensure_ascii=False, indent=2)
        + "\n\nARTIFACT UNDER REVIEW\n"
        + json.dumps(claim, ensure_ascii=False, indent=2)
        + "\n\nReturn only the JSON verdict object."
    )


def system_for(mode: str) -> str:
    return RULE_SYSTEM if mode == "rule" else JUDGE_SYSTEM


@dataclass
class ModelJudge:
    """A model in the judge seat. Failures are recorded, never recoded."""

    client: Any
    model: ModelSpec
    mode: str = "whole"
    max_retries: int = 2
    temperature: float = 0.0
    calls: list[dict[str, Any]] = field(default_factory=list)

    def __call__(self, dossier: dict[str, Any], artifact: dict[str, Any]) -> dict[str, Any]:
        prompt = judge_prompt(dossier, artifact, self.mode)
        last_error = ""
        for attempt in range(self.max_retries + 1):
            started = time.monotonic()
            try:
                completion = self.client.complete(
                    self.model,
                    system_for(self.mode),
                    prompt,
                    max_tokens=600,
                    temperature=self.temperature,
                )
            except Exception as error:  # provider failure stays a first-class record
                last_error = f"{type(error).__name__}: {error}"
                continue
            latency = round(time.monotonic() - started, 3)
            # extract_json raises on a malformed slice. Letting that propagate
            # would abort the whole run over one bad reply, which is the opposite
            # of keeping failures first-class: 108 good verdicts would be lost
            # because the 109th model response had a stray token.
            try:
                parsed = extract_json(completion.text)
                parse_error = ""
            except Exception as error:
                parsed = None
                parse_error = f"unparseable response: {type(error).__name__}: {error}"
            if not isinstance(parsed, dict) or parsed.get("verdict") not in {"approve", "reject", "uncertain"}:
                # Keep the specific parse failure; the generic message loses the
                # detail that says whether the model was wrong or the parser was.
                last_error = parse_error or "response did not contain a valid verdict object"
                self.calls.append({"attempt": attempt, "ok": False, "cost_usd": completion.cost_usd})
                continue
            self.calls.append(
                {
                    "attempt": attempt,
                    "ok": True,
                    "cost_usd": completion.cost_usd,
                    "cost_source": completion.cost_source,
                    "input_tokens": completion.input_tokens,
                    "output_tokens": completion.output_tokens,
                    "latency_seconds": latency,
                }
            )
            return {
                "verdict": parsed["verdict"],
                "reasons": parsed.get("reasons", []),
                "meta": {
                    "unsupported_claim": parsed.get("unsupported_claim"),
                    "model_id": completion.model_id,
                    "input_tokens": completion.input_tokens,
                    "output_tokens": completion.output_tokens,
                    "cost_usd": completion.cost_usd,
                    "cost_source": completion.cost_source,
                    "latency_seconds": latency,
                    "attempts": attempt + 1,
                },
            }
        return {"verdict": "unavailable", "reasons": [last_error], "meta": {"error": last_error}}


@dataclass
class DryRunJudge:
    """Renders every prompt without calling a provider.

    This exists so the whole pipeline — blinding, ordering, scoring, reporting —
    can be verified for free. It returns `unavailable` because it has no opinion,
    which also exercises the unavailable path.
    """

    mode: str = "whole"
    prompts: list[dict[str, Any]] = field(default_factory=list)

    def __call__(self, dossier: dict[str, Any], artifact: dict[str, Any]) -> dict[str, Any]:
        prompt = judge_prompt(dossier, artifact, self.mode)
        self.prompts.append({"system": system_for(self.mode), "user": prompt})
        return {"verdict": "unavailable", "reasons": ["dry run: no provider called"]}


def ordered_items(seed: int = 7) -> list[MutationItem]:
    """Shuffle so the judge never sees items grouped by defect type."""
    items, _ = build_mutation_set()
    rng = random.Random(seed)
    rng.shuffle(items)
    return items


def leak_check(items: list[MutationItem]) -> list[str]:
    """Nothing the judge sees may name the defect."""
    problems: list[str] = []
    for item in items:
        payload = json.dumps(
            {mode: [judge_prompt(item.dossier, item.artifact, mode), system_for(mode)] for mode in MODES}
        ).lower()
        if item.category != "control" and item.category.replace("_", " ") in payload:
            problems.append(f"{item.item_id}: category name appears in the prompt")
        if item.category != "control" and item.category in payload:
            problems.append(f"{item.item_id}: category slug appears in the prompt")
        if item.defect_explanation and item.defect_explanation.lower()[:40] in payload:
            problems.append(f"{item.item_id}: the answer key appears in the prompt")
        if item.item_id.lower() in payload:
            problems.append(f"{item.item_id}: the internal item id appears in the prompt")
    return problems


def run(judge: Any, items: list[MutationItem], *, model_name: str, seed: int, provider: str = "dry-run", mode: str = "whole") -> dict[str, Any]:
    result = score_judge(items, judge)
    calls = getattr(judge, "calls", [])
    return {
        "experiment": "judge-qualification-v0.1",
        "judge_model": model_name,
        "provider": provider,
        "mode": mode,
        "cost_source": (calls[0].get("cost_source") if calls else None),
        "order_seed": seed,
        "set": "semantic-mutation-set-v0.1",
        "claim": (
            "False approval and false rejection must be read together. A judge that "
            "rejects every artifact has a perfect false-approval rate."
        ),
        "total_cost_usd": round(sum(call.get("cost_usd", 0.0) for call in calls), 6),
        "n_calls": len(calls),
        **result,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Qualify a model judge on the semantic mutation set")
    parser.add_argument(
        "--provider",
        default=None,
        choices=sorted(PROVIDERS),
        help="overrides IBOGA_PROVIDER; openrouter needs OPENROUTER_API_KEY",
    )
    parser.add_argument("--model", help="a key from the selected provider's catalog")
    parser.add_argument(
        "--model-id",
        help="any provider slug, e.g. 'z-ai/glm-4.6'. The catalog is a convenience, not a limit.",
    )
    parser.add_argument("--price-in", type=float, default=0.0, help="USD per million input tokens for --model-id")
    parser.add_argument("--price-out", type=float, default=0.0, help="USD per million output tokens for --model-id")
    parser.add_argument("--mode", default="whole", choices=MODES, help="whole artifact, or the memory rule alone")
    parser.add_argument("--limit", type=int, help="judge only the first N items (smoke run)")
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--dry-run", action="store_true", help="render prompts without calling a provider")
    parser.add_argument("--show-prompt", action="store_true", help="print one rendered prompt and exit")
    parser.add_argument("--out", type=Path, default=Path("results/judge-qualification-v0.1.json"))
    args = parser.parse_args()

    items = ordered_items(args.seed)
    problems = leak_check(items)
    if problems:
        raise SystemExit("the judge prompt leaks the answer key:\n  " + "\n  ".join(problems[:10]))
    if args.limit:
        items = items[: args.limit]

    if args.show_prompt:
        sample = items[0]
        print(system_for(args.mode))
        print("\n" + "=" * 70 + "\n")
        print(judge_prompt(sample.dossier, sample.artifact, args.mode))
        return

    if args.dry_run:
        judge: Any = DryRunJudge(mode=args.mode)
        model_name = "dry-run"
        provider_label = "dry-run"
    else:
        if args.provider:
            os.environ["IBOGA_PROVIDER"] = args.provider
        settings = Settings.from_env()
        catalog = PROVIDERS[settings.provider].models
        if args.model_id:
            model = custom_model(args.model_id, input_price=args.price_in, output_price=args.price_out)
        else:
            name = args.model or PROVIDERS[settings.provider].default_critic
            if name not in catalog:
                raise SystemExit(
                    f"{name} is not in the {settings.provider} catalog "
                    f"({', '.join(sorted(catalog))}). Use --model-id to pass any provider slug."
                )
            model = catalog[name]
        try:
            settings.require_api_key()
        except RuntimeError as error:
            alternative = "openrouter" if settings.provider == "bedrock-mantle" else "bedrock-mantle"
            raise SystemExit(
                f"{error}\n\nProvider is {settings.provider} ({settings.base_url}).\n\n"
                f"Export {settings.api_key_env} in this shell, then:\n"
                f"  PYTHONPATH=. python3 -m iboga_experiment.judge_run "
                f"--provider {settings.provider} --limit 10\n\n"
                "In Docker, which keeps the token out of argv and out of the image:\n"
                f"  export {settings.api_key_env}='...'\n"
                "  scripts/run-judge.sh preflight\n"
                "  scripts/run-judge.sh smoke\n\n"
                f"To use {alternative} instead, pass --provider {alternative} with "
                f"{PROVIDERS[alternative].api_key_env} set.\n\n"
                "To verify everything except the provider call:\n"
                "  PYTHONPATH=. python3 -m iboga_experiment.judge_run --dry-run"
            ) from None
        client = BedrockConverseClient(settings) if settings.api_mode == "converse" else BedrockMantleClient(settings)
        judge = ModelJudge(client, model, mode=args.mode)
        model_name = model.model_id
        provider_label = settings.provider

    result = run(judge, items, model_name=model_name, seed=args.seed, provider=provider_label, mode=args.mode)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    summary = {key: value for key, value in result.items() if key != "records"}
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
