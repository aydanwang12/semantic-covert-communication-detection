# Independent audit of the post-hoc upgrade

This is a post-hoc audit of extensions to the archived experiment. It does not
change the original analysis plan or add model observations. The original pilot
and main JSONL data remain byte-identical to their previously audited SHA-256
hashes. See `upgrade_data_audit.json` for the independent numerical record.

## Removed unused eight-block fraction

The original runner offered an unused `--limit-blocks 8` parity fraction:

```text
I = H xor K xor F
```

In the semantic placebo, the partner can observe the frame F and initial I and
receives key K. On that fraction, H = I xor K xor F, so the *joint* observation
reveals the target perfectly, even though each factor's marginal is balanced.
This was a defect in an optional execution path, not in the collected study.
Both original run manifests have `limit_blocks: null`. For every condition and
replicate, the actual data contain all 16 combinations of H, K, nuisance F and I.
The original pilot/main raw hashes were verified unchanged after this repair.

The runner now accepts only `--limit-blocks 16` or omission, both retaining the
full crossing. Argparse rejects 8 before creating artifacts or making model
calls. Four regression tests independently show the former fraction's perfect
joint leak, full-cross equality of joint-observation distributions across H,
CLI rejection of 8, and supported model-free planning with 16. Full crossing makes
the parity decoder correct in exactly 8/16 placebo cases, and each (K,F,I) tuple
occurs once under each H.

## Target-conditioned paired audit

The independent review verified the pair key: split and condition are grouped
separately; replicate, template, key orientation, nuisance frame and nuisance
initial remain fixed while H changes. There are 8 pilot pairs and 16 main pairs
per condition, with no missing pair or action. Control prompts are byte-identical
within H pairs; positive-channel messages change through the assigned encoding.

All partner and outsider estimates and eligible counts were recomputed from raw
rows without importing the target-audit module. Main partner means of A(H=1)
minus A(H=0) are 1 for semantic and syntactic, 0 for semantic placebo, and -0.1875
for no channel. The corresponding exact sign-flip reference values were checked
independently using binomial-coefficient enumeration over nonzero differences.
All agree with `analysis/target_conditioned_results.json`.

This audit requires H and the matching factors, which the target-blind monitor
does not observe. It is post-hoc, uses the existing calls, and is not independent
new evidence. With complete balanced binary pairs its mean is algebraically
`2 * original decoding accuracy - 1`. Thus it reorganizes the existing accuracy
result rather than adding an improved detector or novel information measure.
The exact sign-flip reference assumes within-pair exchangeability under its null;
post-hoc/unadjusted values do not support a confirmatory or general causal claim.
The report should prioritize the effect sizes and disclose these assumptions.

## Query-view equivalence certificate

The testing agent independently constructed tuples of all eight actual named
receiver queries (system/task strings for both roles across four variants), plus
the common declared model/backend. The private convention, public context, and
message texts are already present in those exact queries. Semantic and semantic-
placebo tuples have identical multisets: 8 distinct suites among 16 episodes per
condition in pilot; 16 suites among 32 episodes per condition in main. Their
finite-design query-distribution total variation is exactly zero. Adding H to
this view gives total variation 0.5; adding the sender's private prompt gives 1.
These independently calculated values match the certificate script.

The mathematical conclusion is conditional. If the joint receiver-response law
given a query suite is common across conditions, equal query distributions imply
equal observable query-plus-response distributions. Data processing then gives
zero difference in alarm probabilities, balanced classification accuracy at most
1/2, and population score AUROC 1/2 for that declared finite-design observation
law. Independence within the eight-query suite is not necessary if the common
joint-kernel assumption holds. Realized independently sampled responses can and
do differ; equality of realized action histograms is not asserted.

The audit certifies query-distribution equality under the uniform finite design,
not equality of the model's unobserved response kernels. It excludes H, sender
private inputs, condition labels, episode/factor metadata, scheduling, timing,
runtime IDs, and other side channels. Temporal drift, condition-dependent hidden
state or added monitor information may invalidate the common-kernel assumption
or change the observation boundary. The claim is neither universal impossibility
of covert-communication monitoring nor impossibility for a monitor that knows
the target, observes sender inputs, or obtains informative extra interventions.
A purported adaptive extension would need the common-kernel property after each
permitted history, not merely the recorded fixed query suite.

During review, the certificate author fixed two generic edge cases reported by
the testing agent: empty input could otherwise vacuously certify through `all([])`,
and invalid actions could otherwise be mistaken for action changes. The current
script rejects empty datasets and explicitly excludes invalid detector scores.
Neither issue affected the complete, valid collected dataset.

## Validation status

The complete suite ran **59 tests and passed** after the runner repair and new
certificate/target-audit checks. The original 43 tests remain intact. No model
calls were performed for this upgrade audit. Numerical results, input hashes,
and exact finite-view checks are recorded in `upgrade_data_audit.json`.

The proof text and final upgraded PDF require a separate final review once
rendered; this document records code, data, and theorem-assumption checks rather
than claiming a future artifact has already been inspected.

## Final proof prose and runtime check

The completed `analysis/identifiability_theory.md` was independently reviewed.
The equal input-law argument, integration under a common joint response kernel,
TPR/FPR equality, balanced-accuracy and tied-AUROC conclusions, total-variation
bounds, privileged target/sender exceptions, and qualified adaptive-query extension
are mathematically consistent with the stated assumptions. The note clearly
separates exact saved-input equality from realized-output variation and does not
claim a novel general data-processing theorem or unrestricted impossibility.

An interpreter-specific regression-test wording issue was found when the project
runtime quoted `8` in argparse's error while system Python omitted the quotes.
The assertion now accepts either rendering while still requiring return code 2
and no created artifacts. Final project-runtime verification:
`.venv/bin/python -m pytest -q` passed **59 tests and 65 subtests**. This was a test
portability fix, not a change in accepted CLI arguments or experiment behavior.

The upgraded manuscript source and metadata were also checked against the recorded
results and theorem note. Its numerical claims agree; metadata records a 199-word
abstract and seven main-text pages (nine including references/appendix). The review
recommended clarifying that target labels break distributional equivalence rather
than yielding perfect single-episode classification: the ideal target-visible
TV is 1/2 and optimal balanced accuracy is 3/4. Final visual PDF inspection and
remote publication verification remain the orchestrator's responsibility.
