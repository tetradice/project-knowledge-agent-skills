# init

通常の`init`はscope指定なしで実行できる。[ルート設定](project-config.md)に従い、新規の場合は`uv run <skill>/scripts/init_project.py <project-root> --prepare`で形式1.0のmanifest、ナレッジ Bundleの骨組み、運用設定とSkill同梱の標準Policyへの参照を持つ`knowledge-policy.md`、再構築可能なstate、Reference、AGENTS.mdルーティングを生成する。共有`config.yml`は生成しない。本文生成後に`uv run <skill>/scripts/init_project.py <project-root>`を実行し、生成元コメント、`version: "1.0"`、必須のレイヤーIDとパスだけを持つルート設定を最後に登録する。登録後は読み取り専用となる。空での初期化は`--prepare`なしで1回実行する。

既存設定がある場合は指定先を使い、書き込み可能な場合だけ本文やstateを変更する。読み取り専用の初期化済みレイヤーでは再実行しても変更しない。明示的な設定変更の依頼なしにアクセス権や版を変更しない。

書込み前に形式を検出する。既存Bundleは形式1.0だけを受け付け、manifestがない、壊れている、形式名または版が異なる場合は変更せず停止する。

「空で初期化」の明示があれば、初期構造の生成後に停止し、プロジェクト調査やKnowledge本文生成を行わない。ただし、追加・更新したファイルの分類件数は完了報告へ出力する。この明示がない通常の`init`を、骨組みだけで完了としてはならない。

## 通常の流れ

1. [Format 1.0](data-formats/1.0.md)に従って形式1.0であることを確認する。
2. 初期構造を生成する。新規Bundleではmanifestを含む1.0構造と、`state_schema_version: 2`、`git_baseline_commit: null`のローカルstateを直接生成する。既存stateが欠落・破損・非対応schemaならKnowledge本文を変えずに再生成する。
3. READMEと、存在する範囲で代表的なコード、設定、設計資料を調査する。ユーザーが初期Knowledgeの内容を指定した場合は、その範囲を優先する。これは将来の対象を限定する境界ではない。
4. [knowledge-policy.md](knowledge-policy.md)で保存価値を判定する。保存価値のある事実が見つかった場合は、根拠を持つ通常Conceptを1件以上生成する。保存価値のある事実が見つからない場合は、事実を捏造せず、その旨を報告する。
5. source projectから抽出した事実は、実在する根拠ファイルを`project-artifact`として参照する。単一根拠から直接抽出した知識は`pk_category: extracted`、`pk_derivation: direct`とし、複数根拠を一つの知識へ統合した場合は`pk_category: extracted`、`pk_derivation: synthesized`とする。未決定事項を確定済みのstableな事実へ昇格させず、裏付けのない主張や一時的なデバッグ値を保存しない。
6. [architecture.md](architecture.md)に従ってInformation Architectureを設計し、`docs/index.md`から全ページへ到達可能にする。
7. 生成した管理ファイル、通常Concept、source、indexへの到達性を確認する。新規の場合は確認後に設定登録を完了する。登録前は低水準の形式検査を使い、登録確認が必要な検査CLIは登録後に実行する。
8. [File change classification](file-change-classification.md)に従い、追加・更新したファイルを分類して完了報告へ件数を出力する。網羅的な検証が必要なら同じSkillの`verify`を明示的に依頼するよう案内し、自動実行しない。

再実行は冪等でなければならない。既存の`AGENTS.md`と`.gitignore`は保持し、同じ管理ブロックを重複させない。`state.yml`と`.cache/`はworking copy固有状態として`.gitignore`へ追加する。
