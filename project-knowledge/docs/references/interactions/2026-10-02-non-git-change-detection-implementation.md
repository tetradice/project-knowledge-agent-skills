---
type: Reference
pk_source_type: interaction-record
generated:
  by: project-knowledge/3.1.0
  at: 2026-10-02T11:14:47+09:00
---

# 非Git環境の差分取得停止の実装記録

利用者は、非Git環境で大容量バイナリなどを含むローカルファイルの処理が長時間化するため、差分取得などの処理を行わないよう求めた。

調査では、`detect_changes.py`の非Git分岐がプロジェクト配下を走査し、各ファイルのhashを計算してsnapshotと比較していた。Git分岐はcommit済み差分、staged、working tree、untrackedを取得する既存契約を維持した。

実装では、非Git分岐をファイル走査前に終了させ、`mode: "non-git"`、空の`changed`、空の`removed`を返すようにした。非Git環境でのhash計算、snapshotの読み書き、差分取得は行わない。既存呼び出しとの互換性のため`--write-snapshot`は受け付けるが、非Git環境では何もしない。不要になった非Gitsnapshotの実装とテストを削除し、状態管理のReferenceと説明文を更新した。

検証では、非Git/Git検出と設定境界に関する対象テスト6件が成功し、`ruff`と`py_compile`も成功した。全テスト一括実行は180秒で停止したが、停止時点に失敗表示はなかった。この全体テスト未完了の境界は残す。実装コミットは`445e`である。
