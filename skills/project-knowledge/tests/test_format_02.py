from __future__ import annotations

import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

SKILL_ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = SKILL_ROOT.parent
MIGRATE = SKILL_ROOT / "scripts" / "migrate_project.py"
INIT = SKILL_ROOT / "scripts" / "init_project.py"
VALIDATE = SKILLS_ROOT / "project-knowledge-verify" / "scripts" / "validate_knowledge.py"
SKILL_NAMES = (
    "project-knowledge",
    "project-knowledge-fast-ask",
    "project-knowledge-publish",
    "project-knowledge-verify",
    "project-knowledge-audit",
)


def run(script: Path, *args: object) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(script), *(str(arg) for arg in args)],
        capture_output=True,
        text=True,
        check=False,
    )


def snapshot(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }


def write_legacy_bundle(project: Path) -> Path:
    root = project / "project-knowledge"
    captures = root / "docs" / "references" / "captures"
    memos = root / "docs" / "references" / "memos"
    captures.mkdir(parents=True)
    memos.mkdir(parents=True)
    (root / "config.yml").write_text(
        "# preserved comment\nlearning:\n  mode: opportunistic\n"
        "memo:\n  require_approval_for_trust: true\ncustom_key: keep\n",
        encoding="utf-8",
    )
    (root / "state.yml").write_text(
        "version: 1\nlast_update_at: null\n", encoding="utf-8"
    )
    (root / "knowledge-policy.md").write_text(
        "# プロジェクトKnowledge Policy\n\n"
        "## 基本方針\nKeep useful knowledge.\n\n"
        "## 積極的に保存する情報\nDurable facts.\n\n"
        "## 原則として保存しない情報\nSecrets.\n\n"
        "## 構成方針\nUse indexes.\n",
        encoding="utf-8",
    )
    (root / "docs" / "index.md").write_text(
        "---\ntitle: Legacy\nversion: 0.1\n---\n\n# Legacy\n\n"
        "- [Topic](topic.md)\n- [References](references/index.md)\n",
        encoding="utf-8",
    )
    (root / "docs" / "log.md").write_text(
        "---\ntitle: Log\n---\n\n# Change Log\n\n## 2026-08-20\n\nLegacy.\n",
        encoding="utf-8",
    )
    (root / "docs" / "topic.md").write_text(
        "---\ntitle: Topic\nversion: 7\nstatus: stable\n"
        "generated:\n  by: project-knowledge\n  at: 2026-08-20T00:00:00+09:00\n"
        "sources:\n  - resource: references/captures/statement.md\n"
        "    pk_source_kind: capture\n    pk_authority: primary\n    pk_trust: trusted\n"
        "---\n\n# Topic\n",
        encoding="utf-8",
    )
    (root / "docs" / "references" / "index.md").write_text(
        "---\ntitle: References\n---\n\n# References\n\n"
        "- [Captures](captures/index.md)\n- [Memos](memos/index.md)\n",
        encoding="utf-8",
    )
    (captures / "index.md").write_text(
        "---\ntitle: Captures\n---\n\n# Captures\n\n- [Statement](statement.md)\n",
        encoding="utf-8",
    )
    (memos / "index.md").write_text(
        "---\ntitle: Memos\n---\n\n# Memos\n\n- [Interaction](interaction.md)\n",
        encoding="utf-8",
    )
    event = (
        "generated:\n  by: project-knowledge\n"
        "  at: 2026-08-20T00:00:00+09:00\n"
    )
    (captures / "statement.md").write_text(
        "---\ntitle: Statement\npk_source_kind: capture\n"
        "pk_authority: primary\npk_trust: trusted\n"
        f"{event}---\n\n# Statement\n",
        encoding="utf-8",
    )
    (memos / "interaction.md").write_text(
        "---\ntitle: Interaction\npk_source_kind: memo\n"
        "pk_authority: secondary\npk_trust: provisional\n"
        f"{event}---\n\n# Interaction\n",
        encoding="utf-8",
    )
    return root


def add_concept(
    root: Path,
    filename: str,
    category: str | None,
    derivation: str | None,
    status: str = "stable",
    verified: bool = False,
) -> None:
    metadata: dict[str, object] = {
        "type": "Test Concept",
        "status": status,
        "generated": {
            "by": "project-knowledge/0.2.0",
            "at": "2026-08-26T00:00:00+09:00",
        },
        "sources": [],
    }
    if category is not None:
        metadata["category"] = category
    if derivation is not None:
        metadata["derivation"] = derivation
    if verified:
        metadata["verified"] = {
            "by": "human:reviewer",
            "at": "2026-08-26T00:10:00+09:00",
        }
    path = root / "docs" / "examples" / filename
    frontmatter = yaml.safe_dump(metadata, sort_keys=False, allow_unicode=True).rstrip()
    path.write_text(
        f"---\n{frontmatter}\n---\n\n# {filename}\n", encoding="utf-8"
    )


@pytest.fixture
def classified_bundle(tmp_path: Path) -> Path:
    assert run(INIT, tmp_path, "--empty").returncode == 0
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
    add_concept(
        root,
        "verified-inference.md",
        "derived",
        "inferred",
        status="stable",
        verified=True,
    )
    return root


def test_all_skills_have_independent_semver() -> None:
    expected_versions = {
        "project-knowledge": "0.3.0",
        "project-knowledge-audit": "0.2.0",
        "project-knowledge-fast-ask": "0.2.0",
        "project-knowledge-publish": "0.2.0",
        "project-knowledge-verify": "0.2.0",
    }

    # Skillごとに独立した現在の版とSemVer形式を検証
    for name in SKILL_NAMES:
        text = (SKILLS_ROOT / name / "SKILL.md").read_text(encoding="utf-8")
        metadata = yaml.safe_load(text.split("---", 2)[1])
        version = metadata["metadata"]["version"]
        assert version == expected_versions[name]
        assert re.fullmatch(
            r"(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)",
            version,
        )


def test_init_writes_separate_quoted_versions(tmp_path: Path) -> None:
    assert run(INIT, tmp_path, "--empty").returncode == 0
    root = tmp_path / "project-knowledge"
    manifest = (root / "manifest.yml").read_text(encoding="utf-8")
    state = yaml.safe_load((root / "state.yml").read_text(encoding="utf-8"))
    index = yaml.safe_load(
        (root / "docs" / "index.md").read_text(encoding="utf-8").split("---", 2)[1]
    )
    assert 'format_version: "0.2"' in manifest
    assert yaml.safe_load(manifest) == {
        "format": "project-knowledge",
        "format_version": "0.2",
    }
    assert state["state_schema_version"] == 1
    assert "version" not in state
    assert index == {"okf_version": "0.2"}


def test_migration_check_apply_and_idempotency(tmp_path: Path) -> None:
    root = write_legacy_bundle(tmp_path)
    before = snapshot(root)
    checked = run(MIGRATE, tmp_path, "--check")
    assert checked.returncode == 0
    assert "migration chain: 0.1 -> 0.2" in checked.stdout
    assert snapshot(root) == before

    applied = run(MIGRATE, tmp_path)
    assert applied.returncode == 0
    assert (root / "manifest.yml").is_file()
    assert not (root / "docs" / "references" / "captures").exists()
    assert not (root / "docs" / "references" / "memos").exists()
    statement = root / "docs" / "references" / "user-statements" / "statement.md"
    topic = (root / "docs" / "topic.md").read_text(encoding="utf-8")
    assert statement.is_file()
    assert "pk_source_type: user-statement" in statement.read_text(encoding="utf-8")
    assert "pk_authority" not in topic
    assert "pk_trust" not in topic
    assert "pk_legacy_unclassified: true" in topic
    assert "version: 7" in topic
    assert "by: project-knowledge/0.1.0" in topic
    assert 'okf_version: "0.2"' in (root / "docs" / "index.md").read_text(encoding="utf-8")
    assert "references/user-statements/statement.md" in topic
    assert "state_schema_version: 1" in (root / "state.yml").read_text(encoding="utf-8")
    assert "require_approval_for_trust" not in (root / "config.yml").read_text(encoding="utf-8")
    assert "# preserved comment" in (root / "config.yml").read_text(encoding="utf-8")
    assert "custom_key: keep" in (root / "config.yml").read_text(encoding="utf-8")

    migrated = snapshot(root)
    repeated = run(MIGRATE, tmp_path)
    assert repeated.returncode == 0
    assert "already at target" in repeated.stdout
    assert snapshot(root) == migrated

    validated = run(VALIDATE, root, "--json")
    assert validated.returncode == 0
    assert not any(item["severity"] == "high" for item in json.loads(validated.stdout))


def test_init_automatically_migrates_legacy_before_writing(tmp_path: Path) -> None:
    root = write_legacy_bundle(tmp_path)
    result = run(INIT, tmp_path)
    assert result.returncode == 0
    assert yaml.safe_load((root / "manifest.yml").read_text(encoding="utf-8"))[
        "format_version"
    ] == "0.2"
    assert (root / "docs" / "references" / "user-statements").is_dir()


def test_migration_merges_identical_destination(tmp_path: Path) -> None:
    root = write_legacy_bundle(tmp_path)
    source = root / "docs" / "references" / "captures" / "statement.md"
    destination = root / "docs" / "references" / "user-statements" / "statement.md"
    destination.parent.mkdir()
    destination.write_bytes(source.read_bytes())

    result = run(MIGRATE, tmp_path)
    assert result.returncode == 0
    assert destination.is_file()
    assert not source.exists()


def test_migration_conflict_changes_nothing(tmp_path: Path) -> None:
    root = write_legacy_bundle(tmp_path)
    destination = root / "docs" / "references" / "user-statements" / "statement.md"
    destination.parent.mkdir()
    destination.write_text("different", encoding="utf-8")
    before = snapshot(root)

    result = run(MIGRATE, tmp_path)
    assert result.returncode == 2
    assert "conflicts" in result.stdout
    assert snapshot(root) == before
    assert not (root / "manifest.yml").exists()


@pytest.mark.parametrize(
    ("manifest", "target", "message"),
    [
        ("format: [\n", "0.2", "malformed YAML"),
        ('format: another\nformat_version: "0.2"\n', "0.2", "unsupported manifest format"),
        ('format: project-knowledge\nformat_version: "0.3"\n', "0.2", "not supported"),
    ],
)
def test_migration_rejects_malformed_unknown_and_newer_formats(
    tmp_path: Path, manifest: str, target: str, message: str
) -> None:
    root = tmp_path / "project-knowledge"
    root.mkdir()
    (root / "manifest.yml").write_text(manifest, encoding="utf-8")
    before = snapshot(root)
    result = run(MIGRATE, tmp_path, "--target", target)
    assert result.returncode == 2
    assert message in result.stderr
    assert snapshot(root) == before


def test_migration_rejects_downgrade_and_version_skip(tmp_path: Path) -> None:
    assert run(INIT, tmp_path, "--empty").returncode == 0
    downgrade = run(MIGRATE, tmp_path, "--target", "0.1")
    assert downgrade.returncode == 2
    assert "downgrade" in downgrade.stderr

    legacy_project = tmp_path / "legacy"
    write_legacy_bundle(legacy_project)
    skipped = run(MIGRATE, legacy_project, "--target", "0.3")
    assert skipped.returncode == 2
    assert "no migration chain" in skipped.stderr


def test_unknown_manifestless_directory_is_not_guessed_as_legacy(tmp_path: Path) -> None:
    root = tmp_path / "project-knowledge"
    root.mkdir()
    (root / "unknown.txt").write_text("keep", encoding="utf-8")
    before = snapshot(root)
    migration = run(MIGRATE, tmp_path)
    initialization = run(INIT, tmp_path)
    assert migration.returncode == 2
    assert initialization.returncode == 1
    assert snapshot(root) == before


def test_registry_references_have_matching_documents() -> None:
    spec = importlib.util.spec_from_file_location("pk_migrate", MIGRATE)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    for relative in module.DATA_FORMAT_REGISTRY.values():
        assert (SKILL_ROOT / relative).is_file()
    for relative in module.MIGRATION_REGISTRY.values():
        assert (SKILL_ROOT / relative).is_file()
    documented_formats = {
        path.stem for path in (SKILL_ROOT / "references" / "data-formats").glob("*.md")
    }
    assert documented_formats == set(module.DATA_FORMAT_REGISTRY)
    documented_migrations = {
        path.relative_to(SKILL_ROOT).as_posix()
        for path in (SKILL_ROOT / "references" / "migrations").glob("*.md")
    }
    assert documented_migrations == set(module.MIGRATION_REGISTRY.values())


def test_validator_accepts_four_classification_cases_and_verified_inference(
    classified_bundle: Path,
) -> None:
    result = run(VALIDATE, classified_bundle, "--json")
    assert result.returncode == 0
    assert not any(item["severity"] == "high" for item in json.loads(result.stdout))


def test_validator_requires_unverified_inference_to_be_draft(
    classified_bundle: Path,
) -> None:
    path = classified_bundle / "docs" / "examples" / "inferred.md"
    path.write_text(
        path.read_text(encoding="utf-8").replace("status: draft", "status: stable"),
        encoding="utf-8",
    )
    result = run(VALIDATE, classified_bundle, "--json")
    codes = {item["code"] for item in json.loads(result.stdout)}
    assert result.returncode == 1
    assert "unverified-inference-not-draft" in codes


def test_user_statement_does_not_imply_human_verification(tmp_path: Path) -> None:
    assert run(INIT, tmp_path, "--empty").returncode == 0
    root = tmp_path / "project-knowledge"
    path = root / "docs" / "references" / "user-statements" / "statement.md"
    path.write_text(
        "---\ntype: Reference\npk_source_type: user-statement\n"
        "generated:\n  by: project-knowledge/0.2.0\n"
        "  at: 2026-08-26T00:00:00+09:00\n---\n\n# Statement\n",
        encoding="utf-8",
    )
    index = path.parent / "index.md"
    index.write_text(index.read_text(encoding="utf-8") + "\n- [Statement](statement.md)\n", encoding="utf-8")
    result = run(VALIDATE, root, "--json")
    codes = {item["code"] for item in json.loads(result.stdout)}
    assert result.returncode == 0
    assert "missing-verified" not in codes


def test_validator_checks_source_type_status_and_stale(classified_bundle: Path) -> None:
    path = classified_bundle / "docs" / "examples" / "declared.md"
    text = path.read_text(encoding="utf-8")
    text = text.replace(
        "status: stable",
        "status: obsolete\nstale: 'sometimes'\nstale_after: not-a-date",
    ).replace(
        "sources: []",
        "sources:\n- resource: ../index.md\n  pk_source_type: invalid",
    )
    path.write_text(text, encoding="utf-8")
    result = run(VALIDATE, classified_bundle, "--json")
    codes = {item["code"] for item in json.loads(result.stdout)}
    assert result.returncode == 1
    assert {"invalid-source-type", "invalid-status", "invalid-stale", "invalid-stale-after"} <= codes


def test_validator_enforces_okf_reserved_files(classified_bundle: Path) -> None:
    nested_index = classified_bundle / "docs" / "examples" / "index.md"
    nested_index.write_text(
        "---\ntype: Index\n---\n" + nested_index.read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    log = classified_bundle / "docs" / "log.md"
    log.write_text(
        log.read_text(encoding="utf-8") + "\n## 2026-08-26 — invalid\n",
        encoding="utf-8",
    )
    result = run(VALIDATE, classified_bundle, "--json")
    codes = {item["code"] for item in json.loads(result.stdout)}
    assert result.returncode == 1
    assert {"reserved-file-has-frontmatter", "invalid-log-date-heading"} <= codes


def test_legacy_classification_gap_warns_but_new_gap_fails(tmp_path: Path) -> None:
    legacy = write_legacy_bundle(tmp_path / "legacy")
    legacy_topic = legacy / "docs" / "topic.md"
    legacy_topic.write_text(
        legacy_topic.read_text(encoding="utf-8").replace("title: Topic\n", "type: Knowledge\n"),
        encoding="utf-8",
    )
    legacy_result = run(VALIDATE, legacy, "--json")
    legacy_findings = json.loads(legacy_result.stdout)
    assert legacy_result.returncode == 0
    assert any(item["code"] == "legacy-unclassified-concept" for item in legacy_findings)

    assert run(INIT, tmp_path / "current", "--empty").returncode == 0
    current = tmp_path / "current" / "project-knowledge"
    examples = current / "docs" / "examples"
    examples.mkdir()
    (examples / "index.md").write_text("# Examples\n\n- [Bad](bad.md)\n", encoding="utf-8")
    root_index = current / "docs" / "index.md"
    root_index.write_text(root_index.read_text(encoding="utf-8") + "\n- [Examples](examples/index.md)\n", encoding="utf-8")
    add_concept(current, "bad.md", None, None)
    current_result = run(VALIDATE, current, "--json")
    current_codes = {item["code"] for item in json.loads(current_result.stdout)}
    assert current_result.returncode == 1
    assert "invalid-or-missing-classification" in current_codes
