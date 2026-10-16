"""Builds the two Grafana dashboards from one place.

  stage  (uid gpu-inference-obs):  what the audience sees. One question, 2 pods x 3 big numbers, one trace table.
  deep   (uid gpu-inference-deep): every panel, for Q&A.

Usage: python3 build_dashboard.py gpu-inference-dashboard.json gpu-inference-deep-dive.json
"""
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


# Is the pod getting traffic? (vLLM's own request counter, renamed to the log metric's label)
TRAFFIC = ' and on(pod_name) label_replace(sum by (pod) (rate(vllm:request_success_total{pod=~"$pod"}[3m])) > 0, "pod_name", "$1", "pod", "(.*)")'
KV_PEAK = 'max by (pod_name) (max_over_time(vllm_log_kv_cache_usage_pct{pod_name=~"$pod"}[3m]))' + LIVE

def verdict(pid, title, y, h=5):
    """Peak KV cache while the pod has traffic. No traffic = -1 = OK, so idle pods read OK, not over-provisioned."""
    return {
    "id": pid, "type": "stat", "title": title,
    "description": "KV cache is the real 'GPU full' for an LLM server. With traffic: over 90% = memory-constrained, under 40% = over-provisioned (our rule of thumb). No traffic = OK.",
    "datasource": P, "gridPos": {"x": 0, "y": y, "w": 24, "h": h}, "interval": "5s",
    "targets": [{"datasource": P, "refId": r, "legendFormat": "{{pod_name}}",
                 "expr": f'({KV_PEAK}{TRAFFIC}) or (({KV_PEAK}) * 0 - 1)'.replace('pod_name=~"$pod"', f'pod_name=~"$pod", pod_name=~"{dep}.*"')}
                for r, dep in (("A", "vllm-constrained"), ("B", "vllm-overprov"))],
    "fieldConfig": {"defaults": {"unit": "percent", "decimals": 0, "noValue": "Waiting for the first log line",
        "mappings": [
            {"type": "value", "options": {"-1": {"text": "OK", "color": "green", "index": 0}}},
            {"type": "range", "options": {"from": 90, "to": 1000, "result": {"text": "MEMORY-CONSTRAINED", "color": "red", "index": 1}}},
            {"type": "range", "options": {"from": 40, "to": 90, "result": {"text": "BUSY", "color": "orange", "index": 2}}},
            {"type": "range", "options": {"from": 0, "to": 40, "result": {"text": "OVER-PROVISIONED", "color": "blue", "index": 3}}}],
        "color": {"mode": "fixed", "fixedColor": "text"}}, "overrides": []},
    "options": {"colorMode": "background", "graphMode": "none", "textMode": "value_and_name",
                "justifyMode": "center", "text": {"titleSize": 30, "valueSize": 52}, "orientation": "vertical", "wideLayout": True,
                "reduceOptions": {"calcs": ["lastNotNull"], "fields": "", "values": False}}}

def big(pid, title, desc, expr, legend, x, y, w, h, unit, mx=None, novalue="No traffic", decimals=None, zero_text=None):
    """A big number per pod, with a sparkline so 'flat' and 'climbing' are visible."""
    d = {"unit": unit, "noValue": novalue, "min": 0, "color": {"mode": "fixed", "fixedColor": "text"}}
    if mx is not None: d["max"] = mx
    if decimals is not None: d["decimals"] = decimals
    if zero_text: d["mappings"] = [{"type": "value", "options": {"0": {"text": zero_text, "index": 0}}}]
    return {"id": pid, "type": "stat", "title": title, "description": desc, "datasource": P,
            "gridPos": {"x": x, "y": y, "w": w, "h": h},
            "interval": "5s",   # the datasource default step is 30 s: tiles would lag the room by up to 30 s
            # one query per pod (red first) so every panel lists the pods in the same order
            "targets": [{"datasource": P, "refId": r, "expr": expr.replace("~\"$pod\"", f"~\"$pod\", {lbl}=~\"{dep}.*\""), "legendFormat": legend}
                        for r, dep in (("A", "vllm-constrained"), ("B", "vllm-overprov"))
                        for lbl in [legend.strip("{}")]],
            "fieldConfig": {"defaults": d, "overrides": colours()},
            "options": {"colorMode": "value", "graphMode": "area", "textMode": "value_and_name", "justifyMode": "center",
                        "orientation": "horizontal", "wideLayout": True, "text": {"titleSize": 18, "valueSize": 64},
                        "reduceOptions": {"calcs": ["lastNotNull"], "fields": "", "values": False}}}

TTFT = ('(sum by (pod) (rate(vllm:time_to_first_token_seconds_sum{pod=~"$pod"}[2m]))'
        ' / sum by (pod) (rate(vllm:time_to_first_token_seconds_count{pod=~"$pod"}[2m])) >= 0)')

# ---------------- deep dive: every panel, for Q&A ----------------
deep_panels = []
# Row 0: the verdict, readable from the back of the room
deep_panels.append(verdict(1, "Verdict per pod (peak KV cache while it has traffic, parsed from the serving log)", 0))

# Row 1: three signals, same pods, same colours
deep_panels.append(ts(2, "1. GPU memory (DCGM): flat. The pod in trouble uses less",
    "vLLM reserves its GPU memory at start-up (--gpu-memory-utilization). This counter never moves under load, and the struggling pod looks the healthiest.",
    [{"expr": 'DCGM_FI_DEV_FB_USED{exported_pod=~"$pod"}', "legendFormat": "{{exported_pod}}"}],
    0, 5, 8, 12, "decmbytes", 0, 24576))
deep_panels.append(ts(3, "2. KV cache % (log line, Fluent Bit + Lua): one pod hits 100%",
    "Parsed from the vLLM stats log line by a 15-line Lua filter, turned into a metric by log_to_metrics.",
    [{"expr": 'vllm_log_kv_cache_usage_pct{pod_name=~"$pod"}' + LIVE, "legendFormat": "{{pod_name}}"}],
    8, 5, 8, 12, "percent", 0, 100,
    [{"color": "transparent", "value": None}, {"color": "red", "value": 90}]))
deep_panels.append(ts(4, "3. Time to first token (vLLM /metrics): requests wait for room",
    "Average time until the first token. Rises when the KV cache is full and requests queue.",
    [{"expr": TTFT, "legendFormat": "{{pod}}"}],
    16, 5, 8, 12, "s", 0, None,
    [{"color": "transparent", "value": None}, {"color": "orange", "value": 1}, {"color": "red", "value": 3}], tstyle="dashed"))

# Row 2: traces on the same pods
deep_panels.append(traces(5, "4. Slowest requests on vllm-constrained (traces, click a Trace ID)", "vllm-constrained", 0, 17, 12, 9))
deep_panels.append(traces(6, "4. Slowest requests on vllm-overprov (traces, click a Trace ID)", "vllm-overprov", 12, 17, 12, 9))

# Detail row: GPU counters, cardinality, log fields and native cross-checks
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
deep_panels.append({"id": 10, "type": "row", "title": "Details", "collapsed": False,
               "gridPos": {"x": 0, "y": 26, "w": 24, "h": 1}, "panels": []})
deep_panels += detail


# ---------------- stage: one question, one screen ----------------
stage_panels = [
    verdict(1, "Same model, same GPU. Which pod is in trouble?", 0),
    big(2, "GPU memory in use  ·  GPU exporter (DCGM)  ·  the number we page on",
        "vLLM reserves its GPU memory at start-up, so this never moves under load. The pod in trouble even uses less.",
        'DCGM_FI_DEV_FB_USED{exported_pod=~"$pod"}', "{{exported_pod}}", 0, 5, 8, 12, "decmbytes", decimals=1, novalue="No GPU data"),
    big(3, "How full the server really is  ·  KV cache %  ·  from its own log line",
        "The model server's working memory. Read from the vLLM log line by Fluent Bit + a 15-line Lua filter. 100% = full, new requests wait.",
        'vllm_log_kv_cache_usage_pct{pod_name=~"$pod"}' + LIVE, "{{pod_name}}", 8, 5, 8, 12, "percent", mx=100, decimals=0),
    big(4, "How long until the answer starts  ·  time to first token  ·  what the user feels",
        "Time to first token measured by vLLM itself (/metrics): sum / count over the last 2 min. It includes the time a request waits for room in the KV cache.",
        # >= 0 drops the NaN (0/0) an idle pod returns, so the tile says "No traffic"
        TTFT + ' or (sum by (pod) (rate(vllm:time_to_first_token_seconds_count{pod=~"$pod"}[2m])) * 0)', "{{pod}}",
        16, 5, 8, 12, "s", decimals=2, zero_text="No traffic"),
    traces(5, "The slowest requests on the red pod (traces)  ·  click one", "vllm-constrained", 0, 17, 24, 9),
]

def dashboard(uid, title, panels, link_uid, link_title):
    return {
        "uid": uid, "title": title,
        "links": [{"type": "link", "title": link_title, "url": f"/d/{link_uid}", "icon": "dashboard"}],
        "schemaVersion": 39, "refresh": "5s" if uid == "gpu-inference-obs" else "10s",
        "time": {"from": "now-5m" if uid == "gpu-inference-obs" else "now-15m", "to": "now"},
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

if __name__ == "__main__":
    json.dump(dashboard("gpu-inference-obs", "GPU inference: which pod is in trouble?", stage_panels,
                        "gpu-inference-deep", "Deep dive (all panels)"), open(sys.argv[1], "w"), indent=2)
    json.dump(dashboard("gpu-inference-deep", "GPU inference: deep dive (Q&A)", deep_panels,
                        "gpu-inference-obs", "Stage dashboard"), open(sys.argv[2], "w"), indent=2)
    print("stage panels:", len(stage_panels), " deep panels:", len(deep_panels))
