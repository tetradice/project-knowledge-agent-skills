# ナレッジ log

## 2026-09-16

### 外部レイヤーパスを許可

- `layers[].path`でプロジェクト外へ出る相対パス、ローカル絶対パス、UNC、symlink／junctionで解決される外部レイヤーを登録できるようにした。環境変数、URL、`~`、globの拒否と、設定ファイルsymlink・実体パス重複の禁止は維持する。
- 外部の`read-write`レイヤーは初期化、通常更新、分割、復旧の登録済み対象である。操作記録には正規化済み絶対パスを使い、プロジェクトの`.gitignore`管理ブロックはプロジェクト内レイヤーだけを対象にする。

## 2026-09-15

### 複数レイヤーの初期化と分割フローを追加

- 複数レイヤーの`init`は確定した定義と配置表から全候補を準備・検査し、`project-knowledge.yaml`を最後に公開する。空初期化は本文収集だけを省略する。
- 単一レイヤーの`split`は、元と新規移管先の固定集合だけを対象にし、Conceptの一意な配置、共有Referenceのprovenance維持、最終配置からのリンク・source再計算を行う。
- 操作中はロック、原本、指紋、候補を用いて排他・入力変更検出・復旧を行う。通常の`verify`、`publish`、`audit`、`refactor`は自動起動しない。

### 初期化時の既定レイヤー名を固定

- `init_project.py`が生成する`id: default`レイヤーの`name`を`プロジェクトナレッジ`に固定した。既存の設定値や`name`の一般的な妥当性規則は変更しない。

## 2026-09-14

### 必須表示名を持つ複数レイヤー対応を記録

- `project-knowledge.yaml`は任意数のレイヤーを登録でき、各レイヤーに不変の`id`と必須の表示名`name`を持たせる。参照は全レイヤー、書込みは選択済みの1レイヤーだけを対象とする。
- AIは利用者向けの表示と自然言語選択に`name`を使い、`id`をCLI、根拠、state、キャッシュに維持する。`auto_select: false`のレイヤーは曖昧な自動選択から除外するが、明確な`name`または`id`指定なら選択できる。
- 今回は設定パーサと関連Skillの差分を根拠に更新し、利用者の指定に従ってテストとBenchmarkの詳細な再整備・検証は公開後の検討事項として残した。

### `access`省略時の既定値を更新

- レイヤーの`access`を省略した場合の既定値を`read-write`へ変更した。初期生成設定は最小構成のままとし、読み取り専用で運用するときだけ`access: read-only`を明示する。

### 通常利用Skillのリリース準備レビューを記録

- テスト・ベンチマーク系を除外した通常利用6 Skillのレビュー結果をInteraction Recordへ記録した。通常操作の実行不能や重大矛盾は検出していない一方、READMEのuv/Python 3.11前提、audit/refactorのUI上の明示性、Ruff import-orderをリリース前の対応事項として残した。

### リリース準備レビューのMedium指摘を解消

- READMEに通常利用のPython 3.11以上とuvの前提、およびNode.jsは`npx skills add`によるインストール専用である境界を追記した。
- audit UIの短い説明とdefault promptをread-only監査へ限定し、refactorとファイル変更を明示的に禁止した。テスト・ベンチマーク系Skillは今回も対象外とし、Ruff import-orderのLow指摘は未対応として残した。


### 未登録の旧来ナレッジの移行手順を追加

- `project-knowledge.yaml`がない旧来ナレッジは、既存ディレクトリを利用対象と推測せず、`init_project.py --prepare`で形式1.0のBundleを準備する。
- 旧来の内容を根拠付きConceptへ整理して確認した後、`--prepare`なしの`init_project.py`で設定を登録する。設定の版は利用者の明示指示なしに上げない。

## 2026-09-13

### 独立した版契約とリリース境界を記録

- Project Knowledge設定、各Skill、Knowledge形式、OKF、state schemaの版は独立した契約であり、関連する変更だけで連動して上げないことを記録した。
- 現在のSkill版と、リポジトリ全体のリリースmanifest、changelog、Git tagが未定義である境界を記録した。Skill版をリポジトリリリース版として扱うには、明示的なリリース運用が必要である。

### Project Knowledgeのルート設定を追加

- `project-knowledge.yaml`をProject Knowledge利用の必須入口とし、設定がなければ既存ディレクトリやmanifestから対象を推測しない方針を記録した。
- ルート設定の必須`version: "1.0"`、`layers`、レイヤーの`id`・`path`、初期実装の0〜1レイヤー制限、`default`以外のdescription要件を記録した。ユーザー指示なしに版を上げない。
- 初期生成設定は生成元コメントと必須の最小項目だけを含み、`access`省略時は`read-only`となる。書き込みには`access: read-write`を明示する。

## 2026-09-03

### ファイル変更報告の表示名を日本語化

- 利用者向けの`Knowledge`と`Provenance`を「ナレッジ文書」「根拠資料」とし、内訳も日本語で表示するようにした。
- 内部値は維持し、`derived`の表示名は利用者指定どおり「分析の結果」とした。
- User Statementと実装経緯を保存し、分類報告の契約テストおよびUTF-8モードでのSkill validatorの成功を記録した。

## 2026-09-02

### init / updateのファイル変更報告を追加

- `Knowledge`、`Provenance`、`Support`、`Internal`の共通分類を独立Referenceへ定義し、通常Conceptは`pk_category`、Referenceは文書自身の`pk_source_type`で内訳を示すようにした。
- initとupdateは分類Referenceを参照して完了報告に件数を出す。利用者向けの件数と合計は`Knowledge`と`Provenance`だけで計算し、`Support`と`Internal`は表示しない。
- この方針をUser Statementと実装経緯として保存し、契約テストの成功と、今回未変更の標準Policy文言に残る既存テスト失敗を記録した。

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
