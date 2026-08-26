# project-knowledge-agent-skills

AIエージェントが、プロジェクト固有の仕様・設計判断・実装・運用知識を継続的に整理するAgent Skillです。

## インストール

[Node.js](https://nodejs.org/ja)を用意し、次を実行して表示されたSkillを選択します。

```console
npx skills add https://github.com/tetradice/project-knowledge-agent-skills
```

## Skill構成

責務ごとに5つのSkillへ分かれています。

| Skill | 版 | 責務 | 発火条件 |
| --- | --- | --- | --- |
| `project-knowledge` | `0.4.0` | Knowledgeの初期構築・追加・更新・設定 | ナレッジへの反映などの自然言語intent、または明示指定 |
| `project-knowledge-fast-ask` | `0.3.0` | `project-knowledge/docs/**`だけを根拠に回答 | 明示指定のみ |
| `project-knowledge-publish` | `0.3.0` | Markdownまたはoffline HTMLを生成 | 明示指定のみ |
| `project-knowledge-verify` | `0.3.0` | 正確性・鮮度・形式をread-only検証 | 明示指定のみ |
| `project-knowledge-audit` | `0.3.0` | 重複・肥大化・構造をread-only監査 | 明示指定のみ |

日常的なKnowledgeの構築・更新には`project-knowledge`を使います。`init`、`update`、`config`はCLIサブコマンドではなく、自然言語のintentとして解釈されます。

コマンド名を覚える必要はありません。次の指示はすべて`update`として処理されます。

```text
この仕様をナレッジに追加してください。
今回話した認証方式をナレッジに残してください。
最近変更した実装内容をナレッジに反映してください。
今後は障害対応で判明したことも積極的に保存してください。
```

User StatementとInteraction Recordはユーザー操作ではなく、一次情報と作業経緯を区別する内部provenanceです。旧`capture` / `memo`指定は互換入力として`update`へ読み替えます。旧`scope`指定はKnowledge Policyの表示・変更へ読み替えますが、新しい操作としては案内しません。

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

## バージョン

Skill版とKnowledge形式版は独立して管理します。Skill版は各`SKILL.md`の`metadata.version`にあるSemVer、Knowledge形式版は`project-knowledge/manifest.yml`にある二要素の版です。

```yaml
format: project-knowledge
format_version: "0.3"
```

このほかに、`docs/index.md`の`okf_version: "0.2"`と、`state.yml`の`state_schema_version`があります。SkillのbugfixだけでKnowledge形式版を上げる必要はありません。

manifestがなく、旧`docs/`、config、state構造を持つBundleは形式0.1として検出されます。変更内容の事前確認とmigrationは次のように実行できます。

```console
uv run skills/project-knowledge/scripts/migrate_project.py . --target 0.3 --check
uv run skills/project-knowledge/scripts/migrate_project.py . --target 0.3
```

同名・異内容の移動先がある場合は、全変更を行わず停止します。0.1 Bundleへの`init`または`update`は、書込み前に同じmigrationを行います。未知形式や対応版より新しい形式は推測して変更しません。

## 分類とprovenance

形式0.3の通常Conceptは、情報の種類を`pk_category`、導出方法を`pk_derivation`で別々に記録します。`pk_`はOKF標準外のProject Knowledge独自metadataを示します。代表的な4ケースは次のとおりです。

| ケース | `pk_category` | `pk_derivation` | 例 |
| --- | --- | --- | --- |
| 人がプロジェクト方針を明示 | `declared` | `direct` | 「認証方式はOIDCとする」 |
| 一つのartifactから明示事項を抽出 | `extracted` | `direct` | configの設定値 |
| 複数artifactの明示事項を統合 | `extracted` | `synthesized` | READMEと実装からまとめた起動手順 |
| sourceにない結論を推論 | `derived` | `inferred` | 実装差分から推定した設計意図 |

未検証の`inferred` Conceptは`status: draft`とします。検証後も、推論から生まれた来歴は変えません。`sources`の各sourceには`user-statement`、`reference-document`、`project-artifact`、`interaction-record`、`change-implementation`のいずれかを`pk_source_type`として記録します。

`generated`は現在内容の生成者、`verified`は独立した確認者です。User Statementを保存しただけではhuman verificationになりません。trust tierは保存せず、`verified`から`unverified`、`machine-confirmed`、`human-reviewed`を表示時に導出します。

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
