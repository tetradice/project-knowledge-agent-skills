# Verification

明示的な検証依頼に対して、Knowledgeに記録された内容が、示された根拠と現在のプロジェクト状態に照らして現在も成立するかをread-onlyで検証する。通常の質問、開発作業、実装レビューから自動実行せず、未登録Knowledgeを探すcoverage調査も行わない。

`verify`はKnowledgeに書かれた内容の健全性を扱う。重複、肥大化、Conceptの粒度、過度な分断、ナビゲーション、検索性、ファイル構成などKnowledge Baseの構造品質は`project-knowledge-audit`に委ねる。Knowledge同士の意味的矛盾は`verify`、同内容の重複は`audit`で扱う。

## 検証順序

対象Conceptごとに次の順序で検証する。前段で安全に解釈・参照できないと判明した範囲は、後段で推測せず`not-verifiable`または`not-applicable`とする。

### 1. Structure

このSkillの`scripts/validate_knowledge.py`をread-onlyで実行し、次を機械検査する。

- manifestの形式名と`format_version`
- MarkdownとYAML frontmatterのparse可否
- Conceptの`type`、`pk_category`、`pk_derivation`
- enum、`sources[].resource`、`sources[].pk_source_type`
- `generated`、`verified`、`status`、`stale`、`stale_after`
- Policy frontmatter、reserved index/log、broken link、orphan

形式1.0以外は推測せず検証を停止する。個別Conceptを安全に解釈できない場合は、そのConceptの後続検証を行わない。validatorのHigh/Medium/Lowは機械検査findingの重大度であり、後述するverify結果とは別の軸である。

### 2. Sources

各sourceについて、参照先が存在し、読み取れ、現在利用可能かを確認する。相対パス、URI、User Statement、Interaction Record、Reference、project artifactを実体までたどる。

- ローカルsourceの欠落、ファイルでない参照、明確な読取不能は`fail`とする。
- 外部URIなど、現在の環境から到達性を確認できない場合は`not-verifiable`とする。
- `pk_source_type`と参照先の実体が明白に矛盾する場合はprovenanceの`fail`、断定できない場合は`warning`とする。

sourceを確認できないConceptでは、EvidenceとCurrent Stateを推測で判定しない。

### 3. Provenance

本文だけでなく、実際の由来と`pk_category`、`pk_derivation`、`pk_source_type`が一致するか確認する。

| metadata | 判定基準 |
| --- | --- |
| `pk_category: declared` | 人がプロジェクト固有の方針、判断、意図として宣言したか |
| `pk_category: extracted` | Referenceやproject artifact等に事実が明記されているか |
| `pk_category: derived` | 情報の統合、計算、解釈、推論から得た内容か |
| `pk_derivation: direct` | 一つのsourceまたは一つの明示箇所から意味を変えず記録したか |
| `pk_derivation: synthesized` | 複数sourceまたは複数箇所を整理・統合したか |
| `pk_derivation: inferred` | sourceに明記されない結論を根拠から推論したか |

ユーザーが宣言した方針を`extracted`とする、コードから抽出した事実を`declared`とする、複数sourceの統合を`direct`とするなど、実際の由来との明確な矛盾は`fail`とする。検証によって確からしさが増しても、provenanceである`pk_derivation`を変更せず、`inferred`を`direct`へ昇格させない。

### 4. Evidence

sourceが存在するだけでなく、Knowledgeのclaimを実際に支持するか意味的に確認する。文字列一致だけで判定しない。

- `direct`: claimが指定sourceに直接存在し、意味を追加・変更していれば`fail`とする。
- `synthesized`: 統合結果の各部分をsourceが支持し、source間の差異を隠していないか確認する。
- `inferred`: 前提となるsourceが存在し、その前提から結論を導くことが妥当か再評価する。妥当なら`pass`だが`inferred`のままとする。
- 利用可能な情報だけでは支持も反証もできないclaimは`not-verifiable`とし、無理に`pass`または`fail`へ分類しない。

### 5. Current State

Knowledgeを現在のコード、設定、文書、その他のproject artifactと比較する。比較方法は`pk_category`によって変える。

| `pk_category` | 現在状態との比較 |
| --- | --- |
| `declared` | 宣言された方針・判断・意図が実在することを確認し、実装との差異はKnowledgeの誤りと即断せず`warning`の`implementation-drift`として報告する |
| `extracted` | 現在のartifactに同じ事実が存在するか確認し、明確な不一致は`fail`とする |
| `derived` | 現在のsourceを使って導出過程を再評価し、結論が成立しなければ`fail`、再評価できなければ`not-verifiable`とする |

現在状態との比較対象がない宣言などは`not-applicable`とする。

### 6. Freshness

`stale_after`だけでなく、source変更とsource消失を確認する。Git管理下では、working treeと履歴を使い、最後の`verified.at`、なければ`generated.at`以後にsourceが変更されたかを調べてよい。

- `stale_after`を過ぎたConceptは`stale`とする。
- sourceがcheckpoint後に変更され、今回まだ内容を再確認できていない場合は`stale`とする。
- source変更後でも今回のEvidence検証でclaimが現在も成立すると確認できればEvidenceは`pass`にできる。ただし、期限切れなど保存metadata上の鮮度問題は、別の`update`で反映されるまでFreshnessの`stale`として残す。
- source消失はSourcesの`fail`として報告し、Freshnessでも再検証が必要な状態を示す。
- source変更だけを理由に、内容が誤りだと断定しない。

### 7. Consistency

検証可能なKnowledge同士をclaim単位で比較し、同じ条件・時点について両立しない明確な矛盾を`fail`として報告する。対象条件や時点が不明で断定できない場合は`warning`または`not-verifiable`とする。同内容が複数Conceptに存在するだけなら構造問題として扱わず、`audit`へ委ねる。

## 代表判定

| case | 状況 | 期待する扱い |
| --- | --- | --- |
| 1 | `direct`なclaimをsourceが直接支持する | Evidenceは`pass` |
| 2 | `direct`なclaimへsourceにない説明が追加されている | Evidenceは`fail` |
| 3 | `inferred`な結論をsourceから妥当に導ける | Evidenceは`pass`。`inferred`は変更しない |
| 4 | sourceファイルが削除されている | Sourcesはsource errorの`fail`、依存する後段は`not-verifiable` |
| 5 | source変更後に内容を再確認できていない | Freshnessは`stale` |
| 6 | `extracted`なKnowledgeと現在実装が明確に異なる | Current Stateは`fail`。変更検出だけで内容未確認なら`stale` |
| 7 | `declared`な方針と現在実装が異なる | `warning`の`implementation-drift` |
| 8 | 同じ条件・時点の二つのConceptが矛盾する | Consistencyは`fail` |
| 9 | 二つのConceptが同内容を重複しているだけ | verifyでは構造findingにせず、auditの対象とする |
| 10 | `pk_category`が実際の由来と異なる | Provenanceは`fail` |
| 11 | 複数sourceの統合を`pk_derivation: direct`としている | Provenanceは`fail` |
| 12 | claimを支持も反証もできない | `not-verifiable` |
| 13 | 問題を検出した | ファイルを変更せず、確認・更新候補だけを報告する |
| 14 | verifyだけを依頼された | fix、audit、refactor、publish、updateを実行しない |

## 結果分類

各Concept・検証段階を次のいずれかで記録する。verify全体を単一の成功・失敗へ畳み込まず、結果別の件数と非pass項目を要約する。

| result | 意味 |
| --- | --- |
| `pass` | 必要な確認を実施し、問題が確認されなかった |
| `fail` | 根拠、metadata、現在状態、他Knowledgeとの明確な矛盾またはsource errorがある |
| `warning` | 問題の可能性やimplementation driftがあるが、Knowledge自体の誤りとは断定できない |
| `not-verifiable` | 現在利用可能な情報だけでは検証できない |
| `stale` | 期限超過や未再検証のsource変更により再検証またはmetadata更新が必要 |
| `not-applicable` | その検証段階が対象Conceptに適用されない |

## Report

次の順で報告する。

1. 検証対象、利用したsource、現在状態の比較範囲、未実施範囲
2. result別の件数
3. Concept・検証段階ごとの結果表。対象、claim、sourceまたは比較対象、result、判定理由、次に確認・更新すべき内容を含める
4. 非pass項目の要約。`implementation-drift`、source error、provenance問題、矛盾を区別する
5. 独立した確認を完了したConceptのverification event候補

`pass`を省略せず、どの段階を実施したか分かるようにする。検証不能を成功扱いせず、実行していないブラウザ、DB、device、external service等の範囲を明示する。

## `verified`とread-only境界

`generated`は現在内容を生成・更新した主体、`verified`は独立して内容を確認した主体という意味を維持する。生成直後の読み返しや、ユーザーが情報を発言した事実だけでは`verified`の根拠にならない。

sourceの再読、現在実装の独立確認、導出過程の再評価などを実施し、該当するStructure、Sources、Provenance、Evidence、Current State、Freshness、Consistencyに`fail`、`stale`、`not-verifiable`がない場合だけ、確認方法、actor、時刻を含むverification event候補を示す。verify自身は`verified`その他のファイルを書き換えない。

古いKnowledge、metadata不整合、implementation drift、stale、source切れ、矛盾を検出しても自動修正しない。既存Knowledgeの問題修正は、ユーザーが明示した別の`fix`として行う。新しい情報や変更の反映は別の`update`として行う。`verify`から`fix`、`update`、`audit`、`refactor`、`publish`を自動実行しない。複数操作を実行するのは、ユーザーがそれぞれを明示した場合だけとする。

verify中に未登録情報を偶然見つけても追加しない。リポジトリ全体から未登録Knowledgeを網羅的に探す作業はupdateまたはdiscovery側の別作業とする。
