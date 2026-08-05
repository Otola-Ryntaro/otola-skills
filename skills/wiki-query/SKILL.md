---
name: wiki-query
description: LLM_Wiki（~/Obsidian/LLM_Wiki/）に質問する。00-Index.md を起点に関連ページ（concepts/opinions/entities）を読み、**引用付き**で回答し、再利用価値があればページとして還元する。**外部プロジェクトのセッションからでも vault を絶対パスで参照して回答できる**グローバル版（vault内 `/wiki-query` コマンドと同等）。「wikiに聞く」「wikiで質問」「wiki-query」「wikiに◯◯ある？」「wikiでは何と言ってる」等で発動。LLM_Wiki文脈でのみ使う。
allowed-tools: Read, Glob, Grep, Write, Edit, Bash
---

# wiki-query（グローバル版）— LLM_Wiki に質問する

vault内コマンド `/wiki-query` を、**どのプロジェクトからでも**使えるようにしたグローバルスキル。
vault（`~/Obsidian/LLM_Wiki/`）を絶対パスで参照するため、外部プロジェクトのセッションからでも
wiki の知識に問い合わせできる。

## 🔴 鉄則
- **ロジックの正本は二重化しない（DRY）**。手順は次を読んで従う:
  1. `~/Obsidian/LLM_Wiki/.claude/commands/wiki-query.md`（コマンド定義＝正本）
  2. `~/Obsidian/LLM_Wiki/CLAUDE.md`「5. ワークフロー > Query」
- **すべてのパスは `~/Obsidian/LLM_Wiki/` 配下の絶対パス**で扱う。
- **推測で答えない**。wiki に無いことは「無い」と言い、能動収集（wiki-prospect）を提案する。

## 手順
1. `~/Obsidian/LLM_Wiki/00-Index.md` を読み、関連しそうなページを特定する。
2. 関連ページ（`wiki/concepts/` `wiki/opinions/` `wiki/entities/`）を実際に Read する。
3. **引用付き**で回答（どのページ・どの `sources:` に基づくか明示）。
   - 事実（concepts）と意見（opinions）が両方関わるなら、区別して提示する。
4. wiki に不足があれば欠落を明示し、**wiki-prospect** での能動収集を提案する。
5. 回答が今後も再利用価値を持つなら、`~/Obsidian/LLM_Wiki/wiki/`（type: summary）への還元をユーザーに確認し、
   OK なら作成して `00-Index.md` / `log.md` を更新する。

## 注意
- 日付は環境の currentDate を使う。
- LLM_Wiki 以外の文脈では使わない。
