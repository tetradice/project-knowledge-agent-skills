---
name: project-knowledge
description: project-knowledge/ の参照、新規構築、現在状態との差分検証、同期更新を扱う。`$project-knowledge init`、`check`、`update` の明示指定、または同じ意図の自然言語による依頼で使用する。ナレッジだけを情報源とする質問回答や、人間向け文書、HTMLの公開には使用しない。
---

# 基本

この `SKILL.md` は operation router として使用する。operation 固有の手順は、選択した instruction へ委譲する。

次のルールを守る。

- operation が明示されている場合は、その指定を優先する。
- operation が省略されている場合は、単語の一致ではなく依頼全体の意図から選ぶ。
- 複数の operation が明示されている場合は、指定順に処理し、その時点で必要な instruction だけを読む。
- operation を一意に判断できず、選択によって変更内容が変わる場合は、ファイルを変更する前に確認する。
- 選択していない operation の instruction は読まない。
- instruction が指定した共通 reference だけを追加で読む。
- 通常の実装作業を理由に `project-knowledge/` を更新しない。更新は `update` が明示された場合だけ行う。
- `project-knowledge/` だけを情報源とする質問には `project-knowledge-fast-ask` を使用する。
- 人間向け Markdown は `project-knowledge-publish`、HTML は `project-knowledge-publish-html` で公開する。
- 公開用の Skill を operation として扱わない。

# Operations

## init

現在のソースコード、設定、trusted raw sources などから、プロジェクトナレッジを新規構築する。

代表的な依頼:

- `$project-knowledge init`
- 「プロジェクトナレッジを初期化して」
- 「このプロジェクトに project-knowledge を作成して」

この operation を選択したら、最初に [references/instructions/init.md](references/instructions/init.md) を最後まで読む。

## check

既存ナレッジと現在のコード、設定、外部環境、trusted raw sources の差異を、ファイルを変更せず検証する。

代表的な依頼:

- `$project-knowledge check`
- 「プロジェクトナレッジを検証して」
- 「古くなっているナレッジがないか確認して」

この operation を選択したら、[references/instructions/check.md](references/instructions/check.md) を最後まで読む。

## update

現在のコード、設定、外部環境、trusted raw sources をもとにナレッジを更新し、`pending.md` を整理する。

代表的な依頼:

- `$project-knowledge update`
- 「プロジェクトナレッジを更新して」
- 「現在の変更をナレッジに反映して」

この operation を選択したら、[references/instructions/update.md](references/instructions/update.md) を最後まで読む。
