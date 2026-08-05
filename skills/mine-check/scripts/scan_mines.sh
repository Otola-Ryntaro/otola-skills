#!/usr/bin/env bash
# scan_mines.sh - 決定論的 grep スキャナ（mine-check Phase C 一次フィルタ）
#
# Usage:
#   bash scan_mines.sh --project-root <ABS_PATH> [--scope-files <FILE_LIST>]
#
# 出力: JSON（stdout）。検出した地雷カテゴリと該当箇所を構造化して返す。
#
# 設計方針:
# - LLM の気まぐれに依存しない決定論的層
# - false positive 許容（後段 LLM が判定）
# - エラー時も非ゼロ終了せず JSON で報告
# - macOS bash 3.2 互換（associative array 不使用）

set -u

PROJECT_ROOT=""
SCOPE_FILES=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --project-root) PROJECT_ROOT="$2"; shift 2 ;;
    --scope-files)  SCOPE_FILES="$2"; shift 2 ;;
    *) echo "Unknown arg: $1" >&2; exit 2 ;;
  esac
done

if [[ -z "$PROJECT_ROOT" || ! -d "$PROJECT_ROOT" ]]; then
  echo '{"error":"--project-root is required and must exist"}'
  exit 0
fi

cd "$PROJECT_ROOT" || { echo '{"error":"cd failed"}'; exit 0; }

json_escape() {
  python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))'
}

safe_grep() {
  grep "$@" 2>/dev/null || true
}

# 各カテゴリ実行 → tmp ファイルに保存
TMPDIR=$(mktemp -d -t mine-check.XXXXXX)
trap 'rm -rf "$TMPDIR"' EXIT

run_category() {
  local name="$1"
  local outfile="$TMPDIR/$name"
  shift
  "$@" 2>/dev/null > "$outfile" || true
}

# 1. Prisma 破壊コマンド
run_category prisma_destructive bash -c '
grep -rEn \
  --include="*.ts" --include="*.tsx" --include="*.js" --include="*.jsx" \
  --include="*.sh" --include="*.yml" --include="*.yaml" --include="*.json" --include="*.md" \
  --exclude-dir=node_modules --exclude-dir=.next --exclude-dir=docs/archives \
  "prisma migrate reset|--force-reset|--accept-data-loss|prisma migrate resolve --(applied|rolled-back)|supabase db reset" \
  . 2>/dev/null | head -100
'

# 2. middleware の Prisma 直接使用
run_category middleware_prisma bash -c '
grep -rEn \
  --include="*.ts" --include="*.tsx" \
  --exclude-dir=node_modules --exclude-dir=.next \
  "(from\s+[\"'"'"'](@prisma/client|\.\./prisma)|new PrismaClient)" \
  middleware.ts middleware*.ts app/middleware* lib/middleware* 2>/dev/null | head -50
'

# 3. 患者フロー URL 契約違反
run_category patient_token_url bash -c '
grep -rEn \
  --include="*.ts" --include="*.tsx" \
  --exclude-dir=node_modules --exclude-dir=.next \
  "/clinic/[^\"'"'"' ]+\?token=|/api/patient/session/exchange" \
  app/patient app/clinic 2>/dev/null | head -50
'

# 4. .env 改行事故
run_category env_append_echo bash -c '
grep -rEn \
  --include="*.sh" --include="*.bash" --include="*.zsh" --include="*.md" \
  "echo[^|]*>>[^|]*\.env" \
  . 2>/dev/null | head -30
'

# 5. AI provider timeout (dead code)
run_category ai_timeout_deadcode bash -c '
grep -rEn \
  --include="*.ts" --include="*.tsx" \
  "JOB_POLICIES|GENERATE_REVIEW\.timeoutMs" \
  lib/services/inngest 2>/dev/null | head -30
'

# 6. PostgREST schema cache 関連
run_category postgrest_schema bash -c '
grep -rEn \
  --include="*.ts" --include="*.tsx" --include="*.sql" --include="*.md" --include="*.yml" --include="*.yaml" \
  "pgrst\.db_schemas|NOTIFY pgrst|reload schema" \
  . 2>/dev/null | head -30
'

# 7. 仮 password の禁止記号
run_category password_unsafe_symbols bash -c '
grep -rEn \
  --include="*.ts" --include="*.tsx" \
  "(temp|temporary|initial)[a-zA-Z]*[Pp]assword.*[\$#%&+@=]|password.*charset.*[\$#%&+@=]" \
  . 2>/dev/null | head -30
'

# 8. GitHub Actions クオータ系
run_category gha_continue_on_error bash -c '
grep -rEn \
  --include="*.yml" --include="*.yaml" \
  "continue-on-error|retry-on-error|max-attempts" \
  .github/workflows 2>/dev/null | head -50
'

# 9. Vercel deploy tag
run_category deploy_tag_recent bash -c 'git log --oneline -20 2>/dev/null | head -20'

# 10. Prisma マルチファイル schema
run_category prisma_multifile bash -c 'grep -lE "^model |^datasource |^generator " prisma/schema/*.prisma 2>/dev/null | head -30'

# 11. テナント分離: Prisma クエリで clinicId なし
run_category tenant_missing_clinicid bash -c '
grep -rEn \
  --include="*.ts" --include="*.tsx" \
  "prisma\.[a-zA-Z]+\.(findMany|findFirst|findUnique|update|delete)\(" \
  app lib 2>/dev/null | grep -vE "clinicId|tenant|where:.*clinic" | head -50
'

# 12. Gemini 2.0 (廃止モデル)
run_category gemini_deprecated bash -c '
grep -rEn \
  --include="*.ts" --include="*.tsx" --include="*.md" --include="*.json" \
  "gemini-2\.0-flash" \
  . 2>/dev/null | head -30
'

# git log baseline コミット
GIT_LOG_BASELINE=$(git log --oneline -E --grep='baseline|migrate.*reset|migrate.*resolve' -10 2>/dev/null || true)

CATEGORIES="prisma_destructive middleware_prisma patient_token_url env_append_echo ai_timeout_deadcode postgrest_schema password_unsafe_symbols gha_continue_on_error deploy_tag_recent prisma_multifile tenant_missing_clinicid gemini_deprecated"

# JSON 出力
{
  echo '{'
  echo '  "scan_at": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'",'
  echo '  "project_root": '"$(printf '%s' "$PROJECT_ROOT" | json_escape)"','
  echo '  "scope_files": '"$(printf '%s' "${SCOPE_FILES:-}" | json_escape)"','
  echo '  "categories": {'
  first=1
  for key in $CATEGORIES; do
    if [[ $first -eq 0 ]]; then echo '    ,'; fi
    first=0
    val=""
    if [[ -f "$TMPDIR/$key" ]]; then
      val=$(cat "$TMPDIR/$key")
    fi
    count=0
    if [[ -n "$val" ]]; then
      count=$(printf '%s\n' "$val" | grep -c '' 2>/dev/null || echo 0)
    fi
    echo '    "'"$key"'": {'
    echo '      "count": '"$count"','
    echo '      "raw": '"$(printf '%s' "$val" | json_escape)"
    echo '    }'
  done
  echo '  },'
  echo '  "git_log_baseline": '"$(printf '%s' "$GIT_LOG_BASELINE" | json_escape)"
  echo '}'
}
