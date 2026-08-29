---
name: project-knowledge-inspect
description: Project Knowledgeの構造、格納情報、文書数、更新方針をread-onlyで説明する。$project-knowledge-inspectの明示指定、またはKnowledge Baseの構造や内容の概要を求める自然言語の依頼で使用する。
metadata:
  version: "1.0.0"
---

# Project Knowledge Inspect

現在のProject Knowledgeを読み取り、利用者向けの概要を返すread-only Skillである。
内容の正確性、鮮度、構造品質、改善方法は評価せず、ファイルを作成、更新、削除しない。

## 読み取り前の確認

1. `project-knowledge/manifest.yml`の有無を確認する。
2. manifestが`format: project-knowledge`かつ`format_version: "1.0"`であることを確認する。
3. 未初期化の場合は、その状態だけを報告して読み取りを止める。
4. manifestが壊れている場合や未対応形式の場合は、安全に解釈できないことだけを報告して読み取りを止める。

## 読み取り範囲

次の順で、出力に必要な範囲だけを読む。

1. `manifest.yml`と`knowledge-policy.md`のfrontmatter
2. `docs/index.md`と、そこから到達できるnested `index.md`
3. Knowledge文書のfrontmatter、見出し、index上の説明

Project Knowledge外のソースコードや設定、Knowledgeが参照するsource本文は調査しない。
Raw ReferenceやInteraction Recordの本文を大量に転記しない。

## 出力形式

正常なBundleでは、次の節をこの順序で出力する。
見出しレベルは、出力全体が読みやすくなるよう調整してよいが、節の名前と順序は変えない。
補足が必要な場合だけ、末尾に`補足`節を追加できる。

1. `プロジェクトナレッジ情報`
2. `概要`
3. `構成`
4. `詳細`
5. `統計情報`
6. `ナレッジベースの更新方針`

`統計情報`と`ナレッジベースの更新方針`は`詳細`の配下に置く。

### 概要

indexの説明、Knowledge文書の見出し、要約から、格納している情報の大枠を1〜2文で説明する。
ファイル構成やmetadataの列挙ではなく、利用者がKnowledge Baseの対象領域を把握できる文章にする。

### 構成

Knowledgeとして意味のあるMarkdown文書だけを、`project-knowledge/docs/`からのフォルダツリー形式で表示する。
各文書は可能な限り相対リンクにし、index上の説明があれば短く添える。

次の管理用ファイルやナビゲーション用ファイルは表示しない。

- rootおよびnested `index.md`
- rootおよびnested `log.md`
- `manifest.yml`、`state.yml`、`knowledge-policy.md`
- `published/`、`.cache/`などの生成物・作業用ディレクトリ

`docs/references/`以外のKnowledge文書は原則として省略しない。
`docs/references/`内で同種の文書が10件を超える場合は、先頭10件までを表示し、残りを`ほかN件`と示す。

### 統計情報

次の表を出力する。

| 種別 | 件数 |
| --- | ---: |
| 過去のやり取りの記録（interactions） | `<件数>` |
| ユーザーからの指示の記録（user-statements） | `<件数>` |
| 上記以外の参考資料 | `<件数>` |
| 作成ナレッジ文書 | `<件数>` |
| 合計 | `<上記4区分の合計>` |

件数には`index.md`、`log.md`、管理用ファイルを含めない。
`docs/references/interactions/`をinteractions、`docs/references/user-statements/`をuser-statements、`docs/references/`内の残りをその他の参考資料、`docs/references/`外のKnowledge文書を作成ナレッジ文書として数える。
分類できない文書を推測で割り当てず、必要なら補足節で説明する。

### ナレッジベースの更新方針

`knowledge-policy.md`のfrontmatterにある設定を、利用者が意味を理解できる文章へ変換する。
各項目には設定キーと実値を併記し、最後に`knowledge-policy.md`への相対リンクを付ける。

- `knowledge.human_readable: true`: 人がそのまま読みやすい文章を優先して記録する。
- `knowledge.human_readable: false`: 人間向けの読みやすさより、AIの検索効率、簡潔さ、構造、重複回避を優先して記録する。
- `learning.mode: manual`: 明示的な更新依頼があった場合だけ、Knowledgeへの反映候補を評価する。
- `learning.mode: opportunistic`: 作業単位の完了時に、将来価値のある重要な変更があればKnowledgeへの反映候補を評価する。
- `learning.mode: aggressive`: 作業単位の完了時に候補を広めに評価するが、一時情報や重複は除外する。

未知値や解析不能な値は意味を推測せず、観測した値と説明できない旨を示す。

## 操作の境界

内容が実装と一致するかを検証せず、重複、肥大化、分断、検索性を診断しない。
問題らしい状態を見つけてもfindingに格付けせず、検証、監査、修正、構造改善を自動実行しない。
