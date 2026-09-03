---
type: Reference
pk_source_type: interaction-record
generated:
  by: project-knowledge/3.1.0
  at: 2026-09-03T10:43:11+09:00
---

# ファイル変更報告の表示名を日本語化した実装

利用者向け完了報告の分類名について、内部値を変えずに表示名だけを日本語化する方針を決めた。`Knowledge`は「ナレッジ文書」、`Provenance`は「根拠資料」とし、`pk_category`と`pk_source_type`の内訳にも対応する日本語名を定義した。利用者の指定により、`derived`の表示名は「分析の結果」とした。

`skills/project-knowledge/references/file-change-classification.md`に内部値と表示名の対応表を追加し、出力例を日本語へ置き換えた。`skills/project-knowledge/tests/test_project_knowledge.py`では、内部値を維持した対応表と日本語の合計見出しを契約として確認するようにした。

コミット`0e62`で2ファイルを変更した。分類報告の契約テストはPASSし、Skill validatorもUTF-8モードでPASSした。Windows既定のCP932ではvalidatorがUTF-8文書を読めず失敗するため、`PYTHONUTF8=1`を指定して検証した。
