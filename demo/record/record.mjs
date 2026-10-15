// Scripted, captioned recording of the GPU observability demo. Frames = JPEG screenshots (sharp text),
// assembled into an MP4 by ffmpeg afterwards. Beats wait on real Prometheus values, not fixed timers.
import { chromium } from 'playwright';
import { exec } from 'child_process';
import fs from 'fs';
const REPO = new URL('../..', import.meta.url).pathname.replace(/\/$/, '');
const OUT = process.env.OUT || 'rec';
const G = 'http://localhost:3000', PROM = 'http://localhost:9090';
const sleep = ms => new Promise(r => setTimeout(r, ms));
fs.rmSync(OUT, { recursive: true, force: true }); fs.mkdirSync(`${OUT}/f`, { recursive: true });

const b = await chromium.launch({ channel: 'chrome' });
const ctx = await b.newContext({ viewport: { width: 1920, height: 1080 } });
await ctx.addInitScript(() => { try { localStorage.setItem('grafana.navigation.docked', 'false'); } catch (e) {} });
const p = await ctx.newPage();

// ---------- capture ----------
let rec = false, t0 = 0; const frames = [], cues = [];
async function capLoop() {
  while (rec) {
    const t = Date.now();
    const f = `${OUT}/f/${String(frames.length).padStart(5, '0')}.jpg`;
    try { await p.screenshot({ path: f, type: 'jpeg', quality: 90 }); frames.push([f, t]); } catch (e) {}
    const dt = Date.now() - t; if (dt < 150) await sleep(150 - dt);
  }
}
const ts = () => { const s = Math.round((Date.now() - t0) / 1000); return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`; };

// ---------- overlays ----------
const ui = (fn, arg) => p.evaluate(fn, arg).catch(() => {});
async function caption(title, sub = '', pos = 'bottom') {
  cues.push(`${ts()}  ${title}${sub ? '  |  ' + sub : ''}`); console.log(cues.at(-1));
  await ui(([t, s, pos]) => {
    let c = document.getElementById('cap');
    if (!c) { c = document.createElement('div'); c.id = 'cap'; document.body.appendChild(c); }
    Object.assign(c.style, { position: 'fixed', left: '50%', transform: 'translateX(-50%)', zIndex: 100001,
      background: 'rgba(12,12,16,.95)', color: '#fff', padding: '16px 34px', borderRadius: '14px',
      font: '600 34px/1.25 Inter,Helvetica,Arial,sans-serif', maxWidth: '1750px', textAlign: 'center',
      boxShadow: '0 8px 30px rgba(0,0,0,.7)', border: '2px solid #ff9830', opacity: t ? 1 : 0,
      top: pos === 'top' ? '24px' : 'auto', bottom: pos === 'top' ? 'auto' : '28px' });
    c.innerHTML = t + (s ? `<div style="font-weight:400;font-size:26px;color:#d5d8e0;margin-top:6px">${s}</div>` : '');
  }, [title, sub, pos]);
}
async function boxRect(r) {
  await ui((r) => {
    let x = document.getElementById('hl');
    if (!x) { x = document.createElement('div'); x.id = 'hl'; document.body.appendChild(x);
      Object.assign(x.style, { position: 'fixed', zIndex: 100000, border: '5px solid #ff9830', borderRadius: '10px',
        boxShadow: '0 0 0 9999px rgba(0,0,0,.5)', pointerEvents: 'none', transition: 'all .6s ease', opacity: 0 }); }
    if (!r) { x.style.opacity = 0; return; }
    Object.assign(x.style, { left: (r.x - 7) + 'px', top: (r.y - 7) + 'px', width: (r.width + 14) + 'px', height: (r.height + 14) + 'px', opacity: 1 });
  }, r);
}
async function box(...sels) {          // one or more CSS selectors / locators -> spotlight their union
  if (!sels.length || sels[0] == null) return boxRect(null);
  let u = null;
  for (const s of sels) {
    const bb = await (typeof s === 'string' ? p.locator(s).first() : s).boundingBox({ timeout: 4000 }).catch(() => null);
    if (!bb) continue;
    u = u ? { x: Math.min(u.x, bb.x), y: Math.min(u.y, bb.y),
              width: Math.max(u.x + u.width, bb.x + bb.width) - Math.min(u.x, bb.x),
              height: Math.max(u.y + u.height, bb.y + bb.height) - Math.min(u.y, bb.y) } : bb;
  }
  return boxRect(u);
}
async function cursorTo(x, y) {
  await ui(([x, y]) => {
    let c = document.getElementById('cur');
    if (!c) { c = document.createElement('div'); c.id = 'cur'; document.body.appendChild(c);
      Object.assign(c.style, { position: 'fixed', zIndex: 100002, width: '34px', height: '34px', borderRadius: '50%',
        background: 'rgba(255,152,48,.55)', border: '3px solid #fff', pointerEvents: 'none',
        transform: 'translate(-50%,-50%)', transition: 'left .9s ease, top .9s ease', left: '960px', top: '700px' }); }
    c.style.left = x + 'px'; c.style.top = y + 'px';
  }, [x, y]);
  await sleep(1100);
}
async function clickOn(loc) {
  const bb = await loc.boundingBox({ timeout: 8000 }).catch(() => null);
  if (!bb) { console.log('SKIP click (not found)'); return false; }
  await cursorTo(bb.x + bb.width / 2, bb.y + bb.height / 2);
  await ui(() => { const c = document.getElementById('cur'); c.animate([{ transform: 'translate(-50%,-50%) scale(1)' }, { transform: 'translate(-50%,-50%) scale(1.8)' }, { transform: 'translate(-50%,-50%) scale(1)' }], { duration: 400 }); });
  await sleep(250); await loc.click({ timeout: 5000 }).catch(e => console.log('SKIP click', e.message.slice(0, 60))); await sleep(300); return true;
}
async function card(html) {
  await ui((h) => {
    let c = document.getElementById('card');
    if (!c) { c = document.createElement('div'); c.id = 'card'; document.body.appendChild(c);
      Object.assign(c.style, { position: 'fixed', inset: 0, zIndex: 100003, background: '#111217', color: '#fff',
        display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', textAlign: 'center',
        font: '400 34px/1.5 Inter,Helvetica,Arial,sans-serif', transition: 'opacity .6s' }); }
    if (!h) { c.style.opacity = 0; setTimeout(() => c.style.display = 'none', 700); return; }
    c.style.display = 'flex'; c.style.opacity = 1; c.innerHTML = h;
  }, html);
}

// ---------- data ----------
async function prom(q) {
  try { const r = await (await fetch(`${PROM}/api/v1/query?query=${encodeURIComponent(q)}`)).json();
        return r.data.result.map(x => [x.metric, +x.value[1]]); } catch { return []; }
}
async function until(fn, ms, label) {
  const end = Date.now() + ms;
  while (Date.now() < end) { if (await fn()) return true; await sleep(3000); }
  console.log('timeout waiting for', label); return false;
}
const kv = async (re) => Math.max(0, ...(await prom(`vllm_log_kv_cache_usage_pct{pod_name=~"${re}"}`)).map(x => x[1]));
const queue = async (re) => Math.max(0, ...(await prom(`histogram_quantile(0.95, sum by (le, pod) (rate(vllm:request_queue_time_seconds_bucket{pod=~"${re}"}[1m])))`)).map(x => x[1]).filter(Number.isFinite));
const panel = id => `[data-panelid="${id}"]`;
const DASH = `${G}/d/gpu-inference-obs?orgId=1&kiosk&from=now-5m&to=now&refresh=5s`;

// ---------- set-up (not recorded) ----------
{
  const jobs = await new Promise(r => exec('kubectl -n inference get jobs --no-headers 2>/dev/null', (e, o) => r(o.trim())));
  const kvNow = await prom('vllm_log_kv_cache_usage_pct');
  const q = await prom('sum(rate(vllm:request_queue_time_seconds_count[2m]))');
  if (jobs || kvNow.length || (q[0] && q[0][1] > 0)) { console.log('DIRTY: not idle', jobs, kvNow.length, q); process.exit(2); }
  console.log('idle check OK');
}
await p.goto(`${G}/login`);
await p.fill('input[name="user"]', 'admin'); await p.fill('input[name="password"]', 'gpu-obs-demo');
await p.click('button[type="submit"]'); await p.waitForURL(u => !u.toString().includes('/login'));
await p.goto(DASH, { waitUntil: 'load' }); await sleep(8000);
const gpuMem = Object.fromEntries((await prom('DCGM_FI_DEV_FB_USED{exported_pod=~"vllm-.*"}')).map(([m, v]) => [m.exported_pod.split('-')[1], (v / 1024).toFixed(1)]));
const series = async () => [(await prom('count({__name__=~"DCGM_.*"})'))[0]?.[1] ?? 0, (await prom('count(count_over_time(DCGM_FI_DEV_FB_USED[1h])) + count(count_over_time(DCGM_FI_DEV_FB_FREE[1h])) + count(count_over_time(DCGM_FI_PROF_SM_ACTIVE[1h])) + count(count_over_time(DCGM_FI_PROF_DRAM_ACTIVE[1h])) + count(count_over_time(DCGM_FI_DEV_POWER_USAGE[1h])) + count(count_over_time(DCGM_FI_DEV_GPU_TEMP[1h])) + count(count_over_time(DCGM_FI_DEV_GPU_UTIL[1h]))'))[0]?.[1] ?? 0];

// ---------- recording ----------
rec = true; t0 = Date.now(); const cap = capLoop();

// S0 title
await card(`<div style="font-size:30px;color:#ff9830;letter-spacing:2px">LIVE DEMO</div>
  <div style="font:700 60px/1.2 Inter,Helvetica,Arial;margin:14px 0 30px">Inference is a black box</div>
  <div>Two vLLM pods · same model · same GPU (NVIDIA L4)</div>
  <div><span style="color:#f2495c">red</span>: 15% of GPU memory reserved for the model server
  &nbsp;·&nbsp; <span style="color:#5794f2">blue</span>: 90%</div>
  <div style="margin-top:30px;color:#9fa7b3;font-size:28px">GPU metrics: dcgm-exporter · Logs: Fluent Bit + Lua · Traces: OpenTelemetry · Joined by pod name in Grafana</div>`);
cues.push(`${ts()}  [title card]`);
await sleep(10000); await card(null); await sleep(800);

// S1 idle
await caption('No load yet. Two healthy-looking pods.', 'One dashboard, one row per signal, every panel keyed by pod name');
await sleep(8000);
await box(panel(2));
await caption('1 · GPU memory (DCGM): reserved at start-up, then flat', `red ${gpuMem.constrained ?? '3.5'} GB · blue ${gpuMem.overprov ?? '20.4'} GB. This is the panel most teams page on.`);
await sleep(10000);
await box(panel(3), panel(4));
await caption('2 and 3 · KV cache and queue time: quiet', 'Nothing is waiting. Nothing is full.');
await sleep(8000);

// S2 load
await box(null);
exec(`kubectl -n inference delete job vllm-loadgen --ignore-not-found --wait=true && kubectl apply -f ${REPO}/manifests/20-vllm/loadgen-job.yaml`, (e, o, er) => console.log('load:', e ? er : 'started'));
await caption('Load starts', '192 long requests to the red pod · 16 short requests to the blue pod');
await sleep(12000);

// S3 watch it break
await box(panel(3));
await caption('2 · KV cache %, read from the vLLM log line', 'Fluent Bit tails the log · a 15-line Lua filter extracts it · log_to_metrics turns it into a metric per pod');
await until(async () => (await kv('vllm-constrained.*')) > 90, 240000, 'kv>90');
await sleep(6000);
await caption('Red pod: KV cache full. Blue pod: almost empty.', 'KV cache is the real "GPU memory full" for an LLM server');
await sleep(9000);
await box(panel(4));
await until(async () => (await queue('vllm-constrained.*')) > 2, 150000, 'queue>2');
await sleep(5000);
const qr = (await queue('vllm-constrained.*')).toFixed(1), qb = (await queue('vllm-overprov.*')).toFixed(2);
await caption('3 · Queue time p95 (vLLM /metrics): requests wait', `red ${qr} s before the GPU even starts on them · blue ${qb} s`);
await sleep(10000);
await box(panel(2));
await caption('1 · GPU memory: still flat', 'DCGM cannot see any of this. The pod in trouble even uses less memory.');
await sleep(10000);
await until(async () => (await prom('max_over_time(vllm_log_kv_cache_usage_pct{pod_name=~"vllm-constrained.*"}[5m]) > 90')).length > 0, 60000, 'verdict');
await box(panel(1));
await caption('The verdict, per pod', 'Same model, same GPU: one memory-constrained, one over-provisioned. Only the log line could tell.');
await sleep(10000);
await box(null);
await caption('Same pod name on every panel', 'dcgm-exporter: exported_pod · Fluent Bit: pod_name · vLLM /metrics: pod');
await sleep(9000);

// S4 traces
await box(panel(5), panel(6));
await caption('4 · Traces: the slowest requests per pod', 'red ~12 s · blue ~0.2 s', 'top');
await sleep(10000);
await box(null); await caption('', '');
const first = p.locator(`${panel(5)} a`).first();
const tid = ((await first.textContent({ timeout: 10000 }).catch(() => '')) || '').trim();
let tq = '?', te = '?', pod = '';
try {
  const tr = (await (await fetch(`http://localhost:16686/api/traces/${tid}`)).json()).data[0];
  const sp = tr.spans.find(s => s.operationName === 'llm_request');
  const tag = k => sp.tags.find(t => t.key === k)?.value;
  tq = (+tag('gen_ai.latency.time_in_queue')).toFixed(1); te = (+tag('gen_ai.latency.e2e')).toFixed(1);
  pod = tr.processes[sp.processID].tags.find(t => t.key === 'k8s.pod.name')?.value || '';
} catch (e) { console.log('trace api', e.message); }
await clickOn(first);
await p.waitForURL(u => u.toString().includes('/explore'), { timeout: 20000 }).catch(() => {});
await sleep(6000);
const outline = p.getByRole('button', { name: /^Outline$/ });
if (await outline.count()) { await outline.first().click().catch(() => {}); await sleep(800); }
const rowVllm = p.getByRole('switch', { name: /llm_request/ }).first();
const rowClient = p.getByRole('switch', { name: /chat request/ }).first();
await box(rowClient, rowVllm);
await caption('One request, two hops: client, then vLLM', 'Same trace ID. The client sent a traceparent header; vLLM continued the trace.');
await sleep(11000);
await box(null);
await clickOn(rowVllm); await sleep(1500);
const sa = p.getByText(/^Span Attributes:?$/).first();
await clickOn(sa); await sleep(1200);
const qRow = p.getByText('gen_ai.latency.time_in_queue', { exact: true }).first();
await qRow.scrollIntoViewIfNeeded().catch(() => {}); await sleep(600);
await box(qRow.locator('xpath=ancestor::tr[1]'), p.getByText('gen_ai.latency.e2e', { exact: true }).first().locator('xpath=ancestor::tr[1]'));
await caption('vLLM records its own timings on the span', `This request: ${te} s end to end, ${tq} s of it waiting in the queue before the GPU started`);
await sleep(12000);
await box(null);
await clickOn(sa); await sleep(800);
const res = p.getByText(/^Resource Attributes:?$/).first();
await clickOn(res); await sleep(1200);
const podRow = p.getByText('k8s.pod.name', { exact: true }).first();
await podRow.scrollIntoViewIfNeeded().catch(() => {}); await sleep(600);
await box(podRow.locator('xpath=ancestor::tr[1]'));
await caption('k8s.pod.name: the join key', 'Added to every span by the OTel Collector (k8sattributes processor). The app never knew its pod name.');
await sleep(12000);
await rowVllm.scrollIntoViewIfNeeded().catch(() => {});

// S5 the join
await box(null);
const chain = rowVllm.locator('xpath=following::button[1]');
await clickOn(chain); await sleep(1000);
const kvLink = p.getByRole('link', { name: /KV cache % \(Fluent Bit\) for this pod/ });
await box(kvLink, p.getByRole('link', { name: /GPU memory \(DCGM\) for this pod/ }));
await caption('From this span straight to that pod\'s metrics', 'Grafana trace-to-metrics: span tag k8s.pod.name becomes the Prometheus label', 'top');
await sleep(9000);
await box(null); await caption('', '');
await clickOn(kvLink); await sleep(8000);
const right = p.locator('[data-testid="data-testid Panel header Graph"]').first();
const kvNow = Math.round(Math.max(0, ...(await prom(`max_over_time(vllm_log_kv_cache_usage_pct{pod_name="${pod}"}[5m])`)).map(x => x[1])));
await box(right);
await caption(`That pod's KV cache around this request: ${kvNow}% full`, 'The slow request, explained in one click');
await sleep(11000);
await box(null);
await clickOn(chain); await sleep(1000);
await clickOn(p.getByRole('link', { name: /GPU memory \(DCGM\) for this pod/ })); await sleep(8000);
await box(p.locator('[data-testid="data-testid Panel header Graph"]').first());
await caption('Same pod, GPU memory: flat', 'DCGM alone would never have explained this request');
await sleep(10000);

// S6 extras: what broke + misleading counters
await box(null); await caption('', '');
await p.goto(DASH, { waitUntil: 'load' }); await sleep(7000);
const row = p.getByText('Details (for Q&A)').first();
await clickOn(row); await sleep(3000);
await p.locator(panel(17)).scrollIntoViewIfNeeded().catch(() => {}); await sleep(2500);
const [now, hour] = await series();
await box(panel(17));
await caption('What broke: cardinality from per-pod GPU metrics', `Same 2 GPUs: ${now} live series, ${hour} seen in the last hour. Every pod restart adds a new set. Fix: keep the pod name, drop pod labels.`, 'top');
await sleep(13000);
await p.locator(panel(11)).scrollIntoViewIfNeeded().catch(() => {}); await sleep(2000);
await box(panel(12));
await caption('GPU utilisation %: "busy" if any kernel ran in the sample', 'Coarse. Looks the same for a healthy pod and a drowning one.', 'top');
await sleep(10000);
await box(panel(11));
await caption('SM active: how much of the chip is actually computing', 'The profiling counter to watch instead (DCGM_FI_PROF_SM_ACTIVE)', 'top');
await sleep(10000);

// S7 outro
await box(null); await caption('', '');
await card(`<div style="font:700 56px/1.2 Inter,Helvetica,Arial;margin-bottom:30px">The pod is the join key</div>
  <div>dcgm-exporter <span style="color:#ff9830">exported_pod</span> &nbsp;·&nbsp; Fluent Bit <span style="color:#ff9830">pod_name</span> &nbsp;·&nbsp; OTel <span style="color:#ff9830">k8s.pod.name</span></div>
  <div style="margin-top:26px;color:#9fa7b3">Watch: SM active · KV cache % · requests waiting</div>
  <div style="margin-top:8px;color:#9fa7b3">All configs in the repo: manifests/</div>`);
cues.push(`${ts()}  [end card]`);
await sleep(9000);

rec = false; await cap; await b.close();
// frame list for ffmpeg (each frame shown until the next one was taken)
let list = '';
for (let i = 0; i < frames.length; i++) {
  const d = i + 1 < frames.length ? (frames[i + 1][1] - frames[i][1]) / 1000 : 0.5;
  list += `file '${frames[i][0].replace(OUT + '/', '')}'\nduration ${d.toFixed(3)}\n`;
}
list += `file '${frames.at(-1)[0].replace(OUT + '/', '')}'\n`;
fs.writeFileSync(`${OUT}/frames.txt`, list);
fs.writeFileSync(`${OUT}/cues.txt`, cues.join('\n') + '\n');
console.log(`frames ${frames.length}, length ${ts()}`);
