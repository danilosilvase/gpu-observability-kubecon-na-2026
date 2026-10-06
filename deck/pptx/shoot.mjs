import { chromium } from 'playwright';
const [,, from, to, outdir] = process.argv;
const base = 'http://localhost:3000';
const browser = await chromium.launch();
const ctx = await browser.newContext({ viewport: { width: 1400, height: 620 }, deviceScaleFactor: 3 });
const page = await ctx.newPage();
await page.goto(`${base}/login`);
await page.fill('input[name="user"]', 'admin');
await page.fill('input[name="password"]', 'gpu-obs-demo');
await page.click('button[type="submit"]');
await page.waitForURL(u => !u.toString().includes('/login'), { timeout: 20000 });
await page.waitForTimeout(1000);
const ids = (process.env.IDS||"2,3,4,6,7,8,10,11,12").split(",").map(Number); const vh=Number(process.env.VH||620); await page.setViewportSize({width:1400,height:vh});
for (const id of ids) {
  const url = `${base}/d-solo/gpu-inference-obs/x?orgId=1&panelId=${id}&from=${from}&to=${to}&var-pod=All&theme=dark`;
  await page.goto(url, { waitUntil: 'networkidle' });
  await page.waitForTimeout(3000);
  const title = await page.locator('h2').first().textContent().catch(()=> '');
  await page.screenshot({ path: `${outdir}/panel-${id}${process.env.SUFFIX||""}.png` });
  console.log(id, JSON.stringify(title));
}
await browser.close();
