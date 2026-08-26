# init

通常の`init`はscope指定なしで実行できる。`uv run <skill>/scripts/init_project.py <project-root>`を実行し、形式1.0のmanifest、ナレッジ Bundleの骨組み、運用設定をfrontmatterに持つ`knowledge-policy.md`、再構築可能なstate、Reference、AGENTS.mdルーティングを生成する。共有`config.yml`は生成しない。

書込み前に形式を検出する。既存Bundleは形式1.0だけを受け付け、manifestがない、壊れている、形式名または版が異なる場合は変更せず停止する。

「空で初期化」の明示があれば、初期構造の生成後に停止し、プロジェクト調査やナレッジ本文生成を行わない。

## 通常の流れ

1. [Format 1.0](data-formats/1.0.md)に従って形式1.0であることを確認する。
2. 初期構造を生成する。新規Bundleではmanifestを含む1.0構造と、`state_schema_version: 2`、`git_baseline_commit: null`のローカルstateを直接生成する。既存stateが欠落・破損・非対応schemaならKnowledge本文を変えずに再生成する。
3. ユーザーが初期ナレッジの内容を指定した場合だけ、その範囲を優先してプロジェクトを調査する。これは将来の対象を限定する境界ではない。
4. [knowledge-policy.md](knowledge-policy.md)で保存価値を判定する。
5. [architecture.md](architecture.md)に従ってInformation Architectureを設計し、`docs/index.md`から全ページへ到達可能にする。
6. 生成した管理ファイルとindexへの到達性を確認し、結果を報告する。網羅的な検証が必要なら同じSkillの`verify`を明示的に依頼するよう案内し、自動実行しない。

再実行は冪等でなければならない。既存の`AGENTS.md`と`.gitignore`は保持し、同じ管理ブロックを重複させない。`state.yml`と`.cache/`はworking copy固有状態として`.gitignore`へ追加する。
