# 有料サービス品質バー — Paid-Service Quality Bar

「ユーザーが月額課金を継続してもよい」と思える品質の輪郭。goal-feed / goal-feed-impl の全 Phase で参照するチェックリスト。

**基本方針**:

- 全観点をベタ塗りするのではなく、**本件で厳格化する観点をユーザーと握る**。
- ただし Security / Data integrity は原則すべてのプロジェクトで無条件に厳格。
- 「ユーザーが払っていい」の定義は「壊れない・待たされない・信頼できる・欲しい機能がすぐ手に届く」の 4 点で近似。

---

## 1. Security（無条件で厳格）

### 認証・認可

- [ ] 明示的な authn（ログイン / セッション / トークン）と authz（誰が何をできるか）の境界がコード上で 1 箇所に集約されているか
- [ ] 認可漏れ（IDOR、tenant 越境、admin 権限昇格）が起きないよう、リソースごとに ownership チェック
- [ ] Passwords / tokens が hash / encrypted で保存、平文ログに出ない
- [ ] Session revocation の手段が存在（ログアウト、全端末サインアウト、パスワード変更で失効）

### Secret 管理

- [ ] ハードコードされた秘密が 0
- [ ] `.env` はコミット禁止、`.env.example` のみ
- [ ] Rotation 手順がドキュメント化
- [ ] CI/CD の Secret 露出（プルリクログ）に対策あり

### 入力バリデーション

- [ ] すべての外部入力（HTTP body / query / header / URL / 環境変数 / DB / 外部 API 応答）を型定義 or Schema で検証（例: Zod, Pydantic）
- [ ] SQL injection prevention（parameterized queries / ORM）
- [ ] XSS prevention（サニタイズ、`dangerouslySetInnerHTML` の禁止 or 検証）
- [ ] CSRF protection（SameSite Cookie、CSRF token、Origin/Referer 検証）
- [ ] Rate limit（IP / user / API key ベース）

### エラー応答

- [ ] エラーメッセージから内部情報（stack trace、DB 構造、パス）を漏らさない
- [ ] 認証失敗のメッセージが timing attack を許さない（ユーザー名列挙防止）

### 依存関係

- [ ] `npm audit` / `pip-audit` 等で既知脆弱性ゼロ
- [ ] 未使用 dependency の削除
- [ ] Lock file がコミットされている

---

## 2. Data Integrity（無条件で厳格）

### トランザクション

- [ ] 複数レコード更新の整合性は transaction で担保
- [ ] Idempotency（外部 API 呼び出しの重複防止、webhook の重複受信、決済の二重処理）

### Migration

- [ ] 後方互換な migration（Add before Remove、backfill、feature flag での段階リリース）
- [ ] Rollback plan（migration が壊れたときの復旧手順）
- [ ] Migration の dry-run / plan / apply の分離

### バックアップ・復旧

- [ ] 定期バックアップ
- [ ] PITR（Point-in-Time Recovery）できる程度の recovery target
- [ ] 復旧手順が runbook にある

### PII 分離

- [ ] PII が必要なテーブル / カラムを最小化
- [ ] 保持期間の設計（GDPR / 個人情報保護法）
- [ ] 削除要求への対応フロー

---

## 3. UX Polish

### ステートの網羅

- [ ] Loading state（skeleton, spinner, 進行率）
- [ ] Empty state（データなしの案内、次アクション提示）
- [ ] Error state（人間可読、リカバリー手段、再試行ボタン）
- [ ] Partial data state（一部失敗時の UI）

### レスポンシブ

- [ ] Mobile / Tablet / Desktop で崩れない
- [ ] タッチ操作前提のヒットエリア（44px 以上）

### Accessibility（a11y）

- [ ] キーボード操作（Tab 順、focus visible）
- [ ] Screen reader 対応（aria-* 属性、alt text）
- [ ] コントラスト比 WCAG AA 以上

### Perceived performance

- [ ] Initial paint < 1.5s、interactive < 3s（LCP / FID / CLS）
- [ ] Optimistic UI（送信中に一時 UI 更新）
- [ ] Loading の頻度を下げる（cache、prefetch）

### Copy（文言）

- [ ] エラー文言が「何が起きたか」「どうしたら回復するか」を含む
- [ ] Empty state の文言が単なる "No data" ではない
- [ ] CTA が動詞で始まる

---

## 4. Observability

### ログ

- [ ] 構造化ログ（JSON）
- [ ] 相関 ID（request ID、trace ID）
- [ ] Level（debug / info / warn / error / fatal）の使い分け
- [ ] PII をログに載せない

### メトリクス

- [ ] 主要 KPI（DAU / MAU、conversion、churn）
- [ ] インフラ指標（CPU / mem / disk / DB conn pool）
- [ ] Application 指標（RPS、p50/p95/p99 latency、error rate）

### Error tracking

- [ ] Sentry / Rollbar / Bugsnag 等の統合
- [ ] Release tag / user context 付与
- [ ] Ignore / rate limit で騒音抑制

### Alerts / On-call

- [ ] SLI / SLO 定義
- [ ] Alert が rotation で回る先
- [ ] Runbook link を alert 本文に含める

---

## 5. Testing

### カバレッジ

- [ ] Unit test（純関数、utility、component）: 80%+
- [ ] Integration test（API endpoint、DB 操作）
- [ ] E2E test（Playwright）: 主要ユーザーフロー
- [ ] Contract test（外部 API 契約）

### Regression guard

- [ ] Bug 修正には再現テストを追加（TDD 原則）
- [ ] Flaky test の quarantine 手順

### CI

- [ ] PR ごとに typecheck + lint + test + build
- [ ] Preview deploy でスモークテスト
- [ ] Merge blocking の gate 明示

---

## 6. Payments 固有（決済がある場合）

### Stripe / 決済プロバイダ連携

- [ ] Webhook signature verification（`Stripe-Signature` 検証）
- [ ] Idempotency key の付与
- [ ] Retry backoff（exponential）
- [ ] Failure mode の完全網羅（card declined, insufficient funds, 3DS required, network error）

### Subscription lifecycle

- [ ] Trial → active → past_due → canceled の全状態遷移がテスト済み
- [ ] Proration 計算の正確性
- [ ] Downgrade / upgrade の即時性 or 次周期反映の設計
- [ ] Cancellation の即時失効 vs 期間末失効の選択

### Dunning（未払い回収）

- [ ] Payment failed → retry schedule
- [ ] Grace period 設定
- [ ] User への通知（email）

### Refund / dispute

- [ ] Full / partial refund 手順
- [ ] Dispute / chargeback への reply flow
- [ ] Refund が発生したときの権限失効タイミング

### 税

- [ ] Tax calculation（Stripe Tax / 手動計算）
- [ ] 領収書 / 請求書の発行
- [ ] Legal / 会計要件（invoicing、tax id 収集）

### 監査ログ

- [ ] 金額変更 / 権限変更 / refund は immutable log

---

## 7. Operational

### Deployment

- [ ] Zero-downtime deploy（rolling / blue-green）
- [ ] Rollback ボタン一発
- [ ] Feature flag での段階リリース（1% → 10% → 100%）

### Runbook

- [ ] 主要 alert に対応する runbook
- [ ] 復旧手順が手順書化
- [ ] Escalation path

### Cost

- [ ] インフラコストの monitoring
- [ ] コスト上限アラート
- [ ] 無限ループ / runaway job への対策

### DR / BCP

- [ ] 別 AZ / region への切替手順
- [ ] RTO / RPO 定義
- [ ] 障害訓練の周期

---

## 8. Documentation

### External

- [ ] User-facing docs（機能、ガイド、FAQ）
- [ ] API reference（OpenAPI / Swagger）
- [ ] Changelog

### Internal

- [ ] Architecture diagram
- [ ] Runbook（前述）
- [ ] On-boarding guide for new engineers
- [ ] Decision records（ADR）

---

## 使い方（本 skill 内での参照方法）

### Phase A-4 で

`AskUserQuestion` を使い「本件で特に厳しく見たい観点」を multi-select で確認:

- Security（無条件、確認のみ）
- Data integrity（無条件、確認のみ）
- UX polish
- Observability
- Testing
- Payments（該当時のみ）
- Operational

回答を最終プランの `## Paid-Service Quality Bar` セクションに反映。

### Phase E, F, G で

各レビュー時に本ファイルの該当節を Read し、diff / チケットが該当観点を満たしているかチェック。特に:

- Phase E（ticket review）: プランで宣言した観点がチケットに落ちているか
- Phase F（phase review）: 該当 diff が該当観点を守っているか（例: auth 変更なら Security 節を厳しく見る）
- Phase G（final audit）: 全観点を一巡し、リリース可否を判定

### 本質修正の観点

修正依頼のとき、上記のいずれかを「実装したフリで済ませていないか」を最も厳しく見る。例:

- 「rate limit を厳しくする」→ config だけ書き換えて実装コードは同じ → 症状潰し
- 「エラーハンドリング追加」→ try/catch で握りつぶし → 症状潰し
- 「テスト追加」→ 実装をテストするのではなく、テスト無しでも通る expect のみ → 症状潰し

これらは Critical として指摘し、Codex に「本質修正」を要求する。
