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
const reqTime = async (re) => Math.max(0, ...(await prom(`sum by (pod) (rate(vllm:time_to_first_token_seconds_sum{pod=~"${re}"}[2m])) / sum by (pod) (rate(vllm:time_to_first_token_seconds_count{pod=~"${re}"}[2m]))`)).map(x => x[1]).filter(Number.isFinite));
const panel = id => `[data-panelid="${id}"]`;
const DASH = `${G}/d/gpu-inference-obs?orgId=1&kiosk&from=now-5m&to=now&refresh=5s`;

// ---------- set-up (not recorded): the rig must be idle, so the demo starts on "OK / OK" ----------
{
  const running = await new Promise(r => exec('kubectl -n inference get pods -l app=vllm-loadgen --field-selector=status.phase=Running --no-headers 2>/dev/null', (e, o) => r(o.trim())));
  // 6 min of quiet: the stage dashboard shows the last 5 min, so no old traces or tiles from a previous load
  const traffic = await prom('sum(increase(vllm:request_success_total[6m])) > 0');
  const hot = await prom('vllm_log_kv_cache_usage_pct > 5');
  if (running || traffic.length || hot.length) { console.log('DIRTY: not idle', running, traffic, hot.length); process.exit(2); }
  console.log('idle check OK');
}
await p.goto(`${G}/login`);
await p.fill('input[name="user"]', 'admin'); await p.fill('input[name="password"]', 'gpu-obs-demo');
await p.click('button[type="submit"]'); await p.waitForURL(u => !u.toString().includes('/login'));
await p.goto(DASH, { waitUntil: 'load' }); await sleep(8000);

// ---------- recording ----------
rec = true; t0 = Date.now(); const cap = capLoop();

// S0 the question
await card(`<div style="font-size:30px;color:#ff9830;letter-spacing:2px">LIVE DEMO</div>
  <div style="font:700 64px/1.2 Inter,Helvetica,Arial;margin:14px 0 30px">Which pod is in trouble?</div>
  <div>Two vLLM pods · same model · same GPU (NVIDIA L4)</div>
  <div><span style="color:#f2495c">red</span>: 8% of the GPU memory &nbsp;·&nbsp; <span style="color:#5794f2">blue</span>: 90%</div>
  <div style="margin-top:30px;color:#9fa7b3;font-size:30px">Watch three numbers: GPU memory · how full the car park is (KV cache) · request time</div>`);
cues.push(`${ts()}  [title card: which pod is in trouble?]`);
await sleep(9000); await card(null); await sleep(800);

// S1 idle
await box(panel(1));
await caption('No traffic yet. Both pods: OK.', 'Same model, same GPU. One of them is about to fall over.');
await sleep(8000);
await box(panel(2), panel(4));
await caption('Three numbers per pod', 'GPU memory  ·  how full the car park is (KV cache)  ·  how long a request takes');
await sleep(8000);

// S2 load
await box(null);
exec(`kubectl -n inference delete job vllm-loadgen --ignore-not-found --wait=true && kubectl apply -f ${REPO}/manifests/20-vllm/loadgen-job.yaml`, (e, o, er) => console.log('load:', e ? er : 'started'));
await caption('Load starts', 'Lots of long requests to red  ·  a trickle to blue');
await sleep(9000);

// S3 the number we page on
await box(panel(2));
await caption('GPU memory: the number we page on', 'Flat. Red even looks the healthiest: it uses less.');
await sleep(10000);

// S4 the car park
await box(panel(3));
await caption('How full the car park is: KV cache %, from the server\'s own log', 'Fluent Bit reads the vLLM log line, 15 lines of Lua turn it into a number per pod');
await until(async () => (await kv('vllm-constrained.*')) > 90, 240000, 'kv>90');
await sleep(4000);
const kr = Math.round(await kv('vllm-constrained.*')), kb = Math.round(await kv('vllm-overprov.*'));
await caption(`Red: ${kr}% full. Blue: ${kb}%.`, 'The pod with less memory has run out of room. Nothing on the GPU memory tile moved.');
await sleep(10000);

// S5 what the user feels
await box(panel(4));
await until(async () => (await reqTime('vllm-constrained.*')) > 5, 150000, 'req>5');
await sleep(3000);
const rr = (await reqTime('vllm-constrained.*')).toFixed(0), rb = (await reqTime('vllm-overprov.*')).toFixed(2);
await caption(`Red requests take ${rr} s. Blue: ${rb} s.`, 'Same hardware. New requests wait for a space in the car park.');
await sleep(10000);

// S6 verdict
await until(async () => (await prom('max_over_time(vllm_log_kv_cache_usage_pct{pod_name=~"vllm-constrained.*"}[3m]) > 90')).length > 0, 60000, 'verdict');
await box(panel(1));
await caption('Red: memory-constrained. Blue: over-provisioned.', 'Only the log line could tell. The GPU exporter said both were fine.');
await sleep(10000);

// S7 one slow request
await box(panel(5));
await caption('The slowest requests on red (traces)', 'About 12 s each. Click one.', 'top');
await sleep(7000);
await box(null); await caption('', '');
const first = p.locator(`${panel(5)} a`).first();
const tid = ((await first.textContent({ timeout: 10000 }).catch(() => '')) || '').trim();
let pod = '';
try {
  const tr = (await (await fetch(`http://localhost:16686/api/traces/${tid}`)).json()).data[0];
  const sp = tr.spans.find(s => s.operationName === 'llm_request');
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
await caption('One request, two hops: the client, then vLLM', 'One trace from end to end');
await sleep(9000);
await box(null);
await clickOn(rowVllm); await sleep(1500);
const res = p.getByText(/^Resource Attributes:?$/).first();
await clickOn(res); await sleep(1200);
const podRow = p.getByText('k8s.pod.name', { exact: true }).first();
await podRow.scrollIntoViewIfNeeded().catch(() => {}); await sleep(600);
await box(podRow.locator('xpath=ancestor::tr[1]'));
await caption('The pod name, on the request', 'The OTel Collector added it. The app never knew its pod name.');
await sleep(10000);
await rowVllm.scrollIntoViewIfNeeded().catch(() => {});

// S8 one click to the cause
await box(null);
const chain = rowVllm.locator('xpath=following::button[1]');
await clickOn(chain); await sleep(1000);
const kvLink = p.getByRole('link', { name: /This pod: how full it was/ });
await box(kvLink);
await caption('One click: from this request to that pod', 'Grafana uses the pod name on the span to find the pod\'s metrics', 'top');
await sleep(7000);
await box(null); await caption('', '');
await clickOn(kvLink); await sleep(8000);
const right = p.locator('[data-testid="data-testid Panel header Graph"]').first();
const kvNow = Math.round(Math.max(0, ...(await prom(`max_over_time(vllm_log_kv_cache_usage_pct{pod_name="${pod}"}[5m])`)).map(x => x[1])));
await box(right);
await caption(`That pod's car park during this request: ${kvNow}% full`, 'The slow request, explained in one click');
await sleep(10000);

// S9 back to the dashboard
await box(null); await caption('', '');
await p.goto(DASH, { waitUntil: 'load' }); await sleep(6000);
await caption('Three signals, one pod name', 'GPU exporter: exported_pod  ·  Fluent Bit: pod_name  ·  OTel: k8s.pod.name');
await sleep(9000);

// S10 outro
await box(null); await caption('', '');
await card(`<div style="font:700 56px/1.2 Inter,Helvetica,Arial;margin-bottom:30px">The pod is the join key</div>
  <div>GPU memory says how big the car park is. Only the server's log says how full it is.</div>
  <div style="margin-top:26px;color:#9fa7b3">Watch: KV cache % · request time · SM active (not GPU util)</div>
  <div style="margin-top:8px;color:#9fa7b3">All configs in the repo: manifests/</div>`);
cues.push(`${ts()}  [end card]`);
await sleep(8000);

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
