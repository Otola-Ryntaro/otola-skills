<!--
コラム原稿の frontmatter テンプレート（wiki-essay write モードで使用）
元レポート §2 のスキーマに準拠。値域は自由文字列で拡張可能（enum 化しない）。
-->
---
title: <魅力的なタイトル>             # 1行、読み手が思わずクリックしたくなる強度
seed: <seed-slug>                     # interests/questions.md の seed と対応（必須・孤立コラムを許さない）
audience: patient                     # 読者ペルソナ（軸1）。例: patient / doctor / manager / general / student / investor 等、自由文字列
angle: <論証切り口の一行説明>          # 軸2、自由記述。例: 「ポジショントーク」「反対論への反論」「制度目線」「当事者目線」等
medium: note                          # 想定媒体。例: note / twitter-thread / newsletter / blog / podcast-script 等
length: 3000                          # 概算字数（整数 or 範囲文字列）
status: draft                         # draft → review → adopted → published。adopted で sync_to_vault.py が拾う
created: 2026-06-21                   # 執筆開始日
adopted_at:                           # 採用時に追記（YYYY-MM-DD）
references:                           # 引用した wiki ページ（戻り動線の起点、双方向リンクの種）
  - "[[反科学主義の5類型]]"
  - "[[エビデンスは武器ではない]]"
domain:                               # 横断ドメインタグ。複数指定可
  - medical-science
  - society-thought
confidence: medium                    # high / medium / low — 主張の確信度（vault opinion 規約と統一）
---

<!-- 本文ここから -->

## リード（読者の関心を掴む数行）

...

## 主張

...

## 論拠

...

## 立ち位置・限界

...

## 関連

- [[wiki/opinions/...]]
- [[wiki/concepts/...]]
