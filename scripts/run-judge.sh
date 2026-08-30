#!/usr/bin/env bash
# Run the judge qualification against Bedrock Mantle, in Docker.
#
# The credential is passed with `-e NAME` (no value), so Docker inherits it from
# this shell. The token never appears in argv, so it stays out of `ps`, out of
# shell history, and out of any image layer. Do not add it as a build arg, an
# ENV line, or a file inside the image.
#
# Usage:
#   export AWS_BEARER_TOKEN_BEDROCK=...        # in your shell only
#   scripts/run-judge.sh preflight             # list models, no inference, no spend
#   scripts/run-judge.sh smoke                 # 10 items
#   scripts/run-judge.sh full                  # all 109 items
#   scripts/run-judge.sh tests                 # run the suite in the image
#   scripts/run-judge.sh shell                 # interactive container
#
# MODE=rule narrows review to the persisted memory rule.
#
# Override the judge model with JUDGE_MODEL (default: glm-4.7-flash).
# Available on Bedrock Mantle: deepseek-v3.2, kimi-k2.5, glm-4.7-flash, glm-5

set -euo pipefail

IMAGE="${IMAGE:-iboga-reliability:latest}"
KEY_VAR="AWS_BEARER_TOKEN_BEDROCK"
JUDGE_MODEL="${JUDGE_MODEL:-glm-4.7-flash}"
# whole = the full artifact; rule = the persisted memory rule alone
MODE="${MODE:-whole}"
COMMAND="${1:-smoke}"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ -z "${!KEY_VAR:-}" ]]; then
  cat >&2 <<EOF
$KEY_VAR is not set in this shell.

Export it here, not in a file and not in a chat message:

    export $KEY_VAR='...'
    $0 $COMMAND

It is read at call time, passed to the container by name only, and never
written to a layer, a checkpoint, or a result file.
EOF
  exit 1
fi

if ! docker info >/dev/null 2>&1; then
  echo "The Docker daemon is not running. Start Docker Desktop and retry." >&2
  exit 1
fi

echo "==> building $IMAGE"
docker build -q -t "$IMAGE" "$REPO_ROOT" >/dev/null

# `-e NAME` with no `=value` tells Docker to inherit the value from this
# environment. Writing `-e NAME=$VALUE` would expose the token in the process
# table to every user on the machine.
run() {
  docker run --rm \
    -e "$KEY_VAR" \
    -e IBOGA_PROVIDER=bedrock-mantle \
    -v "$REPO_ROOT/results:/app/results" \
    "$IMAGE" "$@"
}

case "$COMMAND" in
  preflight)
    echo "==> listing models (no inference, no spend)"
    run python -m iboga_experiment.preflight
    ;;
  smoke)
    echo "==> judging 10 items with $JUDGE_MODEL (mode=$MODE)"
    run python -m iboga_experiment.judge_run \
      --provider bedrock-mantle --model "$JUDGE_MODEL" --mode "$MODE" --limit 10 \
      --out "results/judge-qualification-smoke-${MODE}.json"
    ;;
  full)
    echo "==> judging all items with $JUDGE_MODEL (mode=$MODE)"
    run python -m iboga_experiment.judge_run \
      --provider bedrock-mantle --model "$JUDGE_MODEL" --mode "$MODE" \
      --out "results/judge-qualification-${JUDGE_MODEL}-${MODE}.json"
    ;;
  tests)
    echo "==> running the suite inside the image"
    docker run --rm "$IMAGE" python -m unittest discover -s tests
    ;;
  shell)
    docker run --rm -it -e "$KEY_VAR" -e IBOGA_PROVIDER=bedrock-mantle \
      -v "$REPO_ROOT/results:/app/results" "$IMAGE" bash
    ;;
  *)
    echo "unknown command: $COMMAND (expected preflight, smoke, full, tests, or shell)" >&2
    exit 1
    ;;
esac
