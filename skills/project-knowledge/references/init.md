# init

通常の`init`はscope指定なしで実行できる。[ルート設定](project-config.md)に従い、新規の場合は`uv run <skill-root>/scripts/init_project.py <project-root> --prepare`で形式1.0のmanifest、ナレッジ Bundleの骨組み、運用設定とSkill同梱の標準Policyへの参照を持つ`knowledge-policy.md`、再構築可能なstate、Reference、AGENTS.mdルーティングを生成する。共有`config.yml`は生成しない。本文生成後に`uv run <skill-root>/scripts/init_project.py <project-root>`を実行し、生成元コメント、`version: "1.0"`、レイヤーID・名前・パスを持つルート設定を最後に登録する。`access`省略時は`read-write`となる。空での初期化は`--prepare`なしで1回実行する。

## 複数レイヤーでの初期設定

複数構成の明示があれば[複数レイヤー共通手順](multi-layer.md)を読み、レイヤー定義を一度確定する。指定がなければ従来の単一レイヤー初期化を維持する。
ルート設定が存在する場合は、新規全体初期化へ進まない。不正設定も未登録と扱わず、追加導入か`split`かを依頼から判断する。

1. 確定した定義を`layers.json`へ保存する。全レイヤーの保存対象と除外対象を具体化する。
2. `uv run <skill-root>/scripts/init_project.py <project-root> --layers <layers.json> --prepare`で全件を最終パスへ準備する。登録と管理ブロックの更新は保留する。既存ディレクトリへの上書きは拒否される。
3. プロジェクトを一度調査し、全体の収集候補から配置表を作る。ユーザーの明示対応を優先し、未決定の保存先だけ質問する。レイヤーごとに調査を繰り返さない。
4. 配置表に従って各レイヤーへConceptとReferenceを生成する。標準Policyの運用設定を維持して用途を反映し、各索引から到達可能にする。根拠がないレイヤーは`empty_reasons`へ理由を残す。
5. `uv run <skill-root>/scripts/init_project.py <project-root> --layers <layers.json> --plan <collection.json>`で配置・形式・参照・到達性を検査し、全対象が揃った後にルート設定を公開する。通常の`verify`を自動実行することではない。
6. CLI結果で全レイヤーの解決、明示書込み選択と設定の一致を確認し、空の理由と分類件数を報告する。

「空で初期化」の明示時だけ3・4を省略し、`--plan`の代わりに`--empty`を使う。`--prepare`なしでも実行できる。
新規`read-only`は未登録の間に依頼された初期内容を準備し、その権限で登録する。登録後に一時的に昇格しない。
再開には同じ定義・配置表を使う。既存の生成済み内容は上書きしない。編集された内容は登録時に再検査する。

`collection.json`の例（`path`と`references`は移管先`docs/`基準）:

```json
{
  "placements": [
    {"source": "READMEの利用者向け機能", "layer": "product", "path": "features.md", "reason": "製品仕様", "references": []}
  ],
  "empty_reasons": {"development": "現時点で保存価値のある実装・運用の根拠がない"}
}
```

全生成ページを配置表に含め、未決定や重複をゼロにする。同じ主張を持つConceptを複数レイヤーへ複製しない。Referenceも一行ずつ記載する。

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
