# Large scenario

`large-lifecycle`はQuickと同じ6観点を、人工的な大規模Source Project、12回のupdate、成長するKnowledge Baseで評価する。Largeはscale / lifecycleのテストであり、coverage / depthを広げる未実装のFullとは別である。

## 実行手順

1. `uv run --with pyyaml <runner> large prepare large-lifecycle`を実行する。出力された`large.json`が隔離workspace、version、Change Set、step結果を保持する。Largeは明示実行時だけ開始し、通常CIやQuickから起動しない。
2. `agents/scenarios.yml`の`large-lifecycle.actor`設定で独立Actorを起動する。Actorへ渡すのはworkspace、開発中checkoutの`project-knowledge/SKILL.md`、依頼`このプロジェクトのProject Knowledgeを初期構築してください。`だけとし、期待値、Change Set、Judge rubricを渡さない。
3. Actor終了後、`session record <large.json> actor <session-id> --agent-path <agent-path> --step initial`でsessionを記録し、`large validate <large.json>`を実行する。
4. `initial`、`update-06`、`update-12`では、Quickと同じ6観点と`scenarios/large-lifecycle/expectations.yml`で独立Judgeを実行する。JudgeはsourceとKnowledgeを読み取り専用で比較し、`large.json`と同じdirectoryの`judges/<step>.json`だけへQuickと同じJSON契約を書き込む。終了後は`session record <large.json> judge ... --step <step>`で記録する。
5. `large advance <large.json>`で次のChange Setを適用し、独立Git commitを作る。続いて新しい独立Actorへ`このプロジェクトのProject Knowledgeを更新してください。`とworkspace、Project Knowledge Skillだけを渡す。Actor終了後にsession記録、`large validate`を行う。この手順を全12 Change Setで繰り返す。
6. checkpoint以外ではJudgeを起動しない。各stepではdeterministic validation、repository規模、変更ファイル数・変更bytes、Knowledge統計を保存する。
7. `large report <large.json>`で人間向けSummaryを表示し、同じ`large.json`へstep別result、Actor/Judge別usage、集計を保存する。usageは対応するCodex rollout JSONLからだけ計測し、取得不能時は`unavailable`のままとする。
8. 結果を退避した後、成否にかかわらず`large cleanup <large.json>`で一時workspaceを削除する。

Large実行は大きな人工Fixture、複数update cycle、高いtoken usageを伴う。確認promptは追加しないが、実行者は開始前にこのコスト特性を認識する。

## Judge JSON契約

Quickの`correctness`、`completeness`、`provenance`、`classification`、`noise_rejection`、`unsupported_claims`と同じ契約を使う。Large専用の別rubricは作らない。各観点は`result`、`reason`、`evidence`を持ち、全体`result`と`issues`の整合条件もQuickと同じである。

## Step result

`large.json.steps[]`は`step`、`operation`、`change_set`、`changed_files`、`changed_bytes`、`repository`、`validation`、`quality_score`、`knowledge`、`actor_usage`、`judge_usage`、`issues`を保持する。`changed_bytes`はChange Set対象の変更前後byte数の合計であり、token推定には使わない。

Model Benchmarkへ接続するときは、Scenarioを`quick-basic`または`large-lifecycle`、execution modeを`normal`または`benchmark`として分離し、このlifecycle descriptorと共通usage/Judge処理を候補ごとに再利用する。初期実装では高コストな全モデル実行を自動化しない。
