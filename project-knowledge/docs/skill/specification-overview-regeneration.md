---
type: Project Knowledge Guide
pk_category: declared
pk_derivation: synthesized
status: stable
generated:
  by: project-knowledge/3.0.0
  at: 2026-08-26T16:55:24+09:00
sources:
  - resource: ../../../project-knowledge-spec-overview.md
    pk_source_type: project-artifact
---

# 仕様相談用テキストの再生成

Project Knowledgeスキル群の仕様や構成が変わったときは、`project-knowledge-spec-overview.md`を現行仕様から再作成する。
この文書は、リポジトリを知らないChatGPTなど外部チャットの相談相手へ渡す、単独で読めるMarkdown文書とする。

## 再生成を求める指示

次のような自然言語の依頼を、記録済みの方針による再生成intentとして扱う。

- 「Project Knowledgeスキル群の仕様相談用テキストを、記録済みの方針で再作成してください」
- 「`project-knowledge-spec-overview.md`を現行仕様に合わせて再作成してください」

決まったコマンド名や完全一致する文言は要求しない。

## 情報源

再生成時は、各Skillの`SKILL.md`と必要なReference、README、設定、実装を読み直す。
Project Knowledge内の関連Conceptも確認するが、現行実装と矛盾する場合は矛盾を解消してから記述する。

既存の`project-knowledge-spec-overview.md`は構成と文体の参考にする。
古い記述をそのまま正しいものとして扱わず、現行の情報源から内容を組み立て直す。

## 文書の構成

文書は細部を網羅する仕様書ではなく、外部の相手と仕様相談ができる粒度にする。
概要と設計上の考え方を中心に、次の内容を含める。

- Project Knowledgeの目的
- 各Skillの責務と明示呼び出しの境界
- Knowledge Baseの構成と保存方針
- データフォーマットとfrontmatter
- `pk_category`、`pk_derivation`、`pk_source_type`の意味
- provenance、生成主体、検証主体、信頼性の扱い
- バージョンの種類、Source of Truth、更新条件、形式1.0だけを扱う境界
- `knowledge-policy.md`のfrontmatter設定、Skill同梱の標準Policy参照、プロジェクト固有方針の優先規則
- publishの対応出力、対象範囲の実行時指定、非永続化
- `manifest.yml`、`knowledge-policy.md`、`state.yml`という認知モデル
- 外部相談で検討したい論点

具体的な現行バージョン番号は記載しない。
文書冒頭には、再生成した日を「最終更新日」として記載する。

## 再生成後の確認

出力先はリポジトリ直下の`project-knowledge-spec-overview.md`とする。
既存ファイルを更新するときも、古い説明の部分修正だけで済ませず、情報源との整合性を全体で確認する。

必須項目、現行バージョン番号の混入、最終更新日、Markdownの構造を確認し、`git diff --check`を実行する。
