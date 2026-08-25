---
name: project-knowledge-audit
description: Explicit-only read-only workflow for auditing Project Knowledge Base structure, duplication, size, and information quality. Use only when the user explicitly names project-knowledge-audit or invokes it as $project-knowledge-audit; do not use for ordinary documentation review or correctness checks.
metadata:
  version: "0.2.0"
---

# Project Knowledge Baseの監査

明示的に呼び出された場合だけ、Knowledge Baseの重複・冗長性・肥大化・構造・情報品質をread-onlyで監査する。通常の文書レビューや正確性検査から自動選択しない。

[Audit](references/audit.md)を読み、改善候補をHigh impact/Medium impact/Low impactで報告する。初回監査を含め、Knowledgeを変更しない。

形式0.1と0.2をread-onlyで監査する。未知または新しい形式は推測せず、対応するSkill版が必要だと報告する。

改善を自動実行しない。必要なら`project-knowledge`による更新を案内するだけにする。
