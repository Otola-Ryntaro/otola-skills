---
name: storage-audit
description: |
  ~/claude code/ 配下と AI ツールのホームディレクトリ（~/.codex, ~/.claude 等)に蓄積した
  「放置 worktree・セッションログ・状態ファイル・キャッシュ」を read-only で棚卸しし、
  削除候補を分類して回収可能なディスク容量とコピペ可能な削除コマンドを提示するスキル。
  削除は一切実行しない（ユーザーが自分で実行する。または明示承認を得た項目のみ代行）。
  発動条件: (1) /storage-audit コマンド (2)「ストレージ調査」「容量を空けたい」「ディスク掃除」
  「worktree 乱立チェック」「蓄積ファイル調査」「.codex が肥大」等のキーワード
  (3) 定期棚卸し（月一目安）。
  使用しないケース: 特定 1 ファイルの削除依頼 / OS 全体のディスク解析（DaisyDisk 等の領分）/
  git 履歴の縮小（filter-repo 等は別作業）。
allowed-tools: Read, Bash, Grep, Glob, AskUserQuestion, TaskCreate, TaskUpdate
---

# storage-audit — 蓄積ストレージ棚卸しスキル

2026-07-28 の worktree 乱立・~/.codex 肥大調査（2.4GB→回収）で確立した手順の定型化。

## 絶対のルール

1. **本スキルは read-only。** 調査中に rm / delete / remove / prune を実行しない。
2. **削除はコマンド提示のみ**。ユーザーが自分のシェルで実行する。「代行して」と明示されたら、対象を 1 グループずつ AskUserQuestion で承認を取ってから実行する。
3. **稼働中プロセスの書き込み先に触れない**（sqlite / -wal / 実行中セッションのログ）。削除提案には必ず「対象ツールを終了してから」と付記する。
4. **worktree の削除は `git worktree remove` のみ提示**。`rm -rf` は提示もしない。
5. 判断が割れるもの（未マージ・dirty あり・用途不明）は削除候補にせず「要確認」に分類する。

## 実行フロー

### Phase 1 — worktree 監査

```bash
~/claude\ code/Evironment/scripts/worktree-audit.sh
```

- 出力の分類（🗑 削除候補 / 🚧 作業中 / ❓ 要確認 / 🔒 managed / ⚠️ prunable）をそのまま使う。
- 🗑 のみ削除コマンド列に載せる。❓ は dirty の中身（`git -C <path> status --porcelain` と diff 要約）を添えてユーザー判断に回す。
- スクリプトが無い環境では `git worktree list --porcelain` + `git merge-base --is-ancestor` で同等判定を手組みする（判定基準: default branch にマージ済み かつ dirty 0 = 削除候補）。

### Phase 2 — AI ツールホームの肥大調査

```bash
~/claude\ code/Evironment/scripts/codex-storage-audit.sh   # ~/.codex（閾値警告つき）
du -sh ~/.claude 2>/dev/null && du -sm ~/.claude/* 2>/dev/null | sort -rn | head -10
```

主な蓄積源と安全な回収方法:

| 場所 | 内容 | 回収方法（提示用） |
|------|------|------|
| `~/.codex/sessions/` | セッション JSONL が無限蓄積 | `find ~/.codex/sessions -type f -mtime +30 -delete`（Codex 全終了後） |
| `~/.codex/logs_*.sqlite` | ログ DB | Codex 全終了後にのみ削除可。-wal / -shm も同時に |
| `~/.codex/log/` | テキストログ | mtime +30 で削除可 |
| `~/.claude/projects/*/` | セッション履歴・メモリ | 削除しない（メモリ消失）。肥大時のみ古い session jsonl を報告 |
| `~/.codex/plugins`, `backups` | プラグイン・バックアップ | 重複バージョンのみ候補。標準の更新/アーカイブ機構を優先 |

### Phase 3 — プロジェクト側の蓄積調査

```bash
for d in "$HOME/claude code"/*/.claude/state "$HOME/claude code"/*/.agents "$HOME/claude code"/*/.playwright-mcp "$HOME/claude code"/*/node_modules; do
  [ -d "$d" ] || continue
  echo "$(du -sm "$d" | cut -f1)MB	$d"
done | sort -rn | head -20
```

- `.claude/state` / `.claude/sessions`: 数十 MB 超のものだけ報告。削除提案はしない（動作状態のため）。
- `.agents/`: 中身がスキル資産か受信メッセージかを確認してから判断（スキル資産はバグではない — 2026-07-26 調査で Meocli_LP の 1,479 ファイルは nano-banana スキル資産だった）。
- `node_modules`: **休眠プロジェクト**（git 最終コミットが 6 ヶ月超前）のものだけ削除候補。`npm install` で再生成可能な旨を付記。
- プロジェクト内 `.codex/` は通常 hooks.json のみ（4KB）で無害。膨らんでいたら中身を報告。

### Phase 4 — 休眠プロジェクトの特定（アーカイブ候補）

```bash
for repo in "$HOME/claude code"/*/; do
  [ -d "$repo/.git" ] || continue
  last=$(git -C "$repo" log -1 --format=%cs 2>/dev/null) || continue
  echo "$last	$(basename "$repo")"
done | sort | head -20
```

最終コミットが古い順に列挙し、`_archive/` への移動候補として提示する（移動もユーザー実行）。

### Phase 5 — レポート

以下の形式で会話中に提示する（ファイル出力は求められた場合のみ）:

1. **回収可能容量の見積り**（分類別合計）
2. **削除コマンド一覧**（コピペ可能なブロック。グループ別・安全な順）
3. **要確認リスト**（dirty 内容・未マージ規模つき）
4. **触らないもの**（稼働中 DB、メモリ、作業中 worktree）

削除実行後に再度 Phase 1〜2 のスクリプトを流して差分（before → after）を報告すると完了。

## 定期運用

月一目安。`/shime` の締めや大型プロジェクト完了後のタイミングが適する。goal-feed 運用中は
Cleanup Decision Gate（goal-feed review-protocol G-5b）が worktree を都度回収するため、
本スキルはその取りこぼし（異常終了・手動作成分）を拾う安全網の位置づけ。

## 実績（参考ベースライン）

- 2026-07-28: worktree 17→8 個（9 削除 + prune 1）、~/.codex/sessions 1.0GB→570MB 回収。
