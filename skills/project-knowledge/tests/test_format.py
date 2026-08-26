from __future__ import annotations

import json
import re
import runpy
import subprocess
from pathlib import Path

import pytest
import yaml

SKILL_ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = SKILL_ROOT.parent
INIT = SKILL_ROOT / "scripts" / "init_project.py"
VALIDATE = SKILL_ROOT / "scripts" / "validate_knowledge.py"
VALIDATOR = runpy.run_path(str(VALIDATE))
SKILL_NAMES = (
    "project-knowledge",
    "project-knowledge-audit",
    "project-knowledge-fast-ask",
    "project-knowledge-publish",
)


def run(script: Path, *args: object) -> subprocess.CompletedProcess[str]:
    """指定したPythonスクリプトを実行する。"""

    return subprocess.run(
        ["uv", "run", str(script), *(str(arg) for arg in args)],
        capture_output=True,
        text=True,
        check=False,
    )


def add_concept(
    root: Path,
    filename: str,
    category: str | None,
    derivation: str | None,
    status: str = "stable",
    verified: bool = False,
) -> None:
    """validator用のConceptを追加する。"""

    metadata: dict[str, object] = {
        "type": "Test Concept",
        "status": status,
        "generated": {
        "by": "project-knowledge/3.0.0",
            "at": "2026-08-26T00:00:00+09:00",
        },
        "sources": [],
    }
    if category is not None:
        metadata["pk_category"] = category
    if derivation is not None:
        metadata["pk_derivation"] = derivation
    if verified:
        metadata["verified"] = {
            "by": "project-knowledge/3.0.0",
            "at": "2026-08-26T00:10:00+09:00",
        }
    frontmatter = yaml.safe_dump(metadata, sort_keys=False, allow_unicode=True).rstrip()
    path = root / "docs" / "examples" / filename
    path.write_text(f"---\n{frontmatter}\n---\n\n# {filename}\n", encoding="utf-8")


@pytest.fixture
def classified_bundle(tmp_path: Path) -> Path:
    """分類済みConceptを持つ形式1.0 Bundleを作成する。"""

    assert run(INIT, tmp_path).returncode == 0
    root = tmp_path / "project-knowledge"
    examples = root / "docs" / "examples"
    examples.mkdir()
    (examples / "index.md").write_text(
        "# Examples\n\n"
        "- [Declared](declared.md)\n"
        "- [Extracted](extracted.md)\n"
        "- [Synthesized](synthesized.md)\n"
        "- [Inferred](inferred.md)\n"
        "- [Verified inference](verified-inference.md)\n",
        encoding="utf-8",
    )
    index = root / "docs" / "index.md"
    index.write_text(
        index.read_text(encoding="utf-8") + "\n- [Examples](examples/index.md)\n",
        encoding="utf-8",
    )
    add_concept(root, "declared.md", "declared", "direct")
    add_concept(root, "extracted.md", "extracted", "direct")
    add_concept(root, "synthesized.md", "extracted", "synthesized")
    add_concept(root, "inferred.md", "derived", "inferred", status="draft")
    add_concept(root, "verified-inference.md", "derived", "inferred", verified=True)
    return root


def test_all_skills_have_expected_semver() -> None:
    """各Skillが責務変更に応じた版を持つことを確認する。"""

    expected_versions = {
        "project-knowledge": "3.0.0",
        "project-knowledge-audit": "3.0.0",
        "project-knowledge-fast-ask": "2.0.0",
        "project-knowledge-publish": "2.0.0",
    }
    for name in SKILL_NAMES:
        text = (SKILLS_ROOT / name / "SKILL.md").read_text(encoding="utf-8")
        metadata = yaml.safe_load(text.split("---", 2)[1])
        version = metadata["metadata"]["version"]
        assert version == expected_versions[name]
        assert re.fullmatch(r"(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)", version)

    assert not (SKILLS_ROOT / "project-knowledge-verify").exists()


def test_init_writes_current_format(tmp_path: Path) -> None:
    """initが形式1.0と独立したstate schemaを生成することを確認する。"""

    assert run(INIT, tmp_path).returncode == 0
    root = tmp_path / "project-knowledge"
    manifest = yaml.safe_load((root / "manifest.yml").read_text(encoding="utf-8"))
    state = yaml.safe_load((root / "state.yml").read_text(encoding="utf-8"))

    assert manifest == {"format": "project-knowledge", "format_version": "1.0"}
    assert state == {"state_schema_version": 2, "git_baseline_commit": None}


@pytest.mark.parametrize(
    "manifest",
    (
        None,
        "format: [\n",
        'format: another\nformat_version: "1.0"\n',
        'format: project-knowledge\nformat_version: "2.0"\n',
    ),
)
def test_init_rejects_non_current_existing_bundle(
    tmp_path: Path,
    manifest: str | None,
) -> None:
    """initが形式1.0ではない既存Bundleを変更しないことを確認する。"""

    root = tmp_path / "project-knowledge"
    root.mkdir()
    marker = root / "keep.txt"
    marker.write_text("keep", encoding="utf-8")
    if manifest is not None:
        (root / "manifest.yml").write_text(manifest, encoding="utf-8")

    before = {path.name: path.read_bytes() for path in root.iterdir()}
    result = run(INIT, tmp_path)
    after = {path.name: path.read_bytes() for path in root.iterdir()}

    assert result.returncode == 1
    assert before == after


def test_validator_accepts_current_classification(classified_bundle: Path) -> None:
    """形式1.0の分類と検証済み推論を受け付けることを確認する。"""

    result = run(VALIDATE, classified_bundle, "--json")
    assert result.returncode == 0
    assert not any(item["severity"] == "high" for item in json.loads(result.stdout))


def test_validator_treats_rebuildable_state_as_low_severity(
    classified_bundle: Path,
) -> None:
    """再構築可能なstate問題をKnowledge本体の破損と区別する。"""

    state = classified_bundle / "state.yml"
    state.unlink()
    missing = json.loads(run(VALIDATE, classified_bundle, "--json").stdout)
    state.write_text("{broken", encoding="utf-8")
    malformed = json.loads(run(VALIDATE, classified_bundle, "--json").stdout)

    assert {item["code"] for item in missing} >= {"missing-state"}
    assert {item["code"] for item in malformed} >= {"malformed-state"}
    assert all(item["severity"] == "low" for item in missing + malformed)


def test_validator_requires_unverified_inference_to_be_draft(
    classified_bundle: Path,
) -> None:
    """未検証の推論にdraftを要求する。"""

    path = classified_bundle / "docs" / "examples" / "inferred.md"
    path.write_text(
        path.read_text(encoding="utf-8").replace("status: draft", "status: stable"),
        encoding="utf-8",
    )

    result = run(VALIDATE, classified_bundle, "--json")
    codes = {item["code"] for item in json.loads(result.stdout)}
    assert result.returncode == 1
    assert "unverified-inference-not-draft" in codes


def test_validator_rejects_unprefixed_metadata(classified_bundle: Path) -> None:
    """Project Knowledge独自metadataにpk_ prefixを要求する。"""

    path = classified_bundle / "docs" / "examples" / "declared.md"
    path.write_text(
        path.read_text(encoding="utf-8")
        .replace("pk_category:", "category:")
        .replace("pk_derivation:", "derivation:"),
        encoding="utf-8",
    )

    result = run(VALIDATE, classified_bundle, "--json")
    codes = {item["code"] for item in json.loads(result.stdout)}
    assert result.returncode == 1
    assert "unprefixed-project-knowledge-metadata" in codes


def test_validator_checks_source_lifecycle_and_reserved_files(
    classified_bundle: Path,
) -> None:
    """source、lifecycle、OKF予約ファイルを検査する。"""

    concept = classified_bundle / "docs" / "examples" / "declared.md"
    text = concept.read_text(encoding="utf-8")
    concept.write_text(
        text.replace(
            "status: stable",
            "status: obsolete\nstale: 'sometimes'\nstale_after: not-a-date",
        ).replace(
            "sources: []",
            "sources:\n- resource: ../index.md\n  pk_source_type: invalid",
        ),
        encoding="utf-8",
    )
    nested_index = classified_bundle / "docs" / "examples" / "index.md"
    nested_index.write_text(
        "---\ntype: Index\n---\n" + nested_index.read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    result = run(VALIDATE, classified_bundle, "--json")
    codes = {item["code"] for item in json.loads(result.stdout)}
    assert result.returncode == 1
    assert {
        "invalid-source-type",
        "invalid-status",
        "invalid-stale",
        "invalid-stale-after",
        "reserved-file-has-frontmatter",
    } <= codes


def test_validator_rejects_missing_classification(tmp_path: Path) -> None:
    """形式1.0の通常Conceptに分類を要求する。"""

    assert run(INIT, tmp_path).returncode == 0
    root = tmp_path / "project-knowledge"
    examples = root / "docs" / "examples"
    examples.mkdir()
    (examples / "index.md").write_text("# Examples\n\n- [Bad](bad.md)\n", encoding="utf-8")
    index = root / "docs" / "index.md"
    index.write_text(index.read_text(encoding="utf-8") + "\n- [Examples](examples/index.md)\n", encoding="utf-8")
    add_concept(root, "bad.md", None, None)

    result = run(VALIDATE, root, "--json")
    codes = {item["code"] for item in json.loads(result.stdout)}
    assert result.returncode == 1
    assert "invalid-or-missing-classification" in codes


def test_validator_reports_unreadable_knowledge(classified_bundle: Path) -> None:
    """UTF-8として解釈不能なKnowledgeをfindingとして報告する。"""

    concept = classified_bundle / "docs" / "examples" / "declared.md"
    concept.write_bytes(b"\xff\xfe\x00")

    result = run(VALIDATE, classified_bundle, "--json")
    findings = json.loads(result.stdout)

    assert result.returncode == 1
    assert any(
        item["code"] == "unreadable-knowledge"
        and item["path"] == "docs/examples/declared.md"
        for item in findings
    )


def test_validator_reports_unreadable_manifest(classified_bundle: Path) -> None:
    """解釈不能なmanifestを例外にせず形式findingとして報告する。"""

    manifest = classified_bundle / "manifest.yml"
    manifest.write_bytes(b"\xff\xfe\x00")

    result = run(VALIDATE, classified_bundle, "--json")
    codes = {item["code"] for item in json.loads(result.stdout)}

    assert result.returncode == 1
    assert "malformed-manifest" in codes


def test_validator_rejects_source_that_is_not_a_file(
    classified_bundle: Path,
) -> None:
    """存在してもファイルでないsourceを欠落として報告する。"""

    concept = classified_bundle / "docs" / "examples" / "declared.md"
    concept.write_text(
        concept.read_text(encoding="utf-8").replace(
            "sources: []",
            "sources:\n- resource: .\n  pk_source_type: project-artifact",
        ),
        encoding="utf-8",
    )

    result = run(VALIDATE, classified_bundle, "--json")
    codes = {item["code"] for item in json.loads(result.stdout)}

    assert result.returncode == 1
    assert "missing-source-resource" in codes


def test_source_readability_handles_os_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """sourceの読取失敗を例外にせず判定へ変換する。"""

    source = tmp_path / "source.txt"
    source.write_text("evidence", encoding="utf-8")

    def deny_read(path: Path, *_args: object, **_kwargs: object) -> object:
        """テスト対象sourceの読取を拒否する。"""

        if path == source:
            raise PermissionError("denied")
        return original_open(path, *_args, **_kwargs)

    original_open = Path.open
    monkeypatch.setattr(Path, "open", deny_read)

    assert VALIDATOR["is_readable_source"](source) is False


def test_validator_reports_expired_stale_after(
    classified_bundle: Path,
) -> None:
    """期限を過ぎたConceptをstaleとして報告する。"""

    concept = classified_bundle / "docs" / "examples" / "declared.md"
    concept.write_text(
        concept.read_text(encoding="utf-8").replace(
            "status: stable", "status: stable\nstale_after: 2000-01-01"
        ),
        encoding="utf-8",
    )

    result = run(VALIDATE, classified_bundle, "--json")
    findings = json.loads(result.stdout)

    assert result.returncode == 0
    assert any(
        item["code"] == "stale" and item["severity"] == "medium"
        for item in findings
    )


def test_validator_does_not_modify_bundle(classified_bundle: Path) -> None:
    """validatorがKnowledge Bundleを変更しないことを確認する。"""

    before = {
        path.relative_to(classified_bundle): path.read_bytes()
        for path in classified_bundle.rglob("*")
        if path.is_file()
    }

    result = run(VALIDATE, classified_bundle, "--json")
    after = {
        path.relative_to(classified_bundle): path.read_bytes()
        for path in classified_bundle.rglob("*")
        if path.is_file()
    }

    assert result.returncode == 0
    assert before == after
