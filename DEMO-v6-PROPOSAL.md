# Demo v6 proposal: one question, one screen (Oct 15 2026)

Status: BUILT Oct 15 (stage + deep-dive dashboards, deck v6, runbook v6, recorder v6). See DEMO-RUNBOOK.md.

Source: 5 independent reviews (first-time attendee, talk coach, SRE lead, demo engineer, contrarian), checked against the accepted Sessionize abstract. All five converged on the same cut.

## Why v5 is too hard
- The aha depends on "KV cache %", which is never defined. A Prometheus/OTel person has never run an LLM server.
- "GPU memory is flat" is not surprising unless you know vLLM reserves its memory at start-up.
- Too many screens and terms on stage: DCGM, SM active, traceparent, hops, cardinality, two trace tables, Explore split view.

## The one sentence
The GPU memory graph you page on is flat on the pod that is drowning; the server's own log knows, and the pod name connects it to everything else.

## Teach before the demo (one slide, 30 s)
Car park metaphor: GPU memory = the size of the car park you rented (fixed at start-up). KV cache = how full it actually is. Queue = cars circling for a space. The GPU exporter reads the sign at the gate, the server log counts the cars.

## Demo (about 3 min, one screen, live)
| Time | On screen | Say |
|---|---|---|
| 0:00 | 2 pods x 3 big numbers (GPU memory, KV cache, request time). Verdict tiles read OK / OK | "Same model, same GPU. One is about to fall over. Which one?" (let the room guess) |
| 0:20 | Load starts | "Lots of long requests to red, a trickle to blue." |
| 0:40 | GPU memory: flat, red lower | "The number we page on. Red looks healthiest." |
| 1:00 | KV cache: red 100%, blue 0% | "The server's log says red's car park is full." (the aha) |
| 1:20 | Request time 12 s vs 0.2 s, verdict flips | "Twelve seconds versus a fifth. Same hardware. Only the log could tell." |
| 1:45 | Click red's slowest request: trace shows client then server, same pod name | "The request a user felt. Every signal carries the pod name." |
| 2:15 | One click to that pod's KV cache at that second: 100% | "Slow request to cause, one click." |
| 2:40 | Back to the six numbers | "Three signals, one pod name. That is the whole pipeline." |

## The abstract's "what broke" items move to slides after the demo (1 min each)
1. Cardinality: per-pod GPU metrics, 14 live series vs 56 after a few restarts; fix = keep the pod name, drop pod labels (config snippet).
2. Lua parsing: the raw log line, the 15-line filter, the metric it becomes.
3. OTel Collector: k8sattributes stamps k8s.pod.name; Grafana trace-to-metrics uses it (config snippet).

## Off stage (Q&A / deep-dive dashboard tab)
SM active vs GPU util, queue p95 panel, tokens/s, running/waiting/preemptions, the overprov trace table, traceparent mechanics, cardinality live panel.

## 20-minute talk shape
| Min | Section |
|---|---|
| 0-2 | Hook: latency doubled, every GPU dashboard green |
| 2-5 | Why GPU metrics lie for inference + car park slide |
| 5-8 | The pipeline in one diagram: 3 signals, pod name join |
| 8-11 | Demo |
| 11-17 | What broke (3 slides) with the configs |
| 17-19 | Steal this: 3 numbers to watch, repo QR |
| 19-25 | Q&A |

## Build list (about 12 h, before the 4 Nov freeze)
| Change | Hours | Risk |
|---|---|---|
| Stage dashboard: 6 big stat tiles + verdict + one trace table; current dashboard kept as "deep dive" | 4 | Low |
| Verdict reads OK at idle (neutral below a KV threshold) | 1 | Low |
| Plain-English panel titles ("What the server's log says: car park full") | 1 | Low |
| Trace click lands directly on that pod's KV cache | 2 | Medium, fallback demo/trace.sh |
| Car park slide, 3 "what broke" slides, slide 15 numbers | 3 | None |
| Re-record 3-min fallback video | 2 | Low (rig up) |

## Open choice
Live load transition (the aha happens in front of the room, about 40 s for KV to fill) versus load started 5 min early (robust, no waiting). Recommendation: live, with the fallback video one keypress away.
