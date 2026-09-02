# update

新しい情報、変更された仕様、現在のプロジェクト状態、ユーザーから与えられたKnowledgeを確認し、将来利用価値のあるプロジェクトナレッジへ反映する。ユーザー提示情報、会話、実装差分、ナレッジ収集方針の変更を同じ操作で扱う。既存Knowledgeを検査して客観的な問題を正す作業は`fix`、Knowledge Baseの構造改善は`project-knowledge-audit`の`refactor`へ委ねる。

1. [Format 1.0](data-formats/1.0.md)に従って形式1.0であることを確認し、それ以外へは書き込まない。
2. 今回利用可能な情報を確認する。実装反映では`detect_changes.py`をread-onlyで使う。Gitでは有効な`git_baseline_commit`からHEADまでと、staged、working tree、untrackedを抽出する。baselineが無効なら全tracked fileへフォールバックする。Gitがなければ固定位置のhash snapshotとの差分を使う。
3. 今回の入力、変更ファイル、関連する既存ナレッジとReferenceだけからナレッジ候補を抽出する。毎回全体を再解析しない。
4. [data-model.md](data-model.md)に従って通常Conceptの`pk_category`と`pk_derivation`、sourceの`pk_source_type`を判定する。選択をユーザーへ委ねない。
5. [knowledge-policy.md](knowledge-policy.md)でナレッジ-worthyかを意味的に判定する。明示的な保存指示は強いシグナルとして優先する。
6. provenanceを残す価値がある場合だけ[provenance.md](provenance.md)に従ってUser StatementまたはInteraction Recordを作る。User Statementを追加・更新した場合は、その内容を関連するConceptなど他のナレッジにも必ず反映し、当該User Statementをsourceとして残す。既存Referenceやナレッジ本文を複製しない。
7. 会話・共有対話をInteraction Recordへ要約するときは、結論だけに圧縮しない。問題の発生から解決または中断までの時系列を保ち、少なくとも判断・制約、実施した調査または操作、観測された結果・エラー、採用または却下した対応、検証結果、未解決または未検証の境界を、元の情報に存在する範囲で記録する。各項目を無理に埋めず、存在しない情報を補わない。全文保存が明示された場合は、要約の代替にせずRaw Referenceとして原文を保存する。
8. 関連ナレッジへ統合するか、新しいページ・カテゴリを必要最小限に作る。現在存在しない領域でも、Policyに合えば追加してよい。
9. root・nested `index.md`はナビゲーション専用とし、タイトル、短い案内、リンク、リンク先を選ぶための短い説明だけを置く。独立して再利用できる事実、判断、制約、状態、検証結果は通常Conceptへ保存し、`type`、`pk_category`、`pk_derivation`、`sources`を付ける。
10. indexを更新するときは、追加する文章が単独の知識として成立しないか確認する。成立する場合は通常Conceptへ分離し、indexからリンクする。
11. source、実装、設定、既存ナレッジをclaim単位で比較し、矛盾、検証状態、未解決事項を隠さない。
12. 関連indexと`log.md`を更新してvalidatorを実行する。成功後だけ、Gitでは`detect_changes.py <project-root> --write-baseline`、非Gitでは`--write-snapshot`を実行する。失敗時はbaselineとsnapshotを進めない。未commit変更はcheckpointせず、commitされるまで再検出を許容する。詳細は[state.md](state.md)を参照する。

収集方針の自然言語指示は`knowledge-policy.md`の更新として扱う。プロジェクト固有の方針を標準Policyより優先し、本文には固有方針、標準Policyを適用するフォールバック宣言、Skill同梱の`references/standard-knowledge-policy.md`への参照情報をこの順で置く。必要なら同じ会話や作業から該当ナレッジも抽出する。

verify結果を反映するときは、確認方法とactorを確認して`verified`を保存する。`generated`は現在内容の生成者として独立して維持する。

Referenceを不要と判断しても既存ファイルを即削除せず、audit候補にする。

更新完了後は[File change classification](file-change-classification.md)に従い、追加・更新したファイルを分類して完了報告へ件数を出力する。件数とは別に、更新したナレッジと方針を簡潔に示す。
