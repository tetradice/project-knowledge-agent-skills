# Knowledge Policy

`project-knowledge/knowledge-policy.md`を、そのProject Knowledgeで何を保存するかのsource of truthとして読む。YAML frontmatterの`knowledge.human_readable`と`learning.mode`は機械判定用、Markdown本文は収集・品質判断用である。初期値はこのSkillの`templates/knowledge-policy.md`から生成する。

保存価値は固定スコアや対象領域のallow-listではなく、現在のPolicy本文と情報の将来影響から判断する。ユーザーによる保存指示は強いシグナルだが、秘密情報、危険な情報、明らかな一時情報、保存不適切な情報は永続化しない。

## Policyの変更

収集方針に関する自然言語指示は`update`として扱い、対象領域一覧ではなく判断原則または補足方針としてPolicy本文へ反映する。必要なら同じ会話や作業から該当ナレッジも抽出する。
