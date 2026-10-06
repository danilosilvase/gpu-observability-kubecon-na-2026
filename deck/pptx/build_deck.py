#!/usr/bin/env python3
"""Build the KubeCon NA 2026 Observability Day deck (v3 storyline) on the branded template.

Usage:  uv run --with python-pptx python build_deck.py <template.pptx> <out.pptx> [screenshots_dir]
Template = the CNCF "Observability Day North America 2026 - Branded PowerPoint" with the cover + title
slides already filled in (local copy ~/.aki/tmp/kubecon-session.pptx). Slide 3 of the template
("About this session") is dropped. Content lives in SLIDES below; layout code is generic.
"""
import sys, os, copy
from pptx import Presentation
from pptx.util import Emu, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.oxml.ns import qn
from lxml import etree

TEMPLATE, OUT = sys.argv[1], sys.argv[2]
SHOTS = sys.argv[3] if len(sys.argv) > 3 else None

BRAND = RGBColor(153, 19, 70)
DARK = RGBColor(0x26, 0x26, 0x26)
GREY = RGBColor(0x6B, 0x6B, 0x6B)
LIGHT = RGBColor(0xF3, 0xF3, 0xF3)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
GREEN = RGBColor(0x2E, 0x7D, 0x32)
RED = RGBColor(0xC6, 0x28, 0x28)
FONT = "Arial"
MONO = "Courier New"

W, H = 12192000, 6858000
LM = 403682                      # left margin used by the template title box
CW = 11384636                    # content width (W - 2*LM)
BODY_TOP = 1250000
BODY_BOTTOM = 6300000
FOOT_Y = 6380000

prs = Presentation(TEMPLATE)
L_COVER, L_TITLE, L_CONTENT, L_PLAIN = (prs.slide_layouts[i] for i in (0, 1, 2, 3))

# drop template slide 3 ("About this session")
sld_ids = prs.slides._sldIdLst
ids = list(sld_ids)
if len(ids) >= 3:
    rid = ids[2].get(qn("r:id"))
    sld_ids.remove(ids[2])
    prs.part.drop_rel(rid)


def _run(par, text, size, bold=False, color=DARK, font=FONT, italic=False):
    r = par.add_run()
    r.text = text
    f = r.font
    f.name, f.size, f.bold, f.italic = font, Pt(size), bold, italic
    f.color.rgb = color
    return r


def _bullet(par, char="•", indent_emu=285750):
    pPr = par._p.get_or_add_pPr()
    pPr.set("marL", str(indent_emu))
    pPr.set("indent", str(-indent_emu))
    for tag in ("a:buNone", "a:buChar", "a:buAutoNum"):
        for el in pPr.findall(qn(tag)):
            pPr.remove(el)
    bu = etree.SubElement(pPr, qn("a:buChar"))
    bu.set("char", char)


def text_box(slide, x, y, w, h, lines, size=18, color=DARK, bold=False, font=FONT,
             align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, bullets=False, space_after=6, fill=None,
             line_spacing=None):
    """lines: list of str | (str, dict) where dict can override size/bold/color/font/bullet/italic."""
    tb = slide.shapes.add_textbox(Emu(x), Emu(y), Emu(w), Emu(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = Emu(91440)
    tf.margin_top = tf.margin_bottom = Emu(45720)
    if fill is not None:
        tb.fill.solid()
        tb.fill.fore_color.rgb = fill
    first = True
    for item in lines:
        text, o = (item, {}) if isinstance(item, str) else item
        par = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        par.alignment = o.get("align", align)
        par.space_after = Pt(o.get("space_after", space_after))
        if line_spacing:
            par.line_spacing = line_spacing
        if o.get("bullet", bullets) and text:
            _bullet(par)
        _run(par, text, o.get("size", size), o.get("bold", bold), o.get("color", color),
             o.get("font", font), o.get("italic", False))
    return tb


def title(slide, text):
    # same geometry as the template's own title box
    # stays left of the Observability Day logo (x >= 9.4M EMU) and inside the 973013-high bar
    text_box(slide, LM, 0, 8900000, 973013, [text], size=30, bold=True, color=WHITE,
             anchor=MSO_ANCHOR.MIDDLE, space_after=0)


def source(slide, text):
    text_box(slide, LM, FOOT_Y, CW, 380000, [text], size=10, color=GREY)


def notes(slide, text):
    slide.notes_slide.notes_text_frame.text = text


def content_slide(t, note=None, src=None):
    s = prs.slides.add_slide(L_CONTENT)
    title(s, t)
    if src:
        source(s, src)
    if note:
        notes(s, note)
    return s


def statement_slide(big, small=None, note=None, layout=None):
    s = prs.slides.add_slide(layout or L_TITLE)
    lines = [(big, {"size": 54, "bold": True, "color": WHITE})]
    if small:
        lines.append((small, {"size": 22, "color": WHITE, "space_after": 0}))
    text_box(s, LM, 1700000, CW, 3400000, lines, anchor=MSO_ANCHOR.MIDDLE, space_after=18)
    if note:
        notes(s, note)
    return s


def code_box(slide, x, y, w, h, code, size=13):
    lines = [(ln, {"font": MONO, "size": size, "space_after": 0}) for ln in code.rstrip("\n").split("\n")]
    return text_box(slide, x, y, w, h, lines, fill=LIGHT, color=DARK)


def table(slide, x, y, w, h, rows, col_widths=None, header=True, size=14):
    nrows, ncols = len(rows), len(rows[0])
    gt = slide.shapes.add_table(nrows, ncols, Emu(x), Emu(y), Emu(w), Emu(h)).table
    if col_widths:
        for i, cw in enumerate(col_widths):
            gt.columns[i].width = Emu(cw)
    for r, row in enumerate(rows):
        for c, val in enumerate(row):
            cell = gt.cell(r, c)
            text, o = (val, {}) if isinstance(val, str) else val
            cell.text = ""
            par = cell.text_frame.paragraphs[0]
            is_head = header and r == 0
            _run(par, text, o.get("size", size), o.get("bold", is_head),
                 o.get("color", WHITE if is_head else DARK), o.get("font", FONT))
            cell.fill.solid()
            cell.fill.fore_color.rgb = BRAND if is_head else (LIGHT if r % 2 == 0 else WHITE)
            cell.margin_left = cell.margin_right = Emu(91440)
            cell.margin_top = cell.margin_bottom = Emu(45720)
    return gt


def picture_or_placeholder(slide, x, y, w, h, filename, caption):
    path = os.path.join(SHOTS, filename) if SHOTS else None
    if path and os.path.exists(path):
        from PIL import Image
        iw, ih = Image.open(path).size
        scale = min(w / iw, h / ih)
        pw, ph = int(iw * scale), int(ih * scale)
        slide.shapes.add_picture(path, Emu(x + (w - pw) // 2), Emu(y + (h - ph) // 2), width=Emu(pw), height=Emu(ph))
    else:
        text_box(slide, x, y, w, h, [(f"[screenshot: {filename}]", {"size": 14, "color": GREY}),
                                     (caption, {"size": 12, "color": GREY})],
                 fill=LIGHT, anchor=MSO_ANCHOR.MIDDLE, align=PP_ALIGN.CENTER)


COL = (CW - 300000) // 2
RIGHT_X = LM + COL + 300000

# ----------------------------------------------------------------------------------------------
# Slide 3: the incident + hook
s = content_slide(
    "The page fires. Every GPU chart is green.",
    src="Industry average production GPU utilisation ~5%: Cast AI, State of GPU utilisation 2026 (cast.ai/blog/fractional-gpu-kubernetes)",
    note=("2 min. Open with the incident, not the architecture. p99 doubled at 02:14. You open three tabs: "
          "GPU util 95%, framebuffer 90% used, both flat for an hour. The model is healthy, the pods are "
          "Ready, nothing is throttled. Then the hook: across the industry the average production GPU runs at "
          "around 5% utilisation. Those two numbers come from the same counter. One says 'saturated', the other "
          "says 'idle', and neither tells you anything about the inference work. That is the black box."))
text_box(s, LM, BODY_TOP, COL, 4800000, [
    ("02:14  p99 latency doubles", {"size": 26, "bold": True, "color": BRAND}),
    ("GPU utilisation: 95%, flat for an hour", {"size": 20, "bullet": True}),
    ("GPU memory used: 90%, flat since the pod started", {"size": 20, "bullet": True}),
    ("Pods Ready, no throttling, no OOM, no restarts", {"size": 20, "bullet": True}),
    ("Nobody knows why.", {"size": 24, "bold": True, "space_after": 0}),
], space_after=12)
text_box(s, RIGHT_X, BODY_TOP, COL, 4800000, [
    ("Meanwhile, industry-wide", {"size": 18, "color": GREY}),
    ("~5%", {"size": 96, "bold": True, "color": BRAND, "space_after": 0}),
    ("average production GPU utilisation", {"size": 18, "color": GREY}),
    ("Same counter. One fleet looks saturated, the other looks idle. "
     "Neither number says anything about the inference work.", {"size": 18, "space_after": 0}),
], anchor=MSO_ANCHOR.MIDDLE, align=PP_ALIGN.CENTER)

# ----------------------------------------------------------------------------------------------
# Slide 4a: pre-allocation
s = content_slide(
    "vLLM grabs the memory before request one.",
    src="Live rig: two vLLM pods, facebook/opt-125m, EKS Auto Mode, g5.xlarge (A10G 24 GB), DCGM_FI_DEV_FB_USED",
    note=("Section 2 starts here, 5 min total for 4a-4c. Every serious LLM server pre-allocates its KV cache "
          "pool at start-up. vLLM calls it --gpu-memory-utilization. So the framebuffer counter jumps to the "
          "configured fraction in the first 30 seconds and never moves again, whether the server is idle or "
          "melting. Our constrained pod shows 3.6 GB, the over-provisioned one 20.5 GB, both perfectly flat. "
          "The one with less memory is the one that will get into trouble, and this counter cannot tell you that."))
text_box(s, LM, BODY_TOP, COL, 4800000, [
    ("The counter everyone watches", {"size": 18, "color": GREY}),
    ("DCGM_FI_DEV_FB_USED", {"size": 26, "bold": True, "font": MONO, "color": BRAND}),
    ("Pre-allocated KV cache pool, sized by --gpu-memory-utilization", {"size": 18, "bullet": True}),
    ("Jumps to the configured fraction at start-up", {"size": 18, "bullet": True}),
    ("Then flat. Idle or saturated, same number.", {"size": 18, "bullet": True}),
    ("It measures a config value, not a workload.", {"size": 22, "bold": True, "space_after": 0}),
], space_after=10)
table(s, RIGHT_X, BODY_TOP + 200000, COL, 1900000, [
    ["pod", "gpu-mem-util", "FB_USED", "moves under load?"],
    ["vllm-constrained", "0.15", "3.6 GB", "no"],
    ["vllm-overprov", "0.90", "20.5 GB", "no"],
], col_widths=[1900000, 1300000, 1200000, COL - 4400000], size=14)
text_box(s, RIGHT_X, BODY_TOP + 2400000, COL, 1600000, [
    ("Which one is about to fall over?", {"size": 20, "bold": True}),
    ("The smaller one. The memory counter says the opposite.", {"size": 18, "color": GREY, "space_after": 0}),
])

# ----------------------------------------------------------------------------------------------
# Slide 4b: prefill vs decode, GPU util lies, Elastic numbers, MFU/MBU
s = content_slide(
    "GPU util % cannot tell prefill from decode.",
    src="Measured on vLLM by Elastic Observability Labs (2025): GR_ENGINE_ACTIVE 99.8%, PIPE_TENSOR_ACTIVE 16.6%, DRAM_ACTIVE 80.4%. "
        "MFU/MBU framing: Lightbits, The Utilization Illusion.",
    note=("GPU_UTIL means 'at least one kernel was running during the sample window'. A single thread spinning "
          "counts as 100%. Inference has two phases with opposite profiles: prefill is compute-bound (big "
          "matmuls over the prompt), decode is memory-bandwidth-bound (one token per step, re-reading the whole "
          "KV cache). Elastic measured a vLLM server at 99.8% engine-active while the tensor cores were busy "
          "16.6% of the time and the memory bus 80.4%. Bandwidth-bound, not compute-saturated. The training "
          "world has moved to MFU and MBU, model FLOPs and bandwidth utilisation; 99% util with 15 to 40% MFU is "
          "normal. vLLM 0.30 can even emit MFU itself (--enable-mfu-metrics). The counter on your dashboard is "
          "the least informative one the hardware offers."))
text_box(s, LM, BODY_TOP, COL, 2300000, [
    ("Prefill", {"size": 24, "bold": True, "color": BRAND}),
    ("Whole prompt in one pass. Large matmuls. Compute-bound.", {"size": 18}),
    ("Decode", {"size": 24, "bold": True, "color": BRAND}),
    ("One token per step, re-reads the entire KV cache. Memory-bandwidth-bound.", {"size": 18, "space_after": 0}),
], space_after=4)
text_box(s, LM, BODY_TOP + 2500000, COL, 2300000, [
    ("DCGM_FI_DEV_GPU_UTIL = \"a kernel was running in the sample window\"", {"size": 16, "font": MONO}),
    ("One busy thread = 100%. It cannot see which phase you are in, or how much of the silicon is working.",
     {"size": 18, "space_after": 0}),
])
table(s, RIGHT_X, BODY_TOP + 100000, COL, 2000000, [
    ["vLLM under load, same second", "value"],
    ["GR_ENGINE_ACTIVE (\"utilisation\")", "99.8%"],
    ["PIPE_TENSOR_ACTIVE (tensor cores)", "16.6%"],
    ["DRAM_ACTIVE (memory bus)", "80.4%"],
], col_widths=[COL - 1500000, 1500000], size=16)
text_box(s, RIGHT_X, BODY_TOP + 2400000, COL, 2200000, [
    ("Bandwidth-bound, not compute-saturated. \"Utilisation\" said neither.", {"size": 18, "bold": True}),
    ("The field now talks MFU / MBU: 99% util with 15 to 40% model-FLOPs utilisation is normal for serving.",
     {"size": 16, "color": GREY, "space_after": 0}),
])

# ----------------------------------------------------------------------------------------------
# Slide 4c: counter table
s = content_slide(
    "Counters that mislead, counters that matter.",
    src="DCGM field IDs: docs.nvidia.com/datacenter/dcgm. Profiling (PROF_*) fields need a profiling-capable GPU and DCGM >= 2.x.",
    note=("One slide of vocabulary the room can take home. Left column: what most GPU dashboards show. Right "
          "column: what actually describes the work. SM_ACTIVE and SM_OCCUPANCY say how much of the compute is "
          "busy, DRAM_ACTIVE says whether you are bandwidth-bound, PIPE_TENSOR_ACTIVE whether the tensor cores "
          "are doing the matmuls, POWER vs TDP is the cheapest sanity check. And the punchline at the bottom: "
          "none of these counters know what a token is. The GPU cannot tell you about queue depth or KV cache "
          "pressure, because those are concepts of the serving framework, not the silicon."))
table(s, LM, BODY_TOP, CW, 3300000, [
    ["Misleading on an inference server", "Why", "Meaningful", "What it tells you"],
    ["DCGM_FI_DEV_GPU_UTIL", "any kernel = busy", "DCGM_FI_PROF_SM_ACTIVE", "share of SMs doing work"],
    ["DCGM_FI_DEV_FB_USED", "pre-allocated, flat", "DCGM_FI_PROF_SM_OCCUPANCY", "warps resident per SM"],
    ["DCGM_FI_DEV_MEM_COPY_UTIL", "copy engine only", "DCGM_FI_PROF_DRAM_ACTIVE", "memory-bandwidth-bound?"],
    ["nvidia-smi \"Volatile GPU-Util\"", "same as GPU_UTIL", "DCGM_FI_PROF_PIPE_TENSOR_ACTIVE", "tensor cores actually used"],
    ["", "", "DCGM_FI_DEV_POWER_USAGE vs TDP", "cheapest idle detector"],
], col_widths=[3000000, 2100000, 3500000, CW - 8600000], size=13)
text_box(s, LM, BODY_TOP + 3500000, CW, 1200000, [
    ("And none of them know what a token is.", {"size": 28, "bold": True, "color": BRAND}),
    ("Queue depth, KV cache pressure, tokens per second: those belong to the serving framework, not the silicon.",
     {"size": 18, "space_after": 0}),
])

# ----------------------------------------------------------------------------------------------
# Slide 5: statement, join key
s = statement_slide(
    "The pod is the join key.",
    "Hardware counters, serving logs and traces each know the pod name. Nothing else is common to all three.",
    note=("Section 3, 3 min for slides 5 to 6b. If you take one architectural idea home, take this one. DCGM "
          "knows which pod holds the GPU (via the kubelet pod-resources socket). Fluent Bit knows which pod wrote "
          "the log line. The OTel Collector stamps k8s.pod.name on every span. Nothing else is shared across the "
          "three. So you keep the pod name on every signal and you join at query time. Footnote for the people on "
          "newer clusters: Kubernetes 1.35 made Dynamic Resource Allocation stable, and dcgm-exporter 4.8.4 added a "
          "pod_uid label and ResourceSlice tracking because the old device-plugin mapping breaks under DRA. The idea "
          "survives, the plumbing changes."))
text_box(s, LM, 5600000, CW, 700000, [
    ("K8s 1.35: Dynamic Resource Allocation is stable; dcgm-exporter 4.8.4 adds pod_uid + ResourceSlice mapping. "
     "Same join key, new plumbing.", {"size": 13, "color": WHITE, "space_after": 0})])

# ----------------------------------------------------------------------------------------------
# Slide 6a: DCGM per pod
s = content_slide(
    "Signal 1: DCGM, per pod.",
    src="dcgm-exporter --kubernetes reads /var/lib/kubelet/pod-resources. EKS Auto Mode: standalone dcgm-exporter, not the GPU Operator (see slide 15).",
    note=("dcgm-exporter in Kubernetes mode asks the kubelet which pod owns each GPU and stamps exported_pod on "
          "every counter. That gives you two things: which pod is on which GPU, and whether that silicon is busy. "
          "It does not give you why. On EKS Auto Mode you run the exporter standalone as a DaemonSet with the "
          "pod-resources hostPath, because the GPU Operator is not supported there. Seven counters in our "
          "counters.csv, and that smallness is deliberate, next slide explains why."))
code_box(s, LM, BODY_TOP, COL, 2300000,
         "args:\n"
         "  - -f /etc/dcgm-exporter/counters.csv\n"
         "  - --kubernetes=true\n"
         "  - --kubernetes-gpu-id-type=uid\n"
         "env:\n"
         "  DCGM_EXPORTER_KUBERNETES_ENABLE_POD_LABELS: \"false\"\n"
         "volumeMounts:\n"
         "  - /var/lib/kubelet/pod-resources  (ro)", size=10)
code_box(s, LM, BODY_TOP + 2450000, COL, 1500000,
         "DCGM_FI_DEV_FB_USED{exported_pod=\"vllm-constrained-7f9f...\",\n"
         "                    exported_namespace=\"inference\",\n"
         "                    gpu=\"0\", modelName=\"NVIDIA A10G\"} 3606", size=10)
text_box(s, RIGHT_X, BODY_TOP, COL, 4800000, [
    ("What it tells you", {"size": 20, "bold": True, "color": BRAND}),
    ("Which pod holds which GPU", {"size": 18, "bullet": True}),
    ("Whether the silicon is busy (SM_ACTIVE, DRAM_ACTIVE)", {"size": 18, "bullet": True}),
    ("Power, temperature, memory pool size", {"size": 18, "bullet": True}),
    ("What it cannot tell you", {"size": 20, "bold": True, "color": BRAND}),
    ("Why the GPU is busy", {"size": 18, "bullet": True}),
    ("How many requests are queued", {"size": 18, "bullet": True}),
    ("Whether the KV cache is full", {"size": 18, "bullet": True}),
    ("Anything about tokens", {"size": 18, "bullet": True, "space_after": 0}),
], space_after=8)

# ----------------------------------------------------------------------------------------------
# Slide 6b: cardinality
s = content_slide(
    "Keep the join key. Drop every other label.",
    src="Series math: Last9, 10,000 GPUs, one TSDB (last9.io/blog/10-000-gpus-one-tsdb-cardinality-at-gpu-scale). Rig: 7 counters, pod labels off.",
    note=("The first thing we broke was Prometheus. dcgm-exporter can copy every pod label onto every counter "
          "(ENABLE_POD_LABELS). Do the arithmetic at fleet scale: 1,000 nodes, 8 GPUs each, the default 60 or "
          "so counters, three label dimensions, and you are at 1.4 million series before a single pod or job "
          "label is added. One ECC-per-block metric on MI300X alone adds 320 thousand. Pod names churn on every "
          "rollout, so every label you add multiplies by churn. The rule that fixed it: identity on logs, stable "
          "dimensions on metrics, join at query time. We ship seven counters and one identity label."))
text_box(s, LM, BODY_TOP, COL, 2200000, [
    ("1,000 nodes x 8 GPUs x 60 counters x 3 labels", {"size": 18, "font": MONO}),
    ("= 1.4M series", {"size": 44, "bold": True, "color": BRAND, "space_after": 0}),
    ("before a single pod or job label. One ECC-per-block metric alone: +320k.", {"size": 16, "color": GREY}),
])
text_box(s, LM, BODY_TOP + 2400000, COL, 2400000, [
    ("Pod names churn on every rollout. Every extra label multiplies by that churn.", {"size": 18}),
    ("ENABLE_POD_LABELS=true is how you find out.", {"size": 18, "bold": True, "space_after": 0}),
])
text_box(s, RIGHT_X, BODY_TOP, COL, 4800000, [
    ("The rule", {"size": 20, "bold": True, "color": BRAND}),
    ("Identity on logs", {"size": 22, "bullet": True}),
    ("Stable dimensions on metrics", {"size": 22, "bullet": True}),
    ("Join at query time", {"size": 22, "bullet": True}),
    ("Our rig", {"size": 20, "bold": True, "color": BRAND}),
    ("7 counters in counters.csv", {"size": 18, "bullet": True}),
    ("Pod labels off; exported_pod is the only identity", {"size": 18, "bullet": True}),
    ("Join on the fixed part of the name, never the hash", {"size": 18, "bullet": True, "space_after": 0}),
], space_after=10)

# ----------------------------------------------------------------------------------------------
# Slide 7a: the raw log line
s = content_slide(
    "Signal 2: the serving log is the telemetry.",
    src="vLLM V1 engine, vllm/v1/metrics/loggers.py: one stats line every 10 s while the engine is busy (DEBUG level when idle).",
    note=("Section 4 is the centre of the talk, 6 min for 7a to 7c. This is one line of vLLM stdout. Every 10 "
          "seconds while it is busy. Read the fields: prompt and generation throughput, running requests, "
          "waiting requests, KV cache usage, prefix cache hit rate. And when the scheduler starts evicting work "
          "because the cache is full, a Preemptions field appears. Five fields, six under stress, and not one of "
          "them exists in any GPU counter. The two lines are the same rig: idle-ish over-provisioned pod, and the "
          "constrained pod during the demo load."))
text_box(s, LM, BODY_TOP, CW, 500000, [("vllm-overprov, steady load", {"size": 16, "color": GREY, "space_after": 0})])
code_box(s, LM, BODY_TOP + 450000, CW, 900000,
         "INFO [loggers.py] Engine 000: Avg prompt throughput: 1180.2 tokens/s, Avg generation throughput:\n"
         "4711.7 tokens/s, Running: 15 reqs, Waiting: 0 reqs, GPU KV cache usage: 0.1%, Prefix cache hit rate: 0.0%", size=13)
text_box(s, LM, BODY_TOP + 1500000, CW, 500000, [("vllm-constrained, saturating load", {"size": 16, "color": GREY, "space_after": 0})])
code_box(s, LM, BODY_TOP + 1950000, CW, 1100000,
         "INFO [loggers.py] Engine 000: Avg prompt throughput: 9810.4 tokens/s, Avg generation throughput:\n"
         "17227.0 tokens/s, Running: 76 reqs, Waiting: 116 reqs, Preemptions: 41, GPU KV cache usage: 99.6%,\n"
         "Prefix cache hit rate: 0.0%", size=13)
text_box(s, LM, BODY_TOP + 3250000, CW, 1500000, [
    ("tokens/s  ·  running  ·  waiting  ·  KV cache %  ·  prefix hits  ·  preemptions",
     {"size": 20, "bold": True, "color": BRAND}),
    ("Six facts about the inference work. Zero of them in any GPU counter.", {"size": 20, "space_after": 0}),
])

# ----------------------------------------------------------------------------------------------
# Slide 7b: Lua + log_to_metrics
s = content_slide(
    "Fifteen lines of Lua, per-pod metrics.",
    src="Fluent Bit 5.1: tail -> kubernetes -> lua -> grep -> log_to_metrics -> prometheus_exporter. vLLM native metrics: docs.vllm.ai/en/latest/design/metrics",
    note=("Fluent Bit tails the container log, the kubernetes filter attaches the pod name (that is the join key "
          "arriving), the Lua filter does five string.match calls and promotes pod_name to a top-level field, grep "
          "drops everything that is not a stats line, log_to_metrics turns the fields into gauges labelled by "
          "pod_name, and prometheus_exporter serves them on :2021 for the same Prometheus that scrapes DCGM. "
          "Now the honest caveat, say it before someone asks: vLLM exposes all of this natively on /metrics, "
          "kv_cache_usage_perc, num_requests_waiting, request_queue_time_seconds. vLLM is the demo vehicle. This "
          "technique is for everything that does not: custom servers, vendor images you cannot touch, log-only "
          "pipelines, the TGI or Triton you inherited. Same fifteen lines, different regex."))
code_box(s, LM, BODY_TOP, COL + 1500000, 3700000,
         "function extract_vllm_metrics(tag, ts, record)\n"
         "  local line = record[\"log\"] or \"\"\n"
         "  local gen = string.match(line, \"generation throughput:%s*([%d%.]+)\")\n"
         "  if gen == nil then record[\"vllm_parsed\"] = \"false\"; return 1, ts, record end\n"
         "  record[\"gen_tokens_per_s\"]   = tonumber(gen)\n"
         "  record[\"running_reqs\"]       = tonumber(string.match(line, \"Running:%s*(%d+)\")) or 0\n"
         "  record[\"waiting_reqs\"]       = tonumber(string.match(line, \"Waiting:%s*(%d+)\")) or 0\n"
         "  record[\"kv_cache_usage_pct\"] = tonumber(string.match(line, \"KV cache usage:%s*([%d%.]+)%%\")) or 0\n"
         "  record[\"preemptions\"]        = tonumber(string.match(line, \"Preemptions:%s*(%d+)\")) or 0\n"
         "  record[\"pod_name\"]  = record[\"kubernetes\"][\"pod_name\"]   -- the join key\n"
         "  record[\"vllm_parsed\"] = \"true\"\n"
         "  return 2, ts, record\n"
         "end", size=10)
text_box(s, RIGHT_X + 1500000, BODY_TOP, COL - 1500000, 2300000, [
    ("tail -> kubernetes -> lua -> grep", {"size": 13, "font": MONO}),
    ("-> log_to_metrics -> prometheus_exporter", {"size": 13, "font": MONO}),
    ("vllm_log_kv_cache_usage_pct{pod_name=...}", {"size": 12, "font": MONO, "color": BRAND}),
    ("vllm_log_waiting_reqs{pod_name=...}", {"size": 12, "font": MONO, "color": BRAND}),
    ("vllm_log_preemptions_total{pod_name=...}", {"size": 12, "font": MONO, "color": BRAND, "space_after": 0}),
], space_after=6)
text_box(s, RIGHT_X + 1500000, BODY_TOP + 2400000, COL - 1500000, 2400000, [
    ("Honest caveat", {"size": 18, "bold": True, "color": BRAND}),
    ("vLLM already exposes these on /metrics. It is our demo vehicle.", {"size": 15}),
    ("This is for everything that does not: custom servers, vendor images, log-only pipelines, the TGI or Triton you inherited. "
     "Same 15 lines, different regex.", {"size": 15, "space_after": 0}),
], space_after=6)

# ----------------------------------------------------------------------------------------------
# Slide 7c: demo result
s = content_slide(
    "KV cache 100%. Memory counter: unchanged.",
    src="Queue time rises before 'waiting' is visibly non-zero: Elastic Observability Labs, tuning vLLM Prometheus metrics (2025). Rig numbers from the live demo load.",
    note=("LIVE DEMO. Start the loadgen before this slide (kubectl apply loadgen-job.yaml), it runs 12 minutes. "
          "Grafana row 1: FB_USED flat on both pods, GPU_UTIL pegged on both. Row 2: the constrained pod's KV "
          "cache goes to 100%, waiting climbs to around 100, p95 queue time jumps from 0.3 s to 4.8 s. Row 3 cross-check "
          "agrees with the log-derived numbers. Be precise about row 1: GPU_UTIL did go to 100% and SM_ACTIVE to 90% "
          "on the constrained pod, so DCGM does say 'busy'. What it cannot say is why, or how much headroom is left: "
          "FB_USED is 3.6 GB before, during and after. The over-provisioned pod shows 55% util and 0.2% KV cache under "
          "its own load, so it has 99% of its cache free, and no GPU counter tells you that either. Preemptions stayed "
          "at zero in this run (vLLM queues rather than evicts at max-num-seqs 256); if they appear, that is the scheduler "
          "evicting running work."))
picture_or_placeholder(s, LM, BODY_TOP, CW, 3500000, "grafana-rows-1-2.png",
                       "Grafana rows 1 and 2 during saturation: FB_USED flat, KV cache 100%, waiting ~100, queue time p95 4.8 s")
text_box(s, LM, BODY_TOP + 3650000, CW, 1200000, [
    ("Queue time first. Waiting confirms. FB_USED: 3.6 GB before, 3.6 GB after.", {"size": 20, "bold": True, "color": BRAND}),
    ("GPU_UTIL says \"busy\" for both pods. It cannot say that one has zero headroom and 100 requests queued, and the other 99% of its cache free.",
     {"size": 18, "space_after": 0}),
])

# ----------------------------------------------------------------------------------------------
# Slide 8: traces
s = content_slide(
    "Signal 3: a slow span with a pod name.",
    src="vLLM --otlp-traces-endpoint -> OTel Collector (k8sattributes) -> Jaeger. Tracing was removed in the V1 rewrite and reinstated in vllm PR #20372: needs vLLM >= 0.10.2.",
    note=("Section 5, 3 min. vLLM emits one span per request natively, you point it at the OTel Collector. The "
          "k8sattributes processor stamps k8s.pod.name on every span by looking up the source IP. A slow span on "
          "its own tells you a request was slow. A slow span on the pod whose KV cache was at 100% at that second, "
          "with 116 requests waiting, tells you why. Gotcha worth saying out loud: tracing disappeared in the vLLM "
          "V1 engine rewrite and came back in PR 20372, so you need 0.10.2 or later. We run 0.30. If your traces "
          "vanished after an upgrade, that is why. Abstract wording: we show traces from the serving path, one "
          "span per request; multi-hop waterfalls are a flag away but not the point. Bonus in 0.30: vLLM also emits "
          "start-up spans (Load weights, Allocate KV cache, Compile graph), so cold-start time is traceable too."))
code_box(s, LM, BODY_TOP, COL, 1600000,
         "# vLLM\n--otlp-traces-endpoint=grpc://otel-collector.observability:4317\n\n"
         "# OTel Collector\nprocessors:\n  k8sattributes:\n    extract: { metadata: [k8s.pod.name, k8s.namespace.name] }", size=11)
code_box(s, RIGHT_X, BODY_TOP, COL, 1600000,
         "span: llm_request   duration: 5.73s\n"
         "  k8s.pod.name    = vllm-constrained-7f9fdfc497-2mjzz\n"
         "  gen_ai.usage.prompt_tokens      = 582\n"
         "  gen_ai.usage.completion_tokens  = 384\n"
         "  gen_ai.latency.time_in_queue    = 0.61s\n"
         "  gen_ai.latency.time_in_model_decode = 5.33s", size=11)
picture_or_placeholder(s, LM, BODY_TOP + 1700000, CW, 2000000, "jaeger-trace-detail.png",
                       "Jaeger: a 5.7 s llm_request span on vllm-constrained with k8s.pod.name and gen_ai.* tags")
text_box(s, LM, BODY_TOP + 3800000, CW, 1000000, [
    ("Slow span: a fact. Slow span on the pod whose KV cache was 100% at that second: a diagnosis.",
     {"size": 20, "bold": True, "color": BRAND, "space_after": 0}),
])

# ----------------------------------------------------------------------------------------------
# Slide 9: the join
s = content_slide(
    "Same pod name. Three sources. One row.",
    src="Grafana dashboard uid gpu-inference-obs, variable $pod matches exported_pod (DCGM), pod_name (Fluent Bit) and pod (vLLM, traces).",
    note=("Section 6, 2 min. This is the slide the whole talk builds to. One Grafana dashboard, one pod variable, "
          "three data sources that never heard of each other. Point at the timestamps: KV cache pegs, waiting "
          "climbs, span latency jumps, and the DCGM row above is unchanged. That is the black box opened. You did "
          "not need a new agent, a new vendor or eBPF. You needed the pod name on every signal and the discipline to "
          "keep it there."))
picture_or_placeholder(s, LM, BODY_TOP, CW, 3700000, "grafana-full.png",
                       "Grafana dashboard, all rows, $pod = vllm-constrained, during saturation")
text_box(s, LM, BODY_TOP + 3850000, CW, 1000000, [
    ("No new agent. No vendor. No eBPF. The pod name on every signal, and the discipline to keep it there.",
     {"size": 20, "bold": True, "color": BRAND, "space_after": 0}),
])

# ----------------------------------------------------------------------------------------------
# Slide 10: what silently broke
s = content_slide(
    "What silently broke along the way.",
    src="EKS Auto Mode GPU support: docs.aws.amazon.com/eks/latest/userguide/device-management-nvidia-dra-device-plugin.html",
    note=("1 min, pick the first one if short on time. EKS Auto Mode ships NVIDIA drivers and the device plugin "
          "on its GPU AMIs, but does not support the GPU Operator or the NVIDIA DRA driver. Every DCGM how-to "
          "assumes the Operator. So: standalone dcgm-exporter DaemonSet, pod-resources hostPath, SYS_ADMIN cap. "
          "Second: Fluent Bit's kubernetes filter needs Kube_Tag_Prefix to match the tail tag exactly, or the pod "
          "name silently never arrives and your join key is empty. Third, from this morning: one GPU per pod and a "
          "NodePool capped at two GPUs means a RollingUpdate can never surge; the new pod sits Pending forever. "
          "strategy: Recreate."))
table(s, LM, BODY_TOP, CW, 3600000, [
    ["What we expected", "What happened", "Fix"],
    ["GPU Operator installs DCGM on EKS Auto Mode", "Auto Mode supports neither the GPU Operator nor the NVIDIA DRA driver (drivers + device plugin come with the AMI)",
     "Standalone dcgm-exporter DaemonSet, pod-resources hostPath, SYS_ADMIN"],
    ["Fluent Bit kubernetes filter adds pod_name", "Kube_Tag_Prefix did not match the tail tag; metadata silently missing, join key empty",
     "Kube_Tag_Prefix kube.var.log.containers. (match the tag you actually emit)"],
    ["Rolling update of a 1-GPU pod", "NodePool capped at 2 GPUs: new pod Pending forever, old one never releases",
     "strategy: Recreate on every GPU deployment"],
], col_widths=[3300000, 4800000, CW - 8100000], size=13)

# ----------------------------------------------------------------------------------------------
# Slide 11: where this is going
s = content_slide(
    "Where this is going.",
    src="llm-d on AWS: aws.amazon.com/blogs/machine-learning/introducing-disaggregated-inference-on-aws-powered-by-llm-d. Gateway API Inference Extension: github.com/kubernetes-sigs/gateway-api-inference-extension. "
        "CloudWatch OTel Container Insights for EKS (June 2026).",
    note=("1 min. Three things to know before someone asks 'isn't this solved'. One: disaggregated prefill/decode "
          "(llm-d, NVIDIA Dynamo, llm-d-aws) splits a request across two pods, with the KV cache shipped between "
          "them over NIXL and EFA; AWS reports up to 70% more tokens per second at concurrency 128. The pod is no "
          "longer the whole request, so the join key becomes request id plus pod. Two: the Gateway API Inference "
          "Extension's endpoint picker and Dynamo's KV-aware router consume exactly these signals, queue depth and "
          "KV cache, to route. The join is moving from Grafana into the router. Three: AWS's OTel-native Container "
          "Insights, June 2026, packages signal 1 for EKS out of the box. Signals 2 and 3 are still yours to wire."))
text_box(s, LM, BODY_TOP, COL, 4800000, [
    ("Disaggregated prefill / decode", {"size": 20, "bold": True, "color": BRAND}),
    ("llm-d, NVIDIA Dynamo, llm-d-aws: one request, two pods, KV cache shipped over NIXL / EFA. Up to +70% tokens/s at concurrency 128.",
     {"size": 16}),
    ("Join key becomes request id + pod.", {"size": 16, "bold": True}),
    ("Signals move into the router", {"size": 20, "bold": True, "color": BRAND}),
    ("Gateway API Inference Extension endpoint picker and Dynamo's KV-aware router route on queue depth and KV cache %. "
     "The join leaves Grafana.", {"size": 16, "space_after": 0}),
], space_after=8)
text_box(s, RIGHT_X, BODY_TOP, COL, 4800000, [
    ("Signal 1 is becoming a checkbox", {"size": 20, "bold": True, "color": BRAND}),
    ("CloudWatch OTel-native Container Insights for EKS (June 2026) wires DCGM into OTel with pod labels and a PromQL endpoint.",
     {"size": 16}),
    ("Signals 2 and 3 are still yours to wire.", {"size": 16, "bold": True}),
    ("Out of scope today, ask me after", {"size": 20, "bold": True, "color": GREY}),
    ("XID / ECC / thermal faults, output quality, eBPF GPU profiling, Dynamo internals.", {"size": 16, "color": GREY, "space_after": 0}),
], space_after=8)

# ----------------------------------------------------------------------------------------------
# Slide 12: steal this
s = content_slide(
    "Steal this for your cluster.",
    src="Original session design: [original author, AWS]. Reproduced clean-room on EKS Auto Mode; all configs in the repo.",
    note=("1 min. Three counters, one filter, one rule. SM_ACTIVE instead of GPU_UTIL. KV cache percent and queue "
          "time from the serving framework, by log or by /metrics, whichever you have. Pod name on every signal, "
          "nothing else on the metrics. Everything in the repo deploys with one terraform apply on EKS Auto Mode. "
          "Attribution: this session was designed by [original author]; I rebuilt it from the abstract and broke "
          "different things along the way."))
text_box(s, LM, BODY_TOP, COL, 4800000, [
    ("Three counters", {"size": 20, "bold": True, "color": BRAND}),
    ("DCGM_FI_PROF_SM_ACTIVE, not GPU_UTIL", {"size": 18, "bullet": True}),
    ("KV cache %  (log or /metrics)", {"size": 18, "bullet": True}),
    ("Queue time p95, then waiting", {"size": 18, "bullet": True}),
    ("One filter", {"size": 20, "bold": True, "color": BRAND}),
    ("15 lines of Lua + log_to_metrics. Change the regex, keep the pipeline.", {"size": 18, "bullet": True, "space_after": 0}),
], space_after=8)
text_box(s, RIGHT_X, BODY_TOP, COL, 4800000, [
    ("One rule", {"size": 20, "bold": True, "color": BRAND}),
    ("Pod name on every signal. Identity on logs, stable dimensions on metrics, join at query time.", {"size": 18, "bullet": True}),
    ("In the repo", {"size": 20, "bold": True, "color": BRAND}),
    ("Terraform for EKS Auto Mode + GPU NodePool", {"size": 18, "bullet": True}),
    ("dcgm-exporter, Fluent Bit, OTel Collector, Jaeger manifests", {"size": 18, "bullet": True}),
    ("Grafana dashboard, loadgen, validate.sh", {"size": 18, "bullet": True, "space_after": 0}),
], space_after=8)

# ----------------------------------------------------------------------------------------------
# Slide 13: one link
s = statement_slide(
    "github.com/danilosilvase/gpu-observability-kubecon-na-2026",
    "Danilo Souza, AWS Professional Services  ·  Henrique Santana, AWS\nSession feedback: scan the CNCF QR code",
    note=("Thank the room, point at the repo, ask for feedback via the CNCF QR. Q&A. Likely questions: 'why not just "
          "scrape vLLM /metrics' (answered on 7b, repeat it), 'what about MIG or time-slicing' (dcgm-exporter 4.5+ has "
          "per-process metrics, narrows but does not close the gap), 'SGLang / TGI field names' (same technique, verify "
          "the regex against your log line), 'hardware faults' (fourth signal class, out of scope)."))
picture_or_placeholder(s, W - LM - 1800000, 4600000, 1800000, 1800000, "cncf-feedback-qr.png", "CNCF feedback QR")

prs.save(OUT)
print(f"saved {OUT} with {len(prs.slides)} slides")
