#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["PyYAML>=6.0,<7"]
# ///

"""プロジェクトナレッジの安全で冪等な初期構造を作成する。"""

from __future__ import annotations

import argparse
import re
import shutil
from pathlib import Path

import yaml
from state import ensure_state

SKILL_ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = SKILL_ROOT / "templates"
MANAGED_START = "<!-- project-knowledge:start -->"
MANAGED_END = "<!-- project-knowledge:end -->"
FORMAT_NAME = "project-knowledge"
FORMAT_VERSION = "1.0"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("project_root", type=Path)
    args = parser.parse_args()

    # 初期化先を確定し、既存Bundleが現行形式であることを確認
    project_root = args.project_root.resolve()
    knowledge_root = project_root / "project-knowledge"
    docs_root = knowledge_root / "docs"
    policy_path = knowledge_root / "knowledge-policy.md"
    changes: list[str] = []
    format_error = validate_existing_bundle(knowledge_root)
    if format_error:
        print(f"Cannot initialize project-knowledge: {format_error}")
        return 1

    # 必要なディレクトリを作成
    for directory in (
        docs_root / "references" / "user-statements",
        docs_root / "references" / "interactions",
        knowledge_root / "published" / "markdown",
        knowledge_root / "published" / "html",
        knowledge_root / ".cache",
    ):
        directory.mkdir(parents=True, exist_ok=True)

    # 初期ファイルを既存内容を保持して配置
    files = {
        "knowledge-policy.md": policy_path,
        "state.yml": knowledge_root / "state.yml",
        "index.md": docs_root / "index.md",
        "log.md": docs_root / "log.md",
        "reference-index.md": docs_root / "references" / "index.md",
        "user-statements-index.md": docs_root / "references" / "user-statements" / "index.md",
        "interactions-index.md": docs_root / "references" / "interactions" / "index.md",
        "project.gitignore": knowledge_root / ".gitignore",
    }
    for template_name, destination in files.items():
        if not destination.exists():
            if template_name == "index.md":
                rendered = (TEMPLATES / template_name).read_text(encoding="utf-8").replace(
                    "{{project_name}}", project_root.name
                )
                destination.write_text(rendered, encoding="utf-8", newline="\n")
            else:
                shutil.copyfile(TEMPLATES / template_name, destination)
            changes.append(f"created: {destination.relative_to(project_root).as_posix()}")

    # 既存ignore設定を保持し、working copy固有stateだけを追加
    gitignore_path = knowledge_root / ".gitignore"
    if ensure_gitignore_entry(gitignore_path, "state.yml"):
        changes.append(f"updated: {gitignore_path.relative_to(project_root).as_posix()}")

    # 再構築可能なstateだけを対応schemaへ揃える
    state_path = knowledge_root / "state.yml"
    if ensure_state(state_path):
        changes.append(f"rebuilt: {state_path.relative_to(project_root).as_posix()}")

    # AGENTS.mdの管理ブロックを追加または最新版へ置換
    agents_path = project_root / "AGENTS.md"
    agents_change = update_agents_block(agents_path)
    if agents_change:
        changes.append(f"{agents_change}: AGENTS.md managed block")

    manifest = knowledge_root / "manifest.yml"
    if not manifest.exists():
        shutil.copyfile(TEMPLATES / "manifest.yml", manifest)
        changes.append(f"created: {manifest.relative_to(project_root).as_posix()}")

    print("Initialized project-knowledge")
    for change in changes:
        print(change)
    if not changes:
        print("no changes")
    return 0


def validate_existing_bundle(knowledge_root: Path) -> str | None:
    """既存Bundleが形式1.0として初期化可能か確認する。"""

    if not knowledge_root.exists() or not any(knowledge_root.iterdir()):
        return None

    manifest = knowledge_root / "manifest.yml"
    if not manifest.is_file():
        return "existing Bundle has no manifest.yml"
    try:
        data = yaml.safe_load(manifest.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError):
        return "manifest.yml is malformed"
    if not isinstance(data, dict) or data.get("format") != FORMAT_NAME:
        return "manifest.yml has an unsupported format"
    if data.get("format_version") != FORMAT_VERSION:
        return f"format version must be {FORMAT_VERSION}"
    return None


def update_agents_block(path: Path) -> str | None:
    current = path.read_text(encoding="utf-8") if path.exists() else ""
    block = (TEMPLATES / "agents-block.md").read_text(encoding="utf-8").strip()

    # 既存管理ブロックだけを置換し、利用者の指示は保持
    if MANAGED_START in current and MANAGED_END in current:
        pattern = re.compile(re.escape(MANAGED_START) + r".*?" + re.escape(MANAGED_END), re.DOTALL)
        updated = pattern.sub(block, current, count=1)
        if updated == current:
            return None
        path.write_text(updated, encoding="utf-8")
        return "updated"
    if MANAGED_START in current or MANAGED_END in current:
        return None

    separator = "\n\n" if current.strip() else ""
    path.write_text(current.rstrip() + separator + block + "\n", encoding="utf-8")
    return "created"


def ensure_gitignore_entry(path: Path, entry: str) -> bool:
    """既存行を保持して必要なignore entryを一度だけ追加する。"""

    current = path.read_text(encoding="utf-8") if path.exists() else ""
    if entry in {line.strip() for line in current.splitlines()}:
        return False
    separator = "" if not current or current.endswith(("\n", "\r")) else "\n"
    path.write_text(f"{current}{separator}{entry}\n", encoding="utf-8")
    return True


if __name__ == "__main__":
    raise SystemExit(main())
