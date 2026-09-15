# split — 既存1レイヤーから新規レイヤーへの分割

明示された分割依頼に使う。[複数レイヤー共通手順](multi-layer.md)で定義と配置表を固定する。
既存の複数レイヤー間の再配分、全体再編、本文の意味変更は対象外。通常updateや保守的refactorにこの責務を混ぜない。

## 手順

1. 共通設定CLIで元IDを解決する。元ID・パス・権限を維持する。元がread-onlyなら、権限変更の明示指示なしに進まない。
2. 元の全Concept、Reference、User Statement、Interaction、添付ファイルを調べる。主題が混在する文書と未決定文書は元に残す。本文を切り分けない。
3. 本文リンクと`docs/`基準のsourceを追い、元以外の参照元も調べる。対象外レイヤーや外部Markdownを書き換えなければ成立しない場合は、文書群を元に残すか計画を見直す。read-only参照元の書換えを要求する計画は適用しない。
4. 全文書に配置結果を割り当て、依存Referenceも含む`split.json`を作る。保存先Policyの適合、共有Referenceのprovenance保持を確認したら`reference_policy_checked: true`を記載する。この値は権限昇格を許可しない。
5. `uv run <skill>/scripts/split_project.py <project-root> --plan <split.json>`で原本・指紋を保存し、原本を保持したまま候補を生成・検査する。設定・Policy・索引・ログ・未追跡文書も復旧対象になる。既存問題と追加問題を分け、移行可否を判断できない形式・参照エラーでは停止する。
6. 候補の配置結果を確認し、`uv run <skill>/scripts/split_project.py <project-root> --apply`で切り替える。指紋照合後、同一プロジェクトのKnowledge操作を停止するロックを取得する。元文書・参照・索引の更新、新規レイヤーの配置、管理ブロック更新を行い、設定を最後に公開する。
7. 全対象の設定解決、参照、索引からの到達性、権限、Policyと明示書込み選択が検査を通ると完了する。移動・残留理由・複製元・検査結果を報告し、各レイヤーのログにも記録する。

新規レイヤーのPolicyは元の方針・運用設定を引き継ぎ、指定用途を追記する。収集方針や権限を黙って緩めない。既存版と新規stateのschemaは維持する。通常のverify・publish・auditを自動実行しない。

## 入力例

`source`と`references`は元の`docs/`基準、`path`は移管先の`docs/`基準。残留文書にも一行を割り当て、残留パスを変えない。新規レイヤーだけを`layers`へ記載する。

```json
{
  "source_layer": "default",
  "layers": [
    {"id": "development", "name": "開発・運用", "description": "実装判断と運用手順を保存。製品仕様と未決定情報は既定へ残す"}
  ],
  "reference_policy_checked": true,
  "placements": [
    {"source": "features.md", "layer": "default", "path": "features.md", "reason": "製品仕様を維持", "references": ["references/decision.md"]},
    {"source": "operations.md", "layer": "development", "path": "operations.md", "reason": "運用手順", "references": ["references/decision.md"]},
    {"source": "references/decision.md", "layer": "default", "path": "references/decision.md", "reason": "共有根拠の原本", "references": []},
    {"source": "references/decision.md", "layer": "development", "path": "references/decision.md", "reason": "共有根拠を同じprovenanceで複製", "references": []}
  ]
}
```

## 移管規則

| 対象 | 扱い |
| --- | --- |
| Concept | 必ず一つの結果。claim・metadataを維持し、配置変更だけでverifiedを更新しない |
| 専用Reference | 参照する文書群と一緒に移す。外部参照元も確認する |
| 共有Reference / User Statement / Interaction | 元を残し、必要な各移管先へ同じ内容とprovenanceのコピーを配置。Policy不適合なら停止 |
| 本文リンク | Markdownファイル基準で最終パスへ相対化 |
| sources[].resource | docs/基準で再計算。project-artifactの実体と外部URIは維持 |
| Concept間リンク | 両レイヤー必須かつ既存resolver・validatorが扱える相対リンクだけ。optionalをまたぐ場合は文書群を元に残す |
| 索引 | 各階層を再生成して全管理ページへ接続 |
| 履歴 | 元ログ本文を維持し、両側へ移行結果を追記。本文中の参照は移管先へ合わせる |
| manifest / state | 既存テンプレートの版で新規生成。元stateも再構築し、キャッシュは複製しない |
| publish成果物 | 再生成しない。別操作として案内する |

同名衝突を自動連番で回避しない。同一内容・同一provenanceを共有する場合も、配置表を一つの衝突しない宛先へ整理してから再開する。
元の廃止は明示依頼時だけ`retire_source: true`と履歴移管先`history_layer`を指定し、全残留行を移管先へ変える。元をwrite_targetにしていた場合は新しいwrite_targetまたはnullも明示する。旧管理ディレクトリやpublish成果物の一括削除は行わない。

## 中断・復旧・再実行

候補は`.project-knowledge-operation/`へ保存する。適用前に入力や候補が変われば停止する。候補を再作成する場合は差分を確認して固定表を保持し、未適用記録を片付けた後に準備し直す。再分類しない。
切替エラーでは今回書いたファイルだけを復旧する。プロセスが停止してロックが残った場合は、実行中プロセスがないことを確認して`uv run <skill>/scripts/split_project.py <project-root> --recover`を使う。ロックだけを削除して続行しない。初期化の公開中断も同じ復旧入口を使える。
復旧時に別の編集が見つかれば、その編集を上書きせずロックを残して停止する。差分を利用者と確認してから復旧する。
設定ファイルの置換だけで複数ファイル全体が不可分になるわけではない。共通CLIは切替中の新しい操作を止めるが、既に実行中の操作やCLIを介さない編集は呼出し元が止める。
成功後は復旧用コピーを片付け、指紋と完了結果を残す。同じ操作の再実行は設定・ログ・管理ブロックを重複生成しない。
