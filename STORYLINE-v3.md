# Storyline v3 (Oct 6 2026) - "Inference Is a Black Box"

Reason for v3: author feedback. v2 made the plumbing the hero (how to wire DCGM + Fluent Bit + OTel).
An Observability Day audience already knows how to ship signals. What they do not know is what GPU
inference telemetry means and where the useful signal lives. v3 keeps the three-signal pipeline as the
means and makes the message: "the signal that explains inference behaviour is not in any exporter; it
is in the serving framework's log line, and a 15-line Lua filter turns it into a per-pod metric you can
correlate with GPU counters and traces."

Slot: 25 min incl. Q&A -> 21 min talk, 4 min Q&A. Fixed abstract, title unchanged.

## Arc (21 min)

| # | Section | Min | Message | Demo / artefact |
|---|---------|-----|---------|-----------------|
| 1 | The black box | 2 | p99 doubled. GPU util 95%, FB used 90%, both flat for an hour. Dashboards green. Nobody knows why. | Opening Grafana screenshot (fake incident, real panels) |
| 2 | Why GPU metrics lie for inference | 5 | vLLM pre-allocates FB at start (gpu-mem-util), so FB used never moves. "GPU util" = any kernel active in the sample window, not occupancy. Prefill vs decode have opposite profiles (compute-bound vs memory-bandwidth-bound). The counters that matter: DCGM_FI_PROF_SM_ACTIVE, SM_OCCUPANCY, DRAM_ACTIVE, PCIE/NVLINK; the ones that mislead: GPU_UTIL, FB_USED on a pre-allocating server. | One table slide: "misleading vs meaningful counters" |
| 3 | Signal 1: DCGM per pod | 3 | DCGM tells you WHICH pod owns the GPU and whether the silicon is busy. It cannot tell you why. Cardinality trap: ENABLE_POD_LABELS multiplies series by pod churn, allowlist the join key only. | Keep v2 slides 7-9 (kubelet pod mapping, join on fixed part, cardinality numbers) |
| 4 | Signal 2: the serving log IS the telemetry | 6 | vLLM emits one stats line every ~10 s: gen tokens/s, prompt tokens/s, running, waiting, GPU KV cache %. None of this is in DCGM. KV cache % is the real "GPU full" for an LLM server; waiting = queue depth, latency rises here first. Lua filter in Fluent Bit: match the line, string.match five fields, emit record with pod_name, Prometheus exporter output. Same technique for TGI/Triton/SGLang. | LIVE: start saturating loadgen on vllm-constrained. Watch KV cache % go to ~100 and waiting climb while DCGM FB/util stay flat. Show the Lua (15 lines) on one slide |
| 5 | Signal 3: traces from the serving path | 3 | Per-request latency, stamped with pod name by k8sattributes. A slow span alone is not actionable; a slow span on the pod whose KV cache was at 100% at that second is. | LIVE: Jaeger, slow trace on vllm-constrained during saturation, fast on vllm-overprov |
| 6 | The join | 2 | One Grafana row, three sources, same pod_name. Point at the moment: KV cache pegs -> waiting climbs -> span latency jumps -> DCGM unchanged. That is the black box opened. | LIVE: dashboard v3 row |
| 7 | Steal this | 1 | Three counters to watch (SM_ACTIVE, KV cache %, waiting). One Lua filter. Repo link. Attribution to original author. | Keep v2 slide 16-17 |

## Slide mapping from v2 (17 slides)

| v2 slide | Title | v3 action |
|----------|-------|-----------|
| 1 | Inference is a black box | KEEP |
| 2 | The page fires, three tabs | REWRITE: the incident now = latency doubled, all GPU counters flat |
| 3 | Three signals, zero connection | REWRITE: becomes "the counters you have say nothing" |
| 4 | GPU utilization % lies | EXPAND to section 2 (2-3 slides: pre-allocation, util vs occupancy, prefill vs decode, counter table) |
| 5 | The pod is the join key | KEEP, move after section 2 |
| 6 | Three pipelines, one join key | KEEP, shorten |
| 7 | Same string, three pipelines | KEEP |
| 8 | Pod mapping comes from the kubelet | KEEP |
| 9 | Join on the fixed part | KEEP (TODO real cardinality numbers still open) |
| 10 | Tokens/s parsed out of stdout | REWRITE: becomes the centrepiece. "The log line is the telemetry": show the raw line, the five fields, the Lua. 2 slides |
| 11 | Stamp the pod name on every span | KEEP, shorten |
| 12 | Two pods | REWRITE: demo set-up, constrained vs over-provisioned, what we are about to saturate |
| 13 | Same throughput, 3x the memory | REPLACE: "KV cache 100%, queue climbing, DCGM asleep" (demo result) |
| 14 | A slow span becomes actionable | KEEP, tie to KV cache saturation moment |
| 15 | What silently broke | KEEP but cut to one gotcha (Fluent Bit tag prefix), drop GPU Operator unless time |
| 16 | Steal this | KEEP, add the three counters + Lua as takeaways |
| 17 | One link | KEEP |

Net: ~18 slides, 2 fewer plumbing slides, 4 more semantics slides.

## Rig changes needed

1. loadgen: second profile that saturates KV cache on vllm-constrained. opt-125m at gpu-mem-util 0.30 on g6.xlarge (24 GB) leaves ~7 GB for KV; drive long prompts (1-2k tokens) with concurrency 64-128 and max_tokens 256+ until "GPU KV cache usage" approaches 100% and Waiting > 0. Keep the existing 12-min steady profile for the overprov pod as the control.
2. Fluent Bit: already extracts kv_cache_usage_pct, waiting_reqs, running_reqs. Confirm they reach Prometheus (check the prometheus_exporter output / metric names).
3. Grafana dashboard v3: new row "What the log knows" with KV cache %, waiting reqs, running reqs per pod, next to DCGM_FI_PROF_SM_ACTIVE and FB_USED per pod and the trace-latency panel. The "aha" row.
4. DCGM: confirm the profiling counters (DCGM_FI_PROF_SM_ACTIVE / SM_OCCUPANCY / DRAM_ACTIVE) are in the dcgm-exporter metrics csv; g6 (L4) supports them.
5. Validate: run saturating load, screenshot the row, record timestamps for the deck.

## Open items carried from v2
- Real cardinality numbers for slide 9.
- Attribution wording (author review).
- Abstract wording "distributed traces across hops" -> speak of "traces from the serving path".
- GitHub push blocked by Code Defender (Vijay approval).

## v3.1 (Oct 6 evening): research fold-in and what the rig actually showed

Research pass (research-2026-10-06/synthesis.md) folded into the deck:
1. vLLM V1 exposes kv_cache_usage_perc, num_requests_waiting, request_queue_time_seconds natively -> slide 7b
   reframes Lua as "for servers and pipelines that do not"; dashboard row 3 cross-checks log-derived vs native.
2. Queue time rises before waiting -> row 3 p95 queue-time panel, narration "queue time first, waiting confirms".
   Elastic's GR_ENGINE_ACTIVE 99.8% / PIPE_TENSOR_ACTIVE 16.6% / DRAM_ACTIVE 80.4% on slide 4b, with the MFU/MBU line.
3. vLLM tracing removed in V1, reinstated PR #20372 (>= 0.10.2) -> rig upgraded 0.9.0 -> 0.30.0, footnote on slide 8.
4. Cardinality numbers (Last9: 1,000 x 8 x 60 x 3 = 1.4M series) close the slide 6b TODO.
5. DRA stable in K8s 1.35, dcgm-exporter 4.8.4 pod_uid -> footnote on slide 5; rig upgraded to dcgm-exporter 4.8.4.
6. Disaggregated prefill/decode, Inference Gateway, CloudWatch OTel Container Insights -> new slide 11 "where this is going".
7. Cast AI ~5% average GPU utilisation -> hook on slide 3.
Rig checks: Fluent Bit 3.1.9 -> 5.1.3; vLLM 0.30.0 V1 engine (stats line format unchanged, Preemptions field added
to the Lua); request_queue_time_seconds on the dashboard; dcgm-exporter 4.8.4 with driver 580 on A10G works.

What the live rig showed under the saturating load (be precise on stage):
- FB_USED: 3.6 GB (constrained) and 20.5 GB (overprov), flat before, during, after. The memory counter is the one that never moves.
- GPU_UTIL DID move: 0 -> 100% on the constrained pod, ~55% on overprov. SM_ACTIVE 0.9 vs 0.3. So DCGM does say "busy";
  it cannot say why or how much headroom is left.
- Log-derived: KV cache 99.9%, waiting ~95-116, running ~76-108, p95 queue time 4.8 s on constrained; 0.2% / 0 / 0.28 s on overprov.
- Preemptions stayed 0 (vLLM queues rather than evicts at max-num-seqs 256). Keep the gauge, do not promise it on stage.
- Prefix caching matters for the demo: identical prompts share KV blocks and the cache never fills. Loadgen prefixes a uuid.
- Traces: one llm_request span per request (5.7 s under saturation) with k8s.pod.name, gen_ai.latency.time_in_queue,
  time_in_model_decode. vLLM 0.30 also emits start-up spans (Load weights, Allocate KV cache, Compile graph).
