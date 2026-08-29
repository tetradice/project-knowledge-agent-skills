---
type: Reference
pk_source_type: interaction-record
generated:
  by: project-knowledge/3.1.0
  at: 2026-08-29T09:42:47+09:00
---

# helpとinspectの実装記録

利用者の要望に基づき、`project-knowledge`へ`help`と`inspect`を追加した。
両方を個別の専用Skillではなく、メインSkillのread-only操作として実装した。

`help`はメイン操作と利用者向け4 Skillを説明する。
`project-knowledge-scenario-test`は利用者向けの案内から除外した。
`inspect`は`project-knowledge/`だけを段階的に読み、初期化状態、形式、構造、文書種別、カテゴリ、トピック、provenance分類、運用設定を説明する。
内容の正しさは`verify`、構造品質は`audit`、構造改善は`refactor`の責務として維持した。

`SKILL.md`、UI metadata、README、仕様概要、契約テストを更新し、`references/help.md`と`references/inspect.md`を追加した。
Skill版は3.1.0、Knowledge形式版は1.0のままとした。

Skill validatorはPASSした。
既定のPython環境には`pytest`がなかったため、`uv`の一時環境へ`pytest`とPyYAMLを解決して`skills/project-knowledge/tests`を実行し、52件がPASSした。
実装はcommit `f28a60a`として保存した。
