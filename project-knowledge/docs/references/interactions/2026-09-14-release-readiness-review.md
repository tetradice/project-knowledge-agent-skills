---
type: Reference
pk_source_type: interaction-record
generated:
  by: project-knowledge/3.1.0
  at: 2026-09-14T17:38:05+09:00
---

# 通常利用Skillのリリース準備レビュー

利用者は、Agent Skillをリリースへ進める前に内容の問題と矛盾を徹底的にレビューし、結果をProject Knowledgeの`references`以下へ残すよう求めた。テスト系Skillとベンチマーク系Skillは今回の対象外とした。

レビュー対象は通常利用の6 Skill、すなわち`project-knowledge`、`project-knowledge-help`、`project-knowledge-inspect`、`project-knowledge-fast-ask`、`project-knowledge-publish`、`project-knowledge-audit`と、それぞれが通常利用で参照するReference、runtime script、template、metadataである。`developer-tests`と`project-knowledge-benchmark`、およびそれらのテスト・ベンチマーク実行は除外した。

重大な矛盾または通常操作を実行不能にする問題は検出しなかった。全対象のruntime scriptは`py_compile`に成功し、`uv run`経由の設定解決とvalidator実行も成功した。既存Knowledgeのvalidator JSON出力は`[]`だった。テストとベンチマークは対象外のため実行していない。template内で静的には存在しない3リンクは`init_project.py`が生成先を作成するため、問題ではないことも確認した。

リリース前に解消すべきMediumの文書欠落は、READMEがインストールにNode/npxだけを前提としている一方、通常操作の実行例が`uv run`であり、Python 3.11とuvの導入手順をREADMEに示していない点である。新規利用者はruntime scriptを実行できない。READMEへPython 3.11とuvの前提および導入方法を追加する必要がある。

もう一つのMediumは、`project-knowledge-audit`がread-onlyの`audit`と書き込みを伴う`refactor`を明確に分け、自動昇格を禁じているのに、UI entryの`agents/openai.yaml`が短い説明とdefault promptで両方を同列に示し、`refactor`の明示要求を含まない点である。UIのdefault promptを使うと書き込み操作の明示性が弱まる。default promptをaudit専用にするか、auditとrefactorを選択させるべきである。

Lowとして、対象runtime scriptへの`uvx ruff check`はI001 import-orderを3件検出した。該当箇所は`skills/project-knowledge/scripts/detect_changes.py:9`、`skills/project-knowledge/scripts/init_project.py:9`、`skills/project-knowledge-publish/scripts/build_offline_docs.py:10`である。機能不全ではなく自動修正可能な整形だが、ruffをリリース品質ゲートに置くなら未達である。
