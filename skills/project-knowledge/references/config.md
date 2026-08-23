# config

表示、設定、解除の対象を明示する。プロジェクト共通値は`config.yml`、個人・環境値は`config.local.yml`へ保存する。既存の未知のキーやコメントを不用意に消さない。

最低限の設定は次のとおり。

```yaml
knowledge:
  human_readable: false
learning:
  mode: opportunistic
memo:
  require_approval_for_trust: true
publish:
  markdown: true
  html:
    enabled: true
    renderer: material-mkdocs
    offline: true
```

`human_readable: true`では人間がそのまま読める文章を優先する。falseでは検索効率、簡潔さ、構造、重複回避を優先するが、断片的にしすぎない。

`learning.mode`は`manual`、`opportunistic`、`aggressive`のいずれかとする。詳細は[learning-modes.md](learning-modes.md)を読む。既定値は`opportunistic`。旧`update.automatic_after_work`はfalseをmanual、trueをopportunisticへ移行する。

ユーザーが「今後は自動的に更新して」「明示時だけ更新して」などと自然言語で指示した場合も設定変更として処理する。
