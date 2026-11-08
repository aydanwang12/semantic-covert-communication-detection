# Prompt provenance and capture boundary

The repository saves all **experiment-owned prompt components**, every authored
message/intervention, and every returned final response. It does **not** contain
a capture of the full provider request or every instruction/tool definition that
the Codex CLI and service may have added. Claims about “all prompts saved” must be
read with this explicit boundary.

## Exact locally submitted input

Each sender/receiver call is recorded in `pilot.calls.jsonl` or
`results.calls.jsonl`. Frame-rating calls are in `frame_validation.jsonl`.
Every call has `system_prompt` and `prompt` strings. For the collected
`codex_cli` backend, `system_prompt` is a logical experiment label: it is
concatenated into **stdin**, not sent by our code as a separate API system-role
message. The exact stdin construction in `src/agents.py` is:

```python
stdin = (
    "This is a single isolated research trial. Do not call tools, read files, "
    "browse the web, or inspect your environment. Answer only the supplied task.\n\n"
    + record["system_prompt"] + "\n\n" + record["prompt"]
)
```

The `\n` sequences above are Python escapes producing actual newline characters.
Any newline or literal backslash sequence *inside a saved string* is preserved
exactly when that JSON string is decoded; it must not be normalized or repaired.
The command receives this string via `subprocess.run(input=..., text=True)`.

The separate neutral model-instructions file is copied into the call's fresh
temporary directory and passed using the CLI's `model_instructions_file` setting.
Its exact content and SHA-256 are saved in each run manifest under
`model_instructions_text` and `model_instructions_sha256`. Those manifest values,
rather than a possibly later-edited config file, define the run's supplied text.
The fixed isolation prefix, neutral instruction content, and role/task strings
are sufficient to reconstruct the experiment-owned input for every recorded call.

## Reconstructing complete experiment-owned inputs

The completed run includes `submitted_prompts.derived.jsonl` with 1,760 derived
inputs (576 pilot, 1,152 main, and 32 blind frame-validation calls). To reproduce
this export at a fresh path, run from the repository root:

```sh
python experiments/export_submitted_prompts.py \
  data/pilot.calls.jsonl data/results.calls.jsonl data/frame_validation.jsonl \
  --output /tmp/submitted_prompts.reproduced.jsonl
```

The script makes no model calls and does not modify raw records. It reads the
`combined_prompt` string-concatenation expression from `src/agents.py`, checks the
manifest's instruction hash, and writes one derived record per original call.
Each contains exact reconstructed stdin, the supplied neutral instruction text,
source filename/line/hash, source-code hash, and input hash. Its label explicitly
says it is a **derived experiment-owned input**, not a full provider request.
The output must not already exist; choose a fresh output path when reproducing.
The script deliberately rejects an unsupported future construction instead of
guessing how prompts were assembled.

## What is and is not captured

- Captured: sender/receiver/validator task strings, logical role strings, public
  context, actual selected messages, private partner convention or outsider
  `NONE`, every authored intervention, exact neutral instruction text, model
  identifier, configured reasoning setting, CLI version, final response text,
  stdout JSON events, stderr, usage fields and timing where returned.
- Reconstructible: the exact experiment-owned stdin passed to the local CLI,
  including its fixed isolation prefix and separators; the separate instruction
  file content supplied to that CLI.
- Not captured: service-side system prompts, policy instructions, hidden reasoning,
  full network request bodies, all tool-schema or other harness scaffolding,
  runtime-resolved internal model revision, and any provider-side routing details.
  `--ignore-user-config`, zero project-document injection and isolated temporary
  directories reduce local context contamination; they do not establish that the
  provider-visible context consists only of our saved text.

Calls use fresh ephemeral sessions, a read-only sandbox, disabled web search and
instructions prohibiting tools. Returned tool-use events invalidate a call. This
is a recorded behavioral/isolation check, not an independent attestation of the
provider's internal execution. No credentials are stored. Known home-directory
prefixes in process stderr are replaced by `<HOME>`; prompts and model stdout
are not altered. The full supplied CLI input can therefore be reconstructed,
while a bit-for-bit reproduction of the complete model-provider interaction
cannot be claimed.
