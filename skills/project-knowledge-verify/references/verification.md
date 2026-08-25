# Verification

常にread-onlyで実行する。このSkillの`validate_knowledge.py`をread-onlyで実行し、OKF frontmatter、index/log、broken link、orphan、sources、消失source、staleを調べる。Git差分、config、capture、memoと現在の実装も読み取りだけで比較する。

AIによる意味検査では次を確認する。

- Knowledge Policyに反する情報や保存価値の低い情報が大量にないか
- 重要なナレッジが現在のソースと矛盾していないか
- capture、memo、source、config、schemaなどのprovenanceと主張が整合しているか
- provisional情報を確定情報として扱っていないか
- 廃止情報、欠損Reference、関連情報の分散がないか
- indexからの検索性、段階的な読み込み、ページ量、情報のまとまりが自然か

結果をHigh/Medium/Lowで分類し、修正は行わない。修正可能なら、対象を示して`project-knowledge`による更新を案内するだけにする。
