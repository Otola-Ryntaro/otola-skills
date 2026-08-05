---
name: goal-feed-impl
description: |
  既にチケット（ticket_index.md）が生成済みで、Codex 側 goal-feed-impl が /goal 実装ループを回している / 回す予定の場面で、CC 側がレビュー役として並走する短縮スキル。
  Phase A〜D（計画・agmsg 合議・プランファイル Write）はスキップし、Phase E（初回 ticket レビューが未実施なら実施）→ Phase F（Codex から届く phase progress review request を自動処理）→ Phase G（final audit + /shime）を担当する。
  発動条件: (1) /goal-feed-impl コマンド (2)「チケットは出来ているので実装から」「/goal で回すので CC はレビュー係」「Phase 進捗レビューだけお願い」「ticket-verify までまとめて」等のキーワード (3) 既存 docs/tickets*/ や codex/tickets*/ が存在する状態で「Codex と組んで最後まで実装ループを回して」と依頼されたとき。
  使用しないケース: チケット未生成（→ goal-feed 本体を使う）/ 計画を最初からやり直す必要があるとき / 単発 review だけしたいとき（→ /cr を直接使う）。
allowed-tools: Read, Write, Edit, Grep, Glob, Bash, Skill, AskUserQuestion, TaskCreate, TaskUpdate
---

# goal-feed-impl — 実装ループ短縮版

Codex 側 `~/.codex/skills/goal-feed-impl/SKILL.md` の対（レビュアー＋最終監査役）として動く。`goal-feed` 本体の Phase E 以降だけを走らせる短縮エントリ。

## 目的

Codex 側 `goal-feed-impl` が `/goal` を使って `/ko` → `/cr`（自己）→ `/next` を Phase 単位で回す運用中、CC は agmsg 経由で受け取る **phase progress review request** を自動処理し、最後の `/ticket-verify` 結果を受けて **final audit + /shime** まで済ませる。

計画・プランファイル作成が既に完了している前提。まだなら本 skill ではなく `goal-feed` 本体を使う。

## 前提

- `docs/tickets*/ticket_index.md` または `codex/tickets*/ticket_index.md` が存在。
- （望ましい）`codex/plans/*_plan.md` が存在 — Acceptance Criteria との突合に使える。
- agmsg 設定済み。
- ghostty + herdr 環境。Codex の起動・入力操作は CC 側が herdr 経由で行う（`goal-feed` 本体 SKILL.md の「herdr 連携」節と共通ルール: prompt 先頭に `/` を置かない / Codex の skill 起動は `$agmsg` `$ticket-gen` 表記 / slash command は文末のみ）。

## 参照する references

本 skill は独自 references を持たず、`goal-feed` の references を共有する:

- `~/.claude/skills/goal-feed/references/review-protocol.md` — Phase E〜G の詳細（両者で共通）
- `~/.claude/skills/goal-feed/references/message-schema.md` — subject / body 一覧（`goal-feed-impl` prefix 版もここに集約）
- `~/.claude/skills/goal-feed/references/paid-service-quality-bar.md` — レビュー時の観点

各 Phase 直前に上記を Read する。

## 絶対のルール（`goal-feed` と共通）

1. **agmsg 操作はスクリプト経由のみ。** `~/.agents/skills/agmsg/scripts/` 配下。DB / config 直接編集禁止。
2. **自動レビューの二段ゲート。** 「本 skill がこのセッションで発動済み」かつ「subject が `goal-feed-impl ` または `goal-feed ` prefix で始まる review request」の両方で自動処理。
3. **有料サービス品質バーを毎レビューで参照する。**
4. **本質修正を優先する。** 症状潰しの diff は Critical で push back。

## Plan Mode について

`goal-feed` と違って本 skill は **plan mode に自動で入らない**。既にチケット化・計画確定済みの前提だから。ただし Preflight で「未解決の Critical 指摘がある / plan file が見つからない / チケット未着手」の兆候を検知したら、`AskUserQuestion` で「`goal-feed` 本体に切り替えますか？」を確認する。

---

## Preflight — 起動直後

### P-1. `ticket_index.md` の解決

引数指定を優先:

- `$ARGUMENTS` にパス指定あり → 使用（ファイルなら直接、ディレクトリなら `<dir>/ticket_index.md`）
- 未指定 → 探索:
  1. `docs/tickets*/ticket_index.md`（日付順、最新優先）
  2. `codex/tickets*/ticket_index.md`
  3. `docs/Ticket_index.md`（レガシー）

複数見つかったら `AskUserQuestion` で確認。0 件なら「チケットがまだありません。goal-feed 本体を使ってください」と案内して停止。

### P-2. `ticket_index.md` の状態確認

Read して以下を判定:

- 全チケットが `⬜` → 実装未着手。Codex 側で `/goal` を発動して `/ko` から回している最中の待ち状態と解釈。
- 一部が `🔄` / `✅` → 進行中。既に Phase F 段階の可能性。
- 全チケットが `✅` → 実装完了。Phase G に直行。
- Phase 構成テーブルなし → レガシー形式。優先度ベースで進める旨をユーザーに告知。

### P-3. plan file の探索（あれば強い）

`codex/plans/*_plan.md` から本チケット群に対応するプランを推定:

- 日付 prefix が一致（`ticket_index.md` の日付から）
- ファイル内で `ticket_index.md` パスに言及がある
- 見つかったら SLUG / DATE を抽出、以後の出力パスに使う

見つからなければ:

- `SLUG` を `AskUserQuestion` で確認
- `DATE_YYYYMMDD` は `date +%Y%m%d` を使用

### P-4. agmsg identity 確認

`goal-feed` Phase A-2, A-3 と同じ手順で:

- `whoami.sh` で TEAM / AGENT を取得
- `team.sh` で Codex peer を解決（複数なら AskUserQuestion）
- `CODEX_PEER` を握って以後固定

### P-4b. herdr で Codex pane を立ち上げ、実装ループを開始させる

1. `herdr agent list` で既存の codex agent を確認。なければ:

   ```bash
   herdr pane split --current --direction right --cwd "$(pwd)" --no-focus
   # 出力の pane ID を控える
   herdr agent start codex --kind codex --pane <PANE_ID>
   ```

2. 起動確認後、初回 prompt で **goal 機能の使用と完遂条件を明示**して実装ループを開始させる:

   ```bash
   herdr agent prompt codex 'inbox を確認して goal-feed-impl の依頼に対応して。goal 機能を使用すること。goal は全チケットを完遂し shime まで到達すること。skill 起動は $agmsg 表記を使うこと'
   ```

   先頭に `/` を置かない（Codex 側で slash command と誤解釈される）。

### P-5. Critical plan review 指摘の確認

`codex/reviews/*_ticket_review.md` が存在するなら Read し、未解決 Critical があるか確認。あれば `AskUserQuestion` で:

- 修正済みとして続行
- 一旦停止して Codex 側に修正依頼

### P-6. worktree lock 確認

作業が専用 worktree（feature/task 用のリンク worktree）で行われている場合、`git worktree list --porcelain` で locked 状態を確認し、unlocked なら以下で保護する:

```bash
git worktree lock --reason "managed=true goal=<SLUG> owner=cc created=<YYYY-MM-DD>" <exact-path>
```

- primary worktree（main/master/develop チェックアウト中の本体）は**絶対に lock しない**
- 既に別 reason で locked のものは上書き・unlock しない
- lock reason は不変メタデータ。状態の書き換えには使わない
- 後片付けは Phase G の Cleanup Decision Gate（review-protocol.md G-5b）でのみ行う

### P-7. 発動フラグの立て込み

`activated: true` をセッションメモリに保持。以後、subject prefix マッチによる自動処理を有効化。

---

## Phase E — Ticket Review（未実施なら実施）

- Codex から `goal-feed-impl ticket review request` を受信 → 起動
- または起動時に「Ticket レビューが未実施」と判定した場合、自発的に review を実行してから待機モードへ
- 詳細プロトコルは `~/.claude/skills/goal-feed/references/review-protocol.md` の Phase E 節。subject prefix だけ `goal-feed-impl ...` に置き換える

**返信 subject**: `goal-feed-impl ticket review findings`

---

## Phase F — Phase-by-Phase Review（自動ループ）

- Codex から `goal-feed-impl phase progress review request` を受信するたびに自動処理
- 詳細プロトコルは `~/.claude/skills/goal-feed/references/review-protocol.md` の Phase F 節。subject prefix だけ `goal-feed-impl ...` に置き換える

**特記事項**:

- Codex 側 `goal-feed-impl` は各 Phase の `/ko` → `/cr`（自己）→ `/next` を回し、Phase 完遂ごとに request を投げる想定
- `/cr` は CC 側でも呼ぶ（Skill 経由）。strict 判定は共通ロジック
- Critical 相当があれば「修正→再送」の往復。3 回で収束しなければ AskUserQuestion で方針変更を確認
- agmsg 返信後、`herdr agent prompt` で Codex に動作再開を指示する。**prompt 末尾に `/goal resume` を付ける**:

  ```bash
  herdr agent prompt codex 'inbox を確認して。Phase <N> のレビュー結果を返信済み。指摘対応のうえ次へ進んで /goal resume'
  ```

**返信 subject**: `goal-feed-impl phase progress review findings`

---

## Phase G — Final Audit + /shime

- Codex から `goal-feed-impl final review request` を受信 → 起動
- 詳細プロトコルは `~/.claude/skills/goal-feed/references/review-protocol.md` の Phase G 節。subject prefix だけ `goal-feed-impl ...` に置き換える

**返信 subject**: `goal-feed-impl final review findings`

**Worktree Cleanup Decision Gate（G-5b、必須）**: /shime より前に、専用 worktree の後片付け判断（integrate / PR / park / abandon）をユーザーに確認する。integrate / abandon なら「検証→コマンド表示→明示承認→再検証→unlock→直ちに remove」の順序を厳守。詳細は review-protocol.md G-5b。

**最後**: `/shime` を Skill 経由で呼び、日報作成と Plans.md 引き継ぎ。完了後に Codex へ `goal-feed-impl session closed` を通知。

---

## 自動処理ルール（`goal-feed` と共通、prefix だけ違う）

セッション内で新規 agmsg メッセージを検知するたびに、subject を評価する:

- `goal-feed-impl ticket review request` → Phase E
- `goal-feed-impl phase progress review request` → Phase F
- `goal-feed-impl final review request` → Phase G
- `goal-feed-impl ` prefix でその他 → AskUserQuestion
- `goal-feed ` prefix のもの（本体スキルからの request）→ 本 skill でも受けて対応する（後方互換）
- prefix 不一致 → 通常メッセージ、skill 未関与

`activated: false` の状態では自動処理しない。

---

## 出力パス規約（`goal-feed` と共通）

- `codex/reviews/${DATE_YYYYMMDD}_${SLUG}_ticket_review.md`
- `codex/reviews/${DATE_YYYYMMDD}_${SLUG}_phase_${N}_review.md`
- `codex/reviews/${DATE_YYYYMMDD}_${SLUG}_final_audit.md`

`SLUG` は Preflight で確定した値。`DATE_YYYYMMDD` は `ticket_index.md` の日付 prefix を優先し、無ければ本日日付。

---

## エラー・分岐処理

| 状況 | 動作 |
|------|------|
| ticket_index.md が見つからない | ユーザーに `goal-feed` 本体を推奨 |
| plan file が見つからない | 続行するが Acceptance Criteria 突合が甘くなる旨を警告、`AskUserQuestion` で「plan file を後から作りますか？」を確認 |
| 未解決 Critical 指摘あり | Preflight で停止、`AskUserQuestion` で判断 |
| Codex peer 不明 | goal-feed と同じ手順で解決 |
| Codex が長時間沈黙 | 15 分ごとに `inbox.sh` を能動チェック。1 時間無音でユーザーに続行判断を仰ぐ |
| /shime 起動失敗 | 手動で日報テンプレを提示、Plans.md 引き継ぎだけでも履行 |

---

## 完了条件

- 全 Phase の CC レビュー Critical 0
- Codex `/ticket-verify` 合格
- final audit を Write、agmsg 返信済み
- Worktree Cleanup Decision Gate 完了（integrate / PR / park / abandon の判断確定）
- `/shime` で日報作成

## 変更しないもの

- Codex 側 skill / config / state
- 既存 slash commands / agmsg
- `~/.claude/skills/goal-feed/references/`（本 skill から参照するが編集はしない）

## 使い方

```
/goal-feed-impl                            # デフォルト探索
/goal-feed-impl docs/tickets20260701/       # 特定 tickets ディレクトリ指定
/goal-feed-impl docs/tickets20260701/ticket_index.md
```
