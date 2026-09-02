# File change classification

`init`、`update`などが追加・更新したファイルを、操作間で再利用できる同一基準で分類する。

## 集計単位

- 操作開始時に存在しなかったファイルを`追加`、存在し内容が変わったファイルを`更新`とする。
- 同じファイルを操作中に複数回変更しても、最終状態の1ファイルとして1回だけ数える。
- 調査・参照しただけのsource projectファイルは数えず、Project Knowledge操作が実際に追加・更新したファイルだけを数える。
- 各ファイルは、次の大分類のうち一つだけに分類する。分類できないファイルを暗黙に除外せず、完了前に分類規則を見直す。

## 大分類

| 大分類 | 判定 | 追加の内訳 |
| --- | --- | --- |
| `Knowledge` | `project-knowledge/docs/`内の通常Concept。`index.md`、`log.md`、`type: Reference`は除く | `pk_category`の`declared`、`extracted`、`derived` |
| `Provenance` | `type: Reference`を持つReference | 文書自身の`pk_source_type`。通常は`user-statement`、`interaction-record`、`reference-document` |
| `Support` | Knowledge Baseの案内、履歴、収集方針、プロジェクト統合を支えるファイル | `index.md`、`log.md`、`knowledge-policy.md`、AGENTS.mdの管理ブロック、`.gitignore` |
| `Internal` | 形式宣言または再構築可能な機械状態 | `manifest.yml`、`state.yml`、`.cache/`内のsnapshot |

Conceptの`sources[].pk_source_type`は根拠の種類であり、Conceptファイル自身の大分類ではない。複数sourceを持つConceptも`Knowledge`の1ファイルとしてだけ数える。`type`は自由な意味分類なので、利用者向け件数の集計軸には使わない。

## 利用者向け表示

`init`と`update`の完了報告では、`Knowledge`と`Provenance`だけを表示する。`Support`と`Internal`は、各分類の件数、追加・更新件数、ファイル名を利用者へ表示しない。

表示上の合計、追加、更新も、`Knowledge`と`Provenance`のファイルだけで計算する。両分類が0件でも省略せず、0件として表示する。`pk_category`と`pk_source_type`の内訳は0件の項目を省略してよい。

```text
追加・更新したKnowledgeファイル: 3（追加2、更新1）
- Knowledge: 2（追加1、更新1）
  - declared: 1
  - extracted: 1
- Provenance: 1（追加1、更新0）
  - user-statement: 1
```

収集方針だけを変更した場合など、`Support`だけが変わった操作では表示上の合計は0件になる。件数とは別に、操作結果として変更した方針やKnowledgeの要点は簡潔に報告してよい。
