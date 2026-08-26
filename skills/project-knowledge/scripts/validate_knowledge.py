# /// script
# requires-python = ">=3.11"
# dependencies = ["PyYAML>=6.0,<7"]
# ///

"""Validate Project Knowledge and OKF v0.2 without changing files."""

from __future__ import annotations

import argparse
import json
import re
from datetime import date, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import yaml

FORMAT_NAME = "project-knowledge"
FORMAT_VERSION = "1.0"
CATEGORIES = {"declared", "extracted", "derived"}
DERIVATIONS = {"direct", "synthesized", "inferred"}
SOURCE_TYPES = {
    "user-statement",
    "reference-document",
    "project-artifact",
    "interaction-record",
    "change-implementation",
}
STATUSES = {"draft", "active", "stable", "deprecated", "archived"}
STATE_SCHEMA_VERSION = 2
STATE_KEYS = {"state_schema_version", "git_baseline_commit"}
LINK_PATTERN = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
DATE_HEADING_PATTERN = re.compile(r"^## \d{4}-\d{2}-\d{2}\s*$")
ACTOR_PATTERN = re.compile(
    r"^(?:human:[A-Za-z0-9_.@-]+|process:[A-Za-z0-9_.:/-]+|[a-z0-9][a-z0-9-]*/\d+\.\d+\.\d+)$"
)
Finding = dict[str, str]


def _root(path: Path) -> Path:
    candidate = path.resolve()
    if candidate.name == "project-knowledge":
        return candidate
    child = candidate / "project-knowledge"
    return child if child.exists() else candidate


def _mapping(path: Path) -> dict[str, Any] | None:
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError):
        return None
    return value if isinstance(value, dict) else None


def check_manifest(findings: list[Finding], root: Path) -> None:
    """形式1.0のmanifestを検査する。"""

    manifest = root / "manifest.yml"
    if not manifest.exists():
        add(findings, "high", "missing-manifest", manifest, root)
        return

    try:
        raw = manifest.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        add(findings, "high", "malformed-manifest", manifest, root)
        return
    data = _mapping(manifest)
    if data is None:
        add(findings, "high", "malformed-manifest", manifest, root)
        return
    if data.get("format") != FORMAT_NAME:
        add(findings, "high", "unknown-manifest-format", manifest, root)
        return
    version = data.get("format_version")
    if not isinstance(version, str) or not re.fullmatch(r"\d+\.\d+", version):
        add(findings, "high", "invalid-format-version", manifest, root)
        return
    if not re.search(r'^format_version:\s*["\']' + re.escape(version) + r'["\']\s*$', raw, re.MULTILINE):
        add(findings, "high", "unquoted-format-version", manifest, root)
    if version != FORMAT_VERSION:
        add(findings, "high", "unsupported-format-version", manifest, root)


def split_frontmatter(text: str) -> tuple[dict[str, Any] | None, str, str | None]:
    normalized = text.replace("\r\n", "\n")
    if not normalized.startswith("---\n"):
        return None, normalized, None
    end = normalized.find("\n---\n", 4)
    if end < 0:
        return None, normalized, "unterminated"
    try:
        metadata = yaml.safe_load(normalized[4:end])
    except yaml.YAMLError:
        return None, normalized[end + 5 :], "malformed"
    if not isinstance(metadata, dict):
        return None, normalized[end + 5 :], "not-mapping"
    return metadata, normalized[end + 5 :], None


def read_markdown(
    findings: list[Finding], path: Path, root: Path
) -> str | None:
    """Knowledge Markdownを安全に読み取る。"""

    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        add(findings, "high", "unreadable-knowledge", path, root)
        return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("knowledge_root", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    root = _root(args.knowledge_root)
    docs = root / "docs"
    findings: list[Finding] = []
    check_manifest(findings, root)
    require(findings, docs / "index.md", "high", "missing-index", root)
    require(findings, docs / "log.md", "high", "missing-log", root)
    check_knowledge_policy(findings, root)
    check_state(findings, root)

    markdown_files = sorted(docs.rglob("*.md")) if docs.exists() else []
    linked: set[Path] = set()
    readable_markdown: set[Path] = set()
    for path in markdown_files:
        # 解釈不能な文書はfindingに留め、後続の内容検査を行わない
        text = read_markdown(findings, path, root)
        if text is None:
            continue
        readable_markdown.add(path.resolve())
        metadata, body, parse_error = split_frontmatter(text)
        check_reserved(findings, path, docs, metadata, body, parse_error, root)
        if path.name not in {"index.md", "log.md"}:
            check_concept(findings, path, metadata, parse_error, root)
        check_links(findings, linked, path, text, root)

    exempt = {docs / "index.md", docs / "log.md"}
    for path in markdown_files:
        resolved = path.resolve()
        if (
            path not in exempt
            and path.name != "index.md"
            and resolved in readable_markdown
            and resolved not in linked
        ):
            add(findings, "medium", "orphan", path, root)

    order = {"high": 0, "medium": 1, "low": 2}
    findings.sort(key=lambda item: (order[item["severity"]], item["path"], item["code"]))
    if args.json:
        print(json.dumps(findings, ensure_ascii=False, indent=2))
    elif not findings:
        print("No structural findings")
    else:
        for item in findings:
            print(f"{item['severity'].upper()} {item['code']} {item['path']}")
    return 1 if any(item["severity"] == "high" for item in findings) else 0


def check_knowledge_policy(
    findings: list[Finding],
    root: Path,
) -> None:
    """Policy本文と運用設定を検査する。"""

    path = root / "knowledge-policy.md"
    if not path.is_file():
        add(findings, "high", "missing-knowledge-policy", path, root)
        return
    text = read_markdown(findings, path, root)
    if text is None:
        return
    metadata, _, parse_error = split_frontmatter(text)
    if parse_error or metadata is None:
        add(findings, "high", "invalid-policy-frontmatter", path, root)
    else:
        knowledge = metadata.get("knowledge")
        learning = metadata.get("learning")
        if not isinstance(knowledge, dict) or not isinstance(
            knowledge.get("human_readable"), bool
        ):
            add(findings, "high", "invalid-policy-human-readable", path, root)
        if (
            not isinstance(learning, dict)
            or learning.get("mode") not in {"manual", "opportunistic", "aggressive"}
        ):
            add(findings, "high", "invalid-policy-learning-mode", path, root)
    for heading, code in (
        ("# プロジェクトKnowledge Policy", "invalid-knowledge-policy-title"),
        ("## 基本方針", "missing-policy-principles"),
        ("## 積極的に保存する情報", "missing-policy-include-criteria"),
        ("## 原則として保存しない情報", "missing-policy-exclude-criteria"),
        ("## 構成方針", "missing-policy-structure"),
    ):
        if heading not in text:
            add(findings, "high", code, path, root)


def check_state(findings: list[Finding], root: Path) -> None:
    """再構築可能なstateの静的schemaだけを低重大度で検査する。"""

    path = root / "state.yml"
    if not path.is_file():
        add(findings, "low", "missing-state", path, root)
        return
    data = _mapping(path)
    if data is None:
        add(findings, "low", "malformed-state", path, root)
        return

    # repository依存のcommit解決とancestry確認はupdate時に行う
    schema_version = data.get("state_schema_version")
    if isinstance(schema_version, bool) or not isinstance(schema_version, int):
        add(findings, "low", "invalid-state-schema-version", path, root)
    elif schema_version != STATE_SCHEMA_VERSION:
        add(findings, "low", "unsupported-state-schema-version", path, root)
    if "git_baseline_commit" not in data:
        add(findings, "low", "missing-git-baseline-commit", path, root)
    baseline = data.get("git_baseline_commit")
    if baseline is not None and not isinstance(baseline, str):
        add(findings, "low", "invalid-git-baseline-commit", path, root)
    if set(data) - STATE_KEYS:
        add(findings, "low", "unknown-state-key", path, root)


def check_reserved(
    findings: list[Finding],
    path: Path,
    docs: Path,
    metadata: dict[str, Any] | None,
    body: str,
    parse_error: str | None,
    root: Path,
) -> None:
    if parse_error:
        add(findings, "high", f"frontmatter-{parse_error}", path, root)
        return
    if path == docs / "index.md":
        if metadata is None:
            add(findings, "high", "missing-okf-root-frontmatter", path, root)
        elif metadata != {"okf_version": "0.2"}:
            add(findings, "high", "invalid-okf-root-frontmatter", path, root)
    elif path.name in {"index.md", "log.md"} and metadata is not None:
        add(findings, "high", "reserved-file-has-frontmatter", path, root)

    if path.name == "log.md":
        for line in body.splitlines():
            if line.startswith("## ") and not DATE_HEADING_PATTERN.fullmatch(line):
                add(findings, "high", "invalid-log-date-heading", path, root)
                break


def check_concept(
    findings: list[Finding],
    path: Path,
    metadata: dict[str, Any] | None,
    parse_error: str | None,
    root: Path,
) -> None:
    if parse_error:
        add(findings, "high", f"frontmatter-{parse_error}", path, root)
        return
    if metadata is None:
        add(findings, "high", "missing-frontmatter", path, root)
        return
    concept_type = metadata.get("type")
    if not isinstance(concept_type, str) or not concept_type.strip():
        add(findings, "high", "missing-type", path, root)

    if concept_type == "Reference":
        check_reference(findings, path, metadata, root)
    else:
        check_classification(findings, path, metadata, root)
    check_sources(findings, path, metadata, root)
    check_actor_event(findings, path, metadata.get("generated"), "generated", root, True)
    check_actor_event(findings, path, metadata.get("verified"), "verified", root, False)
    check_lifecycle(findings, path, metadata, root)


def check_reference(
    findings: list[Finding],
    path: Path,
    metadata: dict[str, Any],
    root: Path,
) -> None:
    source_type = metadata.get("pk_source_type")
    if source_type not in SOURCE_TYPES:
        add(findings, "high", "invalid-reference-source-type", path, root)
    classification_keys = {"pk_category", "pk_derivation"}
    if any(key in metadata for key in classification_keys):
        add(findings, "high", "reference-has-knowledge-classification", path, root)


def check_classification(
    findings: list[Finding],
    path: Path,
    metadata: dict[str, Any],
    root: Path,
) -> None:
    category = metadata.get("pk_category")
    derivation = metadata.get("pk_derivation")
    if "category" in metadata or "derivation" in metadata:
        add(findings, "high", "unprefixed-project-knowledge-metadata", path, root)
    if category not in CATEGORIES or derivation not in DERIVATIONS:
        add(findings, "high", "invalid-or-missing-classification", path, root)

    if (
        derivation == "inferred"
        and not metadata.get("verified")
        and metadata.get("status") != "draft"
    ):
        add(findings, "high", "unverified-inference-not-draft", path, root)


def check_sources(
    findings: list[Finding],
    path: Path,
    metadata: dict[str, Any],
    root: Path,
) -> None:
    sources = metadata.get("sources", [])
    if not isinstance(sources, list):
        add(findings, "high", "sources-not-list", path, root)
        return
    for source in sources:
        if not isinstance(source, dict):
            add(findings, "high", "source-not-mapping", path, root)
            continue
        resource = source.get("resource")
        if not isinstance(resource, str) or not resource.strip():
            add(findings, "high", "missing-source-resource", path, root)
        elif not is_uri(resource):
            target = (path.parent / resource.split("#", 1)[0]).resolve()
            if not target.is_file():
                add(findings, "high", "missing-source-resource", target, root)
            elif not is_readable_source(target):
                add(findings, "high", "unreadable-source-resource", target, root)
        source_type = source.get("pk_source_type")
        if source_type not in SOURCE_TYPES:
            add(findings, "high", "invalid-source-type", path, root)


def is_readable_source(path: Path) -> bool:
    """sourceを内容へ立ち入らず読取可能か確認する。"""

    try:
        with path.open("rb") as source:
            source.read(1)
    except OSError:
        return False
    return True


def check_actor_event(
    findings: list[Finding],
    path: Path,
    value: Any,
    field: str,
    root: Path,
    required: bool,
) -> None:
    if value is None:
        if required:
            add(findings, "high", f"missing-{field}", path, root)
        return
    events = value if isinstance(value, list) else [value]
    if not events or any(not isinstance(event, dict) for event in events):
        add(findings, "high", f"invalid-{field}", path, root)
        return
    for event in events:
        actor = event.get("by")
        timestamp = event.get("at")
        if not isinstance(actor, str) or not ACTOR_PATTERN.fullmatch(actor):
            add(findings, "high", f"invalid-{field}-actor", path, root)
        if not valid_timestamp(timestamp):
            add(findings, "high", f"invalid-{field}-timestamp", path, root)


def check_lifecycle(
    findings: list[Finding], path: Path, metadata: dict[str, Any], root: Path
) -> None:
    status = metadata.get("status")
    if status is not None and status not in STATUSES:
        add(findings, "high", "invalid-status", path, root)
    stale = metadata.get("stale")
    if stale is not None and not isinstance(stale, bool):
        add(findings, "high", "invalid-stale", path, root)
    stale_after = metadata.get("stale_after")
    if stale_after is None:
        return
    stale_date = parse_date(stale_after)
    if stale_date is None:
        add(findings, "high", "invalid-stale-after", path, root)
    elif stale_date <= datetime.now().astimezone().date() and stale is not True:
        add(findings, "medium", "stale", path, root)


def check_links(
    findings: list[Finding],
    linked: set[Path],
    path: Path,
    text: str,
    root: Path,
) -> None:
    for raw_target in LINK_PATTERN.findall(text):
        target_text = raw_target.strip().split("#", 1)[0]
        if not target_text or is_uri(target_text):
            continue
        target = (path.parent / target_text).resolve()
        if not target.exists():
            add(findings, "high", "broken-link", target, root)
        elif target.suffix.lower() == ".md":
            linked.add(target)


def is_uri(value: str) -> bool:
    if re.match(r"^[A-Za-z]:[\\/]", value):
        return False
    scheme = urlparse(value).scheme
    return bool(scheme and re.fullmatch(r"[A-Za-z][A-Za-z0-9+.-]*", scheme))


def valid_timestamp(value: Any) -> bool:
    if isinstance(value, datetime):
        return value.tzinfo is not None
    if not isinstance(value, str):
        return False
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return parsed.tzinfo is not None


def parse_date(value: Any) -> date | None:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value[:10])
        except ValueError:
            return None
    return None


def require(
    findings: list[Finding], path: Path, severity: str, code: str, root: Path
) -> None:
    if not path.is_file():
        add(findings, severity, code, path, root)


def add(
    findings: list[Finding], severity: str, code: str, path: Path, root: Path
) -> None:
    try:
        display = path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        display = str(path.resolve())
    finding = {"severity": severity, "code": code, "path": display}
    if finding not in findings:
        findings.append(finding)


if __name__ == "__main__":
    raise SystemExit(main())
