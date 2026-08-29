---
type: Reference
pk_source_type: interaction-record
generated:
  by: project-knowledge/3.1.0
  at: 2026-08-28T15:36:03+09:00
---

# Quick / Benchmark credit計測の実装記録

`session_usage.py`をQuick、Benchmark共通のmeasurement層として追加した。`CODEX_HOME`、未設定時はWindowsの`USERPROFILE/.codex`またはユーザーhomeからCodex homeを解決し、session IDを含むrollout候補の`session_meta.id`、`parent_thread_id`、agent path、`turn_context.model`を記録済みsubagent情報と照合する。結果には絶対パスではなくrolloutファイル名だけを残す。

parserは最初の`total_token_usage - last_token_usage`を親由来のbaselineとして復元し、最後の`total_token_usage - baseline`を対象sessionのraw usageにする。累積値と`last_token_usage`は合計しない。必須field欠落、JSONL破損、累積値後退、cached input矛盾、識別子不一致、未知modelなどでは`unavailable`と理由を返す。

`agents/credit-rates.yml`に、checked_at 2026-08-28のGPT-5.6 Luna、Terra、SolのCodex rateを集約した。creditsは`input_tokens - cached_input_tokens`、cached input、outputを別々に換算し、reasoning outputを二重加算しない。Quick reportはActor、Judge、Orchestrator、measured totalを別表示し、Benchmark reportはActor credits、Judge credits、Benchmark total credits、Best quality、Lowest creditsを分離する。

2026-08-27の既存single-run `quick-basic`の6 rolloutを新parserで再計測した。Actor creditsはLuna 0.241434、Terra 11.036310、Sol 14.716300で、既存品質結果はLuna 67、Terra 100、Sol 100だった。Judge credits合計は1.056546、Benchmark totalは27.050590だった。この再計測は新しいBenchmark実行ではない。

`test_session_usage.py`にJSONL parsing、baseline / delta、credit calculation、session対応付けの14件を追加し、Runner統合テストを更新した。Scenario test 34件、Project Knowledge test 49件、Ruff、`py_compile`、`git diff --check`がPASSした。実装commitは`8f1ac755c3de30039773ed7d6882806980ab1940`である。
