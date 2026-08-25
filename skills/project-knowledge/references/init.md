# init

通常の`init`はscope指定なしで実行できる。`uv run <skill>/scripts/init_project.py <project-root>`を実行し、形式0.2のmanifest、ナレッジ Bundleの骨組み、`knowledge-policy.md`、config、state、Reference、AGENTS.mdルーティングを生成する。

書込み前に形式を検出する。既存形式0.1は`migrate_project.py`で0.2へ移行してから初期化を続ける。malformed manifest、未知形式、対応版より新しい形式では変更せず停止する。

`--empty`または「空で初期化」の明示があれば、管理ファイルと最低限の`docs/`構造だけを作り、プロジェクト調査やナレッジ本文生成を行わない。

## 通常の流れ

1. [data-format.md](data-format.md)に従って形式を検出し、必要ならmigrationする。
2. 初期構造を生成する。新規Bundleではmanifestを含む0.2構造を直接生成する。
3. ユーザーが初期ナレッジの内容を指定した場合だけ、その範囲を優先してプロジェクトを調査する。これは将来の対象を限定する境界ではない。
4. [knowledge-policy.md](knowledge-policy.md)で保存価値を判定する。
5. [architecture.md](architecture.md)に従ってInformation Architectureを設計し、`docs/index.md`から全ページへ到達可能にする。
6. 生成した管理ファイルとindexへの到達性を確認し、結果を報告する。網羅的な検証が必要なら`project-knowledge-verify`の明示的な利用を案内し、自動実行しない。

再実行は冪等でなければならない。既存の`AGENTS.md`と`.gitignore`は保持し、同じ管理ブロックを重複させない。
