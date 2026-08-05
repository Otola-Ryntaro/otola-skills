---
name: goal-feed
description: |
  Codex の /goal 機能と Claude Code の並行レビューを組み合わせて、有料サービス品質を目指す実装ループを協調運用するスキル。
  スキル発動時は必ずプランモードへ移行し、agmsg 経由で Codex と report を交換 → いいとこ取りで最終プランを CC 側が Write → Codex に ticket-gen 依頼 → 各 Phase の CC レビュー → 最終監査 → /shime まで面倒を見る。
  発動条件: (1) /goal-feed コマンド (2)「有料品質で実装したい」「Codex と合議してプラン化」「/goal で回す」「ticket-gen から /goal ループ」「Codex と組んで最後まで実装」等のキーワード (3) レポート・アイデア・監査結果を渡されて「Codex と協調して paid-service 品質で最後まで持っていってほしい」と依頼されたとき。
  使用しないケース: 単独の軽微修正 / plan file や ticket が要らない一発タスク / agmsg 未設定で Codex 連携が取れない環境 / 既にチケット完成済みで実装ループだけ回したい場合（→ goal-feed-impl を使う）。
allowed-tools: Read, Write, Edit, Grep, Glob, Bash, Skill, EnterPlanMode, ExitPlanMode, AskUserQuestion, TaskCreate, TaskUpdate
---

# goal-feed — Codex `/goal` × CC 並行レビュー協調スキル

Codex 側 `~/.codex/skills/goal-feed/SKILL.md` の対（受け手＋独立プランナー＋レビュアー）として動作する。

## 目的（Purpose）

Codex の `/goal` 反復実装ループと CC の並行レビューを組み合わせて、**ユーザーが課金してもよいと思える品質**の実装を成立させる。片方の視点だけでは見落とすリスク・仕様漏れ・本質修正でない修正を、両者の独立プランと Phase ごとの diff レビューで潰す。

修正依頼を受けたときは「その場しのぎ」ではなく **根本原因を断つ本質修正** を最優先で狙う。

## いつ Skill 本体を読むか

本 SKILL.md は起動時に読む骨格。**各 Phase の詳細プロトコルは references/ にある**：

- `references/planning-protocol.md` — Phase A〜D（合議→プラン確定→plan file 書き出し）
- `references/review-protocol.md` — Phase E〜G（ticket レビュー / phase 進捗レビュー / 最終監査 / /shime）
- `references/message-schema.md` — agmsg subject / body 完全一覧（Codex 側と対称）
- `references/paid-service-quality-bar.md` — 有料品質チェックリスト

各 Phase の直前に該当 references を Read すること。

## 前提

- **agmsg が設定済み** であること。未設定なら Phase A で誘導する。
- Codex 側でも並行して goal-feed skill を発動させる前提（CC が herdr prompt 経由で `$goal-feed` の起動を指示する）。Codex 側は自身の SKILL.md に従って動くので、CC は subject / セクション構造だけ厳密に合わせれば疎結合で動く。
- 最終プランファイルの authorship は **CC 側**。Codex は report のみ提出する運用（合意済み）。
- ghostty + herdr 環境で動作している前提。Codex の起動・入力操作は herdr 経由で CC 側が行う（下記「herdr 連携」参照）。

## herdr 連携（Codex pane の起動と操作）

ghostty + herdr 環境では、Codex の立ち上げから入力欄への指示投入まで CC 側が herdr CLI で実行する。

### Codex pane の立ち上げ（Phase A で実施）

1. `herdr agent list` で既に codex agent が動いていないか確認。動いていればそれを使う。
2. なければ pane を新規作成して codex を起動する:

   ```bash
   herdr pane split --current --direction right --cwd "$(pwd)" --no-focus
   # 出力に表示される pane ID を控える
   herdr agent start codex --kind codex --pane <PANE_ID>
   ```

3. 起動確認後、`CODEX_AGENT`（agent 名）と `codex_pane_id` をセッション状態に保持する。

### Codex への指示投入（agmsg 送信とセット）

agmsg で Codex にメッセージを送ったら、**必ず続けて** `herdr agent prompt` で Codex の入力欄に「inbox を確認して対応する」旨の指示を投入・送信する（agmsg だけでは Codex は動き出さない）:

```bash
herdr agent prompt codex 'inbox を確認し、goal-feed の依頼に対応して。skill 起動は $agmsg を使うこと'
```

**注意（重要）**:

- prompt テキストの**先頭に `/` を置かない**。先頭 `/` は Codex 側で slash command と解釈され誤動作する。
- Codex 側の Skill 起動コマンドは `$agmsg` `$ticket-gen` 形式（`/agmsg` ではない）。prompt 内で Codex に skill を使わせる指示はこの表記で書く。
- `/goal resume` など slash command を prompt に含める場合は**必ず文末**に置く。

### Phase レビュー後の動作再開

Phase ごとの CC レビューを agmsg で返信したあと、Codex のループを再開させる prompt は**末尾に `/goal resume` を付ける**:

```bash
herdr agent prompt codex 'inbox を確認して。Phase <N> のレビュー結果を返信済み。指摘対応のうえ次へ進んで /goal resume'
```

## 絶対のルール

1. **起動直後、必ず `EnterPlanMode` を呼ぶ。** ユーザーの明示要求。plan mode 中は plan file 以外の Write / Edit をしない。
2. **agmsg 操作はスクリプト経由のみ。** `~/.agents/skills/agmsg/scripts/` 配下を使う。DB/config を直接読み書きしない。
3. **自動レビューの二段ゲート。** 「本 skill がこのセッションで発動済み」かつ「subject が `goal-feed ` で始まる review request」の両方を満たしたときのみ、確認プロンプトなしで即レビュー実行。それ以外は通常配信のまま。
4. **有料サービス品質バーを毎レビューで参照する。** `references/paid-service-quality-bar.md` を検討漏れの起きやすい観点として常に横に置く。
5. **本質修正を優先する。** 症状潰しの diff を見つけたら Critical 相当として扱い、根本原因を提案する。
6. **worktree lifecycle 管理。** 専用 worktree（feature/task 用のリンク worktree）に最初に関与した時点で、unlocked なら `git worktree lock --reason "managed=true goal=<SLUG> owner=cc created=<YYYY-MM-DD>" <path>` で保護する。primary worktree（main/master/develop をチェックアウトしている本体）は**絶対に lock しない**。既に別 reason で locked のものは上書き・unlock しない。lock reason は不変のメタデータであり状態書き換えには使わない。後片付け（unlock → remove）は Phase G の Cleanup Decision Gate（`references/review-protocol.md` G-5b）でのみ、ユーザー明示承認後に行う。

## 状態モデル（セッション内で保持）

以下をセッションメモリ上で保持し、各 Phase 遷移で更新する:

- `activated: true` — このセッションで `/goal-feed` が発動済み
- `TEAM`, `AGENT`, `CODEX_PEER` — agmsg 情報
- `CODEX_AGENT`, `codex_pane_id` — herdr 上の Codex agent 名と pane ID
- `SLUG`, `DATE_YYYYMMDD` — プラン識別子
- `plan_path` — 最終プランファイルパス
- `tickets_dir`, `ticket_index_path`
- `phase_reviews: [ {phase, review_path, verdict, timestamp} ]`

TaskCreate でも同等の進捗を可視化する（各 Phase = 1 タスク）。

---

## 実行フロー（骨格のみ、詳細は references へ）

### Phase A — Establish（Plan Mode 突入 + agmsg 確認）

1. `EnterPlanMode` を呼ぶ。
2. `references/planning-protocol.md` を Read し、Phase A 節に従う。
3. 具体タスク:
   - **herdr で Codex pane を立ち上げる**（「herdr 連携」節参照）。既存 codex agent がなければ pane split → `herdr agent start`。
   - `~/.agents/skills/agmsg/scripts/whoami.sh "$(pwd)" claude-code` で identity 取得。
   - `team.sh` で Codex peer を解決（複数なら `AskUserQuestion`）。
   - `references/paid-service-quality-bar.md` の要点を提示して同意を得る。

### Phase B — Independent Reports（並行 report 作成）

- `references/planning-protocol.md` の Phase B 節に従う。
- Codex に `goal-feed plan review request` を送信し、続けて `herdr agent prompt codex 'inbox を確認し、goal-feed の plan review request に対応して。skill 起動は $agmsg を使うこと'` で Codex を稼働させる。**同時に** CC 側 report を `codex/plans/YYYYMMDD_<slug>_cc_report.md` に Write（plan mode 中の唯一の例外書き込みは plan file のみ、この report は plan file 相当として許可 — ユーザー承認取ってから書き出し）。

  ※ Plan mode 制約下では `codex/plans/*_cc_report.md` の Write は保留し、内容だけ会話中に提示 → Phase D の Write タイミングでまとめて `_cc_report.md` と `_plan.md` を出す方法を推奨。

- Codex report 到着を待つ（agmsg monitor / `inbox.sh` 能動チェック）。

### Phase C — Reconcile（すり合わせ）

- `references/planning-protocol.md` の Phase C 節。
- 両 report を side-by-side 比較、ユーザーと最終プラン草案を握る。

### Phase D — Final Plan File Write & Notify

- `ExitPlanMode` してから:
  - `codex/plans/YYYYMMDD_<slug>_plan.md` を Write（セクション構成は `references/message-schema.md` 参照）。
  - `codex/plans/YYYYMMDD_<slug>_cc_report.md` も同時に Write（履歴として残す）。
  - Codex に `goal-feed plan finalized` を agmsg 送信、ticket-gen 実行を依頼。
  - 続けて `herdr agent prompt codex 'inbox を確認して。plan が確定したので $ticket-gen でチケット化して'` で Codex を稼働させる（先頭 `/` 禁止、`$ticket-gen` 表記）。

### Phase E — Ticket Review

- Codex から `goal-feed ticket review request` 受信で起動。
- `references/review-protocol.md` の Ticket Review 節に従う。
- 結果を `codex/reviews/YYYYMMDD_<slug>_ticket_review.md` へ Write、agmsg で返信。

### Phase F — Phase-by-Phase Review（自動ループ）

- Codex の `/goal` ループから届く `goal-feed phase progress review request` を自動処理。
- `references/review-protocol.md` の Phase Progress Review 節に従う。
- `git diff` 取得 → `/cr`（strict 該当なら `/cr --spec`）→ Write → agmsg 返信。
- 返信後、`herdr agent prompt` で Codex に動作再開を指示する。prompt 末尾に `/goal resume` を付ける（「herdr 連携」節参照）。
- 全 Phase 分繰り返す。

### Phase G — Final Audit + /shime

- `goal-feed final review request` 受信で起動。
- `references/review-protocol.md` の Final Audit 節に従う。
- `/ticket-verify` レポートと phase reviews を集約、最終監査を Write、agmsg 返信。
- **Worktree Cleanup Decision Gate（G-5b）を必ず通す**: 専用 worktree で作業していた場合、integrate / PR / park / abandon をユーザーに選ばせ、integrate / abandon なら承認後に unlock → `git worktree remove`（+ 別承認で `branch -d`）まで完了させる。
- 最後に `/shime` Skill を呼ぶ。

---

## 自動メッセージ処理ルール

セッション内で新規 agmsg メッセージを検知するたびに、subject を評価する:

- `goal-feed plan report from codex` → Phase C を起動
- `goal-feed ticket review request` → Phase E を起動
- `goal-feed phase progress review request` → Phase F を起動
- `goal-feed final review request` → Phase G を起動
- 上記以外の `goal-feed ` prefix → `AskUserQuestion` で扱いを確認
- prefix 不一致 → 通常メッセージとして扱う（skill 側は関与しない）

`activated: false`（本 skill 未発動）の状態では、上記の自動処理は**一切行わない**。誤起動防止の一段目のゲート。

---

## エラー・分岐処理

| 状況 | 動作 |
|------|------|
| agmsg 未設定 | Phase A で `not_joined` を検知 → `/agmsg` の join フローを案内し、完了後 Phase A から再開 |
| Codex peer 不在 | `team.sh` で見つからない場合、Codex 側で `/agmsg spawn codex <name>` または手動 join を依頼 |
| Codex report が返らない | 10 分待って未着 → ユーザーに続行 / 中断を確認、続行なら CC report のみで plan 化（Codex 承認は事後） |
| 最終プランファイル既存 | Write 前に存在チェック、既存があれば `_v2` 等のサフィックスを付けるか上書き承認を取る |
| diff が大きい（>2000 行） | Phase F で要点抽出 + `superpowers:code-reviewer` サブエージェントに委譲 |
| Critical が残り続ける（>3 往復） | Phase F/E で `AskUserQuestion` を挟み、方針転換 / スコープ縮小を提案 |

---

## 完了条件

- 最終プランファイル存在
- ticket_index.md 存在、Critical レビュー指摘 0
- 全 Phase の `/ko` 実行完了、CC レビュー Critical 0
- Codex `/ticket-verify` 合格
- Worktree Cleanup Decision Gate 完了（integrate / PR / park / abandon の判断確定。integrate / abandon なら worktree remove 済み）
- `/shime` で日報作成
- `/goal` を Codex 側で complete マーク済み（agmsg 経由で報告）

---

## 変更しないもの

- `~/.codex/skills/goal-feed*/SKILL.md`
- `/agmsg`, `/ko`, `/cr`, `/next`, `/ticket-verify`, `/shime`, `ticket-gen` の既存挙動
- agmsg の DB / config / team files
- Codex の `/goal` 実装や `~/.codex/goals_1.sqlite`

## 使い方

```
/goal-feed                              # レポート / アイデアを受けて Phase A から
/goal-feed <報告ファイル>                # 特定のレポートを起点に
/goal-feed <URL or 説明>                 # ざっくり方向性を渡す
```

`goal-feed-impl`（短縮版）は「チケット既存、実装ループから」用途。詳細はそちらの SKILL.md へ。
