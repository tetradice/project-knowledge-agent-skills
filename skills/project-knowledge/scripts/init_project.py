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

from migrate_project import (
    CURRENT_FORMAT_VERSION,
    LEGACY_FORMAT_VERSION,
    FormatError,
    apply_migration,
    detect_format,
    plan_migration,
)

SKILL_ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = SKILL_ROOT / "templates"
MANAGED_START = "<!-- project-knowledge:start -->"
MANAGED_END = "<!-- project-knowledge:end -->"
MIGRATION_HEADING = "## 旧scopeから移行した補足方針"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("project_root", type=Path)
    parser.add_argument("--empty", action="store_true", help="ナレッジ本文を作らず骨組みだけを作成")
    parser.add_argument(
        "--scope",
        action="append",
        metavar="TEXT",
        help=argparse.SUPPRESS,
    )
    args = parser.parse_args()

    # 初期化先とデータ形式を確定
    project_root = args.project_root.resolve()
    knowledge_root = project_root / "project-knowledge"
    docs_root = knowledge_root / "docs"
    policy_path = knowledge_root / "knowledge-policy.md"
    changes: list[str] = []

    try:
        format_version = detect_format(project_root)
    except FormatError as exc:
        # scope-only bundles predate format 0.1 and are handled by the existing
        # policy migration below. Other unknown layouts are never guessed.
        existing = (
            {path.name for path in knowledge_root.iterdir()}
            if knowledge_root.exists()
            else set()
        )
        if existing and existing <= {
            "scope.md",
            "scope.yml",
            "config.yml",
            "config.local.yml",
        }:
            format_version = None
        else:
            print(f"Cannot initialize project-knowledge: {exc}")
            return 1

    if format_version == LEGACY_FORMAT_VERSION:
        try:
            plan = plan_migration(project_root, CURRENT_FORMAT_VERSION)
            if plan.conflicts:
                print("Cannot migrate project-knowledge; existing files were preserved")
                for conflict in plan.conflicts:
                    print(f"conflict: {conflict}")
                return 1
            migrated = apply_migration(plan)
            changes.extend(
                f"migrated: {path.relative_to(project_root).as_posix()}"
                for path in migrated
            )
            format_version = CURRENT_FORMAT_VERSION
        except FormatError as exc:
            print(f"Cannot migrate project-knowledge: {exc}")
            return 1
    elif format_version not in {None, CURRENT_FORMAT_VERSION}:
        print(
            f"Cannot initialize unsupported format {format_version}; "
            "update the Project Knowledge skill"
        )
        return 1

    migrated_scopes = migrate_legacy_scopes(knowledge_root, policy_path)
    if migrated_scopes is None:
        print("Cannot safely migrate legacy scope; existing files were preserved")
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
        "config.yml": knowledge_root / "config.yml",
        "state.yml": knowledge_root / "state.yml",
        "index.md": docs_root / "index.md",
        "log.md": docs_root / "log.md",
        "reference-index.md": docs_root / "references" / "index.md",
        "user-statements-index.md": docs_root / "references" / "user-statements" / "index.md",
        "interactions-index.md": docs_root / "references" / "interactions" / "index.md",
        "project.gitignore": knowledge_root / ".gitignore",
    }
    changes.extend(
        f"migrated: project-knowledge/{path.name} -> project-knowledge/knowledge-policy.md"
        for path in migrated_scopes
    )
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

    # 旧boolean設定をlearning modeへ移行
    for config_name in ("config.yml", "config.local.yml"):
        config_path = knowledge_root / config_name
        migrated_mode = migrate_legacy_learning_config(config_path)
        if migrated_mode:
            changes.append(f"migrated: project-knowledge/{config_name} -> learning.mode: {migrated_mode}")

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
    if args.scope:
        print("warning: --scope is deprecated; values are initial topics, not a persistent boundary")
    if args.empty:
        print("empty initialization requested; no ナレッジ pages were generated")
    if not changes:
        print("no changes")
    return 0


def migrate_legacy_scopes(knowledge_root: Path, policy_path: Path) -> list[Path] | None:
    sources = [path for path in (knowledge_root / "scope.md", knowledge_root / "scope.yml") if path.exists()]
    if not sources:
        return []
    if len(sources) > 1:
        return None

    # 既知の旧形式だけをPolicyへ意味的に移し、未知形式は保持
    source = sources[0]
    text = source.read_text(encoding="utf-8")
    parsed = parse_legacy_scope_markdown(text) if source.suffix == ".md" else parse_legacy_scope_yaml(text)
    if parsed is None:
        return None

    included, excluded, notes = parsed
    base = (
        policy_path.read_text(encoding="utf-8")
        if policy_path.exists()
        else (TEMPLATES / "knowledge-policy.md").read_text(encoding="utf-8")
    )
    if MIGRATION_HEADING not in base:
        policy_path.parent.mkdir(parents=True, exist_ok=True)
        policy_path.write_text(
            append_scope_migration(base, included, excluded, notes),
            encoding="utf-8",
            newline="\n",
        )
    source.unlink()
    return [source]


def parse_legacy_scope_markdown(text: str) -> tuple[list[str], list[str], list[str]] | None:
    # 旧scope.mdの既知frontmatterと見出しだけを受け付ける
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None
    frontmatter: dict[str, str] = {}
    for line in parts[1].splitlines():
        if not line.strip():
            continue
        match = re.fullmatch(r"([A-Za-z_-]+):\s*(.+)", line.strip())
        if not match or match.group(1) not in {"version", "status", "expansion"}:
            return None
        frontmatter[match.group(1)] = unquote(match.group(2))
    if frontmatter.get("version") != "1":
        return None
    included: list[str] = []
    excluded: list[str] = []
    notes: list[str] = []
    section = ""
    allowed_sections = {"対象", "原則として対象外", "対象外", "補足"}
    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if stripped.startswith("## "):
            section = stripped[3:].strip()
            if section not in allowed_sections:
                return None
            continue
        if stripped.startswith("- "):
            value = stripped[2:].strip()
            if section == "対象":
                included.append(value)
            elif section in {"原則として対象外", "対象外"}:
                excluded.append(value)
            elif section == "補足":
                notes.append(value)
            else:
                return None
        elif section == "補足" and stripped and not stripped.startswith(("#", "---")):
            notes.append(stripped)
    return included, excluded, notes


def parse_legacy_scope_yaml(text: str) -> tuple[list[str], list[str], list[str]] | None:
    included: list[str] = []
    excluded: list[str] = []
    section = ""
    topic: dict[str, str] | None = None

    # include/exclude/topicsから意味を保持できる文字列だけを抽出
    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if not line.startswith((" ", "\t")):
            if topic:
                included.append(topic.get("description") or topic.get("id", ""))
                topic = None
            match = re.fullmatch(r"([A-Za-z_-]+):\s*(.*)", stripped)
            if not match or match.group(1) not in {"version", "include", "exclude", "topics"}:
                return None
            section, inline = match.groups()
            if section == "version":
                if unquote(inline) != "1":
                    return None
            elif inline not in {"", "[]"}:
                return None
            continue
        if section in {"include", "exclude"}:
            match = re.fullmatch(r"-\s+(.+)", stripped)
            if not match:
                return None
            target = included if section == "include" else excluded
            target.append(unquote(match.group(1)))
            continue
        if section == "topics":
            item = re.fullmatch(r"-\s+(id|description):\s*(.+)", stripped)
            field = re.fullmatch(r"(id|description):\s*(.+)", stripped)
            if item:
                if topic:
                    included.append(topic.get("description") or topic.get("id", ""))
                topic = {item.group(1): unquote(item.group(2))}
            elif field and topic is not None:
                topic[field.group(1)] = unquote(field.group(2))
            else:
                return None
            continue
        return None

    if topic:
        included.append(topic.get("description") or topic.get("id", ""))
    if any(not item for item in included + excluded):
        return None
    return included, excluded, []


def append_scope_migration(base: str, included: list[str], excluded: list[str], notes: list[str]) -> str:
    # 対象指定をallow-list化せず、価値判断の補足へ変換
    notes = [note for note in notes if "scopeとは別に設計する" not in note]
    lines = [
        base.rstrip(),
        "",
        MIGRATION_HEADING,
        "",
        "旧scopeの対象指定はナレッジ領域を限定するものではなく、積極的な保存候補として扱う。",
    ]
    if included:
        lines.extend(["", "### 積極的な保存候補", "", *(f"- {item}" for item in included)])
    if excluded:
        lines.extend(["", "### 保存しない補足", "", *(f"- {item}" for item in excluded)])
    if notes:
        lines.extend(["", "### 移行した補足", "", *(f"- {item}" for item in notes)])
    return "\n".join(lines) + "\n"


def migrate_legacy_learning_config(path: Path) -> str | None:
    if not path.exists():
        return None

    # 旧update.automatic_after_workを新しいlearning.modeへ変換
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    try:
        update_start = lines.index("update:")
    except ValueError:
        return None

    update_end = next(
        (
            index
            for index in range(update_start + 1, len(lines))
            if lines[index] and not lines[index].startswith((" ", "\t", "#"))
        ),
        len(lines),
    )
    setting_index = next(
        (
            index
            for index in range(update_start + 1, update_end)
            if re.fullmatch(r"[ \t]+automatic_after_work:\s*(true|false)\s*", lines[index])
        ),
        None,
    )
    if setting_index is None:
        return None
    enabled = lines[setting_index].split(":", 1)[1].strip() == "true"
    mode = "opportunistic" if enabled else "manual"

    del lines[setting_index]
    remaining_update = lines[update_start + 1 : update_end - 1]
    if not any(line.strip() for line in remaining_update):
        del lines[update_start]

    # 既存learning.modeを優先し、未設定の場合だけ移行値を追加
    learning_start = next((index for index, line in enumerate(lines) if line == "learning:"), None)
    if learning_start is None:
        if lines and lines[-1]:
            lines.append("")
        lines.extend(["learning:", f"  mode: {mode}"])
    else:
        learning_end = next(
            (
                index
                for index in range(learning_start + 1, len(lines))
                if lines[index] and not lines[index].startswith((" ", "\t", "#"))
            ),
            len(lines),
        )
        existing = next(
            (
                line.split(":", 1)[1].strip()
                for line in lines[learning_start + 1 : learning_end]
                if re.fullmatch(r"[ \t]+mode:\s*\w+\s*", line)
            ),
            None,
        )
        if existing:
            mode = existing
        else:
            lines.insert(learning_start + 1, f"  mode: {mode}")

    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8", newline="\n")
    return mode


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


def unquote(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


if __name__ == "__main__":
    raise SystemExit(main())
