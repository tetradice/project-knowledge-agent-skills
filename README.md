# project-knowledge-agent-skills

AIエージェントが、プロジェクト固有の仕様・設計判断・実装・運用知識を継続的に整理するAgent Skillです。

## インストール

[Node.js](https://nodejs.org/ja)を用意し、次を実行して表示されたSkillを選択します。

```console
npx skills add https://github.com/tetradice/project-knowledge-agent-skills
```

## Skill構成

責務ごとに5つのSkillへ分かれています。

| Skill | 責務 | 発火条件 |
| --- | --- | --- |
| `project-knowledge` | Knowledgeの初期構築・追加・更新・設定 | ナレッジへの反映などの自然言語intent、または明示指定 |
| `project-knowledge-fast-ask` | `project-knowledge/docs/**`だけを根拠に回答 | 明示指定のみ |
| `project-knowledge-publish` | Markdownまたはoffline HTMLを生成 | 明示指定のみ |
| `project-knowledge-verify` | 正確性・鮮度・形式をread-only検証 | 明示指定のみ |
| `project-knowledge-audit` | 重複・肥大化・構造をread-only監査 | 明示指定のみ |

日常的なKnowledgeの構築・更新には`project-knowledge`を使います。`init`、`update`、`config`はCLIサブコマンドではなく、自然言語のintentとして解釈されます。

コマンド名を覚える必要はありません。次の指示はすべて`update`として処理されます。

```text
この仕様をナレッジに追加してください。
今回話した認証方式をナレッジに残してください。
最近変更した実装内容をナレッジに反映してください。
今後は障害対応で判明したことも積極的に保存してください。
```

`capture`と`memo`はユーザー操作ではなく、一次情報と会話由来情報を区別する内部provenanceです。旧`capture` / `memo`指定は互換入力として`update`へ読み替えます。旧`scope`指定はKnowledge Policyの表示・変更へ読み替えますが、新しい操作としては案内しません。

旧`$project-knowledge ask|publish|verify|audit`は実行せず、対応する専用Skillの明示指定を案内します。新しい利用例は次のとおりです。

```text
$project-knowledge-fast-ask ログイン方式を教えてください。
$project-knowledge-publish 開発環境構築をoffline HTMLとして出力してください。
$project-knowledge-verify Knowledgeが現在の実装と一致するか確認してください。
$project-knowledge-audit Knowledge Baseの重複や肥大化を監査してください。
```

4つの専用Skillは互いに自動連携しません。情報不足時の通常調査、検出後の自動更新、更新後の自動publishも行いません。

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

## Knowledge Policy

`project-knowledge/knowledge-policy.md`は対象領域のallow-listではなく、将来利用価値のある情報を保存するか判断する品質ポリシーです。新しい領域でも、プロジェクト固有で再利用価値があり、Policyに反しなければナレッジへ追加できます。

肥大化は、ナレッジ-worthiness判定、重複回避、Incremental Update、Progressive Disclosureで抑えます。必要に応じて`project-knowledge-verify`または`project-knowledge-audit`を明示的に実行します。

## Learning mode

```yaml
learning:
  mode: opportunistic
```

- `manual`: 明示的なupdate intentがある場合だけ更新します。
- `opportunistic`: 作業単位の完了時に候補を評価し、価値がある場合だけ更新します。既定値です。
- `aggressive`: opportunisticより広めに候補を拾いますが、一時情報や重複は保存しません。

旧`update.automatic_after_work`はinit時にmanualまたはopportunisticへ安全に移行されます。旧`scope.md` / `scope.yml`も、対象指定をallow-listとして残さずKnowledge Policyへ意味的に移行されます。
