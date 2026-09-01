# ナレッジ log

## 2026-09-01

### publish現在構造補完コミットのレビューを反映

- publishがKnowledgeの持続的な情報と現在のProject Artifactから確認できる実装構造を組み合わせる契約を、Skill概要へ反映した。
- 記述の重複には実行規則、品質ゲート、完了報告という役割の違いがあると判断し、仕様概要の`published/`説明に残る旧表現を未解決事項として記録した。
- 追加契約テストと`git diff --check`の成功、および全体テストに残る今回のコミットと無関係な既存失敗を記録した。

## 2026-08-31

### User Statementの反映ルールを追加

- User Statementを追加・更新した場合は、内容を関連するConceptなど他のナレッジにも必ず反映し、sourceとして残すルールをSkillとupdate手順へ追加した。
- このユーザー指示をUser Statementとして保存し、Skill概要Conceptへ同じ制約とsourceを反映した。

## 2026-08-29

### inspectを専用Skillへ分離して出力形式を変更

- `inspect`をメインSkillから`project-knowledge-inspect`へ分離し、Skill名の明示指定と自然言語の依頼に対応させた。
- 出力を概要、Knowledge文書だけのツリー、4区分の統計、Knowledge Policy設定の自然文説明で構成し、分離前の呼び出し方に関する記述を削除した。

### 標準Knowledge PolicyをSkill同梱Referenceへ分離

- 標準の収集・品質Policyを`references/standard-knowledge-policy.md`へ移し、生成される`knowledge-policy.md`本文は標準Policyに従う宣言と同梱参照だけを持つ形へ変更した。
- プロジェクト固有方針は本文へ記載して標準Policyより優先し、未指定部分には標準Policyを適用する。validatorの自由形式本文許容と既存Bundleを自動上書きしない境界は維持し、pytest 56件、Ruff、validator、`git diff --check`を通過してGit baselineを更新した。

### helpを専用Skillへ分離

- `help`をメインSkillから`project-knowledge-help`へ分離し、対象なし、対象指定、未知対象の定型出力を追加した。
- 基本操作表は6操作の用途、操作名指定、自然言語例を示し、利用者向け専用Skillは4つだけを案内する。旧形式の`$project-knowledge help`は新Skillへの案内だけを返す。

### Scenario Testを開発者向けディレクトリへ分離

- `project-knowledge-scenario-test`を一般ユーザー向けの`skills/`から`developer-tests/`へ移し、関連するsource参照を新しいパスへ更新した。
- 一般ユーザー向けSkillではなく開発者用テストであるという配置方針を、ユーザー指示と実装を根拠にKnowledgeへ記録した。

### helpとinspectを追加

- `help`をメイン操作と利用者向けSkillのread-only案内、`inspect`をKnowledge Baseの構造と格納情報のread-only説明として追加した。
- `inspect`を内容の正しさを扱う`verify`、構造品質を扱う`audit`、構造改善を行う`refactor`から分離し、別操作やSkillを自動実行しない境界を記録した。

## 2026-08-28

### Project Knowledge Utility Benchmarkを追加

- 任意Git repositoryの同一TaskをNo-Knowledge / With-Knowledgeで比較する明示実行Skill、worktree隔離、blind Judge、JSONL由来usage / AI Credit、結果artifact保持を記録した。
- README表記検証Taskのsingle-runでは両条件の機械評価がPASSし、JudgeはWith-Knowledge側を僅差で選好した。単一小Taskの観測を一般的効果として扱わない境界を保存した。

### Quick / Benchmarkのcredit計測を統一

- QuickとQuickベースBenchmarkのusage sourceをCodex session / rollout JSONLだけへ統一し、subagent sessionのbaseline差分とCodex creditsを記録した。
- 既存single-run Benchmarkを再計測し、Actor creditsによる比較とJudge共通costの分離、取得不能時の`unavailable`契約を保存した。

### Largeライフサイクルシナリオを追加

- Quickと同じ品質観点を人工Fixture、12 update、checkpoint Judge、step別のKnowledge規模とtoken usageで評価するLargeを記録した。
- 実行結果として、全stepのdeterministic validation、checkpoint Judge score、Actor/Judge別credit、初期・最終Knowledge規模、既知のFixture規模制約を保存した。

## 2026-08-27

### 通常初期化の品質ゲートを追加

- 通常初期化を骨組み生成だけで完了させず、代表sourceの調査と、保存価値がある場合の根拠付きConcept生成までを完了条件として記録した。
- Quickのdeterministic validationに`missing-concept`と`missing-project-artifact-source`を追加し、改善後の独立Actor/Judge実行が全観点PASSであることを記録した。

### QuickモデルBenchmarkを追加

- Quick fixtureを再利用するLuna/Terra/Solの比較、固定blind Judge、実測不能なActor tokenを`unavailable`とする契約を記録した。
- single-run `quick-basic`のdeterministic結果とJudge結果を、実行記録とともに保存した。

## 2026-08-26

### fixとrefactorを追加

- 内容・正しさを検査して修正する`fix`を`project-knowledge`へ追加した。
- 構造・品質を診断して保守的に改善する`refactor`を`project-knowledge-audit`へ追加した。
- `verify`と`audit`のread-only境界、書き込み操作への非自動昇格、`update`との責務境界を維持した。

### verifyの内容健全性検証を具体化

- verifyをStructure、Sources、Provenance、Evidence、Current State、Freshness、Consistencyの順で実行する契約へ具体化した。
- `pass`、`fail`、`warning`、`not-verifiable`、`stale`、`not-applicable`をreporting上の結果分類として定義した。
- 内容上の矛盾と構造上の重複、既存Knowledgeの検証と未登録Knowledgeのcoverage調査の境界を明文化した。

### verifyをメインスキルへ統合

- `project-knowledge-verify`を廃止し、read-onlyの正確性検証を`project-knowledge`の`verify`へ統合した。
- Skill群を、保守、限定回答、公開、構造監査の4責務へ整理した。
- `verify`と`update`の非自動連鎖、および`verify`と`audit`の責務境界を明文化した。

### 形式1.0専用へ簡略化

- 全Skillを2.0.0へ更新し、Project Knowledge形式1.0だけを扱う契約へ統一した。
- 旧形式の仕様、変換処理、互換分岐、テスト、Referenceを削除した。
- OKF v0.2の現行規約を形式1.0の仕様へ統合した。

### 追加の簡略化

- `project-knowledge-fast-ask`と`project-knowledge-audit`の手順を各`SKILL.md`へ統合し、専用Referenceを削除した。
- 形式判定の中継Reference、`config.local.yml`、未実装のrenderer/offline設定を削除した。
- `init --empty`、差分検出のbaseline/snapshot上書き、旧`--write-state` aliasを廃止し、固定された実装経路へ統一した。
