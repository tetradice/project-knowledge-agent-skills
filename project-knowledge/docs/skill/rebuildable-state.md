---
type: State Management Design
pk_category: extracted
pk_derivation: synthesized
status: stable
generated:
  by: project-knowledge/3.0.0
  at: 2026-08-26T16:55:24+09:00
sources:
- resource: ../../../skills/project-knowledge/references/state.md
  pk_source_type: project-artifact
- resource: ../../../skills/project-knowledge/scripts/detect_changes.py
  pk_source_type: change-implementation
- resource: ../../../skills/project-knowledge/scripts/validate_knowledge.py
  pk_source_type: change-implementation
---
# 再構築可能なProject Knowledge state

`state.yml`と`.cache/`はKnowledgeの正本ではなく、増分更新を効率化するworking copy固有状態である。欠落、破損、非対応schemaでは現在のproject状態から再構築する。

```yaml
state_schema_version: 2
git_baseline_commit: null
```

Git baselineは完全なcommit object IDとし、現在HEADの祖先である場合だけ使う。無効なら全tracked fileを対象とするフルスキャンへ移る。非Git環境は固定位置`project-knowledge/.cache/source-snapshot.json`のfile hashを使う。

Knowledge更新とvalidationが成功した後だけcheckpointを進める。validatorはstate問題をLowとしてKnowledge本体の破損と区別し、静的なschemaとfield型だけを検査する。

`detect_changes.py`はstateのGit baselineまたは固定位置の非Git snapshotだけを使う。CLIでbaselineやsnapshot位置を上書きするoption、旧`--write-state` aliasは持たない。
