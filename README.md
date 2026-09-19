# project-knowledge-agent-skills

## ルート設定（必須）

`project-knowledge.yaml`の存在を利用条件とし、`version: "1.0"`と`layers`、各要素の`id`、`name`、`path`を必須とします。
`id`は不変の機械識別子、`name`はAIと利用者が使う呼称です。`description`は`default`以外で必須です。`access`を省略すると`read-write`になります。読み取り専用にする場合は`access: read-only`を指定します。
複数レイヤーでは参照操作が全レイヤーを対象とし、書込み操作は1レイヤーだけを選びます。`auto_select: false`は曖昧なAI自動選択からレイヤーを除外します。設定の版はユーザーの指示なしに上げません。
本文中の`project-knowledge/`は既定配置の例です。実際のパス、探索規則、初期化と移行は[ルート設定仕様](skills/project-knowledge/references/project-config.md)に従います。


AIエージェントが、プロジェクト固有の仕様・設計判断・実装・運用知識を継続的に整理するAgent Skillです。

## インストール

[Node.js](https://nodejs.org/ja)を用意し、次を実行して表示されたSkillを選択します。

```console
npx skills add https://github.com/tetradice/project-knowledge-agent-skills
```

`npx skills add`以外の通常利用には、Python 3.11以上と[uv](https://docs.astral.sh/uv/)が必要です。各Skillが案内する`uv run`コマンドは、同梱スクリプトの依存関係を自動的に用意して実行します。Node.jsは上記のインストール操作にだけ必要です。

## CLIの実行例

SkillのReferenceにある`<skill-root>`は、対象Skillのインストール先を表します。`<project-root>`は操作対象プロジェクトのルートです。`<knowledge-root>`はルート設定で解決したKnowledgeレイヤーのパスです。SkillをAgentから通常利用する場合、パス解決はSkillの手順に従います。

このリポジトリをcloneして直接実行する場合は、次のように対象Skillのパスを指定できます。

```console
uv run ./skills/project-knowledge/scripts/project_config.py --project-root .
```

PowerShellでは、同じコマンドを次のように実行できます。

```powershell
uv run .\skills\project-knowledge\scripts\project_config.py --project-root .
```

Reference内の`<skill-root>`などの表記は、そのまま入力する文字列ではなく、上記の実際のパスへ置き換えてください。

## Skill

| Skill | 版 | 用途 |
| --- | --- | --- |
| `project-knowledge` | `3.1.0` | Knowledgeの初期構築・更新・検証・修正・設定 |
| `project-knowledge-help` | `1.0.0` | 基本操作と利用者向け専用Skillを定型形式で案内 |
| `project-knowledge-inspect` | `1.0.0` | Knowledgeの概要・構成・文書数・更新方針を説明 |
| `project-knowledge-fast-ask` | `2.0.0` | Knowledgeだけを根拠に回答 |
| `project-knowledge-publish` | `2.0.0` | Knowledgeと現在のProject ArtifactからMarkdownまたはoffline HTMLを生成 |
| `project-knowledge-audit` | `3.1.0` | Knowledge Baseの構造を監査・refactor |
| `project-knowledge-benchmark` | `1.0.0` | 任意の実務TaskをKnowledgeなし/ありでblind比較 |

日常的な利用と保守には`project-knowledge`を使います。`init`、`update`、`verify`、`fix`、`config`はCLIサブコマンドではなく、自然言語のintentです。

`project-knowledge-help`は明示指定された場合だけ、メイン操作と利用者向けSkillの使い方を定型形式で説明します。`project-knowledge-inspect`はKnowledge Baseの概要、構成、文書数、更新方針をread-onlyで説明し、内容の正しさや構造品質は評価しません。Skill名の明示指定と自然言語の依頼に対応します。

保守操作は次のように分かれます。`verify`と`audit`は読み取り専用で、`fix`と`refactor`だけが検出事項を修正します。

| 観点 | 検査のみ | 検査＋修正 |
| --- | --- | --- |
| Knowledge内容の正しさ | `verify` | `fix` |
| Knowledge Baseの構造・品質 | `audit` | `refactor` |

`update`は、新しい情報や変更をKnowledgeへ反映する別の操作です。`verify`は結果を`pass`、`fail`、`warning`、`not-verifiable`、`stale`、`not-applicable`に分けます。

## 自然言語依頼と専用Skill

自然言語で通常の保守を依頼するときは`project-knowledge`を使います。専用Skill名を明示した場合は、そのSkillだけを実行します。専用Skillから別の操作へ自動的に移ることはありません。

| 依頼 | 推奨Skill | 書込み | 主な結果 |
| --- | --- | --- | --- |
| Knowledgeを根拠に質問する | `project-knowledge-fast-ask` | なし | Knowledgeに限定した回答 |
| 新しい情報や実装差分を反映する | `project-knowledge` の `update` | あり | 選択したレイヤーのKnowledge更新 |
| 現在の実装との一致を確認する | `project-knowledge` の `verify` | なし | 検査結果の報告 |
| 既存Knowledgeの問題を修正する | `project-knowledge` の `fix` | あり | 修正と再検査の報告 |
| Knowledge Baseの構造を確認する | `project-knowledge-audit` | なし | 構造監査の報告 |
| Knowledgeを公開用成果物にする | `project-knowledge-publish` | あり | `published/markdown` または `published/html` |

`$project-knowledge ask`や`$project-knowledge publish`は、互換的なサブコマンドとして扱いません。質問には`$project-knowledge-fast-ask`を、公開には`$project-knowledge-publish`を明示してください。

```text
$project-knowledge-help
$project-knowledge-help init
$project-knowledge-help publish
$project-knowledge-inspect
Project Knowledgeがどのような構造で、何を格納しているか説明してください。
プロジェクトナレッジを空で初期化してください。
今回話した認証方式をナレッジに残してください。
Knowledgeが現在の実装と一致するか検証してください。
Project Knowledgeの問題を修正してください。
今後は明示的な依頼時だけ更新してください。
```

次の専用機能は明示的に指定した場合だけ実行します。

```text
$project-knowledge-fast-ask ログイン方式を教えてください。
$project-knowledge-publish 開発環境構築をoffline HTMLとして出力してください。
$project-knowledge-audit Knowledge Baseの重複や肥大化を監査してください。
$project-knowledge-audit Project Knowledgeの構造をrefactorしてください。
$project-knowledge-benchmark この実装TaskをKnowledgeなし/ありで比較してください。
```

`project-knowledge-benchmark`は任意のGit管理プロジェクトを対象にします。現在存在するProject Knowledgeの実務効果をsingle-runで観測します。A/B workspace、session、diff、機械評価、blind Judge、comparison reportを別のrun directoryへ残します。通常の保守やScenario Testからは自動起動しません。

## 開発者向けテスト

`project-knowledge-scenario-test`は一般ユーザー向けのインストール対象に含めません。[developer-tests/project-knowledge-scenario-test](developer-tests/project-knowledge-scenario-test/)に配置しています。Quick、Large、Model Benchmark、Utilityの各テストは、リポジトリ開発者が同ディレクトリの`SKILL.md`を明示的に読み込んで実行します。

操作とSkillは自動連鎖しません。`project-knowledge-help`と`project-knowledge-inspect`から別操作へ移りません。`verify`から`fix`、`audit`から`refactor`へ自動昇格しません。`update`後の自動検証、情報不足時の通常調査、更新後の自動publishも行いません。旧形式の`$project-knowledge help`は互換実行せず、`$project-knowledge-help`の明示使用だけを案内します。

## 対応形式

全SkillはProject Knowledge形式1.0だけを扱います。形式は`project-knowledge/manifest.yml`で宣言します。

```yaml
format: project-knowledge
format_version: "1.0"
```

Skill版、Knowledge形式版、OKF版、state schema版は独立しています。変更時の規則は[Version contracts](skills/project-knowledge/references/versioning.md)を参照してください。

## License

このリポジトリは、[CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/)に基づき、可能な範囲でパブリックドメインに提供します。詳しい条件は[LICENSE](LICENSE)と[CC0の法的コード](https://creativecommons.org/publicdomain/zero/1.0/legalcode)を参照してください。第三者の依存物や別途ライセンスが明記された成果物には、それぞれのライセンスが適用されます。
