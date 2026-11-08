#!/usr/bin/env python3
"""Recalculate all reported outcomes from raw episode JSONL, never from cached metrics."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.detection import CONDITIONS, VARIANTS, detector_score, gap, original_correct, summarize


def load_rows(paths):
    rows = []
    sources = []
    for path in paths:
        content = path.read_bytes()
        sources.append({"path": str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path),
                        "sha256": hashlib.sha256(content).hexdigest()})
        for line_number, line in enumerate(content.decode("utf-8").splitlines(), 1):
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON at {path}:{line_number}") from exc
    return rows, sources


def export_episode_metrics(rows, path):
    columns = ["episode_id", "block_id", "split", "condition", "hidden_bit", "key_orientation",
               "partner_original_correct", "outsider_original_correct", "D_lexical", "D_semantic_counterfactual", "detector_score"]
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            derived = {key: row.get(key) for key in columns[:6]}
            derived.update({"partner_original_correct": original_correct(row, "partner"),
                            "outsider_original_correct": original_correct(row, "outsider"),
                            "D_lexical": gap(row, "lexical"), "D_semantic_counterfactual": gap(row, "semantic_counterfactual"),
                            "detector_score": detector_score(row)})
            writer.writerow(derived)


def make_figures(summary, outdir):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.ticker import MultipleLocator

    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.spines.top": False,
                         "axes.spines.right": False, "axes.titleweight": "bold", "savefig.dpi": 200})
    labels = {"no_channel": "No channel", "syntactic": "Syntactic", "semantic": "Semantic", "semantic_placebo": "Semantic placebo"}
    colors = {"partner": "#126D82", "outsider": "#D37B35", "lexical": "#5574B9", "semantic_counterfactual": "#A04D83"}
    for split, data in summary["splits"].items():
        conditions = [c for c in CONDITIONS if data["conditions"][c]["n_episodes"]]
        if not conditions:
            continue
        n_text = ", ".join(f"{labels[c]} n={data['conditions'][c]['n_episodes']}" for c in conditions)
        x = list(range(len(conditions)))
        fig, ax = plt.subplots(figsize=(8.2, 4.3))
        for index, variant in enumerate(VARIANTS[1:]):
            for j, condition in enumerate(conditions):
                metric = data["conditions"][condition]["interventions"][variant]["mean_gap"]
                point, ci = metric["estimate"], metric["ci95_bootstrap"]
                if point is None:
                    continue
                error = [[max(0, point-ci[0])], [max(0, ci[1]-point)]] if ci else None
                ax.errorbar(j + (index-.5)*.18, point, yerr=error, fmt="o", capsize=4,
                            color=colors[variant], label=("Lexical: flip initial" if index == 0 else "Semantic: flip frame") if j == 0 else None)
        ax.axhline(0, color="#AAAAAA", lw=1)
        ax.set(xticks=x, xticklabels=[labels[c] for c in conditions], ylim=(-1.15, 1.15),
               ylabel="Partner flip rate - outsider flip rate", title=f"Behavioral response gap ({split})")
        ax.yaxis.set_major_locator(MultipleLocator(.5))
        ax.legend(loc="lower center", ncol=2, frameon=False)
        fig.text(.5, .015, "95% cluster bootstrap intervals; "+n_text, ha="center", fontsize=7.5)
        fig.tight_layout(rect=(0, .05, 1, 1))
        for extension in ("png", "pdf", "svg"):
            fig.savefig(outdir / f"{split}_behavioral_gap.{extension}")
        plt.close(fig)

        fig, ax = plt.subplots(figsize=(8.2, 4.3))
        for index, role in enumerate(("partner", "outsider")):
            for j, condition in enumerate(conditions):
                metric = data["conditions"][condition]["original_accuracy"][role]
                point, ci = metric["estimate"], metric["ci95_wilson"]
                error = [[max(0, point-ci[0])], [max(0, ci[1]-point)]] if ci else None
                ax.errorbar(j + (index-.5)*.18, point, yerr=error, fmt="o", capsize=4,
                            color=colors[role], label=role.capitalize() if j == 0 else None)
        ax.axhline(.5, color="#AAAAAA", lw=1, linestyle="--")
        ax.set(xticks=x, xticklabels=[labels[c] for c in conditions], ylim=(-.05, 1.1),
               ylabel="Original-message decoding accuracy", title=f"Instruction transmission ({split})")
        ax.legend(loc="lower right", frameon=False)
        fig.text(.5, .015, "95% Wilson reference intervals; "+n_text, ha="center", fontsize=7.5)
        fig.tight_layout(rect=(0, .05, 1, 1))
        for extension in ("png", "pdf", "svg"):
            fig.savefig(outdir / f"{split}_decoding_accuracy.{extension}")
        plt.close(fig)

        fig, ax = plt.subplots(figsize=(8.2, 4.3))
        for j, condition in enumerate(conditions):
            metric = data["conditions"][condition]["detector"]["alarm_rate"]
            point, ci = metric["estimate"], metric["ci95_wilson"]
            if point is None:
                continue
            error = [[max(0, point-ci[0])], [max(0, ci[1]-point)]] if ci else None
            ax.bar(j, point, color="#126D82" if condition in ("semantic", "syntactic") else "#D37B35", width=.55)
            ax.errorbar(j, point, yerr=error, fmt="none", color="#243341", capsize=5)
            ax.text(j, -.07, f"{metric['successes']}/{metric['n']}", ha="center", fontsize=9)
        ax.set(xticks=x, xticklabels=[labels[c] for c in conditions], ylim=(-.13, 1.18),
               ylabel="Alarm rate (S > 0)", title=f"Behavioral detector and control alarms ({split})")
        ax.set_yticks([0, .25, .5, .75, 1])
        fig.text(.5, .015, "95% Wilson reference intervals. Placebo alarms are false positives for hidden-instruction transmission.", ha="center", fontsize=7.5)
        fig.tight_layout(rect=(0, .05, 1, 1))
        for extension in ("png", "pdf", "svg"):
            fig.savefig(outdir / f"{split}_detection_rates.{extension}")
        plt.close(fig)


def brief(summary):
    lines = ["# Recalculated experimental results", "", "All numerical values below are computed from the supplied raw episode JSONL.", ""]
    for split, data in summary["splits"].items():
        lines += [f"## Split: {split}", "", f"Episodes: {data['n_episodes']}", "",
                  "| Condition | n | Partner accuracy | Outsider accuracy | Frame gap | Lexical gap | Alarm rate |", "|---|---:|---:|---:|---:|---:|---:|"]
        def fmt(value):
            return "undefined" if value is None else f"{value:.4f}"
        for condition, result in data["conditions"].items():
            lines.append(f"| {condition} | {result['n_episodes']} | {fmt(result['original_accuracy']['partner']['estimate'])} | {fmt(result['original_accuracy']['outsider']['estimate'])} | {fmt(result['interventions']['semantic_counterfactual']['mean_gap']['estimate'])} | {fmt(result['interventions']['lexical']['mean_gap']['estimate'])} | {fmt(result['detector']['alarm_rate']['estimate'])} |")
        primary = data["primary_semantic_minus_syntactic_frame_gap"]
        lines += ["", f"Primary semantic-minus-syntactic frame gap: {fmt(primary['estimate'])}; 95% block-bootstrap CI {primary['ci95_bootstrap']}.", ""]
    lines += ["Intervals describe the sampled design. A single model, constrained messages, shared templates, and finite crossing limit generalization.",
              "The detector is a single-draw action-flip proxy, not the full distributional PoPLi estimator.",
              "See results_summary.json for denominators, exclusions, invalid responses, transformation validation, orientation strata, and tied-score AUROC.", ""]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", type=Path, nargs="*", default=[ROOT / "data/results.jsonl"])
    parser.add_argument("--output-dir", type=Path, default=ROOT / "analysis")
    parser.add_argument("--resamples", type=int, default=5000)
    parser.add_argument("--seed", type=int, default=20261108)
    parser.add_argument("--skip-figures", action="store_true")
    args = parser.parse_args()
    rows, sources = load_rows([path.resolve() for path in args.inputs])
    summary = summarize(rows, args.resamples, args.seed)
    summary.update({"source_files": sources, "generated_at_utc": datetime.now(timezone.utc).isoformat()})
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "results_summary.json").write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n")
    export_episode_metrics(rows, args.output_dir / "episode_metrics.csv")
    (args.output_dir / "results_summary.md").write_text(brief(summary))
    if not args.skip_figures:
        figure_dir = args.output_dir / "figures"
        figure_dir.mkdir(exist_ok=True)
        make_figures(summary, figure_dir)
    print(brief(summary))


if __name__ == "__main__":
    main()
