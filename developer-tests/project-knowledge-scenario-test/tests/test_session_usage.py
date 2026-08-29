"""Codex session JSONL usage計測を検証する。"""

from __future__ import annotations

import json
import runpy
from pathlib import Path
from typing import Any

import pytest

SKILL_ROOT = Path(__file__).resolve().parents[1]
MEASUREMENT = runpy.run_path(str(SKILL_ROOT / "scripts" / "session_usage.py"))
RATE_CONFIG = MEASUREMENT["load_credit_rates"](SKILL_ROOT / "agents" / "credit-rates.yml")


def usage(
    input_tokens: int,
    cached_input_tokens: int,
    output_tokens: int,
    reasoning_output_tokens: int = 0,
    **extra: Any,
) -> dict[str, Any]:
    """整合したテスト用usageを作成する。"""

    return {
        "input_tokens": input_tokens,
        "cached_input_tokens": cached_input_tokens,
        "output_tokens": output_tokens,
        "reasoning_output_tokens": reasoning_output_tokens,
        "total_tokens": input_tokens + output_tokens,
        **extra,
    }


def token_event(total: dict[str, Any], last: dict[str, Any]) -> dict[str, Any]:
    """テスト用token_count eventを作成する。"""

    return {
        "type": "event_msg",
        "payload": {
            "type": "token_count",
            "info": {"total_token_usage": total, "last_token_usage": last},
            "future_field": {"ignored": True},
        },
    }


def write_rollout(path: Path, events: list[dict[str, Any]]) -> Path:
    """JSONL fixtureを保存する。"""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(event, ensure_ascii=False) + "\n" for event in events),
        encoding="utf-8",
    )
    return path


def test_reads_cumulative_token_count_without_double_counting(tmp_path: Path) -> None:
    """複数の累積値を合計せず最後の累積値を使うことを確認する。"""

    path = write_rollout(
        tmp_path / "rollout.jsonl",
        [
            token_event(usage(100, 60, 10, 2, unknown=1), usage(100, 60, 10, 2)),
            token_event(usage(250, 180, 25, 6), usage(150, 120, 15, 4)),
            token_event(usage(250, 180, 25, 6), usage(150, 120, 15, 4)),
        ],
    )

    result = MEASUREMENT["read_token_usage"](path)

    assert result["status"] == "available"
    assert result["baseline"]["total_tokens"] == 0
    assert result["usage"] == usage(250, 180, 25, 6)


def test_resolves_codex_home_from_config_then_windows_profile(tmp_path: Path) -> None:
    """固定OS pathを使わずCODEX_HOMEとUSERPROFILEの優先順で解決する。"""

    configured = tmp_path / "configured"
    profile = tmp_path / "profile"

    assert MEASUREMENT["resolve_codex_home"](
        {"CODEX_HOME": str(configured), "USERPROFILE": str(profile)}
    ) == configured.resolve()
    assert MEASUREMENT["resolve_codex_home"](
        {"USERPROFILE": str(profile)}
    ) == (profile / ".codex").resolve()


def test_subtracts_inherited_parent_baseline(tmp_path: Path) -> None:
    """初回累積値から初回last値を引いた親由来baselineを除外する。"""

    path = write_rollout(
        tmp_path / "rollout.jsonl",
        [
            token_event(usage(120, 80, 15, 4), usage(20, 10, 5, 1)),
            token_event(usage(180, 130, 25, 7), usage(60, 50, 10, 3)),
        ],
    )

    result = MEASUREMENT["read_token_usage"](path)

    assert result["status"] == "available"
    assert result["baseline"] == usage(100, 70, 10, 3)
    assert result["usage"] == usage(80, 60, 15, 4)


def test_missing_required_usage_field_is_unavailable(tmp_path: Path) -> None:
    """計算必須fieldが欠落してもクラッシュせずunavailableにする。"""

    incomplete = usage(100, 80, 5)
    del incomplete["cached_input_tokens"]
    path = write_rollout(tmp_path / "rollout.jsonl", [token_event(incomplete, incomplete)])

    result = MEASUREMENT["read_token_usage"](path)

    assert result["status"] == "unavailable"
    assert "cached_input_tokens" in result["reason"]


def test_missing_reasoning_usage_does_not_block_credit_fields(tmp_path: Path) -> None:
    """optionalなreasoning field欠落をraw unavailableとして扱う。"""

    value = usage(100, 80, 5)
    del value["reasoning_output_tokens"]
    path = write_rollout(tmp_path / "rollout.jsonl", [token_event(value, value)])

    result = MEASUREMENT["read_token_usage"](path)

    assert result["status"] == "available"
    assert result["usage"]["reasoning_output_tokens"] == "unavailable"


def test_detects_cumulative_usage_decrease(tmp_path: Path) -> None:
    """finalがbaselineや前回累積値より小さい矛盾を検出する。"""

    path = write_rollout(
        tmp_path / "rollout.jsonl",
        [
            token_event(usage(120, 80, 15), usage(20, 10, 5)),
            token_event(usage(110, 70, 14), usage(10, 0, 4)),
        ],
    )

    result = MEASUREMENT["read_token_usage"](path)

    assert result["status"] == "unavailable"
    assert result["reason"] == "cumulative-usage-decreased"


def test_luna_credit_calculation_uses_uncached_input() -> None:
    """Lunaの例でcached inputを二重課金しないことを確認する。"""

    result = MEASUREMENT["calculate_credits"](
        usage(100_000, 80_000, 5_000, 4_000),
        "gpt-5.6-luna",
        RATE_CONFIG,
    )

    assert result["status"] == "available"
    assert result["credits"] == {
        "uncached_input": 0.1,
        "cached_input": 0.04,
        "output": 0.15,
        "total": 0.29,
    }


@pytest.mark.parametrize(
    ("model", "expected"),
    (
        ("gpt-5.6-luna", 0.29),
        ("gpt-5.6-terra", 2.9),
        ("gpt-5.6-sol", 5.3),
    ),
)
def test_credit_rate_is_selected_by_model(model: str, expected: float) -> None:
    """Luna、Terra、Solそれぞれのrateを適用する。"""

    result = MEASUREMENT["calculate_credits"](
        usage(100_000, 80_000, 5_000, 5_000), model, RATE_CONFIG
    )

    assert result["credits"]["total"] == expected


def test_reasoning_output_is_not_charged_twice() -> None:
    """reasoningはoutput内訳として保持しcreditへ別加算しない。"""

    without_reasoning = MEASUREMENT["calculate_credits"](
        usage(100_000, 80_000, 5_000, 0), "gpt-5.6-sol", RATE_CONFIG
    )
    with_reasoning = MEASUREMENT["calculate_credits"](
        usage(100_000, 80_000, 5_000, 5_000), "gpt-5.6-sol", RATE_CONFIG
    )

    assert with_reasoning["credits"] == without_reasoning["credits"]


def test_unknown_model_credit_is_unavailable() -> None:
    """未知modelへ近いrateを推測適用しない。"""

    result = MEASUREMENT["calculate_credits"](
        usage(100_000, 80_000, 5_000), "gpt-unknown", RATE_CONFIG
    )

    assert result["status"] == "unavailable"
    assert result["reason"] == "credit-rate-not-defined"


def test_measurement_matches_session_parent_agent_and_model(tmp_path: Path) -> None:
    """session IDだけでなく親、agent path、modelも対応付ける。"""

    session_id = "01a00000-0000-7000-8000-000000000001"
    parent_id = "01a00000-0000-7000-8000-000000000000"
    rollout = tmp_path / "sessions" / "2026" / "08" / "28" / f"rollout-test-{session_id}.jsonl"
    write_rollout(
        rollout,
        [
            {
                "type": "session_meta",
                "payload": {
                    "session_id": parent_id,
                    "id": session_id,
                    "parent_thread_id": parent_id,
                    "agent_path": "/root/quick_actor",
                },
            },
            {"type": "turn_context", "payload": {"model": "gpt-5.6-luna"}},
            token_event(usage(100_000, 80_000, 5_000, 1_000), usage(100_000, 80_000, 5_000, 1_000)),
        ],
    )

    result = MEASUREMENT["measure_session"](
        {
            "session_id": session_id,
            "parent_session_id": parent_id,
            "agent_path": "/root/quick_actor",
            "model": "gpt-5.6-luna",
        },
        RATE_CONFIG,
        tmp_path,
    )

    assert result["measurement"] == {
        "source": "codex-session-jsonl",
        "session_id": session_id,
        "rollout_file": rollout.name,
        "status": "available",
        "reason": None,
    }
    assert result["credits"]["total"] == 0.29


def test_measurement_rejects_parent_session_mismatch(tmp_path: Path) -> None:
    """同じsession IDでも親が異なるrolloutを対象にしない。"""

    session_id = "01a00000-0000-7000-8000-000000000002"
    rollout = tmp_path / "sessions" / "2026" / "08" / "28" / f"rollout-test-{session_id}.jsonl"
    write_rollout(
        rollout,
        [
            {
                "type": "session_meta",
                "payload": {
                    "id": session_id,
                    "parent_thread_id": "different-parent",
                    "agent_path": "/root/quick_actor",
                },
            },
            {"type": "turn_context", "payload": {"model": "gpt-5.6-luna"}},
            token_event(usage(10, 5, 1), usage(10, 5, 1)),
        ],
    )

    result = MEASUREMENT["measure_session"](
        {
            "session_id": session_id,
            "parent_session_id": "expected-parent",
            "agent_path": "/root/quick_actor",
            "model": "gpt-5.6-luna",
        },
        RATE_CONFIG,
        tmp_path,
    )

    assert result["usage_status"] == "unavailable"
    assert result["measurement"]["reason"] == "parent-session-mismatch"
