#!/usr/bin/env node
// deploy-state-test.js — 4A 注入后的部署态验收标准件（config 驱动，课件无关）
//
// 用法:
//   node deploy-state-test.js <课件.html> [--config <step4.json>] [--node-id <id>]
//   config 默认取课件同目录 step4.json（schema: {quizzes:[{act,quizId,page,hasAvg}],sims:[{act,page}]}）
//
// 模式自动识别:
//   源码中 NODE_ID/PUBLISH_BASE 已回写 → 部署后模式（断 IS_DEPLOYED=true、body.deployed、四常量）
//   未回写                             → 部署前模式（跳过常量组，断 IS_DEPLOYED=false）
//
// 覆盖四组（≈105 项，随课件测验/仿真数浮动，v2026-10-02 抽屉原理课件实战提炼）:
//   A 源码级：CDN 钉版 / isSubmitMode / S14 回调传参 / 交付链接禁令 / 伪全屏 CSS / navBtns 加固 / 显式规则
//   B 结构级：PAGE_IDS↔section 一致 / 提交按钮↔quizId 一一对应 / 分数元素 / QR 徽章↔活动清单
//             / 每页徽章制（含首页加入徽章 + qrPopup_join，v2026-10-13）/ 导航层 z-index:500
//             / ⛔ 每个 QR 弹窗 innerHTML 必含 xmnClear（sim_popup 缺按钮缺陷的唯一探测器，pagesync 测不出）
//             / 测验弹窗含 openDetail / 详情面板 / mqttStatus
//   C 行为级（jsdom，答案序列运行时从课件 QUIZZES 读取，零硬编码）：
//             提交模式全流程（选完不出反馈→未答拦截→提交→得分→解析→锁定→不可改）
//             学生端导航焊死（nextPage/prevPage/方向键全拦）
//             教师链路（双轮 JSDOM：三连点→localStorage 持久化→重载→可见可翻页可广播）
//             QR 坏码检查 / CLASS_ID 一致性 / 详情面板无数据不崩
//   D 常量回写（仅部署后模式）
//
// jsdom 已知坑的正确解法（内置，勿删）:
//   - canvas stub 22 方法（缺一个仿真页就崩）
//   - 禁 window.close()：终止事件循环 → 进程 SIGTERM 零输出
//   - 三连点触发 location.reload()：jsdom 不支持 → 必须双轮 JSDOM + beforeParse 预置 localStorage
//   - ck() 用 appendFileSync 同步落日志：纯 console.log 在进程异常退出时缓冲丢失，看不到 hang 在哪步
//   - 25s 看门狗强退，exit 2=超时 / 1=有 FAIL / 0=全过

'use strict';
const fs = require('fs');
const path = require('path');

const args = process.argv.slice(2);
function opt(name) { const i = args.indexOf(name); return i >= 0 ? args[i + 1] : null; }
const HTML_PATH = args[0];
if (!HTML_PATH || !fs.existsSync(HTML_PATH)) { console.error('usage: node deploy-state-test.js <课件.html> [--config step4.json] [--node-id <id>]'); process.exit(2); }

const HTML = fs.readFileSync(HTML_PATH, 'utf8');
const CFG_PATH = opt('--config') || path.join(path.dirname(path.resolve(HTML_PATH)), 'step4.json');
const NODE_ID_ARG = opt('--node-id');
if (!fs.existsSync(CFG_PATH)) { console.error('config 不存在: ' + CFG_PATH + '（--config 指定或课件同目录放 step4.json）'); process.exit(2); }
const CFG = JSON.parse(fs.readFileSync(CFG_PATH, 'utf8'));
const QUIZZES_CFG = CFG.quizzes || [];
const SIMS_CFG = CFG.sims || [];

let pass = 0, fail = 0; const fails = [];
const LOG = path.join(path.dirname(path.resolve(HTML_PATH)), '_deploy_state_test.log');
try { fs.unlinkSync(LOG); } catch (e) {}
function ck(n, c, d) {
  const line = (c ? '[PASS] ' : '[FAIL] ') + n + (d ? '  | ' + d : '');
  if (c) pass++; else { fail++; fails.push(n); }
  fs.appendFileSync(LOG, line + '\n');
  console.log(line);
}
const WD = setTimeout(() => { fs.appendFileSync(LOG, 'WATCHDOG TIMEOUT 25s\n'); console.error('WATCHDOG TIMEOUT — 挂起在异步等待'); process.exit(2); }, 25000);

// ---------- A. 源码级断言（不依赖 jsdom） ----------
const DEPLOYED = /var\s+NODE_ID\s*=\s*'[^']+'/.test(HTML) && /var\s+PUBLISH_BASE\s*=\s*'https:\/\//.test(HTML);
console.log('== A 源码级 ==（模式: ' + (DEPLOYED ? '部署后' : '部署前') + '）');

ck('MQTT CDN 钉 4.3.7', HTML.includes('mqtt@4.3.7'));
ck('QR CDN 钉 1.4.4 且 async',
   /qrcode-generator@1\.4\.4[\s\S]{0,160}async/.test(HTML)   // 静态 <script src=...@1.4.4 async>
   || (/qrcode-generator[\/@]1\.4\.4/.test(HTML) && /\.async\s*=\s*true/.test(HTML)));   // 动态多源 loader（.async=true）
ck('isSubmitMode = true（提交模式）', /var\s+isSubmitMode\s*=\s*true/.test(HTML));
ck('S14 清空确认回调传参 onOk(true)', /onOk\s*&&\s*onOk\(true\)/.test(HTML) || /onOk\(true\)/.test(HTML));
ck('S14 无裸 onOk() 旧写法', !/onOk\(\)\s*;/.test(HTML));
ck('交付链接禁令：无 ?teacher=1 字面量', !HTML.includes('?teacher=1'));
ck('无默认班级字面量残留', !HTML.includes('DEFAULT-CLASS'));
ck('伪全屏兜底 CSS 三条保留',
   HTML.includes('body.fs-pseudo #pageContainer') && /body\.fs-pseudo\s+#topNav\s*\{[^}]*z-index:\s*10001/.test(HTML) && HTML.includes('body.fs-pseudo #navBtns'));
ck('navBtns 定位全 !important（防挤位）',
   /#navBtns\{[^}]*position:\s*fixed\s*!important/.test(HTML) && /#navBtns\{[^}]*left:\s*50%\s*!important/.test(HTML));
ck('页码导航 z-index:500 顶层（v2026-10-13：防通信状态/背景图盖住教师入口）',
   /#navBtns\{[^}]*z-index:\s*500/.test(HTML));
ck('二维码徽章 z-index:500（与导航同层的教师操作层）', /\.qr-badge\{[^}]*z-index:\s*500/.test(HTML));
ck('通信状态 z-index:250（低于导航层；移动端上移让位，见注入样式媒体查询）',
   /#mqttStatus\{[^}]*z-index:\s*250/.test(HTML));
ck('body.deployed .qr-badge.on 显式规则在位', /body\.deployed\s+\.qr-badge\.on\s*\{[^}]*display:\s*flex/.test(HTML));
ck('教学控制标准件齐备（startBroadcast/canStudentNavigate/requestCurrentPage）',
   ['function startBroadcast', 'function canStudentNavigate', 'function requestCurrentPage'].every(s => HTML.includes(s)));
ck('submitQuiz 先写本地聚合再发布（isSubmitMode 已切 true 且 submitQuiz 定义存在）', HTML.includes('function submitQuiz'));

// ---------- B/C/D 共用：jsdom 环境 ----------
// jsdom 通过 NODE_PATH 解析（与 pagesync-test-mqtt.js 同一约定）
const { JSDOM } = require('jsdom');

function stubCtx() {
  return {
    canvas: null, fillStyle: '', strokeStyle: '', lineWidth: 1, font: '', textAlign: '', textBaseline: '', globalAlpha: 1,
    setLineDash() {}, getLineDash() { return []; }, save() {}, restore() {}, beginPath() {}, closePath() {},
    moveTo() {}, lineTo() {}, arc() {}, rect() {}, fill() {}, stroke() {}, fillRect() {}, strokeRect() {},
    clearRect() {}, fillText() {}, measureText(t) { return { width: String(t).length * 8 }; },
    translate() {}, rotate() {}, scale() {}, drawImage() {}
  };
}
function mkWindow(url, beforeParse) {
  return new JSDOM(HTML, {
    runScripts: 'dangerously', pretendToBeVisual: true, url,
    beforeParse(w) {
      w.HTMLCanvasElement.prototype.getContext = function () {
        if (!this.__c) { this.__c = stubCtx(); this.__c.canvas = this; } return this.__c;
      };
      if (beforeParse) beforeParse(w);
    }
  }).window;
}
const sleep = ms => new Promise(r => setTimeout(r, ms));

function srcNode() { const m = /var\s+NODE_ID\s*=\s*'([^']*)'/.exec(HTML); return m ? m[1] : ''; }
function srcBase() { const m = /var\s+PUBLISH_BASE\s*=\s*'([^']*)'/.exec(HTML); return m ? m[1] : ''; }
const EFFECT_NODE = NODE_ID_ARG || srcNode() || '';
const PAGE_URL = EFFECT_NODE ? ('https://workbuddy.link/p/' + EFFECT_NODE) : 'https://example.org/';

(async function () {
  // ---------- B. 结构级 + C. 行为级（第一轮 JSDOM） ----------
  console.log('== B 结构级 ==');
  const w = mkWindow(PAGE_URL);
  const doc = w.document;
  const $ = s => doc.querySelector(s), $$ = s => Array.from(doc.querySelectorAll(s));
  const click = el => el && el.dispatchEvent(new w.MouseEvent('click', { bubbles: true }));
  const key = k => doc.dispatchEvent(new w.KeyboardEvent('keydown', { key: k, bubbles: true }));
  await sleep(1000);

  const pageIds = w.PAGE_IDS || [];
  ck('PAGE_IDS 与 section 一一对应',
     pageIds.length === $$('section.page').length &&
     pageIds.every(id => doc.getElementById(id) && doc.getElementById(id).classList.contains('page')),
     pageIds.length + ' 页');
  ck('QUIZZES 键 ↔ HTML 容器 id 一一对应（容器漏 id = 测验引擎静默失效）',
     QUIZZES_CFG.length > 0 && QUIZZES_CFG.every(q => doc.getElementById(q.quizId) && doc.getElementById(q.quizId)._initialized === true),
     QUIZZES_CFG.map(q => q.quizId).join(','));

  const sbBtns = $$('button[id$="_submitBtn"]');
  ck('提交按钮数 = 测验页数', sbBtns.length === QUIZZES_CFG.length, sbBtns.length + '/' + QUIZZES_CFG.length);
  ck('提交按钮 quizId 全部对上 config',
     QUIZZES_CFG.every(q => doc.getElementById(q.quizId + '_submitBtn')));
  ck('分数元素 = quizScoreId 规则（act+Score）',
     QUIZZES_CFG.every(q => doc.getElementById(q.act + 'Score')));
  ck('无「重做」按钮残留（提交模式）', $$('button[onclick*="retryQuiz"]').length === 0);

  const badges = $$('.qr-badge');
  const actBadges = badges.filter(b => b.getAttribute('data-activity'));
  const wantActs = QUIZZES_CFG.map(q => q.act).concat(SIMS_CFG.map(s => s.act));
  ck('QR 活动徽章数 = 测验+仿真活动数', actBadges.length === wantActs.length, actBadges.length + '/' + wantActs.length);
  ck('徽章活动名与 config 一致',
     JSON.stringify(actBadges.map(b => b.getAttribute('data-activity')).sort()) === JSON.stringify(wantActs.slice().sort()));
  ck('每个页面均有 QR 徽章（含首页加入徽章，v2026-10-13 每页徽章制）',
     badges.length === pageIds.length, badges.length + '/' + pageIds.length);
  // v2026-10-13 徽章显示：DOM 就绪后仅「当前页」徽章 ON（防「首屏无徽章」回归）
  const onPages = () => $$('.qr-badge.on').map(b => b.getAttribute('data-page'));
  if (DEPLOYED) {
    ck('徽章：加载后仅首页徽章 ON，其余全部下架',
       onPages().length === 1 && onPages()[0] === pageIds[0],
       onPages().join(',') || '(none)');
  } else {
    ck('徽章：未部署（静态文件）时无徽章 ON（不误导扫码）',
       onPages().length === 0, onPages().join(',') || '(none)');
  }
  ck('加入弹窗存在（qrPopup_join + qrImg_join）',
     !!doc.getElementById('qrPopup_join') && !!doc.getElementById('qrImg_join'));
  const popupsOk = wantActs.every(a => doc.getElementById('qrPopup_' + a) && doc.getElementById('qrImg_' + a));
  ck('每个活动有 qrPopup + qrImg', popupsOk);
  ck('⛔ 含统计的 QR 弹窗 innerHTML 必含 xmnClear（缺清空按钮 = 数据无法清除，pagesync 测不出）',
     wantActs.every(a => {
       const p = doc.getElementById('qrPopup_' + a);
       if (!p) return false;
       const hasStats = /qrPart_|qrAvg_/.test(p.innerHTML);   // 无统计的仿真弹窗无需清空按钮
       return !hasStats || /xmnClear\(\s*['"]/.test(p.innerHTML);
     }));
  ck('测验活动弹窗含每题详情入口（openDetail）',
     QUIZZES_CFG.every(q => {
       const p = doc.getElementById('qrPopup_' + q.act);
       return p && p.innerHTML.includes('openDetail');
     }));
  ck('详情面板与数据状态条存在', !!doc.getElementById('detailPanel') && !!doc.getElementById('mqttStatus'));
  ck('学生端初始视角：导航隐藏、页码指示器保留（教师唯一入口）',
     (() => {
       const g = s => { const e = $(s); return e ? w.getComputedStyle(e).display : '(no el)'; };
       return g('#topNav') === 'none' && g('#btnPrev') === 'none' && g('#btnNext') === 'none' && g('#pageIndicator') !== 'none';
     })());

  console.log('== C 行为级 ==');
  // 提交模式全流程（教师身份才可导航，切教师）
  w.IS_TEACHER = true;
  for (const q of QUIZZES_CFG) {
    const qid = q.quizId, act = q.act;
    const pageIdx = pageIds.indexOf(q.page);
    if (pageIdx < 0) { ck(q.page + ' 在 PAGE_IDS 中', false); continue; }
    w.showPage(pageIdx); await sleep(120);
    const container = doc.getElementById(qid);
    const qs = container._questions;
    for (let i = 0; i < qs.length; i++) {
      const ans = qs[i].answer;                       // 运行时读课件自身答案，零硬编码
      if (Array.isArray(ans)) {
        for (const idx of ans) click($(`#qq_${qid}_${i} .opt[data-idx="${idx}"]`));
        click($(`#qq_${qid}_${i} .opt-confirm`));
      } else {
        click($(`#qq_${qid}_${i} .opt[data-idx="${ans}"]`));
      }
      await sleep(25);
    }
    await sleep(80);
    ck(qid + ' 提交模式：选完不出即时反馈', $$('#' + q.page + ' .feedback.show').length === 0);
    container._chosen = container._chosen.map((c, i) => Array.isArray(qs[i].answer) ? c : c);
    // 未答拦截：把最后一题单选清为未答再试提交（多选跳过此检查）
    const lastSingle = (() => { for (let i = qs.length - 1; i >= 0; i--) if (!Array.isArray(qs[i].answer)) return i; return -1; })();
    if (lastSingle >= 0) {
      const keep = container._chosen[lastSingle];
      container._chosen[lastSingle] = -1;
      click(doc.getElementById(qid + '_submitBtn'));
      await sleep(60);
      ck(qid + ' 未答完提交被拦截', container._submitted !== true);
      container._chosen[lastSingle] = keep;
    }
    click(doc.getElementById(qid + '_submitBtn'));
    await sleep(200);
    ck(qid + ' 提交后全对 ' + qs.length + '/' + qs.length,
       new RegExp(qs.length + '/' + qs.length).test(doc.getElementById(act + 'Score').textContent),
       doc.getElementById(act + 'Score').textContent);
    ck(qid + ' 提交后解析全显示', $$('#' + q.page + ' .feedback.show').length === qs.length);
    ck(qid + ' 提交后选项锁定（.submitted）', $$('#' + q.page + ' .quiz-q.submitted').length === qs.length);
    ck(qid + ' 提交后按钮禁用', doc.getElementById(qid + '_submitBtn').disabled === true);
    const firstOpt = $(`#qq_${qid}_0 .opt[data-idx="0"]`);
    const before = container._chosen[0];
    click(firstOpt); await sleep(40);
    ck(qid + ' 提交后改选无效', JSON.stringify(container._chosen[0]) === JSON.stringify(before));
  }

  // 学生端导航焊死
  w.IS_TEACHER = false;
  w.showPage(Math.min(2, pageIds.length - 1)); await sleep(100);
  const bNav = w.curPage;
  w.nextPage(); await sleep(50);
  ck('学生端 nextPage 被拦', w.curPage === bNav);
  w.prevPage(); await sleep(50);
  ck('学生端 prevPage 被拦', w.curPage === bNav);
  key('ArrowRight'); await sleep(60);
  ck('学生端方向键被拦（页码不变）', w.curPage === bNav);
  w.IS_TEACHER = true;

  // 广播权生命周期
  w.startBroadcast(); await sleep(80);
  ck('startBroadcast 置 isBroadcaster', w.isBroadcaster === true);
  w.stopBroadcast(); await sleep(80);
  ck('stopBroadcast 清 isBroadcaster', w.isBroadcaster === false);

  // 教学控制函数清单
  for (const fn of ['xmnBroadcastPage', 'publishClaim', 'startBroadcast', 'stopBroadcast', 'canStudentNavigate',
                    'closeQRPopup', 'submitQuiz', 'openDetail', 'updateBadgeStats', 'xmnClear', 'xmnClearDo',
                    'requestCurrentPage', 'toggleQRPopup']) {
    ck('函数存在: ' + fn, typeof w[fn] === 'function');
  }

  // 详情面板无数据不崩
  w.showPage(pageIds.length - 1); await sleep(100);
  let detailOk = true;
  try { w.openDetail(QUIZZES_CFG[0].act); await sleep(100); } catch (e) { detailOk = false; }
  ck('openDetail 无数据不抛错', detailOk);

  // QR 坏码 + class 一致性
  w.showPage(pageIds.indexOf(QUIZZES_CFG[0].page) >= 0 ? pageIds.indexOf(QUIZZES_CFG[0].page) : 1); await sleep(100);
  const badge0 = $('.qr-badge[data-activity="' + QUIZZES_CFG[0].act + '"]');
  click(badge0); await sleep(200);
  const qrSrc = (doc.getElementById('qrImg_' + QUIZZES_CFG[0].act).getAttribute('src') || '');
  ck('QR 无 nullsrcdoc 坏码', qrSrc.indexOf('nullsrcdoc') < 0, qrSrc.slice(0, 70));
  ck('QR 含 hash page 与 class 参数', qrSrc.indexOf('%23page%3D') >= 0 && qrSrc.indexOf('class%3D') >= 0, qrSrc.slice(0, 70));
  ck('QR class 参数与 CLASS_ID 一致（不串台）', qrSrc.indexOf(encodeURIComponent(w.CLASS_ID)) >= 0, 'CLASS_ID=' + w.CLASS_ID);
  w.closeQRPopup(QUIZZES_CFG[0].act); await sleep(40);

  // 加入徽章（非活动页，v2026-10-13）：首页可扫码，二维码按页动态生成
  w.showPage(0); await sleep(100);
  const joinBadge = $('.qr-badge:not([data-activity])');
  ck('存在非活动页加入徽章', !!joinBadge);
  // v2026-10-13 回访：切页后再回访，徽章须切回当前页（防「残留在上一页」回归）
  if (DEPLOYED) {
    const _qPage = pageIds.indexOf(QUIZZES_CFG[0].page);
    w.showPage(_qPage >= 0 ? _qPage : Math.min(1, pageIds.length - 1)); await sleep(120);
    const _away = onPages().join(',');
    w.showPage(0); await sleep(120);
    const _back = onPages().join(',');
    ck('徽章：回访首页 → 切回首页徽章（不残留上一页）',
       _back === pageIds[0] && _away !== _back, _away + ' → ' + _back);
  }
  if (joinBadge) {
    click(joinBadge); await sleep(250);
    const jp = doc.getElementById('qrPopup_join');
    const jSrc = (doc.getElementById('qrImg_join').getAttribute('src') || '');
    ck('加入徽章弹出加入弹窗', !!jp && jp.classList.contains('show'));
    ck('加入二维码无 nullsrcdoc 坏码且含 page 参数',
       jSrc.indexOf('nullsrcdoc') < 0 && jSrc.indexOf('%23page%3D') >= 0, jSrc.slice(0, 70));
    w.closeQRPopup('join'); await sleep(40);
  }

  // ---------- D. 常量回写（仅部署后模式） ----------
  console.log('== D 常量回写 ==（' + (DEPLOYED ? '部署后' : '部署前，跳过') + '）');
  if (DEPLOYED) {
    ck('IS_DEPLOYED = true', w.IS_DEPLOYED === true, String(w.IS_DEPLOYED));
    ck('body 带 deployed 类', doc.body.classList.contains('deployed'), doc.body.className);
    ck('NODE_ID 已回写非空', !!w.NODE_ID && w.NODE_ID !== '', w.NODE_ID);
    ck('PUBLISH_BASE 已回写为 workbuddy.link 裸链', /^https:\/\/workbuddy\.link\/p\//.test(w.PUBLISH_BASE || ''), w.PUBLISH_BASE);
    ck('CLASS_ID 派生为 wb-节点（非默认值）', w.CLASS_ID === 'wb-' + w.NODE_ID, w.CLASS_ID);
    if (EFFECT_NODE) {
      ck('NODE_ID 与 --node-id 一致', w.NODE_ID === EFFECT_NODE, w.NODE_ID + ' vs ' + EFFECT_NODE);
    }
    ck('SYNC_TOPIC 含节点 id（按节点隔离）', String(w.SYNC_TOPIC || '').indexOf(w.NODE_ID) >= 0, String(w.SYNC_TOPIC));
  } else {
    ck('部署前 IS_DEPLOYED = false', w.IS_DEPLOYED === false, String(w.IS_DEPLOYED));
    ck('部署前 body 无 deployed 类', !doc.body.classList.contains('deployed'), doc.body.className);
  }

  // ---------- 教师链路：双轮 JSDOM（三连点 → 持久化 → 重载） ----------
  console.log('== C2 教师链路（双轮 JSDOM）==');
  // 三连点 handler 仅在学生模式生效（教师已是控制端无需再切换），故先恢复学生视角再模拟
  w.IS_TEACHER = false;
  const tkey = w.TEACHER_KEY || ('xmn_teacher_' + (EFFECT_NODE || ''));
  // 轮 1：三连点写 localStorage
  const pi = doc.getElementById('pageIndicator');
  for (let i = 0; i < 3; i++) click(pi);
  await sleep(250);
  ck('三连点后教师身份已写入 localStorage', (() => { try { return w.localStorage.getItem(tkey) === '1'; } catch (e) { return false; } })(), 'key=' + tkey);
  // 轮 2：预置身份重载
  const w2 = mkWindow(PAGE_URL, lw => { try { lw.localStorage.setItem(tkey, '1'); } catch (e) {} });
  await sleep(1100);
  const doc2 = w2.document;
  const g2 = s => { const e = doc2.querySelector(s); return e ? w2.getComputedStyle(e).display : '(no el)'; };
  ck('重载后 IS_TEACHER = true', w2.IS_TEACHER === true, String(w2.IS_TEACHER));
  ck('教师端顶部导航可见', g2('#topNav') !== 'none', g2('#topNav'));
  ck('教师端翻页键可见', g2('#btnNext') !== 'none');
  const b2 = w2.curPage; w2.nextPage(); await sleep(80);
  ck('教师端可翻页', w2.curPage === b2 + 1, b2 + '→' + w2.curPage);
  ck('教师端具备广播函数', typeof w2.startBroadcast === 'function' && typeof w2.publishClaim === 'function');

  clearTimeout(WD);
  console.log('\n' + '='.repeat(60));
  fs.appendFileSync(LOG, 'RESULT: ' + (fail ? 'FAILED ' + fail : 'ALL PASS (' + pass + ')') + '\n');
  if (fails.length) { console.log('FAILED ' + fails.length + ' 项：'); fails.forEach(f => console.log('  - ' + f)); process.exit(1); }
  console.log('ALL PASS  (' + pass + ' 项)');
  process.exit(0);
})().catch(e => { fs.appendFileSync(LOG, 'FATAL ' + (e && e.stack || e) + '\n'); console.error('FATAL', e); process.exit(1); });
