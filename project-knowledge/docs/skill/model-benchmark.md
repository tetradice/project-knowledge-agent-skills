---
type: Project Knowledge Scenario Benchmark
pk_category: extracted
pk_derivation: synthesized
status: stable
generated:
  by: project-knowledge/3.1.0
  at: 2026-08-28T15:36:03+09:00
verified:
  by: process:pytest-and-static-checks
  at: 2026-08-28T15:36:03+09:00
sources:
- resource: ../references/user-statements/2026-08-27-model-benchmark.md
  pk_source_type: user-statement
- resource: ../references/user-statements/2026-08-28-scenario-credit-measurement.md
  pk_source_type: user-statement
- resource: ../references/interactions/2026-08-27-model-benchmark-execution.md
  pk_source_type: interaction-record
- resource: ../references/interactions/2026-08-28-scenario-credit-measurement-implementation.md
  pk_source_type: interaction-record
- resource: ../../../skills/project-knowledge-scenario-test/agents/benchmark.yml
  pk_source_type: change-implementation
- resource: ../../../skills/project-knowledge-scenario-test/agents/credit-rates.yml
  pk_source_type: change-implementation
- resource: ../../../skills/project-knowledge-scenario-test/references/benchmark.md
  pk_source_type: change-implementation
- resource: ../../../skills/project-knowledge-scenario-test/scripts/scenario_test.py
  pk_source_type: change-implementation
- resource: ../../../skills/project-knowledge-scenario-test/scripts/session_usage.py
  pk_source_type: change-implementation
- resource: ../../../skills/project-knowledge-scenario-test/tests/test_scenario_test.py
  pk_source_type: change-implementation
- resource: ../../../skills/project-knowledge-scenario-test/tests/test_session_usage.py
  pk_source_type: change-implementation
---
# QuickシナリオのモデルBenchmark

`project-knowledge-scenario-test`は、既存の`quick-basic`を再利用してKnowledge Base構築モデルを比較する明示実行の`benchmark`を提供する。Full scenario、複数回実行、pairwise Judge、Judge ensembleは対象外である。

比較対象ActorとJudgeは`agents/benchmark.yml`に一箇所で定義する。現在のActorはGPT-5.6 Luna、Terra、Solであり、各Actorは同一fixtureと同一依頼を独立workspaceで1回だけ実行する。JudgeはGPT-5.6 Lunaに固定し、各Candidateを`Candidate A`などの匿名IDとして評価する。JudgeへActorのモデル名、token、cost、実行時間は渡さない。

各candidateには既存Quickのdeterministic validatorと6観点（correctness、completeness、provenance、classification、noise rejection、unsupported claims）のJudge rubricを適用する。`benchmark report`はdeterministic結果、JudgeのPASS数を100点換算したquality score、Actor credits、raw token usage、Knowledge Base統計、issueを比較表示し、JSONにも保存する。quality scoreはtoken efficiencyや単一の総合Winnerを決める根拠にはしない。

usage source of truthはCodex session / rollout JSONLだけである。subagent起動時にsession ID、parent session ID、agent path、modelを記録し、Codex home下のrolloutを`session_meta.id`、`parent_thread_id`、agent path、`turn_context.model`で照合する。時刻や最新ファイルだけでは推測しない。

`token_count`は累積値の単純加算をせず、最初の`total_token_usage - last_token_usage`を親session由来baselineとして除外する。最後の`total_token_usage - baseline`をraw usageとし、input、cached input、output、reasoning output、total tokensを保持する。対応不能、破損、必須field欠落、矛盾、未知modelでは`unavailable`と理由を保存し、品質結果を変更しない。

コスト指標は`agents/credit-rates.yml`のCodex creditsであり、rate tableのchecked_atを結果へ残す。uncached input（input - cached input）、cached input、outputを別rateで換算し、reasoning outputを二重計上しない。BenchmarkはActor creditsでCandidateの最低コストを判定する。Judge creditsはBenchmark共通コストとして別集計し、orchestratorは正確に独立計測できない限り`unavailable`のままActor / Judgeへ混在させない。app-server、Responses API、Actor自己申告、token単価や通貨換算は使用しない。

2026-08-27のsingle-run `quick-basic`では、3候補ともdeterministic validationはPASSだった。Lunaは必須Knowledgeとprovenanceの不足によりquality score 67でJudge FAIL、TerraとSolは全6観点PASSでquality score 100だった。既存6 rolloutの再計測ではActor creditsがLuna 0.241434、Terra 11.036310、Sol 14.716300、Judge credits合計が1.056546、Benchmark totalが27.050590だった。Best qualityはTerraとSol、Lowest creditsはLunaである。この再計測はsingle-run結果であり、モデルや版の安定性・分散を表すものではない。
