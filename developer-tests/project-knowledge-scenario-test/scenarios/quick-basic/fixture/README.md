# Quick Relay

Quick Relayは、注文イベントを外部通知先へ中継する小さなサービスです。

## 永続的な仕様

- `order.paid`イベントだけを通知対象とします。
- 顧客識別子は、ログへ出力する前にSHA-256でハッシュ化します。
- 通知失敗時の再試行回数と待機時間は`config/relay.yml`で管理します。

ローカル起動時は`python src/relay.py`を実行します。
