---
type: Reference
pk_source_type: user-statement
generated:
  by: project-knowledge/3.1.0
  at: 2026-08-29T11:11:14+09:00
---
# inspect専用Skillと出力形式の方針

inspectを`project-knowledge-inspect`としてメインSkillから分離する。
Skill名の明示指定だけでなく、Knowledge Baseの構造や格納情報を求める自然言語の依頼にも対応する。

正常時の出力は、概要、Knowledge文書だけのフォルダツリー、4区分の統計、Knowledge Policy frontmatterを説明する自然文で構成する。
見出しレベルは読みやすさに応じて調整できるが、節の構成は固定する。
必要な場合だけ末尾に補足節を追加できる。

構成と件数には`index.md`、`log.md`、manifest、state、Knowledge Policyなどの管理用ファイルを含めない。
references外のKnowledge文書は原則省略せず、references内の文書が多すぎる場合だけ省略を許可する。

既存Skillとデータ形式の版は上げない。
分離前の呼び出し方に関する記述や、新Skillへの誘導は残さない。
