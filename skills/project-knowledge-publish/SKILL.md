---
name: project-knowledge-publish
description: Explicit-only workflow for publishing project-knowledge/docs as human-readable Markdown or offline HTML. Use only when the user explicitly names project-knowledge-publish or invokes it as $project-knowledge-publish; do not use for general summarization or formatting requests.
metadata:
  version: "0.3.0"
---

# Project Knowledgeの公開

明示的に呼び出された場合だけ、`project-knowledge/docs/`を人間向け成果物へ変換し、原則として`project-knowledge/published/`へ出力する。通常の要約・整形依頼から自動選択しない。

[Publishing](references/publishing.md)を読み、MarkdownまたはHTTPサーバー不要のオフラインHTMLを生成する。今回の対象指定は永続的なPolicyやscopeへ反映しない。

形式0.1と0.2をread-onlyで公開できる。未知または新しい形式は推測せず、対応するSkill版が必要だと報告する。

Knowledge本文へ逆同期せず、`project-knowledge`を含む他Skillを自動実行しない。
