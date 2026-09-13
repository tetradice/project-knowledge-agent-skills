---
type: Project Knowledge Root Configuration
pk_category: declared
pk_derivation: synthesized
status: stable
generated:
  by: project-knowledge/3.1.0
  at: 2026-09-13T00:00:00+09:00
sources:
- resource: ../../../project-knowledge-config-proposal.md
  pk_source_type: project-artifact
- resource: ../../../skills/project-knowledge/references/project-config.md
  pk_source_type: change-implementation
- resource: ../references/user-statements/2026-09-13-root-configuration.md
  pk_source_type: user-statement
- resource: ../references/interactions/2026-09-13-root-configuration-implementation.md
  pk_source_type: interaction-record
---
# Project Knowledgeのルート設定

Project Knowledge操作は、プロジェクトルートの`project-knowledge.yaml`を入口にする。設定がなければ対象外であり、`project-knowledge/`ディレクトリや`manifest.yml`だけからナレッジを自動検出、読み込み、書き込みしない。解決済みの設定ファイルの所在ディレクトリをプロジェクトルートとして扱い、レイヤーの`path`はそこから解決する。

設定の`version`は引用した文字列`"1.0"`を必須とする。ユーザーの指示なしにこの版を補完、変換、昇格しない。`layers`も必須で、初期実装は0件または1件だけを受け付け、2件以上は複数レイヤー未対応として拒否する。`layers: []`は利用対象ゼロの有効な設定である。

レイヤーの`id`と`path`は常に必須であり、暗黙のIDやパスを補わない。`id`は`[a-z][a-z0-9_-]*`に従い、`path`は設定所在地からのプロジェクト内相対パスで、ナレッジ管理ディレクトリを指す。`id: default`以外では、`description`を空白だけでない文字列として必須にする。`default`の説明は省略できる。

`access`を省略したレイヤーは`read-only`である。読み取り専用レイヤーには、本文だけでなくPolicy、state、キャッシュ、公開成果物も保存しない。初期化が生成する設定は生成元コメント、`version`、`layers`、`id: default`、`path: ./project-knowledge`だけを含め、`description`、`access`、`optional`、`write_target`を出力しない。そのため、初期生成直後のレイヤーは読み取り専用となる。既存Knowledgeを保守するために書き込みを許可するときは、`access: read-write`を明示する。

空ファイル、必須キーの欠落、未知キー、重複キー、型不一致、未対応版は設定エラーとする。設定が不正な場合や必須レイヤーが利用不能な場合は、親の設定、既定パス、別レイヤーにフォールバックしない。形式チェックは利用前提の確認であり、Knowledgeの正確性を調べる`verify`や修正する`fix`を自動実行するものではない。
