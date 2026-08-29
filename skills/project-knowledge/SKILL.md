---
name: project-knowledge
description: Project Knowledgeを初期構築し、将来価値のあるKnowledgeの追加・更新、内容・根拠・鮮度・形式の検証と修正、収集方針やlearning設定の変更を行う。Project Knowledgeの保守、初期化、明示的な検証・修正依頼に使用する。
metadata:
  version: "3.1.0"
---

# プロジェクトナレッジ

プロジェクト固有の知識を`project-knowledge/`で構築・更新・検証・修正・設定し、正しい状態に保つ。利用案内、Knowledge Baseの説明、Knowledgeを根拠とする質問回答、成果物生成、構造監査・構造改善は扱わない。

## 操作を選ぶ

ユーザーが求める結果から操作を選び、対応するReferenceだけを読む。明示された操作を優先する。

| 操作 | 選ぶ指示・目印 | 選ばないケース | 読むReference |
| --- | --- | --- | --- |
| `init` | 「プロジェクトナレッジを初期化・導入して」「空で初期化して」「既存プロジェクトから初期ナレッジを作って」 | 初期化済みBundleへの通常の追加・同期 | [init.md](references/init.md) |
| `update` | 「ナレッジへ追加・記録・反映・同期」「この会話や判断を覚えて」「実装差分を反映」「検証結果を反映」「何を保存するかという収集方針を変更」 | 設定値の表示・変更だけ、生成済みナレッジへの質問だけ | [update.md](references/update.md) |
| `verify` | 「Project Knowledgeを検証して」「現在の実装と一致するか確認して」「内容・根拠・鮮度・形式を確認して」 | 通常の質問、通常の開発作業、実装レビュー、未登録情報のcoverage調査、構造や情報設計の監査 | [verification.md](references/verification.md) |
| `fix` | 「Project Knowledgeの問題を修正して」「Project Knowledgeをfixして」「ナレッジの間違いや古い情報を直して」 | 検査・報告だけ、単なる新情報の追加、Concept統合・分割やKnowledge階層の再設計 | [fix.md](references/fix.md) |
| `config` | 「設定を表示・変更・解除して」「learning.mode、自動更新、人間向け文章を変えて」 | ナレッジへ何を保存するかという方針変更、publish実行方式の指定 | [config.md](references/config.md) |

ユーザーへ`pk_category`、`pk_derivation`、source typeの選択を求めず、入力と根拠から自動判定する。

`verify`は明示的に検証を意図した依頼でだけ選び、read-onlyで確認する。`fix`は既存Knowledgeの具体的な問題を検査して修正する意図が明示された場合だけ選ぶ。単なる`verify`依頼を`fix`へ昇格させない。重複、肥大化、分断、検索性などKnowledge Baseの構造品質と改善は`project-knowledge-audit`へ委ねる。

`update`は新しい知識や変更を反映し、`fix`は既存Knowledgeの問題を検査して正す。操作は自動連鎖しない。`update`後に`verify`を自動実行せず、`verify`で問題を見つけても`fix`や`update`を自動実行しない。「更新して、その後検証して」のように複数操作を明示された場合だけ、指定順に実行する。`fix`内の再検査は同じ操作の完了条件であり、別の`verify`を自動実行することではない。

## 分離した操作

利用案内、Knowledge Baseの説明、Knowledge限定回答、公開、構造監査・構造改善、Knowledgeなし・ありの実務比較はそれぞれ`project-knowledge-help`、`project-knowledge-inspect`、`project-knowledge-fast-ask`、`project-knowledge-publish`、`project-knowledge-audit`、`project-knowledge-benchmark`の責務である。このSkillから自動実行しない。

`$project-knowledge help`、`ask`、`publish`、`audit`、`refactor`、`benchmark`を受け取った場合は処理を実行せず、対応する専用Skillを明示的に使用するよう案内する。`help`には`$project-knowledge-help`を案内し、互換実行しない。`verify`と`fix`はこのSkillの各操作として実行する。

## 共通ルール

- 書き込み前に[Knowledge Policy](references/knowledge-policy.md)を読み、プロジェクトの`knowledge-policy.md`へ適用する。秘密情報や一時情報は永続化しない。
- 書き込み前に[Format 1.0](references/data-formats/1.0.md)を読み、形式1.0以外へは書き込まない。
- `learning.mode`が自動更新を許可しても、毎ターンではなく作業単位の完了時だけ候補を評価する。詳細は[learning-modes.md](references/learning-modes.md)を読む。
- root・nested `index.md`はナビゲーション専用とする。独立して再利用できる知識は通常Conceptへ分離し、frontmatterで分類と根拠を保持する。
- 既存ファイルを上書き・削除するときは、選択したReferenceの手順に従う。

更新対象を読むときは、`docs/index.md` → 関連カテゴリの`index.md` → 必要な文書 → 必要なReferenceの順に段階的に読む。
