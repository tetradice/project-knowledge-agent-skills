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
├── config.yml
├── config.local.yml
├── state.yml
├── published/
├── .cache/
└── .gitignore
```

## 役割

- `manifest.yml`: Project Knowledge形式と形式版を宣言する。
- `docs/`: OKF v0.2互換の共有Knowledgeを置く。
- `knowledge-policy.md`: 何をKnowledgeに入れるかを管理する。
- `config.yml`: 共有する収集・更新設定を置く。
- `config.local.yml`: 個人設定と秘密情報を置く。通常はcommitしない。
- `state.yml`: 差分検出などの機械状態を置く。
- `published/`: Knowledgeから生成した成果物を置く。
- `.cache/`: 再生成可能な一時データを置く。

`docs/references/user-statements/`と`docs/references/interactions/`は固定のprovenance保存先である。Raw Referenceは`type: Reference`と`pk_source_type`を持ち、通常Conceptの分類対象にはしない。

Skill SemVer、Knowledge形式版、OKF版、state schema版は独立して変更する。ディレクトリ形式の変更はKnowledge形式版、bundle規約の変更はOKF版、実装だけの修正は該当Skill版、state内部形式の変更はstate schema版を更新する。
