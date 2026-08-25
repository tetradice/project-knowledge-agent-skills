---
title: "verify操作の検証範囲"
description: "verifyはナレッジの整合性・鮮度・Policy適合性をread-onlyで検査し、重要度別に報告する"
version: "0.1.0"
generated:
  by: project-knowledge
  at: 2026-08-23T00:00:00Z
pk_source_kind: memo
pk_authority: secondary
pk_trust: provisional
---

# verify操作の検証範囲

## 決定・前提

`verify` は修正を行わないread-only操作である。OKF frontmatter、indexとlog、リンク切れ、孤立ページ、sources、消失したsource、情報の古さ、前回update以降の変更を検査する。

実装、Reference、設定とナレッジ本文の不一致、provisionalな情報への過度な依存、矛盾、廃止情報も確認する。さらに、プロジェクトKnowledge Policyへの不適合、要求された重要情報の欠落、保存価値の低い情報の残存を報告する。

Information ArchitectureはPolicyへの適合とは分けて評価し、indexからの検索性、段階的な読みやすさ、ページ量、情報のまとまりを確認する。Policyの保存候補とページを1対1に対応させる必要はなく、ページ分割や複数領域の統合は、それ自体では問題としない。

結果はHigh、Medium、Lowで分類し、修正可能な場合は対象を示して`update`を案内する。

## 判断理由

現行Skillの`verification.md`とナレッジのSkill概要で、検証対象とread-only性が一致している。旧`scope`は互換用語であり、現在の保存可否はプロジェクトKnowledge Policyで判断する。

## 未解決事項

なし。
