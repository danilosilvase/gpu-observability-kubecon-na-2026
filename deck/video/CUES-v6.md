# Demo video cue sheet v6 (gpu-obs-demo-v6.mp4, 3:21)

Recorded live on the rig, 15 Oct 2026 (take 2, rec7). Captions are burnt in, so you can play it silently and talk over it. One question, one screen: "which pod is in trouble?" One line to say per beat.

| Time | On screen | Say |
|---|---|---|
| 0:00 | Title card | "Two vLLM pods, same model, same L4 GPU. Which one is in trouble?" |
| 0:10 | Idle: OK / OK, no traffic | "Nothing running yet. Both pods read OK." |
| 0:18 | The three numbers | "Three numbers per pod: GPU memory, how full the KV cache is, how long a request takes." |
| 0:26 | Load starts | "Now the same kind of traffic hits both pods." |
| 0:35 | GPU memory | "The number most teams watch. Red 3.5 GB, blue 20.5 GB, and it does not move." |
| 0:45 | KV cache from the log | "This one comes from a log line. vLLM prints how full its cache is; we turn that into a metric per pod." |
| 1:13 | Red 100% / Blue 0% | "Red is full. Blue is empty." |
| 1:26 | Red 11 s / Blue 0.13 s | "So red requests take 11 seconds. Blue: 0.13 seconds." |
| 1:36 | Verdict flips | "There is our pod in trouble. The GPU memory number never told us." |
| 1:46 | Traces | "Now the slow requests themselves." |
| 2:01 | Two hops | "Client, then vLLM. Same trace, two hops." |
| 2:17 | Pod name on the span | "The Collector stamps the pod name on the span. The app never knew it." |
| 2:30 | One click | "One click from this slow request to that pod's metrics." |
| 2:47 | Car park 100% full | "The car park was full. That is why it was slow." |
| 3:03 | Three signals, one pod name | "Metrics, logs, traces: three signals, one pod name." |
| 3:12 | End card | "Configs are in the repo. Now, what broke on the way." |
