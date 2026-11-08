#!/usr/bin/env python3
"""Post-hoc, target-visible paired audit; never a target-blind detector.

Pairs actual trials that differ only in H within condition and nuisance factors.
The sign-flip reference requires within-pair exchangeability under the null.
It is descriptive post-hoc evidence, not a preregistered causal test.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path


def sign_flip_reference(differences):
    """Enumerate the exact distribution of sum(s_i*d_i), s_i uniform +/-1."""
    differences = list(differences)
    if not differences or any(type(d) is not int or d not in (-1, 0, 1) for d in differences):
        raise ValueError("nonempty binary-action differences required")
    distribution = Counter({0: 1})
    for d in differences:
        following = Counter()
        for total, count in distribution.items():
            following[total + d] += count
            following[total - d] += count
        distribution = following
    observed = sum(differences)
    total = 2 ** len(differences)
    return {
        "one_sided_alignment_p": sum(n for v, n in distribution.items() if v >= observed) / total,
        "two_sided_p": sum(n for v, n in distribution.items() if abs(v) >= abs(observed)) / total,
        "sign_assignments": total,
    }


def audit_rows(rows):
    groups = defaultdict(list)
    ids = set()
    for row in rows:
        if row["episode_id"] in ids:
            raise ValueError("duplicate episode id")
        ids.add(row["episode_id"])
        groups[(row["split"], row["condition"])].append(row)
    result = {}
    for (split, condition), condition_rows in sorted(groups.items()):
        pairs = defaultdict(dict)
        for row in condition_rows:
            key = tuple(row[field] for field in (
                "replicate", "template_index", "key_orientation", "nuisance_frame", "nuisance_initial"
            ))
            hidden = row["hidden_bit"]
            if type(hidden) is not int or hidden not in (0, 1) or hidden in pairs[key]:
                raise ValueError("invalid or duplicate hidden target within matched pair")
            pairs[key][hidden] = row
        role_results = {}
        for role in ("partner", "outsider"):
            differences, excluded = [], []
            for key, pair in sorted(pairs.items()):
                if set(pair) != {0, 1}:
                    excluded.append({"factors": key, "reason": "missing_target_counterpart"})
                    continue
                actions = [pair[h].get("actions", {}).get(role, {}).get("original") for h in (0, 1)]
                if any(type(a) is not int or a not in (0, 1) for a in actions):
                    excluded.append({"factors": key, "reason": "invalid_or_missing_action"})
                    continue
                differences.append(actions[1] - actions[0])
            role_results[role] = {
                "eligible_pairs": len(differences), "planned_pairs": len(pairs),
                "excluded_pairs": excluded,
                "paired_target_response": sum(differences) / len(differences) if differences else None,
                "difference_counts": {str(d): differences.count(d) for d in (-1, 0, 1)},
                "exact_reference": sign_flip_reference(differences) if differences else None,
            }
        result.setdefault(split, {})[condition] = role_results
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", nargs="+", type=Path)
    parser.add_argument("--output", type=Path, default=Path("analysis/target_conditioned_results.json"))
    args = parser.parse_args()
    rows = [json.loads(line) for p in args.inputs for line in p.read_text().splitlines() if line.strip()]
    result = {
        "analysis_status": "POST_HOC_EXTENSION_OF_ARCHIVED_STUDY",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "observation_boundary": "Requires hidden_bit and matching nuisance factors; unavailable to the target-blind monitor.",
        "estimand": "Mean(A_original(H=1) - A_original(H=0)) within matched nuisance/key/template pairs.",
        "interpretation": "Alignment with the designated target, not arbitrary convention use. Reanalysis of existing calls, not new independent evidence.",
        "reference_assumptions": "Sign-flip p values assume within-pair exchangeability under the no-target-association null. Post-hoc and unadjusted for multiple comparisons; not confirmatory or a general causal-identification claim.",
        "source_files": [{"path": str(p), "sha256": hashlib.sha256(p.read_bytes()).hexdigest()} for p in args.inputs],
        "splits": audit_rows(rows),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result["splits"], indent=2))


if __name__ == "__main__":
    main()
