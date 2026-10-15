# Demo runbook (v6): one question, one screen, about 3 minutes

KubeCon NA 2026, Mon 9 Nov, 11:50 MST, 25 min. Deck: `deck/kubecon-na-2026-v6.pptx` (demo after slide 8).

**TL;DR:** the room is asked one question, "which pod is in trouble?", and watches three numbers per pod on one screen. GPU memory never moves; the KV cache from the log fills up; requests slow down; the verdict flips. Then one slow request, one click, to that pod's KV cache.

## Commands (that's all of them)

| When | Command | Expect |
|------|---------|--------|
| T-1 day | `cd terraform && terraform apply -auto-approve && ./validate.sh` | `14 passed / 0 failed` |
| T-60 min | `export AWS_PROFILE=<admin>` then `demo/start.sh` | dashboard opens, warm-up load runs |
| T-60, T-5 | `demo/check.sh` | `8 OK, 0 FAIL` |
| T-15 | nothing: the warm-up load must have ended 6+ min before you switch | both verdict tiles **OK**, request time **No traffic**, trace table empty (the stage view shows the last 5 min) |
| On stage, slide 8 | `demo/load.sh` | fresh 12-min load, orange "load hits" line |
| Fallback | `demo/trace.sh`, or play `deck/video/gpu-obs-demo-v6.mp4` | slowest trace in a tab / the recorded demo |
| After | `demo/stop.sh`, then `terraform destroy -auto-approve` | rig costs ~$2.4/hr |

Your IP changed? Re-run the `printf ... > terraform.tfvars` line from the README, then `terraform apply -target=module.eks`.

## What is on screen

Stage dashboard `gpu-inference-obs` (kiosk, 1080p, no scrolling). The deep dive `gpu-inference-deep` has every other panel, for Q&A.

```
+-----------------------------------------------------------------+
|  vllm-constrained-...   OK -> MEMORY-CONSTRAINED  | vllm-overprov-...  OK -> OVER-PROVISIONED |
+---------------------+---------------------+---------------------+
| GPU memory (DCGM)   | How full: KV cache  | Request time        |
| red 3.5 GB          | red 0 -> 100%       | red -> ~12 s        |
| blue 20.5 GB, flat  | blue 0%             | blue ~0.13 s        |
+---------------------+---------------------+---------------------+
| Slowest requests on the red pod (traces): click one             |
+-----------------------------------------------------------------+
```
Red = constrained, blue = over-provisioned, everywhere. Verdict = peak KV cache while the pod has traffic; no traffic = OK.

## The beats (about 3 min). Henrique clicks, Danilo talks.

| # | Time | Do | Say (short) |
|---|------|----|-------------|
| 1 | 0:00 | Slide 8, then switch to the dashboard | "Which pod is in trouble? Both say OK." |
| 2 | 0:15 | `demo/load.sh` | "Lots of long requests to red, a trickle to blue." |
| 3 | 0:30 | Point at GPU memory | "The number we page on. Flat. Red looks healthiest." |
| 4 | 0:50 | Point at KV cache (red climbs, ~40 s) | "Red's car park is full. Blue's is empty." |
| 5 | 1:30 | Point at request time, then the verdict | "12 seconds versus a tenth. Only the log could tell." |
| 6 | 1:50 | Click the top Trace ID | "One request, two hops. The Collector added the pod name." |
| 7 | 2:20 | Click the link icon on `llm_request`, then "This pod: how full it was" | "One click, that pod's car park at that second: full." |
| 8 | 2:50 | Back to the dashboard, back to slides | "Three signals, one pod name." |

Click 6 slow? Run `demo/trace.sh` (pre-opened tab). Anything else stalls: play the video, narrate with `deck/video/CUES-v6.md`.

## Numbers measured on the rig (Oct 15, NVIDIA L4)

| | constrained (0.15) | over-provisioned (0.90) |
|--|--|--|
| GPU memory (DCGM) | 3.5 GB, flat | 20.5 GB, flat |
| KV cache (log) | 99-100% | 0-0.4% |
| Request time (average, vLLM /metrics) | ~12 s | ~0.13 s |
| Slowest traces | 11.9-12.0 s | < 0.2 s |
| GPU series (cardinality) | 14 live, 56 after 3 restarts | |

## T-60 checklist

- [ ] `demo/check.sh` = 8 OK. Not 2 vLLM pods Running? Go straight to the fallback video.
- [ ] Both verdict tiles read OK at T-5 (warm-up load finished at least 3 min ago).
- [ ] Dashboard open in kiosk, browser zoom 100%, on the phone hotspot (not venue Wi-Fi).
- [ ] Logged into Grafana (admin / gpu-obs-demo).
- [ ] Fallback video on the laptop, slide 9 is the screenshot backup.
- [ ] Want the live cardinality panel (deep dive) to show 14 -> 56 in Q&A? Restart the vLLM pods 3 times in the hour before (`kubectl -n inference rollout restart deploy/vllm-constrained deploy/vllm-overprov`, wait for Running each time).

## Risks

| Risk | Fix |
|------|-----|
| Tunnel drops | `demo/start.sh` tunnels restart themselves |
| Verdict tiles still red/blue at T-5 | warm-up load still in the 3-min window: wait, or say "these are from the warm-up" |
| Tiles say "Waiting for the first log line" | Fluent Bit restarted since the last load: run `demo/load.sh` once at T-25 (12-min load + 6 min quiet) |
| GPU nodes rotated overnight | NodePool `expireAfter: 24h`: apply the evening before. Pod names change; the story does not |
| Trace table slow | Jaeger keeps 10k traces in memory to stay fast; fallback `demo/trace.sh` |
| Grafana blank or logged out | slide 9 (screenshot), then the video |
