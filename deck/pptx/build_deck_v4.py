#!/usr/bin/env python3
"""v4 deck: visual rebuild after the Oct 6 critique round (timing, technical, design, followability, language).

Usage: uv run --with python-pptx --with pillow python build_deck_v4.py <template.pptx> <out.pptx> screenshots
Template = branded CNCF template with cover + title filled (~/.aki/tmp/kubecon-session.pptx). Slide 3 is dropped.
Panels in screenshots/v4 were captured solo from Grafana at 3x (shoot.mjs), 16:52 to 17:09 Dublin, Oct 6 2026.
"""
import sys, os, copy
from pptx import Presentation
from pptx.util import Emu, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.oxml.ns import qn
from lxml import etree
from PIL import Image

TEMPLATE, OUT, SHOTS = sys.argv[1], sys.argv[2], sys.argv[3]
V4 = os.path.join(SHOTS, "v4")

BRAND = RGBColor(153, 19, 70)
BRAND_LIGHT = RGBColor(0xF6, 0xE3, 0xEA)
DARK = RGBColor(0x26, 0x26, 0x26)
GREY = RGBColor(0x6B, 0x6B, 0x6B)
LIGHT = RGBColor(0xF3, 0xF3, 0xF3)
MID = RGBColor(0xDD, 0xDD, 0xDD)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
GREEN = RGBColor(0x2E, 0x7D, 0x32)
GREEN_LIGHT = RGBColor(0xE3, 0xF1, 0xE4)
RED = RGBColor(0xC6, 0x28, 0x28)
RED_LIGHT = RGBColor(0xFB, 0xE5, 0xE5)
AMBER = RGBColor(0xB2, 0x6A, 0x00)
BLUE = RGBColor(0x1F, 0x5F, 0xA8)
FONT = "Arial"
MONO = "Courier New"

W, H = 12192000, 6858000
LM = 403682
CW = W - 2 * LM
BODY_TOP = 1250000
BODY_BOTTOM = 6250000
FOOT_Y = 6400000

prs = Presentation(TEMPLATE)
L_COVER, L_TITLE, L_CONTENT = (prs.slide_layouts[i] for i in (0, 1, 2))

# remove the faint KnativeCon watermark from the content layout (it collides with body text)
for pic in list(L_CONTENT.shapes):
    if pic.shape_type == 13 and pic.left > 9000000 and pic.top > 1000000:
        pic._element.getparent().remove(pic._element)

# drop template slide 3 ("About this session")
sld_ids = prs.slides._sldIdLst
ids = list(sld_ids)
if len(ids) >= 3:
    prs.part.drop_rel(ids[2].get(qn("r:id")))
    sld_ids.remove(ids[2])


# ---------------------------------------------------------------- helpers
def _run(par, text, size, bold=False, color=DARK, font=FONT, italic=False):
    r = par.add_run()
    r.text = text
    f = r.font
    f.name, f.size, f.bold, f.italic = font, Pt(size), bold, italic
    f.color.rgb = color
    return r


def _bullet(par, char="•", indent=285750):
    pPr = par._p.get_or_add_pPr()
    pPr.set("marL", str(indent)); pPr.set("indent", str(-indent))
    for tag in ("a:buNone", "a:buChar", "a:buAutoNum"):
        for el in pPr.findall(qn(tag)):
            pPr.remove(el)
    etree.SubElement(pPr, qn("a:buChar")).set("char", char)


def text_box(slide, x, y, w, h, lines, size=18, color=DARK, bold=False, font=FONT, align=PP_ALIGN.LEFT,
             anchor=MSO_ANCHOR.TOP, bullets=False, space_after=6, fill=None, margin=91440, line_spacing=None):
    """lines: str | (str, opts) | list of (str, opts) runs within one paragraph."""
    tb = slide.shapes.add_textbox(Emu(x), Emu(y), Emu(w), Emu(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = Emu(margin)
    tf.margin_top = tf.margin_bottom = Emu(45720)
    if fill is not None:
        tb.fill.solid(); tb.fill.fore_color.rgb = fill
    first = True
    for item in lines:
        par = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        if isinstance(item, list):            # rich paragraph
            runs = item; o = {}
        else:
            text, o = (item, {}) if isinstance(item, str) else item
            runs = [(text, o)]
        par.alignment = o.get("align", align)
        par.space_after = Pt(o.get("space_after", space_after))
        if line_spacing:
            par.line_spacing = line_spacing
        if o.get("bullet", bullets):
            _bullet(par)
        for text, ro in runs:
            _run(par, text, ro.get("size", size), ro.get("bold", bold), ro.get("color", color),
                 ro.get("font", font), ro.get("italic", False))
    return tb


def rect(slide, x, y, w, h, fill, line=None, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.08, line_w=1.0):
    s = slide.shapes.add_shape(shape, Emu(x), Emu(y), Emu(w), Emu(h))
    s.fill.solid(); s.fill.fore_color.rgb = fill
    if line is None:
        s.line.fill.background()
    else:
        s.line.color.rgb = line; s.line.width = Pt(line_w)
    if shape == MSO_SHAPE.ROUNDED_RECTANGLE:
        s.adjustments[0] = radius
    st = s._element.find(qn("p:style"))
    if st is not None: s._element.remove(st)
    s.text_frame.text = ""
    return s


def card(slide, x, y, w, h, head, body, fill=LIGHT, head_color=BRAND, head_size=20, body_size=16, line=None,
         align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP):
    rect(slide, x, y, w, h, fill, line=line)
    lines = [(head, {"size": head_size, "bold": True, "color": head_color})]
    for b in body:
        lines.append(b if isinstance(b, (tuple, list)) else (b, {"size": body_size}))
    lines[-1] = lines[-1] if isinstance(lines[-1], list) else (lines[-1][0], {**lines[-1][1], "space_after": 0})
    text_box(slide, x + 60000, y + 60000, w - 120000, h - 120000, lines, align=align, anchor=anchor, space_after=8,
             margin=120000)


def chip(slide, x, y, w, h, text, fill=BRAND, color=WHITE, size=16, font=FONT, bold=True):
    s = rect(slide, x, y, w, h, fill, radius=0.5)
    tf = s.text_frame
    tf.margin_left = tf.margin_right = Emu(90000); tf.margin_top = tf.margin_bottom = Emu(0)
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
    _run(p, text, size, bold, color, font)
    return s


def arrow(slide, x1, y1, x2, y2, color=GREY, width=2.25):
    c = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Emu(x1), Emu(y1), Emu(x2), Emu(y2))
    c.line.color.rgb = color; c.line.width = Pt(width)
    st = c._element.find(qn("p:style"))
    if st is not None: c._element.remove(st)
    ln = c.line._get_or_add_ln()
    tail = etree.SubElement(ln, qn("a:tailEnd")); tail.set("type", "triangle"); tail.set("w", "med"); tail.set("len", "med")
    return c


def vline(slide, x, y1, y2, color=RED, width=3.0, dash=True):
    c = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Emu(x), Emu(y1), Emu(x), Emu(y2))
    c.line.color.rgb = color; c.line.width = Pt(width)
    st = c._element.find(qn("p:style"))
    if st is not None: c._element.remove(st)
    if dash:
        ln = c.line._get_or_add_ln()
        etree.SubElement(ln, qn("a:prstDash")).set("val", "dash")
    return c


def picture(slide, x, y, w, h, filename, folder=None):
    path = os.path.join(folder or SHOTS, filename)
    iw, ih = Image.open(path).size
    scale = min(w / iw, h / ih)
    pw, ph = int(iw * scale), int(ih * scale)
    px, py = x + (w - pw) // 2, y + (h - ph) // 2
    pic = slide.shapes.add_picture(path, Emu(px), Emu(py), width=Emu(pw), height=Emu(ph))
    return px, py, pw, ph


def panel(slide, x, y, w, h, name):
    """Grafana panel from screenshots/v4 with a thin frame."""
    px, py, pw, ph = picture(slide, x, y, w, h, name, V4)
    f = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Emu(px), Emu(py), Emu(pw), Emu(ph))
    f.fill.background(); f.line.color.rgb = MID; f.line.width = Pt(0.75)
    st = f._element.find(qn("p:style"));  f._element.remove(st) if st is not None else None
    return px, py, pw, ph


def callout(slide, x, y, w, h, big, small=None, fill=BRAND, size=36):
    rect(slide, x, y, w, h, fill, radius=0.12)
    lines = [(big, {"size": size, "bold": True, "color": WHITE, "align": PP_ALIGN.CENTER, "space_after": 0})]
    if small:
        lines.append((small, {"size": 14, "color": WHITE, "align": PP_ALIGN.CENTER, "space_after": 0}))
    text_box(slide, x, y, w, h, lines, anchor=MSO_ANCHOR.MIDDLE, align=PP_ALIGN.CENTER, space_after=2)


def title(slide, text):
    text_box(slide, LM, 0, 8900000, 973013, [text], size=30, bold=True, color=WHITE, anchor=MSO_ANCHOR.MIDDLE, space_after=0)


def source(slide, text):
    text_box(slide, LM, FOOT_Y, CW, 380000, [text], size=10, color=GREY, space_after=0)


def notes(slide, text):
    slide.notes_slide.notes_text_frame.text = text


def content_slide(t, note=None, src=None):
    s = prs.slides.add_slide(L_CONTENT)
    title(s, t)
    if src: source(s, src)
    if note: notes(s, note)
    return s


def statement_slide(big, small=None, note=None, big_size=54):
    s = prs.slides.add_slide(L_TITLE)
    lines = [(big, {"size": big_size, "bold": True, "color": WHITE})]
    if small:
        lines.append((small, {"size": 22, "color": WHITE, "space_after": 0}))
    text_box(s, LM, 1700000, CW, 3400000, lines, anchor=MSO_ANCHOR.MIDDLE, space_after=18)
    if note: notes(s, note)
    return s


def strap(slide, text, y=5450000, size=22, color=BRAND, h=800000):
    text_box(slide, LM, y, CW, h, [(text, {"size": size, "bold": True, "color": color, "space_after": 0})],
             anchor=MSO_ANCHOR.MIDDLE)


def fade_in(slide, shape, duration_ms=700):
    """Click-triggered fade entrance on one shape (PowerPoint p:timing XML)."""
    sid = shape.shape_id
    xml = f"""<p:timing xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
      xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
  <p:tnLst><p:par><p:cTn id="1" dur="indefinite" restart="never" nodeType="tmRoot"><p:childTnLst>
   <p:seq concurrent="1" nextAc="seek"><p:cTn id="2" dur="indefinite" nodeType="mainSeq"><p:childTnLst>
    <p:par><p:cTn id="3" fill="hold"><p:stCondLst><p:cond delay="indefinite"/></p:stCondLst><p:childTnLst>
     <p:par><p:cTn id="4" fill="hold"><p:stCondLst><p:cond delay="0"/></p:stCondLst><p:childTnLst>
      <p:par><p:cTn id="5" presetID="10" presetClass="entr" presetSubtype="0" fill="hold" grpId="0" nodeType="clickEffect">
       <p:stCondLst><p:cond delay="0"/></p:stCondLst><p:childTnLst>
        <p:set><p:cBhvr><p:cTn id="6" dur="1" fill="hold"><p:stCondLst><p:cond delay="0"/></p:stCondLst></p:cTn>
         <p:tgtEl><p:spTgt spid="{sid}"/></p:tgtEl><p:attrNameLst><p:attrName>style.visibility</p:attrName></p:attrNameLst></p:cBhvr>
         <p:to><p:strVal val="visible"/></p:to></p:set>
        <p:animEffect transition="in" filter="fade"><p:cBhvr><p:cTn id="7" dur="{duration_ms}"/>
         <p:tgtEl><p:spTgt spid="{sid}"/></p:tgtEl></p:cBhvr></p:animEffect>
       </p:childTnLst></p:cTn></p:par>
     </p:childTnLst></p:cTn></p:par>
    </p:childTnLst></p:cTn></p:par>
   </p:childTnLst></p:cTn><p:prevCondLst><p:cond evt="onPrev" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:prevCondLst>
   <p:nextCondLst><p:cond evt="onNext" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:nextCondLst></p:seq>
  </p:childTnLst></p:cTn></p:par></p:tnLst>
  <p:bldLst><p:bldP spid="{sid}" grpId="0"/></p:bldLst>
</p:timing>"""
    old = slide._element.find(qn("p:timing"))
    if old is not None: slide._element.remove(old)
    slide._element.append(etree.fromstring(xml))


COL = (CW - 300000) // 2
RIGHT_X = LM + COL + 300000
M = lambda s, c=DARK, b=False: {"font": MONO, "size": s, "color": c, "bold": b}

# ================================================================ 3. the incident
s = content_slide(
    "02:14. p99 doubles. Every GPU chart is green.",
    note=("1.5 min. Open with the incident, not the architecture. p99 doubled at 02:14. You open the GPU dashboard: "
          "utilisation 95%, framebuffer 90% used, both flat for an hour. Pods Ready, nothing throttled, no OOM, no "
          "restart. Everything the GPU can tell you says healthy and busy. Nobody knows why. That is the black box."))
text_box(s, LM, BODY_TOP + 150000, 4300000, 1000000, [
    ("02:14", {"size": 72, "bold": True, "color": BRAND, "space_after": 0})])
# show, do not tell: p99 sparkline (flat green, doubles red at 02:14) replaces the sentence "p99 latency doubles"
picture(s, LM, BODY_TOP + 1050000, 4100000, 2050000, "p99-spark.png", V4)
text_box(s, LM, BODY_TOP + 3150000, 4000000, 1100000, [
    ("The model is healthy.", {"size": 20}),
    ("The pods are Ready.", {"size": 20}),
    ("Nothing is throttled.", {"size": 20, "space_after": 0})], space_after=6)
why_box = text_box(s, LM, BODY_TOP + 4300000, 4300000, 800000, [
    ("Nobody knows why.", {"size": 32, "bold": True, "color": BRAND, "space_after": 0})], space_after=0)
# AI-generated scene (Stable Image Ultra via Bedrock, see gen_images.py): on-call engineer facing a wall of green
# dashboards at 02:14. Replaces the three stat cards; the dashboards in the picture carry the "all green" message.
IMG_X = LM + 4300000
IMG_W = CW - 4300000
IMG_H = IMG_W * 9 // 16
px, py, pw, ph = picture(s, IMG_X, BODY_TOP + 100000, IMG_W, IMG_H, "incident-oncall.png", V4)
f = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Emu(px), Emu(py), Emu(pw), Emu(ph))
f.fill.background(); f.line.color.rgb = MID; f.line.width = Pt(0.75)
st = f._element.find(qn("p:style")); f._element.remove(st) if st is not None else None
text_box(s, IMG_X, py + ph + 150000, IMG_W, 700000, [
    ("Every signal the hardware gives you says: busy and healthy.", {"size": 18, "color": GREY, "align": PP_ALIGN.CENTER,
                                                                      "space_after": 0})], align=PP_ALIGN.CENTER)
fade_in(s, why_box)

# ================================================================ 4. the hook
s = content_slide(
    "Same counter. Opposite story.",
    src="Industry average production GPU utilisation ~5%: Cast AI, State of GPU utilisation 2026 (cast.ai/blog/fractional-gpu-kubernetes)",
    note=("0.5 min. Across the industry the average production GPU runs at around 5% utilisation. Our incident fleet "
          "reads 95%. Same counter, two readings. One fleet looks saturated, the other idle. On its own, the number "
          "says nothing about the actual inference work. The talk is about where that signal actually lives."))
half = (CW - 400000) // 2
for i, (num, lab, sub, col, fill) in enumerate([
        ("95%", "our fleet at 02:14", "looks saturated", RED, RED_LIGHT),
        ("~5%", "industry average", "looks idle", BLUE, RGBColor(0xE4, 0xEE, 0xF8))]):
    x = LM + i * (half + 400000)
    rect(s, x, BODY_TOP, half, 3600000, fill)
    text_box(s, x, BODY_TOP, half, 3600000, [
        (num, {"size": 130, "bold": True, "color": col, "align": PP_ALIGN.CENTER, "space_after": 0}),
        (lab, {"size": 22, "bold": True, "align": PP_ALIGN.CENTER, "space_after": 0}),
        (sub, {"size": 18, "color": GREY, "align": PP_ALIGN.CENTER, "space_after": 0})],
        anchor=MSO_ANCHOR.MIDDLE, align=PP_ALIGN.CENTER, space_after=4)
text_box(s, LM, BODY_TOP + 3650000, CW, 500000, [("DCGM_FI_DEV_GPU_UTIL", {**M(18, GREY), "align": PP_ALIGN.CENTER, "space_after": 0})],
         align=PP_ALIGN.CENTER)
strap(s, "On its own, this number says nothing about the inference work.", y=5450000, size=24)

# ================================================================ 5. pre-allocation (FB_USED panel)
s = content_slide(
    "vLLM grabs the memory before request one.",
    src="Live rig, Oct 6 2026: two vLLM pods, facebook/opt-125m, EKS Auto Mode, g5.xlarge (A10G 24 GB). 0.90 x 24 GB = 21.6 GB; the gap to 20.5 GB is CUDA context and driver overhead.",
    note=("Section 2 starts here, 4.5 min for slides 5 to 8. Every serious LLM server pre-allocates its memory pool "
          "at start-up: weights plus activation workspace plus the KV cache, capped by --gpu-memory-utilization. "
          "On our tiny demo model the weights are small, so the pool is effectively KV cache. The framebuffer counter "
          "jumps to the configured fraction in the first 30 seconds and never moves again, idle or melting. "
          "Constrained pod at 0.15 shows 3.6 GB, over-provisioned at 0.90 shows 20.5 GB, both perfectly flat. "
          "The one with less memory is the one that will get into trouble, and this counter cannot tell you that."))
px, py, pw, ph = panel(s, LM, BODY_TOP, 7400000, 4200000, "panel-2.png")
callout(s, px + pw - 2300000, py + int(ph * 0.14), 2100000, 620000, "20.5 GB, flat", "gpu-mem-util 0.90", fill=GREEN, size=20)
callout(s, px + pw - 2300000, py + int(ph * 0.62), 2100000, 620000, "3.6 GB, flat", "gpu-mem-util 0.15", fill=BLUE, size=20)
rx = LM + 7400000 + 300000; rw = CW - 7400000 - 300000
text_box(s, rx, BODY_TOP, rw, 4200000, [
    ("DCGM_FI_DEV_FB_USED", {**M(17, BRAND, True)}),
    ("The counter everyone watches.", {"size": 16, "color": GREY}),
    ("Pre-allocated pool: weights, activations, KV cache. Sized by --gpu-memory-utilization.", {"size": 17, "bullet": True}),
    ("Jumps to the configured fraction at start-up.", {"size": 17, "bullet": True}),
    ("Then flat. Idle or saturated, same number.", {"size": 17, "bullet": True}),
    ("Which one is about to fall over? The smaller one. The counter says the opposite.", {"size": 17, "bold": True, "space_after": 0}),
], space_after=10)
strap(s, "It measures a config value. Never the workload sitting on top of it.", y=5550000, size=22)

# ================================================================ 6. prefill vs decode
s = content_slide(
    "GPU util % cannot tell prefill from decode.",
    src="DCGM_FI_DEV_GPU_UTIL (field 203) is NVML-polled: 'a kernel ran during the sample window'. The profiling fields on the next slide come from the GPU's hardware profiler.",
    note=("GPU_UTIL means 'at least one kernel was running during the sample window'. A single thread spinning counts "
          "as 100%. Inference has two phases with opposite profiles. Prefill: the whole prompt in one pass, big "
          "matmuls, compute-bound. Decode: one token per step, re-reading the whole KV cache every step, "
          "memory-bandwidth-bound. The same 100% util covers both. It cannot see which phase you are in or how much "
          "of the silicon is doing anything."))
cw2 = (CW - 400000) // 2
card(s, LM, BODY_TOP, cw2, 2900000, "Prefill", [
    ("Whole prompt in one pass.", {"size": 22}),
    ("Large matmuls. Compute-bound.", {"size": 22}),
    ("Tensor cores busy, memory bus quiet.", {"size": 18, "color": GREY})], fill=BRAND_LIGHT, head_size=32)
card(s, LM + cw2 + 400000, BODY_TOP, cw2, 2900000, "Decode", [
    ("One token per step.", {"size": 22}),
    ("Re-reads the entire KV cache each step. Memory-bandwidth-bound.", {"size": 22}),
    ("Memory bus busy, tensor cores waiting.", {"size": 18, "color": GREY})], fill=BRAND_LIGHT, head_size=32)
# util bar: both phases read 100%
by = BODY_TOP + 3200000
rect(s, LM, by, CW, 700000, LIGHT, radius=0.3)
rect(s, LM, by, CW, 700000, RGBColor(0xE8, 0xB4, 0xC4), radius=0.3)
text_box(s, LM, by, CW, 700000, [[("DCGM_FI_DEV_GPU_UTIL ", M(18, DARK, True)), ("= 100% in both phases", {"size": 18, "bold": True})]],
         anchor=MSO_ANCHOR.MIDDLE, align=PP_ALIGN.CENTER)
strap(s, "One busy thread reads as 100%. The counter has no idea which phase you are in.", y=by + 850000, size=22, h=700000)

# ================================================================ 7. the Elastic numbers
s = content_slide(
    "Three profiler counters, same second.",
    src="Measured on vLLM by Elastic Observability Labs (2025): DCGM_FI_PROF_GR_ENGINE_ACTIVE 99.8%, PIPE_TENSOR_ACTIVE 16.6%, DRAM_ACTIVE 80.4%. MFU/MBU vocabulary: Lightbits, The Utilization Illusion.",
    note=("Elastic measured a vLLM server with the DCGM profiling fields, not the NVML util counter. Graphics engine "
          "active 99.8%, which is the profiler's version of 'busy'. Tensor cores, the units doing the actual matmuls, "
          "active 16.6% of the time. Memory bus 80.4%. The card is not computing, it is waiting on memory. "
          "Bandwidth-bound, not compute-saturated, and 'utilisation' never said which. If you need more throughput "
          "here you quantize before you buy hardware. People serving models are starting to borrow the training "
          "world's MFU and MBU vocabulary for exactly this reason."))
tw = (CW - 2 * 300000) // 3
for i, (num, name, what, col) in enumerate([
        ("99.8%", "GR_ENGINE_ACTIVE", "the profiler's 'busy'", GREY),
        ("16.6%", "PIPE_TENSOR_ACTIVE", "tensor cores doing matmuls", RED),
        ("80.4%", "DRAM_ACTIVE", "memory bus", AMBER)]):
    x = LM + i * (tw + 300000)
    rect(s, x, BODY_TOP, tw, 3000000, LIGHT)
    text_box(s, x, BODY_TOP, tw, 3000000, [
        (num, {"size": 72, "bold": True, "color": col, "align": PP_ALIGN.CENTER, "space_after": 2}),
        (name, {**M(16, DARK, True), "align": PP_ALIGN.CENTER, "space_after": 0}),
        (what, {"size": 16, "color": GREY, "align": PP_ALIGN.CENTER, "space_after": 0})],
        anchor=MSO_ANCHOR.MIDDLE, align=PP_ALIGN.CENTER)
strap(s, "Bandwidth-bound, not compute-saturated, and \"utilisation\" never said which.", y=BODY_TOP + 3200000, size=21)
text_box(s, LM, BODY_TOP + 4000000, CW, 700000, [
    ("The counter on your dashboard is the least informative one the hardware offers. Serving teams are borrowing "
     "MFU and MBU (model FLOPs and bandwidth utilisation) from the training world to say so.", {"size": 16, "color": GREY, "space_after": 0})])

# ================================================================ 8. counters
s = content_slide(
    "Counters that lie, counters you can trust.",
    src="DCGM field IDs: docs.nvidia.com/datacenter/dcgm. PROF_* fields need a profiling-capable GPU and DCGM >= 2.x. SM_OCCUPANCY is a ratio: resident warps over the SM maximum.",
    note=("Vocabulary slide, the one to photograph. Left: what most GPU dashboards show. Right: what describes the work. "
          "SM_ACTIVE says how much of the compute is busy, SM_OCCUPANCY what share of the warps an SM can hold are "
          "resident, DRAM_ACTIVE whether you are bandwidth-bound, PIPE_TENSOR_ACTIVE whether the tensor cores are doing "
          "the matmuls. Then the punchline: none of these counters know what a token is. Queue depth, KV cache "
          "pressure, tokens per second. The serving framework owns those, the silicon doesn't."))
cw2 = (CW - 400000) // 2
rect(s, LM, BODY_TOP, cw2, 2900000, RED_LIGHT)
text_box(s, LM + 150000, BODY_TOP + 100000, cw2 - 300000, 500000, [("Misleading on an inference server", {"size": 18, "bold": True, "color": RED, "space_after": 0})])
for i, (n, why) in enumerate([("DCGM_FI_DEV_GPU_UTIL", "any kernel = busy"),
                              ("DCGM_FI_DEV_FB_USED", "pre-allocated, flat"),
                              ("nvidia-smi Volatile GPU-Util", "same as GPU_UTIL")]):
    y = BODY_TOP + 700000 + i * 700000
    chip(s, LM + 150000, y, 3200000, 480000, n, fill=WHITE, color=RED, size=14, font=MONO)
    text_box(s, LM + 3450000, y, cw2 - 3600000, 480000, [(why, {"size": 16, "space_after": 0})], anchor=MSO_ANCHOR.MIDDLE)
rx = LM + cw2 + 400000
rect(s, rx, BODY_TOP, cw2, 2900000, GREEN_LIGHT)
text_box(s, rx + 150000, BODY_TOP + 100000, cw2 - 300000, 500000, [("Meaningful", {"size": 18, "bold": True, "color": GREEN, "space_after": 0})])
for i, (n, why) in enumerate([("DCGM_FI_PROF_SM_ACTIVE", "share of SMs doing work"),
                              ("DCGM_FI_PROF_SM_OCCUPANCY", "resident warps / SM maximum"),
                              ("DCGM_FI_PROF_DRAM_ACTIVE", "bandwidth-bound?"),
                              ("DCGM_FI_PROF_PIPE_TENSOR_ACTIVE", "tensor cores in use")]):
    y = BODY_TOP + 650000 + i * 540000
    chip(s, rx + 150000, y, 3400000, 440000, n, fill=WHITE, color=GREEN, size=12, font=MONO)
    text_box(s, rx + 3650000, y, cw2 - 3800000, 440000, [(why, {"size": 15, "space_after": 0})], anchor=MSO_ANCHOR.MIDDLE)
strap(s, "And none of them know what a token is.", y=BODY_TOP + 3050000, size=28)
text_box(s, LM, BODY_TOP + 3800000, CW, 600000, [
    ("Queue depth, KV cache pressure, tokens per second. The serving framework owns those, the silicon doesn't.", {"size": 18, "space_after": 0})])

# ================================================================ 9. the join key (diagram)
s = content_slide(
    "The pod is the join key.",
    src="K8s 1.35: Dynamic Resource Allocation is stable; dcgm-exporter 4.8.4 adds pod_uid and ResourceSlice mapping because the device-plugin mapping breaks under DRA. Same join key, new plumbing.",
    note=("Section 3, 2.5 min for slides 9 to 11. If you take one architectural idea home, take this one. DCGM knows "
          "which pod holds the GPU, via the kubelet pod-resources socket. Fluent Bit knows which pod wrote the log "
          "line. The OTel Collector stamps k8s.pod.name on every span. Nothing else is shared across the three. So you "
          "keep the pod name on every signal and you join at query time. Footnote for newer clusters: Kubernetes 1.35 "
          "made DRA stable and dcgm-exporter 4.8.4 added pod_uid tracking because the old device-plugin mapping breaks "
          "under DRA. The idea survives, the plumbing changes."))
bw, bh = 3100000, 1500000
cx, cy = W // 2, BODY_TOP + 2500000
srcs = [("DCGM", "dcgm-exporter --kubernetes", "exported_pod", LM, BODY_TOP + 200000),
        ("Serving log", "Fluent Bit kubernetes filter", "pod_name", W // 2 - bw // 2, BODY_TOP + 200000),
        ("Traces", "OTel Collector k8sattributes", "k8s.pod.name", W - LM - bw, BODY_TOP + 200000)]
for head, sub, lab, x, y in srcs:
    rect(s, x, y, bw, bh, LIGHT)
    text_box(s, x, y, bw, bh, [
        (head, {"size": 24, "bold": True, "color": BRAND, "align": PP_ALIGN.CENTER, "space_after": 2}),
        (sub, {"size": 14, "color": GREY, "align": PP_ALIGN.CENTER, "space_after": 6}),
        (lab, {**M(15, DARK, True), "align": PP_ALIGN.CENTER, "space_after": 0})], anchor=MSO_ANCHOR.MIDDLE, align=PP_ALIGN.CENTER)
    arrow(s, x + bw // 2, y + bh, cx + (x + bw // 2 - cx) // 6, cy - 600000, color=BRAND, width=3)
kx, ky, kw, kh = cx - 2400000, cy - 600000, 4800000, 1200000
rect(s, kx, ky, kw, kh, BRAND, radius=0.5)
text_box(s, kx, ky, kw, kh, [("pod_name", {**M(40, WHITE, True), "align": PP_ALIGN.CENTER, "space_after": 0})],
         anchor=MSO_ANCHOR.MIDDLE, align=PP_ALIGN.CENTER)
text_box(s, LM, cy + 800000, CW, 700000, [
    ("Stamp it on every metric, log record and span. Join at query time. Nothing else is common to all three.",
     {"size": 20, "bold": True, "align": PP_ALIGN.CENTER, "space_after": 0})], align=PP_ALIGN.CENTER)

# ================================================================ 10. signal 1: DCGM per pod
s = content_slide(
    "Signal 1: DCGM, per pod.",
    src="dcgm-exporter --kubernetes reads /var/lib/kubelet/pod-resources. EKS Auto Mode: standalone dcgm-exporter, not the GPU Operator (slide 18).",
    note=("dcgm-exporter in Kubernetes mode asks the kubelet which pod owns each GPU and stamps exported_pod on every "
          "counter. Two things: which pod is on which GPU, and whether that silicon is busy. It does not give you why. "
          "On EKS Auto Mode you run it standalone as a DaemonSet with the pod-resources hostPath, because the GPU "
          "Operator is not supported there. Seven counters in counters.csv, and that smallness is deliberate, next slide."))
px, py, pw, ph = panel(s, LM, BODY_TOP, 6200000, 2750000, "panel-4.png")
callout(s, px + pw - 2500000, py + int(ph * 0.2), 2300000, 560000, "SM active, per pod", fill=BRAND, size=16)
text_box(s, LM, BODY_TOP + 2900000, 6200000, 1500000, [
    [("--kubernetes=true  ", M(14, DARK, True)), ("asks the kubelet who owns each GPU", {"size": 15})],
    [("ENABLE_POD_LABELS=false  ", M(14, DARK, True)), ("keep the join key, nothing else (next slide)", {"size": 15, "space_after": 0})]],
    space_after=6)
rx = LM + 6200000 + 300000; rw = CW - 6200000 - 300000
rect(s, rx, BODY_TOP, rw, 2050000, GREEN_LIGHT)
text_box(s, rx + 100000, BODY_TOP + 80000, rw - 200000, 1900000, [
    ("What it tells you", {"size": 18, "bold": True, "color": GREEN}),
    ("Which pod holds which GPU", {"size": 16, "bullet": True}),
    ("Whether the silicon is busy (SM_ACTIVE, DRAM_ACTIVE)", {"size": 16, "bullet": True}),
    ("Power, temperature, pool size", {"size": 16, "bullet": True, "space_after": 0})], space_after=5)
rect(s, rx, BODY_TOP + 2200000, rw, 2300000, RED_LIGHT)
text_box(s, rx + 100000, BODY_TOP + 2280000, rw - 200000, 2150000, [
    ("What it has no idea about", {"size": 18, "bold": True, "color": RED}),
    ("Why the GPU is busy", {"size": 16, "bullet": True}),
    ("How many requests are queued", {"size": 16, "bullet": True}),
    ("Whether the KV cache is full", {"size": 16, "bullet": True}),
    ("Anything about tokens", {"size": 16, "bullet": True, "space_after": 0})], space_after=5)

# ================================================================ 11. cardinality
s = content_slide(
    "Keep the join key. Drop every other label.",
    src="Series math: Last9, 10,000 GPUs, one TSDB (last9.io/blog/10-000-gpus-one-tsdb-cardinality-at-gpu-scale). Our rig: 7 counters, pod labels off, exported_pod is the only identity.",
    note=("The first thing we broke was Prometheus. dcgm-exporter can copy every pod label onto every counter "
          "(ENABLE_POD_LABELS). Do the arithmetic at fleet scale: 1,000 nodes, 8 GPUs each, the default 60 or so "
          "counters, three label dimensions, and you are at 1.4 million series before a single pod or job label is "
          "added. Pod names churn on every rollout, so every label you add multiplies by churn. Here's the rule that "
          "fixed it. Identity on logs, stable dimensions on metrics, join at query time. We ship seven counters and one "
          "identity label, and we join on the fixed part of the pod name, never the hash."))
text_box(s, LM, BODY_TOP, CW, 700000, [("1,000 nodes  x  8 GPUs  x  60 counters  x  3 labels", {**M(22, GREY), "align": PP_ALIGN.CENTER, "space_after": 0})],
         align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
text_box(s, LM, BODY_TOP + 650000, CW, 1500000, [("= 1.4M series", {"size": 96, "bold": True, "color": BRAND, "align": PP_ALIGN.CENTER, "space_after": 0})],
         align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
text_box(s, LM, BODY_TOP + 2150000, CW, 500000, [("before a single pod or job label. Every label you add multiplies by pod churn.", {"size": 18, "color": GREY, "align": PP_ALIGN.CENTER, "space_after": 0})],
         align=PP_ALIGN.CENTER)
tw = (CW - 2 * 300000) // 3
for i, (a, b) in enumerate([("Identity", "on logs"), ("Stable dimensions", "on metrics"), ("Join", "at query time")]):
    x = LM + i * (tw + 300000)
    rect(s, x, BODY_TOP + 2900000, tw, 1300000, LIGHT)
    text_box(s, x, BODY_TOP + 2900000, tw, 1300000, [
        (a, {"size": 26, "bold": True, "color": BRAND, "align": PP_ALIGN.CENTER, "space_after": 0}),
        (b, {"size": 20, "align": PP_ALIGN.CENTER, "space_after": 0})], anchor=MSO_ANCHOR.MIDDLE, align=PP_ALIGN.CENTER)
text_box(s, LM, BODY_TOP + 4350000, CW, 500000, [[("ENABLE_POD_LABELS=true", M(16, RED, True)), ("  is how you find out.", {"size": 16, "space_after": 0})]],
         align=PP_ALIGN.CENTER)

# ================================================================ 12. the raw log line
def logline(slide, x, y, w, h, label, parts):
    text_box(slide, x, y, w, 400000, [(label, {"size": 15, "color": GREY, "space_after": 0})])
    runs = []
    for t, hot in parts:
        runs.append((t, M(15, BRAND if hot else GREY, hot)))
    text_box(slide, x, y + 380000, w, h, [runs], fill=LIGHT, margin=150000, anchor=MSO_ANCHOR.MIDDLE)

s = content_slide(
    "Signal 2: the serving log is the telemetry.",
    src="vLLM V1 engine, vllm/v1/metrics/loggers.py: one stats line every 10 s while the engine is busy (DEBUG level when idle). Both lines from the live rig.",
    note=("Section 4 is the centre of the talk, 6 min for slides 12 to 15. This is one line of vLLM stdout, every 10 "
          "seconds while it is busy. Read the fields: prompt and generation throughput, running requests, waiting "
          "requests, KV cache usage, prefix cache hit rate. When the scheduler starts evicting work because the cache "
          "is full, a Preemptions field appears. Top line: the over-provisioned pod under steady load. Bottom: the "
          "constrained pod during the demo load. Six facts about the inference work, and not one of them shows up in a "
          "GPU counter."))
logline(s, LM, BODY_TOP, CW, 950000, "vllm-overprov, steady load", [
    ("INFO [loggers.py] Engine 000: Avg prompt throughput: 1180.2 tokens/s, Avg generation throughput: ", False),
    ("4711.7 tokens/s", True), (", ", False), ("Running: 15 reqs", True), (", ", False), ("Waiting: 0 reqs", True), (", ", False),
    ("GPU KV cache usage: 0.1%", True), (", Prefix cache hit rate: 0.0%", False)])
logline(s, LM, BODY_TOP + 1650000, CW, 1150000, "vllm-constrained, saturating load", [
    ("INFO [loggers.py] Engine 000: Avg prompt throughput: 9810.4 tokens/s, Avg generation throughput: ", False),
    ("17227.0 tokens/s", True), (", ", False), ("Running: 76 reqs", True), (", ", False), ("Waiting: 116 reqs", True), (", ", False),
    ("Preemptions: 41", True), (", ", False), ("GPU KV cache usage: 99.6%", True), (", Prefix cache hit rate: 0.0%", False)])
cy = BODY_TOP + 3450000
cwid = (CW - 5 * 150000) // 6
for i, t in enumerate(["tokens/s", "running", "waiting", "KV cache %", "prefix hits", "preemptions"]):
    chip(s, LM + i * (cwid + 150000), cy, cwid, 520000, t, fill=BRAND, size=16)
strap(s, "Six facts about the inference work, and not one of them shows up in a GPU counter.", y=cy + 700000, size=22)

# ================================================================ 13. Lua pipeline
s = content_slide(
    "Fifteen lines of Lua turn it into per-pod metrics.",
    src="Fluent Bit 5.1. Full filter and pipeline config in the repo. vLLM native metrics: docs.vllm.ai/en/latest/design/metrics",
    note=("Fluent Bit tails the container log, the kubernetes filter attaches the pod name (that is the join key "
          "arriving), the Lua filter does five string.match calls and promotes pod_name to a top-level field, grep "
          "drops everything that is not a stats line, log_to_metrics turns the fields into gauges labelled by "
          "pod_name, and prometheus_exporter serves them on :2021 for the same Prometheus that scrapes DCGM. "
          "Now the honest caveat, say it before someone asks: vLLM exposes all of this natively on /metrics, "
          "kv_cache_usage_perc, num_requests_waiting, request_queue_time_seconds. vLLM is the demo vehicle. This is "
          "for everything that doesn't have it: custom servers, vendor images you can't touch, log-only pipelines, "
          "the TGI or Triton you inherited. Same fifteen lines, different regex."))
stages = ["tail", "kubernetes", "lua", "grep", "log_to_metrics", "prometheus_exporter"]
subs = ["container log", "+ pod_name", "5 x string.match", "stats lines only", "fields -> gauges", ":2021"]
n = len(stages); gap = 180000; sw = (CW - (n - 1) * gap) // n; sy = BODY_TOP + 150000; sh_ = 900000
for i, (st, sb) in enumerate(zip(stages, subs)):
    x = LM + i * (sw + gap)
    hot = st in ("kubernetes", "lua")
    rect(s, x, sy, sw, sh_, BRAND if hot else LIGHT, radius=0.15)
    text_box(s, x, sy, sw, sh_, [(st, {**M(15 if len(st) < 14 else 10, WHITE if hot else DARK, True), "align": PP_ALIGN.CENTER, "space_after": 2}),
                                 (sb, {"size": 12, "color": WHITE if hot else GREY, "align": PP_ALIGN.CENTER, "space_after": 0})],
             anchor=MSO_ANCHOR.MIDDLE, align=PP_ALIGN.CENTER, margin=30000)
    if i < n - 1:
        arrow(s, x + sw, sy + sh_ // 2, x + sw + gap, sy + sh_ // 2, color=GREY, width=2)
# pod_name token travelling along the pipeline
dot_y = sy + sh_ + 230000
for i in range(1, n):
    x = LM + i * (sw + gap) + sw // 2
    d = s.shapes.add_shape(MSO_SHAPE.OVAL, Emu(x - 90000), Emu(dot_y), Emu(180000), Emu(180000))
    d.fill.solid(); d.fill.fore_color.rgb = BRAND; d.line.fill.background()
    st = d._element.find(qn("p:style"));  d._element.remove(st) if st is not None else None
text_box(s, LM + sw + gap, dot_y + 200000, CW - sw - gap, 350000, [("pod_name rides along from the kubernetes filter onwards: the join key", {"size": 13, "color": BRAND, "space_after": 0})])
# the one line that matters
ly = BODY_TOP + 2000000
rect(s, LM, ly, CW, 1250000, LIGHT)
text_box(s, LM, ly, CW, 1250000, [
    [("record[", M(17, GREY)), ("\"kv_cache_usage_pct\"", M(17, BRAND, True)), ("] =", M(17, GREY))],
    [("    tonumber(string.match(line, ", M(17, GREY)), ("\"KV cache usage:%s*([%d%.]+)%%\"", M(17, BLUE, True)), ("))", M(17, GREY))],
    [("record[", M(17, GREY)), ("\"pod_name\"", M(17, BRAND, True)), ("] = record[\"kubernetes\"][\"pod_name\"]", M(17, GREY)),
     ("   -- the join key", M(17, GREEN, True))]], anchor=MSO_ANCHOR.MIDDLE, margin=200000, space_after=4)
text_box(s, LM, ly + 1300000, CW, 400000, [[("field name", M(13, BRAND, True)), ("   ", M(13)), ("pattern against the log line", M(13, BLUE, True)),
                                             ("   ", M(13)), ("identity from the kubernetes filter", M(13, GREEN, True)),
                                             ("      13 more lines in the repo, same shape.", {"size": 13, "color": GREY})]])
# metric names
my = ly + 1780000
for i, m in enumerate(["vllm_log_kv_cache_usage_pct{pod_name}", "vllm_log_waiting_reqs{pod_name}", "vllm_log_preemptions_total{pod_name}"]):
    chip(s, LM + i * ((CW - 300000) // 3 + 150000), my, (CW - 300000) // 3, 440000, m, fill=WHITE, color=BRAND, size=12, font=MONO)
rect(s, LM, my + 600000, CW, 750000, BRAND_LIGHT)
text_box(s, LM, my + 600000, CW, 750000, [[("Honest caveat: ", {"size": 15, "bold": True, "color": BRAND}),
    ("vLLM already exposes these on /metrics; it is our demo vehicle. The filter is for everything that doesn't: custom servers, vendor images you can't touch, log-only pipelines, the TGI or Triton you inherited. Same lines, different regex.", {"size": 15})]],
    anchor=MSO_ANCHOR.MIDDLE, margin=150000)

# ================================================================ 14. demo set-up (anchor)
s = content_slide(
    "Live: two pods, one is about to run out.",
    note=("LIVE DEMO anchor, 1 min. Start the loadgen before this slide (kubectl apply loadgen-job.yaml), it runs 12 "
          "minutes. Tell the room what to watch before switching: row 1 is DCGM, row 2 is what the log knows. The "
          "constrained pod is about to get long prompts at concurrency 128. Watch KV cache and waiting on row 2 while "
          "FB_USED on row 1 does not move. Then switch to Grafana."))
cw2 = (CW - 400000) // 2
for i, (name, mem, role, col, fill) in enumerate([
        ("vllm-constrained", "gpu-mem-util 0.15, 3.6 GB", "gets the saturating load", BLUE, RGBColor(0xE4, 0xEE, 0xF8)),
        ("vllm-overprov", "gpu-mem-util 0.90, 20.5 GB", "steady load, the control", GREEN, GREEN_LIGHT)]):
    x = LM + i * (cw2 + 400000)
    rect(s, x, BODY_TOP, cw2, 2200000, fill)
    text_box(s, x, BODY_TOP, cw2, 2200000, [
        (name, {**M(28, col, True), "align": PP_ALIGN.CENTER, "space_after": 4}),
        (mem, {"size": 18, "align": PP_ALIGN.CENTER, "space_after": 2}),
        (role, {"size": 18, "color": GREY, "align": PP_ALIGN.CENTER, "space_after": 0})], anchor=MSO_ANCHOR.MIDDLE, align=PP_ALIGN.CENTER)
text_box(s, LM, BODY_TOP + 2450000, CW, 500000, [("facebook/opt-125m on both  ·  long prompts, concurrency 128, 12 minutes", {"size": 16, "color": GREY, "align": PP_ALIGN.CENTER, "space_after": 0})], align=PP_ALIGN.CENTER)
rect(s, LM, BODY_TOP + 3050000, CW, 1500000, BRAND)
text_box(s, LM, BODY_TOP + 3050000, CW, 1500000, [
    ("Watch two rows.", {"size": 22, "bold": True, "color": WHITE, "align": PP_ALIGN.CENTER, "space_after": 6}),
    ("Row 1, DCGM: GPU memory stays flat.   Row 2, the log: KV cache and waiting take off.", {"size": 20, "color": WHITE, "align": PP_ALIGN.CENTER, "space_after": 0})],
    anchor=MSO_ANCHOR.MIDDLE, align=PP_ALIGN.CENTER)

# ================================================================ 15. demo result
s = content_slide(
    "KV cache 100%. Memory counter: unchanged.",
    src="Rig numbers, Oct 6 2026 16:56 to 17:08. Queue time rises before 'waiting' is visibly non-zero: Elastic Observability Labs, tuning vLLM Prometheus metrics (2025).",
    note=("Backup for the live demo, or the recap after it. Left, DCGM: FB_USED 3.6 GB before, during and after on the "
          "constrained pod. Right, the log: KV cache goes to 100% within a minute of the load and stays there, waiting "
          "climbs to around 100, p95 queue time jumps from 0.3 s to 4.8 s. Be precise: GPU_UTIL and SM_ACTIVE did go up "
          "on the constrained pod, so DCGM does say busy. What it can't say: one pod has zero headroom and 100 requests "
          "queued, the other has 99% of its cache sitting free. Queue time moves first, waiting confirms."))
cw2 = (CW - 300000) // 2
px, py, pw, ph = panel(s, LM, BODY_TOP, cw2, 3000000, "panel-2.png")
callout(s, px + pw - 2500000, py + int(ph * 0.58), 2300000, 700000, "3.6 GB before, 3.6 GB after", fill=BLUE, size=16)
text_box(s, LM, BODY_TOP + 3050000, cw2, 400000, [("DCGM: GPU memory used", {"size": 16, "bold": True, "color": GREY, "align": PP_ALIGN.CENTER, "space_after": 0})], align=PP_ALIGN.CENTER)
px, py, pw, ph = panel(s, LM + cw2 + 300000, BODY_TOP, cw2, 3000000, "panel-6.png")
callout(s, px + 300000, py + int(ph * 0.3), 1900000, 800000, "100%", "KV cache, constrained pod", fill=BRAND, size=36)
text_box(s, LM + cw2 + 300000, BODY_TOP + 3050000, cw2, 400000, [("The log: KV cache usage, per pod", {"size": 16, "bold": True, "color": GREY, "align": PP_ALIGN.CENTER, "space_after": 0})], align=PP_ALIGN.CENTER)
tw = (CW - 2 * 300000) // 3
for i, (num, lab) in enumerate([("4.8 s", "p95 queue time, was 0.3 s"), ("~100", "requests waiting"), ("0.2%", "KV cache on the over-provisioned pod")]):
    x = LM + i * (tw + 300000)
    rect(s, x, BODY_TOP + 3550000, tw, 1000000, LIGHT)
    text_box(s, x, BODY_TOP + 3550000, tw, 1000000, [
        (num, {"size": 30, "bold": True, "color": BRAND, "align": PP_ALIGN.CENTER, "space_after": 0}),
        (lab, {"size": 14, "color": GREY, "align": PP_ALIGN.CENTER, "space_after": 0})], anchor=MSO_ANCHOR.MIDDLE, align=PP_ALIGN.CENTER)
strap(s, "Queue time first. Waiting confirms. GPU memory never moved.", y=5700000, size=22, h=600000)

# ================================================================ 16. traces
s = content_slide(
    "Signal 3: a slow span with a pod name.",
    src="vLLM --otlp-traces-endpoint -> OTel Collector (k8sattributes) -> Jaeger. Tracing was removed in the V1 rewrite and reinstated in vllm PR #20372: needs vLLM >= 0.10.2 (rig: 0.30).",
    note=("Section 5, 2.5 min. vLLM emits one span per request natively, you point it at the OTel Collector. The "
          "k8sattributes processor stamps k8s.pod.name on every span by looking up the source IP. A slow span by itself "
          "is just a fact. The same slow span, on the pod whose KV cache hit 100% that second, with 116 requests "
          "waiting, is a diagnosis. Gotcha worth saying out loud: tracing disappeared in the vLLM V1 engine rewrite and "
          "came back in PR 20372, so you need 0.10.2 or later; if your traces vanished after an upgrade, that is why. "
          "Keep this honest: we show traces from the serving path, one span per request. Multi-hop waterfalls are a "
          "flag away, not the point. Bonus in 0.30: start-up spans (load weights, allocate KV cache, compile graph)."))
px, py, pw, ph = picture(s, LM, BODY_TOP, CW, 2350000, "jaeger-trace-detail.png")
callout(s, px + pw - 2900000, py + 150000, 2700000, 600000, "llm_request  5.73 s", fill=BRAND, size=20)
cw3 = (CW - 2 * 200000) // 3
for i, (k, v, col) in enumerate([("k8s.pod.name", "vllm-constrained-7f9fdfc497-2mjzz", BRAND),
                                 ("gen_ai.latency.time_in_queue", "0.61 s", BLUE),
                                 ("gen_ai.latency.time_in_model_decode", "5.33 s", AMBER)]):
    x = LM + i * (cw3 + 200000)
    rect(s, x, BODY_TOP + 2500000, cw3, 1100000, LIGHT)
    text_box(s, x, BODY_TOP + 2500000, cw3, 1100000, [
        (k, {**M(13, GREY), "align": PP_ALIGN.CENTER, "space_after": 2}),
        (v, {**M(18 if len(v) < 20 else 14, col, True), "align": PP_ALIGN.CENTER, "space_after": 0})], anchor=MSO_ANCHOR.MIDDLE, align=PP_ALIGN.CENTER)
text_box(s, LM, BODY_TOP + 3750000, CW, 500000, [[("--otlp-traces-endpoint=grpc://otel-collector.observability:4317", M(14, GREY)),
                                                  ("   plus   ", {"size": 14, "color": GREY}), ("k8sattributes", M(14, GREY, True)), (" on the Collector. That is the whole wiring.", {"size": 14, "color": GREY})]],
         align=PP_ALIGN.CENTER)
strap(s, "A slow span by itself is just a fact. The same span on the pod whose KV cache hit 100% that second is a diagnosis.", y=5350000, size=20, h=900000)

# ================================================================ 17. the join (climax)
s = content_slide(
    "Same pod name. Three sources. One row.",
    src="Grafana dashboard uid gpu-inference-obs, variable $pod matches exported_pod (DCGM), pod_name (Fluent Bit) and pod (vLLM, traces). Constrained pod, 16:52 to 17:09.",
    note=("Section 6, 2 min. This is the slide the whole talk builds to. One Grafana dashboard, one pod variable, three "
          "data sources that never heard of each other. Point at the red line, 16:56, when the load hits. KV cache "
          "pegs, queue time jumps from 0.3 to 4.8 seconds, and the DCGM row above is unchanged. That is the black box "
          "opened. No new agent, no vendor, no eBPF. Just the pod name on every signal, and the discipline to keep it there."))
ph_each = 1560000; gapy = 60000; pwid = 7280000
names = [("panel-2-wide.png", "DCGM memory", "flat", GREY), ("panel-6-wide.png", "KV cache (log)", "100%", BRAND), ("panel-10-wide.png", "queue time p95 (/metrics)", "0.3 s to 4.8 s", RED)]
x0 = LM; ytop = BODY_TOP
for i, (f, lab, word, col) in enumerate(names):
    y = ytop + i * (ph_each + gapy)
    px, py, pw, ph = panel(s, x0, y, pwid, ph_each, f)
    rect(s, px + pw + 150000, py, CW - pw - 150000, ph, LIGHT)
    text_box(s, px + pw + 150000, py, CW - pw - 150000, ph, [
        (word, {"size": 26 if len(word) < 8 else 18, "bold": True, "color": col, "align": PP_ALIGN.CENTER, "space_after": 2}),
        (lab, {"size": 13, "color": GREY, "align": PP_ALIGN.CENTER, "space_after": 0})], anchor=MSO_ANCHOR.MIDDLE, align=PP_ALIGN.CENTER)
# red line at 16:56 (x fraction measured on the wide capture: plot spans ~1.5% to 96% of width, 16:52..17:09 -> 16:56 is 4/17)
frac = 0.025 + (0.99 - 0.025) * (4 / 17)
lx = px + int(pw * frac)
yend = ytop + 3 * ph_each + 2 * gapy
vline(s, lx, ytop - 40000, yend + 40000, color=RED, width=2.5)
chip(s, lx + 80000, ytop + 60000, 1350000, 300000, "16:56  load hits", fill=RED, size=11)
strap(s, "No new agent, no vendor, no eBPF. Just the pod name on every signal, and the discipline to keep it there.", y=yend + 60000, size=16, h=420000)

# ================================================================ 18. what broke
s = content_slide(
    "What silently broke along the way.",
    src="EKS Auto Mode GPU support: docs.aws.amazon.com/eks/latest/userguide/device-management-nvidia-dra-device-plugin.html. Two more gotchas (Fluent Bit Kube_Tag_Prefix, 1-GPU RollingUpdate) in the repo README.",
    note=("0.5 min, one gotcha. EKS Auto Mode ships NVIDIA drivers and the device plugin on its GPU AMIs, but does "
          "not support the GPU Operator or the NVIDIA DRA driver. Every DCGM how-to assumes the Operator. So: "
          "standalone dcgm-exporter DaemonSet, pod-resources hostPath, SYS_ADMIN cap. Two more in the repo if asked: "
          "Fluent Bit's kubernetes filter needs Kube_Tag_Prefix to match the tail tag exactly or the pod name silently "
          "never arrives, and a 1-GPU pod on a NodePool capped at two GPUs can never RollingUpdate, use Recreate."))
tw = (CW - 2 * 300000) // 3
for i, (head, body, col, fill) in enumerate([
        ("What we expected", "GPU Operator installs DCGM on EKS Auto Mode, like every how-to says.", GREY, LIGHT),
        ("What happened", "Auto Mode supports neither the GPU Operator nor the NVIDIA DRA driver. Drivers and device plugin come with the AMI.", RED, RED_LIGHT),
        ("Fix", "Standalone dcgm-exporter DaemonSet, pod-resources hostPath, SYS_ADMIN. Seven counters.", GREEN, GREEN_LIGHT)]):
    x = LM + i * (tw + 300000)
    card(s, x, BODY_TOP + 300000, tw, 2600000, head, [(body, {"size": 18})], fill=fill, head_color=col, head_size=22)
    if i < 2:
        arrow(s, x + tw + 40000, BODY_TOP + 1600000, x + tw + 260000, BODY_TOP + 1600000, color=GREY, width=2.5)
text_box(s, LM, BODY_TOP + 3300000, CW, 1200000, [
    ("Also in the repo: Fluent Bit Kube_Tag_Prefix must match the tail tag or the join key arrives empty; a 1-GPU pod on a 2-GPU NodePool never finishes a RollingUpdate, use Recreate.",
     {"size": 15, "color": GREY, "space_after": 0})])

# ================================================================ 19. where this is going
s = content_slide(
    "Where this is going.",
    src="llm-d on AWS: aws.amazon.com/blogs/machine-learning/introducing-disaggregated-inference-on-aws-powered-by-llm-d. Gateway API Inference Extension: github.com/kubernetes-sigs/gateway-api-inference-extension. CloudWatch OTel Container Insights for EKS (June 2026).",
    note=("1 min. Three things before someone asks 'isn't this solved'. One: disaggregated prefill/decode (llm-d, NVIDIA "
          "Dynamo, llm-d-aws) splits a request across two pods, KV cache shipped between them over NIXL and EFA; AWS "
          "reports up to 70% more tokens per second at concurrency 128. The pod is no longer the whole request, so the "
          "join key becomes request id plus pod. Two: the Gateway API Inference Extension's endpoint picker and Dynamo's "
          "KV-aware router consume exactly these signals, queue depth and KV cache, to route. The join is moving from "
          "Grafana into the router. Three: AWS's OTel-native Container Insights, June 2026, packages signal 1 for EKS out "
          "of the box. Signals 2 and 3 are still yours to wire. Out of scope today, ask me after: XID/ECC/thermal faults, "
          "output quality, eBPF GPU profiling, Dynamo internals."))
tw = (CW - 2 * 300000) // 3
steps = [("Today", "Join in Grafana", "Pod name on every signal, one dashboard variable.", LIGHT, GREY),
         ("Disaggregated prefill / decode", "Join key = request id + pod", "llm-d, Dynamo, llm-d-aws: one request, two pods, KV cache over NIXL / EFA. Up to +70% tokens/s at concurrency 128.", BRAND_LIGHT, BRAND),
         ("Routers consume the signals", "Join leaves Grafana", "Gateway API Inference Extension endpoint picker and Dynamo's KV-aware router route on queue depth and KV cache %.", BRAND, WHITE)]
for i, (head, sub, body, fill, col) in enumerate(steps):
    x = LM + i * (tw + 300000)
    rect(s, x, BODY_TOP + 200000, tw, 2900000, fill)
    text_box(s, x + 80000, BODY_TOP + 280000, tw - 160000, 2750000, [
        (head, {"size": 20, "bold": True, "color": col if fill != BRAND else WHITE, "space_after": 2}),
        (sub, {"size": 17, "bold": True, "color": DARK if fill != BRAND else WHITE, "space_after": 10}),
        (body, {"size": 15, "color": DARK if fill != BRAND else WHITE, "space_after": 0})], margin=120000)
    if i < 2:
        arrow(s, x + tw + 40000, BODY_TOP + 1650000, x + tw + 260000, BODY_TOP + 1650000, color=BRAND, width=3)
rect(s, LM, BODY_TOP + 3350000, CW, 1000000, LIGHT)
text_box(s, LM, BODY_TOP + 3350000, CW, 1000000, [
    [("Signal 1 is becoming a checkbox. ", {"size": 16, "bold": True}),
     ("CloudWatch OTel-native Container Insights for EKS (June 2026) wires DCGM into OTel with pod labels and a PromQL endpoint. Signals 2 and 3 are still yours to wire.", {"size": 16})]],
    anchor=MSO_ANCHOR.MIDDLE, margin=150000)

# ================================================================ 20. steal this
s = content_slide(
    "Steal this for your cluster.",
    src="Original session design: [original author, AWS]. Reproduced clean-room on EKS Auto Mode; all configs in the repo.",
    note=("1 min. Three counters, one filter, one rule, that's the whole kit. SM_ACTIVE instead of GPU_UTIL. KV cache "
          "percent and queue time from the serving framework, by log or by /metrics, whichever you have. Pod name on "
          "every signal, nothing else on the metrics. Everything in the repo deploys with one terraform apply on EKS "
          "Auto Mode. Attribution: this session was designed by [original author]; we rebuilt it from the abstract and "
          "broke different things along the way."))
tw = (CW - 2 * 300000) // 3
cols = [("3 counters", [("DCGM_FI_PROF_SM_ACTIVE", "instead of GPU_UTIL"), ("KV cache %", "log or /metrics"), ("queue time p95", "then waiting")]),
        ("1 filter", [("15 lines of Lua", "+ log_to_metrics"), ("change the regex", "keep the pipeline"), ("works for", "TGI, Triton, anything that logs")]),
        ("1 rule", [("pod name", "on every signal"), ("identity on logs", "stable dimensions on metrics"), ("join", "at query time")])]
for i, (head, items) in enumerate(cols):
    x = LM + i * (tw + 300000)
    rect(s, x, BODY_TOP, tw, 4300000, LIGHT)
    text_box(s, x, BODY_TOP + 100000, tw, 900000, [(head, {"size": 40, "bold": True, "color": BRAND, "align": PP_ALIGN.CENTER, "space_after": 0})], align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    for j, (a, b) in enumerate(items):
        y = BODY_TOP + 1150000 + j * 1000000
        rect(s, x + 150000, y, tw - 300000, 850000, WHITE)
        text_box(s, x + 150000, y, tw - 300000, 850000, [
            (a, {**(M(16, DARK, True) if i == 0 and j == 0 else {"size": 18, "bold": True}), "align": PP_ALIGN.CENTER, "space_after": 0}),
            (b, {"size": 14, "color": GREY, "align": PP_ALIGN.CENTER, "space_after": 0})], anchor=MSO_ANCHOR.MIDDLE, align=PP_ALIGN.CENTER)

# ================================================================ 21. repo + QR
s = prs.slides.add_slide(L_TITLE)
notes(s, ("Thank the room, point at the repo, ask for feedback via the CNCF QR. Q&A. Likely questions: 'why not just "
          "scrape vLLM /metrics' (answered on slide 13, repeat it), 'what about MIG or time-slicing' (dcgm-exporter 4.5+ has "
          "per-process metrics, narrows but does not close the gap), 'SGLang / TGI field names' (same technique, verify "
          "the regex against your log line), 'hardware faults' (fourth signal class, out of scope)."))
text_box(s, LM, 1500000, 7200000, 3600000, [
    ("Thank you.", {"size": 44, "bold": True, "color": WHITE, "space_after": 18}),
    ("github.com/danilosilvase/", {"size": 26, "bold": True, "color": WHITE, "space_after": 0}),
    ("gpu-observability-kubecon-na-2026", {"size": 26, "bold": True, "color": WHITE, "space_after": 18}),
    ("Danilo Souza, AWS Professional Services", {"size": 18, "color": WHITE, "space_after": 2}),
    ("Henrique Santana, AWS", {"size": 18, "color": WHITE, "space_after": 18}),
    ("Scan to rate this session.", {"size": 18, "color": WHITE, "space_after": 0})], anchor=MSO_ANCHOR.MIDDLE)
qs = 3600000
rect(s, W - LM - qs - 200000, (H - qs) // 2 - 200000, qs + 400000, qs + 400000, WHITE, radius=0.05)
picture(s, W - LM - qs, (H - qs) // 2, qs, qs, "cncf-feedback-qr.png")

# speaker scripts (single source: speaker_notes.py)
from speaker_notes import NOTES
for idx, text in NOTES.items():
    prs.slides[idx - 1].notes_slide.notes_text_frame.text = text

prs.save(OUT)
print(f"saved {OUT} with {len(prs.slides)} slides")
