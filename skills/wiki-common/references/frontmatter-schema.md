# frontmatter 規約（正本）

正本は `~/Obsidian/LLM_Wiki/CLAUDE.md` §3「ページ frontmatter 標準」。ここには取込・収集系スキルが参照するために要点を転記する。**vault 側の CLAUDE.md が変更された場合はこのファイルも追従更新すること**（DRY 違反の温床にしないため、転記は最小限に留める）。

## 標準フィールド（全 wiki ページ共通）

```yaml
---
title: <ページ名>
type: concept | entity | opinion | summary | domain-hub | paper
domain: [medical-science]        # 複数可。config.md のキーを使う
tags: []
sources:                          # 元データへの参照（コピーしない）
  - "~/claude code/Paper_Serch/papers/xxx.md"
  - "https://..."
created: YYYY-MM-DD
updated: YYYY-MM-DD
confidence: high | medium | low    # 裏取りの強度（3値固定、注釈付き値は不可）
---
```

## フィールド運用ルール

- `domain:` は物理フォルダでなく frontmatter タグで管理する（概念が複数ドメインにまたがってもページ移動不要）
- `tags:` は横断タグ用。記法統一: frontmatter は `tags: [<タグ名>]`（`#` なし）、本文/行内インラインは `#<タグ名>`
- `confidence:` は `high` / `medium` / `low` の3値固定。`high (要出典確認)` のような注釈付き値は使わない
- `sources:` は既存資産・URL への参照のみで、内容をコピーしない

## `type: paper` 専用フィールド

`type: paper` は research_report 由来の査読論文を `wiki/papers/` に取り込む文献ノート専用。既存 concept 集計とは分離し、paper は流入バッファとして扱う。

| フィールド | 型 | 必須 | 説明 |
|---|---|---|---|
| `pmid` | 文字列 | 必須 | 冪等キー。数値ではなく文字列として保持する |
| `doi` | 文字列 | 必須（空可） | DOI |
| `journal` | 文字列 | 必須（空可） | 掲載誌 |
| `year` | 整数 | 必須 | 出版年 |
| `theme` | 文字列 | 必須 | research_report の theme |
| `rating` | 整数 | 必須 | RATINGS_CSV_URL の最新 rating |
| `rated_at` | YYYY-MM-DD | 必須 | rating を読んだ日 |
| `zotero_key` | 文字列 | 必須（空可） | Zotero item key |
| `status` | unread / read / absorbed / archived | 必須 | 文献ノートの処理状態 |

`status` は paper 専用の正式フィールド。seed 系への展開は引き続き別途判断する。

## `aliases`（未公式フィールド、ad-hoc 運用）

title にファイル名へ使えない文字（`/` `:` `（）` 等）や装飾を入れる場合、`aliases:` に表示名を入れる運用が config.md の「リンク健全性」節にある。ただし CLAUDE.md §3 の標準フィールド一覧には含まれておらず、**正式なスキーマフィールドとしては未確定**。新規スキルで `aliases:` を必須フィールド扱いにしないこと。

## `status` フィールドについて（重要な確認事項）

REB-008 チケット起票時点では「concepts/opinions/entities/seeds の frontmatter に `status` を含む」想定だったが、**2026-07-03 時点の実際の標準（CLAUDE.md §3）に `status` フィールドは存在しない**。seed 系の `status: open | collected` 運用は `interests/questions.md` 内の非 frontmatter な行内表記であり、wiki ページ本体の frontmatter 標準とは別系統。今後 seed を 1 ノート化する際（REB-016）に `status` フィールドを frontmatter へ正式導入するかは、その時点で判断すること。

## 検証コマンド

```
python scripts/validate_frontmatter.py ~/Obsidian/LLM_Wiki/wiki
```

(read-only。フォーマットチェックのみ)
