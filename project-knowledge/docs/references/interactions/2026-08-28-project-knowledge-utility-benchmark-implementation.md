---
type: Reference
pk_source_type: interaction-record
generated:
  by: project-knowledge/3.1.0
  at: 2026-08-28T18:52:00+09:00
---

# Project Knowledge Utility Benchmarkの実装と実行記録

`project-knowledge-benchmark` v1.0.0、設定、Python Runner、session measurement、11件の専用テストを追加した。RunnerはcleanなGit repositoryのcommitからopaque名のA/B worktreeを作り、No-Knowledge側だけ`project-knowledge/`を除外する。Task実行中は元worktreeのGit linkを退避し、各candidateを単一commitだけ持つlocal repositoryへ切り替えるため、No-Knowledge側から元Git履歴でKnowledgeを復元できない。`blind`後または`recover`で元worktree linkを復元し、workspaceは削除しない。

Runnerの段階的CLIは`prepare`、`session record`、`evaluate`、`blind`、`report`、`recover`である。`evaluate`はcondition baselineとの差分を保存するため、Task Agentがcommitした変更も取得する。checksは明示YAMLから固定し、candidate workspaceを複製して実行する。Windowsの深いdirectoryではextended-length pathを使い、evaluation copyとblind snapshotを作成する。

usageはCodex rollout JSONLを唯一のsourceとする。session IDだけでなくparent session ID、agent path、`turn_context.model`を照合し、最初の累積usageから親由来baselineを除く。計測不能時は`unavailable`と理由を保存する。creditはモデル別rate tableからuncached input、cached input、outputを分けて換算し、reasoning outputを二重計上しない。

2026-08-28にこのrepositoryを対象とするsingle-run smoke benchmarkを実行した。baseline commitは`216e89304944e4dd56366c2264266ca414d89f83`で、TaskはREADMEの`project-knowledge-benchmark` Skill表記を完全一致で検証するpytestを追加するものだった。Task AgentとJudgeはともにGPT-5.6 Terra、low reasoning、独立contextで起動した。

No-KnowledgeとWith-Knowledgeはともに1変更ファイル、機械評価PASSだった。Task Agent usageはNo-Knowledgeが420445 tokens、4.53955 credits、With-Knowledgeが503061 tokens、5.95848 creditsだった。Judge usageは176079 tokens、3.1713 creditsだった。blind JudgeはWith-Knowledgeに対応するCandidate 2を、より説明的なtest名を理由に僅差で選好した。両candidateとも同じ要求を満たし、この単純なsingle-runはProject Knowledgeの一般的効果、モデルの優劣、token効率を示すものではない。

実行artifactはrepository外の`C:\work\temp\project-knowledge-agent-skills-project-knowledge-benchmarks\run-20260828-181908-7c4bc0a0\`へ保存した。`comparison.md`、`comparison.json`、`benchmark.json`、session log、A/B diff、機械評価log、blind snapshot、Judge JSON、復元済みA/B workspaceを保持している。

実装後の全pytestは100件、既存Scenario Testは38件、変更対象Ruffと`git diff --check`はPASSした。全体Ruffには今回未変更の`skills/project-knowledge-publish/scripts/build_offline_docs.py`のimport順エラー1件が残る。
