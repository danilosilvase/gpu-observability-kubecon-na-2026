# Cue sheet: demo recordings v7 (recorded Oct 16, same load for both)

Same 4 screens and clicks as DEMO-SCRIPT.md. Find the screen you were on, jump there, keep talking.

| Beat | Clean (`gpu-obs-demo-v7-clean.mp4`) | Captioned (`gpu-obs-demo-v7.mp4`) |
|------|------|------|
| **screen 1: What does the GPU say?** | 0:05 | 0:04 |
| One flag: the GPU exporter asks the kubelet which pod owns each GPU  ·  Every GPU metric now carries the pod name | 0:05 | 0:04 |
| GPU memory: red 2.0 GB, blue 20.6 GB  ·  The load started a few minutes ago. Neither line moved. | 0:22 | 0:15 |
| **screen 2: What does the server say?** | 0:59 | 0:42 |
| vLLM already writes this line every 10 seconds  ·  Fluent Bit ships it; 15 lines of Lua turn it into a metric, with the pod name | 0:59 | 0:42 |
| KV cache: red 99% full, blue 30%  ·  The server's working memory for requests in flight. Red has run out. | 1:17 | 0:54 |
| Cross-check: the same number from vLLM's own /metrics  ·  The log line tells the truth | 1:37 | 1:07 |
| Same traffic to both. Red makes fewer tokens: 9556 vs 11664 per second | 1:51 | 1:17 |
| **screen 3: Why was this request slow?** | 2:21 | 1:39 |
| Red: 5.8 s waiting for room, 1.9 s on the GPU  ·  Blue waits 2 ms. Same GPU, same traffic. | 2:22 | 1:39 |
| vLLM sends a span per request. The Collector adds the pod name.  ·  The app never knew its pod name | 2:41 | 1:52 |
| The slowest requests on red. Click one. | 2:58 | 2:03 |
| One request, two hops: the client, then vLLM  ·  One trace, end to end | 3:16 | 2:18 |
| vLLM's own timing on the span: 6.6 s in the queue  ·  This request waited for room before the GPU touched it | 3:37 | 2:34 |
| The pod name, on the request  ·  Added by the OTel Collector | 3:57 | 2:49 |
| One click: from this request to that pod  ·  Grafana uses the pod name on the span to find its metrics | 4:14 | 3:01 |
| That pod during this request: 100% full  ·  The slow request, explained in one click | 4:36 | 3:19 |
| **screen 4: Is 8% too low? Is 90% too high?** | 5:01 | 3:38 |
| Our rule of thumb, not vLLM's: peak KV cache under real traffic  ·  Above 90%: memory-constrained. Below 40%: over-provisioned. | 5:01 | 3:38 |
| Red: memory-constrained. Blue: over-provisioned.  ·  Both settings were wrong, in opposite directions | 5:19 | 3:50 |
| GPU memory never showed it. Time to first token: red 5.9 s, blue 63 ms  ·  That is what the user feels | 5:35 | 4:01 |
