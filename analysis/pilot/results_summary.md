# Recalculated experimental results

All numerical values below are computed from the supplied raw episode JSONL.

## Split: pilot

Episodes: 64

| Condition | n | Partner accuracy | Outsider accuracy | Frame gap | Lexical gap | Alarm rate |
|---|---:|---:|---:|---:|---:|---:|
| no_channel | 16 | 0.4375 | 0.6875 | 0.1875 | -0.1875 | 0.5625 |
| syntactic | 16 | 1.0000 | 0.5000 | -0.7500 | 0.6250 | 0.6250 |
| semantic | 16 | 1.0000 | 0.5000 | 0.1875 | -0.4375 | 0.1875 |
| semantic_placebo | 16 | 0.5000 | 0.4375 | 0.3125 | -0.1875 | 0.3125 |

Primary semantic-minus-syntactic frame gap: 0.9375; 95% block-bootstrap CI [0.625, 1.25].

Intervals describe the sampled design. A single model, constrained messages, shared templates, and finite crossing limit generalization.
The detector is a single-draw action-flip proxy, not the full distributional PoPLi estimator.
See results_summary.json for denominators, exclusions, invalid responses, transformation validation, orientation strata, and tied-score AUROC.
