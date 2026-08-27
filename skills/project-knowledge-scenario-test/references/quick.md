# Quick scenario

`quick-basic`をActor 1回、deterministic validation 1回、Judge 1回で評価する。

## 実行手順

1. Skill rootを基準にrunnerを特定し、`uv run --with pyyaml <skill-root>/scripts/scenario_test.py prepare quick-basic`を実行する。標準出力の絶対パスがActor用workspaceである。
2. Actorを`model: gpt-5.6-luna`、`reasoning_effort: low`、`fork_turns: none`で起動する。次の情報だけを与える。
   - workspaceの絶対パス
   - `<skill-root>/../project-knowledge/SKILL.md`の絶対パス
   - 依頼文: `このプロジェクトのProject Knowledgeを初期構築してください。`
   - workspaceをプロジェクトrootとして、指定Skillとそこから参照される必要なReference・scriptを通常どおり使うこと
   - workspace外のシナリオ、期待値、テスト実装を読まないこと
3. Actor終了後、`uv run --with pyyaml <runner> validate <workspace>`を実行する。
4. validationがFAILまたはERRORならJudgeを起動しない。`report`でJudgeを`SKIPPED`として表示する。
5. validationがPASSなら、JudgeをActorとは別に`model: gpt-5.6-luna`、`reasoning_effort: low`、`fork_turns: none`で起動する。Judgeには次だけを与える。
   - source projectであるworkspace。ただし`project-knowledge/`を除く
   - Actorが生成した`<workspace>/project-knowledge/`
   - `<skill-root>/scenarios/quick-basic/expectations.yml`
   - 下記JSON契約と評価規則
   - 出力先`<workspaceの親>/judge.json`
6. Judgeには読み取り専用で評価させ、`judge.json`だけを書かせる。Actorの会話や判断過程は渡さない。
7. Judge JSONが不正な場合だけ、同じJudgeへ形式修正を1回依頼する。評価のやり直しや別Judgeの起動は行わない。
8. `uv run --with pyyaml <runner> report <workspace>`を実行し、標準出力をそのままユーザーへ報告する。
9. 成否にかかわらず、最後に`uv run --with pyyaml <runner> cleanup <workspace>`を実行する。cleanup失敗も報告する。

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
