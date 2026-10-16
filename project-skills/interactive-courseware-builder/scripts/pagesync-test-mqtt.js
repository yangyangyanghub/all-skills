// pagesync-test-mqtt.js — 教学控制标准件（ABCD+F+G · MQTT 广播版）逻辑回归
// =====================================================================
// 目的：不依赖浏览器与网络，从课件 HTML 里抽取【真实函数代码】在 vm 沙箱驱动，
//       验证 广播/claim/停播/关弹窗/导航闸门 等行为，另用「剥注释后的静态标记」
//       核对 7 个集成点是否落位（半集成 = 静默失效，此处必须拦住）。
// 用法：node pagesync-test-mqtt.js <课件 index.html>
//       ⚠ 必须用 node 跑（.js 喂给 Python 会报 invalid character U+2014）
// 退出码：0=全过  1=有 FAIL
// 适用：接入了 teaching-control.js 标准件的第四代课件（MQTT 页码同步版）。
//       云数据库轮询版课件请用云变体技能的 pagesync-test.js。
// =====================================================================
const fs = require('fs');
const vm = require('vm');

const file = process.argv[2];
if (!file) { console.error('用法: node pagesync-test-mqtt.js <课件 index.html>'); process.exit(1); }
let html = fs.readFileSync(file, 'utf8').replace(/\r\n/g, '\n');

// ---------- 工具 ----------
// 剥【整行】注释（警示性注释会造成假 PASS/假 FAIL，本脚本反复踩过这个坑）
function stripLineComments(code) {
  return code.split('\n').filter(l => {
    const t = l.trim();
    return !(t.startsWith('//') || t.startsWith('/*') || t.startsWith('*'));
  }).join('\n');
}
const codeNoComment = stripLineComments(html);

function extractFn(name) {
  const re = new RegExp('function ' + name + '\\s*\\([^)]*\\)\\s*\\{');
  const m = re.exec(html);
  if (!m) return null;
  let i = m.index + m[0].length, depth = 1;
  while (i < html.length && depth > 0) {
    const c = html[i];
    if (c === '{') depth++;
    else if (c === '}') depth--;
    i++;
  }
  return html.slice(m.index, i);
}

// ---------- 从课件抽常量 ----------
// 抽取顺序：① 发布后/旧写法 `... || 'xxx'`；② 新模板派生式 `... || ('wb-' + ...)`；③ 字面量
const _cm = /var CLASS_ID[^;\n]*\|\|\s*'([^']+)'/.exec(html)
          || /var CLASS_ID[^;\n]*?'(wb-[^']+)'/.exec(html)
          || /var CLASS_ID\s*=\s*'([^']+)'/;
const CLASS_ID = _cm ? _cm[1] : 'TEST-CLASS';   // 抽不到时的测试兜底名（勿与课件产物混淆）
const _nm = /var NODE_ID\s*=\s*'([^']*)'/.exec(html);
const NODE_ID = _nm ? _nm[1] : '';
const _sm = /var SYNC_TOPIC\s*=\s*([^;\n]+)/.exec(html);
const SYNC_TOPIC_EXPR = _sm ? _sm[1].trim() : "'xmn-sync/unknown'";

const PAGES = html.match(/var PAGE_IDS = \[[^\]]*\]/);
if (!PAGES) { console.error('未找到 var PAGE_IDS = [...]'); process.exit(1); }

// ---------- 沙箱环境 ----------
const publishes = [];              // 记录所有 publish(topic, payload, opts)
const heartbeats = [];             // setInterval 登记表
let hbSeq = 0;
const fakeClient = {
  options: { clientId: 'test_client_1' },
  publish(topic, payload, opts) { publishes.push({ topic, payload, opts }); },
};
const sandbox = {
  JSON, Date, console,
  setTimeout: function () { return 0; }, clearTimeout: function () {},
  setInterval: function (fn, ms) { heartbeats.push(fn); return ++hbSeq; },
  clearInterval: function (id) { /* 标记清除 */ heartbeats[id - 1] = null; },
  PAGE_IDS: eval(PAGES[0].replace('var PAGE_IDS =', '')),
  curPage: 2,
  CLASS_ID, NODE_ID,
  SYNC_TOPIC: eval(SYNC_TOPIC_EXPR),
  SYNC_CTL_TOPIC: eval(SYNC_TOPIC_EXPR) + '/ctl',
  mqttConnected: true,
  mqttClient: fakeClient,
  myClientId: 'test_client_1',
  isBroadcaster: false,
  syncHeartbeat: null,
  activeClaimId: '', activeClaimTs: 0,
  CLAIM_TTL: 6000,
  observedTeacher: false,
  broadcastSinceTs: 0,
  followTeacher: true,
  lastManualNav: 0,
  IS_TEACHER: false,
  showToast: function () {},
  document: { getElementById: function () { return null; } },
};
vm.createContext(sandbox);

function runInSandbox(code) { vm.runInContext(code, sandbox); }

const results = [];
function ck(name, ok, detail) { results.push({ name, ok: !!ok, detail: detail || '' }); }

// ---------- 行为级测试（抽真实函数驱动） ----------
const fns = ['xmnBroadcastPage', 'publishClaim', 'startBroadcast', 'stopBroadcast', 'canStudentNavigate', 'closeQRPopup'];
const extracted = {};
for (const f of fns) {
  const src = extractFn(f);
  ck('函数存在: ' + f, src, src ? '' : '未找到 function ' + f + '（是否接入 teaching-control.js 标准件？）');
  if (src) { extracted[f] = src; try { runInSandbox(src); } catch (e) { ck('函数可编译: ' + f, false, e.message); } }
}

try {
  // T1 startBroadcast：置位 + claim + 立即广播 + 心跳登记
  runInSandbox('startBroadcast();');
  const claim = publishes.find(p => p.topic === sandbox.SYNC_CTL_TOPIC && p.payload.indexOf('"id":"test_client_1"') >= 0);
  const pagePub = publishes.find(p => p.topic === sandbox.SYNC_TOPIC && p.payload.indexOf('"page":"') >= 0);
  ck('T1 startBroadcast 置 isBroadcaster', sandbox.isBroadcaster === true);
  ck('T1 发布 claim 到 SYNC_CTL_TOPIC', !!claim);
  ck('T1 立即广播当前页到 SYNC_TOPIC', !!pagePub && pagePub.payload.indexOf('"page":"' + sandbox.PAGE_IDS[sandbox.curPage] + '"') >= 0);
  ck('T1 心跳定时器已登记', heartbeats.length >= 1 && heartbeats[0]);

  // T2 心跳：本端持权 → 继续广播
  const before = publishes.filter(p => p.topic === sandbox.SYNC_TOPIC).length;
  if (heartbeats[0]) heartbeats[0]();
  const after = publishes.filter(p => p.topic === sandbox.SYNC_TOPIC).length;
  ck('T2 心跳续期 claim 并广播（持权者）', after > before);

  // T3 stopBroadcast：停播 + 双清 retain
  const emptiesBefore = publishes.filter(p => p.payload === '').length;
  runInSandbox('stopBroadcast();');
  const emptiesAfter = publishes.filter(p => p.payload === '').length;
  ck('T3 stopBroadcast 置 isBroadcaster=false', sandbox.isBroadcaster === false);
  ck('T3 清空 SYNC_TOPIC+SYNC_CTL_TOPIC retain', emptiesAfter - emptiesBefore >= 2);
  ck('T3 心跳已清除', heartbeats.every(h => h === null));

  // T4 closeQRPopup：【A修订】教师端不清广播，学生端防御性清除（效果断言：看 isBroadcaster 与空 retain）
  runInSandbox('startBroadcast();');                       // 先恢复广播态
  const emptyBase = publishes.filter(p => p.payload === '').length;
  runInSandbox('IS_TEACHER = true; closeQRPopup("pre");');
  const teacherKept = sandbox.isBroadcaster === true && publishes.filter(p => p.payload === '').length === emptyBase;
  runInSandbox('IS_TEACHER = false; closeQRPopup("pre");');
  const studentStopped = sandbox.isBroadcaster === false
        && publishes.filter(p => p.payload === '').length >= emptyBase + 2;
  ck('T4 教师端关二维码弹窗【不】停广播', teacherKept, teacherKept ? '' : '关弹窗触发了 stopBroadcast —— 同步会静默断掉');
  ck('T4 学生端关弹窗防御性停广播', studentStopped);

  // T5 canStudentNavigate 闸门（焊死纯跟随：学生恒禁导航，无自由浏览开关）
  runInSandbox('IS_TEACHER = false; followTeacher = true;');
  let gate = vm.runInContext('canStudentNavigate()', sandbox);
  ck('T5 学生端恒禁导航（纯跟随）', gate === false);
  runInSandbox('followTeacher = false;');
  gate = vm.runInContext('canStudentNavigate()', sandbox);
  ck('T5 即使翻转 followTeacher 学生仍禁导航（无自由浏览开关）', gate === false);
  ck('T5 不存在 createFollowToggle（学生无跟随/自由开关）', !/function\s+createFollowToggle\s*\(/.test(html));
  runInSandbox('IS_TEACHER = true; followTeacher = true;');
  gate = vm.runInContext('canStudentNavigate()', sandbox);
  ck('T5 教师始终可导航', gate === true);
} catch (e) {
  ck('行为级测试执行', false, e.message);
}

// ---------- 静态集成点核对（剥注释后；6 处集成缺一不可） ----------
const has = (...pats) => pats.every(p => new RegExp(p).test(codeNoComment));
// S1 说明（2026-10-13）：mqtt-framework.js 模板演进后，教师端 connect 后的广播入口有两种合法形态——
//   旧：if (IS_TEACHER) startBroadcast();            （直连广播）
//   新：if(IS_TEACHER){ setTimeout(function(){ xmnEnterTeacherRole(); }, 600); }
//        （先收 retain 租约再持权广播，配合 S2/S17/S18 租约仲裁，防双广播）
// 两种都满足「教师连上即进入广播态」的测试意图，故均可通过。
ck('S1 【G】connect 回调自动广播（startBroadcast 直连 或 xmnEnterTeacherRole 租约入口）',
   has("if\\s*\\(\\s*IS_TEACHER\\s*\\)\\s*startBroadcast\\(\\s*\\)\\s*;") ||
   has("if\\s*\\(\\s*IS_TEACHER\\s*\\)\\s*\\{\\s*setTimeout\\(\\s*function\\s*\\(\\s*\\)\\s*\\{\\s*xmnEnterTeacherRole\\(\\s*\\)"));
ck('S2 【C】控制端唯一：租约仲裁（SYNC_TOPIC/SYNC_CTL_TOPIC 真实订阅 + 持有期 CLAIM_TTL + onClaim）',
   has('SYNC_CTL_TOPIC', 'subscribe\\(\\s*SYNC_TOPIC\\b', 'subscribe\\(\\s*SYNC_CTL_TOPIC\\b',
       'Date\\.now\\(\\)\\s*-\\s*activeClaimTs\\s*<=\\s*CLAIM_TTL',
       'function\\s+onClaim\\s*\\('));
ck('S3 showPage 末尾广播（带 syncing 守卫）+ 手动翻页时间戳',
   has('if\\s*\\(\\s*isBroadcaster\\s*&&\\s*!syncing\\s*\\)\\s*xmnBroadcastPage\\(\\s*\\)\\s*;',
       'lastManualNav\\s*=\\s*Date\\.now\\(\\)'));
ck('S4 nextPage/prevPage 导航闸门',
   has('function\\s+nextPage\\s*\\(\\s*\\)\\s*\\{\\s*if\\s*\\(\\s*!canStudentNavigate\\(\\)\\s*\\)\\s*return\\s*;',
       'function\\s+prevPage\\s*\\(\\s*\\)\\s*\\{\\s*if\\s*\\(\\s*!canStudentNavigate\\(\\)\\s*\\)\\s*return\\s*;'));
ck('S5 【F】三连点教师模式（_piTaps + TEACHER_KEY 持久化）',
   has('_piTaps', 'localStorage\\.setItem\\(\\s*TEACHER_KEY'));
ck('S6 【B】学生端隐藏徽章（.qr-badge 置 display none）',
   has("querySelectorAll\\(\\s*['\\\"]\\.qr-badge['\\\"]\\s*\\)", "display\\s*=\\s*'none'"));
ck('S7 伪全屏 CSS：topNav 必须在课件层之上（z-index:10001）',
   codeNoComment.indexOf('body.fs-pseudo #topNav{z-index:10001') >= 0,
   '缺少 body.fs-pseudo #topNav{z-index:10001} —— 伪全屏会盖死菜单');
ck('S8 教师身份按设备记忆（TEACHER_KEY 绑 NODE_ID）',
   has("TEACHER_KEY\\s*=\\s*'xmn_teacher_'\\s*\\+\\s*NODE_ID"));
ck('S9 CLASS_ID 无 DEFAULT-CLASS 字面量残留',
   !/var CLASS_ID[^;\n]*'DEFAULT-CLASS'/.test(codeNoComment) && CLASS_ID !== 'DEFAULT-CLASS',
   'CLASS_ID=' + CLASS_ID + ' —— 跨课件答题数据会串台');
ck('S10 诊断日志（console [XMN] + IS_TEACHER）',
   has("\\[XMN\\]", 'IS_TEACHER\\s*='));
ck('S11 【H】学生进入主动请求当前页（requestCurrentPage）+ 仅持权者回播 + 2s 心跳',
   has('function\\s+requestCurrentPage\\s*\\(\\s*\\)',
       'requestCurrentPage\\s*\\(\\s*\\)\\s*;',
       "req\\s*:\\s*'page'",
       'isBroadcaster\\s*&&\\s*activeClaimId\\s*===\\s*myClientId',
       '\\},\\s*2000\\s*\\);'),
   '缺少【H】：学生主动请求当前页 / 仅持权者回播(M 广播源不回播风暴) / 2s 心跳，三者缺一');

ck('S12 交付链接禁令：课件内不得出现 ?teacher=1 字面量（壳内必失效，会误导教师）',
   !/\?teacher\s*=\s*1/.test(html),
   '发现 ?teacher=1 —— 资料库外壳 iframe 会剥掉 query，教师点开仍是学生视角。'
   + '交付链接必须用裸链，教师入口只能是三连点页码指示器');

// S13 页面零「连点进教师模式」提示（2026-10-14 定案）：学生会照做夺取控制端权限 → 必须无任何页面提示
ck('S13 零页面「连点进教师模式」提示（不得含 xmnTeacherHint / ‘连点 3 次’文案）',
   !(/xmnTeacherHint/.test(codeNoComment)
     || /快速连点|连点\s*3\s*次|点击\s*3\s*次|点击三次/.test(codeNoComment)),
   '检测到页面内连点提示 —— 学生看到会自行连点夺取控制权，必须删除（教师入口只靠线下交付话术）');

// S19 【C】观察态提示窗 3 秒倒计时：多端抢控制权弹窗须含倒计时 + 超时自动收起
ck('S19 【C】观察态提示窗 3 秒倒计时（TAKEOVER_CD_SEC + _cdTimer + 超时隐藏）',
   has('TAKEOVER_CD_SEC\\s*=\\s*3',
       '_cdTimer',
       '若不接管',
       'clearTakeoverCountdown'));

// S14 清空确认回调必须传 true（2026-09-30 诺尔斯实机踩坑：onOk() 不传参 → ok 恒 undefined → 点确定清空静默失效）
ck('S14 清空确认回调传参：必须 onOk(true)/onConfirm(true)，且不得残留 onOk()/onConfirm() 旧写法',
   (/(onOk\s*&&\s*onOk\(\s*true\s*\)|if\s*\(\s*onOk\s*\)\s*onOk\(\s*true\s*\)|if\s*\(\s*onConfirm\s*\)\s*onConfirm\(\s*true\s*\))/.test(codeNoComment))
   && !(/(onOk\s*&&\s*onOk\(\s*\)|if\s*\(\s*onOk\s*\)\s*onOk\(\s*\)|if\s*\(\s*onConfirm\s*\)\s*onConfirm\(\s*\))/.test(codeNoComment)),
   '确认回调未传 true 或残留旧写法 —— 点「确定」后清空静默不执行，见坑表「清空数据静默失效」');

// S15 静态：connect 回填 myClientId（治沙箱夹具盲区）+ will 遗嘱释放租约（【C/⑦】）
ck('S15 【C/⑦】connect 回填 myClientId（=clientId）+ will 遗嘱（bye 释放租约）',
   has('myClientId\\s*=\\s*_cid',
       'will\\s*:\\s*\\{\\s*topic\\s*:\\s*SYNC_CTL_TOPIC',
       'bye\\s*:\\s*true',
       'clientId\\s*:\\s*_cid'),
   '缺少 myClientId 回填 或 MQTT will 遗嘱 —— 仲裁失效 / 崩溃不释放租约');

// ---------- S16~S18：控制端唯一（租约）行为级仿真（两端共享总线，双 vm 上下文） ----------
(function(){
  const ctrlFns = ['xmnBroadcastPage','publishClaim','onClaim','xmnDowngradeToObserver',
                   'startBroadcast','stopBroadcast','yieldBroadcast','requestCurrentPage',
                   'handleControlMessage','handleSyncMessage','xmnEnterTeacherRole','xmnTakeover'];
  const src = {}; const missing = [];
  for (const f of ctrlFns){ const s = extractFn(f); if (!s) missing.push(f); src[f] = s || ''; }
  if (missing.length){ ck('S16~S18 控制层函数齐备', false, '缺: ' + missing.join(',')); return; }
  const srcAll = ctrlFns.map(f => src[f]).join('\n');

  function makeEp(id, bus){
    const intervals = [];
    const st = {
      JSON, Date, console,
      setTimeout: function(){ return 0; }, clearTimeout: function(){},
      setInterval: function(fn, ms){ intervals.push(fn); return intervals.length; },
      clearInterval: function(i){ if (i) intervals[i-1] = null; },
      PAGE_IDS: ['p1','p2','p3'], curPage: 1, CLASS_ID: 'C',
      SYNC_TOPIC: 'sync', SYNC_CTL_TOPIC: 'sync/ctl',
      mqttConnected: true,
      mqttClient: { options:{ clientId:id }, publish: function(t, p, o){ bus.push({ from:id, topic:t, payload:p }); } },
      myClientId: id, isBroadcaster: false, syncHeartbeat: null,
      activeClaimId: '', activeClaimTs: 0, CLAIM_TTL: 6000,
      observedTeacher: false, broadcastSinceTs: 0,
      followTeacher: true, lastManualNav: 0, syncing: false, IS_TEACHER: true, syncReceived: false,
      showToast: function(){}, showPage: function(){},
      xmnCurIndex: function(){ return st.curPage; },
      document: { getElementById: function(){ return null; },
                  createElement: function(){ return { style:{}, appendChild:function(){}, setAttribute:function(){}, onclick:null }; },
                  querySelectorAll: function(){ return []; } },
      showTeacherObserveBanner: function(){ st._banner = true; },
      hideTeacherObserveBanner: function(){ st._banner = false; }
    };
    const ctx = vm.createContext(st);
    vm.runInContext(srcAll, ctx);
    return { st: st, intervals: intervals, seen: 0, run: function(code){ return vm.runInContext(code, ctx); } };
  }
  // 投递总线新消息给某端（跳过自己发出的）
  function pump(ep, bus){
    for (; ep.seen < bus.length; ep.seen++){
      const m = bus[ep.seen];
      if (m.from === ep.st.myClientId) continue;
      try { ep.run('handleControlMessage(' + JSON.stringify(m.payload) + ');'); } catch(e){}
    }
  }

  const bus = [];
  const A = makeEp('client_A', bus);
  const B = makeEp('client_B', bus);

  // S17 观察态：A 持权广播 → B（第二教师）探活 → 进入观察态，不广播
  A.run('startBroadcast();');
  pump(B, bus);                       // B 收到 A 的 claim/页码
  const bSawA = (B.st.activeClaimId === 'client_A');
  B.run('xmnEnterTeacherRole();');
  ck('S17 第二教师探到活跃租约 → 进入观察态（不广播）',
     bSawA && B.st.isBroadcaster === false && B.st.observedTeacher === true,
     'B.activeClaimId=' + B.st.activeClaimId + ' B.isBroadcaster=' + B.st.isBroadcaster + ' B.observed=' + B.st.observedTeacher);

  // S16 冷启动双认领：两端各自 startBroadcast → 互相收到对方 claim → 字典序确定性裁决，仅一方胜出
  bus.length = 0; A.seen = 0; B.seen = 0;
  [A, B].forEach(function(ep){ ep.st.activeClaimId=''; ep.st.activeClaimTs=0; ep.st.isBroadcaster=false; ep.st.observedTeacher=false; ep.st.broadcastSinceTs=Date.now(); });
  A.run('startBroadcast();'); B.run('startBroadcast();');
  pump(A, bus); pump(B, bus);
  const nBcast = (A.st.isBroadcaster ? 1 : 0) + (B.st.isBroadcaster ? 1 : 0);
  ck('S16 冷启动双认领 → clientId 字典序确定性裁决，仅一方胜出（不双广播）',
     nBcast === 1, '剩余广播源=' + nBcast);

  // S18a 遗嘱/主动退出 → 其他端立即释约
  const winner = A.st.isBroadcaster ? A : B;
  const loser  = winner === A ? B : A;
  bus.length = 0; A.seen = 0; B.seen = 0;
  winner.run('yieldBroadcast();');           // 持权者退出：发 bye + 清 retain
  pump(loser, bus);
  ck('S18a 遗嘱/主动退出 → 其他端立即释约（activeClaimId 清空）',
     loser.st.activeClaimId === '',
     'loser.activeClaimId=' + loser.st.activeClaimId);

  // S18b 强制接管 → 旧控制端立即降级为观察态
  bus.length = 0; A.seen = 0; B.seen = 0;
  A.st.activeClaimId = 'client_A'; A.st.activeClaimTs = Date.now(); A.st.isBroadcaster = true; A.st.observedTeacher = false;
  B.st.activeClaimId = 'client_A'; B.st.activeClaimTs = Date.now(); B.st.isBroadcaster = false;
  B.run('xmnTakeover();');                    // B 强制认领
  pump(A, bus);                               // A 收到 B 的 force claim
  ck('S18b 强制接管 → 旧控制端立即降级为观察态',
     B.st.isBroadcaster === true && A.st.isBroadcaster === false && A.st.observedTeacher === true,
     'B.bcast=' + B.st.isBroadcaster + ' A.bcast=' + A.st.isBroadcaster + ' A.obs=' + A.st.observedTeacher);
})();

// ---------- 汇总 ----------
console.log('=== pagesync-test-mqtt: ' + file);
let bad = 0;
for (const r of results) {
  console.log('  ' + (r.ok ? 'PASS' : 'FAIL') + '  ' + r.name + (r.ok ? '' : '   ← ' + r.detail));
  if (!r.ok) bad++;
}
console.log(bad ? 'RESULT: FAIL=' + bad : 'RESULT: ALL PASS (' + results.length + ' 项)');
process.exit(bad ? 1 : 0);
