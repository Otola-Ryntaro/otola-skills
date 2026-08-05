# Planning Protocol — Phase A〜D

Codex と CC で並行に plan を立て、いいとこ取りで最終プランファイルを CC 側が Write するまでの詳細プロトコル。

対応するのは SKILL.md の Phase A〜D。Phase E 以降は `review-protocol.md` に切り出してある。

---

## Phase A — Establish（Plan Mode 突入 + agmsg 確認）

### A-1. Plan Mode 突入

`EnterPlanMode` を必ず呼ぶ。ユーザーの明示ルール。ここから Phase D で `ExitPlanMode` するまで、plan file と会話上の草案以外は書き出さない。

### A-2. agmsg identity 確認

```bash
~/.agents/skills/agmsg/scripts/whoami.sh "$(pwd)" claude-code
```

分岐:

- **Single identity**: `agent=<name> teams=<t1,...>` — そのまま `AGENT` / `TEAMS` を握って A-3 へ。
- **Multiple identities**: `AskUserQuestion` でどの agent 名で振る舞うか確認。
- **Not joined**: ユーザーに join を促す。ここで skill を一時中断し、`/agmsg` の join フローを案内。完了したら本 skill を再開する。
- **Suggest**: 過去に別 project で使った候補名を提示、reuse するか新規かを確認。

### A-3. Codex peer 解決

各 TEAM について:

```bash
~/.agents/skills/agmsg/scripts/team.sh <TEAM>
```

出力から `type=codex` のメンバーを列挙:

- **1 名**: 自動採用 → `CODEX_PEER=<name>`
- **複数**: `AskUserQuestion` で「今回の相方はどの Codex にする？」を選択
- **0 名**: ユーザーに「Codex 側で `/agmsg spawn codex <name>` するか、既存 Codex セッションに `/agmsg actas <name>` で参加してもらってください」と案内。到着まで待つ or 中断。

セッション内で `CODEX_PEER` を固定（同一セッション中は問い直さない）。

### A-4. paid-service quality bar の握り込み

`references/paid-service-quality-bar.md` を Read し、以下をユーザーに提示:

- Security / Data integrity / UX polish / Observability / Testing / Payments 固有 / Operational の各観点
- 「このプロジェクトで特に厳しくしたい観点は？」を `AskUserQuestion` で確認（複数選択可）
- 「対象は課金機能を含むか、含まないか」で Payments 系の要否を判定
- 修正依頼の場合: 「二度と再発しない本質修正を目指す」ことをユーザーに宣言し、症状潰しは避ける方針を確認

### A-5. SLUG と DATE の確定

- `SLUG`: ユーザーに短縮名（英小文字 + `-` 区切り、例: `payments-retry`）を確認、`AskUserQuestion` の「Other」で自由入力可。
- `DATE_YYYYMMDD`: `date +%Y%m%d` の結果を採用。
- 以後、`codex/plans/${DATE_YYYYMMDD}_${SLUG}_plan.md` を最終出力先とする。

---

## Phase B — Independent Reports

### B-1. Codex への plan review request 送信

`references/message-schema.md` の「Plan Review Request（Outbound）」テンプレを使い:

```bash
~/.agents/skills/agmsg/scripts/send.sh "$TEAM" "$AGENT" "$CODEX_PEER" "<body>"
```

Body には以下を含める:
- 対象（repo / 現ブランチ / CWD）
- 入力（source report path / 依頼概要 / 修正依頼なら現象と再現条件）
- CC 側の初期方針の要約（短く 5〜8 行）
- 観点（有料品質、本質修正、受け入れ条件、テスト方針、セキュリティ / データ、ticket-gen 粒度）
- 締め: 「Codex 側でも独立した plan report を作成し `goal-feed plan report from codex` の subject で返信してください」

### B-2. CC 側 report のインタビュー

`AskUserQuestion` を 1〜3 回に絞って以下を握る（多くても 4 質問まで）:

1. **User value / 何が変わったら成功か** — 定量指標があれば必ず引き出す
2. **Non-negotiables** — 落としてはいけない条件（security / データ / 既存機能）
3. **Root-cause direction** — 修正依頼の場合、現在の仮説とその根拠
4. **Risk tolerance** — 破壊的変更の許容度、リリース時期の制約

追加情報が必要なら repo を Explore agent で調査（並列で最大 3 まで）。

### B-3. CC 側 report ドラフトを会話で提示

plan mode 中は Write を控え、会話中に以下の構成でドラフトを提示:

```
# <Title>（暫定）

## User Value / Success Metrics
## Root-Cause Direction（or 本質修正の狙い）
## Suggested Scope (In / Out)
## Non-Negotiables
## Risks & Compatibility
## Suggested Acceptance Criteria（受け入れ条件の下書き）
## Suggested Ticket Breakdown & Phase Order（軽く）
## Verification Strategy
```

これを最終プラン→ticket-gen へ流し込む前提の粒度で書く。詰めきれない箇所は `Uncertain:` として明示。

### B-4. Codex report 到着待ち

`~/.agents/skills/agmsg/scripts/inbox.sh $TEAM $AGENT` で能動チェック、または agmsg monitor が push する。Subject `goal-feed plan report from codex` を待つ。

- 3 分ごとにチェック（Bash で軽く sleep）— 大きな計算を挟まないなら自然に turn 単位で確認される。
- 10 分経過しても到着しない場合はユーザーに続行判断を仰ぐ。続行時: CC report のみで plan 化し、事後承認ルートに切り替え。

---

## Phase C — Reconcile（すり合わせ）

### C-1. Codex report を Read

Codex が本文にインラインで書いた場合は message text から、ファイルパスで返してきた場合はそのファイルを Read。

### C-2. Side-by-side 比較

以下を含む比較テーブルを会話で提示:

| 項目 | CC 案 | Codex 案 | 差分 / 採用方針 |
|------|-------|----------|-----------------|
| Scope | ... | ... | いいとこ取り: ... |
| Root-cause | ... | ... | Codex の hypothesis を採用、CC の追加ガードを重ねる |
| Acceptance criteria | ... | ... | 統合 |
| Phase 順 | ... | ... | Codex 順 + Phase 2 に CC のテスト追加を挿入 |
| Risk | ... | ... | 両者列挙 |

差分の中身は「本質修正か」「有料品質を毀損しないか」の 2 軸で採否を判断する。

### C-3. ユーザーとの最終合意

`AskUserQuestion` で採否が割れる項目を確認（多くて 2 問）。それ以外は CC 側の推奨として提示 → ユーザーが押し戻したら会話で調整。

### C-4. 最終プラン草案の握り込み

草案テキストを会話中に清書し、次セクションで Write する形に整える。

---

## Phase D — Final Plan File Write & Notify

### D-1. Plan mode 離脱

`ExitPlanMode` を呼ぶ。plan file だけは既に承認済み計画に基づく成果物として、以降通常モードで Write する。

### D-2. Plan file の Write

パス: `codex/plans/${DATE_YYYYMMDD}_${SLUG}_plan.md`

**必須セクション**（Codex 側 SKILL.md と厳密一致）:

```markdown
# <Title>

## Goal

## Paid-Service Quality Bar

## Current State

## Final Scope

## Implementation Strategy

## Acceptance Criteria

## Risks And Guardrails

## Test And Verification Plan

## Claude Code Report Summary

## Codex Report Summary

## Reconciled Decisions

## Ticketing Notes
```

各セクションの中身の指針:

- **Goal**: 何を達成したら成功か、定量指標。
- **Paid-Service Quality Bar**: `references/paid-service-quality-bar.md` から本件で厳格化する観点を抜粋。
- **Current State**: 現状把握（コード / インフラ / 既知のバグ / 制約）。
- **Final Scope**: In / Out を明示。
- **Implementation Strategy**: 大枠のアプローチ、根本原因への当て方。
- **Acceptance Criteria**: 実装完了の判定条件（テスト可能な粒度）。
- **Risks And Guardrails**: 事故ポイントと予防策（feature flag、rollback plan、監視強化）。
- **Test And Verification Plan**: unit / integration / E2E の各層で何を追加するか。
- **Claude Code Report Summary**: B-3 で作った CC report の要約。
- **Codex Report Summary**: B-4 で受け取った Codex report の要約。
- **Reconciled Decisions**: Phase C-2 のテーブルとその決定。
- **Ticketing Notes**: ticket-gen が拾いやすいように、Phase 分割と各チケットのラフな輪郭。

同時に `codex/plans/${DATE_YYYYMMDD}_${SLUG}_cc_report.md` を Write（B-3 の CC report を履歴として残す）。

### D-3. 既存ファイル衝突対策

Write 前に存在チェック:

```bash
ls codex/plans/${DATE_YYYYMMDD}_${SLUG}_plan.md 2>/dev/null
```

- 存在しない → そのまま Write
- 存在する → `AskUserQuestion` で「上書き」「サフィックス `_v2` 付与」「別 SLUG」を選択

### D-4. Codex への完了通知

Subject: `goal-feed plan finalized`

Body:
```
plan_path: codex/plans/${DATE_YYYYMMDD}_${SLUG}_plan.md
cc_report_path: codex/plans/${DATE_YYYYMMDD}_${SLUG}_cc_report.md

最終プランを Write しました。以下をお願いします:
- /ticket-gen codex/plans/${DATE_YYYYMMDD}_${SLUG}_plan.md
- 完了後、goal-feed ticket review request で CC にレビュー依頼を投げてください。
```

送信コマンド:
```bash
~/.agents/skills/agmsg/scripts/send.sh "$TEAM" "$AGENT" "$CODEX_PEER" "<body>"
```

### D-5. Phase A〜D の総括

- TaskUpdate で Phase A〜D を completed に。
- ユーザーに「plan file の場所」「Codex に ticket-gen 依頼を投げた」「以降は review request 到着で自動起動」を短く報告。
- Phase E 以降は `references/review-protocol.md` を参照。

---

## トラブルシュート早見表（Phase A〜D）

| 症状 | 想定原因 | 対応 |
|------|----------|------|
| whoami.sh が `not_joined` | この project で未 join | `/agmsg` の join フローへ誘導 |
| team.sh で codex が見えない | Codex 側が join していない / spawn していない | ユーザー経由で Codex 側の join を依頼 |
| Codex report 未着（10 分超） | Codex 側が忙しい / エラー | 続行判断を仰ぐ。CC 単独で plan 化 + 事後 Codex 承認ルート |
| plan file 上書き警告 | 同日同 SLUG で以前作成済み | `_v2` サフィックスまたは新 SLUG |
| 有料品質項目に迷い | ユーザー要件不明 | `references/paid-service-quality-bar.md` の該当節を提示し `AskUserQuestion` で個別確認 |
| Phase B で Codex 側が strong opinion で押してきた | 対称的レビュー健全 | 内容で判断、Root-cause / User value の観点で軍配。譲れないところは reason を明記して agmsg 返信 |
