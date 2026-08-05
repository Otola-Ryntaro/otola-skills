---
name: wiki-extract
description: 指定したプロジェクトや既存Obsidian vault等のソースを「全文・網羅的に」読み込み、深い抽出ノートを LLM_Wiki の固定フォルダ raw/staging/<source>/ に出力する2段階吸い出しの段階1スキル。内容の性質（医療記事・投資・経営・AIアプリ開発・コラム/意見・研究ノート等）に応じて抽出レンズを切替えるマルチドメイン設計。冒頭だけの浅い要約は禁止し、原文の節構成を保って深く抽出する。数行のアイディアの芽は seed として判定し育てる問いを付す。「このプロジェクトを吸い出して」「網羅的に抽出」「stagingに抽出」「wiki-extract」等で発動。LLM_Wiki文脈でのみ使う。続く段階2は wiki-absorb。
allowed-tools: Read, Glob, Grep, Write, Edit, Bash, Skill
---

# wiki-extract — 段階1：網羅的に深く吸い出す

ソース（`~/claude code/` のプロジェクト、既存Obsidian vault、任意フォルダ）を**全文網羅的に**読み、構造を気にせず深い抽出ノートを `~/Obsidian/LLM_Wiki/raw/staging/<source>/` に出力する。
**wiki本体（wiki/）には触れない。** 統合は段階2 `wiki-absorb` が行う。

## 🔴 鉄則
- **深さ最優先**。各ユニットは**全文を読む**。冒頭だけ読んで数行に丸める前回の失敗を繰り返さない。
- **元ソースは読むだけ・コピーしない**（`source:` に絶対パスを記録）。
- **手動トリガ・提案/確認**。一度に大量に走らせず、1ソース/数ユニット単位で結果を見せる。
- cwd or 引数が LLM_Wiki vault 自身なら警告して停止。

## 最初に読む（正本）
- `~/Obsidian/LLM_Wiki/config.md` … ドメイン定義。
- `~/Obsidian/LLM_Wiki/raw/_sources.md` … 既収穫台帳（重複の参考）。

## Phase 1: 対象決定・検出
1. 引数のパス（無ければ cwd）を対象に。知識ファイルを列挙：
   `docs/ papers/ articles/ Result/ Column/ daily_report/ claudedocs/ codex/ product/ data/` ＋ ルート主要 `*.md`。
2. 「知識ユニット」を決める：最終版記事＝最新版1本／版が並ぶトピックフォルダ＝最新版を主に旧版で補完／単独文書＝それ自体。

## Phase 2: source_type 判定（マルチドメイン）
各ユニットの性質を推定し、抽出レンズを選ぶ：

| source_type | 重点抽出項目 |
|---|---|
| medical-article | 定義・疫学・原因・症状・検査・診断・治療・予後・エビデンス |
| investment | 対象・論拠・指標/データ・リスク・想定シナリオ・結論 |
| business（経営） | 課題・戦略/意思決定・KPI・制約・結果/学び |
| ai-app / code | 目的・アーキテクチャ・技術スタック・設計判断・ハマりどころ・再利用パターン |
| column / opinion | 主張・根拠・反論・前提・スタンス |
| research / notes | 問い・方法・所見・結論・引用 |
| generic | 主要事実・主張・データ・定義・未解決点 |

迷うソースは generic。ドメインは `config.md` のキーで推定。

## Phase 3: 網羅抽出（深さの核）
- ユニットを**全文読む**（長くても節ごとに読み切る）。
- 原文の節構成を保ったまま、レンズの重点項目を**漏らさず**抽出。
- 余計な定型（SEO/schema.org/宣伝/CTA/院名/編集メモ `>...`）は捨てるが、**知識は削らない**。
- 出典・参考文献・数値は必ず拾う。

## Phase 4: seed 判定
- 内容が数行・見出しだけ・アイディアの芽のソースは `depth: seed`。
- 抽出できる中身が無くても、「核となる主張/問い」と「育てるための具体的な問い（wiki-prospect用）」を書き残す。

## Phase 5: 出力（固定フォルダ）
- 出力先: `~/Obsidian/LLM_Wiki/raw/staging/<source>/`（無ければ作成。`<source>` は元の分かりやすい名前）。
- 各ユニット → 1ファイル（下記様式）。
- `_extract_index.md` を作成/更新：抽出一覧・各 source_type/domain/depth・seed一覧。
- 完了後、何を何件抽出したか・seed何件か・次は `wiki-absorb` で統合する旨を報告。

### 抽出ノート様式
```yaml
---
title: <タイトル>
source: <元の絶対パス>
source_type: <上表のいずれか>
domain: [..]
depth: full | seed
status: extracted | seed
extracted: <YYYY-MM-DD>
---
# <タイトル>
## 概要
## 主要な知識（網羅）   ← レンズに沿って全節を深くカバー（箇条書き＋小見出し）
## 判断・論拠・スタンス（あれば）
## 数値・データ
## 未解決・深掘り候補   ← wiki-prospect / questions 行きの問い
## 出典
```

## Phase 6: プロジェクト側 進捗マニフェスト（.llm-wiki/）
ソースプロジェクト側で「**どこまで吸い上げ済み・残り・実行日**」を追えるよう、対象ルート（引数パス、無ければ cwd）に `.llm-wiki/manifest.md` を作成/更新する。
**これがソース側に置く唯一の生成物**（進捗台帳のみ。抽出ノート本体・元ソースのコピーは置かない）。

- 対象ルート＝Phase 1 でスキャンしたルート。`.llm-wiki/` が無ければ作る。
- Phase 1 で検出した全知識ユニットを 1 行ずつ記録する：
  - 今回抽出したもの → extract 列 `✅`＋抽出日＋staging 相対パス。
  - 検出したが未抽出のもの → extract 列 `⬜ pending`（これで「残り」が一覧で見える）。
- 既存 manifest があれば**行をマージ**（既存行の absorb 列・他ユニット・メモは保持し、今回分のみ更新）。`updated` とサマリを再計算。
- absorb 列は wiki-absorb が後で更新するため、extract 時点は未統合なら `⬜` のままにする。
- 対象ルートが git リポジトリなら（`git -C <root> rev-parse` で確認）、`.gitignore` に `.llm-wiki/` 行が無い場合のみ追記する。git 管理外なら何もしない。

### manifest 様式
```markdown
---
project: <プロジェクト名 or 対象ルート絶対パス>
vault: ~/Obsidian/LLM_Wiki/
created: <YYYY-MM-DD>
updated: <YYYY-MM-DD>
---
# LLM_Wiki 吸い出し進捗 — <プロジェクト名>

wiki-extract / wiki-absorb が自動更新する進捗台帳。手動編集はメモ欄のみ推奨。
extract = プロジェクト → vault staging への抽出 ／ absorb = staging → wiki 本体への統合。

## サマリ
- 総ユニット: <N> / extract 済 <X>・残り <Y> / absorb 済 <Z>
- 最終 extract: <YYYY-MM-DD>

## ユニット一覧
| ユニット(相対パス) | source_type | extract | extract日 | staging出力 | absorb | absorb日 | メモ |
|---|---|---|---|---|---|---|---|
| docs/001_x.md | ai-app | ✅ | 2026-06-03 | raw/staging/<src>/001_x.md | ⬜ | — |  |
| Column/bar.md | column | ⬜ pending | — | — | ⬜ | — |  |
```

## 注意
- 日付は環境の currentDate を使う。
- トークン消費が大きい。対象が多い時は「まず数ユニット」と区切る。
- 区切って実行しても manifest はマージ更新するので、検出済み・未抽出の残りが常に追える。
