# Learning modes

`learning.mode`は明示的なupdate以外でナレッジ候補を評価する頻度を定める。設定変更は`config`コマンドを要求せず、「今後は自動的に更新して」などの自然言語でも受け付ける。

| mode | 動作 |
| --- | --- |
| `manual` | 明示的なupdate intentがある場合だけナレッジを書き換える。 |
| `opportunistic` | ナレッジへ影響する作業単位の完了時に候補を評価し、価値がある場合だけupdateする。 |
| `aggressive` | 作業単位完了時にopportunisticより広く候補を拾うが、一時情報・重複・逐語的転記は保存しない。 |

既定値は安全性と自然な成長のバランスから`opportunistic`とする。自動更新の評価は調査・編集・テスト・修正などを含む作業単位が完了した時点で1回行い、毎ターン、毎ツール呼び出し、毎ファイル編集後には行わない。

新しい認証方式、必須環境変数、deploy方法、migrationルール、外部連携、重要な設計判断、仕様と実装の重要な不一致、再利用するトラブルシューティングは候補になりやすい。typo、変数名、null checkだけの変更、debug log、単発のテスト失敗、import整理、formatting、調査コマンドは通常候補にしない。

自動評価で候補がなければナレッジファイル、`log.md`、`state.yml`を変更しない。候補があれば[update.md](update.md)と[knowledge-policy.md](knowledge-policy.md)に従って関連範囲だけを更新する。
