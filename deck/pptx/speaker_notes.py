"""Speaker scripts for the v4 deck. Applied by build_deck_v4.py after the slides are built (single source of truth).
Format per slide: timing line, what to say, then 'Next:' hand-off. Written to be read aloud; plain words, no em dashes."""

NOTES = {
1: """[0:00, 0:15] Cover while people settle. Danilo speaks first.
Say nothing yet beyond a hello. Check the clicker, check Grafana is open on the second screen with the loadgen job ready to apply.
Next: title slide.""",

2: """[0:15, 1:00] Who we are, in two sentences each.
Danilo: "I'm Danilo, I build platforms for customers at AWS Professional Services, mostly Kubernetes and ML infrastructure." Henrique: "I'm Henrique, Principal in AWS Support, I'm the escalation point when ECS and EKS clusters misbehave at scale, which means I see a lot of GPU incidents after the fact." One line on the talk: "This is about what happened when we tried to explain a slow inference service with the GPU dashboard, and why we ended up getting the real answer out of a log line."
Next: the incident.""",

3: """[1:00, 2:30] The incident. Open with it, not with architecture.
"It's 02:14. The page fires. p99 latency on the inference service has doubled. You open the GPU dashboard and everything is green. Utilisation 95%, flat for an hour. Memory 90%, flat since the pod started. Pods Ready, nothing throttled, no OOM, no restarts." Pause. "The model is healthy, the pods are healthy, the GPU says it's busy and fine. And latency has doubled. Nobody knows why." Let that sit for a second. "Every signal the hardware gives you says busy and healthy. That is the black box we're going to open."
Next: same counter, opposite story.""",

4: """[2:30, 3:00] The hook, 30 seconds.
"Here's the thing about that 95%. Across the industry the average production GPU runs at about 5% utilisation. Same counter, DCGM_FI_DEV_GPU_UTIL. One fleet looks saturated, the other looks idle. And neither number tells you anything about the inference work." Point at the counter name. "This talk is about where the signal actually lives, because it isn't here."
Next: section two, why GPU metrics lie for inference. Slides 5 to 8, four and a half minutes. Henrique takes this section.""",

5: """[3:00, 4:15] Pre-allocation. The screenshot is from our rig.
"Every serious LLM server grabs its GPU memory before the first request arrives. vLLM calls it gpu-memory-utilization. It's a cap on the whole pool: weights, activation workspace, and the KV cache. On our tiny demo model the weights are small, so this is essentially the KV cache." Point at the two flat lines. "Two vLLM pods, same model. One at 0.90, 20.5 gigabytes. One at 0.15, 3.6 gigabytes. Both lines are perfectly flat, from start-up, through a saturating load, and after. Now, which one is about to fall over? The small one. The memory counter says the opposite." Tag line: "It measures a config value. Never the workload sitting on top of it."
If asked why 0.90 of 24 is 20.5 and not 21.6: CUDA context and driver overhead, it's in the footer.
Next: utilisation.""",

6: """[4:15, 5:15] Utilisation and the two phases.
"GPU_UTIL has a precise meaning: at least one kernel was running during the sample window. One busy thread reads as 100%." Then the phases. "Inference has two phases with opposite shapes. Prefill: the whole prompt in one pass, big matrix multiplies, compute-bound, tensor cores busy. Decode: one token per step, and every step re-reads the entire KV cache, so it's memory-bandwidth-bound, tensor cores mostly waiting." Point at the bar. "And GPU_UTIL reads 100% in both. It has no idea which phase you're in or how much of the silicon is doing anything."
Next: what the profiler counters say instead.""",

7: """[5:15, 6:30] The Elastic numbers. Be precise about which field.
"These aren't our numbers, they're from Elastic Observability Labs measuring a vLLM server, and they used the DCGM profiling fields, not the NVML utilisation counter." Left to right. "Graphics engine active 99.8%: that's the profiler's version of busy. Tensor cores, the units doing the actual matmuls: 16.6%. Memory bus: 80.4%. The card is not computing. It's waiting on memory." Pause. "Bandwidth-bound, not compute-saturated, and utilisation never said which. If you needed more throughput here you'd quantize before you bought hardware." Last line, lightly: "Serving teams are starting to borrow MFU and MBU from the training world, model FLOPs and bandwidth utilisation, precisely because the dashboard counter is the least informative one the hardware offers."
Next: the vocabulary slide.""",

8: """[6:30, 7:30] Vocabulary slide, the one people photograph. Don't read every row.
"Left: what most GPU dashboards show. GPU_UTIL, framebuffer used, and nvidia-smi's Volatile GPU-Util which is the same thing. Right: what actually describes the work. SM_ACTIVE, how much of the compute is busy. SM_OCCUPANCY, what share of the warps an SM can hold are actually resident. DRAM_ACTIVE, are you bandwidth-bound. PIPE_TENSOR_ACTIVE, are the tensor cores doing matmuls." Then the punchline, slowly: "And none of them know what a token is. Queue depth, KV cache pressure, tokens per second. The serving framework owns those. The silicon doesn't."
Hand back to Danilo.
Next: section three, the one architectural idea.""",

9: """[7:30, 8:30] The join key. If they take one idea home, this is it.
"Three sources that never heard of each other. DCGM knows which pod holds the GPU, because dcgm-exporter asks the kubelet. Fluent Bit knows which pod wrote the log line, because the kubernetes filter tells it. The OTel Collector stamps k8s.pod.name on every span. Nothing else is common to all three. So: stamp the pod name on every metric, every log record, every span, and join at query time. That's the whole architecture."
Footnote only if the room is on new clusters: "Kubernetes 1.35 made Dynamic Resource Allocation stable, and dcgm-exporter 4.8.4 added pod_uid tracking because the old device-plugin mapping breaks under DRA. The idea survives, the plumbing changes."
Next: signal one.""",

10: """[8:30, 9:15] Signal 1, DCGM per pod. Keep it short, the audience knows exporters.
"dcgm-exporter in Kubernetes mode. --kubernetes=true asks the kubelet which pod owns each GPU and stamps exported_pod on every counter. That's the screenshot: SM active, per pod, during our demo." Right side: "It tells you which pod is on which GPU and whether that silicon is busy. It has no idea why, how many requests are queued, whether the KV cache is full, or anything about tokens." Point at the second config line: "ENABLE_POD_LABELS false. That one matters, next slide."
On EKS Auto Mode you run it standalone as a DaemonSet with the pod-resources hostPath; the GPU Operator isn't supported there, we'll come back to that.
Next: cardinality.""",

11: """[9:15, 10:00] Cardinality. War story one.
"The first thing we broke was Prometheus. dcgm-exporter will happily copy every pod label onto every counter. Do the arithmetic at fleet scale: a thousand nodes, eight GPUs each, the default sixty-odd counters, three label dimensions. 1.4 million series before a single pod or job label. And pod names churn on every rollout, so every label you add multiplies by churn." The rule: "Identity on logs. Stable dimensions on metrics. Join at query time. We ship seven counters and one identity label, and we join on the fixed part of the pod name, never the hash."
Next: section four, the centre of the talk, six minutes for slides 12 to 15.""",

12: """[10:00, 11:15] The log line. Read it with them.
"This is one line of vLLM stdout. It prints every ten seconds while the engine is busy. Top line is our over-provisioned pod under steady load. Read the highlighted fields: 4,700 tokens a second, 15 running, 0 waiting, KV cache 0.1%." Bottom line: "Same rig, the constrained pod under the demo load. 17,000 tokens a second, 76 running, 116 waiting, 41 preemptions, KV cache 99.6%." Point at the chips: "Tokens per second, running, waiting, KV cache, prefix hits, preemptions. Six facts about the inference work, and not one of them shows up in a GPU counter."
Next: how fifteen lines of Lua turn that into metrics.""",

13: """[11:15, 12:45] The Lua pipeline. Diagram first, code second, caveat third.
Top row: "Fluent Bit tails the container log. The kubernetes filter attaches the pod name, that's the join key arriving, the red dot. The Lua filter does five string.match calls and promotes pod_name to a top-level field. grep drops everything that isn't a stats line. log_to_metrics turns the fields into gauges labelled by pod_name. prometheus_exporter serves them on port 2021, to the same Prometheus that scrapes DCGM."
The two lines: "This is the shape of every line in the filter: a field name, a pattern against the log line, and the identity from the kubernetes filter. Thirteen more in the repo, same shape."
The caveat, say it before someone asks: "vLLM already exposes all of this on /metrics: kv_cache_usage_perc, num_requests_waiting, request_queue_time_seconds. vLLM is our demo vehicle. This filter is for everything that doesn't have it: custom servers, vendor images you can't touch, log-only pipelines, the TGI or Triton you inherited. Same lines, different regex."
Next: live demo set-up. Henrique drives Grafana, Danilo narrates.""",

14: """[12:45, 13:30] Demo anchor. Tell them what to watch BEFORE switching screens.
Henrique: kubectl apply the loadgen job now if not already running (it takes about a minute to saturate, runs 12 minutes).
Danilo: "Two pods, same model, facebook/opt-125m. vllm-constrained at 0.15, 3.6 gigabytes of pool, gets long prompts at concurrency 128. vllm-overprov at 0.90, 20.5 gigabytes, steady load, that's our control." Then the instruction: "Watch two rows. Row one is DCGM: GPU memory is going to stay flat. Row two is what the log knows: KV cache and waiting are going to take off."
Switch to Grafana. Narrate live for about two minutes: FB_USED flat on both; GPU_UTIL and SM_ACTIVE go up on the constrained pod (so DCGM does say busy, be honest about that); KV cache climbs to 100% and stays; waiting climbs to around 100; p95 queue time jumps from 0.3 to 4.8 seconds; over-provisioned pod sits at 0.2% KV cache.
Next: back to slides, the result slide (also the fallback if the live rig misbehaves).""",

15: """[13:30, 14:30] Demo result. Recap, or fallback if the live demo failed.
"Left, DCGM: GPU memory, 3.6 gigabytes before, during and after. Right, the log: KV cache goes to 100% within a minute of the load and stays there." The three numbers: "p95 queue time 4.8 seconds, was 0.3. About 100 requests waiting. And the over-provisioned pod has 99.8% of its cache free the whole time." Be precise: "GPU_UTIL and SM_ACTIVE did go up on the constrained pod, so DCGM does say busy. What it can't say: one pod has zero headroom and a hundred requests queued, the other has 99% of its cache sitting free." Close: "Queue time moves first. Waiting confirms. GPU memory never moved."
Next: section five, traces, two and a half minutes.""",

16: """[14:30, 16:30] Signal 3, traces. Henrique.
"vLLM emits one span per request natively. You point it at the OTel Collector with --otlp-traces-endpoint. The k8sattributes processor looks up the source IP and stamps k8s.pod.name on every span. That's the whole wiring." The screenshot: "An llm_request span, 5.73 seconds, on vllm-constrained, during the saturation. Time in queue 0.61 seconds, time in decode 5.33." The point: "A slow span by itself is just a fact. The same span, on the pod whose KV cache hit 100% that second, with 116 requests waiting, is a diagnosis."
Gotcha, say it out loud: "Tracing disappeared in the vLLM V1 engine rewrite and came back in PR 20372, so you need 0.10.2 or later. We run 0.30. If your traces vanished after an upgrade, that's why."
Honesty line: "We show traces from the serving path, one span per request. Multi-hop waterfalls across a gateway are a flag away, but they're not the point today."
Next: the join, the slide the whole talk builds to. Danilo.""",

17: """[16:30, 18:30] The join. Slow down here. Two minutes on one slide is fine.
"One Grafana dashboard. One pod variable. Three data sources that never heard of each other: DCGM through exported_pod, Fluent Bit through pod_name, vLLM and the traces through pod." Point at the red line: "16:56, the load hits. Top row, DCGM memory: flat. Middle row, KV cache from the log line: pegs at 100%. Bottom row, queue time from vLLM: 0.3 to 4.8 seconds. Same second, same pod name." Pause. "That's the black box opened. The incident from slide three is this picture." Close: "No new agent, no vendor, no eBPF. Just the pod name on every signal, and the discipline to keep it there."
Next: one thing that broke, 30 seconds.""",

18: """[18:30, 19:00] One gotcha, 30 seconds. Cut this slide first if running late.
"Every DCGM how-to assumes the NVIDIA GPU Operator. EKS Auto Mode ships the drivers and the device plugin on its GPU AMIs and supports neither the Operator nor the NVIDIA DRA driver. So: standalone dcgm-exporter DaemonSet, pod-resources hostPath, SYS_ADMIN capability, seven counters." One breath on the grey line: "Two more in the repo README: Fluent Bit's Kube_Tag_Prefix has to match the tail tag exactly or the pod name silently never arrives, and a one-GPU pod on a two-GPU NodePool never finishes a RollingUpdate, use Recreate."
Next: where this is going, one minute.""",

19: """[19:00, 20:00] Where this is going. Pre-empts "isn't this solved".
Left to right: "Today the join happens in Grafana. Next: disaggregated prefill and decode, llm-d, NVIDIA Dynamo, llm-d on AWS, splits one request across two pods and ships the KV cache between them over NIXL and EFA; AWS measured up to 70% more tokens per second at concurrency 128. The pod is no longer the whole request, so the join key becomes request id plus pod. And then: the Gateway API Inference Extension's endpoint picker and Dynamo's KV-aware router consume exactly these signals, queue depth and KV cache, to decide where traffic goes. The join leaves Grafana and moves into the router."
Bottom: "Signal one is becoming a checkbox. CloudWatch's OTel-native Container Insights for EKS, June this year, wires DCGM into OTel with pod labels out of the box. Signals two and three are still yours to wire."
If asked after: XID/ECC/thermal faults, output quality, eBPF GPU profiling, Dynamo internals are all out of scope today.
Next: takeaways.""",

20: """[20:00, 20:45] Steal this. Three columns, read the headers, not every box.
"Three counters: SM_ACTIVE instead of GPU_UTIL, KV cache percent from the log or from /metrics, queue time p95 and then waiting. One filter: fifteen lines of Lua plus log_to_metrics, change the regex, keep the pipeline, works for anything that logs. One rule: pod name on every signal, identity on logs, stable dimensions on metrics, join at query time." Attribution: "This session was designed by [original author]; we rebuilt it from the abstract on EKS Auto Mode and broke different things along the way. Everything deploys with one terraform apply."
Next: thank you and Q&A.""",

21: """[20:45, 25:00] Close and Q&A, four to five minutes.
"Thank you. The repo has the Terraform, the manifests, the Lua, the dashboard and the validate script. Please scan the QR to rate the session, the organisers read every one." Leave the QR up for the whole Q&A.
Likely questions and short answers:
- "Why not just scrape vLLM /metrics?" We do, row three of the dashboard. The filter is for servers that don't expose it. Slide 13.
- "MIG or time-slicing?" dcgm-exporter 4.5+ has per-process metrics, which narrows the gap but doesn't close it; the serving log still knows more.
- "SGLang / TGI field names?" Same technique, different regex. Verify against your log line before trusting it.
- "Hardware faults, XID, ECC?" A fourth signal class, real, out of scope today.
- "Cardinality numbers from your own rig?" Seven counters, one identity label; the 1.4M is the Last9 fleet math, cited on slide 11.
- "Disaggregated serving breaks the join?" Yes, slide 19: join key becomes request id plus pod.""",
}
