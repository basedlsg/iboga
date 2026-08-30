# Bedrock access and model-selection note

**Checked:** 2026-08-03

This note records the endpoint assumptions used by the experiment. It contains
no credentials. Credentials must be supplied to the process at runtime and must
never be written into source files, Docker layers, logs, or result JSON.

## Verified model IDs

| Role | Model ID | US East standard price / 1M tokens | Documented max output | Use in the experiment |
|---|---|---:|---:|---|
| Primary cost/quality candidate | `deepseek.v3.2` | $0.62 input / $1.85 output | 8K | Main candidate; compare against the controls rather than assuming it wins. |
| Long-context sensitivity candidate | `moonshotai.kimi-k2.5` | $0.60 input / $3.00 output | 16K | Long-context and transfer replication. |
| Low-cost critic candidate | `zai.glm-4.7-flash` | $0.07 input / $0.40 output | 4K | Qualification and critic-cost arm after human validation. |
| Higher-cost critic sensitivity candidate | `zai.glm-5` | $1.00 input / $3.20 output | documented separately | Critic/model-family sensitivity, not the default cost path. |

The prices above are the US East standard on-demand prices shown on the AWS
pricing page at the time of this check. Region, service tier, cross-region
routing, and account terms can change the actual cost.

## API path

AWS documents all three candidate model IDs for the Bedrock Runtime Converse
path and the Bedrock Mantle OpenAI-compatible path. The project supports both:

- `IBOGA_BEDROCK_API=mantle` uses
  `https://bedrock-mantle.{region}.api.aws/v1/chat/completions`;
- `IBOGA_BEDROCK_API=converse` uses
  `https://bedrock-runtime.{region}.amazonaws.com/model/{modelId}/converse`.

The bearer credential is read from `AWS_BEARER_TOKEN_BEDROCK` at call time. The
project does not print it or persist it. The first live request must be a small
preflight that records endpoint, model ID, response shape, token usage, and
cost, then stops if the response is not parseable. It must not silently turn an
HTTP 200 envelope with the wrong schema into an experiment record.

For this project, use Converse when the Runtime path is the intended validation
surface, because it gives a stable `output.message.content` response shape and
supports the AWS-native model ID directly. Use Mantle only when the preflight
confirms the documented Chat Completions response shape for every selected
model.

## Selection rule

There is no defensible claim that one of these models is “best” for this study
before the qualification set is run. The practical default is:

1. DeepSeek V3.2 as the primary cost/quality candidate;
2. GLM 4.7 Flash as the low-cost critic candidate;
3. Kimi K2.5 as a long-context/transfer sensitivity model;
4. GLM 5 as a higher-cost critic sensitivity model if the budget permits.

The verifier must be qualified independently. A cheap model is not a safe
critic merely because it is cheap, and a more expensive model is not a gold
standard. Report false approval, false rejection, uncertainty, evidence recall,
and cost for each verifier configuration.

## Source documents

- [DeepSeek V3.2 model card](https://docs.aws.amazon.com/bedrock/latest/userguide/model-card-deepseek-deepseek-v3-2.html)
- [Kimi K2.5 model card](https://docs.aws.amazon.com/bedrock/latest/userguide/model-card-moonshot-ai-kimi-k2-5.html)
- [GLM 4.7 Flash model card](https://docs.aws.amazon.com/bedrock/latest/userguide/model-card-zai-glm-4-7-flash.html)
- [Bedrock API compatibility by model](https://docs.aws.amazon.com/bedrock/latest/userguide/models-api-compatibility.html)
- [Amazon Bedrock pricing](https://aws.amazon.com/bedrock/pricing/)
