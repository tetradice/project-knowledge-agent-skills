# User Statements

- [fixとrefactorを追加する方針](2026-08-26-fix-and-refactor.md): 内容と構造について、検査のみ/検査と修正を分ける操作体系と安全境界を確認するときに読む。
- [verifyを内容健全性検証として具体化する方針](2026-08-26-verify-content-health.md): 7段階の検証順序、結果分類、verifyとaudit・coverage調査の境界を確認するときに読む。
- [verifyをメインスキルへ統合する方針](2026-08-26-verify-in-main-skill.md): 4スキル構成、verifyの読み取り専用境界、updateとの非自動連鎖を確認するときに読む。
- [形式1.0のみを扱う方針](2026-08-26-current-format-only.md): 旧形式の情報と互換処理を削除し、形式1.0だけを扱うユーザー指示を確認するときに読む。
- [Project Knowledge独自metadataのprefix方針](2026-08-26-pk-metadata-prefix.md): OKF標準外の独自metadataへ`pk_`を付けるユーザー指示を確認するときに読む。
- [indexにナレッジを置かない配置ルール](2026-08-26-index-content-boundary.md): reserved indexをナビゲーション専用にする理由とユーザー指示を確認するときに読む。
- [Quickシナリオを使うモデルBenchmarkの方針](2026-08-27-model-benchmark.md): Quick再利用、比較対象、blind Judge、token usageの制約を確認するときに読む。
- [Scenario testのusageとcredit計測方針](2026-08-28-scenario-credit-measurement.md): Quick / BenchmarkのJSONL由来usage、credits、取得不能時の扱いを確認するときに読む。
- [Project Knowledge Utility Benchmarkの方針](2026-08-28-project-knowledge-utility-benchmark.md): 任意Git repositoryのNo-Knowledge / With-Knowledge比較、隔離、評価、結果保持の要件を確認するときに読む。
