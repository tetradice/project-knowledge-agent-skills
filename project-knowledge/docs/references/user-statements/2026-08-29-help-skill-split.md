---
type: Reference
pk_source_type: user-statement
generated:
  by: project-knowledge/3.1.0
  at: 2026-08-29T00:00:00+09:00
---

# helpを専用Skillへ分割する方針

`help`をメインの`project-knowledge`から外し、explicit-onlyの`project-knowledge-help`として分離する。

対象なし、対象指定あり、未知対象の出力形式を定型化する。
対象なしでは、基本操作の`inspect`、`init`、`update`、`verify`、`fix`、`config`について、操作名指定での呼び出し方と自然言語例の両方を必ず示す。

`project-knowledge-help`は説明対象を実行せず、read-onlyとする。
`$project-knowledge help`は互換実行せず、新Skillの明示使用を案内する。

`project-knowledge-fast-ask`、`project-knowledge-publish`、`project-knowledge-audit`、`project-knowledge-benchmark`は利用者向け専用Skillとして案内する。
`project-knowledge-scenario-test`は案内に含めない。

既存Skillの版は変更せず、新Skillの版を`1.0.0`とする。
基本操作表の「書き込み」列は表示しない。
