# Rebuildable state

`state.yml`はProject Knowledgeの正本ではなく、増分更新を効率化するための再構築可能な機械状態を保持する。Knowledge本文、index、log、manifest、Policyの内容をstateから推測して変更してはならない。

```yaml
state_schema_version: 2
git_baseline_commit: null
```

`state.yml`と`.cache/`はworking copy固有のローカル状態であり、通常はGitへcommitしない。削除、破損、非対応schemaを検出した場合は現在のproject状態から再構築する。復旧できないstateを理由にupdateを停止せず、可能ならフルスキャンへフォールバックする。

## Schema 2

- `state_schema_version`: integer `2`。state内部形式の版であり、Knowledge形式版、Skill版、OKF版とは独立する。
- `git_baseline_commit`: `null`またはGitが返す完全なcommit object ID。短縮object IDは保存しない。

`last_update_at`は差分検出に使わないため保持しない。更新履歴はKnowledgeのlogで扱い、具体的な機械用途が生じるまで鮮度fieldを追加しない。snapshot位置も固定値なのでstateへ保存しない。

## Git mode

`git_baseline_commit`は次回のcommit済み差分検出を開始するcommitである。利用前に、現在のrepositoryでcommitとして解決できることと、現在HEADの祖先であることを確認する。解決不能、短縮object ID、祖先でない値は無効とし、全tracked fileを対象とするフルスキャンへ移る。

差分候補は、有効なbaselineからHEADまでのcommit済み差分に、staged、working tree、untrackedを加えたものとする。baselineはcommit済み変更だけの処理位置である。未commit変更はcheckpointしないため、commitされるまで次回以降も候補として検出され得る。重複検出を許容し、未commit状態のsnapshotは持たない。

Knowledge本文、index、logの更新とvalidationがすべて成功した後だけ、現在HEADの完全object IDをbaselineへ保存する。失敗したupdateではbaselineを進めない。

## Non-Git mode

標準snapshot位置は次に固定する。

```text
<project-root>/project-knowledge/.cache/source-snapshot.json
```

現在のfile hashが前回値と異なる、または前回値がなければ`changed`、前回snapshotだけに存在すれば`removed`とする。snapshotがない、JSONとして壊れている、想定するstring-to-string mappingでない場合は空snapshotとしてフルスキャンする。

Knowledge更新とvalidationが成功した後だけ、`--write-snapshot`で標準位置へ現在hashを保存する。

## Recovery

対応schemaはそのまま使う。既知の旧schemaでも値を安全に引き継げない場合は初期状態へ再生成する。schema版の欠落、未知schema、競合するversion key、YAML破損、安全に判定できない内容は推測して修復しない。

stateの再生成はKnowledge本文を変更せず、履歴の保持だけを理由に失敗させない。

stateとsnapshotは、一時ファイルを同じdirectoryへ書き、完了後にreplaceする。再構築可能性を超えるtransaction機構は設けない。

## Validation boundary

静的validatorはstate欠落・破損をKnowledge Baseの重大破損と区別する。stateがあれば、`state_schema_version`が対応integerであること、`git_baseline_commit`が`null`またはstringであることを検査する。

commitの存在とancestryはrepositoryの現在状態に依存するため、静的validatorではなくbaselineを利用するupdate時に検査する。
