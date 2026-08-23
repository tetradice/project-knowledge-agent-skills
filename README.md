# project-knowledge-agent-skills

AIエージェントが、プロジェクト固有の仕様・設計判断・実装・運用知識を継続的に整理するAgent Skillです。

## インストール

[Node.js](https://nodejs.org/ja)を用意し、次を実行して表示されたSkillを選択します。

```console
npx skills add https://github.com/tetradice/project-knowledge-agent-skills
```

## 基本的な使い方

日常利用では`update`と`ask`を使います。operationはCLIサブコマンドではなく、自然言語のintentとして解釈されます。

| operation | 用途 | 例 |
| --- | --- | --- |
| `update` | 新情報、会話、実装差分、収集方針をナレッジへ統合 | `$project-knowledge update` |
| `ask` | プロジェクトナレッジだけを根拠に回答 | `$project-knowledge ask 認証方式を説明してください` |

管理・保守操作として`init`、`publish`、`verify`、`audit`、`config`も利用できます。

コマンド名を覚える必要はありません。次の指示はすべて`update`として処理されます。

```text
この仕様をナレッジに追加してください。
今回話した認証方式をナレッジに残してください。
最近変更した実装内容をナレッジに反映してください。
今後は障害対応で判明したことも積極的に保存してください。
```

`capture`と`memo`はユーザー操作ではなく、一次情報と会話由来情報を区別する内部provenanceです。旧`capture` / `memo`指定は互換入力として`update`へ読み替えます。旧`scope`指定はナレッジ Policyの表示・変更へ読み替えますが、新しい操作としては案内しません。

## 初期化

scope指定なしで初期化できます。

```text
$project-knowledge init
```

初期ナレッジを指定しても、それは今回最初に作る内容であり、将来のナレッジ領域を限定しません。

```text
プロジェクトナレッジを初期化して、アプリケーション概要と開発環境構築をまとめてください。
```

管理ファイルと最低限の構造だけが必要な場合は`$project-knowledge init --empty`を使います。

## ナレッジ Policy

`project-knowledge/knowledge-policy.md`は対象領域のallow-listではなく、将来利用価値のある情報を保存するか判断する品質ポリシーです。新しい領域でも、プロジェクト固有で再利用価値があり、Policyに反しなければナレッジへ追加できます。

肥大化は、ナレッジ-worthiness判定、重複回避、Incremental Update、Progressive Disclosure、`verify`、`audit`で防ぎます。

## Learning mode

```yaml
learning:
  mode: opportunistic
```

- `manual`: 明示的なupdate intentがある場合だけ更新します。
- `opportunistic`: 作業単位の完了時に候補を評価し、価値がある場合だけ更新します。既定値です。
- `aggressive`: opportunisticより広めに候補を拾いますが、一時情報や重複は保存しません。

旧`update.automatic_after_work`はinit時にmanualまたはopportunisticへ安全に移行されます。旧`scope.md` / `scope.yml`も、対象指定をallow-listとして残さずナレッジ Policyへ意味的に移行されます。
