---
name: project-knowledge-publish
description: Explicit-only workflow for publishing project-knowledge/docs as human-readable Markdown or offline HTML. Use only when the user explicitly names project-knowledge-publish or invokes it as $project-knowledge-publish; do not use for general summarization or formatting requests.
metadata:
  version: "2.0.0"
---

# Project Knowledgeの公開

## 対象プロジェクトの解決

このSkillは共通の設定解決に`project-knowledge` Skillを必要とする。
プロジェクトのKnowledgeへアクセスする前に[ルート設定](../project-knowledge/references/project-config.md)に従って`project_config.py`を実行する。
`project-knowledge.yaml`がなければ対象外とし、固定ディレクトリから推測しない。一般的な利用案内は設定なしでも説明できる。
以後の`project-knowledge/`表記は解決済みのレイヤーパスを意味する。
`description`を用途と適用範囲の判断に使い、書き込み前には`--write`で対象を確認する。読み取り専用レイヤーへstateや成果物も保存しない。
設定の`version: "1.0"`は必須で、ユーザーの指示なしに版を上げない。複数レイヤーの同時利用は未対応とする。


明示的に呼び出された場合だけ、`project-knowledge/docs/`の持続的な情報と現在のProject Artifactから確認できる実装構造を人間向け成果物へ変換し、原則として`project-knowledge/published/`へ出力する。通常の要約・整形依頼から自動選択しない。

公開は`docs/`を機械的にコピーする処理ではない。文書ごとに読み手にとっての理解しやすさを評価し、[Publishing](references/publishing.md)の変換規則と品質ゲートを満たすMarkdown、offline HTML、または両方を生成する。Project Artifactの調査対象、詳細度、今回指定された出力形式と対象範囲をKnowledge Baseへ永続化しない。

形式1.0だけをread-onlyで公開できる。形式が異なる場合は推測せず、対応するSkill版が必要だと報告する。

Knowledge本文へ逆同期せず、`project-knowledge`を含む他Skillを自動実行しない。
