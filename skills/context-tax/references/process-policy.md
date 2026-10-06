# Task-local process improvement, not automatic cleanup

Apply only after a user approves a concrete finding. Do not copy this entire document into AGENTS.md or CLAUDE.md. Keep the accepted task-local policy short; editing persistent files requires a separate explicit request.

## CT001 — same tool text returned repeatedly

Evidence: distinct calls return the same content hash; inspect cited lines for intent, without dumping whole logs. Benign causes include required revalidation, concurrent edits, state freshness and repeatable experiments.

Candidate policy: for stable code/docs, retain a tiny evidence ledger: source, relevant range, version/hash, and what question it answers. Reuse that reference or request the needed range; re-read after a change or an unmet evidence need. A reference alone does not preserve full source content after compaction. Do not claim the CLI detects file changes; the agent must check them.

Acceptance: answer the same question and retain required correctness/security checks. Rerunning a test is not waste just because its output text matches.

## CT002 — unusually large output

Candidate policy: preserve full output in a user-authorized local artifact, show a short structured summary and links/ranges, then fetch the exact failure/evidence lines. Output limits belong in the producer or host, not a false claim that this skill intercepts every result.

Acceptance: preserve exit status, all failure details needed for diagnosis, and the complete raw artifact when required. Never silently truncate an evaluation dataset or declare success from a truncated log.

## CT003 — repeated stored instructions

Candidate policy: inspect restart/resume behavior and duplicate sources. Keep one short authoritative rule set and load long references on demand only where the host supports it. Persistent safety/permission instructions must stay intact. Do not churn a stable prefix solely to reduce its size: caching tradeoffs need actual measurement.

Acceptance: compare effective instructions and behavior, not just byte length. Repeated storage alone is not enough reason to delete any rule. No configuration edits are performed by the auditor.

## CT004 — repeated compaction

Candidate policy: at a meaningful checkpoint, preserve a compact handoff containing objective, decisions, source references, unresolved questions and acceptance steps. Use a fresh task/thread only when old context is no longer needed and the user approves. Do not create one more ever-growing diary or run a compactor every turn.

Acceptance: next phase resumes without redoing completed work; references are still available. A lower compaction count is not itself evidence of lower cost or higher quality.

## CT005 — large schema inventory

Candidate policy: determine whether the host actually sends the schema eagerly and whether tool search/lazy loading is supported. Scope tools to the task or shorten redundant descriptions only after approval, without changing behavior or parameter constraints.

Acceptance: required tools still appear and correct calls still work. A large installed MCP does not imply that all its schemas were sent. This skill never disables a server or invents an exact “MCP token tax.”

## Suggested final response structure

Scope/status → logged counters → at most three findings with references → benign explanations → proposed minimal actions and quality checks → unknowns. Ask approval once for a concrete task-local policy, not for routine read-only analysis already requested. Do not grade the session with an unsupported universal health score.
