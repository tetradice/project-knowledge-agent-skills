---
type: Reference
pk_source_type: user-statement
generated:
  by: project-knowledge/3.1.0
  at: 2026-08-28T18:52:00+09:00
---

# Project Knowledge Utility Benchmarkの方針

任意のGit管理プロジェクトで、同じ実務タスクをProject Knowledgeなしとありの独立Agentへ各1回実行させ、成果物の品質とAI利用量を比較できるようにする。

Benchmarkは明示実行専用の`project-knowledge-benchmark`として追加する。既存Skill群とQuick Scenario Testの責務・挙動は維持し、Runnerは将来Scenario Testや複数モデル比較から再利用できるよう分離する。

初期実装はGit worktree方式とし、A/Bを同一baselineから独立させる。AはProject Knowledgeを除外し、Git履歴経由でも復元できないようにする。終了後もA/B workspaceを残す。BだけにKnowledge利用を強制する指示は与えない。

評価では機械評価、差分、Task Agent最終結果、Codex session log由来のtoken usage、AI Credit、blind Judgeを分離する。取得不能な値は推測しない。Benchmark結果を`project-knowledge/`へ自動反映せず、開始前にverify、fix、audit、refactorを自動実行しない。

初期版はsingle-run、単一Task model、単一Judgeとし、複数回統計、複数モデル、strict snapshot、Full suiteは将来拡張とする。
