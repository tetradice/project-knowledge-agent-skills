# OKF v0.2 compatibility

`project-knowledge/docs/`はOKF v0.2 bundleである。Knowledge形式版は`project-knowledge/manifest.yml`に記録し、OKF版とは別に管理する。

通常のConceptは、予約ファイル以外のMarkdownとしてparse可能なYAML frontmatterを持ち、空でない`type`を含む。Project Knowledge形式0.3で新規作成する通常Conceptには、さらに`pk_category`と`pk_derivation`を含める。`sources`の各項目には`resource`と`pk_source_type`を含める。

```yaml
---
type: Architecture
pk_category: extracted
pk_derivation: synthesized
sources:
  - resource: ../../../README.md
    pk_source_type: project-artifact
generated:
  by: project-knowledge/0.4.0
  at: 2026-08-26T00:00:00+09:00
---
```

actorはOKFのactor文字列として扱う。人は`human:<id>`、処理は`process:<id>`、Skillは`<skill-name>/<semver>`を使用する。

## Reserved files

- root `index.md`のfrontmatterは`okf_version: "0.2"`だけを持つ。
- nested `index.md`はfrontmatterを持たない。
- rootおよびnested `log.md`はfrontmatterを持たない。
- `log.md`の見出しは日付形式にする。

本文リンクはMarkdownファイルからの相対パス、`sources[].resource`はbundle root基準のパスまたは有効なURIとして解決する。claim単位でsourceを示す場合は、本文中にsource ID付きfootnoteを置く。

OKF標準外のProject Knowledge独自fieldには`pk_`を付ける。`type`、`status`、`sources`、`generated`、`verified`、`stale`、`stale_after`はOKF fieldなので改名しない。`manifest.yml`、`state.yml`、`config.yml`はOKF ConceptのfrontmatterではなくProject Knowledgeの管理ファイルであり、このprefix規約の対象外とする。

OKFで任意のfieldでも、Project Knowledge形式0.3が新規Conceptに要求するfieldはvalidatorで検査する。
