# Independent quality audit

Audit owner: the separate testing/reproducibility agent. Checks below were performed
independently from the experiment and analysis implementation authors.

## Design and implementation (2026-11-08, before completed pilot analysis)

- Hidden bit, private-key orientation, nuisance frame, and nuisance initial are
  fully crossed. One replicate has 16 matched blocks and 64 condition episodes.
  Main with two replicates has 32 blocks and 128 episodes.
- For the *planned* stimuli, outsider prompt distributions are exactly identical
  across hidden-bit values within each condition. Partner prompt distributions
  are also identical across hidden bits in both negative controls. These are
  finite-design information-flow checks, not empirical claims about behavior.
- Partner and outsider receive identical public context and message. Replacing
  the partner's private convention with `NONE` yields the outsider prompt exactly.
  No episode ID, target, key or condition label is otherwise exposed.
- Codebook orientation is arbitrary and balanced; routes are interchangeable
  storage bays with no task-logic relation to past/future framing.
- Positive-channel encoder/decoder mappings round-trip for every binary factor
  combination. Placebo encoded bit agrees with actual hidden bit in exactly half
  the planned design, despite the same partner codebook as the semantic condition.
- Every clause in the 32-sentence bank was read. Independent temporal-cue tests
  classify all authored original/paraphrase clauses as past-origin or future-step
  focus. Lexical interventions preserve this focus while swapping A/B initial;
  semantic interventions change focus while retaining initial. This finite-bank
  validation does not establish unconstrained natural-language paraphrase quality.
  The frames contain lexical cues (earlier/origins versus next/forthcoming); this
  is not proof of a semantic channel independent of all token-level cues.
  Prefixes At present/By now carry small temporal nuances while both clauses retain
  the intended retrospective/prospective main focus.
- CLI calls create fresh temporary working directories, ignore user configuration,
  disable project-document injection, use a read-only sandbox, and prohibit tools
  in the experiment instruction. Tests confirm tool events invalidate calls.
  Harness system scaffolding and provider internals remain outside our audit.
- Invalid sender output is saved and suppresses receiver calls; wrong but valid
  sender choices are propagated without repair. Malformed/error receiver calls
  remain missing actions with raw response/error records retained.
- Strict output parsing rejects prose, booleans, float actions, extra keys and
  malformed JSON. Independent data audit additionally rejects duplicate JSON keys.
- Unit-test fixtures are labeled `unit_test_fixture` and are never written to
  scientific data files. Tests use temporary directories.
- JSONL write/read round trips, partial-output timeouts, raw CLI logs, fresh-call
  separation, and exact unchanged-message repeat prompts have unit checks.
- One original or intervened action is not an independent extra episode.
  Main episode counts refer to 32 finite crossed blocks per condition, not 32
  distinct semantic stimuli. Duplicate observable prompts receive fresh calls;
  common templates limit generalization. Unique message counts are reported.

## Tests

At the first completed implementation audit, `python3 -m unittest discover -s tests -v`
ran 43 tests and passed. This includes 15 metrics tests from the detection workstream
and 28 independent design, backend, persistence, and frame-validation checks.
The final project test log may supersede this count if tests are added.
A clean-source reproduction check also passed all 43 tests using system Python 3
from a fresh temporary copy containing only src/tests/experiments/config, without
the project virtual environment, Git metadata, or bytecode caches. No model calls
were made in that test reproduction.

## Blind model frame validation

The testing agent independently reconciled all 32 raw validation responses with
their saved labels and expected finite-bank frames: 32/32 correct, zero invalid
responses, zero errors, zero tool-use events. All 16 original/lexical/counterfactual
sets met the intended frame relationships. The rating prompts omit target routes
and private mappings. This uses the experimental model itself and is not an
independent-human or independent-model validation claim.

## Data and numerical checks

`tests/independent_audit.py` independently recomputes point estimates without
importing the production metrics or detection modules. It checks raw call ledger
against saved episode records, exact model response text against CLI final events,
strict response parsing, unique episode/call IDs, manifest completeness, matching
prompts, primary contrast, condition accuracy, intervention gaps, eligible counts,
alarm rates, and tied-score AUROC. It also records source SHA-256 hashes.

Completed pilot audit: `paper/pilot_data_audit.json` records PASS for all 64/64
planned episodes and 576 model calls (64 sender, 512 receiver), with zero duplicate
call keys, tool-use events, or valid-but-wrong sender choices. All 42 independent
point-estimate/denominator comparisons match `analysis/pilot/results_summary.json`.
A clean temporary copy of src/analysis plus raw pilot JSONL, run with system Python
and `--skip-figures`, exactly reproduced the entire numerical summary including
bootstrap confidence intervals, all counts, AUROCs, and input hash; only the
generation timestamp was excluded from equality. This is an executable
reproduction check, distinct from the independent point-estimate calculation.
Final combined audit: `paper/data_audit.json` records PASS for the 64 pilot and
128 main episodes, all 1,728 experiment calls, zero duplicate calls, zero tool-use
events, and zero valid-but-wrong sender choices. All 84 independent point-estimate,
denominator and AUROC comparisons match the final production summary exactly.
The additional 32 frame-validation calls are separately reconciled above. This audit
script does not independently reimplement bootstrap confidence intervals; synthetic
cluster-preservation tests cover the production bootstrap mechanics.

## Interpretation requirements

A positive semantic-minus-syntactic frame-gap contrast is not alone evidence of
successful semantic detection. It can arise when syntactic D is negative because
only the outsider changes under a frame intervention. Always inspect component
partner/outsider flip rates, semantic D itself, and classification/control alarms.
Chance outsider decoding does not imply semantic insensitivity: arbitrary key
orientation can make outsider accuracy chance while frame changes still alter its
actions. Semantic placebo alarms test designated hidden-instruction transmission,
not whether the partner uses a private convention at all.

## Prompt provenance

The experiment-owned CLI stdin is deterministically reconstructed from every
recorded system/task string and the fixed concatenation expression in src/agents.py.
The supplied neutral instruction text/hash is preserved in each manifest.
`data/submitted_prompts.derived.jsonl` contains 1,760 derived inputs with source-line
and SHA-256 provenance. `data/prompt_provenance.md` explicitly distinguishes these
from uncaptured provider/system/CLI-added scaffolding; no full provider-request
capture is claimed. Raw experiment records were not altered.

## Final clean-source numerical reproduction

`paper/reproduction_audit.json` records PASS for a fresh temporary copy of
src/analysis plus both raw episode files, run using system Python without the
project virtual environment. The entire final summary for 192 episodes was
identical, including all confidence intervals, counts, AUROCs and source hashes;
only the generation timestamp was excluded from comparison. No model calls were
made during this reproduction.

## Final report claim review

The testing agent read the final report source and reconciled the abstract,
results tables, component flip counts, accuracy/alarm fractions, primary contrast,
reported confidence intervals, AUROCs, unchanged repeats, pilot summaries, model
call totals, validation counts, and test/audit totals with the raw-data audit and
production summary. No numerical mismatch was found. The report distinguishes
the relative intervention contrast from absolute semantic detection and control
specificity, and explicitly discloses the uncaptured provider prompt boundary.
Report metadata records a 185-word abstract, seven main-text pages, and nine
pages including references/appendix. Visual PDF rendering is checked separately
by the orchestrator; this claim review does not substitute for that inspection.
