---
type: Project Knowledge Scenario Benchmark
pk_category: extracted
pk_derivation: synthesized
status: stable
generated:
  by: project-knowledge/3.1.0
  at: 2026-08-27T00:00:00+09:00
verified:
  by: process:scenario-test
  at: 2026-08-27T00:00:00+09:00
sources:
- resource: ../references/user-statements/2026-08-27-model-benchmark.md
  pk_source_type: user-statement
- resource: ../references/interactions/2026-08-27-model-benchmark-execution.md
  pk_source_type: interaction-record
- resource: ../../../skills/project-knowledge-scenario-test/agents/benchmark.yml
  pk_source_type: change-implementation
- resource: ../../../skills/project-knowledge-scenario-test/references/benchmark.md
  pk_source_type: change-implementation
- resource: ../../../skills/project-knowledge-scenario-test/scripts/scenario_test.py
  pk_source_type: change-implementation
- resource: ../../../skills/project-knowledge-scenario-test/tests/test_scenario_test.py
  pk_source_type: change-implementation
---
# QuickシナリオのモデルBenchmark

`project-knowledge-scenario-test`は、既存の`quick-basic`を再利用してKnowledge Base構築モデルを比較する明示実行の`benchmark`を提供する。Full scenario、複数回実行、pairwise Judge、Judge ensembleは対象外である。

比較対象ActorとJudgeは`agents/benchmark.yml`に一箇所で定義する。現在のActorはGPT-5.6 Luna、Terra、Solであり、各Actorは同一fixtureと同一依頼を独立workspaceで1回だけ実行する。JudgeはGPT-5.6 Lunaに固定し、各Candidateを`Candidate A`などの匿名IDとして評価する。JudgeへActorのモデル名、token、cost、実行時間は渡さない。

各candidateには既存Quickのdeterministic validatorと6観点（correctness、completeness、provenance、classification、noise rejection、unsupported claims）のJudge rubricを適用する。`benchmark report`はdeterministic結果、JudgeのPASS数を100点換算したquality score、Knowledge Base統計、issueを比較表示し、JSONにも保存する。quality scoreはtoken efficiencyや単一の総合Winnerを決める根拠にはしない。

Actor usageを実測できるAPI値がない項目は推定せず`unavailable`として記録する。JudgeとorchestratorのusageをActor usageへ混在させない。

2026-08-27のsingle-run `quick-basic`では、3候補ともdeterministic validationはPASSだった。Lunaは必須Knowledgeとprovenanceの不足によりquality score 67でJudge FAIL、TerraとSolは全6観点PASSでquality score 100だった。Actor tokenは全候補で`unavailable`だった。この結果は1回の実行だけであり、安定性や分散を表すものではない。
