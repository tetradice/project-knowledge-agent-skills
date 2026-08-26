# Version contracts

Project Knowledgeは、用途の異なる四つの版を独立して管理する。

| 版 | Source of truth | 形式 | 用途 |
| --- | --- | --- | --- |
| Skill版 | 各`SKILL.md`の`metadata.version` | SemVer `MAJOR.MINOR.PATCH` | Skillの公開動作 |
| Knowledge形式版 | `project-knowledge/manifest.yml`の`format_version` | `MAJOR.MINOR` | Knowledgeディレクトリのデータ形式。現在は`0.3` |
| OKF版 | `project-knowledge/docs/index.md`の`okf_version` | OKF仕様に従う | `docs/` bundle規約 |
| state schema版 | `project-knowledge/state.yml`の`state_schema_version` | 整数 | 機械状態の内部schema |

## Skill SemVer

- PATCH: 公開動作を変えない修正。
- MINOR: 後方互換な機能、対応形式、deprecationの追加。
- MAJOR: 操作、入出力、対応形式、安全境界の非互換変更。

関連Skillは互いに独立した版を持つ。同じKnowledge形式に対応していても、変更の影響を受けたSkillだけを更新する。

## Knowledge形式版

- MINOR: 既存readerが安全に無視または解釈できる互換な追加。
- MAJOR: 既存readerでは安全に解釈できない変更。

形式を変更するときは、形式仕様、前版との差分、migration手順、対応Skill版を同時に追加する。
