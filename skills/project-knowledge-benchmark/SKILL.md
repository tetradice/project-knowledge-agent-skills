---
name: project-knowledge-benchmark
description: Git管理プロジェクトの同一実務タスクを、現在のProject Knowledgeなし/ありの独立Agentで実行し、機械評価、差分、Codex session usage、AI Credit、blind Judgeを比較する。ユーザーがProject Knowledgeの実務効果、Utility、A/B Benchmarkを明示的に求めた場合だけ使用する。
metadata:
  version: "1.0.0"
---

# Project Knowledge Benchmark

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
