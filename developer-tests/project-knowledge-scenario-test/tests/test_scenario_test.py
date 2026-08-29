from __future__ import annotations

import runpy
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

SKILL_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = SKILL_ROOT.parents[1]
SKILLS_ROOT = REPOSITORY_ROOT / "skills"
RUNNER_PATH = SKILL_ROOT / "scripts" / "scenario_test.py"
RUNNER = runpy.run_path(str(RUNNER_PATH))
INIT = SKILLS_ROOT / "project-knowledge" / "scripts" / "init_project.py"
FIXTURE = SKILL_ROOT / "scenarios" / "quick-basic" / "fixture"
LARGE_FIXTURE = SKILL_ROOT / "scenarios" / "large-lifecycle" / "fixture" / "initial"


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


def add_concept(workspace: Path, sources: list[dict[str, str]] | None = None) -> Path:
    """テスト用の分類済みConceptを追加する。"""

    metadata = {
        "type": "Relay behavior",
        "status": "stable",
        "pk_category": "extracted",
        "pk_derivation": "direct",
        "generated": {
            "by": "project-knowledge/3.1.0",
            "at": "2026-08-27T00:00:00+09:00",
        },
        "sources": sources if sources is not None else [
            {"resource": "../../README.md", "pk_source_type": "project-artifact"}
        ],
    }
    frontmatter = yaml.safe_dump(metadata, sort_keys=False, allow_unicode=True).rstrip()
    concept = workspace / "project-knowledge" / "docs" / "relay-behavior.md"
    concept.write_text(f"---\n{frontmatter}\n---\n\n# Relay behavior\n", encoding="utf-8")
    return concept


def valid_judge() -> dict[str, object]:
    """全観点PASSのJudge結果を作成する。"""

    dimensions = {
        name: {"result": "PASS", "reason": "sourceと一致", "evidence": ["README.md"]}
        for name in RUNNER["DIMENSIONS"]
    }
    return {"result": "PASS", "dimensions": dimensions, "issues": []}


def available_measurement(total_credits: float) -> dict[str, object]:
    """Runner統合テスト用の実測済みmeasurementを作成する。"""

    return {
        "usage_status": "available",
        "usage": {
            "input_tokens": 100,
            "cached_input_tokens": 80,
            "output_tokens": 5,
            "reasoning_output_tokens": 2,
            "total_tokens": 105,
        },
        "credits": {
            "uncached_input": 0.1,
            "cached_input": 0.04,
            "output": 0.15,
            "total": total_credits,
        },
        "credit_rate": {"checked_at": "2026-08-28"},
        "measurement": {
            "source": "codex-session-jsonl",
            "session_id": "test-session",
            "rollout_file": "rollout-test-session.jsonl",
            "status": "available",
            "reason": None,
        },
    }


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


def test_validate_rejects_empty_knowledge_bundle() -> None:
    """骨組みだけのBundleをQuick初期構築の失敗として検出する。"""

    workspace = prepare()
    try:
        initialize_knowledge(workspace)
        result = RUNNER["validate"](workspace)
        codes = {item["code"] for item in result["findings"]}
        assert result["status"] == "FAIL"
        assert result["error"] is None
        assert {"missing-concept", "missing-project-artifact-source"} <= codes
    finally:
        RUNNER["cleanup"](workspace)


def test_validate_accepts_concept_with_project_artifact() -> None:
    """根拠付き通常ConceptがQuickの最低契約を満たすことを確認する。"""

    workspace = prepare()
    try:
        initialize_knowledge(workspace)
        add_concept(workspace)
        result = RUNNER["validate"](workspace)
        assert result["status"] == "PASS"
        assert result["error"] is None
        assert not any(item["severity"] == "high" for item in result["findings"])
    finally:
        RUNNER["cleanup"](workspace)


def test_validate_requires_project_artifact_source() -> None:
    """通常Conceptにproject artifact根拠がなければFAILとする。"""

    workspace = prepare()
    try:
        initialize_knowledge(workspace)
        add_concept(workspace, sources=[])
        result = RUNNER["validate"](workspace)
        codes = {item["code"] for item in result["findings"]}
        assert result["status"] == "FAIL"
        assert "missing-concept" not in codes
        assert "missing-project-artifact-source" in codes
    finally:
        RUNNER["cleanup"](workspace)


def test_validate_detects_actor_source_mutation() -> None:
    """ActorがFixture sourceを変更した場合にFAILとすることを確認する。"""

    workspace = prepare()
    try:
        initialize_knowledge(workspace)
        add_concept(workspace)
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
        add_concept(
            workspace,
            sources=[
                {"resource": "../../README.md", "pk_source_type": "project-artifact"},
                {"resource": str(outside.resolve()), "pk_source_type": "project-artifact"},
            ],
        )
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


def test_quick_report_displays_recorded_actor_and_judge_credits(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Quick reportが品質結果と独立して役割別creditsを表示・保存する。"""

    workspace = prepare()
    try:
        RUNNER["write_json"](
            workspace.parent / RUNNER["DETERMINISTIC_RESULT"],
            {"status": "PASS", "findings": [], "error": None},
        )
        RUNNER["write_json"](workspace.parent / RUNNER["JUDGE_RESULT"], valid_judge())
        RUNNER["record_session"](
            workspace,
            "actor",
            "actor-session",
            "/root/quick_actor",
            parent_session_id="parent-session",
        )
        RUNNER["record_session"](
            workspace,
            "judge",
            "judge-session",
            "/root/quick_judge",
            parent_session_id="parent-session",
        )

        def fake_measurement(reference: dict[str, str], _: dict[str, object]) -> dict[str, object]:
            """agent pathに応じた固定creditを返す。"""

            return available_measurement(
                0.29 if reference["agent_path"].endswith("actor") else 0.11
            )

        monkeypatch.setitem(
            RUNNER["report"].__globals__, "measure_session", fake_measurement
        )
        output, exit_code = RUNNER["report"](workspace)
        metadata = RUNNER["read_json"](workspace.parent / RUNNER["MARKER"])

        assert exit_code == 0
        assert "Usage measurement: AVAILABLE" in output
        assert "Actor: 0.29" in output
        assert "Judge: 0.11" in output
        assert "Total (measured): 0.4" in output
        assert metadata["measured_total_credits"] == 0.4
        assert metadata["measurement_results"]["actor"]["usage"]["total_tokens"] == 105
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
    scenarios = yaml.safe_load(
        (SKILL_ROOT / "agents" / "scenarios.yml").read_text(encoding="utf-8")
    )

    assert agent["policy"]["allow_implicit_invocation"] is False
    assert scenarios["quick-basic"] == scenarios["large-lifecycle"]
    assert scenarios["quick-basic"]["actor"]["model"] == "gpt-5.6-luna"
    assert "agents/scenarios.yml" in skill
    assert "fork_turns: none" in skill
    assert "expectations.yml" not in quick.split("3. Actor終了後", 1)[0]
    assert "app-server" in skill
    assert "session record" in quick
    assert set(expectations) == {
        "scenario",
        "required_knowledge",
        "forbidden_knowledge",
        "expected_properties",
    }
    assert len(RUNNER["DIMENSIONS"]) == 6


def test_prepare_large_isolates_versioned_fixture_and_lifecycle() -> None:
    """Largeが十分な初期Sourceと12 Change Setを隔離して準備する。"""

    fixture_hash = RUNNER["tree_hash"](LARGE_FIXTURE)
    descriptor_path = RUNNER["prepare_large"]("large-lifecycle")
    try:
        descriptor = RUNNER["read_json"](descriptor_path)
        workspace = Path(descriptor["workspace"])

        assert descriptor["scenario_version"] == "1"
        assert descriptor["fixture_version"] == "1"
        assert descriptor["execution_mode"] == "normal"
        assert descriptor["fixture"]["files"] >= 35
        assert len(descriptor["change_sets"]) == 12
        assert descriptor["judge_checkpoints"] == ["initial", "update-06", "update-12"]
        assert (workspace / ".git").is_dir()
        assert not (workspace.parent / "expectations.yml").exists()
        assert RUNNER["tree_hash"](LARGE_FIXTURE) == fixture_hash
    finally:
        RUNNER["cleanup_large"](descriptor_path)


def test_large_applies_all_change_sets_as_independent_commits() -> None:
    """追加・変更・削除・移動を含む12 updateを順序どおりcommitする。"""

    descriptor_path = RUNNER["prepare_large"]("large-lifecycle")
    try:
        initial_descriptor = RUNNER["read_json"](descriptor_path)
        initial_workspace = Path(initial_descriptor["workspace"])
        initialize_knowledge(initial_workspace)
        add_concept(initial_workspace)
        for expected in range(1, 13):
            descriptor = RUNNER["read_json"](descriptor_path)
            descriptor["steps"][-1]["validation"] = {
                "status": "PASS", "findings": [], "error": None
            }
            RUNNER["write_json"](descriptor_path, descriptor)
            step = RUNNER["advance_large"](descriptor_path)
            assert step["step"] == f"update-{expected:02d}"
            assert step["changed_files"] > 0
            assert step["changed_bytes"] > 0

        descriptor = RUNNER["read_json"](descriptor_path)
        workspace = Path(descriptor["workspace"])
        assert not (workspace / "docs" / "archive" / "v1-routing.md").exists()
        assert (
            workspace / "backend" / "notifications" / "src" / "workers" / "delivery.py"
        ).is_file()
        assert (
            workspace / "backend" / "payments" / "src" / "reconciliation.py"
        ).is_file()
        commits = subprocess.run(
            ["git", "rev-list", "--count", "HEAD"],
            cwd=workspace,
            capture_output=True,
            text=True,
            check=False,
        )
        assert commits.returncode == 0
        assert commits.stdout.strip() == "14"
    finally:
        RUNNER["cleanup_large"](descriptor_path)


def test_large_validation_records_knowledge_growth_statistics() -> None:
    """Large validationがQuick共通検査とKnowledge統計をstepへ保存する。"""

    descriptor_path = RUNNER["prepare_large"]("large-lifecycle")
    try:
        descriptor = RUNNER["read_json"](descriptor_path)
        workspace = Path(descriptor["workspace"])
        initialize_knowledge(workspace)
        add_concept(workspace)

        step = RUNNER["validate_large"](descriptor_path)

        assert step["validation"]["status"] == "PASS"
        assert step["knowledge"]["concepts"] >= 1
        assert step["knowledge"]["knowledge_markdown_files"] >= 1
        assert step["repository"]["files"] >= 35
    finally:
        RUNNER["cleanup_large"](descriptor_path)


def test_large_report_separates_actor_and_judge_tokens(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Large reportがstep別Actor/Judge tokenを分離して集計する。"""

    descriptor_path = RUNNER["prepare_large"]("large-lifecycle")
    try:
        descriptor = RUNNER["read_json"](descriptor_path)
        descriptor["change_sets"] = []
        descriptor["steps"][0]["validation"] = {
            "status": "PASS", "findings": [], "error": None
        }
        descriptor["steps"][0]["knowledge"] = {
            "concepts": 40,
            "knowledge_markdown_files": 48,
            "knowledge_characters": 60000,
            "sources": 72,
            "draft_concepts": 2,
            "inferred_concepts": 3,
        }
        RUNNER["write_json"](descriptor_path, descriptor)
        RUNNER["record_session"](
            descriptor_path, "actor", "large-actor", "/root/large_actor", step_id="initial"
        )
        RUNNER["record_session"](
            descriptor_path, "judge", "large-judge", "/root/large_judge", step_id="initial"
        )
        RUNNER["write_json"](
            RUNNER["large_judge_path"](descriptor_path, "initial"), valid_judge()
        )

        def fake_measurement(
            reference: dict[str, str] | None, _: dict[str, object]
        ) -> dict[str, object]:
            """ActorとJudgeに異なるtoken値を返す。"""

            assert reference is not None
            value = available_measurement(0.1)
            value["usage"]["total_tokens"] = (
                1000 if reference["agent_path"].endswith("actor") else 200
            )
            return value

        monkeypatch.setitem(
            RUNNER["large_report"].__globals__, "measure_session", fake_measurement
        )
        output, exit_code = RUNNER["large_report"](descriptor_path)
        result = RUNNER["read_json"](descriptor_path)

        assert exit_code == 0
        assert "Result: PASS" in output
        assert "Initial score: 100" in output
        assert result["steps"][0]["actor_usage"]["total_tokens"] == 1000
        assert result["steps"][0]["judge_usage"]["total_tokens"] == 200
        assert result["summary"]["tokens"]["cumulative_actor"] == 1000
        assert result["summary"]["tokens"]["judge_total"] == 200
    finally:
        RUNNER["cleanup_large"](descriptor_path)


def test_prepare_benchmark_reuses_isolated_quick_workspaces() -> None:
    """Benchmarkが同じQuick Fixtureから候補ごとのworkspaceを作ることを確認する。"""

    descriptor_path = RUNNER["prepare_benchmark"]("quick-basic")
    try:
        descriptor = RUNNER["read_json"](descriptor_path)
        assert descriptor["single_run"] is True
        assert [candidate["model_id"] for candidate in descriptor["candidates"]] == [
            "luna",
            "terra",
            "sol",
        ]
        workspaces = [Path(candidate["workspace"]) for candidate in descriptor["candidates"]]
        assert len(set(workspaces)) == 3
        assert all((workspace / ".git").is_dir() for workspace in workspaces)
        assert all(candidate["actor_usage"]["total_tokens"] == "unavailable" for candidate in descriptor["candidates"])
        assert all(candidate["actor_session"] is None for candidate in descriptor["candidates"])
    finally:
        for candidate in RUNNER["read_json"](descriptor_path)["candidates"]:
            RUNNER["cleanup"](Path(candidate["workspace"]))
        descriptor_path.unlink()
        descriptor_path.parent.rmdir()


def test_benchmark_compares_actor_credits_and_separates_judge_cost(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Benchmarkの最低コストをActor creditsで判定しJudgeを別集計する。"""

    descriptor_path = RUNNER["prepare_benchmark"]("quick-basic")
    credit_by_model = {
        "gpt-5.6-luna": 0.8,
        "gpt-5.6-terra": 7.2,
        "gpt-5.6-sol": 15.4,
    }
    try:
        descriptor = RUNNER["read_json"](descriptor_path)
        for candidate in descriptor["candidates"]:
            workspace = Path(candidate["workspace"])
            RUNNER["write_json"](
                workspace.parent / RUNNER["DETERMINISTIC_RESULT"],
                {"status": "PASS", "findings": [], "error": None},
            )
            RUNNER["write_json"](workspace.parent / RUNNER["JUDGE_RESULT"], valid_judge())
            RUNNER["record_session"](
                descriptor_path,
                "actor",
                f"{candidate['model_id']}-actor-session",
                f"/root/{candidate['model_id']}_actor",
                candidate["model_id"],
                "parent-session",
            )
            RUNNER["record_session"](
                descriptor_path,
                "judge",
                f"{candidate['model_id']}-judge-session",
                f"/root/{candidate['model_id']}_judge",
                candidate["model_id"],
                "parent-session",
            )

        def fake_measurement(
            reference: dict[str, str] | None, _: dict[str, object]
        ) -> dict[str, object]:
            """Candidate marker未記録分とBenchmark記録分を区別する。"""

            if reference is None:
                return RUNNER["unavailable_measurement"]("session-not-recorded")
            if reference["agent_path"].endswith("judge"):
                return available_measurement(0.1)
            return available_measurement(credit_by_model[reference["model"]])

        monkeypatch.setitem(
            RUNNER["benchmark_report"].__globals__, "measure_session", fake_measurement
        )
        output, exit_code = RUNNER["benchmark_report"](descriptor_path)
        result = RUNNER["read_json"](descriptor_path)

        assert exit_code == 0
        assert "Lowest credits: GPT-5.6 Luna" in output
        assert "Judge credits: 0.3" in output
        assert "Benchmark total credits: 23.7" in output
        assert result["actor_credits"] == 23.4
        assert result["judge_credits"] == pytest.approx(0.3)
        assert result["benchmark_total_credits"] == 23.7
    finally:
        for candidate in RUNNER["read_json"](descriptor_path)["candidates"]:
            RUNNER["cleanup"](Path(candidate["workspace"]))
        descriptor_path.unlink()
        descriptor_path.parent.rmdir()


def test_runner_cli_reports_unsupported_scenario(capsys: pytest.CaptureFixture[str]) -> None:
    """Fullを暗黙にQuickとして実行しないことを確認する。"""

    exit_code = RUNNER["main"](["prepare", "full"])
    captured = capsys.readouterr()
    assert exit_code == 2
    assert "unsupported scenario: full" in captured.err


def test_prepare_utility_isolates_equal_source_workspaces() -> None:
    """Utilityが同じsourceからBuilderと二つのTask workspaceを作ることを確認する。"""

    descriptor_path = RUNNER["prepare_utility"]("utility-basic")
    try:
        descriptor = RUNNER["read_json"](descriptor_path)
        workspaces = {
            role: Path(path) for role, path in descriptor["workspaces"].items()
        }

        assert descriptor["single_run"] is True
        assert descriptor["models"]["task"]["model"] == "gpt-5.6-terra"
        assert descriptor["models"]["judge"]["model"] == "gpt-5.6-terra"
        assert len(set(workspaces.values())) == 3
        assert all((workspace / ".git").is_dir() for workspace in workspaces.values())
        assert all(not (workspace / "task.md").exists() for workspace in workspaces.values())
        assert all(not (workspace / "project-knowledge").exists() for workspace in workspaces.values())
        hashes = {
            RUNNER["tree_hash"](workspace, RUNNER["MANAGED_SOURCE_NAMES"])
            for workspace in workspaces.values()
        }
        assert len(hashes) == 1
    finally:
        RUNNER["cleanup_utility"](descriptor_path)


def test_install_utility_knowledge_only_changes_with_kb() -> None:
    """BuilderのKnowledgeがWith-KBだけへ同一内容で複製されることを確認する。"""

    descriptor_path = RUNNER["prepare_utility"]("utility-basic")
    try:
        descriptor = RUNNER["read_json"](descriptor_path)
        builder = Path(descriptor["workspaces"]["knowledge_builder"])
        no_kb = Path(descriptor["workspaces"]["no_kb"])
        with_kb = Path(descriptor["workspaces"]["with_kb"])
        initialize_knowledge(builder)
        add_concept(builder)

        knowledge = RUNNER["install_utility_knowledge"](descriptor_path)

        assert knowledge["status"] == "ready"
        assert not (no_kb / "project-knowledge").exists()
        assert (with_kb / "project-knowledge" / "docs" / "relay-behavior.md").is_file()
        assert RUNNER["tree_hash"](builder / "project-knowledge") == RUNNER["tree_hash"](
            with_kb / "project-knowledge"
        )
    finally:
        RUNNER["cleanup_utility"](descriptor_path)


def test_utility_evaluation_keeps_hidden_checks_outside_workspace() -> None:
    """未実装成果物をhidden evaluatorで判定し、hidden filesをTaskへ漏らさない。"""

    descriptor_path = RUNNER["prepare_utility"]("utility-basic")
    try:
        descriptor = RUNNER["read_json"](descriptor_path)
        workspace = Path(descriptor["workspaces"]["no_kb"])

        result = RUNNER["evaluate_utility_condition"](descriptor_path, "no_kb")

        assert result["build"] == "PASS"
        assert result["existing_tests"] == {"passed": 2, "total": 2, "status": "PASS"}
        assert result["hidden_tests"]["total"] == 11
        assert result["task_success"] is False
        assert not (workspace / "hidden_tests").exists()
        assert not (workspace / "expectations.yml").exists()
    finally:
        RUNNER["cleanup_utility"](descriptor_path)


def test_blind_candidates_hide_conditions_and_knowledge() -> None:
    """Judge snapshotが中立名を使い、KnowledgeとGit情報を除外することを確認する。"""

    descriptor_path = RUNNER["prepare_utility"]("utility-basic")
    try:
        descriptor = RUNNER["read_json"](descriptor_path)
        with_kb = Path(descriptor["workspaces"]["with_kb"])
        (with_kb / "project-knowledge").mkdir()

        candidates = RUNNER["prepare_blind_candidates"](descriptor_path)

        assert set(candidates) == {"Candidate A", "Candidate B"}
        for candidate_path in map(Path, candidates.values()):
            assert "no_kb" not in str(candidate_path)
            assert "with_kb" not in str(candidate_path)
            assert not (candidate_path / ".git").exists()
            assert not (candidate_path / "project-knowledge").exists()
    finally:
        RUNNER["cleanup_utility"](descriptor_path)


def test_utility_report_restores_conditions_and_calculates_delta() -> None:
    """blind CandidateをConditionへ戻し、qualityとtestのdeltaを保存する。"""

    descriptor_path = RUNNER["prepare_utility"]("utility-basic")
    try:
        descriptor = RUNNER["read_json"](descriptor_path)
        for condition, passed in (("no_kb", 7), ("with_kb", 10)):
            workspace = Path(descriptor["workspaces"][condition])
            RUNNER["write_json"](workspace.parent / RUNNER["DETERMINISTIC_RESULT"], {
                "condition": condition,
                "build": "PASS",
                "existing_tests": {"passed": 2, "total": 2, "status": "PASS"},
                "hidden_tests": {"passed": passed, "total": 11, "categories": {}, "checks": []},
                "scope": {"status": "PASS", "forbidden_changes": []},
                "task_success": passed == 10,
            })
        scores = {descriptor["candidate_mapping"]["no_kb"]: 78, descriptor["candidate_mapping"]["with_kb"]: 92}
        candidates = {}
        for candidate, score in scores.items():
            candidates[candidate] = {"dimensions": {
                name: {"score": score, "reason": "source review", "evidence": ["src/courier/api.py"]}
                for name in RUNNER["UTILITY_DIMENSIONS"]
            }}
        RUNNER["write_json"](descriptor_path.parent / RUNNER["JUDGE_RESULT"], {
            "candidates": candidates,
            "preference": descriptor["candidate_mapping"]["with_kb"],
            "summary": "One candidate follows more project conventions.",
        })

        output, exit_code = RUNNER["utility_report"](descriptor_path)
        result = RUNNER["read_json"](descriptor_path)

        assert exit_code == 0
        assert "single-run utility benchmark" in output
        assert "7/11" in output and "10/11" in output and "+3" in output
        assert result["delta"]["quality"] == 14
        assert result["delta"]["tokens"]["total_tokens"] == "unavailable"
    finally:
        RUNNER["cleanup_utility"](descriptor_path)
