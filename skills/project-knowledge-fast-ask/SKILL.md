---
name: project-knowledge-fast-ask
description: Explicit-only workflow for answering a user question using project-knowledge/docs as the sole information source. Use only when the user explicitly names project-knowledge-fast-ask or invokes it as $project-knowledge-fast-ask; do not use for ordinary project questions.
metadata:
  version: "2.0.0"
---

# Project Knowledge限定回答

明示的に呼び出された場合だけ、`project-knowledge/docs/**`にある情報だけを使って質問へ回答する。通常のプロジェクト質問から自動選択しない。

`project-knowledge/docs/index.md`から必要なページだけを段階的に読み、必要な場合だけ`docs/references/`を読む。ソースコード、その他のプロジェクトファイル、Git履歴、Web、外部文書、一般知識を根拠にしない。

形式1.0だけをread-onlyで扱う。形式が異なる場合は推測せず、対応するSkill版が必要だと報告する。

形式1.0の`pk_category`と`pk_derivation`を`verified`、`status`、`stale`と合わせて読み、推論、未検証、draft、staleを回答上の制約として明示する。trust tierは`verified`から導出し、保存された格付けを前提にしない。

回答には、Project Knowledge内の情報のみを使用したことを明示する。十分な情報がなければ推測や通常調査へフォールバックせず、「Project Knowledgeには、この点を判断できる情報がない」と伝える。

`project-knowledge`を含む他Skillや外部情報源を自動実行・参照しない。
