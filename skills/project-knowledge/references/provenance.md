# Provenance and verification

`sources`はOKF provenanceとして、Conceptの根拠となるresourceを保持する。sourceごとにProject Knowledge独自の`pk_source_type`を付ける。

| `pk_source_type` | 用途 |
| --- | --- |
| `user-statement` | ユーザーが会話で宣言したプロジェクト固有情報 |
| `reference-document` | ユーザーが提供した外部・補助文書 |
| `project-artifact` | リポジトリ内のコード、設定、文書 |
| `interaction-record` | 会話や作業経緯の記録 |
| `change-implementation` | 実装された変更そのもの |

```yaml
sources:
  - resource: ../references/user-statements/2026-08-26-version-policy.md
    author: human:user
    pk_source_type: user-statement
```

ユーザー発言は`docs/references/user-statements/`、作業経緯は`docs/references/interactions/`へ保存する。`pk_authority`、`pk_trust`のような主観的な格付けは保存しない。

プロジェクト内部の方針や判断について、ユーザー宣言は一次情報になり得る。一方、外部事実に関する発言を、ユーザー発言であるという理由だけで確認済みにしない。

## generatedとverified

- `generated`は現在の内容を生成または更新したactorを表す。
- `verified`は内容を独立に確認したactorと時刻を表す。
- ユーザーが情報を提供したことと、人が検証したことは別である。
- Skill actorには版を含める。例: `project-knowledge/3.1.0`。

```yaml
generated:
  by: project-knowledge/3.1.0
  at: 2026-08-26T00:00:00+09:00
verified:
  by: project-knowledge/3.1.0
  at: 2026-08-26T00:10:00+09:00
```

trust tierは保存せず、`verified`から表示時に導出する。

| 導出tier | 条件 |
| --- | --- |
| `unverified` | `verified`がない |
| `machine-confirmed` | `verified.by`がversion付きSkillまたはprocess actor |
| `human-reviewed` | `verified.by`が`human:*` |

`project-knowledge`のverify操作はread-onlyであり、成功時もverification event候補を報告するだけである。ユーザーが反映を求めた別のupdateだけが`verified`を保存する。
