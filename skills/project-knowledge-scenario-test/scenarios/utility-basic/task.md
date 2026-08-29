# Task: shipment cancellation API

既存アーキテクチャとプロジェクト規約に従って、shipmentをキャンセルするAPI関数を追加してください。

- 公開入口は`courier.api.cancel_shipment(repository, shipment_id, reason)`とする。
- 成功時は既存APIと同じresponse形式で、更新後のshipmentを返す。
- ID、validation、状態遷移、error mappingはプロジェクト内の既存情報と規約に従う。
- 既存機能を壊さず、必要な層へ実装を分ける。
- workspace外のファイルは読まない。

実装と必要なtestだけを変更してください。
