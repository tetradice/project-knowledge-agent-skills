---
type: Reference
pk_source_type: user-statement
generated:
  by: project-knowledge/3.1.0
  at: 2026-09-14T20:41:27+09:00
---

# 複数レイヤーと必須表示名の方針

利用者は、`version: "1.0"`を維持したまま任意数のProject Knowledgeレイヤーを扱えるよう求めた。一般的な構成は個人用、チーム用、公開用の3レイヤーとし、更新先は常に1レイヤー、参照は全レイヤーを対象とする。

各レイヤーでは不変の機械識別子`id`を維持し、AIと利用者の呼称として必須の`name`を追加する。AIは`name`を表示と自然言語選択に使い、`id`はCLI、根拠、state、キャッシュに使う。公開用のように曖昧な依頼から自動選択したくないレイヤーには`auto_select: false`を設定し、明確な`name`または`id`指定はこの除外を上書きして選択できる。
