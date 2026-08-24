from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = SKILL_ROOT.parent
PUBLISH_ROOT = SKILLS_ROOT / "project-knowledge-publish"
VERIFY_ROOT = SKILLS_ROOT / "project-knowledge-verify"
AUDIT_ROOT = SKILLS_ROOT / "project-knowledge-audit"
ASK_ROOT = SKILLS_ROOT / "project-knowledge-fast-ask"


def run_script(name: str, *args: object, skill_root: Path = SKILL_ROOT) -> subprocess.CompletedProcess[str]:
    # 所有Skillのscriptsから対象コマンドを実行
    return subprocess.run(
        [sys.executable, str(skill_root / "scripts" / name), *(str(arg) for arg in args)],
        capture_output=True,
        text=True,
        check=False,
    )


def test_init_without_scope_is_idempotent_and_preserves_agents(tmp_path: Path) -> None:
    agents = tmp_path / "AGENTS.md"
    agents.write_text("# Existing\n", encoding="utf-8")

    # scope指定なしで二度初期化し、既存指示とナレッジを保持
    first = run_script("init_project.py", tmp_path)
    index_before = (tmp_path / "project-knowledge" / "docs" / "index.md").read_text(encoding="utf-8")
    second = run_script("init_project.py", tmp_path)

    assert first.returncode == 0
    assert second.returncode == 0
    assert "# Existing" in agents.read_text(encoding="utf-8")
    assert agents.read_text(encoding="utf-8").count("<!-- project-knowledge:start -->") == 1
    assert (tmp_path / "project-knowledge" / "docs" / "index.md").read_text(encoding="utf-8") == index_before


def test_init_creates_open_world_policy_and_opportunistic_config(tmp_path: Path) -> None:
    result = run_script("init_project.py", tmp_path)
    root = tmp_path / "project-knowledge"
    policy = (root / "knowledge-policy.md").read_text(encoding="utf-8")
    config = (root / "config.yml").read_text(encoding="utf-8")

    assert result.returncode == 0
    assert "対象領域のallow-listではない" in policy
    assert "## 積極的に保存する情報" in policy
    assert "mode: opportunistic" in config
    assert not (root / "scope.md").exists()
    assert not (root / "scope.yml").exists()


def test_empty_init_creates_management_skeleton_only(tmp_path: Path) -> None:
    result = run_script("init_project.py", tmp_path, "--empty")
    root = tmp_path / "project-knowledge"
    markdown_files = {path.relative_to(root / "docs").as_posix() for path in (root / "docs").rglob("*.md")}

    assert result.returncode == 0
    assert "no ナレッジ pages were generated" in result.stdout
    assert markdown_files == {
        "index.md",
        "log.md",
        "references/index.md",
        "references/captures/index.md",
        "references/memos/index.md",
    }


def test_deprecated_scope_argument_is_not_persisted_as_boundary(tmp_path: Path) -> None:
    result = run_script("init_project.py", tmp_path, "--scope", "アプリケーション概要")
    policy = (tmp_path / "project-knowledge" / "knowledge-policy.md").read_text(encoding="utf-8")

    assert result.returncode == 0
    assert "--scope is deprecated" in result.stdout
    assert "アプリケーション概要" not in policy


def test_init_migrates_known_legacy_scope_yaml_to_policy(tmp_path: Path) -> None:
    root = tmp_path / "project-knowledge"
    root.mkdir()
    (root / "scope.yml").write_text(
        "version: 1\n"
        "topics:\n"
        "  - id: application-overview\n"
        "    description: アプリケーション概要\n"
        "exclude:\n"
        "  - 低レベルな実装詳細\n",
        encoding="utf-8",
    )

    # 対象は候補へ、除外は品質方針へ変換
    result = run_script("init_project.py", tmp_path)
    policy = (root / "knowledge-policy.md").read_text(encoding="utf-8")

    assert result.returncode == 0
    assert "旧scopeの対象指定はナレッジ領域を限定するものではなく" in policy
    assert "- アプリケーション概要" in policy
    assert "- 低レベルな実装詳細" in policy
    assert not (root / "scope.yml").exists()


def test_init_migrates_known_legacy_scope_markdown_to_policy(tmp_path: Path) -> None:
    root = tmp_path / "project-knowledge"
    root.mkdir()
    (root / "scope.md").write_text(
        "---\nversion: 1\nstatus: active\nexpansion: explicit-only\n---\n\n"
        "# プロジェクトナレッジ Scope\n\n## 対象\n\n- デプロイ方式\n\n"
        "## 原則として対象外\n\n- メソッド単位の網羅的仕様\n",
        encoding="utf-8",
    )

    result = run_script("init_project.py", tmp_path)
    policy = (root / "knowledge-policy.md").read_text(encoding="utf-8")

    assert result.returncode == 0
    assert "- デプロイ方式" in policy
    assert "- メソッド単位の網羅的仕様" in policy
    assert not (root / "scope.md").exists()


def test_init_preserves_unknown_legacy_scope(tmp_path: Path) -> None:
    root = tmp_path / "project-knowledge"
    root.mkdir()
    legacy = root / "scope.yml"
    legacy.write_text("version: 2\nrules:\n  preserve: true\n", encoding="utf-8")

    result = run_script("init_project.py", tmp_path)

    assert result.returncode == 1
    assert legacy.read_text(encoding="utf-8") == "version: 2\nrules:\n  preserve: true\n"
    assert not (root / "knowledge-policy.md").exists()


def test_init_migrates_legacy_learning_boolean(tmp_path: Path) -> None:
    for legacy_value, expected_mode in (("true", "opportunistic"), ("false", "manual")):
        project = tmp_path / legacy_value
        root = project / "project-knowledge"
        root.mkdir(parents=True)
        (root / "config.yml").write_text(
            "knowledge:\n  human_readable: false\nupdate:\n"
            f"  automatic_after_work: {legacy_value}\n",
            encoding="utf-8",
        )

        # true/falseを対応するmodeへ変換し、空の旧updateキーを残さない
        result = run_script("init_project.py", project)
        config = (root / "config.yml").read_text(encoding="utf-8")

        assert result.returncode == 0
        assert "automatic_after_work" not in config
        assert "update:" not in config
        assert f"learning:\n  mode: {expected_mode}" in config


def test_init_replaces_legacy_agents_managed_block(tmp_path: Path) -> None:
    agents = tmp_path / "AGENTS.md"
    agents.write_text(
        "# Existing\n\n<!-- project-knowledge:start -->\nold scope rule\n<!-- project-knowledge:end -->\n",
        encoding="utf-8",
    )

    result = run_script("init_project.py", tmp_path)
    text = agents.read_text(encoding="utf-8")

    assert result.returncode == 0
    assert "# Existing" in text
    assert "knowledge-policy.md" in text
    assert "old scope rule" not in text


def test_validator_is_read_only_and_does_not_inspect_scope(tmp_path: Path) -> None:
    run_script("init_project.py", tmp_path)
    root = tmp_path / "project-knowledge"
    (root / "scope.md").write_text("legacy file", encoding="utf-8")
    before = {path: path.read_bytes() for path in root.rglob("*") if path.is_file()}

    result = run_script("validate_knowledge.py", root, "--json", skill_root=VERIFY_ROOT)
    after = {path: path.read_bytes() for path in root.rglob("*") if path.is_file()}

    assert result.returncode == 0
    assert json.loads(result.stdout) == []
    assert before == after


def test_validator_checks_reference_provenance(tmp_path: Path) -> None:
    run_script("init_project.py", tmp_path)
    root = tmp_path / "project-knowledge"
    capture = root / "docs" / "references" / "captures" / "invalid.md"
    capture.write_text(
        "---\ntitle: Invalid\ndescription: Invalid capture\nversion: \"0.1.0\"\n"
        "generated:\n  by: test\npk_source_kind: memo\npk_authority: secondary\npk_trust: provisional\n"
        "---\n\n# Invalid\n",
        encoding="utf-8",
    )

    result = run_script("validate_knowledge.py", root, "--json", skill_root=VERIFY_ROOT)
    codes = {finding["code"] for finding in json.loads(result.stdout)}

    assert result.returncode == 1
    assert {"invalid-pk-source-kind", "invalid-pk-authority", "invalid-pk-trust"} <= codes


def test_skill_contract_exposes_update_centered_operations() -> None:
    skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
    operations = {
        line.split("|", 2)[1].strip().strip("`")
        for line in skill.splitlines()
        if line.startswith("| `")
    }
    learning = (SKILL_ROOT / "references" / "learning-modes.md").read_text(encoding="utf-8")

    # 公開操作と自動学習の主要な安全境界をSkill契約として固定
    assert operations == {"update", "init", "config"}
    assert "質問回答、成果物生成、網羅的な検証、構造監査は扱わない" in skill
    for removed_reference in ("ask.md", "publishing.md", "verification.md", "audit.md"):
        assert not (SKILL_ROOT / "references" / removed_reference).exists()
    assert not (SKILL_ROOT / "references" / "capture.md").exists()
    assert not (SKILL_ROOT / "references" / "memo.md").exists()
    assert not (SKILL_ROOT / "references" / "scope.md").exists()
    assert "作業単位の完了時" in learning
    assert "毎ターン" in learning
    assert "typo" in learning


def test_update_contract_covers_provenance_policy_and_incremental_flow() -> None:
    update = (SKILL_ROOT / "references" / "update.md").read_text(encoding="utf-8")
    provenance = (SKILL_ROOT / "references" / "provenance.md").read_text(encoding="utf-8")
    policy = (SKILL_ROOT / "templates" / "knowledge-policy.md").read_text(encoding="utf-8")
    verification = (VERIFY_ROOT / "references" / "verification.md").read_text(encoding="utf-8")
    audit = (AUDIT_ROOT / "references" / "audit.md").read_text(encoding="utf-8")

    # 依頼された意味的シナリオを構成する各契約が保守されていることを確認
    assert "user assertion" in update
    assert "conversation-derived" in update
    assert "detect_changes.py" in update
    assert "毎回全体を再解析しない" in update
    assert "収集方針" in update
    assert "pk_source_kind: capture" in provenance
    assert "pk_authority: primary" in provenance
    assert "pk_trust: trusted" in provenance
    assert "pk_source_kind: memo" in provenance
    assert "pk_authority: secondary" in provenance
    assert "pk_trust: provisional" in provenance
    assert "対象領域およびページ構成は固定しない" in policy
    assert "ナレッジ Policy" in verification
    assert "provenance" in verification
    assert "ナレッジ Policy" in audit
    assert "scope" not in verification.lower()
    assert "scope" not in audit.lower()


def test_specialized_skills_are_explicit_only_and_do_not_auto_chain() -> None:
    expected_boundaries = {
        ASK_ROOT: ("project-knowledge/docs/**", "フォールバックせず"),
        PUBLISH_ROOT: ("Markdown", "逆同期せず"),
        VERIFY_ROOT: ("read-only", "更新を自動実行しない"),
        AUDIT_ROOT: ("read-only", "改善を自動実行しない"),
    }

    # descriptionとUI policyの両方で暗黙発火を防止
    for skill_root, required_text in expected_boundaries.items():
        skill = (skill_root / "SKILL.md").read_text(encoding="utf-8")
        metadata = (skill_root / "agents" / "openai.yaml").read_text(encoding="utf-8")
        assert "Explicit-only" in skill
        assert "allow_implicit_invocation: false" in metadata
        assert all(value in skill for value in required_text)


def test_agents_template_routes_specialized_operations_explicitly() -> None:
    template = (SKILL_ROOT / "templates" / "agents-block.md").read_text(encoding="utf-8")

    # init後のAGENTS.mdに新しい責務境界を短く反映
    assert "project-knowledge-fast-ask" in template
    assert "通常のプロジェクト質問" in template
    for name in ("project-knowledge-publish", "project-knowledge-verify", "project-knowledge-audit"):
        assert name in template


def test_detect_changes_without_git(tmp_path: Path) -> None:
    source = tmp_path / "app.txt"
    source.write_text("one", encoding="utf-8")
    snapshot = tmp_path / "snapshot.json"

    # snapshot更新は明示時だけ行う
    first = run_script("detect_changes.py", tmp_path, "--snapshot", snapshot)
    assert json.loads(first.stdout)["changed"] == ["app.txt"]
    assert not snapshot.exists()

    run_script("detect_changes.py", tmp_path, "--snapshot", snapshot, "--write-state")
    source.write_text("two", encoding="utf-8")
    changed = run_script("detect_changes.py", tmp_path, "--snapshot", snapshot)
    assert json.loads(changed.stdout)["changed"] == ["app.txt"]


def test_detect_changes_with_git(tmp_path: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "fixture@example.invalid"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Fixture"], cwd=tmp_path, check=True)
    tracked = tmp_path / "tracked.txt"
    tracked.write_text("one", encoding="utf-8")
    subprocess.run(["git", "add", "tracked.txt"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "fixture"], cwd=tmp_path, check=True)
    tracked.write_text("two", encoding="utf-8")
    (tmp_path / "untracked.txt").write_text("new", encoding="utf-8")

    # Git環境ではworking treeとuntrackedを検出
    result = run_script("detect_changes.py", tmp_path)
    payload = json.loads(result.stdout)

    assert payload["mode"] == "git"
    assert payload["changed"] == ["tracked.txt", "untracked.txt"]


def test_offline_config_has_no_external_assets(tmp_path: Path) -> None:
    sys.path.insert(0, str(PUBLISH_ROOT / "scripts"))
    from build_offline_docs import render_config

    # file://配布向けのローカル資産だけを使う
    config = render_config("ナレッジ", tmp_path / "docs", tmp_path / "html")
    assert "offline" in config
    assert "use_directory_urls: false" in config
    assert "http://" not in config
    assert "https://" not in config
