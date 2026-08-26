---
type: Project Knowledge Skill
pk_category: declared
pk_derivation: synthesized
status: stable
generated:
  by: project-knowledge/3.1.0
  at: 2026-08-26T21:21:07+09:00
sources:
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
- resource: ../../../skills/project-knowledge/SKILL.md
  pk_source_type: change-implementation
- resource: ../../../skills/project-knowledge/references/verification.md
  pk_source_type: change-implementation
- resource: ../../../skills/project-knowledge/references/update.md
  pk_source_type: change-implementation
- resource: ../../../skills/project-knowledge/references/fix.md
  pk_source_type: change-implementation
- resource: ../../../skills/project-knowledge-fast-ask/SKILL.md
  pk_source_type: change-implementation
- resource: ../../../skills/project-knowledge-audit/SKILL.md
  pk_source_type: change-implementation
- resource: ../../../skills/project-knowledge-audit/references/refactor.md
  pk_source_type: change-implementation
- resource: ../../../skills/project-knowledge-publish/references/publishing.md
  pk_source_type: change-implementation
---
# プロジェクトナレッジ Skill

## 責務と操作

メインの`project-knowledge`は`init`、`update`、`verify`、`fix`、`config`を扱い、Knowledgeを構築・追加・更新・検証・修正・設定して保守する。Knowledge限定回答、成果物生成、構造監査・構造改善は、それぞれ`project-knowledge-fast-ask`、`project-knowledge-publish`、`project-knowledge-audit`へ分離する。

内容・正しさの検査のみは`verify`、検査と修正は`fix`が担当する。どちらも形式、source、provenance、根拠、現在状態、鮮度、Knowledge間の意味的整合性の順に確認する。`verify`はread-onlyで、`fix`は客観的に修正できる既存Knowledgeの問題だけを直して再検査する。単なる`verify`依頼から`fix`へ昇格しない。

構造・品質の診断のみは`project-knowledge-audit`の`audit`、診断と保守的な構造改善は同Skillの`refactor`が担当する。`audit`はread-onlyであり、`refactor`はKnowledgeの意味・source・provenanceを維持して再診断する。一般的な「整理して」「改善して」から自動選択せず、SkillまたはProject Knowledgeの構造refactorを明示した場合だけ実行する。

`update`は新しい情報や変更を反映する操作であり、既存Knowledgeの問題を正す`fix`、既存Knowledge Baseの構造を改善する`refactor`と区別する。各操作は互いを自動実行しない。未登録Knowledgeのcoverage調査はupdateまたはdiscovery側へ委ねる。宣言された方針と実装の差異はKnowledgeの誤りと即断せずimplementation driftとして報告し、検証後も`inferred`などのprovenanceを書き換えない。

3つの専用Skillはexplicit-onlyとし、通常質問、要約、実装レビュー、文書レビューから自動発火させない。各Skillは別Skillを自動実行しない。

限定回答の手順は`project-knowledge-fast-ask`の`SKILL.md`へ集約する。構造監査・構造改善は`project-knowledge-audit`の`SKILL.md`から`audit`と`refactor`のReferenceへ振り分ける。公開はMarkdownとMaterial for MkDocsによるoffline HTMLだけを扱い、rendererやoffline設定を永続化しない。

## 対応形式

全SkillはProject Knowledge形式1.0だけを扱う。manifestがない、壊れている、形式名または版が異なる場合は推測せず停止する。`init`は新規Bundleまたは形式1.0の既存Bundleだけを対象とする。

## KnowledgeとIndex

root・nested `index.md`はナビゲーション専用とする。独立して再利用できる事実、判断、制約、状態、検証結果は通常Conceptへ分離し、frontmatterで分類と根拠を保持する。

`project-knowledge/knowledge-policy.md`はKnowledgeをどう育てるかを定義する。対象領域は固定せず、肥大化はPolicy、重複回避、Incremental Update、Progressive Disclosureで抑える。

`init`のスクリプトは常に管理構造だけを生成する。「空で初期化」の指定は、生成後にエージェントが調査・本文作成を行わないためのintentであり、CLI optionではない。

## Provenance

通常Conceptは`pk_category`で情報の種類、`pk_derivation`で導出方法を表す。sourceには`pk_source_type`を付け、ユーザー原文はUser Statement、作業経緯はInteraction Recordとして必要な場合だけ保存する。

`generated`は現在内容の生成者、`verified`は独立した確認者である。trust tierは`verified`から表示時に導出する。

## Learning mode

`manual`は明示的なupdate時だけ書き換える。`opportunistic`は作業単位完了時に候補を評価し、価値がある場合だけupdateする。`aggressive`は候補を広めに拾うが、一時情報と重複は除外する。

## 専用操作

askは`project-knowledge/docs/**`だけを情報源とし、不足時は推測しない。publishは再生成可能なMarkdownとoffline HTMLを出力する。内容の正しさは`verify`/`fix`、構造・品質は`audit`/`refactor`が、それぞれ検査のみ/検査と修正を担当する。書き込み操作へ自動昇格しない。
