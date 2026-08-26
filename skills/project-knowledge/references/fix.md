# fix

既存Knowledgeを[verification.md](verification.md)と同じStructure、Sources、Provenance、Evidence、Current State、Freshness、Consistencyの順で検査し、客観的に修正できる問題を直して再検査する。`verify`を別操作として呼び出さず、検査、修正、再検査を`fix`の一連の処理として行う。

## 手順

1. [Format 1.0](data-formats/1.0.md)と[Knowledge Policy](knowledge-policy.md)を読み、形式1.0であることを確認する。形式が異なる場合は書き込まない。
2. [verification.md](verification.md)の検証順序と判定規則で対象Knowledgeを検査し、findingごとに修正可否と根拠を判断する。
3. sourceやproject artifactから一意に正しい状態を確認できる問題だけを修正する。本文、source、リンク、frontmatter、metadata、manifestとの不整合、古い内容、`stale`を必要最小限の差分で直す。
4. 変更後にvalidatorを実行し、同じ観点で対象範囲を再検査する。修正可能なfindingが残る場合は追加修正し、根拠不足や曖昧さが残る場合は止めて未修正として報告する。
5. 修正したfinding、再検査結果、修正しなかったfindingと理由を報告する。

`stale`は、原因となった差分を確認して内容またはsourceを正した後だけ解消する。既存artifactから根拠を明確に補完できる場合はsourcesへ追加できるが、推測で根拠を作らない。修正で現在内容を変更した場合は`generated`を更新し、sourceと`pk_source_type`を保持する。自分で修正後に読み返しただけでは独立検証にならないため、`verified`を自動追加・更新しない。

## 境界

- `verify`は検査のみでファイルを書き換えない。`fix`は修正意図が明示された場合だけ書き込む。
- `update`は新しい知識、変更された仕様、ユーザーから与えられたKnowledgeを反映する。`fix`は既存Knowledgeにある客観的な問題を見つけて正す。
- Conceptの大規模な統合・分割、重複整理、Knowledge階層やnavigationの再設計、Knowledge Base全体の検索性改善は行わず、明示的な`project-knowledge-audit`の`refactor`へ委ねる。
- 複数の妥当な修正案がある、Knowledgeの意味が変わる、根拠が失われる、または大規模な変更になる場合は勝手に修正しない。
- `fix`から`update`、`verify`、`audit`、`refactor`、`publish`を別操作として自動実行しない。
