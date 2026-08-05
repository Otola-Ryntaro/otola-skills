---
name: web-test
description: |
  Playwright CLI ベースのブラウザ目視検証スキル。操作ステップごとにスクリーンショットを撮影し、
  コンソールログ・ネットワークリクエストも記録する。
  発動条件:
  (1) /web-test コマンド + 自然言語のフロー記述
  (2) 「ブラウザで動作確認」「目視検証」「スクショで確認」等のキーワード
  総合チェック（パフォーマンス・a11y・SEO・セキュリティ）が必要な場合は /web-exam を使用すること。
---

# web-test: ブラウザ目視検証スキル

Playwright CLI (`playwright-cli`) を使用した目視検証。
自然言語でフローを記述すると、操作ステップごとにスクリーンショット・ログを記録する。

> 総合チェック（パフォーマンス・a11y・SEO・セキュリティ）が必要な場合 → `/web-exam` を使用

## 実行プロトコル

### Phase 0: 準備
1. `date +%Y%m%d` で日付取得
2. フロー記述から短い英語 description を生成
3. `output/playwright/YYYYMMDD_<description>/` を作成（同名は `_v2` 等を付与）
4. ステップカウンタ `NNN=001` から開始

### Phase 1: 環境検出
```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000
```
- 200系 → `http://localhost:3000`（ローカル）
- それ以外 → `https://app.meocli.com`（本番）
- 報告: `環境: local / production`

### Phase 2: ブラウザ起動
```bash
playwright-cli open
playwright-cli resize 1440 900
```

### Phase 3: フロー実行
ユーザーの自然言語フロー記述を操作ステップに分解し、各ステップで **ステップ実行サイクル** を回す。
フロー参照 → [references/flows.md](references/flows.md)

### Phase 4: ログ保存
```bash
playwright-cli console   # → console.log に保存
playwright-cli network   # → network.log に保存
```

### Phase 4.5: 検証 & レポート判定
以下のいずれかに該当する場合、エラーレポートを自動生成:
1. コンソールに error レベルのログがある
2. ネットワークで 4xx/5xx レスポンスがある
3. 操作が期待通りに進まなかった
4. ユーザーが指定した目的の動作が確認できなかった

### Phase 5: 終了
```bash
playwright-cli close
```

## ステップ実行サイクル

### 1. Snapshot（現在状態の把握）
```bash
playwright-cli snapshot
```
snapshot の ref を読み取り、操作対象の要素を特定。

### 2. 操作実行
```bash
playwright-cli goto <url>          # ページ遷移
playwright-cli click <ref>         # クリック
playwright-cli fill <ref> "text"   # テキスト入力
```

### 3. Screenshot（結果の記録）
```bash
playwright-cli screenshot --filename=output/playwright/YYYYMMDD_<desc>/NNN_<step>.png
```

### 4. 状態確認
- ページ遷移 → 新しい snapshot を取得
- エラー表示 → `playwright-cli console error` で即時確認
- 次のステップへ

### ページ遷移時の追加ルール
- `goto` 後は必ず snapshot → screenshot
- SPA遷移はクリック後の snapshot で遷移完了を確認

## 出力規約

### ディレクトリ
```
output/playwright/YYYYMMDD_<description>/
├── 001_<step>.png
├── 002_<step>.png
├── ...
├── console.log
├── network.log
└── YYYYMMDD_HHMMSS_report.md    # エラー検出時のみ
```

### ファイル命名
- `NNN`: 3桁ゼロ埋め連番 (001, 002, ...)
- `<step>`: ステップ内容の短い英語スネークケース

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

### プラットフォーム管理（MFA 必須）
MFA コード入力画面でユーザーに通知し、コードを教えてもらう。

## 終了レポート

```
## web-test 完了レポート

**環境**: local / production
**フロー**: <フロー概要>
**日時**: YYYY-MM-DD HH:MM

### スクリーンショット一覧
| # | ステップ | ファイル |
|---|---------|---------|
| 001 | ... | `001_xxx.png` |

### 検出事項
- コンソールエラー / ネットワークエラー / 問題なし

### 出力先
`output/playwright/YYYYMMDD_<description>/`
```

## エラーレポート自動生成

エラー検出時に `YYYYMMDD_HHMMSS_report.md` を生成:

```markdown
# web-test エラーレポート

## 概要
| 項目 | 値 |
|------|-----|
| 環境 | local / production |
| 日時 | YYYY-MM-DD HH:MM:SS |
| 目的 | <フローの目的> |
| 結果 | エラー検出 |

## コンソールエラー
| # | レベル | メッセージ |

## ネットワークエラー
| # | ステータス | URL | メソッド |

## 期待動作 vs 実際の動作
| ステップ | 期待 | 実際 | 状態 |

## 関連スクリーンショット
## 推奨対応
```

## フロー参照

プロジェクト固有のURL・フロー定義 → [references/flows.md](references/flows.md)
