# Architecture

依存方向は`api -> service -> repository`です。APIからRepositoryの読み書きを直接行ってはいけません。

- 外部の文字列IDはAPI境界で`ShipmentId.parse`を使ってdomain型へ変換する。
- Serviceは業務上の失敗を`CourierError`の派生型で通知する。
- APIは`CourierError`を捕捉し、各exceptionの`code`とmessageを公開responseへ変換する。
- Shipmentの変更は新しい値を返し、Repositoryの`save`で保存する。
- 状態名やvalidation値はコードへ重複記述せず、`config/cancellation.json`から読み込む。
