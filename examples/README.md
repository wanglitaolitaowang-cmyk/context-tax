# SYNTHETIC examples — not customer data or a savings experiment

All three JSONL files in ../tests/fixtures were constructed for this package. Their counts were chosen for deterministic tests and are NOT observations from a real Codex/Claude/OpenRouter session. prices.example.json contains fictitious model IDs and fictitious rates, not actual provider prices. schemas.example.json is intentionally oversized for demonstration.

Run from the extracted repository root:

```
python skills/context-tax/scripts/context_tax.py audit --source codex --log tests/fixtures/codex-synthetic.jsonl --prices examples/prices.example.json --schemas examples/schemas.example.json
python skills/context-tax/scripts/context_tax.py audit --source claude --log tests/fixtures/claude-synthetic.jsonl
python skills/context-tax/scripts/context_tax.py audit --source openrouter --log tests/fixtures/openrouter-synthetic.jsonl
```

Each command should exit 0 (OBSERVED accounting). Codex expected: 6 requests, 78,000 input, 60,000 cache reads, 18,000 fresh input, 600 output; 1 duplicate usage snapshot excluded; 12,000 extra repeated payload bytes. The fictitious API-equivalent estimate is USD 0.0528. This is not a real bill, demonstrated savings or a prediction.

Saved *-sample-report.md/json files are actual outputs of these commands with --md-out and --json-out. The files themselves have machine-generated titles; this README supplies the synthetic provenance. The auditor refuses to overwrite them; choose new output filenames when rerunning file exports.

comparison-blocked.example.json compares the Codex sample with itself WITHOUT a declared case, PASS or evidence. It demonstrates that a percentage is withheld rather than invented. It is not an optimization benchmark.
