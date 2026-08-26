---
name: project-knowledge-audit
description: Explicit-only workflow for read-only audits and conservative structural refactoring of Project Knowledge Base duplication, fragmentation, navigation, searchability, and information architecture. Use only when the user explicitly names project-knowledge-audit, invokes $project-knowledge-audit, or explicitly requests a Project Knowledge structural refactor; do not use for content, evidence, freshness, or format verification.
metadata:
  version: "3.1.0"
---

# Project Knowledge Baseの構造監査・構造改善

明示的に呼び出された場合だけ、Knowledge Baseの構造品質を診断または改善する。通常の文書レビュー、一般的な「整理して」「改善して」、内容・根拠・鮮度・形式の正確性検証から自動選択しない。

## 操作を選ぶ

| 操作 | 選ぶ指示・目印 | 書き込み | 読むReference |
| --- | --- | --- | --- |
| `audit` | 「project-knowledge-auditで監査して」「$project-knowledge-audit Knowledge Baseの重複や肥大化を監査して」 | なし | [audit.md](references/audit.md) |
| `refactor` | 「project-knowledge-auditでrefactorして」「Project Knowledgeの構造をrefactorして」 | あり | [refactor.md](references/refactor.md) |

`audit`はread-onlyであり、findingを検出しても`refactor`へ昇格させない。`refactor`内の再診断は同じ操作の完了条件であり、別の`audit`を自動実行することではない。

形式1.0だけを扱う。形式が異なる場合は処理せず、対応するSkill版が必要だと報告する。

Knowledgeの主張と根拠・現在状態の一致、Knowledge同士の意味的矛盾、sourceの存在、鮮度、frontmatterや形式への適合性は`project-knowledge`の`verify`または`fix`へ委ねる。同内容の重複は内容上の矛盾ではないため、このSkillで扱う。別Skillを自動実行しない。
