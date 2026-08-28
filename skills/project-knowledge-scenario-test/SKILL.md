---
name: project-knowledge-scenario-test
description: Project Knowledge Skill自身のE2E生成品質と、Knowledge利用時の実作業Utilityを隔離Fixture、deterministic validation、独立Judgeで評価する。開発者がQuick、Model Benchmark、Utility Benchmarkを明示実行した場合だけ使用する。
metadata:
  version: "1.0.0"
---

# Project Knowledge Scenario Test

Project Knowledge Skillの生成品質と実作業でのUtilityを、通常利用に近い独立AgentとJudgeで評価する。Knowledge Baseの保守操作ではなく、Skill開発者向けテストとして扱う。

## 実行モード

`quick`、`benchmark`、`utility`を扱う。`full`や未指定の別モードをQuickへ読み替えず、未対応として報告する。

Quickを実行するときは[Quick scenario](references/quick.md)を読み、記載された順序、モデル、隔離境界、終了条件に従う。

Benchmarkを実行するときは[Benchmark](references/benchmark.md)を読み、Quickを再利用した候補実行、blind Judge、結果集計の順序に従う。

Utilityを実行するときは[Utility Benchmark](references/utility.md)を読み、Knowledge Builder、No-KB / With-KB Task Agent、deterministic evaluation、blind Judge、delta reportを独立contextで実行する。

## 共通ルール

- QuickのActorとJudgeは従来どおり別の`gpt-5.6-luna`サブエージェントとし、`reasoning_effort: low`、`fork_turns: none`で起動する。Model BenchmarkのActorとJudgeは`agents/benchmark.yml`、UtilityのTask / Judgeは`agents/utility.yml`だけで定義する。
- ActorへJudgeの期待値、採点観点、`expectations.yml`の場所を渡さない。
- JudgeへActorの会話、判断過程、プロンプトを渡さない。
- Actorには開発中checkoutの`project-knowledge` Skillを通常どおり実行させ、テスト専用の生成手順へ置き換えない。
- 機械判定できる問題は既存validatorを再利用し、意味評価だけをJudgeへ委ねる。
- 元Fixtureやリポジトリを変更せず、最後に一時workspaceを必ず破棄する。
- QuickではActor 1 + Judge 1を基本とし、多数決や観点別Judgeを追加しない。
- Benchmarkは明示実行時だけ行い、Full scenario、複数回実行、pairwise Judge、Judge ensembleを追加しない。
- Utilityも明示実行時だけ行い、QuickやBenchmarkから自動起動しない。single-runの観測結果を統計的効果として断定しない。
- QuickとModel Benchmarkのusageは、記録したsubagent session IDに対応するCodex rollout JSONLだけから計測する。Actorへ自己申告させず、app-serverやusage APIへfallbackしない。正確に対応付けまたはbaseline算出できなければ、品質結果とは独立して`unavailable`とする。
- コスト比較は`agents/credit-rates.yml`の基準日つきCodex credit rateを使い、token数や通貨換算をコスト指標にしない。
