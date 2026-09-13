---
type: Versioning Contract
pk_category: declared
pk_derivation: synthesized
status: stable
generated:
  by: project-knowledge/3.1.0
  at: 2026-09-13T13:45:00+09:00
sources:
- resource: ../../../project-knowledge.yaml
  pk_source_type: project-artifact
- resource: ../../../project-knowledge/manifest.yml
  pk_source_type: project-artifact
- resource: ../../../skills/project-knowledge/references/versioning.md
  pk_source_type: change-implementation
- resource: ../../../skills/project-knowledge/SKILL.md
  pk_source_type: change-implementation
- resource: ../../../skills/project-knowledge-audit/SKILL.md
  pk_source_type: change-implementation
- resource: ../../../skills/project-knowledge-fast-ask/SKILL.md
  pk_source_type: change-implementation
- resource: ../../../skills/project-knowledge-publish/SKILL.md
  pk_source_type: change-implementation
- resource: ../../../skills/project-knowledge-help/SKILL.md
  pk_source_type: change-implementation
- resource: ../../../skills/project-knowledge-inspect/SKILL.md
  pk_source_type: change-implementation
- resource: ../../../skills/project-knowledge-benchmark/SKILL.md
  pk_source_type: change-implementation
---

# Versioning contracts

The repository has independent contracts for Project Knowledge configuration, each Skill, the Knowledge format, the OKF bundle, and rebuildable state. A change to one contract does not imply a change to another.

| Contract | Source of truth | Current value | Scope |
| --- | --- | --- | --- |
| Project Knowledge configuration | `project-knowledge.yaml` | `1.0` | Layer registration and access |
| Skill | Each `skills/*/SKILL.md` `metadata.version` | `project-knowledge` and `project-knowledge-audit`: `3.1.0`; `project-knowledge-fast-ask` and `project-knowledge-publish`: `2.0.0`; `project-knowledge-help`, `project-knowledge-inspect`, and `project-knowledge-benchmark`: `1.0.0` | Public Skill contract (SemVer) |
| Knowledge format | `project-knowledge/manifest.yml` | `1.0` | Knowledge directory format |
| OKF bundle | `project-knowledge/docs/index.md` | `0.2` | `docs/` bundle |
| State schema | `project-knowledge/state.yml` | `2` | Rebuildable local state |

Do not change a version merely because a related contract changes. In particular, the root configuration and Knowledge-format versions remain `1.0` unless the user explicitly directs a version change.

## Release boundary

The repository currently has no root release manifest, changelog, or Git tags. Skill metadata versions therefore describe individual Skill contracts; they do not establish a repository-wide release version or release process. Define that process explicitly before treating any Skill version as a repository release identifier.
