---
type: Reference
pk_source_type: user-statement
generated:
  by: project-knowledge/3.0.0
  at: 2026-08-26T17:57:49+09:00
---

# verifyを内容健全性検証として具体化する方針

`verify`は、Knowledgeに記録された内容が、示された根拠と現在のプロジェクト状態に照らして現在も成立するかをread-onlyで検証する。形式、source、provenance、根拠、現在状態、鮮度、Knowledge間の意味的整合性の順に確認する。

結果は`pass`、`fail`、`warning`、`not-verifiable`、`stale`、`not-applicable`を区別する。検証不能を成功・失敗へ無理に分類せず、`declared`な方針と実装の差異はimplementation driftとして扱う。検証後も`inferred`などのprovenanceを書き換えない。

重複、肥大化、分断、検索性などKnowledge Baseの構造健全性は`audit`、未登録Knowledgeのcoverage調査はupdateまたはdiscovery側へ委ねる。verifyからupdate、audit、publishを自動実行せず、問題を検出しても自動修正しない。
