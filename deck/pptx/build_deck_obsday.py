"""Observability Day NA 2026 deck, built on the branded template (assets/obsday-na-2026-template.pptx).
Content = TALK-DECISIONS.md S1-S9. Usage: python3 build_deck_obsday.py ../kubecon-obsday-2026.pptx"""
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
notes(title_s, "0:00 (0:30) HENRIQUE\n- Hi, I'm Henrique; this is Danilo.\n- 20 minutes, one question, a live demo, then questions.\n"
      "- (Danilo: terminal open with demo/load.sh typed, not run. Grafana screen 1 in the next app.)")
notes(cover, "Walk-in slide. Up while people sit down.")

# ---------- slide 1: the vote ----------
s = body_slide("Which one is in trouble?")
text(s, 0.6, 1.35, 10.5, 0.5, "Two vLLM pods. Same model, same GPU type, same traffic.", size=24, color=GREY)
for x, col, name, pct in ((0.6, RED, "Pod A", "8%"), (6.75, BLUE, "Pod B", "90%")):
    box(s, x, 2.0, 5.95, 2.65, fill=WHITE, line=col, lw=3)
    text(s, x + 0.35, 2.12, 5.3, 0.5, name, size=22, color=col, bold=True)
    text(s, x + 0.35, 2.55, 5.3, 1.35, pct, size=80, color=col, bold=True, spacing=0.9, anchor=MSO_ANCHOR.MIDDLE)
    text(s, x + 0.35, 4.05, 5.3, 0.5, "of GPU memory reserved for vLLM", size=20, color=INK)
text(s, 0.6, 4.95, 3.0, 0.5, "Hands up:", size=24, color=INK, bold=True)
for i, opt in enumerate(("8%", "90%", "both", "can't tell from here")):
    w = 3.4 if i == 3 else 2.35; x = 0.6 + sum((2.35 + 0.3) for _ in range(i))
    b = box(s, x, 5.5, w, 0.85, fill=LIGHT, line=LINE)
    text(s, x, 5.5, w, 0.85, opt, size=24, bold=True, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
notes(s, "0:30 (1:30) HENRIQUE\n- Say exactly: \"Two vLLM pods. Same model, same GPU type, same traffic. One reserved 8% of GPU memory, "
      "the other 90%. Which one is in trouble?\"\n- Hands up for each option. Count roughly out loud.\n"
      "- Do NOT reveal. \"Hold that. Danilo will answer it live.\"\n- This is a test cluster we built for this talk: say it now.")

# ---------- slide 2: a setting, not a signal ----------
s = body_slide("GPU memory is a setting, not a signal")
tiles = (("CPU", "how busy the cores are"), ("Memory", "RAM the container uses"),
         ("Network", "bytes in and out"), ("Disk", "reads and writes"))
for i, (n, d) in enumerate(tiles):
    x = 0.6 + i * 2.45
    box(s, x, 1.95, 2.25, 1.9, fill=LIGHT, line=LINE)
    text(s, x + 0.2, 2.1, 1.9, 0.5, n, size=24, bold=True, color=GREY)
    text(s, x + 0.2, 2.7, 1.9, 1.2, d, size=17, color=GREY)
text(s, 0.6, 3.95, 9.6, 0.45, "Node and container resources. None of them sees the server's queue.", size=16, color=GREY, italic=True)
x = 10.5
box(s, x, 1.95, 2.25, 1.9, fill=WHITE, line=MAG, lw=3)
text(s, x + 0.15, 2.1, 2.0, 0.5, "GPU memory", size=19, bold=True, color=MAG)
box(s, x + 0.25, 2.65, 1.75, 0.75, fill=LIGHT, line=None, shape=MSO_SHAPE.RECTANGLE)
ln = s.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, I(x + 0.25), I(2.75), I(x + 2.0), I(2.75)); ln.line.color.rgb = rgb(MAG); ln.line.width = Pt(4)
text(s, x + 0.3, 2.82, 1.7, 0.4, "92%, flat", size=15, bold=True, color=MAG)
text(s, x + 0.2, 3.42, 1.9, 0.4, "set at startup", size=16, color=INK)
text(s, 0.6, 4.75, 12.1, 1.2, [[("vLLM reserves 92% of GPU memory when it starts. ", {"bold": True}),
     ("Busy or idle, that number stays put. So the chart we page on can't tell a struggling server from a quiet one.", {})]],
     size=24, color=INK)
foot(s, "vLLM default: gpu_memory_utilization = 0.92 (vllm/config/cache.py, vLLM main, Oct 2026)")
notes(s, "2:00 (1:30) HENRIQUE\n- The four we all watch measure resources. Fine, but none of them sees the server's queue.\n"
      "- GPU memory: vLLM takes 92% at startup by default. After that it does not move.\n- Say: \"GPU memory is a setting, not a signal.\"")

# ---------- slide 3: the connection pool ----------
s = body_slide("What runs out first: room for requests in flight")
text(s, 0.6, 1.35, 5.6, 0.45, "One GPU, as vLLM uses it", size=20, bold=True, color=INK)
segs = ((1.2, "333338", "weights", WHITE), (3.4, MAG, "KV cache", WHITE), (0.9, LINE, "other", INK))
x = 0.6
for w, c, lab, tc in segs:
    box(s, x, 1.9, w, 0.9, fill=c, line=WHITE, shape=MSO_SHAPE.RECTANGLE, lw=2)
    text(s, x, 1.9, w, 0.9, lab, size=15, bold=True, color=tc, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE); x += w
text(s, 1.5, 2.85, 3.6, 0.7, "room for requests in flight. Its size is set by --gpu-memory-utilization",
     size=14, color=GREY, align=PP_ALIGN.CENTER)
text(s, 0.6, 3.75, 5.6, 0.45, "It behaves like a connection pool", size=20, bold=True, color=INK)
for i in range(6):
    box(s, 0.6 + i * 0.5, 4.35, 0.4, 0.55, fill=MAG, line=None, shape=MSO_SHAPE.RECTANGLE)
text(s, 0.6, 4.95, 3.0, 0.4, "all slots in use", size=14, color=GREY)
ar = s.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, I(4.0), I(4.62), I(3.65), I(4.62)); ar.line.color.rgb = rgb(GREY); ar.line.width = Pt(2.5)
ar.line._get_or_add_ln().append(copy.deepcopy(ar.line._get_or_add_ln().makeelement("{http://schemas.openxmlformats.org/drawingml/2006/main}tailEnd", {"type": "triangle"})))
for i in range(5):
    box(s, 4.15 + i * 0.42, 4.45, 0.34, 0.34, fill=LIGHT, line=GREY, shape=MSO_SHAPE.OVAL, lw=1.5)
text(s, 4.1, 4.95, 2.3, 0.4, "waiting", size=14, color=GREY)
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
text(s, 0.6, 5.85, 12.1, 0.8, "vLLM tells you how full it is, every 10 seconds, in its log.", size=28, bold=True, color=MAG)
foot(s, "Intro structure inspired by Jimmy Song, jimmysong.io/blog/gpu-to-token-observability")
notes(s, "3:30 (2:30) HENRIQUE\n- Most of that 92% is the KV cache: the server's working memory for requests in flight.\n"
      "- Think connection pool: you set its size, requests hold a slot, when it is full new ones wait. Latency climbs, nothing else looks wrong.\n"
      "- vLLM prints how full it is every 10 s in a log line you already ship.\n- No pod named here: the demo answers the vote.")

# ---------- bridge + hidden backup ----------
s = prs.slides.add_slide(L_TITLE)
text(s, 0.8, 1.3, 11.5, 0.6, "LIVE DEMO", size=24, bold=True, color="F4C2D4")
text(s, 0.8, 1.9, 11.5, 1.6, "Is 8% too low? Is 90% too high?", size=54, bold=True, color=WHITE)
for i, st in enumerate(("1  GPU", "2  Log", "3  Trace", "4  Answer")):
    x = 0.8 + i * 3.0
    box(s, x, 3.9, 2.6, 0.9, fill=None, line=WHITE, lw=2)
    text(s, x, 3.9, 2.6, 0.9, st, size=26, bold=True, color=WHITE, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    if i < 3: text(s, x + 2.6, 3.9, 0.4, 0.9, "›", size=30, color=WHITE, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
text(s, 0.8, 5.3, 11.5, 0.6, "Two vLLM pods  ·  same model  ·  same GPU type  ·  same traffic", size=22, color=WHITE)
notes(s, "6:00 (9:00) HENRIQUE hands over: \"Danilo, which one is in trouble?\"\nDANILO\n- Cmd+Tab to Grafana screen 1. Terminal has demo/load.sh typed.\n"
      "- Script: DEMO-SCRIPT.md. Same strip on every screen: 1 GPU > 2 Log > 3 Trace > 4 Answer.\n"
      "- Rig dead? Clean video (gpu-obs-demo-v8-clean.mp4) on this laptop, Space to pause, keep the same lines.\n"
      "- Out: after screen 4, Cmd+Tab back here and advance to slide 4.")
s = body_slide("Backup: what screen 4 showed (recorded 16 Oct)")
s._element.set("show", "0")
s.shapes.add_picture(A("backup-screen4.png"), I(1.17), I(1.25), height=I(5.6))
foot(s, "Hidden slide. Only if the rig is down AND the video will not play.")
notes(s, "HIDDEN. Red (8%): memory-constrained, 2.0 GB, 100% KV, 5.9 s to first token. Blue (90%): over-provisioned, 20.6 GB, 30%, 80 ms.")

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
for i, (n, saw, lr) in enumerate(stories):
    y = 2.45 + i * 1.45
    box(s, 0.6, y, 12.15, 1.3, fill=LIGHT if i % 2 == 0 else WHITE, line=LINE)
    text(s, 0.8, y, 2.0, 1.3, n, size=19, bold=True, color=MAG, anchor=MSO_ANCHOR.MIDDLE)
    text(s, 2.9, y, 4.6, 1.3, saw, size=17, color=INK, anchor=MSO_ANCHOR.MIDDLE)
    text(s, 7.75, y, 4.85, 1.3, lr, size=17, color=INK, anchor=MSO_ANCHOR.MIDDLE)
notes(s, "15:00 (2:30) HENRIQUE\n- Open: \"Our first load test didn't stress anything.\" It took unique prompts to make it struggle, and the GPU dashboard never noticed either way.\n"
      "- Cardinality: promised in the abstract. 14 live, 56 after 3 rollouts.\n"
      "- CUT RULE: if this slide starts after 16:30, skip \"An unfair test\".")

# ---------- slide 5: take this home ----------
s = body_slide("Take this home")
text(s, 0.6, 1.3, 12.0, 0.6, "Who voted both? You were right.", size=30, bold=True, color=MAG)
text(s, 0.6, 1.95, 10.2, 0.9, "GPU memory can't tell you an inference server is in trouble. Read the server's own signal.", size=22, color=INK)
cards = (("dcgm-exporter", "GPU  →  pod", "--kubernetes=true"),
         ("Fluent Bit", "log line  →  KV cache %", 'string.match(line,\n"KV cache usage:%s*([%d%.]+)%%")'),
         ("OTel Collector", "trace  →  pod", "k8sattributes:\n  extract:\n    metadata: [k8s.pod.name]"))
for i, (n, sub, code) in enumerate(cards):
    x = 0.6 + i * 3.45
    box(s, x, 3.0, 3.3, 2.45, fill=WHITE, line=LINE)
    text(s, x + 0.15, 3.1, 3.0, 0.45, n, size=20, bold=True, color=INK)
    text(s, x + 0.15, 3.55, 3.0, 0.4, sub, size=15, color=GREY)
    box(s, x + 0.12, 4.0, 3.06, 1.3, fill=CODEBG, line=None, radius=0.05)
    text(s, x + 0.17, 4.05, 2.98, 1.2, code.split("\n"), size=10.5, font="Consolas", color=INK, anchor=MSO_ANCHOR.MIDDLE, spacing=1.0)
s.shapes.add_picture(A("qr-repo.png"), I(11.2), I(3.0), height=I(1.7))
text(s, 10.95, 4.75, 2.2, 0.7, "All configs, deployable", size=13, bold=True, color=INK, align=PP_ALIGN.CENTER)
text(s, 0.6, 5.62, 12.1, 0.75, [[("Rule of thumb (ours, not vLLM's): ", {"bold": True}),
     ("peak KV cache under your traffic. Above 90%: too small. Below 40%: too big.", {})]], size=17, color=INK)
text(s, 0.6, 6.42, 12.1, 0.45, REPO, size=18, bold=True, color=MAG, font="Consolas")
notes(s, "17:30 (1:30) HENRIQUE\n- Say: \"Who voted both? You were right.\"\n- Takeaway line, word for word.\n"
      "- Three lines of config, one per tool. Everything else is in the repo (QR).\n- Rule of thumb: say it is ours.")

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
notes(s, "19:00 (6:00) BOTH\n- Leave this up for all of Q&A (feedback QR).\n- Q&A backups: deep-dive dashboard gpu-inference-deep (cardinality panel), hidden backup slide.\n"
      "- TODO before the talk: replace [original author].")

# ---------- order: drop template instruction + sample slides, keep cover + title first ----------
ids = prs.slides._sldIdLst; items = list(ids)
for el in (items[0], items[1], items[4]):              # AV instructions x2, sample "Title / Content"
    prs.part.drop_rel(el.rId); ids.remove(el)
out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "kubecon-obsday-2026.pptx")
prs.save(out); print("saved", out, len(prs.slides), "slides")
