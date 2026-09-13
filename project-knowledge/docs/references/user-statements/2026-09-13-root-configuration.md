---
type: Reference
pk_source_type: user-statement
generated:
  by: project-knowledge/3.1.0
  at: 2026-09-13T00:00:00+09:00
---

# Project Knowledgeのルート設定

利用者は、Project Knowledgeを設定ファイルで明示的に登録したプロジェクトだけで利用するよう求めた。設定では`version: "1.0"`、`layers`、各レイヤーの`id`と`path`を必須とし、利用者の指示なしにversionを上げない。

初期設定は`default`レイヤーだけを定義し、生成元コメント、version、id、pathを含める。`description`、`access`、`optional`、`write_target`は初期生成時に省略する。将来のレイヤード運用を見据え、`default`以外のレイヤーには用途と適用範囲を判断できる`description`を必須とする。
