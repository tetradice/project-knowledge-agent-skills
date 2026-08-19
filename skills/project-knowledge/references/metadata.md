# メタデータ

`index.md` と `pending.md` を除くコンセプトファイルでは、次の frontmatter を基本とする。

```yaml
---
type: <概念種別>
description: <短い説明>
tags: [<tag>]
sources:
  - id: <安定した識別子>
    resource: <URLまたはbundleルートからの相対パス>
generated: { by: <actor>, at: <UTC の ISO 8601 日時> }
verified:
  - { by: <actor>, at: <UTC の ISO 8601 日時> }
git_base_commit: "<調査開始時点の完全長 Git SHA>"
---
```

情報源がない場合は `sources`、照合していない場合は `verified`、Git SHA を取得できない場合は `git_base_commit` を省略する。

## provenance

- `sources`: コンセプト内の主張を根拠づけるために参照した情報源
- `generated`: コンセプトを作成した日時、または内容を意味のある形で更新した日時
- `verified`: コンセプト全体を情報源と照合した記録

`sources[].resource` を必須とし、実際に参照した情報源だけを追加する。
脚注から参照する項目には安定した `id` を付ける。
更新時は、残る主張を支える既存の情報源を、今回読み直していないという理由だけで削除しない。
情報源がどの主張も支えなくなった場合だけ削除する。

`project-knowledge/references/` の資料を参照した場合は、`resource` にbundleルートからの相対パスを記録する。
資料に秘密値が含まれる場合も、値は転記しない。

## actor と時刻

actor には次の形式を使用する。

- エージェント: `<producer>/<version>`
- 人: `human:<id>`
- 自動処理: `process:<id>`

時刻は UTC の ISO 8601 形式とする。
人が確認した事実がない限り、`human:` の検証を追加しない。

同じ actor が再検証した場合は、その actor の `verified` を最新日時へ更新し、他の actor による項目は保持する。
すべての `verified.at` が `generated.at` より古い場合は未検証として扱う。
検証記録だけを更新する場合は `generated` を変更しない。

## Git 基準コミット

Git リポジトリで `HEAD` を取得できる場合だけ、調査開始時点の完全長40文字 SHA を `git_base_commit` に記録する。
未コミット変更がある場合も、作業ツリーの基準である `HEAD` を使用する。
新規作成または更新するコンセプトだけを変更し、`index.md` には記録しない。
