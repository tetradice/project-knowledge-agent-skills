# init

通常の`init`はscope指定なしで実行できる。`uv run <skill>/scripts/init_project.py <project-root>`を実行し、形式1.0のmanifest、ナレッジ Bundleの骨組み、運用設定をfrontmatterに持つ`knowledge-policy.md`、再構築可能なstate、Reference、AGENTS.mdルーティングを生成する。共有`config.yml`は生成しない。このscriptが行うのは初期構造の生成までであり、通常の`init`はその後のプロジェクト調査とKnowledge本文の生成まで終えて完了とする。

書込み前に形式を検出する。既存Bundleは形式1.0だけを受け付け、manifestがない、壊れている、形式名または版が異なる場合は変更せず停止する。

「空で初期化」の明示があれば、初期構造の生成後に停止し、プロジェクト調査やKnowledge本文生成を行わない。この明示がない通常の`init`を、骨組みだけで完了としてはならない。

## 通常の流れ

1. [Format 1.0](data-formats/1.0.md)に従って形式1.0であることを確認する。
2. 初期構造を生成する。新規Bundleではmanifestを含む1.0構造と、`state_schema_version: 2`、`git_baseline_commit: null`のローカルstateを直接生成する。既存stateが欠落・破損・非対応schemaならKnowledge本文を変えずに再生成する。
3. READMEと、存在する範囲で代表的なコード、設定、設計資料を調査する。ユーザーが初期Knowledgeの内容を指定した場合は、その範囲を優先する。これは将来の対象を限定する境界ではない。
4. [knowledge-policy.md](knowledge-policy.md)で保存価値を判定する。保存価値のある事実が見つかった場合は、根拠を持つ通常Conceptを1件以上生成する。保存価値のある事実が見つからない場合は、事実を捏造せず、その旨を報告する。
5. source projectから抽出した事実は、実在する根拠ファイルを`project-artifact`として参照する。単一根拠から直接抽出した知識は`pk_category: extracted`、`pk_derivation: direct`とし、複数根拠を一つの知識へ統合した場合は`pk_category: extracted`、`pk_derivation: synthesized`とする。未決定事項を確定済みのstableな事実へ昇格させず、裏付けのない主張や一時的なデバッグ値を保存しない。
6. [architecture.md](architecture.md)に従ってInformation Architectureを設計し、`docs/index.md`から全ページへ到達可能にする。
7. 生成した管理ファイル、通常Concept、source、indexへの到達性を確認し、結果を報告する。網羅的な検証が必要なら同じSkillの`verify`を明示的に依頼するよう案内し、自動実行しない。

再実行は冪等でなければならない。既存の`AGENTS.md`と`.gitignore`は保持し、同じ管理ブロックを重複させない。`state.yml`と`.cache/`はworking copy固有状態として`.gitignore`へ追加する。
