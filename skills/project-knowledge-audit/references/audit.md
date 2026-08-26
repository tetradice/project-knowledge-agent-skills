# audit

Knowledge Baseの重複・冗長性・肥大化・分断・ナビゲーション・検索性・情報設計をread-onlyで監査する。

次を確認し、改善候補をHigh impact/Medium impact/Low impactで報告する。

- 重複Knowledgeと同内容のReference重複
- 不要・未参照Reference、一時情報、ソースコードの過剰転記
- 細かすぎる、巨大すぎる、利用されないKnowledge
- 不要な分割・カテゴリ、関連情報の分散、統合候補
- orphan、肥大化したindex、`.cache/`や生成物の残骸
- 巨大ページへの過度な集約、不自然な階層、indexからの探しにくさ

監査中はファイルの削除・統合・分割・移動・再編を行わない。findingごとに根拠、影響、対象、推奨する改善を示すだけにし、`refactor`その他の操作を自動実行しない。
