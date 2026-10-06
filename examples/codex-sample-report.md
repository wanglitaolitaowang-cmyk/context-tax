# Context Tax 0.1.0

Status: **OBSERVED** | Source: **codex** | Scope: **one selected log**

Values below are observed log counters unless marked otherwise. Repetition is not automatically waste.

| Metric | Value |
|---|---:|
| Input (includes cache) | 78,000 |
| Fresh input (excludes cache read/write) | 18,000 |
| Cache reads | 60,000 |
| Cache writes | 0 |
| Output (do not add reasoning again) | 600 |
| Cache token share on 6 known records | 76.92% |
| Usage records / identifiable requests | 6 / 6 |
| Duplicate usage snapshots excluded | 1 |
| Tool text bytes / repeated payload extra bytes | 39,000 / 12,000 |
| API-equivalent estimate USD (not subscription bill) | 0.052800 |
| Reported OpenRouter credits (known records) | unknown |

## Evidence to review
**CT002 — observed_text_bytes** (L1:18; bytes: 21,000).
Prefer targeted queries or bounded lines; retain full evidence locally. Do not truncate failures or replace verification with a reassuring summary.

**CT005 — static_serialized_schema_bytes** (S1/tools-1; bytes: 20,166).
Review schema verbosity and host tool-search/lazy-loading support. An inventory is not proof this schema was sent or billed.

**CT001 — observed_text_equality** (L1:5, L1:10, L1:15; bytes: 12,000).
Review identical results. Reuse a prior read only when target, range and version are unchanged. Never skip required tests or freshness checks.

**CT003 — repeated_logged_instruction_paragraph** (L1:3/paragraph-1, L1:12/paragraph-1; bytes: 816).
Inspect restart/resume or instruction reinjection. Stored repetition is not proof of wire replay or waste. Preserve safety instructions.

## Boundaries
Exact per-schema tokens, token-level replay, avoidable cost and compression savings are unknown.
Local bytes/4 schema estimates are not tokenizer measurements. High cache use is not a waste finding.
User-declared PASS and an evidence hash do not certify task correctness. This audit does not modify agent configuration.

L1 means the selected log; numbers are original 1-based JSONL line references. S1 means an explicitly supplied schema inventory.
No raw prompts, commands or absolute paths are printed. Hashes/aliases remain pseudonymous; review before public sharing.
