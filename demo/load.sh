#!/usr/bin/env bash
# (Re)start the 12-minute demo load. Drops a "load hits" marker on the dashboard.
set -euo pipefail
cd "$(dirname "$0")/.."
kubectl -n inference delete job vllm-loadgen --ignore-not-found --wait=true >/dev/null
kubectl apply -f manifests/20-vllm/loadgen-job.yaml >/dev/null
echo "load started (12 min)"
