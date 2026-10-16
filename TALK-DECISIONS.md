# Talk decisions (grill session, Oct 16 2026)

Inference Is a Black Box, KubeCon NA Observability Day, Mon 9 Nov, 25-min slot (~20 min talk). Speakers: Henrique Santana (session owner), Danilo.

| # | Decision |
|---|---|
| 1 | Takeaway: GPU memory cannot tell you an inference server is in trouble. Read the server's own signal. Opening hook and closing line. |
| 2 | Why the log: "the signal you already ship" (Fluent Bit already collects every pod's log). No claimed customer story. Live cross-check tile: log value matches vLLM /metrics. |
| 3 | Origin: an experiment on a test cluster we built (say so in the first 30 s). Credit the original author on the closing slide: placeholder [original author] until the name is confirmed. |
| 4 | Demo question: "Is 8% too low? Is 90% too high? How would you know?" Answer = method: watch peak KV cache under real traffic. Thresholds (>90% constrained, <40% over-provisioned) are our rule of thumb, said on stage. |
| 5 | Opening: cold-open vote (D), then after the reveal one line of what happened to us (A): "it took unique prompts to make it struggle, and the GPU dashboard never noticed". |
| 6 | Split: Henrique 5 slides (~9 min) = story; Danilo demo (~10-11 min) = build. Henrique: 1 vote, 2 the usual four (CPU/mem/net/disk) do not see it + vLLM reserves 92% by default, 3 what runs out first (KV cache, buffer-pool analogy, generic box picture, no spoiler), 4 what broke while we built it, 5 take this home + repo + credit. |
| 7 | Demo = 4 screens, same layout (question, <=6-line config with 1 highlighted line, 1 red/blue chart, 1 sentence): GPU (dcgm --kubernetes), log (Lua KV line + tokens/s tile + /metrics cross-check), trace (k8s.pod.name, one click), answer (verdict). |
| 8 | Fair experiment: SAME traffic to both pods (192 long requests each), red at 0.08 (was 0.15), user-facing number = time to first token (not average request time). |
| 9 | Intro structure borrowed from Jimmy Song's GPU-to-token post (paradox, known-to-new bridge, buffer-pool analogy). Not named on stage; footnote on slide 3 + further-reading link. |

## Measured Oct 16 (equal traffic, NVIDIA A10G 24 GB on g5.xlarge, opt-125m; the NodePool allows g5 or g6, so pin it before the talk)

| | red 0.08 | blue 0.90 |
|---|---|---|
| GPU memory (DCGM) | 2.0 GB flat | 20.6 GB flat |
| Peak KV cache | 100% | 31% |
| Running / waiting | 49 / 143 | 191 / 0 |
| Tokens/s | 9,500 | 12,200 |
| Time to first token | 5.9 s | 0.08 s |
| Total request time | 7.8 s | 6.1 s |

Retired: 0.15 + unequal traffic (12 s vs 0.13 s came from the traffic split), car park analogy, 95%/5% utilisation slide, deck v6 main path.

## 10. Live, with a recorded twin (Oct 16)
Live by default. One setup: the 4 walkthrough screens `gpu-walk-1..4` (build_walkthrough.py), the same load (`demo/load.sh`,
started when Henrique opens the talk so it is 4-6 min old at the demo). The recording walks the same screens with the same clicks,
in two versions recorded at the same time during the same load: captioned + spotlight (works without a narrator) and clean
(slower, no overlays, to talk over on stage). Script: DEMO-SCRIPT.md. Runbook: DEMO-RUNBOOK.md.

## 11. Who clicks (Oct 16)
Danilo drives and talks on all 4 screens. Henrique stays on the slides laptop. No hand-offs mid-demo.

## 12. Longer demo by showing more, not by waiting (Oct 16)
About 9 min without slowing down: the load starts on camera on screen 1 (GPU memory stays flat as requests arrive),
red's KV cache fills while screen 2 is explained, and screen 3 adds one blue trace next to the red one (queue time contrast).
Next candidate: a green "right number" pod (screen 5), after a GPU capacity check on the rig. Supersedes "load starts at Henrique slide 1".

## Slides (grill, Oct 16): template = Observability Day NA 2026 branded PowerPoint
S1. Cold-open vote (Henrique, slide 1): "Two vLLM pods. Same model, same GPU type, same traffic. One reserved 8% of GPU memory,
the other 90%. Which one is in trouble?" Hands up: 8% / 90% / both / can't tell. NO reveal on slide 1 ("Hold that. Danilo
will answer it live."). Reveal = demo screen 4. Slide 5 calls back: "Who voted both?". The "what happened to us" line moves
to after the demo (opens slide 4). Supersedes decision 5's reveal timing. Fact checked: vLLM default gpu_memory_utilization = 0.92
(vllm/config/cache.py, main).

S2. Slide 2 = "GPU memory is a setting, not a signal". Four grey tiles (CPU, memory, network, disk) say what they MEASURE
(node/container resources), no fake green numbers; fifth tile: GPU memory flat at 92% "set at startup". Footnote: vLLM default 0.92.
S3. Slide 3 = "What runs out first: room for requests in flight". CONNECTION POOL analogy (replaces buffer pool: a full buffer
pool is healthy, the opposite lesson): pool size = --gpu-memory-utilization, in use = KV cache %, waiting = requests waiting,
latency climbs while GPU memory is flat. Generic GPU box (weights | KV cache | rest) + pool/queue sketch, no pod named.
Bottom line: "vLLM tells you how full it is, every 10 seconds, in its log." Jimmy Song footnote stays.
S4. Slide 4 = opener (prefix caching: identical prompts shared the cache, only unique prompts made it struggle) + cardinality
(promised in the abstract: 14 live -> 56 after 3 rollouts) + unfair experiment (12 s vs 0.13 s -> equal traffic 5.9 s vs 0.08 s;
first to cut, else backup slide). Rows: what we saw / what we changed. No charts.
S5. Close = two slides. Slide 5 "Take this home": "Who voted both? You were right.", takeaway, one config line per component
(dcgm --kubernetes=true, Fluent Bit Lua KV match, k8sattributes k8s.pod.name), rule of thumb, repo QR. Slide 6 "Questions":
CNCF feedback QR, credit [original author], Jimmy Song further reading. GitHub repo WILL be public (Danilo owns it).

S6. ONE laptop on stage (Danilo's): deck in PowerPoint (Extended display, notes) + Grafana + terminal; Henrique uses a clicker
(bring one); Cmd+Tab in/out of the demo. BOTH laptops fully set up for redundancy (deck, demo access to the rig account,
kubectl, tunnels, Grafana login, both videos); Henrique runs demo/check.sh on his laptop before Oct 22.
S7. Bridge slide after slide 3: vote question large + strip "1 GPU > 2 Log > 3 Trace > 4 Answer" (same as the dashboards);
Henrique: "Danilo, which one is in trouble?". Out of the demo: Cmd+Tab straight to slide 4 (no thank-you slide).
Hidden backup slide after the bridge: static screen-4 image (verdict, 2.0/20.6 GB, 100%/31%, 5.9 s/0.08 s).
S8. Title slide: accepted abstract title verbatim. Henrique Santana, Principal Cloud Engineer, AWS; Danilo Silva, Senior
Delivery Consultant, AWS. No logos. TODO Henrique: Sessionize still says "Danilo Souza", fix to Danilo Silva.
S9. Speaker notes = short cues + timing + click counts. Budget: title 0:00, vote 0:30, S2 2:00, S3 3:30, demo 6:00-15:00,
what broke 15:00, take home 17:30, Q&A 19:30 (5:30). Native PowerPoint animations on every slide, fade transitions.
S10. "Take this home" (S5) split into three animated slides, 2:00 total: 5a "Who voted both? You were right." (Pod A too small,
Pod B too big, takeaway), 5b "Three lines of config, one join key" (dcgm / Fluent Bit / OTel cards, arrows converge on pod name),
5c "Size it from peak KV cache" (gauge 0-40 too big / 40-90 about right / 90+ too small, Pod A lands at 100%, Pod B at ~30%,
rule of thumb is ours, repo QR).

## Still open
- Timed rehearsal of DEMO-SCRIPT.md (target 10 min).
- Henrique's 5 slides.
- Stage dashboard `gpu-inference-obs` is Q&A only now; its title "Which pod is in trouble?" can stay.
- Original author name. GitHub publish (Code Defender, before Nov 2).
