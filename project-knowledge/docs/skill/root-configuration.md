---
type: Project Knowledge Root Configuration
pk_category: declared
pk_derivation: synthesized
status: stable
generated:
  by: project-knowledge/3.1.0
  at: 2026-09-16T10:20:04+09:00
sources:
- resource: ../../../project-knowledge-config-proposal.md
  pk_source_type: project-artifact
- resource: ../../../skills/project-knowledge/references/project-config.md
  pk_source_type: change-implementation
- resource: ../references/user-statements/2026-09-13-root-configuration.md
  pk_source_type: user-statement
- resource: ../references/user-statements/2026-09-14-default-read-write.md
  pk_source_type: user-statement
- resource: ../references/user-statements/2026-09-15-default-layer-name.md
  pk_source_type: user-statement
- resource: ../references/user-statements/2026-09-14-multi-layer-display-names.md
  pk_source_type: user-statement
- resource: ../references/user-statements/2026-09-16-external-layer-paths.md
  pk_source_type: user-statement
- resource: ../references/interactions/2026-09-16-external-layer-paths-implementation.md
  pk_source_type: interaction-record
- resource: references/user-statements/2026-09-15-multi-layer-workflows.md
  pk_source_type: user-statement
- resource: ../../multi-layer-workflow-proposal.md
  pk_source_type: project-artifact
- resource: ../../skills/project-knowledge/references/multi-layer.md
  pk_source_type: change-implementation
- resource: ../../skills/project-knowledge/references/split.md
  pk_source_type: change-implementation
- resource: ../../skills/project-knowledge/scripts/layer_workflow.py
  pk_source_type: change-implementation
- resource: ../../skills/project-knowledge/scripts/split_project.py
  pk_source_type: change-implementation
- resource: ../../skills/project-knowledge/scripts/init_project.py
  pk_source_type: change-implementation
- resource: ../../skills/project-knowledge/scripts/project_config.py
  pk_source_type: change-implementation
- resource: ../../skills/project-knowledge/scripts/layer_workflow.py
  pk_source_type: change-implementation
- resource: ../references/interactions/2026-09-14-multi-layer-implementation.md
  pk_source_type: interaction-record
- resource: ../references/interactions/2026-09-13-root-configuration-implementation.md
  pk_source_type: interaction-record
---
# Project Knowledgeのルート設定

Project Knowledge操作は、プロジェクトルートの`project-knowledge.yaml`を入口にする。設定がなければ対象外であり、`project-knowledge/`ディレクトリや`manifest.yml`だけからナレッジを自動検出、読み込み、書き込みしない。解決済みの設定ファイルの所在ディレクトリをプロジェクトルートとして扱い、レイヤーの`path`はそこから解決する。

設定の`version`は引用した文字列`"1.0"`を必須とする。ユーザーの指示なしにこの版を補完、変換、昇格しない。`layers`も必須で、0件以上を登録できる。`layers: []`は利用対象ゼロの有効な設定である。参照操作は利用可能な全レイヤーを対象とする一方、書込み操作は常に1レイヤーだけを選ぶ。

レイヤーの`id`、`name`、`path`は常に必須であり、暗黙の値を補わない。`id`は`[a-z][a-z0-9_-]*`に従う不変の機械識別子であり、CLI、根拠、state、キャッシュで使う。`name`は空白以外を含む一意な利用者向け呼称であり、AIの表示と自然言語による明確な対象指定に使う。`path`は設定所在地から解決する相対パスまたは絶対パスで、プロジェクト外も指せるナレッジ管理ディレクトリを指定する。`..`、ローカル絶対パス、UNC、symlink／junctionで解決された実体パスを登録できるが、URL、環境変数、`~`、globは登録できない。プロジェクトルート自身、設定ファイル自身のsymlink、同一または親子関係にあるレイヤー実体パスは登録できない。`id: default`以外では、`description`を空白だけでない文字列として必須にする。`default`の説明は省略できる。

`access`を省略したレイヤーは`read-write`である。読み取り専用レイヤーには、本文だけでなくPolicy、state、キャッシュ、公開成果物も保存しない。`auto_select`は省略時`true`で、`false`のレイヤーは曖昧な更新依頼に対するAIの内容ベース選択候補から外す。`write_target`は`auto_select: false`のレイヤーを指せず、明示指定、明確な`name`または`id`指定、Policyに適合する一意なAI候補のいずれもない場合だけ使う。初期化が生成する設定は生成元コメント、`version`、`layers`、`id: default`、`name: プロジェクトナレッジ`、`path: ./project-knowledge`だけを含め、`description`、`access`、`optional`、`auto_select`、`write_target`を出力しない。そのため、初期生成直後のレイヤーは書き込み可能となる。読み取り専用で運用するときは、`access: read-only`を明示する。

空ファイル、必須キーの欠落、未知キー、重複キー、型不一致、未対応版、重複する`id`・`name`・実体パス、親子関係にある実体パスは設定エラーとする。設定が不正な場合や必須レイヤーが利用不能な場合は、親の設定、既定パス、別レイヤーにフォールバックしない。形式チェックは利用前提の確認であり、Knowledgeの正確性を調べる`verify`や修正する`fix`を自動実行するものではない。

外部レイヤーも`access: read-write`なら初期化、通常更新、分割、復旧の登録済み対象になる。初期化・分割の操作記録は正規化済み絶対パスを対象キーにし、候補、バックアップ、指紋はプロジェクト内の作業領域に保存する。適用時は記録済みの対象だけを書き換える。表示はプロジェクト内なら相対、外部なら解決済み絶対パスにする。プロジェクト直下の設定、`AGENTS.md`、`.gitignore`はプロジェクト側で管理し、`.gitignore`の管理ブロックにはプロジェクト内レイヤーの`state.yml`と`.cache/`だけを入れる。

複数レイヤーの新規初期化では、全レイヤーの定義、管理構造、配置表、参照を検査してから設定を最後に公開する。既存の単一レイヤーを分ける`split`では、元レイヤーと新しい移管先の固定集合だけを変更し、通常の書込み先1件という規則を変えない。切替中はロックにより新規の設定解決を停止し、復旧は記録された操作から行う。ロックだけを削除して処理を再開しない。
