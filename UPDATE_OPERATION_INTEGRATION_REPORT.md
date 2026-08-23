# プロジェクトナレッジ update操作統合・scope廃止 実装報告

## 1. 変更したファイル一覧

実装コミット`114beff`で次の36ファイルを変更した。

- `AGENTS.md`
- `PROJECT_KNOWLEDGE_IMPLEMENTATION_REPORT.md`
- `README.md`
- `SCOPE_INIT_CHANGE_REPORT.md`
- `project-knowledge/config.yml`
- `project-knowledge/docs/index.md`
- `project-knowledge/docs/log.md`
- `project-knowledge/docs/references/index.md`
- `project-knowledge/docs/skill/index.md`
- `project-knowledge/knowledge-policy.md`（追加）
- `project-knowledge/scope.md`（削除）
- `skills/project-knowledge/SKILL.md`
- `skills/project-knowledge/agents/openai.yaml`
- `skills/project-knowledge/references/architecture.md`
- `skills/project-knowledge/references/audit.md`
- `skills/project-knowledge/references/capture.md`（削除）
- `skills/project-knowledge/references/config.md`
- `skills/project-knowledge/references/data-model.md`
- `skills/project-knowledge/references/init.md`
- `skills/project-knowledge/references/knowledge-policy.md`（追加）
- `skills/project-knowledge/references/learning-modes.md`（追加）
- `skills/project-knowledge/references/memo.md`（削除）
- `skills/project-knowledge/references/provenance.md`（追加）
- `skills/project-knowledge/references/publishing.md`
- `skills/project-knowledge/references/scope.md`（削除）
- `skills/project-knowledge/references/update.md`
- `skills/project-knowledge/references/verification.md`
- `skills/project-knowledge/scripts/init_project.py`
- `skills/project-knowledge/scripts/validate_knowledge.py`
- `skills/project-knowledge/templates/agents-block.md`
- `skills/project-knowledge/templates/config.yml`
- `skills/project-knowledge/templates/index.md`
- `skills/project-knowledge/templates/knowledge-policy.md`（追加）
- `skills/project-knowledge/templates/reference-index.md`
- `skills/project-knowledge/templates/scope.md`（削除）
- `skills/project-knowledge/tests/test_project_knowledge.py`

この報告書`UPDATE_OPERATION_INTEGRATION_REPORT.md`は実装後の成果報告として別途追加した。

## 2. 廃止したコマンド

ユーザー向け操作から`capture`、`memo`、`scope`を廃止した。日常操作は`update`と`ask`、管理・保守操作は`init`、`publish`、`verify`、`audit`、`config`とした。

## 3. updateへ統合した処理

ユーザー提示情報、会話、実装・設定・schema・Git差分、既存ナレッジ、外部Reference、ナレッジ収集方針の変更を`update`へ統合した。入力分類、ナレッジ-worthy判定、必要なReference生成、ナレッジ統合、Information Architecture整理、index・log・state更新、validationまでを一つの内部フローとして定義した。

## 4. capture / memoを内部provenanceへ変更した方法

独立した操作Referenceであった`capture.md`と`memo.md`を削除し、`references/provenance.md`へ統合した。captureはユーザー原文の`primary` / `trusted`、memoは会話から意味的に抽出した`secondary` / `provisional`として維持する。ユーザーが内容を確定した場合、memoはprovenanceを維持したままtrustedへ昇格できる。

すべてのupdateでReferenceを生成せず、由来を保持する価値がある場合だけ作る。Referenceはナレッジ本文の複製にしない。

## 5. scopeを削除した方法

Skillの操作表、共通ルール、init、verify、audit、architecture、validator、templates、自己ナレッジからscope前提を削除した。`scope.md`、`scope.yml`をsource of truthとして生成・検査しない。対象領域は固定せず、ナレッジ Policyに反しない新領域を追加できるopen-world型にした。

## 6. knowledge-policy.mdの仕様

`project-knowledge/knowledge-policy.md`を管理ファイルとして導入した。対象domainのallow-listではなく、積極的に保存する情報、原則として保存しない情報、構成方針、プロジェクト固有の補足方針を記録する。

## 7. ナレッジ-worthy判定ルール

プロジェクト固有性、将来再利用性、持続性、コードだけでは分からない背景・理由、重要な制約・前提、運用や障害対応での反復利用、誤った場合の手戻り、明示的な保存指示を高価値シグナルとする。一時的なdebug、単発エラー、途中経過、rename、typo、formatting、逐語的なコード説明、一般論、重複は通常保存しない。

## 8. learning modeの仕様

- `manual`: 明示的なupdate intentがある場合だけ書き換える。
- `opportunistic`: 作業単位完了時に候補を評価し、価値がある場合だけupdateする。
- `aggressive`: opportunisticより広く候補を拾うが、一時情報・重複・ソース転記は除外する。

新規初期化の既定値は、安全性と自然な成長のバランスから`opportunistic`を採用した。

## 9. opportunisticモードの動作

毎ターン、毎ツール呼び出し、毎ファイル編集後には更新しない。調査、編集、テスト、修正を含む作業単位の完了時に一度だけ評価する。認証方式、必須環境変数、deploy、migration、外部連携、重要な設計判断、再利用可能なトラブルシューティングは候補とし、typoやformattingなどは更新しない。

## 10. 旧設定・旧scopeからのmigration

既知形式の`scope.md` / `scope.yml`は、対象指定を「積極的な保存候補」、対象外・粒度条件を保存しない補足方針へ移す。他領域を拒否する境界は引き継がない。未知schema、または旧scopeファイルが複数存在してsource of truthが曖昧な場合は、元ファイルを保持して停止する。

旧`update.automatic_after_work: false`は`learning.mode: manual`、trueはopportunisticへ変換する。既存`learning.mode`があればそれを優先する。このリポジトリ自身は旧false設定からmanualへ移行し、新規既定とは分けて後方互換性を保った。

## 11. verify / auditへの変更

verifyからscope検査を削除し、ナレッジ Policy適合性、低価値情報、現在ソースとの矛盾、provenance、capture/memo/source整合、broken link、orphan、stale、index、OKF、欠損Reference、provisional情報の誤用を確認するようにした。

auditは初回read-onlyを維持し、重複、一時情報、ソースコードの過剰転記、細かすぎる・巨大すぎる・古いナレッジ、不要Reference・カテゴリ、関連情報の分散、index肥大化、Policy違反を重点対象とした。

## 12. 実施したテスト

- Python構文検査: 成功
- pytest: 16件すべて成功
- Codex Skill `quick_validate.py`: `Skill is valid!`
- プロジェクトナレッジ validator: findingなし（`[]`）
- `git diff --cached --check`: 成功
- 実リポジトリへのinit再実行: `no changes`で冪等性を確認

テストにはscopeなしinit、empty init、open-world Policy、opportunistic既定、旧scope Markdown/YAML移行、未知schema保持、旧booleanのtrue/false移行、AGENTS更新、validator read-only、provenance metadata、公開操作契約、opportunisticの完了時評価・negative case、incremental diff、verify/auditのscope非依存を含む。

## 13. 後方互換性

旧`capture` / `memo`指定はprompt-levelのcompatibility aliasとして`update`へ、旧`scope`指定はナレッジ Policyの表示・更新へ読み替える。新仕様・操作表・READMEでは推奨コマンドとして案内しない。deprecatedなinit `--scope`は一時的に受け付けるが、値を永続的な境界として保存しない。

## 14. 残っている懸念事項

- ナレッジ-worthy判定、会話からのmemo抽出、ナレッジ統合は意味判断を伴うAgent処理であり、決定的スクリプトだけでは完全検証できない。今回は指示契約と観測可能なmigration・validationを自動テストした。
- 未知形式の旧scopeはデータ損失を避けるため自動移行せず停止する。利用者による内容確認と意味的移行が必要になる。
- compatibility aliasは独立CLIではなくSkillのルーティング規則である。旧操作名を恒久的に公開APIとして保証するものではない。
