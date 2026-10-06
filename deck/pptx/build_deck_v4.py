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


def strike(slide, x1, y1, x2, y2, color=RED, width=3.0):
    """Plain line, no arrowhead: used to cross something out."""
    c = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Emu(x1), Emu(y1), Emu(x2), Emu(y2))
    c.line.color.rgb = color; c.line.width = Pt(width)
    st = c._element.find(qn("p:style"))
    if st is not None: c._element.remove(st)
    return c


def fade_in(slide, shapes, duration_ms=700):
    """Click-triggered fade entrance. One shape or a list; one click per shape, single sequence."""
    if not isinstance(shapes, (list, tuple)):
        shapes = [shapes]
    nid = 3
    clicks = []
    for shape in shapes:
        sid = shape.shape_id
        a, b, c, d, e = nid, nid + 1, nid + 2, nid + 3, nid + 4
        nid += 5
        clicks.append(f"""<p:par><p:cTn id="{a}" fill="hold"><p:stCondLst><p:cond delay="indefinite"/></p:stCondLst><p:childTnLst>
     <p:par><p:cTn id="{b}" fill="hold"><p:stCondLst><p:cond delay="0"/></p:stCondLst><p:childTnLst>
      <p:par><p:cTn id="{c}" presetID="10" presetClass="entr" presetSubtype="0" fill="hold" grpId="0" nodeType="clickEffect">
       <p:stCondLst><p:cond delay="0"/></p:stCondLst><p:childTnLst>
        <p:set><p:cBhvr><p:cTn id="{d}" dur="1" fill="hold"><p:stCondLst><p:cond delay="0"/></p:stCondLst></p:cTn>
         <p:tgtEl><p:spTgt spid="{sid}"/></p:tgtEl><p:attrNameLst><p:attrName>style.visibility</p:attrName></p:attrNameLst></p:cBhvr>
         <p:to><p:strVal val="visible"/></p:to></p:set>
        <p:animEffect transition="in" filter="fade"><p:cBhvr><p:cTn id="{e}" dur="{duration_ms}"/>
         <p:tgtEl><p:spTgt spid="{sid}"/></p:tgtEl></p:cBhvr></p:animEffect>
       </p:childTnLst></p:cTn></p:par>
     </p:childTnLst></p:cTn></p:par>
    </p:childTnLst></p:cTn></p:par>""")
    builds = "".join(f'<p:bldP spid="{sh.shape_id}" grpId="0"/>' for sh in shapes)
    xml = f"""<p:timing xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
      xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
  <p:tnLst><p:par><p:cTn id="1" dur="indefinite" restart="never" nodeType="tmRoot"><p:childTnLst>
   <p:seq concurrent="1" nextAc="seek"><p:cTn id="2" dur="indefinite" nodeType="mainSeq"><p:childTnLst>
    {"".join(clicks)}
   </p:childTnLst></p:cTn><p:prevCondLst><p:cond evt="onPrev" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:prevCondLst>
   <p:nextCondLst><p:cond evt="onNext" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:nextCondLst></p:seq>
  </p:childTnLst></p:cTn></p:par></p:tnLst>
  <p:bldLst>{builds}</p:bldLst>
</p:timing>"""
    old = slide._element.find(qn("p:timing"))
    if old is not None: slide._element.remove(old)
    slide._element.append(etree.fromstring(xml))


# ---------------------------------------------------------------- 2. title slide (template)
s2 = prs.slides[1]
for sh in s2.shapes:
    if sh.has_text_frame and "Senior Delivery Consultant" in sh.text_frame.text:
        for par, txt in zip(sh.text_frame.paragraphs,
                            ["Danilo Souza, AWS Professional Services",
                             "Henrique Santana, AWS Support",
                             "Observability Day North America, Salt Lake City, 9 November 2026"]):
            if par.runs:
                par.runs[0].text = txt
                for r in par.runs[1:]:
                    r._r.getparent().remove(r._r)
# show, do not tell: the thesis as two chips instead of a spoken sentence
chip(s2, 729046, 5100000, 3000000, 560000, "GPU dashboard = ?", fill=WHITE, color=RED, size=18)
chip(s2, 729046 + 3300000, 5100000, 3400000, 560000, "One log line = answer", fill=WHITE, color=GREEN, size=18)


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
    "Utilisation alone tells you nothing.",
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
    "Memory usage is a config value, not a warning.",
    src="Live rig, Oct 6 2026: two vLLM pods, facebook/opt-125m, EKS Auto Mode, g5.xlarge (A10G 24 GB).",
    note=("Section 2 starts here, 4 min for slides 5 to 8. Every serious LLM server pre-allocates its memory pool "
          "at start-up: weights plus activation workspace plus the KV cache, capped by --gpu-memory-utilization. "
          "On our tiny demo model the weights are small, so the pool is effectively KV cache. The framebuffer counter "
          "jumps to the configured fraction in the first 30 seconds and never moves again, idle or melting. "
          "Constrained pod at 0.15 shows 3.6 GB, over-provisioned at 0.90 shows 20.5 GB, both perfectly flat. "
          "The one with less memory is the one that will get into trouble, and this counter cannot tell you that."))
# show, do not tell: the chart carries the point, the five bullets are spoken only
px, py, pw, ph = panel(s, LM, BODY_TOP, CW, 3900000, "panel-2.png")
callout(s, px + pw - 2500000, py + int(ph * 0.12), 2300000, 640000, "20.5 GB, flat", "gpu-mem-util 0.90", fill=GREEN, size=20)
callout(s, px + pw - 2500000, py + int(ph * 0.64), 2300000, 640000, "3.6 GB, flat", "gpu-mem-util 0.15", fill=BLUE, size=20)
text_box(s, LM, 5200000, CW, 350000, [("DCGM_FI_DEV_FB_USED", {**M(17, GREY), "align": PP_ALIGN.CENTER, "space_after": 0})],
         align=PP_ALIGN.CENTER)
strap(s, "Sized once at start-up. Flat forever, including the one about to fall over.", y=5600000, size=24, h=600000)

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
# show, do not tell: the same 100% stamped on two opposite realities
for i in range(2):
    chip(s, LM + i * (cw2 + 400000) + cw2 - 2550000, BODY_TOP + 2250000, 2400000, 520000,
         "GPU_UTIL 100%", fill=RED, size=18)
# util bar: the counter that cannot tell them apart
by = BODY_TOP + 3200000
rect(s, LM, by, CW, 700000, RGBColor(0xE8, 0xB4, 0xC4), radius=0.3)
text_box(s, LM, by, CW, 700000, [("DCGM_FI_DEV_GPU_UTIL", {**M(20, DARK, True), "align": PP_ALIGN.CENTER})],
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
pill = chip(s, kx, ky, kw, kh, "pod_name", fill=BRAND, color=WHITE, size=40, font=MONO)
# show, do not tell: the join itself, not just the convergence
where = chip(s, cx - 2100000, cy + 750000, 4200000, 560000, 'WHERE pod_name = $pod',
             fill=WHITE, color=BRAND, size=18, font=MONO)
where.line.color.rgb = BRAND; where.line.width = Pt(1.25)
text_box(s, LM, cy + 1450000, CW, 700000, [
    ("Stamp it on every metric, log record and span. Join at query time. Nothing else is common to all three.",
     {"size": 20, "bold": True, "align": PP_ALIGN.CENTER, "space_after": 0})], align=PP_ALIGN.CENTER)
fade_in(s, [pill, where])

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
LW = 8400000
text_box(s, LM, BODY_TOP, LW, 700000, [("1,000 nodes  x  8 GPUs  x  60 counters  x  3 labels", {**M(18, GREY), "align": PP_ALIGN.CENTER, "space_after": 0})],
         align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
big = text_box(s, LM, BODY_TOP + 650000, LW, 1500000, [("= 1.4M series", {"size": 88, "bold": True, "color": BRAND, "align": PP_ALIGN.CENTER, "space_after": 0})],
               align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
text_box(s, LM, BODY_TOP + 2150000, LW, 500000, [("before a single pod or job label. Every label you add multiplies by pod churn.", {"size": 18, "color": GREY, "align": PP_ALIGN.CENTER, "space_after": 0})],
         align=PP_ALIGN.CENTER)
# show, do not tell: one pod name times churn, exploding into a dot cloud
rx = LM + LW + 200000; rw = CW - LW - 200000
chip(s, rx + (rw - 1500000) // 2, BODY_TOP + 100000, 1500000, 440000, "pod_name", fill=LIGHT, color=DARK, size=16, font=MONO)
text_box(s, rx, BODY_TOP + 580000, rw, 350000, [("x every rollout", {"size": 16, "color": GREY, "align": PP_ALIGN.CENTER, "space_after": 0})],
         align=PP_ALIGN.CENTER)
arrow(s, rx + rw // 2, BODY_TOP + 950000, rx + rw // 2, BODY_TOP + 1180000, color=GREY, width=2)
cloud = [(0.10, 0.08, 150000), (0.42, 0.02, 190000), (0.74, 0.11, 130000), (0.26, 0.26, 170000),
         (0.58, 0.22, 140000), (0.86, 0.33, 160000), (0.05, 0.45, 120000), (0.37, 0.48, 180000),
         (0.68, 0.52, 140000), (0.18, 0.66, 150000), (0.50, 0.72, 130000), (0.80, 0.70, 170000),
         (0.32, 0.88, 120000), (0.62, 0.90, 150000)]
for fx, fy, d in cloud:
    ox = rx + int(fx * (rw - 250000))
    oy = BODY_TOP + 1280000 + int(fy * 820000)
    o = s.shapes.add_shape(MSO_SHAPE.OVAL, Emu(ox), Emu(oy), Emu(d), Emu(d))
    o.fill.solid(); o.fill.fore_color.rgb = BRAND; o.line.fill.background()
    stl = o._element.find(qn("p:style"))
    if stl is not None: o._element.remove(stl)
text_box(s, rx, BODY_TOP + 2150000, rw, 500000, [("series, per label", {"size": 16, "color": BRAND, "align": PP_ALIGN.CENTER, "space_after": 0})],
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
fade_in(s, big)

# ================================================================ 12. the serving log, as numbers
s = content_slide(
    "The log says six things the GPU can't.",
    src="vLLM V1 engine, vllm/v1/metrics/loggers.py: one stats line every 10 s while the engine is busy (DEBUG level when idle). Numbers from the live rig.",
    note=("Section 4 is the centre of the talk, 9:30 to 16:30 for slides 12 to 15. One line of vLLM stdout, every 10 "
          "seconds while it is busy. Read the raw line aloud, do not put it on the slide. Over-provisioned pod: 4,700 "
          "tokens a second, nothing waiting, cache at 0.1%. Constrained pod, same model: 17,000 tokens a second, 116 "
          "waiting, cache at 99.6%, and a Preemptions field that only appears once the scheduler starts evicting work. "
          "Six facts about the inference work, and not one of them shows up in a GPU counter."))
rows = [("vllm-overprov, steady load", "4,711 tok/s  ·  0 waiting  ·  0.1% KV cache", GREY),
        ("vllm-constrained, saturating load", "17,227 tok/s  ·  116 waiting  ·  99.6% KV cache", RED)]
shapes = []
for i, (lab, txt, col) in enumerate(rows):
    y = BODY_TOP + 150000 + i * 1750000
    text_box(s, LM, y, CW, 400000, [(lab, {"size": 16, "color": GREY, "space_after": 0})])
    shapes.append(chip(s, LM, y + 480000, CW, 1100000, txt, fill=col, size=32))
text_box(s, LM, BODY_TOP + 3700000, CW, 450000, [
    ("tokens/s  ·  running  ·  waiting  ·  KV cache %  ·  prefix hits  ·  preemptions",
     {**M(16, GREY), "align": PP_ALIGN.CENTER, "space_after": 0})], align=PP_ALIGN.CENTER)
strap(s, "Six facts about the inference work, and not one of them shows up in a GPU counter.", y=5350000, size=22)
fade_in(s, shapes[1])

# ================================================================ 13. Lua pipeline
s = content_slide(
    "Fifteen lines of Lua. The pod name rides along.",
    src="Fluent Bit 5.1. Full filter and pipeline config in the repo. vLLM native metrics: docs.vllm.ai/en/latest/design/metrics",
    note=("Fluent Bit tails the container log, the kubernetes filter attaches the pod name (that is the join key "
          "arriving), five Lua string.match calls turn fields into numbers, grep keeps only stats lines, "
          "log_to_metrics makes gauges labelled by pod, and prometheus_exporter serves them on :2021 for the same "
          "Prometheus that scrapes DCGM. Then the honest caveat, spoken not shown: vLLM already exposes most of this "
          "on /metrics; this filter is for the servers that don't, same lines, different regex."))
stages = ["tail", "kubernetes", "lua", "grep", "log_to_metrics", "prometheus_exporter"]
subs = ["container log", "+ pod_name", "5 x string.match", "stats lines only", "fields -> gauges", ":2021"]
n = len(stages); gap = 180000; sw = (CW - (n - 1) * gap) // n; sy = BODY_TOP + 1000000; sh_ = 1900000
for i, (st, sb) in enumerate(zip(stages, subs)):
    x = LM + i * (sw + gap)
    hot = st in ("kubernetes", "lua")
    rect(s, x, sy, sw, sh_, BRAND if hot else LIGHT, radius=0.15)
    text_box(s, x, sy, sw, sh_, [(st, {**M(18 if len(st) < 10 else (12 if len(st) < 18 else 10), WHITE if hot else DARK, True), "align": PP_ALIGN.CENTER, "space_after": 6}),
                                 (sb, {"size": 14, "color": WHITE if hot else GREY, "align": PP_ALIGN.CENTER, "space_after": 0})],
             anchor=MSO_ANCHOR.MIDDLE, align=PP_ALIGN.CENTER, margin=30000)
    if i < n - 1:
        arrow(s, x + sw, sy + sh_ // 2, x + sw + gap, sy + sh_ // 2, color=GREY, width=2)
# pod_name token travelling along the pipeline
dot_y = sy + sh_ + 300000
for i in range(1, n):
    x = LM + i * (sw + gap) + sw // 2
    d = s.shapes.add_shape(MSO_SHAPE.OVAL, Emu(x - 110000), Emu(dot_y), Emu(220000), Emu(220000))
    d.fill.solid(); d.fill.fore_color.rgb = BRAND; d.line.fill.background()
    st = d._element.find(qn("p:style"));  d._element.remove(st) if st is not None else None
text_box(s, LM, dot_y + 320000, CW, 500000, [
    ("pod_name rides along from the kubernetes filter onward: the join key",
     {"size": 20, "bold": True, "color": BRAND, "align": PP_ALIGN.CENTER, "space_after": 0})], align=PP_ALIGN.CENTER)
text_box(s, LM, dot_y + 850000, CW, 400000, [
    ("For serving engines without a /metrics endpoint. vLLM exposes most of this natively; same pipeline, different regex.",
     {"size": 16, "color": GREY, "align": PP_ALIGN.CENTER, "space_after": 0})], align=PP_ALIGN.CENTER)

# ================================================================ 14. demo set-up (anchor)
s = content_slide(
    "Live: two pods, one is about to run out.",
    note=("Demo signpost, 12:15 to 13:00, then the live demo runs 13:00 to 16:00. Nothing is typed on stage. Tell the "
          "room what to watch before switching: row 1 is DCGM, row 2 is what the log knows. Henrique drives Grafana, "
          "Danilo narrates. Hard stop at 16:30."))
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
tw = (CW - 3 * 220000) // 4
# fourth chip is the honesty beat: DCGM did say busy, it just could not say why
for i, (num, lab, col) in enumerate([("4.8 s", "p95 queue time, was 0.3 s", BRAND), ("~100", "requests waiting", BRAND),
                                     ("0.2%", "KV cache, over-prov pod", BRAND),
                                     ("90%", "SM_ACTIVE: busy, but blind", GREY)]):
    x = LM + i * (tw + 220000)
    rect(s, x, BODY_TOP + 3550000, tw, 900000, LIGHT)
    text_box(s, x, BODY_TOP + 3550000, tw, 900000, [
        (num, {"size": 30, "bold": True, "color": col, "align": PP_ALIGN.CENTER, "space_after": 0}),
        (lab, {"size": 14, "color": GREY, "align": PP_ALIGN.CENTER, "space_after": 0})], anchor=MSO_ANCHOR.MIDDLE, align=PP_ALIGN.CENTER)
strap(s, "Queue time first. Waiting confirms. GPU memory never moved.", y=5780000, size=22, h=550000)

# ================================================================ 16. traces
s = content_slide(
    "Signal 3: a slow span with a pod name.",
    src="vLLM --otlp-traces-endpoint -> OTel Collector (k8sattributes) -> Jaeger. Tracing was removed in the V1 rewrite and reinstated in vllm PR #20372: needs vLLM >= 0.10.2 (rig: 0.30). gen_ai.* attributes follow OTel GenAI semconv, status Development, names can still change.",
    note=("Section 5, 16:30 to 17:30. vLLM emits one span per request natively, you point it at the OTel Collector. The "
          "k8sattributes processor stamps k8s.pod.name on every span by looking up the source IP. A slow span by itself "
          "is just a fact. The same slow span, on the pod whose KV cache hit 100% that second, with 116 requests "
          "waiting, is a diagnosis. Gotcha worth saying out loud: tracing disappeared in the vLLM V1 engine rewrite and "
          "came back in PR 20372, so you need 0.10.2 or later; if your traces vanished after an upgrade, that is why. "
          "Keep this honest: we show traces from the serving path, one span per request. Multi-hop waterfalls are a "
          "flag away, not the point. Bonus in 0.30: start-up spans (load weights, allocate KV cache, compile graph)."))
px, py, pw, ph = picture(s, LM, BODY_TOP, CW, 2350000, "jaeger-trace-detail.png")
callout(s, px + pw - 3500000, py + 150000, 3300000, 600000, "llm_request  5.73 s", fill=BRAND, size=20)
# show, do not tell: the fact plus the context that makes it a diagnosis
chip(s, px + pw - 3500000, py + 830000, 3300000, 520000, "KV cache this second: 99.6%", fill=RED, size=16)
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
    note=("Section 6, 17:30 to 19:30. This is the slide the whole talk builds to. One Grafana dashboard, one pod variable, three "
          "data sources that never heard of each other. Point at the red line, 16:56, when the load hits. KV cache "
          "pegs, queue time jumps from 0.3 to 4.8 seconds, and the DCGM row above is unchanged. That is the black box "
          "opened. No new agent, no vendor, no eBPF. Just the pod name on every signal, and the discipline to keep it there."))
ph_each = 1500000; gapy = 60000; pwid = 7280000
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
opened = chip(s, LM, yend + 60000, 1650000, 460000, "Opened.", fill=BRAND, size=20)
strap(s, "No new agent, no vendor, no eBPF. Just the pod name on every signal.",
      y=yend + 60000, size=18, h=460000)
s.shapes[-1].left = Emu(LM + 1800000); s.shapes[-1].width = Emu(CW - 1800000)
fade_in(s, opened)

# ================================================================ 18. what broke
s = content_slide(
    "What silently broke along the way.",
    src="EKS Auto Mode GPU support: docs.aws.amazon.com/eks/latest/userguide/device-management-nvidia-dra-device-plugin.html. Two more gotchas (Fluent Bit Kube_Tag_Prefix, 1-GPU RollingUpdate) in the repo README.",
    note=("20 seconds, one gotcha. EKS Auto Mode ships NVIDIA drivers and the device plugin on its GPU AMIs, but does "
          "not support the GPU Operator or the NVIDIA DRA driver. Every DCGM how-to assumes the Operator. So: "
          "standalone dcgm-exporter DaemonSet, pod-resources hostPath, SYS_ADMIN cap. Two more in the repo if asked: "
          "Fluent Bit's kubernetes filter needs Kube_Tag_Prefix to match the tail tag exactly or the pod name silently "
          "never arrives, and a 1-GPU pod on a NodePool capped at two GPUs can never RollingUpdate, use Recreate."))
tw = (CW - 2 * 300000) // 3
for i, (head, body, col, fill) in enumerate([
        ("What we expected", "Every DCGM how-to assumes the GPU Operator. Check your platform's driver model before you follow one.", GREY, LIGHT),
        ("What happened", "EKS Auto Mode supports neither the GPU Operator nor the NVIDIA DRA driver. Drivers and device plugin ship with the AMI.", RED, RED_LIGHT),
        ("Fix", "Standalone dcgm-exporter DaemonSet, pod-resources hostPath, SYS_ADMIN. Seven counters.", GREEN, GREEN_LIGHT)]):
    x = LM + i * (tw + 300000)
    card(s, x, BODY_TOP + 300000, tw, 2600000, head, [(body, {"size": 18})], fill=fill, head_color=col, head_size=22)
    if i == 0:
        # show, do not tell: the thing we expected, crossed out
        bw_ = 2400000
        bx = x + (tw - bw_) // 2; byy = BODY_TOP + 2280000
        gpuop = chip(s, bx, byy, bw_, 460000, "GPU Operator", fill=WHITE, color=DARK, size=16)
        gpuop.line.color.rgb = MID; gpuop.line.width = Pt(1.0)
        strike(s, bx, byy + 420000, bx + bw_, byy + 40000, color=RED, width=3.0)
    if i < 2:
        arrow(s, x + tw + 40000, BODY_TOP + 1600000, x + tw + 260000, BODY_TOP + 1600000, color=GREY, width=2.5)
text_box(s, LM, BODY_TOP + 3300000, CW, 1200000, [
    ("Also in the repo: Fluent Bit Kube_Tag_Prefix must match the tail tag or the join key arrives empty; a 1-GPU pod on a 2-GPU NodePool never finishes a RollingUpdate, use Recreate.",
     {"size": 15, "color": GREY, "space_after": 0})])

# ================================================================ 19. where this is going
s = content_slide(
    "The join key is moving into the router.",
    src="llm-d on AWS: aws.amazon.com/blogs/machine-learning/introducing-disaggregated-inference-on-aws-powered-by-llm-d. Gateway API Inference Extension: github.com/kubernetes-sigs/gateway-api-inference-extension.",
    note=("40 seconds. Three beats, vendor-neutral first. Today the join happens in Grafana. Next, disaggregated "
          "serving splits one request across two pods, llm-d and Dynamo, so the join key becomes request id plus pod. "
          "Then the router itself consumes queue depth and KV cache to route traffic, Gateway API Inference Extension "
          "endpoint picker and Dynamo's KV-aware router, and the join leaves Grafana entirely."))
tw = (CW - 2 * 300000) // 3
steps = [("Today: join in Grafana", "one pod, one request", "PromQL on pod_name", LIGHT, DARK, GREY),
         ("Next: join key = request id + pod", "prefill and decode on different pods", "llm-d, NVIDIA Dynamo", BRAND_LIGHT, BRAND, BRAND),
         ("Then: router consumes the join", "routes on queue depth and KV cache", "Gateway API Inference Extension", BRAND, WHITE, WHITE)]
for i, (head, sub, who, fill, col, subcol) in enumerate(steps):
    x = LM + i * (tw + 300000)
    rect(s, x, BODY_TOP + 600000, tw, 2600000, fill)
    text_box(s, x + 80000, BODY_TOP + 600000, tw - 160000, 2600000, [
        (head, {"size": 26, "bold": True, "color": col, "align": PP_ALIGN.CENTER, "space_after": 10}),
        (sub, {"size": 16, "color": subcol, "align": PP_ALIGN.CENTER, "space_after": 4}),
        (who, {"size": 14, "color": subcol, "align": PP_ALIGN.CENTER, "space_after": 0, "font": MONO})],
        anchor=MSO_ANCHOR.MIDDLE, align=PP_ALIGN.CENTER, margin=120000)
    if i < 2:
        arrow(s, x + tw + 40000, BODY_TOP + 1900000, x + tw + 260000, BODY_TOP + 1900000, color=BRAND, width=3)
# the join key migrating, left to right
chip(s, LM, BODY_TOP + 3550000, 1900000, 480000, "join key", fill=LIGHT, color=BRAND, size=18, font=MONO)
arrow(s, LM + 2050000, BODY_TOP + 3790000, LM + CW - 100000, BODY_TOP + 3790000, color=BRAND, width=3)

# ================================================================ 20. steal this
s = content_slide(
    "Steal this for your cluster.",
    src="Reproduced clean-room on EKS Auto Mode; all configs in the repo.",
    note=("30 seconds. Three counters, one filter, one rule, that's the whole kit. SM_ACTIVE instead of GPU_UTIL. KV cache "
          "percent and queue time from the serving framework, by log or by /metrics, whichever you have. Pod name on "
          "every signal, nothing else on the metrics. Everything in the repo deploys with one terraform apply on EKS "
          "Auto Mode, and the repo pointer is the next slide."))
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
# show, do not tell: the closing claim as a badge
chip(s, (W - 2900000) // 2, 5700000, 2900000, 560000, "0 new agents", fill=BRAND, size=24)

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
