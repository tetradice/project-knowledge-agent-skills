#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["PyYAML>=6.0,<7"]
# ///

"""Gitから更新候補を抽出する。非Git環境では差分を取得しない。"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from project_config import ConfigError, load_config, select_layer
from state import load_state, write_state


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("project_root", type=Path)
    parser.add_argument("--layer")
    parser.add_argument(
        "--write-snapshot",
        action="store_true",
        help="後方互換のため受け付けるが、非Git環境では何もしない",
    )
    parser.add_argument(
        "--write-baseline",
        action="store_true",
        help="Git HEADをstate.ymlのbaselineとして保存する",
    )
    args = parser.parse_args()

    # Git管理下でcommitと未コミット差分を統合
    root = args.project_root.resolve()
    try:
        config = load_config(root)
        layer = select_layer(config, args.layer, write=args.write_snapshot or args.write_baseline)
        knowledge_root = Path(layer["resolved_path"])
    except ConfigError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    state_path = knowledge_root / "state.yml"
    if is_git_repository(root):
        state = load_state(state_path)
        configured_baseline = state.get("git_baseline_commit") if state else None
        baseline = valid_git_baseline(root, configured_baseline)
        changed = git_changes(root, baseline)
        if args.write_baseline:
            head = git_head(root)
            if head is None:
                print("Cannot checkpoint Git baseline because HEAD is unavailable", file=sys.stderr)
                return 2
            write_state(state_path, head)
        print(
            json.dumps(
                {
                    "mode": "git",
                    "baseline": baseline,
                    "full_scan": baseline is None,
                    "changed": changed,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    # Git管理外では大容量ファイルを含む差分取得やhash計算を行わない
    print(json.dumps({"mode": "non-git", "changed": [], "removed": []}, ensure_ascii=False, indent=2))
    return 0


def is_git_repository(root: Path) -> bool:
    result = subprocess.run(
        ["git", "rev-parse", "--is-inside-work-tree"], cwd=root, capture_output=True, text=True, check=False
    )
    return result.returncode == 0 and result.stdout.strip() == "true"


def valid_git_baseline(root: Path, baseline: str | None) -> str | None:
    """完全object IDであり、現在HEADの祖先であるbaselineだけを返す。"""

    if not baseline:
        return None

    # commitとして解決し、短縮object IDを除外
    resolved = subprocess.run(
        ["git", "rev-parse", "--verify", f"{baseline}^{{commit}}"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    object_id = resolved.stdout.strip()
    if resolved.returncode != 0 or baseline.lower() != object_id.lower():
        return None

    # 現在HEADへつながらないbaselineはbranch固有状態として破棄
    ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", object_id, "HEAD"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    return object_id if ancestor.returncode == 0 else None


def git_head(root: Path) -> str | None:
    """現在HEADの完全object IDを返す。"""

    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else None


def git_changes(root: Path, baseline: str | None) -> list[str]:
    """commit済み差分とcheckpointしない未commit差分を統合する。"""

    # committed、staged、working tree、untrackedを収集
    commands: list[list[str]] = []
    if baseline:
        commands.append(["git", "diff", "--name-only", f"{baseline}..HEAD"])
    else:
        commands.append(["git", "ls-files"])
    commands.extend(
        [
            ["git", "diff", "--name-only", "--cached"],
            ["git", "diff", "--name-only"],
            ["git", "ls-files", "--others", "--exclude-standard"],
        ]
    )
    paths: set[str] = set()
    for command in commands:
        result = subprocess.run(command, cwd=root, capture_output=True, text=True, check=False)
        if result.returncode == 0:
            paths.update(line for line in result.stdout.splitlines() if line)
    return sorted(paths)


if __name__ == "__main__":
    raise SystemExit(main())
