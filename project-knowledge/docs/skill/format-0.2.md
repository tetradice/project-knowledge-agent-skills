---
type: Project Knowledge Data Format
category: declared
derivation: synthesized
status: stable
generated:
  by: project-knowledge/0.3.0
  at: 2026-08-26T01:31:00+09:00
sources:
  - resource: ../references/user-statements/2026-08-26-format-0.2-plan.md
    pk_source_type: user-statement
  - resource: ../../../skills/project-knowledge/references/data-formats/0.2.md
    pk_source_type: change-implementation
  - resource: ../../../README.md
    pk_source_type: change-implementation
---

# Project Knowledge形式0.2

## 独立した版

各Skillは`SKILL.md`に固有のSemVerを持つ。Knowledge形式版は`manifest.yml`、OKF版はroot `docs/index.md`、state schema版は`state.yml`で別々に管理する。メインSkillの版は`0.3.0`、Knowledge形式は`0.2`、OKFは`0.2`、state schemaは`1`である。

## 分類4ケース

| 情報 | category | derivation |
| --- | --- | --- |
| ユーザーが宣言したプロジェクト方針 | `declared` | `direct` |
| 単一artifactに明記された事実 | `extracted` | `direct` |
| 複数artifactの明示事項を統合した説明 | `extracted` | `synthesized` |
| sourceに明記されない推論結果 | `derived` | `inferred` |

未検証のinferenceは`status: draft`とする。検証後も`derivation: inferred`は維持する。User Statementを保存したこととhuman verificationは連動しない。

## Migration

形式0.1はmanifestがなく既知のlegacy構造を持つ場合だけ検出する。migrationは`--check`、全件競合検査、同一内容統合、pathとmetadataの変換、post-checkを行い、最後にmanifestを書く。分類根拠がない既存Conceptは推測せず、次回更新候補として明示する。

## 実装結果

形式0.2の実装はcommit `45f45b6`で完了した。pytestは36件、全5 Skillのquick validation、repository自身のKnowledge validator、migrationの再実行check、Ruff、差分検査がすべて成功した。
