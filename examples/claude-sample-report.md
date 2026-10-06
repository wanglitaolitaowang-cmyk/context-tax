# Context Tax 0.1.0

Status: **OBSERVED** | Source: **claude** | Scope: **one selected log**

Values below are observed log counters unless marked otherwise. Repetition is not automatically waste.

| Metric | Value |
|---|---:|
| Input (includes cache) | 2,200 |
| Fresh input (excludes cache read/write) | 400 |
| Cache reads | 1,600 |
| Cache writes | 200 |
| Output (do not add reasoning again) | 100 |
| Cache token share on 2 known records | 72.73% |
| Usage records / identifiable requests | 2 / 2 |
| Duplicate usage snapshots excluded | 1 |
| Tool text bytes / repeated payload extra bytes | 5,200 / 2,600 |
| API-equivalent estimate USD (not subscription bill) | unknown |
| Reported OpenRouter credits (known records) | unknown |

## Evidence to review
**CT001 — observed_text_equality** (L1:3, L1:5; bytes: 2,600).
Review identical results. Reuse a prior read only when target, range and version are unchanged. Never skip required tests or freshness checks.

## Boundaries
Exact per-schema tokens, token-level replay, avoidable cost and compression savings are unknown.
Local bytes/4 schema estimates are not tokenizer measurements. High cache use is not a waste finding.
User-declared PASS and an evidence hash do not certify task correctness. This audit does not modify agent configuration.

L1 means the selected log; numbers are original 1-based JSONL line references. S1 means an explicitly supplied schema inventory.
No raw prompts, commands or absolute paths are printed. Hashes/aliases remain pseudonymous; review before public sharing.
