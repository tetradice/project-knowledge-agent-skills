# init

## 既存ナレッジの確認

1. 現在のプロジェクトのルートを特定する。
2. ルートの `project-knowledge/index.md` が存在するか確認する。
3. 存在する場合は、`プロジェクトナレッジがすでに存在しています。` と回答して直ちに中断する。
4. `index.md` が存在しない場合は、`project-knowledge/references/` の有無を確認する。

`project-knowledge/references/` だけが既に存在していても、`index.md` がなければ初期構築を続ける。
既存の trusted raw sources は削除、上書き、整形せず、初期構築の情報源として利用する。

この確認より前に、他の reference やテンプレートを読まない。ファイル、Git の状態、外部環境も変更しない。

## 前提の確認

既存ナレッジがない場合だけ、次のファイルを最後まで読む。

1. [../format.md](../format.md)
2. [../metadata.md](../metadata.md)
3. [../evidence.md](../evidence.md)
4. [../template_AGENTS.md](../template_AGENTS.md)

必要なファイルが存在しない、または読めない場合は、代替処理を行わず中断する。

`evidence.md` に従って Git 状態を確認し、完全長の `HEAD` を取得する。Git 管理外や初回コミット前など、前提を満たさない場合は、ファイルを変更せず中断する。作業ツリーが dirty の場合は処理を続け、完了時にその事実を報告する。

## ナレッジの初期構築

現在のソースコード、設定、Git、必要な外部環境、関連する trusted raw sources からナレッジを構築する。

- `project-knowledge/index.md` が存在しない状態を初期状態として扱う。
- `format.md`、`metadata.md`、`evidence.md` の規則を適用する。
- `project-knowledge/references/` が存在する場合は、ファイル名、ユーザー依頼、構築対象コンセプトから関連資料を絞り込む。全資料を無条件に全文ロードしない。
- authority の対象を区別し、現在の安定した実装や環境状態と、信頼済みの要件、制約、設計判断を必要に応じて記録する。
- 要件と現在実装が異なる場合は、一方へ合わせず両方と不一致の状態を記録する。
- `project-knowledge/index.md` と `project-knowledge/pending.md` を必ず作成する。
- システムの理解に必要なコンセプトファイルだけを追加する。
- 推測、一時状態、作業履歴、秘密情報を記録しない。
- 作成する各コンセプトへ、実際に参照した情報源、実行 actor、現在の UTC 日時、調査開始時の完全長 SHA を記録する。
- 参照した trusted raw source は既存の `sources` へ記録し、資料自体は変更しない。
- コンセプト全体を情報源と照合できた場合だけ `verified` を記録する。

構築または完了確認に失敗した場合は中断し、`AGENTS.md` には触れない。

## AGENTS.md への追記

ナレッジの構築と検証に成功した後だけ、`../template_AGENTS.md` の内容をルートの `AGENTS.md` へ反映する。

- `AGENTS.md` が存在しない場合は、テンプレートと同じ内容で新規作成する。
- `AGENTS.md` が存在する場合は、既存の全バイトを保持し、末尾に必要最小限の改行とテンプレートだけを追記する。
- 既存箇所を編集、削除、置換、並べ替え、整形しない。
- 改行コードを変換しない。
- ファイル全体を書き直さない。

## 完了確認

- `project-knowledge/index.md` と `project-knowledge/pending.md` が存在する。
- 作成したナレッジが、読み込んだ共通 reference の規則に従う。
- 既存の `project-knowledge/references/` と配下の全ファイルが変更されていない。
- `AGENTS.md` がなかった場合は、内容が `../template_AGENTS.md` と一致する。
- 既存の `AGENTS.md` があった場合は、実行前の内容をすべて保持し、テンプレートを末尾にだけ追加している。

完了後は、作成したナレッジファイルを報告する。`AGENTS.md` については、新規作成と追記のどちらだったかを示す。調査開始時の作業ツリーが dirty だった場合は、その事実も報告する。
