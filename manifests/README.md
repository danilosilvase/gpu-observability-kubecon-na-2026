# Deployable configs

**The pod is the join key.** Each signal carries the pod name; Grafana joins on it.

| # | Signal | Component | File | Pod label |
|---|--------|-----------|------|-----------|
| 1 | GPU metrics | dcgm-exporter, `--kubernetes=true` | `10-gpu-metrics/dcgm-exporter.yaml` | `exported_pod` |
| 2 | Serving logs -> metrics | Fluent Bit + Lua + `log_to_metrics` | `30-logs/fluent-bit.yaml` | `pod_name` |
| 3 | Traces, 2 hops | OTel Collector `k8sattributes` -> Jaeger | `40-traces/otel-collector.yaml` | `k8s.pod.name` |
| - | Trace -> GPU links | Grafana Jaeger datasource | `60-grafana/jaeger-datasource.yaml` | maps `k8s.pod.name` |
| - | Dashboard | Grafana | `60-grafana/gpu-inference-dashboard.json` | `$pod` |

Workload: `20-vllm/vllm.yaml` (two vLLM pods, 15% vs 90% GPU memory) and
`20-vllm/loadgen-job.yaml` (load + client span, hop 1 of each trace).

## Deploy

```bash
./deploy.sh          # onto an existing cluster
# or: ../terraform   # cluster + everything, from these same files
```

## Where to look in the code

| Talk point | Where |
|------------|-------|
| What broke: cardinality | `50-prometheus/CARDINALITY-DEMO.md`, `ENABLE_POD_LABELS=false` in dcgm-exporter |
| Lua that pulls tokens/s and KV cache out of the log | `extract_tokens.lua` in `30-logs/fluent-bit.yaml` |
| Collector config that makes trace-to-GPU queryable | `k8sattributes` in `40-traces/otel-collector.yaml` + `tracesToMetrics` in `60-grafana/jaeger-datasource.yaml` |

EKS Auto Mode ships the NVIDIA driver and device plugin, so dcgm-exporter runs standalone.
Do not install the GPU Operator there. Elsewhere, use the GPU Operator's bundled dcgm-exporter.
