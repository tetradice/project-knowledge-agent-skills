---
name: project-knowledge-publish-html
description: project-knowledge/ のAI向けナレッジを、project-knowledge-publishの規則に従って人間向けに再構成し、Blumeで静的HTMLサイトとして出力する。「HTML形式で出力してください」と明示された場合、または `$project-knowledge-publish-html` を手動で呼び出した場合のみ使用する。通常の公開・出力依頼では使用しない。
---

# 目的

`project-knowledge-publish` が生成する人間向け文書をMarkdown原稿として保持し、Blumeで閲覧用の静的HTMLサイトへ変換する。

元の `project-knowledge/` は変更しない。

# 実行条件

現在の依頼が次のいずれかを満たす場合だけ処理する。

- 「HTML形式で出力してください」と明示されている
- `$project-knowledge-publish-html` が手動で呼び出されている

単に「公開して」「出力して」「人間向けにまとめて」と依頼されただけの場合は、このスキルを使用しない。

# 前提確認

出力ファイルを作る前に、次の順序で確認する。

1. 利用可能なスキルまたは同じスキルルートから、名前が完全に `project-knowledge-publish` と一致するスキルを探す。
2. 対応する `SKILL.md` を最後まで読めることを確認する。存在しない、または読めない場合は、代替処理を行わず中断する。
3. `node --version` を実行し、Node.js 22.12.0以上であることを確認する。コマンドが使えない、またはバージョンが古い場合は中断する。
4. `npm --version` を実行し、Blumeを導入・実行できることを確認する。使用できない場合は中断する。

中断時は不足している前提を明示する。前提を満たすまで `project-knowledge/` を読まず、出力フォルダも作らない。

# 文書の生成

読み込んだ `project-knowledge-publish` の規則を、対象範囲、読み込み、再構成、情報の扱い、詳細度、セキュリティの正本として適用する。

特に次を守る。

- `project-knowledge/index.md` を入口にし、必要なリンク先だけ読む
- コード、設定、外部環境を再調査しない
- `pending.md` は要求された場合を除いて含めない
- 元ナレッジにない事実を追加しない
- 秘密情報を出力しない
- `docs/index.md` と、1つ以上の個別Markdownファイルを作る
- `docs/index.md` から全個別ファイルへ相対リンクで辿れるようにする

Markdownファイルを `docs/` に配置した後、Markdown文書を指すローカルリンクのURLをBlumeで処理可能なルートURLへ置き換える。リンク文字列、クエリ、フラグメントは維持し、リンク先のパス部分の末尾にある `.md` または `.mdx` を `/` に変換する。外部URL、画像、文書以外のローカルファイルは変更しない。

```markdown
[System](system.md) -> [System](system/)
[API](guides/api.md#認証) -> [API](guides/api/#認証)
```

HTML用の出力構成だけは、元スキルの出力先を次の `docs/` に読み替える。別のMarkdown公開フォルダを追加で作らない。

# 出力先

出力ごとに新しいフォルダを作る。

出力先の指定がない場合は、リポジトリルートに `project-knowledge-published-html-YYYYMMDD-HHmmss/` を作る。日時には実行環境のローカル時刻を使用する。

ユーザー指定の出力先がすでに存在する場合は上書きしない。末尾に `-YYYYMMDD-HHmmss` を付けた別フォルダを作る。

完成時の構成は次のとおりとする。

```text
project-knowledge-published-html-YYYYMMDD-HHmmss/
├── docs/
│   ├── index.md
│   └── <topic>.md
├── dist/
│   ├── index.html
│   └── ...
├── blume.config.ts
├── package.json
└── package-lock.json
```

`node_modules/` と `.blume/` は完成物に含めない。

# Blumeサイトの構築

1. このスキルの `references/template/` の内容を、隠しファイルを含めて出力フォルダのルートへすべてコピーする。`npx blume init` は使用せず、必ずこのテンプレートBlumeプロジェクトを構築のベースにする。
2. テンプレートの構成と設定を引き継ぎ、サンプル文書を生成した `docs/index.md` と個別Markdownファイルに置き換える。
3. `blume.config.ts` を更新し、`content.root` を `docs` に設定する。サイトタイトルと説明には、`docs/index.md` の文書タイトルと対象範囲を使用する。
4. Markdown文書を指すローカルリンクのURLを、前述の規則に従ってBlumeで処理可能なルートURLへ置き換える。
5. 出力フォルダで `npm install --save-exact blume@latest` を実行する。実際に解決したバージョンを `package.json` と `package-lock.json` に残す。
6. `npm run build` を実行する。既定のstrict動作を維持し、`--no-strict` は使用しない。
7. `npm exec blume validate` を実行し、内部リンクとアセットを検証する。
8. `dist/index.html` が存在し、`docs/index.md` からリンクした各ページに対応するHTMLが `dist/` へ生成されていることを確認する。
9. 検証成功後、今回作成した出力フォルダ直下の `node_modules/` と `.blume/` だけを削除する。削除前に対象が今回の出力フォルダ内であることを確認する。

npmパッケージの取得、Blumeのビルド、リンク検証のいずれかが失敗した場合は処理を中断する。失敗した工程、エラーの要点、残っている出力フォルダを示し、HTML出力が完了したとは報告しない。

# 完了確認

完了前に次を確認する。

- `project-knowledge-publish` の全規則に反していない
- 指定テーマから逸脱していない
- 元ナレッジにない事実や秘密情報を含まない
- `docs/index.md` から全個別Markdownファイルへ辿れる
- Markdown文書を指すローカルリンクがBlumeで処理可能なルートURLへ置き換えられている
- Blumeのビルドとリンク検証が成功している
- `dist/index.html` と各個別ページのHTMLが存在する
- 完成物に `node_modules/` と `.blume/` が残っていない

完了後の応答では、作成した出力フォルダ、`dist/index.html`、`docs/index.md` のパスを示す。文書本文は応答へ重複して掲載しない。
