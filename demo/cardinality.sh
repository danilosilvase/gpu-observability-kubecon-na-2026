#!/usr/bin/env bash
# The "what broke" numbers, measured in this lab. Needs the Prometheus tunnel (demo/start.sh).
P=localhost:9090
curl -s -m 3 "$P/-/ready" >/dev/null || { echo "Prometheus not reachable on :9090. Run demo/start.sh first."; exit 1; }
now=$(curl -s "$P/api/v1/query" --data-urlencode 'query=count({__name__=~"DCGM_.*"})' \
      | python3 -c 'import json,sys; r=json.load(sys.stdin)["data"]["result"]; print(r[0]["value"][1] if r else 0)')
hour=$(curl -s -G "$P/api/v1/series" --data-urlencode 'match[]={__name__=~"DCGM_.*"}' \
      --data-urlencode "start=$(( $(date +%s) - 3600 ))" \
      | python3 -c 'import json,sys; print(len(json.load(sys.stdin)["data"]))')
pods=$(curl -s -G "$P/api/v1/label/exported_pod/values" --data-urlencode "start=$(( $(date +%s) - 3600 ))" \
      | python3 -c 'import json,sys; print(len([p for p in json.load(sys.stdin)["data"] if p]))')
echo "GPU series right now:   $now"
echo "GPU series, last hour:  $hour   ($pods pod names seen)"
echo "Same 2 GPUs. Every new pod name = a new set of series."
