#!/usr/bin/env bash
# One command before going on stage: tunnels + fresh load + open the dashboard.
set -euo pipefail
cd "$(dirname "$0")/.."
aws eks update-kubeconfig --name gpu-obs-demo --region eu-central-1 >/dev/null

# Self-healing tunnels. kubectl port-forward can go stale (hangs, never exits), so a watchdog
# curls each one every 5 s and restarts it on the first failure.
PIDS=/tmp/gpu-obs-tunnels.pid
tunnel() {  # service local:remote health-path
  ( set +e; while true; do
      kubectl -n observability port-forward "svc/$1" "$2" >/dev/null 2>&1 & pf=$!
      sleep 3
      while kill -0 $pf 2>/dev/null && curl -s -m 3 -o /dev/null "http://127.0.0.1:${2%%:*}$3"; do sleep 5; done
      kill -9 $pf 2>/dev/null; wait $pf 2>/dev/null
    done ) & echo $! >> "$PIDS"
}
demo/stop.sh --tunnels-only >/dev/null
tunnel kube-prometheus-stack-grafana    3000:80     /api/health
tunnel jaeger-ui                        16686:16686 /
tunnel kube-prometheus-stack-prometheus 9090:9090   /-/ready

demo/load.sh
sleep 3
open "http://localhost:3000/d/gpu-inference-obs?orgId=1&kiosk" 2>/dev/null || true
echo "Grafana   http://localhost:3000   (admin / gpu-obs-demo)"
echo "Saturation shows in ~90 s. Stop tunnels: demo/stop.sh"
