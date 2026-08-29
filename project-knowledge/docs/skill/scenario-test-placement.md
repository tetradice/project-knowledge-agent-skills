---
type: Project Knowledge Scenario Test placement
pk_category: declared
pk_derivation: synthesized
status: stable
generated:
  by: project-knowledge/3.1.0
  at: 2026-08-29T00:00:00+09:00
sources:
- resource: ../references/user-statements/2026-08-29-scenario-test-placement.md
  pk_source_type: user-statement
- resource: ../../../README.md
  pk_source_type: project-artifact
- resource: ../../../developer-tests/project-knowledge-scenario-test/SKILL.md
  pk_source_type: change-implementation
---

# Scenario Testの配置

`project-knowledge-scenario-test`は一般ユーザー向けSkillではなく、Project Knowledgeの開発者が品質を確認するためのテストハーネスである。そのため、配布対象の`skills/`には置かず、`developer-tests/project-knowledge-scenario-test/`へ配置する。

Quick、Large、Model Benchmark、Utilityは、リポジトリ開発者が同ディレクトリの`SKILL.md`を明示的に読み込んで実行する。通常のProject Knowledge操作や一般ユーザー向けSkillから自動実行しない。
