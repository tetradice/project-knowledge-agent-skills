# Data model

## 根拠の性質

| 主張 | 主なauthoritative source |
| --- | --- |
| 現在の実装 | ソースコード、設定、schema |
| 本来あるべき仕様 | capture、明示的なユーザー指示 |
| 過去の設計判断 | trusted memo |
| 整理済み説明 | 既存ナレッジ |
| 未確定事項 | provisional memo |

固定順位で勝者を決めない。たとえば仕様が30秒、実装が10秒なら、両方と不一致を記録する。

captureとmemoはユーザー操作ではなく内部provenanceである。独自metadataは `pk_` 接頭辞を使う。captureは `pk_source_kind: capture`, `pk_authority: primary`, `pk_trust: trusted`。memoは `pk_source_kind: memo`, `pk_authority: secondary` とし、承認前は `pk_trust: provisional` にする。詳細は[provenance.md](provenance.md)を読む。

ナレッジの`verified`はその文書自体の検証を表す。memoの承認だけで派生ナレッジへhuman verificationを付けない。

`state.yml` は最終update時刻・commitと差分検出情報だけを持つ。`.cache/` のhash/mtime snapshotは再生成可能であり、ナレッジとして参照しない。
