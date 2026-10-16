// Recording of the live demo: walks the same 4 walkthrough screens (gpu-walk-1..4) and clicks as DEMO-SCRIPT.md.
// Frames = JPEG screenshots (sharp text), assembled into an MP4 by ffmpeg afterwards.
//   CLEAN=0 (default): captions + spotlight boxes + click pulse, so the video works without a narrator.
//   CLEAN=1          : same clicks and timing, no overlays (a plain pointer only), for talking over it live.
// The load starts ON CAMERA on screen 1, as on stage. START_LOAD=1 (the captioned run) starts it; the clean run, recorded
// at the same time, just shows the same moment. Steps before the load use fixed timing so both runs hit it together.
import { chromium } from 'playwright';
import fs from 'fs';
import { exec } from 'child_process';
const REPO = process.env.REPO || new URL('../..', import.meta.url).pathname.replace(/\/$/, '');
const OUT = process.env.OUT || 'rec';
const CLEAN = process.env.CLEAN === '1';
const START_LOAD = process.env.START_LOAD === '1';
const PACE = +(process.env.PACE || 1);          // multiply every dwell time
const hold = s => sleep(s * 1000 * PACE);
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
async function caption(title, sub = '', pos = 'auto') {
  // on the 4 screens the empty space under the config box holds the caption, so nothing on screen is covered
  if (pos === 'auto') pos = p.url().includes('gpu-walk') ? 'left' : 'bottom';
  if (title) { cues.push(`${ts()}  ${title}${sub ? '  |  ' + sub : ''}`); console.log(cues.at(-1)); }
  if (CLEAN) return;
  await ui(([t, s, pos]) => {
    let c = document.getElementById('cap');
    if (!c) { c = document.createElement('div'); c.id = 'cap'; document.body.appendChild(c); }
    Object.assign(c.style, { position: 'fixed', left: '50%', transform: 'translateX(-50%)', zIndex: 100001,
      background: 'rgba(12,12,16,.95)', color: '#fff', padding: '16px 34px', borderRadius: '14px',
      font: '600 34px/1.25 Inter,Helvetica,Arial,sans-serif', maxWidth: '1750px', textAlign: 'center',
      boxShadow: '0 8px 30px rgba(0,0,0,.7)', border: '2px solid #ff9830', opacity: t ? 1 : 0,
      top: pos === 'top' ? '24px' : 'auto', bottom: pos === 'top' ? 'auto' : '28px' });
    if (pos === 'left') Object.assign(c.style, { left: '25px', transform: 'none', top: '545px', bottom: 'auto',
      width: '640px', maxWidth: '640px', textAlign: 'left', fontSize: '30px' });
    c.innerHTML = t + (s ? `<div style="font-weight:400;font-size:26px;color:#d5d8e0;margin-top:6px">${s}</div>` : '');
  }, [title, sub, pos]);
}
async function boxRect(r) {
  if (CLEAN) return;
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
  await ui(([x, y, clean]) => {
    let c = document.getElementById('cur');
    if (!c) { c = document.createElement('div'); c.id = 'cur'; document.body.appendChild(c);
      Object.assign(c.style, { position: 'fixed', zIndex: 100002, width: clean ? '18px' : '34px', height: clean ? '18px' : '34px', borderRadius: '50%',
        background: clean ? 'rgba(255,255,255,.85)' : 'rgba(255,152,48,.55)', border: clean ? '2px solid #222' : '3px solid #fff', pointerEvents: 'none',
        transform: 'translate(-50%,-50%)', transition: 'left .9s ease, top .9s ease', left: '960px', top: '700px' }); }
    c.style.left = x + 'px'; c.style.top = y + 'px';
  }, [x, y, CLEAN]);
  await sleep(1100);
}
async function clickOn(loc) {
  const bb = await loc.boundingBox({ timeout: 8000 }).catch(() => null);
  if (!bb) { console.log('SKIP click (not found)'); return false; }
  await cursorTo(bb.x + bb.width / 2, bb.y + bb.height / 2);
  if (!CLEAN) await ui(() => { const c = document.getElementById('cur'); c.animate([{ transform: 'translate(-50%,-50%) scale(1)' }, { transform: 'translate(-50%,-50%) scale(1.8)' }, { transform: 'translate(-50%,-50%) scale(1)' }], { duration: 400 }); });
  await sleep(250); await loc.click({ timeout: 5000 }).catch(e => console.log('SKIP click', e.message.slice(0, 60))); await sleep(300); return true;
}
async function term(cmd) {           // the command the presenter types, shown in both versions
  await ui((cmd) => {
    let t = document.getElementById('term');
    if (!t) { t = document.createElement('div'); t.id = 'term'; document.body.appendChild(t); }
    Object.assign(t.style, { position: 'fixed', right: '30px', top: '110px', zIndex: 100001, background: '#0b0c0e',
      color: '#7ee787', font: '500 26px/1.4 Menlo,monospace', padding: '14px 22px', borderRadius: '10px',
      border: '1px solid #444', boxShadow: '0 8px 30px rgba(0,0,0,.7)', transition: 'opacity .5s', opacity: cmd ? 1 : 0 });
    t.textContent = cmd ? '$ ' + cmd : '';
  }, cmd);
}

// ---------- data (live values for the captions, so they always match the screen) ----------
async function prom(q) {
  try { const r = await (await fetch(`${PROM}/api/v1/query?query=${encodeURIComponent(q)}`)).json();
        return r.data.result.map(x => [x.metric, +x.value[1]]); } catch { return []; }
}
async function until(fn, ms, label) {   // wait on a real value, not a timer
  const end = Date.now() + ms;
  while (Date.now() < end) { if (await fn()) return true; await sleep(3000); }
  console.log('timeout waiting for', label); return false;
}
const one = async q => { const v = (await prom(q)).map(x => x[1]).filter(Number.isFinite); return v.length ? Math.max(...v) : NaN; };
const R = 'vllm-constrained.*', B = 'vllm-overprov.*';
const gb   = re => one(`DCGM_FI_DEV_FB_USED{exported_pod=~"${re}"}`).then(v => (v / 1000).toFixed(1));
const kv   = re => one(`max_over_time(vllm_log_kv_cache_usage_pct{pod_name=~"${re}"}[1m])`).then(Math.round);
const tps  = re => one(`vllm_log_gen_tokens_per_s{pod_name=~"${re}"}`).then(Math.round);
const avg  = (m, re) => one(`sum(rate(vllm:${m}_sum{pod=~"${re}"}[2m])) / sum(rate(vllm:${m}_count{pod=~"${re}"}[2m]))`);
const secs = v => v >= 1 ? `${v.toFixed(1)} s` : `${Math.round(v * 1000)} ms`;
const panel = id => `[data-panelid="${id}"]`;
const W = n => `${G}/d/gpu-walk-${n}?orgId=1&kiosk`;
async function next(n) {               // click the screen's own "Next" link, as the presenter does
  const a = p.locator(`${panel(100)} a`).first();
  if (!(await clickOn(a))) await p.goto(W(n));
  await p.waitForURL(u => u.toString().includes(`gpu-walk-${n}`), { timeout: 15000 }).catch(() => p.goto(W(n)));
  await p.locator(panel(102)).waitFor({ timeout: 15000 }).catch(() => {}); await sleep(5000);
}
const hiLine = (id, txt) => p.locator(panel(id)).getByText(txt, { exact: false }).first();

const inflight = re => one(`sum(vllm:num_requests_running{pod=~"${re}"} + vllm:num_requests_waiting{pod=~"${re}"})`);

// ---------- precondition (not recorded): the rig is idle, so the load starts on camera ----------
{
  const busy = (await inflight('vllm-.*')) > 0 || (await kv(R)) > 5;
  if (busy) { console.log('NOT IDLE: a load is running or ended under a minute ago (demo/stop.sh, wait)'); process.exit(2); }
  console.log('idle check OK');
}
await p.goto(`${G}/login`);
await p.fill('input[name="user"]', 'admin'); await p.fill('input[name="password"]', 'gpu-obs-demo');
await p.click('button[type="submit"]'); await p.waitForURL(u => !u.toString().includes('/login'));
await p.goto(W(1), { waitUntil: 'load' }); await p.locator(panel(102)).waitFor({ timeout: 20000 }).catch(() => {}); await sleep(8000);

// both versions start recording at the same moment (SYNC=<dir>, PEERS=2): each writes a ready file, waits for all
if (process.env.SYNC) {
  fs.mkdirSync(process.env.SYNC, { recursive: true }); fs.writeFileSync(`${process.env.SYNC}/${OUT.replace(/\W/g, '_')}`, '');
  const end = Date.now() + 120000;
  while (fs.readdirSync(process.env.SYNC).length < +(process.env.PEERS || 2) && Date.now() < end) await sleep(200);
}

// ---------- recording ----------
rec = true; t0 = Date.now(); const cap = capLoop();
await hold(3);

// ===== Screen 1: What does the GPU say? =====
cues.push(`${ts()}  [screen 1: What does the GPU say?]`);
await box(panel(101));
await caption('One flag: the GPU exporter asks the kubelet which pod owns each GPU', 'Every GPU metric now carries the pod name');
await sleep(10000);                          // fixed (not PACE) until the load starts: both versions hit it together
const g1r = await gb(R), g1b = await gb(B);
await box(panel(10));
await caption(`GPU memory: red ${g1r} GB, blue ${g1b} GB`, 'No traffic yet. Red reserved 8% of the GPU, blue 90%.');
await sleep(10000);
await box(null); await caption('', '');
await term('demo/load.sh'); const tLoad = Date.now();
if (START_LOAD) exec(`kubectl --request-timeout=30s -n inference delete job vllm-loadgen --ignore-not-found --wait=true --timeout=30s; kubectl --request-timeout=30s apply -f ${REPO}/manifests/20-vllm/loadgen-job.yaml`,
  (e, o, er) => console.log('load:', e ? er : 'started'));
await caption('Start the load: the same traffic to both pods', '192 long requests each, all the time');
await sleep(6000); await term(null);
await box(panel(11));
await until(async () => (await inflight(R)) > 100 && (await inflight(B)) > 100, 120000, 'inflight');
await caption('Requests arrive: the same number in flight on both pods', '');
await hold(7);
await box(panel(10));
await caption(`GPU memory, under load: still red ${await gb(R)} GB, blue ${await gb(B)} GB`, 'Not a wiggle. This chart cannot tell you which one is in trouble.');
await hold(10);
await box(panel(102)); await caption('', ''); await hold(5);
await box(null); await next(2);

// ===== Screen 2: What does the server say? =====
cues.push(`${ts()}  [screen 2: What does the server say?]`);
await box(hiLine(101, 'KV cache usage: 100'));
await caption('vLLM already writes this line every 10 seconds', 'Fluent Bit ships it; 15 lines of Lua turn it into a metric, with the pod name');
await hold(10);
await box(panel(20));
await caption('KV cache: the server\'s working memory for requests in flight', 'Watch red');
await until(async () => (await kv(R)) > 90, 180000, 'kv>90');
await hold(4);
const k2r = await kv(R), k2b = await kv(B);
await caption(`Red: ${k2r}% full, ${Math.round((Date.now() - tLoad) / 1000)} s into the load. Blue: ${k2b}%.`, 'Red has run out of room. New requests have to wait.');
await hold(10);
await box(panel(22));
await caption('Cross-check: the same number from vLLM\'s own /metrics', 'The log line tells the truth');
await hold(8);
const t2r = await tps(R), t2b = await tps(B);
await box(panel(21));
await caption(`Same traffic to both. Red makes fewer tokens: ${t2r} vs ${t2b} per second`, '');
await hold(8);
await box(panel(102)); await caption('', ''); await hold(5);
await box(null); await next(3);

// ===== Screen 3: Why was this request slow? =====
cues.push(`${ts()}  [screen 3: Why was this request slow?]`);
await until(async () => (await avg('request_queue_time_seconds', R)) > 3, 120000, 'queue>3');
const qr = await avg('request_queue_time_seconds', R), ir = await avg('request_inference_time_seconds', R);
const qb = await avg('request_queue_time_seconds', B);
await box(panel(30));
await caption(`Red: ${secs(qr)} waiting for room, ${secs(ir)} on the GPU`, `Blue waits ${secs(qb)}. Same GPU, same traffic.`);
await hold(11);
await box(hiLine(101, 'k8s.pod.name'));
await caption('vLLM sends a span per request. The Collector adds the pod name.', 'The app never knew its pod name');
await hold(9);
await box(panel(31));
await caption('The slowest requests on red. Click one.', '');
await hold(6);
await box(null); await caption('', '');
const first = p.locator(`${panel(31)} a`).first();
const tid = ((await first.textContent({ timeout: 10000 }).catch(() => '')) || '').trim();
let pod = '', qSpan = NaN;
try {
  const tr = (await (await fetch(`http://localhost:16686/api/traces/${tid}`)).json()).data[0];
  const sp = tr.spans.find(s => s.operationName === 'llm_request');
  pod = tr.processes[sp.processID].tags.find(t => t.key === 'k8s.pod.name')?.value || '';
  qSpan = +(sp.tags.find(t => t.key === 'gen_ai.latency.time_in_queue')?.value);
} catch (e) { console.log('trace api', e.message); }
await clickOn(first);
await p.waitForURL(u => u.toString().includes('/explore'), { timeout: 20000 }).catch(() => {});
await sleep(6000);
const outline = p.getByRole('button', { name: /^Outline$/ });
if (await outline.count()) { await outline.first().click().catch(() => {}); await sleep(800); }
const rowVllm = p.getByRole('switch', { name: /llm_request/ }).first();
const rowClient = p.getByRole('switch', { name: /chat request/ }).first();
await box(rowClient, rowVllm);
await caption('One request, two hops: the client, then vLLM', 'One trace, end to end');
await hold(8);
await box(null);
await clickOn(rowVllm); await sleep(1500);
const attrs = p.getByText(/^Span Attributes:?$/).first();
if (await attrs.count()) { await clickOn(attrs); await sleep(1000); }
const qRow = p.locator('tr', { hasText: 'gen_ai.latency.time_in_queue' }).first();
if (await qRow.count()) {
  await qRow.scrollIntoViewIfNeeded().catch(() => {}); await sleep(500);
  await box(qRow);
  await caption(Number.isFinite(qSpan) ? `vLLM's own timing on the span: ${secs(qSpan)} in the queue` : 'vLLM\'s own timing on the span: time in the queue',
    'This request waited for room before the GPU touched it');
  await hold(9); await box(null);
}
const res = p.getByText(/^Resource Attributes:?$/).first();
await clickOn(res); await sleep(1200);
const podRow = p.getByText('k8s.pod.name', { exact: true }).first();
await podRow.scrollIntoViewIfNeeded().catch(() => {}); await sleep(600);
await box(podRow.locator('xpath=ancestor::tr[1]'));
await caption('The pod name, on the request', 'Added by the OTel Collector');
await hold(8);
await rowVllm.scrollIntoViewIfNeeded().catch(() => {});
await box(null); await caption('', '');
const chain = rowVllm.locator('xpath=following::button[1]');
await clickOn(chain); await sleep(1000);
const kvLink = p.getByRole('link', { name: /This pod: how full it was/ });
await box(kvLink);
await caption('One click: from this request to that pod', 'Grafana uses the pod name on the span to find its metrics', 'top');
await hold(7);
await box(null); await caption('', '');
await clickOn(kvLink); await sleep(8000);
const right = p.locator('[data-testid="data-testid Panel header Graph"]').first();
const kvNow = Math.round(await one(`max_over_time(vllm_log_kv_cache_usage_pct{pod_name="${pod}"}[5m])`));
await box(right);
await caption(`That pod during this request: ${Number.isFinite(kvNow) ? kvNow + '% full' : 'full'}`, 'The slow request, explained in one click');
await hold(10);

// the same request on blue, for contrast: back to screen 3 (browser Back, as on stage), click a blue trace
await box(null); await caption('', '');
for (let i = 0; i < 3 && !p.url().includes('gpu-walk-3'); i++) { await p.goBack().catch(() => {}); await sleep(1500); }
if (!p.url().includes('gpu-walk-3')) await p.goto(W(3));
await p.locator(panel(32)).waitFor({ timeout: 15000 }).catch(() => {}); await sleep(5000);
await box(panel(32));
await caption('Now the same kind of request on blue', 'Same model, same GPU, same traffic');
await hold(6);
await box(null); await caption('', '');
const bFirst = p.locator(`${panel(32)} a`).first();
const bTid = ((await bFirst.textContent({ timeout: 10000 }).catch(() => '')) || '').trim();
let qBlue = NaN;
try { const tr = (await (await fetch(`http://localhost:16686/api/traces/${bTid}`)).json()).data[0];
      qBlue = +(tr.spans.find(s => s.operationName === 'llm_request').tags.find(t => t.key === 'gen_ai.latency.time_in_queue')?.value); } catch {}
await clickOn(bFirst);
await p.waitForURL(u => u.toString().includes('/explore'), { timeout: 20000 }).catch(() => {});
await sleep(6000);
const bRow = p.getByRole('switch', { name: /llm_request/ }).first();
await clickOn(bRow); await sleep(1500);
const bAttrs = p.getByText(/^Span Attributes:?$/).first();
if (await bAttrs.count()) { await clickOn(bAttrs); await sleep(1000); }
const bq = p.locator('tr', { hasText: 'gen_ai.latency.time_in_queue' }).first();
if (await bq.count()) { await bq.scrollIntoViewIfNeeded().catch(() => {}); await sleep(500); await box(bq); }
await caption(`Blue: ${Number.isFinite(qBlue) ? secs(qBlue) : 'almost nothing'} in the queue. Red: ${Number.isFinite(qSpan) ? secs(qSpan) : 'seconds'}.`,
  'Same request. The only difference is how much room the server reserved.');
await hold(10);

// ===== Screen 4: Is 8% too low? Is 90% too high? =====
await box(null); await caption('', '');
await p.goto(W(4), { waitUntil: 'load' }); await p.locator(panel(102)).waitFor({ timeout: 15000 }).catch(() => {}); await sleep(6000);
cues.push(`${ts()}  [screen 4: Is 8% too low? Is 90% too high?]`);
await box(panel(101));
await caption('Our rule of thumb, not vLLM\'s: peak KV cache under real traffic', 'Above 90%: memory-constrained. Below 40%: over-provisioned.');
await hold(10);
await box(panel(40));
await caption('Red: memory-constrained. Blue: over-provisioned.', 'Both settings were wrong, in opposite directions');
await hold(9);
const t4r = await avg('time_to_first_token_seconds', R), t4b = await avg('time_to_first_token_seconds', B);
await box(panel(41), panel(43));
await caption(`GPU memory never showed it. Time to first token: red ${secs(t4r)}, blue ${secs(t4b)}`, 'That is what the user feels');
await hold(11);
await box(panel(102)); await caption('', ''); await hold(7);
await box(null); await hold(3);

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
