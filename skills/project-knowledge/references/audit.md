# audit

初回は必ずread-only。固定した対象領域による入口制限の代わりに、ナレッジの品質とコンパクション候補を重点的に監査する。

次をHigh/Medium/Lowで報告する。

- 重複ナレッジと同内容のReference重複
- 不要・未参照Reference、一時情報、ソースコードの過剰転記
- 細かすぎる、巨大すぎる、古い、利用されないナレッジ
- 不要な分割・カテゴリ、関連情報の分散、統合候補
- orphan、肥大化したindex、不要metadata、`.cache/`や生成物の残骸
- ナレッジ Policyに反する情報

Information Architectureでは、巨大ページへの過度な集約、不自然な階層、関連情報の分断、indexからの探しにくさ、より簡潔にできる再編候補を確認する。

ユーザーが実施を明示した場合だけ削除・統合・再編する。`sources`から参照されるReferenceは不用意に削除しない。実施後はlink、source、indexを再検証し、変更内容を`log.md`へ記録する。
