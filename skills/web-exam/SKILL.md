---
name: web-exam
description: >
  Browser Use CLI ベースのブラウザ総合検証スキル。実ブラウザでページを操作しながら、
  スクリーンショット撮影・コンソールエラー捕捉・パフォーマンス計測・アクセシビリティチェック・
  SEOチェック・セキュリティチェック・ページ監査を自動実行し、レポートを生成する。
  発動条件:
  (1) /web-exam コマンド + 自然言語のフロー記述
  (2) 「ブラウザ検証」「サイト検査」「ページ監査」「web exam」等のキーワード
  (3) パフォーマンス・アクセシビリティ・SEO・セキュリティを含むブラウザチェック依頼
  Playwright MCP や /web-test ではなく、Browser Use CLI を使用する。
---

# web-exam: ブラウザ総合検証スキル

Browser Use CLI (`~/.browser-use-env/bin/browser-use`) を使用したブラウザ検証。
コマンドリファレンス → [references/commands.md](references/commands.md)

## 起動時プラン提示

スキル起動時、まず **検証プラン** をユーザーに提示し、確認を得てから実行する。

### プランテンプレート

```
## web-exam 検証プラン

**対象**: <フロー概要>
**環境**: (Phase 1 で検出)

### 実行項目（チェック/外すものがあれば教えてください）

- [x] フロー操作 + スクリーンショット撮影
- [x] コンソールエラー監視
- [x] パフォーマンス計測 (TTFB, FCP, CLS, リソース分析)
- [x] アクセシビリティチェック (11項目)
- [x] SEO チェック (11項目)
- [x] セキュリティチェック (8項目)
- [x] ページ監査 (画像・リンク・DOM)

### オプション
- [ ] --headed（ブラウザウィンドウ表示）
- [ ] --profile（Real Chrome プロファイル利用）
- [ ] Cookie 保存/復元

このプランで実行しますか？変更があれば指示してください。
```

ユーザーが確認・変更したら、選択された項目のみ実行する。

## 実行プロトコル

### Phase 0: 準備
1. `date +%Y%m%d` で日付取得
2. フロー記述から短い英語 description を生成
3. `output/browser-exam/YYYYMMDD_<description>/` を作成（同名は `_v2` 等を付与）
4. `BU=~/.browser-use-env/bin/browser-use` をエイリアスとして使用

### Phase 1: 環境検出
```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000
```
- 200系 → `http://localhost:3000`（ローカル）
- それ以外 → `https://app.meocli.com`（本番）
- 報告: `環境: local / production`

### Phase 2: ブラウザ起動 & モニター注入
```bash
$BU open <base_url>
$BU eval "$(cat ~/.claude/skills/web-exam/scripts/inject-monitors.js)"
```
- `--headed` オプション: ユーザーがプランで選択した場合
- `--profile "Default"`: プランで選択した場合

### Phase 3: フロー実行（スクリーンショット付き）
ユーザーの自然言語フロー記述を操作ステップに分解し、各ステップで **ステップ実行サイクル** を回す。
**スクリーンショットは各ステップで必ず撮影する。**
フロー参照 → [references/flows.md](references/flows.md)

### Phase 4: 自動チェック実行
プランで選択されたチェックのみ実行。
各チェックの詳細 → [references/checks.md](references/checks.md)

```bash
# 1. 監視データ回収（コンソールエラー + パフォーマンス）
$BU eval "$(cat ~/.claude/skills/web-exam/scripts/collect-monitors.js)"

# 2. アクセシビリティチェック
$BU eval "$(cat ~/.claude/skills/web-exam/scripts/a11y-check.js)"

# 3. SEO チェック
$BU eval "$(cat ~/.claude/skills/web-exam/scripts/seo-check.js)"

# 4. セキュリティチェック
$BU eval "$(cat ~/.claude/skills/web-exam/scripts/security-check.js)"

# 5. ページ監査
$BU eval "$(cat ~/.claude/skills/web-exam/scripts/page-audit.js)"
```

各結果の JSON を解析し、レポートに統合する。

### Phase 5: レポート生成
結果を `YYYYMMDD_HHMMSS_report.md` に保存（後述テンプレート参照）。

### Phase 6: 終了
```bash
$BU close
```

## ステップ実行サイクル

各操作ステップで以下を **必ず** 回す:

### 1. State（現在状態の把握）
```bash
$BU state
```
番号付き要素一覧を取得し、操作対象の index を特定。

### 2. 操作実行
```bash
$BU open <url>           # ページ遷移
$BU click <index>        # クリック
$BU input <index> "text" # テキスト入力
$BU select <index> "val" # ドロップダウン選択
$BU keys "Enter"         # キー送信
$BU scroll down          # スクロール
```

### 3. 待機（SPA / 動的コンテンツ対応）
```bash
$BU wait text "読み込み完了"              # テキスト出現待機
$BU wait selector ".result"              # 要素出現待機
$BU wait selector ".spinner" --state hidden  # 要素消滅待機
```

### 4. Screenshot（必須 — 毎ステップ撮影）
```bash
$BU screenshot output/browser-exam/YYYYMMDD_<desc>/NNN_<step>.png
```
**スクリーンショットの省略は不可。** 全ステップで撮影し、レポートに一覧化する。

### 5. 状態確認
- エラーが疑われる場合 → `$BU eval "JSON.stringify(window.__bu_monitors.errors)"` で即時確認
- ページ遷移後 → `$BU eval "$(cat ~/.claude/skills/web-exam/scripts/inject-monitors.js)"` で再注入

## ページ遷移時の追加ルール
- `open` / `click` によるページ遷移後は必ず **monitors を再注入**
- SPA遷移の場合は monitors が維持されるため再注入不要
- 遷移後は `state` → `screenshot` の順で記録

## 認証ハンドリング

### 患者フロー（認証なし）
`/s/{slug}` からアクセス → そのままフロー実行

### 管理画面（Supabase Auth）
```
管理画面へのログインが必要です。
1. メールアドレス
2. パスワード
3. テスト用クリニックのslug (あれば)
```

### Real Chrome プロファイル利用
既存ログイン状態を利用する場合:
```bash
$BU --profile "Default" open <url>
```

### Cookie 保存・復元
テスト用にログイン状態を保存:
```bash
$BU cookies export output/browser-exam/cookies_admin.json
$BU cookies import output/browser-exam/cookies_admin.json
```

### プラットフォーム管理（MFA 必須）
MFA コード入力画面でユーザーに通知し、コードを教えてもらう。

## マルチタブ対応

タブ間の操作が必要な場合:
```bash
$BU switch 0       # 最初のタブに切り替え
$BU switch 1       # 2番目のタブに切り替え
$BU close-tab 1    # タブを閉じる
```

## 出力規約

### ディレクトリ
```
output/browser-exam/YYYYMMDD_<description>/
├── 001_<step>.png           # ステップスクリーンショット（必須）
├── 002_<step>.png
├── ...
├── YYYYMMDD_HHMMSS_report.md  # 総合レポート
└── cookies_*.json            # Cookie エクスポート（任意）
```

### ファイル命名
- `NNN`: 3桁ゼロ埋め連番 (001, 002, ...)
- `<step>`: ステップ内容の短い英語スネークケース

## レポートテンプレート

````markdown
# web-exam 総合検証レポート

## 概要
| 項目 | 値 |
|------|-----|
| 環境 | local / production |
| URL | <検証対象URL> |
| 日時 | YYYY-MM-DD HH:MM:SS |
| 目的 | <フローの目的> |
| 実行項目 | <プランで選択された項目> |

## フロー実行結果

### スクリーンショット一覧
| # | ステップ | ファイル | 状態 |
|---|---------|---------|------|
| 001 | ... | `001_xxx.png` | OK / NG |

### 操作ログ
- 期待と異なった動作があれば記載

## パフォーマンス

| 指標 | 値 | 判定 |
|------|-----|------|
| TTFB | XXms | OK / WARN / NG |
| First Contentful Paint | XXms | OK / WARN / NG |
| DOM Ready | XXms | OK / WARN / NG |
| Load | XXms | OK / WARN / NG |
| CLS | X.XX | OK / WARN / NG |
| リソース数 | XX | - |
| 総転送サイズ | XX KB | OK / WARN / NG |

### 遅いリソース Top 5
| リソース | 時間 | サイズ |
|---------|------|--------|

## アクセシビリティ (スコア: XX%)

| チェック | 結果 | 詳細 |
|---------|------|------|

## SEO (スコア: XX%)

| チェック | 結果 | 詳細 |
|---------|------|------|

### メタ情報
| 項目 | 値 |
|------|-----|

## セキュリティ (スコア: XX%)

| チェック | 結果 | 詳細 |
|---------|------|------|

## ページ監査

### 画像
| 項目 | 値 |
|------|-----|
| 総数 | XX |
| alt なし | XX |
| lazy loading なし | XX |
| 大サイズ (>1200px) | XX |

### リンク
| 項目 | 値 |
|------|-----|
| 総数 | XX |
| 外部リンク | XX |
| 壊れたリンク | XX |

### DOM
| 項目 | 値 |
|------|-----|
| 総要素数 | XX |
| 最大ネスト深度 | XX |

## コンソール

### エラー
| # | メッセージ | ソース |
|---|-----------|--------|

### 警告
| # | メッセージ |
|---|-----------|

## 総合判定

| カテゴリ | スコア | 判定 |
|---------|--------|------|
| パフォーマンス | - | OK / WARN / NG |
| アクセシビリティ | XX% | OK / WARN / NG |
| SEO | XX% | OK / WARN / NG |
| セキュリティ | XX% | OK / WARN / NG |
| コンソール | エラーX件 | OK / NG |

## 推奨対応
- 優先度順に改善提案を記載
````
