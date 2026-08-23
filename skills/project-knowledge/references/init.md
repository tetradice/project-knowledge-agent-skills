# init

通常の`init`はscope指定なしで実行できる。`python <skill>/scripts/init_project.py <project-root>`を実行し、ナレッジ Bundleの骨組み、`knowledge-policy.md`、config、state、Reference、AGENTS.mdルーティングを生成する。

`--empty`または「空で初期化」の明示があれば、管理ファイルと最低限の`docs/`構造だけを作り、プロジェクト調査やナレッジ本文生成を行わない。

## 通常の流れ

1. 初期構造を生成し、旧scopeと旧learning設定のmigration結果を確認する。
2. ユーザーが初期ナレッジの内容を指定した場合だけ、その範囲を優先してプロジェクトを調査する。これは将来の対象を限定する境界ではない。
3. [knowledge-policy.md](knowledge-policy.md)で保存価値を判定する。
4. [architecture.md](architecture.md)に従ってInformation Architectureを設計し、`docs/index.md`から全ページへ到達可能にする。
5. `validate_knowledge.py`を実行し、結果を報告する。

既存の`scope.md`または`scope.yml`がある場合、既知形式の対象指定はPolicy上の「積極的な保存候補」、対象外・粒度・補足条件は保存しない方針や補足へ移す。対象指定をallow-listとしては残さない。意味を安全に変換できない場合は旧ファイルを保持して停止するため、内容を報告してから意味的に移行する。

旧`update.automatic_after_work`は`false`なら`learning.mode: manual`、`true`なら`learning.mode: opportunistic`へ変換する。既存の未知の設定は保持する。

再実行は冪等でなければならない。既存の`AGENTS.md`と`.gitignore`は保持し、同じ管理ブロックを重複させない。
