# refactor

Knowledgeの外部的な意味・情報・provenanceをできるだけ維持しながら、[audit.md](audit.md)と同じ観点でKnowledge Baseを診断し、客観的で安全な構造問題を改善して再診断する。`audit`を別操作として呼び出さず、診断、変更、再診断を`refactor`の一連の処理として行う。

## 手順

1. [Format 1.0](../../project-knowledge/references/data-formats/1.0.md)を読み、形式1.0であることを確認する。形式が異なる場合は書き込まない。
2. [audit.md](audit.md)の観点で対象範囲を診断し、findingごとに改善の確実性、意味への影響、変更規模を判断する。
3. 明白な重複の統合、過度に大きいConceptの分割、過度に細かいConceptの統合、不適切な配置、index・navigation、dead link、表現揺れ、空ページや明白な残骸を必要最小限の差分で改善する。
4. 移動・統合・分割時は、元のclaimとsourceを新しい配置へ対応づける。sourcesを和集合として保持して重複だけを除き、`pk_source_type`、User Statement、Interaction Recordへの到達性を失わせない。変更後の内容には適切な`generated`を記録する。
5. 関連indexとリンクを更新してvalidatorを実行し、同じaudit観点で対象範囲を再診断する。安全に解消できるfindingが残る場合は追加修正し、不確実性が残る場合は止めて未修正として報告する。
6. 改善したfinding、意味・source・provenanceの保持方法、再診断結果、改善しなかったfindingと理由を報告する。

## 保守的な境界

- Knowledgeの意味を変える変更、根拠やprovenanceを失う変更は行わない。
- 大量のConceptを一度に統合・削除せず、Knowledge Base全体のinformation architectureを根本的に変更しない。
- 複数の妥当な構造案があり一意に優れた案を判断できない場合や、意図的な分離の可能性が高い場合は変更しない。
- 空ページや残骸を削除するのは、固有のclaimやsourceがなく、参照元を更新でき、削除後も情報と到達性が保たれる場合だけとする。
- 内容・根拠・鮮度・形式の正しさは修正せず、必要なら`project-knowledge`の`fix`を案内するだけにする。
- `refactor`から`audit`、`verify`、`fix`、`update`、`publish`を別操作として自動実行しない。
