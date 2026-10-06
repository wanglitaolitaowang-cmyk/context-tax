# Supported adapters and boundaries — v0.1.0

This is a bounded file parser, not a live collector. One UTF-8 JSONL file per audit, 64 MiB/4 MiB per line/200,000 lines by default. A file changing during the audit is flagged PARTIAL; prefer a completed session or a locally authorized stable copy. Unknown record types may be skipped; recognized accounting does not prove complete real-world capture. Do not merge unrelated sessions or parent/subagent files and assume correct total attribution.

## Codex — primary design target

Known records: session_meta; turn_context; response_item message/function_call/function_call_output/custom_tool_call/custom_tool_call_output; event_msg with payload.type=token_count and info.total_token_usage/last_token_usage; persisted compacted markers.

Running totals are differenced; unchanged snapshots and rate-limit-only events are excluded. First observed totals with an unallocated earlier prefix are flagged. Counter resets, invalid fields and a context-window sentinel are not silently treated as normal requests. Aggregate gaps are intervals without invented model attribution. Model/provider aliases are retained only from recognized metadata.

Default metadata discovery: CODEX_HOME/sessions, or ~/.codex/sessions. It does not access auth.json, secrets, configuration or archived sessions automatically. Newer/alternative schemas, remote-only sessions, missing usage records, task-level split, subagent family accounting, live prevention and all Desktop versions are NOT claimed supported. Cross-platform Python design is not Windows/Codex Desktop E2E proof.

## Claude Code — secondary, known JSONL shapes

Assistant records containing message.id/model/usage, assistant tool_use blocks and user tool_result blocks are supported. Latest snapshot of a repeated message.id replaces earlier usage. Missing IDs make reliable deduplication uncertain and therefore PARTIAL. Missing cache counters stay unknown. compact_boundary is a marker, not proof of saved tokens.

Default metadata discovery: ~/.claude/projects. Subagent files are not followed or aggregated. These are transcript structures, not a guarantee of support for future Claude Code log formats.

## OpenRouter — secondary, supplied exports only

Each JSONL line must be a final chat-completion response with id/model/usage.prompt_tokens/completion_tokens, or:

```json
{"request":{"messages":[],"tools":[]},"response":{"id":"r-1","model":"fixture-model","usage":{"prompt_tokens":100,"completion_tokens":10,"prompt_tokens_details":{"cached_tokens":80}}}}
```

This adapter assumes these records actually came from OpenRouter; generic compatible JSON does not prove origin. Latest response.id wins for duplicate snapshots. No ID means uncertain deduplication/PARTIAL. `usage.cost` is separately reported in credits. Request messages/tools are optional local evidence; normal retained request history is not counted as repeated execution. Without requests or a supplied schema inventory, schema/payload attribution can be empty and is not evidence of no overhead.

Not supported: dashboard activity CSV, arbitrary pretty-printed multi-line JSON, SSE streams, Responses API usage.input_tokens shapes, automatic API retrieval, provider cache-causality diagnosis or live wire interception.

## Optional inventory

`--schemas` accepts a JSON array of tools or `{"tools":[...]}`. This is a caller-supplied snapshot only; no MCP is launched or queried. Footprints omit non-tool request fields. Serialized bytes and labelled rough tokens are reported; exact per-schema token charge remains unavailable.

## Exit statuses

0: OBSERVED supported accounting in selected file (findings may exist).
2: PARTIAL report is valid but incomplete (do not retry blindly or claim zero usage).
1: input/format/filesystem failure; no successful audit.

Discovery reads metadata only, caps at 5,000 file entries and 2,000 directories, skips symlink/reparse entries, and flags potentially incomplete listings. Never auto-select the newest candidate when the intended project is unknown. This is not a filesystem sandbox against adversarial concurrent mutation.
