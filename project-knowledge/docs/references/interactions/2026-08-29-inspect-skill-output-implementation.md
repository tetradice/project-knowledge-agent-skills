---
type: Reference
pk_source_type: interaction-record
generated:
  by: project-knowledge/3.1.0
  at: 2026-08-29T11:14:14+09:00
---
# inspect専用Skill化と出力形式変更の実装記録

## 依頼と判断

既存inspectの出力が、利用者向けの概要、構成、統計、更新方針を示す期待形式と異なっていた。
ユーザーは節構成の固定、Knowledge文書だけのツリー、管理ファイルを除いた4区分の件数、Policy frontmatterの自然文説明、inspectの専用Skill化、helpへの反映を求めた。

呼び出し方は、Skill名の明示指定と自然言語の依頼に対応する方針を選択した。
実装開始時に、分離前の呼び出し方に関する記述と、新Skillへの誘導を残さないという追加指示を受けた。

## 実装

`project-knowledge-inspect` 1.0.0を追加し、正常時の固定節、Knowledge文書だけのツリー、referencesの省略境界、4区分の集計、Policy設定の文章化、read-only境界を`SKILL.md`へ集約した。
メインSkillからinspectの操作行、説明、Reference、UI metadata上の責務を削除した。

helpではinspectを基本操作から専用Skillへ移し、README、仕様概要、AGENTSテンプレート、現在のAGENTS、契約テストを新しい責務境界へ合わせた。
既存Skill、Knowledge形式、OKF、state schemaの版は変更していない。

## 検証

対象pytestは56件、リポジトリ全体のpytestは107件が成功した。
`project-knowledge`、`project-knowledge-help`、`project-knowledge-inspect`のSkill validator、Project Knowledge validator、`git diff --check`も成功した。

全pytestの初回起動では、context-modeのJavaScript実行環境が`uv`のbinary pathを解決できず、`mise ERROR cannot find binary path`となった。
同じコマンドをcontext-modeのシェル実行へ切り替えると107件すべて成功したため、実装やテストの問題ではなく実行環境差と判断した。

ユーザーが提示した未追跡の`output.md`と`output_expected.md`は比較資料としてだけ使用し、変更対象へ含めていない。
