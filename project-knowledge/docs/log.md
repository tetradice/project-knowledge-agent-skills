---
title: ナレッジ log
description: プロジェクトナレッジの変更履歴
version: "0.1.0"
generated:
  by: project-knowledge
---

# ナレッジ log

## 2026-08-25 — Knowledge限定回答Skillを改名

- `project-knowledge-ask`を`project-knowledge-fast-ask`へ改名した。
- Skillの明示呼び出し契約、AGENTS.md生成テンプレート、README、回帰テスト、Project Knowledgeのsource参照を新名称へ同期した。

## 2026-08-25 — Project Knowledgeを5 Skillへ責務分割

- メインSkillを`init`、`update`、`config`へ純化し、ask、publish、verify、auditを専用Skillへ分離した。
- 4つの専用Skillをexplicit-onlyにし、暗黙発火、情報源フォールバック、検出後の自動更新、update後の自動publishを禁止した。
- offline HTML生成処理はpublish、構造検証処理はverifyへ移し、AGENTS.mdの初期化テンプレートと利用例を新構成へ更新した。

## 2026-08-23 — verify操作のmemoを現行Policyに同期

verify操作のmemoから旧`scope`を現行のプロジェクトKnowledge Policyへ置き換えた。検証対象、Information Architectureとの分離、索引説明を現行Skillの`verification.md`に合わせた。

## 2026-08-23 — update操作統合の実装報告を同期

- 対象: `docs/skill/index.md`
- 内容: 実装報告をprovenanceへ追加し、16件の自動テストを含む検証実績と、意味判断・未知scope・互換aliasに関する既知の制約を反映。
- 根拠: [update操作統合・scope廃止 実装報告](../../UPDATE_OPERATION_INTEGRATION_REPORT.md)

## 2026-08-23 — update統合・scope廃止・Knowledge Policy導入

- 対象: プロジェクトナレッジ Skillの操作体系、provenance、Policy、learning mode、migration、verify、audit
- 内容: ナレッジ書き込みをupdateへ統合し、capture/memoを内部provenanceへ変更。scopeを廃止してopen-world型のKnowledge Policyを導入し、新規既定をopportunisticとした。
- 移行: このリポジトリの旧scopeをPolicyへ意味的に変換し、`automatic_after_work: false`は互換性のため`learning.mode: manual`へ移行。
- 根拠: `skills/project-knowledge/`のSkill、references、templates、scripts、tests

## 2026-08-23 — verify操作の検証範囲を記録

- 対象: `verify` 操作
- 内容: read-only性、構造・鮮度・scope適合性・Information Architectureの検査範囲と、High/Medium/Lowによる報告形式をprovisional memoへ記録。
- 根拠: `skills/project-knowledge/references/verification.md`、`docs/skill/index.md`

## 2026-08-23 — 初期化と実装報告の取り込み

- 対象: `PROJECT_KNOWLEDGE_IMPLEMENTATION_REPORT.md`
- 内容: ナレッジ基盤を初期化し、レポートをtrusted captureとして保存。レポートに基づくSkill概要を追加。
- 根拠: [プロジェクトナレッジ Agent Skill 実装報告](references/captures/project-knowledge-implementation-report.md)

## 2026-08-23 — scopeとInformation Architectureの分離

- 対象: プロジェクトナレッジ Skillのscope、init、Information Architecture、verify、audit
- 内容: 通常initのscope必須化、empty init、`scope.md`、旧scope移行、scopeと`docs/`構造の非1対1化を反映。
- 根拠: `skills/project-knowledge/`のSkill、references、scripts、tests

## 2026-08-23 scope仕様のナレッジ同期

- 対象: `docs/index.md`と`docs/skill/index.md`
- 内容: 現在のscopeに合わせて入口を修正し、scopeの状態、Information Architectureとの分離、旧scope移行、verifyとauditの評価基準をナレッジ本文へ反映。
- 根拠: `project-knowledge/scope.md`、`skills/project-knowledge/SKILL.md`、関連references、init script
