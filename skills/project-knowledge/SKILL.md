---
name: project-knowledge
description: Project Knowledgeを初期構築し、プロジェクト・ユーザー指示・会話・Referenceから将来価値のあるKnowledgeを追加・更新・保守する。ナレッジへの反映、初期化、収集方針やlearning設定の変更に使用する。
---

# プロジェクトナレッジ

プロジェクト固有の知識を`project-knowledge/`で育てる。質問回答、成果物生成、網羅的な検証、構造監査は扱わない。

## 操作を選ぶ

ユーザーが求める結果から操作を選び、対応するReferenceだけを読む。明示された操作を優先する。

| 操作 | 選ぶ指示・目印 | 選ばないケース | 読むReference |
| --- | --- | --- | --- |
| `update` | 「ナレッジへ追加・記録・反映・同期」「この会話や判断を覚えて」「実装差分を反映」「何を保存するかという収集方針を変更」「memoを確定情報へ昇格」 | 設定値の表示・変更だけ、生成済みナレッジへの質問だけ | [update.md](references/update.md) |
| `init` | 「プロジェクトナレッジを初期化・導入して」「空で初期化して」「既存プロジェクトから初期ナレッジを作って」 | 初期化済みBundleへの通常の追加・同期 | [init.md](references/init.md) |
| `config` | 「設定を表示・変更・解除して」「learning.mode、自動更新、人間向け文章、publish設定を変えて」 | ナレッジへ何を保存するかという方針変更 | [config.md](references/config.md) |

`capture`と`memo`は内部provenanceとして扱い、ユーザーへ分類選択を求めない。

## 分離した操作

質問回答、公開、検証、監査はそれぞれ`project-knowledge-fast-ask`、`project-knowledge-publish`、`project-knowledge-verify`、`project-knowledge-audit`の責務である。このSkillから自動実行しない。

旧形式の`$project-knowledge ask`、`publish`、`verify`、`audit`を受け取った場合は処理を実行せず、対応する専用Skillを明示的に使用するよう案内する。

## 共通ルール

- 書き込み前に[Knowledge Policy](references/knowledge-policy.md)を読み、プロジェクトの`knowledge-policy.md`へ適用する。秘密情報や一時情報は永続化しない。
- `learning.mode`が自動更新を許可しても、毎ターンではなく作業単位の完了時だけ候補を評価する。詳細は[learning-modes.md](references/learning-modes.md)を読む。
- 既存ファイルを上書き・削除するときは、選択したReferenceの手順に従う。

更新対象を読むときは、`docs/index.md` → 関連カテゴリの`index.md` → 必要な文書 → 必要なReferenceの順に段階的に読む。
