---
type: Reference
pk_source_type: user-statement
generated:
  by: project-knowledge/3.1.0
  at: 2026-08-27T00:00:00+09:00
---
# Quickシナリオを使うモデルBenchmarkの方針

既存のProject Knowledge Quickシナリオテストを再利用し、同一のQuick FixtureとActor依頼でGPT-5.6 Luna、Terra、SolのKnowledge Base構築結果を比較する。

比較ではdeterministic validation、固定かつblindなJudge、共通の6評価観点、Actor token usage、Knowledge Base統計を用いる。token usageは実測値だけを扱い、取得不能な項目は推定しない。Full scenario、複数回実行、pairwise Judge、複数Judgeは対象外とする。
