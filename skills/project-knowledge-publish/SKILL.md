---
name: project-knowledge-publish
description: Explicit-only workflow for publishing project-knowledge/docs as human-readable Markdown or offline HTML. Use only when the user explicitly names project-knowledge-publish or invokes it as $project-knowledge-publish; do not use for general summarization or formatting requests.
metadata:
  version: "2.0.0"
---

# Project Knowledgeの公開

明示的に呼び出された場合だけ、`project-knowledge/docs/`を人間向け成果物へ変換し、原則として`project-knowledge/published/`へ出力する。通常の要約・整形依頼から自動選択しない。

[Publishing](references/publishing.md)を読み、Markdown、offline HTML、または両方を生成する。今回指定された出力形式と対象範囲をKnowledge Baseへ永続化しない。

形式1.0だけをread-onlyで公開できる。形式が異なる場合は推測せず、対応するSkill版が必要だと報告する。

Knowledge本文へ逆同期せず、`project-knowledge`を含む他Skillを自動実行しない。
