---
type: Project Knowledge Root Configuration
pk_category: declared
pk_derivation: synthesized
status: stable
generated:
  by: project-knowledge/3.1.0
  at: 2026-09-14T20:41:27+09:00
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
- resource: ../references/interactions/2026-09-14-multi-layer-implementation.md
  pk_source_type: interaction-record
- resource: ../references/interactions/2026-09-13-root-configuration-implementation.md
  pk_source_type: interaction-record
---
# Project Knowledgeのルート設定

Project Knowledge操作は、プロジェクトルートの`project-knowledge.yaml`を入口にする。設定がなければ対象外であり、`project-knowledge/`ディレクトリや`manifest.yml`だけからナレッジを自動検出、読み込み、書き込みしない。解決済みの設定ファイルの所在ディレクトリをプロジェクトルートとして扱い、レイヤーの`path`はそこから解決する。

設定の`version`は引用した文字列`"1.0"`を必須とする。ユーザーの指示なしにこの版を補完、変換、昇格しない。`layers`も必須で、0件以上を登録できる。`layers: []`は利用対象ゼロの有効な設定である。参照操作は利用可能な全レイヤーを対象とする一方、書込み操作は常に1レイヤーだけを選ぶ。

レイヤーの`id`、`name`、`path`は常に必須であり、暗黙の値を補わない。`id`は`[a-z][a-z0-9_-]*`に従う不変の機械識別子であり、CLI、根拠、state、キャッシュで使う。`name`は空白以外を含む一意な利用者向け呼称であり、AIの表示と自然言語による明確な対象指定に使う。`path`は設定所在地からのプロジェクト内相対パスで、ナレッジ管理ディレクトリを指す。`id: default`以外では、`description`を空白だけでない文字列として必須にする。`default`の説明は省略できる。

`access`を省略したレイヤーは`read-write`である。読み取り専用レイヤーには、本文だけでなくPolicy、state、キャッシュ、公開成果物も保存しない。`auto_select`は省略時`true`で、`false`のレイヤーは曖昧な更新依頼に対するAIの内容ベース選択候補から外す。`write_target`は`auto_select: false`のレイヤーを指せず、明示指定、明確な`name`または`id`指定、Policyに適合する一意なAI候補のいずれもない場合だけ使う。初期化が生成する設定は生成元コメント、`version`、`layers`、`id: default`、`name: プロジェクトナレッジ`、`path: ./project-knowledge`だけを含め、`description`、`access`、`optional`、`auto_select`、`write_target`を出力しない。そのため、初期生成直後のレイヤーは書き込み可能となる。読み取り専用で運用するときは、`access: read-only`を明示する。

空ファイル、必須キーの欠落、未知キー、重複キー、型不一致、未対応版、重複する`id`・`name`・実体パス、親子関係にある実体パスは設定エラーとする。設定が不正な場合や必須レイヤーが利用不能な場合は、親の設定、既定パス、別レイヤーにフォールバックしない。形式チェックは利用前提の確認であり、Knowledgeの正確性を調べる`verify`や修正する`fix`を自動実行するものではない。
