# ルート設定の解決

Project Knowledge操作は、プロジェクト直下の`project-knowledge.yaml`を入口にする。
設定がなければ対象外であり、ナレッジディレクトリやmanifestだけを見つけて利用しない。
一般的なSkillの利用案内は設定なしでも説明できるが、プロジェクトのKnowledgeにはアクセスしない。

## 実行手順

明示されたプロジェクトルートでは`uv run <project-knowledge-skill>/scripts/project_config.py --project-root <project-root>`を実行する。
ルートが不明な場合は`--start <cwd> --workspace-root <workspace-root>`で探索する。
Git管理下では最寄りのGit作業ツリールートを越えず、Git管理外でworkspaceが不明なら現在ディレクトリだけを調べる。
最寄りの設定だけを使い、親子の設定をマージしない。
明示ルートで設定が欠けている場合や、見つけた設定が不正な場合は親へフォールバックしない。

JSON結果の`project_root`と各レイヤーの`resolved_path`を以後の基準にする。
手順や実行例中の`project-knowledge/`は既定配置の例であり、実際には解決済みのレイヤーパスへ置き換える。
書き込み前には`--write`を付け、対象を明示する場合は`--layer <id>`も指定する。
結果の`description`を、関連性、適用範囲、記録先候補の判断に使う。
`name`はAIと利用者が使う必須の呼称であり、自然言語での明確な対象指定にも使う。`id`はCLI、根拠、stateで使う不変の機械識別子である。
説明はPolicyやアクセス指定を上書きしない。

## 設定仕様

新規initが生成する設定は次のとおり。

```yaml
# この設定ファイルは project-knowledge skill で生成されました。
version: "1.0"
layers:
  - id: default
    name: プロジェクトナレッジ
    path: ./project-knowledge
```

| キー | 条件と省略時の動作 |
| --- | --- |
| `version` | 必須の文字列`"1.0"`。ユーザーの指示なしに版を上げない |
| `layers` | 必須の配列。0件以上を登録できる |
| `layers[].id` | 必須。`[a-z][a-z0-9_-]*` |
| `layers[].name` | 必須。空白以外を含む利用者向け呼称。レイヤー間で一意。初期化時の`id: default`は`プロジェクトナレッジ` |
| `layers[].path` | 必須。設定所在地からのプロジェクト内相対パス。管理ディレクトリを指す |
| `layers[].description` | `default`以外は空白だけでない文字列を必須とする。`default`は省略可。複数行可。nullは禁止 |
| `layers[].access` | `read-only`または`read-write`。省略時は`read-write` |
| `layers[].optional` | boolean。省略時は`false`。ディレクトリの欠落だけを許容する |
| `layers[].auto_select` | boolean。省略時は`true`。`false`なら曖昧なAI自動選択の候補から除外 |
| `write_target` | 登録された書き込み可能なIDかnull。省略時は1件の`read-write`レイヤーのID、それ以外はnull |

空ファイル、未知キー、重複キー、型不一致、未対応版、複数YAML文書、独自タグ、アンカー、エイリアス、merge keyを拒否する。
相対パスの区切りは`/`とし、絶対パス、URL、環境変数、`~`、globを受け付けない。
実体パスはプロジェクト直下より下に限定し、プロジェクトルート自身やシンボリックリンク経由の範囲外参照を拒否する。
設定ファイル自体のシンボリックリンクも拒否する。
`layers: []`は登録済みだが対象ゼロである。親設定の利用を止める場合も`version: "1.0"`とともに指定する。

`optional: true`で欠落したレイヤーは`available: false`として結果に残し、利用者へ省略したIDを示す。
参照先が存在する場合、manifestの破損やアクセスエラーは無視しない。
対象がない、書き込み先が未指定、読み取り専用、指定先が欠落している場合は書き込まず、他のレイヤーに切り替えない。
nullの書き込み先は、明示した書き込み可能レイヤーの使用まで禁止するものではない。
`write_target`には`auto_select: false`のレイヤーを指定できない。複数レイヤーの参照操作は全件を対象にし、書込み操作は明示指定、明確な`name`または`id`指定、AIの一意な候補判定、`write_target`の順で1件を選ぶ。

## 操作と設定の境界

新規initだけは未登録プロジェクトへ初期内容を生成してよい。
通常の新規initでは`init_project.py <project-root> --prepare`で骨組みを準備し、本文を生成した後、`init_project.py <project-root>`で設定登録を完了する。
複数レイヤーの新規initは[init](init.md)の`--layers`で確定定義を渡し、全件検査後に設定を公開する。既存1レイヤーからの[split](split.md)だけは、元と新規移管先の固定集合を一操作で変更する。通常更新の対象1件という規則は維持する。
切替中は`.project-knowledge.lock`により共通設定解決を停止する。復旧手順はsplitのReferenceに従い、ロックだけを削除しない。
空での初期化は`--prepare`を使わず1回で完了できる。
登録完了後は生成設定の書き込み可能指定を守る。読み取り専用で運用したい場合は、明示的に`access: read-only`を指定する。
既存の読み取り専用レイヤーへのinit再実行は、初期化済みなら変更なしで終了し、修復が必要なら停止する。

Policyの運用設定は各レイヤーの`knowledge-policy.md`に残す。
読み取り専用レイヤーでは本文だけでなく、Policy、ログ、state、キャッシュ、公開成果物も変更しない。
差分検出は既存stateを読み、不正ならメモリ内でフルスキャンに戻せるが、保存は`read-write`の場合だけ許す。
ルート設定の表示や、明示依頼による`access`などの編集はレイヤー内の書き込みとは別操作である。
ルート設定の編集では既存コメントと無関係な値を保持し、更新後に共通CLIで確認する。`version`を補完、昇格、修復しない。

PolicyのCLIは`policy_settings.py <knowledge-root>/knowledge-policy.md --project-root <project-root>`、検査は`validate_knowledge.py <knowledge-root> --project-root <project-root>`を使う。
いずれも`--layer <id>`で対象を明示でき、渡したファイルやディレクトリと登録先の一致を確認する。
検査CLIではmanifestの破損はfindingとして扱う。低水準の検査関数やPolicy編集関数は単体利用できるが、Skillは登録確認を省略しない。
