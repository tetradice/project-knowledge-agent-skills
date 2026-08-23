# init

通常の`init`はscope指定なしで実行できる。`python <skill>/scripts/init_project.py <project-root>`を実行し、ナレッジ Bundleの骨組み、`knowledge-policy.md`、config、state、Reference、AGENTS.mdルーティングを生成する。

`--empty`または「空で初期化」の明示があれば、管理ファイルと最低限の`docs/`構造だけを作り、プロジェクト調査やナレッジ本文生成を行わない。

## 通常の流れ

1. 初期構造を生成する。
2. ユーザーが初期ナレッジの内容を指定した場合だけ、その範囲を優先してプロジェクトを調査する。これは将来の対象を限定する境界ではない。
3. [knowledge-policy.md](knowledge-policy.md)で保存価値を判定する。
4. [architecture.md](architecture.md)に従ってInformation Architectureを設計し、`docs/index.md`から全ページへ到達可能にする。
5. `validate_knowledge.py`を実行し、結果を報告する。

再実行は冪等でなければならない。既存の`AGENTS.md`と`.gitignore`は保持し、同じ管理ブロックを重複させない。
