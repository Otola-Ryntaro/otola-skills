#!/usr/bin/env bash
# where: project-hero/scripts/gemini-image.sh
# what : Gemini API (gemini-2.5-flash-image) で背景アートを1枚生成する
# why  : oracle/ChatGPT 画像生成が失敗・枯渇した場合のフォールバック経路
set -euo pipefail

PROMPT="${1:?usage: gemini-image.sh \"<prompt>\" <output.png>}"
OUT="${2:?usage: gemini-image.sh \"<prompt>\" <output.png>}"

KEY="${GEMINI_API_KEY:-}"
if [[ -z "$KEY" && -f "$HOME/.gemini/api_key" ]]; then
  KEY="$(cat "$HOME/.gemini/api_key")"
fi
if [[ -z "$KEY" ]]; then
  echo "ERROR: GEMINI_API_KEY が未設定です（env または ~/.gemini/api_key）" >&2
  exit 2
fi

RESP="$(mktemp)"
trap 'rm -f "$RESP"' EXIT

curl -sS -X POST \
  "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-image:generateContent" \
  -H "x-goog-api-key: $KEY" \
  -H "Content-Type: application/json" \
  -d "$(python3 -c 'import json,sys; print(json.dumps({
    "contents":[{"parts":[{"text": sys.argv[1]}]}],
    "generationConfig":{"responseModalities":["IMAGE"]}
  }))' "$PROMPT")" > "$RESP"

python3 - "$RESP" "$OUT" <<'PY'
import base64, json, sys
resp = json.load(open(sys.argv[1]))
try:
    parts = resp["candidates"][0]["content"]["parts"]
    data = next(p["inlineData"]["data"] for p in parts if "inlineData" in p)
except (KeyError, IndexError, StopIteration):
    print("ERROR: 画像データが返りませんでした:", json.dumps(resp)[:500], file=sys.stderr)
    sys.exit(1)
open(sys.argv[2], "wb").write(base64.b64decode(data))
print("saved:", sys.argv[2])
PY
