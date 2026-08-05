# Review Protocol — Phase E〜G

`goal-feed` と `goal-feed-impl` の両方から参照される共通レビュープロトコル。

Phase E（ticket review）→ Phase F（phase-by-phase review、自動ループ）→ Phase G（最終監査 + /shime）の詳細を規定する。

---

## 前提

- CC 側で本 skill（`goal-feed` または `goal-feed-impl`）が発動済み（`activated: true`）。
- agmsg identity（`TEAM` / `AGENT` / `CODEX_PEER`）が Phase A 相当で確定済み。
- 最終プランファイル `codex/plans/${DATE_YYYYMMDD}_${SLUG}_plan.md` が存在（goal-feed-impl の場合は Preflight で確認、無ければ「plan file なし」として動作するが Ticket Review で Acceptance Criteria の突合が甘くなる旨をユーザーに警告）。
- 出力先ディレクトリ `codex/reviews/` は無ければ作成する（`mkdir -p codex/reviews`）。

---

## Phase E — Ticket Review

### E-1. トリガーと入力

Subject: `goal-feed ticket review request`（または `goal-feed-impl ticket review request`）

期待される Body 項目:
- `ticket_index`: `docs/tickets{YYYYMMDD}/ticket_index.md` などのパス
- `tickets-dir`: 上位ディレクトリ
- `final plan`（`goal-feed` 由来のときのみ）: プランファイルパス

### E-2. Read フェーズ

以下を Read:
1. `ticket_index.md`（Phase 構成テーブル / チケット一覧）
2. 各チケットファイル（Glob で列挙してから並列 Read）
3. 最終プランファイル（存在する場合）
4. 直近 commit range: `git log --oneline -20`（背景把握）

### E-3. 評価軸

Critical / Major / Minor の判定基準:

**Critical**（必修正）:
- プランの Acceptance Criteria が 1 個以上チケットに落ちていない
- 有料品質バーの必須項目（例: webhook 署名検証、rate limit、認証境界）が省略されている
- 症状潰しに留まっている（根本原因未処置、再発リスク高）
- チケット粒度が 1 セッション超（S/M/L の L 濫用、真の分割が必要）
- 依存関係の矛盾（Phase 2 が Phase 3 に依存など）
- テストなしで済まされている項目

**Major**（強く推奨）:
- Phase 順序の非効率（並列化余地の見逃し / 直列で回避可能な blocking）
- strict モード自動発動条件（auth / payment / migration 等）にも関わらず strict 明示がないチケット
- 受け入れ条件の記述が曖昧
- ロールバック計画 / feature flag 記述なし

**Minor**（任意）:
- チケットタイトル・命名の曖昧
- 対象ファイルリストの抜け（実装で追加してもよいが記述漏れ）
- 参考リンクや docs 参照の不足

### E-4. Write

出力先: `codex/reviews/${DATE_YYYYMMDD}_${SLUG}_ticket_review.md`

構成:

```markdown
# Ticket Review — {SLUG}

**tickets_dir**: <tickets-dir>
**ticket_index**: <ticket_index-path>
**final plan**: <plan-path or "N/A">
**reviewer**: CC (goal-feed) / {DATE_YYYYMMDD} {HH:MM}

## Verdict

- Critical: <n> 件
- Major: <n> 件
- Minor: <n> 件
- Approve: <APPROVE / REQUEST_CHANGES>

## Critical

| # | チケット | 指摘 | 推奨アクション |
|---|---------|------|---------------|
| 1 | SEC-003 | Webhook 署名検証が受け入れ条件に無い | SEC-003 の Acceptance Criteria に「Stripe-Signature ヘッダ検証」を追加、テスト必須 |

## Major

| # | チケット | 指摘 | 推奨アクション |
|---|---------|------|---------------|

## Minor

| # | チケット | 指摘 | 推奨アクション |
|---|---------|------|---------------|

## Phase 構成レビュー

| Phase | 判定 | 指摘 |
|-------|------|------|

## プラン整合性

- プランの Acceptance Criteria 総数: N
- チケットで拾えている数: M（%）
- 未反映項目リスト
```

### E-5. 返信

Subject: `goal-feed ticket review findings`（`goal-feed-impl` 由来なら `goal-feed-impl ticket review findings`）

Body:
```
review_path: codex/reviews/${DATE_YYYYMMDD}_${SLUG}_ticket_review.md
verdict: REQUEST_CHANGES / APPROVE
critical: <n> / major: <n> / minor: <n>

要旨:
<3〜5 行の要約>

Critical / Major を修正のうえ再送してください。修正不要の Minor は残置可。
```

送信:
```bash
~/.agents/skills/agmsg/scripts/send.sh "$TEAM" "$AGENT" "$CODEX_PEER" "<body>"
```

### E-6. 往復

Codex が修正版を送ってきたら E-2〜E-5 を再度実行。Critical が 0 になるまで繰り返す。往復 3 回で収束しなければ `AskUserQuestion` で「方針転換 / スコープ縮小 / 一部受容」を確認。

### E-7. 収束後の遷移

Critical=0 になったら Codex に「Phase F 実装ループへ進んで OK」を短く agmsg 通知（subject: `goal-feed ticket review findings` 本文に `verdict: APPROVE` を含めて再送で兼ねてもよい）。以降は Phase F の自動待ち受けに入る。

---

## Phase F — Phase-by-Phase Review（自動ループ）

### F-1. トリガーと入力

Subject: `goal-feed phase progress review request`

期待される Body 項目:
- `ticket_index`: パス
- `phase`: `Phase N`
- `status`: `completed` / `in-progress` / `blocked`
- Codex 実施内容の要約
- 検証（commands and results）
- 差分の起点（推奨: base commit SHA / branch）

### F-2. 差分の取得

Body に commit range が明示されていればそれを使う。無ければ:

```bash
# 直近の /ko によるコミット群を推定
git log --format='%H %s' -20
# Phase N の開始コミットを特定するため、直前の /next で完了マークされた commit を境界とする
```

差分:
```bash
git diff <base>..HEAD -- <対象ファイル群>
```

差分行数が 2000 行を超えたら:
- 要点抽出 + 個別ファイル単位で `Read`
- 大きい場合は `superpowers:code-reviewer` サブエージェントに委譲（並列 Agent 呼び出し）

### F-3. Strict 判定

対象チケット（Body に含まれる or Phase N の全チケット）を Read し、以下いずれかがあれば strict:

- チケットファイルに `🔒` マーカー
- 優先度が HIGH
- 本文・対象ファイル・受け入れ条件に含まれるキーワード: `auth`, `clerk`, `supabase auth`, `stripe`, `payment`, `subscription`, `webhook`, `secret`, `token`, `api key`, `webhook secret`, `migration`, `prisma`, `supabase db`, `rls`, `policy`, `schema`

Strict なら `/cr --spec <ticket-path>` を呼ぶ、それ以外は `/cr` を呼ぶ。

### F-4. `/cr` 実行

Skill ツールで:

```
Skill(skill: "cr", args: "--spec <ticket-path>")  # strict の場合
Skill(skill: "cr", args: "")                       # 通常
```

`/cr` の Phase 1（Claude 自己レビュー）+ 必要なら Phase 2（harness / codex / subagent）を実行。Phase 2 のセカンドオピニオンは Codex 側が同時並行で自己 `/cr` をやっているので、CC 側は default で harness-review、コストを避けたければ `--subagent` に切り替える。

### F-4b. スクショ確認（UI を伴う Phase は必須）

Phase の差分に UI（画面表示・スタイル・フロントエンドコンポーネント）が含まれる場合、**実画面のスクリーンショットを必須**とする:

- 保存先規約: `output/goal-feed/${DATE_YYYYMMDD}_phase${N}/NNN_<desc>.png`（web-test と同形式の連番）
- Codex の progress request にスクショパスが含まれていればそれを確認する。無ければ CC 側で `/web-test`（または Playwright）で該当画面を開いて撮影し、上記パスへ保存する
- 撮影したスクショはレビュー md（F-6）の「## Evidence」節にパス列挙で参照する
- ここに保存されたスクショは、セッション終了時の `/shime --visualize` が「本日のスクショ」ギャラリーとして自動収集する（→ visualize-common/references/screenshot-embed.md）
- UI を一切含まない Phase（バックエンドのみ・設定のみ）はスキップしてよいが、レビュー md にその旨を 1 行書く

### F-5. 結果集約

`/cr` の出力（Critical / Major / Minor テーブル）を受け取り、Codex 側の Phase progress request 本文に書かれた自己 `/cr` サマリと突合。**両者一致** の Critical は最優先、**片方だけ**の Critical はもう片方にも要検討として扱う。

### F-6. Write

出力先: `codex/reviews/${DATE_YYYYMMDD}_${SLUG}_phase_${N}_review.md`

構成:

```markdown
# Phase {N} Review — {SLUG}

**ticket_index**: <path>
**phase**: Phase {N}
**base**: <commit sha or branch>
**HEAD**: <commit sha>
**reviewer**: CC (goal-feed) / {DATE_YYYYMMDD} {HH:MM}

## Verdict

- Critical: <n>
- Major: <n>
- Minor: <n>
- Verdict: APPROVE / REQUEST_CHANGES

## Acceptance Criteria 突合（strict 時のみ）

| # | 受け入れ条件 | 実装場所 | ステータス |
|---|------------|---------|----------|
| 1 | ... | lib/x.ts:42 | ✅ 充足 |

## Critical

| # | ファイル | 行 | 指摘元 | 内容 | 推奨アクション |
|---|---------|-----|--------|------|---------------|

## Major

| # | ファイル | 行 | 指摘元 | 内容 | 推奨アクション |
|---|---------|-----|--------|------|---------------|

## Minor

## Evidence

<!-- UI を伴う Phase は必須（F-4b）。スクショパスを列挙。UI 無し Phase は「UI 変更なしのためスクショなし」と 1 行 -->
- output/goal-feed/{DATE_YYYYMMDD}_phase{N}/001_<desc>.png — <何が確認できるか 1 文>

## 有料品質バー観点での追加指摘

<references/paid-service-quality-bar.md の観点で当該 diff に対する所見。特に対象領域が payments / auth / migration の場合に強く記述>

## Codex 自己 /cr との差異

| 観点 | Codex 側 | CC 側 | 一致 / 差 |
|------|---------|-------|-----------|
```

### F-7. 返信

Subject: `goal-feed phase progress review findings`

Body:
```
review_path: codex/reviews/${DATE_YYYYMMDD}_${SLUG}_phase_${N}_review.md
phase: Phase {N}
verdict: REQUEST_CHANGES / APPROVE
critical: <n> / major: <n> / minor: <n>

要旨:
<3〜6 行>

次 Phase 進行前に Critical / Major を修正してください。
```

送信は `send.sh` 経由。

### F-8. 往復と収束

Critical あり → Codex 修正 → 新しい `phase progress review request` が届くはず → F-1 から再実行。

Critical=0 で APPROVE → Codex は `/next` へ進む想定。CC 側は次の `phase progress review request` を待つ待機状態に戻る。

### F-9. Phase F の並行性

CC は他のタスクを兼任できる。Phase F は idempotent で、複数 Phase の review request が来ても順次処理する。ただし同時多発時（>2 件同時）はユーザーに合流を促す（`AskUserQuestion`）。

### F-10. Long-running セッション対策

セッションが長引くと Monitor が停止する場合がある。Phase F 待機中に定期的に `inbox.sh` を呼び、取りこぼしがないか確認する。

---

## Phase G — Final Audit + /shime

### G-1. トリガー

Subject: `goal-feed final review request`

期待される Body 項目:
- `ticket_index`: パス
- `verification`: `/ticket-verify` レポートパス（例: `codex/${YYYYMMDD}_verification_report.md`）
- 全 Phase 完了サマリ
- 残リスク列挙

### G-2. 集約 Read

- `/ticket-verify` レポート
- Phase F で書いた各 `phase_${N}_review.md`
- 最終プランファイル
- `ticket_index.md`（全チケットが ✅ か確認）
- `git log --oneline <plan finalized 通知以降>`

### G-3. 最終監査観点

以下を必ずチェック:

1. **プラン Acceptance Criteria vs 実装 diff の完全突合**
   - 未実装項目 0 か
2. **有料品質バーの各観点（`references/paid-service-quality-bar.md`）** に対する最終所見
   - Security / Data / UX / Observability / Testing / Payments / Operational
3. **回帰リスク**
   - 変更外の既存機能が壊れていないか（テスト網羅、既存 E2E の pass）
4. **Phase F で残した Minor / Major** の後始末
5. **リリース前チェックリスト**
   - Env vars / secrets / feature flag / monitoring / on-call docs

### G-4. Write

出力先: `codex/reviews/${DATE_YYYYMMDD}_${SLUG}_final_audit.md`

構成:

```markdown
# Final Audit — {SLUG}

**ticket_index**: <path>
**plan_file**: <plan-path>
**verification_report**: <path>
**auditor**: CC (goal-feed) / {DATE_YYYYMMDD} {HH:MM}

## Verdict

- 総合: PASS / CONDITIONAL PASS / FAIL
- 残 Critical: <n>
- 残 Major: <n>
- 残 Minor: <n>

## 1. Plan Acceptance Criteria vs 実装

| # | 受け入れ条件 | 実装場所 | ステータス |
|---|------------|---------|----------|

## 2. 有料品質バー観点

### Security
### Data Integrity
### UX Polish
### Observability
### Testing
### Payments（該当時）
### Operational

## 3. 回帰・既存機能への影響

## 4. Phase F 残課題の状態

## 5. リリース前チェックリスト

- [ ] Env / Secrets 準備完了
- [ ] Feature flag / rollout 計画
- [ ] Monitoring / alert 設定
- [ ] On-call runbook 更新

## 6. 総合判定と推奨アクション
```

### G-5. 返信

Subject: `goal-feed final review findings`

Body:
```
final_audit_path: codex/reviews/${DATE_YYYYMMDD}_${SLUG}_final_audit.md
verdict: PASS / CONDITIONAL PASS / FAIL

要旨:
<5〜10 行>

CC 側はこの後 /shime に移ります。
```

### G-5b. Worktree Cleanup Decision Gate（必須 — /shime より前に実行）

goal の作業が専用 worktree（feature/task 用のリンク worktree）で行われた場合、**このゲートを飛ばして G-6 に進んではならない**。worktree を作った側が最後まで面倒を見る、が本ゲートの契約（作成側と完了側の契約断絶を防ぐ）。

**対象外（絶対に触らない）**: primary worktree（リポジトリ本体、main/master/develop 等をチェックアウトしている作業ツリー）。lock / unlock / remove のいずれも行わない。

1. **対象特定**: `git worktree list --porcelain` で対象 worktree の exact path / branch / locked 状態を取得する。
2. **ユーザー選択**（`AskUserQuestion`、4 択）:
   - `integrate` — main へ統合済み（または今統合する）。worktree と branch を後片付け
   - `PR` — PR を出して worktree は保持（lock 維持）
   - `park` — 作業保留で worktree 保持（lock 維持）
   - `abandon` — 成果破棄で後片付け
3. **integrate / abandon の場合のみ**、以下の順序を厳守（順序の入れ替え禁止）:
   1. 検証: dirty なし（`git status --porcelain`）／integrate なら main にマージ済み（`git merge-base --is-ancestor HEAD main`）／exact path が想定と一致／その worktree で稼働中プロセスなし
   2. 実行予定コマンドをそのまま表示: `git worktree unlock <exact-path>` → `git worktree remove <exact-path>`
   3. **ユーザーの明示承認を取る**（承認前の unlock は禁止）
   4. 承認後、手順 1 を**再検証**
   5. `git worktree unlock <exact-path>` → **直ちに** `git worktree remove <exact-path>`
   6. remove 失敗時は best-effort で即 `git worktree lock <exact-path>` し直し、「要手動確認」とユーザーに報告して停止
4. **branch 削除は別承認**: remove 成功後、`git branch -d <branch>` を別途提示し、承認を得てから実行する。
5. **PR / park の場合**: lock を維持したまま終了し、/shime の Plans.md 引き継ぎに「park 中 worktree: <path>（branch, 理由）」を必ず記録する。
6. `rm -rf` での worktree 削除は**いかなる場合も禁止**。必ず `git worktree remove` を使う。
7. 判断に迷う worktree（unmanaged / 別 reason で locked / detached）は削除候補にせず「要確認」としてユーザーに列挙するだけに留める。

### G-6. /shime 起動

Skill ツールで `/shime` を呼ぶ:

```
Skill(skill: "shime")
```

これで:
- daily_report/YYYY-MM-DD_<title>.md を作成
- Plans.md への引き継ぎを対話的に確認
- 可視化オプション（--visualize）を確認

`/shime` 完了後、Codex 側で `/goal` を complete マークしてもらうよう最終 agmsg で促す:

```
Subject: goal-feed session closed
Body: /shime 完了。日報 <path>。Codex 側で /goal を complete にしてください。
```

### G-7. Phase G の総括

- TaskUpdate で全 Phase を completed に。
- ユーザーに以下を短く報告:
  - 最終監査結果（PASS / FAIL）
  - 監査レポートパス
  - 日報パス
  - 次アクション（リリース手順、追跡課題）

---

## Cross-Phase 共通事項

### 出力ファイルの命名規則

- `codex/plans/${DATE_YYYYMMDD}_${SLUG}_plan.md` — 最終プラン
- `codex/plans/${DATE_YYYYMMDD}_${SLUG}_cc_report.md` — CC 側 report 履歴
- `codex/reviews/${DATE_YYYYMMDD}_${SLUG}_ticket_review.md`
- `codex/reviews/${DATE_YYYYMMDD}_${SLUG}_phase_${N}_review.md`
- `codex/reviews/${DATE_YYYYMMDD}_${SLUG}_final_audit.md`

### `SLUG` / `DATE_YYYYMMDD` の引き継ぎ

`goal-feed-impl` から呼ばれた場合は、Preflight で `ticket_index.md` からプランパスを推定し、そこから SLUG / DATE を抽出。抽出できない場合は `AskUserQuestion` で確認。

### agmsg 送受信の共通ルール

- 送信は必ず `send.sh` 経由。DB / files を直接触らない。
- 受信は agmsg monitor が push で配信。念のため 3〜5 turn ごとに `inbox.sh` を能動チェック。
- Subject の strict prefix マッチで review request 判定。曖昧なら AskUserQuestion。

### 「本質修正」観点の共通判定

diff レビュー時、以下があれば Critical 相当:

- ガード条件で症状だけ抑えている（例外を catch して握りつぶし、ログのみ）
- 定数を書き換えて根本原因を回避（config で本来の閾値を無視するだけ）
- テストを skip / delete で緑にした
- 再発する条件が temperature-dependent（並行アクセス / 特定 timing）で、その条件下のテストが無い

これらは Codex に「症状潰しに見える。根本の原因は X ではないか」と Push back を返す。
