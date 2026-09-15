---
type: Project Knowledge Multi-layer Workflow
pk_category: declared
pk_derivation: synthesized
status: stable
generated:
  by: project-knowledge/3.1.0
  at: 2026-09-15T11:51:37+09:00
sources:
- resource: ../../multi-layer-workflow-proposal.md
  pk_source_type: project-artifact
- resource: references/user-statements/2026-09-15-multi-layer-workflows.md
  pk_source_type: user-statement
- resource: references/interactions/2026-09-15-multi-layer-workflows-implementation.md
  pk_source_type: interaction-record
- resource: ../../skills/project-knowledge/references/multi-layer.md
  pk_source_type: change-implementation
- resource: ../../skills/project-knowledge/references/init.md
  pk_source_type: change-implementation
- resource: ../../skills/project-knowledge/references/split.md
  pk_source_type: change-implementation
- resource: ../../skills/project-knowledge/scripts/layer_workflow.py
  pk_source_type: change-implementation
- resource: ../../skills/project-knowledge/scripts/init_project.py
  pk_source_type: change-implementation
- resource: ../../skills/project-knowledge/scripts/split_project.py
  pk_source_type: change-implementation
- resource: ../../skills/project-knowledge/scripts/project_config.py
  pk_source_type: change-implementation
- resource: ../../skills/project-knowledge/scripts/validate_knowledge.py
  pk_source_type: change-implementation
---
# 複数レイヤーの初期化と分割

複数レイヤーの新規`init`と既存単一レイヤーの`split`は、通常のKnowledge更新とは別の明示操作である。両操作は、利用者の指定を優先して確定したレイヤー定義と配置表を唯一の入力にする。定義には一意の`id`、表示用`name`、保存対象を説明する`description`、`access`、`optional`、`auto_select`、`write_target`を含める。定義済みのID、パス、用途は実行中・再開時に再生成しない。

複数レイヤーの新規`init`では、各レイヤーの骨組み、Policy、索引、本文候補を準備し、最終配置を基準に配置表、形式、参照、索引を検査する。すべてが揃うまでルート設定を公開しない。明示的な空初期化では本文収集を省略できる。読み取り専用の新規レイヤーも、登録前に必要な初期内容を準備してからその権限で登録する。骨組み保存直前の中断は`pending_create`記録で同じ定義から再開する。新規複数構成の`write_target`は、指定がなければ`null`と明記し、初期収集の配置を決めるために使わない。

`split`は元レイヤーを維持し、確定した文書だけを新規レイヤーへ取り出す。各Conceptは元に残すか一つの移管先へ移す。主題が混在する文書と未決定文書は、元を残せる場合に元へ置き、本文は分割しない。専用Referenceは依存するConceptと移動し、共有Reference、User Statement、Interactionは同じprovenanceを保持して必要なレイヤーへコピーする。リンクはMarkdownファイル基準、`sources[].resource`は各bundleの`docs/`基準で最終パスへ再計算する。

適用前には対象の原本と指紋を操作用の一時領域へ保存し、候補で新しい形式・参照・索引不整合がないことを確認する。適用中はロックで新規の設定解決とKnowledge操作を停止する。入力、根拠、候補の変更、他者による編集、読み取り専用参照元の更新が必要な配置を検出した場合は停止する。切替の失敗は今回の変更だけを復旧し、ロックだけを削除して再開しない。ルート設定は既存コメントを保持して最後に公開する。新しいstateは複製せず、source snapshotを無効化して再構築対象にする。元を廃止するときは履歴移管先`history_layer`を明示する。成功後は復旧用コピーを片付け、指紋と完了結果を残す。

これらの操作は`verify`、`fix`、`publish`、`audit`、`refactor`を自動実行しない。複数レイヤーの通常更新も、明示指定、明確な`name`または`id`、Policyに適合する一意候補、`write_target`の順で、書込み先を必ず一つに決める。

sourceの正本はbundleの`docs/`基準である。既存Bundleに残る文書相対sourceは、docs基準で実在先を解決できない場合だけ、その文書相対の実在先へ互換的に解決する。`split`は旧参照が指す実体を保持したdocs基準のsourceへ再計算する。この互換は既存文書の一括変換を意味しない。
