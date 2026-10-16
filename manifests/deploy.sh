#!/usr/bin/env bash
# Deploy the demo onto a cluster you already have (Terraform does the same from these files).
# Needs: EKS Auto Mode (or GPU nodes with the NVIDIA device plugin) + kube-prometheus-stack in "observability".
set -euo pipefail
cd "$(dirname "$0")"

kubectl apply -f 00-cluster/                       # GPU NodePool + namespaces
kubectl apply -f 10-gpu-metrics/                   # signal 1: dcgm-exporter, GPU -> pod
kubectl apply -f 20-vllm/vllm.yaml                 # 2 vLLM pods: constrained vs over-provisioned
kubectl apply -f 30-logs/                          # signal 2: Fluent Bit + Lua -> metrics
kubectl apply -f 40-traces/                        # signal 3: OTel Collector + Jaeger
kubectl apply -f 50-prometheus/servicemonitors.yaml
kubectl apply -f 60-grafana/jaeger-datasource.yaml # trace -> GPU links
kubectl -n observability create configmap gpu-inference-dashboard \
  --from-file=60-grafana/gpu-inference-dashboard.json --from-file=60-grafana/gpu-inference-deep-dive.json --dry-run=client -o yaml \
  | kubectl label --local -f - grafana_dashboard=1 -o yaml | kubectl -n observability apply -f -
kubectl -n observability create configmap gpu-walkthrough-dashboards \
  --from-file=60-grafana/walk/ --dry-run=client -o yaml \
  | kubectl label --local -f - grafana_dashboard=1 -o yaml | kubectl -n observability apply -f -   # the 4 demo screens

kubectl -n inference rollout status deploy/vllm-constrained --timeout=900s
kubectl -n inference rollout status deploy/vllm-overprov    --timeout=900s
echo "Ready. Start the demo: ../demo/start.sh"
