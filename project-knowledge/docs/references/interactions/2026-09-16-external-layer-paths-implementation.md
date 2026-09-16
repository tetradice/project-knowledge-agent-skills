---
type: Reference
pk_source_type: interaction-record
generated:
  by: project-knowledge/3.1.0
  at: 2026-09-16T10:20:04+09:00
---

# 外部レイヤーパス対応の実装記録

利用者は、レイヤーの`path`をプロジェクト内相対パスに限る境界を外し、`..`、絶対パス、UNC、symlink／junction経由の外部レイヤーを、登録済みの`read-write`対象として扱うよう求めた。一方で、環境変数、URL、`~`、globは引き続き拒否し、`version: "1.0"`、設定ファイル自身のsymlink禁止、実体パスの同一・親子重複禁止を維持することを指定した。

実装は、設定解決時に相対・絶対・UNCとリンク先を正規化し、プロジェクトルート自身だけをレイヤー登録から除外する。初期化・分割・復旧の操作記録は正規化済み絶対パスをキーにし、候補、バックアップ、指紋はプロジェクト内の作業領域へ保管する。適用は記録済みの登録対象に限る。プロジェクト内のパスは相対、外部は解決済み絶対パスとして表示し、プロジェクト側の`.gitignore`管理ブロックにはプロジェクト内レイヤーだけを出力する。

実装側は次を確認した。外部パス関連の設定テストは12 passed、1 skipped、44 deselectedで、skipはWindows環境でsymlink作成権限がないためである。UNC、外部`read-write`レイヤーの標準操作、外部source/destinationを持つsplitの中核3件は3 passedだった。`test_layer_workflow.py`全24件は、前半14件と残り7件、ならびに重複する中核3件の実行で全件PASSした。
