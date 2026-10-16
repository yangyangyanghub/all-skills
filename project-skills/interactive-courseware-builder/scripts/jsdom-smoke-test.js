// jsdom 冒烟测试（通用版）：无需浏览器、不联网，快速验证第四代课件 HTML 可运行且关键结构齐全。
// 用法: node jsdom-smoke-test.js <courseware.html> [--pages 14]
// 依赖: npm install jsdom（装到任意 node_modules 目录后配 NODE_PATH 指向该目录）
// 定位: publish_to_library.py 发布前的最后一道关卡，与 syntax-check.js（纯语法）互补——
//       本脚本能抓到「运行时初始化中断」类缺陷（如缺 scrollIntoView 导致脚本后半段不执行、常量注入失败）。
const fs = require('fs');
const path = require('path');
const { JSDOM, VirtualConsole } = require('jsdom');

const args = process.argv.slice(2);
const file = args[0];
if (!file) { console.error('用法: node jsdom-smoke-test.js <courseware.html> [--pages N]'); process.exit(2); }
const pagesIdx = args.indexOf('--pages');
const expectPages = pagesIdx >= 0 ? parseInt(args[pagesIdx + 1], 10) : null;

const html = fs.readFileSync(file, 'utf8');

// jsdom 环境桩：canvas / scrollIntoView / toDataURL（jsdom 未实现，真浏览器无需）
function ctxStub(canvas) {
  const noop = function () {};
  return {
    canvas: canvas, fillStyle: '', strokeStyle: '', lineWidth: 1, font: '',
    globalAlpha: 1, textAlign: 'left', textBaseline: 'alphabetic', lineCap: 'butt',
    shadowBlur: 0, shadowColor: '', lineJoin: 'miter',
    save: noop, restore: noop, beginPath: noop, closePath: noop, moveTo: noop,
    lineTo: noop, arc: noop, rect: noop, fill: noop, stroke: noop, fillRect: noop,
    strokeRect: noop, clearRect: noop, translate: noop, rotate: noop, scale: noop,
    setTransform: noop, setLineDash: noop, quadraticCurveTo: noop, bezierCurveTo: noop,
    arcTo: noop, ellipse: noop, clip: noop, drawImage: noop, putImageData: noop,
    fillText: noop, strokeText: noop,
    measureText: function (t) { return { width: (t ? String(t).length : 0) * 8 }; },
    createLinearGradient: function () { return { addColorStop: noop }; },
    createRadialGradient: function () { return { addColorStop: noop }; },
    getImageData: function (x, y, w, h) { return { data: new Uint8ClampedArray(w * h * 4) }; },
  };
}

const errors = [];
const dom = new JSDOM(html, {
  runScripts: 'dangerously',
  pretendToBeVisual: true,
  url: 'https://workbuddy.link/p/test/',   // 模拟发布环境（https，让 IS_DEPLOYED 判定走线上分支）
  beforeParse(window) {
    window.HTMLCanvasElement.prototype.getContext = function () { return ctxStub(this); };
    window.Element.prototype.scrollIntoView = function () {};
    window.HTMLCanvasElement.prototype.toDataURL = function () { return 'data:image/png;base64,'; };
  },
  virtualConsole: new VirtualConsole()
    .on('jsdomError', e => errors.push('jsdomError: ' + e.message))
    .on('error', (...a) => errors.push('console.error: ' + a.join(' '))),
});
const w = dom.window;
const d = w.document;

let pass = 0, fail = 0;
function ck(name, cond, extra) {
  if (cond) { pass++; console.log('  PASS  ' + name); }
  else { fail++; console.log('  FAIL  ' + name + (extra ? '  <- ' + extra : '')); }
}

setTimeout(() => {
  console.log('=== jsdom smoke: ' + path.basename(file));
  ck('无脚本错误（初始化完整跑通）', errors.length === 0, errors.slice(0, 3).join(' | '));

  // ---- 页面结构 ----
  const secs = d.querySelectorAll('section.page');
  if (expectPages) ck('页面数 = ' + expectPages, secs.length === expectPages, 'got ' + secs.length);
  else ck('页面数 > 0', secs.length > 0, 'got ' + secs.length);
  ck('PAGE_IDS 与 section 数一致', Array.isArray(w.PAGE_IDS) && w.PAGE_IDS.length === secs.length,
     w.PAGE_IDS ? 'len=' + w.PAGE_IDS.length : 'undefined（⚠ 若前半段函数在、常量 undefined，多半是初始化中断）');
  const missing = (w.PAGE_IDS || []).filter(id => !d.getElementById(id));
  ck('PAGE_IDS 全部有对应 section', missing.length === 0, missing.join(','));

  // ---- 教学控制标准件函数（MQTT 版）----
  ['showPage', 'nextPage', 'prevPage', 'submitQuiz', 'showToast', 'showConfirmModal',
   'startBroadcast', 'stopBroadcast', 'requestCurrentPage', 'canStudentNavigate',
   'xmnBroadcastPage', 'handleControlMessage', 'handleSyncMessage',
   'openDetail', 'closeDetail', 'toggleQRPopup', 'closeQRPopup', 'updateBadgeStats',
  ].forEach(fn => ck('函数 ' + fn, typeof w[fn] === 'function'));

  // ---- 测验容器（自动探测，不写死）----
  const quizMap = w.ACTIVITY_QUIZ_MAP || {};
  const quizIds = Object.keys(quizMap).filter(k => quizMap[k]);
  quizIds.forEach(act => {
    const cid = quizMap[act];
    const c = d.getElementById(cid);
    ck('测验渲染 ' + act + ' (' + cid + ') 题数>0', c && c.querySelectorAll('.quiz-q').length > 0,
       c ? 'n=' + c.querySelectorAll('.quiz-q').length : '容器不存在');
    ck('提交按钮 ' + cid + '_submitBtn', !!d.getElementById(cid + '_submitBtn'));
    ck('QR 徽章 ' + cid, !!c && !!c.querySelector && !!d.querySelector('[data-quiz="' + cid + '"], #' + cid + ' .qr-badge, .qr-badge[data-act="' + act + '"]') || !!d.querySelector('.qr-badge'));
  });
  ck('至少探测到一个测验活动', quizIds.length > 0, 'ACTIVITY_QUIZ_MAP=' + JSON.stringify(quizMap).slice(0, 120));
  ck('QR 徽章存在', d.querySelectorAll('.qr-badge').length >= quizIds.length,
     'n=' + d.querySelectorAll('.qr-badge').length + ' / 活动数 ' + quizIds.length);
  // v2026-10-13 每页徽章制：每个页面 section 各注入 1 枚徽章；活动页（测验/仿真）徽章带 data-activity
  //   且各配 1 个统计弹窗；非活动页徽章共用 1 个加入弹窗（#qrPopup_join）。
  //   故正确关系：弹窗数 = 活动徽章数 + 1，徽章数 = 页数。旧的「徽章数 === 弹窗数」在此形态下属误报。
  const badgeN = d.querySelectorAll('.qr-badge').length;
  const actBadgeN = d.querySelectorAll('.qr-badge[data-activity]').length;
  const popupN = d.querySelectorAll('.qr-popup').length;
  const pageN = (typeof w.PAGE_IDS !== 'undefined' && w.PAGE_IDS.length) || expectPages || 0;
  ck('QR 弹窗与徽章配对（每页徽章制）', popupN === actBadgeN + 1 && (pageN === 0 || badgeN === pageN),
     'badge=' + badgeN + ' activity=' + actBadgeN + ' popup=' + popupN + ' pages=' + pageN);

  // ---- 常量注入（⚠ 若这里 undefined 但函数都在，= 初始化中断，查 scrollIntoView 之类的环境依赖）----
  ck('NODE_ID 已声明', typeof w.NODE_ID === 'string', typeof w.NODE_ID);
  ck('PUBLISH_BASE 已声明', typeof w.PUBLISH_BASE === 'string', typeof w.PUBLISH_BASE);
  ck('SYNC_TOPIC 非空', typeof w.SYNC_TOPIC === 'string' && w.SYNC_TOPIC.length > 4, String(w.SYNC_TOPIC));
  ck('CLASS_ID 非空且非 DEFAULT', typeof w.CLASS_ID === 'string' && w.CLASS_ID !== '' && w.CLASS_ID.indexOf('DEFAULT') === -1, String(w.CLASS_ID));

  // ---- 翻页 ----
  try {
    const id0 = w.PAGE_IDS[0], id1 = w.PAGE_IDS[1];
    w.showPage(1);
    ck('showPage(1) -> 第2页 active', d.getElementById(id1).classList.contains('active'));
    w.showPage(0);
    ck('showPage(0) -> 第1页 active', d.getElementById(id0).classList.contains('active'));
  } catch (e) { ck('showPage 可调用', false, e.message); }

  // ---- 学生答题可点选（离线：mqtt 未连，走本地聚合）----
  try {
    const cid = quizMap[Object.keys(quizMap)[0]];
    const firstQ = d.getElementById(cid).querySelector('.quiz-q');
    firstQ.querySelector('.opt').click();
    ck('选项可点选', firstQ.querySelectorAll('.opt.selected, .opt.correct, .opt.wrong').length > 0);
  } catch (e) { ck('选项可点选', false, e.message); }

  console.log('RESULT: ' + (fail === 0 ? 'ALL PASS' : 'FAIL=' + fail) + ' (' + (pass + fail) + ' 项)');
  if (errors.length) console.log('errors:\n' + errors.slice(0, 8).join('\n'));
  process.exit(fail === 0 ? 0 : 1);
}, 800);
