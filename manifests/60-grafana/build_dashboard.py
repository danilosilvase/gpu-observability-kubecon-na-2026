import json, sys
P = {"type": "prometheus", "uid": "prometheus"}
J = {"type": "jaeger", "uid": "jaeger"}
RED, BLUE = "red", "blue"
# *_over_time drops the metric name, so count each counter separately and add them up.
COUNTERS = ["DCGM_FI_DEV_FB_USED", "DCGM_FI_DEV_FB_FREE", "DCGM_FI_PROF_SM_ACTIVE", "DCGM_FI_PROF_DRAM_ACTIVE",
            "DCGM_FI_DEV_POWER_USAGE", "DCGM_FI_DEV_GPU_TEMP", "DCGM_FI_DEV_GPU_UTIL"]
SEEN_1H = " + ".join(f"count(count_over_time({c}[1h]))" for c in COUNTERS)
# Fluent Bit log_to_metrics gauges keep their last value after a pod dies. Join on pods Running now.
LIVE = ' and on(pod_name) label_replace(kube_pod_status_phase{namespace="inference", phase="Running"} == 1, "pod_name", "$1", "pod", "(.*)")'

def colours():
    return [
        {"matcher": {"id": "byRegexp", "options": ".*constrained.*"},
         "properties": [{"id": "color", "value": {"mode": "fixed", "fixedColor": RED}}]},
        {"matcher": {"id": "byRegexp", "options": ".*overprov.*"},
         "properties": [{"id": "color", "value": {"mode": "fixed", "fixedColor": BLUE}}]},
    ]

def ts(pid, title, desc, targets, x, y, w, h, unit, mn=None, mx=None, steps=None, extra=None, tstyle="line+area"):
    d = {"unit": unit, "custom": {"lineWidth": 3, "fillOpacity": 10, "showPoints": "never",
                                  "spanNulls": True}}
    if mn is not None: d["min"] = mn
    if mx is not None: d["max"] = mx
    if steps:
        d["thresholds"] = {"mode": "absolute", "steps": steps}
        d["custom"]["thresholdsStyle"] = {"mode": tstyle}
    if extra: d.update(extra)
    d["noValue"] = "No load yet"
    return {"id": pid, "type": "timeseries", "title": title, "description": desc, "datasource": P,
            "gridPos": {"x": x, "y": y, "w": w, "h": h},
            "fieldConfig": {"defaults": d, "overrides": colours()},
            "options": {"legend": {"displayMode": "list", "placement": "bottom", "calcs": ["lastNotNull"]},
                        "tooltip": {"mode": "multi"}},
            "targets": [dict(datasource=P, refId=chr(65+i), **t) for i, t in enumerate(targets)]}

def traces(pid, title, service, x, y, w, h):
    return {"id": pid, "type": "table", "title": title, "datasource": J,
            "description": "Jaeger search for this service. Click a Trace ID: the trace opens, and each span has links to this pod's GPU memory and KV cache.",
            "gridPos": {"x": x, "y": y, "w": w, "h": h},
            "targets": [{"datasource": J, "refId": "A", "queryType": "search", "service": service,
                         "operation": "llm_request", "limit": 40}],
            "transformations": [{"id": "sortBy", "options": {"sort": [{"field": "Duration", "desc": True}]}},
                                {"id": "limit", "options": {"limitField": 6}},
                                {"id": "organize", "options": {"excludeByName": {"Trace name": True, "Start time": True}}}],
            "fieldConfig": {"defaults": {"custom": {"align": "left"}},
                            "overrides": [{"matcher": {"id": "byName", "options": "Duration"},
                                           "properties": [{"id": "custom.cellOptions", "value": {"type": "color-background", "mode": "basic"}},
                                                          {"id": "unit", "value": "µs"},
                                                          {"id": "thresholds", "value": {"mode": "absolute", "steps": [
                                                              {"color": "green", "value": None},
                                                              {"color": "orange", "value": 1000000},
                                                              {"color": "red", "value": 3000000}]}}]}]},
            "options": {"showHeader": True, "cellHeight": "sm"}}

panels = []
# Row 0: the verdict, readable from the back of the room
panels.append({
    "id": 1, "type": "stat", "title": "Verdict per pod (peak KV cache, last 5 min, parsed from the serving log)",
    "description": "KV cache is the real 'GPU full' for an LLM server. Over 90% = memory-constrained, under 30% = over-provisioned.",
    "datasource": P, "gridPos": {"x": 0, "y": 0, "w": 24, "h": 5},
    "targets": [{"datasource": P, "refId": "A", "legendFormat": "{{pod_name}}",
                 "expr": 'max by (pod_name) (max_over_time(vllm_log_kv_cache_usage_pct{pod_name=~"$pod"}[5m]))' + LIVE}],
    "fieldConfig": {"defaults": {"unit": "percent", "decimals": 0, "noValue": "No load yet",
        "mappings": [
            {"type": "range", "options": {"from": 90, "to": 1000, "result": {"text": "MEMORY-CONSTRAINED", "color": "red", "index": 0}}},
            {"type": "range", "options": {"from": 30, "to": 90, "result": {"text": "BUSY", "color": "orange", "index": 1}}},
            {"type": "range", "options": {"from": 0, "to": 30, "result": {"text": "OVER-PROVISIONED", "color": "blue", "index": 2}}}],
        "color": {"mode": "fixed", "fixedColor": "text"}}, "overrides": []},
    "options": {"colorMode": "background", "graphMode": "none", "textMode": "value_and_name",
                "justifyMode": "center", "text": {"titleSize": 30, "valueSize": 52}, "orientation": "vertical", "wideLayout": True,
                "reduceOptions": {"calcs": ["lastNotNull"], "fields": "", "values": False}}})

# Row 1: three signals, same pods, same colours
panels.append(ts(2, "1. GPU memory (DCGM): flat. The pod in trouble uses less",
    "vLLM reserves its GPU memory at start-up (--gpu-memory-utilization). This counter never moves under load, and the struggling pod looks the healthiest.",
    [{"expr": 'DCGM_FI_DEV_FB_USED{exported_pod=~"$pod"}', "legendFormat": "{{exported_pod}}"}],
    0, 5, 8, 12, "decmbytes", 0, 24576))
panels.append(ts(3, "2. KV cache % (log line, Fluent Bit + Lua): one pod hits 100%",
    "Parsed from the vLLM stats log line by a 15-line Lua filter, turned into a metric by log_to_metrics.",
    [{"expr": 'vllm_log_kv_cache_usage_pct{pod_name=~"$pod"}' + LIVE, "legendFormat": "{{pod_name}}"}],
    8, 5, 8, 12, "percent", 0, 100,
    [{"color": "transparent", "value": None}, {"color": "red", "value": 90}]))
panels.append(ts(4, "3. Queue time p95 (vLLM /metrics): requests start waiting",
    "Time a request waits before the GPU picks it up. Rises when the KV cache is full.",
    [{"expr": 'histogram_quantile(0.95, sum by (le, pod) (rate(vllm:request_queue_time_seconds_bucket{pod=~"$pod"}[1m])))',
      "legendFormat": "{{pod}}"}],
    16, 5, 8, 12, "s", 0, None,
    [{"color": "transparent", "value": None}, {"color": "orange", "value": 1}, {"color": "red", "value": 3}], tstyle="dashed"))

# Row 2: traces on the same pods
panels.append(traces(5, "4. Slowest requests on vllm-constrained (traces, click a Trace ID)", "vllm-constrained", 0, 17, 12, 9))
panels.append(traces(6, "4. Slowest requests on vllm-overprov (traces, click a Trace ID)", "vllm-overprov", 12, 17, 12, 9))

# Collapsed detail row: off-screen on stage, there for Q&A
detail = [
    {"id": 17, "type": "stat", "title": "What broke: GPU series, same 2 GPUs (live now vs seen in the last hour)",
     "description": "Every new pod name creates a new set of GPU series. Prometheus keeps old ones until retention ends.",
     "datasource": P, "gridPos": {"x": 0, "y": 27, "w": 24, "h": 6},
     "targets": [{"datasource": P, "refId": "A", "legendFormat": "live now", "instant": True,
                  "expr": 'count({__name__=~"DCGM_.*"})'},
                 {"datasource": P, "refId": "B", "legendFormat": "seen in the last hour", "instant": True,
                  "expr": SEEN_1H}],
     "fieldConfig": {"defaults": {"unit": "none", "decimals": 0, "color": {"mode": "fixed", "fixedColor": "orange"}}, "overrides": []},
     "options": {"colorMode": "value", "graphMode": "none", "textMode": "value_and_name", "justifyMode": "center",
                 "text": {"titleSize": 28, "valueSize": 80},
                 "reduceOptions": {"calcs": ["lastNotNull"], "fields": "", "values": False}}},
    ts(11, "SM active ratio (real compute occupancy) · DCGM", "",
       [{"expr": 'DCGM_FI_PROF_SM_ACTIVE{exported_pod=~"$pod"}', "legendFormat": "{{exported_pod}}"}], 0, 30, 8, 8, "percentunit", 0, 1),
    ts(12, "GPU utilisation % (coarse, misleading) · DCGM", "",
       [{"expr": 'DCGM_FI_DEV_GPU_UTIL{exported_pod=~"$pod"}', "legendFormat": "{{exported_pod}}"}], 8, 30, 8, 8, "percent", 0, 100),
    ts(13, "Generation tokens/s · from the log", "",
       [{"expr": 'vllm_log_gen_tokens_per_s{pod_name=~"$pod"}' + LIVE, "legendFormat": "{{pod_name}}"}], 16, 30, 8, 8, "none", 0),
    ts(14, "Waiting / running / preemptions · from the log", "",
       [{"expr": 'vllm_log_waiting_reqs{pod_name=~"$pod"}' + LIVE, "legendFormat": "waiting {{pod_name}}"},
        {"expr": 'vllm_log_running_reqs{pod_name=~"$pod"}' + LIVE, "legendFormat": "running {{pod_name}}"},
        {"expr": 'vllm_log_preemptions_total{pod_name=~"$pod"}' + LIVE, "legendFormat": "preempted {{pod_name}}"}], 0, 38, 8, 8, "none", 0),
    ts(15, "Cross-check: KV cache % · native vLLM /metrics", "vLLM exposes this itself; many servers do not, which is why the log path exists.",
       [{"expr": 'vllm:kv_cache_usage_perc{pod=~"$pod"} * 100', "legendFormat": "{{pod}}"}], 8, 38, 8, 8, "percent", 0, 100),
    ts(16, "Cross-check: tokens/s · native vLLM /metrics", "",
       [{"expr": 'rate(vllm:generation_tokens_total{pod=~"$pod"}[1m])', "legendFormat": "{{pod}}"}], 16, 38, 8, 8, "none", 0),
]
panels.append({"id": 10, "type": "row", "title": "Details (for Q&A)", "collapsed": True,
               "gridPos": {"x": 0, "y": 26, "w": 24, "h": 1}, "panels": detail})

dash = {
    "uid": "gpu-inference-obs", "title": "GPU inference: the pod is the join key",
    "schemaVersion": 39, "refresh": "10s", "time": {"from": "now-15m", "to": "now"},
    "tags": ["gpu", "inference", "vllm", "dcgm", "fluent-bit", "otel"],
    "graphTooltip": 1,   # shared crosshair: hover one panel, see the same second on all
    "annotations": {"list": [
        {"builtIn": 1, "datasource": {"type": "grafana", "uid": "-- Grafana --"}, "enable": True, "hide": True,
         "iconColor": "rgba(0, 211, 255, 1)", "name": "Annotations & Alerts", "type": "dashboard"},
        {"datasource": {"type": "grafana", "uid": "-- Grafana --"}, "enable": True, "iconColor": "orange",
         "name": "load hits", "target": {"type": "tags", "tags": ["load"], "matchAny": True, "limit": 20}}]},
    "templating": {"list": [{"name": "pod", "label": "pod", "type": "query", "datasource": P,
        # vLLM pods Running right now (instant query), so restarted pods drop off every panel.
        "query": {"query": 'query_result(kube_pod_status_phase{namespace="inference", phase="Running", pod=~"vllm-(constrained|overprov).*"} == 1)', "refId": "pod"},
        "regex": '/pod="([^"]+)"/',
        "includeAll": True, "multi": True, "refresh": 2, "current": {"text": "All", "value": "$__all"}}]},
    "panels": panels,
}
json.dump(dash, open(sys.argv[1], "w"), indent=2)
print("panels:", len(panels))
