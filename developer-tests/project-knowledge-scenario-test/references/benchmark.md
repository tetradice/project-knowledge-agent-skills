# Benchmark

`benchmark`は`quick-basic`を各Actorモデルで1回ずつ実行する、開発者向けのsingle-run比較である。Quickのfixture、Actor依頼、deterministic validation、Judge rubricを複製・変更しない。

## 実行手順

1. `uv run --with pyyaml <skill-root>/scripts/scenario_test.py benchmark prepare quick-basic`を実行する。出力された`benchmark.json`が候補とworkspaceの対応を保持する。`agents/benchmark.yml`がActorモデルと固定Judgeの唯一の定義場所である。
2. JSONの各candidateについて、対応する`model`、`reasoning_effort: low`、`fork_turns: none`でActorを起動する。すべてに同一の依頼を渡す。
   - workspaceの絶対パス
   - `<skill-root>/../project-knowledge/SKILL.md`の絶対パス
   - 依頼文: `このプロジェクトのProject Knowledgeを初期構築してください。`
   - workspaceをプロジェクトrootとして、指定Skillと必要なReference・scriptを通常どおり使うこと
   - workspace外のシナリオ、期待値、テスト実装を読まないこと
3. 各Actor終了後、spawn結果を`session record <benchmark.json> actor <session-id> --agent-path <agent-path> --candidate <model-id>`で記録する。prepare時に親session IDを取得できなかった場合だけ`--parent-session-id`も指定する。Actorへusageを自己申告させない。
4. 各workspaceへ既存の`validate`を実行する。FAILまたはERRORのcandidateはJudgeを起動しない。
5. PASSしたcandidateだけを、`agents/benchmark.yml`の固定Judgeモデルで評価する。Judgeには`Candidate A`、`Candidate B`等のIDだけを渡し、モデル名、トークン、コスト、実行時間を渡さない。Quickと同じexpectations、JSON契約、読み取り専用制約を使い、各candidateの親directoryへ`judge.json`を書かせる。Judge終了後も`session record <benchmark.json> judge <session-id> --agent-path <agent-path> --candidate <model-id>`で記録する。
6. `uv run --with pyyaml <skill-root>/scripts/scenario_test.py benchmark report <benchmark.json>`を実行する。標準出力の比較表と更新されたJSONを報告する。
7. 完了後、各candidate workspaceを既存の`cleanup`で削除し、空になったbenchmark rootを削除する。

## Usageとcredits

Quickと共通の`session_usage.py`が、記録したsession IDに対応するrollout JSONLをCodex homeから一意に特定し、session metadataとmodelを照合する。最初の累積usageから最初のlast usageを引いて親由来baselineを求め、最後の累積usageとの差だけを対象Actor/Judgeのusageとする。JSONL以外へfallbackせず、安全に特定・算出できない値は`unavailable`とする。

比較用コストは`agents/credit-rates.yml`の`checked_at: 2026-08-28`のCodex credit rateを使う。uncached input、cached input、outputを別々に換算し、cached inputとreasoning outputを二重計上しない。Actor creditsをCandidate間比較の主指標にし、Judge creditsは全Candidate共通コストとして合計を別表示する。Orchestratorを独立sessionとして正確に区切れない場合は`unavailable`とし、Actor/Judgeへ混ぜない。

## 結果

`benchmark report`はdeterministic結果、Quick Judgeの6観点、PASS数の100点換算quality score、Actor credits、raw token usage、Knowledgeの基本統計、issueを表示する。`Best quality`と`Lowest credits`は分離し、quality/creditsだけでBest Modelを自動決定しない。usage計測失敗は品質結果と独立して表示する。
