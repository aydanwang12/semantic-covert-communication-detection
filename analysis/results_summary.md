# Recalculated experimental results

All numerical values below are computed from the supplied raw episode JSONL.

## Split: main

Episodes: 128

| Condition | n | Partner accuracy | Outsider accuracy | Frame gap | Lexical gap | Alarm rate |
|---|---:|---:|---:|---:|---:|---:|
| no_channel | 32 | 0.4062 | 0.5625 | -0.0312 | 0.1250 | 0.3438 |
| syntactic | 32 | 1.0000 | 0.4688 | -0.8125 | 0.7188 | 0.7188 |
| semantic | 32 | 1.0000 | 0.5625 | 0.2188 | -0.2500 | 0.2188 |
| semantic_placebo | 32 | 0.5000 | 0.5312 | 0.2812 | -0.4688 | 0.2812 |

Primary semantic-minus-syntactic frame gap: 1.0312; 95% block-bootstrap CI [0.84375, 1.21875].

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
