---
type: Project Knowledge Data Format
pk_category: declared
pk_derivation: synthesized
status: stable
generated:
  by: project-knowledge/3.1.0
  at: 2026-08-29T10:46:55+09:00
sources:
- resource: ../references/user-statements/2026-08-26-current-format-only.md
  pk_source_type: user-statement
- resource: ../references/user-statements/2026-08-29-standard-policy-reference.md
  pk_source_type: user-statement
- resource: ../../../skills/project-knowledge/references/data-formats/1.0.md
  pk_source_type: change-implementation
- resource: ../../../skills/project-knowledge/references/standard-knowledge-policy.md
  pk_source_type: change-implementation
- resource: ../../../skills/project-knowledge/scripts/validate_knowledge.py
  pk_source_type: change-implementation
- resource: ../../../skills/project-knowledge-publish/references/publishing.md
  pk_source_type: change-implementation
---
# Project Knowledge形式1.0

## 管理ファイル

- `manifest.yml`: `format: project-knowledge`と`format_version: "1.0"`を宣言する。
- `knowledge-policy.md`: frontmatterに運用設定、本文にSkill同梱の標準Policyへの参照と任意のプロジェクト固有方針を持つ。
- `state.yml`: 増分更新用の再構築可能なworking copy固有状態を保持する。

形式1.0以外は読み書きしない。manifestがない、壊れている、形式名または版が異なる場合は処理を停止する。

## Policy frontmatter

`knowledge.human_readable`はboolean、`learning.mode`は`manual`、`opportunistic`、`aggressive`のいずれかとする。本文はAgent Skill `project-knowledge`同梱の`references/standard-knowledge-policy.md`を参照し、プロジェクト固有方針がある場合はそれを標準Policyより優先する。設定変更は既知キーだけを更新し、本文、コメント、未知キーを保持する。不正なfrontmatterは自動修復しない。

## OKF bundle

`docs/`はOKF v0.2 bundleである。root `index.md`だけが`okf_version: "0.2"`を持ち、その他のindexとlogはfrontmatterを持たない。通常Conceptは`type`、`pk_category`、`pk_derivation`、`generated`を持ち、sourceには`resource`と`pk_source_type`を記録する。

## Publish境界

publishは既定でMarkdownとMaterial for MkDocsによるoffline HTMLを生成する。出力形式と対象範囲は実行時だけ指定でき、Knowledge Baseへ永続化しない。
