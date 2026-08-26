---
type: Project Knowledge Skill
pk_category: extracted
pk_derivation: synthesized
status: stable
generated:
  by: project-knowledge/0.4.0
  at: 2026-08-26 12:00:00+09:00
sources:
- resource: ../references/user-statements/project-knowledge-implementation-report.md
  pk_source_type: user-statement
- resource: ../references/user-statements/2026-08-26-index-content-boundary.md
  pk_source_type: user-statement
- resource: ../../../skills/project-knowledge/SKILL.md
  pk_source_type: change-implementation
- resource: ../../../skills/project-knowledge/references/update.md
  pk_source_type: change-implementation
---
# プロジェクトナレッジ Skill

## 責務と操作

メインの`project-knowledge`はKnowledgeを育てるSkillであり、`init`、`update`、`config`だけを扱う。Knowledge限定回答、成果物生成、正確性・鮮度検証、構造監査は、それぞれ`project-knowledge-fast-ask`、`project-knowledge-publish`、`project-knowledge-verify`、`project-knowledge-audit`へ分離している。

4つの専用Skillは`agents/openai.yaml`で`allow_implicit_invocation: false`とし、descriptionと本文でもexplicit-onlyを明記する。通常質問、一般的な要約、通常の実装レビュー、一般的な文書レビューからは自動発火させない。

ユーザーが提示した原文、会話から抽出した判断、実装差分、収集方針変更は、すべてupdate内で情報源を分類して処理する。User StatementとInteraction Recordはユーザー操作ではなく内部provenanceであり、旧`capture` / `memo`指定だけを互換入力としてupdateへ読み替える。旧`scope`指定はKnowledge Policyの表示・更新へ読み替える。

## IndexとConceptの境界

root・nested `index.md`はナビゲーション専用とし、タイトル、短い案内、リンク、リンク先を選ぶための短い説明だけを置く。独立して再利用できる事実、判断、制約、状態、検証結果は通常Conceptへ分離し、frontmatterで分類と根拠を保持する。

indexを更新するときは、追加する文章が単独の知識として成立しないか確認する。成立する場合は通常Conceptへ保存し、indexからリンクする。

## Knowledge Policyとopen-world

`project-knowledge/knowledge-policy.md`は対象領域のallow-listではなく、情報の将来価値を判断する収集・品質Policyである。プロジェクト固有性、再利用性、持続性、背景や理由、重要な制約、誤った場合の影響、明示的な保存指示を考慮する。

対象領域は固定せず、新しい機能、設計、運用情報に価値があればページやカテゴリを追加できる。肥大化はPolicy、重複回避、Incremental Update、Progressive Disclosureで抑え、必要な監査は専用Skillを明示的に使用する。

## Provenance

通常Conceptは`pk_category`で情報の種類、`pk_derivation`で導出方法を独立して表す。OKF標準外のProject Knowledge独自metadataには`pk_` prefixを付ける。sourceには`pk_source_type`を付け、主観的なauthorityやtrustは保存しない。ユーザー原文はUser Statement、作業経緯はInteraction Recordとして必要な場合だけ保存する。

`generated`は現在内容の生成者、`verified`は独立した確認者である。trust tierは`verified`から表示時に導出し、User Statementであることだけをhuman verificationとはみなさない。

すべてのupdateでReferenceを作る必要はない。ナレッジ本文の複製を避け、由来を保持する価値がある場合だけ作成する。

## Learning mode

`manual`は明示的なupdate時だけ書き換える。`opportunistic`は作業単位完了時に候補を評価し、ナレッジ-worthyな場合だけupdateする。`aggressive`は候補を広めに拾うが、一時情報・重複・逐語的なソース転記は除外する。

新規プロジェクトの既定値は`opportunistic`である。このリポジトリは旧`automatic_after_work: false`からの互換migrationにより`manual`を維持している。

## Initとmigration

通常initはscope指定を要求しない。初期ナレッジの指定は今回作る内容であり、将来の対象を制限しない。`--empty`では管理ファイルと最低限のナレッジ Bundleだけを作る。

manifestなしの既知構造を形式0.1として検出し、形式0.1または0.2への書込み前に形式0.3へ移行する。移行は事前競合検査、`--check`、同一内容統合、冪等な変換を備え、manifestを最後に書く。未知形式、より新しい形式、downgrade、未定義の移行先は変更せず拒否する。

既知形式の旧`scope.md` / `scope.yml`は、対象指定を「積極的な保存候補」、対象外・粒度条件を保存しない補足方針へ変換して`knowledge-policy.md`へ移す。未知schemaは保持して停止する。旧`update.automatic_after_work`はfalseをmanual、trueをopportunisticへ移す。

## Ask、Publish、Verify、Audit

askは`project-knowledge/docs/**`だけを情報源とし、不足時は推測や通常調査へフォールバックしない。回答にはKnowledge限定であることを明示する。

publishはMarkdownと`file://`対応のoffline HTMLを`project-knowledge/published/`へ生成し、Knowledgeへ逆同期しない。

verifyは常にread-onlyで、manifest、OKF、link、orphan、source、分類、導出方法、検証状態、stale、Policy適合性、実装との矛盾を確認する。成功時もverification event候補を報告するだけで、`verified`の保存はユーザーが反映を求めたupdateで行う。auditもread-onlyで、重複、一時情報、過剰なソース転記、粒度、不要Reference・カテゴリ、情報分散、index肥大化、Policy違反を確認する。

各Skillは別Skillを自動実行しない。verifyやauditの指摘を修正する場合は`project-knowledge`を案内し、update後もpublishを自動実行しない。

## 実装上の分離

意味理解が必要なナレッジ-worthy判定、provenance分類、文書統合、Policy変更はAgentが行う。初期構造・migration・差分検出はメインSkill、構造・provenance検証はverify Skill、HTML生成とCSSはpublish Skillが所有する。決定的な処理を複製せず、責務の所有先へ配置する。

## 検証実績

形式0.2移行後の自動テストは36件すべて成功した。
Python構文検査、5 SkillのCodex Skill検証、プロジェクトナレッジ validator、差分検査も成功した。
実リポジトリへのinit再実行は`no changes`となり、初期化とmigrationの冪等性を確認した。

テストはscopeなしinit、empty init、open-world Policy、opportunistic既定、旧scope移行、旧boolean設定移行、AGENTS更新、validatorのread-only性、provenance metadata、incremental diffを含む。
形式版についてはmanifest生成、0.1検出、check/apply、再実行、同一内容統合、競合時の無変更、未知版・新しい版・downgrade拒否、registryと仕様文書の対応を検査する。分類については4ケース、未検証・検証済みinference、User Statementとhuman verificationの非連動をfixtureで検査する。
メインSkillの3操作への限定、4 Skillのexplicit-only policy、情報源・read-only・非自動連携境界、publishのoffline設定も契約テストで確認した。

## 既知の制約

ナレッジ-worthy判定、会話からのInteraction Record抽出、ナレッジ統合は意味判断を伴うため、決定的スクリプトだけでは完全に検証できない。
未知形式の旧scopeはデータ損失を避けるため自動移行せず、元ファイルを保持して停止する。
旧`$project-knowledge ask|publish|verify|audit`は処理せず、対応する専用Skillの明示利用を案内する互換ガードだけを残している。
