---
name: project-knowledge-scenario-test
description: Project Knowledge Skill自身のE2E品質を、隔離Fixture、Actor、deterministic validation、独立Judgeで評価する。開発者がQuickシナリオテストを明示実行した場合だけ使用する。
metadata:
  version: "1.0.0"
---

# Project Knowledge Scenario Test

Project Knowledge Skillの生成品質を、通常利用に近いActorと独立したJudgeで評価する。Knowledge Baseの保守操作ではなく、Skill開発者向けテストとして扱う。

## 実行モード

`quick`だけを扱う。`full`や未指定の別モードをQuickへ読み替えず、未対応として報告する。

Quickを実行するときは[Quick scenario](references/quick.md)を読み、記載された順序、モデル、隔離境界、終了条件に従う。

## 共通ルール

- ActorとJudgeは別のサブエージェントとし、どちらも`gpt-5.6-luna`、`reasoning_effort: low`、`fork_turns: none`で起動する。
- ActorへJudgeの期待値、採点観点、`expectations.yml`の場所を渡さない。
- JudgeへActorの会話、判断過程、プロンプトを渡さない。
- Actorには開発中checkoutの`project-knowledge` Skillを通常どおり実行させ、テスト専用の生成手順へ置き換えない。
- 機械判定できる問題は既存validatorを再利用し、意味評価だけをJudgeへ委ねる。
- 元Fixtureやリポジトリを変更せず、最後に一時workspaceを必ず破棄する。
- QuickではActor 1 + Judge 1を基本とし、多数決や観点別Judgeを追加しない。
