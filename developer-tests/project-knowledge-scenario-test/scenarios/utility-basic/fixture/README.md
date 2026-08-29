# Courier Ledger

Courier Ledgerはshipmentの状態を扱う小さなPythonライブラリです。Python 3.11以上と標準ライブラリだけを使います。

公開APIは入力をdomain型へ変換してServiceを呼び出し、`ApiError`を次のresponseへ変換します。

```python
{"status": 400, "error": {"code": "...", "message": "..."}}
```

業務処理はServiceへ置き、永続化はRepositoryを通してください。詳細は`docs/architecture.md`、キャンセル規則は`config/cancellation.json`、既存の実装例は`src/courier/`と`tests/`にあります。

Testは次で実行します。

```console
python -m unittest discover -s tests
```
