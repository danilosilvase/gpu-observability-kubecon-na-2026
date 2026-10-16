#!/usr/bin/env bash
# Records the backup video twice, at the same time, during the same load:
#   gpu-obs-demo-v7.mp4        captions + spotlight boxes (works without a narrator)
#   gpu-obs-demo-v7-clean.mp4  same clicks and timing, no overlays (talk over it live)
# Same 4 screens (gpu-walk-1..4) and same load as the live demo. Needs demo/start.sh tunnels, Chrome,
# `npm i playwright` in this folder, ffmpeg.  WARMUP = seconds of load before recording starts (live: 4-6 min).
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"; REPO="$HERE/../.."; cd "$HERE"
WARMUP="${WARMUP:-240}"; VID="$REPO/deck/video"
PACE_FX="${PACE_FX:-1.2}"; PACE_CLEAN="${PACE_CLEAN:-1.8}"   # clean is slower: room to talk (and pause)
for u in localhost:3000/api/health localhost:9090/-/ready localhost:16686/; do
  curl -s -m 5 -o /dev/null "http://$u" || { echo "tunnel down: $u (run demo/start.sh)"; exit 1; }; done

start=$(kubectl --request-timeout=20s -n inference get job vllm-loadgen -o jsonpath='{.status.startTime}' 2>/dev/null || true)
if [ -z "$start" ] || [ "$(kubectl --request-timeout=20s -n inference get job vllm-loadgen -o jsonpath='{.status.active}')" != "1" ]; then
  "$REPO/demo/load.sh"; start=$(date -u +%Y-%m-%dT%H:%M:%SZ)
fi
age=$(( $(date -u +%s) - $(date -ju -f %Y-%m-%dT%H:%M:%SZ "$start" +%s) ))
[ "$age" -gt 540 ] && { echo "load is ${age}s old; the recording needs ~10 min of it. Restart: demo/load.sh"; exit 1; }
[ "$age" -lt "$WARMUP" ] && { echo "load is ${age}s old, waiting $((WARMUP - age))s"; sleep $((WARMUP - age)); }

CLEAN=0 PACE=$PACE_FX    OUT=out-fx    node record.mjs > out-fx.log 2>&1 &   fx=$!
CLEAN=1 PACE=$PACE_CLEAN OUT=out-clean node record.mjs > out-clean.log 2>&1 & cl=$!
wait $fx; wait $cl
for v in fx:gpu-obs-demo-v7 clean:gpu-obs-demo-v7-clean; do
  ( cd "out-${v%%:*}" && ffmpeg -loglevel error -y -f concat -safe 0 -i frames.txt -vf "fps=30,format=yuv420p" \
      -c:v libx264 -crf 18 -movflags +faststart "$VID/${v#*:}.mp4" )
done
cp out-fx/cues.txt "$VID/cues-v7.txt"
ls -la "$VID"/gpu-obs-demo-v7*.mp4
