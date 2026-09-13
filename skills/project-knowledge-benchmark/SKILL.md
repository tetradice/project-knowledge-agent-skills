---
name: project-knowledge-benchmark
description: Git管理プロジェクトの同一実務タスクを、現在のProject Knowledgeなし/ありの独立Agentで実行し、機械評価、差分、Codex session usage、AI Credit、blind Judgeを比較する。ユーザーがProject Knowledgeの実務効果、Utility、A/B Benchmarkを明示的に求めた場合だけ使用する。
metadata:
  version: "1.0.0"
---

# Project Knowledge Benchmark

## 対象プロジェクトの解決

このSkillは共通の設定解決に`project-knowledge` Skillを必要とする。
プロジェクトのKnowledgeへアクセスする前に[ルート設定](../project-knowledge/references/project-config.md)に従って`project_config.py`を実行する。
`project-knowledge.yaml`がなければ対象外とし、固定ディレクトリから推測しない。一般的な利用案内は設定なしでも説明できる。
以後の`project-knowledge/`表記は解決済みのレイヤーパスを意味する。
`description`を用途と適用範囲の判断に使い、書き込み前には`--write`で対象を確認する。読み取り専用レイヤーへstateや成果物も保存しない。
設定の`version: "1.0"`は必須で、ユーザーの指示なしに版を上げない。複数レイヤーの同時利用は未対応とする。


現在存在するProject KnowledgeがSoftware Engineering Taskへ与える効果をsingle-runで比較する。通常のProject Knowledge保守やScenario Testから自動実行しない。

## 実行前に読む

[Runner workflow](references/runner.md)を最後まで読み、そこに記載した順序と隔離境界を守る。

## 共通ルール

- `project-knowledge`、`verify`、`fix`、`audit`、`refactor`、`update`をBenchmark前後に実行しない。
- baselineはcleanなGit commitに固定し、dirty/untrackedな内容を暗黙に含めない。
- A/B Task Agentは`agents/benchmark.yml`の同一model、reasoning effort、`fork_turns: none`で同時に起動する。
- A/Bへ同一taskと同一境界指示だけを渡す。With-Knowledgeへ利用を強制する指示を追加しない。
- Task Agentへもう一方のworkspace、run descriptor、Judge rubric、機械評価結果を渡さない。
- Judgeへ条件対応、Project Knowledge、session、usage、credits、機械評価結果を渡さない。
- usageはAgentへ自己申告させず、Runnerにsession IDを記録してCodex rollout JSONLから取得する。
- 取得不能値は推測せず`unavailable`のまま報告する。
- workspaceと結果は削除しない。中断時は`recover`で元worktree接続を復元する。
- single-run結果を統計的効果や恒久的な優劣として断定しない。
