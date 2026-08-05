---
name: wiki-essay
description: LLM_Wiki の seed（意見の芽）から能動的に長文コラム（5000字級、note・Twitter スレッド・メルマガ等の公開原稿）を執筆するスキル。「読者ペルソナ × 論証切り口」の二軸で同じ seed を多角度から書くことで、陳腐化を防ぎ知的生産を深める。4モード：write（seed から新規執筆、esseist で脱AI仕上げ）／reflect（_inbox の申し送りを提案→承認で wiki に反映）／handoff（完成記事から相手拠点向け申し送り文生成）／rebuild-threads（_seed_threads.md 全体再生成）。2拠点モデル（既存の `~/claude code/コラム/` と新設の `~/claude code/LLM_wiki/essays/`）で `_inbox/*_request.md` による疎結合連携。採用時のみ vault へワンウェイ同期。発動：「コラム書く」「seed からエッセイ」「視点を変えて書く」「wiki-essay」「多視点コラム」「note 原稿」等。短い意見追加は wiki-interview、外部源取り込みは wiki-absorb の担当で本スキルではない。
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, AskUserQuestion, TodoWrite, Skill
---

# wiki-essay — seed から多視点コラムを能動的に書く

LLM_Wiki が蓄積した seed と既存 wiki 知識（concepts/opinions）を起点に、公開原稿水準のコラム
（note / Twitter スレッド / メルマガ等）を **読者ペルソナ × 論証切り口の二軸** で複数視点に展開する。
書いた原稿は git 管理、採用時のみ vault にミラー。Obsidian バックリンクで wiki ↔ コラムが繋がる。

## 🔴 鉄則

- **執筆途中で勝手に vault を書き換えない**。reflect モードでのみ提案→承認経由で vault に触る
- **sync_to_vault.py はデフォルト dry-run**。書き込みは `--apply` 明示時のみ（vault は git管理外で復元不可）
- **`~/claude code/コラム/` プロジェクトの既存テーマフォルダには触らない**。`_inbox/` のみ追加
- **write モードは esseist 仕上げを必ず通す**。LLM 直生成のままで保存しない
- **拠点越境は申し送りファイルで疎結合**。別セッションの相手拠点に直接書き換えに行かない
- **🔴 write モードは章ごと段階執筆を原則とする** — まとめて全章書かない。Phase 3 で「章ごと内容 draft（章タイトル＋箇条書き）」を全章一括提示して承認、Phase 4 で **1章ずつ** 本文化してユーザーに提示・承認を取りながら進める。理由: まとめて書くと破綻する／満足いかないことが多い（ユーザーフィードバック 2026-06-25）

## 拠点モデル

| 拠点 | 場所 | 役割 |
|------|------|------|
| 拠点A: コラム/ | `~/claude code/コラム/` | 歴史的本拠地、テーマ別フォルダ運用（既存16テーマ）、今後も継続 |
| 拠点B: essays/ | `~/claude code/LLM_wiki/essays/` | seed 駆動、本スキルの主舞台 |
| vault ミラー | `~/Obsidian/LLM_Wiki/essays/` | 採用時のみ同期、Obsidian バックリンク用 |

両拠点は `_inbox/*_request.md`（申し送り文）で疎結合連携。

## モード

`/wiki-essay <mode> [args...]` で起動。第一引数が mode。

| モード | 用途 | プロンプト |
|--------|------|----------|
| `write <seed-slug>` | seed から新規コラム執筆（A+B 二軸の視点選択） | `prompts/write.md` |
| `write --book <seed-slug>` | 連作モード、`books/<seed-slug>/` に章立て保存 | `prompts/write.md`（分岐） |
| `reflect` | `_inbox/` 申し送りを処理（提案→承認で wiki 更新） | `prompts/reflect.md` |
| `handoff <file>` | 完成記事から相手拠点向け `_request.md` を生成 | `prompts/handoff.md` |
| `rebuild-threads` | `_seed_threads.md` を全拠点走査で再生成 | `prompts/rebuild_threads.md` |

各モードの詳細は対応する `prompts/<mode>.md` を Read して指示として読む。

## 実行手順

1. 引数を解析して mode を判定。未指定 or 不明なら `AskUserQuestion` で1問だけ確認
2. 対応する `~/.claude/skills/wiki-essay/prompts/<mode>.md` を Read
3. プロンプトの指示に従って処理を進める
4. モード終端で `TodoWrite` に「次のアクション」を残す
   - write 後: 「frontmatter `status:` を `adopted` に手動更新、その後 `sync_to_vault.py --apply` を提案」
   - reflect 後: 「処理済み件数とユーザー次の判断」
   - handoff 後: 「相手拠点で `/wiki-essay reflect` を起動するよう案内」

## 起動例

```
/wiki-essay write 医局所属のメリットデメリット
/wiki-essay write --book 専門家こそ発信すべき
/wiki-essay reflect
/wiki-essay handoff コラム/医師のゆるキャリア/202604_main.md
/wiki-essay rebuild-threads
```

## 依存スキル

- **`esseist`** — write モードの最終仕上げで `Skill` ツール経由で呼ぶ（脱AI + エッセイ化）
- **`wiki-query`** — write モードの初期コンテキスト収集で呼べる（任意、wiki 既存知識の文脈収集）

## 関連ファイル

| パス | 役割 |
|------|------|
| `~/claude code/LLM_wiki/essays/README.md` | 拠点の役割と構造 |
| `~/claude code/LLM_wiki/essays/_seed_threads.md` | seed × 視点マトリクス（振り返りの主役） |
| `~/claude code/LLM_wiki/essays/_publish_queue.md` | adopted → published の段階管理 |
| `~/claude code/LLM_wiki/essays/_pending_backlinks.md` | sync 時に生成される逆リンク追加提案 |
| `~/claude code/LLM_wiki/essays/_inbox/` | コラム/ 拠点からの申し送り受け皿 |
| `~/claude code/コラム/_inbox/` | LLM_wiki/essays/ 拠点からの申し送り受け皿 |
| `~/claude code/LLM_wiki/essays/scripts/sync_to_vault.py` | 採用同期スクリプト（dry-run / --apply / 既存 diff Y/N） |
| `templates/column_frontmatter.md` | コラム frontmatter テンプレート |
| `templates/inbox_request.md` | 申し送り文テンプレート |
| `templates/seed_threads_entry.md` | `_seed_threads.md` 1 seed セクションのスニペット |
| `~/Obsidian/LLM_Wiki/log.md` | 操作ログの追記先（既存 wiki 運用と統一） |

## 制約事項

- vault (`~/Obsidian/LLM_Wiki/`) の `wiki/opinions/`, `wiki/concepts/`, `interests/questions.md` は **必ず提案→承認経由**でのみ変更
- 自動書き込み禁止（reflect モードでもユーザー承認を得てから適用、wiki-weave と同形式）
- `~/claude code/コラム/` プロジェクトには `_inbox/` 以外に書き込まない
- `sync_to_vault.py` はデフォルト dry-run、`--apply` 明示が必要。vault 既存ファイルとの上書きは Y/N 確認
- 連作モード（`books/`）はユーザー明示指定時のみ。デフォルトは単発フラット運用

## 設計プラン / チケット

- 詳細設計: `~/.claude/plans/wiki-wiki-te-wiki-essey-brainstorming-mighty-crown.md`
- チケット群: `~/claude code/LLM_wiki/docs/tickets20260621/`
- ブレスト経緯: Q1〜Q5b で 2拠点モデル + A+B二軸 + ワンウェイ同期を確定
