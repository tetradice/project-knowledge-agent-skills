# プロジェクトナレッジについて

ナレッジ: `project-knowledge/index.md`

ルール:

- プロジェクト情報が必要な場合は、Agent Skill `$project-knowledge` に従う。
- ナレッジの検証は、Agent Skill `$project-knowledge check` に従う。
- ナレッジの更新と最新化は、Agent Skill `$project-knowledge update` に従う。
- 通常の実装変更だけを理由にナレッジを更新しない。
- 秘密情報や `.env` の値をナレッジへ保存しない。
