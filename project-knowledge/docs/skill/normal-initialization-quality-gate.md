---
type: Project Knowledge initialization
pk_category: extracted
pk_derivation: synthesized
status: stable
generated:
  by: project-knowledge/3.1.0
  at: 2026-08-27T00:00:00+09:00
sources:
- resource: ../../../skills/project-knowledge/references/init.md
  pk_source_type: change-implementation
- resource: ../../../skills/project-knowledge-scenario-test/references/quick.md
  pk_source_type: change-implementation
- resource: ../../../skills/project-knowledge-scenario-test/scripts/scenario_test.py
  pk_source_type: change-implementation
- resource: ../../../skills/project-knowledge/tests/test_project_knowledge.py
  pk_source_type: change-implementation
- resource: ../../../skills/project-knowledge-scenario-test/tests/test_scenario_test.py
  pk_source_type: change-implementation
- resource: ../references/interactions/2026-08-27-normal-initialization-quick-execution.md
  pk_source_type: interaction-record
---
# 通常初期化の品質ゲート

通常の`init`は、`init_project.py`による形式1.0の初期構造生成だけでは完了しない。READMEと、存在する範囲で代表的なコード、設定、設計資料を調査し、保存価値のある事実があれば、実在するsourceを`project-artifact`として参照する通常Conceptを1件以上生成する。明示的な「空で初期化」だけは、初期構造の生成後に調査とKnowledge本文の生成を行わない。

単一sourceから直接抽出した知識は`extracted/direct`、複数sourceを一つの知識へ統合した知識は`extracted/synthesized`として扱う。未決定事項をstableな事実へ昇格させず、裏付けのない主張や一時的なデバッグ値を保存しない。

`quick-basic`のdeterministic validationは既存validatorに加え、通常Conceptが1件以上存在することと、そのConceptがworkspace内に実在する`project-artifact`を1件以上参照することを要求する。骨組みだけのBundleは`missing-concept`と`missing-project-artifact-source`でFAILとなる。この検査は初期構築の最低契約だけを扱い、内容の正確性、網羅性、provenance、分類、ノイズ除外、unsupported claimは独立Judgeの6観点で評価する。

実装commit `68ec732df3a1896a4f87ceba4d3a350f3c7e7c2d`では、通常/空初期化の契約、上記deterministic validation、回帰テストを追加した。QuickをGPT-5.6 Lunaの独立ActorとJudge（ともにlow reasoning）で1回実行し、deterministic validationと6観点すべてがPASS、issueはなかった。pytestは62件PASS、変更対象のRuffと`git diff --check`はPASSした。リポジトリ全体Ruffには今回未変更のpublish scriptのimport順エラーが1件残っている。
