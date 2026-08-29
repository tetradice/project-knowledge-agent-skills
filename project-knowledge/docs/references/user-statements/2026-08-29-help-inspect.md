---
type: Reference
pk_source_type: user-statement
generated:
  by: project-knowledge/3.1.0
  at: 2026-08-29T09:42:47+09:00
---

# helpとinspectを追加する方針

`project-knowledge`に、使い方を説明する`help`と、Knowledge Baseの構造と格納情報を説明する`inspect`をread-only操作として追加する。

`help`はメインSkillの操作と、`project-knowledge-fast-ask`、`project-knowledge-publish`、`project-knowledge-audit`、`project-knowledge-benchmark`の使い方を説明できるようにする。
利用者向けではないScenario Testは案内に含めない。

`inspect`は初期化状態、形式、ディレクトリ構造、文書種別、主要カテゴリとトピック、`pk_category`、`pk_derivation`、`pk_source_type`の分布を説明する。
内容の正しさ、鮮度、重複、検索性、改善案は扱わず、`verify`、`audit`、`refactor`を自動実行しない。

Skill版とKnowledge形式版は変更しない。
