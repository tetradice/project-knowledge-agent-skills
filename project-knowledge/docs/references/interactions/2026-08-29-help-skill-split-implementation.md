---
type: Reference
pk_source_type: interaction-record
generated:
  by: project-knowledge/3.1.0
  at: 2026-08-29T00:00:00+09:00
---

# help専用Skill化の実装記録

利用者の要望に基づき、メインSkillの`help`操作を`project-knowledge-help`へ分離した。
新Skillは`SKILL.md`と`agents/openai.yaml`だけを持つ自己完結したexplicit-only Skillとし、版は`1.0.0`とした。

対象なしの出力は、`# Project Knowledge Help`、`## 基本操作`、`## 専用Skill`、`## 詳細ヘルプ`の順に固定した。
基本操作表には`操作`、`用途`、`操作名指定`、`自然言語例`を置き、6操作すべての呼び出し例を記載した。
対象指定ありと未知対象では、用途、書き込み、呼び出し方、主な結果、対象外の順で出力する。

メインSkillから`help`操作と`references/help.md`を削除し、旧形式の`$project-knowledge help`は新Skillを案内するだけにした。
README、仕様概要、UI metadata、初期化時のAGENTSテンプレート、契約テストを新しい6 Skill構成へ同期した。

`pytest`で`skills/project-knowledge/tests`を実行し、55件がPASSした。
両Skillのvalidatorと`git diff --check`もPASSした。
実装commitは`83077c9`であり、その後の「書き込み」列削除は`d716df6`である。
