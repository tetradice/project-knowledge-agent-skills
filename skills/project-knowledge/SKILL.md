---
name: project-knowledge
description: project-knowledge/ の新規構築、現在状態との差分検証、明示的な同期更新を扱う。`$project-knowledge init`、`$project-knowledge check`、`$project-knowledge update` の指定、または同じ意図の自然言語による依頼で使用する。ナレッジだけを情報源とする質問回答や、人間向け文書、HTMLの公開には使用しない。
---

# Operation

依頼全体の意図から、次の operation を一つ選ぶ。
明示された operation を優先し、判断によって変更内容が変わる場合は変更前に確認する。
複数指定された場合は、最初に実行する operation を確認する。

選択した instruction を最後まで読む。
instruction に従って処理を続ける場合は、共通 reference の [format.md](references/format.md)、[metadata.md](references/metadata.md)、[evidence.md](references/evidence.md) を最後まで読む。

- `init`: ナレッジを新規構築し、`AGENTS.md` へ案内を反映する。[init.md](references/instructions/init.md) に従い、指定された時点で [template_AGENTS.md](references/template_AGENTS.md) を読む。
- `check`: ナレッジと現在状態の差分を、ファイルを変更せず検証する。[check.md](references/instructions/check.md) に従う。
- `update`: 明示的な依頼に基づいてナレッジを更新する。[update.md](references/instructions/update.md) に従う。

通常の実装作業だけを理由に `update` を実行しない。
