# Known Landmines Catalog — kuchikomi_maker プロジェクト

過去事故・障害レポート・運用ルールから抽出した「触ると壊れる場所」のカタログ。
mine-check Phase C で `scripts/scan_mines.sh` の grep 結果と組み合わせて多重照合に使う。

各カテゴリは **検出手法 1（決定論的 grep）+ 検出手法 2（doc 照合 or git log）** の 2 つを必ず実行する。

---

## Table of Contents

1. [Prisma 破壊コマンド](#1-prisma-破壊コマンド)
2. [middleware の Prisma 直接使用](#2-middleware-の-prisma-直接使用)
3. [患者フロー URL 契約違反](#3-患者フロー-url-契約違反)
4. [.env 改行事故](#4-env-改行事故)
5. [AI provider timeout (dead code)](#5-ai-provider-timeout-dead-code)
6. [PostgREST schema cache](#6-postgrest-schema-cache)
7. [仮 password の禁止記号](#7-仮-password-の禁止記号)
8. [GitHub Actions クオータ枯渇](#8-github-actions-クオータ枯渇)
9. [Vercel デプロイタグ不使用](#9-vercel-デプロイタグ不使用)
10. [Prisma マルチファイル symlink](#10-prisma-マルチファイル-symlink)
11. [テナント分離不備](#11-テナント分離不備)
12. [Gemini 廃止モデル](#12-gemini-廃止モデル)

---

## 1. Prisma 破壊コマンド

| 項目            | 内容                                                                                                                                                |
| --------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| Severity        | 🚨 Critical                                                                                                                                         |
| 過去事故        | 2026-04-05 本番 DB 全消失（commit 481362b9 baseline 再構成中に本番 URL で `prisma migrate reset` 相当が走り、public スキーマ消失。16 日間気付かず） |
| 出典            | `docs/problem_solved/20260421_production_db_data_loss_*.md`、`memory/feedback_prisma_production_guard.md`                                           |
| 検出手法 1      | scan_mines.sh の `prisma_destructive` カテゴリ                                                                                                      |
| 検出手法 2      | `git log --oneline --grep='baseline\|migrate.*reset\|migrate.*resolve' -10` で過去の事故関連コミットと比較                                          |
| 推奨修正        | すべての破壊コマンドは `scripts/prisma-safe.sh` 経由のみ。Override は `PRISMA_PUSH_OVERRIDE=yes-destroy-production-data` のみ許可                   |
| チケット PREFIX | `DB-`                                                                                                                                               |

---

## 2. middleware の Prisma 直接使用

| 項目            | 内容                                                                                                                                                                                                     |
| --------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Severity        | 🚨 Critical                                                                                                                                                                                              |
| 過去事故        | 2026-03-28 Vercel 500（middleware の Prisma engine binary 未含 + DIP ポート未登録）                                                                                                                      |
| 出典            | `docs/problem_solved/20260328_middleware_*.md`、`memory/feedback_no_prisma_in_middleware.md`、`.claude/error-patterns/dip-port-unregistered.md`、`.claude/error-patterns/prisma-query-engine-missing.md` |
| 検出手法 1      | scan_mines.sh の `middleware_prisma` カテゴリ                                                                                                                                                            |
| 検出手法 2      | DIP ポート使用検出: `grep -rn "getSubscriptionGate\|registerPort" middleware*`                                                                                                                           |
| 推奨修正        | middleware からは Prisma を import しない。代わりに Supabase Admin Client（HTTP ベース）を使う。R-001-FB の self-healing パターン参照                                                                    |
| チケット PREFIX | `SEC-`                                                                                                                                                                                                   |

---

## 3. 患者フロー URL 契約違反

| 項目            | 内容                                                                                                 |
| --------------- | ---------------------------------------------------------------------------------------------------- |
| Severity        | ⚠️ Warning                                                                                           |
| 過去事故        | 2026-04-18 E2E-107 auth/session 失敗、患者フロー URL が token 露出する旧パターン混入                 |
| 出典            | `docs/problem_solved/20260418_e2e_auth_*.md`、`CLAUDE.md` 「患者アクセス URL 契約」                  |
| 検出手法 1      | scan_mines.sh の `patient_token_url` カテゴリ                                                        |
| 検出手法 2      | CLAUDE.md の「患者アクセス URL 契約」節と照合し、固定 QR が `/s/{slug}` を正本としているか確認       |
| 推奨修正        | 固定 QR は `/s/{slug}` を正本に。token は患者ブラウザに再露出させない。`sessionId` で継続（TTL 72h） |
| チケット PREFIX | `SEC-`                                                                                               |

---

## 4. .env 改行事故

| 項目            | 内容                                                                                        |
| --------------- | ------------------------------------------------------------------------------------------- |
| Severity        | ⚠️ Warning                                                                                  |
| 過去事故        | `echo "VALUE" >> .env` で末尾改行なしファイルに append し、前行と結合する事故（複数回経験） |
| 出典            | `memory/feedback_env_append_newline.md`                                                     |
| 検出手法 1      | scan_mines.sh の `env_append_echo` カテゴリ                                                 |
| 検出手法 2      | `printf` 不使用パターン: `grep -rEn 'echo[^\|]*\.env' scripts/ docs/`                       |
| 推奨修正        | `printf '\n%s\n' "KEY=VAL" >> .env` を使う。`echo` は禁止                                   |
| チケット PREFIX | `BUG-`                                                                                      |

---

## 5. AI provider timeout (dead code)

| 項目            | 内容                                                                                                                                       |
| --------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| Severity        | 🚨 Critical（再発時）                                                                                                                      |
| 過去事故        | 2026-04-29 患者ユーザー全員 AI 生成失敗。`JOB_POLICIES.GENERATE_REVIEW.timeoutMs = 8000` を信用したが Inngest 経路から呼ばれない dead code |
| 出典            | `docs/problem_solved/20260429_ai_provider_timeout.md`（v1.40.2 リリース）                                                                  |
| 検出手法 1      | scan_mines.sh の `ai_timeout_deadcode` カテゴリ                                                                                            |
| 検出手法 2      | Inngest step-level の `timeout` / `retries` 設定が正本になっているか: `grep -rn 'step.run\|retries:\|timeout:' lib/services/inngest`       |
| 推奨修正        | `JOB_POLICIES` のタイムアウト記述を信用しない。Inngest の step-level 設定を正本とする。dead code は削除                                    |
| チケット PREFIX | `BUG-`                                                                                                                                     |

---

## 6. PostgREST schema cache

| 項目            | 内容                                                                                                                                                             |
| --------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Severity        | ⚠️ Warning                                                                                                                                                       |
| 過去事故        | 2026-04-15 e2e 全テスト雪崩（PGRST205）。CI セットアップで Prisma 実行後に PostgREST schema cache reload 漏れ                                                    |
| 出典            | `docs/problem_solved/20260415_postgrest_schema_cache.md`、`.claude/error-patterns/ci-prisma-supabase-database-mismatch.md`、`memory/project_postgrest_schema.md` |
| 検出手法 1      | scan_mines.sh の `postgrest_schema` カテゴリ                                                                                                                     |
| 検出手法 2      | migration 追加 PR で `pgrst.db_schemas` 設定 + `NOTIFY pgrst, 'reload schema'` 手順がチェックリスト化されているか確認                                            |
| 推奨修正        | migration を伴う変更は `docs/operations/prisma-safety-guardrails.md` の手順を踏む。`pgrst.db_schemas` に `public` 含むこと                                       |
| チケット PREFIX | `DB-`                                                                                                                                                            |

---

## 7. 仮 password の禁止記号

| 項目            | 内容                                                                                                                            |
| --------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| Severity        | ⚠️ Warning                                                                                                                      |
| 過去事故        | 仮パスワードに `$ # % & + @ =` を含めるとメール本文で化ける                                                                     |
| 出典            | `memory/feedback_password_email_safe.md`                                                                                        |
| 検出手法 1      | scan_mines.sh の `password_unsafe_symbols` カテゴリ                                                                             |
| 検出手法 2      | password 関連サービス層（`lib/services/*password*`, `lib/auth/*`）の symbol set を読み、許容記号 `! * - _` のみであることを確認 |
| 推奨修正        | 仮 password 生成の symbol set を `! * - _` のみに制限                                                                           |
| チケット PREFIX | `BUG-`                                                                                                                          |

---

## 8. GitHub Actions クオータ枯渇

| 項目            | 内容                                                                                                                                                          |
| --------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Severity        | ⚠️ Warning                                                                                                                                                    |
| 過去事故        | 2026-04-30 GA クオータ枯渇 → CI 実行停止                                                                                                                      |
| 出典            | `docs/problem_solved/20260430_github_actions_quota.md`、`.claude/error-patterns/github-actions-quota-exhausted.md`、`memory/feedback_github_actions_quota.md` |
| 検出手法 1      | scan_mines.sh の `gha_continue_on_error` カテゴリ                                                                                                             |
| 検出手法 2      | jobs 並列度の増加: `git diff main -- .github/workflows/` で `strategy: matrix` の追加・jobs ブロック追加を確認                                                |
| 推奨修正        | push 前ローカル検証必須、不要な re-run 禁止、`continue-on-error` の追加は明示的レビュー必須                                                                   |
| チケット PREFIX | `OPS-`                                                                                                                                                        |

---

## 9. Vercel デプロイタグ不使用

| 項目            | 内容                                                                                                                                   |
| --------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| Severity        | ℹ️ Info                                                                                                                                |
| 過去事故        | デプロイ節約のため `[deploy]` タグまたは `release:` で始まるコミットのみビルド。タグなしで本番影響コードを push するとデプロイされない |
| 出典            | `memory/feedback_deploy_cost_saving.md`、`scripts/ignore-build-step.sh`                                                                |
| 検出手法 1      | 本番影響あるコード変更（`app/`, `lib/services/`, `prisma/`）                                                                           |
| 検出手法 2      | コミットメッセージに `[deploy]` または `release:` プレフィックスがあるか git log で確認                                                |
| 推奨修正        | `/vpush` 経由で `release:` コミット、または手動で `[deploy]` タグ                                                                      |
| チケット PREFIX | `OPS-`                                                                                                                                 |

---

## 10. Prisma マルチファイル symlink

| 項目            | 内容                                                                                                             |
| --------------- | ---------------------------------------------------------------------------------------------------------------- |
| Severity        | ⚠️ Warning                                                                                                       |
| 過去事故        | Prisma マルチファイル schema 採用後、`prisma/schema/migrations/` シンボリックリンク欠落で migration 実行が壊れた |
| 出典            | `memory/feedback_prisma_multifile_migrations.md`                                                                 |
| 検出手法 1      | scan_mines.sh の `prisma_multifile` カテゴリ                                                                     |
| 検出手法 2      | symlink 存在確認: `test -L prisma/schema/migrations && echo OK`                                                  |
| 推奨修正        | マルチファイル schema 採用時は `prisma/schema/migrations` symlink 必須。pre-commit でチェック                    |
| チケット PREFIX | `DB-`                                                                                                            |

---

## 11. テナント分離不備

| 項目            | 内容                                                                                                                                         |
| --------------- | -------------------------------------------------------------------------------------------------------------------------------------------- |
| Severity        | 🚨 Critical                                                                                                                                  |
| 過去事故        | 多テナント SaaS でテナント分離は最重要。Prisma クエリで `clinicId` フィルタなしで実行すると他テナントデータ漏洩のリスク                      |
| 出典            | `CLAUDE.md`「人物定義」「患者アクセス URL 契約」、`docs/architecture/review-checklist.md`、`docs/operations/patient-flow-rollout-runbook.md` |
| 検出手法 1      | scan_mines.sh の `tenant_missing_clinicid` カテゴリ（過剰検知が出やすい、LLM 二次判定で絞る）                                                |
| 検出手法 2      | `extractClinicId()` を経由して取得した `clinicId` を where 句に渡しているか個別 review。E2E_TEST_MODE 系のバイパスがないかも確認             |
| 推奨修正        | 全テナント横断クエリは管理画面・テスト時のみ。runbook で分離検証                                                                             |
| チケット PREFIX | `SEC-`                                                                                                                                       |

---

## 12. Gemini 廃止モデル

| 項目            | 内容                                                                                                      |
| --------------- | --------------------------------------------------------------------------------------------------------- |
| Severity        | ℹ️ Info                                                                                                   |
| 過去事故        | `gemini-2.0-flash` は API 廃止済み。コード残骸は将来エラー                                                |
| 出典            | `memory/feedback_no_gemini_2_0.md`、`memory/project_gemini_newline_literal.md`                            |
| 検出手法 1      | scan_mines.sh の `gemini_deprecated` カテゴリ                                                             |
| 検出手法 2      | LLM ルーティング config（`lib/llm/*` または `lib/services/ai/*`）の選択肢に廃止モデルが残っていないか確認 |
| 推奨修正        | `gemini-2.5-flash` 以降のモデルに置換                                                                     |
| チケット PREFIX | `BUG-`                                                                                                    |

---

## 追加カテゴリの登録方法

新規発見した地雷は `references/new_pattern_template.md` の形式で `<project>/.claude/error-patterns/<slug>.md` に登録 → INDEX 更新 → 本ファイルに 1 セクション追加。
