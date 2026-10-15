# Deck build

```bash
cd deck/pptx
uv run --with python-pptx python build_deck.py <branded-template.pptx> ../kubecon-na-2026-v3.pptx screenshots
```

- Template: CNCF "Observability Day North America 2026 - Branded PowerPoint" with the cover and title slides
  filled in (OneDrive copy, local copy ~/.aki/tmp/kubecon-session.pptx). Not committed to the public repo.
- `screenshots/`: captured from the live rig during the saturating loadgen (Playwright, 1800px, 2x).
  `grafana-full.png` (all rows), `grafana-rows-1-2.png` (crop), `jaeger-trace-detail.png` (one llm_request span
  with k8s.pod.name and gen_ai.* tags). Missing files render as grey placeholders. `cncf-feedback-qr.png` is
  still a placeholder.
- Render check: `soffice --headless --convert-to pdf` then `pdftoppm -png`.
- Speaker notes carry the timing and the narration; the source line on each slide carries the citation.

## v4 (Oct 6 2026, after the critique round)

```bash
cd deck/pptx
uv run --with python-pptx --with pillow python build_deck_v4.py <branded-template.pptx> ../kubecon-na-2026-v4.pptx screenshots
```

- 21 slides, visual rebuild: diagrams and big numbers instead of tables, one idea per slide, KnativeCon watermark
  removed from the content layout, CNCF feedback QR on the last slide. Critique reports: `~/.aki/tmp/kc-review/`
  (followability, technical accuracy, design, timing, humanize), summarised in `../../research-2026-10-06/`.
- `screenshots/v4/panel-*.png`: solo Grafana panels captured at 3x with `shoot.mjs` (Playwright, form login,
  `d-solo` URLs, panel ids 2..12 assigned by Grafana at load). Window 16:52 to 17:09 Dublin, Oct 6 2026.
  `-wide` variants are 1400x300 viewports for the stacked climax slide.
  `node shoot.mjs <from_ms> <to_ms> <outdir>`, env `IDS`, `VH`, `SUFFIX`; needs `kubectl port-forward svc/kube-prometheus-stack-grafana 3000:80`.
- Technical fixes vs v3: GR_ENGINE_ACTIVE (profiler) is not GPU_UTIL (NVML); --gpu-memory-utilization caps the whole
  pool, not just KV cache; SM_OCCUPANCY is a ratio; MFU/MBU line softened (training-world source).
- Still open: attribution placeholder on slide 20 ("[original author, AWS]").

## v6 (Oct 15 2026, simpler story)

```bash
cd deck/pptx
uv run --with python-pptx --with pillow python build_deck_v6.py <branded-template.pptx> ../kubecon-na-2026-v6.pptx screenshots
```

- Built from the v4 slides, then reordered: 14 main slides (about 18 min with a 3-min demo), an appendix divider, and the
  v4 slides that left the main path (prefill/decode, profiler counters, counter table, DCGM per pod, log fields, join row,
  Auto Mode gotcha, router) as backup for Q&A.
- New: car park slide (GPU memory = the car park, KV cache = how full it is), demo signpost "which pod is in trouble?",
  recap = stage dashboard screenshot, three deep dives from the abstract (1 cardinality with measured 14 -> 56,
  2 the Lua with a real vLLM log line, 3 the OTel Collector + Grafana tracesToMetrics config).
- `screenshots/v6/`: stage dashboard at saturation, fresh GPU memory panel (red/blue, load line), two-hop trace. Oct 15 2026.
- Speaker scripts: `speaker_notes_v6.py` for the main path (by final slide position); appendix slides keep `speaker_notes.py`.
