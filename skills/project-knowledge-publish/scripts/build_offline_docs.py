# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "mkdocs-material>=9.6,<10",
# ]
# ///

"""Project KnowledgeのMarkdownをfile://対応のMaterial for MkDocsサイトへ変換する。"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit


SKILL_ROOT = Path(__file__).resolve().parent.parent
CSS_PATH = SKILL_ROOT / "assets" / "offline-docs.css"
LOCAL_ATTRIBUTES = {"href", "src", "poster", "data"}
ASSET_TAGS = {"img", "script", "link", "source", "video", "audio", "iframe"}


class ReferenceParser(HTMLParser):
    """HTMLからローカル参照と外部アセット参照を抽出する。"""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.references: list[tuple[str, str]] = []
        self.external_assets: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        # file://表示に影響するURL属性だけを収集
        for name, value in attrs:
            if value is None or name.casefold() not in LOCAL_ATTRIBUTES:
                continue
            scheme = urlsplit(value).scheme.casefold()
            if scheme in {"http", "https"} and tag.casefold() in ASSET_TAGS:
                self.external_assets.append(value)
            else:
                self.references.append((name.casefold(), value))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--site-name")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    try:
        report = build_site(args.input, args.output, args.site_name, args.force)
    except (FileExistsError, RuntimeError, ValueError, subprocess.CalledProcessError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


def build_site(input_dir: Path, output_dir: Path, site_name: str | None, force: bool) -> dict[str, object]:
    # 入出力と上書き許可を検証
    input_dir = input_dir.resolve()
    output_dir = output_dir.resolve()
    validate_paths(input_dir, output_dir, force)
    if not any(input_dir.rglob("*.md")):
        raise ValueError(f"Markdownファイルがありません: {input_dir}")

    # 入力を変更せず一時領域でMkDocsサイトを構成
    with tempfile.TemporaryDirectory(prefix="project-knowledge-publish-") as temporary:
        work = Path(temporary)
        docs = work / "docs"
        shutil.copytree(input_dir, docs)
        asset_dir = docs / "_project_knowledge_assets"
        asset_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(CSS_PATH, asset_dir / CSS_PATH.name)
        config = work / "mkdocs.yml"
        config.write_text(render_config(site_name or input_dir.name, docs, output_dir), encoding="utf-8")

        # PEP 723で用意された同一環境のMkDocsを実行
        subprocess.run(
            [sys.executable, "-m", "mkdocs", "build", "--clean", "--strict", "--config-file", str(config)],
            cwd=work,
            check=True,
        )

    # file://互換性を検査して不完全な成果物を成功扱いしない
    (output_dir / "404.html").unlink(missing_ok=True)
    report = verify_site(output_dir)
    if report["errors"]:
        raise RuntimeError(f"HTML検証で{len(report['errors'])}件のエラーを検出しました")
    return report


def validate_paths(input_dir: Path, output_dir: Path, force: bool) -> None:
    if not input_dir.is_dir():
        raise ValueError(f"入力フォルダが存在しません: {input_dir}")
    if output_dir == input_dir or input_dir.is_relative_to(output_dir):
        raise ValueError("出力に入力自身またはその親は指定できません")
    if output_dir == Path(output_dir.anchor):
        raise ValueError("ドライブのルートは出力に指定できません")
    if output_dir.exists() and any(output_dir.iterdir()) and not force:
        raise FileExistsError(f"非空の出力を置換するには承認後に--forceを指定してください: {output_dir}")


def render_config(site_name: str, docs_dir: Path, output_dir: Path) -> str:
    # JSON文字列はYAML scalarとしても有効なのでパスを安全に埋め込める
    quote = lambda value: json.dumps(str(value), ensure_ascii=False)
    return f"""site_name: {quote(site_name)}
site_url: ""
docs_dir: {quote(docs_dir.as_posix())}
site_dir: {quote(output_dir.as_posix())}
use_directory_urls: false
theme:
  name: material
  language: ja
  font: false
  features:
    - navigation.sections
    - navigation.top
    - search.highlight
    - search.suggest
    - content.code.copy
plugins:
  - privacy:
      concurrency: 1
      log_level: error
  - search:
      lang: [ja, en]
  - offline
markdown_extensions:
  - admonition
  - attr_list
  - footnotes
  - md_in_html
  - tables
  - toc:
      permalink: true
  - pymdownx.details
  - pymdownx.highlight
  - pymdownx.superfences
  - pymdownx.tabbed:
      alternate_style: true
  - pymdownx.tasklist:
      custom_checkbox: true
extra_css:
  - _project_knowledge_assets/offline-docs.css
"""


def verify_site(root: Path) -> dict[str, object]:
    # 全HTMLのローカル参照と外部アセットを確認
    errors: list[str] = []
    warnings: list[str] = []
    html_files = sorted(root.rglob("*.html"))
    if not (root / "index.html").is_file():
        errors.append("missing index.html")
    for html_file in html_files:
        parser = ReferenceParser()
        parser.feed(html_file.read_text(encoding="utf-8"))
        errors.extend(f"external asset: {value}" for value in parser.external_assets)
        for _, target in parser.references:
            check_reference(root, html_file, target, errors, warnings)
    if not any(path.name == "search_index.js" for path in root.rglob("search_index.js")):
        errors.append("missing offline search_index.js")
    images = sum(1 for path in root.rglob("*") if path.suffix.casefold() in {".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp"})
    return {
        "index": str(root / "index.html"),
        "pages": len(html_files),
        "images": images,
        "warnings": warnings,
        "broken_links": sum(item.startswith("broken reference:") for item in errors),
        "errors": errors,
    }


def check_reference(root: Path, owner: Path, target: str, errors: list[str], warnings: list[str]) -> None:
    clean = target.strip()
    if not clean or clean.startswith("#"):
        return
    if clean.startswith(("/", "\\")):
        errors.append(f"root absolute reference: {owner.name}: {clean}")
        return
    parsed = urlsplit(clean)
    if parsed.scheme in {"http", "https", "mailto", "tel", "data", "javascript"}:
        return
    if parsed.scheme:
        warnings.append(f"unsupported scheme: {parsed.scheme}: {clean}")
        return
    destination = (owner.parent / unquote(parsed.path)).resolve()
    try:
        destination.relative_to(root)
    except ValueError:
        errors.append(f"outside site: {owner.name}: {clean}")
        return
    if parsed.path and not destination.exists():
        errors.append(f"broken reference: {owner.name}: {clean}")


if __name__ == "__main__":
    raise SystemExit(main())
