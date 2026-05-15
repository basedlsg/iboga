#!/usr/bin/env python3
"""Iboga host-side trajectory launcher.

Usage:
  python scripts/iboga_runner.py \
    --trajectory-id <hash> \
    --model <openrouter-slug> \
    --problem <slopcodebench-problem-id> \
    --arm A|B|C|0 \
    [--dry-run]
"""

import argparse
import json
import logging
import os
import shlex
import subprocess
import sys
import time
from pathlib import Path

import httpx
import jsonschema

# Configure basic logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


# --- Configuration and Constants ---
PRICING = {
    "anthropic/claude-opus-4.7": (5.0, 25.0),
    "qwen/qwen3-32b": (0.08, 0.28),
    "meta-llama/llama-3.1-8b-instruct": (0.02, 0.05),
    "deepseek/deepseek-chat-v3-0324": (0.20, 0.77),
}

ARM_SCHEMAS = {
    "A": "schemas/arm-a.json",
    "B": "schemas/arm-b.json",
    "C": "schemas/arm-c.json",
    "0": "schemas/arm-c.json", # Arm 0 uses C schema but emits empty
}

# Maps the OpenRouter slug (arm-assignment.json) -> SlopCodeBench --model arg.
# The internal names match slop-code-bench/configs/models/*.yaml internal_name fields.
SCB_MODEL_MAP = {
    "anthropic/claude-opus-4.7": "openrouter/claude-opus-4-7",
    "qwen/qwen3-32b": "openrouter/qwen3-32b",
    "meta-llama/llama-3.1-8b-instruct": "openrouter/llama-3.1-8b-instruct",
    "deepseek/deepseek-chat-v3-0324": "openrouter/deepseek-chat-v3-0324",
}

MAX_BUDGET = 900.0

def get_slopcodebench_dir() -> Path:
    # Resolve SlopCodeBench directory
    scb_dir = os.environ.get("SLOPCODEBENCH_DIR")
    if scb_dir:
        scb_path = Path(scb_dir)
    else:
        scb_path = Path(__file__).resolve().parent.parent.parent / "slop-code-bench"
        if not scb_path.exists():
            # Try to see if it's cloned inside the repo
            scb_path = Path(__file__).resolve().parent.parent / "slop-code-bench"

    return scb_path

def check_mount_guard(scb_path: Path):
    run_config = os.environ.get("SCB_RUN_CONFIG", "configs/runs/lite_under20.yaml")
    config_path = scb_path / run_config
    if not config_path.exists():
        logging.warning(f"SlopCodeBench config {config_path} not found. Skipping mount guard.")
        return

    in_mounts = False
    with open(config_path, "r") as f:
        for line in f:
            if "extra_mounts:" in line:
                in_mounts = True
                continue
            if in_mounts:
                stripped = line.strip()
                if stripped.startswith("-"):
                    mount_path = stripped.lstrip("-").strip()
                    if "iboga-data" in mount_path:
                        logging.error(f"Mount guard violation! Config {config_path} mounts iboga-data: {mount_path}")
                        sys.exit(1)
                elif stripped and not stripped.startswith("#"):
                    if not line.startswith(" ") and not line.startswith("	"):
                        in_mounts = False

def ensure_session_dir(trajectory_id: str) -> Path:
    home = Path.home()
    session_dir = home / "iboga-data" / "sessions" / trajectory_id
    session_dir.mkdir(parents=True, exist_ok=True)
    return session_dir

def check_budget_and_abort():
    home = Path.home()
    cost_total_path = home / "iboga-data" / "cost-total.json"
    if cost_total_path.exists():
        try:
            with open(cost_total_path) as f:
                data = json.load(f)
                total = data.get("total_cost", 0.0)
                if total >= MAX_BUDGET:
                    logging.error(f"Hard stop! Cumulative cost {total:.2f} >= budget {MAX_BUDGET}")
                    sys.exit(1)
        except Exception as e:
            logging.warning(f"Failed to read cost total: {e}")

def update_cost(trajectory_id: str, in_tokens: int, out_tokens: int, model: str):
    home = Path.home()
    session_dir = home / "iboga-data" / "sessions" / trajectory_id
    cost_log_path = session_dir / "cost-log.jsonl"
    
    in_price_per_m, out_price_per_m = PRICING.get(model, (0.0, 0.0))
    cost = (in_tokens / 1_000_000) * in_price_per_m + (out_tokens / 1_000_000) * out_price_per_m
    
    entry = {
        "model": model,
        "in_tokens": in_tokens,
        "out_tokens": out_tokens,
        "cost": cost,
        "timestamp": time.time()
    }
    
    with open(cost_log_path, "a") as f:
        f.write(json.dumps(entry) + "\n")
        
    # Sum all cost logs
    total_cost = 0.0
    sessions_dir = home / "iboga-data" / "sessions"
    if sessions_dir.exists():
        for log_file in sessions_dir.glob("*/cost-log.jsonl"):
            with open(log_file) as f:
                for line in f:
                    try:
                        record = json.loads(line)
                        total_cost += record.get("cost", 0.0)
                    except:
                        pass
                        
    cost_total_path = home / "iboga-data" / "cost-total.json"
    with open(cost_total_path, "w") as f:
        json.dump({"total_cost": total_cost}, f)

# --- Hook Script Generation ---

def write_hook_script(session_dir: Path, trajectory_id: str, model: str, problem_id: str, arm: str, is_dry_run: bool):
    hook_path = session_dir / "hook.sh"
    
    # Generate python script for hook logic
    repo_root = Path(__file__).resolve().parent.parent
    
    hook_content = f"""#!/usr/bin/env python3
import json
import logging
import os
import sys
import time
from pathlib import Path
import httpx
import jsonschema

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

TRAJECTORY_ID = {repr(trajectory_id)}
MODEL = {repr(model)}
PROBLEM_ID = {repr(problem_id)}
ARM = {repr(arm)}
IS_DRY_RUN = {repr(is_dry_run)}
REPO_ROOT = Path({repr(str(repo_root))})

def main():
    try:
        payload = json.load(sys.stdin)
    except Exception as e:
        logging.error(f"Failed to read J6 JSON payload from stdin: {{e}}")
        sys.exit(1)
        
    current_checkpoint_name = payload.get("current_checkpoint_name", "unknown")
    previous_diff_path = payload.get("previous_diff_path")
    
    session_dir = Path.home() / "iboga-data" / "sessions" / TRAJECTORY_ID
    
    if IS_DRY_RUN:
        if ARM == "0":
            stub_json = {{}}
            prefix = ""
        else:
            stub_json = {{"retrospective": "stub retrospective"}}
            if ARM in ["A", "B"]:
                stub_json = {{"resentment_inventory": "stub", "past_tense_panorama": "stub"}}
            prefix = "Prior session retrospective: stub retrospective. Continue your work."
            
        session_file = session_dir / f"session-{{current_checkpoint_name}}.json"
        with open(session_file, "w") as f:
            json.dump(stub_json, f)
            
        print(prefix)
        sys.exit(0)

    if ARM == "0":
        # No LLM call
        session_file = session_dir / f"session-{{current_checkpoint_name}}.json"
        with open(session_file, "w") as f:
            json.dump({{}}, f)
        print("") # Empty prefix
        sys.exit(0)
        
    # Check budget
    sys.path.append(str(REPO_ROOT))
    import scripts.iboga_runner as runner
    runner.check_budget_and_abort()

    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        logging.error("OPENROUTER_API_KEY not set")
        sys.exit(1)

    # Read diff
    diff_content = ""
    if previous_diff_path and Path(previous_diff_path).exists():
        with open(previous_diff_path) as f:
            diff_content = f.read()

    # Load schema
    schema_path = REPO_ROOT / runner.ARM_SCHEMAS[ARM]
    with open(schema_path) as f:
        schema = json.load(f)


    # In a real implementation we'd read the template from arm-templates.md and use OpenRouter's tools
    # For now we'll do a simple OpenRouter chat call
    
    system_prompt = f"You are completing an introspection for arm {{ARM}}.\\nDiff:\\n{{diff_content}}"
    
    tools = []
    if ARM in ["A", "B"]:
        tools = [{{"type": "function", "function": t}} for t in schema.get("tools", [])]
    else:
        # Arm C
        tools = [{{
            "type": "function",
            "function": {{"name": "record_unstructured_retrospective", "description": "...", "parameters": schema.get("input_schema", {{}})}}
        }}]

    headers = {{"Authorization": f"Bearer {{api_key}}", "HTTP-Referer": "https://github.com/basedlsg/iboga"}}
    data = {{
        "model": MODEL,
        "messages": [{{"role": "user", "content": system_prompt}}],
        "tools": tools,
        "tool_choice": "auto"
    }}

    retries = 2
    for attempt in range(retries + 1):
        try:
            resp = httpx.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data, timeout=60.0)
            resp.raise_for_status()
            result = resp.json()
            
            usage = result.get("usage", {{}})
            runner.update_cost(TRAJECTORY_ID, usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0), MODEL)
            
            choice = result.get("choices", [{{}}])[0]
            message = choice.get("message", {{}})
            
            tool_calls = message.get("tool_calls", [])
            output_data = {{}}
            if tool_calls:
                try:
                    tool_call = tool_calls[0]
                    func_name = tool_call["function"]["name"]
                    output_data = json.loads(tool_call["function"]["arguments"])
                    
                    # Find matching schema for this tool
                    tool_schema = None
                    if ARM in ["A", "B"]:
                        for t in schema.get("tools", []):
                            if t.get("name") == func_name:
                                tool_schema = t.get("input_schema")
                                break
                    else:
                        tool_schema = schema.get("input_schema")
                        
                    if tool_schema:
                        jsonschema.validate(instance=output_data, schema=tool_schema)
                        
                    break
                except (json.JSONDecodeError, jsonschema.exceptions.ValidationError) as e:
                    logging.warning(f"Validation failure: {{e}}")
                    continue # Retry on validation error
            elif message.get("content"):
                 output_data = {{"retrospective": message.get("content")}}
                 break
        except Exception as e:
            logging.warning(f"LLM call attempt {{attempt}} failed: {{e}}")
            time.sleep(2)
    else:
        # Final failure
        logging.error("Structured output failure")
        session_file = session_dir / f"session-{{current_checkpoint_name}}.json"
        with open(session_file, "w") as f:
            json.dump({{"error": "structured_output_failure"}}, f)
        print("")
        sys.exit(0)
        
    session_file = session_dir / f"session-{{current_checkpoint_name}}.json"
    with open(session_file, "w") as f:
        json.dump(output_data, f)
        
    print("Prior session retrospective: " + json.dumps(output_data) + ". Continue your work.")

if __name__ == "__main__":
    main()
"""
    with open(hook_path, "w") as f:
        f.write(hook_content)
    hook_path.chmod(0o755)
    return hook_path


# --- Main Runner ---

def main():
    parser = argparse.ArgumentParser(description="Iboga runner")
    parser.add_argument("--trajectory-id", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--problem", required=True)
    parser.add_argument("--arm", required=True, choices=["A", "B", "C", "0"])
    parser.add_argument("--dry-run", action="store_true")
    
    args = parser.parse_args()
    
    # 1. Validate ARM (handled by choices)
    
    # 2. Check OPENROUTER_API_KEY
    if not args.dry_run and not os.environ.get("OPENROUTER_API_KEY"):
        logging.error("OPENROUTER_API_KEY not set")
        sys.exit(1)
        
    # 3. Create host session directory
    session_dir = ensure_session_dir(args.trajectory_id)
    
    # 4. Check budget limit
    check_budget_and_abort()
    
    # 5. Check Mount Guard
    scb_path = get_slopcodebench_dir()
    check_mount_guard(scb_path)
    
    # 6. Write hook script
    hook_path = write_hook_script(session_dir, args.trajectory_id, args.model, args.problem, args.arm, args.dry_run)
    
    # 7. Invoke SlopCodeBench fork
    agent = os.environ.get("SCB_AGENT", "opencode")
    run_config = os.environ.get("SCB_RUN_CONFIG", "configs/runs/lite_under20.yaml")
    
    # Map the OpenRouter model slug (as used in arm-assignment.json) to the
    # SlopCodeBench --model argument <provider>/<internal_name>, where
    # internal_name matches a config in slop-code-bench/configs/models/.
    scb_model = SCB_MODEL_MAP.get(args.model)
    if scb_model is None:
        # Unknown model: best-effort — strip the vendor prefix and route via openrouter
        internal = args.model.split("/")[-1]
        scb_model = f"openrouter/{internal}"
        logging.warning(f"Model '{args.model}' not in SCB_MODEL_MAP; using best-effort '{scb_model}'")
    
    cmd = [
        "uv", "run", "slop-code", "run",
        "--config", run_config,
        "--agent", agent,
        "--model", scb_model,
        "--problem", args.problem,
        "--between-checkpoint-hook", str(hook_path),
        "--no-live-progress"
    ]
    
    if args.dry_run:
        logging.info("DRY RUN: would execute command:")
        print(shlex.join(cmd))
        
        # Test dry run of hook
        logging.info("DRY RUN: testing hook execution")
        # Provide dummy payload
        payload = json.dumps({
            "trajectory_id": args.trajectory_id,
            "model_id": args.model,
            "problem_id": args.problem,
            "previous_checkpoint_name": "ch1",
            "current_checkpoint_name": "ch2"
        })
        try:
            res = subprocess.run([str(hook_path)], input=payload, text=True, capture_output=True, check=True)
            logging.info(f"Hook output prefix: {res.stdout.strip()}")
        except subprocess.CalledProcessError as e:
            logging.error(f"Hook execution failed: {e.stderr}")
            sys.exit(1)
    else:
        logging.info(f"Executing: {shlex.join(cmd)}")
        subprocess.run(cmd, cwd=scb_path, check=True)

        # Extract per-checkpoint metrics from the SlopCodeBench run output.
        metrics_file = session_dir / "metrics.json"
        checkpoints = extract_checkpoint_metrics(scb_path, args.problem)
        with open(metrics_file, "w") as f:
            json.dump(
                {
                    "trajectory_id": args.trajectory_id,
                    "model": args.model,
                    "problem": args.problem,
                    "arm": args.arm,
                    "checkpoints": checkpoints,
                },
                f,
                indent=2,
            )
        logging.info(f"Wrote per-checkpoint metrics for {len(checkpoints)} checkpoint(s) to {metrics_file}")


def find_latest_run_dir(scb_path: Path, problem: str) -> Path | None:
    """Find the most recent SlopCodeBench output run directory containing <problem>/."""
    outputs = scb_path / "outputs"
    if not outputs.exists():
        return None
    candidates = [d for d in outputs.rglob(problem) if d.is_dir() and (d / "run_info.yaml").exists()]
    if not candidates:
        return None
    return max(candidates, key=lambda d: d.stat().st_mtime)


def extract_checkpoint_metrics(scb_path: Path, problem: str) -> list[dict]:
    """Run scb-check on each completed checkpoint snapshot and collect erosion / verbosity / solve_rate.

    The primary DV (erosion_slope, verbosity_slope) is computed downstream by the
    analysis script as the OLS slope of these per-checkpoint values vs checkpoint index.
    """
    run_dir = find_latest_run_dir(scb_path, problem)
    if run_dir is None:
        logging.error(f"No SlopCodeBench run directory found for problem '{problem}'")
        return []

    checkpoints: list[dict] = []
    ckpt_dirs = sorted(
        (d for d in run_dir.iterdir() if d.is_dir() and d.name.startswith("checkpoint_")),
        key=lambda d: int(d.name.split("_")[-1]),
    )
    for ckpt_dir in ckpt_dirs:
        idx = int(ckpt_dir.name.split("_")[-1])
        record: dict = {"checkpoint": ckpt_dir.name, "idx": idx,
                         "erosion": None, "verbosity": None, "solve_rate": None}

        # erosion + verbosity: run scb-check on the checkpoint snapshot (the documented production path)
        snapshot = ckpt_dir / "snapshot"
        if snapshot.exists():
            try:
                proc = subprocess.run(
                    ["uvx", "scb-check", "check", "--report", "--include-all", str(snapshot.resolve())],
                    capture_output=True, text=True, cwd=scb_path, timeout=300,
                )
                if proc.returncode == 0 and proc.stdout.strip():
                    report = json.loads(proc.stdout.strip().splitlines()[-1])
                    record["erosion"] = report.get("erosion")
                    record["verbosity"] = report.get("verbosity")
                    record["scb_check_raw"] = report
                else:
                    logging.warning(f"scb-check failed for {ckpt_dir.name}: {proc.stderr[:200]}")
            except (subprocess.SubprocessError, json.JSONDecodeError) as e:
                logging.warning(f"scb-check error for {ckpt_dir.name}: {e}")

        # solve_rate: passed / total tests from evaluation.json
        eval_file = ckpt_dir / "evaluation.json"
        if eval_file.exists():
            try:
                ev = json.loads(eval_file.read_text())
                passed = total = 0
                for suite in ev.get("tests", {}).values():
                    passed += len(suite.get("passed", []))
                    total += len(suite.get("passed", [])) + len(suite.get("failed", []))
                record["solve_rate"] = (passed / total) if total else 0.0
                record["tests_passed"] = passed
                record["tests_total"] = total
            except (json.JSONDecodeError, OSError) as e:
                logging.warning(f"evaluation.json parse error for {ckpt_dir.name}: {e}")

        checkpoints.append(record)
    return checkpoints


if __name__ == "__main__":
    main()
