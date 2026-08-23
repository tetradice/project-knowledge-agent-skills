# Architecture

`project-knowledge/knowledge-policy.md`は何を保存する価値があるかという収集・品質方針である。`project-knowledge/docs/`は、その情報をどう整理するかというInformation Architectureであり、OKF v0.2 ナレッジ Bundleかつ唯一のナレッジ本体である。対象領域や文書構造は固定しない。

```text
project-knowledge/
├─ docs/
│  ├─ index.md
│  ├─ log.md
│  ├─ <必要なページまたはカテゴリ>
│  └─ references/{index.md,captures/index.md,memos/index.md}
├─ knowledge-policy.md
├─ config.yml
├─ config.local.yml
├─ state.yml
├─ published/{markdown,html}/
├─ .cache/
└─ .gitignore
```

Skillが固定する`docs/`構造は`index.md`、`log.md`、`references/captures/`、`references/memos/`までとする。`overview/`、`development/`、`architecture/`、`operations/`などをinit時に一律作成しない。

ページとカテゴリは、プロジェクトの性質・規模、情報同士の関係、利用者の探索経路、Progressive Disclosure、ページ量、重複、既存ナレッジとの一貫性、将来の拡張性を基準に決める。巨大ページと過剰な細分化を避け、必要な情報だけをindexから段階的に読めるようにする。新しい領域は既存ページへの統合を先に検討し、必要な場合だけカテゴリを増やす。

ナレッジは整理済みの主張、Referenceは原文や判断材料であり、Referenceを直接ナレッジの代わりにしない。`references/`は根拠、`published/`は再生成可能な成果物、`.cache/`は差分検出用の補助データとして分離する。

設定優先順位は、コマンド指定 > `config.local.yml` > `config.yml` > Skill既定値。`config.local.yml` は原則Git管理しない。
