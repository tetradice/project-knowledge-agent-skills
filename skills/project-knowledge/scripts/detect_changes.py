#!/usr/bin/env python3
"""Gitまたはfile hashから更新候補を抽出する。"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path


IGNORED_PARTS = {".git", ".cache", "published", "project-knowledge"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("project_root", type=Path)
    parser.add_argument("--baseline")
    parser.add_argument("--snapshot", type=Path)
    parser.add_argument("--write-state", action="store_true")
    args = parser.parse_args()

    # Gitが利用できればcommitと未コミット差分を統合
    root = args.project_root.resolve()
    if is_git_repository(root):
        changed = git_changes(root, args.baseline)
        print(json.dumps({"mode": "git", "changed": changed}, ensure_ascii=False, indent=2))
        return 0

    # Gitがなければ内容hashのsnapshotと比較
    snapshot_path = args.snapshot or root / "project-knowledge" / ".cache" / "source-snapshot.json"
    current = build_snapshot(root, snapshot_path)
    previous = load_snapshot(snapshot_path)
    changed = sorted(path for path, digest in current.items() if previous.get(path) != digest)
    removed = sorted(path for path in previous if path not in current)
    if args.write_state:
        snapshot_path.parent.mkdir(parents=True, exist_ok=True)
        snapshot_path.write_text(json.dumps(current, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"mode": "hash", "changed": changed, "removed": removed}, ensure_ascii=False, indent=2))
    return 0


def is_git_repository(root: Path) -> bool:
    result = subprocess.run(
        ["git", "rev-parse", "--is-inside-work-tree"], cwd=root, capture_output=True, text=True, check=False
    )
    return result.returncode == 0 and result.stdout.strip() == "true"


def git_changes(root: Path, baseline: str | None) -> list[str]:
    # committed、staged、working tree、untrackedを収集
    commands = []
    if baseline:
        commands.append(["git", "diff", "--name-only", f"{baseline}..HEAD"])
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
    if not path.is_file():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except (json.JSONDecodeError, OSError):
        return {}


if __name__ == "__main__":
    raise SystemExit(main())
