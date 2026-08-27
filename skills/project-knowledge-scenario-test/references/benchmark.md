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
3. 各workspaceへ既存の`validate`を実行する。FAILまたはERRORのcandidateはJudgeを起動しない。
4. PASSしたcandidateだけを、`agents/benchmark.yml`の固定Judgeモデルで評価する。Judgeには`Candidate A`、`Candidate B`等のIDだけを渡し、モデル名、トークン、コスト、実行時間を渡さない。Quickと同じexpectations、JSON契約、読み取り専用制約を使い、各candidateの親directoryへ`judge.json`を書かせる。
5. `uv run --with pyyaml <skill-root>/scripts/scenario_test.py benchmark report <benchmark.json>`を実行する。標準出力の比較表と更新されたJSONを報告する。
6. 完了後、各candidate workspaceを既存の`cleanup`で削除し、空になったbenchmark rootを削除する。

## Token usage

Actor usageは実行環境が実測値を返す場合だけ記録する。文字数その他から推定しない。現行のsubagent起動結果がusageを返さない場合、`benchmark.json`と比較表ではすべて`unavailable`のままにする。JudgeとorchestratorのusageをActor usageへ混ぜない。

## 結果

`benchmark report`はdeterministic結果、Quick Judgeの6観点、PASS数の100点換算quality score、Actor token usage、Knowledgeの基本統計、issueを表示する。quality scoreはQuick Judgeの集計値であり、token efficiencyや恣意的な総合Winnerには用いない。
