#!/usr/bin/env bash
# Open the slowest recent request on vllm-constrained in Grafana (trace view, 2 hops).
# Shortcut for screen 3 if the trace table is slow: opens the trace directly. Needs demo/start.sh tunnels.
TID=$(curl -s -m 10 "localhost:16686/api/traces?service=vllm-constrained&operation=llm_request&limit=40&lookback=10m" \
  | python3 -c 'import json,sys; t=json.load(sys.stdin)["data"]; print(max(t, key=lambda x: max(s["duration"] for s in x["spans"]))["traceID"] if t else "")')
[ -z "$TID" ] && { echo "no traces yet: is the load running? (demo/load.sh)"; exit 1; }
LEFT=$(python3 -c 'import json,sys,urllib.parse; print(urllib.parse.quote(json.dumps({"datasource":"jaeger","queries":[{"refId":"A","datasource":{"type":"jaeger","uid":"jaeger"},"queryType":"traceId","query":sys.argv[1]}],"range":{"from":"now-15m","to":"now"}})))' "$TID")
open "http://localhost:3000/explore?orgId=1&left=$LEFT" 2>/dev/null || echo "http://localhost:3000/explore?orgId=1&left=$LEFT"
echo "trace $TID"
