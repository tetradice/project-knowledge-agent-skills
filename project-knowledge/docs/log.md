# ナレッジ log

## 2026-08-26

### 仕様相談用テキストの再生成契約を追加

- Project Knowledgeスキル群の仕様概要を外部チャットへ相談するための文書構成を記録した。
- データフォーマット、独自metadata、バージョニング、`config.yml`を詳しく扱い、現行バージョン番号を載せない方針を明文化した。
- 短い自然言語の依頼から`project-knowledge-spec-overview.md`を現行仕様で再作成する手順と確認事項を追加した。

### Project Knowledge形式0.3と`pk_` metadata規約を反映

- Knowledge形式を`0.3`へ更新し、Project Knowledge独自のfrontmatter fieldを`pk_` prefixへ統一した。
- `0.1`および`0.2`から`0.3`へのmigration、形式validator、テンプレート、回帰テストを同じ規約へ同期した。
- 関連5 Skillの版とREADMEを更新し、既存のSkill概要と形式Knowledgeを0.3の契約へ移行した。
- 実装はcommit `7459031`で完了した。テスト結果はこの更新時点で未再検証である。

### indexと通常Conceptの配置境界を明確化

- メインSkillを`0.3.0`へ更新し、root・nested `index.md`をナビゲーション専用とした。
- 独立した知識をfrontmatter付き通常Conceptへ分離するupdate契約と回帰テストを追加した。
- `docs/skill/index.md`の既存本文を`overview.md`へ移し、分類、導出、生成actor、sourcesを付与した。
- 実装はcommit `6d51cbd`で完了し、pytest 36件、Skill validation、差分検査を通過した。

### Project Knowledge形式0.2へ移行

- 関連5 Skillへ独立したSemVer `0.2.0`を設定した。
- Knowledge形式`0.2`のmanifest、分類・導出・source type、OKF v0.2、state schema版の分離を導入した。
- 競合時に変更しない0.1→0.2 migration CLIとYAML validatorを追加した。
- repository自身のReference保存先、reserved files、provenanceを0.2へ移行した。
- 実装はcommit `45f45b6`で完了し、pytest 36件、5 Skill validation、Knowledge validator、migration再実行check、Ruff、差分検査を通過した。

## 2026-08-25

### Knowledge限定回答Skillを改名

- `project-knowledge-ask`を`project-knowledge-fast-ask`へ改名した。
- Skillの明示呼び出し契約、AGENTS.md生成テンプレート、README、回帰テスト、Project Knowledgeのsource参照を新名称へ同期した。

## 2026-08-25

### Project Knowledgeを5 Skillへ責務分割

- メインSkillを`init`、`update`、`config`へ純化し、ask、publish、verify、auditを専用Skillへ分離した。
- 4つの専用Skillをexplicit-onlyにし、暗黙発火、情報源フォールバック、検出後の自動更新、update後の自動publishを禁止した。
- offline HTML生成処理はpublish、構造検証処理はverifyへ移し、AGENTS.mdの初期化テンプレートと利用例を新構成へ更新した。

## 2026-08-23

### verify操作のmemoを現行Policyに同期

verify操作のmemoから旧`scope`を現行のプロジェクトKnowledge Policyへ置き換えた。検証対象、Information Architectureとの分離、索引説明を現行Skillの`verification.md`に合わせた。

## 2026-08-23

### update操作統合の実装報告を同期

- 対象: `docs/skill/index.md`
- 内容: 実装報告をprovenanceへ追加し、16件の自動テストを含む検証実績と、意味判断・未知scope・互換aliasに関する既知の制約を反映。
- 根拠: [初期実装報告のRaw Reference](references/user-statements/project-knowledge-implementation-report.md)

## 2026-08-23

### update統合・scope廃止・Knowledge Policy導入

- 対象: プロジェクトナレッジ Skillの操作体系、provenance、Policy、learning mode、migration、verify、audit
- 内容: ナレッジ書き込みをupdateへ統合し、capture/memoを内部provenanceへ変更。scopeを廃止してopen-world型のKnowledge Policyを導入し、新規既定をopportunisticとした。
- 移行: このリポジトリの旧scopeをPolicyへ意味的に変換し、`automatic_after_work: false`は互換性のため`learning.mode: manual`へ移行。
- 根拠: `skills/project-knowledge/`のSkill、references、templates、scripts、tests

## 2026-08-23

### verify操作の検証範囲を記録

- 対象: `verify` 操作
- 内容: read-only性、構造・鮮度・scope適合性・Information Architectureの検査範囲と、High/Medium/Lowによる報告形式をprovisional memoへ記録。
- 根拠: `skills/project-knowledge/references/verification.md`、`docs/skill/index.md`

## 2026-08-23

### 初期化と実装報告の取り込み

- 対象: `PROJECT_KNOWLEDGE_IMPLEMENTATION_REPORT.md`
- 内容: ナレッジ基盤を初期化し、レポートをtrusted captureとして保存。レポートに基づくSkill概要を追加。
- 根拠: [プロジェクトナレッジ Agent Skill 実装報告](references/user-statements/project-knowledge-implementation-report.md)

## 2026-08-23

### scopeとInformation Architectureの分離

- 対象: プロジェクトナレッジ Skillのscope、init、Information Architecture、verify、audit
- 内容: 通常initのscope必須化、empty init、`scope.md`、旧scope移行、scopeと`docs/`構造の非1対1化を反映。
- 根拠: `skills/project-knowledge/`のSkill、references、scripts、tests

## 2026-08-23

### scope仕様のナレッジ同期

- 対象: `docs/index.md`と`docs/skill/index.md`
- 内容: 現在のscopeに合わせて入口を修正し、scopeの状態、Information Architectureとの分離、旧scope移行、verifyとauditの評価基準をナレッジ本文へ反映。
- 根拠: `project-knowledge/scope.md`、`skills/project-knowledge/SKILL.md`、関連references、init script
