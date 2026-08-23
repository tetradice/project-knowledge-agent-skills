---
name: project-knowledge
description: プロジェクトルートの`project-knowledge/`にプロジェクト固有の知識を蓄積し、初期化・更新・照会・設定・公開・検証・整理する。
---

# プロジェクトナレッジ

プロジェクト固有の知識を`project-knowledge/`で管理する。

## 操作を選ぶ

ユーザーが求める結果から操作を選び、対応するReferenceだけを読む。明示された操作を優先する。

| 操作 | 選ぶ指示・目印 | 選ばないケース | 読むReference |
| --- | --- | --- | --- |
| `update` | 「ナレッジへ追加・記録・反映・同期」「この会話や判断を覚えて」「実装差分を反映」「何を保存するかという収集方針を変更」「memoを確定情報へ昇格」 | 設定値の表示・変更だけ、生成済みナレッジへの質問だけ | [update.md](references/update.md) |
| `ask` | 「プロジェクトナレッジによると？」「ナレッジだけを根拠に答えて」「ナレッジに記載がある？」 | ソースコード、Web、一般知識も使う通常の調査や質問 | [ask.md](references/ask.md) |
| `init` | 「プロジェクトナレッジを初期化・導入して」「空で初期化して」「既存プロジェクトから初期ナレッジを作って」 | 初期化済みBundleへの通常の追加・同期 | [init.md](references/init.md) |
| `publish` | 「人間向けドキュメントを生成・再生成・公開して」「Markdown/HTMLへ出力して」 | ナレッジ本文そのものの追加・修正 | [publishing.md](references/publishing.md) |
| `verify` | 「整合性・リンク・source・鮮度・矛盾を検証して」「壊れていないか確認して」 | 重複削減や構成整理が主目的の依頼。検査はread-onlyで、修正は含めない | [verification.md](references/verification.md) |
| `audit` | 「肥大化・重複・古い情報・不要Referenceを監査して」「Information Architectureや整理候補を見て」 | 正しさやリンク切れだけの検証。初回監査はread-only | [audit.md](references/audit.md) |
| `config` | 「設定を表示・変更・解除して」「learning.mode、自動更新、人間向け文章、publish設定を変えて」 | ナレッジへ何を保存するかという方針変更 | [config.md](references/config.md) |

複数の結果を求められた場合は操作を順に併用する。「検査して修正」「監査して整理」では、先に`verify`または`audit`で対象を特定し、修正が明示されている場合だけ書き込み手順へ進む。実行順を決められない場合だけ確認する。

## 共通ルール

- 書き込み前に[ナレッジ Policy](references/knowledge-policy.md)を読み、プロジェクトの`knowledge-policy.md`へ適用する。秘密情報や一時情報は永続化しない。
- `learning.mode`が自動更新を許可しても、毎ターンではなく作業単位の完了時だけ候補を評価する。詳細は[learning-modes.md](references/learning-modes.md)を読む。
- 既存ファイルを上書き・削除するときは、選択したReferenceの手順に従う。

## 読み方

ナレッジを読むときは、`docs/index.md` → 関連カテゴリの`index.md` → 必要な文書 → 必要なReferenceの順に段階的に読む。
