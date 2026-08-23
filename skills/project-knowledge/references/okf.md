# OKF v0.2

`docs/` 全体をナレッジ Bundleとして扱い、`docs/index.md` と `docs/log.md` を必須とする。通常のナレッジ文書はConceptとして、少なくとも次のfrontmatterを持たせる。

```yaml
---
title: 文書タイトル
description: いつ読む文書かが分かる短い説明
version: "0.1.0"
generated:
  by: ai-agent
  at: 2026-08-23T00:00:00Z
sources:
  - id: implementation
    resource: ../../../src/example.ts
---
```

根拠がない場合も`generated`を残し、推測を事実として書かない。検証済みなら`verified`、陳腐化期限が妥当なら`stale_after`を追加する。絶対パスは避ける。ナレッジからReferenceへは相対リンクまたは`sources.resource`で追跡可能にする。

indexはルーティング文書であり、各リンクに「何を判断するときに読むか」を添える。`log.md` は変更の要約、対象、根拠を追記し、秘密情報や会話全文を保存しない。

