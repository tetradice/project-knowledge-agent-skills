# Verification

常にread-onlyで実行する。このSkillの`validate_knowledge.py`をread-onlyで実行し、manifest、形式版、OKF frontmatter、reserved index/log、分類、導出方法、actor、sources、broken link、orphan、消失source、status、staleをYAMLとして調べる。Git差分、config、User Statement、Interaction Recordと現在の実装も読み取りだけで比較する。

AIによる意味検査では次を確認する。

- Knowledge Policyに反する情報や保存価値の低い情報が大量にないか
- 重要なナレッジが現在のソースと矛盾していないか
- User Statement、Interaction Record、source、config、schemaなどのprovenanceとclaimが整合しているか
- provisional情報を確定情報として扱っていないか
- 廃止情報、欠損Reference、関連情報の分散がないか
- indexからの検索性、段階的な読み込み、ページ量、情報のまとまりが自然か

形式0.1は分類欠落をwarningとして読み続け、形式0.2または0.3で新規生成された不完全ConceptはHighとする。形式0.3では、Project Knowledge独自metadataに`pk_`がない場合もHighとする。未対応形式は推測せず停止する。

結果をHigh/Medium/Lowで分類し、修正は行わない。検証が成功しても`verified`を書き込まず、確認方法、actor、時刻を含むverification event候補を示す。ユーザーが反映を求めた場合だけ、`project-knowledge`によるupdateを案内する。
