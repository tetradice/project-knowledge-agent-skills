# /// script
# requires-python = ">=3.11"
# dependencies = ["PyYAML>=6.0,<7"]
# ///

"""Project Knowledgeの再構築可能なstateを読み書きする。"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Any

import yaml

STATE_SCHEMA_VERSION = 2
STATE_KEYS = {"state_schema_version", "git_baseline_commit"}


def load_state(path: Path) -> dict[str, Any] | None:
    """対応schemaのstateを読み、不正または非対応なら無効として返す。"""

    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError):
        return None
    if not isinstance(value, dict) or set(value) != STATE_KEYS:
        return None
    if value.get("state_schema_version") != STATE_SCHEMA_VERSION:
        return None
    baseline = value.get("git_baseline_commit")
    if baseline is not None and not isinstance(baseline, str):
        return None
    return value


def render_state(git_baseline_commit: str | None) -> str:
    """schema 2の最小stateを生成する。"""

    baseline = "null" if git_baseline_commit is None else git_baseline_commit
    return (
        f"state_schema_version: {STATE_SCHEMA_VERSION}\n"
        f"git_baseline_commit: {baseline}\n"
    )


def ensure_state(path: Path) -> bool:
    """欠落・破損・旧schemaのstateを初期状態へ再構築する。"""

    if load_state(path) is not None:
        return False
    atomic_write_text(path, render_state(None))
    return True


def write_state(path: Path, git_baseline_commit: str | None) -> None:
    """stateを一時ファイル経由で原子的に置き換える。"""

    atomic_write_text(path, render_state(git_baseline_commit))


def atomic_write_text(path: Path, text: str) -> None:
    """同じdirectory内の一時ファイルからtextを置き換える。"""

    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(text)
        temporary_path.replace(path)
    finally:
        temporary_path.unlink(missing_ok=True)
