---
type: Reference
pk_source_type: user-statement
generated:
  by: project-knowledge/2.0.0
  at: 2026-08-26 01:31:00+09:00
---
# indexにナレッジを置かない配置ルール

`project-knowledge/docs/skill/index.md`はOKFの仕様上frontmatterを持てないため、ナレッジ的な情報を記載すると分類やsourcesを管理できない。

このような状況を防ぐため、reserved `index.md`をナビゲーション専用とし、独立した知識をメタデータ付き通常Conceptへ分離するようSkillを改修する。
