# Recording the demo (backup videos)

`record.mjs` walks the same 4 screens as the live demo (`gpu-walk-1` to `gpu-walk-4`) with the same clicks
(see `DEMO-SCRIPT.md`). Captions read live values from Prometheus and Jaeger, so they always match the screen.

| Mode | Output | Use |
|------|--------|-----|
| `CLEAN=0` (default), `PACE=1.2` | `deck/video/gpu-obs-demo-v8.mp4` | captions + spotlight boxes, works without a narrator |
| `CLEAN=1`, `PACE=1.8` | `deck/video/gpu-obs-demo-v8-clean.mp4` | no overlays, slower: talk over it on stage |

Prerequisites: rig up, `demo/start.sh` running (Grafana :3000, Jaeger :16686, Prometheus :9090), Chrome, ffmpeg,
`npm i playwright` in this folder. Best with no load in the 10 min before, so screen 1 shows idle and then the load.

```
./record-both.sh        # starts the load if none, waits until it is 4 min old, records both at once, encodes
```

`PACE` multiplies every pause. `out-fx/cues.txt` and `out-clean/cues.txt` hold the caption timelines.
