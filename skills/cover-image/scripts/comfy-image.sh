#!/bin/bash
# where: cover-image スキル / scripts/comfy-image.sh
# what : ローカル ComfyUI (SDXL) で背景アートを 1 枚生成する。usage: comfy-image.sh "<prompt>" <out.png>
# why  : 二次生成手段。ローカル・無料・API キー不要。ComfyUI 未起動なら exit 2 で上位がフォールバック判断する
set -euo pipefail

PROMPT="${1:?usage: comfy-image.sh \"<prompt>\" <out.png>}"
OUT="${2:?usage: comfy-image.sh \"<prompt>\" <out.png>}"
HOST="${COMFY_HOST:-127.0.0.1:8188}"
NEGATIVE="text, letters, typography, watermark, logo, signature, low quality, blurry"

# 起動確認（未起動 → exit 2 = フォールバックシグナル）
curl -s -m 3 "http://${HOST}/system_stats" > /dev/null || { echo "ComfyUI unreachable at ${HOST}" >&2; exit 2; }

SEED=$RANDOM$RANDOM
WORKFLOW=$(jq -n --arg p "$PROMPT" --arg n "$NEGATIVE" --argjson seed "$SEED" '{
  "1": {class_type:"CheckpointLoaderSimple", inputs:{ckpt_name:"sd_xl_base_1.0.safetensors"}},
  "2": {class_type:"CLIPTextEncode", inputs:{text:$p, clip:["1",1]}},
  "3": {class_type:"CLIPTextEncode", inputs:{text:$n, clip:["1",1]}},
  "4": {class_type:"EmptyLatentImage", inputs:{width:1280, height:640, batch_size:1}},
  "5": {class_type:"KSampler", inputs:{seed:$seed, steps:25, cfg:7, sampler_name:"euler", scheduler:"normal", denoise:1, model:["1",0], positive:["2",0], negative:["3",0], latent_image:["4",0]}},
  "6": {class_type:"VAEDecode", inputs:{samples:["5",0], vae:["1",2]}},
  "7": {class_type:"SaveImage", inputs:{filename_prefix:"cover-image", images:["6",0]}}
}')

PROMPT_ID=$(curl -s -X POST "http://${HOST}/prompt" -H 'Content-Type: application/json' \
  -d "{\"prompt\": ${WORKFLOW}}" | jq -r '.prompt_id // empty')
[ -n "$PROMPT_ID" ] || { echo "ComfyUI rejected workflow" >&2; exit 1; }

# 完了ポーリング（最大 5 分）
for _ in $(seq 1 150); do
  sleep 2
  ENTRY=$(curl -s "http://${HOST}/history/${PROMPT_ID}" | jq -r ".\"${PROMPT_ID}\" // empty")
  [ -z "$ENTRY" ] && continue
  if [ "$(echo "$ENTRY" | jq -r '.status.completed')" = "true" ]; then
    IMG=$(echo "$ENTRY" | jq -r '[.outputs[].images[]? | select(.type=="output")][0]')
    FN=$(echo "$IMG" | jq -r .filename); SUB=$(echo "$IMG" | jq -r .subfolder)
    curl -s -G "http://${HOST}/view" --data-urlencode "filename=${FN}" \
      --data-urlencode "subfolder=${SUB}" --data-urlencode "type=output" -o "$OUT"
    [ -s "$OUT" ] && { echo "saved: $OUT"; exit 0; }
    echo "download failed" >&2; exit 1
  fi
  if [ "$(echo "$ENTRY" | jq -r '.status.status_str')" = "error" ]; then
    echo "ComfyUI execution error" >&2; echo "$ENTRY" | jq -c '.status.messages' >&2; exit 1
  fi
done
echo "timeout waiting for ComfyUI" >&2; exit 1
