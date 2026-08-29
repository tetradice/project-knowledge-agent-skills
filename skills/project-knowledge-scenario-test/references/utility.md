# Utility Benchmark

`utility`は`utility-basic`の同一TaskをNo-KB / With-KBで各1回実行する、開発者向けのsingle-run A/B Benchmarkである。Knowledge Baseの統計的効果を断定する回帰testではない。

## 実行手順

1. `uv run --with pyyaml <skill-root>/scripts/scenario_test.py utility prepare utility-basic`を実行する。出力された`utility.json`だけがCondition、workspace、blind Candidateの対応を保持する。
2. `knowledge_builder` workspaceで、Quickと同じ開発中checkoutの`project-knowledge` Skillを使う独立Agentを起動する。依頼は`このプロジェクトのProject Knowledgeを初期構築してください。`だけとし、`task.md`、`expectations.yml`、`hidden_tests/`、Task Agentのcontextを渡さない。モデルはQuickのBuilder設定を使い、`fork_turns: none`とする。
3. Builder終了後、`utility install-knowledge <utility.json>`を実行する。runnerはBuilderのsource不変性とKnowledgeを検査し、同じsource stateから作ったWith-KB workspaceだけへ`project-knowledge/`を複製する。No-KB workspaceには追加しない。
4. `agents/utility.yml`の`task`設定で、No-KBとWith-KBを別々のTask Agentとして起動する。両方とも`model: gpt-5.6-terra`、`reasoning_effort: low`、`fork_turns: none`を使い、各Agentへ次だけを渡す。
   - 対応するworkspaceの絶対path
   - `<skill-root>/scenarios/utility-basic/task.md`の本文
   - workspace全体を調査して実装すること
   - workspace外のscenario、期待値、hidden test、もう一方のCandidateを読まないこと
5. 各Task Agent終了後、`utility evaluate <utility.json> no_kb`と`utility evaluate <utility.json> with_kb`を実行する。build、既存test、Task Agent非公開のhidden checks、scopeを機械評価する。deterministic結果はJudgeへ渡さない。
6. `utility blind <utility.json>`を実行する。runnerはCondition対応をrandom化した`Candidate A` / `Candidate B` snapshotを作り、`.git`と`project-knowledge/`を除外する。
7. `agents/utility.yml`の`judge`設定で独立Judgeを`model: gpt-5.6-terra`、`reasoning_effort: low`、`fork_turns: none`として起動する。Judgeには次だけを渡す。
   - `blind_candidates`に記録されたCandidate A / Bのpath
   - 同一のTask本文
   - 下記JSON契約と共通rubric
   - 出力先`<utility.jsonの親>/judge.json`
8. JudgeへCondition対応、Knowledgeの有無、token usage、実行時間、deterministic結果、改善期待を渡さない。成果物だけを読み取り、`judge.json`以外を変更させない。不正JSONの場合だけ同じJudgeへ形式修正を1回依頼する。
9. `utility report <utility.json>`を実行する。標準出力と更新された機械可読`utility.json`を報告する。
10. 結果を保存した後、`utility cleanup <utility.json>`でBuilder、Task、blind workspaceをまとめて破棄する。成否にかかわらずcleanupする。

## Judge JSON契約

```json
{
  "candidates": {
    "Candidate A": {
      "dimensions": {
        "requirement_compliance": {"score": 0, "reason": "...", "evidence": ["..."]},
        "project_convention_compliance": {"score": 0, "reason": "...", "evidence": ["..."]},
        "architectural_consistency": {"score": 0, "reason": "...", "evidence": ["..."]},
        "scope_discipline": {"score": 0, "reason": "...", "evidence": ["..."]},
        "code_quality": {"score": 0, "reason": "...", "evidence": ["..."]},
        "maintainability": {"score": 0, "reason": "...", "evidence": ["..."]}
      }
    },
    "Candidate B": {"dimensions": "same keys as Candidate A"}
  },
  "preference": "Candidate A",
  "summary": "成果物の主要な違いを簡潔に記述"
}
```

各scoreは0から100の整数とし、両Candidateへ同じ基準を使う。動作確認の代替として推測で加点せず、成果物から観察できる設計、規約、scope、保守性だけを評価する。

## Token usage

`utility.json`は`knowledge_builder`、`no_kb_task`、`with_kb_task`、`judge`を分離する。実行環境が各Agentの実測usageを返す場合だけ対応欄へ記録する。推定値を正式なBenchmark値にせず、取得できなければ全項目を`unavailable`のままにする。Task比較へBuilderやJudgeのusageを混ぜない。

## Fixtureとhidden evaluation

`utility-basic/fixture`内のREADME、source、config、docs、公開testsには、Taskを解く一次情報を分散して置く。BuilderはこれらだけからKnowledgeを構築する。`task.md`と`hidden_tests/`はworkspaceへ複製しない。

hidden evaluatorは機能、validation、error mapping、Service/Repository境界、config利用を評価する。既存testの回帰はTask Agentが変更できない初期契約のcopyで分母を固定して評価する。AI Judgeのscoreと混ぜず、`deterministic.json`へcheck単位で保存する。
