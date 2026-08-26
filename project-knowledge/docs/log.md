# ナレッジ log

## 2026-08-26

### verifyの内容健全性検証を具体化

- verifyをStructure、Sources、Provenance、Evidence、Current State、Freshness、Consistencyの順で実行する契約へ具体化した。
- `pass`、`fail`、`warning`、`not-verifiable`、`stale`、`not-applicable`をreporting上の結果分類として定義した。
- 内容上の矛盾と構造上の重複、既存Knowledgeの検証と未登録Knowledgeのcoverage調査の境界を明文化した。

### verifyをメインスキルへ統合

- `project-knowledge-verify`を廃止し、read-onlyの正確性検証を`project-knowledge`の`verify`へ統合した。
- Skill群を、保守、限定回答、公開、構造監査の4責務へ整理した。
- `verify`と`update`の非自動連鎖、および`verify`と`audit`の責務境界を明文化した。

### 形式1.0専用へ簡略化

- 全Skillを2.0.0へ更新し、Project Knowledge形式1.0だけを扱う契約へ統一した。
- 旧形式の仕様、変換処理、互換分岐、テスト、Referenceを削除した。
- OKF v0.2の現行規約を形式1.0の仕様へ統合した。

### 追加の簡略化

- `project-knowledge-fast-ask`と`project-knowledge-audit`の手順を各`SKILL.md`へ統合し、専用Referenceを削除した。
- 形式判定の中継Reference、`config.local.yml`、未実装のrenderer/offline設定を削除した。
- `init --empty`、差分検出のbaseline/snapshot上書き、旧`--write-state` aliasを廃止し、固定された実装経路へ統一した。
