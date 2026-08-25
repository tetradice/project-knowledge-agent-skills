---
title: プロジェクトナレッジ Agent Skill 実装報告
description: プロジェクトナレッジ Skillの初期実装に関するユーザー指定レポートの原文
version: 0.1.0
generated:
  by: project-knowledge/0.1.0
  at: 2026-08-23 00:00:00+00:00
pk_source_type: user-statement
type: Reference
---
# プロジェクトナレッジ Agent Skill 実装報告

## 1. 作成・変更したファイル

- `skills/project-knowledge/SKILL.md`: 操作ルーティング、共通安全規則、Progressive Disclosure
- `skills/project-knowledge/agents/openai.yaml`: UI metadata
- `skills/project-knowledge/references/*.md`: architecture、data model、OKF、10操作の詳細手順
- `skills/project-knowledge/templates/*`: 初期設定、state、index、log、capture、memo、AGENTS管理ブロック
- `skills/project-knowledge/scripts/init_project.py`: 非破壊・冪等初期化
- `skills/project-knowledge/scripts/detect_changes.py`: Git/hash差分検出
- `skills/project-knowledge/scripts/validate_knowledge.py`: read-only構造検証
- `skills/project-knowledge/scripts/build_offline_docs.py`: Material for MkDocsオフラインHTML生成・検証
- `skills/project-knowledge/assets/offline-docs.css`: ローカル表示用CSS
- `skills/project-knowledge/tests/test_project_knowledge.py`: fixtureベースの単体テスト
- `skills/project-knowledge/.gitignore`: Pythonテスト生成物の除外

## 2. Skill全体のアーキテクチャ

一つの`project-knowledge` Skillへ全操作を集約した。`SKILL.md`は操作選択と不変条件だけを持ち、操作固有の判断は`references/`から必要時だけ読む。初期データは`templates/`、決定的な初期化・差分検出・検証・HTML生成は`scripts/`へ分離した。

利用先では`project-knowledge/docs/`をOKF ナレッジ Bundleのsource of truthとし、Reference、再生成可能な`published/`、補助的な`.cache/`を分離する。

## 3. 各コマンドの処理概要

- `init`: 基盤、index、log、Reference index、設定、state、AGENTS管理ブロックを非破壊で作成する。
- `capture`: ユーザー原文をtrustedな一次情報として保存し、関連範囲だけ更新する。
- `memo`: 会話から再利用価値のある判断をprovisionalな二次情報として保存する。
- `update`: Gitまたはhash差分から影響範囲だけを同期する。
- `ask`: `project-knowledge/docs/**`だけを根拠に回答する。
- `scope`: 対象範囲を表示・追加・除外し、除外文書は即削除しない。
- `config`: 共通設定とローカル設定を優先順位どおり表示・変更する。
- `publish`: 人間向けMarkdownとオフラインHTMLを再生成する。
- `verify`: 形式、リンク、source、鮮度、矛盾をread-only検査する。
- `audit`: 重複、肥大化、陳腐化、統合候補を初回read-onlyで報告する。

## 4. 設定ファイルの仕様

優先順位はコマンド指定、`config.local.yml`、`config.yml`、Skill既定値の順。`knowledge.human_readable`、`update.automatic_after_work`、`memo.require_approval_for_trust`、Markdown publish、HTMLのenabled/renderer/offlineを定義した。`config.local.yml`はGit除外対象である。

## 5. Git連携方法

`detect_changes.py`はbaseline commitからHEAD、staged、working tree、untrackedを統合する。Gitがない場合は内容hash snapshotを利用する。snapshot更新は`--write-state`明示時だけ行い、通常の検査はread-onlyである。

## 6. OKFへの対応方法

`docs/index.md`と`docs/log.md`を必須とし、ナレッジ文書にtitle、description、version、generatedを要求する。`sources`で相対パスのprovenanceを保持し、必要に応じてverifiedとstale_afterを扱う。capture/memoの性質は`pk_source_kind`、`pk_authority`、`pk_trust`で区別する。

## 7. HTML publishの方式

HTML生成はこのSkill内の`build_offline_docs.py`が担当する。PEP 723でMaterial for MkDocs 9系を固定し、offline/search/privacy plugin、`use_directory_urls: false`、ローカルCSSを用いる。生成後にindex、offline検索index、外部アセット、ルート絶対URL、サイト外参照、broken linkを検証する。別Skillへの依存・委譲はない。

## 8. 実施したテスト

- Skill validator: 成功
- Python構文検証: 成功
- 単体テスト: 5件成功
- init再実行の冪等性と既存AGENTS保持: 成功
- validatorのread-only性: 成功
- Gitあり・Gitなし差分検出: 成功
- HTML設定の外部アセット非依存: 成功
- 実Material for MkDocsビルド: 5ページ、警告0、broken link 0、エラー0
- SKILL.mdからのreference link検査: 欠落0

## 9. 残っている制約・懸念事項

capture、memo、ナレッジ分割、矛盾説明、Markdown publishは意味理解が必要なためAgentの判断として実装した。`validate_knowledge.py`は構造上の不備を決定的に検出するが、主張の意味的矛盾やscope適合性はAgentによる確認が必要である。Material for MkDocs 9系は上流からMkDocs 2.0に関する将来互換性警告が表示されるため、依存上限を10未満に固定した。

## 10. 今後改善できる点

実利用fixtureを増やし、複雑な相対source、anchor link、stale判定、公開時の機密Reference除外を検証できる。renderer交換が必要になった時点で、`publishing.md`の契約を保った別実装を追加できる。

## 主な設計判断

旧版の内容は設計根拠に使わず、今回の依頼を基準に再構成した。HTML生成をSkill内へ含めるため、外部Skillへの委譲をなくした。一方、意味理解を要する処理までCLI化すると誤った自動更新やscope拡張を招くため、決定的処理だけをscript化し、ユーザー制御を保った。
