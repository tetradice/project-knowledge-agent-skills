from __future__ import annotations

import runpy
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

SKILL_ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = SKILL_ROOT.parent
RUNNER_PATH = SKILL_ROOT / "scripts" / "scenario_test.py"
RUNNER = runpy.run_path(str(RUNNER_PATH))
INIT = SKILLS_ROOT / "project-knowledge" / "scripts" / "init_project.py"
FIXTURE = SKILL_ROOT / "scenarios" / "quick-basic" / "fixture"


def prepare() -> Path:
    """Quick Fixtureの一時workspaceを作成する。"""

    return RUNNER["prepare"]("quick-basic")


def initialize_knowledge(workspace: Path) -> None:
    """既存scriptで空のProject Knowledgeを初期化する。"""

    result = subprocess.run(
        [sys.executable, str(INIT), str(workspace)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def valid_judge() -> dict[str, object]:
    """全観点PASSのJudge結果を作成する。"""

    dimensions = {
        name: {"result": "PASS", "reason": "sourceと一致", "evidence": ["README.md"]}
        for name in RUNNER["DIMENSIONS"]
    }
    return {"result": "PASS", "dimensions": dimensions, "issues": []}


def test_prepare_isolates_fixture_and_initializes_git() -> None:
    """prepareが元Fixtureを変えずにGit workspaceを作ることを確認する。"""

    fixture_hash = RUNNER["tree_hash"](FIXTURE)
    workspace = prepare()
    try:
        assert (workspace / ".git").is_dir()
        assert (workspace / "README.md").is_file()
        assert not (workspace.parent / "expectations.yml").exists()
        assert RUNNER["tree_hash"](FIXTURE) == fixture_hash
        commit = subprocess.run(
            ["git", "rev-parse", "--verify", "HEAD"],
            cwd=workspace,
            capture_output=True,
            text=True,
            check=False,
        )
        assert commit.returncode == 0
    finally:
        RUNNER["cleanup"](workspace)


def test_validate_reuses_current_project_knowledge_validator() -> None:
    """現行形式の空Bundleがdeterministic validationを通ることを確認する。"""

    workspace = prepare()
    try:
        initialize_knowledge(workspace)
        result = RUNNER["validate"](workspace)
        assert result["status"] == "PASS"
        assert result["error"] is None
        assert not any(item["severity"] == "high" for item in result["findings"])
    finally:
        RUNNER["cleanup"](workspace)


def test_validate_detects_actor_source_mutation() -> None:
    """ActorがFixture sourceを変更した場合にFAILとすることを確認する。"""

    workspace = prepare()
    try:
        initialize_knowledge(workspace)
        readme = workspace / "README.md"
        readme.write_text(readme.read_text(encoding="utf-8") + "\nchanged\n", encoding="utf-8")
        result = RUNNER["validate"](workspace)
        assert result["status"] == "FAIL"
        assert "source-project-modified" in {item["code"] for item in result["findings"]}
    finally:
        RUNNER["cleanup"](workspace)


def test_validate_rejects_source_outside_workspace(tmp_path: Path) -> None:
    """実在してもworkspace外のlocal sourceを拒否することを確認する。"""

    outside = tmp_path / "outside.md"
    outside.write_text("outside", encoding="utf-8")
    workspace = prepare()
    try:
        initialize_knowledge(workspace)
        concept = workspace / "project-knowledge" / "docs" / "outside-source.md"
        metadata = {
            "type": "Test Concept",
            "status": "stable",
            "pk_category": "extracted",
            "pk_derivation": "direct",
            "generated": {
                "by": "project-knowledge/3.1.0",
                "at": "2026-08-27T00:00:00+09:00",
            },
            "sources": [
                {"resource": str(outside.resolve()), "pk_source_type": "project-artifact"}
            ],
        }
        frontmatter = yaml.safe_dump(metadata, sort_keys=False, allow_unicode=True).rstrip()
        concept.write_text(f"---\n{frontmatter}\n---\n\n# Outside source\n", encoding="utf-8")
        result = RUNNER["validate"](workspace)
        assert result["status"] == "FAIL"
        assert "source-outside-workspace" in {item["code"] for item in result["findings"]}
    finally:
        RUNNER["cleanup"](workspace)


def test_report_passes_only_when_validator_and_judge_pass() -> None:
    """全deterministic条件と全Judge観点のPASSだけを全体PASSにする。"""

    workspace = prepare()
    try:
        RUNNER["write_json"](
            workspace.parent / RUNNER["DETERMINISTIC_RESULT"],
            {"status": "PASS", "findings": [], "error": None},
        )
        RUNNER["write_json"](workspace.parent / RUNNER["JUDGE_RESULT"], valid_judge())
        output, exit_code = RUNNER["report"](workspace)
        assert exit_code == 0
        assert "Result: PASS" in output
        assert "unsupported_claims: PASS" in output
        assert "Issues:\n  none" in output
    finally:
        RUNNER["cleanup"](workspace)


def test_report_skips_judge_after_deterministic_failure() -> None:
    """deterministic FAIL時にJudgeなしで失敗を報告できることを確認する。"""

    workspace = prepare()
    try:
        RUNNER["write_json"](
            workspace.parent / RUNNER["DETERMINISTIC_RESULT"],
            {
                "status": "FAIL",
                "findings": [
                    {"severity": "high", "code": "missing-index", "path": "docs/index.md"}
                ],
                "error": None,
            },
        )
        output, exit_code = RUNNER["report"](workspace)
        assert exit_code == 1
        assert "Result: FAIL" in output
        assert "AI Judge:\n  SKIPPED" in output
        assert "deterministic missing-index" in output
    finally:
        RUNNER["cleanup"](workspace)


def test_report_rejects_inconsistent_judge_result() -> None:
    """観点FAILを全体PASSとする不整合Judge JSONを拒否する。"""

    workspace = prepare()
    try:
        RUNNER["write_json"](
            workspace.parent / RUNNER["DETERMINISTIC_RESULT"],
            {"status": "PASS", "findings": [], "error": None},
        )
        judge = valid_judge()
        judge["dimensions"]["correctness"]["result"] = "FAIL"
        RUNNER["write_json"](workspace.parent / RUNNER["JUDGE_RESULT"], judge)
        output, exit_code = RUNNER["report"](workspace)
        assert exit_code == 2
        assert "AI Judge:\n  ERROR" in output
        assert "inconsistent" in output
    finally:
        RUNNER["cleanup"](workspace)


def test_cleanup_refuses_unmarked_directory(tmp_path: Path) -> None:
    """markerのないディレクトリをcleanupしないことを確認する。"""

    workspace = tmp_path / "workspace"
    workspace.mkdir()
    with pytest.raises(RUNNER["ScenarioError"]):
        RUNNER["cleanup"](workspace)
    assert workspace.is_dir()


def test_skill_contract_keeps_actor_and_judge_independent() -> None:
    """Skillが明示起動とActor/Judgeの隔離条件を公開することを確認する。"""

    skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
    quick = (SKILL_ROOT / "references" / "quick.md").read_text(encoding="utf-8")
    agent = yaml.safe_load((SKILL_ROOT / "agents" / "openai.yaml").read_text(encoding="utf-8"))
    expectations = yaml.safe_load(
        (SKILL_ROOT / "scenarios" / "quick-basic" / "expectations.yml").read_text(
            encoding="utf-8"
        )
    )

    assert agent["policy"]["allow_implicit_invocation"] is False
    assert skill.count("gpt-5.6-luna") == 1
    assert "reasoning_effort: low" in skill
    assert "fork_turns: none" in skill
    assert "expectations.yml" not in quick.split("3. Actor終了後", 1)[0]
    assert set(expectations) == {
        "scenario",
        "required_knowledge",
        "forbidden_knowledge",
        "expected_properties",
    }
    assert len(RUNNER["DIMENSIONS"]) == 6


def test_runner_cli_reports_unsupported_scenario(capsys: pytest.CaptureFixture[str]) -> None:
    """Fullを暗黙にQuickとして実行しないことを確認する。"""

    exit_code = RUNNER["main"](["prepare", "full"])
    captured = capsys.readouterr()
    assert exit_code == 2
    assert "unsupported scenario: full" in captured.err
