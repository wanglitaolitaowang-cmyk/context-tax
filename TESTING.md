# Validation record — source delivery 0.1.0

Prepared 2026-10-06. Runtime used here: Linux, CPython 3.13.5.

## Actually executed

```
python -m unittest discover -s tests -v
```

71 tests passed: 64 auditor/accounting/CLI tests plus 7 temporary-directory installer tests. The full runner output is in tests/verification-output.txt. The tests use constructed records; they do not access the user's home, agent account, logs or configuration.

Coverage includes cumulative counters versus last-request counters, identical usage snapshots versus distinct requests, missing earlier prefixes, counter resets, aggregate intervals, excluded context-window sentinel, rate-only events, cache partition validation, reasoning-output double counting, Claude message-ID replacement, OpenRouter response-ID replacement, credits/upstream-cost separation, missing values, unknown model pricing, cache-write TTL rates, payload repeats, static schema estimates, controlled comparison gates, report privacy, bounded input, no overwrite and symlink handling. Installer tests cover dry-run, copy/check, existing-directory refusal, changed/missing files, invalid destination and symlink refusal.

Three CLI demos were actually executed with --source codex/claude/openrouter using the synthetic files in tests/fixtures. All returned exit 0 and created examples/*-sample-report.md/json. The Codex demo includes fictitious price/schema inputs. A comparison without a declared case/PASS/evidence was executed and correctly withheld a reduction fraction.

## NOT executed or demonstrated

Windows 10/11, PowerShell 5.1/7, macOS, Python 3.10/3.11/3.12, actual Codex Desktop/CLI skill discovery, actual Claude Code skill discovery, real customer logs, provider bill reconciliation, latency changes or any genuine savings experiment. Python 3.10+ is the implementation target, not proof of a tested version matrix. Byte-for-byte installation success is not host end-to-end success. No external CI run was performed.

## Manual acceptance before calling this a stable release

On the intended machine, record Python/OS/host versions. Run the synthetic suite; install only into an absent skill directory and verify host discovery. Select a completed non-sensitive real log belonging to the intended project; compare a small sequence of usage counters with the audit's line-referenced rows. Confirm source/configuration/PATH remain unchanged and missing fields produce PARTIAL/unknown rather than fabricated numbers.

Confirm privacy by inspecting output locally before sharing. Check that the Skill proposes at most three concrete actions, accepts a legitimate revalidation explanation, and does not silently edit files or weaken acceptance tests. Only then try a small approved process change against an equivalent task with unchanged quality criteria. Repeat trials before publishing an efficacy claim. Do not publish customer logs merely to obtain test fixtures.

No automated green result replaces those host-specific checks.
