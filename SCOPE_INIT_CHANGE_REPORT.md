# プロジェクトナレッジ scope / init 仕様変更報告

> [!IMPORTANT]
> この文書は旧scope設計の履歴です。現行仕様は`README.md`と`skills/project-knowledge/`を参照してください。scopeは廃止され、ナレッジ Policyへ移行しました。

## 1. 変更したファイル

- `README.md`
- `project-knowledge/scope.md`（`scope.yml`から移行）
- `project-knowledge/docs/skill/index.md`
- `project-knowledge/docs/log.md`
- `skills/project-knowledge/SKILL.md`
- `skills/project-knowledge/references/init.md`
- `skills/project-knowledge/references/scope.md`
- `skills/project-knowledge/references/architecture.md`
- `skills/project-knowledge/references/update.md`
- `skills/project-knowledge/references/verification.md`
- `skills/project-knowledge/references/audit.md`
- `skills/project-knowledge/scripts/init_project.py`
- `skills/project-knowledge/scripts/validate_knowledge.py`
- `skills/project-knowledge/templates/scope.md`（`scope.yml`を置換）
- `skills/project-knowledge/tests/test_project_knowledge.py`

## 2. scope.ymlからscope.mdへの変更

scopeをYAML配列ではなく、`version`、`status`、`expansion`だけをfrontmatterに持つMarkdown管理文書へ変更した。本文には対象、対象外、境界条件、粒度、重視事項を自然言語で記録できる。

このリポジトリ自身の`project-knowledge/scope.yml`も、内容を保った`scope.md`へ移行した。

## 3. initのscope必須ルール

通常initは、ユーザーが明示したscopeを必須とする。Agentはscope未指定時にREADMEやソースコードから対象を推測せず、対象範囲が指定されていないことを伝えて停止する。

決定的スクリプトでも`--scope`または`--empty`を必須の排他的引数にした。複数scope項目は`--scope`を複数回指定できる。

## 4. empty init

`--empty`、または「空の状態」「スコープなし」など同じ意図を明示した自然言語だけをempty initとして扱う。`scope.md`は`status: undefined`となり、固定のindex、log、referencesの骨組みだけを作る。ソース調査やナレッジ本文生成は行わない。

## 5. scopeとInformation Architectureの分離

`project-knowledge/scope.md`を「何をナレッジに含めるか」というナレッジ Boundary、`project-knowledge/docs/`を「どう整理するか」というInformation Architectureとして定義した。scopeはOKF ナレッジ Bundleの外に置く管理情報だが、init、update、verify、audit時には必ず参照する。

scope項目と文書・ディレクトリの1対1対応は要求しない。

## 6. docs構成の自動設計ルール

固定構造は`docs/index.md`、`docs/log.md`、`docs/references/captures/`、`docs/references/memos/`に限定した。その他のページとカテゴリは、プロジェクトの性質・規模、情報の関係、探索経路、Progressive Disclosure、ページ量、重複、既存ナレッジとの一貫性、将来の拡張性からAgentが判断する。

scope変更時は既存構成への統合を優先し、変更コストに見合わない大規模再編を避ける。

## 7. 既存データのmigration

旧`scope.yml`の既知schemaである`include`、`exclude`、`topics[].id`、`topics[].description`を`scope.md`へ変換する。変換成功後に旧ファイルを削除するため、scopeのsource of truthは1つになる。

未知のversion、キー、構造を検出した場合は、意味を推測せず旧ファイルを保持して初期化を停止する。旧scopeが空で、通常initに明示scopeが渡された場合は、そのscopeをactiveな`scope.md`へ反映する。

## 8. verify / auditへの影響

validatorは`scope.md`の存在と最小frontmatterを構造検証し、旧`scope.yml`が残っていれば報告する。

verifyはscope超過、scope内の重要情報欠落、scope外ナレッジの残存と、Information Architectureの検索性・段階的読み込みを別々に評価する。auditは機械的なページ分割、巨大ページ、不自然な階層、関連情報の分断、indexの探しにくさ、再編候補を監査する。初回read-onlyと、scope縮小時に即削除しない方針は維持した。

## 9. 実施したテスト

- `uvx pytest -q`: 11件成功
- `python -m py_compile ...`: 成功
- `git diff --check`: 成功
- `validate_knowledge.py project-knowledge`: `No structural findings`
- Skill Creatorの`quick_validate.py`: `Skill is valid!`

単体テストは通常init、scope未指定拒否、empty init、旧scope移行、未知schema保持、空の旧scopeへの明示scope反映、scope項目からのディレクトリ非生成、冪等性、validatorのread-only性などを確認した。自然言語empty initとscope addはAgentが意味を解釈する操作であるため、決定的スクリプトへ文字列判定を実装せず、Skill referenceの指示として確認した。

## 10. 互換性上の懸念

- 独自拡張された旧`scope.yml`は自動変換せず、手動の意味的移行が必要になる。
- `init_project.py`を直接呼んでいた既存自動処理は、`--scope`または`--empty`の追加が必要になる。
- scope適合性、自然言語によるscope編集、Information Architectureの妥当性は意味理解が必要であり、validatorだけでは完結しない。
- 旧実装報告captureは一次資料として保持しているため、内部に当時の`scope.yml`記述が残る。現在仕様のsource of truthには使用しない。
