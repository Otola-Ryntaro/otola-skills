---
name: wiki-common
description: 単独では発動しない共有リファレンス置き場。他の wiki-* スキルが confidence 判定基準・frontmatter 規約・ドメイン定義・HTML スタイルガイドを参照する際に Read で直接読み込む。
allowed-tools: Read
---

# wiki-common — 共有 references（発動しない）

このスキルはユーザーの発話では起動しない。他の wiki 系スキル（wiki-in, wiki-care, wiki-seed 等）が `references/` 配下のファイルを **Read ツールで直接参照** するための共有置き場。

- `references/confidence-table.md` — 資料種別×confidence 上限の判定基準
- `references/frontmatter-schema.md` — wiki ページの frontmatter 標準
- `references/domain-definitions.md` — ドメイン定義（vault `config.md` の正本を反映）
- `references/html-style-guide.md` — HTML 可視化のスタイルガイド（wiki-view 系が使用）
