# メタデータ

## 基本形式

`index.md` と `pending.md` を除くナレッジファイルでは、次の frontmatter を基本とする。

```yaml
---
type: <概念種別>
description: <短い説明>
tags: [<tag>]
sources:
  - id: <安定した識別子>
    resource: <実際に参照した URL またはパス>
generated: { by: <producer>/<version>, at: <UTC の ISO 8601 日時> }
verified:
  - { by: <producer>/<version>, at: <UTC の ISO 8601 日時> }
git_base_commit: "<調査開始時点の完全長 40 文字 Git SHA>"
---
```

## provenance と trust

`sources`、`generated`、`verified` を積極的に使用する。

- `sources`: コンセプトの作成や更新で実際に参照した情報源
- `generated`: コンセプトを新規作成した日時、または本文や frontmatter を意味のある形で更新した日時
- `verified`: 現在のコンセプト全体を `sources` または `resource` と照合した記録

`sources` では次のルールを守る。

- 各項目の `resource` を必須とする。
- 実際に参照した情報源だけを記録する。
- 本文の脚注から情報源を示す場合は、対応する安定した `id` を付ける。
- 情報源がない場合は、推測で補わず `sources` を省略する。

利用先プロジェクトの `project-knowledge/references/` にある trusted raw source を実際に参照した場合も、独自の provenance 形式は作らず `sources` に記録する。
`resource` には bundle ルートからの相対パス（例: `references/requirements/authentication.md`）を記録し、必要な場合は内容を安定して指せる `id` を付ける。
関連しそうという理由だけで、読んでいない資料を記録しない。
資料に秘密値が含まれていても値は転記せず、パス自体が秘密でない場合に限って `resource` を記録する。

`generated.by` と `verified[].by` には、次の actor 形式を使用する。

- エージェント: `<producer>/<version>`
- 人: `human:<id>`
- 自動処理: `process:<id>`

`generated.at` と `verified[].at` は UTC の ISO 8601 日時とする。人による確認の事実がない限り、`human:` の検証を追加しない。

同じ actor が再検証した場合は、その actor の `verified` 項目を最新日時へ更新する。他の actor による項目は保持する。すべての `verified.at` が `generated.at` より古い場合、現在の内容は未検証として扱う。

## Git 基準コミット

`git_base_commit` は OKF の拡張フィールドとする。

- ナレッジの調査前に、bundle を含む Git リポジトリのルートで `HEAD` を取得する。
- 省略形ではなく、完全長 40 文字の SHA を記録する。
- 新規作成または更新するコンセプトだけに記録する。
- 未コミット変更がある場合も、作業ツリーの基準である `HEAD` を記録する。
- `index.md` には記録しない。ルート `index.md` の frontmatter は `okf_version` のみにする。
