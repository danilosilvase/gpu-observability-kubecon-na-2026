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

## Measured Oct 16 (equal traffic, NVIDIA L4, opt-125m)

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

## Still open
- Timed rehearsal of DEMO-SCRIPT.md (target 10 min).
- Henrique's 5 slides.
- Who clicks (default in the script: Danilo clicks and talks).
- Stage dashboard `gpu-inference-obs` is Q&A only now; its title "Which pod is in trouble?" can stay.
- Original author name. GitHub publish (Code Defender, before Nov 2).
