# Runner workflow

## 1. 実行条件を固定する

対象repository、task本文、baseline refを確認する。build/test/lint commandはCI、manifest、READMEに明記されたものだけを選び、次のYAMLとして保存する。確定できない種類は省略する。

```yaml
checks:
  - name: test
    command: uv run --with pytest --with pyyaml pytest -q
```

`prepare`を実行する。

```console
uv run --with pyyaml python <skill-root>/scripts/benchmark_runner.py prepare <repository> --task-file <task.md> --checks <checks.yml>
```

出力された`benchmark.json`だけがconditionとopaque workspaceの対応を保持する。

## 2. Task Agentを独立実行する

descriptorの`models.task`で2 Agentを同じturnに起動する。各Agentへ対応するworkspace、task本文、次の共通指示だけを渡す。

- workspaceをproject rootとして調査・実装・検証する。
- workspace外、run descriptor、もう一方のcandidateを読まない。
- `project-knowledge/`を変更しない。
- 通常のrepository情報を利用できるが、Project Knowledge Skillの保守操作を実行しない。

各完了通知のsession IDとagent pathを記録する。

```console
python <runner> session record <benchmark.json> task-a <session-id> --agent-path <path>
python <runner> session record <benchmark.json> task-b <session-id> --agent-path <path>
```

## 3. 機械評価とblind snapshotを作る

```console
python <runner> evaluate <benchmark.json> no_knowledge
python <runner> evaluate <benchmark.json> with_knowledge
python <runner> blind <benchmark.json>
```

`evaluate`はTask workspaceのdiffを保存し、使い捨て複製で同じchecksを実行する。`blind`はProject KnowledgeとGit情報を除外した`Candidate 1` / `Candidate 2`を作り、元worktree接続を復元する。

## 4. Judgeを独立実行する

descriptorの`models.judge`と`fork_turns: none`でJudgeを起動する。task本文、blind candidate paths、次のJSON契約だけを渡し、`judge.json`以外を変更させない。

```json
{
  "candidates": {
    "Candidate 1": {
      "dimensions": {
        "requirement_compliance": {"score": 0, "reason": "...", "evidence": ["..."]},
        "project_convention_compliance": {"score": 0, "reason": "...", "evidence": ["..."]},
        "architectural_consistency": {"score": 0, "reason": "...", "evidence": ["..."]},
        "scope_discipline": {"score": 0, "reason": "...", "evidence": ["..."]},
        "code_quality": {"score": 0, "reason": "...", "evidence": ["..."]},
        "maintainability": {"score": 0, "reason": "...", "evidence": ["..."]}
      },
      "overall_score": 0
    },
    "Candidate 2": {}
  },
  "preference": "Candidate 1|Candidate 2|tie",
  "summary": "..."
}
```

Judge sessionを記録し、reportを生成する。

```console
python <runner> session record <benchmark.json> judge <session-id> --agent-path <path>
python <runner> report <benchmark.json>
```

機械評価、Judge、usage/creditsを分離して報告し、run directoryと残した両workspaceをユーザーへ示す。
