#!/usr/bin/env bash
# Opens the demo: points kubectl at the cluster, starts self-healing tunnels to Grafana, Jaeger
# and Prometheus, and opens screens 4 and 1 in the browser. Does not start the load (demo/load.sh).
# Overrides: REGION, CLUSTER (defaults match terraform/variables.tf), LOAD=1 to also start the load.
set -euo pipefail
cd "$(dirname "$0")/.."
REGION="${REGION:-eu-central-1}"; CLUSTER="${CLUSTER:-gpu-obs-demo}"
aws eks update-kubeconfig --name "$CLUSTER" --region "$REGION" >/dev/null

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

# The load runs 20 min; the constrained pod's KV cache fills about 90 s after it starts.
[ "${LOAD:-0}" = 1 ] && demo/load.sh
# Two tabs: screen 4 first, then screen 1 (active). Each screen's Next button goes to the next one; after the
# trace click on screen 3 you are in Explore, and Ctrl+Shift+Tab lands on screen 4.
browse() { open "$1" 2>/dev/null || xdg-open "$1" >/dev/null 2>&1 || true; }
sleep 2
browse "http://localhost:3000/d/gpu-walk-4?orgId=1&kiosk"; sleep 1
browse "http://localhost:3000/d/gpu-walk-1?orgId=1&kiosk"
echo "Grafana     http://localhost:3000   (admin / ${GRAFANA_PASSWORD:-gpu-obs-demo})"
echo "Jaeger      http://localhost:16686"
echo "Prometheus  http://localhost:9090"
echo "Demo        screens 1-4: /d/gpu-walk-1 .. /d/gpu-walk-4   (walkthrough: DEMO.md)"
echo "Next: demo/check.sh, then demo/load.sh. Stop the tunnels with demo/stop.sh"
