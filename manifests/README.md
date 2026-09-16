# GPU-Aware Observability — deployable reference (clean-room rebuild)

Reproduces the KubeCon talk "Inference Is a Black Box": correlate three GPU
inference signals at the **pod** level.

| Signal | Component | Path |
|---|---|---|
| GPU hardware metrics | dcgm-exporter (K8s mode, standalone) | `10-gpu-metrics/` |
| Serving logs -> tokens/s | Fluent Bit + Lua | `30-logs/` |
| Distributed traces | vLLM OTLP -> OTel Collector (k8sattributes) | `40-traces/` |
| Metrics store + ServiceMonitors | Prometheus Operator | `50-prometheus/` |
| Joined dashboard | Grafana (pod template var) | `60-grafana/` |

**Join key = pod identity.** DCGM adds `exported_pod`/`exported_namespace`
(`--kubernetes=true`). Fluent Bit's kubernetes filter + Lua promote
`pod_name`/`namespace`. OTel's k8sattributes stamps `k8s.pod.name` on spans.

## Cluster choice
EKS Auto Mode. Auto Mode manages NVIDIA drivers + device plugin on GPU nodes,
so we run **dcgm-exporter standalone**, NOT the GPU Operator driver stack
(it would conflict). On self-managed nodegroups, use the GPU Operator instead
and drop `10-gpu-metrics/` in favour of its bundled dcgm-exporter.

## Deploy
```bash
./deploy.sh
```

## The three talk "war stories"
1. Cardinality explosion  -> `50-prometheus/CARDINALITY-DEMO.md`
2. Fluent Bit Lua parsing  -> `30-logs/fluent-bit-config.yaml` (extract_tokens.lua)
3. Trace-to-GPU correlation -> `40-traces/otel-collector.yaml` (k8sattributes)

## Cost
One g5.xlarge (A10G) on-demand ~ $1.0/hr. NodePool sets expireAfter=24h. Tear
down: `kubectl delete -f . -R` then delete the NodePool.

## Not validated on a live cluster yet
These are clean-room manifests built from the reference pattern. Pin/adjust:
image tags, HF model access, kube-prometheus-stack release label
(`release: kube-prometheus-stack` on ServiceMonitors must match your install).
