---
name: project-knowledge
description: プロジェクトルートの project-knowledge/ に配置するプロジェクトナレッジに知識を集積するスキル。プロジェクトナレッジの初期化・追加・更新・照会・設定・公開・検証・整理を扱う。
---

# プロジェクトナレッジ

プロジェクト固有の仕様、実装、判断、運用知識を`project-knowledge/`へ保守する。ユーザーは情報源の種類を選ばず、ナレッジへ反映したいintentだけを示せばよい。

## 操作を選ぶ

operationはCLIサブコマンドではなく、ユーザーが求める結果から選ぶ。明示された操作を優先し、操作名がなくても次の目印でルーティングする。選択後は対応するReferenceだけを読む。

| 操作 | 選ぶ指示・目印 | 選ばないケース | 読むReference |
| --- | --- | --- | --- |
| `update` | 「ナレッジへ追加・記録・反映・同期」「この会話や判断を覚えて」「実装差分を反映」「何を保存するかという収集方針を変更」「memoを確定情報へ昇格」 | 設定値の表示・変更だけ、生成済みナレッジへの質問だけ | [update.md](references/update.md) |
| `ask` | 「プロジェクトナレッジによると？」「ナレッジだけを根拠に答えて」「ナレッジに記載がある？」 | ソースコード、Web、一般知識も使う通常の調査や質問 | [ask.md](references/ask.md) |
| `init` | 「プロジェクトナレッジを初期化・導入して」「空で初期化して」「既存プロジェクトから初期ナレッジを作って」 | 初期化済みBundleへの通常の追加・同期 | [init.md](references/init.md) |
| `publish` | 「人間向けドキュメントを生成・再生成・公開して」「Markdown/HTMLへ出力して」 | ナレッジ本文そのものの追加・修正 | [publishing.md](references/publishing.md) |
| `verify` | 「整合性・リンク・source・鮮度・矛盾を検証して」「壊れていないか確認して」 | 重複削減や構成整理が主目的の依頼。検査はread-onlyで、修正は含めない | [verification.md](references/verification.md) |
| `audit` | 「肥大化・重複・古い情報・不要Referenceを監査して」「Information Architectureや整理候補を見て」 | 正しさやリンク切れだけの検証。初回監査はread-only | [audit.md](references/audit.md) |
| `config` | 「設定を表示・変更・解除して」「learning.mode、自動更新、人間向け文章、publish設定を変えて」 | ナレッジへ何を保存するかという方針変更 | [config.md](references/config.md) |

迷う場合は、次の境界で決める。

- ナレッジの内容または`knowledge-policy.md`を変えるなら`update`、Skillの動作を制御する設定値を変えるなら`config`を選ぶ。
- ナレッジを根拠に質問へ答えるなら`ask`、ナレッジ自体の品質を検査するなら`verify`または`audit`を選ぶ。
- 正確性、整合性、鮮度、リンク、sourceの問題を探すなら`verify`、量、重複、粒度、構成、整理候補を探すなら`audit`を選ぶ。
- 公開用成果物を作るだけなら`publish`を選ぶ。公開物からナレッジへ逆同期しない。
- 「検査して修正」「監査して整理」のような複合指示では、先に`verify`または`audit`で対象を特定し、修正まで明示されている場合だけ対応する書き込み手順へ進む。
- 複数の結果が明示されている場合は操作を併用する。たとえば「更新して検証」は`update`→`verify`、「設定を変えて再生成」は`config`→`publish`とする。実行順が結果を変えるのに指示から決められない場合だけ確認する。

次のintentはすべて`update`へルーティングする。

- 情報や仕様をナレッジへ追加・更新したい
- 今回の会話や設計判断を覚えさせたい
- 実装変更をナレッジへ反映したい
- 今後の収集方針を変えたい
- memoを確定情報へ昇格したい

旧`capture`と`memo`の指定は互換入力として`update`へ、旧`scope`の表示・変更は`knowledge-policy.md`の表示・更新へ読み替える。新しい操作として案内しない。

## 共通ルール

- 書き込み前に[ナレッジ Policy](references/knowledge-policy.md)を読み、プロジェクトの`knowledge-policy.md`へ適用する。
- 対象領域は固定しない。将来利用価値が高くPolicyに反しなければ、新しいページやカテゴリを追加してよい。
- 明示的な保存指示は強いシグナルとして扱うが、秘密情報、一時情報、危険または保存不適切な情報は永続化しない。
- captureとmemoは操作ではなく内部provenanceである。必要な場合だけReferenceを作り、ナレッジ本文を複製しない。詳細は[provenance.md](references/provenance.md)を読む。
- updateは変更範囲と関連ナレッジを中心にIncrementalに行い、毎回プロジェクト全体を再解析しない。
- `learning.mode`が自動更新を許可しても、毎ターンではなく作業単位の完了時だけ候補を評価する。詳細は[learning-modes.md](references/learning-modes.md)を読む。
- `docs/`のInformation Architectureは、情報の関係、検索効率、Progressive Disclosure、人間の読みやすさを基準に設計する。
- capture原文、既存Reference、既存設定を不用意に上書き・削除しない。

## 読み方

ナレッジを読むときは、`docs/index.md` → 関連カテゴリの`index.md` → 必要な文書 → 必要なReferenceの順に段階的に読む。
