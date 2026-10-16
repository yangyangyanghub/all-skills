#!/usr/bin/env node
/**
 * verify-library-online.js — 资料库路线「线上发布态」核验（playwright 免登录实测）
 * =============================================================================
 * 用途：4B 发布后确认 workbuddy.link 线上跑的确实是本地刚改的新版本。
 *       本地四关（syntax / quiz-modify / jsdom 冒烟 / pagesync）全 PASS ≠ 线上已生效，
 *       发布通道可能降级、覆盖可能落旧版本——必须拉线上真身核对标记。
 *
 * 用法：
 *   node verify-library-online.js <线上URL> [额外标记文件]
 *   NODE_PATH 需指向含 playwright 的 node_modules。
 *   例：NODE_PATH=... node verify-library-online.js https://workbuddy.link/p/<node_id>
 *
 * 原理（三个实测坑都已内置处理）：
 *   1. 资料库外壳用 iframe 加载课件，且 `workbuddy.link/p/<id>` 直拉只有 ~4.7KB 外壳、
 *      静态资源路径 NoSuchKey（内容经 API 动态加载）——curl 拉不到源码，必须真浏览器遍历 frames。
 *   2. 跨域 iframe 的 frame.content() 会【挂起】导致整体超时被 SIGTERM——
 *      必须逐个 frame.evaluate(outerHTML) 并 Promise.race 超时兜底（勿用 content()）。
 *   3. MQTT 长连接令 networkidle 永不触发——waitUntil 用 domcontentloaded + 固定等待。
 *      另加 150s 看门狗强退（playwright/broker 挂起时脚本永不结束，实测挂到 7 分钟）。
 *
 * 判定逻辑：内置 MQTT 版课件通用标记；「❌应消失」类标记出现即 FAIL。
 *   额外标记文件：每行一条，格式 `标记`（须出现）或 `!标记`（须为零）。
 *
 * 退出码：0=PASS（或根本没抓到任何课件内容时以聚合长度提示人工复核）；1=FAIL。
 * 来源：世界的本质与规律课件 4B 发布核验实战（2026-09-30 固化），8 项实测通过。
 * =============================================================================
 */
const { chromium } = require('playwright');
const fs = require('fs');

const WATCHDOG_MS = 150000;

// 内置标记：[片段, 说明]。说明以「❌」开头 = 该片段线上必须为 0（出现即旧版/缺陷）。
const BUILTIN_MARKS = [
  ['var NODE_ID', '发布常量 NODE_ID 已注入'],
  ['var PUBLISH_BASE', '发布常量 PUBLISH_BASE 已注入'],
  ['subscribe(SYNC_TOPIC', '页码广播话题已订阅（漏订=学生永久不跟随）'],
  ['subscribe(SYNC_CTL_TOPIC', '控制话题已订阅（漏订=claim仲裁与秒级跳页静默失效）'],
  ['function startBroadcast', '标准件 startBroadcast'],
  ['function canStudentNavigate', '标准件 canStudentNavigate'],
  ['function getPageParam', 'getPageParam（hash→search 参数读取）'],
  ['xmn_teacher_', '教师身份键绑 NODE_ID'],
  ['new URLSearchParams', '❌旧式 URL 参数直读应已清零'],
  ["DEFAULT-CLASS'", '❌DEFAULT-CLASS 字面量兜底应已清零（串台）'],
];

function loadExtraMarks(file) {
  if (!file) return [];
  const out = [];
  fs.readFileSync(file, 'utf8').split(/\r?\n/).forEach((line) => {
    const t = line.trim();
    if (!t || t.startsWith('#')) return;
    if (t.startsWith('!')) out.push([t.slice(1), '❌(自定义)线上必须为 0: ' + t.slice(1)]);
    else out.push([t, '(自定义)线上必须出现: ' + t]);
  });
  return out;
}

const withTimeout = (p, ms, dflt) =>
  Promise.race([p.catch(() => dflt), new Promise((r) => setTimeout(() => r(dflt), ms))]);

// 同步写 stdout/stderr：SIGTERM/崩溃时管道缓冲会丢日志，关键行必须 writeSync 才保得住
const log = (s) => { try { fs.writeSync(1, s + '\n'); } catch (e) {} };
const logErr = (s) => { try { fs.writeSync(2, s + '\n'); } catch (e) {} };

(async () => {
  const url = process.argv[2];
  if (!url || url.startsWith('-')) {
    logErr('用法: node verify-library-online.js <线上URL> [额外标记文件]');
    process.exit(2);
  }
  const marks = BUILTIN_MARKS.concat(loadExtraMarks(process.argv[3]));

  // 看门狗：任何挂起（browser/CDN/broker）150s 强杀，绝不悬挂。
  // ⚠ 必须先 kill 浏览器进程再 exit：否则 chrome 子进程仍握住管道写端，
  //   外层 `| tail` 永等 EOF → 整条命令被外部超时强杀 → 所有日志丢失（实测坑）。
  const watchdog = setTimeout(() => {
    logErr('WATCHDOG: ' + (WATCHDOG_MS / 1000) + 's 强制退出（页面/浏览器挂起）');
    try { browser.process().kill(); } catch (e) {}
    process.exit(3);
  }, WATCHDOG_MS);

  const browser = await chromium.launch({ timeout: 30000 });
  const page = await browser.newPage();
  let gotoMsg = 'ok';
  try {
    // ⚠ 必须用 commit：资料库外壳的 domcontentloaded 实测会永久挂起（CDP 层超时也不兑现），
    //   等它=整体卡死。commit 1s 返回，外壳 HTML 到位，iframe 内容由下方固定等待+自适应补等兜底。
    await page.goto(url, { waitUntil: 'commit', timeout: 20000 });
  } catch (e) { gotoMsg = 'warn: ' + String(e.message).split('\n')[0]; }
  await page.waitForTimeout(6000);

  const grabAll = async (timeoutMs) => {
    const fs2 = page.frames();
    const hs = await Promise.all(fs2.map((f) => withTimeout(
      f.evaluate(() => document.documentElement.outerHTML), timeoutMs, '')));
    return { html: hs.join(''), n: fs2.length };
  };
  // ⚠ 超时必须随课件体积放大：base64 内联图的大课件（30MB+）在 iframe 内求值
  //   outerHTML 远超 8s，会被 withTimeout 兜底成空串 → 聚合只剩外壳 → 全项误报 FAIL。
  //   2026-10-02 印象派（40.7MB 单文件）实测：8s 抓空、12s 抓全。故按体积自适应。
  const isHuge = (await page.content()).length > 4000000;
  const T0 = isHuge ? 45000 : 8000;
  let g = await grabAll(T0);
  // 自适应补等：外壳先到、iframe 课件尚未注入时会抓到过短内容，补等再抓一次
  if (g.html.length < 20000) {
    await page.waitForTimeout(5000);
    const g2 = await grabAll(T0);
    if (g2.html.length > g.html.length) g = g2;
  }
  // 大体积课件：首抓可能只拿到部分 frame，再补抓一次并取更长者
  if (g.html.length > 20000 && g.html.length < 30000000) {
    await page.waitForTimeout(3000);
    const g3 = await grabAll(T0);
    if (g3.html.length > g.html.length) g = g3;
  }
  const frames = page.frames();
  const all = g.html;
  log('URL         : ' + url);
  log('goto        : ' + gotoMsg);
  log('frames      : ' + frames.length);
  log('聚合HTML长度: ' + all.length + (all.length < 20000 ? ' ⚠ 过短：可能只抓到外壳，结果仅供参考' : ''));
  log('--- 标记核验 ---');
  let fail = 0;
  for (const [m, desc] of marks) {
    const n = all.split(m).length - 1;
    const wantZero = desc.indexOf('❌') === 0;
    const ok = wantZero ? n === 0 : n > 0;
    if (!ok) fail++;
    log('  ' + (ok ? 'PASS' : 'FAIL') + ' | x' + n + ' | ' + desc);
  }
  log(fail === 0 ? '\nRESULT: ONLINE VERIFY PASS' : '\nRESULT: ONLINE VERIFY FAIL (' + fail + ')');
  clearTimeout(watchdog);
  try { await withTimeout(browser.close(), 5000, null); } catch (e) {}
  try { if (browser.process()) browser.process().kill(); } catch (e) {}
  process.exit(fail === 0 ? 0 : 1);
})().catch((e) => { logErr('FATAL: ' + (e && e.message)); process.exit(4); });
