# プロジェクトの知識を次の開発に活かす：Project Knowledgeスキル入門

AIエージェントに、同じ設計判断やプロジェクトの前提を何度も説明していないでしょうか。
コードには現在の実装が残っていても、「なぜこの方式を選んだのか」「どの制約を前提にしたのか」は、会話や担当者の記憶に埋もれがちです。

Project Knowledgeは、プロジェクト固有の仕様、設計判断、実装・運用上の知識を、根拠とともにMarkdownへ整理し、次の作業で再利用するAgent Skillです。
この記事では、何を解決するSkillなのか、どのように使い始め、日々の開発でどう育てるのかを説明します。

## この記事の対象と到達点

対象読者は、AIエージェントを使って開発しているものの、過去の調査結果や設計判断を再利用できていない開発者です。

読み終えると、次のことができるようになります。

- Project Knowledgeが解決しようとしている問題を説明する。
- プロジェクトへKnowledgeを初期化し、保存した内容を質問する。
- 新しい判断や実装差分を`update`で反映し、`verify`と`fix`を使い分ける。
- 保存先の設定と、専用Skillとの責務の違いを判断する。

記事の対象バージョンは、リポジトリに含まれる`project-knowledge` Skill 3.1.0とProject Knowledge形式1.0です。
AIエージェントへの依頼例は利用するホストに依存しません。
後半のCLI例だけは、Skillをリポジトリから直接実行するWindows PowerShell環境を前提にしています。

## Project Knowledgeが解決する問題

Project Knowledgeが扱うのは、単にファイルを置くことではありません。
「あとで使う価値のある知識を選び、根拠と状態を保ったまま、AIエージェントが参照できる形に整える」ことが目的です。

たとえば認証方式を決めたとき、コードには実装だけを残し、採用理由や前提条件は会話にしか残らないことがあります。
Project Knowledgeでは、将来も使う判断を関連するKnowledge文書へ反映し、根拠となるファイルややり取りも追跡できるようにします。

これにより、次の作業で毎回プロジェクト全体を調べ直したり、過去の会話から採用案を探したりする負担を減らせます。
一時的なデバッグ情報や、保存に向かない秘密情報を何でも記録する仕組みではありません。

README、設計書、ADRを置き換えるものでもありません。
それらを人が読む正式な文書として維持しつつ、AIエージェントが次の作業で再利用する価値のある知識を、根拠とともに管理する補助線として使います。
既存文書をすべてコピーするのではなく、将来の判断に使う情報だけをPolicyに従って残すのが基本です。

## まずは初期化して、保存した知識に質問する

### 事前に用意するもの

SkillのインストールにはNode.jsを使います。
Skillの付属スクリプトを実行する通常利用には、Python 3.11以上とuvも必要です。

リポジトリからSkillをインストールする場合は、ターミナルで次を実行します。

```console
npx skills add https://github.com/tetradice/project-knowledge-agent-skills
```

以降の`$project-knowledge ...`は、PowerShellへ入力するターミナルコマンドではなく、Skillを利用できるAIエージェントのチャット欄へ入力する例です。
`$`はSkillを明示的に呼び出す記法であり、利用するエージェントの記法に合わせて省略できる場合があります。
このSkillの`init`や`update`は、独立したCLIサブコマンドではなく、AIエージェントへ伝える操作の意図です。

### 既存プロジェクトからKnowledgeを作る

対象プロジェクトを開き、次のように依頼します。

```text
$project-knowledge init
```

自然言語で「プロジェクトナレッジを初期化してください」と依頼してもかまいません。
既存プロジェクトのREADME、コード、設定、設計資料などを調査し、形式1.0のKnowledge Bundleを作成します。
何も入れずに構造だけ作りたい場合は、「空で初期化してください」と明示します。

すでに`project-knowledge.yaml`があるプロジェクトでは、初期化をやり直さないでください。
まず`project-knowledge-inspect`で現在の構成を確認し、既存Knowledgeへ情報を追加するなら`update`、単一レイヤーを分けるなら明示的に`split`を依頼します。

初期化後は、`project-knowledge-inspect`で保存された内容の概要、構成、文書数、更新方針を確認できます。

```text
$project-knowledge-inspect
```

初期化の成功は、AIエージェントの報告だけで判断しません。
少なくとも、`project-knowledge.yaml`が対象プロジェクトのルートにあり、解決されたレイヤーに`manifest.yml`と`docs/index.md`があり、`inspect`で保存内容の概要を確認できる状態を目安にします。

### 保存した内容をKnowledgeだけで確認する

たとえば、認証方式と採用理由を確認するには次のように依頼します。

```text
$project-knowledge-fast-ask 認証方式と、その採用理由を教えてください。
```

`project-knowledge-fast-ask`は、`project-knowledge/docs/`に保存されたKnowledgeだけを根拠に回答します。
Knowledgeに根拠がなければ、コードやWebを勝手に調べて補わず、判断できないと伝えます。
保存済みの判断を確認する用途と、現在のコードの動作を調査する用途を分けられる点が重要です。
質問への回答に、保存された文書や根拠が示され、記録がない場合に「判断できない」と返ることを確認できれば、最初の利用は成功です。

## 日々の開発でKnowledgeを更新する

設計を決めたとき、実装を変更したとき、運用上の注意点が分かったときは、Knowledgeも更新します。

```text
$project-knowledge update 今回決めた認証方式と採用理由をナレッジに残してください。
```

`update`は、依頼内容、会話、実装差分、既存Knowledge、収集Policyを確認し、将来利用価値のある情報だけを関連文書へ反映します。
User StatementやInteraction Recordが必要な場合は、根拠として残し、関連するConceptにも反映します。

保存するタイミングは`knowledge-policy.md`の`learning.mode`で選べます。

| 設定 | 更新候補を評価するタイミング |
| --- | --- |
| `manual` | 明示的に更新を依頼したときだけ |
| `opportunistic` | 作業単位の完了時に、将来価値のある変更があるか評価するとき |
| `aggressive` | 作業単位の完了時に、より広い範囲の候補を評価するとき |

自動更新を選んでも、発言や操作を毎回そのまま保存するわけではありません。
収集方針はプロジェクト固有の`knowledge-policy.md`に残り、秘密情報、一時情報、重複した情報は保存対象から外します。

## `update`、`verify`、`fix`を使い分ける

似た依頼でも、目的によって操作が変わります。

| やりたいこと | 使う操作 | 書き込み |
| --- | --- | --- |
| 新しい判断や実装差分を反映する | `project-knowledge`の`update` | あり |
| Knowledgeの内容が根拠や現在の実装と一致するか確認する | `project-knowledge`の`verify` | なし |
| 既存Knowledgeの客観的な問題を直す | `project-knowledge`の`fix` | あり |
| 保存方針や学習タイミングを変更する | `project-knowledge`の`config` | 設定に応じてあり |

たとえば、実装変更を反映したいときは`update`を使います。
現在の実装と文書の一致を調べたいだけなら、次のように明示します。

```text
$project-knowledge verify
```

検査だけを依頼した`verify`は、ファイルを修正しません。
問題が見つかり、根拠のある修正まで求めるときは、別途`fix`を依頼します。

```text
$project-knowledge fix
```

このSkillでは、`update`の後に`verify`を自動実行したり、`verify`の後に`fix`へ自動昇格したりしません。
何を変更するかを利用者が判断できるように、情報の追加、正しさの検査、既存問題の修正を分けています。

迷ったときは、次のように判断します。

- 新しい判断や実装差分を記録するなら`update`。
- 状態を調べるだけで、ファイルを変更しないなら`verify`。
- 既存Knowledgeの誤りや古さを、根拠に基づいて直すなら`fix`。
- `verify`で新しい実装状態が分かり、それをKnowledgeへ反映するなら、結果を確認したうえで`update`。
- `verify`で既存記述の客観的な誤りが確認でき、修正を依頼するなら`fix`。

## 保存先は設定ファイルから解決する

Project Knowledgeは、プロジェクト内に`project-knowledge/`というディレクトリがあるだけでは動作しません。
プロジェクトルートの`project-knowledge.yaml`を入口にして、登録されたKnowledgeレイヤーを解決します。

最小構成の設定は次の形です。

```yaml
version: "1.0"
layers:
  - id: default
    name: プロジェクトナレッジ
    path: ./project-knowledge
```

`version`は文字列の`"1.0"`で、ユーザーの指示なしに上げません。
`id`は機械向けの不変な識別子、`name`は利用者向けの呼称、`path`はKnowledgeの管理ディレクトリです。
`access`を省略すると`read-write`になり、読み取り専用にする場合は`access: read-only`を明示します。

複数の保存先を使う場合は、レイヤーごとに用途、権限、任意性、自動選択の可否を設定できます。
参照時は利用可能な全レイヤーを対象にし、書き込み時は明示指定や`write_target`などから一つのレイヤーだけを選びます。
これにより、開発用の知識と運用用の知識を混ぜずに管理できます。

設定がない場合に、既定のディレクトリを推測して読み書きすることはありません。
まず設定を解決し、対象と書き込み先を明確にするのが安全な使い方です。

## 何が保存されるのか

既定配置では、次のようなファイルが作られます。

```text
プロジェクト/
├── project-knowledge.yaml
└── project-knowledge/
    ├── manifest.yml
    ├── knowledge-policy.md
    ├── state.yml
    └── docs/
        ├── index.md
        ├── log.md
        ├── 知識をまとめたMarkdown文書
        └── references/
            ├── interactions/
            └── user-statements/
```

`manifest.yml`はKnowledge形式と版を示します。
Knowledge本文は`docs/`にあり、`index.md`が文書への入口になります。
`knowledge-policy.md`は何を保存するかと、更新候補を評価するタイミングを定めます。
`state.yml`は差分検出などに使う作業状態で、Knowledge本文の正本とは分離されています。

形式1.0では、Knowledge文書のfrontmatterに、知識の分類、導出方法、根拠となる`sources`などを持たせます。
そのため、本文だけをコピーするよりも「この判断はどこから来たのか」「現在も確認できるのか」を追跡しやすくなります。

## 目的別の専用Skill

日常の初期化・更新・検証・修正は`project-knowledge`が担当します。
それ以外の目的には、専用Skillを明示して使います。

| 目的 | 専用Skill |
| --- | --- |
| 操作方法を確認する | `project-knowledge-help` |
| 保存内容や構成、更新方針を把握する | `project-knowledge-inspect` |
| Knowledgeだけを根拠に質問する | `project-knowledge-fast-ask` |
| 人向けMarkdownやオフラインHTMLを生成する | `project-knowledge-publish` |
| 重複、肥大化、分断などの構造を監査する | `project-knowledge-audit` |
| Knowledgeなし・ありで同じ作業を比較する | `project-knowledge-benchmark` |

たとえば、操作方法だけを知りたいときは次のように依頼します。

```text
$project-knowledge-help update
```

`help`や`inspect`が別の操作を自動実行することはありません。
同じように、構造の監査である`audit`と、実際に整理する`refactor`も分かれています。

## リポジトリ開発者向け：CLIで設定と形式を確認する

普段の利用は、ここまでに説明したようにAIエージェントへ依頼します。
SkillやKnowledgeの開発者が、このリポジトリから直接実行して設定や形式を確認する場合だけ、次のCLIを使います。

```powershell
uv run .\skills\project-knowledge\scripts\project_config.py --project-root .
```

出力に`version: "1.0"`、登録レイヤー、`resolved_path`、書き込み先が現れれば、どのKnowledgeを対象にするかを確認できます。
この記事の対象リポジトリでは、設定解決が成功し、1件の`read-write`レイヤーが`default`として選ばれました。

形式とリンクなどの構造を読み取り専用で検査する場合は、解決済みのKnowledgeパスを渡します。

```powershell
uv run .\skills\project-knowledge\scripts\validate_knowledge.py .\project-knowledge --project-root .
```

この記事の確認環境では`No structural findings`が出力されました。
これは構造検査の結果であり、Knowledgeに書かれたすべての主張が現在の実装と一致することを意味しません。
内容の根拠や鮮度まで確認するには、AIエージェントへ明示的に`$project-knowledge verify`を依頼します。

## まず一つの判断から始める

最初からプロジェクト全体を完璧に記録しようとする必要はありません。
次の順序で、一つの仕様や設計判断を対象に試すと仕組みを確認しやすくなります。

1. `init`で既存プロジェクトのKnowledgeを作る。
2. `project-knowledge-fast-ask`で、保存した仕様や判断を質問する。
3. 次の開発で分かった採用理由や運用上の注意を`update`で追加する。
4. 必要な時点で`verify`を依頼し、問題を直す場合だけ`fix`を使う。

Project Knowledgeの価値は、情報を大量に保存することではなく、次の作業で使う知識を、根拠とともに残し、更新できることにあります。

## 参考資料

- [README](../README.md)：インストール、CLI、専用Skillの一覧
- [`project-knowledge` Skill](../skills/project-knowledge/SKILL.md)：操作の選択と共通ルール
- [ルート設定の解決](../skills/project-knowledge/references/project-config.md)：設定ファイルとレイヤーの解決規則
- [Format 1.0](../skills/project-knowledge/references/data-formats/1.0.md)：保存形式とfrontmatter
- [Knowledge Policy](../skills/project-knowledge/references/knowledge-policy.md)：保存方針の扱い
- [`project-knowledge-help`](../skills/project-knowledge-help/SKILL.md)：利用者向けの操作案内
- [`project-knowledge-fast-ask`](../skills/project-knowledge-fast-ask/SKILL.md)：Knowledge限定回答の範囲
