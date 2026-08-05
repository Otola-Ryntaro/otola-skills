---
name: wiki-lint
description: LLM_Wiki（~/Obsidian/LLM_Wiki/）の健全化チェック。矛盾・陳腐化・孤立ページ・リンク切れ・欠落概念・裏取り不足（confidence: low）・データ欠落を検出し、修復案と「次に調べるべき問い」を提案する。**外部プロジェクトのセッションからでも vault を絶対パスで点検できる**グローバル版（vault内 `/wiki-lint` コマンドと同等）。「wikiをlint」「wiki点検」「wiki-lint」「矛盾チェック」「孤立ページ」「リンク切れ」「wikiを健全化」等で発動。extract→absorb や prospect の後の点検にも使う。LLM_Wiki文脈でのみ使う。
allowed-tools: Read, Glob, Grep, Write, Edit, Bash
---

# wiki-lint（グローバル版）— LLM_Wiki の健全化チェック

vault内コマンド `/wiki-lint` を、**どのプロジェクトからでも**使えるようにしたグローバルスキル。
`/wiki-lint` は vault（`~/Obsidian/LLM_Wiki/`）を開いたセッションでしか起動できないが、本スキルは
**vault を絶対パスで触る**ため、外部プロジェクト（例: `~/claude code/...`）から extract→absorb した直後でも
そのまま点検へ進める。

## 🔴 鉄則
- **ロジックの正本は二重化しない（DRY）**。実処理の手順は次の2つを読んで従う:
  1. `~/Obsidian/LLM_Wiki/.claude/commands/wiki-lint.md`（コマンド定義＝正本）
  2. `~/Obsidian/LLM_Wiki/CLAUDE.md`「5. ワークフロー > Lint」
- **すべてのパスは `~/Obsidian/LLM_Wiki/` 配下の絶対パス**で扱う（cwd が vault でなくても動くように）。
- **自動で削除・大改変しない**。検出と提案に留め、修復はユーザー承認後にまとめて実行。

## 手順
1. 上記2つの正本を Read し、検出観点と出力先を把握する。
2. 範囲を決める（引数: 空欄=wiki全体 / ドメイン名 / フォルダ）。
3. 次の観点で `~/Obsidian/LLM_Wiki/wiki/` 等を走査（Glob/Grep/Read）:
   1. **矛盾** — 食い違う記述のページ対
   2. **陳腐化** — 後発ソースに supersede された古い主張（`updated` が古い）
   3. **孤立ページ** — どこからも `[[リンク]]` されていないページ
   4. **リンク切れ** — 存在しないページへの `[[リンク]]`
   5. **欠落概念** — 何度も言及されるのに専用ページが無い概念
   6. **裏取り不足** — `confidence: low` の放置ページ
   7. **データ欠落** — 補完できそうな空白
4. 結果を `~/Obsidian/LLM_Wiki/meta/lint-reports/[日付].md` に保存（観点別・重要度順）。
5. リンク切れ等の機械的修復は**ユーザー確認後**にまとめて実行。
6. **「次に調べるべき問い」を `~/Obsidian/LLM_Wiki/interests/questions.md` への追記候補として提案**（承認分のみ追記）。
7. `~/Obsidian/LLM_Wiki/log.md` に `## [日付] lint | 孤立N/陳腐N/新問いN提案` を追記。
8. **孤立ページ・リンク切れを実際に修復する場合**は lint レポートを確認後、`wiki-weave` スキルを使う（lint は検出・提案のみ、weave が適用）。

## 注意
- 日付は環境の currentDate を使う。
- 手動トリガ・提案→承認を厳守。点検対象を勝手に書き換えない。
- LLM_Wiki 以外の文脈では使わない（汎用の lint ではない）。
