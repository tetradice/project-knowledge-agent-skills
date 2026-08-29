# Knowledge Policy

このSkillに同梱する[標準Knowledge Policy](standard-knowledge-policy.md)を、Project Knowledgeで何を保存するかの標準方針として読む。

`project-knowledge/knowledge-policy.md`は、YAML frontmatterに機械判定用の`knowledge.human_readable`と`learning.mode`を持ち、Markdown本文に標準Policyへの宣言と参照情報を持つ。初期値はこのSkillの`templates/knowledge-policy.md`から生成する。

プロジェクト固有の収集方針が本文にある場合は、その方針を標準Policyより優先し、指定されていない部分へ標準Policyを適用する。保存価値は固定スコアや対象領域のallow-listではなく、適用されるPolicyと情報の将来影響から判断する。ユーザーによる保存指示は強いシグナルだが、秘密情報、危険な情報、明らかな一時情報、保存不適切な情報は永続化しない。

## Policyの変更

収集方針に関する自然言語指示は`update`として扱い、対象領域一覧ではなく判断原則または補足方針としてPolicy本文へ反映する。本文は次の順序で構成する。

1. `プロジェクト固有の方針は以下です。`
2. ユーザーが指定したプロジェクト固有の方針
3. `上記以外は Agent Skill \`project-knowledge\` の標準ポリシーに従います。`
4. `参照: Agent Skill \`project-knowledge\` 同梱の \`references/standard-knowledge-policy.md\``

プロジェクト固有の方針がない場合は、標準Policyに従う宣言と同梱Referenceの参照情報だけを本文に置く。必要なら同じ会話や作業から該当ナレッジも抽出する。
