# Demo script (v8): 4 screens, about 9 minutes live (recordings: 5:45 captioned, 7:42 clean)

Same 4 screens, same load, same clicks whether it runs live or from the recording. The load starts on camera, on screen 1.
Screens: `gpu-walk-1` to `gpu-walk-4` (Grafana, kiosk). Each screen has the same layout:
progress strip and question at the top, the config that makes it work on the left (one line highlighted),
one chart on the right (red vs blue), one sentence at the bottom. The orange **Next** button (top right) goes to the next screen.

Red = `vllm-constrained` (`--gpu-memory-utilization=0.08`). Blue = `vllm-overprov` (0.90). Same model, same GPU type (NVIDIA A10G, 24 GB, g5.xlarge; one per pod), same traffic.

## Before the demo

| When | Who | Do |
|------|-----|----|
| T-60 | Danilo | `demo/start.sh` (tunnels, opens screen 4 then screen 1 in two tabs; does not start the load), then `demo/check.sh` = 9 OK |
| T-15 | Danilo | no load from now on: screen 1 must start idle (the charts show the last 10 min) |
| T-5 | Danilo | `demo/check.sh` again. Clean video open in QuickTime, paused at 0:00. A terminal in the repo, `demo/load.sh` typed, not run |
| Henrique ends slide 3 | Danilo | switch the projector to Grafana, screen 1 |

## Screen 1: What does the GPU say? (0:00-2:00)

| Point at | Say |
|----------|-----|
| highlighted `--kubernetes=true` | "One flag. The GPU exporter asks the kubelet which pod owns each GPU, so every GPU metric carries the pod name." |
| the chart | "This is the chart we page on. No traffic yet. Red reserved 8% of the GPU, 2 GB. Blue reserved 90%, 20.6." |
| press Enter on `demo/load.sh` | "Now the same traffic to both: 192 long requests each, all the time." |
| requests-in-flight tile | "Requests arrive. Same number in flight on both pods." |
| the chart again | "Under load: not a wiggle. So which one is in trouble? This chart can't tell you." |
| click **Next** | |

## Screen 2: What does the server say? (2:00-4:30)

| Point at | Say |
|----------|-----|
| highlighted log line | "vLLM already writes this line every 10 seconds. Fluent Bit ships it, 15 lines of Lua turn it into a metric, with the pod name." |
| KV cache chart (red climbs while you talk, full ~60-90 s after the load) | "KV cache: the server's working memory for requests in flight. Watch red... full. Blue uses about a third." |
| cross-check tile | "Same number from vLLM's own /metrics. The log tells the truth." |
| tokens/s tile | "Same traffic to both. Red makes fewer tokens per second." |
| click **Next** | |

## Screen 3: Why was this request slow? (4:30-8:00)

| Do | Say |
|----|-----|
| point at the bars | "Where each request's time goes. Red: about 6 seconds waiting for room, 2 on the GPU. Blue barely waits." |
| point at highlighted `k8s.pod.name` | "vLLM sends a span per request. The Collector adds the pod name. The app never knew it." |
| click the top Trace ID | "One request, two hops: the client, then vLLM." |
| click the `llm_request` row, then **Span Attributes** | "vLLM's own timing: this one waited over 6 seconds in the queue before the GPU touched it." |
| click **Resource Attributes**, point at `k8s.pod.name` | "And here is the pod name, on the request." |
| click the link icon on `llm_request`, then **This pod: how full it was** | "One click from this request to that pod: 100% full while it waited." |
| browser Back (Cmd+[) twice, to screen 3, click the top Trace ID in **Slowest requests on blue**, then `llm_request`, **Span Attributes** | "Same kind of request on blue: a few milliseconds in the queue. Same model, same GPU, same traffic. The only difference is how much room the server reserved." |
| Ctrl+Shift+Tab: the tab before is screen 4 (`demo/start.sh` opens it first). Explore has no Next button | |

## Screen 4: Is 8% too low? Is 90% too high? (8:00-10:00)

| Point at | Say |
|----------|-----|
| the rule | "Our rule of thumb, not vLLM's: look at the peak KV cache under real traffic. Above 90%: memory-constrained. Below 40%: over-provisioned." |
| the verdict | "Red is memory-constrained. Blue is over-provisioned. Both settings were wrong, in opposite directions." |
| GPU memory, then time to first token | "GPU memory never showed it. Time to first token did: about 6 seconds against under a tenth. That's what the user feels." |
| the sentence | "8% is too low, 90% is too high. Only the server's own signal could tell." Hand back to Henrique, slide 4. |

## If something breaks

Switch to the clean recording (`deck/video/gpu-obs-demo-v8-clean.mp4`), jump to the screen you were on, keep talking with the same lines. Space pauses it.
Chapter times are in [the cue sheet](deck/video/CUES-v8.md). The captioned version (`gpu-obs-demo-v8.mp4`) works without a narrator (sharing after the talk, or if both of us lose the mic).

| Symptom | Do |
|---------|----|
| A chart says "No data" | load not running: `demo/load.sh` and keep talking about the config; or the video |
| Trace click slow (> 5 s) | `demo/trace.sh`, or skip to the video chapter "screen 3" |
| Grafana logged out or blank | the video |
| Red not full after 2 min on screen 2 | keep talking about the config, it gets there; or the video, chapter "screen 2" |
