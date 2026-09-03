# User Statements

- [ファイル変更報告の表示名](2026-09-03-file-change-reporting-labels.md): 利用者向け分類名を日本語で表示し、`derived`を「分析の結果」とする方針を確認するときに読む。
- [init / updateのファイル変更報告の方針](2026-09-02-file-change-reporting.md): 分類規則の独立化、Support/Internalの非表示・合計除外を確認するときに読む。
- [User Statementの反映ルール](2026-08-31-user-statement-reflection.md): User Statementの追加・更新時に関連Conceptなどへ内容を反映するユーザー指示を確認するときに読む。
- [inspect専用Skillと出力形式の方針](2026-08-29-inspect-skill-output.md): 専用Skillへの分離、自然言語対応、固定節、集計対象、旧記述の削除を確認するときに読む。
- [標準Knowledge PolicyをSkillから参照する方針](2026-08-29-standard-policy-reference.md): 標準Policyの同梱場所、`knowledge-policy.md`の参照形式、プロジェクト固有方針の優先規則を確認するときに読む。
- [Scenario Testの配置方針](2026-08-29-scenario-test-placement.md): 一般ユーザー向けSkillではないScenario Testを開発者向けディレクトリへ分離する理由を確認するときに読む。
- [helpを専用Skillへ分割する方針](2026-08-29-help-skill-split.md): explicit-onlyのhelp、定型出力、旧形式の非互換案内、利用者向け専用Skillの範囲を確認するときに読む。
- [helpとinspectを追加する方針](2026-08-29-help-inspect.md): メインSkillへ追加するread-only操作、利用者向けSkillの案内範囲、verify/auditとの責務境界を確認するときに読む。
- [fixとrefactorを追加する方針](2026-08-26-fix-and-refactor.md): 内容と構造について、検査のみ/検査と修正を分ける操作体系と安全境界を確認するときに読む。
- [verifyを内容健全性検証として具体化する方針](2026-08-26-verify-content-health.md): 7段階の検証順序、結果分類、verifyとaudit・coverage調査の境界を確認するときに読む。
- [verifyをメインスキルへ統合する方針](2026-08-26-verify-in-main-skill.md): 4スキル構成、verifyの読み取り専用境界、updateとの非自動連鎖を確認するときに読む。
- [形式1.0のみを扱う方針](2026-08-26-current-format-only.md): 旧形式の情報と互換処理を削除し、形式1.0だけを扱うユーザー指示を確認するときに読む。
- [Project Knowledge独自metadataのprefix方針](2026-08-26-pk-metadata-prefix.md): OKF標準外の独自metadataへ`pk_`を付けるユーザー指示を確認するときに読む。
- [indexにナレッジを置かない配置ルール](2026-08-26-index-content-boundary.md): reserved indexをナビゲーション専用にする理由とユーザー指示を確認するときに読む。
- [Quickシナリオを使うモデルBenchmarkの方針](2026-08-27-model-benchmark.md): Quick再利用、比較対象、blind Judge、token usageの制約を確認するときに読む。
- [Scenario testのusageとcredit計測方針](2026-08-28-scenario-credit-measurement.md): Quick / BenchmarkのJSONL由来usage、credits、取得不能時の扱いを確認するときに読む。
- [Project Knowledge Utility Benchmarkの方針](2026-08-28-project-knowledge-utility-benchmark.md): 任意Git repositoryのNo-Knowledge / With-Knowledge比較、隔離、評価、結果保持の要件を確認するときに読む。
