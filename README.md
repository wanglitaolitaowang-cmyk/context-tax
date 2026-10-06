# Context Tax

**Find repeated context and inspect logged usage.**

[中文说明](README.zh-CN.md)

A local audit skill for selected Codex, Claude Code and OpenRouter JSONL logs, with a deterministic Python CLI. Inspect logged usage counters and repeated text, then use the manually invoked skill to review possible process improvements. The CLI runs offline with Python 3.10+ and the standard library. It requires no API keys or pip/npm dependencies.

## Quick start

### Get the source

Clone the repository:

```sh
git clone https://github.com/wanglitaolitaowang-cmyk/context-tax.git
cd context-tax
```

Alternatively, download and extract the source ZIP from GitHub. Run the commands below from the repository root, the directory containing `install.py`. An existing Python 3.10+ interpreter is required; the installer does not download Python. Windows users can substitute `py -3` for `python`.

### Try the CLI without installing a skill

```sh
python skills/context-tax/scripts/context_tax.py audit --source codex --log tests/fixtures/codex-synthetic.jsonl
```

This uses synthetic data. See the [example reports and expected values](examples/README.md).

### Install the skill

```sh
python install.py --target codex --dry-run
python install.py --target codex
python install.py --target codex --check
```

The installer creates a new skill directory and refuses any existing destination. Codex default: `~/.agents/skills/context-tax`; for Claude Code, use `--target claude` with each command to install into `~/.claude/skills/context-tax`. `--dest` sets an exact alternative directory ending in `context-tax`; custom destinations must be in a location searched by your host.

Explicitly invoke `$context-tax` in a supporting Codex surface / choose it from the host's skill picker, or `/context-tax` in Claude Code. Restart if not discovered. Host loading is a separate manual check, not proved by installation byte checks. Manual-only metadata is included for both hosts. No hooks or persistent configuration are changed. A skill's instructions are not a sandbox for the hosting agent.

### Run the tests

```sh
python -m unittest discover -s tests -v
```

Tests use synthetic records and temporary installation directories. See [validation results and coverage](TESTING.md).

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

Synthetic tests and CLI runs have been verified on Linux / Python 3.13.5 and Windows / Python 3.12.14. [TESTING.md](TESTING.md) records results, skipped tests and coverage. Real-user logs and host skill discovery in Codex Desktop/CLI and Claude Code remain unverified. No actual savings have been demonstrated.

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

## Related projects and references

TokenScope, context-audit, ccusage and context-mode address related usage profiling or context-management tasks. See [related projects and primary format references](skills/context-tax/references/sources.md).

## License

Licensed under the [MIT License](LICENSE).
