---
name: project-knowledge-audit
description: Explicit-only read-only workflow for auditing Project Knowledge Base structure, duplication, fragmentation, navigation, searchability, and information architecture. Use only when the user explicitly names project-knowledge-audit or invokes it as $project-knowledge-audit; do not use for content, evidence, freshness, or format verification.
metadata:
  version: "3.0.0"
---

# Project Knowledge Baseの監査

明示的に呼び出された場合だけ、Knowledge Baseの重複・冗長性・肥大化・分断・ナビゲーション・検索性・情報設計をread-onlyで監査する。通常の文書レビューや、内容・根拠・鮮度・形式の正確性検証から自動選択しない。

形式1.0だけをread-onlyで監査する。形式が異なる場合は処理せず、対応するSkill版が必要だと報告する。

次を確認し、改善候補をHigh impact/Medium impact/Low impactで報告する。

- 重複ナレッジと同内容のReference重複
- 不要・未参照Reference、一時情報、ソースコードの過剰転記
- 細かすぎる、巨大すぎる、利用されないナレッジ
- 不要な分割・カテゴリ、関連情報の分散、統合候補
- orphan、肥大化したindex、`.cache/`や生成物の残骸
- 巨大ページへの過度な集約、不自然な階層、indexからの探しにくさ

Knowledgeの主張と根拠・現在状態の一致、Knowledge同士の意味的矛盾、sourceの存在、鮮度、frontmatterや形式への適合性は`project-knowledge`の`verify`に委ねる。同内容の重複は内容上の矛盾ではないため、このauditで扱う。

監査中は削除・統合・再編を行わない。改善を実施する場合は、対象と期待効果を示して`project-knowledge`による更新を案内するだけにする。
