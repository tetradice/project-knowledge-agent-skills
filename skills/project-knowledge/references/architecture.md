# Directory architecture

```text
project-knowledge/
├── manifest.yml
├── docs/
│   ├── index.md
│   ├── log.md
│   ├── <topic>/
│   │   ├── index.md
│   │   └── <concept>.md
│   └── references/
│       ├── index.md
│       ├── user-statements/
│       │   └── index.md
│       └── interactions/
│           └── index.md
├── knowledge-policy.md
├── state.yml
├── published/
├── .cache/
└── .gitignore
```

## 役割

- `manifest.yml`: Project Knowledge形式と形式版を宣言する。
- `docs/`: OKF v0.2互換の共有Knowledgeを置く。
- `knowledge-policy.md`: Knowledgeをどう育て、記述し、更新するかを、frontmatterの運用設定とMarkdown本文のPolicyで管理する。
- `state.yml`: 増分更新用の再構築可能なworking copy固有状態を置く。正本ではなく、通常はcommitしない。詳細は[state.md](state.md)を参照する。
- `published/`: Knowledgeから生成した成果物を置く。
- `.cache/`: 非Git環境のhash snapshotなど、再生成可能なworking copy固有データを置く。

`docs/references/user-statements/`と`docs/references/interactions/`は固定のprovenance保存先である。Raw Referenceは`type: Reference`と`pk_source_type`を持ち、通常Conceptの分類対象にはしない。
