---
type: Reference
pk_source_type: interaction-record
generated:
  by: project-knowledge/3.1.0
  at: 2026-09-02T11:41:40+09:00
---

# init / updateのファイル変更報告の実装

利用者は、update時に追加・更新したファイル数を、AIが保守するKnowledge、根拠として残すReference、ナビゲーション・管理情報の違いを踏まえて分類したいと相談した。分類の主軸は`type`ではなく文書の役割とし、通常Conceptには`pk_category`、Referenceには`pk_source_type`を補助的に使う方針を提示した。

続いて利用者は、この方針を`project-knowledge` Skillへ導入するよう依頼し、init/update後の件数出力、`Support`と`Internal`の非表示・合計除外、再利用できる独立Markdownへの分類規則の集約を指定した。

実装では`skills/project-knowledge/references/file-change-classification.md`を追加し、`Knowledge`、`Provenance`、`Support`、`Internal`の四分類、追加・更新の数え方、利用者向け報告の表示範囲を定義した。`init.md`と`update.md`はこの共通Referenceを参照し、空initも含めて完了報告に分類件数を出す契約にした。契約テストも追加した。

コミット`8ee7`は分類Reference、init手順、update手順、契約テストの4ファイルだけを変更した。新規契約テストはPASSし、関連テストは既知の標準Policy文言テストを除いて58件PASSした。全体テストの109件PASS・1件FAILについて、失敗は今回未変更の標準Policy文言と既存assertionの不一致であることを確認し、この作業の回帰とは扱わなかった。`git diff --check`はPASSした。
