---
type: Legacy Knowledge Migration
pk_category: declared
pk_derivation: synthesized
status: stable
generated:
  by: project-knowledge/3.1.0
  at: 2026-09-14T00:00:00+09:00
sources:
- resource: ../../../skills/project-knowledge/references/init.md
  pk_source_type: change-implementation
- resource: ../references/user-statements/2026-09-14-legacy-knowledge-migration.md
  pk_source_type: user-statement
---

# 未登録の旧来ナレッジを移行する

`project-knowledge.yaml`がないプロジェクトは、既存の`project-knowledge/`ディレクトリや`manifest.yml`から利用対象を推測しない。旧来ナレッジを移行するときだけ、新規`init`の準備と登録を分けて実行する。[利用者の移行要求](../references/user-statements/2026-09-14-legacy-knowledge-migration.md)を根拠にする。

## 移行手順

1. 旧来ナレッジと根拠資料を保全し、`uv run <project-knowledge-skill>/scripts/init_project.py <project-root> --prepare`を実行する。`--prepare`は未登録プロジェクトでのみ使え、形式1.0のBundle骨組みを準備するが、`project-knowledge.yaml`はまだ作成しない。
2. 旧来ナレッジをそのまま移すのではなく、再利用可能な内容を独立Conceptへ整理する。各Conceptには`type`、`pk_category`、`pk_derivation`、`sources`を付け、根拠資料は適切なsource typeで参照する。`index.md`はナビゲーション専用に保つ。
3. 形式・リンク・根拠を確認し、既存Bundleの形式不整合を解消する。既存の`manifest.yml`を自動上書きしない。
4. 準備内容に問題がなければ、同じ`init_project.py <project-root>`を`--prepare`なしで実行する。この最終登録で、`version: "1.0"`の`project-knowledge.yaml`と書き込み可能な`default`レイヤーを作成する。

設定を先に手書きして旧来ディレクトリを登録済みとして扱わず、準備・内容整理・確認の後に登録する。設定の版は利用者が明示しない限り上げない。
