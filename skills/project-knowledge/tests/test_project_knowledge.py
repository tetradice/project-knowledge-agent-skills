from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

SKILL_ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = SKILL_ROOT.parent
PUBLISH_ROOT = SKILLS_ROOT / "project-knowledge-publish"
AUDIT_ROOT = SKILLS_ROOT / "project-knowledge-audit"
ASK_ROOT = SKILLS_ROOT / "project-knowledge-fast-ask"
HELP_ROOT = SKILLS_ROOT / "project-knowledge-help"
INSPECT_ROOT = SKILLS_ROOT / "project-knowledge-inspect"
POLICY_SETTINGS = "policy_settings.py"


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


def test_init_creates_policy_from_current_template(tmp_path: Path) -> None:
    result = run_script("init_project.py", tmp_path)
    root = tmp_path / "project-knowledge"
    policy = (root / "knowledge-policy.md").read_text(encoding="utf-8")
    template = (SKILL_ROOT / "templates" / "knowledge-policy.md").read_text(
        encoding="utf-8"
    )

    assert result.returncode == 0
    assert policy == template
    assert "knowledge:\n  human_readable: false" in policy
    assert "learning:\n  mode: opportunistic" in policy
    assert policy.split("---", 2)[2].strip() == (
        "Agent Skill `project-knowledge` の標準ポリシーに従います。\n\n"
        "参照: Agent Skill `project-knowledge` 同梱の "
        "`references/standard-knowledge-policy.md`"
    )
    assert "持続的なプロジェクト固有知識を保存する" not in policy
    assert not (root / "config.yml").exists()
    assert not (root / "scope.md").exists()
    assert not (root / "scope.yml").exists()


def test_standard_policy_reference_contains_default_principles() -> None:
    standard_policy = (
        SKILL_ROOT / "references" / "standard-knowledge-policy.md"
    ).read_text(encoding="utf-8")

    # 生成先から分離した標準の保存・除外・構成原則を固定
    assert "持続的なプロジェクト固有知識を保存する" in standard_policy
    assert "将来の利用価値が高い情報を優先する" in standard_policy
    assert "秘密情報などは原則として保存しない" in standard_policy
    assert "対象領域や構成は固定せず" in standard_policy


def test_validator_accepts_freeform_policy_body(tmp_path: Path) -> None:
    run_script("init_project.py", tmp_path)
    root = tmp_path / "project-knowledge"
    policy = root / "knowledge-policy.md"

    # Policy本文は固定タイトルや見出しを要求しない
    policy.write_text(
        "---\nknowledge:\n  human_readable: false\n\n"
        "learning:\n  mode: opportunistic\n---\n\n自由形式のPolicy本文です。\n",
        encoding="utf-8",
    )
    result = run_script("validate_knowledge.py", root, "--json")

    assert result.returncode == 0
    assert json.loads(result.stdout) == []


def test_init_preserves_gitignore_and_ignores_local_state(tmp_path: Path) -> None:
    assert run_script("init_project.py", tmp_path).returncode == 0
    knowledge_root = tmp_path / "project-knowledge"
    gitignore = knowledge_root / ".gitignore"
    gitignore.write_text("custom.local\n", encoding="utf-8")

    result = run_script("init_project.py", tmp_path)

    assert result.returncode == 0
    assert gitignore.read_text(encoding="utf-8") == "custom.local\nstate.yml\n"


def test_init_creates_management_skeleton_only(tmp_path: Path) -> None:
    result = run_script("init_project.py", tmp_path)
    root = tmp_path / "project-knowledge"
    markdown_files = {path.relative_to(root / "docs").as_posix() for path in (root / "docs").rglob("*.md")}

    assert result.returncode == 0
    assert markdown_files == {
        "index.md",
        "log.md",
        "references/index.md",
        "references/user-statements/index.md",
        "references/interactions/index.md",
    }


def test_policy_settings_reads_frontmatter(tmp_path: Path) -> None:
    policy = tmp_path / "knowledge-policy.md"
    policy.write_text(
        "---\nknowledge:\n  human_readable: true\nlearning:\n  mode: aggressive\n---\n# Policy\n",
        encoding="utf-8",
    )
    configured = run_script(POLICY_SETTINGS, policy)

    assert configured.returncode == 0
    assert "knowledge.human_readable: true" in configured.stdout
    assert "learning.mode: aggressive" in configured.stdout


def test_policy_settings_updates_known_keys_only(tmp_path: Path) -> None:
    policy = tmp_path / "knowledge-policy.md"
    body = "# Policy\n\n<!-- keep -->\n本文を保持する。\n"
    policy.write_text(
        "---\ncustom:\n  future: keep\nknowledge:\n  human_readable: false # keep comment\n"
        f"learning:\n  mode: opportunistic\n---\n{body}",
        encoding="utf-8",
    )

    result = run_script(
        POLICY_SETTINGS,
        policy,
        "--human-readable",
        "true",
        "--learning-mode",
        "manual",
    )
    updated = policy.read_text(encoding="utf-8")

    assert result.returncode == 0
    assert "human_readable: true # keep comment" in updated
    assert "mode: manual" in updated
    assert "custom:\n  future: keep" in updated
    assert updated.endswith(body)


def test_policy_settings_preserves_crlf_markdown_body(tmp_path: Path) -> None:
    policy = tmp_path / "knowledge-policy.md"
    body = b"# Policy\r\n\r\nBody\r\n"
    policy.write_bytes(
        b"---\r\nknowledge:\r\n  human_readable: false\r\n"
        b"learning:\r\n  mode: opportunistic\r\n---\r\n" + body
    )

    result = run_script(POLICY_SETTINGS, policy, "--learning-mode", "manual")

    assert result.returncode == 0
    assert policy.read_bytes().endswith(body)


@pytest.mark.parametrize(
    "frontmatter",
    (
        "knowledge: [\n",
        "knowledge:\n  human_readable: maybe\nlearning:\n  mode: opportunistic\n",
        "knowledge:\n  human_readable: false\nlearning:\n  mode: unexpected\n",
    ),
)
def test_policy_settings_stops_on_invalid_frontmatter(
    tmp_path: Path,
    frontmatter: str,
) -> None:
    policy = tmp_path / "knowledge-policy.md"
    original = f"---\n{frontmatter}---\n# Policy\n"
    policy.write_text(original, encoding="utf-8")

    result = run_script(POLICY_SETTINGS, policy, "--learning-mode", "manual")

    assert result.returncode == 2
    assert policy.read_text(encoding="utf-8") == original


def test_policy_settings_requires_frontmatter(tmp_path: Path) -> None:
    policy = tmp_path / "knowledge-policy.md"
    original = "# Policy\n"
    policy.write_text(original, encoding="utf-8")

    result = run_script(POLICY_SETTINGS, policy, "--learning-mode", "manual")

    assert result.returncode == 2
    assert policy.read_text(encoding="utf-8") == original


def test_init_replaces_existing_agents_managed_block(tmp_path: Path) -> None:
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


def test_validator_checks_reference_provenance(tmp_path: Path) -> None:
    run_script("init_project.py", tmp_path)
    root = tmp_path / "project-knowledge"
    reference = root / "docs" / "references" / "user-statements" / "invalid.md"
    reference.write_text(
        "---\ntype: Reference\npk_source_type: invalid\n"
        "generated:\n  by: test\n  at: never\n"
        "---\n\n# Invalid\n",
        encoding="utf-8",
    )

    result = run_script("validate_knowledge.py", root, "--json")
    codes = {finding["code"] for finding in json.loads(result.stdout)}

    assert result.returncode == 1
    assert {
        "invalid-reference-source-type",
        "invalid-generated-actor",
        "invalid-generated-timestamp",
    } <= codes


def test_skill_contract_exposes_maintenance_operations() -> None:
    skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
    operations = {
        line.split("|", 2)[1].strip().strip("`")
        for line in skill.splitlines()
        if line.startswith("| `")
    }
    # 公開操作と対応Referenceの構造をSkill契約として固定
    assert operations == {"init", "update", "verify", "fix", "config"}
    for reference in (
        "init.md",
        "update.md",
        "verification.md",
        "fix.md",
        "config.md",
    ):
        assert (SKILL_ROOT / "references" / reference).is_file()
    assert not (SKILL_ROOT / "references" / "help.md").exists()
    assert "[help.md]" not in skill


def test_help_contract_has_fixed_overview_output() -> None:
    """対象なしhelpの見出し、列、全操作の呼び出し例を固定する。"""

    help_skill = (HELP_ROOT / "SKILL.md").read_text(encoding="utf-8")
    headings = (
        "# Project Knowledge Help",
        "## 基本操作",
        "## 専用Skill",
        "## 詳細ヘルプ",
    )
    positions = [help_skill.index(heading, help_skill.index("## 対象なしの出力")) for heading in headings]
    assert positions == sorted(positions)
    assert "| 操作 | 用途 | 操作名指定 | 自然言語例 |" in help_skill

    for operation in ("init", "update", "verify", "fix", "config"):
        row = next(
            line
            for line in help_skill.splitlines()
            if line.startswith(f"| `{operation}` |")
        )
        cells = [cell.strip() for cell in row.strip("|").split("|")]
        assert len(cells) == 4
        assert f"$project-knowledge {operation}" in cells[2]
        assert cells[3]


def test_help_contract_explains_only_user_facing_specialized_skills() -> None:
    """利用者向け専用Skillと非実行境界を固定する。"""

    help_skill = (HELP_ROOT / "SKILL.md").read_text(encoding="utf-8")
    for skill_name in (
        "project-knowledge-inspect",
        "project-knowledge-fast-ask",
        "project-knowledge-publish",
        "project-knowledge-audit",
        "project-knowledge-benchmark",
    ):
        assert f"| `{skill_name}` |" in help_skill

    assert "$project-knowledge-help publish" in help_skill
    assert "$project-knowledge-inspect" in help_skill
    assert "説明対象の操作やSkillを起動せず" in help_skill
    assert "project-knowledge-scenario-test" not in help_skill


def test_help_contract_has_fixed_target_and_unknown_output() -> None:
    """対象指定時と未知対象時の定型出力、非実行境界を固定する。"""

    help_skill = (HELP_ROOT / "SKILL.md").read_text(encoding="utf-8")
    sections = ("## 用途", "## 書き込み", "## 呼び出し方", "## 主な結果", "## 対象外")

    targeted = help_skill[help_skill.index("## 対象指定ありの出力") : help_skill.index("## 未知の対象の出力")]
    unknown = help_skill[help_skill.index("## 未知の対象の出力") :]
    for output_contract in (targeted, unknown):
        positions = [output_contract.index(section) for section in sections]
        assert positions == sorted(positions)

    for target in ("inspect", "init", "update", "verify", "fix", "config", "fast-ask", "publish", "audit", "refactor", "benchmark"):
        assert f"`{target}`" in unknown
    assert "未知の対象は推測して補正せず" in help_skill
    assert "説明対象の操作やSkillを実行しない" in help_skill


def test_main_skill_routes_legacy_help_without_compatibility_execution() -> None:
    """旧help形式は親Skillで処理せず、新Skillを案内する。"""

    skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
    assert "`$project-knowledge help`" in skill
    assert "`$project-knowledge-help`を案内し、互換実行しない" in skill


def test_inspect_contract_has_fixed_report_shape_without_evaluation() -> None:
    """inspectの出力形式、集計規則、read-only境界をSkill契約として固定する。"""

    inspect = (INSPECT_ROOT / "SKILL.md").read_text(encoding="utf-8")

    # 利用者向けの固定節と、Knowledge文書だけを扱う境界を固定
    for marker in (
        "`プロジェクトナレッジ情報`",
        "`概要`",
        "`構成`",
        "`詳細`",
        "`統計情報`",
        "`ナレッジベースの更新方針`",
        "フォルダツリー形式",
        "rootおよびnested `index.md`",
        "rootおよびnested `log.md`",
        "過去のやり取りの記録（interactions）",
        "ユーザーからの指示の記録（user-statements）",
        "上記以外の参考資料",
        "作成ナレッジ文書",
        "`knowledge.human_readable: false`",
        "`learning.mode: opportunistic`",
        "Project Knowledge外のソースコードや設定",
        "ファイルを作成、更新、削除しない",
    ):
        assert marker in inspect

    assert "内容の正確性、鮮度、構造品質、改善方法は評価せず" in inspect
    assert "検証、監査、修正、構造改善を自動実行しない" in inspect


def test_update_contract_keeps_conversation_summaries_evidence_rich() -> None:
    """会話記録が結論だけの要約へ退行しないことを固定する。"""

    update = (SKILL_ROOT / "references" / "update.md").read_text(encoding="utf-8")

    for marker in (
        "結論だけに圧縮しない",
        "問題の発生から解決または中断までの時系列",
        "判断・制約",
        "実施した調査または操作",
        "観測された結果・エラー",
        "採用または却下した対応",
        "検証結果",
        "未解決または未検証の境界",
        "全文保存が明示された場合",
        "Raw Referenceとして原文を保存する",
    ):
        assert marker in update


def test_init_contract_distinguishes_normal_and_empty_initialization() -> None:
    """通常初期化が調査と根拠付きConcept生成まで行う契約を固定する。"""

    init = (SKILL_ROOT / "references" / "init.md").read_text(encoding="utf-8")

    # 空初期化だけが初期構造の生成後に停止する
    assert "「空で初期化」の明示があれば" in init
    assert "通常の`init`を、骨組みだけで完了としてはならない" in init
    assert "通常の`init`はその後のプロジェクト調査とKnowledge本文の生成まで" in init

    # 通常初期化は代表sourceを調査して保存価値とprovenanceを判定する
    for marker in (
        "READMEと、存在する範囲で代表的なコード、設定、設計資料を調査する",
        "根拠を持つ通常Conceptを1件以上生成する",
        "実在する根拠ファイルを`project-artifact`として参照する",
        "`pk_category: extracted`、`pk_derivation: direct`",
        "`pk_category: extracted`、`pk_derivation: synthesized`",
        "未決定事項を確定済みのstableな事実へ昇格させず",
        "一時的なデバッグ値を保存しない",
    ):
        assert marker in init


def test_verify_contract_defines_ordered_content_health_checks() -> None:
    """verifyの検証順序と結果分類をSkill契約として固定する。"""

    verification = (SKILL_ROOT / "references" / "verification.md").read_text(
        encoding="utf-8"
    )
    phases = (
        "### 1. Structure",
        "### 2. Sources",
        "### 3. Provenance",
        "### 4. Evidence",
        "### 5. Current State",
        "### 6. Freshness",
        "### 7. Consistency",
    )
    positions = [verification.index(phase) for phase in phases]

    assert positions == sorted(positions)
    for result in (
        "pass",
        "fail",
        "warning",
        "not-verifiable",
        "stale",
        "not-applicable",
    ):
        assert f"| `{result}` |" in verification
    assert "High/Medium/Low" in verification
    assert "verify全体を単一の成功・失敗へ畳み込まず" in verification


def test_verify_contract_covers_requested_decision_cases() -> None:
    """代表14ケースの判定規則がSource of Truthに存在することを確認する。"""

    verification = (SKILL_ROOT / "references" / "verification.md").read_text(
        encoding="utf-8"
    )

    for case_id in range(1, 15):
        assert f"| {case_id} |" in verification
    for marker in (
        "`inferred`は変更しない",
        "source errorの`fail`",
        "`implementation-drift`",
        "verifyでは構造findingにせず",
        "fix、audit、refactor、publish、updateを実行しない",
    ):
        assert marker in verification


def test_verify_contract_preserves_provenance_and_read_only_boundaries() -> None:
    """verifyがprovenanceを変更せず他操作を自動実行しないことを確認する。"""

    verification = (SKILL_ROOT / "references" / "verification.md").read_text(
        encoding="utf-8"
    )

    assert "`inferred`を`direct`へ昇格させない" in verification
    assert "ユーザーが情報を発言した事実だけでは`verified`の根拠にならない" in verification
    assert "verify自身は`verified`その他のファイルを書き換えない" in verification
    assert "未登録Knowledgeを探すcoverage調査も行わない" in verification
    assert "`verify`から`fix`、`update`、`audit`、`refactor`、`publish`を自動実行しない" in verification


def test_fix_contract_repairs_content_findings_and_rechecks() -> None:
    """fixの修正範囲、再検査、保守的な境界をSkill契約として固定する。"""

    fix = (SKILL_ROOT / "references" / "fix.md").read_text(encoding="utf-8")

    # verify相当の検査後に明白な問題だけを直し、再検査する
    for marker in (
        "Structure、Sources、Provenance、Evidence、Current State、Freshness、Consistency",
        "sourceやproject artifactから一意に正しい状態を確認できる問題だけを修正する",
        "同じ観点で対象範囲を再検査する",
        "修正しなかったfindingと理由",
    ):
        assert marker in fix

    # updateや構造refactorへ責務を広げず、provenanceを保持する
    assert "`update`は新しい知識、変更された仕様" in fix
    assert "Conceptの大規模な統合・分割" in fix
    assert "sourceと`pk_source_type`を保持する" in fix
    assert "`verified`を自動追加・更新しない" in fix


def test_audit_and_refactor_contract_preserves_safety_boundaries() -> None:
    """auditのread-only境界とrefactorの保守的な改善契約を固定する。"""

    skill = (AUDIT_ROOT / "SKILL.md").read_text(encoding="utf-8")
    audit = (AUDIT_ROOT / "references" / "audit.md").read_text(encoding="utf-8")
    refactor = (AUDIT_ROOT / "references" / "refactor.md").read_text(
        encoding="utf-8"
    )

    assert "| `audit` |" in skill
    assert "| `refactor` |" in skill
    assert "`audit`はread-only" in skill
    assert "一般的な「整理して」「改善して」" in skill
    assert "削除・統合・分割・移動・再編を行わない" in audit

    # 構造改善後の再診断と、意味・source・provenance保持を必須にする
    for marker in (
        "意味・情報・provenanceをできるだけ維持",
        "sourcesを和集合として保持",
        "同じaudit観点で対象範囲を再診断する",
        "複数の妥当な構造案",
        "別操作として自動実行しない",
    ):
        assert marker in refactor


def test_skill_markdown_links_resolve() -> None:
    for skill_root in (SKILL_ROOT, ASK_ROOT, HELP_ROOT, PUBLISH_ROOT, AUDIT_ROOT):
        skill = (skill_root / "SKILL.md").read_text(encoding="utf-8")
        for target in re.findall(r"\]\(([^)]+\.md)\)", skill):
            assert (skill_root / target).is_file()


def test_publish_contract_requires_reader_focused_transformation() -> None:
    """公開時の人間向け変換規則と品質ゲートを固定する。"""

    skill = (PUBLISH_ROOT / "SKILL.md").read_text(encoding="utf-8")
    publishing = (PUBLISH_ROOT / "references" / "publishing.md").read_text(encoding="utf-8")

    assert "機械的にコピーする処理ではない" in skill
    for marker in (
        "略記・キー値表現・圧縮された箇条書き",
        "`status`、`verified`、`stale`",
        "トークン数の削減や増加を成功条件にしない",
        "## 文書単位の品質ゲート",
        "単独で読んでも",
        "変更目的だけの言い換えは避け",
        "再編集した文書と主な編集内容",
        "内容を維持した文書と、そのままで品質ゲートを満たすと判断した理由",
        "公開対象から除外した文書と理由",
    ):
        assert marker in publishing


def test_publish_contract_complements_current_project_artifacts() -> None:
    """公開時の現在構造補完とKnowledge非更新の境界を固定する。"""

    skill = (PUBLISH_ROOT / "SKILL.md").read_text(encoding="utf-8")
    publishing = (PUBLISH_ROOT / "references" / "publishing.md").read_text(encoding="utf-8")

    assert "現在のProject Artifactから確認できる実装構造" in skill
    for marker in (
        "## Project Artifactによる現在構造の補完",
        "全ファイル、全クラス、全メソッドを無差別に列挙せず",
        "実装から確実に判断できない意図、採用理由、仕様、将来方針を推測しない",
        "Knowledgeの記載",
        "現在のProject Artifact",
        "限定的な検索で見つからないことだけを不一致の根拠にしない",
        "User Statement、Interaction Record、Reference",
        "`update`、`verify`、`fix`、`audit`、`refactor`を自動実行しない",
        "汎用コードインデックスや構造キャッシュを作らず",
    ):
        assert marker in publishing


def test_specialized_skills_are_explicit_only() -> None:
    expected_boundaries = (
        ASK_ROOT,
        HELP_ROOT,
        PUBLISH_ROOT,
        AUDIT_ROOT,
    )

    # descriptionとUI policyの両方で暗黙発火を防止
    for skill_root in expected_boundaries:
        skill = (skill_root / "SKILL.md").read_text(encoding="utf-8")
        metadata = (skill_root / "agents" / "openai.yaml").read_text(encoding="utf-8")
        assert "Explicit-only" in skill
        assert "allow_implicit_invocation: false" in metadata


def test_agents_template_routes_specialized_operations_explicitly() -> None:
    template = (SKILL_ROOT / "templates" / "agents-block.md").read_text(encoding="utf-8")

    # init後のAGENTS.mdに新しい責務境界を短く反映
    assert "project-knowledge-fast-ask" in template
    assert "project-knowledge-help" in template
    assert "通常のプロジェクト質問" in template
    assert "正確性検証・修正には`project-knowledge`" in template
    assert "`verify`は検査のみ、`fix`は検査と修正" in template
    assert "`audit`は読み取り専用、`refactor`は構造改善" in template
    for name in (
        "project-knowledge-publish",
        "project-knowledge-audit",
        "project-knowledge-benchmark",
    ):
        assert name in template
    assert "project-knowledge-verify" not in template


def test_detect_changes_without_git(tmp_path: Path) -> None:
    source = tmp_path / "app.txt"
    source.write_text("one", encoding="utf-8")
    snapshot = tmp_path / "project-knowledge" / ".cache" / "source-snapshot.json"

    # snapshot更新は明示時だけ行う
    first = run_script("detect_changes.py", tmp_path)
    assert json.loads(first.stdout)["changed"] == ["app.txt"]
    assert not snapshot.exists()

    written = run_script("detect_changes.py", tmp_path, "--write-snapshot")
    assert written.returncode == 0
    source.write_text("two", encoding="utf-8")
    changed = run_script("detect_changes.py", tmp_path)
    assert json.loads(changed.stdout)["changed"] == ["app.txt"]


@pytest.mark.parametrize("snapshot_content", (b"{broken", b"[]", b"\x80"))
def test_detect_changes_rebuilds_malformed_snapshot(
    tmp_path: Path,
    snapshot_content: bytes,
) -> None:
    source = tmp_path / "app.txt"
    source.write_text("one", encoding="utf-8")
    snapshot = tmp_path / "project-knowledge" / ".cache" / "source-snapshot.json"
    snapshot.parent.mkdir(parents=True)
    snapshot.write_bytes(snapshot_content)

    # 壊れたcacheは空snapshotとして扱い、Knowledge本文には触れない
    result = run_script("detect_changes.py", tmp_path, "--write-snapshot")
    payload = json.loads(result.stdout)

    assert result.returncode == 0
    assert payload["changed"] == ["app.txt"]
    assert json.loads(snapshot.read_text(encoding="utf-8"))["app.txt"]


def test_detect_changes_with_git(tmp_path: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "fixture@example.invalid"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Fixture"], cwd=tmp_path, check=True)
    tracked = tmp_path / "tracked.txt"
    tracked.write_text("one", encoding="utf-8")
    knowledge_root = tmp_path / "project-knowledge"
    knowledge_root.mkdir()
    (knowledge_root / ".gitignore").write_text("state.yml\n.cache/\n", encoding="utf-8")
    subprocess.run(["git", "add", "tracked.txt", "project-knowledge/.gitignore"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "fixture"], cwd=tmp_path, check=True)
    tracked.write_text("two", encoding="utf-8")
    (tmp_path / "staged.txt").write_text("staged", encoding="utf-8")
    subprocess.run(["git", "add", "staged.txt"], cwd=tmp_path, check=True)
    (tmp_path / "untracked.txt").write_text("new", encoding="utf-8")

    # stateなしでは全tracked fileと未commit変更を検出
    result = run_script("detect_changes.py", tmp_path)
    payload = json.loads(result.stdout)

    assert payload["mode"] == "git"
    assert payload["full_scan"] is True
    assert payload["changed"] == ["project-knowledge/.gitignore", "staged.txt", "tracked.txt", "untracked.txt"]

    # checkpointはcommit位置だけを進め、未commit変更は次回も検出
    checkpoint = run_script("detect_changes.py", tmp_path, "--write-baseline")
    state = (tmp_path / "project-knowledge" / "state.yml").read_text(encoding="utf-8")
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=tmp_path, capture_output=True, text=True, check=True
    ).stdout.strip()
    repeated = json.loads(run_script("detect_changes.py", tmp_path).stdout)

    assert checkpoint.returncode == 0
    assert f"git_baseline_commit: {head}" in state
    assert repeated["full_scan"] is False
    assert repeated["changed"] == ["staged.txt", "tracked.txt", "untracked.txt"]


def test_detect_changes_invalidates_non_ancestor_baseline(tmp_path: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "fixture@example.invalid"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Fixture"], cwd=tmp_path, check=True)
    tracked = tmp_path / "tracked.txt"
    tracked.write_text("one", encoding="utf-8")
    knowledge_root = tmp_path / "project-knowledge"
    knowledge_root.mkdir()
    (knowledge_root / ".gitignore").write_text("state.yml\n.cache/\n", encoding="utf-8")
    subprocess.run(["git", "add", "tracked.txt", "project-knowledge/.gitignore"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "first"], cwd=tmp_path, check=True)
    original_branch = subprocess.run(
        ["git", "branch", "--show-current"], cwd=tmp_path, capture_output=True, text=True, check=True
    ).stdout.strip()
    subprocess.run(["git", "branch", "other"], cwd=tmp_path, check=True)
    tracked.write_text("two", encoding="utf-8")
    subprocess.run(["git", "commit", "-qam", "second"], cwd=tmp_path, check=True)
    run_script("detect_changes.py", tmp_path, "--write-baseline")
    state = tmp_path / "project-knowledge" / "state.yml"
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=tmp_path, capture_output=True, text=True, check=True
    ).stdout.strip()

    # 解決可能でも短縮object IDは永続baselineとして使わない
    state.write_text(
        "state_schema_version: 2\n" f"git_baseline_commit: {head[:7]}\n",
        encoding="utf-8",
    )
    abbreviated = json.loads(run_script("detect_changes.py", tmp_path).stdout)
    assert abbreviated["baseline"] is None
    assert abbreviated["full_scan"] is True
    run_script("detect_changes.py", tmp_path, "--write-baseline")

    # branch切替でbaselineがHEADの祖先でなくなればフルスキャンへ戻る
    subprocess.run(["git", "checkout", "-q", "other"], cwd=tmp_path, check=True)
    payload = json.loads(run_script("detect_changes.py", tmp_path).stdout)

    assert original_branch
    assert payload["baseline"] is None
    assert payload["full_scan"] is True
    assert payload["changed"] == ["project-knowledge/.gitignore", "tracked.txt"]

    # rebaseやforce-pushでobjectが消失した場合も同じ復旧経路を使う
    state.write_text(
        "state_schema_version: 2\n" f"git_baseline_commit: {'f' * 40}\n",
        encoding="utf-8",
    )
    missing_object = json.loads(run_script("detect_changes.py", tmp_path).stdout)

    assert missing_object["baseline"] is None
    assert missing_object["full_scan"] is True


def test_offline_config_has_no_external_assets(tmp_path: Path) -> None:
    sys.path.insert(0, str(PUBLISH_ROOT / "scripts"))
    from build_offline_docs import render_config

    # file://配布向けのローカル資産だけを使う
    config = render_config("ナレッジ", tmp_path / "docs", tmp_path / "html")
    assert "offline" in config
    assert "use_directory_urls: false" in config
    assert "http://" not in config
    assert "https://" not in config
