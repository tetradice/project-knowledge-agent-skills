---
name: project-knowledge-fast-ask
description: Explicit-only workflow for answering a user question using project-knowledge/docs as the sole information source. Use only when the user explicitly names project-knowledge-fast-ask or invokes it as $project-knowledge-fast-ask; do not use for ordinary project questions.
metadata:
  version: "0.3.0"
---

# Project Knowledge限定回答

明示的に呼び出された場合だけ、`project-knowledge/docs/**`にある情報だけを使って質問へ回答する。通常のプロジェクト質問から自動選択しない。

[Query rules](references/query-rules.md)を読み、`project-knowledge/docs/index.md`から必要なKnowledgeだけを段階的に参照する。

形式0.1、0.2、0.3をread-onlyで扱う。未知または新しい形式は推測せず、対応するSkill版が必要だと報告する。

回答には、Project Knowledge内の情報のみを使用したことを明示する。十分な情報がなければ推測や通常調査へフォールバックせず、「Project Knowledgeには、この点を判断できる情報がない」と伝える。

`project-knowledge`を含む他Skillや外部情報源を自動実行・参照しない。
