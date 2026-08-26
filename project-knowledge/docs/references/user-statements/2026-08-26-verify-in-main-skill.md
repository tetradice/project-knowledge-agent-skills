---
type: Reference
pk_source_type: user-statement
generated:
  by: project-knowledge/3.0.0
  at: 2026-08-26T15:38:55+09:00
---

# verifyをメインスキルへ統合する方針

`project-knowledge-verify`を廃止し、その読み取り専用の正確性検証を`project-knowledge`の`verify`操作へ統合する。

メインスキルは`init`、`update`、`verify`、`config`でKnowledgeを保守する。`verify`は内容・根拠・鮮度・形式を確認し、通常の質問や開発作業から自動実行しない。`verify`と`update`は暗黙に連鎖させず、両方を明示された場合だけ`update`から`verify`の順に実行する。

`project-knowledge-fast-ask`、`project-knowledge-publish`、`project-knowledge-audit`は独立Skillとして維持する。`audit`は重複、肥大化、分断、ナビゲーション、検索性、情報設計を担当する。
