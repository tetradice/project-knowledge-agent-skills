# config

Knowledgeの育成・記述方針に属する設定を表示・変更する。保存先は`knowledge-policy.md`のYAML frontmatterであり、Policy本文や未知キーを変更しない。

管理する設定は次のとおり。

```yaml
knowledge:
  human_readable: false
learning:
  mode: opportunistic
```

`human_readable: true`では人間がそのまま読める文章を優先する。falseでは検索効率、簡潔さ、構造、重複回避を優先するが、断片的にしすぎない。

`learning.mode`は`manual`、`opportunistic`、`aggressive`のいずれかとする。詳細は[learning-modes.md](learning-modes.md)を読む。形式1.0では両方の設定を必須とし、欠落や不正値を推測して補わない。

ユーザーが「今後は自動的に更新して」「明示時だけ更新して」などと自然言語で指示した場合も設定変更として処理する。

表示または変更には`uv run <skill>/scripts/policy_settings.py project-knowledge/knowledge-policy.md`を使う。変更時は`--human-readable true|false`または`--learning-mode manual|opportunistic|aggressive`を指定する。

壊れたYAML、未知のmode、不正型では推測せず停止する。publishの出力形式と対象範囲は`project-knowledge-publish`の実行時指定であり、ここでは永続化しない。
