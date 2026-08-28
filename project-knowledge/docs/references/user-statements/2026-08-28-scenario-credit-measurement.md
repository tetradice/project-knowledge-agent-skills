---
type: Reference
pk_source_type: user-statement
generated:
  by: project-knowledge/3.1.0
  at: 2026-08-28T15:36:03+09:00
---

# Scenario testのusageとcredit計測方針

QuickシナリオテストとQuickを利用するBenchmarkのusage source of truthを、Codexがローカルへ保存するsession / rollout JSONLだけへ統一する。Codex app-server、Responses API、Actor自身の自己申告、token単価や通貨への換算は使用しない。

対象subagentはsession / thread ID、parent session ID、agent path、modelでrolloutを対応付ける。`token_count`の累積値を単純加算せず、session開始時のbaselineとの差分だけをActorまたはJudge固有usageとする。正確に対応付け・計算できない場合は推測せず`unavailable`とし、品質評価のPASS / FAILとは分離する。

コスト比較はOpenAI Codex creditsを使う。cached inputを通常inputへ二重計上せず、reasoning outputはoutput usageの内訳として扱う。BenchmarkではActor creditsをCandidate比較に使い、Judge creditsは共通コストとして別表示する。Full scenarioは今回追加しない。
