# Knowledge 0.2 data model

通常のKnowledge Conceptは、情報の種類と導出方法を独立した軸で記録する。

```yaml
---
type: Project Knowledge Guide
category: extracted
derivation: synthesized
status: stable
generated:
  by: project-knowledge/0.3.0
  at: 2026-08-26T00:00:00+09:00
sources:
  - resource: ../../README.md
    pk_source_type: project-artifact
---
```

## category

| 値 | 意味 |
| --- | --- |
| `declared` | 人がプロジェクト固有の方針、判断、意図として宣言した情報 |
| `extracted` | Referenceやproject artifactに明示された事実を抽出した情報 |
| `derived` | 複数情報の統合、計算、解釈、推論から得た情報 |

## derivation

| 値 | 意味 |
| --- | --- |
| `direct` | 一つのsourceから意味を変えず直接記録した |
| `synthesized` | 複数のsourceまたは複数箇所を整理・統合した |
| `inferred` | sourceに明記されていない結論を推論した |

`category`と`derivation`は独立して選ぶ。たとえば、複数の設計資料から明示事項を統合したConceptは`category: extracted`かつ`derivation: synthesized`になり得る。

未検証の`derivation: inferred`は`status: draft`にする。後から検証されても、推論から生まれたという来歴は変更しない。

混在するclaimは可能ならConceptを分割する。分割できない場合は、文書全体に最も保守的な`derivation`と`status`を設定し、直接確認できるclaimはsource ID付きfootnote、推論は本文中の表現で区別する。

## Raw Reference

Raw Referenceは次のように記録し、Knowledge分類の対象外とする。

```yaml
---
type: Reference
pk_source_type: reference-document
---
```

Raw Referenceには`category`と`derivation`を付けない。

## Legacy migration

0.1から移行した既存Conceptで分類を根拠なく決められない場合は、`category`と`derivation`を推測せず、`pk_legacy_unclassified: true`を付ける。validatorはwarningとして読み取りを継続する。次にそのConceptを更新するとき、根拠を確認して分類を補完し、このmarkerを削除する。

`state.yml`のschema版は`state_schema_version`で管理する。Knowledge形式版、Skill版、OKF版とは連動させない。
