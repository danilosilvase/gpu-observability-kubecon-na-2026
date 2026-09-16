# KubeCon NA 2026 · "Inference Is a Black Box" · Demo runbook

Slot: Mon 9 Nov 2026, 11:50 to 12:15 MST (18:50 Dublin), Observability Day Room 1, 25 min.
Deck: deck/kubecon-na-2026.html (open in browser, press F for fullscreen, N for speaker notes, arrows to move).

## Timing (25 min)

| min | slide | what |
|-----|-------|------|
| 0:00 | 1-2 | Cold open: the 2am page, "which pod?" |
| 1:30 | 3-4 | Three silos, why GPU util lies |
| 3:30 | 5 | The one idea: the pod is the join key (pause here) |
| 4:30 | 6-7 | Architecture, same string in all three pipelines |
| 6:30 | 8-9 | DCGM pod mapping, war story 1 cardinality |
| 9:30 | 10 | Fluent Bit + Lua |
| 11:30 | 11 | OTel k8sattributes |
| 13:00 | 12 | LIVE DEMO (8 min, hard stop at 21:00) |
| 21:00 | 13-14 | Skip if demo worked, otherwise use as backup |
| 21:00 | 15-16 | War stories 2 and 3, takeaways |
| 23:30 | 17 | Repro, thanks, Q&A into the buffer |

## T minus 1 day

```bash
cd terraform
export AWS_PROFILE=<your-admin-profile>
helm repo remove stable argo 2>/dev/null || true
terraform init
terraform apply -target=module.eks -auto-approve
terraform apply -auto-approve
./validate.sh          # expect 12 passed / 0 failed
```

Note the NodePool has expireAfter: 24h. Apply the evening before, not two days before, or the GPU nodes will rotate during the talk. If they do rotate, the pod names in slide 7 and 14 no longer match the live rig; that is fine, the point is the string is the same across pipelines, not which string.

Record a fallback video of the full demo path the same evening (QuickTime, ~6 min). Put it on the laptop desktop as `gpu-obs-demo-fallback.mov`.

## T minus 60 min (in the room, on venue Wi-Fi or hotspot)

```bash
export AWS_PROFILE=<your-admin-profile>
aws eks update-kubeconfig --name gpu-obs-demo --region eu-central-1
kubectl get nodes -L node.kubernetes.io/instance-type
kubectl -n inference get pods -o wide
```

Open three terminals and leave them running:

```bash
# T1: Grafana
kubectl -n observability port-forward svc/kube-prometheus-stack-grafana 3000:80
# T2: Jaeger
kubectl -n observability port-forward svc/jaeger-ui 16686:16686
# T3: load, so charts are moving during the talk
kubectl -n inference delete job loadgen --ignore-not-found
kubectl -n inference apply -f ../manifests/20-vllm/loadgen-job.yaml
```

Browser tabs, in this order, all logged in and pre-zoomed to 125 percent:
1. http://localhost:3000/d/gpu-inference-obs  (admin / gpu-obs-demo), time range last 15 min, refresh 10s
2. http://localhost:16686  service = vllm-overprov, Find Traces
3. Deck

Terminal font size 22+, dark theme, prompt shortened.

## Demo script (8 min)

### 1. Grafana, the money shot (3 min)
Tab 1. Point at the top row.
- "Two pods, same model, same load generator. Framebuffer used: constrained about 20 GB, over-provisioned about 6.7 GB."
- Middle row: "SM active and tokens per second, essentially the same."
- "Same throughput, three times the memory reservation. That is a right-sizing decision, and I can only make it because every one of these series carries the pod name."
Change the `$pod` variable to one pod, show every panel follows.

### 2. Fluent Bit, the log side (2 min)
Terminal:
```bash
kubectl -n observability logs ds/fluent-bit --tail=200 | grep gen_tokens_per_s | tail -3 | python3 -m json.tool
```
Point at `gen_tokens_per_s`, `kv_cache_usage_pct`, and `pod_name` at the top level. "That was free text ten seconds ago. One Lua function."

### 3. Jaeger, trace to GPU (3 min)
Tab 2. Open the slowest vllm-overprov trace. Expand the root span tags.
- Point at `k8s.pod.name`, `gen_ai.usage.completion_tokens`.
- Copy the pod name. Back to Tab 1, paste into `$pod`. "Slow request, this pod, this GPU, this second. Trace, pod, GPU, root cause."

Hard stop at minute 21 whatever happens.

## Optional live break (only if ahead of time, otherwise skip)
Cardinality explosion, see manifests/50-prometheus/CARDINALITY-DEMO.md. Prometheus tab:
```promql
count({__name__=~"DCGM_.*"})
```
Do not flip ENABLE_POD_LABELS live; show the pre-captured before/after numbers on slide 9 instead.

## Fallbacks
- Venue network blocks kubectl: hotspot from phone. Port-forwards only need outbound 443 to the EKS endpoint.
- Rig unreachable: play `gpu-obs-demo-fallback.mov`, narrate over it, then slides 13 and 14.
- Grafana empty: check T3 loadgen is running (`kubectl -n inference get jobs`), re-apply.
- Fluent Bit shows no pod_name: `kubectl -n observability logs ds/fluent-bit | grep -i "invalid pattern"`; that is war story 3 live, own it and move to slide 15.

## Teardown (same day, the rig costs about $2.4/hr)
```bash
cd terraform
terraform destroy -auto-approve
```

## Open items before Nov 9
- Review call with the original AWS author (calendar draft Thu 17 Sep 17:00 Dublin, not yet sent): confirm attribution wording for slide 17.
- Repo published at github.com/danilosilvase/gpu-observability-kubecon-na-2026; keep it in sync with the deck.
- Replace slide 9 bar chart with real before/after series counts from CARDINALITY-DEMO.md.
- Rehearse twice against the clock, once with the fallback video.
