# update

新しい情報、現在のプロジェクト状態、既存ナレッジを確認し、将来利用価値のあるプロジェクトナレッジを追加・修正・整理する。ユーザー提示情報、会話、実装差分、ナレッジ収集方針の変更を同じ操作で扱う。

1. [Format 1.0](data-formats/1.0.md)に従って形式1.0であることを確認し、それ以外へは書き込まない。
2. 今回利用可能な情報を確認する。実装反映では`detect_changes.py`をread-onlyで使う。Gitでは有効な`git_baseline_commit`からHEADまでと、staged、working tree、untrackedを抽出する。baselineが無効なら全tracked fileへフォールバックする。Gitがなければ固定位置のhash snapshotとの差分を使う。
3. 今回の入力、変更ファイル、関連する既存ナレッジとReferenceだけからナレッジ候補を抽出する。毎回全体を再解析しない。
4. [data-model.md](data-model.md)に従って通常Conceptの`pk_category`と`pk_derivation`、sourceの`pk_source_type`を判定する。選択をユーザーへ委ねない。
5. [knowledge-policy.md](knowledge-policy.md)でナレッジ-worthyかを意味的に判定する。明示的な保存指示は強いシグナルとして優先する。
6. provenanceを残す価値がある場合だけ[provenance.md](provenance.md)に従ってUser StatementまたはInteraction Recordを作る。既存Referenceやナレッジ本文を複製しない。
7. 関連ナレッジへ統合するか、新しいページ・カテゴリを必要最小限に作る。現在存在しない領域でも、Policyに合えば追加してよい。
8. root・nested `index.md`はナビゲーション専用とし、タイトル、短い案内、リンク、リンク先を選ぶための短い説明だけを置く。独立して再利用できる事実、判断、制約、状態、検証結果は通常Conceptへ保存し、`type`、`pk_category`、`pk_derivation`、`sources`を付ける。
9. indexを更新するときは、追加する文章が単独の知識として成立しないか確認する。成立する場合は通常Conceptへ分離し、indexからリンクする。
10. source、実装、設定、既存ナレッジをclaim単位で比較し、矛盾、検証状態、未解決事項を隠さない。
11. 関連indexと`log.md`を更新してvalidatorを実行する。成功後だけ、Gitでは`detect_changes.py <project-root> --write-baseline`、非Gitでは`--write-snapshot`を実行する。失敗時はbaselineとsnapshotを進めない。未commit変更はcheckpointせず、commitされるまで再検出を許容する。詳細は[state.md](state.md)を参照する。

収集方針の自然言語指示は`knowledge-policy.md`の更新として扱い、必要なら同じ会話や作業から該当ナレッジも抽出する。

verify結果を反映するときは、確認方法とactorを確認して`verified`を保存する。`generated`は現在内容の生成者として独立して維持する。

Referenceを不要と判断しても既存ファイルを即削除せず、audit候補にする。通常の完了報告では内部分類を強調せず、更新したナレッジと方針だけを簡潔に示す。
