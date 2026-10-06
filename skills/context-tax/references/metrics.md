# Measurement contract — v0.1.0

Read only when interpreting a report. See sources.md for primary specifications.

## Observed token accounting

All values are log-reported provider/host counters, not independently measured tokenizer results or a reconciled invoice. `null` means unknown, not zero. `coverage_records` shows how many observed usage rows have each field. Totals on a PARTIAL report are only known subtotals. `OBSERVED` means supported accounting fields were present in this selected file; it does not prove the file captured every real request.

Codex and supported OpenRouter chat-completion records:

```
total input = fresh input + cache reads + cache writes
fresh input = total input - cache reads - cache writes
```

For supported Claude records:

```
fresh input = usage.input_tokens
total input = input_tokens + cache_read_input_tokens + cache_creation_input_tokens
```

Do not sum Codex running totals. Use cumulative differences, reconcile with last_token_usage, deduplicate unchanged snapshots. A gap covering multiple requests is an interval, not a request with an invented model. Reasoning output is not added to output_tokens. Cache-write omission maps to zero only in the documented Codex/OpenRouter shapes; missing cache-read counters remain unknown.

```
cache token share = sum(cache read) / sum(total input)
```

The numerator and denominator use the SAME rows with both counters known. This differs from:

```
cache-hit request rate = requests with cache read > 0 / requests with a known cache-read counter
```

Aggregate intervals are excluded from the request-rate denominator. Neither metric tells whether reuse was beneficial, preventable, or caused by provider routing. High cache share alone produces no waste finding.

## Payload evidence, not billed-token attribution

Tool payload sizes are UTF-8 bytes of text results after stripping only recognized Codex runner envelopes. Binary, images and encrypted reasoning are excluded. Two distinct tool calls returning identical text are repeated-payload evidence; a duplicate log record for the same call and payload is not another call. Repeated-byte total counts occurrences beyond the first, including small repeated payloads; CT001 findings require at least 1 KiB. Verify necessity before changing behavior.

Instruction evidence uses exact, non-overlapping paragraphs of at least 512 bytes, observed as system/developer messages. Repeated storage may be resume bookkeeping, not provider wire replay. No semantic/fuzzy duplicate detection is performed.

Static tool schemas are canonical-JSON bytes. `rough_tokens_bytes_div_4 = ceil(bytes / 4)` is a deliberately labelled rough heuristic, not a tokenizer; language, JSON and model tokenizers can differ substantially. An inventory does not prove that a tool schema was sent, selected by tool search, cached, or billed. Unknown/custom tool names are aliases, not MCP server identities.

Optional OpenRouter request snapshots expose exact canonical-JSON message overlap with the previous supplied request. Its denominator includes all messages in all supplied snapshots, including the first. This is a byte ratio, not token-level context replay. Normal retained history is not a newly executed read. Only use snapshots from one chronological conversation.

Defaults for triage: CT002 tool output >=16 KiB; CT005 static schema >=16 KiB; CT004 at least two persisted compaction markers. These are local review thresholds, not universal best-practice limits. Findings are capped at 20 in JSON, 5 in Markdown.

## Cost

Reported OpenRouter `usage.cost` is kept in OpenRouter credits. Do not add `upstream_inference_cost` to it. No subscription charge, remaining quota, latency or non-token fees are inferred.

Optional API-equivalent USD estimation:

```
(fresh * fresh_rate + read * read_rate + writes * matching_write_rate
 + output * output_rate) / 1_000_000
```

A caller supplies a dated, exact-model price table. No download or built-in current pricing. Positive buckets require a matching rate; unknown models/fields or intervals have no estimate. Claude's known 5-minute/1-hour write splits require matching rates and reconciliation with the total. A generic write rate is accepted only without a TTL split; choosing it is the caller's assumption. Example prices and model IDs in the repository are fictitious.

`cost_per_successful_task` additionally requires complete observed accounting, one explicitly declared case, a user-declared PASS and a hash of an existing acceptance file. The tool does NOT examine that file for correctness. A multi-task session is not automatically a single successful task.

## Before/after

The comparator reports raw input deltas when numbers exist. A reduction fraction requires the same declared case, both PASS+evidence, the same source and known model set, consistent provider coverage, no intervals and complete accounting. An API-equivalent cost delta also requires matching price-table fingerprints. Unknown providers remain unverified even when equally absent. Matching model sets do not establish an identical model mix.

These gates are minimum checks, not experiment validation: task/environment equivalence and outcomes are user assertions. Use repeated trials, representative tasks and unchanged quality criteria for any public efficacy claim. Include the auditing workflow's own overhead. `compression_saving` and avoidable dollars remain unknown in v0.1.0.

## Privacy and report references

L1:25 refers to physical JSONL line 25 of the selected local file, using one-based indexing. S1/tools-3 refers to item 3 of an explicitly supplied schema inventory. Reports omit original prompts, command arguments, absolute paths, and arbitrary/custom tool/model/provider/case names. Stable hashes and aliases are pseudonyms, not guaranteed anonymization; counts and patterns can still be sensitive. Metadata discovery intentionally prints private candidate paths. Review everything before public sharing.
