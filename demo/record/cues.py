import re, sys
fx = open(sys.argv[1]).read().splitlines(); cl = open(sys.argv[2]).read().splitlines()
def parse(ls): return [(l[:5].strip(), l[5:].strip()) for l in ls if l.strip()]
F, C = parse(fx), parse(cl)
out = ["# Cue sheet: demo recordings v7 (recorded Oct 16, same load for both)", "",
       "Same 4 screens and clicks as DEMO-SCRIPT.md. Find the screen you were on, jump there, keep talking.", "",
       "| Beat | Clean (`gpu-obs-demo-v7-clean.mp4`) | Captioned (`gpu-obs-demo-v7.mp4`) |", "|------|------|------|"]
for (tf, txt), (tc, _) in zip(F, C):
    t = txt.replace("|", "·")
    if t.startswith("[screen"): t = "**" + t.strip("[]") + "**"
    out.append(f"| {t} | {tc} | {tf} |")
open(sys.argv[3], "w").write("\n".join(out) + "\n")
print(len(F), len(C))
