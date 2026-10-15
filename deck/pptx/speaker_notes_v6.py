"""Speaker scripts for the v6 deck, keyed by final slide position (main path 1-14, appendix divider 15).
Appendix slides 16+ keep their v4 scripts (speaker_notes.py). Plain words, read aloud, no em dashes.
Timing: about 18 min of talk including a 3-min demo, leaving about 7 min for Q&A in the 25-min slot."""

NOTES = {
1: """[0:00, 0:15] [Danilo] Cover while people settle.
Check the clicker. Grafana open on the second screen, stage dashboard in kiosk mode, rig idle (both verdict tiles say OK).
Next: title slide.""",

2: """[0:15, 1:00] [Danilo + Henrique] Who we are, one line each, then the thesis.
Danilo: "I'm Danilo, I build platforms for customers at AWS, mostly Kubernetes and ML infrastructure." Henrique: "I'm Henrique, AWS Support, I see a lot of GPU incidents after the fact." Point at the two chips: "We tried to explain a slow inference service with the GPU dashboard and got nothing. The answer was in a log line."
Next: the incident.""",

3: """[1:00, 2:30] [Danilo] The incident.
"It's 02:14. The page fires. Every GPU chart is green." Let the sparkline do the rest. Pause. "Utilisation 95%, memory 90%, both flat for an hour. Pods Ready, nothing throttled, no restarts. Every signal the hardware gives you says busy and healthy. Nobody knows why. That is the black box."
Next: the same counter, opposite story.""",

4: """[2:30, 3:00] [Danilo] 30 seconds.
"Across the industry the average production GPU runs at about 5% utilisation. Ours read 95%. Same counter. One looks saturated, one looks idle, and neither tells you anything about the inference work."
Next: Henrique, why GPU memory lies.""",

5: """[3:00, 4:00] [Henrique] GPU memory is a config value.
"Every LLM server grabs its GPU memory before the first request. vLLM calls it gpu-memory-utilization." Point at the two flat lines. "Two pods, same model. Blue got 90% of the GPU: 20.5 GB. Red got 15%: 3.5 GB. The orange line is where we start a heavy load. Neither line moves. Ever." Then: "Which one is about to fall over? The small one. And this chart, the one most of us page on, cannot tell you."
Next: so what does move?""",

6: """[4:00, 5:00] [Henrique] The car park. This slide is why the demo makes sense, do not rush it.
"Think of GPU memory as a car park. When the pod starts, it rents a car park of a fixed size. That's the number DCGM shows you: the size on the sign. Inside, every request that is running parks its working state, that's the KV cache. When the car park is full, new requests circle and wait." Point at red: "Small car park, every space taken, cars circling." Point at blue: "Huge car park, almost empty, we're paying for it." Last line: "The GPU exporter reads the sign. Only the server's own log counts the cars."
Next: Danilo, how we get all three onto one screen.""",

7: """[5:00, 6:30] [Danilo] The pipeline, one idea: the pod name.
"Three tools, three signals. DCGM knows which pod owns a GPU. Fluent Bit knows which pod wrote a log line. The OTel Collector knows which pod a request went through. The only thing all three share is the pod name. So we stamp it on everything and join at query time." Click: the pill, then the WHERE. "That's the whole architecture. All the configs are in the repo."
Next: the demo.""",

8: """[6:30, 7:00] [Danilo] Set up the question, then switch to Grafana. Henrique clicks, Danilo narrates.
"Two pods, same model, same GPU. Red got 15% of the memory, blue 90%. We'll send lots of long requests to red and a trickle to blue. Watch three numbers: GPU memory, how full the car park is, and how long a request takes. Which pod breaks first?" Let one person answer.
DEMO, 7:00 to 10:00 (runbook: DEMO-RUNBOOK.md). Henrique runs demo/load.sh at the switch.
1. Idle: both tiles OK. "Both look fine."
2. Load hits (about 20 s): GPU memory tiles do not move. "The number we page on. Red even looks healthiest."
3. KV cache: red climbs to 99-100%, blue stays at 0. "Red's car park is full." (the aha, pause)
4. Request time: red about 12 s, blue about 0.13 s. Verdict tiles flip: MEMORY-CONSTRAINED, OVER-PROVISIONED. "Same hardware. Only the log could tell."
5. Click the top trace ID: two bars, client then vLLM, same pod name. Click the link icon on llm_request, then "This pod: how full it was". "One slow request, one click, that pod's car park at that second: full."
6. Back to the dashboard. "Three signals, one pod name."
If anything stalls: play deck/video, or demo/trace.sh for step 5.
Next: back to slides, the recap.""",

9: """[10:00, 10:30] [Danilo] Recap, or the backup if the demo failed.
"This is what you just saw. GPU memory: 3.5 and 20.5 GB, flat. KV cache from the log: 99% versus 0%. Requests: 12 seconds versus 0.13 seconds. One pod name on every signal." If the demo failed, walk the screenshot with the same four lines.
Next: three things we had to get right, the ones in the abstract. One minute and a half each.""",

10: """[10:30, 12:30] [Henrique] Deep dive 1: what broke, cardinality.
"The first thing we broke was Prometheus. To join on the pod name, dcgm-exporter has to put the pod name on every GPU counter. Every time a pod restarts it gets a new name, so you get a brand new set of series, and Prometheus keeps the old ones until retention." Point at 14 and 56: "Same two GPUs, seven counters. 14 series live. 56 in the last hour, after three restarts." Click: fleet math. "At fleet scale, 1.4 million series before you add a single pod label, and every label multiplies by churn." Then the rule: "Keep the pod name. Drop every other pod label. Join at query time."
Next: the log line.""",

11: """[12:30, 14:30] [Danilo] Deep dive 2: the Lua parsing.
Point at the raw line: "This is what vLLM prints every ten seconds. Token throughput, running, waiting, and the KV cache. It's text, not a metric." Walk the pipeline left to right: "Fluent Bit tails the container log, the kubernetes filter adds the pod name, fifteen lines of Lua pull out the numbers, grep keeps only these lines, log_to_metrics turns them into gauges, and Prometheus scrapes them next to DCGM." Honest caveat: "vLLM also exposes most of this on /metrics. This pipeline is for the servers that don't, or when logs are all you get. Same pipeline, different regex."
Next: traces.""",

12: """[14:30, 16:30] [Danilo] Deep dive 3: the OTel Collector config.
"vLLM emits a span per request, and our client adds its own span and a traceparent header, so one trace has two hops: client, then vLLM. That's this 11.9-second request." Left box: "The app never knew its pod name. The Collector's k8sattributes processor looks up who sent the span and adds k8s.pod.name." Right box: "In Grafana, the Jaeger datasource maps k8s.pod.name to the metric label. That's what turned one click from a slow request into that pod's KV cache." Gotcha if time: "vLLM tracing disappeared in the V1 rewrite and came back in 0.10.2. If your traces vanished after an upgrade, that's why."
Next: what to take home.""",

13: """[16:30, 17:30] [Henrique] Steal this.
"Three numbers: KV cache, request or queue time, and SM active instead of GPU util. One filter: fifteen lines of Lua, change the regex for your server. One rule: the pod name on every signal, nothing else on the metrics. Zero new agents."
Next: thank you and the repo.""",

14: """[17:30, 18:00] [Danilo] Thank you, repo, CNCF feedback QR. Then Q&A (about 7 min).
Likely questions and where the answer is: "why not just scrape /metrics" (slide 11 caveat), "does GPU util really not move" (appendix: it does go up, it just cannot say why), "MIG or time-slicing" (dcgm-exporter 4.5+ per-process metrics), "disaggregated prefill/decode" (appendix: the join key becomes request id plus pod), "EKS Auto Mode" (appendix gotcha).""",

15: """Appendix divider. Only reached from Q&A.""",
}
