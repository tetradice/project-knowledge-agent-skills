# /// script
# requires-python = ">=3.11"
# dependencies = ["PyYAML>=6.0,<7"]
# ///

"""Detect and migrate Project Knowledge data formats."""

from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

FORMAT_NAME = "project-knowledge"
CURRENT_FORMAT_VERSION = "0.2"
LEGACY_FORMAT_VERSION = "0.1"
MANIFEST_TEXT = 'format: project-knowledge\nformat_version: "0.2"\n'
LEGACY_MARKERS = (
    Path("docs/index.md"),
    Path("docs/log.md"),
    Path("config.yml"),
    Path("state.yml"),
)
SOURCE_TYPE_MAP = {
    "user-assertion": "user-statement",
    "capture": "user-statement",
    "conversation-derived": "interaction-record",
    "memo": "interaction-record",
    "source-code": "project-artifact",
    "config": "project-artifact",
    "schema": "project-artifact",
    "existing-knowledge": "project-artifact",
    "external-reference": "reference-document",
}
DATA_FORMAT_REGISTRY = {
    "0.1": "references/data-formats/0.1.md",
    "0.2": "references/data-formats/0.2.md",
}
MIGRATION_REGISTRY = {
    ("0.1", "0.2"): "references/migrations/0.1-to-0.2.md",
}


class FormatError(RuntimeError):
    """Raised when a Project Knowledge format cannot be handled safely."""


@dataclass(frozen=True)
class FilePlan:
    source: Path
    destination: Path
    content: bytes


@dataclass(frozen=True)
class MigrationPlan:
    root: Path
    source_version: str
    target_version: str
    files: tuple[FilePlan, ...]
    conflicts: tuple[str, ...]

    @property
    def changed_files(self) -> tuple[FilePlan, ...]:
        return tuple(
            item
            for item in self.files
            if item.source != item.destination
            or not item.destination.exists()
            or item.destination.read_bytes() != item.content
        )


def knowledge_root(project_root: Path | str) -> Path:
    candidate = Path(project_root).resolve()
    if candidate.name == "project-knowledge":
        return candidate
    return candidate / "project-knowledge"


def _load_mapping(path: Path) -> dict[str, Any]:
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        raise FormatError(f"malformed YAML: {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise FormatError(f"expected a YAML mapping: {path}")
    return value


def detect_format(project_root: Path | str) -> str | None:
    """Return a supported/declared format version, or None for a new bundle."""

    root = knowledge_root(project_root)
    manifest = root / "manifest.yml"
    if manifest.exists():
        data = _load_mapping(manifest)
        if data.get("format") != FORMAT_NAME:
            raise FormatError(
                f"unsupported manifest format: {data.get('format')!r}; expected {FORMAT_NAME!r}"
            )
        version = data.get("format_version")
        if not isinstance(version, str) or not re.fullmatch(r"\d+\.\d+", version):
            raise FormatError("manifest format_version must be a quoted MAJOR.MINOR string")
        return version

    if root.exists() and all((root / marker).is_file() for marker in LEGACY_MARKERS):
        return LEGACY_FORMAT_VERSION
    if not root.exists() or not any(root.iterdir()):
        return None
    raise FormatError(
        "manifest is missing and the directory does not match the known 0.1 structure"
    )


def require_supported_read(project_root: Path | str) -> str:
    version = detect_format(project_root)
    if version not in {LEGACY_FORMAT_VERSION, CURRENT_FORMAT_VERSION}:
        if version is None:
            raise FormatError("Project Knowledge is not initialized")
        raise FormatError(
            f"format {version} is not supported; update the Project Knowledge skill"
        )
    return version


def _split_frontmatter(text: str) -> tuple[dict[str, Any] | None, str]:
    normalized = text.replace("\r\n", "\n")
    if not normalized.startswith("---\n"):
        return None, normalized
    end = normalized.find("\n---\n", 4)
    if end < 0:
        raise FormatError("unterminated YAML frontmatter")
    raw = normalized[4:end]
    try:
        metadata = yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        raise FormatError(f"malformed YAML frontmatter: {exc}") from exc
    if metadata is None:
        metadata = {}
    if not isinstance(metadata, dict):
        raise FormatError("frontmatter must be a YAML mapping")
    return metadata, normalized[end + 5 :]


def _dump_frontmatter(metadata: dict[str, Any], body: str) -> str:
    frontmatter = yaml.safe_dump(
        metadata,
        allow_unicode=True,
        sort_keys=False,
        default_flow_style=False,
    ).rstrip()
    return f"---\n{frontmatter}\n---\n{body.lstrip()}"


def _convert_metadata(value: Any) -> Any:
    if isinstance(value, list):
        return [_convert_metadata(item) for item in value]
    if not isinstance(value, dict):
        return value

    converted: dict[str, Any] = {}
    for key, item in value.items():
        if key in {"pk_authority", "pk_trust"}:
            continue
        new_key = "pk_source_type" if key == "pk_source_kind" else key
        new_value = _convert_metadata(item)
        if new_key == "pk_source_type" and isinstance(new_value, str):
            new_value = SOURCE_TYPE_MAP.get(new_value, new_value)
        converted[new_key] = new_value
    return converted


def _normalize_event_actors(metadata: dict[str, Any]) -> None:
    legacy_skills = {
        "project-knowledge",
        "project-knowledge-fast-ask",
        "project-knowledge-publish",
        "project-knowledge-verify",
        "project-knowledge-audit",
    }
    for field in ("generated", "verified"):
        value = metadata.get(field)
        events = value if isinstance(value, list) else [value]
        for event in events:
            if isinstance(event, dict) and event.get("by") in legacy_skills:
                event["by"] = f"{event['by']}/0.1.0"


def _fill_source_types(metadata: dict[str, Any]) -> None:
    sources = metadata.get("sources")
    if not isinstance(sources, list):
        return
    for source in sources:
        if not isinstance(source, dict) or source.get("pk_source_type"):
            continue
        resource = source.get("resource")
        if not isinstance(resource, str):
            continue
        normalized = resource.replace("\\", "/")
        if "references/captures/" in normalized or "references/user-statements/" in normalized:
            source["pk_source_type"] = "user-statement"
        elif "references/memos/" in normalized or "references/interactions/" in normalized:
            source["pk_source_type"] = "interaction-record"
        elif re.match(r"^(?:https?://|urn:)", normalized):
            source["pk_source_type"] = "reference-document"
        else:
            source["pk_source_type"] = "project-artifact"


def _replace_legacy_paths(text: str) -> str:
    replacements = (
        ("references/captures/", "references/user-statements/"),
        ("references/memos/", "references/interactions/"),
        ("captures/", "user-statements/"),
        ("memos/", "interactions/"),
    )
    for old, new in replacements:
        text = text.replace(old, new)
    return text


def _is_raw_reference(relative: Path) -> bool:
    parts = relative.as_posix().split("/")
    return (
        len(parts) >= 4
        and parts[:2] == ["docs", "references"]
        and parts[2] in {"captures", "memos", "user-statements", "interactions"}
        and relative.name not in {"index.md", "log.md"}
    )


def _source_type_for_path(relative: Path) -> str:
    parts = relative.as_posix().split("/")
    directory = parts[2] if len(parts) > 2 else ""
    if directory in {"captures", "user-statements"}:
        return "user-statement"
    return "interaction-record"


def _transform_markdown(text: str, relative: Path) -> str:
    text = _replace_legacy_paths(text)
    metadata, body = _split_frontmatter(text)
    is_root_index = relative == Path("docs/index.md")
    is_reserved = relative.name in {"index.md", "log.md"}

    if relative.name == "log.md":
        lines: list[str] = []
        for line in body.splitlines():
            match = re.fullmatch(r"## (\d{4}-\d{2}-\d{2})\s+[—-]\s+(.+)", line)
            if match:
                lines.extend((f"## {match.group(1)}", "", f"### {match.group(2)}"))
            else:
                lines.append(line)
        body = "\n".join(lines).rstrip() + "\n"

    if is_root_index:
        return f'---\nokf_version: "0.2"\n---\n{body.lstrip()}'
    if is_reserved:
        return body.lstrip()

    converted = _convert_metadata(metadata or {})
    _normalize_event_actors(converted)
    _fill_source_types(converted)
    if _is_raw_reference(relative):
        converted["type"] = "Reference"
        converted["pk_source_type"] = _source_type_for_path(relative)
        converted.pop("category", None)
        converted.pop("derivation", None)
    elif relative.parts and relative.parts[0] == "docs":
        converted.setdefault("type", "Knowledge")
        if "category" not in converted or "derivation" not in converted:
            converted["pk_legacy_unclassified"] = True
    if converted or metadata is not None:
        return _dump_frontmatter(converted, body)
    return text


def _transform_yaml(text: str, relative: Path) -> str:
    try:
        original = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise FormatError(f"malformed YAML in {relative}: {exc}") from exc
    if original is None:
        original = {}
    if not isinstance(original, dict):
        raise FormatError(f"expected a YAML mapping in {relative}")

    had_final_newline = text.endswith(("\n", "\r"))
    lines = _replace_legacy_paths(text).splitlines()
    rewritten: list[str] = []
    for line in lines:
        key_match = re.match(r"^(\s*)(pk_source_kind|pk_authority|pk_trust):(.*)$", line)
        if not key_match:
            rewritten.append(line)
            continue
        indent, key, raw_value = key_match.groups()
        if key in {"pk_authority", "pk_trust"}:
            continue
        value_text, separator, comment = raw_value.partition("#")
        stripped = value_text.strip()
        quote = stripped[0] if len(stripped) >= 2 and stripped[0] == stripped[-1] and stripped[0] in {'"', "'"} else ""
        value = stripped[1:-1] if quote else stripped
        value = SOURCE_TYPE_MAP.get(value, value)
        suffix = f" #{comment}" if separator else ""
        rewritten.append(f"{indent}pk_source_type: {quote}{value}{quote}{suffix}")

    if relative in {Path("config.yml"), Path("config.local.yml")}:
        rewritten = _remove_legacy_memo_setting(rewritten)
    if relative == Path("state.yml"):
        has_schema_version = any(
            re.match(r"^state_schema_version\s*:", line) for line in rewritten
        )
        migrated_state: list[str] = []
        for line in rewritten:
            if re.match(r"^version\s*:", line):
                if not has_schema_version:
                    line = re.sub(r"^version(\s*:)", r"state_schema_version\1", line)
                    has_schema_version = True
                else:
                    continue
            migrated_state.append(line)
        if not has_schema_version:
            migrated_state.insert(0, "state_schema_version: 1")
        rewritten = migrated_state

    transformed = "\n".join(rewritten) + ("\n" if had_final_newline else "")
    try:
        checked = yaml.safe_load(transformed)
    except yaml.YAMLError as exc:
        raise FormatError(f"migration produced malformed YAML in {relative}: {exc}") from exc
    if checked is None:
        checked = {}
    if not isinstance(checked, dict):
        raise FormatError(f"migration produced a non-mapping in {relative}")
    return transformed


def _remove_legacy_memo_setting(lines: list[str]) -> list[str]:
    try:
        start = next(
            index
            for index, line in enumerate(lines)
            if re.match(r"^memo\s*:\s*(?:#.*)?$", line)
        )
    except StopIteration:
        return lines
    end = next(
        (
            index
            for index in range(start + 1, len(lines))
            if lines[index].strip()
            and not lines[index].lstrip().startswith("#")
            and not lines[index].startswith((" ", "\t"))
        ),
        len(lines),
    )
    block = lines[start + 1 : end]
    filtered = [
        line
        for line in block
        if not re.match(r"^[ \t]+require_approval_for_trust\s*:", line)
    ]
    has_values = any(
        line.strip() and not line.lstrip().startswith("#") for line in filtered
    )
    replacement = ([lines[start]] if has_values else []) + filtered
    return lines[:start] + replacement + lines[end:]


def _destination(relative: Path) -> Path:
    parts = list(relative.parts)
    if len(parts) >= 3 and parts[:2] == ["docs", "references"]:
        if parts[2] == "captures":
            parts[2] = "user-statements"
        elif parts[2] == "memos":
            parts[2] = "interactions"
    return Path(*parts)


def _transform(path: Path, relative: Path) -> bytes:
    raw = path.read_bytes()
    if path.suffix.lower() not in {".md", ".yml", ".yaml"}:
        return raw
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise FormatError(f"expected UTF-8 text: {path}") from exc
    destination = _destination(relative)
    if path.suffix.lower() == ".md":
        transformed = _transform_markdown(text, destination)
    else:
        transformed = _transform_yaml(text, destination)
    return transformed.encode("utf-8")


def plan_migration(project_root: Path | str, target: str = CURRENT_FORMAT_VERSION) -> MigrationPlan:
    root = knowledge_root(project_root)
    version = detect_format(root)
    if version is None:
        raise FormatError("Project Knowledge is not initialized")
    if version == CURRENT_FORMAT_VERSION:
        if target != CURRENT_FORMAT_VERSION:
            raise FormatError(f"downgrade from {version} to {target} is not supported")
        return MigrationPlan(root, version, target, (), ())
    if (version, target) not in MIGRATION_REGISTRY:
        if version not in DATA_FORMAT_REGISTRY:
            raise FormatError(
                f"format {version} is not supported; update the Project Knowledge skill"
            )
        raise FormatError(f"no migration chain from {version} to target {target}")
    if version != LEGACY_FORMAT_VERSION:
        raise FormatError(
            f"format {version} is not supported; update the Project Knowledge skill"
        )

    groups: dict[Path, list[FilePlan]] = defaultdict(list)
    for source in sorted(path for path in root.rglob("*") if path.is_file()):
        relative = source.relative_to(root)
        if (
            source.name == "manifest.yml"
            or relative.parts[0] in {".cache", "published"}
        ):
            continue
        destination = root / _destination(relative)
        groups[destination].append(FilePlan(source, destination, _transform(source, relative)))

    conflicts: list[str] = []
    files: list[FilePlan] = []
    for destination, candidates in sorted(groups.items(), key=lambda item: str(item[0])):
        expected = {candidate.content for candidate in candidates}
        if len(expected) > 1:
            conflicts.append(
                f"different content maps to {destination}: "
                + ", ".join(str(candidate.source) for candidate in candidates)
            )
            continue
        content = next(iter(expected))
        files.extend(
            FilePlan(candidate.source, destination, content) for candidate in candidates
        )

    return MigrationPlan(root, version, target, tuple(files), tuple(conflicts))


def _post_check(root: Path) -> None:
    legacy_dirs = (
        root / "docs/references/captures",
        root / "docs/references/memos",
    )
    for directory in legacy_dirs:
        if directory.exists() and any(directory.rglob("*")):
            raise FormatError(f"legacy directory still contains files: {directory}")
    state = _load_mapping(root / "state.yml")
    if "state_schema_version" not in state or "version" in state:
        raise FormatError("state.yml was not migrated to state_schema_version")
    config = _load_mapping(root / "config.yml")
    memo = config.get("memo")
    if isinstance(memo, dict) and "require_approval_for_trust" in memo:
        raise FormatError("legacy memo.require_approval_for_trust remains")

    docs = root / "docs"
    root_index = docs / "index.md"
    if not root_index.read_text(encoding="utf-8").startswith(
        '---\nokf_version: "0.2"\n---\n'
    ):
        raise FormatError("docs/index.md is not an OKF v0.2 root index")

    legacy_tokens = ("pk_source_kind:", "pk_authority:", "pk_trust:")
    legacy_paths = ("references/captures/", "references/memos/")
    for path in sorted(docs.rglob("*.md")):
        text = path.read_text(encoding="utf-8")
        relative = path.relative_to(root)
        metadata, body = _split_frontmatter(text)
        if path != root_index and path.name in {"index.md", "log.md"} and metadata is not None:
            raise FormatError(f"reserved file still has frontmatter: {relative}")
        if path.name == "log.md":
            for line in body.splitlines():
                if line.startswith("## ") and not re.fullmatch(r"## \d{4}-\d{2}-\d{2}", line):
                    raise FormatError(f"invalid log heading after migration: {relative}: {line}")
        if path.name not in {"index.md", "log.md"}:
            if metadata is None or not isinstance(metadata.get("type"), str):
                raise FormatError(f"Concept is missing type after migration: {relative}")
            sources = metadata.get("sources", [])
            if isinstance(sources, list):
                for source in sources:
                    if isinstance(source, dict) and source.get("pk_source_type") is None:
                        raise FormatError(
                            f"source is missing pk_source_type after migration: {relative}"
                        )
        metadata_text = yaml.safe_dump(metadata or {}, sort_keys=False)
        if any(token in metadata_text for token in legacy_tokens) or any(
            legacy_path in text for legacy_path in legacy_paths
        ):
            raise FormatError(f"legacy metadata or path remains: {relative}")


def apply_migration(plan: MigrationPlan) -> tuple[Path, ...]:
    if plan.conflicts:
        raise FormatError("migration has conflicts; no files were changed")
    if plan.source_version == plan.target_version:
        return ()

    groups: dict[Path, list[FilePlan]] = defaultdict(list)
    for item in plan.files:
        groups[item.destination].append(item)

    changed: list[Path] = []
    for destination, candidates in sorted(groups.items(), key=lambda item: str(item[0])):
        content = candidates[0].content
        if not destination.exists() or destination.read_bytes() != content:
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(content)
            changed.append(destination)

    for item in sorted(plan.files, key=lambda value: len(value.source.parts), reverse=True):
        if item.source != item.destination and item.source.exists():
            item.source.unlink()

    for directory in (
        plan.root / "docs/references/captures",
        plan.root / "docs/references/memos",
    ):
        if directory.exists():
            for candidate in sorted(directory.rglob("*"), key=lambda path: len(path.parts), reverse=True):
                if candidate.is_dir() and not any(candidate.iterdir()):
                    candidate.rmdir()
            if not any(directory.iterdir()):
                directory.rmdir()

    _post_check(plan.root)
    manifest = plan.root / "manifest.yml"
    manifest.write_text(MANIFEST_TEXT, encoding="utf-8", newline="\n")
    changed.append(manifest)
    return tuple(changed)


def migrate_project(
    project_root: Path | str,
    target: str = CURRENT_FORMAT_VERSION,
    check: bool = False,
) -> MigrationPlan:
    plan = plan_migration(project_root, target)
    if not check:
        apply_migration(plan)
    return plan


def _print_plan(plan: MigrationPlan, check: bool) -> None:
    print(f"migration chain: {plan.source_version} -> {plan.target_version}")
    if plan.source_version == plan.target_version:
        print("already at target; no changes")
        return
    print(f"mode: {'check' if check else 'apply'}")
    print(f"planned file operations: {len(plan.changed_files)}")
    for item in plan.changed_files:
        action = "move" if item.source != item.destination else "update"
        print(f"  {action}: {item.source.relative_to(plan.root)} -> {item.destination.relative_to(plan.root)}")
    if plan.conflicts:
        print("conflicts:")
        for conflict in plan.conflicts:
            print(f"  - {conflict}")
    else:
        print("conflicts: none")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_root", type=Path)
    parser.add_argument("--target", default=CURRENT_FORMAT_VERSION)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    try:
        plan = plan_migration(args.project_root, args.target)
        _print_plan(plan, args.check)
        if plan.conflicts:
            return 2
        if not args.check:
            changed = apply_migration(plan)
            print(f"changed files: {len(changed)}")
        return 0
    except FormatError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
