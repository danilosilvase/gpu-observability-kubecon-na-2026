# KubeCon NA 2026 · "Inference Is a Black Box" · Demo runbook (v4)

Slot: Mon 9 Nov 2026, 11:50 to 12:15 MST (18:50 Dublin), Salt Palace Level 2, 250 A-C, 25 min.

Deck: `deck/kubecon-na-2026-v4.pptx`, 21 slides, speaker notes on every slide. Rebuild with `deck/pptx/build_deck_v4.py` (see deck/pptx/README.md). Design rule for deck and demo: show, do not tell. If the audience needs the speaker to read a sentence to get the point, the slide or the dashboard is wrong.

## What changed from v3, and why

- **Removed the three-tab, three-terminal choreography** (Grafana, then `kubectl logs | grep | python3 -m json.tool`, then Jaeger, then copy a pod name back into Grafana). Three tool switches and a typed pipeline mid-sentence is exactly the complexity the speaker rejected. Replaced with Design A from r1-demo.md: two pre-opened tabs, nothing typed live.
- **Removed the live `kubectl apply` of the loadgen job during the talk.** It now starts at T-60min, so saturation has already happened once and is re-triggered on a timer before the anchor slide, not during it.
- **Removed the live cardinality `promql` break.** It was already optional in v3; cut entirely to protect slide 17's two minutes.
- **Removed copying a pod name from Jaeger into the Grafana `$pod` variable live.** The three dashboard rows and the Jaeger tab now carry the join visually; no live interaction is needed to make the point.
- **Timing retimed to the actual 21-slide notes** (demo anchor at 12:45, not 13:00; result at 13:30; done by 14:30, a 1:45 window, not 8 minutes), matching deck-text.md exactly.
- **Kept:** loadgen job and its two profiles, pinned versions, `admin_cidrs`/`terraform.tfvars` pattern, three port-forwards, `Recreate` strategy rationale, 24h NodePool expiry warning, teardown command, fallback video concept (re-specified below).

## Timing (21 slides, 25 min slot)

| min | slide | what |
|-----|-------|------|
| 0:00 | 1-2 | Cover, who we are (Danilo, then Henrique) |
| 1:00 | 3-4 | The 02:14 incident, sparkline shows p99 doubling, hook |
| 3:00 | 5-8 | Why GPU counters lie: pre-allocation, prefill vs decode, profiler counters, vocabulary (Henrique) |
| 7:00 | 9 | The one idea: the pod is the join key (Danilo, pause here) |
| 8:00 | 10-11 | Signal 1 DCGM per pod, cardinality war story |
| 9:30 | 12-13 | Signal 2: the log line, Fluent Bit + Lua pipeline |
| 12:15 | 14 | Demo anchor: "watch two rows", stay on the deck 15 s |
| 13:00 | live | Grafana three rows, 90 s (Henrique drives, Danilo narrates) |
| 14:30 | live | Jaeger pre-opened trace, 60 s |
| 15:30 | live | Back to Grafana, the aligned spike, 30 s |
| 16:00 | 15 | Result slide: the numbers from the slide, not the rig |
| 16:30 | 16 | Signal 3 trace screenshot, 1 min (Henrique) |
| 17:30 | 17 | The join. Protected two minutes. |
| 19:30 | 18 | One gotcha, 20 s, cut first if late |
| 19:50 | 19 | Where this is going |
| 20:30 | 20 | Steal this |
| 21:00 | 21 | Thanks, QR, Q&A (4 min) |

Live demo window: 13:00 to 16:00, three minutes used. Hard stop at 16:30 whatever happens; slide 17 is never cut.

## T minus 1 day

```bash
cd terraform
export AWS_PROFILE=<your-admin-profile>
printf 'aws_profile = "%s"\nadmin_cidrs = ["%s/32"]\n' "$AWS_PROFILE" "$(curl -s https://checkip.amazonaws.com)" > terraform.tfvars
helm repo remove stable argo 2>/dev/null || true
terraform init
terraform apply -target=module.eks -auto-approve
terraform apply -auto-approve
./validate.sh          # expect 12 passed / 0 failed
```

Versions: vLLM v0.30.0 (needs >= 0.10.2 for OTel tracing on the V1 engine), Fluent Bit 5.1.3 (verified on the rig, 5.1 line is current, keep in deck), dcgm-exporter 4.8.4. vLLM pods use `strategy: Recreate`, one GPU per pod, NodePool capped at two GPUs, a RollingUpdate can never surge.

NodePool `expireAfter: 24h`. Apply the evening before, not two days before, or GPU nodes rotate during the talk. If they rotate anyway, live pod names will not match the slide 15 and 17 screenshots; say so out loud, the string is the same across pipelines, not which string.

Record the fallback video tonight (QuickTime, 60s, muted, same two tabs in the same order as the live beats below). Save as `gpu-obs-demo-fallback.mov` on the laptop desktop.

Dashboard build, same evening: open Grafana, confirm the panel layout below matches `gpu-inference-obs`, re-export the dashboard JSON into the repo if anything drifted.

## Grafana dashboard layout (`gpu-inference-obs`), top to bottom

The dashboard must say the whole story with the sound off. Three rows, no scrolling, 125% zoom:

1. **"GPU memory: flat"**: DCGM `FB_USED`, two series, constrained = red, overprov = grey, fixed colour mapping on the `$pod` variable so it never shuffles. Unit GB, y-axis fixed 0-24. Legend: `vllm-constrained (3.6 GB)` / `vllm-overprov (20.5 GB)`.
2. **"KV cache: 0.1% to 100%"**: Fluent Bit `kv_cache_usage_pct`, same colour pair. Threshold line at 100%, red fill above 90%. Legend shows live value, not just series name.
3. **"Queue time: 0.3 s to 4.8 s"**: vLLM `/metrics` `request_queue_time_seconds` p95, same colours. Threshold marker at 1s (amber) and 3s (red).

Vertical annotation labelled "load hits", created by the loadgen job itself (Grafana annotation API call at the start of the saturate profile) so it always sits at the real start of the current run, never a hard-coded clock time. Drawn across all three rows so the alignment is impossible to miss. On stage say "where the line is", never a clock time. Time range: last 15 min, refresh 10s. `$pod` variable default "All", with `vllm-constrained` and `vllm-overprov` pinned as the only two series rendered anywhere.

## Jaeger pre-opened state

URL pattern, built and bookmarked the night before so nothing is clicked live:

```
http://localhost:16686/trace/<trace_id>?uiFind=k8s.pod.name
```

Pre-filtered to `service=vllm-constrained`, `operation=llm_request`, lookback widened to 1 hour (not the default), sorted by duration, slowest trace already selected by trace ID in the URL, root span already expanded, tags panel already open showing `k8s.pod.name`, `gen_ai.latency.time_in_queue`, `gen_ai.latency.time_in_model_decode`. "Find Traces" is never clicked on stage.

## T minus 60 min

```bash
export AWS_PROFILE=<your-admin-profile>
aws eks update-kubeconfig --name gpu-obs-demo --region eu-central-1
kubectl get nodes -L node.kubernetes.io/instance-type
kubectl -n inference get pods -o wide
```

If this does not show exactly two `Running` pods, stop here, do not attempt a live recovery, go straight to the fallback video plan below.

```bash
kubectl -n observability port-forward svc/kube-prometheus-stack-grafana 3000:80 &
kubectl -n observability port-forward svc/jaeger-ui 16686:16686 &
kubectl -n inference delete job vllm-loadgen --ignore-not-found --wait=true
kubectl -n inference apply -f ../manifests/20-vllm/loadgen-job.yaml
```

Port-forwards run on a phone hotspot already proven to work, laptop never touches venue Wi-Fi for the demo tabs. Loadgen runs two 12-minute profiles (steady, concurrency 16, overprov; saturate, concurrency 192, constrained). Saturation visible in the dashboard within about 90 seconds.

Open and arrange tabs in order, all logged in, 125% zoom:
1. Grafana `gpu-inference-obs`, three-row layout above, time range last 15 min
2. Jaeger, pre-filtered trace as above
3. Deck

## T minus 5 min

- Re-check `kubectl -n inference get pods -o wide`, both `Running`.
- Confirm Grafana row 2 is climbing or has already peaked once; if the 12-minute cycle is about to end flat, re-apply the loadgen job now so saturation lands inside the 12:45 window, timed from this table, not from feel.
- Confirm the Jaeger trace is still the slowest one visible; if a newer slower trace exists, re-bookmark its trace ID.
- Take a full-resolution screenshot of the three-row Grafana view as a static backup slide, flip to it in two clicks if the live tab misbehaves.

## The five beats

**Beat 1 (0:00, slide 14, stay on deck, 15s)**
Says: "Watch two rows. Row one, GPU memory, flat. Row two, the log, KV cache and waiting take off."
Sees: slide 14's two-pod summary and the "watch two rows" instruction text, no screen switch yet.

**Beat 2 (0:15, switch to Grafana, 90s)**
Says: "FB_USED hasn't moved. KV cache on the red line just crossed 100%. Queue time went from 0.3 to 4.8 seconds."
Sees: the three stacked rows, red annotation at load start, red line flat on row 1, pegged at 100% on row 2, stepping up on row 3, no clicking, speaker points only.

**Beat 3 (1:45, switch to Jaeger, 60s)**
Says: "Same pod name. 5.73 second span, 0.61 in queue, 5.33 in decode."
Sees: the already-expanded root span, `k8s.pod.name` tag visible, no typing or copying.

**Beat 4 (2:45, back to Grafana, 45s)**
Says: "DCGM through exported_pod, Fluent Bit through pod_name, vLLM traces through pod. Same string, three systems, one second."
Sees: the same three-row view, eye follows the vertical annotation line down through all three panels in one screen, no interaction.

**Beat 5 (3:30, slide 15)**
Says: the three numbers again, read from the slide, not a live readout, so they survive even if the rig froze mid-sentence.
Sees: slide 15's static numbers (3.6 GB, 100%, 0.3s to 4.8s).

## Fallback video

`gpu-obs-demo-fallback.mov`, 60 seconds, muted, recorded the night before on the exact same two tabs (Grafana three-row view, then Jaeger expanded trace) in the exact same order as the five beats. Played inline, narrated live over it exactly as scripted above. Trigger: if the T-60min pod check fails, skip live entirely, open the video cold, no recovery attempt on stage.

## Risk register

1. Venue Wi-Fi drops mid-sentence. Mitigation: hotspot-only port-forwards, proven at T-60min.
2. NodePool rotates overnight, pod names mismatch slides. Mitigation: apply the evening before; if it still rotates, say so, the shape survives even if the string doesn't.
3. Loadgen cycle finishes before 12:45 and charts go flat. Mitigation: re-apply at T-5min per the checklist above, timed, not felt.
4. Jaeger has no matching trace in its default lookback. Mitigation: 1-hour lookback, trace ID pinned in the bookmarked URL, never click "Find Traces" live.
5. Grafana tab drops to blank or login screen. Mitigation: stay logged in and tested at T-60min; static screenshot backup slide, two clicks away.

## Teardown (same day, rig costs about $2.4/hr)

```bash
cd terraform
terraform destroy -auto-approve
```

## Open items before Nov 9

- Attribution: removed from slide 20 (placeholder would have shipped); credit the original session design in the repo README.
- Repo publish to `github.com/danilosilvase/gpu-observability-kubecon-na-2026` blocked on Code Defender approval (Vijay). Do not push the branded template or research folder.
- CNCF feedback QR on slide 21 placeholder, ask Henrique or CNCF for the session QR.
- Rehearse the five-beat sequence twice against the clock, once ending in the fallback video deliberately, so the recovery itself is rehearsed, not just the happy path.
- Co-speaker split with Henrique: confirm he drives Grafana for beat 2 and the trace screenshot narration on slide 16, Danilo drives beats 1, 3, 4, 5 and slide 17.
- Dry run specifically checks Jaeger load time on venue-class hardware; if unreliable, fall back to Design B from r1-demo.md (drop Jaeger, keep the pre-captured trace screenshot already on slide 16) rather than cutting the whole live segment.
- Add the Grafana annotation call to `manifests/20-vllm/loadgen-job.yaml` (curl to /api/annotations at saturate start) and re-export the dashboard JSON with the three-row layout, fixed colours and takeaway panel titles.
- Fallback video is also a candidate to embed on slide 15 as a muted 60 s clip, so the fallback is one click away inside the deck.
