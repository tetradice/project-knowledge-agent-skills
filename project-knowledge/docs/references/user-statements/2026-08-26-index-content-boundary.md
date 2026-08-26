---
type: Reference
pk_source_type: user-statement
generated:
  by: project-knowledge/0.3.0
  at: 2026-08-26 01:31:00+09:00
---
# indexにナレッジを置かない配置ルール

`project-knowledge/docs/skill/index.md`はOKFの仕様上frontmatterを持てないにもかかわらず、ナレッジ的な情報が記載されていた。その結果、`category`や`sources`を記載できず、知識のメタデータを判断できない状態になっていた。

このような状況を防ぐため、reserved `index.md`をナビゲーション専用とし、独立した知識をメタデータ付き通常Conceptへ分離するようSkillを改修する。
