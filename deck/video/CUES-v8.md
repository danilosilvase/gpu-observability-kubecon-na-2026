# Cue sheet: demo recordings v8 (recorded Oct 16, same load for both)

Same 4 screens and clicks as DEMO-SCRIPT.md. Find the screen you were on, jump there, keep talking.

| Beat | Clean (`gpu-obs-demo-v8-clean.mp4`) | Captioned (`gpu-obs-demo-v8.mp4`) |
|------|------|------|
| **screen 1: What does the GPU say?** | 0:05 | 0:04 |
| One flag: the GPU exporter asks the kubelet which pod owns each GPU  ·  Every GPU metric now carries the pod name | 0:05 | 0:04 |
| GPU memory: red 2.0 GB, blue 20.6 GB  ·  No traffic yet. Red reserved 8% of the GPU, blue 90%. | 0:15 | 0:14 |
| Start the load: the same traffic to both pods  ·  192 long requests each, all the time | 0:25 | 0:24 |
| Requests arrive: the same number in flight on both pods | 0:44 | 0:42 |
| GPU memory, under load: still red 2.0 GB, blue 20.6 GB  ·  Not a wiggle. This chart cannot tell you which one is in trouble. | 0:56 | 0:50 |
| **screen 2: What does the server say?** | 1:30 | 1:15 |
| vLLM already writes this line every 10 seconds  ·  Fluent Bit ships it; 15 lines of Lua turn it into a metric, with the pod name | 1:30 | 1:15 |
| KV cache: the server's working memory for requests in flight  ·  Watch red | 1:48 | 1:27 |
| Red: 100% full, 68 s into the load. Blue: 31%.  ·  Red has run out of room. New requests have to wait. | 1:55 | 1:32 |
| Cross-check: the same number from vLLM's own /metrics  ·  The log line tells the truth | 2:13 | 1:44 |
| Same traffic to both. Red makes fewer tokens: 9510 vs 11993 per second | 2:28 | 1:54 |
| **screen 3: Why was this request slow?** | 2:58 | 2:16 |
| Red: 5.6 s waiting for room, 1.9 s on the GPU  ·  Blue waits 19 ms. Same GPU, same traffic. | 2:58 | 2:16 |
| vLLM sends a span per request. The Collector adds the pod name.  ·  The app never knew its pod name | 3:18 | 2:29 |
| The slowest requests on red. Click one. | 3:34 | 2:40 |
| One request, two hops: the client, then vLLM  ·  One trace, end to end | 3:53 | 2:55 |
| vLLM's own timing on the span: 6.6 s in the queue  ·  This request waited for room before the GPU touched it | 4:14 | 3:11 |
| The pod name, on the request  ·  Added by the OTel Collector | 4:33 | 3:26 |
| One click: from this request to that pod  ·  Grafana uses the pod name on the span to find its metrics | 4:51 | 3:38 |
| That pod during this request: 100% full  ·  The slow request, explained in one click | 5:13 | 3:56 |
| Now the same kind of request on blue  ·  Same model, same GPU, same traffic | 5:40 | 4:17 |
| Blue: 0 ms in the queue. Red: 6.6 s.  ·  Same request. The only difference is how much room the server reserved. | 6:05 | 4:38 |
| **screen 4: Is 8% too low? Is 90% too high?** | 6:29 | 4:56 |
| Our rule of thumb, not vLLM's: peak KV cache under real traffic  ·  Above 90%: memory-constrained. Below 40%: over-provisioned. | 6:29 | 4:56 |
| Red: memory-constrained. Blue: over-provisioned.  ·  Both settings were wrong, in opposite directions | 6:47 | 5:08 |
| GPU memory never showed it. Time to first token: red 5.8 s, blue 65 ms  ·  That is what the user feels | 7:03 | 5:19 |
