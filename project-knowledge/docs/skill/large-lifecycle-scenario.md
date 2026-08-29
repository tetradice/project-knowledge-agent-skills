---
type: Project Knowledge Large Scenario
pk_category: extracted
pk_derivation: synthesized
status: stable
generated:
  by: project-knowledge/3.1.0
  at: 2026-08-28T15:20:09+09:00
verified:
  by: process:scenario-test
  at: 2026-08-28T15:20:09+09:00
sources:
- resource: ../../../developer-tests/project-knowledge-scenario-test/SKILL.md
  pk_source_type: change-implementation
- resource: ../../../developer-tests/project-knowledge-scenario-test/references/large.md
  pk_source_type: change-implementation
- resource: ../../../developer-tests/project-knowledge-scenario-test/scripts/scenario_test.py
  pk_source_type: change-implementation
- resource: ../../../developer-tests/project-knowledge-scenario-test/agents/scenarios.yml
  pk_source_type: change-implementation
- resource: ../../../developer-tests/project-knowledge-scenario-test/agents/credit-rates.yml
  pk_source_type: change-implementation
- resource: ../../../developer-tests/project-knowledge-scenario-test/scenarios/large-lifecycle/scenario.yml
  pk_source_type: change-implementation
- resource: ../references/interactions/2026-08-28-large-lifecycle-execution.md
  pk_source_type: interaction-record
---
# Largeライフサイクルシナリオ

`project-knowledge-scenario-test`の`large`は、Quickと同じdeterministic validationとJudgeの6観点を、人工Fixtureの規模と長期更新で評価する明示実行専用のシナリオである。評価観点を広げるFullとは異なり、Largeはscale / lifecycle、Fullはcoverage / depthを扱う。Full、Utility、audit、refactor、fixはLargeから自動実行しない。

`large-lifecycle`は初期Fixtureを隔離workspaceへ複製してGit初期commitを作成し、通常のProject Knowledge Actorによる初期構築、12個のChange Set、各update後の通常updateを順番に実行する。Change Setは追加、設定変更、module追加、documentation-only、large変更、noise-only、削除、移動、architecture、deployment、rename、運用追加を含む。Actorには期待値、Change Set、Judge rubricを渡さず、JudgeはActorの会話や判断過程を参照しない。

各stepは`large.json`へoperation、Change Set、repository files、changed files、changed bytes、deterministic validation、Knowledge統計、Actor/Judge usage、quality score、issuesを保存する。Judgeは`initial`、`update-06`、`update-12`だけで実行し、それ以外のstepはdeterministic validationと機械統計だけを記録する。workspaceは結果を退避した後にcleanupするため、Fixtureと次回実行は汚染されない。

ActorとJudgeのusageは、対応づけたCodex rollout JSONLからだけ取得する。input tokenにはcached inputが含まれるため、creditはuncached input、cached input、outputを別レートで計算する。取得・対応づけできないusageは推定せず`unavailable`とする。GPT-5.6 Lunaの2026-08-28レート表では、100万tokenあたりinput 5、cached input 0.5、output 30 creditsである。orchestrator usageはActor usageへ混在させない。

2026-08-28に実行したFixture version 1は、初期Source 39 files・8,098 characters、12 updatesだった。全13 stepのdeterministic validationはPASSし、Knowledgeは3 Concept・2,840 charactersから12 Concept・11,420 charactersへ増加した。checkpoint Judge scoreはinitial 83、update-06 83、final 100であり、初期とupdate-06のcompleteness/provenance不足によりシナリオ全体はFAILとなった。final checkpointでは6観点すべてPASSだった。noise-only updateではKnowledge更新不要と判断された。

同実行のActorは7.420043 credits、Judgeは0.973913 credits、合計は8.393956 creditsだった。Actor creditの内訳はuncached input 2.165825、cached input 3.971328、output 1.282890、Judgeの内訳は0.381135、0.376448、0.216330である。これはsingle-run結果であり、モデルや版の安定性・分散を示すものではない。

Fixture version 1はQuickより明確に大きく、lifecycleとtoken推移を検出できるが、39 files・約8 KBは数百～千files級の実案件規模ではない。実案件規模の選択や見積りに使う前には、同じ構造を保ったままFixtureを段階的に拡張し、Largeを再実行する必要がある。
