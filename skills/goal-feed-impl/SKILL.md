---
name: goal-feed-impl
description: |
  既にチケット（ticket_index.md）が生成済みで、Codex 側 goal-feed-impl が /goal 実装ループを回している / 回す予定の場面で、CC 側がレビュー役として並走する短縮スキル。
  Phase A〜D（計画・agmsg 合議・プランファイル Write）はスキップし、Phase E（初回 ticket レビューが未実施なら実施）→ Phase F（Codex から届く phase progress review request を自動処理）→ Phase G（final audit + /shime）を担当する。
  発動条件: (1) /goal-feed-impl コマンド (2)「チケットは出来ているので実装から」「/goal で回すので CC はレビュー係」「Phase 進捗レビューだけお願い」「ticket-verify までまとめて」等のキーワード (3) 既存 docs/tickets*/ や codex/tickets*/ が存在する状態で「Codex と組んで最後まで実装ループを回して」と依頼されたとき。
  使用しないケース: チケット未生成（→ goal-feed 本体を使う）/ 計画を最初からやり直す必要があるとき / 単発 review だけしたいとき（→ /cr を直接使う）/ Orca の外で動かすとき（Orca のターミナルで起動し直す）。
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
- Orca のターミナルで動作していること。worktree の作成と Codex の起動は CC 側が `orca` で行う（`goal-feed` 本体 SKILL.md の「Orca 連携」節と共通ルール: 送る文の先頭に `/` を置かない / Codex の skill 起動は `$agmsg` `$ticket-gen` 表記 / slash command は文末のみ）。

## 参照する references

本 skill は独自 references を持たず、`goal-feed` の references を共有する:

- `~/.claude/skills/goal-feed/references/orca-protocol.md` — worktree・agmsg の名前・ペイン入力・待機・片付け（Preflight の前に必ず読む）
- `~/.claude/skills/goal-feed/references/review-protocol.md` — Phase E〜G の詳細（両者で共通）
- `~/.claude/skills/goal-feed/references/message-schema.md` — subject / body 一覧（`goal-feed-impl` prefix 版もここに集約）
- `~/.claude/skills/goal-feed/references/paid-service-quality-bar.md` — レビュー時の観点

各 Phase 直前に上記を Read する。

## 絶対のルール（`goal-feed` と共通）

1. **agmsg 操作はスクリプト経由のみ。** `~/.agents/skills/agmsg/scripts/` 配下。DB / config 直接編集禁止。
2. **自動レビューの二段ゲート。** 「本 skill がこのセッションで発動済み」かつ「subject が `goal-feed-impl ` または `goal-feed ` prefix で始まる review request」の両方で自動処理。
3. **有料サービス品質バーを毎レビューで参照する。**
4. **本質修正を優先する。** 症状潰しの diff は Critical で push back。
5. **自己修復プロトコルに従う。** `goal-feed` 本体 SKILL.md の「自己修復プロトコル」節（S-1〜S-5）を共有する: `.goalfeed/state.json` への状態永続化、Codex の手が止まったのに返信がないときの自動起こし直し（ユーザー確認なし、3 連続停滞でのみエスカレーション）、冪等な待機、APPROVE への検証根拠引用の必須化。

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

### P-4. Orca の配置を確定し、Codex を起動する

`orca-protocol.md` の 1〜5 節に従う。

1. 前提チェックと配置の判定を行う。orca-master 配下なら渡された worktree・ハンドル・名前を使い、2 と 3 は飛ばす。
2. `ticket_index.md` がコミット済みか `git ls-files --error-unmatch <path>` で確かめる（未コミットだと worktree に来ない）。未コミットなら、コミットしてよいかを `AskUserQuestion` で確認する。
3. worktree を作り、agmsg の名前を登録し、Codex を起動する。ブリーフには goal 機能の使用と完遂条件を明示する:

   ```text
   $goal-feed-impl <ticket_index のパス> で対応して。goal 機能を使用すること。goal は全チケットを完遂し、CC の final review を通すこと
   ```

### P-5. Critical plan review 指摘の確認

`codex/reviews/*_ticket_review.md` が存在するなら Read し、未解決 Critical があるか確認。あれば `AskUserQuestion` で:

- 修正済みとして続行
- 一旦停止して Codex 側に修正依頼

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
- agmsg 返信後、Codex を起こす。**文の末尾に `/goal resume` を付ける**:

  ```bash
  orca terminal send --terminal <codex_handle> --enter --wait-submit 10 --json \
    --text '~/.agents/skills/agmsg/scripts/inbox.sh <TEAM> <slug>-codex で受信を確認して。Phase <N> のレビュー結果を返信済み。指摘対応のうえ次へ進んで /goal resume'
  ```

**返信 subject**: `goal-feed-impl phase progress review findings`

---

## Phase G — Final Audit + /shime

- Codex から `goal-feed-impl final review request` を受信 → 起動
- 詳細プロトコルは `~/.claude/skills/goal-feed/references/review-protocol.md` の Phase G 節。subject prefix だけ `goal-feed-impl ...` に置き換える

**返信 subject**: `goal-feed-impl final review findings`

**Worktree Cleanup Decision Gate（G-5b、必須）**: /shime より前に、先に Codex を閉じ、後片付け判断（integrate / PR / park / abandon）をユーザーに確認する。詳細は review-protocol.md G-5b。

**最後**: `/shime` を Skill 経由で呼び、日報作成と Plans.md 引き継ぎ。

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
| Orca の外にいる | Orca のターミナルで起動し直すようユーザーに伝えて停止 |
| Codex の手が止まったのに返信がない | 自己修復プロトコル S-2: 画面を読んで起こし直す（ユーザー確認なし）。3 連続停滞でユーザーに確認を依頼 |
| /shime 起動失敗 | 手動で日報テンプレを提示、Plans.md 引き継ぎだけでも履行 |

---

## 完了条件

- 全 Phase の CC レビュー Critical 0
- Codex `/ticket-verify` 合格
- final audit を Write、agmsg 返信済み
- Worktree Cleanup Decision Gate 完了（integrate / PR / park / abandon の判断確定）
- `/shime` で日報作成

## 変更しないもの

- Codex 側 config / state
- 既存 slash commands / agmsg
- `~/.claude/skills/goal-feed/references/`（本 skill から参照するが編集はしない）

## 使い方

```
/goal-feed-impl                            # デフォルト探索
/goal-feed-impl docs/tickets20260701/       # 特定 tickets ディレクトリ指定
/goal-feed-impl docs/tickets20260701/ticket_index.md
```
