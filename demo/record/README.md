# Recording the demo (backup video)

Records the live demo as a captioned 1920x1080 video, for use if the venue network or the rig fails.

Prerequisites: rig up, `demo/start.sh` running (Grafana :3000, Jaeger :16686, Prometheus :9090), rig idle (no loadgen job), Chrome installed, `npm i playwright` in this folder.

```
OUT=out node record.mjs          # about 5 min; starts the load itself, waits on real Prometheus values
cd out && ffmpeg -f concat -safe 0 -i frames.txt -vf "fps=30,format=yuv420p" \
  -c:v libx264 -crf 18 -movflags +faststart ../../../deck/video/gpu-obs-demo.mp4
```

`out/cues.txt` holds the caption timeline. Restart the vLLM pods a few times beforehand so the cardinality beat has "seen in the last hour" > "live now".
