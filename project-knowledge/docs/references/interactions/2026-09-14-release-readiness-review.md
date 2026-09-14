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

## Medium指摘の対応結果

利用者は、上記のMedium 2件への対応を指示した。`README.md`には、`npx skills add`以外の通常利用でPython 3.11以上と`uv`が必要であり、Node.jsは`npx skills add`によるインストール操作にだけ必要であることを追記した。これにより、通常操作の`uv run`実行例と導入前提が一致した。

`skills/project-knowledge-audit/agents/openai.yaml`は、短い説明をread-only監査に限定し、default promptもread-onlyの`audit`だけを依頼し、refactorやファイル変更を禁止する内容へ変更した。UI entryから`refactor`を暗黙に選ばせないため、書き込みを伴う構造改善は引き続き明示指示が必要である。

今回の対応ではテスト系・ベンチマーク系Skillと、それらの実行を対象外のままとした。LowのRuff import-order 3件も、このMedium対応の対象外であり未変更である。
