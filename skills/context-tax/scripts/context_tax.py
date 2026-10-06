#!/usr/bin/env python3
"""Context Tax 0.1.0: bounded, offline, read-only transcript evidence.

Python 3.10+, standard library only. See references/metrics.md for contracts.
A log is untrusted data: never execute it or echo its prose into the report.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import stat
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

VERSION = "0.1.0"
REPORT_SCHEMA = "context-tax/v1"
MIB = 1024 * 1024
KNOWN_TOOLS = {
    "Read", "Bash", "Grep", "Glob", "Write", "Edit", "MultiEdit", "WebFetch",
    "WebSearch", "Task", "Agent", "Skill", "ToolSearch", "exec_command",
    "shell_command", "shell", "local_shell", "read_file", "grep_files",
    "list_dir", "apply_patch", "write_stdin", "view_image", "spawn_agent",
    "wait", "update_plan", "get_resource", "read_resource", "list_resources",
}


class AuditError(Exception):
    """A user-actionable validation error; never embeds raw log content."""


def canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def alias(prefix: str, value: Any) -> str | None:
    return prefix + "-" + digest(str(value))[:12] if value is not None else None


def tool_label(value: Any) -> str:
    name = str(value or "unknown")
    short = name.removeprefix("functions.")
    return short if short in KNOWN_TOOLS else str(alias("tool", name))


def integer(value: Any) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) and 0 <= value <= 2**63 - 1 else None


def amount(value: Any) -> float | None:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        try:
            return float(value) if math.isfinite(value) and value >= 0 else None
        except OverflowError:
            return None
    return None


def text_of(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        # Text-only footprint. Images, encrypted reasoning and binary blocks are excluded.
        return "\n".join(text_of(v) for v in value if isinstance(v, (str, dict)))
    if isinstance(value, dict):
        for key in ("text", "output_text", "input_text"):
            if isinstance(value.get(key), str):
                return value[key]
    return ""


def payload_text(value: Any) -> str:
    text = text_of(value)
    if text.startswith(("Chunk ID:", "Wall time:")):
        # Remove only a recognized Codex runner envelope, not arbitrary prose.
        match = re.search(r"(?m)^(?:Final output|Output):\s*\n", text[:2048])
        if match:
            return text[match.end():]
    return text


def is_link(path: Path) -> bool:
    info = path.lstat()
    return stat.S_ISLNK(info.st_mode) or bool(getattr(info, "st_file_attributes", 0) & 0x400)


def regular_file(path: Path, max_bytes: int) -> os.stat_result:
    try:
        info = path.stat()
        if is_link(path) or not stat.S_ISREG(info.st_mode):
            raise AuditError("Input must be a regular file, not a symlink/reparse point.")
        if info.st_size > max_bytes:
            raise AuditError("Input exceeds the size cap; select a smaller log or explicitly raise --max-mb.")
        return info
    except OSError as exc:
        raise AuditError("Cannot access the input file; check its path and permissions.") from exc


def load_json(path: Path, max_bytes: int = 8 * MIB) -> Any:
    regular_file(path, max_bytes)
    try:
        with path.open("r", encoding="utf-8-sig") as stream:
            return json.load(stream, parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
    except (OSError, ValueError, RecursionError) as exc:
        raise AuditError("Invalid or unreadable JSON input.") from exc


def detect(record: dict) -> str | None:
    if "type" in record and not isinstance(record["type"], str):
        return None
    if record.get("type") in {"session_meta", "turn_context", "response_item", "compacted"}:
        return "codex"
    payload = record.get("payload")
    if record.get("type") == "event_msg" and isinstance(payload, dict):
        return "codex"
    message = record.get("message")
    if record.get("type") in {"assistant", "user", "system"} and (
        isinstance(message, dict) or "subtype" in record
    ):
        return "claude"
    response = record.get("response", record)
    if isinstance(response, dict) and isinstance(response.get("usage"), dict):
        if "prompt_tokens" in response["usage"]:
            return "openrouter"
    return None


def normalize_usage(kind: str, usage: dict) -> dict:
    if kind == "claude":
        fresh = integer(usage.get("input_tokens"))
        read = integer(usage.get("cache_read_input_tokens"))
        write = integer(usage.get("cache_creation_input_tokens"))
        total = fresh + read + write if None not in (fresh, read, write) else None
        output = integer(usage.get("output_tokens"))
    elif kind == "codex":
        total = integer(usage.get("input_tokens"))
        read = integer(usage.get("cached_input_tokens", usage.get("input_cached_tokens")))
        # Codex's protocol uses serde(default) = 0 for cache_write_input_tokens.
        write = integer(usage.get("cache_write_input_tokens", 0))
        output = integer(usage.get("output_tokens"))
        fresh = total - read - write if None not in (total, read, write) else None
    else:
        details = usage.get("prompt_tokens_details")
        details = details if isinstance(details, dict) else {}
        total = integer(usage.get("prompt_tokens"))
        read = integer(details.get("cached_tokens"))
        # OpenRouter omits cache_write_tokens for models without explicit paid writes.
        write = integer(details.get("cache_write_tokens", 0))
        output = integer(usage.get("completion_tokens"))
        fresh = total - read - write if None not in (total, read, write) else None
    if fresh is not None and fresh < 0:
        raise AuditError("Invalid cache partition: cached input plus cache writes exceeds total input.")
    for value in (total, fresh, read, write, output):
        if value is not None and value < 0:
            raise AuditError("Negative token counts are invalid.")
    # Reject invalid numeric values instead of interpreting them as reported zeroes.
    fields = {
        "claude": ("input_tokens", "output_tokens", "cache_read_input_tokens", "cache_creation_input_tokens"),
        "codex": ("input_tokens", "output_tokens", "cached_input_tokens", "input_cached_tokens", "cache_write_input_tokens"),
        "openrouter": ("prompt_tokens", "completion_tokens"),
    }[kind]
    if any(k in usage and integer(usage[k]) is None for k in fields):
        raise AuditError("Invalid token value in usage object.")
    if kind == "openrouter":
        if any(k in details and integer(details[k]) is None for k in ("cached_tokens", "cache_write_tokens")):
            raise AuditError("Invalid cache count in usage object.")
    return {
        "input_tokens": total, "fresh_input_tokens": fresh, "cached_input_tokens": read,
        "cache_write_tokens": write, "output_tokens": output,
    }


class Auditor:
    def __init__(self, source: str = "auto", large_bytes: int = 16384):
        self.source = source
        self.large_bytes = large_bytes
        self.rows: dict[str, dict] = {}
        self.calls: dict[str, str] = {}
        self.results: list[dict] = []
        self.result_seen: set[tuple] = set()
        self.message_seen: set[str] = set()
        self.instruction_blocks: dict[str, dict] = {}
        self.previous_total: dict | None = None
        self.previous_signature: str | None = None
        self.model: str | None = None
        self.provider: str | None = None
        self.compactions: list[str] = []
        self.warnings: Counter[str] = Counter()
        self.accounting_incomplete = False
        self.line_count = 0
        self.recognized = 0
        self.ignored = 0
        self.duplicate_usage_snapshots = 0
        self.schema_items: dict[str, dict] = {}
        self.request_snapshots: dict[str, dict] = {}
        self.session_ids: set[str] = set()

    def warn(self, code: str, incomplete: bool = False):
        self.warnings[code] += 1
        self.accounting_incomplete |= incomplete

    def add_row(self, key: str, kind: str, usage: dict, line: int,
                model: str | None, provider: str | None = None,
                granularity: str = "request", cost: Any = None):
        try:
            normalized = normalize_usage(kind, usage)
        except AuditError:
            self.warn("invalid_usage_object", True)
            return
        if normalized["input_tokens"] is None or normalized["output_tokens"] is None:
            self.warn("missing_usage_fields", True)
        creation = usage.get("cache_creation", {})
        creation = creation if isinstance(creation, dict) else {}
        model = model if isinstance(model, str) and len(model) <= 256 else None
        provider = provider if isinstance(provider, str) and len(provider) <= 256 else None
        row = dict(normalized, ref=f"L1:{line}", model_alias=alias("model", model),
                   provider_alias=alias("provider", provider), granularity=granularity,
                   _model=model, _source=kind, _cache_creation=creation,
                   reported_openrouter_credits=amount(cost) if kind == "openrouter" else None)
        if key in self.rows:
            self.duplicate_usage_snapshots += 1
        self.rows[key] = row

    def tool_result(self, call_id: Any, value: Any, line: int, tool: Any = None):
        text = payload_text(value)
        if not text:
            return
        cid = str(call_id) if call_id else f"unkeyed-{line}-{len(self.results)}"
        hashed = digest(text)
        signature = (cid, hashed)
        if signature in self.result_seen:
            return
        self.result_seen.add(signature)
        self.results.append({"ref": f"L1:{line}", "call": cid, "hash": hashed,
                             "bytes": len(text.encode("utf-8")),
                             "tool": tool_label(tool or self.calls.get(cid))})

    def instruction(self, role: Any, content: Any, line: int, message_id: Any = None):
        if not isinstance(role, str) or role not in {"system", "developer"}:
            return
        if message_id is not None:
            key = str(message_id)
            if key in self.message_seen:
                return
            self.message_seen.add(key)
        text = text_of(content)
        # Non-overlapping paragraphs only; no fuzzy matching or semantic accusation.
        for index, block in enumerate(re.split(r"\n[ \t]*\n", text)):
            size = len(block.encode("utf-8"))
            if size < 512:
                continue
            key = digest(block)
            entry = self.instruction_blocks.setdefault(key, {"bytes": size, "refs": [], "count": 0})
            entry["count"] += 1
            if len(entry["refs"]) < 8:
                entry["refs"].append(f"L1:{line}/paragraph-{index + 1}")

    def schema(self, tools: Any, ref: str):
        if not isinstance(tools, list):
            return
        for index, tool in enumerate(tools):
            if not isinstance(tool, dict):
                self.warn("non_object_schema_entry")
                continue
            serialized = canonical(tool)
            key = digest(serialized)
            fn = tool.get("function", tool)
            fn = fn if isinstance(fn, dict) else {}
            item = self.schema_items.setdefault(key, {
                "schema_alias": alias("schema", key), "tool": tool_label(fn.get("name")),
                "serialized_bytes": len(serialized.encode("utf-8")),
                "rough_tokens_bytes_div_4": math.ceil(len(serialized.encode("utf-8")) / 4),
                "occurrences": 0, "refs": [],
            })
            item["occurrences"] += 1
            if len(item["refs"]) < 5:
                item["refs"].append(f"{ref}/tools-{index + 1}")

    def codex(self, obj: dict, line: int):
        typ = obj.get("type")
        payload = obj.get("payload", {})
        if not isinstance(payload, dict):
            self.warn("non_object_codex_payload", True)
            return
        if typ == "session_meta":
            self.model = payload.get("model", self.model)
            self.provider = payload.get("model_provider", self.provider)
            if payload.get("id"):
                self.session_ids.add(str(payload["id"]))
            if len(self.session_ids) > 1:
                self.warn("multiple_sessions_in_one_file", True)
        elif typ == "turn_context":
            self.model = payload.get("model", self.model)
            self.provider = payload.get("model_provider", self.provider)
        elif typ == "response_item":
            ptype = payload.get("type")
            if not isinstance(ptype, str):
                self.warn("invalid_codex_item_type", True)
                return
            if ptype in {"function_call", "custom_tool_call"}:
                cid = payload.get("call_id", payload.get("id"))
                if cid:
                    self.calls[str(cid)] = str(payload.get("name", "unknown"))
            elif ptype in {"function_call_output", "custom_tool_call_output"}:
                self.tool_result(payload.get("call_id"), payload.get("output"), line)
            elif ptype == "message":
                self.instruction(payload.get("role"), payload.get("content"), line, payload.get("id"))
        elif typ == "compacted":
            self.compactions.append(f"L1:{line}")
        elif typ == "event_msg":
            if payload.get("type") == "context_compacted":
                # Event notifications can mirror persisted `compacted` items.
                self.warn("compaction_notification_seen_not_double_counted")
            if payload.get("type") != "token_count":
                return
            info = payload.get("info")
            if info is None:  # Rate-limit-only notification; not an inference request.
                return
            if not isinstance(info, dict) or not isinstance(info.get("total_token_usage"), dict):
                self.warn("codex_missing_cumulative_usage", True)
                return
            total = info["total_token_usage"]
            last = info.get("last_token_usage")
            last = last if isinstance(last, dict) else None
            signature = canonical(total)
            if signature == self.previous_signature:
                self.duplicate_usage_snapshots += 1
                return
            self.previous_signature = signature
            # Codex may emit a context-window sentinel, not real provider usage.
            if total.get("input_tokens") == 0 and total.get("output_tokens") == 0 and total.get("total_tokens", 0) > 0:
                self.warn("codex_context_window_sentinel_excluded", True)
                self.previous_total = None
                return
            try:
                cur = normalize_usage("codex", total)
                old = normalize_usage("codex", self.previous_total) if self.previous_total else None
                last_norm = normalize_usage("codex", last) if last else None
            except AuditError:
                self.warn("invalid_codex_cumulative_usage", True)
                self.previous_total = None
                return
            self.previous_total = total
            keys = ("input_tokens", "cached_input_tokens", "cache_write_tokens", "output_tokens")
            if old is None:
                chosen = last if last is not None else total
                if last_norm is None or any(cur[k] != last_norm[k] for k in keys):
                    self.warn("codex_initial_cumulative_prefix_unattributed", True)
                self.add_row(f"codex:{line}", "codex", chosen, line, self.model, self.provider,
                             "request" if last is not None else "interval")
                return
            delta = {k: cur[k] - old[k] if cur[k] is not None and old[k] is not None else None for k in keys}
            if any(v is not None and v < 0 for v in delta.values()):
                self.warn("codex_cumulative_counter_reset", True)
                if last is not None:
                    self.add_row(f"codex:{line}", "codex", last, line, self.model, self.provider)
                return
            if all(v == 0 for v in delta.values()):
                self.duplicate_usage_snapshots += 1
                return
            one_request = last_norm is not None and all(delta[k] == last_norm[k] for k in keys)
            if not one_request:
                self.warn("codex_aggregated_usage_interval")
            converted = {"input_tokens": delta["input_tokens"], "cached_input_tokens": delta["cached_input_tokens"],
                         "cache_write_input_tokens": delta["cache_write_tokens"], "output_tokens": delta["output_tokens"]}
            # Missing values stay absent, never synthesized as zero.
            converted = {k: v for k, v in converted.items() if v is not None}
            self.add_row(f"codex:{line}", "codex", converted, line,
                         self.model if one_request else None, self.provider if one_request else None,
                         "request" if one_request else "interval")

    def claude(self, obj: dict, line: int):
        if obj.get("type") == "system" and obj.get("subtype") == "compact_boundary":
            self.compactions.append(f"L1:{line}")
        message = obj.get("message")
        if not isinstance(message, dict):
            return
        content = message.get("content")
        if obj.get("type") == "assistant":
            mid = message.get("id")
            usage = message.get("usage")
            if isinstance(usage, dict):
                if not mid:
                    self.warn("claude_usage_without_message_id", True)
                key = f"claude:{mid}" if mid else f"claude:line:{line}"
                self.add_row(key, "claude", usage, line, message.get("model"))
            if isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "tool_use" and block.get("id"):
                        self.calls[str(block["id"])] = str(block.get("name", "unknown"))
        if obj.get("type") == "user" and isinstance(content, list):
            for block in content:
                if isinstance(block, dict) and block.get("type") == "tool_result":
                    self.tool_result(block.get("tool_use_id"), block.get("content"), line)
        self.instruction(message.get("role"), content, line, message.get("id"))

    def openrouter(self, obj: dict, line: int):
        response = obj.get("response", obj)
        if not isinstance(response, dict) or not isinstance(response.get("usage"), dict):
            return
        usage = response["usage"]
        rid = response.get("id")
        if not rid:
            self.warn("openrouter_usage_without_response_id", True)
        key = f"openrouter:{rid}" if rid else f"openrouter:line:{line}"
        self.add_row(key, "openrouter", usage, line, response.get("model"), response.get("provider"),
                     cost=usage.get("cost"))
        request = obj.get("request")
        if isinstance(request, dict):
            # Request snapshots are not tool-result events. Do NOT count retained
            # history as a new read call on each request.
            if isinstance(request.get("messages"), list):
                values = [canonical(m) for m in request["messages"] if isinstance(m, dict)]
                self.request_snapshots[key] = {
                    "messages": [(digest(m), len(m.encode("utf-8"))) for m in values],
                    "tools": request.get("tools"), "ref": f"L1:{line}",
                }

    def consume(self, obj: dict, line: int):
        kind = detect(obj)
        if self.source == "auto" and kind:
            self.source = kind
        if kind and kind != self.source:
            self.warn("mixed_log_sources_rejected", True)
            return
        if self.source not in {"codex", "claude", "openrouter"}:
            self.ignored += 1
            return
        if kind is None:
            self.ignored += 1
            return
        self.recognized += 1
        getattr(self, self.source)(obj, line)

    def findings(self) -> tuple[list[dict], dict]:
        groups: dict[str, list[dict]] = defaultdict(list)
        by_tool: dict[str, dict] = {}
        for item in self.results:
            groups[item["hash"]].append(item)
            tool = by_tool.setdefault(item["tool"], {"tool": item["tool"], "text_bytes": 0, "result_records": 0})
            tool["text_bytes"] += item["bytes"]
            tool["result_records"] += 1
        findings = []
        duplicates = 0
        for group in groups.values():
            distinct_calls = len({x["call"] for x in group})
            if distinct_calls > 1:
                extra = (distinct_calls - 1) * group[0]["bytes"]
                duplicates += extra
                if group[0]["bytes"] >= 1024:
                    findings.append({"rule": "CT001", "kind": "review", "evidence": "observed_text_equality",
                        "extra_observed_bytes": extra, "distinct_calls": distinct_calls,
                        "refs": [x["ref"] for x in group[:8]], "tool": group[0]["tool"],
                        "action": "Review identical results. Reuse a prior read only when target, range and version are unchanged. Never skip required tests or freshness checks."})
        for item in sorted(self.results, key=lambda x: -x["bytes"])[:10]:
            if item["bytes"] >= self.large_bytes:
                findings.append({"rule": "CT002", "kind": "review", "evidence": "observed_text_bytes",
                    "text_bytes": item["bytes"], "refs": [item["ref"]], "tool": item["tool"],
                    "action": "Prefer targeted queries or bounded lines; retain full evidence locally. Do not truncate failures or replace verification with a reassuring summary."})
        for entry in self.instruction_blocks.values():
            if entry["count"] > 1:
                findings.append({"rule": "CT003", "kind": "review", "evidence": "repeated_logged_instruction_paragraph",
                    "extra_observed_bytes": (entry["count"] - 1) * entry["bytes"],
                    "occurrences": entry["count"], "refs": entry["refs"],
                    "action": "Inspect restart/resume or instruction reinjection. Stored repetition is not proof of wire replay or waste. Preserve safety instructions."})
        if len(self.compactions) >= 2:
            findings.append({"rule": "CT004", "kind": "info", "evidence": "persisted_compaction_markers",
                "occurrences": len(self.compactions), "refs": self.compactions[:8],
                "action": "Check whether missing state caused re-reading after compaction. Compaction count alone does not prove savings or a defect."})
        for item in sorted(self.schema_items.values(), key=lambda x: -x["serialized_bytes"])[:5]:
            if item["serialized_bytes"] >= self.large_bytes:
                findings.append({"rule": "CT005", "kind": "review", "evidence": "static_serialized_schema_bytes",
                    "text_bytes": item["serialized_bytes"], "refs": item["refs"], "tool": item["tool"],
                    "action": "Review schema verbosity and host tool-search/lazy-loading support. An inventory is not proof this schema was sent or billed."})
        findings.sort(key=lambda f: -f.get("extra_observed_bytes", f.get("text_bytes", 0)))
        total = sum(x["bytes"] for x in self.results)
        return findings[:20], {
            "tool_result_text_bytes": total,
            "repeated_tool_payload_extra_bytes": duplicates,
            "tool_payload_repeat_byte_ratio": duplicates / total if total else None,
            "tool_result_records": len(self.results),
            "top_tools_by_observed_text_bytes": sorted(by_tool.values(), key=lambda x: -x["text_bytes"])[:10],
            "definition": "Text payloads observed in this transcript, excluding recognized runner envelopes; not provider tokens, wire replay or proven waste.",
        }

    def finish(self, prices: dict | None = None, case: str | None = None, outcome: str = "unknown",
               acceptance_hash: str | None = None) -> dict:
        if self.recognized == 0:
            raise AuditError("No supported records found. This is not evidence of zero usage; expected JSONL, not a pretty-printed JSON export.")
        rows = list(self.rows.values())
        if not rows:
            self.warn("no_usage_records", True)
        fields = ("input_tokens", "fresh_input_tokens", "cached_input_tokens", "cache_write_tokens", "output_tokens")
        totals = {k: sum(r[k] for r in rows if r[k] is not None) if any(r[k] is not None for r in rows) else None for k in fields}
        coverage = {k: sum(r[k] is not None for r in rows) for k in fields}
        known = [r for r in rows if r["input_tokens"] is not None and r["cached_input_tokens"] is not None]
        known_input = sum(r["input_tokens"] for r in known)
        requests = [r for r in known if r["granularity"] == "request"]
        # A snapshot may be overwritten by an updated record of the same response.
        previous = Counter()
        reuse = size_sum = 0
        for snap in self.request_snapshots.values():
            current = Counter(k for k, _ in snap["messages"])
            sizes = dict(snap["messages"])
            reuse += sum(min(n, previous[k]) * sizes[k] for k, n in current.items())
            size_sum += sum(size for _, size in snap["messages"])
            previous = current
            self.schema(snap["tools"], snap["ref"])
        reported = [r["reported_openrouter_credits"] for r in rows if r["reported_openrouter_credits"] is not None]
        estimated = [price_row(r, prices) for r in rows] if prices else []
        complete_prices = bool(estimated) and all(x is not None for x in estimated)
        complete_reported = bool(rows) and len(reported) == len(rows)
        findings, payload = self.findings()
        public_rows = [{k: v for k, v in r.items() if not k.startswith("_")} for r in rows]
        complete = not self.accounting_incomplete and all(coverage[k] == len(rows) for k in fields)
        rates_fingerprint = alias("rates", canonical(prices)) if prices else None
        cost = {
            "reported_openrouter_credits_known_sum": sum(reported) if reported else None,
            "reported_cost_records": len(reported),
            "reported_cost_complete_for_observed_usage": complete_reported,
            "api_equivalent_estimate_usd": sum(estimated) if complete_prices else None,
            "price_table_fingerprint": rates_fingerprint,
            "estimate_complete_for_observed_usage": complete_prices,
            "cost_per_successful_task": None,
            "billing_note": "No subscription charge/remaining quota is inferred. API-equivalent estimates exclude non-token fees and are not invoices. OpenRouter credits remain separately denominated.",
        }
        if case and outcome == "pass" and acceptance_hash and complete:
            if complete_reported:
                cost["cost_per_successful_task"] = {"value": sum(reported), "unit": "openrouter_credits", "success": "user_declared_not_verified"}
            elif complete_prices:
                cost["cost_per_successful_task"] = {"value": sum(estimated), "unit": "api_equivalent_usd_estimate", "success": "user_declared_not_verified"}
        return {
            "schema": REPORT_SCHEMA, "version": VERSION, "source": self.source,
            "source_label": "L1", "status": "OBSERVED" if complete else "PARTIAL",
            "privacy": "No transcript prose, arguments, absolute paths or custom tool names are included. Stable aliases/hashes are pseudonyms, not guaranteed anonymization. Review before sharing.",
            "scope": {"lines_scanned": self.line_count, "recognized_records": self.recognized, "other_records": self.ignored,
                      "one_file_only": True, "no_subagent_auto_discovery": True},
            "accounting": {"totals_observed": totals, "coverage_records": coverage,
                "usage_records": len(rows), "request_records": sum(r["granularity"] == "request" for r in rows),
                "interval_records": sum(r["granularity"] != "request" for r in rows),
                "duplicate_usage_snapshots_excluded": self.duplicate_usage_snapshots,
                "cache_token_share_on_known_records": sum(r["cached_input_tokens"] for r in known) / known_input if known_input else None,
                "cache_share_records": len(known), "cache_share_input_denominator": known_input,
                "cache_hit_request_rate_on_known_records": sum(r["cached_input_tokens"] > 0 for r in requests) / len(requests) if requests else None,
                "cache_hit_request_denominator": len(requests),
                "max_observed_request_input_tokens": max((r["input_tokens"] for r in rows if r["input_tokens"] is not None and r["granularity"] == "request"), default=None),
                "complete_for_selected_file": complete},
            "payloads": payload, "schema_inventory": sorted(self.schema_items.values(), key=lambda x: -x["serialized_bytes"])[:20],
            "compaction_markers": {"count": len(self.compactions), "refs": self.compactions[:8]},
            "cost": cost,
            "task": {"case_alias": alias("case", case), "outcome": outcome, "acceptance_evidence_sha256": acceptance_hash,
                     "note": "Outcome and task equivalence are user-supplied; a hashed evidence file does not prove correctness."},
            "unavailable": {
                "tool_schema_tokens_exact": "No provider per-schema token attribution. Inventory bytes/4 is a rough heuristic only.",
                "context_replay_ratio_tokens": "Transcripts do not provide complete tokenized request bodies; cache share is not replay ratio.",
                "compression_saving": "No controlled intervention and quality-preserving repeated trials are established.",
                "avoidable_cost": "Repetition can be necessary; no counterfactual billing is observed.",
            },
            "request_snapshot_evidence": {"snapshots": len(self.request_snapshots),
                "message_reuse_byte_ratio": reuse / size_sum if size_sum else None,
                "definition": "Exact canonical-JSON message byte overlap with the previous supplied request; includes first request in denominator. Not tokens or waste. Valid only for one chronological conversation."},
            "findings": findings, "warnings": dict(self.warnings), "usage_evidence": public_rows,
        }


def validate_prices(value: Any) -> dict:
    if not isinstance(value, dict) or not isinstance(value.get("models"), dict) or not value.get("as_of"):
        raise AuditError("Price table needs an as_of label and a models object; all rates are USD per million tokens.")
    for rates in value["models"].values():
        if not isinstance(rates, dict) or any(amount(v) is None for v in rates.values()):
            raise AuditError("Prices must be finite nonnegative numbers.")
    return value


def price_row(row: dict, prices: dict | None) -> float | None:
    if not prices or row["granularity"] != "request" or row["_model"] is None:
        return None
    rates = prices["models"].get(row["_model"])
    if not isinstance(rates, dict):
        return None
    fields = (("fresh_input_tokens", "fresh_input"), ("cached_input_tokens", "cached_input"), ("output_tokens", "output"))
    cost = 0.0
    for field, key in fields:
        tokens = row[field]
        if tokens is None or (tokens and key not in rates):
            return None
        cost += tokens * rates.get(key, 0)
    writes = row["cache_write_tokens"]
    if writes is None:
        return None
    if writes:
        creation = row["_cache_creation"]
        five = integer(creation.get("ephemeral_5m_input_tokens"))
        hour = integer(creation.get("ephemeral_1h_input_tokens"))
        if five is not None and hour is not None:
            if five + hour != writes:
                return None
            for tokens, key in ((five, "cache_write_5m"), (hour, "cache_write_1h")):
                if tokens and key not in rates:
                    return None
                cost += tokens * rates.get(key, 0)
        elif "cache_write" in rates:
            cost += writes * rates["cache_write"]
        else:
            return None
    result = cost / 1_000_000
    return result if math.isfinite(result) else None


def audit(path: Path, source: str = "auto", max_mb: int = 64, line_mb: int = 4,
          prices: dict | None = None, schemas: Path | None = None, case: str | None = None,
          outcome: str = "unknown", acceptance: Path | None = None, large_bytes: int = 16384) -> dict:
    if not 1 <= max_mb <= 1024 or not 1 <= line_mb <= 32:
        raise AuditError("Use 1..1024 for --max-mb and 1..32 for --line-mb.")
    if source not in {"auto", "codex", "claude", "openrouter"}:
        raise AuditError("Unsupported source.")
    original = regular_file(path, max_mb * MIB)
    worker = Auditor(source, large_bytes)
    count_bytes = 0
    try:
        with path.open("rb") as stream:
            for line_num in range(1, 200002):
                raw = stream.readline(line_mb * MIB + 1)
                if not raw:
                    break
                worker.line_count = line_num
                count_bytes += len(raw)
                if line_num > 200000 or count_bytes > max_mb * MIB:
                    worker.warn("scan_limit_reached", True)
                    break
                if len(raw) > line_mb * MIB:
                    worker.warn("oversize_line_scan_stopped", True)
                    break
                if not raw.strip():
                    continue
                try:
                    text = raw.decode("utf-8-sig" if line_num == 1 else "utf-8")
                    obj = json.loads(text, parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
                    if not isinstance(obj, dict):
                        worker.warn("non_object_record", True)
                        continue
                    worker.consume(obj, line_num)
                except (UnicodeError, ValueError, RecursionError, TypeError, AttributeError, OverflowError):
                    worker.warn("malformed_jsonl_record", True)
    except OSError as exc:
        raise AuditError("Could not read the selected file.") from exc
    current = path.stat()
    if current.st_size != original.st_size or current.st_mtime_ns != original.st_mtime_ns:
        worker.warn("log_changed_during_audit", True)
    if schemas:
        inv = load_json(schemas)
        tools = inv.get("tools") if isinstance(inv, dict) else inv
        if not isinstance(tools, list):
            raise AuditError("--schemas expects a JSON tools array or an object with tools: [...].")
        worker.schema(tools, "S1")
    acceptance_hash = None
    if acceptance:
        regular_file(acceptance, 8 * MIB)
        acceptance_hash = hashlib.sha256(acceptance.read_bytes()).hexdigest()
    if prices is not None:
        prices = validate_prices(prices)
    return worker.finish(prices, case, outcome, acceptance_hash)


def compare(before: dict, after: dict) -> dict:
    if any(not isinstance(r, dict) or r.get("schema") != REPORT_SCHEMA for r in (before, after)):
        raise AuditError("compare expects two context-tax/v1 reports.")
    reasons = []
    try:
        if not before["task"]["case_alias"] or before["task"]["case_alias"] != after["task"]["case_alias"]:
            reasons.append("task_case_missing_or_different")
        if any(r["task"]["outcome"] != "pass" or not r["task"]["acceptance_evidence_sha256"] for r in (before, after)):
            reasons.append("both_runs_need_user_declared_pass_and_evidence")
        if any(not r["accounting"]["complete_for_selected_file"] for r in (before, after)):
            reasons.append("partial_accounting")
        if before["source"] != after["source"]:
            reasons.append("different_log_sources")
        models = [set(x["model_alias"] for x in r["usage_evidence"]) for r in (before, after)]
        providers = [set(x["provider_alias"] for x in r["usage_evidence"]) for r in (before, after)]
        if None in models[0] or None in models[1] or models[0] != models[1]:
            reasons.append("model_missing_or_changed")
        if providers[0] != providers[1]:
            reasons.append("provider_changed_or_coverage_changed")
        if any(r["accounting"]["interval_records"] for r in (before, after)):
            reasons.append("aggregated_intervals_not_request_attributable")
        a = before["accounting"]["totals_observed"]["input_tokens"]
        b = after["accounting"]["totals_observed"]["input_tokens"]
        valid_numbers = integer(a) is not None and integer(b) is not None
        if not valid_numbers:
            reasons.append("input_totals_missing")
        comparable = not reasons
        result = {
            "schema": "context-tax-comparison/v1", "comparable_under_user_declared_conditions": comparable,
            "blocking_reasons": reasons, "before_input_tokens": a, "after_input_tokens": b,
            "observed_input_delta_after_minus_before": b - a if valid_numbers else None,
            "observed_input_reduction_fraction": (a - b) / a if comparable and a else None,
            "observed_api_equivalent_cost_reduction_usd": None,
            "compression_saving": None,
            "note": "A single before/after pair is descriptive, not causal proof or a future savings guarantee. Task/environment/acceptance equivalence and success are user-declared, not verified by this tool. Include audit overhead in any end-to-end claim.",
        }
        ca = before["cost"]["api_equivalent_estimate_usd"]
        cb = after["cost"]["api_equivalent_estimate_usd"]
        if comparable and amount(ca) is not None and amount(cb) is not None and before["cost"]["price_table_fingerprint"] == after["cost"]["price_table_fingerprint"]:
            result["observed_api_equivalent_cost_reduction_usd"] = ca - cb
        return result
    except (KeyError, TypeError, ValueError) as exc:
        raise AuditError("Incomplete or invalid context-tax report structure.") from exc


def format_number(value: Any) -> str:
    if value is None:
        return "unknown"
    if isinstance(value, float):
        return f"{value:.6f}"
    return f"{value:,}" if isinstance(value, int) else str(value)


def markdown(report: dict) -> str:
    acc = report["accounting"]
    totals = acc["totals_observed"]
    out = [f"# Context Tax {VERSION}", "", f"Status: **{report['status']}** | Source: **{report['source']}** | Scope: **one selected log**", "",
           "Values below are observed log counters unless marked otherwise. Repetition is not automatically waste.", "",
           "| Metric | Value |", "|---|---:|"]
    labels = {"input_tokens": "Input (includes cache)", "fresh_input_tokens": "Fresh input (excludes cache read/write)",
              "cached_input_tokens": "Cache reads", "cache_write_tokens": "Cache writes", "output_tokens": "Output (do not add reasoning again)"}
    for key, label in labels.items():
        out.append(f"| {label} | {format_number(totals[key])} |")
    share = acc["cache_token_share_on_known_records"]
    out.extend([f"| Cache token share on {acc['cache_share_records']} known records | {str(round(share * 100, 2)) + '%' if share is not None else 'unknown'} |",
                f"| Usage records / identifiable requests | {acc['usage_records']} / {acc['request_records']} |",
                f"| Duplicate usage snapshots excluded | {acc['duplicate_usage_snapshots_excluded']} |",
                f"| Tool text bytes / repeated payload extra bytes | {report['payloads']['tool_result_text_bytes']:,} / {report['payloads']['repeated_tool_payload_extra_bytes']:,} |",
                f"| API-equivalent estimate USD (not subscription bill) | {format_number(report['cost']['api_equivalent_estimate_usd'])} |",
                f"| Reported OpenRouter credits (known records) | {format_number(report['cost']['reported_openrouter_credits_known_sum'])} |", "",
                "## Evidence to review"])
    if not report["findings"]:
        out.append("No threshold-level finding in the observed payloads. This is not a clean bill of health.")
    for item in report["findings"][:5]:
        refs = ", ".join(item["refs"][:4])
        size = item.get("extra_observed_bytes", item.get("text_bytes"))
        out.extend([f"**{item['rule']} — {item['evidence']}** ({refs}; bytes: {format_number(size)}).", item["action"], ""])
    out.extend(["## Boundaries", "Exact per-schema tokens, token-level replay, avoidable cost and compression savings are unknown.",
                "Local bytes/4 schema estimates are not tokenizer measurements. High cache use is not a waste finding.",
                "User-declared PASS and an evidence hash do not certify task correctness. This audit does not modify agent configuration."])
    if report["warnings"]:
        out.extend(["", "Warnings: " + "; ".join(f"{k} ({v})" for k, v in report["warnings"].items())])
    out.extend(["", "L1 means the selected log; numbers are original 1-based JSONL line references. S1 means an explicitly supplied schema inventory.",
                "No raw prompts, commands or absolute paths are printed. Hashes/aliases remain pseudonymous; review before public sharing.", ""])
    return "\n".join(out)


def discover(source: str, root: Path | None = None, limit: int = 5) -> dict:
    if root is None:
        root = (Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))) / "sessions") if source == "codex" else Path.home() / ".claude" / "projects"
    if not root.is_dir() or is_link(root):
        raise AuditError("Log root is missing or is a link/reparse point. Supply an explicit local --root.")
    candidates = []
    visited = 0
    directories_seen = 0
    incomplete = False
    def onerror(_: OSError):
        nonlocal incomplete
        incomplete = True
    for folder, dirs, files in os.walk(root, topdown=True, followlinks=False, onerror=onerror):
        directories_seen += 1
        if directories_seen > 2000:
            incomplete = True
            break
        dirs.sort(reverse=True)
        kept = []
        for name in dirs:
            try:
                if not is_link(Path(folder) / name):
                    kept.append(name)
            except OSError:
                incomplete = True
        dirs[:] = kept
        for name in files:
            visited += 1
            if visited > 5000:
                incomplete = True
                break
            path = Path(folder) / name
            if path.suffix != ".jsonl":
                continue
            try:
                if is_link(path) or not path.is_file():
                    continue
                info = path.stat()
                candidates.append((info.st_mtime_ns, str(path.resolve()), info.st_size))
            except OSError:
                incomplete = True
        if visited > 5000:
            break
    candidates.sort(reverse=True)
    return {"source": source, "metadata_only": True, "listing_may_be_incomplete": incomplete,
            "note": "Paths below are local/private; choose the intended project. Newest is not necessarily the current task. No log contents were read.",
            "candidates": [{"path": p, "bytes": s, "mtime_ns": t} for t, p, s in candidates[:limit]]}


def write_new(path: Path, text: str):
    if path.exists() or path.is_symlink():
        raise AuditError("Output already exists; choose a new report filename. Overwriting is disabled.")
    if not path.parent.is_dir():
        raise AuditError("Output parent directory does not exist.")
    try:
        with path.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(text)
    except OSError as exc:
        raise AuditError("Unable to create output file.") from exc


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", action="version", version=VERSION)
    subs = parser.add_subparsers(dest="command", required=True)
    p = subs.add_parser("audit", help="Audit one explicit JSONL file; no changes to source or config")
    p.add_argument("--log", type=Path, required=True)
    p.add_argument("--source", choices=["auto", "codex", "claude", "openrouter"], default="auto")
    p.add_argument("--max-mb", type=int, default=64)
    p.add_argument("--line-mb", type=int, default=4)
    p.add_argument("--prices", type=Path)
    p.add_argument("--schemas", type=Path)
    p.add_argument("--case", help="Same controlled task+code+inputs+acceptance conditions across runs; stored as an alias")
    p.add_argument("--outcome", choices=["unknown", "pass", "fail"], default="unknown")
    p.add_argument("--acceptance", type=Path, help="Existing acceptance result file; only its hash is recorded")
    p.add_argument("--json-out", type=Path)
    p.add_argument("--md-out", type=Path)
    p.add_argument("--format", choices=["markdown", "json"], default="markdown")
    p = subs.add_parser("discover", help="Bounded metadata-only listing of local log candidates (prints private paths)")
    p.add_argument("--source", choices=["codex", "claude"], required=True)
    p.add_argument("--root", type=Path)
    p.add_argument("--limit", type=int, choices=range(1, 11), default=5)
    p = subs.add_parser("compare", help="Compare saved reports; refuse savings percentages without equivalent declared conditions")
    p.add_argument("before", type=Path)
    p.add_argument("after", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "discover":
            print(json.dumps(discover(args.source, args.root, args.limit), ensure_ascii=False, indent=2))
            return 0
        if args.command == "compare":
            print(json.dumps(compare(load_json(args.before), load_json(args.after)), ensure_ascii=False, indent=2))
            return 0
        for output in (args.json_out, args.md_out):
            if output and (output.exists() or output.is_symlink()):
                raise AuditError("Output already exists; choose new filenames. No file was overwritten.")
        if args.json_out and args.md_out and args.json_out.resolve() == args.md_out.resolve():
            raise AuditError("JSON and Markdown outputs must use different filenames.")
        prices = validate_prices(load_json(args.prices)) if args.prices else None
        report = audit(args.log, args.source, args.max_mb, args.line_mb, prices, args.schemas, args.case, args.outcome, args.acceptance)
        js = json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
        md = markdown(report)
        if args.json_out:
            write_new(args.json_out, js)
        if args.md_out:
            write_new(args.md_out, md)
        print(js if args.format == "json" else md)
        return 0 if report["status"] == "OBSERVED" else 2
    except (AuditError, OSError, RecursionError) as exc:
        message = str(exc) if isinstance(exc, AuditError) else "Filesystem or nesting error; audit stopped without modifying inputs."
        print(f"context-tax: {message}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
