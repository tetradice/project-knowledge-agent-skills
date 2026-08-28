---
type: Project Knowledge Utility Benchmark
pk_category: extracted
pk_derivation: synthesized
status: stable
generated:
  by: project-knowledge/3.1.0
  at: 2026-08-28T18:52:00+09:00
verified:
  by: process:pytest-and-static-checks
  at: 2026-08-28T18:52:00+09:00
sources:
- resource: ../references/user-statements/2026-08-28-project-knowledge-utility-benchmark.md
  pk_source_type: user-statement
- resource: ../references/interactions/2026-08-28-project-knowledge-utility-benchmark-implementation.md
  pk_source_type: interaction-record
- resource: ../../../skills/project-knowledge-benchmark/SKILL.md
  pk_source_type: change-implementation
- resource: ../../../skills/project-knowledge-benchmark/references/runner.md
  pk_source_type: change-implementation
- resource: ../../../skills/project-knowledge-benchmark/scripts/benchmark_runner.py
  pk_source_type: change-implementation
- resource: ../../../skills/project-knowledge-benchmark/scripts/benchmark_session.py
  pk_source_type: change-implementation
- resource: ../../../skills/project-knowledge-benchmark/agents/benchmark.yml
  pk_source_type: change-implementation
- resource: ../../../skills/project-knowledge-benchmark/agents/credit-rates.yml
  pk_source_type: change-implementation
- resource: ../../../skills/project-knowledge-benchmark/tests/test_benchmark_runner.py
  pk_source_type: change-implementation
- resource: ../../../skills/project-knowledge-benchmark/tests/test_benchmark_session.py
  pk_source_type: change-implementation
---
# Project Knowledge Utility Benchmark

`project-knowledge-benchmark`は、任意のcleanなGit repositoryと同一実務Taskを、No-Knowledge / With-Knowledgeの独立Task Agentで各1回実行する明示実行Skillである。通常のProject Knowledge保守、Scenario Test、verify、fix、audit、refactorから自動起動しない。

## 実行境界

`prepare`は指定baseline commitからA/B worktreeを作る。No-Knowledge側だけ`project-knowledge/`を除外し、それ以外のtree hashが一致することを確認する。実行中は各worktreeの元Git linkを退避し、単一commitのlocal historyへ切り替える。これによりNo-Knowledge側は削除済みKnowledgeをGit履歴から復元できない。`blind`または`recover`は元のworktree linkを復元し、A/B workspaceを削除しない。

Task Agentは同一model、reasoning effort、Task本文、workspace外を読まない境界指示で独立起動する。With-Knowledge側にKnowledge利用を強制する追加指示は与えない。Task Agentは開始時点の`project-knowledge/`を変更しない。

## 評価と保存

Runnerは`prepare`、`session record`、`evaluate`、`blind`、`report`、`recover`の段階的CLIを持つ。checksは明示YAMLから固定し、candidateを使い捨て複製して実行する。差分はTask Agentがcommitした変更も含め、condition baselineから取得する。Windowsの長いsource pathではextended-length pathで複製する。

`blind`は`.git`、`project-knowledge/`、condition名、session、usage、機械評価を除外した`Candidate 1` / `Candidate 2` snapshotを作る。JudgeにはTaskとsnapshotだけを渡し、対応関係、Project Knowledge、runtime、usage、credits、機械評価を渡さない。Judge結果は機械評価と別の`judge.json`として扱う。

session usageはCodex rollout JSONLだけから取得する。session ID、parent session ID、agent path、modelを照合し、最初の`total_token_usage - last_token_usage`を親baselineとして除外する。対応不能、破損、field矛盾、rate未定義は推測せず`unavailable`にする。AI Creditはモデル別rate tableでuncached input、cached input、outputを別々に換算し、reasoning outputを二重計上しない。

各runはrepository外の`<repository-name>-project-knowledge-benchmarks/<run-id>/`へ`benchmark.json`、task、workspace、session log、Task Agent最終結果、diff、機械評価log、blind snapshot、Judge結果、`comparison.json`、`comparison.md`を残す。`comparison`は機械評価、LLM Judge、usage / creditsを別セクションとして保存する。

## 2026-08-28 single-run smoke結果

このrepositoryのREADME表記を検証するpytest追加Taskを、GPT-5.6 Terra / low reasoningでA/B各1回、独立Judge 1回として実行した。baselineは`216e89304944e4dd56366c2264266ca414d89f83`である。

| 指標 | No-Knowledge | With-Knowledge |
| --- | ---: | ---: |
| Task Agent total tokens | 420445 | 503061 |
| Task Agent AI Credit | 4.53955 | 5.95848 |
| 変更ファイル数 | 1 | 1 |
| 機械評価 | PASS | PASS |

Judgeは176079 tokens、3.1713 creditsを使用した。blind JudgeはWith-Knowledgeに対応するCandidate 2を、より説明的なtest名を理由に僅差で選好した。これは小さな単一Task・single-runの観測であり、Project Knowledgeの一般的効果、モデルの恒久的な優劣、token効率を結論づけない。
