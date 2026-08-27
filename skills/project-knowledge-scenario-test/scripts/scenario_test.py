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
from typing import Any
from urllib.parse import urlparse

import yaml

SKILL_ROOT = Path(__file__).resolve().parents[1]
SCENARIOS_ROOT = SKILL_ROOT / "scenarios"
PROJECT_KNOWLEDGE_ROOT = SKILL_ROOT.parent / "project-knowledge"
VALIDATOR = PROJECT_KNOWLEDGE_ROOT / "scripts" / "validate_knowledge.py"
MARKER = ".project-knowledge-scenario-test.json"
WORKSPACE_NAME = "workspace"
DETERMINISTIC_RESULT = "deterministic.json"
JUDGE_RESULT = "judge.json"
BENCHMARK_RESULT = "benchmark.json"
BENCHMARK_CONFIG = SKILL_ROOT / "agents" / "benchmark.yml"
UTILITY_RESULT = "utility.json"
UTILITY_CONFIG = SKILL_ROOT / "agents" / "utility.yml"
UTILITY_MARKER = ".project-knowledge-utility-benchmark.json"
UTILITY_SCENARIO = "utility-basic"
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
        shutil.copytree(fixture, workspace)
        metadata = {
            "scenario": scenario,
            "fixture": str(fixture),
            "fixture_hash": tree_hash(fixture),
            "workspace_source_hash": tree_hash(workspace, MANAGED_SOURCE_NAMES),
            "workspace": str(workspace.resolve()),
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


def unavailable_usage() -> dict[str, str]:
    """実測APIがないusage項目を推定せず明示する。"""

    return {key: "unavailable" for key in (
        "input_tokens", "output_tokens", "total_tokens", "cached_input_tokens", "reasoning_tokens"
    )}


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
            })
        write_json(benchmark_root / BENCHMARK_RESULT, {
            "benchmark": "project-knowledge-quick", "single_run": True, "scenario": scenario,
            "judge": config["judge"], "candidates": candidates,
        })
    except Exception:
        if benchmark_root.is_dir():
            make_tree_writable(benchmark_root)
            shutil.rmtree(benchmark_root)
        raise
    return (benchmark_root / BENCHMARK_RESULT).resolve()


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


def report(workspace: Path) -> tuple[str, int]:
    """deterministic結果とJudge結果を人間向けに集約する。"""

    run_root, _ = load_run(workspace)
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
            metadata.get("pk_category") == "concept" or metadata.get("type") == "Concept"
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
    for key, label in (("input_tokens", "Actor input tokens"), ("output_tokens", "Actor output tokens"), ("total_tokens", "Actor total tokens")):
        lines.append(f"{label:<25}" + "  ".join(str(row["actor_usage"].get(key, "unavailable")) for row in rows))
    for key, label in (("concepts", "Concepts"), ("knowledge_markdown_files", "Knowledge Markdown files"), ("knowledge_characters", "Knowledge chars"), ("sources", "Sources")):
        lines.append(f"{label:<25}" + "  ".join(str(row["statistics"][key]) for row in rows))
    scores = [(int(score), row["display_name"]) for row in rows if (score := quality_score(row["judge"])).isdigit()]
    best = "unavailable" if not scores else ", ".join(name for score, name in scores if score == max(value for value, _ in scores))
    lines.extend(["", f"Best quality: {best}", "Lowest actor token usage: unavailable (measured actor usage is unavailable)", "", "Candidate findings:"])
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
        rows.append({
            **candidate, "exit_code": exit_code,
            "deterministic": deterministic.get("status", "ERROR"), "judge": judge,
            "statistics": knowledge_statistics(workspace / "project-knowledge"),
        })
    payload = {**descriptor, "results": rows}
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
        cleanup(args.workspace)
        print("Temporary workspace removed")
        return 0
    except ScenarioError as error:
        print(f"Scenario infrastructure error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
