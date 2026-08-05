# Message Schema — agmsg subject / body 完全一覧

Codex 側 `~/.codex/skills/goal-feed/SKILL.md` および `~/.codex/skills/goal-feed-impl/SKILL.md` と**厳密に対称**であること。

すべての subject / body 形式はここに集約。SKILL.md や他の references はここへ back-reference する。

---

## Subject prefix 規約

- `goal-feed ` — フルフロー用（Phase A から Phase G まで）
- `goal-feed-impl ` — 短縮版用（Phase E 以降のみ）

**subject の最初のトークンで prefix を厳密判定**（`goal-feed` の後ろが space か `-impl ` かを見る）。それ以外の派生 prefix は誤動作を防ぐため自動処理しない。

---

## outbound（CC → Codex）

### 1. Plan Review Request

**トリガー**: Phase B-1
**Subject**: `goal-feed plan review request`
**Body テンプレ**:

```text
件名: goal-feed plan review request

対象: <repo path / branch>
入力: <source report or brief>

CC側の初期方針:
<short summary 5-8 行>

重視してほしい観点:
- 有料サービスとしてユーザーがお金を払える品質に届くか
- その場限りではなく本質修正になっているか
- 受け入れ条件とテスト方針に抜けがないか
- セキュリティ、データ安全、互換性、運用上のリスク
- ticket-genに渡せる粒度まで計画が具体化されているか

Codex 側でも独立した plan report を作り、subject
`goal-feed plan report from codex`
で返信してください。
```

### 2. Plan Finalized（Codex への完了通知 + ticket-gen 依頼）

**トリガー**: Phase D-4
**Subject**: `goal-feed plan finalized`
**Body テンプレ**:

```text
件名: goal-feed plan finalized

plan_path: codex/plans/{YYYYMMDD}_{SLUG}_plan.md
cc_report_path: codex/plans/{YYYYMMDD}_{SLUG}_cc_report.md

最終プランを Write しました。以下をお願いします:
- /ticket-gen codex/plans/{YYYYMMDD}_{SLUG}_plan.md
- 完了後、subject `goal-feed ticket review request` で CC にレビュー依頼を投げてください。

CC 側は本 skill セッション中、review request を自動処理します。
```

### 3. Ticket Review Findings

**トリガー**: Phase E-5
**Subject**: `goal-feed ticket review findings` （`goal-feed-impl` 由来なら `goal-feed-impl ticket review findings`）
**Body テンプレ**:

```text
件名: goal-feed ticket review findings

review_path: codex/reviews/{YYYYMMDD}_{SLUG}_ticket_review.md
verdict: REQUEST_CHANGES / APPROVE
critical: <n> / major: <n> / minor: <n>

要旨:
<3〜5 行>

Critical / Major を修正のうえ再送してください。
修正不要の Minor は残置可。
```

### 4. Phase Progress Review Findings

**トリガー**: Phase F-7
**Subject**: `goal-feed phase progress review findings`（`-impl` 版は `goal-feed-impl` prefix）
**Body テンプレ**:

```text
件名: goal-feed phase progress review findings

review_path: codex/reviews/{YYYYMMDD}_{SLUG}_phase_{N}_review.md
phase: Phase {N}
verdict: REQUEST_CHANGES / APPROVE
critical: <n> / major: <n> / minor: <n>

要旨:
<3〜6 行>

次 Phase 進行前に Critical / Major を修正してください。
```

### 5. Final Review Findings

**トリガー**: Phase G-5
**Subject**: `goal-feed final review findings`（`-impl` 版は `goal-feed-impl` prefix）
**Body テンプレ**:

```text
件名: goal-feed final review findings

final_audit_path: codex/reviews/{YYYYMMDD}_{SLUG}_final_audit.md
verdict: PASS / CONDITIONAL PASS / FAIL

要旨:
<5〜10 行>

CC 側はこの後 /shime に移ります。
```

### 6. Session Closed（最終アナウンス）

**トリガー**: Phase G-6 の後
**Subject**: `goal-feed session closed`
**Body テンプレ**:

```text
件名: goal-feed session closed

daily_report: daily_report/{YYYY-MM-DD}_{title}.md
Plans.md 引き継ぎ: 記録済み

CC 側の作業は完了しました。Codex 側で /goal を complete マークしてください。
```

---

## inbound（Codex → CC）

CC 側 skill が自動処理する subject 一覧。それぞれの Body 期待項目と、CC 側の起動 Phase を示す。

### A. Plan Report From Codex

**Subject**: `goal-feed plan report from codex`
**Trigger**: Phase C-1 起動
**Body 期待項目**:
- Codex 側 plan report 本文（インラインまたはファイルパス）
- 対象範囲・観点
- Codex 独自の推奨ポイント

**CC 側動作**:
1. Body から report を取得（パス指定なら Read）
2. Phase C-2 の side-by-side 比較へ

### B. Ticket Review Request

**Subject**: `goal-feed ticket review request` / `goal-feed-impl ticket review request`
**Trigger**: Phase E-1 起動
**Body 期待項目**:
- `ticket_index`: 生成された ticket_index.md パス
- `tickets-dir`: 上位ディレクトリ
- `final plan`（`goal-feed` 由来のみ）: プランファイルパス

**CC 側動作**:
1. `references/review-protocol.md` の Phase E に従う
2. Read → 評価 → Write → 返信

### C. Phase Progress Review Request

**Subject**: `goal-feed phase progress review request` / `goal-feed-impl phase progress review request`
**Trigger**: Phase F-1 起動
**Body 期待項目**:
- `ticket_index`: パス
- `phase`: `Phase N`
- `status`: `completed` / `in-progress` / `blocked`
- Codex 実施内容の要約
- 検証（commands and results）
- 差分の起点（推奨: base commit SHA / branch）

**CC 側動作**:
1. `references/review-protocol.md` の Phase F に従う
2. diff 取得 → strict 判定 → `/cr` or `/cr --spec` → Write → 返信

### D. Final Review Request

**Subject**: `goal-feed final review request` / `goal-feed-impl final review request`
**Trigger**: Phase G-1 起動
**Body 期待項目**:
- `ticket_index`: パス
- `verification`: `/ticket-verify` レポートパス
- 全 Phase 完了サマリ
- 残リスク列挙

**CC 側動作**:
1. `references/review-protocol.md` の Phase G に従う
2. 集約 Read → 監査 → Write → 返信 → `/shime`

### E. Ambiguous / Clarification

**Subject**: `goal-feed ...` だが上記に一致しない
**CC 側動作**: `AskUserQuestion` で扱いを確認。自動処理はしない。

---

## Non-goal-feed メッセージの扱い

- subject が `goal-feed` / `goal-feed-impl` prefix を持たないメッセージは通常配信のまま。
- 本 skill は関与せず、ユーザーが手動で応答する。

---

## Skill 未発動時の扱い

セッション内で本 skill が発動していない（`activated: false`）状態では、上記 A〜D の subject が届いても**自動処理しない**。誤動作防止のため、通常配信のまま扱い、ユーザーに「`goal-feed` skill を発動しますか？」と会話上で提案する程度に留める。

---

## 送信スクリプト規約

```bash
# 送信
~/.agents/skills/agmsg/scripts/send.sh "$TEAM" "$AGENT" "$CODEX_PEER" "<body>"

# 受信の能動チェック
~/.agents/skills/agmsg/scripts/inbox.sh "$TEAM" "$AGENT"

# 履歴
~/.agents/skills/agmsg/scripts/history.sh "$TEAM" "$AGENT"

# チーム構成
~/.agents/skills/agmsg/scripts/team.sh "$TEAM"

# identity
~/.agents/skills/agmsg/scripts/whoami.sh "$(pwd)" claude-code
```

- Body は Bash の quoted string 内で通ることを確認。特殊文字は必要に応じてエスケープ。
- 長文は改行を含む文字列として直接渡す（`send.sh` はそのまま保存する）。
- 添付ファイルは絶対パスで body 内に明記。

---

## セクション構成規約（最終プランファイル）

`codex/plans/{YYYYMMDD}_{SLUG}_plan.md` は次の順序・見出しで書く（Codex 側 SKILL.md と一致必須）:

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

見出し名を変更しないこと。Codex 側および ticket-gen が見出しの一致を前提に動く。

---

## 対称性チェックリスト（メンテナンス用）

Codex 側 SKILL.md を編集する際は、以下が保たれているか本 references と付き合わせる:

- [ ] Subject 文字列（大文字小文字 / space / hyphen）が一字一句一致
- [ ] Body の必須項目名（`ticket_index`, `phase`, `verdict` など）が一致
- [ ] プランファイルセクション名 12 項目が一致
- [ ] `-impl` 版 prefix の使い分けが一致
- [ ] 出力パスの規約（`codex/plans/`, `codex/reviews/`）が一致
