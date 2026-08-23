# update

新しい情報、現在のプロジェクト状態、既存ナレッジを確認し、将来利用価値のあるプロジェクトナレッジを追加・修正・整理する。ユーザー提示情報、会話、実装差分、ナレッジ収集方針の変更を同じ操作で扱う。

1. 今回利用可能な情報を確認する。実装反映では`detect_changes.py`をread-onlyで使い、前回commit以降、staged、working tree、untrackedを抽出する。Gitがなければhash snapshotとの差分を使う。
2. 今回の入力、変更ファイル、関連する既存ナレッジとReferenceだけからナレッジ候補を抽出する。毎回全体を再解析しない。
3. 情報源をuser assertion、conversation-derived、source-code、config、schema、external-reference、existing-knowledgeなどへ分類する。
4. [knowledge-policy.md](knowledge-policy.md)でナレッジ-worthyかを意味的に判定する。明示的な保存指示は強いシグナルとして優先する。
5. provenanceを残す価値がある場合だけ[provenance.md](provenance.md)に従ってcaptureまたはmemo Referenceを作る。既存Referenceやナレッジ本文を複製しない。
6. 関連ナレッジへ統合するか、新しいページ・カテゴリを必要最小限に作る。現在存在しない領域でも、Policyに合えば追加してよい。
7. capture、memo、実装、設定、既存ナレッジを主張単位で比較し、矛盾、信頼度、未解決事項を隠さない。
8. 関連indexと`log.md`を更新し、validator成功後だけ`state.yml`とsnapshotを進める。

収集方針の自然言語指示は`knowledge-policy.md`の更新として扱い、必要なら同じ会話や作業から該当ナレッジも抽出する。

Referenceを不要と判断しても既存ファイルを即削除せず、audit候補にする。通常の完了報告では内部分類を強調せず、更新したナレッジと方針だけを簡潔に示す。
