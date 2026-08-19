# init

## 既存ナレッジ

プロジェクトルートの `project-knowledge/index.md` を確認する。
存在する場合は既存ナレッジとして扱い、変更せず `update` の利用を案内する。

`index.md` がなく `project-knowledge/references/` だけが存在する場合は、資料を保持して初期構築を続ける。
この確認より前にファイルや外部環境を変更しない。

## 前提

共通 reference を読めない場合は、変更せず中断する。
`evidence.md` に従って Git 状態と調査範囲を確認する。

## 構築

現在のコード、設定、関連する trusted raw sources、必要な外部環境から、システムの理解に必要なコンセプトだけを作成する。
`format.md`、`metadata.md`、`evidence.md` を適用する。

中断後に再実行できるよう、次の順序で処理する。

1. 作成内容を確定し、書き込む前に共通 reference との整合性を確認する。
2. `pending.md` とコンセプトファイルを作成する。
3. 最後に、作成済みファイルだけを指す `index.md` を作成する。

`index.md` を作成する前に失敗した場合は、作成済みファイルを報告する。
再実行時はそれらを入力として利用し、内容を無条件に上書きしない。

## 完了確認

- `index.md` と `pending.md` が存在する。
- `index.md` のリンク先が存在する。
- 作成したナレッジが共通 reference に従う。
- `project-knowledge/references/` を変更していない。

作成したファイル、取得できなかった情報源、Git 履歴を利用できなかった理由、調査開始時の dirty 状態を必要に応じて報告する。
