# Primary references and prior art

Reviewed 2026-10-06. URLs identify the documents used to define v0.1.0. Upstream formats and documentation may change. This package does not vendor third-party implementation code, claim to be first, or incorporate media volume estimates into its accounting.

## Formats and installation

- OpenAI Codex protocol TokenUsage/TokenUsageInfo/TokenCountEvent: https://github.com/openai/codex/blob/main/codex-rs/protocol/src/protocol.rs
- OpenAI skill authoring and current .agents/skills paths: https://learn.chatgpt.com/docs/build-skills
- OpenAI openai.yaml conventions: https://github.com/openai/skills/blob/main/skills/.system/skill-creator/references/openai_yaml.md
- Claude skills and manual invocation: https://code.claude.com/docs/en/skills
- Anthropic cache read/write accounting: https://platform.claude.com/docs/en/build-with-claude/prompt-caching
- OpenRouter usage and credits: https://openrouter.ai/docs/cookbook/administration/usage-accounting
- OpenRouter prompt caching: https://openrouter.ai/docs/guides/best-practices/prompt-caching
- Agent Skills specification: https://agentskills.io/specification

## Existing alternatives — do not claim an empty market

- AviVAvi/TokenScope: https://github.com/AviVAvi/TokenScope — direct Claude Code profiler + /tokenscope skill; repeated reads, expensive output, cache, MCP and recommendations. A strong existing alternative for Claude users.
- CShark-Hub/context-audit: https://github.com/CShark-Hub/context-audit — Claude Code configuration/context hygiene skill with approved changes. Its bytes/4 convention is heuristic, not exact tokenizer measurement.
- Agent-Skills-for-Context-Engineering: https://github.com/muratcankoylan/Agent-Skills-for-Context-Engineering — general context engineering/optimization skills.
- ccusage: https://github.com/ccusage/ccusage — local multi-agent usage reporting including Codex and Claude.
- context-mode: https://github.com/mksglu/context-mode — runtime output/context management via MCP/hooks, including Codex support; a larger intervention than this read-only audit.

Context Tax is an independently written, conservative Codex-first audit adapter and workflow. It does not claim greater maturity or unique ownership of the problem.
