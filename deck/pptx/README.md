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
