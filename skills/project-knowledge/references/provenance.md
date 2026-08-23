# Provenance

captureとmemoはユーザー操作ではなく、情報がどこから来たかを示す内部Reference種別である。

| kind | 用途 | authority | 初期trust |
| --- | --- | --- | --- |
| `capture` | ユーザーが直接提示した仕様・事実・決定事項の原文 | `primary` | `trusted` |
| `memo` | 会話からAIが意味的に抽出した決定・理由・制約・未解決事項 | `secondary` | `provisional` |
| `source-code` | 現在の実装 | 実装根拠 | 検査時点の状態 |
| `config` | 設定・build・dependency・infra | 設定根拠 | 検査時点の状態 |
| `schema` | DB・API schema・migration | schema根拠 | 検査時点の状態 |
| `external-reference` | 外部仕様・文書 | 出典に依存 | 出典に依存 |
| `existing-knowledge` | 既存の整理済みナレッジ | 二次的 | provenanceに依存 |

captureを作る場合はユーザー原文を`docs/references/captures/`へ保持し、`pk_source_kind: capture`、`pk_authority: primary`、`pk_trust: trusted`を付ける。memoを作る場合は会話ログを複製せず再利用価値のある判断材料だけを`docs/references/memos/`へ記録し、`pk_source_kind: memo`、`pk_authority: secondary`、`pk_trust: provisional`を付ける。

すべてのupdateでReferenceを作らない。ソース変更から既存ナレッジを直接更新でき、別の由来を保持する価値がなければ不要である。Referenceとナレッジ本文に同じ説明を二重保存しない。

`memo.require_approval_for_trust: true`では、ユーザーが「この内容で確定」「正式なものとして扱う」などと明示した場合だけmemoを`trusted`へ昇格する。provenanceはmemoのまま維持する。captureやtrusted memoと実装が矛盾する場合は勝者を機械的に決めず、不一致をナレッジへ明示する。
