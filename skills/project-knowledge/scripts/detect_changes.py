#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["PyYAML>=6.0,<7"]
# ///

"""Gitまたはfile hashから更新候補を抽出する。"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

from state import atomic_write_text, load_state, write_state

IGNORED_PARTS = {".git", ".cache", "published", "project-knowledge"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("project_root", type=Path)
    parser.add_argument(
        "--write-snapshot",
        action="store_true",
        help="hash snapshotを保存する",
    )
    parser.add_argument(
        "--write-baseline",
        action="store_true",
        help="Git HEADをstate.ymlのbaselineとして保存する",
    )
    args = parser.parse_args()

    # Gitが利用できればcommitと未コミット差分を統合
    root = args.project_root.resolve()
    state_path = root / "project-knowledge" / "state.yml"
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

    # Gitがなければ内容hashのsnapshotと比較
    snapshot_path = root / "project-knowledge" / ".cache" / "source-snapshot.json"
    current = build_snapshot(root, snapshot_path)
    previous = load_snapshot(snapshot_path)
    changed = sorted(path for path, digest in current.items() if previous.get(path) != digest)
    removed = sorted(path for path in previous if path not in current)
    if args.write_snapshot:
        atomic_write_text(snapshot_path, json.dumps(current, indent=2) + "\n")
    print(json.dumps({"mode": "hash", "changed": changed, "removed": removed}, ensure_ascii=False, indent=2))
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


def build_snapshot(root: Path, snapshot_path: Path | None = None) -> dict[str, str]:
    """非Git差分検出用の現在snapshotを作る。"""

    snapshot = {}
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        relative = path.relative_to(root)
        if any(part in IGNORED_PARTS for part in relative.parts):
            continue
        if snapshot_path is not None and path.resolve() == snapshot_path.resolve():
            continue
        snapshot[relative.as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return snapshot


def load_snapshot(path: Path) -> dict[str, str]:
    """壊れたsnapshotを空snapshotとして読み込む。"""

    if not path.is_file():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(value, dict) or any(
            not isinstance(key, str) or not isinstance(digest, str)
            for key, digest in value.items()
        ):
            return {}
        return value
    except (json.JSONDecodeError, OSError, UnicodeError):
        return {}


if __name__ == "__main__":
    raise SystemExit(main())
