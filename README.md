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
| `project-knowledge` | `3.1.0` | Knowledgeの初期構築・更新・検証・修正・設定 |
| `project-knowledge-fast-ask` | `2.0.0` | Knowledgeだけを根拠に回答 |
| `project-knowledge-publish` | `2.0.0` | Markdownまたはoffline HTMLを生成 |
| `project-knowledge-audit` | `3.1.0` | Knowledge Baseの構造を監査・refactor |
| `project-knowledge-scenario-test` | `1.0.0` | Project Knowledge SkillのQuick E2E品質とUtilityを評価 |

日常的な保守には`project-knowledge`を使います。`init`、`update`、`verify`、`fix`、`config`はCLIサブコマンドではなく、自然言語のintentです。

保守操作は次のように分かれます。`verify`と`audit`は読み取り専用で、`fix`と`refactor`だけが検出事項を修正します。

| 観点 | 検査のみ | 検査＋修正 |
| --- | --- | --- |
| Knowledge内容の正しさ | `verify` | `fix` |
| Knowledge Baseの構造・品質 | `audit` | `refactor` |

`update`は、新しい情報や変更をKnowledgeへ反映する別の操作です。`verify`は結果を`pass`、`fail`、`warning`、`not-verifiable`、`stale`、`not-applicable`に分けます。

```text
プロジェクトナレッジを空で初期化してください。
今回話した認証方式をナレッジに残してください。
Knowledgeが現在の実装と一致するか検証してください。
Project Knowledgeの問題を修正してください。
今後は明示的な依頼時だけ更新してください。
```

次の開発者向け・専用機能は明示的に指定した場合だけ実行します。

```text
$project-knowledge-fast-ask ログイン方式を教えてください。
$project-knowledge-publish 開発環境構築をoffline HTMLとして出力してください。
$project-knowledge-audit Knowledge Baseの重複や肥大化を監査してください。
$project-knowledge-audit Project Knowledgeの構造をrefactorしてください。
$project-knowledge-scenario-test quick
$project-knowledge-scenario-test large
$project-knowledge-scenario-test utility
```

`project-knowledge-scenario-test`はSkill開発者向けです。Quickは小さなFixtureからKnowledgeを正しく構築できるかを確認します。LargeはQuickと同じ品質観点を人工的な実案件規模のFixtureと12回の増分updateで測定し、step別のKnowledge規模とActor/Judge tokenを記録します。Model BenchmarkはActor creditsを主なコスト指標として構築モデルを比較します。Utilityは同一sourceと同一TaskをNo-KB / With-KBで1回ずつ実行し、実作業の品質とtoken usageの差を観測します。通常のProject Knowledge保守から自動起動せず、一時workspaceは実行後に破棄します。Fullシナリオは未実装です。

操作とSkillは自動連鎖しません。`verify`から`fix`、`audit`から`refactor`へ自動昇格せず、`update`後の自動検証、情報不足時の通常調査、更新後の自動publishも行いません。

## 対応形式

全SkillはProject Knowledge形式1.0だけを扱います。形式は`project-knowledge/manifest.yml`で宣言します。

```yaml
format: project-knowledge
format_version: "1.0"
```

Skill版、Knowledge形式版、OKF版、state schema版は独立しています。変更時の規則は[Version contracts](skills/project-knowledge/references/versioning.md)を参照してください。
