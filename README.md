# agent-skills

公開 MCP サーバーの探索と、プロジェクト固有のナレッジ管理に使用する Agent Skills を管理するリポジトリです。

MCP サーバー探索 CLI の使い方は、[packages/mcp-server-search/README.md](./packages/mcp-server-search/README.md) を参照してください。

## project-knowledge の使い方

`project-knowledge` は、プロジェクトナレッジの作成、検証、更新を1つの router Skill で扱います。

`$project-knowledge` で Skill を選び、後ろに operation を指定します。
operation は CLI のサブコマンドではなく、通常のユーザー指示として解釈されます。

| operation | 用途 | 呼び出し例 |
|---|---|---|
| `init` | 現在のコードと設定からプロジェクトナレッジを新規構築する | `$project-knowledge init` |
| `check` | 現在状態との差異を、ファイルを変更せず検証する | `$project-knowledge check` |
| `update` | 現在状態へ同期し、`pending.md` を整理する | `$project-knowledge update` |

operation を書かず、自然言語で意図を伝えることもできます。

```text
プロジェクトナレッジを初期化してください。
古くなっているナレッジがないか確認してください。
現在の変更をプロジェクトナレッジへ反映してください。
```

operation が明示されている場合は、その指定が優先されます。
operation を省略した場合は、依頼全体の意図から処理が選ばれます。

## ナレッジだけを使った回答

`project-knowledge/` だけを情報源として質問に答える場合は、独立した `project-knowledge-fast-ask` を使います。

```text
$project-knowledge-fast-ask を使って、プロジェクトナレッジの情報だけをもとに回答してください。
```

この Skill は、コード、設定、Git、外部環境、Web、一般知識を回答の根拠にしません。

## 人間向け文書の出力

プロジェクトナレッジを人間向けに公開する処理は、独立した Skill が担当します。

```text
$project-knowledge-publish を使って、プロジェクトナレッジを人間向けのMarkdown文書として出力してください。
$project-knowledge-publish-html を使って、プロジェクトナレッジをHTML形式で出力してください。
```

`project-knowledge-publish` は Markdown 文書を生成します。
`project-knowledge-publish-html` は、Blume を使って静的 HTML サイトを生成します。
どちらも元の `project-knowledge/` は変更しません。

詳細なルーティング規則とファイル構成は、[wiki/project-knowledge-skills.md](./wiki/project-knowledge-skills.md) を参照してください。
