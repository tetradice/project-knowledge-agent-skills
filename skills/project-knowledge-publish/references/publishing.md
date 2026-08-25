# Publishing

ナレッジをsource of truthのまま保持し、成果物は`published/`へ再生成する。公開物からナレッジへ逆同期しない。

永続的なpublish範囲は持たない。ユーザーが「開発環境構築だけ」などと指定した場合は、その実行だけの対象指定として扱う。

- Markdown: `docs/`を人間向けに再構成し、`published/markdown/`へ出力する。User StatementやInteraction RecordなどのRaw Referenceを無条件に公開しない。
- HTML: rendererが`material-mkdocs`なら、このSkillの`scripts/build_offline_docs.py`を`uv run`で実行し、Markdown成果物から`published/html/index.html`を生成する。スクリプトは`file://`ナビゲーション、ローカル検索、CDN非依存、broken linkを検証する。

実行例は `uv run <skill>/scripts/build_offline_docs.py project-knowledge/published/markdown project-knowledge/published/html`。既存の非空出力先を置換する場合は事前承認を得てから`--force`を付ける。renderer固有の処理をナレッジ生成へ混ぜない。別rendererが設定されていて利用手段がなければ、勝手にfallbackせず報告する。

ビルド後は出力された`index.html`、ページ数、画像数、警告数、broken link数を報告する。

形式0.1と0.2をread-onlyで扱う。0.2では通常Conceptの`category`、`derivation`、`verified`から導出したtrust tier、`status`、`stale`を必要に応じて人間向けに表現する。Raw ReferenceはKnowledge分類の対象外とする。未対応形式では生成せず、対応Skillの更新が必要と報告する。
