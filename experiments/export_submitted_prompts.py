#!/usr/bin/env python3
"""Derive exact experiment-owned Codex stdin and instruction text from saved logs.

This exports reconstructible client inputs, NOT the full provider request or all
CLI/system scaffolding. Originals are read-only. No model calls are made.
"""
import argparse
import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def combined_expression():
    source = ROOT / "src/agents.py"
    tree = ast.parse(source.read_text())
    backend = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "CodexBackend")
    complete = next(n for n in backend.body if isinstance(n, ast.FunctionDef) and n.name == "complete")
    assignments = [n for n in ast.walk(complete) if isinstance(n, ast.Assign)
                   and any(isinstance(t, ast.Name) and t.id == "combined_prompt" for t in n.targets)]
    if len(assignments) != 1:
        raise ValueError("Cannot unambiguously locate the submitted-prompt expression")
    return assignments[0].value, hashlib.sha256(source.read_bytes()).hexdigest()


def reconstruct(expression, system, prompt):
    """Interpret only string concatenation and the two known local inputs."""
    if isinstance(expression, ast.Constant) and isinstance(expression.value, str):
        return expression.value
    if isinstance(expression, ast.Name) and expression.id in ("system", "prompt"):
        return {"system": system, "prompt": prompt}[expression.id]
    if isinstance(expression, ast.BinOp) and isinstance(expression.op, ast.Add):
        return reconstruct(expression.left, system, prompt) + reconstruct(expression.right, system, prompt)
    raise ValueError("Unsupported prompt-construction expression; no reconstruction guessed")


def manifest_for(path):
    name = path.name[:-len(".calls.jsonl")] if path.name.endswith(".calls.jsonl") else path.stem
    return path.with_name(name + ".manifest.json")


def export(paths, output):
    expression, source_hash = combined_expression()
    count = 0
    with output.open("x", encoding="utf-8") as destination:
        for path in paths:
            manifest_path = manifest_for(path)
            manifest = json.loads(manifest_path.read_text())
            instruction = manifest.get("model_instructions_text")
            instruction_hash = hashlib.sha256(instruction.encode()).hexdigest() if instruction is not None else None
            if instruction_hash != manifest.get("model_instructions_sha256"):
                raise ValueError("Saved model-instruction text/hash mismatch")
            content = path.read_bytes()
            input_hash = hashlib.sha256(content).hexdigest()
            for line_number, line in enumerate(content.decode().splitlines(), 1):
                if not line.strip():
                    continue
                record = json.loads(line)
                if record["backend"] != "codex_cli":
                    raise ValueError("This reconstruction supports only the collected Codex CLI backend")
                stdin = reconstruct(expression, record["system_prompt"], record["prompt"])
                derived = {
                    "artifact_type": "derived_experiment_owned_cli_inputs",
                    "source_file": path.name, "source_line": line_number,
                    "source_file_sha256": input_hash, "source_agents_py_sha256": source_hash,
                    "episode_id": record.get("episode_id"), "validation_id": record.get("validation_id"),
                    "role": record.get("role", "frame_validator"), "variant": record.get("variant"),
                    "model": record["model"], "backend": record["backend"],
                    "submitted_cli_stdin": stdin,
                    "submitted_cli_stdin_sha256": hashlib.sha256(stdin.encode()).hexdigest(),
                    "supplied_model_instructions": instruction,
                    "supplied_model_instructions_sha256": instruction_hash,
                    "full_provider_request_captured": False,
                    "boundary": "Reconstructed local stdin plus supplied instruction file; provider/system/CLI-added scaffolding is not captured."
                }
                destination.write(json.dumps(derived, ensure_ascii=False, sort_keys=True) + "\n")
                count += 1
    return count


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", nargs="+", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.resolve() in {p.resolve() for p in args.inputs}:
        parser.error("Output must not overwrite an input")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    count = export(args.inputs, args.output)
    print(json.dumps({"exported_calls": count, "output": str(args.output), "full_provider_request_captured": False}))


if __name__ == "__main__":
    main()
