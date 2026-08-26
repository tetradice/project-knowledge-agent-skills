# Query rules

参照範囲を `project-knowledge/docs/**` に限定する。ソースコード、その他のプロジェクトファイル、Git履歴、Web、外部文書、一般知識を根拠にしない。

`docs/index.md`から必要なページだけを段階的に読み、必要な場合だけ`docs/references/`を読む。回答には「この回答はプロジェクトナレッジ内の情報のみを使用しています」という趣旨を明示する。情報がなければ推測せず、判断材料がないと答える。

形式0.1、0.2、0.3をread-onlyで扱う。0.2では`category`と`derivation`、0.3では`pk_category`と`pk_derivation`を`verified`、`status`、`stale`と合わせて読み、推論、未検証、draft、staleを回答上の制約として明示する。trust tierは`verified`から導出し、保存された格付けを前提にしない。0.1で分類がない場合は分類を推測せず、legacyの未分類情報として扱う。
