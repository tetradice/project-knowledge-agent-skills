---
title: "プロジェクトナレッジ Skill"
description: "5 Skillの責務分割、explicit-only境界、update、provenance、Policy、learning modeを確認するときに読む"
version: "0.3.1"
generated:
  by: project-knowledge
  at: 2026-08-25T08:40:19+09:00
sources:
  - id: skill
    resource: "../../../skills/project-knowledge/SKILL.md"
  - id: init-script
    resource: "../../../skills/project-knowledge/scripts/init_project.py"
  - id: update-rules
    resource: "../../../skills/project-knowledge/references/update.md"
  - id: provenance-rules
    resource: "../../../skills/project-knowledge/references/provenance.md"
  - id: policy-rules
    resource: "../../../skills/project-knowledge/references/knowledge-policy.md"
  - id: learning-rules
    resource: "../../../skills/project-knowledge/references/learning-modes.md"
  - id: fast-ask-skill
    resource: "../../../skills/project-knowledge-fast-ask/SKILL.md"
  - id: publish-skill
    resource: "../../../skills/project-knowledge-publish/SKILL.md"
  - id: verification-skill
    resource: "../../../skills/project-knowledge-verify/SKILL.md"
  - id: audit-skill
    resource: "../../../skills/project-knowledge-audit/SKILL.md"
  - id: update-operation-integration-report
    resource: "../../../UPDATE_OPERATION_INTEGRATION_REPORT.md"
---

# プロジェクトナレッジ Skill

## 責務と操作

メインの`project-knowledge`はKnowledgeを育てるSkillであり、`init`、`update`、`config`だけを扱う。Knowledge限定回答、成果物生成、正確性・鮮度検証、構造監査は、それぞれ`project-knowledge-fast-ask`、`project-knowledge-publish`、`project-knowledge-verify`、`project-knowledge-audit`へ分離している。

4つの専用Skillは`agents/openai.yaml`で`allow_implicit_invocation: false`とし、descriptionと本文でもexplicit-onlyを明記する。通常質問、一般的な要約、通常の実装レビュー、一般的な文書レビューからは自動発火させない。

ユーザーが提示した原文、会話から抽出した判断、実装差分、収集方針変更は、すべてupdate内で情報源を分類して処理する。`capture`と`memo`はユーザー操作ではなく内部provenanceであり、旧`capture` / `memo`指定だけを互換入力としてupdateへ読み替える。旧`scope`指定はナレッジ Policyの表示・更新へ読み替える。

## ナレッジ Policyとopen-world

`project-knowledge/knowledge-policy.md`は対象領域のallow-listではなく、情報の将来価値を判断する収集・品質Policyである。プロジェクト固有性、再利用性、持続性、背景や理由、重要な制約、誤った場合の影響、明示的な保存指示を考慮する。

対象領域は固定せず、新しい機能、設計、運用情報に価値があればページやカテゴリを追加できる。肥大化はPolicy、重複回避、Incremental Update、Progressive Disclosureで抑え、必要な監査は専用Skillを明示的に使用する。

## Provenance

ユーザー原文を保存する必要がある場合はcaptureとして`primary` / `trusted`、会話から意味的に抽出した判断材料はmemoとして`secondary` / `provisional`にする。ユーザーが内容を確定した場合、memoはprovenanceを維持したままtrustedへ昇格できる。

すべてのupdateでReferenceを作る必要はない。ナレッジ本文の複製を避け、由来を保持する価値がある場合だけ作成する。

## Learning mode

`manual`は明示的なupdate時だけ書き換える。`opportunistic`は作業単位完了時に候補を評価し、ナレッジ-worthyな場合だけupdateする。`aggressive`は候補を広めに拾うが、一時情報・重複・逐語的なソース転記は除外する。

新規プロジェクトの既定値は`opportunistic`である。このリポジトリは旧`automatic_after_work: false`からの互換migrationにより`manual`を維持している。

## Initとmigration

通常initはscope指定を要求しない。初期ナレッジの指定は今回作る内容であり、将来の対象を制限しない。`--empty`では管理ファイルと最低限のナレッジ Bundleだけを作る。

既知形式の旧`scope.md` / `scope.yml`は、対象指定を「積極的な保存候補」、対象外・粒度条件を保存しない補足方針へ変換して`knowledge-policy.md`へ移す。未知schemaは保持して停止する。旧`update.automatic_after_work`はfalseをmanual、trueをopportunisticへ移す。

## Ask、Publish、Verify、Audit

askは`project-knowledge/docs/**`だけを情報源とし、不足時は推測や通常調査へフォールバックしない。回答にはKnowledge限定であることを明示する。

publishはMarkdownと`file://`対応のoffline HTMLを`project-knowledge/published/`へ生成し、Knowledgeへ逆同期しない。

verifyは常にread-onlyで、OKF、link、orphan、source、stale、provenance、Policy適合性、実装との矛盾、provisional情報の扱いを確認する。auditもread-onlyで、重複、一時情報、過剰なソース転記、粒度、不要Reference・カテゴリ、情報分散、index肥大化、Policy違反を確認する。

各Skillは別Skillを自動実行しない。verifyやauditの指摘を修正する場合は`project-knowledge`を案内し、update後もpublishを自動実行しない。

## 実装上の分離

意味理解が必要なナレッジ-worthy判定、provenance分類、文書統合、Policy変更はAgentが行う。初期構造・migration・差分検出はメインSkill、構造・provenance検証はverify Skill、HTML生成とCSSはpublish Skillが所有する。決定的な処理を複製せず、責務の所有先へ配置する。

## 検証実績

責務分割後の自動テストは18件すべて成功した。
Python構文検査、5 SkillのCodex Skill検証、プロジェクトナレッジ validator、差分検査も成功した。
実リポジトリへのinit再実行は`no changes`となり、初期化とmigrationの冪等性を確認した。

テストはscopeなしinit、empty init、open-world Policy、opportunistic既定、旧scope移行、旧boolean設定移行、AGENTS更新、validatorのread-only性、provenance metadata、incremental diffを含む。
メインSkillの3操作への限定、4 Skillのexplicit-only policy、情報源・read-only・非自動連携境界、publishのoffline設定も契約テストで確認した。

## 既知の制約

ナレッジ-worthy判定、会話からのmemo抽出、ナレッジ統合は意味判断を伴うため、決定的スクリプトだけでは完全に検証できない。
未知形式の旧scopeはデータ損失を避けるため自動移行せず、元ファイルを保持して停止する。
旧`$project-knowledge ask|publish|verify|audit`は処理せず、対応する専用Skillの明示利用を案内する互換ガードだけを残している。
