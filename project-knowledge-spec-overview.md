# Project Knowledgeスキル群の現行仕様（相談用概要）

最終更新日：2026-08-26

外部のチャットへ設計相談するために、現在の仕様を要約したものです。

## 目的

Project Knowledgeは、リポジトリ固有の仕様、設計判断、運用知識、検証結果を、AIと人間が再利用できるMarkdownのKnowledge Baseとしてプロジェクト内に蓄積する仕組みです。
会話履歴をそのまま保存するのではなく、将来も価値がある情報だけを選び、根拠と導出方法を残しながら更新します。

## 4つのスキル

責務の混在と意図しない副作用を避けるため、保守、限定回答、公開、構造監査・構造改善を4つのSkillに分離しています。

| スキル | 主な責務 | 呼び出し方 |
| --- | --- | --- |
| `project-knowledge` | 初期構築、Knowledgeの追加と更新、内容・根拠・鮮度・形式の検証と修正、設定変更 | 自然言語の依頼から使用可能。verify/fixは明示的な検査・修正依頼時だけ |
| `project-knowledge-fast-ask` | Knowledgeだけを根拠に回答 | 明示指定のみ |
| `project-knowledge-publish` | 人間向けMarkdownまたはオフラインHTMLを生成 | 明示指定のみ |
| `project-knowledge-audit` | 重複、肥大化、分断、検索性を監査し、明示時は保守的にrefactor | 明示指定のみ |

メインスキルは`init`、`update`、`verify`、`fix`、`config`を扱います。
`init`は空のKnowledge Baseを作る初期構築、`update`は新しい情報・実装差分・収集方針の反映、`config`は既知の運用設定の表示・変更を担います。`pk_category`、`pk_derivation`、source種別は、利用者に選択を求めず、入力と根拠からスキルが判定します。
保守操作は次の認知モデルで分けます。

| 観点 | 検査のみ | 検査＋修正 |
| --- | --- | --- |
| Knowledge内容の正しさ | `verify` | `fix` |
| Knowledge Baseの構造・品質 | `audit` | `refactor` |

`verify`は既存Knowledgeの内容健全性を、形式、source、provenance、根拠、現在状態、鮮度、Knowledge間の意味的整合性の順にread-onlyで確認します。`fix`は同じ観点で明白な問題を修正して再検査します。`audit`は重複・肥大化・分断・検索性などをread-onlyで診断し、`refactor`は意味・source・provenanceを維持しながら構造を改善して再診断します。

各操作とほかの3スキルは互いを自動実行しません。`verify`から`fix`、`audit`から`refactor`へ自動昇格せず、書き込みはユーザーが`update`、`fix`、`refactor`を明示的に意図した場合だけ行います。`project-knowledge-audit`はexplicit-onlyを維持し、一般的な「整理して」「改善して」から自動実行しません。

この境界により、「保守（構築・追加・更新・検証・修正・設定）」「限定回答」「公開」「構造監査・構造改善」を個別に制御できます。

## データフォーマット

Knowledge Baseは各プロジェクトの`project-knowledge/`に置きます。
中心となる`docs/`はOKF（Open Knowledge Format）互換のMarkdown群で、次の管理ファイルと生成先を組み合わせます。

| パス | 役割 |
| --- | --- |
| `manifest.yml` | Project Knowledge形式と形式版の宣言 |
| `docs/` | Concept、Reference、ナビゲーション、更新履歴 |
| `knowledge-policy.md` | Knowledgeをどう育てるか。frontmatterに運用設定、本文に収集・品質方針を持つ |
| `state.yml` | 増分更新用の再構築可能なworking copy固有状態。Knowledgeの正本ではなく通常はcommitしない |
| `published/` | Knowledgeから再生成した公開成果物 |
| `.cache/` | 非Git環境のhash snapshotなど、再生成できるworking copy固有データ |

`index.md`は案内とリンクだけを持つナビゲーション専用ページです。

`state.yml`は`state_schema_version`と`git_baseline_commit`を持ちます。Git baselineは完全object IDで保存し、利用時にcommitとして解決でき、現在HEADの祖先であることを確認します。無効なら全tracked fileのフルスキャンへ戻ります。Knowledge本文・index・logの更新とvalidationがすべて成功した後だけbaselineを進めます。staged、working tree、untrackedはcheckpointしないため、commitされるまで再検出され得ます。非Git環境では`project-knowledge/.cache/source-snapshot.json`を使い、欠落・破損時は空snapshotから再生成します。
単独で再利用できる事実、判断、制約、状態、検証結果は、frontmatter付きのConceptへ分離します。
人間の原文はUser Statement、作業経緯はInteraction Record、外部文書や既存資料はReferenceとして、必要な場合だけ根拠側に残します。

通常のConceptは、少なくともOKFの`type`と、Project Knowledge独自の`pk_category`、`pk_derivation`を持ちます。
必要に応じて、成熟度を表す`status`、生成主体と日時を表す`generated`、独立した確認主体と日時を表す`verified`、根拠を列挙する`sources`、陳腐化を表す`stale`や`stale_after`などのOKFメタデータを加えます。
`sources`の各要素は、参照先の`resource`と独自メタデータの`pk_source_type`を必須とします。

```yaml
---
type: Project Knowledge Guide
pk_category: extracted
pk_derivation: synthesized
status: stable
generated:
  by: project-knowledge/<SemVer>
  at: <ISO 8601 timestamp>
sources:
  - resource: ../../README.md
    pk_source_type: project-artifact
---
```

Raw Referenceは`type: Reference`と`pk_source_type`を持ち、通常Conceptの分類対象にはしません。
管理ファイルである`manifest.yml`、`state.yml`のキーと、`knowledge-policy.md`の運用設定はOKF Concept metadataではないため、`pk_`接頭辞の対象外です。

## 独自メタデータ

OKF標準にないProject Knowledge固有のfrontmatterには、由来を判別できるよう`pk_`接頭辞を付けます。
現在の仕様で定義する独自メタデータは次のとおりです。

| メタデータ | 値 | 意味 |
| --- | --- | --- |
| `pk_category` | `declared` | 人がプロジェクト固有の方針、判断、意図として宣言した情報 |
|  | `extracted` | Referenceやプロジェクト内の成果物に明記された事実を抽出した情報 |
|  | `derived` | 情報の統合、計算、解釈、推論によって得た情報 |
| `pk_derivation` | `direct` | 一つのsourceから意味を変えず直接記録した |
|  | `synthesized` | 複数のsourceまたは複数箇所を整理して統合した |
|  | `inferred` | sourceに明記されていない結論を推論した |
| `pk_source_type` | `user-statement` | ユーザーが会話で宣言したプロジェクト固有情報 |
|  | `reference-document` | ユーザーが提供した外部文書や補助文書 |
|  | `project-artifact` | リポジトリ内のコード、設定、文書 |
|  | `interaction-record` | 会話や作業経緯の記録 |
|  | `change-implementation` | 実装された変更そのもの |

`pk_category`は「どの種類の情報か」、`pk_derivation`は「根拠からどう作ったか」を表す独立した軸です。
たとえば、複数の設計資料に明記された内容を統合した場合は、`extracted`かつ`synthesized`になります。

未検証の`inferred`は`status: draft`にします。
検証後も、推論から生まれたという来歴を`direct`へ書き換えません。
直接確認できる主張と推論が一つのConceptに混在する場合は、可能ならConceptを分割し、分割できなければ文書全体へ保守的な導出方法とstatusを設定します。

主観的な格付けとなる`pk_authority`や`pk_trust`は保存しません。

## 保存と更新の考え方

Knowledge Policyは対象分野の固定リストではなく、情報の将来価値を判断する方針です。
プロジェクト固有性、再利用性、持続性、背景や理由、重要な制約、誤りによる影響、明示的な保存指示を基準にします。
秘密情報、一時的な状態、デバッグ出力、重複、原文の不要な丸写しは原則として保存しません。

更新頻度は`manual`、`opportunistic`、`aggressive`の3段階です。
既定は、作業単位の完了時に候補を一度だけ評価する`opportunistic`です。
このスキル群自身のKnowledge Baseは`manual`です。

## 根拠と信頼性

`generated`は内容を生成または更新した主体、`verified`は独立して確認した主体です。
ユーザー発言を保存したこと自体は、人による検証とは扱いません。
主観的な信頼度は保存せず、表示時に`verified`から未検証、機械確認済み、人間レビュー済みを導出します。

## バージョニングと互換性

用途が異なる4種類の版を、次のSource of Truthで独立して管理します。

| 版 | Source of Truth | 形式 | 変更対象 |
| --- | --- | --- | --- |
| Skill版 | 各`SKILL.md`の`metadata.version` | SemVer `MAJOR.MINOR.PATCH` | Skillが外部へ示す操作、入出力、対応形式、安全境界 |
| Knowledge形式版 | `manifest.yml`の`format_version` | `MAJOR.MINOR` | `project-knowledge/`ディレクトリのデータ形式 |
| OKF版 | `docs/index.md`の`okf_version` | OKF仕様に従う | `docs/`内のBundle規約 |
| state schema版 | `state.yml`の`state_schema_version` | 整数 | 差分検出などの内部状態 |

Skill版のPATCHは公開動作を変えない修正、MINORは後方互換な機能の追加、MAJORは操作、入出力、対応形式、安全境界の非互換変更に使います。
関連スキルは同じ版へ揃えず、変更の影響を受けたスキルだけを更新します。

Knowledge形式版のMINORは、既存readerが安全に無視または解釈できる互換な追加、MAJORは既存readerが安全に解釈できない変更に使います。
形式を変更する場合は、形式仕様と対応Skill版を同時に更新します。現在は形式1.0だけを扱い、manifestがない、壊れている、形式名または版が異なる場合は推測せず停止します。

## Knowledge Policyの設定

`knowledge-policy.md`は「Knowledgeをどう育てるか」を一箇所で表します。機械が読む運用設定はYAML frontmatter、人間とAIが読む収集・品質方針はMarkdown本文に置きます。設定変更時は管理する既知キーだけを変更し、本文、コメント、未知キーを保持します。

```yaml
---
knowledge:
  human_readable: false
learning:
  mode: opportunistic
---
```

| キー | 設定内容 |
| --- | --- |
| `knowledge.human_readable` | `true`なら人がそのまま読める文章を優先する。`false`ならAIの検索効率、簡潔さ、構造、重複回避を優先するが、断片的にはしない |
| `learning.mode` | `manual`は明示的な更新依頼時だけ評価する。`opportunistic`は作業単位の完了時に価値のある候補だけを評価する。`aggressive`は候補を広めに拾うが、一時情報や重複は除外する |

`learning.mode`は設定ファイル名やキーを指定しなくても、「今後は自動的に更新して」「明示時だけ更新して」のような自然言語の依頼から変更できます。

収集方針を変える自然言語の依頼は`update`としてPolicy本文へ反映します。これに対し、publishの出力形式と対象範囲は実行時だけの指定であり、Knowledge Baseへ保存しません。

共有publish設定は使用しません。publishは既定でMarkdownとMaterial for MkDocsによるoffline HTMLを生成し、Knowledge本文へ逆同期しません。

## 仕様相談で検討したい論点

- 4スキルへの分離は、安全性と分かりやすさに対して適切か。verifyをメインスキルの独立した保守操作とする境界は明確か。
- Knowledge Policyによるopen-worldな収集は、対象領域を固定する方式より長期運用に向いているか。
- `pk_category`と`pk_derivation`の二軸は、実務で扱える複雑さに収まっているか。
- User Statement、Interaction Record、Reference、Conceptの分離は、根拠追跡と保守コストの釣り合いが取れているか。
- `verify`/`fix`と`audit`/`refactor`の対は、日常的な修正の簡便さと書き込み境界の安全性を両立できているか。
- `opportunistic`な自動学習を「毎ターン」ではなく「作業単位の完了時」に限定する境界は明確か。
- Skill版、Knowledge形式版、OKF版、state schema版の分離は、変更判断を明確にする効果と運用負荷が釣り合っているか。
- 運用設定と意味的なPolicyを`knowledge-policy.md`にまとめた認知モデルは、利用者が迷わず変更できるか。
