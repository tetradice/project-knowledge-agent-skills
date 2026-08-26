# project-knowledge-agent-skills

AIエージェントが、プロジェクト固有の仕様・設計判断・実装・運用知識を継続的に整理するAgent Skillです。

## インストール

[Node.js](https://nodejs.org/ja)を用意し、次を実行して表示されたSkillを選択します。

```console
npx skills add https://github.com/tetradice/project-knowledge-agent-skills
```

## Skill

| Skill | 版 | 用途 |
| --- | --- | --- |
| `project-knowledge` | `3.0.0` | Knowledgeの初期構築・更新・read-only検証・設定 |
| `project-knowledge-fast-ask` | `2.0.0` | Knowledgeだけを根拠に回答 |
| `project-knowledge-publish` | `2.0.0` | Markdownまたはoffline HTMLを生成 |
| `project-knowledge-audit` | `3.0.0` | 重複・肥大化・分断・検索性をread-only監査 |

日常的な保守には`project-knowledge`を使います。`init`、`update`、`verify`、`config`はCLIサブコマンドではなく、自然言語のintentです。

`verify`は「Knowledgeに書かれている内容が正しいか」を根拠・現在状態・Knowledge間の整合性から確認します。`audit`は「Knowledge Baseが適切に整理されているか」を重複・肥大化・分断・検索性から確認します。verifyの結果は`pass`、`fail`、`warning`、`not-verifiable`、`stale`、`not-applicable`を区別し、検出事項を自動修正しません。

```text
プロジェクトナレッジを空で初期化してください。
今回話した認証方式をナレッジに残してください。
Knowledgeが現在の実装と一致するか検証してください。
今後は明示的な依頼時だけ更新してください。
```

次の3つは明示的に指定した場合だけ実行します。

```text
$project-knowledge-fast-ask ログイン方式を教えてください。
$project-knowledge-publish 開発環境構築をoffline HTMLとして出力してください。
$project-knowledge-audit Knowledge Baseの重複や肥大化を監査してください。
```

操作とSkillは自動連鎖しません。`update`後の自動検証、検証結果の自動反映、情報不足時の通常調査、更新後の自動publishは行いません。

## 対応形式

全SkillはProject Knowledge形式1.0だけを扱います。形式は`project-knowledge/manifest.yml`で宣言します。

```yaml
format: project-knowledge
format_version: "1.0"
```

Skill版、Knowledge形式版、OKF版、state schema版は独立しています。変更時の規則は[Version contracts](skills/project-knowledge/references/versioning.md)を参照してください。
