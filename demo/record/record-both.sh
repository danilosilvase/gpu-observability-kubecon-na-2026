#!/usr/bin/env bash
# Records the backup video twice, at the same time, during the same load:
#   gpu-obs-demo-v7.mp4        captions + spotlight boxes (works without a narrator)
#   gpu-obs-demo-v7-clean.mp4  same clicks and timing, no overlays (talk over it live)
# Same 4 screens (gpu-walk-1..4), same clicks and same on-camera load start as the live demo (DEMO-SCRIPT.md).
# Needs demo/start.sh tunnels, Chrome, `npm i playwright` in this folder, ffmpeg, and an IDLE rig: no load in the
# last 10 min, so screen 1 shows idle and then the load arriving. The captioned run starts the load itself.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"; REPO="$HERE/../.."; cd "$HERE"
VID="$REPO/deck/video"; mkdir -p "$VID"
PACE_FX="${PACE_FX:-1.2}"; PACE_CLEAN="${PACE_CLEAN:-1.8}"   # clean is slower: room to talk (and pause)
for u in localhost:3000/api/health localhost:9090/-/ready localhost:16686/; do
  curl -s -m 5 -o /dev/null "http://$u" || { echo "tunnel down: $u (run demo/start.sh)"; exit 1; }; done
[ "$(kubectl --request-timeout=20s -n inference get job vllm-loadgen -o jsonpath='{.status.active}' 2>/dev/null)" = 1 ] && {
  echo "a load is running: demo/stop.sh, then wait 10 min so screen 1 starts idle"; exit 1; }

rm -rf .sync
SYNC=.sync START_LOAD=1 CLEAN=0 PACE=$PACE_FX    OUT=out-fx    node record.mjs > out-fx.log 2>&1 &   fx=$!
SYNC=.sync START_LOAD=0 CLEAN=1 PACE=$PACE_CLEAN OUT=out-clean node record.mjs > out-clean.log 2>&1 & cl=$!
# SYNC: both start recording together; steps before the load use fixed timing, so both see it start at the same second
rc=0; wait $fx || rc=$?; wait $cl || rc=$?
[ $rc -eq 0 ] || { tail -5 out-fx.log out-clean.log; exit $rc; }
for v in fx:gpu-obs-demo-v7 clean:gpu-obs-demo-v7-clean; do
  ( cd "out-${v%%:*}" && ffmpeg -loglevel error -y -f concat -safe 0 -i frames.txt -vf "fps=30,format=yuv420p" \
      -c:v libx264 -crf 18 -movflags +faststart "$VID/${v#*:}.mp4" )
done
python3 cues.py out-fx/cues.txt out-clean/cues.txt "$VID/CUES-v7.md"   # chapter times for both videos
ls -la "$VID"/gpu-obs-demo-v7*.mp4
