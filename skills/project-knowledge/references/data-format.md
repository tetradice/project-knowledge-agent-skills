# Knowledge data formats

Skill版、Knowledge形式版、OKF版、state schema版の違いは[Version contracts](versioning.md)を参照する。

書込み前に`project-knowledge/manifest.yml`を読み、形式を選択する。

| 形式 | 検出 | Skill 0.2.0の対応 |
| --- | --- | --- |
| `0.1` | manifestがなく、既知のlegacy構造を持つ | specialized Skillはread-only。`project-knowledge`は書込み前に0.2へ移行 |
| `0.2` | 正常なmanifestで`format: project-knowledge`、`format_version: "0.2"` | read-only対応。書込み前に0.3へ移行 |
| `0.3` | 正常なmanifestで`format: project-knowledge`、`format_version: "0.3"` | 全Skillが通常対応 |
| 未知・より新しい形式 | manifestのformatまたは版が未対応 | 推測せず停止し、Skill更新が必要と報告 |

- [Format 0.1](data-formats/0.1.md)
- [Format 0.2](data-formats/0.2.md)
- [Format 0.3](data-formats/0.3.md)
- [Migration 0.1 to 0.2](migrations/0.1-to-0.2.md)
- [Migration 0.1 to 0.3](migrations/0.1-to-0.3.md)
- [Migration 0.2 to 0.3](migrations/0.2-to-0.3.md)

malformed manifestはlegacy扱いしない。downgradeとmigration版の飛び越しは禁止する。
