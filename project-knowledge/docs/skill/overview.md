---
type: Project Knowledge Skill
pk_category: declared
pk_derivation: synthesized
status: stable
generated:
  by: project-knowledge/3.1.0
  at: 2026-09-14T20:41:27+09:00
sources:
- resource: ../references/user-statements/2026-08-31-user-statement-reflection.md
  pk_source_type: user-statement
- resource: ../references/user-statements/2026-08-29-inspect-skill-output.md
  pk_source_type: user-statement
- resource: ../references/interactions/2026-08-29-inspect-skill-output-implementation.md
  pk_source_type: interaction-record
- resource: ../references/user-statements/2026-08-29-standard-policy-reference.md
  pk_source_type: user-statement
- resource: ../references/interactions/2026-08-29-standard-policy-reference-implementation.md
  pk_source_type: interaction-record
- resource: ../references/user-statements/2026-08-29-help-inspect.md
  pk_source_type: user-statement
- resource: ../references/user-statements/2026-08-29-help-skill-split.md
  pk_source_type: user-statement
- resource: ../references/user-statements/2026-08-26-fix-and-refactor.md
  pk_source_type: user-statement
- resource: ../references/user-statements/2026-08-26-verify-content-health.md
  pk_source_type: user-statement
- resource: ../references/user-statements/2026-08-26-verify-in-main-skill.md
  pk_source_type: user-statement
- resource: ../references/user-statements/2026-08-26-current-format-only.md
  pk_source_type: user-statement
- resource: ../references/user-statements/2026-08-26-index-content-boundary.md
  pk_source_type: user-statement
- resource: ../references/user-statements/2026-09-14-multi-layer-display-names.md
  pk_source_type: user-statement
- resource: ../../../skills/project-knowledge/SKILL.md
  pk_source_type: change-implementation
- resource: ../../../skills/project-knowledge/references/verification.md
  pk_source_type: change-implementation
- resource: ../../../skills/project-knowledge/references/update.md
  pk_source_type: change-implementation
- resource: ../../../skills/project-knowledge/references/project-config.md
  pk_source_type: change-implementation
- resource: ../../../skills/project-knowledge/references/standard-knowledge-policy.md
  pk_source_type: change-implementation
- resource: ../../../skills/project-knowledge/references/fix.md
  pk_source_type: change-implementation
- resource: ../../../skills/project-knowledge-inspect/SKILL.md
  pk_source_type: change-implementation
- resource: ../../../skills/project-knowledge-help/SKILL.md
  pk_source_type: change-implementation
- resource: ../../../skills/project-knowledge-fast-ask/SKILL.md
  pk_source_type: change-implementation
- resource: ../../../skills/project-knowledge-audit/SKILL.md
  pk_source_type: change-implementation
- resource: ../../../skills/project-knowledge-audit/references/refactor.md
  pk_source_type: change-implementation
- resource: ../../../skills/project-knowledge-publish/references/publishing.md
  pk_source_type: change-implementation
- resource: ../references/interactions/2026-09-01-publish-current-structure-review.md
  pk_source_type: interaction-record
- resource: ../references/interactions/2026-08-29-help-inspect-implementation.md
  pk_source_type: interaction-record
- resource: ../references/interactions/2026-08-29-help-skill-split-implementation.md
  pk_source_type: interaction-record
- resource: ../references/interactions/2026-09-14-multi-layer-implementation.md
  pk_source_type: interaction-record
- resource: references/user-statements/2026-09-15-multi-layer-workflows.md
  pk_source_type: user-statement
- resource: references/interactions/2026-09-15-multi-layer-workflows-implementation.md
  pk_source_type: interaction-record
- resource: ../../skills/project-knowledge/references/multi-layer.md
  pk_source_type: change-implementation
- resource: ../../skills/project-knowledge/references/split.md
  pk_source_type: change-implementation
---
# プロジェクトナレッジ Skill

## 責務と操作

メインの`project-knowledge`は`init`、`split`、`update`、`verify`、`fix`、`config`を扱い、Knowledgeを構築、分割、追加、更新、検証、修正、設定して保守する。利用案内、Knowledge Baseの説明、Knowledge限定回答、成果物生成、構造監査・構造改善、Knowledgeなし・ありの実務比較は、それぞれ`project-knowledge-help`、`project-knowledge-inspect`、`project-knowledge-fast-ask`、`project-knowledge-publish`、`project-knowledge-audit`、`project-knowledge-benchmark`へ分離する。

`project-knowledge-help`はexplicit-onlyのread-only Skillである。対象なしでは5基本操作の用途、操作名指定、自然言語例と、利用者向け5専用Skillの明示呼び出し例を定型形式で説明する。対象指定ありと未知対象には別の定型を使い、説明した操作やSkillを自動実行しない。旧形式の`$project-knowledge help`は互換実行せず、新Skillを案内する。

`project-knowledge-inspect`はSkill名の明示指定または自然言語の依頼から使用できるread-only Skillである。正常時は概要、Knowledge文書だけのフォルダツリー、interactions・user-statements・その他Reference・作成Knowledgeの4区分の統計、Knowledge Policy設定の自然文説明を固定順で返す。内容の正しさ、鮮度、構造品質、改善方法は評価せず、未初期化または未対応形式では安全に読み取りを止める。

内容・正しさの検査のみは`verify`、検査と修正は`fix`が担当する。どちらも形式、source、provenance、根拠、現在状態、鮮度、Knowledge間の意味的整合性の順に確認する。`verify`はread-onlyで、`fix`は客観的に修正できる既存Knowledgeの問題だけを直して再検査する。単なる`verify`依頼から`fix`へ昇格しない。

構造・品質の診断のみは`project-knowledge-audit`の`audit`、診断と保守的な構造改善は同Skillの`refactor`が担当する。`audit`はread-onlyであり、`refactor`はKnowledgeの意味・source・provenanceを維持して再診断する。一般的な「整理して」「改善して」から自動選択せず、SkillまたはProject Knowledgeの構造refactorを明示した場合だけ実行する。

`update`は新しい情報や変更を反映する操作であり、既存Knowledgeの問題を正す`fix`、既存Knowledge Baseの構造を改善する`refactor`と区別する。各操作は互いを自動実行しない。未登録Knowledgeのcoverage調査はupdateまたはdiscovery側へ委ねる。宣言された方針と実装の差異はKnowledgeの誤りと即断せずimplementation driftとして報告し、検証後も`inferred`などのprovenanceを書き換えない。

`project-knowledge-help`、`project-knowledge-fast-ask`、`project-knowledge-publish`、`project-knowledge-audit`、`project-knowledge-benchmark`はexplicit-onlyとし、通常質問、要約、実装レビュー、文書レビューから自動発火させない。`project-knowledge-inspect`は構造・格納情報の説明を求める自然言語に対応する。各Skillは別Skillを自動実行しない。

限定回答の手順は`project-knowledge-fast-ask`の`SKILL.md`へ集約する。構造監査・構造改善は`project-knowledge-audit`の`SKILL.md`から`audit`と`refactor`のReferenceへ振り分ける。

公開は、Knowledgeに記録された持続的な設計意図、制約、理由、仕様と、現在のProject Artifactから直接確認できる実装構造を組み合わせ、MarkdownまたはMaterial for MkDocsによるoffline HTMLとして出力する。調査対象と詳細度は実行時に決め、Knowledge Baseへ永続化しない。Project Artifactから意図や将来方針を推測せず、Knowledgeとの明確な不一致は由来と根拠を区別して成果物へ示す。補完内容をKnowledgeへ逆同期せず、他のProject Knowledge操作も自動実行しない。

## 対応形式

Project Knowledgeへアクセスする前に、プロジェクトルートの`project-knowledge.yaml`を解決する。設定がなければ対象外であり、固定の`project-knowledge/`配置やmanifestから推測しない。解決結果のプロジェクトルートと全レイヤーのパスを以後の基準とする。参照操作は全レイヤーを対象にしてレイヤーIDを結果へ付け、書込みは明示指定、明確な`name`または`id`指定、Policyに適合する一意なAI候補、`write_target`の順で書込み可能な1レイヤーを選ぶ。

全SkillはProject Knowledge形式1.0だけを扱う。解決済みレイヤーのmanifestがない、壊れている、形式名または版が異なる場合は推測せず停止する。`init`は未登録プロジェクトへの単一または複数レイヤー設定の作成、または形式1.0の既存Bundleの登録を扱う。複数レイヤーでは全レイヤーの候補を検査して設定を最後に公開する。`split`は既存単一レイヤーと明示した新規レイヤーの固定集合を、確定済み配置表に基づき変更する。通常の`update`や`refactor`はレイヤーを再配分しない。

## KnowledgeとIndex

root・nested `index.md`はナビゲーション専用とする。独立して再利用できる事実、判断、制約、状態、検証結果は通常Conceptへ分離し、frontmatterで分類と根拠を保持する。

`project-knowledge/knowledge-policy.md`は、Agent Skill `project-knowledge`同梱の標準Policyに従う宣言と参照情報を持つ。プロジェクト固有方針がある場合は本文へ記載して標準Policyより優先し、指定されていない部分には標準Policyを適用する。対象領域は固定せず、肥大化はPolicy、重複回避、Incremental Update、Progressive Disclosureで抑える。

`init`のスクリプトは常に管理構造だけを生成する。「空で初期化」の指定は、生成後にエージェントが調査・本文作成を行わないためのintentであり、CLI optionではない。

## Provenance

通常Conceptは`pk_category`で情報の種類、`pk_derivation`で導出方法を表す。sourceには`pk_source_type`を付け、ユーザー原文はUser Statement、作業経緯はInteraction Recordとして必要な場合だけ保存する。

User Statementを追加・更新した場合は、内容を関連するConceptなど他のナレッジにも必ず反映し、そのUser Statementをsourceとして残す。

`generated`は現在内容の生成者、`verified`は独立した確認者である。trust tierは`verified`から表示時に導出する。

## Learning mode

`manual`は明示的なupdate時だけ書き換える。`opportunistic`は作業単位完了時に候補を評価し、価値がある場合だけupdateする。`aggressive`は候補を広めに拾うが、一時情報と重複は除外する。

## 専用操作

inspectは`project-knowledge/`だけを読み、固定形式で概要を説明する。askは`project-knowledge/docs/**`だけを情報源とし、不足時は推測しない。publishはKnowledgeと現在のProject Artifactから再生成可能なMarkdownとoffline HTMLを出力する。benchmarkは同一実務TaskをProject Knowledgeなし・ありで比較する。内容の正しさは`verify`/`fix`、構造・品質は`audit`/`refactor`が、それぞれ検査のみ/検査と修正を担当する。書き込み操作へ自動昇格しない。
