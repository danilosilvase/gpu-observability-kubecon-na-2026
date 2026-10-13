#!/usr/bin/env bash
# One command before going on stage: tunnels + fresh load + open the dashboard.
set -euo pipefail
cd "$(dirname "$0")/.."
aws eks update-kubeconfig --name gpu-obs-demo --region eu-central-1 >/dev/null

# Self-healing tunnels: kubectl port-forward dies on a dropped connection, so loop it.
PIDS=/tmp/gpu-obs-tunnels.pid
tunnel() { ( while true; do kubectl -n observability port-forward "svc/$1" "$2" >/dev/null 2>&1; sleep 1; done ) & echo $! >> "$PIDS"; }
demo/stop.sh --tunnels-only >/dev/null
tunnel kube-prometheus-stack-grafana 3000:80
tunnel jaeger-ui 16686:16686
tunnel kube-prometheus-stack-prometheus 9090:9090

demo/load.sh
sleep 3
open "http://localhost:3000/d/gpu-inference-obs?orgId=1&kiosk" 2>/dev/null || true
echo "Grafana   http://localhost:3000   (admin / gpu-obs-demo)"
echo "Saturation shows in ~90 s. Stop tunnels: demo/stop.sh"
