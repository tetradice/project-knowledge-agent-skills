---
name: project-knowledge-verify
description: Explicit-only read-only workflow for checking whether Project Knowledge is accurate, current, well-formed, and consistent with authoritative project sources. Use only when the user explicitly names project-knowledge-verify or invokes it as $project-knowledge-verify; do not use for ordinary implementation review.
---

# Project Knowledgeの検証

明示的に呼び出された場合だけ、Project Knowledgeの正確性・鮮度・形式・provenanceをread-onlyで検証する。通常の実装レビューから自動選択しない。

[Verification](references/verification.md)を読み、結果をHigh/Medium/Lowで報告する。Knowledge、設定、capture、memo、ソースコード、Git履歴などを検証目的で参照できるが、変更しない。

問題を見つけても更新を自動実行しない。必要なら`project-knowledge`による更新を案内するだけにする。
