from __future__ import annotations

import runpy
import subprocess
from pathlib import Path

import pytest

SKILL_ROOT = Path(__file__).resolve().parents[1]
RUNNER = runpy.run_path(str(SKILL_ROOT / "scripts" / "benchmark_runner.py"))


def git(repository: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    """テストrepositoryでGit commandを実行する。"""

    return subprocess.run(["git", *args], cwd=repository, capture_output=True, text=True, check=check)


def create_repository(root: Path, with_knowledge: bool = True) -> Path:
    """Benchmark対象の最小Git repositoryを作る。"""

    repository = root / "source"
    repository.mkdir(parents=True)
    (repository / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
    if with_knowledge:
        (repository / "project-knowledge.yaml").write_text(
            'version: "1.0"\nlayers:\n  - id: default\n    name: 既定\n    path: ./project-knowledge\n', encoding="utf-8"
        )
        knowledge = repository / "project-knowledge"
        knowledge.mkdir()
        (knowledge / "manifest.yml").write_text('format: project-knowledge\nformat_version: "1.0"\n', encoding="utf-8")
        (knowledge / "guide.md").write_text("Use VALUE constants.\n", encoding="utf-8")
    git(repository, "init")
    git(repository, "config", "user.name", "Test")
    git(repository, "config", "user.email", "test@example.invalid")
    git(repository, "add", "-A")
    git(repository, "commit", "-m", "baseline")
    return repository


def create_task(root: Path) -> Path:
    """共通task fileを作る。"""

    root.mkdir(parents=True, exist_ok=True)
    task = root / "task.md"
    task.write_text("Change VALUE to 2.\n", encoding="utf-8")
    return task


def cleanup(descriptor_path: Path) -> None:
    """テストで残したworktree registrationを回収する。"""

    if not descriptor_path.is_file():
        return
    descriptor = RUNNER["read_json"](descriptor_path)
    RUNNER["recover"](descriptor_path)
    repository = Path(descriptor["repository"])
    for candidate in descriptor["candidates"].values():
        git(repository, "worktree", "remove", "--force", candidate["workspace"], check=False)


def valid_judge() -> dict[str, object]:
    """Runner契約を満たすblind Judge結果を作る。"""

    candidates: dict[str, object] = {}
    for name in ("Candidate 1", "Candidate 2"):
        candidates[name] = {
            "dimensions": {
                dimension: {"score": 80, "reason": "Meets the task.", "evidence": ["app.py"]}
                for dimension in RUNNER["DIMENSIONS"]
            },
            "overall_score": 80,
        }
    return {"candidates": candidates, "preference": "tie", "summary": "Equivalent."}


def test_prepare_isolates_history_and_only_removes_knowledge(tmp_path: Path) -> None:
    """Aから元履歴を読めず、Knowledge以外のsourceが同じことを確認する。"""

    repository = create_repository(tmp_path)
    descriptor_path = RUNNER["prepare"](repository, create_task(tmp_path), output_root=tmp_path / "runs")
    try:
        descriptor = RUNNER["read_json"](descriptor_path)
        no_kb = Path(descriptor["candidates"]["no_knowledge"]["workspace"])
        with_kb = Path(descriptor["candidates"]["with_knowledge"]["workspace"])
        assert not (no_kb / "project-knowledge").exists()
        assert (with_kb / "project-knowledge" / "manifest.yml").is_file()
        assert git(no_kb, "rev-list", "--count", "HEAD").stdout.strip() == "1"
        assert git(no_kb, "show", "HEAD^:project-knowledge/manifest.yml", check=False).returncode != 0
        assert RUNNER["content_hash"](no_kb, True) == RUNNER["content_hash"](with_kb, True)
        assert "no_knowledge" not in no_kb.name
        assert "with_knowledge" not in with_kb.name
    finally:
        cleanup(descriptor_path)


def test_prepare_rejects_dirty_and_missing_knowledge(tmp_path: Path) -> None:
    """曖昧なbaselineとKnowledgeなしrepositoryを拒否する。"""

    dirty = create_repository(tmp_path / "dirty")
    (dirty / "untracked.txt").write_text("dirty", encoding="utf-8")
    with pytest.raises(RUNNER["BenchmarkError"], match="clean"):
        RUNNER["prepare"](dirty, create_task(tmp_path / "dirty"), output_root=tmp_path / "runs-dirty")
    missing = create_repository(tmp_path / "missing", with_knowledge=False)
    with pytest.raises(RUNNER["BenchmarkError"], match="not registered"):
        RUNNER["prepare"](missing, create_task(tmp_path / "missing"), output_root=tmp_path / "runs-missing")


def test_prepare_uses_config_from_baseline_and_custom_path(tmp_path: Path) -> None:
    """過去commitの設定で独自配置を解決し、設定とKnowledgeだけを除去する。"""

    repository = create_repository(tmp_path)
    git(repository, "mv", "project-knowledge", "custom-knowledge")
    config = repository / "project-knowledge.yaml"
    config.write_text('version: "1.0"\nlayers:\n  - id: team\n    name: チーム用\n    path: ./custom-knowledge\n    description: Team decisions\n', encoding="utf-8")
    git(repository, "add", "-A")
    git(repository, "commit", "-m", "custom configuration")
    baseline = git(repository, "rev-parse", "HEAD").stdout.strip()
    config.write_text('version: "1.0"\nlayers: []\n', encoding="utf-8")
    git(repository, "commit", "-am", "disable current knowledge")
    descriptor_path = RUNNER["prepare"](repository, create_task(tmp_path), baseline=baseline, output_root=tmp_path / "runs")
    try:
        descriptor = RUNNER["read_json"](descriptor_path)
        without = Path(descriptor["candidates"]["no_knowledge"]["workspace"])
        with_kb = Path(descriptor["candidates"]["with_knowledge"]["workspace"])
        assert not (without / "project-knowledge.yaml").exists()
        assert not (without / "custom-knowledge").exists()
        assert (with_kb / "custom-knowledge" / "manifest.yml").is_file()
        assert "./custom-knowledge" in (with_kb / "project-knowledge.yaml").read_text(encoding="utf-8")
        assert (without / "app.py").read_bytes() == (with_kb / "app.py").read_bytes()
    finally:
        cleanup(descriptor_path)


def test_prepare_removes_all_registered_layers(tmp_path: Path) -> None:
    """No-KB条件とblind snapshotが全登録レイヤーを除外する。"""

    repository = create_repository(tmp_path)
    team = repository / "team-knowledge"
    team.mkdir()
    (team / "manifest.yml").write_text('format: project-knowledge\nformat_version: "1.0"\n', encoding="utf-8")
    (team / "guide.md").write_text("Shared VALUE rules.\n", encoding="utf-8")
    (repository / "project-knowledge.yaml").write_text(
        'version: "1.0"\nlayers:\n  - id: personal\n    name: Personal\n    path: ./project-knowledge\n    description: private\n  - id: team\n    name: Team\n    path: ./team-knowledge\n    description: shared\n',
        encoding="utf-8",
    )
    git(repository, "add", "-A")
    git(repository, "commit", "-m", "add team knowledge")
    descriptor_path = RUNNER["prepare"](repository, create_task(tmp_path), output_root=tmp_path / "runs")
    try:
        descriptor = RUNNER["read_json"](descriptor_path)
        no_kb = Path(descriptor["candidates"]["no_knowledge"]["workspace"])
        assert not (no_kb / "project-knowledge").exists()
        assert not (no_kb / "team-knowledge").exists()
        paths = RUNNER["blind"](descriptor_path)
        assert all(not (Path(path) / "project-knowledge").exists() for path in paths.values())
        assert all(not (Path(path) / "team-knowledge").exists() for path in paths.values())
    finally:
        cleanup(descriptor_path)


def test_evaluate_preserves_workspace_and_records_checks(tmp_path: Path) -> None:
    """Task diffと機械評価を別artifactとして保存する。"""

    repository = create_repository(tmp_path)
    checks = tmp_path / "checks.yml"
    checks.write_text("checks:\n  - name: syntax\n    command: python -m py_compile app.py\n", encoding="utf-8")
    descriptor_path = RUNNER["prepare"](repository, create_task(tmp_path), output_root=tmp_path / "runs", checks_file=checks)
    try:
        descriptor = RUNNER["read_json"](descriptor_path)
        workspace = Path(descriptor["candidates"]["no_knowledge"]["workspace"])
        (workspace / "app.py").write_text("VALUE = 2\n", encoding="utf-8")
        (workspace / "new.bin").write_bytes(b"\x00\x01")
        result = RUNNER["evaluate"](descriptor_path, "no_knowledge")
        assert result["status"] == "PASS"
        assert result["diff"]["changed_entries"] == 2
        assert (workspace / "new.bin").read_bytes() == b"\x00\x01"
        assert Path(result["checks"][0]["log"]).is_file()
    finally:
        cleanup(descriptor_path)


def test_evaluate_includes_task_agent_commits(tmp_path: Path) -> None:
    """Task Agentがcommitしてもcondition baselineとの差分を保持する。"""

    repository = create_repository(tmp_path)
    descriptor_path = RUNNER["prepare"](repository, create_task(tmp_path), output_root=tmp_path / "runs")
    try:
        descriptor = RUNNER["read_json"](descriptor_path)
        workspace = Path(descriptor["candidates"]["no_knowledge"]["workspace"])
        (workspace / "app.py").write_text("VALUE = 2\n", encoding="utf-8")
        git(workspace, "add", "app.py")
        git(workspace, "commit", "-m", "task result")
        result = RUNNER["evaluate"](descriptor_path, "no_knowledge")
        assert result["diff"]["changed_entries"] == 1
        assert "VALUE = 2" in Path(result["diff"]["patch"]).read_text(encoding="utf-8")
    finally:
        cleanup(descriptor_path)


def test_blind_hides_condition_knowledge_and_restores_worktrees(tmp_path: Path) -> None:
    """Judge snapshotをblind化し、人間確認用worktreeを復旧する。"""

    repository = create_repository(tmp_path)
    descriptor_path = RUNNER["prepare"](repository, create_task(tmp_path), output_root=tmp_path / "runs")
    try:
        paths = RUNNER["blind"](descriptor_path)
        assert set(paths) == {"Candidate 1", "Candidate 2"}
        assert all(not (Path(path) / "project-knowledge").exists() for path in paths.values())
        assert all(not (Path(path) / ".git").exists() for path in paths.values())
        descriptor = RUNNER["read_json"](descriptor_path)
        assert all((Path(value["workspace"]) / ".git").is_file() for value in descriptor["candidates"].values())
    finally:
        cleanup(descriptor_path)


def test_report_keeps_machine_judge_and_usage_separate(tmp_path: Path) -> None:
    """comparisonが三種の評価を混同せず保持する。"""

    repository = create_repository(tmp_path)
    descriptor_path = RUNNER["prepare"](repository, create_task(tmp_path), output_root=tmp_path / "runs")
    try:
        for condition in RUNNER["CONDITIONS"]:
            RUNNER["evaluate"](descriptor_path, condition)
        RUNNER["write_json"](descriptor_path.parent / "judge.json", valid_judge())
        output, exit_code = RUNNER["report"](descriptor_path)
        comparison = RUNNER["read_json"](descriptor_path.parent / "comparison.json")
        assert exit_code == 0
        assert "Mechanical evaluation" in output
        assert comparison["llm_judge"]["preference"] == "tie"
        assert comparison["conditions"]["no_knowledge"]["usage"] == "unavailable"
    finally:
        cleanup(descriptor_path)


def test_rejects_invalid_judge_schema() -> None:
    """不足したblind Judge結果を受理しない。"""

    with pytest.raises(RUNNER["BenchmarkError"], match="dimensions"):
        RUNNER["validate_judge"]({"candidates": {"Candidate 1": {}, "Candidate 2": {}}, "preference": "tie", "summary": ""})
