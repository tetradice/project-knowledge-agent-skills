"""Project Knowledge有無の実務Task Benchmarkを準備・評価・集計する。"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import secrets
import shutil
import stat
import subprocess
import sys
import time
import uuid
from pathlib import Path
from typing import Any

import yaml

sys.dont_write_bytecode = True

SCRIPT_ROOT = Path(__file__).resolve().parent
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from benchmark_session import record_session as measure_session

SKILL_ROOT = SCRIPT_ROOT.parent
MODEL_CONFIG = SKILL_ROOT / "agents" / "benchmark.yml"
CREDIT_CONFIG = SKILL_ROOT / "agents" / "credit-rates.yml"
CONDITIONS = ("no_knowledge", "with_knowledge")
DIMENSIONS = (
    "requirement_compliance",
    "project_convention_compliance",
    "architectural_consistency",
    "scope_discipline",
    "code_quality",
    "maintainability",
)


class BenchmarkError(RuntimeError):
    """安全に継続できないBenchmark状態を表す。"""


def run_git(repository: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    """対象repositoryでGit commandを実行する。"""

    result = subprocess.run(["git", *args], cwd=repository, capture_output=True, text=True, check=False)
    if check and result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        raise BenchmarkError(f"git {' '.join(args)} failed: {detail}")
    return result


def prepare(repository: Path, task_file: Path, baseline: str = "HEAD", output_root: Path | None = None, checks_file: Path | None = None) -> Path:
    """同一commitから履歴隔離したA/B worktreeを準備する。"""

    repository = repository.resolve()
    if not (repository / ".git").exists():
        raise BenchmarkError(f"not a Git repository: {repository}")
    if run_git(repository, "status", "--porcelain=v1", "--untracked-files=all").stdout:
        raise BenchmarkError("repository must be clean, including untracked files")
    commit = run_git(repository, "rev-parse", "--verify", f"{baseline}^{{commit}}").stdout.strip()
    if run_git(repository, "cat-file", "-e", f"{commit}:project-knowledge/manifest.yml", check=False).returncode != 0:
        raise BenchmarkError("baseline does not contain project-knowledge/manifest.yml")
    if not task_file.is_file():
        raise BenchmarkError(f"task file not found: {task_file}")

    # 実行条件をrun directoryへ固定
    root = (output_root.resolve() if output_root else repository.parent / f"{repository.name}-project-knowledge-benchmarks")
    run_root = root / f"run-{time.strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:8]}"
    run_root.mkdir(parents=True)
    (run_root / "task.md").write_text(task_file.read_text(encoding="utf-8"), encoding="utf-8")
    checks = load_checks(checks_file)
    models = yaml.safe_load(MODEL_CONFIG.read_text(encoding="utf-8"))
    labels = ["Candidate 1", "Candidate 2"]
    secrets.SystemRandom().shuffle(labels)
    candidate_labels = dict(zip(CONDITIONS, labels, strict=True))
    candidates: dict[str, dict[str, Any]] = {}

    try:
        for condition in CONDITIONS:
            opaque_id = f"candidate-{secrets.token_hex(6)}"
            workspace = run_root / "workspaces" / opaque_id
            run_git(repository, "worktree", "add", "--detach", str(workspace), commit)
            create_condition_baseline(workspace, condition)
            condition_baseline = isolate_history(workspace, run_root / "control", opaque_id)
            candidates[condition] = {
                "opaque_id": opaque_id,
                "blind_id": candidate_labels[condition],
                "workspace": str(workspace),
                "condition_baseline": condition_baseline,
                "evaluation": None,
                "session": None,
            }
        if content_hash(Path(candidates["no_knowledge"]["workspace"]), exclude_knowledge=True) != content_hash(Path(candidates["with_knowledge"]["workspace"]), exclude_knowledge=True):
            raise BenchmarkError("candidate sources differ outside project-knowledge")
        descriptor = {
            "schema_version": 1,
            "benchmark": "project-knowledge-utility",
            "single_run": True,
            "workspace_mode": "worktree",
            "state": "prepared",
            "repository": str(repository),
            "baseline": {"requested": baseline, "commit": commit},
            "task_file": str(run_root / "task.md"),
            "models": models,
            "checks": checks,
            "candidates": candidates,
            "judge_session": None,
            "orchestrator_session_id": os.environ.get("CODEX_THREAD_ID", "unavailable"),
        }
        write_json(run_root / "benchmark.json", descriptor)
        return (run_root / "benchmark.json").resolve()
    except Exception:
        recover_workspaces(run_root, candidates)
        raise


def load_checks(path: Path | None) -> list[dict[str, str]]:
    """明示された機械評価commandだけを読み込む。"""

    if path is None:
        return []
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    checks = data.get("checks") if isinstance(data, dict) else None
    if not isinstance(checks, list):
        raise BenchmarkError("checks file must contain a checks list")
    result: list[dict[str, str]] = []
    for item in checks:
        if not isinstance(item, dict) or not isinstance(item.get("name"), str) or not isinstance(item.get("command"), str):
            raise BenchmarkError("each check requires string name and command")
        result.append({"name": item["name"], "command": item["command"]})
    return result


def create_condition_baseline(workspace: Path, condition: str) -> None:
    """Project Knowledgeだけが異なるdetached baseline commitを作る。"""

    run_git(workspace, "config", "user.name", "Project Knowledge Benchmark")
    run_git(workspace, "config", "user.email", "benchmark@local.invalid")
    if condition == "no_knowledge":
        shutil.rmtree(workspace / "project-knowledge")
    run_git(workspace, "add", "-A")
    run_git(workspace, "commit", "--allow-empty", "-m", "Project Knowledge benchmark condition baseline")


def isolate_history(workspace: Path, control_root: Path, opaque_id: str) -> str:
    """元Git pointerを退避し、単一commitのlocal repositoryへ置き換える。"""

    git_link = workspace / ".git"
    if not git_link.is_file():
        raise BenchmarkError(f"worktree Git link is invalid: {workspace}")
    control_root.mkdir(parents=True, exist_ok=True)
    (control_root / f"{opaque_id}.gitlink").write_text(git_link.read_text(encoding="utf-8"), encoding="utf-8")
    git_link.unlink()
    run_git(workspace, "init")
    run_git(workspace, "config", "user.name", "Project Knowledge Benchmark")
    run_git(workspace, "config", "user.email", "benchmark@local.invalid")
    run_git(workspace, "add", "-A")
    run_git(workspace, "commit", "-m", "Benchmark task baseline")
    return run_git(workspace, "rev-parse", "HEAD").stdout.strip()


def content_hash(root: Path, exclude_knowledge: bool = False) -> str:
    """Git情報と必要に応じKnowledgeを除いたtree hashを返す。"""

    digest = hashlib.sha256()
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        relative = path.relative_to(root)
        if relative.parts[0] == ".git" or (exclude_knowledge and relative.parts[0] == "project-knowledge"):
            continue
        digest.update(relative.as_posix().encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def record_session(descriptor_path: Path, role: str, session_id: str, agent_path: str, parent_session_id: str | None = None) -> dict[str, Any]:
    """Task/Judge session参照とrollout由来measurementを保存する。"""

    descriptor = read_json(descriptor_path)
    if role not in {"task-a", "task-b", "judge"}:
        raise BenchmarkError(f"unsupported session role: {role}")
    if role == "judge":
        model = descriptor["models"]["judge"]["model"]
        key = "judge"
    else:
        condition = CONDITIONS[0 if role == "task-a" else 1]
        model = descriptor["models"]["task"]["model"]
        key = descriptor["candidates"][condition]["opaque_id"]
    reference = {"session_id": session_id, "agent_path": agent_path, "parent_session_id": parent_session_id or descriptor.get("orchestrator_session_id", "unavailable"), "model": model}
    measurement = measure_session(reference, descriptor_path.parent / "sessions" / f"{key}.jsonl", CREDIT_CONFIG)
    reference["measurement"] = measurement
    if role == "judge":
        descriptor["judge_session"] = reference
    else:
        descriptor["candidates"][condition]["session"] = reference
        (descriptor_path.parent / "artifacts" / key).mkdir(parents=True, exist_ok=True)
        (descriptor_path.parent / "artifacts" / key / "task-final.md").write_text(str(measurement.get("final_result", "unavailable")), encoding="utf-8")
    write_json(descriptor_path, descriptor)
    return reference


def evaluate(descriptor_path: Path, condition: str) -> dict[str, Any]:
    """Task diffを保存し、使い捨て複製で機械評価する。"""

    if condition not in CONDITIONS:
        raise BenchmarkError(f"unsupported condition: {condition}")
    descriptor = read_json(descriptor_path)
    candidate = descriptor["candidates"][condition]
    workspace = Path(candidate["workspace"])
    baseline = candidate.get("condition_baseline") or run_git(workspace, "rev-list", "--max-parents=0", "HEAD").stdout.strip()
    artifact_root = descriptor_path.parent / "artifacts" / candidate["opaque_id"]
    artifact_root.mkdir(parents=True, exist_ok=True)
    status = run_git(workspace, "status", "--porcelain=v1", "--untracked-files=all").stdout
    changed = run_git(workspace, "diff", "--name-status", baseline).stdout
    patch = run_git(workspace, "diff", "--binary", baseline).stdout
    stat = run_git(workspace, "diff", "--numstat", baseline).stdout
    (artifact_root / "status.txt").write_text(status, encoding="utf-8")
    (artifact_root / "changed-files.txt").write_text(changed, encoding="utf-8")
    (artifact_root / "diff.patch").write_text(patch, encoding="utf-8")
    (artifact_root / "diff-numstat.txt").write_text(stat, encoding="utf-8")

    # 機械評価によるworkspace汚染を避ける
    evaluation_root = descriptor_path.parent / "evaluation" / candidate["opaque_id"]
    copy_tree(workspace, evaluation_root, shutil.ignore_patterns(".git", "__pycache__", "*.pyc"))
    checks: list[dict[str, Any]] = []
    for configured in descriptor["checks"]:
        started = time.monotonic()
        result = subprocess.run(configured["command"], cwd=evaluation_root, shell=True, capture_output=True, text=True, check=False)
        log_path = artifact_root / f"check-{safe_name(configured['name'])}.log"
        log_path.write_text(result.stdout + result.stderr, encoding="utf-8")
        checks.append({"name": configured["name"], "command": configured["command"], "status": "PASS" if result.returncode == 0 else "FAIL", "returncode": result.returncode, "duration_seconds": round(time.monotonic() - started, 3), "log": str(log_path)})
    evaluation = {
        "status": "PASS" if checks and all(item["status"] == "PASS" for item in checks) else ("not_configured" if not checks else "FAIL"),
        "checks": checks,
        "diff": {"baseline": baseline, "patch": str(artifact_root / "diff.patch"), "status": str(artifact_root / "status.txt"), "changed_files": str(artifact_root / "changed-files.txt"), "numstat": str(artifact_root / "diff-numstat.txt"), "changed_entries": len({line[3:] for line in status.splitlines() if line} | {line.split("\t")[-1] for line in changed.splitlines() if line})},
    }
    candidate["evaluation"] = evaluation
    descriptor["state"] = "evaluated" if all(descriptor["candidates"][item].get("evaluation") for item in CONDITIONS) else descriptor["state"]
    write_json(descriptor_path, descriptor)
    write_json(artifact_root / "mechanical.json", evaluation)
    return evaluation


def blind(descriptor_path: Path) -> dict[str, str]:
    """条件情報を除外したJudge用snapshotを作りworktreeを復旧する。"""

    descriptor = read_json(descriptor_path)
    paths: dict[str, str] = {}
    blind_root = descriptor_path.parent / "blind"
    if blind_root.exists():
        remove_tree(blind_root)
    for condition in CONDITIONS:
        candidate = descriptor["candidates"][condition]
        destination = blind_root / candidate["blind_id"].lower().replace(" ", "-")
        copy_tree(Path(candidate["workspace"]), destination, shutil.ignore_patterns(".git", "project-knowledge", "__pycache__", "*.pyc"))
        paths[candidate["blind_id"]] = str(destination)
    descriptor["blind_candidates"] = paths
    recover_workspaces(descriptor_path.parent, descriptor["candidates"])
    descriptor["state"] = "blind_ready"
    write_json(descriptor_path, descriptor)
    return paths


def recover(descriptor_path: Path) -> None:
    """中断したrunの元worktree接続を復元する。"""

    descriptor = read_json(descriptor_path)
    recover_workspaces(descriptor_path.parent, descriptor.get("candidates", {}))
    descriptor["state"] = "recovered"
    write_json(descriptor_path, descriptor)


def recover_workspaces(run_root: Path, candidates: dict[str, Any]) -> None:
    """既知candidateだけを検証してGit pointerを戻す。"""

    for candidate in candidates.values():
        if not isinstance(candidate, dict) or not candidate.get("workspace") or not candidate.get("opaque_id"):
            continue
        workspace = Path(candidate["workspace"]).resolve()
        if run_root.resolve() not in workspace.parents:
            raise BenchmarkError(f"workspace escapes run root: {workspace}")
        backup = run_root / "control" / f"{candidate['opaque_id']}.gitlink"
        if not backup.is_file():
            continue
        local_git = workspace / ".git"
        if local_git.is_dir():
            make_tree_writable(local_git)
            shutil.rmtree(local_git)
        elif local_git.exists():
            local_git.unlink()
        local_git.write_text(backup.read_text(encoding="utf-8"), encoding="utf-8")
        backup.unlink()


def make_tree_writable(root: Path) -> None:
    """Windowsのread-only Git objectを削除可能にする。"""

    for path in [root, *root.rglob("*")]:
        try:
            os.chmod(path, stat.S_IWRITE | stat.S_IREAD)
        except OSError:
            continue


def copy_tree(source: Path, destination: Path, ignore: Any) -> None:
    """Windowsの深いrepositoryも拡張長pathで複製する。"""

    if destination.exists():
        remove_tree(destination)
    shutil.copytree(long_path(source), long_path(destination), ignore=ignore)


def long_path(path: Path) -> Path:
    """Windowsだけ絶対pathへextended-length prefixを付ける。"""

    resolved = path.resolve()
    if os.name == "nt" and not str(resolved).startswith("\\\\?\\"):
        return Path(f"\\\\?\\{resolved}")
    return resolved


def remove_tree(root: Path) -> None:
    """拡張長pathとread-only fileを扱って既知treeを削除する。"""

    def make_writable(function: Any, path: str, _error: BaseException) -> None:
        os.chmod(path, stat.S_IWRITE | stat.S_IREAD)
        function(path)

    shutil.rmtree(long_path(root), onexc=make_writable)


def report(descriptor_path: Path) -> tuple[str, int]:
    """機械評価、Judge、usageを分離した比較reportを生成する。"""

    descriptor = read_json(descriptor_path)
    judge_path = descriptor_path.parent / "judge.json"
    judge = read_json(judge_path) if judge_path.is_file() else None
    if judge is not None:
        validate_judge(judge)
    rows: dict[str, Any] = {}
    for condition in CONDITIONS:
        candidate = descriptor["candidates"][condition]
        measurement = (candidate.get("session") or {}).get("measurement") or {"usage_status": "unavailable"}
        rows[condition] = {
            "workspace": candidate["workspace"],
            "blind_id": candidate["blind_id"],
            "mechanical": candidate.get("evaluation"),
            "usage": measurement.get("usage", "unavailable"),
            "credits": measurement.get("credits", "unavailable"),
            "task_final": str(descriptor_path.parent / "artifacts" / candidate["opaque_id"] / "task-final.md"),
        }
    comparison = {
        "schema_version": 1,
        "baseline": descriptor["baseline"],
        "task": descriptor["task_file"],
        "models": descriptor["models"],
        "conditions": rows,
        "mechanical_evaluation": {key: rows[key]["mechanical"] for key in CONDITIONS},
        "llm_judge": judge or "unavailable",
        "judge_session": descriptor.get("judge_session"),
        "deltas": numeric_deltas(rows),
    }
    write_json(descriptor_path.parent / "comparison.json", comparison)
    output = render_report(comparison)
    (descriptor_path.parent / "comparison.md").write_text(output, encoding="utf-8")
    descriptor["state"] = "complete"
    descriptor["comparison_report"] = str(descriptor_path.parent / "comparison.md")
    write_json(descriptor_path, descriptor)
    success = all(rows[item]["mechanical"] and rows[item]["mechanical"]["status"] in {"PASS", "not_configured"} for item in CONDITIONS) and judge is not None
    return output, 0 if success else 1


def validate_judge(judge: dict[str, Any]) -> None:
    """blind Judge JSONの共通契約を検証する。"""

    candidates = judge.get("candidates")
    if not isinstance(candidates, dict) or set(candidates) != {"Candidate 1", "Candidate 2"}:
        raise BenchmarkError("judge candidates are invalid")
    for candidate in candidates.values():
        dimensions = candidate.get("dimensions") if isinstance(candidate, dict) else None
        if not isinstance(dimensions, dict) or set(dimensions) != set(DIMENSIONS):
            raise BenchmarkError("judge dimensions are invalid")
        for value in dimensions.values():
            if not isinstance(value, dict) or not isinstance(value.get("score"), int) or not 0 <= value["score"] <= 100 or not isinstance(value.get("reason"), str) or not isinstance(value.get("evidence"), list):
                raise BenchmarkError("judge dimension value is invalid")
        if not isinstance(candidate.get("overall_score"), int) or not 0 <= candidate["overall_score"] <= 100:
            raise BenchmarkError("judge overall score is invalid")
    if judge.get("preference") not in {"Candidate 1", "Candidate 2", "tie"} or not isinstance(judge.get("summary"), str):
        raise BenchmarkError("judge preference or summary is invalid")


def numeric_deltas(rows: dict[str, Any]) -> dict[str, Any]:
    """両条件で取得できたusage/creditsだけB-Aを返す。"""

    result: dict[str, Any] = {"usage": {}, "credits": {}}
    for group, delta in result.items():
        left = rows["no_knowledge"].get(group)
        right = rows["with_knowledge"].get(group)
        if not isinstance(left, dict) or not isinstance(right, dict):
            continue
        for key in set(left) & set(right):
            if isinstance(left[key], (int, float)) and isinstance(right[key], (int, float)):
                delta[key] = right[key] - left[key]
    return result


def render_report(comparison: dict[str, Any]) -> str:
    """人間向けMarkdown比較表を作る。"""

    lines = ["# Project Knowledge Utility Benchmark", "", f"Baseline: `{comparison['baseline']['commit']}`", "", "## Mechanical evaluation", "", "| Condition | Status | Changed entries |", "| --- | --- | ---: |"]
    for condition in CONDITIONS:
        value = comparison["conditions"][condition]["mechanical"] or {}
        lines.append(f"| {condition} | {value.get('status', 'unavailable')} | {value.get('diff', {}).get('changed_entries', 'unavailable')} |")
    lines.extend(["", "## LLM Judge", "", f"Preference: `{comparison['llm_judge'].get('preference', 'unavailable') if isinstance(comparison['llm_judge'], dict) else 'unavailable'}`", "", "## Usage and AI Credit", "", "| Condition | Total tokens | AI Credit |", "| --- | ---: | ---: |"])
    for condition in CONDITIONS:
        row = comparison["conditions"][condition]
        usage = row["usage"].get("total_tokens", "unavailable") if isinstance(row["usage"], dict) else "unavailable"
        credits = row["credits"].get("total", "unavailable") if isinstance(row["credits"], dict) else "unavailable"
        lines.append(f"| {condition} | {usage} | {credits} |")
    lines.extend(["", "Machine evaluation, Judge evaluation, and usage are independent observations. This single run does not establish a statistical effect."])
    return "\n".join(lines) + "\n"


def safe_name(value: str) -> str:
    """artifact filenameへ使える短い名前へ変換する。"""

    return "".join(character if character.isalnum() or character in "-_" else "-" for character in value).strip("-") or "check"


def read_json(path: Path) -> dict[str, Any]:
    """JSON objectを読み込む。"""

    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise BenchmarkError(f"JSON object required: {path}")
    return value


def write_json(path: Path, value: Any) -> None:
    """後から検証できる整形JSONを書き込む。"""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    """段階的Runner CLIを構築する。"""

    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    prepare_parser = commands.add_parser("prepare")
    prepare_parser.add_argument("repository", type=Path)
    prepare_parser.add_argument("--task-file", required=True, type=Path)
    prepare_parser.add_argument("--baseline", default="HEAD")
    prepare_parser.add_argument("--output-root", type=Path)
    prepare_parser.add_argument("--checks", type=Path)
    session_parser = commands.add_parser("session")
    session_commands = session_parser.add_subparsers(dest="session_command", required=True)
    record_parser = session_commands.add_parser("record")
    record_parser.add_argument("descriptor", type=Path)
    record_parser.add_argument("role", choices=("task-a", "task-b", "judge"))
    record_parser.add_argument("session_id")
    record_parser.add_argument("--agent-path", required=True)
    record_parser.add_argument("--parent-session-id")
    evaluate_parser = commands.add_parser("evaluate")
    evaluate_parser.add_argument("descriptor", type=Path)
    evaluate_parser.add_argument("condition", choices=CONDITIONS)
    for name in ("blind", "report", "recover"):
        command = commands.add_parser(name)
        command.add_argument("descriptor", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI commandを実行し、結果pathまたはreportを表示する。"""

    args = build_parser().parse_args(argv)
    try:
        if args.command == "prepare":
            print(prepare(args.repository, args.task_file, args.baseline, args.output_root, args.checks))
        elif args.command == "session":
            print(json.dumps(record_session(args.descriptor, args.role, args.session_id, args.agent_path, args.parent_session_id), ensure_ascii=False, indent=2))
        elif args.command == "evaluate":
            print(json.dumps(evaluate(args.descriptor, args.condition), ensure_ascii=False, indent=2))
        elif args.command == "blind":
            print(json.dumps(blind(args.descriptor), ensure_ascii=False, indent=2))
        elif args.command == "recover":
            recover(args.descriptor)
            print(args.descriptor)
        else:
            output, exit_code = report(args.descriptor)
            print(output, end="")
            return exit_code
    except (BenchmarkError, OSError, ValueError, yaml.YAMLError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
