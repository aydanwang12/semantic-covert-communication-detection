# Raw experimental data

These files contain actual model responses from the controlled experiment.
Synthetic or mocked responses used in unit tests are not experimental data.
The task messages are authored administrative sentences; no user communications
or confidential datasets are used.

## File types

| File | Contents |
|---|---|
| `pilot.jsonl` | One completed pilot episode per line, including actual prompts, sender selection, transformed messages, receiver outputs/actions, and validation fields |
| `results.jsonl` | Main-split episode rows, using the same schema |
| `*.calls.jsonl` | Append-only record of every attempted sender/receiver model call, including raw CLI JSON events, raw response, usage, elapsed time, errors, validity, and task prompt |
| `*.manifest.json` | Configuration saved before calls begin, planned episode IDs, model settings, neutral instructions/hash, and CLI metadata |
| `frame_validation.jsonl` | Separate codebook-blind classifications of the 32 unique bank sentences, preserving every raw response |
| `frame_validation.summary.json` | Reconciliation of sentence labels and the 16 intervention triplets |

During collection, a file may be partial. The authoritative expected count is in
its manifest; the observed count is the number of saved episode records. Results
must not be described as complete until the counts and unique IDs are audited.

## Episode schema

`episode_id` is unique within the split. `block_id` identifies matched conditions
sharing the hidden bit, key orientation, nuisance frame, nuisance initial, and
replicate. `condition` is `no_channel`, `syntactic`, `semantic`, or
`semantic_placebo`. `hidden_bit` is the routing instruction; `encoded_bit` is what
the selected message means under the assigned codebook, and can differ from the
hidden instruction in controls or after a sender error.

`messages` contains `original`, `lexical`, `semantic_counterfactual`, and
`unchanged_repeat`. The last is exactly the original text. `prompts` and `actions`
are indexed first by `partner`/`outsider`, then by variant. Actions are integers
0 or 1; `null` means invalid or missing, never a guessed replacement. `responses`
contains the associated full raw call records. `sender_response` preserves the
sender call; `sender_valid` records whether it selected an approved literal
sentence. `planned_frame`/`planned_initial` and observed `frame`/`initial` preserve
valid wrong sender selections rather than repairing them.

The record includes the codebook for auditability, but it is not part of the
outsider's task prompt. Only `prompts.outsider[variant]`, the common system prompt,
and the common neutral CLI instructions are presented in that receiver call.
There is no shared conversation history across roles or variants.

`intervention_validation` checks exact agreement with the finite reviewed bank.
The separate frame-validation file supplies an additional same-model blind
semantic-label check. Exact bank matching does not by itself constitute
independent semantic validation.

## Invalidity, retries, and counting

Every attempted model call is appended and flushed. A timeout, process error,
unexpected tool use, malformed action, or invalid sender selection remains in
the data. Invalid sender responses produce an episode with planned receiver
actions set to `null` and no attempted receiver calls. Valid but wrong sender
selections are propagated into the interventions and receiver trials.

Repeated receiver calls are measurements within one episode, not independent
episodes. Conditions share factor blocks, and blocks are the bootstrap resampling
unit. The full design contains repeated identical prompts; episode counts must
not be represented as counts of independently authored messages.

A resume after an interrupted episode can leave partial call attempts in the
ledger as well as the eventual completed episode. Such attempts must be disclosed
and reconciled, not silently deleted or counted as extra independent observations.
The ordinary uninterrupted workflow makes no retries and performs no response
caching. The audit flags duplicate IDs, malformed rows, and ledger mismatches.

The same raw call appears in its call ledger and inside its episode record for
convenient auditing. These are two storage representations of one call, not two
observations. Analyze episode rows; use the ledger to verify collection fidelity.

## Redaction and reproduction

Only local home-directory prefixes in process stderr are replaced with `<HOME>`.
Prompts and raw model outputs are otherwise unchanged. For the supplied Codex-backed run, authentication is handled by the CLI; the
experiment code does not read the login token. Credentials are never included
in prompts or saved in these files.

From the repository root, numerical recalculation requires Python's standard
library and no model credentials:

```sh
python3 analysis/analyze.py data/pilot.jsonl data/results.jsonl --skip-figures
python3 tests/independent_audit.py data/pilot.jsonl data/results.jsonl \
  --summary analysis/results_summary.json --output analysis/independent_audit.json
```

Only pass files present in the checkout. Analysis records the SHA-256 of each
input. For live reruns and figure dependencies, follow the root README.
