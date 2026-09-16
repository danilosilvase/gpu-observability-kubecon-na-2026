#!/usr/bin/env bash
# End-to-end validation of the GPU observability stack.
set -uo pipefail
export AWS_PROFILE="${AWS_PROFILE:-default}"
REGION=eu-central-1
CLUSTER=gpu-obs-demo
PASS=0; FAIL=0
chk(){ if eval "$2"; then echo "PASS: $1"; PASS=$((PASS+1)); else echo "FAIL: $1"; FAIL=$((FAIL+1)); fi; }

aws eks update-kubeconfig --name $CLUSTER --region $REGION >/dev/null 2>&1

echo "=== 1. GPU node provisioned by Auto Mode ==="
kubectl get nodes -L workload-type,node.kubernetes.io/instance-type
chk "at least one gpu-inference node Ready" \
  "kubectl get nodes -l workload-type=gpu-inference --no-headers 2>/dev/null | grep -q ' Ready'"

echo "=== 2. vLLM pods running ==="
kubectl -n inference get pods -o wide
chk "vllm-constrained running"  "kubectl -n inference get pods -l profile=constrained     --no-headers | grep -q Running"
chk "vllm-overprov running"     "kubectl -n inference get pods -l profile=overprovisioned  --no-headers | grep -q Running"

echo "=== 3. SIGNAL A: DCGM GPU metrics with pod mapping ==="
kubectl -n observability get pods -l app=dcgm-exporter
DCGM=$(kubectl -n observability run dcgmprobe --image=curlimages/curl --restart=Never --rm -i --quiet -- curl -s http://dcgm-exporter.observability:9400/metrics 2>/dev/null)
chk "DCGM_FI_DEV_FB_USED exposed"   "echo \"$DCGM\" | grep -q DCGM_FI_DEV_FB_USED"
chk "DCGM metric carries pod label" "echo \"$DCGM\" | grep DCGM_FI_DEV_FB_USED | grep -q 'pod='"

echo "=== 4. SIGNAL B: Fluent Bit Lua extracted tokens/sec ==="
sleep 5
chk "fluent-bit parsed gen_tokens_per_s + pod_name" \
  "kubectl -n observability logs ds/fluent-bit --tail=300 2>/dev/null | grep gen_tokens_per_s | grep -q pod_name"

echo "=== 5. SIGNAL C: OTel traces reached Jaeger ==="
kubectl -n observability get pods -l app=jaeger -l app=otel-collector 2>/dev/null
chk "otel-collector running" "kubectl -n observability get pods -l app=otel-collector --no-headers | grep -q Running"
chk "jaeger running"         "kubectl -n observability get pods -l app=jaeger --no-headers | grep -q Running"
SVCS=$(kubectl -n observability run jprobe --image=curlimages/curl --restart=Never --rm -i --quiet -- curl -s http://jaeger-ui.observability:16686/api/services 2>/dev/null)
chk "jaeger has vllm trace services" "echo \"$SVCS\" | grep -q vllm-constrained"

echo "=== 6. Prometheus scraping DCGM + vLLM ==="
kubectl -n observability get servicemonitors 2>/dev/null
chk "prometheus pod up" "kubectl -n observability get pods -l app.kubernetes.io/name=prometheus --no-headers | grep -q Running"

echo "=== 7. Grafana up with dashboard ==="
chk "grafana pod up" "kubectl -n observability get pods -l app.kubernetes.io/name=grafana --no-headers | grep -q Running"
chk "dashboard configmap present" "kubectl -n observability get cm gpu-inference-dashboard >/dev/null 2>&1"

echo
echo "==================== RESULT: $PASS passed / $FAIL failed ===================="
