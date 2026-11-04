---
name: goal-feed
description: |
  Codex の /goal 機能と Claude Code の並行レビューを組み合わせて、有料サービス品質を目指す実装ループを協調運用するスキル。
  スキル発動時は必ずプランモードへ移行し、agmsg 経由で Codex と report を交換 → いいとこ取りで最終プランを CC 側が Write → Codex に ticket-gen 依頼 → 各 Phase の CC レビュー → 最終監査 → /shime まで面倒を見る。
  発動条件: (1) /goal-feed コマンド (2)「有料品質で実装したい」「Codex と合議してプラン化」「/goal で回す」「ticket-gen から /goal ループ」「Codex と組んで最後まで実装」等のキーワード (3) レポート・アイデア・監査結果を渡されて「Codex と協調して paid-service 品質で最後まで持っていってほしい」と依頼されたとき。
  使用しないケース: 単独の軽微修正 / plan file や ticket が要らない一発タスク / agmsg 未設定で Codex 連携が取れない環境 / 既にチケット完成済みで実装ループだけ回したい場合（→ goal-feed-impl を使う）/ Orca の外で動かすとき（Orca のターミナルで起動し直す）。
allowed-tools: Read, Write, Edit, Grep, Glob, Bash, Skill, EnterPlanMode, ExitPlanMode, AskUserQuestion, TaskCreate, TaskUpdate
---

# goal-feed — Codex `/goal` × CC 並行レビュー協調スキル

Codex 側 `~/.codex/skills/goal-feed/SKILL.md` の対（受け手＋独立プランナー＋レビュアー）として動作する。

## 目的（Purpose）

Codex の `/goal` 反復実装ループと CC の並行レビューを組み合わせて、**ユーザーが課金してもよいと思える品質**の実装を成立させる。片方の視点だけでは見落とすリスク・仕様漏れ・本質修正でない修正を、両者の独立プランと Phase ごとの diff レビューで潰す。

修正依頼を受けたときは「その場しのぎ」ではなく **根本原因を断つ本質修正** を最優先で狙う。

## いつ Skill 本体を読むか

本 SKILL.md は起動時に読む骨格。**各 Phase の詳細プロトコルは references/ にある**：

- `references/orca-protocol.md` — worktree・agmsg の名前・ペイン入力・待機・片付け（Phase A の前に必ず読む）
- `references/planning-protocol.md` — Phase A〜D（合議→プラン確定→plan file 書き出し）
- `references/review-protocol.md` — Phase E〜G（ticket レビュー / phase 進捗レビュー / 最終監査 / /shime）
- `references/message-schema.md` — agmsg subject / body 完全一覧（Codex 側と対称）
- `references/paid-service-quality-bar.md` — 有料品質チェックリスト

各 Phase の直前に該当 references を Read すること。

## 前提

- **agmsg が設定済み** であること。未設定なら Phase A で誘導する。
- Codex 側でも並行して goal-feed skill を発動させる前提（CC が `orca agent launch --prompt` のブリーフで `$goal-feed` の起動を指示する）。Codex 側は自身の SKILL.md に従って動くので、CC は subject / セクション構造だけ厳密に合わせれば疎結合で動く。
- 最終プランファイルの authorship は **CC 側**。Codex は report のみ提出する運用（合意済み）。
- Orca のターミナルで動作している前提。worktree の作成と Codex の起動は CC 側が `orca` で行う（下記「Orca 連携」参照）。

## Orca 連携（worktree・Codex の起動と操作）

手順の正本は `references/orca-protocol.md`。要点は次のとおり。

- Phase A で CC が `orca worktree create` で worktree を作り、`orca agent launch --surface terminal` で Codex を起動する。orca-master 配下なら既に揃っているので作らない。
- agmsg の名前は `<slug>-cc`・`<slug>-codex` を CC が両方登録し、以後 `whoami.sh` を使わない。
- agmsg で送ったら、必ず続けて `orca terminal send` で相手を起こす（以下「起こす」と書く）。Codex も同じ方法で CC を起こす。
- 送る文の先頭に `/` を置かない。Codex のスキルは `$agmsg` `$ticket-gen` と書く。`/goal resume` は文末に置く。
- Phase レビューの返信後は、末尾に `/goal resume` を付けた文で Codex を起こす。

## 絶対のルール

1. **起動直後、必ず `EnterPlanMode` を呼ぶ。** ユーザーの明示要求。plan mode 中は plan file 以外の Write / Edit をしない。
2. **agmsg 操作はスクリプト経由のみ。** `~/.agents/skills/agmsg/scripts/` 配下を使う。DB/config を直接読み書きしない。
3. **自動レビューの二段ゲート。** 「本 skill がこのセッションで発動済み」かつ「subject が `goal-feed ` で始まる review request」の両方を満たしたときのみ、確認プロンプトなしで即レビュー実行。それ以外は自動処理しない。
4. **有料サービス品質バーを毎レビューで参照する。** `references/paid-service-quality-bar.md` を検討漏れの起きやすい観点として常に横に置く。
5. **本質修正を優先する。** 症状潰しの diff を見つけたら Critical 相当として扱い、根本原因を提案する。
6. **停滞は自動で回復する。** Codex の手が止まったのに返信がないときは、ユーザーの指示を待たず画面を読んで起こし直す。ユーザーの再送指示なしでループが続くことが目標。詳細は「自己修復プロトコル」節。
7. **worktree は CC が作り、CC が片付ける。** 作成は `orca worktree create` だけ。`git worktree add`・`git worktree lock` は使わない。primary worktree は片付けの対象にしない。後片付けは Phase G の Cleanup Decision Gate（`references/review-protocol.md` G-5b）でのみ行い、削除はユーザーが `!` で実行する。

## 状態モデル（セッション内で保持）

以下をセッションメモリ上で保持し、各 Phase 遷移で更新する:

- `activated: true` — このセッションで `/goal-feed` が発動済み
- `TEAM`, `AGENT`, `CODEX_PEER` — agmsg 情報
- `task_worktree`, `worktree_id` — Orca worktree のパスと ID
- `codex_handle`, `cc_handle` — Codex と CC のターミナルハンドル
- `SLUG`, `DATE_YYYYMMDD` — プラン識別子
- `plan_path` — 最終プランファイルパス
- `tickets_dir`, `ticket_index_path`
- `phase_reviews: [ {phase, review_path, verdict, timestamp} ]`

TaskCreate でも同等の進捗を可視化する（各 Phase = 1 タスク）。

さらに、同じ内容を `.goalfeed/state.json` へ**永続化**する（下記「自己修復プロトコル」参照）。セッションメモリはコンテキスト要約や中断で失われうるため、Phase 遷移・agmsg 送受信のたびにこのファイルを更新し、再開時はまず state.json から状態を再構築する。

---

## 自己修復プロトコル（停滞検知・状態永続化）

Codex の停滞やバックグラウンド監視の停止からの復旧をユーザーに頼らないよう、ループを自己修復型にする。

### S-1. 状態の永続化（.goalfeed/state.json）

プロジェクトルートの `.goalfeed/state.json` に以下を保持し、変化のたびに上書きする:

```json
{
  "slug": "<SLUG>",
  "phase": "F",
  "team": "<TEAM>",
  "agmsg_names": { "cc": "<SLUG>-cc", "codex": "<SLUG>-codex" },
  "task_worktree": "<絶対パス>",
  "worktree_id": "<repoId>::<path>",
  "codex_handle": "<handle>",
  "cc_handle": "<handle>",
  "last_sent": { "subject": "...", "at": "2026-08-08T10:00:00+09:00" },
  "last_received": { "subject": "...", "at": "..." },
  "stall_count": 0,
  "phase_reviews": [ { "phase": 1, "verdict": "APPROVE", "review_path": "..." } ]
}
```

- `.goalfeed/` は `.gitignore` に追加を提案（コミット対象にしない）
- セッション再開時（/saikai 含む）は state.json があれば読み、会話コンテキストより優先して現在地を復元する

### S-2. 停滞検知と起こし直し

時間の経過ではなく、Codex の手が止まったかどうかで判定する。`orca terminal wait --for tui-idle` が戻ったときの分岐は `references/orca-protocol.md` の 7 節に従う。

- **idle で新着なし** → 画面を読み、1 回起こし直して `stall_count` を +1。**ユーザーに確認しない**
- **タイムアウト** → Codex は作業中。停滞に数えず待ち直す
- **新着あり** → `stall_count` を 0 にリセット
- `stall_count >= 3`（3 連続停滞）で初めてユーザーにエスカレーション

### S-3. 待機はブロッキング型・冪等（コンテキストを浪費しない）

Codex は数時間単位で作業を続けることがある。その間の**前面での定期ポーリングは禁止**（1 回ごとの出力が会話履歴に蓄積し、レビューに使うべきコンテキストを侵食する）。

- 待機は `orca terminal wait` を run_in_background で 1 本だけ起動する。Codex から起こされたら、待機の終了を待たずに処理する
- **出力衛生**: 復帰後に読むのは保存した inbox の該当メッセージのみ。Codex の作業把握は画面全文ではなく、届いた本文と成果ファイル（diff・レビュー対象）を直接 Read する
- 待機が kill されても、復旧は冪等チェック（state.json → `inbox.sh` 1 回 → 差分比較 → 行動 → state.json 更新）の再実行 1 回で済む設計を保つ

### S-4. 人間エスカレーションキュー

ユーザーの判断が本当に必要な事項（方針転換・スコープ変更・3 連続停滞）は `.goalfeed/needs-human.md` に文脈と選択肢付きで追記し、**ループ全体を止めずに**他のブロックされていない作業（レビュー準備・ドキュメント整備）を続ける。ユーザーが戻ったらまとめて確認する。

### S-5. APPROVE の根拠必須化

Phase F / G の APPROVE 判定には、検証根拠（実行したテストコマンドと結果・ビルド出力・動作確認手順のいずれか）の引用を必須とする。根拠を提示できない場合は APPROVE を出さず、検証手順の実行から行う。

---

## 実行フロー（骨格のみ、詳細は references へ）

### Phase A — Establish（Plan Mode 突入 + agmsg 確認）

1. `EnterPlanMode` を呼ぶ。
2. `references/planning-protocol.md` を Read し、Phase A 節に従う。
3. 具体タスク:
   - `references/orca-protocol.md` を Read し、前提チェックと配置の判定を行う。
   - SLUG を確定し、worktree の作成・agmsg の名前登録・Codex の起動を行う（同 3〜5 節）。
   - `references/paid-service-quality-bar.md` の要点を提示して同意を得る。

### Phase B — Independent Reports（並行 report 作成）

- `references/planning-protocol.md` の Phase B 節に従う。
- Codex に `goal-feed plan review request` を送信し、続けて Codex を起こす。**同時に** CC 側 report の内容を会話中に提示する（plan mode 中はファイルに書き出さない）。`codex/plans/YYYYMMDD_<slug>_cc_report.md` は Phase D で `_plan.md` と一緒に Write する。

- Codex report 到着を待つ（`orca-protocol.md` 7 節）。

### Phase C — Reconcile（すり合わせ）

- `references/planning-protocol.md` の Phase C 節。
- 両 report を side-by-side 比較、ユーザーと最終プラン草案を握る。

### Phase D — Final Plan File Write & Notify

- `ExitPlanMode` してから:
  - `<task_worktree>/codex/plans/YYYYMMDD_<slug>_plan.md` を Write（セクション構成は `references/message-schema.md` 参照）。
  - `codex/plans/YYYYMMDD_<slug>_cc_report.md` も同時に Write（履歴として残す）。
  - Codex に `goal-feed plan finalized` を agmsg 送信、ticket-gen 実行を依頼。
  - 続けて `plan が確定したので $ticket-gen でチケット化して` を添えて Codex を起こす。

### Phase E — Ticket Review

- Codex から `goal-feed ticket review request` 受信で起動。
- `references/review-protocol.md` の Ticket Review 節に従う。
- 結果を `codex/reviews/YYYYMMDD_<slug>_ticket_review.md` へ Write、agmsg で返信。

### Phase F — Phase-by-Phase Review（自動ループ）

- Codex の `/goal` ループから届く `goal-feed phase progress review request` を自動処理。
- `references/review-protocol.md` の Phase Progress Review 節に従う。
- `git diff` 取得 → `/cr`（strict 該当なら `/cr --spec`）→ Write → agmsg 返信。
- 返信後、末尾に `/goal resume` を付けた文で Codex を起こす（「Orca 連携」節参照）。
- 全 Phase 分繰り返す。

### Phase G — Final Audit + /shime

- `goal-feed final review request` 受信で起動。
- `references/review-protocol.md` の Final Audit 節に従う。
- `/ticket-verify` レポートと phase reviews を集約、最終監査を Write、agmsg 返信。
- **Worktree Cleanup Decision Gate（G-5b）を必ず通す**: 先に Codex を閉じ、integrate / PR / park / abandon をユーザーに選ばせる。integrate / abandon なら `orca worktree rm` のコマンドを提示し、ユーザーが `!` で実行する。
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
| Orca の外にいる | `$ORCA_TERMINAL_HANDLE` が空 → Orca のターミナルで起動し直すようユーザーに伝えて停止 |
| Codex report が返らない | 自己修復プロトコル S-2 に従う。3 連続停滞でユーザーに続行 / 中断を確認、続行なら CC report のみで plan 化（Codex 承認は事後） |
| 最終プランファイル既存 | Write 前に存在チェック、既存があれば `_v2` 等のサフィックスを付けるか上書き承認を取る |
| diff が大きい（>2000 行） | Phase F で要点抽出 + `feature-dev:code-reviewer` エージェントに委譲 |
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
