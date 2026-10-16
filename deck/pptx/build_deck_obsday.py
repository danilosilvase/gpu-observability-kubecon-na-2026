"""Observability Day NA 2026 deck, built on the branded template (assets/obsday-na-2026-template.pptx).
Content = TALK-DECISIONS.md S1-S10. Usage: python3 build_deck_obsday.py ../kubecon-obsday-2026.pptx"""
import sys, os, copy
from pptx import Presentation
from pptx.util import Inches as I, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR

HERE = os.path.dirname(os.path.abspath(__file__)); A = lambda f: os.path.join(HERE, "assets", f)
MAG, INK, GREY, LIGHT, LINE = "991346", "1F1F24", "6B6B76", "F3F3F5", "D5D5DB"
RED, BLUE, WHITE, CODEBG = "D7263D", "2F6FDB", "FFFFFF", "F1F1F4"
REPO = "github.com/danilosilvase/gpu-observability-kubecon-na-2026"
rgb = lambda h: RGBColor.from_string(h)

prs = Presentation(A("obsday-na-2026-template.pptx"))
L_TITLE = next(l for l in prs.slide_layouts if l.name == "Title Slide")
L_BODY = next(l for l in prs.slide_layouts if l.name == "Title and Content")

def text(s, x, y, w, h, runs, size=20, color=INK, bold=False, italic=False, align=PP_ALIGN.LEFT,
         anchor=MSO_ANCHOR.TOP, font="Arial", spacing=1.1):
    """runs: str, or list of paragraphs; a paragraph is a str or a list of (text, {overrides})."""
    tb = s.shapes.add_textbox(I(x), I(y), I(w), I(h)); tf = tb.text_frame
    tf.word_wrap = True; tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = I(0.05); tf.margin_top = tf.margin_bottom = I(0.02)
    paras = runs if isinstance(runs, list) else [runs]
    for i, para in enumerate(paras):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align; p.line_spacing = spacing
        for t, o in ([(para, {})] if isinstance(para, str) else para):
            r = p.add_run(); r.text = t; f = r.font
            f.name = o.get("font", font); f.size = Pt(o.get("size", size)); f.bold = o.get("bold", bold)
            f.italic = o.get("italic", italic); f.color.rgb = rgb(o.get("color", color))
    return tb

def box(s, x, y, w, h, fill=None, line=None, shape=MSO_SHAPE.ROUNDED_RECTANGLE, lw=1.5, radius=0.08):
    sh = s.shapes.add_shape(shape, I(x), I(y), I(w), I(h))
    if shape == MSO_SHAPE.ROUNDED_RECTANGLE: sh.adjustments[0] = radius
    if fill: sh.fill.solid(); sh.fill.fore_color.rgb = rgb(fill)
    else: sh.fill.background()
    if line: sh.line.color.rgb = rgb(line); sh.line.width = Pt(lw)
    else: sh.line.fill.background()
    sh.shadow.inherit = False
    return sh

def body_slide(title):
    s = prs.slides.add_slide(L_BODY)
    text(s, 0.44, 0.0, 10.0, 1.06, title, size=34 if len(title) <= 38 else 28, color=WHITE, bold=True, anchor=MSO_ANCHOR.MIDDLE)
    return s

def notes(s, t): s.notes_slide.notes_text_frame.text = t

# ---- animation: native PowerPoint entrance effects (p:timing). One "step" = one click (or auto, after the previous). ----
from lxml import etree
NS = 'xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"'
mark = lambda s: len(s.shapes)                      # remember where a group of shapes starts
since = lambda s, m: list(s.shapes)[m:]             # shapes added after the mark
FX = {"fade": (10, 0, "fade"), "wipe": (22, 8, "wipe(left)"), "up": (42, 0, None), "zoom": (53, 16, None)}
def _effect(ids, sp, fx, delay, dur, node):
    pid, sub, flt = FX[fx]
    beh = ""
    if fx == "up":    # fade + rise a little
        beh = (f'<p:animEffect transition="in" filter="fade"><p:cBhvr><p:cTn id="{ids()}" dur="{dur}"/><p:tgtEl><p:spTgt spid="{sp}"/></p:tgtEl></p:cBhvr></p:animEffect>'
               f'<p:anim calcmode="lin" valueType="num"><p:cBhvr><p:cTn id="{ids()}" dur="{dur}" fill="hold"/><p:tgtEl><p:spTgt spid="{sp}"/></p:tgtEl>'
               f'<p:attrNameLst><p:attrName>ppt_y</p:attrName></p:attrNameLst></p:cBhvr><p:tavLst><p:tav tm="0"><p:val><p:strVal val="#ppt_y+0.05"/></p:val></p:tav>'
               f'<p:tav tm="100000"><p:val><p:strVal val="#ppt_y"/></p:val></p:tav></p:tavLst></p:anim>')
    elif fx == "zoom":
        beh = (f'<p:animEffect transition="in" filter="fade"><p:cBhvr><p:cTn id="{ids()}" dur="{dur}"/><p:tgtEl><p:spTgt spid="{sp}"/></p:tgtEl></p:cBhvr></p:animEffect>'
               + "".join(f'<p:anim calcmode="lin" valueType="num"><p:cBhvr><p:cTn id="{ids()}" dur="{dur}" fill="hold"/><p:tgtEl><p:spTgt spid="{sp}"/></p:tgtEl>'
                         f'<p:attrNameLst><p:attrName>{a}</p:attrName></p:attrNameLst></p:cBhvr><p:tavLst><p:tav tm="0"><p:val><p:strVal val="0"/></p:val></p:tav>'
                         f'<p:tav tm="100000"><p:val><p:strVal val="#{a}"/></p:val></p:tav></p:tavLst></p:anim>' for a in ("ppt_w", "ppt_h")))
    else:
        beh = f'<p:animEffect transition="in" filter="{flt}"><p:cBhvr><p:cTn id="{ids()}" dur="{dur}"/><p:tgtEl><p:spTgt spid="{sp}"/></p:tgtEl></p:cBhvr></p:animEffect>'
    return (f'<p:par><p:cTn id="{ids()}" presetID="{pid}" presetClass="entr" presetSubtype="{sub}" fill="hold" nodeType="{node}">'
            f'<p:stCondLst><p:cond delay="{delay}"/></p:stCondLst><p:childTnLst>'
            f'<p:set><p:cBhvr><p:cTn id="{ids()}" dur="1" fill="hold"><p:stCondLst><p:cond delay="0"/></p:stCondLst></p:cTn>'
            f'<p:tgtEl><p:spTgt spid="{sp}"/></p:tgtEl><p:attrNameLst><p:attrName>style.visibility</p:attrName></p:attrNameLst></p:cBhvr>'
            f'<p:to><p:strVal val="visible"/></p:to></p:set>{beh}</p:childTnLst></p:cTn></p:par>')
def animate(s, steps):
    """steps: list of (trigger, [(shapes, fx, stagger_ms, dur_ms), ...]); trigger 'click' or 'auto' (right after the previous step)."""
    n = [2]
    def ids(): n[0] += 1; return n[0]
    out = []
    for trig, groups in steps:
        effs, t, first = [], 0, True
        for shapes, fx, stagger, dur in groups:
            for sh in shapes:
                node = ("clickEffect" if trig == "click" else "afterEffect") if first else "withEffect"
                effs.append(_effect(ids, sh.shape_id, fx, t, dur, node)); first = False; t += stagger
        outer, inner = ids(), ids()
        out.append(f'<p:par><p:cTn id="{outer}" fill="hold"><p:stCondLst><p:cond delay="indefinite"/>'
                   + ('<p:cond evt="onBegin" delay="0"><p:tn val="2"/></p:cond>' if (trig == "auto" and not out) else '')
                   + f'</p:stCondLst><p:childTnLst><p:par><p:cTn id="{inner}" fill="hold"><p:stCondLst><p:cond delay="0"/></p:stCondLst>'
                   f'<p:childTnLst>{"".join(effs)}</p:childTnLst></p:cTn></p:par></p:childTnLst></p:cTn></p:par>')
    xml = (f'<p:timing {NS}><p:tnLst><p:par><p:cTn id="1" dur="indefinite" restart="never" nodeType="tmRoot"><p:childTnLst>'
           f'<p:seq concurrent="1" nextAc="seek"><p:cTn id="2" dur="indefinite" nodeType="mainSeq"><p:childTnLst>{"".join(out)}</p:childTnLst></p:cTn>'
           f'<p:prevCondLst><p:cond evt="onPrev" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:prevCondLst>'
           f'<p:nextCondLst><p:cond evt="onNext" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:nextCondLst></p:seq>'
           f'</p:childTnLst></p:cTn></p:par></p:tnLst></p:timing>')
    _insert(s, etree.fromstring(xml))
def fade_transition(s):
    _insert(s, etree.fromstring(f'<p:transition {NS} spd="med"><p:fade/></p:transition>'), before_timing=True)
def _insert(s, el, before_timing=False):
    sld = s._element
    for old in sld.findall(el.tag): sld.remove(old)
    ext = sld.find("{http://schemas.openxmlformats.org/presentationml/2006/main}extLst")
    tim = sld.find("{http://schemas.openxmlformats.org/presentationml/2006/main}timing")
    anchor = tim if (before_timing and tim is not None) else ext
    (anchor.addprevious(el) if anchor is not None else sld.append(el))

def foot(s, t): text(s, 0.6, 6.95, 12.0, 0.4, t, size=11, color=GREY)

# ---------- 0 cover (template), 1 title (template slide, retexted) ----------
cover, title_s = prs.slides[2], prs.slides[3]
for sh in title_s.shapes:
    if sh.has_text_frame and sh.text_frame.text.strip() == "Title":
        sh.top, sh.height = I(1.5), I(2.4); tf = sh.text_frame; tf.word_wrap = True
        tf.paragraphs[0].runs[0].text = "Inference Is a Black Box:"
        p = tf.add_paragraph(); r = p.add_run(); r.text = "How We Built GPU-Aware Observability with Fluent Bit and OpenTelemetry"
        tf.paragraphs[0].runs[0].font.size = Pt(48)
        r.font.size, r.font.bold, r.font.name, r.font.color.rgb = Pt(30), False, "Arial", rgb(WHITE)
    elif sh.has_text_frame and sh.text_frame.text.strip() == "Speaker Name":
        sh.top, sh.height = I(4.3), I(1.6); tf = sh.text_frame; tf.word_wrap = True
        tf.paragraphs[0].runs[0].text = "Henrique Santana, Principal Cloud Engineer, AWS"
        tf.paragraphs[0].runs[0].font.size = Pt(26)
        p = tf.add_paragraph(); r = p.add_run(); r.text = "Danilo Silva, Senior Delivery Consultant, AWS"
        r.font.size, r.font.italic, r.font.name, r.font.color.rgb = Pt(26), True, "Arial", rgb(WHITE)

# ---------- slide 1: the vote ----------
s = body_slide("Which one is in trouble?")
text(s, 0.6, 1.35, 10.5, 0.5, "Two vLLM pods. Same model, same GPU type, same traffic.", size=24, color=GREY)
m1 = mark(s); cardsA = []
for x, col, name, pct in ((0.6, RED, "Pod A", "8%"), (6.75, BLUE, "Pod B", "90%")):
    box(s, x, 2.0, 5.95, 2.65, fill=WHITE, line=col, lw=3)
    text(s, x + 0.35, 2.12, 5.3, 0.5, name, size=22, color=col, bold=True)
    text(s, x + 0.35, 2.55, 5.3, 1.35, pct, size=80, color=col, bold=True, spacing=0.9, anchor=MSO_ANCHOR.MIDDLE)
    text(s, x + 0.35, 4.05, 5.3, 0.5, "of GPU memory reserved for vLLM", size=20, color=INK)
    cardsA.append(since(s, m1)); m1 = mark(s)
m2 = mark(s)
text(s, 0.6, 4.95, 3.0, 0.5, "Hands up:", size=24, color=INK, bold=True)
for i, opt in enumerate(("8%", "90%", "both", "can't tell from here")):
    w = 3.4 if i == 3 else 2.35; x = 0.6 + sum((2.35 + 0.3) for _ in range(i))
    b = box(s, x, 5.5, w, 0.85, fill=LIGHT, line=LINE)
    text(s, x, 5.5, w, 0.85, opt, size=24, bold=True, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
vote = since(s, m2)
animate(s, [("click", [(cardsA[0], "up", 0, 500)]), ("click", [(cardsA[1], "up", 0, 500)]),
            ("click", [(vote[:1], "fade", 0, 300)] + [(vote[i:i + 2], "zoom", 180, 350) for i in range(1, len(vote), 2)])])

# ---------- slide 2: a setting, not a signal ----------
s = body_slide("GPU memory is a setting, not a signal")
tiles = (("CPU", "how busy the cores are"), ("Memory", "RAM the container uses"),
         ("Network", "bytes in and out"), ("Disk", "reads and writes"))
m1 = mark(s)
for i, (n, d) in enumerate(tiles):
    x = 0.6 + i * 2.45
    box(s, x, 1.95, 2.25, 1.9, fill=LIGHT, line=LINE)
    text(s, x + 0.2, 2.1, 1.9, 0.5, n, size=24, bold=True, color=GREY)
    text(s, x + 0.2, 2.7, 1.9, 1.2, d, size=17, color=GREY)
text(s, 0.6, 3.95, 9.6, 0.45, "Node and container resources. None of them sees the server's queue.", size=16, color=GREY, italic=True)
four = since(s, m1); m2 = mark(s)
x = 10.5
box(s, x, 1.95, 2.25, 1.9, fill=WHITE, line=MAG, lw=3)
text(s, x + 0.15, 2.1, 2.0, 0.5, "GPU memory", size=19, bold=True, color=MAG)
box(s, x + 0.25, 2.65, 1.75, 0.75, fill=LIGHT, line=None, shape=MSO_SHAPE.RECTANGLE)
gpu_tile = since(s, m2); m3 = mark(s)
ln = s.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, I(x + 0.25), I(2.75), I(x + 2.0), I(2.75)); ln.line.color.rgb = rgb(MAG); ln.line.width = Pt(4)
line_ = since(s, m3); m4 = mark(s)
mk = s.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, I(x + 1.62), I(2.62), I(x + 1.62), I(3.42)); mk.line.color.rgb = rgb("E8871E"); mk.line.width = Pt(2)
mk.line.dash_style = 4
text(s, x + 0.3, 3.1, 1.28, 0.3, "load starts", size=11, bold=True, color="E8871E", align=PP_ALIGN.RIGHT)
marker = since(s, m4); m5 = mark(s)
text(s, x + 0.3, 2.8, 1.28, 0.35, "92%, flat", size=14, bold=True, color=MAG)
text(s, x + 0.2, 3.42, 1.9, 0.4, "set at startup", size=16, color=INK)
flat_lbl = since(s, m5); m6 = mark(s)
text(s, 0.6, 4.75, 12.1, 1.2, [[("vLLM reserves 92% of GPU memory when it starts. ", {"bold": True}),
     ("Busy or idle, that number stays put. So the chart we page on can't tell a struggling server from a quiet one.", {})]],
     size=24, color=INK)
sentence2 = since(s, m6)
animate(s, [("click", [(four[i:i + 3], "up", 150, 400) for i in range(0, 12, 3)] + [(four[12:], "fade", 0, 400)]),
            ("click", [(gpu_tile, "zoom", 0, 400), (line_, "wipe", 0, 1400)]),
            ("click", [(marker, "fade", 0, 300)]), ("auto", [(flat_lbl, "fade", 0, 400)]),
            ("click", [(sentence2, "fade", 0, 500)])])
foot(s, "vLLM default: gpu_memory_utilization = 0.92 (vllm/config/cache.py, vLLM main, Oct 2026)")

# ---------- slide 3: the connection pool ----------
s = body_slide("What runs out first: room for requests in flight")
m1 = mark(s)
text(s, 0.6, 1.35, 5.6, 0.45, "One GPU, as vLLM uses it", size=20, bold=True, color=INK)
segs = ((1.2, "333338", "weights", WHITE), (3.4, MAG, "KV cache", WHITE), (0.9, LINE, "other", INK))
x = 0.6
for w, c, lab, tc in segs:
    box(s, x, 1.9, w, 0.9, fill=c, line=WHITE, shape=MSO_SHAPE.RECTANGLE, lw=2)
    text(s, x, 1.9, w, 0.9, lab, size=15, bold=True, color=tc, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE); x += w
gpu_bar = since(s, m1); m2 = mark(s)
text(s, 1.5, 2.85, 3.6, 0.7, "room for requests in flight. Its size is set by --gpu-memory-utilization",
     size=14, color=GREY, align=PP_ALIGN.CENTER)
gpu_cap = since(s, m2); m3 = mark(s)
text(s, 0.6, 3.75, 5.6, 0.45, "It behaves like a connection pool", size=20, bold=True, color=INK)
pool_t = since(s, m3); m4 = mark(s)
for i in range(6):
    box(s, 0.6 + i * 0.5, 4.35, 0.4, 0.55, fill=MAG, line=None, shape=MSO_SHAPE.RECTANGLE)
slots = since(s, m4); m5 = mark(s)
text(s, 0.6, 4.95, 3.0, 0.4, "all slots in use", size=14, color=GREY)
ar = s.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, I(4.0), I(4.62), I(3.65), I(4.62)); ar.line.color.rgb = rgb(GREY); ar.line.width = Pt(2.5)
ar.line._get_or_add_ln().append(copy.deepcopy(ar.line._get_or_add_ln().makeelement("{http://schemas.openxmlformats.org/drawingml/2006/main}tailEnd", {"type": "triangle"})))
full_lbl = since(s, m5); m6 = mark(s)
for i in range(5):
    box(s, 4.15 + i * 0.42, 4.45, 0.34, 0.34, fill=LIGHT, line=GREY, shape=MSO_SHAPE.OVAL, lw=1.5)
text(s, 4.1, 4.95, 2.3, 0.4, "waiting", size=14, color=GREY)
queue = since(s, m6); m7 = mark(s)
rows = (("Connection pool", "vLLM KV cache"), ("Pool size: you set it", "--gpu-memory-utilization"),
        ("Connections in use", "KV cache usage %"), ("Waiting for a connection", "Requests waiting"),
        ("Latency climbs, CPU looks fine", "Time to first token climbs, GPU memory flat"))
tbl = s.shapes.add_table(len(rows), 2, I(6.75), I(2.25), I(6.0), I(3.0)).table
tbl.columns[0].width, tbl.columns[1].width = I(2.65), I(3.35)
for r, (a, b) in enumerate(rows):
    for c, t in enumerate((a, b)):
        cell = tbl.cell(r, c); cell.fill.solid(); cell.fill.fore_color.rgb = rgb(MAG if r == 0 else (LIGHT if r % 2 else WHITE))
        cell.margin_left = cell.margin_right = I(0.12); cell.vertical_anchor = MSO_ANCHOR.MIDDLE
        p = cell.text_frame.paragraphs[0]; p.text = ""; run = p.add_run(); run.text = t
        run.font.size = Pt((14 if (c == 1 and r == 1) else 16) if r else 17); run.font.bold = (r == 0); run.font.name = "Consolas" if (c == 1 and r == 1) else "Arial"
        run.font.color.rgb = rgb(WHITE if r == 0 else INK)
table_ = since(s, m7); m8 = mark(s)
text(s, 0.6, 5.85, 12.1, 0.8, "vLLM tells you how full it is, every 10 seconds, in its log.", size=28, bold=True, color=MAG)
punch3 = since(s, m8)
# the queue: arrow + 5 waiting requests + label. Slots fill one by one, then the queue grows one by one.
animate(s, [("click", [(gpu_bar[:1], "fade", 0, 300)] + [(gpu_bar[i:i + 2], "wipe", 450, 600) for i in range(1, len(gpu_bar), 2)]),
            ("auto", [(gpu_cap, "fade", 0, 400)]),
            ("click", [(pool_t, "fade", 0, 300)] + [([sl], "zoom", 280, 260) for sl in slots] + [(full_lbl, "fade", 0, 300)]),
            ("click", [(queue[:1], "wipe", 300, 300)] + [([q], "zoom", 420, 300) for q in queue[1:6]] + [(queue[6:], "fade", 0, 300)]),
            ("click", [(table_, "fade", 0, 500)]), ("click", [(punch3, "up", 0, 500)])])
foot(s, "Intro structure inspired by Jimmy Song, jimmysong.io/blog/gpu-to-token-observability")

# ---------- bridge + hidden backup ----------
s = prs.slides.add_slide(L_TITLE)
text(s, 0.8, 1.3, 11.5, 0.6, "LIVE DEMO", size=24, bold=True, color="F4C2D4")
text(s, 0.8, 1.9, 11.5, 1.6, "Is 8% too low? Is 90% too high?", size=54, bold=True, color=WHITE)
m1 = mark(s)
for i, st in enumerate(("1  GPU", "2  Log", "3  Trace", "4  Answer")):
    x = 0.8 + i * 3.0
    box(s, x, 3.9, 2.6, 0.9, fill=None, line=WHITE, lw=2)
    text(s, x, 3.9, 2.6, 0.9, st, size=26, bold=True, color=WHITE, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    if i < 3: text(s, x + 2.6, 3.9, 0.4, 0.9, "›", size=30, color=WHITE, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
strip = since(s, m1)
text(s, 0.8, 5.3, 11.5, 0.6, "Two vLLM pods  ·  same model  ·  same GPU type  ·  same traffic", size=22, color=WHITE)
groups = []; i = 0
while i < len(strip):                                    # box + label (+ arrow) per step
    k = 3 if i + 3 < len(strip) else 2; groups.append(strip[i:i + k]); i += k
animate(s, [("auto", [(g, "up", 350, 400) for g in groups])])
s = body_slide("Backup: what screen 4 showed (recorded 16 Oct)")
s._element.set("show", "0")
s.shapes.add_picture(A("backup-screen4.png"), I(1.17), I(1.25), height=I(5.6))
foot(s, "Hidden slide. Only if the rig is down AND the video will not play.")

# ---------- slide 4: what broke ----------
s = body_slide("What broke while we built it")
text(s, 0.6, 1.3, 12.0, 0.6, "Our first load test didn't stress anything.", size=26, italic=True, color=MAG, bold=True)
text(s, 2.9, 2.0, 4.6, 0.4, "What we saw", size=16, bold=True, color=GREY)
text(s, 7.75, 2.0, 5.0, 0.4, "What we learned", size=16, bold=True, color=GREY)
stories = (("Prefix caching", "Identical prompts. vLLM shared the cache between them, so nothing filled up.",
            "A unique prefix on every prompt. A load test with repeated prompts is lying to you."),
           ("Cardinality", "The pod name on every GPU metric: 14 series live, 56 after 3 rollouts.",
            "Every restart mints a new set of series. Budget retention for pod churn."),
           ("An unfair test", "More traffic to one pod: 12 s vs 0.13 s. Too good to be true.",
            "Same traffic to both: 5.9 s vs 0.08 s to the first token. Test with your own traffic."))
rows4 = []; hdr = list(s.shapes)[-2:]
for i, (n, saw, lr) in enumerate(stories):
    m1 = mark(s)
    y = 2.45 + i * 1.45
    box(s, 0.6, y, 12.15, 1.3, fill=LIGHT if i % 2 == 0 else WHITE, line=LINE)
    text(s, 0.8, y, 2.0, 1.3, n, size=19, bold=True, color=MAG, anchor=MSO_ANCHOR.MIDDLE)
    text(s, 2.9, y, 4.6, 1.3, saw, size=17, color=INK, anchor=MSO_ANCHOR.MIDDLE)
    text(s, 7.75, y, 4.85, 1.3, lr, size=17, color=INK, anchor=MSO_ANCHOR.MIDDLE)
    rows4.append(since(s, m1))
foot(s, "Test cluster: vLLM v0.30.0, facebook/opt-125m, one A10G per pod. Cardinality: 7 DCGM counters x 2 GPUs, measured 13 Oct 2026.")
animate(s, [("click", [(hdr, "fade", 0, 300), (rows4[0], "up", 0, 450)]), ("click", [(rows4[1], "up", 0, 450)]),
            ("click", [(rows4[2], "up", 0, 450)])])

# ---------- slides 5a-5c: take this home (S10: three slides, animated) ----------
GREEN, ORANGE, PURPLE, DARK = "2E9E5B", "E8871E", "7B4FBF", "333338"
from pptx.oxml.ns import qn
def arrow(s, x1, y1, x2, y2, col, w=3):
    c = s.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, I(x1), I(y1), I(x2), I(y2)); c.line.color.rgb = rgb(col); c.line.width = Pt(w)
    etree.SubElement(c.line._get_or_add_ln(), qn("a:tailEnd"), type="triangle", w="med", len="med"); return c

# 5a: the answer to the vote
s = body_slide("Who voted both? You were right.")
cards5a = []; verdicts = []
for x, col, name, pct, verdict, detail in (
        (0.6, RED, "Pod A", "8%", "Too small", "KV cache hit 100%. New requests waited 5.9 s for the first token."),
        (6.75, BLUE, "Pod B", "90%", "Too big", "KV cache peaked near 30%. 20.6 GB held, mostly empty.")):
    m = mark(s)
    box(s, x, 1.95, 5.95, 3.2, fill=WHITE, line=col, lw=3)
    text(s, x + 0.35, 2.05, 5.3, 0.5, name, size=22, color=col, bold=True)
    text(s, x + 0.35, 2.45, 2.6, 1.2, pct, size=72, color=col, bold=True, spacing=0.9, anchor=MSO_ANCHOR.MIDDLE)
    cards5a.append(since(s, m)); m = mark(s)
    b = box(s, x + 3.0, 2.6, 2.65, 0.85, fill=col, line=None, radius=0.15)
    text(s, x + 3.0, 2.6, 2.65, 0.85, verdict, size=28, bold=True, color=WHITE, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    text(s, x + 0.35, 3.8, 5.3, 1.3, detail, size=20, color=INK)
    verdicts.append(since(s, m))
m = mark(s)
text(s, 0.6, 5.45, 12.1, 1.3, [[("GPU memory can't tell you an inference server is in trouble. ", {"bold": True}),
     ("Read the server's own signal.", {"color": MAG, "bold": True})]], size=28, color=INK)
take5a = since(s, m)
foot(s, "Measured 16 Oct 2026, our test cluster: vLLM v0.30.0, facebook/opt-125m (a small model), one A10G per pod, same traffic to both.")
animate(s, [("auto", [(cards5a[0] + cards5a[1], "fade", 0, 400)]),
            ("click", [(verdicts[0][:2], "zoom", 0, 400), (verdicts[0][2:], "up", 0, 450)]),
            ("click", [(verdicts[1][:2], "zoom", 0, 400), (verdicts[1][2:], "up", 0, 450)]),
            ("click", [(take5a, "fade", 0, 500)])])

# 5b: three lines of config, one join key
s = body_slide("Three lines of config, one join key")
text(s, 0.6, 1.25, 12.0, 0.5, "Each signal carries the pod name, so one dashboard can line them up.", size=20, color=GREY)
cfg = ((DARK, "dcgm-exporter", "GPU metrics  →  pod", ["--kubernetes=true"]),
       (ORANGE, "Fluent Bit", "vLLM log  →  KV cache %", ["string.match(line,", '  "KV cache usage:%s*([%d%.]+)%%")']),
       (PURPLE, "OTel Collector", "traces  →  pod", ["k8sattributes:", "  extract:", "    metadata: [k8s.pod.name]"]))
NX, NY, NR = 10.3, 4.35, 1.0                          # join node centre + radius
steps5b = []
for i, (col, name, sub, code) in enumerate(cfg):
    y = 1.95 + i * 1.65; m = mark(s)
    box(s, 0.6, y, 7.0, 1.45, fill=WHITE, line=LINE)
    box(s, 0.6, y, 0.14, 1.45, fill=col, line=None, shape=MSO_SHAPE.RECTANGLE)
    text(s, 0.9, y + 0.2, 2.6, 0.5, name, size=20, bold=True, color=INK)
    text(s, 0.9, y + 0.72, 2.6, 0.6, sub, size=14, color=GREY)
    box(s, 3.55, y + 0.12, 3.9, 1.21, fill=CODEBG, line=None, radius=0.05)
    text(s, 3.65, y + 0.12, 3.75, 1.21, code, size=12, font="Consolas", color=INK, anchor=MSO_ANCHOR.MIDDLE, spacing=1.0)
    card = since(s, m)
    a = arrow(s, 7.7, y + 0.725, NX - NR - 0.05, NY + (i - 1) * 0.45, col)
    steps5b.append(("click", [(card, "up", 0, 450), ([a], "wipe", 0, 600)]))
m = mark(s)
box(s, NX - NR, NY - NR, 2 * NR, 2 * NR, fill=MAG, line=None, shape=MSO_SHAPE.OVAL)
text(s, NX - NR, NY - 0.5, 2 * NR, 0.55, "pod name", size=22, bold=True, color=WHITE, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
text(s, NX - NR, NY + 0.05, 2 * NR, 0.4, "k8s.pod.name", size=12, font="Consolas", color=WHITE, align=PP_ALIGN.CENTER)
node = since(s, m); m = mark(s)
text(s, 8.7, 5.5, 3.2, 1.0, "GPU, log and trace for the same pod, on one screen", size=15, color=INK, align=PP_ALIGN.CENTER)
node_cap = since(s, m)
foot(s, "Tested: dcgm-exporter 4.8.4, Fluent Bit 5.1.3, OTel Collector contrib 0.111.0. vLLM also exports KV cache % on /metrics; "
        "the log path works for servers that only log it.")
animate(s, steps5b + [("click", [(node, "zoom", 0, 450)]), ("auto", [(node_cap, "fade", 0, 400)])])

# 5c: the rule of thumb, on a gauge
s = body_slide("Size it from peak KV cache")
text(s, 0.6, 1.25, 12.0, 0.5, "Peak KV cache usage, under your own traffic", size=20, color=GREY)
GX, GW, GY, GH = 0.6, 12.1, 2.75, 0.85
px = lambda p: GX + GW * p / 100
bands = ((0, 40, "AFC6EE", "Below 40%: too big", "Memory you reserved and never use."),
         (40, 90, "A8DDBD", "40 to 90%: about right", "Headroom for a burst."),
         (90, 100, "F2A7B0", "Above 90%: too small", "Requests start to queue."))
band_steps = []
for j, (a, b, col, head, sub) in enumerate(bands):
    m = mark(s)
    box(s, px(a), GY, px(b) - px(a), GH, fill=col, line=WHITE, shape=MSO_SHAPE.RECTANGLE, lw=2)
    text(s, px(a) - (0.3 if a else 0.05), GY + GH + 0.05, 0.7, 0.35, f"{a}%", size=13, color=GREY, align=PP_ALIGN.CENTER if a else PP_ALIGN.LEFT)
    bar = since(s, m); m = mark(s)
    tx, tw, al = (px(a) + 0.05, 4.6, PP_ALIGN.LEFT) if j < 2 else (px(b) - 3.6, 3.6, PP_ALIGN.RIGHT)
    if j == 1: tx, tw = px(a) + 0.15, 4.2
    text(s, tx, GY + GH + 0.5, tw, 1.0, [[(head, {"bold": True})], sub], size=17, color=INK, align=al)
    band_steps.append((bar, "wipe", 0, 500)); band_steps.append((since(s, m), "fade", 350, 350))
m = mark(s)
text(s, px(100) - 0.65, GY + GH + 0.05, 0.7, 0.35, "100%", size=13, color=GREY, align=PP_ALIGN.RIGHT)
band_steps.append((since(s, m), "fade", 0, 300))
pins = []
for p, col, lbl, al, lx in ((100, RED, "Pod A (8%): peak 100%", PP_ALIGN.RIGHT, px(100) - 4.2),
                            (30, BLUE, "Pod B (90%): peak about 30%", PP_ALIGN.CENTER, px(30) - 2.1)):
    m = mark(s)
    text(s, lx, 1.85, 4.2, 0.45, lbl, size=17, bold=True, color=col, align=al)
    tri = box(s, min(px(p), px(100) - 0.08) - 0.17, 2.32, 0.34, 0.36, fill=col, line=None, shape=MSO_SHAPE.ISOSCELES_TRIANGLE)
    tri.rotation = 180
    pins.append(since(s, m))
steps5c = []
for k, (head, sub) in enumerate((("Measure", [("peak KV cache under your own traffic", {})]),
                                 ("Change", [("--gpu-memory-utilization", {"font": "Consolas", "size": 12})]),
                                 ("Measure again", [("until the peak sits between 40 and 90%", {})]))):
    m = mark(s); x = 0.6 + k * 3.4
    text(s, x, 5.0, 0.55, 0.9, str(k + 1), size=40, bold=True, color=MAG, spacing=0.9)
    text(s, x + 0.55, 5.05, 2.75, 0.95, [[(head, {"bold": True})], sub], size=16, color=INK)
    steps5c += [(since(s, m), "up", 300, 400)]
m = mark(s)
text(s, 0.6, 6.05, 10.0, 0.4, "Caveat: 40% and 90% are our rule of thumb, from one model on one GPU type. Use the method, not our numbers.",
     size=13, italic=True, color=GREY)
text(s, 0.6, 6.5, 10.0, 0.45, REPO, size=17, bold=True, color=MAG, font="Consolas")
s.shapes.add_picture(A("qr-repo.png"), I(11.05), I(4.95), height=I(1.65))
text(s, 10.6, 6.62, 2.55, 0.4, "All configs, deployable", size=12, bold=True, color=INK, align=PP_ALIGN.CENTER)
rule5c = since(s, m)
animate(s, [("click", band_steps), ("click", [(pins[0], "up", 0, 450)]), ("click", [(pins[1], "up", 0, 450)]),
            ("click", steps5c), ("auto", [(rule5c, "fade", 0, 500)])])

# ---------- slide 6: questions ----------
s = prs.slides.add_slide(L_TITLE)
text(s, 0.8, 1.3, 7.6, 1.5, "Questions?", size=66, bold=True, color=WHITE)
text(s, 0.8, 2.9, 7.6, 1.2, ["Henrique Santana, Principal Cloud Engineer, AWS", "Danilo Silva, Senior Delivery Consultant, AWS"],
     size=20, color=WHITE)
text(s, 0.8, 4.4, 7.6, 1.8, [[("Original idea: ", {"bold": True}), ("[original author]", {})],
     [("Further reading: ", {"bold": True}), ("jimmysong.io/blog/gpu-to-token-observability", {})],
     [("Repo: ", {"bold": True}), (REPO, {})]], size=15, color=WHITE)
box(s, 9.1, 2.3, 3.4, 3.4, fill=WHITE, line=None, radius=0.04)
s.shapes.add_picture(A("qr-feedback-cncf.png"), I(9.18), I(2.36), height=I(3.28))   # official session feedback code (organisers)
text(s, 9.1, 5.8, 3.4, 0.5, "Rate this session", size=18, bold=True, color=WHITE, align=PP_ALIGN.CENTER)


# ---------- hidden Q&A backups (after Questions; jump with number + Enter) ----------
def qa_slide(q, answer, src):
    s = body_slide(q); s._element.set("show", "0")
    text(s, 0.6, 1.25, 4.3, 0.4, "Q&A BACKUP", size=13, bold=True, color=MAG)
    text(s, 0.6, 1.7, 5.6, 4.9, answer, size=19, color=INK, spacing=1.15)
    foot(s, src); return s
def code_card(s, x, y, w, h, label, lines, col):
    box(s, x, y, w, h, fill=WHITE, line=LINE); box(s, x, y, 0.12, h, fill=col, line=None, shape=MSO_SHAPE.RECTANGLE)
    text(s, x + 0.3, y + 0.12, w - 0.4, 0.4, label, size=15, bold=True, color=INK)
    box(s, x + 0.3, y + 0.6, w - 0.5, h - 0.75, fill=CODEBG, line=None, radius=0.05)
    text(s, x + 0.4, y + 0.6, w - 0.7, h - 0.75, lines, size=13, font="Consolas", color=INK, anchor=MSO_ANCHOR.MIDDLE, spacing=1.0)

s = qa_slide("Why parse the log if vLLM has /metrics?",
    [[("Scrape /metrics if you can. ", {"bold": True}), ("We do too: demo screen 2 puts both side by side, and they match.", {})], "",
     [("The log path needs no new scrape target. ", {"bold": True}), ("Fluent Bit already reads every pod's log.", {})], "",
     [("It works on any server that prints its cache usage, ", {}), ("even one that does not export it.", {"bold": True})]],
    "README.md; dashboard gpu-walk-2 (log_kv_cache_usage_pct vs vllm:kv_cache_usage_perc). The log line comes every 10 s, coarser than a scrape.")
code_card(s, 6.75, 1.95, 6.0, 1.75, "vLLM /metrics", ["vllm:kv_cache_usage_perc"], DARK)
code_card(s, 6.75, 3.85, 6.0, 1.65, "vLLM log line, every 10 s", ["... GPU KV cache usage: 99.6%, ..."], ORANGE)
text(s, 6.75, 5.65, 6.0, 0.6, "Same number, two paths.", size=22, bold=True, color=MAG, align=PP_ALIGN.CENTER)

s = qa_slide("Why not set 0.90 everywhere?",
    [[("The default is already 0.92.", {"bold": True})], "",
     [("One pod, one GPU, nothing else on it: ", {}), ("0.90 is fine.", {"bold": True}), (" You paid for headroom.", {})], "",
     [("Shared GPUs: ", {"bold": True}), ("the memory is reserved at startup, used or not. It is what the next pod needs.", {})]],
    "vllm/config/cache.py (default 0.92); 16 Oct 2026 recording. Sharing needs time-slicing, MPS or MIG; not tested on this rig.")
text(s, 6.75, 1.95, 6.0, 0.4, "Pod B, 90%: 20.6 GB reserved", size=17, bold=True, color=BLUE)
box(s, 6.75, 2.45, 6.0, 1.0, fill=LIGHT, line=BLUE, shape=MSO_SHAPE.RECTANGLE, lw=2)
box(s, 6.75, 2.45, 1.8, 1.0, fill=BLUE, line=None, shape=MSO_SHAPE.RECTANGLE)
text(s, 6.75, 2.45, 1.8, 1.0, "used ~30%", size=15, bold=True, color=WHITE, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
text(s, 8.55, 2.45, 4.2, 1.0, "reserved, never used", size=16, color=GREY, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
text(s, 6.75, 3.7, 6.0, 1.2, "Size from the peak. Give the rest back.", size=22, bold=True, color=MAG)

s = qa_slide("What about GPU utilisation?",
    [[("GPU_UTIL = share of time at least one kernel ran.", {"bold": True})], "",
     [("One busy kernel reads as 100%. Waiting on memory looks the same as flat out.", {})], "",
     [("Profiling fields say more. ", {"bold": True}), ("None of them knows about the queue.", {})]],
    "NVML nvmlUtilization_t; manifests/10-gpu-metrics/dcgm-exporter.yaml (scraped on the A10G). Profiling fields need GPU and driver support.")
rows_u = (("DCGM_FI_DEV_GPU_UTIL", "a kernel ran"), ("DCGM_FI_PROF_SM_ACTIVE", "share of SMs working"),
          ("DCGM_FI_PROF_DRAM_ACTIVE", "memory bus busy"), ("the server's queue", "none of the above"))
for r, (f, d) in enumerate(rows_u):
    y = 1.95 + r * 0.95; last = r == 3
    box(s, 6.75, y, 6.0, 0.8, fill=MAG if last else (LIGHT if r % 2 == 0 else WHITE), line=LINE)
    text(s, 6.9, y, 3.4, 0.8, f, size=14 if not last else 16, font="Arial" if last else "Consolas", bold=last,
         color=WHITE if last else INK, anchor=MSO_ANCHOR.MIDDLE)
    text(s, 10.3, y, 2.4, 0.8, d, size=15, color=WHITE if last else GREY, bold=last, anchor=MSO_ANCHOR.MIDDLE)

s = qa_slide("How much does the pod name cost?",
    [[("One new set of series per pod restart.", {"bold": True})], "",
     [("Keep the pod name: it is the join key.", {})], "",
     [("Drop what churns: ", {"bold": True}), ("no pod labels, a short counter list, short retention for per-pod data.", {})]],
    "manifests/50-prometheus/CARDINALITY-DEMO.md, measured 13 Oct 2026: 7 counters x 2 GPUs. Default counter set is about 40.")
for k, (num, lbl) in enumerate((("14", "series now"), ("56", "after 3 rollouts"))):
    x = 6.75 + k * 3.1
    box(s, x, 1.95, 2.9, 1.8, fill=WHITE, line=MAG if k else LINE, lw=3 if k else 1.5)
    text(s, x, 2.0, 2.9, 1.1, num, size=60, bold=True, color=MAG if k else INK, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    text(s, x, 3.1, 2.9, 0.5, lbl, size=16, color=GREY, align=PP_ALIGN.CENTER)
code_card(s, 6.75, 4.0, 6.0, 2.5, "The fix we ship", ["--kubernetes=true", "..._ENABLE_POD_LABELS=false", "counters.csv: 7 counters", "retention: 6h"], MAG)

# ---------- order: drop template instruction + sample slides, keep cover + title first ----------
ids = prs.slides._sldIdLst; items = list(ids)
for el in (items[0], items[1], items[4]):              # AV instructions x2, sample "Title / Content"
    prs.part.drop_rel(el.rId); ids.remove(el)
for sl in prs.slides: fade_transition(sl)
sys.path.insert(0, HERE); from notes_obsday import NOTES
assert len(prs.slides) == len(NOTES), (len(prs.slides), len(NOTES))
for k, sl in enumerate(prs.slides, 1): notes(sl, NOTES[k])
out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "kubecon-obsday-2026.pptx")
prs.save(out); print("saved", out, len(prs.slides), "slides")
