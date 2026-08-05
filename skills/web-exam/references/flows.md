# プロジェクト固有フロー・URL契約

## URL パターン

### 患者フロー
| ステップ | URL | 説明 |
|---------|-----|------|
| QR入口 | `/s/{slug}` | 患者がQRコードからアクセスする正本URL |
| アンケート | `/clinic/{slug}/survey?session={sessionId}` | アンケート回答画面 |
| 口コミ生成 | `/clinic/{slug}/review?session={sessionId}` | AI口コミ生成・表示画面 |
| 完了 | `/clinic/{slug}/complete?session={sessionId}` | 完了画面（Google口コミリンク） |

### 管理画面 (admin)
| ステップ | URL | 説明 |
|---------|-----|------|
| ログイン | `/admin/login` | Supabase Auth ログイン |
| ダッシュボード | `/admin/dashboard` | メイン画面 |
| アンケート設問 | `/admin/questions` | 質問設定 |
| AI設定 | `/admin/ai-models` | AIモデル・プロンプト設定 |
| クリニック設定 | `/admin/settings` | クリニック基本情報 |
| 口コミ一覧 | `/admin/reviews` | 生成された口コミ一覧 |

### プラットフォーム管理 (platform-admin)
| ステップ | URL | 説明 |
|---------|-----|------|
| ログイン | `/platform-admin/login` | MFA必須ログイン |
| ダッシュボード | `/platform-admin` | 管理人ダッシュボード |
| クリニック管理 | `/platform-admin/clinics` | 全クリニック一覧 |
| AI設定 | `/platform-admin/ai-models` | グローバルAI設定 |

## 認証パターン

| ロール | 認証方式 | 備考 |
|--------|---------|------|
| 患者 | 認証なし | `/s/{slug}` からセッション自動発行 |
| ユーザー (admin/owner) | Supabase Auth | メール + パスワード |
| 管理人 (platform_admin) | Supabase Auth + MFA | TOTP必須 |

## 自然言語 → ステップ変換の例

### 例1: 「患者アンケートフローを確認」
```
1. /s/{slug} にアクセス (slugは既知のテスト用クリニック)
2. アンケート開始ボタンをクリック
3. Q1〜最終質問まで順に回答
4. 送信ボタンをクリック
5. 口コミ生成画面の表示を確認
6. Google口コミリンクが表示されることを確認
```

### 例2: 「管理画面のアンケート設問を確認」
```
1. /admin/login でログイン
2. サイドバーから「アンケート設問」をクリック
3. 質問一覧・トグル・設定を確認
```

## テスト用クリニック slug の確認方法

1. Supabase MCP で `SELECT slug FROM clinics LIMIT 5` を実行
2. または `.env.local` の `TEST_CLINIC_SLUG` を確認 (Claude Code からはアクセス不可)
3. いずれも不明な場合はユーザーに質問
