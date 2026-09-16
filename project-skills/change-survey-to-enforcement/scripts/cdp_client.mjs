// CDP 只读客户端：连本地 Chrome 调试端口，读页面文本 / 执行 JS。
// 零依赖：使用 Node 22 内置 WebSocket。
const DEFAULT_PORT = 9222;

export async function getPageTarget(port = DEFAULT_PORT) {
  const res = await fetch(`http://127.0.0.1:${port}/json`);
  const tabs = await res.json();
  return tabs.find(t => t.type === 'page' && /^https?:/.test(t.url))
      || tabs.find(t => t.type === 'page')
      || null;
}

function connect(wsUrl) {
  return new Promise((resolve, reject) => {
    const ws = new WebSocket(wsUrl);
    let id = 0;
    const pending = new Map();
    ws.onerror = (e) => reject(new Error('WebSocket 连接失败: ' + (e.message || 'unknown')));
    ws.onopen = () => resolve({
      send(method, params = {}) {
        return new Promise((res2, rej) => {
          const mid = ++id;
          pending.set(mid, { res2, rej });
          ws.send(JSON.stringify({ id: mid, method, params }));
        });
      },
      close: () => ws.close(),
    });
    ws.onmessage = (ev) => {
      const msg = JSON.parse(ev.data);
      if (msg.id && pending.has(msg.id)) {
        const p = pending.get(msg.id);
        pending.delete(msg.id);
        if (msg.error) p.rej(new Error(JSON.stringify(msg.error)));
        else p.res2(msg);
      }
    };
  });
}

export async function evaluate(port, expr) {
  const target = await getPageTarget(port);
  if (!target) throw new Error('未找到可用页面，请确认 Chrome 已开调试端口');
  const cdp = await connect(target.webSocketDebuggerUrl);
  try {
    const r = await cdp.send('Runtime.evaluate', {
      expression: expr, returnByValue: true, awaitPromise: true,
    });
    if (r.result && r.result.exceptionDetails) {
      throw new Error(r.result.exceptionDetails.exception?.description || r.result.exceptionDetails.text);
    }
    return r.result && r.result.result ? r.result.result.value : undefined;
  } finally {
    cdp.close();
  }
}

export async function dumpText(port) {
  return await evaluate(port, 'document.body.innerText');
}

export async function navigate(port, url) {
  const target = await getPageTarget(port);
  const cdp = await connect(target.webSocketDebuggerUrl);
  try {
    await cdp.send('Page.navigate', { url });
    await new Promise(r => setTimeout(r, 3000));
  } finally {
    cdp.close();
  }
  return await evaluate(port, 'location.href');
}

export async function clickByText(port, text) {
  const js = `(() => {
    const target = ${JSON.stringify(text)};
    const all = [...document.querySelectorAll('button,a,span,div,li')];
    const hits = all.filter(e => e.textContent.trim() === target);
    if (!hits.length) return 'NOT_FOUND';
    hits[0].click();
    return 'CLICKED:' + hits.length;
  })()`;
  return await evaluate(port, js);
}

// CLI
import { pathToFileURL } from 'node:url';
const isMain = process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href;
if (isMain) {
  const fs = await import('node:fs');
  const [cmd, arg] = process.argv.slice(2);
  const port = Number(process.env.CDP_PORT || DEFAULT_PORT);
  if (cmd === 'url') console.log(await evaluate(port, 'location.href'));
  else if (cmd === 'title') console.log(await evaluate(port, 'document.title'));
  else if (cmd === 'dump') console.log(await dumpText(port));
  else if (cmd === 'dumpfile') {
    const text = await dumpText(port);
    fs.writeFileSync(arg, text, 'utf8');
    console.log(`written ${text.length} chars → ${arg}`);
  } else if (cmd === 'click') console.log(await clickByText(port, arg));
  else if (cmd === 'nav') console.log('→', await navigate(port, arg));
  else if (cmd === 'eval') {
    const js = fs.readFileSync(arg, 'utf8');
    const out = await evaluate(port, js);
    fs.writeFileSync(arg + '.out.json', JSON.stringify(out, null, 2), 'utf8');
    console.log(`eval done → ${arg}.out.json`);
  } else console.log('usage: node cdp_client.mjs <url|title|dump|dumpfile <out>|click <text>|nav <url>|eval <js-file>>');
}
