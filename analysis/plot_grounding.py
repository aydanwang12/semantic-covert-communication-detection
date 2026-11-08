#!/usr/bin/env python3
"""Compare two measured questions; no new observations or simulated data."""
from pathlib import Path
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
target = json.loads((ROOT / "analysis/target_conditioned_results.json").read_text())
raw = [json.loads(line) for line in (ROOT / "data/results.jsonl").read_text().splitlines()]
conditions = ["semantic", "semantic_placebo"]
flips = []
for condition in conditions:
    rows = [row for row in raw if row["condition"] == condition]
    assert len(rows) == 32
    flips.append(sum(row["actions"]["partner"]["original"] != row["actions"]["partner"]["semantic_counterfactual"] for row in rows) / len(rows))
effects = [target["splits"]["main"][condition]["partner"]["paired_target_response"] for condition in conditions]
fig, axes = plt.subplots(1, 2, figsize=(8, 3.3), sharey=True)
for ax, values, title, ylabel in zip(axes, [flips, effects],
    ["Response to frame change", "Response aligned with target"],
    ["Partner action-flip rate", "Mean A(H=1) - A(H=0)"]):
    ax.bar([0, 1], values, color=["#146c80", "#d88332"], width=.58)
    ax.set_xticks([0, 1], ["Semantic", "Placebo"])
    ax.set_ylim(-.06, 1.2)
    ax.set_yticks([0, .5, 1])
    ax.set_title(title, fontsize=10, fontweight="bold")
    ax.set_ylabel(ylabel, fontsize=9)
    ax.spines[["top", "right"]].set_visible(False)
    for index, value in enumerate(values):
        ax.text(index, value + .04, f"{value:.2f}", ha="center", fontsize=10)
axes[0].text(.5, -.23, "32 actual episodes per condition", transform=axes[0].transAxes, ha="center", fontsize=8)
axes[1].text(.5, -.23, "16 matched target pairs per condition", transform=axes[1].transAxes, ha="center", fontsize=8)
fig.suptitle("Convention use and designated-target transmission differ", fontsize=11, fontweight="bold")
fig.subplots_adjust(top=.78, bottom=.25, wspace=.38, left=.08, right=.98)
folder = ROOT / "analysis/figures"
folder.mkdir(exist_ok=True)
for suffix in ("png", "pdf", "svg"):
    fig.savefig(folder / f"main_target_grounding.{suffix}", dpi=190, bbox_inches="tight")
plt.close(fig)
