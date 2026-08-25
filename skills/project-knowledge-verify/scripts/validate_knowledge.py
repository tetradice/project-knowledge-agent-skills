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
SUPPORTED_FORMATS = {"0.1", "0.2"}
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
LINK_PATTERN = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
DATE_HEADING_PATTERN = re.compile(r"^## \d{4}-\d{2}-\d{2}\s*$")
ACTOR_PATTERN = re.compile(
    r"^(?:human:[A-Za-z0-9_.@-]+|process:[A-Za-z0-9_.:/-]+|[a-z0-9][a-z0-9-]*/\d+\.\d+\.\d+)$"
)
LEGACY_MARKERS = (
    Path("docs/index.md"),
    Path("docs/log.md"),
    Path("config.yml"),
    Path("state.yml"),
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


def detect_format(findings: list[Finding], root: Path) -> str | None:
    manifest = root / "manifest.yml"
    if not manifest.exists():
        if all((root / marker).is_file() for marker in LEGACY_MARKERS):
            add(findings, "medium", "legacy-format-0.1", root, root)
            return "0.1"
        add(findings, "high", "missing-or-unrecognized-manifest", manifest, root)
        return None

    raw = manifest.read_text(encoding="utf-8")
    data = _mapping(manifest)
    if data is None:
        add(findings, "high", "malformed-manifest", manifest, root)
        return None
    if data.get("format") != FORMAT_NAME:
        add(findings, "high", "unknown-manifest-format", manifest, root)
        return None
    version = data.get("format_version")
    if not isinstance(version, str) or not re.fullmatch(r"\d+\.\d+", version):
        add(findings, "high", "invalid-format-version", manifest, root)
        return None
    if not re.search(r'^format_version:\s*["\']' + re.escape(version) + r'["\']\s*$', raw, re.MULTILINE):
        add(findings, "high", "unquoted-format-version", manifest, root)
    if version not in SUPPORTED_FORMATS:
        add(findings, "high", "unsupported-format-version", manifest, root)
        return None
    return version


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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("knowledge_root", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    root = _root(args.knowledge_root)
    docs = root / "docs"
    findings: list[Finding] = []
    version = detect_format(findings, root)
    require(findings, docs / "index.md", "high", "missing-index", root)
    require(findings, docs / "log.md", "high", "missing-log", root)
    check_knowledge_policy(findings, root)
    check_state(findings, root, version)

    markdown_files = sorted(docs.rglob("*.md")) if docs.exists() else []
    linked: set[Path] = set()
    for path in markdown_files:
        text = path.read_text(encoding="utf-8")
        metadata, body, parse_error = split_frontmatter(text)
        check_reserved(findings, path, docs, metadata, body, parse_error, root, version)
        if path.name not in {"index.md", "log.md"}:
            check_concept(findings, path, metadata, parse_error, root, version)
        check_links(findings, linked, path, text, root)

    exempt = {docs / "index.md", docs / "log.md"}
    for path in markdown_files:
        if path not in exempt and path.name != "index.md" and path.resolve() not in linked:
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


def check_knowledge_policy(findings: list[Finding], root: Path) -> None:
    path = root / "knowledge-policy.md"
    if not path.is_file():
        add(findings, "high", "missing-knowledge-policy", path, root)
        return
    text = path.read_text(encoding="utf-8")
    for heading, code in (
        ("# プロジェクトKnowledge Policy", "invalid-knowledge-policy-title"),
        ("## 基本方針", "missing-policy-principles"),
        ("## 積極的に保存する情報", "missing-policy-include-criteria"),
        ("## 原則として保存しない情報", "missing-policy-exclude-criteria"),
        ("## 構成方針", "missing-policy-structure"),
    ):
        if heading not in text:
            add(findings, "high", code, path, root)


def check_state(findings: list[Finding], root: Path, version: str | None) -> None:
    path = root / "state.yml"
    if not path.is_file():
        add(findings, "high", "missing-state", path, root)
        return
    data = _mapping(path)
    if data is None:
        add(findings, "high", "malformed-state", path, root)
        return
    if version == "0.2":
        if "state_schema_version" not in data:
            add(findings, "high", "missing-state-schema-version", path, root)
        if "version" in data:
            add(findings, "high", "ambiguous-state-version", path, root)


def check_reserved(
    findings: list[Finding],
    path: Path,
    docs: Path,
    metadata: dict[str, Any] | None,
    body: str,
    parse_error: str | None,
    root: Path,
    version: str | None,
) -> None:
    if version != "0.2":
        return
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
    version: str | None,
) -> None:
    if parse_error:
        add(findings, "high", f"frontmatter-{parse_error}", path, root)
        return
    if metadata is None:
        add(findings, "high", "missing-frontmatter", path, root)
        return
    concept_type = metadata.get("type")
    if not isinstance(concept_type, str) or not concept_type.strip():
        severity = "medium" if version == "0.1" else "high"
        add(findings, severity, "missing-type", path, root)

    if concept_type == "Reference":
        check_reference(findings, path, metadata, root, version)
    else:
        check_classification(findings, path, metadata, root, version)
    check_sources(findings, path, metadata, root, version)
    check_actor_event(findings, path, metadata.get("generated"), "generated", root, version, True)
    check_actor_event(findings, path, metadata.get("verified"), "verified", root, version, False)
    check_lifecycle(findings, path, metadata, root)


def check_reference(
    findings: list[Finding],
    path: Path,
    metadata: dict[str, Any],
    root: Path,
    version: str | None,
) -> None:
    source_type = metadata.get("pk_source_type")
    if version == "0.2" and source_type not in SOURCE_TYPES:
        add(findings, "high", "invalid-reference-source-type", path, root)
    if "category" in metadata or "derivation" in metadata:
        add(findings, "high", "reference-has-knowledge-classification", path, root)


def check_classification(
    findings: list[Finding],
    path: Path,
    metadata: dict[str, Any],
    root: Path,
    version: str | None,
) -> None:
    category = metadata.get("category")
    derivation = metadata.get("derivation")
    legacy_missing = metadata.get("pk_legacy_unclassified") is True
    if category not in CATEGORIES or derivation not in DERIVATIONS:
        if version == "0.1" or legacy_missing:
            add(findings, "medium", "legacy-unclassified-concept", path, root)
        else:
            add(findings, "high", "invalid-or-missing-classification", path, root)
    elif legacy_missing:
        add(findings, "low", "stale-legacy-classification-marker", path, root)

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
    version: str | None,
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
            if not target.exists():
                add(findings, "high", "missing-source-resource", target, root)
        source_type = source.get("pk_source_type")
        if version == "0.2" and source_type not in SOURCE_TYPES:
            add(findings, "high", "invalid-source-type", path, root)


def check_actor_event(
    findings: list[Finding],
    path: Path,
    value: Any,
    field: str,
    root: Path,
    version: str | None,
    required: bool,
) -> None:
    if value is None:
        if required and version == "0.2":
            add(findings, "high", f"missing-{field}", path, root)
        return
    events = value if isinstance(value, list) else [value]
    if not events or any(not isinstance(event, dict) for event in events):
        severity = "medium" if version == "0.1" else "high"
        add(findings, severity, f"invalid-{field}", path, root)
        return
    severity = "medium" if version == "0.1" else "high"
    for event in events:
        actor = event.get("by")
        timestamp = event.get("at")
        if not isinstance(actor, str) or not ACTOR_PATTERN.fullmatch(actor):
            add(findings, severity, f"invalid-{field}-actor", path, root)
        if not valid_timestamp(timestamp):
            add(findings, severity, f"invalid-{field}-timestamp", path, root)


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
