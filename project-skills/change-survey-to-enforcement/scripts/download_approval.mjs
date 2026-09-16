// 下载某个图斑的「批文矢量附件 .zip」
//
// 用法：
//   node adapter/download_approval.mjs --id 130403SJBG26210183 --out <目录>
//
// 流程：
//   ① 打开该图斑详情页（列表里找行 → 点「详情」→ 校验图斑编号）
//   ② 点「批文矢量附件」的绿色下载按钮
//   ③ 截获预签名 URL（frameRequestedNavigation，导航发生在下载前）
//   ④ fetch 下载（预签名 URL 无需 cookie）→ 保存 .zip
//
// 依赖：调试浏览器已登录（CDP 9222）
import { mkdirSync, writeFileSync } from 'node:fs';
import { pathToFileURL } from 'node:url';

const DEFAULT_PORT = 9222;
const LIST_URL = 'http://121.29.50.223:8085/hbgty/#/biz/user/d27f325f-e178-42b3-9820-b2f70b47b84c/1/2026/spotListSHDBgdc';

// ---------- 参数解析 ----------
const argv = process.argv.slice(2);
function arg(name, dflt) {
  const i = argv.indexOf(name);
  return i >= 0 ? argv[i + 1] : dflt;
}
const id = arg('--id');
const outDir = arg('--out', '.');
const port = Number(arg('--port', String(DEFAULT_PORT)));
if (!id) { console.error('需要 --id <图斑编号>'); process.exit(1); }
mkdirSync(outDir, { recursive: true });

// ---------- CDP ----------
async function getPage() {
  const tabs = await (await fetch(`http://127.0.0.1:${port}/json`)).json();
  return tabs.find(t => t.type === 'page' && /^https?:/.test(t.url));
}
function connect(wsUrl) {
  return new Promise((resolve, reject) => {
    const ws = new WebSocket(wsUrl);
    let mid = 0; const pending = new Map(); const listeners = [];
    ws.onerror = () => reject(new Error('WebSocket 连接失败'));
    ws.onopen = () => resolve({
      send(method, params = {}) {
        return new Promise((res, rej) => { const i = ++mid; pending.set(i, { res, rej }); ws.send(JSON.stringify({ id: i, method, params })); });
      },
      on(method, cb) { listeners.push([method, cb]); },
      close: () => ws.close(),
    });
    ws.onmessage = (ev) => {
      const m = JSON.parse(ev.data);
      for (const [method, cb] of listeners) if (m.method === method) cb(m.params);
      if (m.id && pending.has(m.id)) { const p = pending.get(m.id); pending.delete(m.id); m.error ? p.rej(new Error(JSON.stringify(m.error))) : p.res(m); }
    };
  });
}
const sleep = (ms) => new Promise(r => setTimeout(r, ms));

// ---------- 主流程 ----------
const page = await getPage();
const cdp = await connect(page.webSocketDebuggerUrl);
await cdp.send('Page.enable');

// ① 打开图斑详情（列表 → 找行 → 点详情）
await cdp.send('Page.navigate', { url: LIST_URL });
await sleep(6000);
const open = await cdp.send('Runtime.evaluate', {
  expression: `(() => {
    const rows = [...document.querySelectorAll('tr')].filter(tr => tr.innerText.includes('${id}'));
    if (!rows.length) return 'ROW_NOT_FOUND';
    const btns = [...rows[0].querySelectorAll('button,a,span')].filter(e => e.textContent.trim() === '详情');
    if (!btns.length) return 'BTN_NOT_FOUND';
    btns[0].click(); return 'CLICKED';
  })()`, returnByValue: true,
});
const openResult = open.result?.result?.value;
if (openResult !== 'CLICKED') { console.error(`打开详情失败: ${openResult}（图斑 ${id} 可能不在第一页）`); cdp.close(); process.exit(1); }
await sleep(3000);

// ② 点 zip 下载按钮 + 截获导航 URL
const navs = [];
cdp.on('Page.frameRequestedNavigation', (p) => { if (p.url.startsWith('http')) navs.push(p.url); });
await cdp.send('Runtime.evaluate', {
  expression: `(() => {
    const btns = [...document.querySelectorAll('button')].filter(b => b.querySelector('.el-icon-download'));
    if (!btns.length) return 'NO_BTN';
    btns[btns.length - 1].click();  // 最后一个 = 批文矢量附件 .zip
    return 'CLICKED';
  })()`, returnByValue: true,
});
await sleep(6000);

// ③ 找 .zip 的预签名 URL
const zipUrl = navs.find(u => /\.zip/i.test(decodeURIComponent(u)));
if (!zipUrl) { console.error('未捕获到 .zip 导航 URL。全部导航:', navs.map(u => decodeURIComponent(u).slice(0, 80))); cdp.close(); process.exit(1); }
cdp.close();

// ④ fetch 下载
const resp = await fetch(zipUrl);
const buf = Buffer.from(await resp.arrayBuffer());
const fn = decodeURIComponent(zipUrl.match(/\/([^/?]+\.zip)(\?|$)/)?.[1] || `${id}_批文矢量.zip`);
const outPath = outDir.replace(/\\/g, '/') + '/' + fn;
writeFileSync(outPath, buf);
console.log(JSON.stringify({
  id, fileName: fn, path: outPath, bytes: buf.length, httpStatus: resp.status,
  isZip: buf.slice(0, 4).toString('hex') === '504b0304',
  url: decodeURIComponent(zipUrl).slice(0, 160),
}, null, 2));
