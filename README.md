# Context Tax

**Find repeated context. Prove what you measured.**

[中文说明](README.zh-CN.md)

A Codex-first, explicitly invoked, local context-audit skill with a deterministic Python CLI. Audit one selected JSONL transcript, inspect actual usage counters and repeated text evidence, then propose minimal task-local process changes. No network, telemetry, API keys, pip/npm dependencies or automatic configuration edits. Python 3.10+.

This is not a new market: AviVAvi/TokenScope already provides a Claude Code profiler + skill. context-audit, ccusage and context-mode cover adjacent or overlapping needs. Context Tax is a small independently implemented, conservative adapter/workflow, not a claim of novelty, universal compatibility or proven savings. See [prior art and primary sources](skills/context-tax/references/sources.md).

## Quick start

From the extracted repository root:

```sh
python skills/context-tax/scripts/context_tax.py audit --source codex --log tests/fixtures/codex-synthetic.jsonl
python -m unittest discover -s tests -v
python install.py --target codex --dry-run
python install.py --target codex
python install.py --target codex --check
```

Windows users can substitute `py -3` for `python`. The interpreter must already exist; nothing is downloaded. The create-only installer refuses any existing destination. Codex default: `~/.agents/skills/context-tax`; Claude default with `--target claude`: `~/.claude/skills/context-tax`. `--dest` can set an exact alternative directory ending in `context-tax`; it does not register arbitrary paths with a host.

Explicitly invoke `$context-tax` in a supporting Codex surface / choose it from the host's skill picker, or `/context-tax` in Claude Code. Restart if not discovered. Host loading is a separate manual check, not proved by installation byte checks. Manual-only metadata is included for both hosts. No hooks or persistent configuration are changed. A skill's instructions are not a sandbox for the hosting agent.

## Real audit

```sh
python skills/context-tax/scripts/context_tax.py discover --source codex --limit 5
python skills/context-tax/scripts/context_tax.py audit --source codex --log "/replace/with/selected.jsonl" --json-out report-01.json --md-out report-01.md
```

Select the intended project, not automatically the newest file. Discovery reads bounded metadata only and displays private paths. Use one stable/completed session where possible. A session may contain several tasks. Default caps: 64 MiB file, 4 MiB line, 200,000 lines. Existing outputs are never overwritten. Exit 0 means observed supported accounting, 2 a valid partial report, 1 an input/format/filesystem failure. No real token usage is inferred from an empty report.

The CLI is offline; the agent invoking it still uses its normal model/network/billing. Do not load entire logs or the Python implementation into the model context. Read the compact report, then only small authorized evidence ranges.

## What is measured

Log-reported input, cache read/write and output; separate cache-token share and request cache-hit rate; cumulative-snapshot deduplication; exact repeated tool-result text and repeated stored instruction paragraphs; large output bytes and persisted compaction markers. Each finding carries line references and a review action. Repeated tests, fresh state checks and required verification are not automatically waste.

Optional `--schemas inventory.json` examines only supplied tool definitions. Canonical JSON bytes and a clearly labelled bytes/4 heuristic are not exact tokens or proof the schema was transmitted. Optional `--prices rates.json` uses caller-reviewed exact-model USD-per-million rates. The example rates and model names are fictitious. Missing prices/fields/models mean unknown. OpenRouter-reported credits remain separate from API-equivalent estimates and subscription bills.

Exact token replay ratio, hidden per-schema token attribution, avoidable cost and compression savings remain unknown. No automatic compaction, MCP removal, source changes, transcript truncation, cache invalidation diagnosis or live capture. Recommended process policies require approval and preserve acceptance criteria.

## Comparison, not causal claims

```sh
python skills/context-tax/scripts/context_tax.py compare before.json after.json
```

A descriptive reduction fraction requires both reports to share a user-defined `--case`, user-declared `--outcome pass`, `--acceptance` evidence hashes, complete accounting and compatible known models/source. The case must represent equivalent task/code/data/environment/acceptance conditions. The tool hashes evidence; it does not verify success or equivalence. A single permitted pair is not a causal savings experiment. Include audit overhead in end-to-end claims. See [metrics](skills/context-tax/references/metrics.md).

## Compatibility and validation

Known Codex rollout, Claude transcript and OpenRouter chat-completion JSONL shapes only; see [adapters](skills/context-tax/references/adapters.md). No automatic subagent aggregation, remote logs, arbitrary CSV, SSE or every future host version. Raw OpenRouter responses often lack payload/schema evidence; unavailable is not zero.

71 tests passed on Linux / Python 3.13.5, including CLI and temporary-directory installer tests. Three synthetic adapter demos were also executed. **No Windows, real-user-log or Codex Desktop E2E has been executed for this delivery. No actual savings demonstrated.** See [TESTING.md](TESTING.md) and [synthetic examples](examples/README.md).

Reports omit original prose, arguments and absolute paths; arbitrary tool/model/provider/case names become stable aliases. These are pseudonyms, not guaranteed anonymization. Review reports before public sharing. The CLI is read-only for inputs, not a filesystem security sandbox. Installation can leave a new partial directory after interruption; inspect rather than force-overwriting.

## Layout

```
skills/context-tax/SKILL.md           concise, manually invoked workflow
skills/context-tax/scripts/          deterministic offline auditor
skills/context-tax/references/       metrics, adapters, process policy, sources
skills/context-tax/agents/           Codex invocation metadata
install.py                           create-only local installer / byte check
tests/                               synthetic unit + CLI + installer tests
examples/                            fictitious rates and generated reports
```

MIT licensed. Source delivery only: no account connection, public repository publication or installation on the user's machine was performed.
