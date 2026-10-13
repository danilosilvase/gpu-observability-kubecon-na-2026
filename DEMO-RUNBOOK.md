# Demo runbook (v5): one tab, one dashboard, two clicks

KubeCon NA 2026, Mon 9 Nov, 11:50 MST, 25 min. Deck: `deck/kubecon-na-2026-v4.pptx`.

**TL;DR:** `demo/start.sh` at T-60. `demo/check.sh` at T-60 and T-5. On stage: dashboard, click one trace, click one link, back.

## Commands (that's all of them)

| When | Command | Expect |
|------|---------|--------|
| T-1 day | `cd terraform && terraform apply -auto-approve && ./validate.sh` | `14 passed / 0 failed` |
| T-60 min | `export AWS_PROFILE=<admin>` then `demo/start.sh` | dashboard opens, load running |
| T-60, T-5 | `demo/check.sh` | `7 OK, 0 FAIL` |
| T-5 | `demo/load.sh` | fresh 12-min load, new "load hits" line |
| Fallback | `demo/trace.sh` | opens the slowest trace in a tab |
| After | `demo/stop.sh`, then `terraform destroy -auto-approve` | rig costs ~$2.4/hr |

Your IP changed? Re-run the `printf ... > terraform.tfvars` line from the README, then `terraform apply -target=module.eks`.

## What is on screen

Dashboard `gpu-inference-obs`, kiosk mode, 1080p, no scrolling:

```
+------------------------------------------------------------------+
|  vllm-constrained-...  MEMORY-CONSTRAINED | vllm-overprov-... OVER-PROVISIONED |
+----------------------+----------------------+--------------------+
| 1 GPU memory (DCGM)  | 2 KV cache (log)     | 3 Queue time p95   |
|   flat, both pods    |   red hits 100%      |   red 9.6s, blue 0.3s |
+----------------------+----------------------+--------------------+
| 4 Slowest requests: constrained (~12 s) | 4 Slowest: overprov (<1 s) |
+------------------------------------------------------------------+
```
Red = constrained, blue = over-provisioned, everywhere. Orange dashed line = "load hits".

## The five beats (3 min)

| # | Time | Do | Say (short) |
|---|------|----|-------------|
| 1 | 0:00 | Stay on slide 14 | "Watch the top row. Then why." |
| 2 | 0:15 | Switch to dashboard | "GPU memory: flat. The red pod even uses less. The log says KV cache 100%. Queue: 9 seconds vs 0.3." |
| 3 | 1:30 | Click the top Trace ID (left table) | "Two hops: client, then vLLM. Same pod name on the span." |
| 4 | 2:15 | Click the chain icon on `llm_request`, then "KV cache % for this pod" | "From one slow request straight to that pod's KV cache. That is the join." |
| 5 | 2:45 | Back to dashboard, then slide 15 | "One pod name, three systems." |

Click 3 fails or is slow: run `demo/trace.sh` (pre-opened tab), or play the fallback video.

## Numbers measured on the rig (Oct 13, L4 GPUs)

| | constrained (0.15) | over-provisioned (0.90) |
|--|--|--|
| GPU memory (DCGM) | 3.5 GB, flat | 20.4 GB, flat |
| KV cache (log) | 99-100% | 0.3% |
| Queue time p95 | 9.6 s | 0.29 s |
| Request (trace) | ~11.9 s | < 1 s |

Deck slide 15 still says 3.6 GB / 0.3 s to 4.8 s: update it to these, or re-measure the night before.

## T-60 checklist

- [ ] `demo/check.sh` = 7 OK. Not 2 vLLM pods Running? Go straight to the fallback video.
- [ ] Dashboard open in kiosk, browser zoom 100-125%, on the phone hotspot (not venue Wi-Fi).
- [ ] Logged into Grafana (admin / gpu-obs-demo).
- [ ] Fallback video `gpu-obs-demo-fallback.mov` on the desktop (record it the night before, same 5 beats).
- [ ] Screenshot of the dashboard saved as a backup slide.

## Risks

| Risk | Fix |
|------|-----|
| Tunnel drops | `demo/start.sh` tunnels restart themselves |
| Load ended, charts flat | `demo/load.sh` at T-5 (load lasts 12 min) |
| GPU nodes rotated overnight | NodePool `expireAfter: 24h`: apply the evening before. Pod names change; the story does not |
| Trace table slow | Jaeger keeps 10k traces in memory to stay fast; fallback `demo/trace.sh` |
| Grafana blank or logged out | Backup screenshot slide, two clicks away |

## Open items

- Update slide 15 numbers (table above).
- Public GitHub push: needs Code Defender approval (Vijay). Do not push `research-*`.
- Record the fallback video against the v5 beats.
- Agree with Henrique on who clicks (beats 3 and 4).
