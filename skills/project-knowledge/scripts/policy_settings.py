# /// script
# requires-python = ">=3.11"
# dependencies = ["PyYAML>=6.0,<7"]
# ///

"""Read and update Project Knowledge settings in Policy frontmatter."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

LEARNING_MODES = {"manual", "opportunistic", "aggressive"}


class PolicySettingsError(RuntimeError):
    """Raised when Policy settings cannot be handled safely."""


@dataclass(frozen=True)
class PolicySettings:
    """Knowledge Policyに保存された設定。"""

    human_readable: bool
    learning_mode: str


@dataclass(frozen=True)
class PolicyDocument:
    """Policy text split without changing its Markdown body."""

    newline: str
    frontmatter: str | None
    body: str


def _split_policy(text: str) -> PolicyDocument:
    """Split Policy frontmatter from the exact Markdown body."""

    newline = "\r\n" if "\r\n" in text else "\n"
    if not text.startswith(f"---{newline}"):
        return PolicyDocument(newline, None, text)

    closing = f"{newline}---{newline}"
    end = text.find(closing, len(f"---{newline}"))
    if end < 0:
        raise PolicySettingsError("unterminated YAML frontmatter")
    frontmatter = text[len(f"---{newline}") : end]
    return PolicyDocument(newline, frontmatter, text[end + len(closing) :])


def _load_frontmatter(raw: str | None) -> dict[str, Any]:
    """Parse frontmatter as a mapping without guessing malformed values."""

    if raw is None:
        raise PolicySettingsError("YAML frontmatter is required")
    try:
        metadata = yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        raise PolicySettingsError(f"malformed YAML frontmatter: {exc}") from exc
    if metadata is None:
        raise PolicySettingsError("frontmatter must be a YAML mapping")
    if not isinstance(metadata, dict):
        raise PolicySettingsError("frontmatter must be a YAML mapping")
    return metadata


def _mapping(metadata: dict[str, Any], key: str) -> dict[str, Any]:
    """Return an optional settings section after validating its type."""

    value = metadata.get(key)
    if not isinstance(value, dict):
        raise PolicySettingsError(f"{key} must be a YAML mapping")
    return value


def resolve_policy_settings(text: str) -> PolicySettings:
    """Policy frontmatterの必須設定を読み取る。"""

    document = _split_policy(text)
    metadata = _load_frontmatter(document.frontmatter)
    knowledge = _mapping(metadata, "knowledge")
    learning = _mapping(metadata, "learning")

    # 既知設定の型と値を検証
    human_readable = knowledge.get("human_readable")
    if not isinstance(human_readable, bool):
        raise PolicySettingsError("knowledge.human_readable must be a boolean")
    learning_mode = learning.get("mode")
    if not isinstance(learning_mode, str):
        raise PolicySettingsError("learning.mode must be a string")
    if learning_mode not in LEARNING_MODES:
        raise PolicySettingsError(f"unknown learning.mode: {learning_mode!r}")
    return PolicySettings(human_readable, learning_mode)


def _replace_nested_scalar(
    frontmatter: str,
    newline: str,
    section: str,
    key: str,
    value: str,
) -> str:
    """Replace or insert one scalar while preserving unrelated YAML text."""

    lines = frontmatter.splitlines(keepends=True)
    section_index = next(
        (index for index, line in enumerate(lines) if re.fullmatch(rf"{re.escape(section)}:\s*(?:#.*)?(?:\r?\n)?", line)),
        None,
    )
    if section_index is None:
        separator = "" if not lines or lines[-1].endswith(("\n", "\r")) else newline
        return frontmatter + separator + f"{section}:{newline}  {key}: {value}{newline}"

    section_end = next(
        (
            index
            for index in range(section_index + 1, len(lines))
            if lines[index].strip()
            and not lines[index].lstrip().startswith("#")
            and not lines[index].startswith((" ", "\t"))
        ),
        len(lines),
    )
    setting = re.compile(rf"^(\s+){re.escape(key)}\s*:\s*([^#\r\n]*)(.*)$")
    for index in range(section_index + 1, section_end):
        match = setting.match(lines[index].rstrip("\r\n"))
        if match:
            ending = newline if lines[index].endswith(("\n", "\r")) else ""
            suffix = match.group(3)
            if suffix.startswith("#"):
                suffix = f" {suffix}"
            lines[index] = f"{match.group(1)}{key}: {value}{suffix}{ending}"
            return "".join(lines)

    lines.insert(section_index + 1, f"  {key}: {value}{newline}")
    return "".join(lines)


def render_policy_settings(
    text: str,
    *,
    human_readable: bool | None = None,
    learning_mode: str | None = None,
) -> str:
    """Render known Policy settings without changing its Markdown body."""

    current = resolve_policy_settings(text)
    if learning_mode is not None and learning_mode not in LEARNING_MODES:
        raise PolicySettingsError(f"unknown learning.mode: {learning_mode!r}")
    target_human_readable = current.human_readable if human_readable is None else human_readable
    target_learning_mode = current.learning_mode if learning_mode is None else learning_mode
    document = _split_policy(text)
    assert document.frontmatter is not None
    frontmatter = document.frontmatter

    # 管理対象の二つのキーだけを更新
    frontmatter = _replace_nested_scalar(
        frontmatter,
        document.newline,
        "knowledge",
        "human_readable",
        str(target_human_readable).lower(),
    )
    frontmatter = _replace_nested_scalar(
        frontmatter,
        document.newline,
        "learning",
        "mode",
        target_learning_mode,
    )
    return (
        f"---{document.newline}{frontmatter.rstrip()}{document.newline}"
        f"---{document.newline}{document.body}"
    )


def read_policy_text(path: Path) -> str:
    """Read Policy text without normalizing line endings."""

    with path.open("r", encoding="utf-8", newline="") as stream:
        return stream.read()


def read_policy_settings(path: Path) -> PolicySettings:
    """Read settings from a Policy file."""

    return resolve_policy_settings(read_policy_text(path))


def update_policy_settings(
    path: Path,
    *,
    human_readable: bool | None = None,
    learning_mode: str | None = None,
) -> PolicySettings:
    """Update known Policy settings after validating the whole frontmatter."""

    original = read_policy_text(path)
    rendered = render_policy_settings(
        original,
        human_readable=human_readable,
        learning_mode=learning_mode,
    )
    if rendered != original:
        path.write_text(rendered, encoding="utf-8", newline="")
    return resolve_policy_settings(rendered)


def _parse_boolean(value: str) -> bool:
    """Parse a command-line boolean without accepting ambiguous values."""

    return value == "true"


def main(argv: list[str] | None = None) -> int:
    """Show or update Policy settings."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("policy", type=Path)
    parser.add_argument("--human-readable", choices=("true", "false"))
    parser.add_argument("--learning-mode", choices=tuple(sorted(LEARNING_MODES)))
    args = parser.parse_args(argv)
    try:
        if args.human_readable is None and args.learning_mode is None:
            settings = read_policy_settings(args.policy)
        else:
            settings = update_policy_settings(
                args.policy,
                human_readable=(
                    None
                    if args.human_readable is None
                    else _parse_boolean(args.human_readable)
                ),
                learning_mode=args.learning_mode,
            )
        print(f"knowledge.human_readable: {str(settings.human_readable).lower()}")
        print(f"learning.mode: {settings.learning_mode}")
        return 0
    except (OSError, UnicodeError, PolicySettingsError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
