#!/bin/bash
# where: cover-image スキル / scripts/codex-image.sh
# what : Codex CLI の組み込み image_gen で背景アートを 1 枚生成する。usage: codex-image.sh "<prompt>" <out.png>
# why  : 一次生成手段。ChatGPT ログインで動き API キー不要。codex が使えなければ exit 2 で上位がフォールバック判断する
set -euo pipefail

PROMPT="${1:?usage: codex-image.sh \"<prompt>\" <out.png>}"
OUT="${2:?usage: codex-image.sh \"<prompt>\" <out.png>}"
TIMEOUT_SEC="${CODEX_IMAGE_TIMEOUT:-300}"
IMAGES_DIR="${CODEX_HOME:-$HOME/.codex}/generated_images"

# 利用可否の確認（未導入 → exit 2 = フォールバックシグナル）
command -v codex > /dev/null || { echo "codex CLI not found" >&2; exit 2; }

WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT

# stdin を閉じないと codex exec は入力待ちで止まる
codex exec --skip-git-repo-check --ephemeral -s read-only -C "$WORK" --json \
  "Use the built-in image_gen tool once to generate this image: ${PROMPT} Do not run any other tool. Then reply with only the word DONE." \
  < /dev/null > "$WORK/events.jsonl" 2> "$WORK/err.txt" &
CODEX_PID=$!

# macOS には timeout コマンドがないので自前で打ち切る。呼び出し側のパイプを塞がないよう出力は捨てる
( sleep "$TIMEOUT_SEC"; kill "$CODEX_PID" ) > /dev/null 2>&1 &
WATCHDOG_PID=$!

STATUS=0
wait "$CODEX_PID" || STATUS=$?
kill "$WATCHDOG_PID" 2> /dev/null || true
wait "$WATCHDOG_PID" 2> /dev/null || true
[ "$STATUS" -eq 0 ] || { echo "codex exec failed (status ${STATUS}): $(tail -3 "$WORK/err.txt")" >&2; exit 1; }

# 他の Codex セッションも同じ場所へ保存するので、最新ファイルではなくスレッド ID で特定する
THREAD_ID=$(grep '"thread.started"' "$WORK/events.jsonl" | head -1 | jq -r '.thread_id // empty')
[ -n "$THREAD_ID" ] || { echo "codex thread id not found" >&2; exit 1; }
IMAGE=$(ls -t "$IMAGES_DIR/$THREAD_ID"/*.png 2> /dev/null | head -1 || true)
[ -n "$IMAGE" ] || { echo "codex produced no image (thread ${THREAD_ID})" >&2; exit 1; }

mkdir -p "$(dirname "$OUT")"
cp "$IMAGE" "$OUT"
echo "saved: $OUT"
