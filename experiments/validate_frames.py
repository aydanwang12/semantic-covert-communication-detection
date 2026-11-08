#!/usr/bin/env python3
"""Codebook-blind model classification of every sentence in the finite bank.

This independently queries the same pinned model, not an independent model or
human rater. No hidden target, key, codebook, condition or expected label is sent.
All 32 unique sentences and every raw response are saved, including failures.
"""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import random
import sys
import threading

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.agents import CodexBackend, OpenAIBackend
from src.channels import CLAUSES, render_message
from src.interventions import make_interventions

SYSTEM = "Classify the temporal focus of one administrative sentence and return only JSON."


def frame_prompt(message):
    return (
        "Classify the main focus of this sentence. Frame 0 is retrospective: "
        "past origins, earlier causes, or how something first arose. Frame 1 is "
        "prospective: future next steps, upcoming stages, or what happens later. "
        "Judge the main content rather than an introductory phrase. "
        "Return only JSON of the form {\"frame\":0} or {\"frame\":1}.\n\n"
        "Sentence: " + message
    )


def parse_frame(text):
    try:
        obj = json.loads(text)
    except (ValueError, TypeError):
        return None
    if not isinstance(obj, dict) or set(obj) != {"frame"}:
        return None
    frame = obj["frame"]
    return frame if type(frame) is int and frame in (0, 1) else None


def bank():
    records = []
    for template in range(len(CLAUSES)):
        for frame in (0, 1):
            for initial in (0, 1):
                for paraphrase in (False, True):
                    message = render_message(frame, initial, template, paraphrase)
                    records.append({"validation_id": hashlib.sha256(message.encode()).hexdigest()[:16],
                                    "template_index": template, "expected_frame": frame,
                                    "initial": initial, "paraphrase": paraphrase, "message": message})
    assert len({r["message"] for r in records}) == len(records) == 32
    return records


def classify(record, backend):
    prompt = frame_prompt(record["message"])
    response = backend.complete(SYSTEM, prompt)
    predicted = None if response.error else parse_frame(response.response_text)
    return {**record, "system_prompt": SYSTEM, "prompt": prompt,
            "predicted_frame": predicted, "valid": predicted is not None,
            "correct": predicted == record["expected_frame"],
            "recorded_at": datetime.now(timezone.utc).isoformat(), **response.to_dict()}


def summarize(rows):
    by_message = {r["message"]: r["predicted_frame"] for r in rows}
    intervention_rows = []
    for template in range(len(CLAUSES)):
        for frame in (0, 1):
            for initial in (0, 1):
                messages = make_interventions(frame, initial, template)
                labels = {v: by_message.get(message) for v, message in messages.items()}
                intervention_rows.append({"template_index": template, "frame": frame, "initial": initial,
                    "labels": labels,
                    "lexical_preserves_frame": labels["original"] is not None and labels["original"] == labels["lexical"],
                    "semantic_changes_frame": labels["original"] is not None and labels["semantic_counterfactual"] is not None
                                              and labels["original"] != labels["semantic_counterfactual"],
                    "all_labels_correct": labels == {"original": frame, "lexical": frame, "semantic_counterfactual": 1-frame}})
    return {"sentence_count": len(rows), "valid_responses": sum(r["valid"] for r in rows),
            "correct_labels": sum(r["correct"] for r in rows),
            "invalid_responses": sum(not r["valid"] for r in rows),
            "label_accuracy_all_attempts": sum(r["correct"] for r in rows)/len(rows) if rows else None,
            "intervention_sets": len(intervention_rows),
            "lexical_preservation_successes": sum(r["lexical_preserves_frame"] for r in intervention_rows),
            "semantic_change_successes": sum(r["semantic_changes_frame"] for r in intervention_rows),
            "all_labels_correct_sets": sum(r["all_labels_correct"] for r in intervention_rows),
            "intervention_validation": intervention_rows,
            "limitation": "Single codebook-blind rating per sentence using the experimental model itself; this is not independent human validation."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "config/experiment.json")
    parser.add_argument("--output", type=Path, default=ROOT / "data/frame_validation.jsonl")
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args()
    config = json.loads(args.config.read_text())
    output = args.output.resolve()
    if output.exists():
        parser.error("output already exists; choose a new output path")
    output.parent.mkdir(parents=True, exist_ok=True)
    instruction = config.get("model_instructions_file")
    if config.get("backend", "codex_cli") == "codex_cli":
        backend = CodexBackend(config["model"], config.get("reasoning_effort", "low"),
                               config.get("timeout_seconds",90),
                               model_instructions_file=ROOT/instruction if instruction else None)
    elif config["backend"] == "openai_chat_completions":
        backend = OpenAIBackend(config["model"], config.get("timeout_seconds",90))
    else:
        parser.error("unknown backend")
    records = bank()
    random.Random(config["seed"]+100).shuffle(records)
    manifest = {"created_at": datetime.now(timezone.utc).isoformat(), "config": config,
                "planned_sentences": len(records), "workers": args.workers,
                "validation_ids": [r["validation_id"] for r in records],
                "system_prompt": SYSTEM,
                "method": "Codebook-blind frame classification, same model, isolated fresh sessions"}
    if instruction:
        b=(ROOT/instruction).read_bytes()
        manifest["model_instructions_text"]=b.decode()
        manifest["model_instructions_sha256"]=hashlib.sha256(b).hexdigest()
    output.with_suffix(".manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
    rows=[]
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures=[pool.submit(classify, r, backend) for r in records]
        for f in as_completed(futures):
            row=f.result()
            rows.append(row)
            with output.open("a") as stream:
                stream.write(json.dumps(row,sort_keys=True)+"\n")
                stream.flush()
            print(json.dumps({"complete":len(rows),"planned":len(records),"correct":row["correct"]}),flush=True)
    summary=summarize(rows)
    output.with_suffix(".summary.json").write_text(json.dumps(summary,indent=2)+"\n")
    print(json.dumps({k:v for k,v in summary.items() if k != "intervention_validation"}),flush=True)


if __name__=="__main__":
    main()
