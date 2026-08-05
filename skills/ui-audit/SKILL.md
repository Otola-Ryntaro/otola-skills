---
name: ui-audit
description: >
  テスト通過済みプロダクトの実地ブラウザ UI 監査スキル。
  /web-exam の Browser Use CLI インフラをそのまま活用し、アプリ全ページを
  Phase 分割で網羅的に巡回。各ページでスクショ撮影・コンソールエラー収集・
  目視チェックを行い、Critical/Major/Minor に分類した問題リストと
  チケット化可能な粒度のレポートを生成する。
  発動条件:
  (1) /ui-audit コマンド
  (2) 「UI監査」「全ページチェック」「実地レビュー」「ブラウザ監査」等のキーワード
  (3) テスト通過後のリリース前品質チェック依頼
  (4) 「画面を全部見て問題を洗い出して」等の網羅的検証依頼
  /web-exam（単一フロー検証）とは異なり、アプリ全体を Phase 分割で系統的に監査する。
---

# ui-audit: ブラウザ UI 監査スキル

テスト通過済みプロダクトを実ブラウザで網羅巡回し、問題を発見・分類・レポートする。
`/web-exam` の Browser Use CLI + スクリプト群をそのまま利用する。

## 前提

- `/web-exam` スキルのインフラ一式（`$BU` コマンド、`inject-monitors.js` 等）
- Browser Use CLI: `~/.browser-use-env/bin/browser-use`
- スクリプト群: `~/.claude/skills/web-exam/scripts/`

## 出力ディレクトリ命名規約

すべての出力は以下の規約に従う。前回の監査結果を参照できるよう、命名は厳格に守る。

```
output/browser-exam/
├── YYYYMMDD_ui_audit_phase1_<short_name>/
│   ├── 001_<page>.png
│   ├── 002_<page>.png
│   ├── ...
│   ├── mobile_375_<page>.png       # モバイル検証（オプション）
│   ├── tablet_768_<page>.png       # タブレット検証（オプション）
│   └── report.md                   # Phase レポート（必須）
├── YYYYMMDD_ui_audit_phase2_<short_name>/
│   ├── ...
│   └── report.md
├── YYYYMMDD_ui_audit_phase3_<short_name>/
│   ├── ...
│   └── report.md
├── YYYYMMDD_ui_audit_summary/
│   └── report.md                   # 全 Phase 統合レポート
└── cookies_admin.json              # Cookie（Phase 間共有）
```

### 命名ルール

| 要素           | 規約                           | 例                                   |
| -------------- | ------------------------------ | ------------------------------------ |
| 日付           | `YYYYMMDD`                     | `20260404`                           |
| プレフィックス | `ui_audit` 固定                |                                      |
| Phase          | `phase<N>` (1始まり)           | `phase1`, `phase2`                   |
| short_name     | Phase 内容の英語スネークケース | `auth_billing`, `dashboard_nav`      |
| スクショ       | `NNN_<page>.png` (3桁連番)     | `001_login.png`, `002_dashboard.png` |
| レポート       | `report.md` 固定               |                                      |
| 統合           | `_summary` 固定                | `20260404_ui_audit_summary`          |

この命名に従うことで、次回の監査時に `output/browser-exam/*_ui_audit_*` で前回の結果を Glob できる。

## Step 0: プランモードで監査計画を策定

**ブラウザを開く前に、まずプランモードに入って計画を立てる。**

### 0-1. 前回の監査結果確認

まず、前回の監査記録があるか確認する:

```bash
ls output/browser-exam/*_ui_audit_*/report.md 2>/dev/null
```

**前回の記録がある場合**、ユーザーに以下を質問:

```
## 前回の監査結果

前回の UI 監査記録が見つかりました:
- <日付>: <Phase 一覧と問題件数の要約>

### 前回指摘箇所の再チェック
前回指摘された問題箇所を優先的に確認しますか？

- [ ] はい — 前回の Critical/Major を最初に再チェックし、修正状況を確認
- [ ] いいえ — 通常の監査フローで実施
- [ ] 前回の指摘箇所のみ再チェック（フル監査はスキップ）
```

「はい」の場合、前回の report.md を Read して問題リストを抽出し、
Step 1 の各 Phase で該当ページを優先的に巡回する。
レポートには「前回指摘 → 今回結果」の対比列を追加する。

### 0-2. コードベース調査

EnterPlanMode で計画モードに入り、以下を調査する:

1. **ルート全量収集**: `app/` 配下の `page.tsx` を Glob で列挙
2. **認証ガード確認**: middleware.ts、layout.tsx のガード条件を Read
3. **ナビゲーション構造**: サイドバー・ヘッダーのメニュー定義を確認
4. **課金ゲート**: プラン制限がかかるページ・機能を特定
5. **既知の問題**: `docs/problem_solved/` や過去の `output/browser-exam/` レポートを確認

### 0-3. ページインベントリ作成

調査結果から全ページの一覧表を作成:

```
| # | パス | セクション | 認証 | 課金ゲート | 前回指摘 | 備考 |
|---|------|-----------|------|-----------|---------|------|
| 1 | /admin/login | 認証 | 不要 | なし | M-2 英語エラー | |
| 2 | /admin/dashboard | メイン | admin | なし | — | |
| 3 | /admin/billing | 課金 | admin | なし | M-4 回数欠落 | |
```

前回の監査結果がある場合、「前回指摘」列に該当する問題 ID を記載する。

### 0-4. Phase 分割 & 重点ポイント設計

ページを機能的なまとまりで Phase に分割し、各 Phase の重点チェック観点を定義:

```
## 監査計画

### Phase 分割

| Phase | スコープ | ページ数 | 重点チェック観点 | 前回指摘数 |
|-------|---------|---------|----------------|-----------|
| 1 | 認証・課金ゲート | 6 | ログインフロー、エラー表示、プラン制限 | M:2, m:1 |
| 2 | ダッシュボード・ナビ | 4 | データ表示、ナビ遷移、空状態 | — |
| 3 | 設定系 | 5 | フォーム操作、保存/キャンセル、バリデーション | — |

### 各 Phase の観点

**Phase 1: 認証・課金ゲート**
- [ ] ログイン成功/失敗の両パス
- [ ] エラーメッセージの日本語化
- [ ] パスワードリセットフロー到達性
- [ ] 課金画面のプラン情報表示
- [ ] 未課金ユーザーのゲート動作
- [ ] 【再チェック】M-2: ログインエラー英語表示
- [ ] 【再チェック】M-4: AI返信回数の表示欠落
```

### 0-5. ユーザー確認 → ExitPlanMode

計画をユーザーに提示し、以下を確認:

- Phase 分割と優先順序
- 監査範囲の追加/除外
- 認証情報（メール/パスワード/slug）
- オプション（モバイル検証、自動チェック）

確認が取れたら ExitPlanMode で実行フェーズに移行する。

## Step 1: Phase 実行

各 Phase で以下のサイクルを回す。**Phase ごとに report.md を作成する（必須）。**

### Phase 開始

```bash
BU=~/.browser-use-env/bin/browser-use
DATE=$(date +%Y%m%d)
PHASE_NAME="phase<N>_<short_name>"
OUTDIR="output/browser-exam/${DATE}_ui_audit_${PHASE_NAME}"
mkdir -p "$OUTDIR"
```

### Cookie 復元（Phase 2 以降）

```bash
$BU cookies import output/browser-exam/cookies_admin.json
```

Phase 1 でログイン後に Cookie を保存し、以降の Phase で復元する。

### ページ巡回サイクル

各ページで `/web-exam` のステップ実行サイクルを回す:

1. **state** → `$BU state`（要素一覧取得）
2. **操作** → `$BU open <url>` / `$BU click` 等
3. **wait** → `$BU wait selector` / `$BU wait text`
4. **screenshot** → `$BU screenshot $OUTDIR/NNN_<page>.png` **（省略不可）**
5. **確認** → 目視 + monitors チェック

### モニター管理

```bash
# ページ遷移後に毎回注入
$BU eval "$(cat ~/.claude/skills/web-exam/scripts/inject-monitors.js)"

# エラー即時確認
$BU eval "JSON.stringify(window.__bu_monitors.errors)"

# Phase 末にモニターデータ回収
$BU eval "$(cat ~/.claude/skills/web-exam/scripts/collect-monitors.js)"
```

### Cookie 保存（Phase 1 完了時）

```bash
$BU cookies export output/browser-exam/cookies_admin.json
```

### Phase レポート作成（必須 — セッション間の記録保全）

**各 Phase 完了時に、そのディレクトリ内に `report.md` を必ず作成する。**
Phase レポートテンプレート → [references/phase-report-template.md](references/phase-report-template.md)

目的: 監査が複数セッションにまたがる場合に、発見した問題を失わないための記録。
Phase レポートは `/ticket-gen` には直接渡さない（チケット化は統合レポート経由）。

## Step 2: 問題分類

各ページで発見した問題を以下の基準で分類する。

### 深刻度基準

| レベル       | 基準                                                           | 例                                                 |
| ------------ | -------------------------------------------------------------- | -------------------------------------------------- |
| **Critical** | 機能不能、白画面、データ漏洩リスク                             | ページ 500、認証バイパス、個人情報露出             |
| **Major**    | 主要機能の品質問題、翻訳抜け（ユーザー影響大）、課金ゲート不備 | エラーメッセージ英語、機能到達不能、表示データ欠落 |
| **Minor**    | パディングずれ、コンソール Warning、軽微な翻訳抜け             | レイアウト崩れ、deprecation warning、タイトル改行  |

### 問題記録フォーマット

各問題は以下の粒度で記録（チケット化可能）:

```
| ID | ページ | 深刻度 | 問題 | 詳細 | 再現手順 | スクショ | 前回指摘 |
```

「前回指摘」列: 前回と同じ問題なら前回の ID を記載、新規なら `NEW`、修正済みなら `FIXED`。

## Step 3: モバイル検証（オプション）

スコープで選択された場合、主要ページを以下のビューポートで再検証:

```bash
# iPhone SE (375px)
$BU eval "window.resizeTo(375, 812)"
$BU screenshot $OUTDIR/NNN_mobile_375_<page>.png

# iPad (768px)
$BU eval "window.resizeTo(768, 1024)"
$BU screenshot $OUTDIR/NNN_tablet_768_<page>.png
```

確認ポイント:

- ナビゲーション（ハンバーガーメニュー、サイドバー折りたたみ）
- テーブルの横スクロール / レスポンシブ対応
- フォームの入力しやすさ
- ボタン・リンクのタップターゲットサイズ (44x44px)

## Step 4: 統合レポート生成

全 Phase のレポートを統合した `summary/report.md` を作成する。

```bash
mkdir -p "output/browser-exam/${DATE}_ui_audit_summary"
```

統合レポートテンプレート → [references/report-template.md](references/report-template.md)

統合レポートには以下を含める:

- 全 Phase の問題を深刻度順にソートした一覧
- 前回指摘の修正状況（FIXED / 未修正 / 新規）
- 各 Phase レポートへのリンク

## Step 5: チケット連携

統合レポート完了後、ユーザーに提案:

```
## 次のアクション

監査で <Critical N件 / Major N件 / Minor N件> の問題を発見しました。
（前回からの変化: FIXED N件 / 未修正 N件 / 新規 N件）

- [ ] /ticket-gen で統合レポートをチケット化
- [ ] Critical/Major のみチケット化
- [ ] 手動で対応（レポート参照）
```

**`/ticket-gen` には統合レポートを渡す。Phase 分割は `/ticket-gen` に一任する。**

```bash
/ticket-gen output/browser-exam/20260404_ui_audit_summary/report.md
```

## 注意事項

- **スクリーンショットは全ページ・全ステップで必須**（省略するとレビュー不能）
- **ページ遷移後は monitors 再注入**（SPA 内遷移を除く）
- **Phase レポートは各 Phase 完了時に必ず作成**（後回し禁止）
- 問題の記述は「何が」「どう」「なぜ問題か」を明記（チケット化時の情報不足を防ぐ）
- 認証情報はレポートに含めない
- `/web-exam` の自動チェック（a11y, SEO, security, performance）はスコープで選択された場合のみ実行
- 命名規約を厳守する（次回の監査で前回結果を自動参照するため）
