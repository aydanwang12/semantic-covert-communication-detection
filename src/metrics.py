"""Small, dependency-free statistical helpers; no model calls or data mutation."""

from __future__ import annotations

import math
import random
from collections import defaultdict
from statistics import mean


def is_binary(value):
    """Booleans, strings, missing values, and out-of-range integers are invalid."""
    return type(value) is int and value in (0, 1)


def flip_gap(partner_original, partner_intervened, outsider_original, outsider_intervened):
    values = (partner_original, partner_intervened, outsider_original, outsider_intervened)
    if not all(is_binary(x) for x in values):
        return None
    return int(partner_intervened != partner_original) - int(outsider_intervened != outsider_original)


def wilson_interval(successes, total, z=1.959963984540054):
    """Descriptive binomial Wilson interval. None for an empty denominator."""
    if total < 0 or successes < 0 or successes > total:
        raise ValueError("Require 0 <= successes <= total")
    if total == 0:
        return None
    p = successes / total
    denom = 1 + z * z / total
    center = (p + z * z / (2 * total)) / denom
    radius = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / denom
    return [max(0.0, center - radius), min(1.0, center + radius)]


def proportion(successes, total):
    return {"successes": successes, "n": total,
            "estimate": successes / total if total else None,
            "ci95_wilson": wilson_interval(successes, total)}


def percentile(values, q):
    if not values or not 0 <= q <= 1:
        raise ValueError("Nonempty values and 0 <= q <= 1 required")
    ordered = sorted(values)
    index = (len(ordered) - 1) * q
    lower = int(index)
    upper = min(lower + 1, len(ordered) - 1)
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (index - lower)


def cluster_bootstrap(records, statistic, cluster_key="block_id", resamples=5000, seed=20261108):
    """Resample whole blocks; statistic returns None when an estimate is undefined.

    Each sampled block retains all of its records. Falling back to episode_id
    never treats the repeated six decisions inside a record as independent.
    """
    if resamples < 1:
        raise ValueError("resamples must be positive")
    grouped = defaultdict(list)
    for record in records:
        key = record.get(cluster_key) or record["episode_id"]
        grouped[key].append(record)
    point = statistic(records)
    if not grouped or point is None:
        return {"estimate": point, "ci95_bootstrap": None, "n_clusters": len(grouped),
                "bootstrap_resamples": resamples, "valid_resamples": 0}
    blocks = list(grouped.values())
    rng = random.Random(seed)
    estimates = []
    for _ in range(resamples):
        sample = [row for _ in blocks for row in rng.choice(blocks)]
        value = statistic(sample)
        if value is not None:
            estimates.append(value)
    return {"estimate": point,
            "ci95_bootstrap": [percentile(estimates, .025), percentile(estimates, .975)] if estimates else None,
            "n_clusters": len(blocks), "bootstrap_resamples": resamples,
            "valid_resamples": len(estimates)}


def mean_or_none(values):
    values = [value for value in values if value is not None]
    return mean(values) if values else None


def roc_auc(positive_scores, negative_scores):
    """Mann-Whitney AUROC with half credit for ties; None if either class is empty."""
    if not positive_scores or not negative_scores:
        return None
    return sum((p > n) + .5 * (p == n)
               for p in positive_scores for n in negative_scores) / (len(positive_scores) * len(negative_scores))
