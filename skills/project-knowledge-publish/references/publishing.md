# Publishing

ナレッジをsource of truthのまま保持し、成果物は`published/`へ再生成する。公開物からナレッジへ逆同期しない。

既定ではMarkdownとoffline HTMLの両方を生成する。ユーザーが出力形式または対象範囲を指定した場合は、その実行だけに適用し、Knowledge Baseへ永続化しない。

- Markdown: `docs/`を人間向けに再構成し、`published/markdown/`へ出力する。User StatementやInteraction RecordなどのRaw Referenceを無条件に公開しない。
- HTML: このSkillの`scripts/build_offline_docs.py`を`uv run`で実行し、Markdown成果物からMaterial for MkDocsによる`published/html/index.html`を生成する。スクリプトは`file://`ナビゲーション、ローカル検索、CDN非依存、broken linkを検証する。

実行例は `uv run <skill>/scripts/build_offline_docs.py project-knowledge/published/markdown project-knowledge/published/html`。既存の非空出力先を置換する場合は事前承認を得てから`--force`を付ける。HTML生成処理をナレッジ生成へ混ぜない。

ビルド後は出力された`index.html`、ページ数、画像数、警告数、broken link数を報告する。

形式1.0だけをread-onlyで扱う。通常Conceptの分類、verified、status、staleを必要に応じて人間向けに表現し、Raw ReferenceはKnowledge分類の対象外とする。形式が異なる場合は生成せず、対応Skillの更新が必要と報告する。
