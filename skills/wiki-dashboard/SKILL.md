---
name: wiki-dashboard
description: LLM_Wiki（~/Obsidian/LLM_Wiki/）の可視化。wiki配下を走査してドメイン別件数・type別（concept/opinion/entity）・直近更新ページ・confidence:low一覧・未解決の問い数を集計し、meta/dashboard.md の静的サマリを更新する。**外部プロジェクトのセッションからでも vault を絶対パスで集計できる**グローバル版（vault内 `/wiki-dashboard` コマンドと同等）。「wikiのダッシュボード」「wiki全体像」「wiki集計」「wiki-dashboard」「どれだけ溜まった」「手薄なドメインは」等で発動。LLM_Wiki文脈でのみ使う。
allowed-tools: Read, Glob, Grep, Write, Edit, Bash
---

# wiki-dashboard（グローバル版）— LLM_Wiki の可視化

vault内コマンド `/wiki-dashboard` を、**どのプロジェクトからでも**使えるようにしたグローバルスキル。
vault（`~/Obsidian/LLM_Wiki/`）を絶対パスで集計するため、外部プロジェクトのセッションからでも全体像を把握できる。

## 🔴 鉄則
- **ロジックの正本は二重化しない（DRY）**。手順は次を読んで従う:
  1. `~/Obsidian/LLM_Wiki/.claude/commands/wiki-dashboard.md`（コマンド定義＝正本）
  2. `~/Obsidian/LLM_Wiki/CLAUDE.md`「5. ワークフロー > Dashboard」
- **すべてのパスは `~/Obsidian/LLM_Wiki/` 配下の絶対パス**で扱う。
- **数値は実際にファイルを数えて出す。推測しない。**

## 手順
1. `~/Obsidian/LLM_Wiki/wiki/` 配下を走査（Glob/Grep）して集計:
   - ドメイン別ノート数（frontmatter `domain:`）
   - type別（concept / opinion / entity）の数
   - 直近更新ページ（`updated` 降順10件）
   - `confidence: low` のページ一覧
   - `~/Obsidian/LLM_Wiki/interests/questions.md` の未解決（open）数
2. `~/Obsidian/LLM_Wiki/meta/dashboard.md` 下部の「静的サマリ」を最新数値に書き換える（Dataviewブロックは消さない）。
3. 気づいた傾向を2〜3行添える（例: 「投資・ai-techが手薄」「low confidenceがN件、要強化」）。
4. `~/Obsidian/LLM_Wiki/log.md` に `## [日付] dashboard | 更新` を追記。

## 注意
- 日付は環境の currentDate を使う。
- LLM_Wiki 以外の文脈では使わない。
