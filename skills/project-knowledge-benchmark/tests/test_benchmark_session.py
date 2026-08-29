from __future__ import annotations

import json
import runpy
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
USAGE = runpy.run_path(str(SKILL_ROOT / "scripts" / "benchmark_session.py"))


def token(total: dict[str, int], last: dict[str, int]) -> str:
    """Codex token_count eventをJSONL化する。"""

    return json.dumps({"type": "event_msg", "payload": {"type": "token_count", "info": {"total_token_usage": total, "last_token_usage": last}}})


def values(input_tokens: int, cached: int, output: int, reasoning: int = 0) -> dict[str, int]:
    """整合したusage objectを作る。"""

    return {"input_tokens": input_tokens, "cached_input_tokens": cached, "output_tokens": output, "reasoning_output_tokens": reasoning, "total_tokens": input_tokens + output}


def test_parse_rollout_subtracts_parent_and_extracts_final(tmp_path: Path) -> None:
    """親baselineを除き最後のAgent結果を取得する。"""

    path = tmp_path / "rollout.jsonl"
    path.write_text("\n".join([
        token(values(120, 80, 10), values(20, 10, 5)),
        token(values(180, 130, 25, 7), values(60, 50, 15, 7)),
        json.dumps({"type": "event_msg", "payload": {"type": "agent_message", "message": "Implemented."}}),
    ]), encoding="utf-8")
    result = USAGE["parse_rollout"](path, "session")
    assert result["usage_status"] == "available"
    assert result["usage"] == values(80, 60, 20, 7)
    assert result["final_result"] == "Implemented."


def test_credit_rate_is_model_specific() -> None:
    """cached inputを分離してモデルrateを適用する。"""

    config = {"source": "test", "checked_at": "2026-08-28", "credit_rates": {"model": {"input_per_million": 10, "cached_input_per_million": 1, "output_per_million": 20}}}
    result = USAGE["calculate_credits"](values(100, 80, 5), "model", config)
    assert result["credits"]["total"] == 0.00038
    assert USAGE["calculate_credits"](values(100, 80, 5), "unknown", config)["credit_rate"] == "unavailable"


def test_incomplete_rollout_is_unavailable(tmp_path: Path) -> None:
    """baselineがないusageを推測しない。"""

    path = tmp_path / "rollout.jsonl"
    path.write_text(json.dumps({"type": "event_msg", "payload": {"type": "agent_message", "message": "done"}}), encoding="utf-8")
    result = USAGE["parse_rollout"](path, "session")
    assert result["usage_status"] == "unavailable"
    assert result["usage"]["total_tokens"] == "unavailable"


def test_reference_validation_checks_parent_agent_and_model(tmp_path: Path) -> None:
    """session ID以外の対応関係も一致させる。"""

    path = tmp_path / "rollout.jsonl"
    path.write_text("\n".join([
        json.dumps({"type": "session_meta", "payload": {"id": "child", "parent_thread_id": "parent", "agent_path": "/root/task"}}),
        json.dumps({"type": "turn_context", "payload": {"model": "gpt-5.6-terra"}}),
    ]), encoding="utf-8")
    reference = {"session_id": "child", "parent_session_id": "parent", "agent_path": "/root/task", "model": "gpt-5.6-terra"}
    assert USAGE["validate_reference"](path, reference) is None
    reference["parent_session_id"] = "other"
    assert USAGE["validate_reference"](path, reference) == "parent-session-mismatch"
