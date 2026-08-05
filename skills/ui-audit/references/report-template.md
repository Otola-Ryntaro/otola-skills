# UI 監査 統合レポートテンプレート

全 Phase 完了後に `YYYYMMDD_ui_audit_summary/report.md` として保存する。

````markdown
# UI 監査 統合レポート

## 概要

| 項目       | 値                 |
| ---------- | ------------------ |
| 対象       | <アプリ名>         |
| 環境       | local / production |
| URL        | <ベースURL>        |
| 日時       | YYYY-MM-DD         |
| 監査範囲   | Phase 1〜N         |
| 総ページ数 | XX                 |
| 前回監査   | YYYY-MM-DD / なし  |

## サマリー

| 深刻度   | 件数  | 対応方針       |
| -------- | ----- | -------------- |
| Critical | X     | 即時修正       |
| Major    | X     | リリース前修正 |
| Minor    | X     | 次スプリント   |
| **合計** | **X** |                |

### 前回との差分

| 指標           | 件数 |
| -------------- | ---- |
| 前回から FIXED | X    |
| 未修正（継続） | X    |
| 新規発見       | X    |

## Phase レポート一覧

| Phase | スコープ             | レポート                                                         | C   | M   | m   | FIXED |
| ----- | -------------------- | ---------------------------------------------------------------- | --- | --- | --- | ----- |
| 1     | 認証・課金ゲート     | [report.md](../YYYYMMDD_ui_audit_phase1_auth_billing/report.md)  | 0   | 2   | 1   | 1     |
| 2     | ダッシュボード・ナビ | [report.md](../YYYYMMDD_ui_audit_phase2_dashboard_nav/report.md) | 0   | 1   | 2   | 0     |
| ...   | ...                  | ...                                                              | ... | ... | ... | ...   |

## 全問題リスト（深刻度順）

Phase 横断で深刻度順にソート。`/ticket-gen` に渡す場合は Phase レポート単位を推奨。

| ID  | Phase | 深刻度   | ページ | 問題 | 詳細 | 前回           |
| --- | ----- | -------- | ------ | ---- | ---- | -------------- |
| C-1 | 3     | Critical | ...    | ...  | ...  | NEW            |
| M-1 | 1     | Major    | ...    | ...  | ...  | 前回M-2 未修正 |
| M-2 | 1     | Major    | ...    | ...  | ...  | NEW            |
| m-1 | 1     | Minor    | ...    | ...  | ...  | NEW            |

## 前回指摘の修正状況

（前回の監査記録がある場合のみ）

| 前回ID | Phase | ページ                 | 問題           | 今回の状況        |
| ------ | ----- | ---------------------- | -------------- | ----------------- |
| M-1    | 1     | /admin/login           | ルート404      | FIXED             |
| M-2    | 1     | /admin/login           | エラー英語     | 未修正 → 今回 M-1 |
| M-3    | 1     | /admin/forgot-password | フロー到達不能 | FIXED             |
| M-4    | 1     | /admin/billing         | AI返信回数欠落 | 未修正 → 今回 M-2 |

## コンソールエラー（全Phase統合）

| Phase | ページ           | エラー数 | 主なエラー     |
| ----- | ---------------- | -------- | -------------- |
| 1     | /admin/login     | 0        | —              |
| 2     | /admin/dashboard | 1        | TypeError: ... |

## パフォーマンス（計測ページ）

スコープで選択された場合のみ記載。

| ページ           | TTFB | FCP  | CLS  | 判定      |
| ---------------- | ---- | ---- | ---- | --------- |
| /admin/dashboard | XXms | XXms | X.XX | OK / WARN |

## モバイル検証（オプション）

スコープで選択された場合のみ記載。

| ページ           | 375px | 768px | 問題 |
| ---------------- | ----- | ----- | ---- |
| /admin/dashboard | OK    | OK    | —    |

## 推奨対応

1. **即時対応** (Critical): <一覧>
2. **リリース前** (Major): <一覧>
3. **次スプリント** (Minor): <一覧>

## チケット化

Phase レポート単位で `/ticket-gen` に渡すことを推奨:

```bash
/ticket-gen output/browser-exam/YYYYMMDD_ui_audit_phase1_auth_billing/report.md
/ticket-gen output/browser-exam/YYYYMMDD_ui_audit_phase2_dashboard_nav/report.md
```

## 出力ディレクトリ

```
output/browser-exam/YYYYMMDD_ui_audit_summary/
```
````
