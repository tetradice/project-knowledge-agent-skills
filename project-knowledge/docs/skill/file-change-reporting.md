---
type: Project Knowledge Reporting Contract
pk_category: extracted
pk_derivation: synthesized
status: stable
generated:
  by: project-knowledge/3.1.0
  at: 2026-09-03T10:43:11+09:00
sources:
  - resource: ../references/user-statements/2026-09-03-file-change-reporting-labels.md
    pk_source_type: user-statement
  - resource: ../references/interactions/2026-09-03-file-change-reporting-labels-implementation.md
    pk_source_type: interaction-record
  - resource: ../references/user-statements/2026-09-02-file-change-reporting.md
    pk_source_type: user-statement
  - resource: ../references/interactions/2026-09-02-file-change-reporting-implementation.md
    pk_source_type: interaction-record
  - resource: ../../../skills/project-knowledge/references/file-change-classification.md
    pk_source_type: change-implementation
  - resource: ../../../skills/project-knowledge/references/init.md
    pk_source_type: change-implementation
  - resource: ../../../skills/project-knowledge/references/update.md
    pk_source_type: change-implementation
  - resource: ../../../skills/project-knowledge/tests/test_project_knowledge.py
    pk_source_type: change-implementation
---

# init / updateのファイル変更報告

`init`と`update`は、Project Knowledge操作が実際に追加・更新したファイルを、操作開始時の存在有無で`追加`または`更新`として数える。同じファイルを操作中に複数回変更しても最終状態で1回だけ数え、調査しただけのsource projectファイルは数えない。

分類の正本は`skills/project-knowledge/references/file-change-classification.md`である。各ファイルは次の大分類の一つへ分類する。

- `Knowledge`: `docs/`内の通常Concept。`pk_category`の`declared`、`extracted`、`derived`を内訳に使う。
- `Provenance`: `type: Reference`のReference。文書自身の`pk_source_type`を内訳に使う。
- `Support`: `index.md`、`log.md`、`knowledge-policy.md`、AGENTS.mdの管理ブロック、`.gitignore`など、案内・履歴・収集方針・統合を支えるファイル。
- `Internal`: `manifest.yml`、`state.yml`、`.cache/`内のsnapshotなど、形式宣言または再構築可能な機械状態。

Conceptの`sources[].pk_source_type`は根拠の種類であり、Conceptファイル自身の大分類ではない。複数のsourceを持つConceptも`Knowledge`の1ファイルとしてだけ数える。`type`は自由な意味分類なので、件数の集計軸には使わない。

利用者向けの完了報告には`Knowledge`と`Provenance`だけを表示し、合計、追加、更新もこの二分類だけで計算する。`Support`と`Internal`は件数、追加・更新件数、ファイル名を表示しない。二分類がともに0件でも0件として表示し、収集方針だけを変えた場合などは、件数とは別に変更内容を簡潔に報告する。

利用者向けの表示名は、内部値を変えずに日本語化する。`Knowledge`は「ナレッジ文書」、`Provenance`は「根拠資料」とし、`declared`、`extracted`、`derived`はそれぞれ「方針・判断」、「資料から抽出した情報」、「分析の結果」と表示する。`user-statement`、`interaction-record`、`reference-document`はそれぞれ「ユーザー指示」、「作業・対話記録」、「参照資料」と表示する。

通常init、空init、updateのいずれでも分類件数を出力する。分類規則はinit/update手順へ重複記載せず、両手順から共通Referenceを参照する。

## 実装と検証境界

実装コミット`8ee7`で独立Reference、init/updateの参照、契約テストを追加した。分類契約の単体テストはPASSし、Project Knowledge関連テストは既知の標準Policy文言テストを除いて58件PASSした。全体テストは109件PASS、1件FAILで、失敗は今回変更していない標準Policy文言と既存assertionの不一致である。`git diff --check`はPASSした。

後続コミット`0e62`で表示名の対応表と日本語の出力例を追加し、`derived`は利用者指定どおり「分析の結果」とした。対応表を確認する契約テストと、UTF-8モードでのSkill validatorはPASSした。
