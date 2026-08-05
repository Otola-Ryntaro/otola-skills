---
name: wiki-absorb
description: 2段階吸い出しの段階2スキル。wiki-extract が LLM_Wiki の raw/staging/<source>/ に出力した深い抽出ノートを読み、深さを保ったまま LLM_Wiki 本体（wiki/concepts・opinions・entities）へ構造化して統合する。seed（depth: seed の芽）は concept 化せず interests/questions.md に「育てる問い」として登録し、後で wiki-prospect が深掘りできるようにする。統合後は抽出ノートを absorbed にして archive へ退避。「stagingを取り込んで」「抽出を統合して」「wiki-absorb」等で発動。LLM_Wiki文脈でのみ使う。先行する段階1は wiki-extract。
allowed-tools: Read, Glob, Grep, Write, Edit, Bash, Skill
---

# wiki-absorb — 段階2：staging を LLM_Wiki に統合

`~/Obsidian/LLM_Wiki/raw/staging/<source>/` の抽出ノート（wiki-extract の出力）を、**深さを落とさず** wiki 本体へ統合する。

## 🔴 鉄則
- **段階1の深さを保つ**。抽出ノートの濃い知識を、統合時に薄い数行へ要約し直さない。
- **手動トリガ・提案/確認**。どれを統合するか提示してから書く。
- 正本は `~/Obsidian/LLM_Wiki/CLAUDE.md`「5. ワークフロー > Ingest」。

## Phase 0: 実行前スナップショット＋操作 manifest（必須・省略不可）

absorb の開始前に必ず実施する。Phase 0 を完了するまで Phase 1 に進んではならない。

1. **影響範囲の列挙**: Phase 1 で対象 source を確定後、以下を事前にリストアップする:
   - 新規作成予定の wiki ページ
   - 既存更新予定のファイル（wiki ページ・00-Index.md・domains ハブ・interests/questions.md・raw/_sources.md・log.md）
   - 移動予定のノート（staging → absorbed、移動前後パスと frontmatter status 変更内容）
   - ソース側 `.llm-wiki/manifest.md`（存在する場合）

2. **バックアップ（_pre_absorb_backup/）**: 「既存更新」と「移動」に該当するファイルを
   `raw/staging/<source>/_pre_absorb_backup/` へコピーする（新規作成はコピー不要）。

3. **操作 manifest 作成**: `raw/staging/<source>/_absorb_manifest.md` を作成し、
   区分付きで全変更ファイルを記録する:

   ```markdown
   # absorb manifest — <source> — <日付>

   ## 新規作成
   - wiki/concepts/<ページ>.md

   ## 既存更新
   - wiki/concepts/<既存ページ>.md
   - 00-Index.md
   - wiki/domains/<domain>.md
   - interests/questions.md
   - raw/_sources.md
   - log.md

   ## 移動
   | ノート | 移動前 | 移動後 | status変更 |
   | --- | --- | --- | --- |
   | <ノート>.md | raw/staging/<source>/<ノート>.md | raw/staging/<source>/absorbed/<ノート>.md | extracted → absorbed |
   ```

Phase 0 が完了したら Phase 1 へ進む。

## Phase 1: 対象選択
1. `raw/staging/` 配下を走査し、`status: extracted` と `status: seed` のノートを一覧提示。
2. どの source（or 個別ノート）を統合するか確認（all 可）。

## Phase 2: 統合（depth: full）
各 `extracted` ノートについて、`source_type`/`domain` を引き継ぎつつ振り分け：
- 客観的事実・データ・手順 → `wiki/concepts/`（type: concept）
- ユーザーの主張・スタンス・批評 → `wiki/opinions/`（type: opinion）
- 人物・薬剤・企業・製品など固有名 → `wiki/entities/`（type: entity）

統合時：
- frontmatter標準（type/domain/tags/sources/created/updated/confidence）。`sources:` は抽出ノートの `source:` を引き継ぐ。
- **抽出ノートの「主要な知識（網羅）」「数値・データ」を要点を保って移植**（章立てを保持してよい）。
- 既存 concept ↔ opinion と `[[wikilink]]` 相互リンク。
- 「未解決・深掘り候補」は `interests/questions.md` に追記候補として提示。

## Phase 3: seed の分岐（depth: seed）
- `depth: seed` のノートは **concept 化しない**。
- `interests/questions.md` に「育てる問い」を登録（domain/優先度/status: open、由来を明記）。
- → 以後 `wiki-prospect` がその問いを web/論文で深掘りして concept/opinion に育てる。
- （必要なら `status: seed` のスタブ concept を作る運用も可。既定は questions 行き。）

## Phase 4: 後処理（二段構え）
- 統合/登録したノートの frontmatter を `status: absorbed` に更新。
- `raw/staging/<source>/absorbed/` へ移動（履歴は残し、未処理一覧から外す）。

## Phase 5: 台帳・索引・ログ
- `raw/_sources.md` 台帳に `| 統合日 | 元パス | 収穫先 | type |` を追記。
- 該当 `wiki/domains/<domain>.md` ハブ・`00-Index.md` を更新。
- `log.md` に `## [日付] absorb | <source> → concept/opinion N件・seed M件` を追記。
- 統合サマリ（件数・ドメイン内訳・seed→questions・相互リンク）を報告。

## Phase 6: ソース側 進捗マニフェスト（.llm-wiki/）の absorb 反映
wiki-extract がソースプロジェクトに置いた `.llm-wiki/manifest.md` の absorb 列を更新し、ソース側でも「統合済み・残り」を追えるようにする。
- 統合した各ノートの frontmatter `source:`（元ファイルの絶対パス）から、ディレクトリを上方向に辿って `.llm-wiki/manifest.md` を探す（`<dir>/.llm-wiki/manifest.md` が見つかるまで親へ）。
- 見つかれば、該当ユニット行の absorb 列を `✅`＋統合日に更新し、サマリ（absorb 済 <Z>）と `updated` を再計算する。
- seed として questions に登録したノートは absorb 列を `→Q`（育てる問い行き）と記録してよい。
- manifest が見つからない（extract を別経路で行った等）場合は vault 側台帳のみ更新し、その旨を報告（ソース側マニフェストは作らない＝absorb はソースをコピーしない原則を保つ）。

## 注意
- 日付は環境の currentDate を使う。
- 元データはコピーしない（staging の抽出は要約であり参照は `sources:` で保持）。

---

## ロールバック手順（manifest あり）

absorb 後に誤統合に気付いた場合:

1. `raw/staging/<source>/_absorb_manifest.md` を Read して変更ファイル一覧を把握する。
2. **新規作成**ファイル（manifest「新規作成」欄） → ユーザー承認後に削除。
3. **既存更新**ファイル → `raw/staging/<source>/_pre_absorb_backup/` から復元（上書きコピー）。
   対象: wiki ページ・00-Index.md・domains ハブ・questions.md・_sources.md・log.md。
4. **移動済みノート** → `_pre_absorb_backup/` のコピーから**内容と frontmatter（status 含む）ごと**元パスに復元する
   （単純な逆移動では `status: absorbed` 等の変更が戻らない）。ソース側 `.llm-wiki/manifest.md` も同様に復元。
5. 復元完了後、`_absorb_manifest.md` にロールバック実施日と理由を追記する。

## ロールバック手順（manifest なし・過去の absorb）

**削除を既定にしない**。以下の保守的手順に限定する。

**前提確認（必須）**: まず直近バックアップ（`~/exports/vault_backup_*/`、docs/030 参照）の存在と
取得日時を確認する。バックアップが当該 absorb より古い・存在しない場合は機械的復元を中止し、
ユーザーに手動マージを提案する。

1. 直近バックアップと現状の diff を取り、当該 absorb 以降に変化したファイル一覧を提示する
   （例: `diff -rq ~/exports/vault_backup_<日付>/wiki ~/Obsidian/LLM_Wiki/wiki`）。
2. 各ファイルについて区分を判定する:
   - バックアップに存在しない → **新規**（削除候補としてユーザーに提示、承認後のみ削除）
   - バックアップに存在する → **既存更新**（バックアップから復元を提案）
3. 新規・更新の判定と復元方針について**ユーザーの承認を1件ずつ得てから**実行する。まとめて自動実行しない。
4. questions.md・_sources.md・log.md・domains ハブ・00-Index.md についても差分を提示し、
   復元要否をユーザーが判断できるようにする。
