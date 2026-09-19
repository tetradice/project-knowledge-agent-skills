# config

最初に[ルート設定](project-config.md)から対象を解決する。ルート設定の表示は`project_config.py --project-root <project-root>`を使い、変更は明示されたキーだけに限定する。設定の`version`をユーザーの指示なしに上げない。
`access`の変更はルート設定で行い、Policyの`learning.mode`や`knowledge.human_readable`とは独立して扱う。
複数構成の`layers`、用途、権限、`write_target`はルート設定で扱い、レイヤー内Policyの設定変更は明示した1件に限定する。新規の複数設定は[init](init.md)、既存文書の配置変更を伴う単一レイヤーの分割は[split](split.md)を使う。configだけで文書を移動しない。

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

表示または変更には`uv run <skill-root>/scripts/policy_settings.py <knowledge-root>/knowledge-policy.md --project-root <project-root>`を使う。`<skill-root>`と`<knowledge-root>`は[ルート設定](project-config.md)の説明に従って実際のパスへ置き換える。変更時は`--human-readable true|false`または`--learning-mode manual|opportunistic|aggressive`を指定する。書き込み可能レイヤーを明示する場合は`--layer <id>`も指定する。

壊れたYAML、未知のmode、不正型では推測せず停止する。publishの出力形式と対象範囲は`project-knowledge-publish`の実行時指定であり、ここでは永続化しない。
