#!/usr/bin/env bash
# GPU-Aware Observability demo — deploy end to end on an EKS Auto Mode cluster.
# Prereqs: kubectl context on an EKS Auto Mode cluster; kube-prometheus-stack
# installed (for ServiceMonitor CRDs + Prometheus + Grafana); HF model pullable.
set -euo pipefail
K="kubectl"

echo "==> 0. cluster: GPU NodePool + namespaces"
$K apply -f 00-cluster/

echo "==> 1. dcgm-exporter (standalone, cardinality-safe)"
$K apply -f 10-gpu-metrics/

echo "==> 2. vLLM (2 replicas)"
$K apply -f 20-vllm/vllm-deployment.yaml
# create the over-provisioned vs constrained contrast:
$K -n inference patch deploy vllm-opt125m --type=json \
  -p='[{"op":"replace","path":"/spec/template/spec/containers/0/args/1","value":"--gpu-memory-utilization=0.30"}]' || true
echo "   (one replica set to 0.30 util = over-provisioned; scale to show both)"

echo "==> 3. logs: Fluent Bit + Lua token extractor"
$K apply -f 30-logs/

echo "==> 4. traces: Jaeger + OTel Collector"
$K apply -f 50-prometheus/jaeger-demo.yaml
$K apply -f 40-traces/

echo "==> 5. Prometheus ServiceMonitors"
$K apply -f 50-prometheus/servicemonitors.yaml

echo "==> waiting for GPU node + vLLM to be Ready (can take ~3-5 min)"
$K -n inference rollout status deploy/vllm-opt125m --timeout=600s

echo "==> 6. generate load"
$K apply -f 20-vllm/loadgen-job.yaml

cat <<'MSG'

Next:
  - Import 60-grafana/gpu-inference-dashboard.json into Grafana.
  - Jaeger UI:      kubectl -n observability port-forward svc/jaeger-ui 16686:16686
  - Verify Lua:     kubectl -n observability logs ds/fluent-bit | grep gen_tokens_per_s
  - Cardinality demo: see 50-prometheus/CARDINALITY-DEMO.md
MSG
