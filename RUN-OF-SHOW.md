# Run of show, 25 min slot (Mon 9 Nov, 11:50-12:15 MST, 250 A-C)

Deck: `deck/kubecon-na-2026-v6.pptx` (main path slides 1-14, appendix 15-23 for Q&A only). Full scripts in the speaker notes. Demo beats: `DEMO-RUNBOOK.md`. Fallback video: `deck/video/gpu-obs-demo-v6.mp4` (3:21).

| Clock | Slide | Who | What the room learns |
|---|---|---|---|
| 0:00 | 1 Cover | Danilo | (people settle) |
| 0:15 | 2 Title | both | Who we are. Thesis: the GPU dashboard said nothing, a log line had the answer |
| 1:00 | 3 Incident 02:14 | Danilo | Every GPU chart green, users waiting. The black box |
| 2:30 | 4 Utilisation | Danilo | 95% and 5% are the same useless number (Cast AI 2026, tens of thousands of clusters) |
| 3:00 | 5 GPU memory | Henrique | GPU memory is a config value: 3.5 vs 20.5 GB, flat forever |
| 4:00 | 6 Car park | Henrique | KV cache = cars in the car park. DCGM reads the sign, only the log counts the cars |
| 5:00 | 7 Pod is the join key | Danilo | Three tools, one shared field: the pod name |
| 6:30 | 8 Live: which pod is in trouble? | Danilo | Ask the room to guess |
| 7:00 | Grafana, live | Henrique clicks, Danilo narrates | 3 min: idle OK, load, red car park 100%, 12 s vs 0.13 s, verdict flips, one trace, one click to that pod's KV cache |
| 10:00 | 9 Recap | Danilo | Four numbers on one slide (also the backup if the demo dies) |
| 10:30 | 10 What broke: cardinality | Henrique | 14 series live, 56 after 3 restarts. Keep the pod name, drop other pod labels |
| 12:30 | 11 Lua: log line to metric | Danilo | Fluent Bit + 15 lines of Lua: throughput, running, waiting, KV cache per pod |
| 14:30 | 12 OTel Collector config | Danilo | k8sattributes stamps k8s.pod.name; Grafana tracesToMetrics turns it into one click |
| 16:30 | 13 Steal this | Henrique | 3 numbers, 1 filter, 1 rule, 0 new agents |
| 17:30 | 14 Thank you | Danilo | Repo + CNCF feedback QR |
| 18:00 | Q&A | both | 7 min. Appendix slides 16-23 answer the likely questions |

Abstract coverage: dcgm-exporter Kubernetes mode (7, 10), Fluent Bit enrich + Lua token throughput (11), OTel Collector multi-hop traces (12, demo), Grafana join by pod (demo, 9), over-provisioned vs memory-constrained (demo verdict), what broke: cardinality (10), deployable configs (14, repo).

Buffer: about 2 min. If the room is slow, stretch the demo; if Q&A is quiet, open appendix 16 (prefill vs decode).
