# Demo video cue sheet (gpu-obs-demo-2026-10-15.mp4, 5:03)

Recorded live on the rig, 15 Oct 2026. Captions are burnt in, so you can play the video silently and talk over it. One line to say per beat.

| Time | On screen | Say |
|---|---|---|
| 0:00 | Title card | "Two vLLM pods, same model, same L4 GPU. One gets 15% of the GPU memory, one gets 90%." |
| 0:11 | Idle dashboard | "One dashboard, one row per signal, every panel keyed by pod name." (Both tiles read over-provisioned at idle; that is correct, nothing is under pressure yet.) |
| 0:19 | GPU memory (DCGM) | "This is the panel most teams page on. Reserved at start-up, then flat." |
| 0:29 | KV cache, queue: quiet | "Nothing waiting, nothing full." |
| 0:37 | Load starts | "192 long requests to red, 16 short ones to blue." |
| 0:49 | KV cache from the log line | "Fluent Bit tails the vLLM log, a 15-line Lua filter pulls out KV cache %, log_to_metrics makes it a metric per pod." |
| 1:16 | Red KV cache full | "KV cache is the real 'GPU memory full' for an LLM server." |
| 1:30 | Queue p95 | "Red requests wait 9.5 s before the GPU even starts. Blue: 0.28 s." |
| 1:40 | GPU memory still flat | "DCGM cannot see any of this. The pod in trouble even uses less memory." |
| 1:50 | Verdict flips red | "Same model, same GPU: one memory-constrained, one over-provisioned. Only the log line could tell." |
| 2:00 | Pod name on every panel | "exported_pod, pod_name, pod: three sources, one join key." |
| 2:09 | Trace tables | "Slowest requests per pod: about 12 s versus 0.2 s." |
| 2:27 | Two-hop trace | "Client span, then vLLM span, same trace ID through traceparent." |
| 2:45 | Span timings | "vLLM records its own timings: 11.9 s total, 6 s of it queued." |
| 3:03 | k8s.pod.name | "The Collector adds the pod name; the app never knew it." |
| 3:18 | Trace to metrics | "One click from this span to that pod's metrics." |
| 3:37 | KV cache 100% | "The slow request, explained in one click." |
| 4:00 | GPU memory flat | "DCGM alone would never have explained this request." |
| 4:18 | Cardinality: 14 live, 56 last hour | "What broke: every pod restart adds a new set of GPU series. Keep the pod name, drop the pod labels." |
| 4:33 | GPU utilisation % | "Busy if any kernel ran. Looks the same for a healthy pod and a drowning one." |
| 4:43 | SM active | "The profiling counter to watch instead." |
| 4:53 | End card | "The pod is the join key. Configs are in manifests/." |
