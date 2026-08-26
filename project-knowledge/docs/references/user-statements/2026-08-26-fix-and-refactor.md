---
type: Reference
pk_source_type: user-statement
generated:
  by: project-knowledge/3.1.0
  at: 2026-08-26T21:21:07+09:00
---

# fixとrefactorを追加する方針

Knowledge内容の正しさについて、`verify`は読み取り専用の検査、`fix`は同じ観点で検査して明白な問題を修正し、再検査する操作とする。`fix`は古い内容、sourceとの不整合、stale、参照、frontmatter、metadata、manifestとの不整合などを保守的に直し、新しい情報や変更を反映する`update`とは区別する。

Knowledge Baseの構造・品質について、`project-knowledge-audit`の`audit`は読み取り専用の診断、`refactor`は同じ観点で診断して構造を改善し、再診断する操作とする。`refactor`は意味・情報・source・provenanceを維持し、大規模または主観的な再設計を勝手に行わない。

`verify`から`fix`、`audit`から`refactor`へ自動昇格しない。書き込みはユーザーが`fix`または`refactor`を明示的に意図した場合だけ行う。`project-knowledge-audit`はexplicit-onlyを維持し、一般的な「整理して」「改善して」から自動実行しない。
