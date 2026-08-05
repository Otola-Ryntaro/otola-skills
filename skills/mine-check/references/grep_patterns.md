# Grep Patterns — scan_mines.sh で使う検出パターン集

`scripts/scan_mines.sh` の各カテゴリ grep の根拠と、追加検証用の派生パターンを集約。
パターンを変更した場合は本ファイルと scan_mines.sh の両方を更新する。

---

## カテゴリ別 grep パターン

### 1. prisma_destructive

```bash
grep -rEn \
  --include="*.{ts,tsx,js,jsx,sh,yml,yaml,json,md}" \
  --exclude-dir=node_modules --exclude-dir=.next --exclude-dir=docs/archives \
  'prisma migrate reset|--force-reset|--accept-data-loss|prisma migrate resolve --(applied|rolled-back)|supabase db reset' \
  .
```

派生検証:

- 環境変数経由の bypass: `PRISMA_PUSH_OVERRIDE=yes-destroy-production-data`
- 直接 `npx prisma` の使用箇所が `scripts/prisma-safe.sh` 外にないか

---

### 2. middleware_prisma

```bash
grep -rEn --include="*.{ts,tsx}" \
  --exclude-dir=node_modules --exclude-dir=.next \
  '(from\s+["'\''](@prisma/client|\.\./prisma)|new PrismaClient)' \
  middleware.ts middleware*.ts app/middleware* lib/middleware*
```

派生検証:

- DIP ポート使用: `grep -rEn 'getSubscriptionGate|registerPort' middleware*`
- subscription_status 取得方法: app_metadata 経由（R-001）か Supabase Admin Client（R-001-FB）か

---

### 3. patient_token_url

```bash
grep -rEn --include="*.{ts,tsx}" \
  --exclude-dir=node_modules --exclude-dir=.next \
  '/clinic/[^"'\'' ]+\?token=|/api/patient/session/exchange' \
  app/patient app/clinic
```

派生検証:

- 固定 QR の生成箇所が `/s/{slug}` を使っているか: `grep -rEn '/s/\$\{|/s/[a-z]' lib/services/qr*`
- sessionId 継続経路: `grep -rEn '\?session=' app/clinic`

---

### 4. env_append_echo

```bash
grep -rEn --include="*.{sh,bash,zsh,md}" \
  'echo[^|]*>>[^|]*\.env' .
```

派生検証:

- 安全形式の存在確認: `grep -rn "printf '\\\\n.*=.*' >>.*\\.env" scripts/`

---

### 5. ai_timeout_deadcode

```bash
grep -rEn --include="*.{ts,tsx}" \
  'JOB_POLICIES|GENERATE_REVIEW\.timeoutMs' \
  lib/services/inngest
```

派生検証:

- Inngest step-level 設定: `grep -rn 'step\.run\|retries:\|timeout:' lib/services/inngest`
- 削除対象 dead code か呼び出し元を確認: `grep -rn 'JOB_POLICIES' lib app`

---

### 6. postgrest_schema

```bash
grep -rEn --include="*.{ts,tsx,sql,md,yml,yaml}" \
  'pgrst\.db_schemas|NOTIFY pgrst|reload schema' .
```

派生検証:

- supabase config: `cat supabase/config.toml | grep -A2 db_schemas`
- migration 後の reload 手順 doc: `ls docs/operations/*postgrest*`

---

### 7. password_unsafe_symbols

```bash
grep -rEn --include="*.{ts,tsx}" \
  '(temp|temporary|initial)[a-zA-Z]*[Pp]assword.*[\$#%&+@=]|password.*charset.*[\$#%&+@=]' .
```

派生検証:

- password 生成関数の charset 定義: `grep -rEn 'symbols.*=|charset.*=' lib/services/*password*`
- 許容記号は `! * - _` のみ

---

### 8. gha_continue_on_error

```bash
grep -rEn --include="*.{yml,yaml}" \
  'continue-on-error|retry-on-error|max-attempts' \
  .github/workflows
```

派生検証:

- jobs 並列度の増加: `git diff main -- .github/workflows/`
- 全 workflow でクオータ消費が大きい job を特定

---

### 9. deploy_tag_missing

```bash
git log --oneline -20 | grep -vE '^\w+ (\[deploy\]|release:)'
```

派生検証:

- 本番影響コードの変更: `git diff main -- app/ lib/services/ prisma/`
- `scripts/ignore-build-step.sh` のロジック確認

---

### 10. prisma_multifile

```bash
grep -lE '^model |^datasource |^generator ' prisma/schema/*.prisma 2>/dev/null
```

派生検証:

- symlink 存在: `test -L prisma/schema/migrations && echo OK || echo MISSING`
- generator-output: `grep -rEn 'output\s*=' prisma/schema/*.prisma`

---

### 11. tenant_missing_clinicid

```bash
grep -rEn --include="*.{ts,tsx}" \
  'prisma\.[a-zA-Z]+\.(findMany|findFirst|findUnique|update|delete)\([^)]*\)' \
  app lib | grep -vE 'clinicId|tenant|where:.*clinic'
```

注意: 過剰検知が出やすいカテゴリ。LLM 二次判定で false positive を除去。

派生検証:

- `extractClinicId()` 呼び出し: `grep -rEn 'extractClinicId' app lib`
- E2E_TEST_MODE のバイパス: `grep -rn 'E2E_TEST_MODE' lib middleware*`

---

### 12. gemini_deprecated

```bash
grep -rEn --include="*.{ts,tsx,md,json}" \
  'gemini-2\.0-flash' .
```

派生検証:

- 現行モデル定義: `grep -rEn 'gemini-2\.5-flash|gemini-1\.5' lib/services/ai`

---

## 共通の grep 安全策

- `safe_grep` ラッパで exit code 1（0 件ヒット）を吸収
- `--exclude-dir=node_modules --exclude-dir=.next --exclude-dir=docs/archives` を一貫適用
- 結果は `head -50` または `head -100` で打ち切り（巨大出力を防ぐ）
- false positive 許容前提で広めにヒット → LLM 二次判定で絞る
