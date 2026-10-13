#!/usr/bin/env bash
# Stop tunnels and load. The cluster keeps running (and billing): terraform destroy removes it.
PIDS=/tmp/gpu-obs-tunnels.pid
[ -f "$PIDS" ] && kill $(cat "$PIDS") 2>/dev/null; rm -f "$PIDS"
pkill -f "port-forward svc/(kube-prometheus-stack|jaeger-ui)" 2>/dev/null
[ "${1:-}" = "--tunnels-only" ] && exit 0
kubectl -n inference delete job vllm-loadgen --ignore-not-found >/dev/null
echo "stopped"
