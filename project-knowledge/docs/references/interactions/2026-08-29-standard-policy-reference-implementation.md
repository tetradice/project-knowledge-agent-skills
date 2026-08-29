---
type: Reference
pk_source_type: interaction-record
generated:
  by: project-knowledge/3.1.0
  at: 2026-08-29T10:59:23+09:00
---

# 標準Knowledge Policy参照化の実装記録

利用者は、`knowledge-policy.md`の本文を標準Policyへの宣言とSkill同梱Referenceの参照情報だけにし、外部URLを使わないことを求めた。

既存のプロジェクト固有方針を本文へ保持する機能との関係を確認し、固有方針が提示された場合はそれを先に置き、未指定部分に標準Policyを適用するフォールバックを記載する形に決定した。validatorは新しい本文構造を必須化せず、自由形式本文を許容し続ける。

テンプレートの標準Policy本文を`skills/project-knowledge/references/standard-knowledge-policy.md`へ移し、テンプレートとこのrepositoryの`project-knowledge/knowledge-policy.md`は標準Policyに従う宣言と`references/standard-knowledge-policy.md`への参照だけを持つ形に変更した。更新・初期化・形式・仕様資料と関連Knowledgeも同じモデルへ同期した。

`skills/project-knowledge/tests`のpytestは56件、変更したテストのRuff、Project Knowledge validator、`git diff --check`がすべてPASSした。実装commitは`7eab9f5`であり、Git baselineはそのHEADへ更新した。

この後の`update`で差分検出を行った時点では、ユーザー管理の未追跡`output.md`と`output_expected.md`だけが変更候補であり、どちらもこの方針変更とは無関係なため更新対象から除外した。
