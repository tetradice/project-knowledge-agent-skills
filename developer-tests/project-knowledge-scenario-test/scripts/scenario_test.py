"""Project KnowledgeシナリオとBenchmarkの決定的な処理を実行する。"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import secrets
import shutil
import stat
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path
from statistics import median
from typing import Any
from urllib.parse import urlparse

import yaml

SCRIPT_ROOT = Path(__file__).resolve().parent
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from session_usage import (
    load_credit_rates,
    measure_session,
    unavailable_measurement,
    unavailable_usage,
)

SKILL_ROOT = Path(__file__).resolve().parents[1]
SCENARIOS_ROOT = SKILL_ROOT / "scenarios"
REPOSITORY_ROOT = SKILL_ROOT.parents[1]
PROJECT_KNOWLEDGE_ROOT = REPOSITORY_ROOT / "skills" / "project-knowledge"
VALIDATOR = PROJECT_KNOWLEDGE_ROOT / "scripts" / "validate_knowledge.py"
MARKER = ".project-knowledge-scenario-test.json"
WORKSPACE_NAME = "workspace"
DETERMINISTIC_RESULT = "deterministic.json"
JUDGE_RESULT = "judge.json"
BENCHMARK_RESULT = "benchmark.json"
BENCHMARK_CONFIG = SKILL_ROOT / "agents" / "benchmark.yml"
CREDIT_RATES_CONFIG = SKILL_ROOT / "agents" / "credit-rates.yml"
UTILITY_RESULT = "utility.json"
UTILITY_CONFIG = SKILL_ROOT / "agents" / "utility.yml"
UTILITY_MARKER = ".project-knowledge-utility-benchmark.json"
UTILITY_SCENARIO = "utility-basic"
SCENARIO_CONFIG = SKILL_ROOT / "agents" / "scenarios.yml"
LARGE_RESULT = "large.json"
LARGE_SCENARIO = "large-lifecycle"
LARGE_SCENARIO_CONFIG = SCENARIOS_ROOT / LARGE_SCENARIO / "scenario.yml"
LARGE_OPERATIONS = {"write", "delete", "move"}
UTILITY_CONDITIONS = ("no_kb", "with_kb")
UTILITY_DIMENSIONS = (
    "requirement_compliance",
    "project_convention_compliance",
    "architectural_consistency",
    "scope_discipline",
    "code_quality",
    "maintainability",
)
DIMENSIONS = (
    "correctness",
    "completeness",
    "provenance",
    "classification",
    "noise_rejection",
    "unsupported_claims",
)
MANAGED_SOURCE_NAMES = {".git", ".gitignore", "AGENTS.md", "project-knowledge", "__pycache__"}


class ScenarioError(RuntimeError):
    """シナリオ実行基盤のエラーを表す。"""


def prepare(scenario: str) -> Path:
    """Fixtureを隔離workspaceへ複製してGit baselineを作成する。"""

    if scenario != "quick-basic":
        raise ScenarioError(f"unsupported scenario: {scenario}")
    # 期待値を含まない一時workspaceだけをActorへ渡す
    run_root = Path(tempfile.gettempdir()).resolve() / f"pk-scenario-{uuid.uuid4().hex}"
    return prepare_in(scenario, run_root)


def prepare_in(scenario: str, run_root: Path) -> Path:
    """指定したrun rootにQuick workspaceを準備する。"""

    if scenario != "quick-basic":
        raise ScenarioError(f"unsupported scenario: {scenario}")
    fixture = (SCENARIOS_ROOT / scenario / "fixture").resolve()
    if not fixture.is_dir():
        raise ScenarioError(f"fixture not found: {fixture}")
    workspace = run_root / WORKSPACE_NAME
    try:
        shutil.copytree(
            fixture,
            workspace,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"),
        )
        metadata = {
            "scenario": scenario,
            "fixture": str(fixture),
            "fixture_hash": tree_hash(fixture),
            "workspace_source_hash": tree_hash(workspace, MANAGED_SOURCE_NAMES),
            "workspace": str(workspace.resolve()),
            "orchestrator_session_id": os.environ.get("CODEX_THREAD_ID", "unavailable"),
            "sessions": {"actor": None, "judge": None},
        }
        write_json(run_root / MARKER, metadata)
        initialize_git(workspace)
    except Exception:
        # prepareが途中で失敗したrunだけを回収する
        if run_root.is_dir():
            make_tree_writable(run_root)
            shutil.rmtree(run_root)
        raise
    return workspace.resolve()


def load_scenario_agent_config(scenario: str) -> dict[str, Any]:
    """QuickとLargeで共通利用するActor/Judge設定を読み込む。"""

    try:
        config = yaml.safe_load(SCENARIO_CONFIG.read_text(encoding="utf-8"))
    except OSError as error:
        raise ScenarioError(f"scenario agent configuration unavailable: {error}") from error
    scenario_config = config.get(scenario) if isinstance(config, dict) else None
    if not isinstance(scenario_config, dict):
        raise ScenarioError(f"scenario agent configuration not found: {scenario}")
    for role in ("actor", "judge"):
        role_config = scenario_config.get(role)
        if not isinstance(role_config, dict) or not all(
            isinstance(role_config.get(key), str)
            for key in ("model", "reasoning_effort")
        ):
            raise ScenarioError(f"scenario {role} configuration is invalid: {scenario}")
    return scenario_config


def load_large_scenario() -> dict[str, Any]:
    """Large Fixtureとlifecycleのversion管理された定義を読み込む。"""

    try:
        config = yaml.safe_load(LARGE_SCENARIO_CONFIG.read_text(encoding="utf-8"))
    except OSError as error:
        raise ScenarioError(f"large scenario configuration unavailable: {error}") from error
    if not isinstance(config, dict):
        raise ScenarioError("large scenario configuration is invalid")
    required_strings = ("scenario", "scenario_version", "fixture_version")
    if not all(isinstance(config.get(key), str) for key in required_strings):
        raise ScenarioError("large scenario versions are invalid")
    if config["scenario"] != LARGE_SCENARIO:
        raise ScenarioError(f"unsupported large scenario: {config['scenario']}")
    checkpoints = config.get("judge_checkpoints")
    if not string_list(checkpoints):
        raise ScenarioError("large judge checkpoints are invalid")
    return config


def prepare_large(scenario: str) -> Path:
    """Large Fixtureを隔離し、lifecycle descriptorを準備する。"""

    if scenario != LARGE_SCENARIO:
        raise ScenarioError(f"unsupported large scenario: {scenario}")
    config = load_large_scenario()
    load_scenario_agent_config(scenario)
    fixture = (SCENARIOS_ROOT / scenario / "fixture" / "initial").resolve()
    changes_root = (SCENARIOS_ROOT / scenario / "changes").resolve()
    if not fixture.is_dir() or not changes_root.is_dir():
        raise ScenarioError("large fixture or changes not found")
    change_sets = load_change_sets(changes_root)
    run_root = Path(tempfile.gettempdir()).resolve() / f"pk-large-{uuid.uuid4().hex}"
    workspace = run_root / WORKSPACE_NAME
    try:
        # Actorへ期待値やchange set本体を渡さず、初期Sourceだけを複製
        shutil.copytree(fixture, workspace)
        initialize_git(workspace)
        source_hash = tree_hash(workspace, MANAGED_SOURCE_NAMES)
        marker = {
            "scenario": scenario,
            "fixture": str(fixture),
            "fixture_hash": tree_hash(fixture),
            "workspace_source_hash": source_hash,
            "workspace": str(workspace.resolve()),
            "orchestrator_session_id": os.environ.get("CODEX_THREAD_ID", "unavailable"),
            "sessions": {"actor": None, "judge": None},
        }
        write_json(run_root / MARKER, marker)
        (run_root / "judges").mkdir()
        initial = build_large_step("initial", "init", None, True, workspace)
        descriptor = {
            "benchmark": "project-knowledge-large",
            "execution_mode": "normal",
            "single_run": True,
            "scenario": scenario,
            "scenario_version": config["scenario_version"],
            "fixture_version": config["fixture_version"],
            "workspace": str(workspace.resolve()),
            "fixture": {
                "path": str(fixture),
                "hash": marker["fixture_hash"],
                **repository_statistics(workspace),
            },
            "change_sets": change_sets,
            "judge_checkpoints": config["judge_checkpoints"],
            "current_step": "initial",
            "steps": [initial],
            "orchestrator_session_id": marker["orchestrator_session_id"],
            "summary": None,
        }
        write_json(run_root / LARGE_RESULT, descriptor)
    except Exception:
        if run_root.is_dir():
            make_tree_writable(run_root)
            shutil.rmtree(run_root)
        raise
    return (run_root / LARGE_RESULT).resolve()


def load_change_sets(changes_root: Path) -> list[dict[str, Any]]:
    """順序付きChange Set manifestを検証して読み込む。"""

    change_sets: list[dict[str, Any]] = []
    for path in sorted(changes_root.glob("*.yml")):
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(value, dict) or not all(
            isinstance(value.get(key), str) for key in ("id", "size", "summary")
        ):
            raise ScenarioError(f"invalid change set: {path}")
        operations = value.get("operations")
        if not isinstance(operations, list) or not operations:
            raise ScenarioError(f"change set has no operations: {path}")
        for operation in operations:
            validate_change_operation(operation, path)
        change_sets.append({
            "id": value["id"],
            "size": value["size"],
            "summary": value["summary"],
            "manifest": str(path.resolve()),
        })
    if len(change_sets) < 10:
        raise ScenarioError("large scenario requires at least 10 change sets")
    if len({item["id"] for item in change_sets}) != len(change_sets):
        raise ScenarioError("large change set ids must be unique")
    return change_sets


def validate_change_operation(operation: Any, path: Path) -> None:
    """Change Set operationの必須項目と種別を検査する。"""

    if not isinstance(operation, dict) or operation.get("action") not in LARGE_OPERATIONS:
        raise ScenarioError(f"invalid change operation: {path}")
    action = operation["action"]
    required = {"write": ("path", "content"), "delete": ("path",), "move": ("from", "to")}
    if not all(isinstance(operation.get(key), str) for key in required[action]):
        raise ScenarioError(f"invalid {action} operation: {path}")


def build_large_step(
    step_id: str,
    operation: str,
    change_set: dict[str, Any] | None,
    checkpoint: bool,
    workspace: Path,
) -> dict[str, Any]:
    """step別machine-readable resultの初期値を構築する。"""

    return {
        "step": step_id,
        "operation": operation,
        "change_set": change_set,
        "judge_checkpoint": checkpoint,
        "changed_files": 0,
        "changed_bytes": 0,
        "repository": repository_statistics(workspace),
        "validation": None,
        "quality_score": "unavailable",
        "knowledge": None,
        "actor_session": None,
        "judge_session": None,
        "actor_usage": unavailable_usage(),
        "judge_usage": unavailable_usage(),
        "issues": [],
    }


def load_benchmark_config() -> dict[str, Any]:
    """比較対象Actorと固定Judgeの設定を読み込む。"""

    try:
        config = yaml.safe_load(BENCHMARK_CONFIG.read_text(encoding="utf-8"))
    except OSError as error:
        raise ScenarioError(f"benchmark configuration unavailable: {error}") from error
    if not isinstance(config, dict) or not isinstance(config.get("models"), list):
        raise ScenarioError("benchmark configuration models are invalid")
    models = config["models"]
    valid_model = lambda model: isinstance(model, dict) and all(
        isinstance(model.get(key), str) for key in ("id", "display_name", "model")
    )
    if not models or not all(valid_model(model) for model in models):
        raise ScenarioError("benchmark model definitions are invalid")
    if len({model["id"] for model in models}) != len(models):
        raise ScenarioError("benchmark model ids must be unique")
    judge = config.get("judge")
    if not isinstance(judge, dict) or not isinstance(judge.get("model"), str):
        raise ScenarioError("benchmark judge definition is invalid")
    return config


def load_utility_config() -> dict[str, Any]:
    """Utility用Task AgentとJudgeの設定を読み込む。"""

    try:
        config = yaml.safe_load(UTILITY_CONFIG.read_text(encoding="utf-8"))
    except OSError as error:
        raise ScenarioError(f"utility configuration unavailable: {error}") from error
    if not isinstance(config, dict):
        raise ScenarioError("utility configuration is invalid")
    for role in ("task", "judge"):
        value = config.get(role)
        if not isinstance(value, dict) or not all(
            isinstance(value.get(key), str) for key in ("display_name", "model", "reasoning_effort")
        ):
            raise ScenarioError(f"utility {role} definition is invalid")
    return config


def prepare_utility(scenario: str) -> Path:
    """同じsource stateからBuilderとA/B Task workspaceを準備する。"""

    if scenario != UTILITY_SCENARIO:
        raise ScenarioError(f"unsupported utility scenario: {scenario}")
    fixture = (SCENARIOS_ROOT / scenario / "fixture").resolve()
    if not fixture.is_dir():
        raise ScenarioError(f"fixture not found: {fixture}")

    # 三つのworkspaceを同一Fixtureから個別に複製
    config = load_utility_config()
    run_root = Path(tempfile.gettempdir()).resolve() / f"pk-utility-{uuid.uuid4().hex}"
    workspaces: dict[str, str] = {}
    try:
        for role in ("knowledge_builder", *UTILITY_CONDITIONS):
            workspace = prepare_fixture_workspace(fixture, run_root / role)
            workspaces[role] = str(workspace)

        # JudgeへCondition名を渡さないため、対応表だけをdescriptorへ保持
        candidate_ids = ["Candidate A", "Candidate B"]
        secrets.SystemRandom().shuffle(candidate_ids)
        candidates = {
            condition: candidate_ids[index] for index, condition in enumerate(UTILITY_CONDITIONS)
        }
        payload = {
            "benchmark": "project-knowledge-utility",
            "single_run": True,
            "runs_per_condition": 1,
            "scenario": scenario,
            "task": "Add shipment cancellation API",
            "models": config,
            "workspaces": workspaces,
            "candidate_mapping": candidates,
            "usage": {
                "knowledge_builder": unavailable_usage(),
                "no_kb_task": unavailable_usage(),
                "with_kb_task": unavailable_usage(),
                "judge": unavailable_usage(),
            },
        }
        write_json(run_root / UTILITY_MARKER, {"descriptor": str(run_root / UTILITY_RESULT)})
        write_json(run_root / UTILITY_RESULT, payload)
    except Exception:
        if run_root.is_dir():
            make_tree_writable(run_root)
            shutil.rmtree(run_root)
        raise
    return (run_root / UTILITY_RESULT).resolve()


def prepare_fixture_workspace(fixture: Path, run_root: Path) -> Path:
    """Utility Fixtureを独立したGit workspaceへ複製する。"""

    workspace = run_root / WORKSPACE_NAME
    shutil.copytree(
        fixture,
        workspace,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"),
    )
    metadata = {
        "scenario": UTILITY_SCENARIO,
        "fixture": str(fixture),
        "fixture_hash": tree_hash(fixture),
        "workspace_source_hash": tree_hash(workspace, MANAGED_SOURCE_NAMES),
        "workspace": str(workspace.resolve()),
    }
    write_json(run_root / MARKER, metadata)
    initialize_git(workspace)
    return workspace.resolve()


def install_utility_knowledge(descriptor_path: Path) -> dict[str, Any]:
    """Builderの生成物を検査し、With-KB workspaceだけへ複製する。"""

    descriptor = load_utility_descriptor(descriptor_path)
    builder = Path(descriptor["workspaces"]["knowledge_builder"])
    with_kb = Path(descriptor["workspaces"]["with_kb"])

    # Builderがsource projectを変更せず有効なKnowledgeを作ったことを確認
    builder_result = validate(builder)
    if builder_result["status"] != "PASS":
        raise ScenarioError("knowledge builder deterministic validation did not pass")
    knowledge = builder / "project-knowledge"
    target = with_kb / "project-knowledge"
    if target.exists():
        raise ScenarioError("with-kb workspace already contains project-knowledge")
    shutil.copytree(knowledge, target)

    # No-KB側を含む三workspaceの一次情報が同一であることを固定
    source_hashes = {
        role: tree_hash(Path(path), MANAGED_SOURCE_NAMES)
        for role, path in descriptor["workspaces"].items()
    }
    if len(set(source_hashes.values())) != 1:
        raise ScenarioError("utility source workspaces are not identical")
    descriptor["knowledge"] = {
        "status": "ready",
        "source_hashes": source_hashes,
        "knowledge_hash": tree_hash(knowledge),
        "builder_deterministic": builder_result,
    }
    write_json(descriptor_path, descriptor)
    return descriptor["knowledge"]


def evaluate_utility_condition(descriptor_path: Path, condition: str) -> dict[str, Any]:
    """Task成果物を公開test、hidden checks、scope検査で評価する。"""

    if condition not in UTILITY_CONDITIONS:
        raise ScenarioError(f"unsupported utility condition: {condition}")
    descriptor = load_utility_descriptor(descriptor_path)
    workspace = Path(descriptor["workspaces"][condition])
    scenario_root = SCENARIOS_ROOT / descriptor["scenario"]

    # 構文、既存回帰、Task Agent非公開の機能・設計checkを順に実行
    build = run_command([sys.executable, "-m", "compileall", "-q", "src"], workspace)
    candidate_tests = run_command(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests"], workspace
    )
    existing = run_command(
        [sys.executable, str(scenario_root / "hidden_tests" / "regression_test.py"), str(workspace)],
        workspace,
    )
    hidden = run_command(
        [sys.executable, str(scenario_root / "hidden_tests" / "evaluate.py"), str(workspace)],
        workspace,
    )
    hidden_result = parse_hidden_result(hidden)

    # Task範囲外の変更とCondition間へ漏れてはいけないKnowledge変更を検出
    changed = git_changed_paths(workspace)
    forbidden = [path for path in changed if not path.startswith(("src/", "tests/"))]
    if condition == "with_kb":
        forbidden = [path for path in forbidden if not path.startswith("project-knowledge/")]
        knowledge_hash = descriptor.get("knowledge", {}).get("knowledge_hash")
        if knowledge_hash != tree_hash(workspace / "project-knowledge"):
            forbidden.append("project-knowledge/ (modified)")
    existing_total = parse_unittest_count(existing["output"])
    result = {
        "condition": condition,
        "build": "PASS" if build["returncode"] == 0 else "FAIL",
        "existing_tests": {
            "passed": existing_total if existing["returncode"] == 0 else 0,
            "total": existing_total,
            "status": "PASS" if existing["returncode"] == 0 else "FAIL",
        },
        "candidate_tests": {
            "passed": parse_unittest_count(candidate_tests["output"]) if candidate_tests["returncode"] == 0 else 0,
            "total": parse_unittest_count(candidate_tests["output"]),
            "status": "PASS" if candidate_tests["returncode"] == 0 else "FAIL",
        },
        "hidden_tests": hidden_result,
        "scope": {"status": "PASS" if not forbidden else "FAIL", "forbidden_changes": forbidden},
    }
    result["task_success"] = all((
        result["build"] == "PASS",
        result["existing_tests"]["status"] == "PASS",
        result["candidate_tests"]["status"] == "PASS",
        hidden_result["passed"] == hidden_result["total"],
        result["scope"]["status"] == "PASS",
    ))
    write_json(workspace.parent / DETERMINISTIC_RESULT, result)
    return result


def run_command(command: list[str], cwd: Path) -> dict[str, Any]:
    """評価commandを実行し、診断用の結合出力を返す。"""

    result = subprocess.run(command, cwd=cwd, capture_output=True, text=True, check=False)
    return {"returncode": result.returncode, "output": (result.stdout + result.stderr).strip()}


def parse_hidden_result(result: dict[str, Any]) -> dict[str, Any]:
    """hidden evaluatorの機械可読結果を検証する。"""

    if result["returncode"] not in {0, 1}:
        raise ScenarioError(f"hidden evaluator failed: {result['output']}")
    try:
        payload = json.loads(result["output"])
    except json.JSONDecodeError as error:
        raise ScenarioError("hidden evaluator returned invalid JSON") from error
    if not isinstance(payload, dict) or not all(
        isinstance(payload.get(key), int) for key in ("passed", "total")
    ):
        raise ScenarioError("hidden evaluator result is invalid")
    return payload


def parse_unittest_count(output: str) -> int:
    """unittest標準出力から実行件数だけを取得する。"""

    match = re.search(r"Ran (\d+) tests?", output)
    return int(match.group(1)) if match else 0


def git_changed_paths(workspace: Path) -> list[str]:
    """Task Agentがbaselineから変更したpathを列挙する。"""

    # 先頭空白を保持するporcelain形式でpathを安全に分離
    result = subprocess.run(
        ["git", "status", "--porcelain=v1", "-z", "--untracked-files=all"],
        cwd=workspace,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        raise ScenarioError(f"cannot inspect task changes: {detail}")
    paths = [item[3:].replace("\\", "/") for item in result.stdout.split("\0") if len(item) > 3]
    return sorted(
        path for path in paths
        if "__pycache__/" not in path and not path.endswith((".pyc", ".pyo"))
    )


def prepare_blind_candidates(descriptor_path: Path) -> dict[str, str]:
    """Judge用にCondition情報とKnowledgeを除いた中立snapshotを作る。"""

    descriptor = load_utility_descriptor(descriptor_path)
    blind_root = descriptor_path.parent / "blind"
    if blind_root.exists():
        raise ScenarioError("blind candidates already prepared")
    paths: dict[str, str] = {}
    for condition in UTILITY_CONDITIONS:
        candidate = descriptor["candidate_mapping"][condition]
        destination = blind_root / candidate.lower().replace(" ", "-")
        shutil.copytree(
            Path(descriptor["workspaces"][condition]),
            destination,
            ignore=shutil.ignore_patterns(".git", "project-knowledge", "__pycache__", "*.pyc"),
        )
        paths[candidate] = str(destination.resolve())
    descriptor["blind_candidates"] = paths
    write_json(descriptor_path, descriptor)
    return paths


def validate_utility_judge(judge: dict[str, Any]) -> None:
    """Blind Judge JSONのscore契約を検証する。"""

    candidates = judge.get("candidates")
    if not isinstance(candidates, dict) or set(candidates) != {"Candidate A", "Candidate B"}:
        raise ScenarioError("utility judge candidates are invalid")
    for candidate, value in candidates.items():
        if not isinstance(value, dict):
            raise ScenarioError(f"utility judge candidate is invalid: {candidate}")
        dimensions = value.get("dimensions")
        if not isinstance(dimensions, dict) or set(dimensions) != set(UTILITY_DIMENSIONS):
            raise ScenarioError(f"utility judge dimensions are invalid: {candidate}")
        for name, dimension in dimensions.items():
            if not isinstance(dimension, dict) or not isinstance(dimension.get("score"), int):
                raise ScenarioError(f"utility judge score is invalid: {candidate} {name}")
            if not 0 <= dimension["score"] <= 100:
                raise ScenarioError(f"utility judge score is out of range: {candidate} {name}")
            if not isinstance(dimension.get("reason"), str) or not string_list(dimension.get("evidence")):
                raise ScenarioError(f"utility judge details are invalid: {candidate} {name}")
    if judge.get("preference") not in {"Candidate A", "Candidate B", "tie"}:
        raise ScenarioError("utility judge preference is invalid")
    if not isinstance(judge.get("summary"), str):
        raise ScenarioError("utility judge summary is invalid")


def utility_report(descriptor_path: Path) -> tuple[str, int]:
    """A/B結果をConditionへ復元し、delta付きReportとJSONを生成する。"""

    descriptor = load_utility_descriptor(descriptor_path)
    judge = read_json(descriptor_path.parent / JUDGE_RESULT)
    validate_utility_judge(judge)
    results: dict[str, Any] = {}
    for condition in UTILITY_CONDITIONS:
        deterministic = read_json(Path(descriptor["workspaces"][condition]).parent / DETERMINISTIC_RESULT)
        candidate = descriptor["candidate_mapping"][condition]
        candidate_judge = judge["candidates"][candidate]
        results[condition] = {
            "deterministic": deterministic,
            "judge": candidate_judge,
            "tokens": descriptor["usage"][f"{condition}_task"],
            "quality_score": round(sum(
                item["score"] for item in candidate_judge["dimensions"].values()
            ) / len(UTILITY_DIMENSIONS)),
        }
    delta = utility_delta(results)
    descriptor["results"] = results
    descriptor["judge"] = {"preference": judge["preference"], "summary": judge["summary"]}
    descriptor["delta"] = delta
    write_json(descriptor_path, descriptor)
    return render_utility_report(descriptor), 0


def utility_delta(results: dict[str, Any]) -> dict[str, Any]:
    """With-KBからNo-KBを引いた主要差分を計算する。"""

    no_kb = results["no_kb"]
    with_kb = results["with_kb"]
    token_delta: dict[str, Any] = {}
    for key in unavailable_usage():
        left = no_kb["tokens"].get(key)
        right = with_kb["tokens"].get(key)
        token_delta[key] = right - left if isinstance(left, int) and isinstance(right, int) else "unavailable"
    return {
        "quality": with_kb["quality_score"] - no_kb["quality_score"],
        "hidden_tests": with_kb["deterministic"]["hidden_tests"]["passed"] - no_kb["deterministic"]["hidden_tests"]["passed"],
        "tokens": token_delta,
    }


def render_utility_report(payload: dict[str, Any]) -> str:
    """Utility結果をsingle-runであることが分かる比較表へ整形する。"""

    no_kb = payload["results"]["no_kb"]
    with_kb = payload["results"]["with_kb"]
    delta = payload["delta"]
    existing_no, existing_with = (
        no_kb["deterministic"]["existing_tests"], with_kb["deterministic"]["existing_tests"]
    )
    hidden_no, hidden_with = (
        no_kb["deterministic"]["hidden_tests"], with_kb["deterministic"]["hidden_tests"]
    )
    lines = [
        "Project Knowledge Utility Benchmark",
        f"Task: {payload['task']}",
        f"Task model: {payload['models']['task']['display_name']}",
        f"Judge model: {payload['models']['judge']['display_name']}",
        "Runs per condition: 1 (single-run utility benchmark)",
        "",
        "                           No-KB    With-KB    Delta",
        f"Task success               {pass_fail(no_kb['deterministic']['task_success']):<9}{pass_fail(with_kb['deterministic']['task_success']):<11}--",
        f"Build                      {no_kb['deterministic']['build']:<9}{with_kb['deterministic']['build']:<11}--",
        f"Existing tests             {ratio(existing_no):<9}{ratio(existing_with):<11}--",
        f"Hidden tests               {ratio(hidden_no):<9}{ratio(hidden_with):<11}{signed(delta['hidden_tests'])}",
        f"Requirement score          {judge_score(no_kb, 'requirement_compliance'):<9}{judge_score(with_kb, 'requirement_compliance'):<11}{signed(judge_score(with_kb, 'requirement_compliance') - judge_score(no_kb, 'requirement_compliance'))}",
        f"Convention score           {judge_score(no_kb, 'project_convention_compliance'):<9}{judge_score(with_kb, 'project_convention_compliance'):<11}{signed(judge_score(with_kb, 'project_convention_compliance') - judge_score(no_kb, 'project_convention_compliance'))}",
        f"Architecture score         {judge_score(no_kb, 'architectural_consistency'):<9}{judge_score(with_kb, 'architectural_consistency'):<11}{signed(judge_score(with_kb, 'architectural_consistency') - judge_score(no_kb, 'architectural_consistency'))}",
        f"Judge quality score        {no_kb['quality_score']:<9}{with_kb['quality_score']:<11}{signed(delta['quality'])}",
    ]
    for key, label in (("input_tokens", "Task input tokens"), ("output_tokens", "Task output tokens"), ("total_tokens", "Task total tokens")):
        left = no_kb["tokens"].get(key, "unavailable")
        right = with_kb["tokens"].get(key, "unavailable")
        lines.append(f"{label:<27}{left!s:<12}{right!s:<12}{signed(delta['tokens'][key])}")
    lines.extend(["", "Observed result in this run:"])
    if delta["quality"] > 0:
        lines.append(f"- With-KB received a {signed(delta['quality'])} higher Judge quality score.")
    elif delta["quality"] < 0:
        lines.append(f"- With-KB received a {signed(delta['quality'])} lower Judge quality score.")
    else:
        lines.append("- Both conditions received the same Judge quality score.")
    lines.append(f"- With-KB changed the hidden-test pass count by {signed(delta['hidden_tests'])}.")
    lines.append("- This single run does not establish a statistical improvement effect.")
    mapping = payload["candidate_mapping"]
    lines.extend([
        "",
        "Major candidate differences:",
        f"- Blind mapping restored: No-KB = {mapping['no_kb']}; With-KB = {mapping['with_kb']}.",
        f"- {payload['judge']['summary']}",
    ])
    return "\n".join(lines)


def ratio(value: dict[str, Any]) -> str:
    """passed/total形式へ整形する。"""

    return f"{value['passed']}/{value['total']}"


def judge_score(result: dict[str, Any], dimension: str) -> int:
    """Condition結果から指定したJudge scoreを返す。"""

    return result["judge"]["dimensions"][dimension]["score"]


def pass_fail(value: bool) -> str:
    """真偽値をReport用statusへ変換する。"""

    return "PASS" if value else "FAIL"


def signed(value: Any) -> str:
    """数値deltaへ符号を付け、取得不能値はそのまま返す。"""

    return f"{value:+}" if isinstance(value, int) else str(value)


def load_utility_descriptor(descriptor_path: Path) -> dict[str, Any]:
    """Utility descriptorと安全な一時runの対応を確認する。"""

    resolved = descriptor_path.resolve()
    marker = read_json(resolved.parent / UTILITY_MARKER)
    if marker.get("descriptor") != str(resolved):
        raise ScenarioError("descriptor does not match utility marker")
    descriptor = read_json(resolved)
    if descriptor.get("benchmark") != "project-knowledge-utility":
        raise ScenarioError("invalid utility descriptor")
    return descriptor


def cleanup_utility(descriptor_path: Path) -> None:
    """markerで識別できるUtility一時run全体を削除する。"""

    load_utility_descriptor(descriptor_path)
    run_root = descriptor_path.resolve().parent
    temporary_root = Path(tempfile.gettempdir()).resolve()
    if not is_within(run_root, temporary_root) or run_root == temporary_root:
        raise ScenarioError(f"refusing cleanup outside temporary root: {run_root}")
    make_tree_writable(run_root)
    shutil.rmtree(run_root)


def prepare_benchmark(scenario: str) -> Path:
    """同一Quick fixtureからモデルごとの隔離workspaceを準備する。"""

    config = load_benchmark_config()
    benchmark_root = Path(tempfile.gettempdir()).resolve() / f"pk-benchmark-{uuid.uuid4().hex}"
    candidates: list[dict[str, Any]] = []
    try:
        for index, model in enumerate(config["models"]):
            workspace = prepare_in(scenario, benchmark_root / model["id"])
            candidates.append({
                "id": f"Candidate {chr(ord('A') + index)}", "model_id": model["id"],
                "model": model["model"], "display_name": model["display_name"],
                "workspace": str(workspace), "actor_usage": unavailable_usage(),
                "actor_session": None, "judge_session": None,
            })
        write_json(benchmark_root / BENCHMARK_RESULT, {
            "benchmark": "project-knowledge-quick", "single_run": True, "scenario": scenario,
            "judge": config["judge"], "candidates": candidates,
            "orchestrator_session_id": os.environ.get("CODEX_THREAD_ID", "unavailable"),
        })
    except Exception:
        if benchmark_root.is_dir():
            make_tree_writable(benchmark_root)
            shutil.rmtree(benchmark_root)
        raise
    return (benchmark_root / BENCHMARK_RESULT).resolve()


def record_session(
    target: Path,
    role: str,
    session_id: str,
    agent_path: str,
    candidate_id: str | None = None,
    parent_session_id: str | None = None,
    step_id: str | None = None,
) -> dict[str, Any]:
    """ActorまたはJudgeのsubagent session識別子をrunへ記録する。"""

    if role not in {"actor", "judge"}:
        raise ScenarioError(f"unsupported session role: {role}")
    if target.is_dir():
        run_root, metadata = load_run(target)
        model = load_scenario_agent_config(metadata["scenario"])[role]["model"]
        reference = build_session_reference(
            metadata, model, session_id, agent_path, parent_session_id
        )
        sessions = metadata.setdefault("sessions", {"actor": None, "judge": None})
        store_session_reference(sessions, role, reference)
        write_json(run_root / MARKER, metadata)
        return reference

    descriptor = read_json(target)
    if descriptor.get("benchmark") == "project-knowledge-large":
        return record_large_session(
            target, descriptor, role, session_id, agent_path, parent_session_id, step_id
        )
    candidates = descriptor.get("candidates")
    if not isinstance(candidates, list) or not isinstance(candidate_id, str):
        raise ScenarioError("benchmark candidate id is required")
    candidate = next(
        (
            item for item in candidates
            if isinstance(item, dict) and item.get("model_id") == candidate_id
        ),
        None,
    )
    if candidate is None:
        raise ScenarioError(f"benchmark candidate not found: {candidate_id}")
    model = candidate["model"] if role == "actor" else descriptor["judge"]["model"]
    reference = build_session_reference(
        descriptor, model, session_id, agent_path, parent_session_id
    )
    store_session_reference(candidate, f"{role}_session", reference)
    write_json(target, descriptor)
    return reference


def record_large_session(
    descriptor_path: Path,
    descriptor: dict[str, Any],
    role: str,
    session_id: str,
    agent_path: str,
    parent_session_id: str | None,
    step_id: str | None,
) -> dict[str, str]:
    """Largeのoperation単位でActor/Judge sessionを記録する。"""

    selected_step = step_id or descriptor.get("current_step")
    step = find_large_step(descriptor, selected_step)
    model = load_scenario_agent_config(descriptor["scenario"])[role]["model"]
    reference = build_session_reference(
        descriptor, model, session_id, agent_path, parent_session_id
    )
    store_session_reference(step, f"{role}_session", reference)
    write_json(descriptor_path, descriptor)
    return reference


def build_session_reference(
    container: dict[str, Any],
    model: str,
    session_id: str,
    agent_path: str,
    parent_session_id: str | None,
) -> dict[str, str]:
    """session照合に必要な識別子をまとめる。"""

    parent = parent_session_id or container.get("orchestrator_session_id")
    return {
        "session_id": session_id,
        "parent_session_id": parent if isinstance(parent, str) else "unavailable",
        "agent_path": agent_path,
        "model": model,
    }


def store_session_reference(
    container: dict[str, Any], key: str, reference: dict[str, str]
) -> None:
    """異なるsessionで既存対応を暗黙に上書きしない。"""

    existing = container.get(key)
    if existing is not None and existing != reference:
        raise ScenarioError(f"session reference already recorded: {key}")
    container[key] = reference


def initialize_git(workspace: Path) -> None:
    """一時workspaceに再現可能な初期Git commitを作成する。"""

    commands = (
        ("git", "init", "--quiet"),
        ("git", "config", "user.name", "Project Knowledge Scenario Actor"),
        ("git", "config", "user.email", "scenario@example.invalid"),
        ("git", "add", "."),
        ("git", "commit", "--quiet", "-m", "Initial fixture"),
    )
    environment = os.environ.copy()
    environment["GIT_AUTHOR_DATE"] = "2026-08-27T00:00:00+09:00"
    environment["GIT_COMMITTER_DATE"] = "2026-08-27T00:00:00+09:00"
    for command in commands:
        result = subprocess.run(
            command,
            cwd=workspace,
            env=environment,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            detail = result.stderr.strip() or result.stdout.strip()
            raise ScenarioError(f"Git initialization failed: {detail}")


def advance_large(descriptor_path: Path) -> dict[str, Any]:
    """次のChange Setを適用して独立commitを作成する。"""

    descriptor = load_large_descriptor(descriptor_path)
    workspace = Path(descriptor["workspace"])
    current = find_large_step(descriptor, descriptor["current_step"])
    if not isinstance(current.get("validation"), dict):
        raise ScenarioError(f"current large step is not validated: {current['step']}")
    completed_updates = sum(step["operation"] == "update" for step in descriptor["steps"])
    if completed_updates >= len(descriptor["change_sets"]):
        raise ScenarioError("large scenario has no remaining change set")
    checkpoint_large_actor(workspace, current["step"])
    change_set = descriptor["change_sets"][completed_updates]
    changed_files, changed_bytes = apply_change_set(workspace, Path(change_set["manifest"]))
    commit_change_set(workspace, change_set["id"], completed_updates + 1)

    # 次stepで正当なSource変更だけを許容するためexpected hashを更新
    marker_path = descriptor_path.parent / MARKER
    marker = read_json(marker_path)
    marker["workspace_source_hash"] = tree_hash(workspace, MANAGED_SOURCE_NAMES)
    marker["sessions"] = {"actor": None, "judge": None}
    write_json(marker_path, marker)
    checkpoint = change_set["id"] in descriptor["judge_checkpoints"]
    step = build_large_step(change_set["id"], "update", change_set, checkpoint, workspace)
    step["changed_files"] = changed_files
    step["changed_bytes"] = changed_bytes
    descriptor["steps"].append(step)
    descriptor["current_step"] = change_set["id"]
    write_json(descriptor_path, descriptor)
    return step


def apply_change_set(workspace: Path, manifest_path: Path) -> tuple[int, int]:
    """宣言的Change Setをworkspace内だけへ適用する。"""

    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    operations = manifest["operations"]
    touched: set[Path] = set()
    changed_bytes = 0
    for operation in operations:
        action = operation["action"]
        paths = [operation.get("path")] if action != "move" else [operation["from"], operation["to"]]
        targets = [safe_large_target(workspace, value) for value in paths if isinstance(value, str)]
        before = sum(target.stat().st_size for target in targets if target.is_file())
        if action == "write":
            target = targets[0]
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(operation["content"], encoding="utf-8", newline="\n")
            touched.add(target)
        elif action == "delete":
            target = targets[0]
            if not target.is_file():
                raise ScenarioError(f"change set delete target not found: {target}")
            target.unlink()
            touched.add(target)
        else:
            source, target = targets
            if not source.is_file():
                raise ScenarioError(f"change set move source not found: {source}")
            target.parent.mkdir(parents=True, exist_ok=True)
            source.replace(target)
            touched.update({source, target})
        after = sum(target.stat().st_size for target in targets if target.is_file())
        changed_bytes += before + after
    return len(touched), changed_bytes


def safe_large_target(workspace: Path, relative: str) -> Path:
    """Change Set pathをSource領域内の安全な相対pathへ限定する。"""

    candidate = (workspace / relative).resolve()
    if (
        not is_within(candidate, workspace.resolve())
        or candidate == workspace.resolve()
        or any(part in {".git", "project-knowledge"} for part in Path(relative).parts)
    ):
        raise ScenarioError(f"unsafe large change target: {relative}")
    return candidate


def ensure_clean_git(workspace: Path) -> None:
    """Change Set適用前に前operationがcommit済みであることを保証する。"""

    result = subprocess.run(
        ["git", "status", "--porcelain"], cwd=workspace,
        capture_output=True, text=True, check=False,
    )
    if result.returncode != 0 or result.stdout.strip():
        detail = result.stderr.strip() or result.stdout.strip() or "git status failed"
        raise ScenarioError(f"large workspace must be clean before advance: {detail}")


def checkpoint_large_actor(workspace: Path, step_id: str) -> None:
    """検証済みKnowledgeだけをcommitし、次updateのGit baselineを確定する。"""

    changed = git_changed_paths(workspace)
    allowed = [
        path for path in changed
        if path in {"AGENTS.md", ".gitignore"} or path.startswith("project-knowledge/")
    ]
    unexpected = sorted(set(changed) - set(allowed))
    if unexpected:
        raise ScenarioError(
            f"large actor changed source files before checkpoint: {', '.join(unexpected)}"
        )
    if allowed:
        commands = (
            ("git", "add", "--", "AGENTS.md", ".gitignore", "project-knowledge"),
            ("git", "commit", "--quiet", "-m", f"Checkpoint knowledge {step_id}"),
        )
        for command in commands:
            result = subprocess.run(
                command, cwd=workspace, capture_output=True, text=True, check=False
            )
            if result.returncode != 0:
                detail = result.stderr.strip() or result.stdout.strip()
                raise ScenarioError(f"large knowledge checkpoint failed: {detail}")

    # state.ymlはlocal cacheなのでKnowledge commit後のHEADへ進める
    detector = PROJECT_KNOWLEDGE_ROOT / "scripts" / "detect_changes.py"
    result = subprocess.run(
        [sys.executable, str(detector), str(workspace), "--write-baseline"],
        capture_output=True, text=True, check=False,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        raise ScenarioError(f"large baseline update failed: {detail}")
    ensure_clean_git(workspace)


def commit_change_set(workspace: Path, change_id: str, sequence: int) -> None:
    """Change Setを再現可能な日時の独立commitとして保存する。"""

    environment = os.environ.copy()
    environment["GIT_AUTHOR_DATE"] = f"2026-08-{27 + (sequence // 24):02d}T{sequence % 24:02d}:00:00+09:00"
    environment["GIT_COMMITTER_DATE"] = environment["GIT_AUTHOR_DATE"]
    for command in (("git", "add", "-A"), ("git", "commit", "--quiet", "-m", f"Apply {change_id}")):
        result = subprocess.run(
            command, cwd=workspace, env=environment,
            capture_output=True, text=True, check=False,
        )
        if result.returncode != 0:
            detail = result.stderr.strip() or result.stdout.strip()
            raise ScenarioError(f"large change commit failed: {detail}")


def repository_statistics(workspace: Path) -> dict[str, int]:
    """Knowledge領域とGit管理情報を除いたSource規模を計測する。"""

    files = [
        path for path in workspace.rglob("*")
        if path.is_file() and not any(part in MANAGED_SOURCE_NAMES for part in path.parts)
    ]
    return {"files": len(files), "characters": sum(len(path.read_text(encoding="utf-8")) for path in files)}


def validate(workspace: Path) -> dict[str, Any]:
    """既存validatorとシナリオ固有の隔離条件を検査する。"""

    run_root, metadata = load_run(workspace)
    findings: list[dict[str, str]] = []

    # 元FixtureとActorへ渡したsource projectの不変性を確認
    fixture = Path(metadata["fixture"])
    if tree_hash(fixture) != metadata["fixture_hash"]:
        add_finding(findings, "high", "fixture-modified", fixture)
    if tree_hash(workspace, MANAGED_SOURCE_NAMES) != metadata["workspace_source_hash"]:
        add_finding(findings, "high", "source-project-modified", workspace)

    # 現行Project Knowledge validatorをそのまま再利用
    knowledge_root = workspace / "project-knowledge"
    validator_findings, validator_error = run_validator(knowledge_root)
    findings.extend(validator_findings)
    if validator_error is not None:
        result = {
            "status": "ERROR",
            "findings": findings,
            "error": validator_error,
        }
        write_json(run_root / DETERMINISTIC_RESULT, result)
        return result

    # Quick初期構築として最低限必要なKnowledgeとprovenanceを検査
    findings.extend(find_required_knowledge(knowledge_root, workspace))

    # 存在するlocal sourceが隔離workspace外を指していないことを追加検査
    findings.extend(find_outside_sources(knowledge_root, workspace))
    findings.sort(key=finding_sort_key)
    status = "FAIL" if any(item["severity"] == "high" for item in findings) else "PASS"
    result = {"status": status, "findings": findings, "error": None}
    write_json(run_root / DETERMINISTIC_RESULT, result)
    return result


def run_validator(knowledge_root: Path) -> tuple[list[dict[str, str]], str | None]:
    """既存validatorをJSONモードで実行する。"""

    result = subprocess.run(
        [sys.executable, str(VALIDATOR), str(knowledge_root), "--json"],
        capture_output=True,
        text=True,
        check=False,
    )
    try:
        findings = json.loads(result.stdout)
    except json.JSONDecodeError:
        detail = result.stderr.strip() or result.stdout.strip() or "no output"
        return [], f"validator returned invalid JSON: {detail}"
    if not isinstance(findings, list) or result.returncode not in {0, 1}:
        return [], f"validator failed with exit code {result.returncode}"
    return findings, None


def find_required_knowledge(
    knowledge_root: Path, workspace: Path
) -> list[dict[str, str]]:
    """Quick初期構築に通常Conceptとproject artifact根拠を要求する。"""

    findings: list[dict[str, str]] = []
    docs = knowledge_root / "docs"
    concepts: list[tuple[Path, dict[str, Any]]] = []

    # 管理ページを除いた形式上有効な通常Conceptを収集
    if docs.is_dir():
        for path in sorted(docs.rglob("*.md")):
            metadata = read_frontmatter(path)
            if path.name in {"index.md", "log.md"} or not isinstance(metadata, dict):
                continue
            if all(metadata.get(key) for key in ("type", "pk_category", "pk_derivation")):
                concepts.append((path, metadata))
    if not concepts:
        add_finding(findings, "high", "missing-concept", docs)

    # 通常Conceptからworkspace内の実在project artifactへ到達できることを確認
    workspace_root = workspace.resolve()
    has_project_artifact = False
    for path, metadata in concepts:
        sources = metadata.get("sources")
        if not isinstance(sources, list):
            continue
        for source in sources:
            if not isinstance(source, dict) or source.get("pk_source_type") != "project-artifact":
                continue
            resource = source.get("resource")
            if not isinstance(resource, str) or is_uri(resource):
                continue
            target = (path.parent / resource.split("#", 1)[0]).resolve()
            if target.is_file() and is_within(target, workspace_root):
                has_project_artifact = True
                break
        if has_project_artifact:
            break
    if not has_project_artifact:
        add_finding(findings, "high", "missing-project-artifact-source", docs)
    return findings


def find_outside_sources(knowledge_root: Path, workspace: Path) -> list[dict[str, str]]:
    """local sourceが隔離workspace内に収まることを確認する。"""

    findings: list[dict[str, str]] = []
    docs = knowledge_root / "docs"
    if not docs.is_dir():
        return findings
    for path in sorted(docs.rglob("*.md")):
        metadata = read_frontmatter(path)
        if not isinstance(metadata, dict):
            continue
        sources = metadata.get("sources")
        if not isinstance(sources, list):
            continue
        for source in sources:
            if not isinstance(source, dict):
                continue
            resource = source.get("resource")
            if not isinstance(resource, str) or is_uri(resource):
                continue
            target = (path.parent / resource.split("#", 1)[0]).resolve()
            if not is_within(target, workspace.resolve()):
                add_finding(findings, "high", "source-outside-workspace", path)
    return findings


def measure_quick_sessions(
    metadata: dict[str, Any], deterministic_status: str
) -> dict[str, dict[str, Any]]:
    """QuickのActor、Judge、Orchestratorを役割別に計測する。"""

    try:
        rates = load_credit_rates(CREDIT_RATES_CONFIG)
    except (TypeError, ValueError) as error:
        unavailable = unavailable_measurement(str(error))
        return {"actor": unavailable, "judge": unavailable, "orchestrator": unavailable}
    sessions = metadata.get("sessions")
    actor_reference = sessions.get("actor") if isinstance(sessions, dict) else None
    judge_reference = sessions.get("judge") if isinstance(sessions, dict) else None
    actor = measure_session(actor_reference, rates)
    judge = (
        measure_session(judge_reference, rates)
        if deterministic_status == "PASS"
        else unavailable_measurement("judge-not-run")
    )
    orchestrator = unavailable_measurement(
        "independent-orchestrator-usage-unavailable",
        metadata.get("orchestrator_session_id")
        if isinstance(metadata.get("orchestrator_session_id"), str)
        else None,
    )
    return {"actor": actor, "judge": judge, "orchestrator": orchestrator}


def combined_credits(measurements: list[dict[str, Any]]) -> float | int | str:
    """すべて実測できた役割だけを合計し、欠落時は推測しない。"""

    if not measurements or any(
        item.get("measurement", {}).get("status") != "available" for item in measurements
    ):
        return "unavailable"
    return round(sum(float(item["credits"]["total"]) for item in measurements), 12)


def format_credit(value: Any) -> str:
    """credit値またはunavailableを表示用に整形する。"""

    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return "unavailable"
    return f"{value:.6f}".rstrip("0").rstrip(".")


def render_quick_credits(
    measurements: dict[str, dict[str, Any]], deterministic_status: str
) -> list[str]:
    """Quickの役割別creditsと計測状態を表示する。"""

    actor_value = measurements["actor"]["credits"]["total"]
    judge_expected = deterministic_status == "PASS"
    judge_value = measurements["judge"]["credits"]["total"]
    expected = [measurements["actor"]]
    if judge_expected:
        expected.append(measurements["judge"])
    status = "AVAILABLE" if combined_credits(expected) != "unavailable" else "UNAVAILABLE"
    total = combined_credits(expected)
    return [
        f"Usage measurement: {status}",
        "Credits:",
        f"  Actor: {format_credit(actor_value)}",
        f"  Judge: {format_credit(judge_value) if judge_expected else 'not run'}",
        "  Orchestrator: unavailable",
        f"  Total (measured): {format_credit(total)}",
    ]


def report(workspace: Path) -> tuple[str, int]:
    """deterministic結果とJudge結果を人間向けに集約する。"""

    run_root, metadata = load_run(workspace)
    deterministic = read_json(run_root / DETERMINISTIC_RESULT)
    deterministic_status = deterministic.get("status", "ERROR")
    judge: dict[str, Any] | None = None
    judge_error: str | None = None
    if deterministic_status == "PASS":
        try:
            judge = read_json(run_root / JUDGE_RESULT)
            validate_judge(judge)
        except ScenarioError as error:
            judge_error = str(error)

    overall_pass = deterministic_status == "PASS" and judge_error is None
    if judge is not None:
        overall_pass = overall_pass and judge["result"] == "PASS"

    # 品質結果と独立してsession JSONL由来のusageを計測
    measurements = measure_quick_sessions(metadata, deterministic_status)
    metadata["measurement_results"] = measurements
    metadata["measured_total_credits"] = combined_credits(
        [measurements["actor"]]
        + ([measurements["judge"]] if deterministic_status == "PASS" else [])
    )
    write_json(run_root / MARKER, metadata)

    lines = [
        "Project Knowledge Quick Scenario Test",
        "",
        f"Result: {'PASS' if overall_pass else 'FAIL'}",
        "",
        f"Deterministic validation: {deterministic_status}",
        "",
        "AI Judge:",
    ]
    if deterministic_status != "PASS":
        lines.append("  SKIPPED")
    elif judge_error is not None:
        lines.append("  ERROR")
    else:
        assert judge is not None
        for dimension in DIMENSIONS:
            lines.append(f"  {dimension}: {judge['dimensions'][dimension]['result']}")

    lines.extend(["", *render_quick_credits(measurements, deterministic_status)])
    issues = collect_issues(deterministic, judge, judge_error)
    lines.extend(["", "Issues:"])
    if not issues:
        lines.append("  none")
    else:
        for severity in ("critical", "major", "minor"):
            selected = [issue for issue in issues if issue["severity"] == severity]
            if not selected:
                continue
            lines.append(f"  {severity.capitalize()}:")
            for issue in selected:
                lines.append(f"  - {issue['message']}")
    if deterministic_status == "ERROR" or judge_error is not None:
        exit_code = 2
    else:
        exit_code = 0 if overall_pass else 1
    return "\n".join(lines), exit_code


def validate_large(descriptor_path: Path) -> dict[str, Any]:
    """現在のLarge stepを共通validatorで検査し規模推移を保存する。"""

    descriptor = load_large_descriptor(descriptor_path)
    workspace = Path(descriptor["workspace"])
    step = find_large_step(descriptor, descriptor["current_step"])
    result = validate(workspace)
    step["validation"] = result
    step["knowledge"] = knowledge_statistics(workspace / "project-knowledge")
    step["repository"] = repository_statistics(workspace)
    step["issues"] = collect_issues(result, None, None)
    write_json(descriptor_path, descriptor)
    return step


def large_report(descriptor_path: Path) -> tuple[str, int]:
    """Large lifecycleのstep結果、品質、token usageを集約する。"""

    descriptor = load_large_descriptor(descriptor_path)
    rates_error: str | None = None
    try:
        rates = load_credit_rates(CREDIT_RATES_CONFIG)
    except (TypeError, ValueError) as error:
        rates = {}
        rates_error = str(error)
    validation_error = False
    judge_error = False
    for step in descriptor["steps"]:
        validation = step.get("validation")
        validation_status = validation.get("status") if isinstance(validation, dict) else "ERROR"
        validation_error = validation_error or validation_status != "PASS"
        actor = (
            measure_session(step.get("actor_session"), rates)
            if rates_error is None
            else unavailable_measurement(rates_error)
        )
        step["actor_measurement"] = actor
        step["actor_usage"] = actor["usage"]
        judge: dict[str, Any] | None = None
        step_judge_error: str | None = None
        if step["judge_checkpoint"] and validation_status == "PASS":
            try:
                judge = read_json(large_judge_path(descriptor_path, step["step"]))
                validate_judge(judge)
            except ScenarioError as error:
                step_judge_error = str(error)
            judge_measurement = (
                measure_session(step.get("judge_session"), rates)
                if rates_error is None
                else unavailable_measurement(rates_error)
            )
            step["judge_measurement"] = judge_measurement
            step["judge_usage"] = judge_measurement["usage"]
            judge_error = judge_error or step_judge_error is not None or (
                judge is not None and judge["result"] != "PASS"
            )
        else:
            step["judge_measurement"] = unavailable_measurement("judge-not-run")
            step["judge_usage"] = unavailable_usage()
        step["quality_score"] = quality_score(judge)
        step["issues"] = collect_issues(
            validation if isinstance(validation, dict) else {
                "status": "ERROR", "findings": [], "error": "step-not-validated"
            },
            judge,
            step_judge_error,
        )

    completed_updates = sum(step["operation"] == "update" for step in descriptor["steps"])
    lifecycle_complete = completed_updates == len(descriptor["change_sets"])
    overall_pass = lifecycle_complete and not validation_error and not judge_error
    descriptor["summary"] = build_large_summary(descriptor, lifecycle_complete)
    descriptor["summary"]["result"] = "PASS" if overall_pass else "FAIL"
    write_json(descriptor_path, descriptor)
    output = render_large_report(descriptor)
    if not lifecycle_complete or any(
        not isinstance(step.get("validation"), dict) for step in descriptor["steps"]
    ):
        return output, 2
    return output, 0 if overall_pass else 1


def build_large_summary(
    descriptor: dict[str, Any], lifecycle_complete: bool
) -> dict[str, Any]:
    """Largeのmachine-readable最終集計を構築する。"""

    steps = descriptor["steps"]
    actor_values = [usage_integer(step["actor_usage"], "total_tokens") for step in steps]
    judge_values = [
        usage_integer(step["judge_usage"], "total_tokens")
        for step in steps if step["judge_checkpoint"]
    ]
    update_values = [
        usage_integer(step["actor_usage"], "total_tokens")
        for step in steps if step["operation"] == "update"
    ]
    checkpoint_scores = [
        int(step["quality_score"])
        for step in steps if step["quality_score"] != "unavailable"
    ]
    available_actor = all(value is not None for value in actor_values)
    available_updates = all(value is not None for value in update_values)
    available_judges = all(value is not None for value in judge_values)
    largest = max(
        (step for step in steps if step["operation"] == "update"),
        key=lambda step: step["changed_bytes"],
        default=None,
    )
    largest_tokens = (
        usage_integer(largest["actor_usage"], "total_tokens") if largest else None
    )
    return {
        "lifecycle_complete": lifecycle_complete,
        "initial_builds": 1,
        "updates": sum(step["operation"] == "update" for step in steps),
        "validation": {
            "initial": validation_status(steps[0]),
            "final": validation_status(steps[-1]),
        },
        "quality": {
            "initial": steps[0]["quality_score"],
            "final": steps[-1]["quality_score"],
            "lowest_checkpoint": min(checkpoint_scores) if checkpoint_scores else "unavailable",
        },
        "tokens": {
            "initial_build": actor_values[0] if actor_values[0] is not None else "unavailable",
            "updates_total": sum(update_values) if available_updates else "unavailable",
            "cumulative_actor": sum(actor_values) if available_actor else "unavailable",
            "average_update": round(sum(update_values) / len(update_values)) if available_updates and update_values else "unavailable",
            "median_update": round(median(update_values)) if available_updates and update_values else "unavailable",
            "maximum_update": max(update_values) if available_updates and update_values else "unavailable",
            "judge_total": sum(judge_values) if available_judges else "unavailable",
            "orchestrator": "unavailable",
        },
        "largest_update": {
            "step": largest["step"] if largest else "unavailable",
            "changed_files": largest["changed_files"] if largest else "unavailable",
            "changed_bytes": largest["changed_bytes"] if largest else "unavailable",
            "actor_tokens": largest_tokens if largest_tokens is not None else "unavailable",
        },
        "issues": [
            {"step": step["step"], **issue}
            for step in steps for issue in step["issues"]
        ],
    }


def render_large_report(descriptor: dict[str, Any]) -> str:
    """Large summaryを人間向けに整形する。"""

    steps = descriptor["steps"]
    initial = steps[0]
    final = steps[-1]
    summary = descriptor["summary"]
    tokens = summary["tokens"]
    lines = [
        "Project Knowledge Large Scenario",
        "",
        f"Result: {summary['result']}",
        "",
        "Fixture:",
        f"  Version: {descriptor['fixture_version']}",
        f"  Source files: {descriptor['fixture']['files']}",
        f"  Initial source characters: {descriptor['fixture']['characters']}",
        "",
        "Lifecycle:",
        "  Initial build: 1",
        f"  Updates: {summary['updates']} / {len(descriptor['change_sets'])}",
        "",
        "Validation:",
        f"  Initial: {summary['validation']['initial']}",
        f"  Final: {summary['validation']['final']}",
        "",
        "Quality:",
        f"  Initial score: {summary['quality']['initial']}",
        f"  Final score: {summary['quality']['final']}",
        f"  Lowest checkpoint score: {summary['quality']['lowest_checkpoint']}",
        "",
        "Knowledge:",
        "                         Initial      Final",
    ]
    for label, key in (
        ("Concepts", "concepts"), ("Markdown files", "knowledge_markdown_files"),
        ("Knowledge chars", "knowledge_characters"), ("Sources", "sources"),
        ("Draft concepts", "draft_concepts"), ("Inferred concepts", "inferred_concepts"),
    ):
        initial_value = initial["knowledge"].get(key, 0) if isinstance(initial["knowledge"], dict) else 0
        final_value = final["knowledge"].get(key, 0) if isinstance(final["knowledge"], dict) else 0
        lines.append(f"  {label:<20} {initial_value:>8} {final_value:>10}")
    lines.extend([
        "",
        "Actor tokens:",
        f"  Init: {tokens['initial_build']}",
        f"  Updates total: {tokens['updates_total']}",
        f"  Cumulative: {tokens['cumulative_actor']}",
        f"  Average update: {tokens['average_update']}",
        f"  Median update: {tokens['median_update']}",
        f"  Maximum update: {tokens['maximum_update']}",
        f"  Judge total: {tokens['judge_total']}",
        "  Orchestrator: unavailable",
        "",
        "Largest source change:",
        f"  Step: {summary['largest_update']['step']}",
        f"  Changed files: {summary['largest_update']['changed_files']}",
        f"  Changed bytes: {summary['largest_update']['changed_bytes']}",
        f"  Actor tokens: {summary['largest_update']['actor_tokens']}",
        "",
        "Steps:",
        "  step | operation | changed files | changed bytes | validation | quality | actor tokens | judge tokens",
    ])
    for step in steps:
        lines.append(
            f"  {step['step']} | {step['operation']} | {step['changed_files']} | "
            f"{step['changed_bytes']} | {validation_status(step)} | {step['quality_score']} | "
            f"{usage_display(step['actor_usage'])} | {usage_display(step['judge_usage'])}"
        )
    lines.extend(["", "Observed issues:"])
    if summary["issues"]:
        lines.extend(
            f"  - [{issue['step']}] {issue['message']}" for issue in summary["issues"]
        )
    else:
        lines.append("  none")
    return "\n".join(lines)


def usage_integer(usage: Any, key: str) -> int | None:
    """推定せず実測済みtoken整数だけを返す。"""

    value = usage.get(key) if isinstance(usage, dict) else None
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def usage_display(usage: Any) -> str:
    """step表へtoken値またはunavailableを表示する。"""

    value = usage_integer(usage, "total_tokens")
    return str(value) if value is not None else "unavailable"


def validation_status(step: dict[str, Any]) -> str:
    """stepのdeterministic validation状態を返す。"""

    validation = step.get("validation")
    return str(validation.get("status", "ERROR")) if isinstance(validation, dict) else "NOT RUN"


def large_judge_path(descriptor_path: Path, step_id: str) -> Path:
    """checkpoint固有のJudge JSON出力先を返す。"""

    return descriptor_path.resolve().parent / "judges" / f"{step_id}.json"


def validate_judge(judge: dict[str, Any]) -> None:
    """Judge JSONがレポート契約へ適合することを確認する。"""

    if judge.get("result") not in {"PASS", "FAIL"}:
        raise ScenarioError("judge result must be PASS or FAIL")
    dimensions = judge.get("dimensions")
    if not isinstance(dimensions, dict):
        raise ScenarioError("judge dimensions must be a mapping")
    for name in DIMENSIONS:
        item = dimensions.get(name)
        if not isinstance(item, dict) or item.get("result") not in {"PASS", "FAIL"}:
            raise ScenarioError(f"judge dimension is invalid: {name}")
        if not isinstance(item.get("reason"), str) or not string_list(item.get("evidence")):
            raise ScenarioError(f"judge dimension details are invalid: {name}")
    issues = judge.get("issues")
    if not isinstance(issues, list):
        raise ScenarioError("judge issues must be a list")
    for issue in issues:
        if not isinstance(issue, dict):
            raise ScenarioError("judge issue must be a mapping")
        if issue.get("severity") not in {"critical", "major", "minor"}:
            raise ScenarioError("judge issue severity is invalid")
        if issue.get("dimension") not in DIMENSIONS:
            raise ScenarioError("judge issue dimension is invalid")
        if not isinstance(issue.get("message"), str) or not string_list(issue.get("evidence")):
            raise ScenarioError("judge issue details are invalid")
    expected = all(dimensions[name]["result"] == "PASS" for name in DIMENSIONS) and not any(
        issue["severity"] in {"critical", "major"} for issue in issues
    )
    if (judge["result"] == "PASS") != expected:
        raise ScenarioError("judge result is inconsistent with dimensions or issues")


def collect_issues(
    deterministic: dict[str, Any],
    judge: dict[str, Any] | None,
    judge_error: str | None,
) -> list[dict[str, str]]:
    """レポートへ表示する問題を共通severityへ変換する。"""

    issues: list[dict[str, str]] = []
    for finding in deterministic.get("findings", []):
        severity = {"high": "critical", "medium": "major", "low": "minor"}.get(
            finding.get("severity"), "major"
        )
        message = f"deterministic {finding.get('code', 'unknown')}: {finding.get('path', '')}"
        issues.append({"severity": severity, "message": message})
    error = deterministic.get("error")
    if isinstance(error, str) and error:
        issues.append({"severity": "critical", "message": error})
    if judge_error is not None:
        issues.append({"severity": "critical", "message": judge_error})
    if judge is not None:
        for issue in judge["issues"]:
            issues.append({"severity": issue["severity"], "message": issue["message"]})
    return issues


def knowledge_statistics(knowledge_root: Path) -> dict[str, int]:
    """Judgeと独立したKnowledge Baseの参考統計を収集する。"""

    docs = knowledge_root / "docs"
    files = sorted(docs.rglob("*.md")) if docs.is_dir() else []
    concepts = drafts = inferred = sources = characters = 0
    for path in files:
        text = path.read_text(encoding="utf-8")
        characters += len(text)
        metadata = read_frontmatter(path)
        if not isinstance(metadata, dict):
            continue
        concepts += int(
            path.name not in {"index.md", "log.md"}
            and all(metadata.get(key) for key in ("type", "pk_category", "pk_derivation"))
        )
        drafts += int(metadata.get("pk_derivation") == "draft")
        inferred += int(metadata.get("pk_derivation") == "inferred")
        source_list = metadata.get("sources")
        sources += len(source_list) if isinstance(source_list, list) else 0
    return {
        "concepts": concepts,
        "knowledge_markdown_files": len(files),
        "knowledge_characters": characters,
        "sources": sources,
        "draft_concepts": drafts,
        "inferred_concepts": inferred,
    }


def quality_score(judge: dict[str, Any] | None) -> str:
    """Quick JudgeのPASS数だけを100点換算した比較用Scoreを返す。"""

    if judge is None:
        return "unavailable"
    passed = sum(judge["dimensions"][name]["result"] == "PASS" for name in DIMENSIONS)
    return str(round(passed * 100 / len(DIMENSIONS)))


def render_benchmark_report(payload: dict[str, Any]) -> str:
    """単一実行Benchmarkを人間向けの比較表として整形する。"""

    rows = payload["results"]
    names = [row["display_name"] for row in rows]
    lines = [
        "Project Knowledge Model Benchmark",
        f"Scenario: {payload['scenario']}",
        "Runs per model: 1 (single-run benchmark)",
        f"Credit rates: {payload['credit_rate']['source']}",
        f"Rate checked: {payload['credit_rate']['checked_at']}",
        "",
        "                         " + "  ".join(names),
        "Deterministic             " + "  ".join(row["deterministic"] for row in rows),
    ]
    for dimension in DIMENSIONS:
        values = [
            row["judge"]["dimensions"][dimension]["result"] if row["judge"] else "SKIPPED"
            for row in rows
        ]
        lines.append(f"{dimension:<25}" + "  ".join(values))
    lines.append("Quality score              " + "  ".join(quality_score(row["judge"]) for row in rows))
    lines.append(
        "Actor credits            "
        + "  ".join(format_credit(row["actor_measurement"]["credits"]["total"]) for row in rows)
    )
    for key, label in (
        ("input_tokens", "Actor input tokens"),
        ("cached_input_tokens", "Actor cached tokens"),
        ("output_tokens", "Actor output tokens"),
        ("reasoning_output_tokens", "Actor reasoning tokens"),
        ("total_tokens", "Actor total tokens"),
    ):
        lines.append(f"{label:<25}" + "  ".join(str(row["actor_usage"].get(key, "unavailable")) for row in rows))
    for key, label in (("concepts", "Concepts"), ("knowledge_markdown_files", "Knowledge Markdown files"), ("knowledge_characters", "Knowledge chars"), ("sources", "Sources")):
        lines.append(f"{label:<25}" + "  ".join(str(row["statistics"][key]) for row in rows))
    scores = [(int(score), row["display_name"]) for row in rows if (score := quality_score(row["judge"])).isdigit()]
    best = "unavailable" if not scores else ", ".join(name for score, name in scores if score == max(value for value, _ in scores))
    credit_values = [
        (float(value), row["display_name"])
        for row in rows
        if isinstance(
            (value := row["actor_measurement"]["credits"]["total"]), (int, float)
        )
        and not isinstance(value, bool)
    ]
    lowest = (
        "unavailable"
        if len(credit_values) != len(rows)
        else ", ".join(
            name for value, name in credit_values
            if value == min(item[0] for item in credit_values)
        )
    )
    lines.extend([
        "",
        f"Best quality: {best}",
        f"Lowest credits: {lowest}",
        f"Judge credits: {format_credit(payload['judge_credits'])}",
        f"Benchmark total credits: {format_credit(payload['benchmark_total_credits'])}",
        "",
        "Candidate findings:",
    ])
    for row in rows:
        lines.append(row["display_name"])
        issues = collect_issues({"status": row["deterministic"], "findings": [], "error": None}, row["judge"], None)
        if not issues:
            lines.append("- no reported issues")
        else:
            lines.extend(f"- {issue['message']}" for issue in issues)
    return "\n".join(lines)


def benchmark_report(descriptor_path: Path) -> tuple[str, int]:
    """各Quick実行の結果をモデル名へ復元して比較表示する。"""

    descriptor = read_json(descriptor_path)
    candidates = descriptor.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        raise ScenarioError("benchmark candidates are invalid")
    try:
        rates = load_credit_rates(CREDIT_RATES_CONFIG)
        rate_metadata = {"source": rates["source"], "checked_at": rates["checked_at"]}
    except (TypeError, ValueError) as error:
        rates = None
        rate_metadata = {"source": "unavailable", "checked_at": "unavailable"}
        rate_error = str(error)
    rows: list[dict[str, Any]] = []
    for candidate in candidates:
        if not isinstance(candidate, dict) or not isinstance(candidate.get("workspace"), str):
            raise ScenarioError("benchmark candidate is invalid")
        workspace = Path(candidate["workspace"])
        _, exit_code = report(workspace)
        run_root, _ = load_run(workspace)
        deterministic = read_json(run_root / DETERMINISTIC_RESULT)
        judge = None
        if deterministic.get("status") == "PASS":
            try:
                judge = read_json(run_root / JUDGE_RESULT)
                validate_judge(judge)
            except ScenarioError:
                pass
        actor_measurement = (
            measure_session(candidate.get("actor_session"), rates)
            if rates is not None
            else unavailable_measurement(rate_error)
        )
        judge_measurement = (
            (
                measure_session(candidate.get("judge_session"), rates)
                if rates is not None
                else unavailable_measurement(rate_error)
            )
            if deterministic.get("status") == "PASS"
            else unavailable_measurement("judge-not-run")
        )
        rows.append({
            **candidate, "exit_code": exit_code,
            "deterministic": deterministic.get("status", "ERROR"), "judge": judge,
            "statistics": knowledge_statistics(workspace / "project-knowledge"),
            "actor_usage": actor_measurement["usage"],
            "actor_measurement": actor_measurement,
            "judge_measurement": judge_measurement,
        })
    actor_measurements = [row["actor_measurement"] for row in rows]
    judge_measurements = [
        row["judge_measurement"] for row in rows if row["deterministic"] == "PASS"
    ]
    payload = {
        **descriptor,
        "credit_rate": rate_metadata,
        "results": rows,
        "actor_credits": combined_credits(actor_measurements),
        "judge_credits": combined_credits(judge_measurements),
        "benchmark_total_credits": combined_credits(
            actor_measurements + judge_measurements
        ),
    }
    write_json(descriptor_path, payload)
    return render_benchmark_report(payload), 0 if all(row["exit_code"] == 0 for row in rows) else 1


def cleanup(workspace: Path) -> None:
    """markerで識別できる一時runだけを削除する。"""

    run_root, _ = load_run(workspace)
    temporary_root = Path(tempfile.gettempdir()).resolve()
    if not is_within(run_root, temporary_root) or run_root == temporary_root:
        raise ScenarioError(f"refusing cleanup outside temporary root: {run_root}")
    make_tree_writable(run_root)
    shutil.rmtree(run_root)


def cleanup_large(descriptor_path: Path) -> None:
    """Large descriptorで識別した一時run全体を削除する。"""

    descriptor = load_large_descriptor(descriptor_path)
    cleanup(Path(descriptor["workspace"]))


def load_large_descriptor(descriptor_path: Path) -> dict[str, Any]:
    """Large descriptorと一時workspaceの対応を検証する。"""

    descriptor_path = descriptor_path.resolve()
    descriptor = read_json(descriptor_path)
    if descriptor.get("benchmark") != "project-knowledge-large":
        raise ScenarioError(f"not a large scenario descriptor: {descriptor_path}")
    workspace_value = descriptor.get("workspace")
    if not isinstance(workspace_value, str):
        raise ScenarioError("large workspace is invalid")
    workspace = Path(workspace_value).resolve()
    if descriptor_path.name != LARGE_RESULT or descriptor_path.parent != workspace.parent:
        raise ScenarioError("large descriptor and workspace do not share a run root")
    load_run(workspace)
    steps = descriptor.get("steps")
    if not isinstance(steps, list) or not steps:
        raise ScenarioError("large steps are invalid")
    return descriptor


def find_large_step(descriptor: dict[str, Any], step_id: Any) -> dict[str, Any]:
    """descriptorから一意なstepを取得する。"""

    if not isinstance(step_id, str):
        raise ScenarioError("large step id is required")
    matches = [
        step for step in descriptor.get("steps", [])
        if isinstance(step, dict) and step.get("step") == step_id
    ]
    if len(matches) != 1:
        raise ScenarioError(f"large step not found: {step_id}")
    return matches[0]


def load_run(workspace: Path) -> tuple[Path, dict[str, Any]]:
    """workspaceとmarkerの対応を検証してrun情報を返す。"""

    resolved = workspace.resolve()
    if resolved.name != WORKSPACE_NAME:
        raise ScenarioError(f"invalid workspace name: {resolved}")
    run_root = resolved.parent
    metadata = read_json(run_root / MARKER)
    if metadata.get("workspace") != str(resolved):
        raise ScenarioError("workspace does not match scenario marker")
    return run_root, metadata


def tree_hash(root: Path, excluded_names: set[str] | None = None) -> str:
    """ディレクトリの相対パスと内容から安定したhashを計算する。"""

    excluded = excluded_names or set()
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if any(part in excluded for part in relative.parts) or not path.is_file():
            continue
        digest.update(relative.as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def make_tree_writable(root: Path) -> None:
    """Windowsのread-onlyなGit objectを含めて削除可能にする。"""

    mode = stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR
    for path in sorted(root.rglob("*"), reverse=True):
        try:
            path.chmod(mode)
        except OSError:
            continue
    root.chmod(mode)


def read_frontmatter(path: Path) -> dict[str, Any] | None:
    """Markdown先頭のYAML frontmatterを読み取る。"""

    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return None
    if not text.startswith("---\n"):
        return None
    parts = text.split("---", 2)
    if len(parts) != 3:
        return None
    try:
        metadata = yaml.safe_load(parts[1])
    except yaml.YAMLError:
        return None
    return metadata if isinstance(metadata, dict) else None


def read_json(path: Path) -> dict[str, Any]:
    """JSON objectを読み取り、欠落や不正を実行基盤エラーにする。"""

    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ScenarioError(f"cannot read {path.name}: {error}") from error
    if not isinstance(value, dict):
        raise ScenarioError(f"{path.name} must contain a JSON object")
    return value


def write_json(path: Path, value: dict[str, Any]) -> None:
    """JSONをUTF-8で保存する。"""

    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def add_finding(
    findings: list[dict[str, str]], severity: str, code: str, path: Path
) -> None:
    """シナリオ固有findingを追加する。"""

    findings.append({"severity": severity, "code": code, "path": str(path)})


def finding_sort_key(item: dict[str, str]) -> tuple[int, str, str]:
    """findingをseverity、path、codeの順に並べる。"""

    order = {"high": 0, "medium": 1, "low": 2}
    return order.get(item.get("severity", "medium"), 1), item.get("path", ""), item.get("code", "")


def is_uri(value: str) -> bool:
    """source resourceがURIか判定する。"""

    if len(value) >= 3 and value[1] == ":" and value[2] in {"/", "\\"}:
        return False
    scheme = urlparse(value).scheme
    return bool(scheme)


def is_within(path: Path, root: Path) -> bool:
    """pathがroot自身または配下か判定する。"""

    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def string_list(value: Any) -> bool:
    """値が文字列だけのlistか判定する。"""

    return isinstance(value, list) and all(isinstance(item, str) for item in value)


def build_parser() -> argparse.ArgumentParser:
    """runnerのCLI parserを構築する。"""

    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    prepare_parser = commands.add_parser("prepare")
    prepare_parser.add_argument("scenario")
    for name in ("validate", "report", "cleanup"):
        command_parser = commands.add_parser(name)
        command_parser.add_argument("workspace", type=Path)
    session_parser = commands.add_parser("session")
    session_commands = session_parser.add_subparsers(dest="session_command", required=True)
    session_record = session_commands.add_parser("record")
    session_record.add_argument("target", type=Path)
    session_record.add_argument("role", choices=("actor", "judge"))
    session_record.add_argument("session_id")
    session_record.add_argument("--agent-path", required=True)
    session_record.add_argument("--candidate")
    session_record.add_argument("--parent-session-id")
    session_record.add_argument("--step")
    benchmark_parser = commands.add_parser("benchmark")
    benchmark_commands = benchmark_parser.add_subparsers(dest="benchmark_command", required=True)
    benchmark_prepare = benchmark_commands.add_parser("prepare")
    benchmark_prepare.add_argument("scenario")
    benchmark_report_parser = benchmark_commands.add_parser("report")
    benchmark_report_parser.add_argument("descriptor", type=Path)
    utility_parser = commands.add_parser("utility")
    utility_commands = utility_parser.add_subparsers(dest="utility_command", required=True)
    utility_prepare = utility_commands.add_parser("prepare")
    utility_prepare.add_argument("scenario")
    for name in ("install-knowledge", "blind", "report", "cleanup"):
        command_parser = utility_commands.add_parser(name)
        command_parser.add_argument("descriptor", type=Path)
    utility_evaluate = utility_commands.add_parser("evaluate")
    utility_evaluate.add_argument("descriptor", type=Path)
    utility_evaluate.add_argument("condition", choices=UTILITY_CONDITIONS)
    large_parser = commands.add_parser("large")
    large_commands = large_parser.add_subparsers(dest="large_command", required=True)
    large_prepare = large_commands.add_parser("prepare")
    large_prepare.add_argument("scenario")
    for name in ("advance", "validate", "report", "cleanup"):
        command_parser = large_commands.add_parser(name)
        command_parser.add_argument("descriptor", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    """指定されたシナリオ補助処理を実行する。"""

    # WindowsでもJudgeの日本語issueをUTF-8で表示
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")
    args = build_parser().parse_args(argv)
    try:
        if args.command == "prepare":
            print(prepare(args.scenario))
            return 0
        if args.command == "validate":
            result = validate(args.workspace)
            print(f"Deterministic validation: {result['status']}")
            return 0 if result["status"] == "PASS" else (2 if result["status"] == "ERROR" else 1)
        if args.command == "report":
            output, exit_code = report(args.workspace)
            print(output)
            return exit_code
        if args.command == "session":
            reference = record_session(
                args.target,
                args.role,
                args.session_id,
                args.agent_path,
                args.candidate,
                args.parent_session_id,
                args.step,
            )
            print(json.dumps(reference, ensure_ascii=False, indent=2))
            return 0
        if args.command == "benchmark":
            if args.benchmark_command == "prepare":
                print(prepare_benchmark(args.scenario))
                return 0
            output, exit_code = benchmark_report(args.descriptor)
            print(output)
            return exit_code
        if args.command == "utility":
            if args.utility_command == "prepare":
                print(prepare_utility(args.scenario))
                return 0
            if args.utility_command == "install-knowledge":
                install_utility_knowledge(args.descriptor)
                print("Knowledge installed into With-KB workspace")
                return 0
            if args.utility_command == "evaluate":
                result = evaluate_utility_condition(args.descriptor, args.condition)
                print(json.dumps(result, ensure_ascii=False, indent=2))
                return 0 if result["task_success"] else 1
            if args.utility_command == "blind":
                print(json.dumps(prepare_blind_candidates(args.descriptor), ensure_ascii=False, indent=2))
                return 0
            if args.utility_command == "report":
                output, exit_code = utility_report(args.descriptor)
                print(output)
                return exit_code
            cleanup_utility(args.descriptor)
            print("Utility benchmark workspaces removed")
            return 0
        if args.command == "large":
            if args.large_command == "prepare":
                print(prepare_large(args.scenario))
                return 0
            if args.large_command == "advance":
                step = advance_large(args.descriptor)
                print(json.dumps(step, ensure_ascii=False, indent=2))
                return 0
            if args.large_command == "validate":
                step = validate_large(args.descriptor)
                print(json.dumps(step, ensure_ascii=False, indent=2))
                status = step["validation"]["status"]
                return 0 if status == "PASS" else (2 if status == "ERROR" else 1)
            if args.large_command == "report":
                output, exit_code = large_report(args.descriptor)
                print(output)
                return exit_code
            cleanup_large(args.descriptor)
            print("Large scenario workspace removed")
            return 0
        cleanup(args.workspace)
        print("Temporary workspace removed")
        return 0
    except ScenarioError as error:
        print(f"Scenario infrastructure error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
