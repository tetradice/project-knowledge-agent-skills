# Quick scenario

`quick-basic`をActor 1回、deterministic validation 1回、Judge 1回で評価する。

## 実行手順

1. Skill rootを基準にrunnerを特定し、`uv run --with pyyaml <skill-root>/scripts/scenario_test.py prepare quick-basic`を実行する。標準出力の絶対パスがActor用workspaceである。
2. Actorを`agents/scenarios.yml`の`quick-basic.actor`設定、`fork_turns: none`で起動する。次の情報だけを与える。
   - workspaceの絶対パス
   - `<skill-root>/../project-knowledge/SKILL.md`の絶対パス
   - 依頼文: `このプロジェクトのProject Knowledgeを初期構築してください。`
   - workspaceをプロジェクトrootとして、指定Skillとそこから参照される必要なReference・scriptを通常どおり使うこと
   - workspace外のシナリオ、期待値、テスト実装を読まないこと
3. Actor終了後、spawn結果のsession/thread IDとcanonical agent pathを`uv run --with pyyaml <runner> session record <workspace> actor <session-id> --agent-path <agent-path>`で記録する。prepare時に`CODEX_THREAD_ID`を取得できなかった場合だけ、`--parent-session-id <orchestrator-session-id>`も指定する。Actorにusageを自己申告させない。
4. `uv run --with pyyaml <runner> validate <workspace>`を実行する。既存validatorに加えて、通常Conceptが1件以上あることと、そのConceptがworkspace内に実在する`project-artifact`を1件以上参照することを検査する。骨組みだけのBundleは`missing-concept`と`missing-project-artifact-source`でFAILとする。
5. validationがFAILまたはERRORならJudgeを起動しない。`report`でJudgeを`SKIPPED`として表示する。
6. validationがPASSなら、JudgeをActorとは別に`agents/scenarios.yml`の`quick-basic.judge`設定、`fork_turns: none`で起動する。Judgeには次だけを与える。
   - source projectであるworkspace。ただし`project-knowledge/`を除く
   - Actorが生成した`<workspace>/project-knowledge/`
   - `<skill-root>/scenarios/quick-basic/expectations.yml`
   - 下記JSON契約と評価規則
   - 出力先`<workspaceの親>/judge.json`
7. Judgeには読み取り専用で評価させ、`judge.json`だけを書かせる。Actorの会話や判断過程は渡さない。Judge終了後はActorと同様に`session record <workspace> judge <session-id> --agent-path <agent-path>`で識別子を記録する。
8. Judge JSONが不正な場合だけ、同じJudgeへ形式修正を1回依頼する。評価のやり直しや別Judgeの起動は行わない。
9. `uv run --with pyyaml <runner> report <workspace>`を実行し、品質結果、Actor/Judge別credits、raw usage、計測状態を含む標準出力をそのままユーザーへ報告する。
10. 成否にかかわらず、最後に`uv run --with pyyaml <runner> cleanup <workspace>`を実行する。cleanup失敗も報告する。

## Usageとcredits

RunnerはCodex homeを`CODEX_HOME`、未設定ならユーザーhomeの`.codex`として解決し、`sessions/**/rollout-*<session-id>*.jsonl`を探索する。ファイル名の時刻や最新ファイルでは選ばず、`session_meta`のsession ID、parent thread ID、agent pathと`turn_context`のmodelを記録値へ照合する。絶対パスは結果へ保存せず、rolloutファイル名だけを残す。

`token_count`の最初の`total_token_usage - last_token_usage`をsession開始前baselineとし、最後の`total_token_usage - baseline`を対象subagent固有のraw usageとする。累積値や重複した`last_token_usage`を合計しない。必須field欠落、破損、値の後退、識別子不一致では推測せず`unavailable`とし、シナリオ品質のPASS/FAILは変えない。

creditsは`agents/credit-rates.yml`を使い、`input_tokens - cached_input_tokens`、cached input、`output_tokens`をそれぞれのrateで換算する。`reasoning_output_tokens`はraw内訳として保持するだけで、outputへ二重加算しない。app-server、Responses API、その他usage source、token単価、通貨換算は使用しない。

## Judge JSON契約

```json
{
  "result": "PASS",
  "dimensions": {
    "correctness": {"result": "PASS", "reason": "...", "evidence": ["..."]},
    "completeness": {"result": "PASS", "reason": "...", "evidence": ["..."]},
    "provenance": {"result": "PASS", "reason": "...", "evidence": ["..."]},
    "classification": {"result": "PASS", "reason": "...", "evidence": ["..."]},
    "noise_rejection": {"result": "PASS", "reason": "...", "evidence": ["..."]},
    "unsupported_claims": {"result": "PASS", "reason": "...", "evidence": ["..."]}
  },
  "issues": [
    {
      "severity": "critical",
      "dimension": "correctness",
      "message": "...",
      "evidence": ["..."]
    }
  ]
}
```

- 各観点はsource、生成Knowledge、意味期待を照合し、文字列一致や固定ファイル構成では判定しない。
- 6観点すべてがPASSで、critical/major issueがない場合だけ全体をPASSとする。
- minor issueは表示するが、それ単独ではFAILにしない。
- `result`は`PASS`または`FAIL`、severityは`critical`、`major`、`minor`だけを使う。
- 問題がなければ`issues`を空配列にする。
