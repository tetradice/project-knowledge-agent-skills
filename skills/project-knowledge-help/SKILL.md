---
name: project-knowledge-help
description: Explicit-onlyでProject Knowledgeの基本操作と利用者向け専用Skillの使い方を定型形式で説明する。$project-knowledge-helpが明示された場合だけ使用し、説明対象の操作やSkillは実行しない。
metadata:
  version: "1.0.0"
---

# Project Knowledge Help

Project Knowledgeの基本操作と利用者向け専用Skillを、決められた形式で案内するread-only Skillである。明示的に`$project-knowledge-help`を使用された場合だけ実行する。

説明対象の操作やSkillを起動せず、ファイルを作成、更新、削除しない。通常のプロジェクト質問、Knowledge内容への質問、操作の実行には使用しない。

## 対象を選ぶ

引数なし、既知の対象、未知の対象のいずれかを選び、対応する出力形式だけを使う。

既知の対象は次のとおり。

- 基本操作: `init`、`update`、`verify`、`fix`、`config`
- 専用Skill: `inspect`、`fast-ask`、`publish`、`audit`、`refactor`、`benchmark`
- 専用Skillの正式名も受け付ける: `project-knowledge-inspect`、`project-knowledge-fast-ask`、`project-knowledge-publish`、`project-knowledge-audit`、`project-knowledge-benchmark`

`audit`と`refactor`は同じ`project-knowledge-audit` Skillの別操作として説明する。

## 対象なしの出力

見出し、順序、表の列を変更せず、次の内容を出力する。表の各行を省略しない。

# Project Knowledge Help

## 基本操作

| 操作 | 用途 | 操作名指定 | 自然言語例 |
| --- | --- | --- | --- |
| `init` | Project Knowledgeを空または既存プロジェクトの情報から初期構築する | `$project-knowledge init` | `プロジェクトナレッジを初期化してください。` |
| `update` | 将来価値のある情報、実装差分、収集方針をKnowledgeへ反映する | `$project-knowledge update` | `今回決めた認証方式をナレッジに残してください。` |
| `verify` | Knowledgeの内容、根拠、鮮度、形式を読み取り専用で検証する | `$project-knowledge verify` | `Project Knowledgeが現在の実装と一致するか検証してください。` |
| `fix` | 既存Knowledgeの明白な問題を検査して修正し、再検査する | `$project-knowledge fix` | `Project Knowledgeの間違いや古い情報を修正してください。` |
| `config` | 既知の運用設定を表示、変更、解除する | `$project-knowledge config` | `今後は明示的な依頼時だけ更新してください。` |

## 専用Skill

| Skill | 用途 | 明示呼び出し例 |
| --- | --- | --- |
| `project-knowledge-inspect` | Knowledge Baseの概要、構成、文書数、更新方針をread-onlyで説明する | `$project-knowledge-inspect` |
| `project-knowledge-fast-ask` | Knowledgeだけを根拠に質問へ回答する | `$project-knowledge-fast-ask ログイン方式を教えてください。` |
| `project-knowledge-publish` | Knowledgeから人間向けMarkdownまたはoffline HTMLを生成する | `$project-knowledge-publish 開発環境構築をoffline HTMLとして出力してください。` |
| `project-knowledge-audit` | Knowledge Baseの構造をauditし、明示時はrefactorする | `$project-knowledge-audit Knowledge Baseの重複や肥大化を監査してください。` |
| `project-knowledge-benchmark` | 同一TaskをKnowledgeなし・ありで実行して比較する | `$project-knowledge-benchmark この実装TaskをKnowledgeなし・ありで比較してください。` |

## 詳細ヘルプ

対象だけを詳しく確認するには、`$project-knowledge-help init`や`$project-knowledge-help publish`のように指定する。有効な対象は`inspect`、`init`、`update`、`verify`、`fix`、`config`、`fast-ask`、`publish`、`audit`、`refactor`、`benchmark`である。

## 対象指定ありの出力

既知の対象が指定された場合は、その対象だけを説明する。次の見出しをこの順序で使い、見出しを追加、省略、並べ替えしない。

```markdown
# <対象> Help

## 用途
<対象が解決すること>

## 書き込み
<なし、あり、または条件付きの説明>

## 呼び出し方
- 操作名指定: `<明示呼び出し>`
- 自然言語例: `<同じ意図の依頼例>`

## 主な結果
<利用者が受け取る結果>

## 対象外
<扱わないことと責務境界>
```

基本操作の操作名指定には`$project-knowledge <操作名>`を使う。専用Skillには対応する`$project-knowledge-...`を使う。`inspect`の明示呼び出しには`$project-knowledge-inspect`を使う。説明に必要な情報はこのSkill内の対象なし出力と責務境界から組み立て、説明対象を実行しない。

## 未知の対象の出力

未知の対象は推測して補正せず、次の形式だけを返す。説明対象の操作やSkillを実行しない。

```markdown
# Project Knowledge Help

## 用途
指定された対象はProject Knowledge Helpの対象として認識できません。

## 書き込み
なし

## 呼び出し方
- 有効な対象: `inspect`、`init`、`update`、`verify`、`fix`、`config`、`fast-ask`、`publish`、`audit`、`refactor`、`benchmark`

## 主な結果
有効な対象を指定すると、その対象だけの定型ヘルプを返します。

## 対象外
未知の対象の推測、補正、実行は行いません。
```
