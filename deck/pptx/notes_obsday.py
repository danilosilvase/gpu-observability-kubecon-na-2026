"""Speaker notes for kubecon-obsday-2026.pptx, in Henrique's house style:
header, timing | speaker | clicks, the script with [PAUSE] [SLOWLY] [EMPHASIS], SOURCE (what the evidence shows and what it
does not prove), [IF ASKED]. Keyed by final slide number (1 = cover). No em dashes."""
REPO = "github.com/danilosilvase/gpu-observability-kubecon-na-2026"
MEAS = ("16 Oct 2026 recording (deck/video/gpu-obs-demo-v8.mp4): facebook/opt-125m on vLLM v0.30.0, one A10G (g5.xlarge) "
        "per pod, equal traffic (192 long requests at a time per pod, unique prompts).")

NOTES = {
1: """SLIDE 1: WALK-IN
Before 0:00 | nobody | no clicks

Up while people sit down. No script.

SOURCE: Observability Day NA 2026 branded template.""",

2: """SLIDE 2: TITLE
0:00 to 0:30 | HENRIQUE | no clicks

Hi everyone, I'm Henrique, and this is Danilo. We both work at AWS. [PAUSE]

We have twenty minutes: one question for you, a live demo, and then your questions.

(Danilo: terminal open with demo/load.sh typed, not run. Grafana screen 1 in the next app.)

SOURCE: Title is the accepted abstract title, verbatim (ABSTRACT.md).""",

3: """SLIDE 3: WHICH ONE IS IN TROUBLE?
0:30 to 2:00 | HENRIQUE | 3 clicks: Pod A (ring sweeps to 8%), Pod B (ring sweeps to 90%, then the "same" chips pop in), the vote

Two vLLM pods. Same model, same GPU type, same traffic. [click] One reserved 8% of GPU memory. [click] The other, 90%. [PAUSE]

[click] [SLOWLY] Which one is in trouble? Hands up for 8%. For 90%. For both. And who can't tell from here? (count roughly, out loud)

[EMPHASIS] Hold that. Danilo will answer it live.

One thing to say now: this is a test cluster we built for this talk, not a customer system.

SOURCE: manifests/20-vllm/vllm.yaml: vllm-constrained --gpu-memory-utilization=0.08, vllm-overprov 0.90, same model and server (facebook/opt-125m, vLLM v0.30.0). manifests/20-vllm/loadgen-job.yaml: same traffic to both pods. The percentage is the vLLM setting, a share of the GPU's total memory. Do NOT reveal the answer here.
[IF ASKED]
- Which model? facebook/opt-125m, a small model, so the cache fills on one A10G with modest traffic. We did not measure bigger models; the mechanism (a fixed pool that fills) does not depend on model size, the numbers do.""",

4: """SLIDE 4: GPU MEMORY IS A SETTING, NOT A SIGNAL
2:00 to 3:30 | HENRIQUE | 4 clicks: the four tiles, the GPU memory line draws, load starts (bars climb, "92%, flat" pops by itself), the sentence

[click] These are the four we all watch: CPU, memory, network, disk. They measure resources on the node and in the container, and that's useful. [PAUSE] But none of them sees the server's queue.

[click] So we add GPU memory. vLLM takes 92% of it at startup, by default. [click] Now the load starts. Requests pile up. [PAUSE] [EMPHASIS] And the line doesn't move.

[click] [SLOWLY] GPU memory is a setting, not a signal. Busy or idle, it stays put. So the chart we page on can't tell a struggling server from a quiet one.

SOURCE: vLLM default gpu_memory_utilization = 0.92 (vllm/config/cache.py, vLLM main, checked Oct 2026). vLLM pre-allocates that share at startup for weights, activations and the KV cache, so used memory (DCGM_FI_DEV_FB_USED, demo screen 1) stays flat under load. The request bars are illustrative (shape only, not measured values); the flat line is what demo screen 1 shows. The slide does not say CPU or memory metrics are useless; only that they do not see the inference queue.
[IF ASKED]
- What about GPU utilisation? Hidden slide 15.""",

5: """SLIDE 5: WHAT RUNS OUT FIRST: ROOM FOR REQUESTS IN FLIGHT
3:30 to 6:00 | HENRIQUE | 5 clicks: the GPU, the pool fills, the queue grows, the table, the punchline (the caption under the GPU appears by itself)

[click] Here's one GPU, the way vLLM uses it. The model weights, a little extra, and most of that 92% goes to the KV cache: the server's working memory for requests in flight. One flag sets its size: gpu-memory-utilization.

[click] The easiest way to think about it is a connection pool. You set the size. Every request holds a slot while it runs. [click] When every slot is taken, new requests wait. [PAUSE]

[click] And it fails the way a pool fails. [EMPHASIS] Latency climbs, and nothing else on the dashboard looks wrong. CPU fine. GPU memory flat.

[click] The good news: vLLM tells you how full it is, every ten seconds, in a log line you already ship.

(Do not name a pod here. The demo answers the vote.)

SOURCE: KV cache = the attention keys and values held for every request in flight (vLLM docs, PagedAttention). The pool analogy is ours. It holds for "fixed size, set by you, full means waiting". It breaks on preemption: vLLM can evict a running request to make room, a connection pool does not. vLLM V1 prints the stats line every 10 s while the engine is busy (vllm/v1/metrics/loggers.py). Intro structure credit: Jimmy Song (footer).
[IF ASKED]
- Does vLLM preempt? Yes. When the cache is full it can preempt running requests and recompute them later; the stats line then shows a preemption count.""",

6: f"""SLIDE 6: LIVE DEMO
6:00 to 15:00 | HENRIQUE hands over, DANILO drives | no clicks, the strip builds by itself

HENRIQUE: [SLOWLY] Is 8% too low? Is 90% too high? [PAUSE] Danilo, which one is in trouble?

DANILO: Cmd+Tab to Grafana screen 1. Run demo/load.sh on camera. Follow DEMO-SCRIPT.md. Same strip on every screen: 1 GPU, 2 Log, 3 Trace, 4 Answer.

OUT: after screen 4, Cmd+Tab back here and advance (lands on slide 8, slide 7 is hidden).
RIG DEAD: play deck/video/gpu-obs-demo-v8-clean.mp4 on this laptop, Space to pause, same lines.
VIDEO DEAD TOO: type 7 + Enter for the hidden backup.

SOURCE: live cluster gpu-obs-demo (EKS, eu-central-1), two g5.xlarge nodes, one A10G each. Dashboards gpu-walk-1 to 4 (manifests/60-grafana/build_walkthrough.py). Load: demo/load.sh, 20 minutes, equal traffic.
[IF ASKED]
- Is it really live? Yes. The load starts on screen 1; Pod A's cache fills about 68 s later.""",

7: """SLIDE 7: BACKUP, WHAT SCREEN 4 SHOWED (HIDDEN)
Only if the rig is down AND the video will not play | DANILO

Here's what screen 4 showed when we recorded it. [point] Red, 8%: memory-constrained. 2.0 GB of GPU memory, cache at 100%, 5.9 seconds to the first token. [PAUSE] Blue, 90%: over-provisioned. 20.6 GB held, cache at about 30%, 80 milliseconds.

SOURCE: screenshot of gpu-walk-4 from the """ + MEAS,

8: """SLIDE 8: WHAT BROKE WHILE WE BUILT IT
15:00 to 17:30 | HENRIQUE | 3 clicks, one story each | CUT RULE: if this slide starts after 16:30, skip "An unfair test"

[SLOWLY] Our first load test didn't stress anything. [PAUSE]

[click] We sent the same prompt over and over. vLLM noticed, shared the cache between them, and nothing filled up. It took a unique prefix on every prompt to make it struggle. [EMPHASIS] A load test with repeated prompts is lying to you.

[click] Cardinality. We put the pod name on every GPU metric, because that's the join key. Fourteen series when we started. Fifty-six after three rollouts. Every restart mints a new set, and Prometheus keeps the old ones until retention ends.

[click] And an unfair test. Our first comparison sent more traffic to one pod: 12 seconds against 0.13. Too good to be true. Same traffic to both: 5.9 seconds against 0.08. Test with your own traffic.

SOURCE: prefix caching: vLLM automatic prefix caching shares KV blocks across identical prefixes; the loadgen now starts every prompt with a uuid (manifests/20-vllm/loadgen-job.yaml). Cardinality: manifests/50-prometheus/CARDINALITY-DEMO.md, measured 13 Oct 2026, 7 DCGM counters x 2 GPUs = 14 series, 56 after 3 rollouts (8 pod names seen). Unfair test: an earlier run with unequal traffic; the equal-traffic numbers are from the 16 Oct recording. 14 and 56 are for our 7 counters; with the default counter set the multiplier is the same, the totals are bigger.
[IF ASKED]
- How do you keep cardinality down? Hidden slide 16.""",

9: """SLIDE 9: WHO VOTED BOTH? YOU WERE RIGHT.
17:30 to 18:00 | HENRIQUE | the cards come in by themselves; 3 clicks: Pod A verdict, Pod B verdict, the takeaway

[SLOWLY] Who voted both? [PAUSE] You were right.

[click] Pod A, at 8%, was too small. The cache hit 100%, and new requests waited almost six seconds for the first token. [click] Pod B, at 90%, was too big. Its cache never got past about 30%. Twenty gigabytes held, mostly empty.

[click] [EMPHASIS] GPU memory can't tell you an inference server is in trouble. Read the server's own signal.

SOURCE: screen 4 of the """ + MEAS + """ Pod A 2.0 GB, peak cache 100%, 5.9 s to first token. Pod B 20.6 GB, peak about 30%, about 0.08 s. These numbers are for this model and this traffic; they do not predict your latency.
[IF ASKED]
- Is "too big" really trouble? Not for latency. It is memory reserved at startup and never used. Hidden slide 14.""",

10: """SLIDE 10: THREE LINES OF CONFIG, ONE JOIN KEY
18:00 to 18:45 | HENRIQUE | 4 clicks: dcgm, Fluent Bit, OTel, the join (the caption appears by itself)

Everything you saw comes down to three lines of config. One per tool, nothing exotic.

[click] dcgm-exporter in Kubernetes mode asks the kubelet which pod owns each GPU. [click] Fluent Bit reads vLLM's log and pulls out the cache number. [click] And the OpenTelemetry Collector tags every trace with the pod it came from. [PAUSE]

[click] [EMPHASIS] The trick is the join. Every signal carries the pod name. That's what let Danilo go from the GPU, to the log, to the trace, for the same pod.

SOURCE: manifests/10-gpu-metrics/dcgm-exporter.yaml (--kubernetes=true reads the kubelet pod-resources API; dcgm-exporter 4.8.4). manifests/30-logs/fluent-bit.yaml (Lua string.match on "KV cache usage"; Fluent Bit 5.1.3). manifests/40-traces/otel-collector.yaml (k8sattributes, pod name from the sender's IP; collector-contrib 0.111.0). vLLM also exports the cache on /metrics (vllm:kv_cache_usage_perc); the log path is the technique for servers that only log it, and demo screen 2 cross-checks the two.
[IF ASKED]
- Why the log if /metrics exists? Hidden slide 13.
- The pod name on GPU metrics is the cardinality cost from slide 8.""",

11: """SLIDE 11: SIZE IT FROM PEAK KV CACHE
18:45 to 19:30 | HENRIQUE | 4 clicks: the gauge, Pod A lands, Pod B lands, the three steps (caveat and repo appear by themselves)

So how do you size it? Not from GPU memory. [click] From peak KV cache, under your own traffic. Below 40%, you reserved memory you don't use. Above 90%, requests start to queue. In between, you have room for a burst.

[click] Pod A landed here, at 100%. [click] Pod B, here, at about 30%. [PAUSE]

[click] Three steps for Monday. Measure the peak. Change gpu-memory-utilization. Measure again.

[EMPHASIS] The 40 and the 90 are our rule of thumb, not vLLM's. Use the method, not our numbers. Everything is in the repo.

SOURCE: the bands are our own heuristic from this rig (one model, one GPU type, our traffic); vLLM publishes no threshold. Pod markers from the 16 Oct recording. Repo: """ + REPO + """ (all manifests, Terraform, dashboards).
[IF ASKED]
- Why 90 and not 100? Above about 90% a burst fills the rest and requests queue. Our pick, not a vLLM number.
- Why not just 0.90 everywhere? Hidden slide 14.""",

12: """SLIDE 12: QUESTIONS
19:30 to 25:00 | BOTH | no clicks; leave up for all of Q&A (feedback QR)

Thank you. [PAUSE] The code on screen is the session feedback; it really helps us. [PAUSE] Questions?

HIDDEN ANSWERS (in Slideshow, type the number + Enter):
- 13: Why parse the log if vLLM has /metrics?
- 14: Why not set 0.90 everywhere?
- 15: What about GPU utilisation?
- 16: How much does the pod name cost?
- 7: what screen 4 showed
Deep dive: Grafana dashboard gpu-inference-deep (cardinality panel) on Danilo's laptop.

TODO before the talk: replace [original author].

SOURCE: feedback QR from the organisers.
[IF ASKED]
- Does this need EKS? No. The three configs are plain Kubernetes. We only tested on EKS Auto Mode with A10G.
- Other servers (TGI, SGLang, Triton)? We only tested vLLM. The method carries over if the server reports its cache usage, in a log line or on a metrics endpoint.""",

13: """SLIDE 13 (HIDDEN, Q&A): WHY PARSE THE LOG IF VLLM HAS /METRICS?
Q&A only | DANILO

Fair question. [PAUSE] vLLM does export it on /metrics, and if you can scrape it, do. We do too: screen 2 of the demo puts the two side by side, and they match.

We show the log path because Fluent Bit already reads every pod's log, so there's no new scrape target, and the same few lines of Lua work on any server that prints its cache usage, even one that doesn't export it.

SOURCE: README.md ("vLLM exposes KV cache %, waiting and queue time natively on /metrics. The Fluent Bit Lua + log_to_metrics path demonstrates the technique for servers that do not"). gpu-walk-2 plots log_kv_cache_usage_pct (log) against vllm:kv_cache_usage_perc (/metrics). The log line arrives every 10 s, so it is coarser than a scrape.""",

14: """SLIDE 14 (HIDDEN, Q&A): WHY NOT SET 0.90 EVERYWHERE?
Q&A only | HENRIQUE

The default is already 0.92, so most of us run there without choosing to. [PAUSE]

If one pod owns one GPU and nothing else will ever run on it, 0.90 is fine. You've paid for headroom. [EMPHASIS] The cost shows up when GPUs are shared: the memory is reserved at startup, used or not. Pod B held 20.6 GB, and its cache used about a third.

So size from the peak, and give the rest back to the next pod.

SOURCE: vllm/config/cache.py default 0.92. Pod B numbers from the """ + MEAS + """ Sharing a GPU between pods needs time-slicing, MPS or MIG; we did not test sharing on this rig.""",

15: """SLIDE 15 (HIDDEN, Q&A): WHAT ABOUT GPU UTILISATION?
Q&A only | DANILO

GPU utilisation has a precise meaning: the share of time at least one kernel was running. [PAUSE] So one busy kernel reads as 100%, and a server that's waiting on memory looks the same as one that's flat out.

The profiling fields say more: how many SMs are active, how busy the memory bus is, whether the tensor cores are working. We scrape two of them. [EMPHASIS] But none of them knows about the queue. That lives in the server.

SOURCE: NVML nvmlUtilization_t: "percent of time over the past sample period during which one or more kernels was executing on the GPU" (DCGM_FI_DEV_GPU_UTIL). manifests/10-gpu-metrics/dcgm-exporter.yaml scrapes DCGM_FI_DEV_GPU_UTIL, DCGM_FI_PROF_SM_ACTIVE, DCGM_FI_PROF_DRAM_ACTIVE on the A10G. Profiling fields need a GPU and driver that support DCGM profiling.""",

16: """SLIDE 16 (HIDDEN, Q&A): HOW MUCH DOES THE POD NAME COST?
Q&A only | DANILO

It costs one new set of series every time a pod restarts. [PAUSE] Fourteen series on our two GPUs, fifty-six after three rollouts. Same two GPUs, four times the series, until retention drops the old ones.

So keep the pod name, because it's the join key, and drop everything else that churns: no pod labels, a short counter list, short retention for per-pod data.

SOURCE: manifests/50-prometheus/CARDINALITY-DEMO.md, measured 13 Oct 2026: 7 counters x 2 GPUs = 14 live, 56 after 3 rollouts (8 pod names seen). Fix shipped: --kubernetes=true, DCGM_EXPORTER_KUBERNETES_ENABLE_POD_LABELS=false, 7 counters in counters.csv (default set is about 40), retention 6h. Reproduce: rollout restart both deployments a few times, then demo/cardinality.sh.""",
}
