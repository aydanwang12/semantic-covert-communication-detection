#!/usr/bin/env python3
"""Run real, isolated LLM trials and append every attempted response to disk.

Example:
  python experiments/run_experiment.py --split pilot --output data/pilot.jsonl

The run manifest is written before any model call. Resume only skips complete
saved episode IDs; completed attempts remain recorded in the call ledger.
"""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import random
import subprocess
import sys
import threading
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.agents import CodexBackend, OpenAIBackend, parse_action, parse_sender_message
from src.channels import VARIANTS
from src.environment import generate_episodes, sender_task, adopt_sender_message


def utcnow():
    return datetime.now(timezone.utc).isoformat()


def append_jsonl(path, record, lock):
    """Flush each append so completed records survive interruption."""
    with lock:
        with Path(path).open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(record, sort_keys=True, ensure_ascii=False) + "\n")
            stream.flush()


def run_episode(episode, backend, ledger, lock, repeat_original=True, sender_mode="llm_constrained_selector"):
    episode["started_at"] = utcnow()
    episode["backend"] = backend.name
    episode["model"] = backend.model
    episode["sender_type"] = sender_mode
    if sender_mode == "llm_constrained_selector":
        prompt, candidates, features = sender_task(episode)
        result = backend.complete("Select exactly one approved message and output only the required JSON.", prompt)
        record = {"episode_id": episode["episode_id"], "block_id": episode["block_id"],
                  "split": episode["split"], "condition": episode["condition"], "role": "sender",
                  "variant": "original", "system_prompt": "Select exactly one approved message and output only the required JSON.",
                  "prompt": prompt, "recorded_at": utcnow(), **result.to_dict()}
        selected = None if result.error else parse_sender_message(result.response_text, candidates)
        record["valid"] = selected is not None
        append_jsonl(ledger, record, lock)
        episode["sender_prompt"], episode["sender_candidates"] = prompt, candidates
        episode["sender_response"] = record
        episode["sender_valid"] = selected is not None
        if selected is None:
            variants = list(VARIANTS) + (["unchanged_repeat"] if repeat_original else [])
            episode["actions"] = {role: {variant: None for variant in variants} for role in ("partner", "outsider")}
            episode["responses"] = {role: {} for role in ("partner", "outsider")}
            episode["episode_status"] = "invalid_sender_no_receiver_calls"
            episode["completed_at"] = utcnow()
            return episode
        adopt_sender_message(episode, selected, candidates, features, repeat_original)
    elif sender_mode == "deterministic_controlled_encoder":
        prompt, candidates, features = sender_task(episode)
        selected = episode["messages"]["original"]
        adopt_sender_message(episode, selected, candidates, features, repeat_original)
        episode["sender_valid"] = True
    else:
        raise ValueError(sender_mode)

    episode["actions"] = {role: {} for role in ("partner", "outsider")}
    episode["responses"] = {role: {} for role in ("partner", "outsider")}
    # The order is randomized deterministically per episode; every call remains
    # isolated, and the roles never share histories or tool environments.
    calls = [(role, variant) for role in ("partner", "outsider") for variant in episode["messages"]]
    callseed = int(hashlib.sha256(episode["episode_id"].encode()).hexdigest()[:16], 16)
    random.Random(callseed).shuffle(calls)
    episode["receiver_call_order"] = [list(c) for c in calls]
    for role, variant in calls:
        prompt = episode["prompts"][role][variant]
        result = backend.complete(episode["system_prompt"], prompt)
        action = None if result.error else parse_action(result.response_text)
        record = {"episode_id": episode["episode_id"], "block_id": episode["block_id"],
                  "split": episode["split"], "condition": episode["condition"],
                  "role": role, "variant": variant, "system_prompt": episode["system_prompt"],
                  "prompt": prompt, "action": action, "valid": action is not None,
                  "recorded_at": utcnow(), **result.to_dict()}
        append_jsonl(ledger, record, lock)
        episode["actions"][role][variant] = action
        episode["responses"][role][variant] = record
    episode["episode_status"] = "complete" if all(
        a is not None for role in episode["actions"].values() for a in role.values()) else "complete_with_invalid_responses"
    episode["completed_at"] = utcnow()
    return episode


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "config/experiment.json")
    parser.add_argument("--split", choices=("pilot", "main", "validation"), default="main")
    parser.add_argument("--output", type=Path, default=ROOT / "data/results.jsonl")
    parser.add_argument("--replicates", type=int)
    parser.add_argument("--workers", type=int)
    parser.add_argument("--limit-blocks", type=int, help="Use a preselected balanced subset: 8 or 16 blocks per replicate")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--plan-only", action="store_true", help="Save planned episodes; make zero model calls")
    args = parser.parse_args()
    config = json.loads(args.config.read_text())
    replicates = args.replicates or config.get(f"{args.split}_replicates", 1)
    workers = args.workers or config.get("max_workers", 8)
    seed = config["seed"] + {"pilot": 0, "main": 1, "validation": 2}[args.split]
    episodes = generate_episodes(args.split, replicates, seed, config["conditions"])
    if args.limit_blocks:
        if args.limit_blocks not in (8, 16):
            parser.error("limit-blocks must be 8 or 16")
        # Optional balanced half-fraction fixed without observing responses.
        if args.limit_blocks == 8:
            episodes = [e for e in episodes if e["nuisance_initial"] == (e["hidden_bit"] ^ e["key_orientation"] ^ e["nuisance_frame"])]
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    ledger = output.with_suffix(".calls.jsonl")
    manifest_path = output.with_suffix(".manifest.json")
    if (output.exists() or ledger.exists() or manifest_path.exists()) and not args.resume:
        parser.error("output/ledger/manifest already exists; choose a fresh path or explicitly --resume")
    completed = set()
    if args.resume and output.exists():
        completed = {json.loads(line)["episode_id"] for line in output.read_text().splitlines() if line.strip()}
    planned_ids = [e["episode_id"] for e in episodes]
    manifest = {"created_at": utcnow(), "split": args.split, "config": config,
                "effective_replicates": replicates, "effective_workers": workers,
                "effective_seed": seed, "limit_blocks": args.limit_blocks,
                "planned_episode_count": len(episodes), "planned_episode_ids": planned_ids,
                "output": output.name, "ledger": ledger.name,
                "plan_only": args.plan_only, "argv": [x.replace(str(Path.home()), "<HOME>") for x in sys.argv],
                "redaction_policy": config.get("redaction_policy"),
                "cli_version": subprocess.run(["codex", "--version"], capture_output=True, text=True).stdout.strip() if config.get("backend") == "codex_cli" else None}
    instruction = config.get("model_instructions_file")
    if instruction:
        instruction_bytes = (ROOT / instruction).read_bytes()
        manifest["model_instructions_text"] = instruction_bytes.decode()
        manifest["model_instructions_sha256"] = hashlib.sha256(instruction_bytes).hexdigest()
    if not manifest_path.exists():
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    else:
        old = json.loads(manifest_path.read_text())
        if old["planned_episode_ids"] != planned_ids or old["config"] != config:
            parser.error("resume configuration differs from original manifest")
    if args.plan_only:
        plan = output.with_suffix(".planned.json")
        plan.write_text(json.dumps(episodes, indent=2) + "\n")
        print(json.dumps({"planned_episodes": len(episodes), "model_calls": 0, "plan": str(plan)}))
        return
    backend_name = config.get("backend", "codex_cli")
    if backend_name == "codex_cli":
        instruction_file = config.get("model_instructions_file")
        if instruction_file:
            instruction_file = ROOT / instruction_file
        backend = CodexBackend(config["model"], config.get("reasoning_effort", "low"),
                               config.get("timeout_seconds", 90),
                               model_instructions_file=instruction_file)
    elif backend_name == "openai_chat_completions":
        backend = OpenAIBackend(config["model"], config.get("timeout_seconds", 90))
    else:
        parser.error(f"unknown backend {backend_name}")
    lock = threading.Lock()
    remaining = [e for e in episodes if e["episode_id"] not in completed]
    started = time.monotonic()
    print(json.dumps({"started_at": utcnow(), "planned": len(episodes), "remaining": len(remaining),
                      "backend": backend.name, "model": backend.model}), flush=True)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(run_episode, e, backend, ledger, lock,
                    config.get("repeat_original", True), config.get("sender_mode", "llm_constrained_selector")): e
                   for e in remaining}
        for future in as_completed(futures):
            source = futures[future]
            try:
                row = future.result()
            except Exception as exc:
                row = {**source, "episode_status": "runner_exception", "error": f"{type(exc).__name__}: {exc}",
                       "actions": {role: {variant: None for variant in VARIANTS} for role in ("partner", "outsider")}}
            append_jsonl(output, row, lock)
            completed.add(row["episode_id"])
            print(json.dumps({"complete": len(completed), "planned": len(episodes),
                              "episode_id": row["episode_id"], "status": row["episode_status"],
                              "elapsed_seconds": round(time.monotonic()-started, 2)}), flush=True)
    print(json.dumps({"finished_at": utcnow(), "episodes": len(completed), "output": str(output)}), flush=True)


if __name__ == "__main__":
    main()
