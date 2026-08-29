"""Codex session JSONLからシナリオ共通のusageとcreditsを計測する。"""

from __future__ import annotations

import json
import os
from decimal import Decimal
from itertools import pairwise
from pathlib import Path
from typing import Any

import yaml

USAGE_FIELDS = (
    "input_tokens",
    "cached_input_tokens",
    "output_tokens",
    "reasoning_output_tokens",
    "total_tokens",
)
REQUIRED_USAGE_FIELDS = (
    "input_tokens",
    "cached_input_tokens",
    "output_tokens",
    "total_tokens",
)
CREDIT_FIELDS = ("uncached_input", "cached_input", "output", "total")
MEASUREMENT_SOURCE = "codex-session-jsonl"


def unavailable_usage() -> dict[str, str]:
    """取得不能なraw usageを機械可読な形で返す。"""

    return {field: "unavailable" for field in USAGE_FIELDS}


def unavailable_credits() -> dict[str, str]:
    """取得不能なcredit内訳を機械可読な形で返す。"""

    return {field: "unavailable" for field in CREDIT_FIELDS}


def unavailable_measurement(
    reason: str,
    session_id: str | None = None,
    rollout_file: str | None = None,
) -> dict[str, Any]:
    """推測せずunavailableと理由を返す。"""

    return {
        "usage_status": "unavailable",
        "usage": unavailable_usage(),
        "credits": unavailable_credits(),
        "credit_rate": "unavailable",
        "measurement": {
            "source": MEASUREMENT_SOURCE,
            "session_id": session_id or "unavailable",
            "rollout_file": rollout_file or "unavailable",
            "status": "unavailable",
            "reason": reason,
        },
    }


def resolve_codex_home(environment: dict[str, str] | None = None) -> Path:
    """環境変数またはユーザーhomeからCodex homeを解決する。"""

    values = os.environ if environment is None else environment
    configured = values.get("CODEX_HOME")
    if configured:
        return Path(configured).expanduser().resolve()
    user_profile = values.get("USERPROFILE")
    if user_profile:
        return (Path(user_profile).expanduser() / ".codex").resolve()
    return (Path.home() / ".codex").resolve()


def find_rollout_file(session_id: str, codex_home: Path | None = None) -> tuple[Path | None, str | None]:
    """session IDを含みmetadataも一致するrolloutを一意に特定する。"""

    home = resolve_codex_home() if codex_home is None else codex_home.resolve()
    sessions_root = home / "sessions"
    if not sessions_root.is_dir():
        return None, "codex-sessions-directory-not-found"

    # ファイル時刻ではなくsession IDで候補を限定
    candidates = sorted(sessions_root.rglob(f"rollout-*{session_id}*.jsonl"))
    matches: list[Path] = []
    for path in candidates:
        metadata, error = read_session_metadata(path)
        if error is None and metadata is not None and session_metadata_id(metadata) == session_id:
            matches.append(path)
    if not matches:
        return None, "rollout-not-found"
    if len(matches) != 1:
        return None, "rollout-not-unique"
    return matches[0], None


def read_session_metadata(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    """rollout先頭側からsession metadataを取得する。"""

    try:
        with path.open(encoding="utf-8") as stream:
            for line_number, line in enumerate(stream, start=1):
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    return None, f"invalid-jsonl-line-{line_number}"
                if isinstance(event, dict) and event.get("type") == "session_meta":
                    payload = event.get("payload")
                    if isinstance(payload, dict):
                        return payload, None
                    return None, "session-metadata-invalid"
    except (OSError, UnicodeError):
        return None, "rollout-unreadable"
    return None, "session-metadata-not-found"


def session_metadata_id(metadata: dict[str, Any]) -> str | None:
    """schema差を許容してsession IDを取得する。"""

    # subagent schemaではidが子thread、session_idがroot sessionを表す
    for key in ("id", "session_id"):
        value = metadata.get(key)
        if isinstance(value, str) and value:
            return value
    return None


def read_token_usage(path: Path) -> dict[str, Any]:
    """累積token_countからsession開始前baselineを除いたusageを返す。"""

    cumulative_values: list[dict[str, int | None]] = []
    first_last_usage: dict[str, int | None] | None = None
    try:
        with path.open(encoding="utf-8") as stream:
            for line_number, line in enumerate(stream, start=1):
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    return unavailable_usage_result(f"invalid-jsonl-line-{line_number}")
                if not token_count_event(event):
                    continue
                info = event.get("payload", {}).get("info")
                if not isinstance(info, dict) or "total_token_usage" not in info:
                    continue
                total, error = parse_usage_value(info.get("total_token_usage"))
                if error is not None:
                    return unavailable_usage_result(error)
                assert total is not None
                cumulative_values.append(total)
                if first_last_usage is None:
                    first_last_usage, error = parse_usage_value(info.get("last_token_usage"))
                    if error is not None:
                        return unavailable_usage_result(f"baseline-{error}")
    except (OSError, UnicodeError):
        return unavailable_usage_result("rollout-unreadable")

    if not cumulative_values:
        return unavailable_usage_result("token-count-not-found")
    if first_last_usage is None:
        return unavailable_usage_result("baseline-last-token-usage-missing")
    if not cumulative_is_monotonic(cumulative_values):
        return unavailable_usage_result("cumulative-usage-decreased")

    baseline, error = subtract_usage(cumulative_values[0], first_last_usage)
    if error is not None:
        return unavailable_usage_result(f"baseline-{error}")
    usage, error = subtract_usage(cumulative_values[-1], baseline)
    if error is not None:
        return unavailable_usage_result(f"final-{error}")
    assert usage is not None
    normalized_usage: dict[str, int | str] = {
        field: "unavailable" if value is None else value for field, value in usage.items()
    }
    error = validate_usage_consistency(normalized_usage)
    if error is not None:
        return unavailable_usage_result(error)
    return {
        "status": "available",
        "usage": normalized_usage,
        "baseline": {
            field: "unavailable" if value is None else value for field, value in baseline.items()
        },
        "reason": None,
    }


def token_count_event(event: Any) -> bool:
    """未知イベントを無視してtoken_countだけを判定する。"""

    return (
        isinstance(event, dict)
        and event.get("type") == "event_msg"
        and isinstance(event.get("payload"), dict)
        and event["payload"].get("type") == "token_count"
    )


def parse_usage_value(value: Any) -> tuple[dict[str, int | None] | None, str | None]:
    """usage objectを既知フィールドだけへ正規化する。"""

    if not isinstance(value, dict):
        return None, "usage-object-missing"
    result: dict[str, int | None] = {}
    for field in USAGE_FIELDS:
        item = value.get(field)
        if field == "reasoning_output_tokens" and item is None:
            result[field] = None
            continue
        if not isinstance(item, int) or isinstance(item, bool) or item < 0:
            return None, f"usage-field-invalid-{field}"
        result[field] = item
    return result, None


def subtract_usage(
    final: dict[str, int | None],
    baseline: dict[str, int | None],
) -> tuple[dict[str, int | None] | None, str | None]:
    """usageの各累積値からbaselineを安全に差し引く。"""

    result: dict[str, int | None] = {}
    for field in USAGE_FIELDS:
        final_value = final.get(field)
        baseline_value = baseline.get(field)
        if final_value is None or baseline_value is None:
            if field == "reasoning_output_tokens":
                result[field] = None
                continue
            return None, f"usage-field-missing-{field}"
        if final_value < baseline_value:
            return None, f"usage-decreased-{field}"
        result[field] = final_value - baseline_value
    return result, None


def cumulative_is_monotonic(values: list[dict[str, int | None]]) -> bool:
    """累積値が後退していないことを確認する。"""

    for previous, current in pairwise(values):
        for field in REQUIRED_USAGE_FIELDS:
            if current[field] is None or previous[field] is None or current[field] < previous[field]:
                return False
    return True


def validate_usage_consistency(usage: dict[str, int | str]) -> str | None:
    """cached inputやtotalの矛盾を検出する。"""

    input_tokens = usage["input_tokens"]
    cached_tokens = usage["cached_input_tokens"]
    output_tokens = usage["output_tokens"]
    total_tokens = usage["total_tokens"]
    assert all(isinstance(value, int) for value in (
        input_tokens, cached_tokens, output_tokens, total_tokens
    ))
    if cached_tokens > input_tokens:
        return "cached-input-exceeds-input"
    if total_tokens != input_tokens + output_tokens:
        return "total-token-count-inconsistent"
    reasoning_tokens = usage["reasoning_output_tokens"]
    if isinstance(reasoning_tokens, int) and reasoning_tokens > output_tokens:
        return "reasoning-output-exceeds-output"
    return None


def unavailable_usage_result(reason: str) -> dict[str, Any]:
    """parser内部の取得不能結果を返す。"""

    return {"status": "unavailable", "usage": unavailable_usage(), "baseline": unavailable_usage(), "reason": reason}


def load_credit_rates(path: Path) -> dict[str, Any]:
    """基準日つきcredit rate tableを読み込む。"""

    try:
        config = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as error:
        raise ValueError(f"credit-rate-config-unavailable: {error}") from error
    if not isinstance(config, dict) or not isinstance(config.get("credit_rates"), dict):
        raise TypeError("credit-rate-config-invalid")
    if not isinstance(config.get("checked_at"), str) or not isinstance(config.get("source"), str):
        raise TypeError("credit-rate-metadata-invalid")
    return config


def calculate_credits(
    usage: dict[str, int | str],
    model: str,
    rate_config: dict[str, Any],
) -> dict[str, Any]:
    """cached inputとreasoningを二重計上せずcreditsへ換算する。"""

    rate = rate_config["credit_rates"].get(model)
    if not isinstance(rate, dict):
        return {"status": "unavailable", "credits": unavailable_credits(), "credit_rate": "unavailable", "reason": "credit-rate-not-defined"}
    try:
        input_tokens = integer_usage(usage, "input_tokens")
        cached_tokens = integer_usage(usage, "cached_input_tokens")
        output_tokens = integer_usage(usage, "output_tokens")
        if cached_tokens > input_tokens:
            raise ValueError("cached-input-exceeds-input")
        input_rate = Decimal(str(rate["input_per_million"]))
        cached_rate = Decimal(str(rate["cached_input_per_million"]))
        output_rate = Decimal(str(rate["output_per_million"]))
    except (KeyError, TypeError, ValueError, ArithmeticError) as error:
        reason = str(error) or "credit-rate-invalid"
        return {"status": "unavailable", "credits": unavailable_credits(), "credit_rate": "unavailable", "reason": reason}

    # input_tokensはcached inputを含むため差分だけを通常input rateで計算
    million = Decimal(1_000_000)
    uncached = Decimal(input_tokens - cached_tokens) * input_rate / million
    cached = Decimal(cached_tokens) * cached_rate / million
    output = Decimal(output_tokens) * output_rate / million
    credits = {
        "uncached_input": decimal_number(uncached),
        "cached_input": decimal_number(cached),
        "output": decimal_number(output),
        "total": decimal_number(uncached + cached + output),
    }
    return {
        "status": "available",
        "credits": credits,
        "credit_rate": {
            "model": model,
            "input_per_million": rate["input_per_million"],
            "cached_input_per_million": rate["cached_input_per_million"],
            "output_per_million": rate["output_per_million"],
            "checked_at": rate_config["checked_at"],
            "source": rate_config["source"],
        },
        "reason": None,
    }


def integer_usage(usage: dict[str, int | str], field: str) -> int:
    """credit計算に必要な整数usageを取得する。"""

    value = usage.get(field)
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ValueError(f"usage-field-invalid-{field}")
    return value


def decimal_number(value: Decimal) -> int | float:
    """JSONへ保存できる数値へ変換する。"""

    return int(value) if value == value.to_integral_value() else float(value)


def measure_session(
    reference: dict[str, Any] | None,
    rate_config: dict[str, Any],
    codex_home: Path | None = None,
) -> dict[str, Any]:
    """session識別子を照合してusageとcreditsを計測する。"""

    if not isinstance(reference, dict):
        return unavailable_measurement("session-not-recorded")
    session_id = reference.get("session_id")
    model = reference.get("model")
    parent_session_id = reference.get("parent_session_id")
    agent_path = reference.get("agent_path")
    if not all(isinstance(value, str) and value for value in (
        session_id, model, parent_session_id, agent_path
    )):
        return unavailable_measurement("session-reference-incomplete", session_id if isinstance(session_id, str) else None)

    rollout, error = find_rollout_file(session_id, codex_home)
    if error is not None or rollout is None:
        return unavailable_measurement(error or "rollout-not-found", session_id)
    metadata, error = read_session_metadata(rollout)
    if error is not None or metadata is None:
        return unavailable_measurement(error or "session-metadata-not-found", session_id, rollout.name)
    if metadata.get("parent_thread_id") != parent_session_id:
        return unavailable_measurement("parent-session-mismatch", session_id, rollout.name)
    if metadata_agent_path(metadata) != agent_path:
        return unavailable_measurement("agent-path-mismatch", session_id, rollout.name)

    session_model, error = read_session_model(rollout)
    if error is not None:
        return unavailable_measurement(error, session_id, rollout.name)
    if session_model != model:
        return unavailable_measurement("session-model-mismatch", session_id, rollout.name)

    parsed = read_token_usage(rollout)
    if parsed["status"] != "available":
        return unavailable_measurement(parsed["reason"], session_id, rollout.name)
    calculated = calculate_credits(parsed["usage"], model, rate_config)
    if calculated["status"] != "available":
        return unavailable_measurement(calculated["reason"], session_id, rollout.name)
    return {
        "usage_status": "available",
        "usage": parsed["usage"],
        "credits": calculated["credits"],
        "credit_rate": calculated["credit_rate"],
        "measurement": {
            "source": MEASUREMENT_SOURCE,
            "session_id": session_id,
            "rollout_file": rollout.name,
            "status": "available",
            "reason": None,
        },
    }


def metadata_agent_path(metadata: dict[str, Any]) -> str | None:
    """schema差を許容してsubagent pathを取得する。"""

    direct = metadata.get("agent_path")
    if isinstance(direct, str) and direct:
        return direct
    source = metadata.get("source")
    if not isinstance(source, dict):
        return None
    spawn = source.get("subagent", {}).get("thread_spawn")
    if isinstance(spawn, dict) and isinstance(spawn.get("agent_path"), str):
        return spawn["agent_path"]
    return None


def read_session_model(path: Path) -> tuple[str | None, str | None]:
    """turn contextからsessionで使用したmodelを一意に取得する。"""

    models: set[str] = set()
    try:
        with path.open(encoding="utf-8") as stream:
            for line_number, line in enumerate(stream, start=1):
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    return None, f"invalid-jsonl-line-{line_number}"
                if not isinstance(event, dict) or event.get("type") != "turn_context":
                    continue
                payload = event.get("payload")
                model = payload.get("model") if isinstance(payload, dict) else None
                if isinstance(model, str) and model:
                    models.add(model)
    except (OSError, UnicodeError):
        return None, "rollout-unreadable"
    if not models:
        return None, "session-model-not-found"
    if len(models) != 1:
        return None, "session-model-not-unique"
    return next(iter(models)), None
