"""Builds the 4-screen demo walkthrough (one dashboard per screen, one browser tab each).

Every screen has the same layout so the room learns it once:
  progress strip + the question | config (<= 6 lines, 1 highlighted) | one chart, red vs blue | one sentence.
Same dashboards for the live demo and the recording (demo/record/record.mjs walks them in order).

Usage: python3 build_walkthrough.py walk/      -> walk/gpu-walk-{1..4}.json
"""
import json, os, sys
from build_dashboard import P, ts, traces, verdict, big, dashboard, LIVE, TTFT

RED_C, BLUE_C, HI = "#f2495c", "#5794f2", "#ffd666"
STEPS = ["1 GPU", "2 Log", "3 Trace", "4 Answer"]
red = lambda t: f'<span style="color:{RED_C};font-weight:700">{t}</span>'
blue = lambda t: f'<span style="color:{BLUE_C};font-weight:700">{t}</span>'

def text(pid, html, x, y, w, h):
    return {"id": pid, "type": "text", "title": "", "transparent": True,
            "gridPos": {"x": x, "y": y, "w": w, "h": h},
            "options": {"mode": "html", "content": html}}

def header(n, question):
    pills = []
    for i, s in enumerate(STEPS, 1):
        style = ("color:#ffffff;font-weight:700;border-bottom:4px solid #ff9830;padding-bottom:2px" if i == n
                 else "color:#6e6e6e" if i > n else "color:#a0a0a0")
        pills.append(f'<span style="{style}">{s}</span>')
    sep = '<span style="color:#555"> &rsaquo; </span>'
    nxt = (f'<a href="/d/gpu-walk-{n + 1}?orgId=1&kiosk" style="font-size:18px;line-height:1.2;color:#ff9830;font-weight:700;'
           f'text-decoration:none;border:2px solid #ff9830;border-radius:6px;padding:0 12px">Next: {STEPS[n]} &rsaquo;</a>'
           if n < len(STEPS) else '')
    return (f'<div style="display:flex;justify-content:space-between;align-items:center;font-size:20px;line-height:1.2;letter-spacing:0.5px">'
            f'<span>{sep.join(pills)}</span>{nxt}</div>'
            f'<div style="font-size:40px;line-height:1.2;font-weight:700;color:#ffffff;margin-top:0;padding-bottom:6px">{question}</div>')

def config(path, lines, note):
    """lines: list of (text, highlighted?)."""
    body = "".join(
        (f'<span style="display:block;background:#4d3d00;color:{HI};font-weight:700;margin:0 -16px;padding:0 16px">{t}</span>'
         if hi else f'<span style="display:block">{t}</span>') for t, hi in lines)
    return (f'<div style="font-size:16px;color:#9a9a9a;margin-bottom:6px">{path}</div>'
            f'<pre style="font-size:23px;line-height:1.5;background:#111217;border:1px solid #2c3235;'
            f'padding:14px 16px;border-radius:8px;white-space:pre-wrap;margin:0">{body}</pre>'
            f'<div style="font-size:21px;color:#d8d9da;margin-top:14px;line-height:1.4">{note}</div>')

def sentence(html):
    return f'<div style="font-size:34px;font-weight:600;color:#ffffff;text-align:center;padding-top:6px">{html}</div>'

def walk(n, uid, title, question, cfg, panels, line):
    ps = [text(100, header(n, question), 0, 0, 24, 3), text(101, cfg, 0, 3, 9, 20)] + panels + \
         [text(102, sentence(line), 0, 23, 24, 4)]
    d = dashboard(uid, title, ps, f"gpu-walk-{n % 4 + 1}", f"Next: {STEPS[n % 4]}")
    d["refresh"] = "5s"
    d["time"] = {"from": "now-10m", "to": "now"}   # idle, then the load (started ~4-6 min before the demo)
    return d

# ---- 1 GPU: what the GPU exporter sees ----
s1 = walk(1, "gpu-walk-1", "1 · What does the GPU say?", "What does the GPU say?",
    config("manifests/10-gpu-metrics/dcgm-exporter.yaml", [
        ("args:", False),
        ("  - --kubernetes=true", True),
        ("  - --kubernetes-gpu-id-type=uid", False),
        ("env:", False),
        ("  ENABLE_POD_LABELS: \"false\"", False)],
        "dcgm-exporter asks the kubelet which pod owns each GPU, so every GPU metric carries the <b>pod name</b>."),
    [ts(10, "GPU memory in use, per pod  ·  DCGM_FI_DEV_FB_USED", "",
        [{"expr": 'DCGM_FI_DEV_FB_USED{exported_pod=~"$pod"}', "legendFormat": "{{exported_pod}}"}],
        9, 3, 15, 14, "decmbytes", 0, 24576),
     big(11, "Requests in flight per pod  ·  running + waiting  ·  vLLM", "Same traffic to both pods: 192 long requests each, all the time.",
         'sum by (pod) (vllm:num_requests_running{pod=~"$pod"} + vllm:num_requests_waiting{pod=~"$pod"})', "{{pod}}",
         9, 17, 15, 6, "none", decimals=0, zero_text="No traffic")],
    f'The chart we page on: {red("red 2 GB")}, {blue("blue 20.6 GB")}. Flat under load. It cannot tell you which one is in trouble.')

# ---- 2 Log: what the server says ----
s2 = walk(2, "gpu-walk-2", "2 · What does the server say?", "What does the server say?",
    config("manifests/30-logs/fluent-bit.yaml  ·  example line vLLM logs every 10 s:", [
        ("Avg generation throughput: 9528 tokens/s,", False),
        ("Running: 49 reqs, Waiting: 143 reqs,", False),
        ("GPU KV cache usage: 100.0%", True),
        ("", False),
        ("kv = string.match(line, \"KV cache usage:%s*([%d%.]+)%%\")", True)],
        "Fluent Bit already ships this log. 15 lines of Lua turn it into a metric with the <b>pod name</b>."),
    [ts(20, "KV cache in use, per pod  ·  from the vLLM log line", "",
        [{"expr": 'vllm_log_kv_cache_usage_pct{pod_name=~"$pod"}' + LIVE, "legendFormat": "{{pod_name}}"}],
        9, 3, 15, 13, "percent", 0, 100, [{"color": "transparent", "value": None}, {"color": "red", "value": 90}]),
     big(21, "Tokens/s  ·  same log line", "", 'vllm_log_gen_tokens_per_s{pod_name=~"$pod"}' + LIVE,
         "{{pod_name}}", 9, 16, 8, 7, "none", decimals=0),
     big(22, "Cross-check: KV cache peak from vLLM /metrics", "Same number, read from vLLM's own /metrics endpoint instead of the log.",
         'max by (pod) (max_over_time(vllm:kv_cache_usage_perc{pod=~"$pod"}[1m])) * 100', "{{pod}}",
         17, 16, 7, 7, "percent", mx=100, decimals=0)],
    f'{red("Red is full")}: new requests wait for room. {blue("Blue")} uses about a third of its own.')

# ---- 3 Trace: why was this request slow? ----
def avg(m, dep):
    return (f'sum(rate(vllm:{m}_sum{{pod=~"$pod", pod=~"{dep}.*"}}[2m])) / '
            f'sum(rate(vllm:{m}_count{{pod=~"$pod", pod=~"{dep}.*"}}[2m]))')
split = {"id": 30, "type": "bargauge", "title": "Where each request's time goes  ·  average, last 2 min  ·  vLLM",
    "datasource": P, "gridPos": {"x": 9, "y": 3, "w": 15, "h": 11}, "interval": "5s",
    "targets": [{"datasource": P, "refId": r, "legendFormat": lf, "expr": avg(m, dep)} for r, lf, m, dep in (
        ("A", "red waiting", "request_queue_time_seconds", "vllm-constrained"),
        ("B", "red on GPU", "request_inference_time_seconds", "vllm-constrained"),
        ("C", "blue waiting", "request_queue_time_seconds", "vllm-overprov"),
        ("D", "blue on GPU", "request_inference_time_seconds", "vllm-overprov"))],
    "fieldConfig": {"defaults": {"unit": "s", "decimals": 1, "min": 0, "max": 8, "noValue": "No traffic",
                                 "color": {"mode": "fixed", "fixedColor": "green"}},
        "overrides": [{"matcher": {"id": "byRegexp", "options": ".*waiting.*"},
                       "properties": [{"id": "color", "value": {"mode": "fixed", "fixedColor": "orange"}}]}]},
    "options": {"displayMode": "basic", "orientation": "horizontal", "showUnfilled": True, "valueMode": "text",
                "namePlacement": "top", "sizing": "manual", "minVizHeight": 56, "maxVizHeight": 64,
                "text": {"titleSize": 18, "valueSize": 26},
                "reduceOptions": {"calcs": ["lastNotNull"], "fields": "", "values": False}}}
s3 = walk(3, "gpu-walk-3", "3 · Why was this request slow?", "Why was this request slow?",
    config("manifests/40-traces/otel-collector.yaml", [
        ("processors:", False),
        ("  k8sattributes:", False),
        ("    extract:", False),
        ("      metadata: [k8s.pod.name]", True),
        ("    pod_association:", False),
        ("      - sources: [{from: connection}]", False)],
        "vLLM sends a span per request. The Collector adds the <b>pod name</b>. Grafana uses it to jump from a trace to that pod's metrics."),
    [split, traces(31, "Slowest requests on red  ·  click one", "vllm-constrained", 9, 14, 8, 9),
     traces(32, "Slowest requests on blue", "vllm-overprov", 17, 14, 7, 9)],
    f'{red("Red")}: most of each request is spent <b>waiting in line</b>, not on the GPU. One click shows why.')

# ---- 4 Answer: which one was set wrong? ----
KV_PEAK3 = 'max by (pod_name) (max_over_time(vllm_log_kv_cache_usage_pct{pod_name=~"$pod"}[3m]))' + LIVE
s4 = walk(4, "gpu-walk-4", "4 · Which one was set wrong?", "Is 8% too low? Is 90% too high?",
    config("rule of thumb (ours, not vLLM's)", [
        ("peak KV cache under real traffic", False),
        ("  > 90%  memory-constrained", True),
        ("  < 40%  over-provisioned", True)],
        "Watch the server's own signal, per pod. The GPU memory chart cannot answer this."),
    [dict(verdict(40, "Verdict per pod  ·  peak KV cache while it has traffic", 3, 6), gridPos={"x": 9, "y": 3, "w": 15, "h": 7}),
     big(41, "GPU memory  ·  DCGM", "", 'DCGM_FI_DEV_FB_USED{exported_pod=~"$pod"}', "{{exported_pod}}",
         9, 10, 5, 13, "decmbytes", decimals=1, novalue="No GPU data"),
     big(42, "KV cache peak  ·  log", "", KV_PEAK3, "{{pod_name}}", 14, 10, 5, 13, "percent", mx=100, decimals=0),
     big(43, "Time to first token", "", TTFT + ' or (sum by (pod) (rate(vllm:time_to_first_token_seconds_count{pod=~"$pod"}[2m])) * 0)',
         "{{pod}}", 19, 10, 5, 13, "s", decimals=2, zero_text="No traffic")],
    f'{red("8% is too low")}. {blue("90% is too high")}. Only the server\'s own signal could tell.')

if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "walk"
    os.makedirs(out, exist_ok=True)
    for i, d in enumerate((s1, s2, s3, s4), 1):
        json.dump(d, open(os.path.join(out, f"gpu-walk-{i}.json"), "w"), indent=2)
    print("walkthrough screens:", 4, "->", out)
