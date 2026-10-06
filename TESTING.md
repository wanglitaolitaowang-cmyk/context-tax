# Testing and validation

Validation covers the v0.1.0 implementation and synthetic fixtures. It does not establish compatibility with every host version or real-user log format.

## Verified runtimes

Results recorded on 2026-10-06:

| Runtime | Tests passed | Tests skipped | Evidence |
|---|---:|---:|---|
| Linux, CPython 3.13.5 | 71 | 0 | [Runner output](tests/verification-output.txt) |
| Windows, CPython 3.12.14 | 69 | 2 | [Runner output](tests/verification-output.windows.txt) |

Run the suite from the repository root:

```
python -m unittest discover -s tests -v
```

The suite contains 64 auditor/accounting/CLI tests and 7 installer tests. All records are constructed; installation tests write only to temporary directories. Tests do not read home-directory logs, agent accounts or configuration.

The Windows run used a fresh GitHub clone. Two tests were skipped: `test_symlink_input_rejected` because symlinks were unavailable, and `test_link_destination_rejected` because Windows symlink permission is host-dependent. Symlink protection is therefore not verified by that Windows run.

## Coverage

Coverage includes cumulative counters versus last-request counters, identical usage snapshots versus distinct requests, missing earlier prefixes, counter resets, aggregate intervals, excluded context-window sentinel, rate-only events, cache partition validation, reasoning-output double counting, Claude message-ID replacement, OpenRouter response-ID replacement, credits/upstream-cost separation, missing values, unknown model pricing, cache-write TTL rates, payload repeats, static schema estimates, controlled comparison gates, report privacy, bounded input, no overwrite and symlink handling. Installer tests cover dry-run, copy/check, existing-directory refusal, changed/missing files, invalid destination and symlink refusal.

CLI audits with `--source codex`, `claude` and `openrouter` were executed using the synthetic files in `tests/fixtures` on both runtimes. All returned exit 0. The Codex demo uses fictitious price/schema inputs. In the Windows run, generated JSON and Markdown reports matched the committed examples. A comparison without a declared case/PASS/evidence correctly withheld a reduction fraction. CLI help and installer dry runs for both targets also succeeded.

## Unverified coverage

macOS, Python 3.10/3.11, a Windows or PowerShell version matrix, actual Codex Desktop/CLI skill discovery, actual Claude Code skill discovery, real customer logs, provider bill reconciliation, latency changes and savings experiments remain unverified. Python 3.10+ is the implementation target; the table above lists tested runtimes. Byte-for-byte installation checks do not verify host discovery. The validation records are local runs, not external CI results.

## Verify on your host

On the intended machine, record Python/OS/host versions. Run the synthetic suite; install only into an absent skill directory and verify host discovery. Select a completed non-sensitive real log belonging to the intended project; compare a small sequence of usage counters with the audit's line-referenced rows. Confirm source/configuration/PATH remain unchanged and missing fields produce PARTIAL/unknown rather than fabricated numbers.

Confirm privacy by inspecting output locally before sharing. Check that the Skill proposes at most three concrete actions, accepts a legitimate revalidation explanation, and does not silently edit files or weaken acceptance tests. Only then try a small approved process change against an equivalent task with unchanged quality criteria. Repeat trials before publishing an efficacy claim. Do not publish customer logs merely to obtain test fixtures.

## File integrity and line endings

`SHA256SUMS.txt` records SHA-256 hashes of repository files with LF line endings. Git can convert a Windows checkout to CRLF when `core.autocrlf=true`; the resulting byte hashes differ even when Git reports a clean working tree. For byte-level verification, use a checkout that preserves LF. For example, clone into a new directory with this command:

```sh
git -c core.autocrlf=false clone https://github.com/wanglitaolitaowang-cmyk/context-tax.git context-tax-lf
```

This option applies to that clone command and does not change global Git configuration.
