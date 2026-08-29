"""Codex rollout JSONLからBenchmark sessionのusageと最終結果を取得する。"""

from __future__ import annotations

import json
import os
import shutil
from decimal import Decimal
from pathlib import Path
from typing import Any

import yaml

USAGE_FIELDS = ("input_tokens", "cached_input_tokens", "output_tokens", "reasoning_output_tokens", "total_tokens")


def unavailable(reason: str, session_id: str | None = None) -> dict[str, Any]:
    """推測せず取得不能理由を返す。"""

    return {
        "usage_status": "unavailable",
        "usage": {field: "unavailable" for field in USAGE_FIELDS},
        "credits": {field: "unavailable" for field in ("uncached_input", "cached_input", "output", "total")},
        "credit_rate": "unavailable",
        "final_result": "unavailable",
        "measurement": {"source": "codex-session-jsonl", "session_id": session_id or "unavailable", "status": "unavailable", "reason": reason},
    }


def record_session(reference: dict[str, str], destination: Path, rate_path: Path) -> dict[str, Any]:
    """一意なrolloutを保存しusage、credits、最終応答を返す。"""

    session_id = reference["session_id"]
    model = reference["model"]
    matches = find_rollouts(session_id)
    if len(matches) != 1:
        return unavailable("rollout-not-unique", session_id)
    source = matches[0]
    mismatch = validate_reference(source, reference)
    if mismatch is not None:
        return unavailable(mismatch, session_id)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    parsed = parse_rollout(destination, session_id)
    if parsed["usage_status"] != "available":
        parsed["measurement"]["rollout_file"] = str(destination)
        return parsed
    rates = yaml.safe_load(rate_path.read_text(encoding="utf-8"))
    parsed.update(calculate_credits(parsed["usage"], model, rates))
    parsed["measurement"].update({"rollout_file": str(destination), "original_rollout_file": str(source)})
    return parsed


def validate_reference(path: Path, reference: dict[str, str]) -> str | None:
    """session metadataを親、agent path、modelまで照合する。"""

    metadata: dict[str, Any] | None = None
    model: str | None = None
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            item = json.loads(line)
            if item.get("type") == "session_meta" and isinstance(item.get("payload"), dict):
                metadata = item["payload"]
            if item.get("type") == "turn_context" and isinstance(item.get("payload"), dict):
                value = item["payload"].get("model")
                if isinstance(value, str):
                    model = value
                    break
    except (OSError, UnicodeError, json.JSONDecodeError):
        return "rollout-unreadable"
    if metadata is None:
        return "session-metadata-not-found"
    expected_parent = reference.get("parent_session_id")
    actual_parent = metadata.get("parent_thread_id") or metadata.get("session_id")
    if expected_parent and expected_parent != "unavailable" and actual_parent != expected_parent:
        return "parent-session-mismatch"
    if metadata.get("agent_path") != reference.get("agent_path"):
        return "agent-path-mismatch"
    if model != reference.get("model"):
        return "model-mismatch"
    return None


def find_rollouts(session_id: str) -> list[Path]:
    """session metadataが一致するrolloutだけを列挙する。"""

    codex_home = Path(os.environ.get("CODEX_HOME") or Path(os.environ.get("USERPROFILE", str(Path.home()))) / ".codex")
    matches: list[Path] = []
    for path in (codex_home / "sessions").rglob("*.jsonl"):
        try:
            with path.open(encoding="utf-8") as stream:
                for line in stream:
                    item = json.loads(line)
                    if item.get("type") == "session_meta" and item.get("payload", {}).get("id") == session_id:
                        matches.append(path)
                        break
        except (OSError, UnicodeError, json.JSONDecodeError):
            continue
    return matches


def parse_rollout(path: Path, session_id: str) -> dict[str, Any]:
    """累積usageの親baselineを除き、最後のassistant結果を抽出する。"""

    totals: list[dict[str, int]] = []
    first_last: dict[str, int] | None = None
    final_result = "unavailable"
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            item = json.loads(line)
            payload = item.get("payload", {})
            if item.get("type") == "event_msg" and payload.get("type") == "token_count":
                info = payload.get("info") or {}
                total = normalize_usage(info.get("total_token_usage"))
                last = normalize_usage(info.get("last_token_usage"))
                if total is not None:
                    totals.append(total)
                    if first_last is None and last is not None:
                        first_last = last
            text = assistant_text(item)
            if text:
                final_result = text
    except (OSError, UnicodeError, json.JSONDecodeError):
        return unavailable("rollout-unreadable", session_id)
    if not totals or first_last is None:
        return unavailable("token-count-or-baseline-missing", session_id)
    baseline = subtract(totals[0], first_last)
    usage = subtract(totals[-1], baseline)
    if baseline is None or usage is None:
        return unavailable("usage-inconsistent", session_id)
    return {
        "usage_status": "available",
        "usage": usage,
        "final_result": final_result,
        "measurement": {"source": "codex-session-jsonl", "session_id": session_id, "status": "available", "baseline": baseline},
    }


def normalize_usage(value: Any) -> dict[str, int] | None:
    """Codex usage objectを既知fieldへ正規化する。"""

    if not isinstance(value, dict):
        return None
    result: dict[str, int] = {}
    for field in USAGE_FIELDS:
        raw = value.get(field, 0 if field == "reasoning_output_tokens" else None)
        if not isinstance(raw, int) or raw < 0:
            return None
        result[field] = raw
    return result


def subtract(left: dict[str, int], right: dict[str, int]) -> dict[str, int] | None:
    """usageをfield単位で減算する。"""

    result = {field: left[field] - right[field] for field in USAGE_FIELDS}
    return result if all(value >= 0 for value in result.values()) else None


def assistant_text(item: dict[str, Any]) -> str | None:
    """rollout itemからassistantの最終テキスト候補を取り出す。"""

    payload = item.get("payload", {})
    if item.get("type") == "event_msg" and payload.get("type") == "agent_message":
        message = payload.get("message")
        return message if isinstance(message, str) and message.strip() else None
    if item.get("type") == "response_item" and payload.get("type") == "message" and payload.get("role") == "assistant":
        texts = [part.get("text") for part in payload.get("content", []) if isinstance(part, dict) and isinstance(part.get("text"), str)]
        return "\n".join(texts) if texts else None
    return None


def calculate_credits(usage: dict[str, int], model: str, config: dict[str, Any]) -> dict[str, Any]:
    """モデル別rateからCodex creditsを算出する。"""

    rate = config.get("credit_rates", {}).get(model)
    if not isinstance(rate, dict):
        return {"credits": {field: "unavailable" for field in ("uncached_input", "cached_input", "output", "total")}, "credit_rate": "unavailable"}
    cached = usage["cached_input_tokens"]
    uncached = usage["input_tokens"] - cached
    if uncached < 0:
        return {"credits": {field: "unavailable" for field in ("uncached_input", "cached_input", "output", "total")}, "credit_rate": "unavailable"}
    million = Decimal(1_000_000)
    values = {
        "uncached_input": Decimal(uncached) * Decimal(str(rate["input_per_million"])) / million,
        "cached_input": Decimal(cached) * Decimal(str(rate["cached_input_per_million"])) / million,
        "output": Decimal(usage["output_tokens"]) * Decimal(str(rate["output_per_million"])) / million,
    }
    values["total"] = sum(values.values())
    return {
        "credits": {key: float(value) for key, value in values.items()},
        "credit_rate": {"model": model, "source": config.get("source"), "checked_at": config.get("checked_at"), **rate},
    }
