---
type: Project Knowledge Data Format
pk_category: declared
pk_derivation: synthesized
status: stable
generated:
  by: project-knowledge/0.4.0
  at: 2026-08-26 12:00:00+09:00
sources:
- resource: ../references/user-statements/2026-08-26-pk-metadata-prefix.md
  pk_source_type: user-statement
- resource: ../references/user-statements/2026-08-26-format-0.2-plan.md
  pk_source_type: user-statement
- resource: ../../../skills/project-knowledge/references/data-formats/0.3.md
  pk_source_type: change-implementation
- resource: ../../../README.md
  pk_source_type: change-implementation
---
# Project Knowledge形式0.3

## 独立した版

各Skillは`SKILL.md`に固有のSemVerを持つ。Knowledge形式版は`manifest.yml`、OKF版はroot `docs/index.md`、state schema版は`state.yml`で別々に管理する。メインSkillの版は`0.4.0`、Knowledge形式は`0.3`、OKFは`0.2`、state schemaは`1`である。

## OKF拡張metadata

OKF標準外のProject Knowledge独自fieldには`pk_` prefixを付ける。分類fieldは`pk_category`、導出方法は`pk_derivation`、source種別は`pk_source_type`とする。OKF fieldである`type`、`status`、`sources`、`generated`、`verified`、`stale`、`stale_after`は改名しない。

`manifest.yml`、`state.yml`、`config.yml`はOKF ConceptのfrontmatterではなくProject Knowledgeの管理ファイルなので、このprefix規約の対象外とする。

## 分類4ケース

| 情報 | pk_category | pk_derivation |
| --- | --- | --- |
| ユーザーが宣言したプロジェクト方針 | `declared` | `direct` |
| 単一artifactに明記された事実 | `extracted` | `direct` |
| 複数artifactの明示事項を統合した説明 | `extracted` | `synthesized` |
| sourceに明記されない推論結果 | `derived` | `inferred` |

未検証のinferenceは`status: draft`とする。検証後も`pk_derivation: inferred`は維持する。User Statementを保存したこととhuman verificationは連動しない。

## Migration

形式0.1はmanifestがなく既知のlegacy構造を持つ場合だけ検出する。形式0.1と0.2から0.3へのmigrationは`--check`、全件競合検査、同一内容統合、pathとmetadataの変換、post-checkを行い、最後にmanifestを書く。分類根拠がない既存Conceptは推測せず、次回更新候補として明示する。

## 実装結果

形式0.2の実装はcommit `45f45b6`で完了した。形式0.3ではProject Knowledge独自metadataの`pk_` prefixをスキーマ、migration、validator、テンプレート、テストへ一貫して導入した。
