# Context Tax 0.1.0

Status: **OBSERVED** | Source: **openrouter** | Scope: **one selected log**

Values below are observed log counters unless marked otherwise. Repetition is not automatically waste.

| Metric | Value |
|---|---:|
| Input (includes cache) | 2,000 |
| Fresh input (excludes cache read/write) | 400 |
| Cache reads | 1,600 |
| Cache writes | 0 |
| Output (do not add reasoning again) | 200 |
| Cache token share on 2 known records | 80.0% |
| Usage records / identifiable requests | 2 / 2 |
| Duplicate usage snapshots excluded | 0 |
| Tool text bytes / repeated payload extra bytes | 0 / 0 |
| API-equivalent estimate USD (not subscription bill) | unknown |
| Reported OpenRouter credits (known records) | 0.002000 |

## Evidence to review
No threshold-level finding in the observed payloads. This is not a clean bill of health.
## Boundaries
Exact per-schema tokens, token-level replay, avoidable cost and compression savings are unknown.
Local bytes/4 schema estimates are not tokenizer measurements. High cache use is not a waste finding.
User-declared PASS and an evidence hash do not certify task correctness. This audit does not modify agent configuration.

L1 means the selected log; numbers are original 1-based JSONL line references. S1 means an explicitly supplied schema inventory.
No raw prompts, commands or absolute paths are printed. Hashes/aliases remain pseudonymous; review before public sharing.
