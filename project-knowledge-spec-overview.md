# Project Knowledgeスキル群の現行仕様（相談用概要）

最終更新日：2026-08-26

外部のチャットへ設計相談するために、現在の仕様を要約したものです。

## 目的

Project Knowledgeは、リポジトリ固有の仕様、設計判断、運用知識、検証結果を、AIと人間が再利用できるMarkdownのKnowledge Baseとしてプロジェクト内に蓄積する仕組みです。
会話履歴をそのまま保存するのではなく、将来も価値がある情報だけを選び、根拠と導出方法を残しながら更新します。

## 5つのスキル

責務の混在と意図しない副作用を避けるため、操作を5つに分離しています。

| スキル | 主な責務 | 呼び出し方 |
| --- | --- | --- |
| `project-knowledge` | 初期構築、Knowledgeの追加と更新、設定変更 | 自然言語の依頼から使用可能 |
| `project-knowledge-fast-ask` | Knowledgeだけを根拠に回答 | 明示指定のみ |
| `project-knowledge-publish` | 人間向けMarkdownまたはオフラインHTMLを生成 | 明示指定のみ |
| `project-knowledge-verify` | 現在の実装との整合性、鮮度、形式を読み取り専用で検証 | 明示指定のみ |
| `project-knowledge-audit` | 重複、肥大化、分断、検索性を読み取り専用で監査 | 明示指定のみ |

メインスキルは`init`、`update`、`config`に限定されています。
ほかの4スキルは互いを自動実行せず、情報不足時の通常調査、検出事項の自動更新、更新後の自動公開も行いません。
この境界により、「保存」「限定回答」「公開」「正確性検証」「構造改善」を個別に制御できます。

## データフォーマット

Knowledge Baseは各プロジェクトの`project-knowledge/`に置きます。
中心となる`docs/`はOKF（Open Knowledge Format）互換のMarkdown群で、次の管理ファイルと生成先を組み合わせます。

| パス | 役割 |
| --- | --- |
| `manifest.yml` | Project Knowledge形式と形式版の宣言 |
| `docs/` | Concept、Reference、ナビゲーション、更新履歴 |
| `knowledge-policy.md` | 保存対象を判断する収集方針と品質方針 |
| `config.yml` | プロジェクトで共有する動作設定 |
| `config.local.yml` | 個人設定、環境固有の設定、秘密情報。通常はコミットしない |
| `state.yml` | 差分検出などに使う機械状態 |
| `published/` | Knowledgeから再生成した公開成果物 |
| `.cache/` | 再生成できる一時データ |

`index.md`は案内とリンクだけを持つナビゲーション専用ページです。
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
管理ファイルである`manifest.yml`、`config.yml`、`state.yml`のキーはOKF frontmatterではないため、`pk_`接頭辞の対象外です。

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
| `pk_legacy_unclassified` | `true` | 旧形式から移行したConceptを根拠不足で分類できないことを示す一時的な印。新規生成では使用しない |

`pk_category`は「どの種類の情報か」、`pk_derivation`は「根拠からどう作ったか」を表す独立した軸です。
たとえば、複数の設計資料に明記された内容を統合した場合は、`extracted`かつ`synthesized`になります。

未検証の`inferred`は`status: draft`にします。
検証後も、推論から生まれたという来歴を`direct`へ書き換えません。
直接確認できる主張と推論が一つのConceptに混在する場合は、可能ならConceptを分割し、分割できなければ文書全体へ保守的な導出方法とstatusを設定します。

主観的な格付けとなる`pk_authority`や`pk_trust`は保存しません。
旧形式の`pk_source_kind`は移行時に`pk_source_type`へ変換します。

## 保存と更新の考え方

Knowledge Policyは対象分野の固定リストではなく、情報の将来価値を判断する方針です。
プロジェクト固有性、再利用性、持続性、背景や理由、重要な制約、誤りによる影響、明示的な保存指示を基準にします。
秘密情報、一時的な状態、デバッグ出力、重複、原文の不要な丸写しは原則として保存しません。

更新頻度は`manual`、`opportunistic`、`aggressive`の3段階です。
既定は、作業単位の完了時に候補を一度だけ評価する`opportunistic`です。
ただし、このスキル群自身のKnowledge Baseは、旧設定との互換移行により現在`manual`です。

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

Skill版のPATCHは公開動作を変えない修正、MINORは後方互換な機能、対応形式、非推奨化の追加、MAJORは操作、入出力、対応形式、安全境界の非互換変更に使います。
関連スキルは同じ版へ揃えず、変更の影響を受けたスキルだけを更新します。

Knowledge形式版のMINORは、既存readerが安全に無視または解釈できる互換な追加、MAJORは既存readerが安全に解釈できない変更に使います。
形式を追加または変更する場合は、形式仕様、前版との差分、migration手順、その形式に対応するSkill版を同時に用意します。

既知の旧形式は、競合検査と事前確認を行ってから移行します。
移行は冪等で、同名かつ異内容のファイルがある場合や、未知または新しい形式の場合は推測して変更せず停止します。
壊れたmanifestを旧形式とみなすこと、downgrade、未定義の版を飛び越すmigrationも認めません。

## `config.yml`の設定

`config.yml`はプロジェクトで共有する動作設定です。
個人設定、環境固有の値、秘密情報は`config.local.yml`へ分離し、設定変更時も既知でないキーや既存コメントを不用意に削除しません。

```yaml
knowledge:
  human_readable: false
learning:
  mode: opportunistic
publish:
  markdown: true
  html:
    enabled: true
    renderer: material-mkdocs
    offline: true
```

| キー | 設定内容 |
| --- | --- |
| `knowledge.human_readable` | `true`なら人がそのまま読める文章を優先する。`false`ならAIの検索効率、簡潔さ、構造、重複回避を優先するが、断片的にはしない |
| `learning.mode` | `manual`は明示的な更新依頼時だけ評価する。`opportunistic`は作業単位の完了時に価値のある候補だけを評価する。`aggressive`は候補を広めに拾うが、一時情報や重複は除外する |
| `publish.markdown` | 人間向けMarkdown成果物を生成対象にするかを指定する |
| `publish.html.enabled` | HTML成果物を生成対象にするかを指定する |
| `publish.html.renderer` | HTML生成に使うrendererを指定する。利用できないrendererを指定した場合は、別方式へ自動フォールバックせず報告する |
| `publish.html.offline` | HTTPサーバー、CDN、外部通信に依存しないHTMLとして生成するかを指定する |

`learning.mode`は設定ファイル名やキーを指定しなくても、「今後は自動的に更新して」「明示時だけ更新して」のような自然言語の依頼から変更できます。
一方、何をKnowledgeへ保存するかという収集方針は`config.yml`ではなく`knowledge-policy.md`で管理します。
publish時に指定した対象範囲は、その実行だけに適用し、永続的な設定にはしません。

## 仕様相談で検討したい論点

- 5スキルへの分離は、安全性と分かりやすさに対して適切か。明示指定のみの操作が多すぎないか。
- Knowledge Policyによるopen-worldな収集は、対象領域を固定する方式より長期運用に向いているか。
- `pk_category`と`pk_derivation`の二軸は、実務で扱える複雑さに収まっているか。
- User Statement、Interaction Record、Reference、Conceptの分離は、根拠追跡と保守コストの釣り合いが取れているか。
- 検証と監査を読み取り専用にし、反映を別の`update`へ委ねる設計は堅すぎないか。
- `opportunistic`な自動学習を「毎ターン」ではなく「作業単位の完了時」に限定する境界は明確か。
- Skill版、Knowledge形式版、OKF版、state schema版の分離は、変更判断を明確にする効果と運用負荷が釣り合っているか。
- `config.yml`と`knowledge-policy.md`の責務境界は、利用者が迷わず判断できるか。
