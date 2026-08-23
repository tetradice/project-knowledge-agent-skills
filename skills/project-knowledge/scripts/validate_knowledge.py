#!/usr/bin/env python3
"""プロジェクトナレッジを変更せず構造検証する。"""

from __future__ import annotations

import argparse
import json
import re
from datetime import date
from pathlib import Path


LINK_PATTERN = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
SOURCE_PATTERN = re.compile(r"^\s*resource:\s*[\"']?([^\"'#]+)", re.MULTILINE)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("knowledge_root", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    # ナレッジ Bundleと収集Policyをread-onlyで検査
    root = args.knowledge_root.resolve()
    docs = root / "docs"
    findings: list[dict[str, str]] = []
    require(findings, docs / "index.md", "high", "missing-index")
    require(findings, docs / "log.md", "high", "missing-log")
    check_knowledge_policy(findings, root)

    markdown_files = sorted(docs.rglob("*.md")) if docs.exists() else []
    linked: set[Path] = set()
    for path in markdown_files:
        text = path.read_text(encoding="utf-8")
        check_frontmatter(findings, path, text, root)
        check_links(findings, linked, path, text, root)
        check_sources(findings, path, text, root)
        check_stale(findings, path, text, root)
        check_reference_provenance(findings, path, text, root)

    # indexから到達できないナレッジ候補を報告
    exempt = {docs / "index.md", docs / "log.md"}
    for path in markdown_files:
        if path not in exempt and path.name != "index.md" and path.resolve() not in linked:
            add(findings, "medium", "orphan", path, root)

    # 結果を重要度順に出力
    order = {"high": 0, "medium": 1, "low": 2}
    findings.sort(key=lambda item: (order[item["severity"]], item["path"], item["code"]))
    if args.json:
        print(json.dumps(findings, ensure_ascii=False, indent=2))
    else:
        if not findings:
            print("No structural findings")
        for item in findings:
            print(f"{item['severity'].upper()} {item['code']} {item['path']}")
    return 1 if any(item["severity"] == "high" for item in findings) else 0


def check_knowledge_policy(findings: list[dict[str, str]], root: Path) -> None:
    policy_path = root / "knowledge-policy.md"
    if not policy_path.is_file():
        add(findings, "high", "missing-knowledge-policy", policy_path, root)
        return

    # Policyが対象領域一覧ではなく価値判断を扱える最小構造を確認
    text = policy_path.read_text(encoding="utf-8")
    for heading, code in (
        ("# プロジェクトナレッジ Policy", "invalid-knowledge-policy-title"),
        ("## 基本方針", "missing-policy-principles"),
        ("## 積極的に保存する情報", "missing-policy-include-criteria"),
        ("## 原則として保存しない情報", "missing-policy-exclude-criteria"),
        ("## 構成方針", "missing-policy-structure"),
    ):
        if heading not in text:
            add(findings, "high", code, policy_path, root)


def require(findings: list[dict[str, str]], path: Path, severity: str, code: str) -> None:
    if not path.is_file():
        add(findings, severity, code, path, path.parents[1])


def check_frontmatter(findings: list[dict[str, str]], path: Path, text: str, root: Path) -> None:
    if not text.startswith("---\n") and not text.startswith("---\r\n"):
        add(findings, "high", "missing-frontmatter", path, root)
        return
    end = text.find("\n---", 4)
    frontmatter = text[4:end] if end >= 0 else ""
    for key in ("title:", "description:", "version:", "generated:"):
        if key not in frontmatter:
            add(findings, "high", f"missing-{key[:-1]}", path, root)


def check_links(findings: list[dict[str, str]], linked: set[Path], path: Path, text: str, root: Path) -> None:
    for target in LINK_PATTERN.findall(text):
        if target.startswith(("http://", "https://", "mailto:", "#")):
            continue
        clean = target.split("#", 1)[0]
        destination = (path.parent / clean).resolve()
        linked.add(destination)
        if clean and not destination.exists():
            add(findings, "high", "broken-link", path, root, target)


def check_sources(findings: list[dict[str, str]], path: Path, text: str, root: Path) -> None:
    for target in SOURCE_PATTERN.findall(text):
        clean = target.strip()
        if clean.startswith(("http://", "https://")):
            continue
        destination = (path.parent / clean).resolve()
        if not destination.exists():
            add(findings, "medium", "missing-source", path, root, clean)


def check_stale(findings: list[dict[str, str]], path: Path, text: str, root: Path) -> None:
    match = re.search(r"^stale_after:\s*[\"']?(\d{4}-\d{2}-\d{2})", text, re.MULTILINE)
    if match and date.fromisoformat(match.group(1)) < date.today():
        add(findings, "medium", "stale", path, root, match.group(1))


def check_reference_provenance(
    findings: list[dict[str, str]], path: Path, text: str, root: Path
) -> None:
    if path.name == "index.md":
        return

    # captureとmemoを操作ではなくReference provenanceとして検査
    parent = path.parent.name
    expected = {
        "captures": ("capture", "primary", "trusted"),
        "memos": ("memo", "secondary", "provisional|trusted"),
    }.get(parent)
    if not expected:
        return
    for key, value in zip(("pk_source_kind", "pk_authority", "pk_trust"), expected, strict=True):
        if not re.search(rf"^{key}:\s*(?:{value})\s*$", text, re.MULTILINE):
            add(findings, "high", f"invalid-{key.replace('_', '-')}", path, root)


def add(
    findings: list[dict[str, str]], severity: str, code: str, path: Path, root: Path, detail: str = ""
) -> None:
    try:
        display = path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        display = str(path)
    findings.append({"severity": severity, "code": code, "path": display, "detail": detail})


if __name__ == "__main__":
    raise SystemExit(main())
