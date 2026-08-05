# New Pattern Template — `.claude/error-patterns/<slug>.md` 登録用テンプレ

mine-check Phase F で発見した新規地雷を `<project>/.claude/error-patterns/<slug>.md` に登録するときに使うテンプレ。
ci-fix Phase 7b と同じフォーマットを踏襲する。INDEX.md への 1 行追加もセット。

---

## ファイル名規則

```
<project>/.claude/error-patterns/<slug>.md
```

slug の付け方:

- 全小文字、ハイフン区切り
- 何が起きるかを 2-4 単語で表現
- 例: `prisma-query-engine-missing`, `dip-port-unregistered`, `inngest-retry-loop`

---

## ファイル本体テンプレ

````markdown
---
name: <slug>
description: <1 行で何のエラーか>
type: error-pattern
category: <deploy|test|runtime|db|infrastructure|security|migration>
severity: <critical|warning|info>
last_seen: <YYYY-MM-DD>
last_verified: <YYYY-MM-DD>
status: <🟢 active | 🟡 stale-6mo | 🔴 deprecated>
source_reports:
  - docs/problem_solved/YYYYMMDD_xxx.md
  - codex/YYYYMMDD_mine_check_report.md
---

# <人間可読のタイトル>

## Signature

エラーログ / 症状の正規表現。CI ログや Sentry で grep する用途。

```regex
(複数行 OK)
^Error: ...$
```
````

## Symptoms

実際の症状。ユーザー視点・運用視点の両方を書く。

- ユーザー視点: 「ログインできない」「500 エラー」
- 運用視点: 「Vercel ログに XXX」「CI quality job が赤」

## Root Cause

なぜ起きるのか。技術的なメカニズム。

- 何のコンポーネントが
- どんな前提で動いていて
- 何が壊れると発火するか

## Fix

### ❌ NG パターン

```typescript
// 壊れているコード例
```

### ✅ OK パターン

```typescript
// 修正後のコード例
```

## Prevention

再発防止策。チェックリスト・grep パターン・runbook リンク等。

- [ ] CI で <X> をチェック
- [ ] PR テンプレに <Y> 項目を追加
- [ ] runbook: `docs/operations/<file>.md`

## Source Reports

- 初出: `docs/problem_solved/YYYYMMDD_xxx.md`
- 関連: `memory/feedback_<slug>.md`（あれば）
- mine-check 検出: `codex/YYYYMMDD_mine_check_report.md`

````

---

## INDEX.md への追加（必須）

`<project>/.claude/error-patterns/INDEX.md` のテーブル末尾に 1 行追加（Edit）:

```markdown
| <slug> | <category> | <one-liner: 何のエラーパターンか> |
````

---

## 蓄積判断基準

新規パターンを蓄積するかどうかの判断:

| 観点       | 蓄積する                               | 蓄積しない                  |
| ---------- | -------------------------------------- | --------------------------- |
| 再発可能性 | 同じ条件で再発しうる                   | 一回きりの事象              |
| 検出可能性 | 静的に検出できる（grep / lint / type） | 実行時しか分からない        |
| 汎用性     | プロジェクト全体に効く                 | 特定の 1 ファイル限定の bug |
| 影響範囲   | 本番影響あり / セキュリティ影響あり    | UI 上の小さな崩れ           |

迷ったら蓄積する側に倒す（false negative より false positive）。

---

## Phase F での運用フロー

```
1. mine-check Phase D のレポート「🆕 新規発見パターン候補」を確認
2. 各候補について:
   a. ユーザーに「これを error-patterns/ に登録してよいか」確認
   b. 承認 → 本テンプレを使って <slug>.md を Write
   c. INDEX.md にエントリ追加
3. 完了したら mine-check のレポートに「蓄積完了: N 件」を追記
4. ユーザーに次ステップ（/ticket-gen）を案内
```
