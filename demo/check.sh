#!/usr/bin/env bash
# Pre-flight: one line per thing the demo needs (9 checks). Needs the tunnels from demo/start.sh.
cd "$(dirname "$0")/.."
G="admin:${GRAFANA_PASSWORD:-gpu-obs-demo}"
ok=0; bad=0
c() { if eval "$2" >/dev/null 2>&1; then echo "  OK   $1"; ok=$((ok+1)); else echo "  FAIL $1"; bad=$((bad+1)); fi; }
q() { curl -s -m 5 localhost:9090/api/v1/query --data-urlencode "query=$1" | grep -q '"value"'; }

c "vLLM pods Running (2)"          "[ \$(kubectl -n inference get pods -l app=vllm --no-headers | grep -c Running) -eq 2 ]"
c "screen 1: GPU memory per pod"   "q 'DCGM_FI_DEV_FB_USED{exported_pod=~\"vllm-.*\"}'"
c "screen 2: KV cache from log"    "q 'vllm_log_kv_cache_usage_pct'"
c "screen 4: time to first token"  "q 'vllm:time_to_first_token_seconds_count'"
c "screen 3: traces client->vLLM"  "curl -s -m 5 localhost:16686/api/services | grep -q chat-client"
c "single-screen dashboard loaded" "curl -s -m 5 -u \"\$G\" localhost:3000/api/dashboards/uid/gpu-inference-obs | grep -q 'Which pod is in trouble'"
c "walkthrough screens 1-4 loaded" "(for i in 1 2 3 4; do curl -s -m 5 -u \"\$G\" localhost:3000/api/dashboards/uid/gpu-walk-\$i | grep -q gpu-walk-\$i || exit 1; done)"
c "deep-dive dashboard loaded"     "curl -s -m 5 -u \"\$G\" localhost:3000/api/dashboards/uid/gpu-inference-deep | grep -q 'deep dive'"
c "Grafana up"                     "curl -s -m 5 -o /dev/null -w '%{http_code}' localhost:3000/login | grep -q 200"
echo "$ok OK, $bad FAIL"
[ "$bad" -eq 0 ]
