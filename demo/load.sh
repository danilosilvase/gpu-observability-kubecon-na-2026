#!/usr/bin/env bash
# (Re)start the 20-minute demo load. Drops a "load hits" marker on the dashboard.
set -euo pipefail
cd "$(dirname "$0")/.."
kubectl -n inference delete job vllm-loadgen --ignore-not-found --wait=true >/dev/null
# The Job annotates Grafana; pass it the password (GRAFANA_PASSWORD, default gpu-obs-demo), quoted safely.
python3 -c 'import json,os,sys; print(sys.stdin.read().replace("\"admin:gpu-obs-demo\"", json.dumps("admin:" + os.environ.get("GRAFANA_PASSWORD", "gpu-obs-demo"))), end="")' \
  < manifests/20-vllm/loadgen-job.yaml | kubectl apply -f - >/dev/null
echo "load started (20 min). The constrained pod's KV cache fills in about 90 s."
