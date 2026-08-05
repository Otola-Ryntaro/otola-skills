---
name: wiki-weave
description: LLM_Wiki（~/Obsidian/LLM_Wiki/）の孤立ノード（実体はあるが [[リンク]] が無いページ）を検出し、本文を読んで意味的に繋ぐべき既存ページを特定、双方向リンクを末尾「## 関連」節に追記して孤立を解消する。検出専用の wiki-lint に対する「適用系」。lintレポートがあれば入力に使える。「孤立ノードを繋いで」「浮いてるページを繋いで」「孤立リンク生成」「リンクを張り直して」「wiki-weave」等で発動。手動トリガのみ・提案→承認を厳守。LLM_Wiki文脈でのみ使う。
allowed-tools: Read, Glob, Grep, Write, Edit, Bash
---

# wiki-weave — 孤立ノードを意味推論で繋ぎ直す（適用系）

「実体はあるが線が無い」ページを、意味的に正しい既存ページへ双方向リンクで繋ぎ、孤立を解消する。
検出専用の `wiki-lint` のカウンターパート（lint は読み取り専用のまま、weave が書き込みを担う）。

## 🔴 鉄則
- ロジックの正本を二重化しない（DRY）。実処理前に必ず読む:
  1. `~/Obsidian/LLM_Wiki/CLAUDE.md`（§1 最重要原則・§3 frontmatter）
  2. `~/Obsidian/LLM_Wiki/config.md`（ドメイン定義・入口・「リンク健全性（空ノード対策）」節＝ファイル名/`aliases` のリンク解決規則。リンク切れ／偽の空ノードを生まないために必読）
- すべてのパスは `~/Obsidian/LLM_Wiki/` 配下の絶対パスで扱う（cwd が vault でなくても動く）。
- 手動トリガのみ。提案→承認を厳守。承認分以外は wiki に書き込まない（vault原則1・2）。
- 扱うのは「実体あり・線なし」だけ。「線あり・実体なし」＝未解決リンク／空ノードは対象外（wiki-lint・docs/013 の領分）。
- vault は復元不可。リンク適用（手順 step 5）は append 中心の外科的変更に限り、本文整形・既存行削除をしない。

## 対象と非対象
- 対象: `wiki/`（concepts / opinions / entities / domains）の .md。
- 非対象（走査から除外）: `00-Index.md` / `log.md` / `config.md` / `CLAUDE.md` / `meta/*` / `interests/*` / `raw/*` / `investigations/*`。

## 孤立ランク
- Rank A = 完全孤立（出リンク0・被リンク0）— 最優先。
- Rank B = 被リンクゼロ（出リンク>0・被リンク0）— 次点。
- 被リンク判定はファイル名と frontmatter `aliases` の両方で行う（Obsidian のリンク解決はファイル名ベース、表示エイリアスを取りこぼさない）。
- 🔴 被リンクプールから `00-Index.md` と `wiki/domains/` ハブを除外する。これらは目次的 index（vault原則5でほぼ全ページが index に載る）であり、そこからの参照は「セマンティックな繋がり」ではない。除外しないと全ページが被リンクありとなり孤立を1件も検出できない（偽陰性）。「index や目次には載るが関連概念と相互リンクされていない」ページこそ本スキルの対象。

## 手順
1. 前提読込・範囲決定: 上記正本2つ（`CLAUDE.md` §1/§3 と `config.md` のドメイン・「リンク健全性」節）＋`~/Obsidian/LLM_Wiki/00-Index.md` を Read。引数で範囲を決める（空欄=wiki全体／ドメイン名／フォルダ）。
2. 孤立検出（ランク付け）: `~/Obsidian/LLM_Wiki/wiki/` の各ページの出リンク・被リンクを Glob/Grep で集計し Rank A → Rank B に分類。被リンクプールは `00-Index.md` と `wiki/domains/` を除いたコンテンツページ（concepts/opinions/entities）に限る（上記「孤立ランク」の除外規則）。`~/Obsidian/LLM_Wiki/meta/lint-reports/` に孤立リストがあれば突き合わせる（無くても単独で算出して動く）。
3. 繋ぎ先の意味推論: 各孤立ページ本文と、同ドメインの concept/opinion/entity・`wiki/domains/` ハブ・`00-Index.md` を Read し、意味的に関連する既存ページを提案。各候補に〔繋ぎ先ページ / 関係種別（concept↔opinion・上位/下位概念・同ドメイン関連・entity言及）/ 根拠1行 / 確信度〕を付す。確信度 high/medium のみ採用。low しか出ない孤立ページは強制リンクせず「知識の穴」候補として `interests/questions.md` 追記を提案する。
4. 提案レポート → 承認: `~/Obsidian/LLM_Wiki/meta/weave-reports/[YYYY-MM-DD].md` に表形式で出力（`| 孤立ページ | ランク | 繋ぎ先候補 | 関係 | 根拠 | 確信度 |`）。承認粒度はリンク単位（行ごとに採否可）。ユーザーが承認するまで wiki へ書き込まない。
5. リンク適用（承認分のみ）: 双方向。繋ぎ先ファイル名の実在を確認した上で、両ページ末尾の `## 関連` 節（無ければ作成）に `[[リンク]]` を append。concept↔opinion は「関連する自分の見解 / 関連する事実」の既存イディオムに寄せる。本文は整形しない。title≠ファイル名のページへは `[[ファイル名|表示文言]]`。`updated` フィールドがあれば当日に更新（無ければ追加しない＝frontmatter 構造を変えない）。
6. 反映: 必要なら `00-Index.md` を更新し、`~/Obsidian/LLM_Wiki/log.md` に `## [YYYY-MM-DD] weave | 孤立解消 N件 / 保留 M件` を1行追記。
7. 検証: 適用した Rank A/B ページが被リンク>0 になったことを Grep で再確認。新たなリンク切れ（実在しないファイル名への `[[...]]`）を生んでいないことを確認。

## 注意
- 日付は環境の currentDate を使う（不明なら相対日付を書かない）。
- 自動削除・本文の大改変・自動巡回はしない。
- LLM_Wiki 以外の文脈では使わない（汎用の link-fixer ではない）。
