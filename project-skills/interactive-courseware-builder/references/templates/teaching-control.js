/**
 * teaching-control.js — 教学控制标准件（第四代 · 资料库路线 · 控制端唯一版）
 * =====================================================================
 * 覆盖 SKILL.md「资料库发布 & 教学控制标准件（第四代硬规则）」整章：
 *   A 关弹窗不清广播(教师端) · B 学生端隐藏徽章
 *   C 控制端唯一：全网唯一广播者 —— 租约制（在位者优先）+ MQTT 遗嘱 + 观察态 + 一键接管
 *     ⛔ 页面内**零**「连点页码进教师模式」提示（2026-10-14 定案：学生看到会自行连点夺取控制权）；
 *        观察态提示窗（多端抢控制权时）带 **3 秒倒计时**，不接管则自动收起。
 *   D 学生焊死纯跟随(+8s宽限) · E 跟随时隐藏导航 · F 三连点教师模式
 *   G 广播权随教师模式常驻 · H 学生进入主动请求当前页（仅持权者回播）
 *   + 三级降级全屏（v2026-09-28e 定案：默认不启用，不放 #fullscreenBtn 按钮，需要时引导按 F11）
 *
 * ⛔ C 为何不能用「最新 ts 恒赢」：两端各按 2s 心跳续约时，后发布者 ts 必然更大 →
 *    非持权者每次心跳都必定窃权 → 广播权以心跳速率确定性易主 → 学生端在两源页面间来回跳。
 *    正解 = 租约制：持权者活跃期间，任何更新的外来 claim 都夺不走权；仅在【失联超 CLAIM_TTL】
 *    或【带 force 的显式接管】时才易主。判定用「本地最后听到该端续约的时刻」，不跨设备比 ts
 *    （规避两端时钟漂移）。实证：大模型工作原理课件 2026-10-12 控制端唯一改造。
 *
 * 依赖（加载本文件前必须已存在，全部来自 courseware-skeleton / mqtt-framework / 页面主脚本）：
 *   PAGE_IDS, showPage(i), showToast(msg,ms), showConfirmModal(msg,onOk,confirmText), getPageParam(key),
 *   当前页索引 curPage（或经 xmnCurIndex() 桥接）,  // 见下方「索引兼容取值」
 *   NODE_ID, SYNC_TOPIC, CLASS_ID, ACTIVITY_QUIZ_MAP, IS_DEPLOYED(可选),
 *   mqttClient, mqttConnected, MQTT_BROKERS, MQTT_BROKER_INDEX, MQTT_TRIES, MQTT_MAX_TRIES,
 *   xmnConnect, xmnRetryOrNextBroker, updateBadgeStats, offlineQueue, updateSyncStatusUI(可选)
 *
 * 集成点（7 处，缺一不可——半集成会静默失效）：
 *   ① mqtt 'connect' 回调（教师）：  setTimeout(function(){ xmnEnterTeacherRole(); }, 600);   【C/G】
 *      （xmnEnterTeacherRole：探到活跃租约→观察态不广播；否则 startBroadcast 持权）
 *   ② mqtt 'message' 回调开头：      handleControlMessage(raw) / handleSyncMessage(raw)（下方已给出，照抄）
 *   ③ showPage 末尾追加：            if (isBroadcaster && !syncing) xmnBroadcastPage();
 *                                    if (!syncing) lastManualNav = Date.now();      【D】
 *   ④ nextPage/prevPage 首行加闸门：  if (!canStudentNavigate()) return;            【E】
 *   ⑤ closeQRPopup：                 教师端【不要】调 stopBroadcast（弹窗只是出示二维码的工具）；
 *                                    仅学生端防御性 if(!IS_TEACHER) stopBroadcast(); 【A】
 *   ⑥ mqtt 'connect' 回调（学生端）： requestCurrentPage();                        【H】
 *   ⑦ xmnConnect：                   clientId 提升为变量 → 回填 myClientId；connect options 增加 will 遗嘱
 *                                    （topic=SYNC_CTL_TOPIC，payload={id,bye:true}，qos1，retain）【C】
 *
 * 伪全屏 CSS（必须复制到 <style>，菜单必须盖在课件层之上且不透明——实测反模式警告见 SKILL.md §3）：
 *   body.fs-pseudo #pageContainer{position:fixed !important;inset:0 !important;margin-top:0 !important;z-index:9999 !important}
 *   body.fs-pseudo #topNav{z-index:10001 !important}
 *   body.fs-pseudo #navBtns, body.fs-pseudo #mqttStatus{z-index:10000 !important}
 * ===================================================================== */

// ===== 内置 UI 反馈标准件（⚠ 必须内联进课件主脚本，教学控制依赖它） =====
// 微信 WebView / 跨域 sandbox iframe 会【静默抑制】原生 confirm() 与 alert()，
// 必须用页内自定义弹窗。下方两份是审计脚本 audit_skill_self.py 的强制项（showToast + showConfirmModal 缺一不可）。
// 课件缺其中任一个，都会导致对应按钮「点击无反应」（2026-09-29 深度神经网络课件踩坑：只内置了 showToast、漏 showConfirmModal → 清空数据无反应）。
// ⛔ 确认按钮回调【必须传 true】：ok.onclick → onOk(true)。否则调用方 if(ok){...} 恒为假 → 点「确定」清空静默不执行。
function showToast(msg, ms){
  try{
    var t = document.getElementById('xmnToast');
    if(!t){ t = document.createElement('div'); t.id = 'xmnToast';
      t.style.cssText = 'position:fixed;left:50%;top:80px;transform:translateX(-50%);z-index:3000;background:rgba(26,58,92,.92);color:#fff;padding:10px 22px;border-radius:22px;font-size:17px;font-weight:600;box-shadow:0 4px 16px rgba(0,0,0,.25)';
      document.body.appendChild(t); }
    t.textContent = msg; t.style.display = 'block';
    clearTimeout(t._timer); t._timer = setTimeout(function(){ t.style.display = 'none'; }, ms || 2500);
  }catch(e){}
}
function showConfirmModal(msg, onOk, confirmText){
  var old = document.getElementById('xmnConfirmMask'); if(old) old.remove();
  var mask = document.createElement('div'); mask.id = 'xmnConfirmMask';
  mask.style.cssText = 'position:fixed;inset:0;z-index:10001;background:rgba(0,0,0,.5);display:flex;align-items:center;justify-content:center;';
  var box = document.createElement('div');
  box.style.cssText = 'background:#fff;border-radius:16px;padding:24px 28px;max-width:320px;width:86%;text-align:center;box-shadow:0 12px 48px rgba(0,0,0,.28);font-size:16px;line-height:1.6;';
  box.textContent = msg;
  var row = document.createElement('div'); row.style.cssText = 'margin-top:18px;display:flex;gap:12px;justify-content:center;';
  var cancel = document.createElement('button');
  cancel.textContent = '取消';
  cancel.style.cssText = 'padding:9px 22px;border-radius:20px;border:1px solid #ccd;background:#fff;color:#5F5E5A;font-size:15px;cursor:pointer;';
  var ok = document.createElement('button');
  ok.textContent = confirmText || '确认';
  ok.style.cssText = 'padding:9px 22px;border-radius:20px;border:none;background:#E24B4A;color:#fff;font-size:15px;cursor:pointer;';
  cancel.onclick = function(){ mask.remove(); };
  ok.onclick = function(){ mask.remove(); if(onOk) onOk(true); };
  row.appendChild(cancel); row.appendChild(ok); box.appendChild(row); mask.appendChild(box);
  document.body.appendChild(mask);
}
// =====================================================================

// ---- 状态变量（粘贴到主脚本模块级；NODE_ID/PUBLISH_BASE 由 publish_to_library.py 发布时回写） ----
var TEACHER_KEY = 'xmn_teacher_' + NODE_ID;
// 教师身份判定：query（直开时）→ localStorage（设备记忆，裸链保持教师端）。
// ⚠⚠ 交付禁令（2026-09-30 定案）：绝不可把 URL 参数形式写进交付给老师的链接或话术！
//   资料库外壳 302 → iframe 白名单会剥掉 query 与 hash，课件 iframe 内取不到该参数
//   → 教师点开链接仍是学生视角（已实测复现）。_teacherByUrl 仅作「本地直开 / 自托管调试」兜底。
//   唯一可靠的教师入口是下方【F】三连点页码指示器（不依赖任何 URL 参数）。
//   交付话术见 SKILL.md §4.5：三条原文照写，**链接一律用裸链**（不带任何 query）。
var _teacherByUrl = getPageParam('teacher') === '1';
try { if (_teacherByUrl) localStorage.setItem(TEACHER_KEY, '1'); } catch(e){}
var IS_TEACHER = _teacherByUrl || (function(){ try { return localStorage.getItem(TEACHER_KEY) === '1'; } catch(e){ return false; } })();
var SYNC_CTL_TOPIC = SYNC_TOPIC + '/ctl';           // 【C】控制端唯一：租约 + 请求 控制子话题
var CLAIM_TTL = 6000;                               // 租约有效期(ms)：3× 心跳周期，连续 3 次未续约即失联易主
var myClientId = '';                                // 本端 MQTT clientId（xmnConnect 时回填）
var activeClaimId = '';                             // 当前唯一控制端的设备 id
var activeClaimTs = 0;                              // 本地「最后一次听到该端续租」的时刻（不跨设备比 ts）
var observedTeacher = false;                        // 观察态：本端有教师身份但课堂已有活跃控制端，暂不广播
var broadcastSinceTs = 0;                           // 本端认领租约的时刻（冷启动双认领的裁决窗口）
var followTeacher = true;                           // 【D】学生端焊死纯跟随：恒为 true，无自由浏览开关
var lastManualNav = 0;                              // 【D】学生手动翻页时间戳（8s 宽限）
var syncing = false;                                // 同步触发的翻页（不计入手动）
var isBroadcaster = false;                          // 本端是否为「当前唯一控制端」并正在广播
var syncHeartbeat = null;                           // 2s 心跳：续租 +（仅持权者）广播页码
var syncReceived = false;                           // 本端是否收到过老师页码广播

// ---- 页码广播（retain 确保晚进来的学生立即拿到当前页） ----
function xmnBroadcastPage(){
  if(!isBroadcaster || !mqttConnected || !mqttClient) return;
  try{
    // 索引兼容取值：模板分页引擎用 curPage；存量课件沿用旧变量名（如 cur）时经 xmnCurIndex() 桥接。
    // ⚠ 必须内联（勿抽成独立函数）：pagesync-test-mqtt.js 只把具名函数抽进沙箱驱动，
    //   依赖文件内其他自定义函数会 ReferenceError → 回归 FAIL。
    var _ci = (typeof xmnCurIndex === 'function') ? xmnCurIndex() : ((typeof curPage !== 'undefined') ? curPage : -1);
    var payload = JSON.stringify({activity:'__sync__', class:CLASS_ID, page:PAGE_IDS[_ci], idx:_ci, ts:Date.now()});
    mqttClient.publish(SYNC_TOPIC, payload, {qos:1, retain:true});
  }catch(e){}
}
// 【C】续租本端租约（retain 让后来者一进来就读到「课堂已有控制端」）；force=true 为用户显式接管
function publishClaim(force){
  if(!mqttConnected || !mqttClient) return;
  try{
    var _p = {id:myClientId, ts:Date.now()};
    if(force) _p.force = true;
    mqttClient.publish(SYNC_CTL_TOPIC, JSON.stringify(_p), {qos:1, retain:true});
  }catch(e){}
}
// 【C】租约仲裁：在位者优先（本地时间判定，不跨设备比 ts → 规避时钟漂移）
function onClaim(c){
  if(!c || !c.id) return;
  if(c.bye){ if(c.id === activeClaimId){ activeClaimId = ''; activeClaimTs = 0; } return; }  // 遗嘱/主动退出 → 立即释约
  if(!c.ts) return;
  if(c.id === myClientId){ activeClaimTs = Date.now(); return; }                              // 自己续租的回声
  var fresh = activeClaimId && (Date.now() - activeClaimTs <= CLAIM_TTL);                     // 在位者是否仍活跃
  if(fresh && !c.force){
    // 冷启动双认领窗口（本端刚认领 ≤3s 且与对方竞争）：以 clientId 字典序确定性裁决，id 小者胜
    if(activeClaimId === myClientId && (Date.now() - broadcastSinceTs) <= 3000 && c.id < myClientId){
      activeClaimId = c.id; activeClaimTs = Date.now(); xmnDowngradeToObserver(c.id);
    }
    return;
  }
  activeClaimId = c.id; activeClaimTs = Date.now();                                           // 无主/失联/强制接管 → 采纳
  if(isBroadcaster) xmnDowngradeToObserver(c.id);
}
// 让权为观察态（不 publish 空 retain，避免清掉新控制端的租约/页码）
function xmnDowngradeToObserver(holderId){
  isBroadcaster = false;
  if(syncHeartbeat){ clearInterval(syncHeartbeat); syncHeartbeat = null; }
  observedTeacher = true;
  showTeacherObserveBanner(holderId);   // 提示窗自带 3 秒倒计时，超时自动隐藏
}
// 【H】学生进入主动请求当前页：摆脱对 2s 心跳/retain 的被动等待，进入即秒级跳页
function requestCurrentPage(){
  if(!mqttConnected || !mqttClient || IS_TEACHER) return;
  try{ mqttClient.publish(SYNC_CTL_TOPIC, JSON.stringify({req:'page', from:myClientId, ts:Date.now()}), {qos:1}); }catch(e){}
}
function startBroadcast(force){
  isBroadcaster = true;
  observedTeacher = false;
  activeClaimId = myClientId; activeClaimTs = Date.now(); broadcastSinceTs = Date.now();  // 认领租约
  publishClaim(force);
  if(syncHeartbeat) clearInterval(syncHeartbeat);
  // 每 2s：租约续期 +（仅当本端持权时）广播页码——在位者续租、非在位者静默等待，杜绝心跳级易主
  syncHeartbeat = setInterval(function(){
    if(!activeClaimId || activeClaimId === myClientId || Date.now() - activeClaimTs > CLAIM_TTL) publishClaim();
    if(activeClaimId === myClientId) xmnBroadcastPage();
  }, 2000);
  xmnBroadcastPage();
}
function stopBroadcast(){
  isBroadcaster = false;
  if(syncHeartbeat){ clearInterval(syncHeartbeat); syncHeartbeat = null; }
  // 清 retain：避免晚来的学生被旧页码/旧 claim 拽走
  if(mqttConnected && mqttClient){
    try{ mqttClient.publish(SYNC_TOPIC, '', {qos:1, retain:true}); }catch(e){}
    try{ mqttClient.publish(SYNC_CTL_TOPIC, '', {qos:1, retain:true}); }catch(e){}
  }
}
// 主动让权（退出/切换身份）：发一次 bye 让其他端立即释约，再清 retain
function yieldBroadcast(){
  isBroadcaster = false;
  if(syncHeartbeat){ clearInterval(syncHeartbeat); syncHeartbeat = null; }
  if(mqttConnected && mqttClient){
    try{ mqttClient.publish(SYNC_CTL_TOPIC, JSON.stringify({id:myClientId, bye:true, ts:Date.now()}), {qos:1, retain:true}); }catch(e){}
    try{ mqttClient.publish(SYNC_CTL_TOPIC, '', {qos:1, retain:true}); }catch(e){}
    try{ mqttClient.publish(SYNC_TOPIC, '', {qos:1, retain:true}); }catch(e){}
  }
}

// ---- mqtt 'message' 回调的两个前置分支（照抄到回调开头，处理完 return） ----
function handleControlMessage(raw){
  try{
    var _c = JSON.parse(raw);
    if(!_c) return;
    // 【H】学生请求当前页 → 仅持权者回播（M 个广播源也不会回播风暴）
    if(_c.req === 'page'){ if(isBroadcaster && activeClaimId === myClientId) xmnBroadcastPage(); return; }
    onClaim(_c);
  }catch(e){}
}
function handleSyncMessage(raw){
  try{
    var s = JSON.parse(raw);
    if(s && s.page && PAGE_IDS.indexOf(s.page) >= 0){
      syncReceived = true;
      if(IS_TEACHER) return;                            // 【C】教师是广播源，永不跟随
      if(!followTeacher) return;                        // 【D】焊死后恒不触发（纯跟随）
      if(Date.now() - lastManualNav < 8000) return;     // 【D】手动翻页 8s 宽限
      var target = PAGE_IDS.indexOf(s.page);
      var _cur = (typeof xmnCurIndex === 'function') ? xmnCurIndex() : ((typeof curPage !== 'undefined') ? curPage : -1);
      if(target !== _cur){
        syncing = true; showPage(target); syncing = false;
        showToast('已同步到老师正在展示的页面', 2500);
      }
    }
  }catch(e){}
}

// ---- 【C】教师角色进入决策：观察态 / 持权广播 ----
function xmnEnterTeacherRole(){
  var freshHolder = activeClaimId && activeClaimId !== myClientId && (Date.now() - activeClaimTs <= CLAIM_TTL);
  if(freshHolder){
    observedTeacher = true;
    showTeacherObserveBanner(activeClaimId);   // 提示窗自带 3 秒倒计时，超时自动隐藏
  } else {
    observedTeacher = false;
    hideTeacherObserveBanner();
    startBroadcast();
  }
}
// 【C】一键接管：强制认领租约并广播（旧控制端收到 force claim 后立即降级为观察态）
function xmnTakeover(){
  activeClaimId = myClientId; activeClaimTs = Date.now(); broadcastSinceTs = Date.now();
  observedTeacher = false;
  hideTeacherObserveBanner();
  startBroadcast(true);
  showToast('已接管：本机成为唯一控制端', 3000);
}
// 【C】观察态提示窗（多端抢控制权时弹出）：居中弹窗 + 「接管控制」按钮 + **3 秒倒计时**；
//   3 秒内不点「接管控制」→ 弹窗自动隐藏（不夺取控制权），杜绝常驻横幅干扰教学。
var TAKEOVER_CD_SEC = 3;
function clearTakeoverCountdown(b){
  try{ if(b && b._cdTimer){ clearInterval(b._cdTimer); b._cdTimer = null; } }catch(e){}
}
function showTeacherObserveBanner(holderId){
  try{
    var b = document.getElementById('xmnObserveBanner');
    if(!b){
      b = document.createElement('div'); b.id = 'xmnObserveBanner';
      b.style.cssText = 'position:fixed;left:50%;top:50%;transform:translate(-50%,-50%);z-index:3100;' +
        'background:#fff;color:#1A3A5C;padding:22px 26px;border-radius:16px;text-align:center;' +
        'box-shadow:0 14px 50px rgba(0,0,0,.35);border-top:5px solid #E8892B;max-width:320px;width:86%;';
      var msg = document.createElement('div');
      msg.style.cssText = 'font-size:16px;font-weight:700;line-height:1.5;';
      msg.appendChild(document.createTextNode('⚠ 课堂已有控制端，本机处于观察态（不广播）'));
      b.appendChild(msg);
      var cd = document.createElement('div'); cd.id = 'xmnTakeoverCd';
      cd.style.cssText = 'margin-top:10px;font-size:14px;color:#8A6D3B;font-weight:600;';
      b.appendChild(cd);
      var btn = document.createElement('button');
      btn.textContent = '接管控制';
      btn.style.cssText = 'margin-top:14px;padding:9px 24px;border:none;border-radius:20px;background:#E8892B;color:#fff;font-size:15px;font-weight:700;cursor:pointer;';
      btn.onclick = function(){ clearTakeoverCountdown(b); xmnTakeover(); };
      b.appendChild(btn);
      document.body.appendChild(b);
    }
    b.style.display = 'block';
    // 3 秒倒计时：不接管则自动收起（仅隐藏本次提示，不改变控制权归属）
    var _left = TAKEOVER_CD_SEC;
    var _cd = document.getElementById('xmnTakeoverCd');
    var _tick = function(){
      if(_left > 0){ if(_cd) _cd.textContent = '若不接管，' + _left + ' 秒后自动关闭'; }
      else { clearTakeoverCountdown(b); b.style.display = 'none'; }
      _left--;
    };
    clearTakeoverCountdown(b);
    _tick();
    b._cdTimer = setInterval(_tick, 1000);
  }catch(e){}
}
function hideTeacherObserveBanner(){
  try{ var b = document.getElementById('xmnObserveBanner'); if(b){ clearTakeoverCountdown(b); b.style.display = 'none'; } }catch(e){}
}

// ---- 【E】学生端导航闸门（键盘/触摸/按钮全拦，仅页内「逐步揭示」不受影响） ----
function canStudentNavigate(){ return IS_TEACHER; }
// 焊死纯跟随（v2026-09-28e 定案）：学生恒禁导航（按钮/键盘/滑动全锁），仅教师可翻页
// 用法：function nextPage(){ if (!canStudentNavigate()) return; ... }
//      function prevPage(){ if (!canStudentNavigate()) return; ... }

// ---- 初始化（B / 退出按钮 / E / D / F）——在 body 末尾 IIFE 执行 ----
(function xmnInitTeachingControl(){
  // 【B】学生模式：隐藏 📱 徽章（无法误触变成广播者）；教师模式可见
  if(!IS_TEACHER){
    document.querySelectorAll('.qr-badge').forEach(function(el){ el.style.display = 'none'; });
    // 【F-提示已移除 · 2026-10-14 定案】⛔ 任何「连点页码进教师模式」的**页面内提示一律不得出现**
    //   （含 xmnTeacherHint 及任何形式的 toast/浮条）。原因：学生看到后自行连点即夺取控制端权限，
    //   造成课堂混乱。教师入口只靠**线下交付话术**告知（SKILL.md §4B【教师必看】第 2 条），页面零提示。
    // 【H】在 mqtt connect 成功的回调里调用 requestCurrentPage() 主动拉取当前页，
    //     摆脱对 2s 心跳/retain 的被动等待；300ms 首发 + 每 600ms 重试直到 syncReceived（≤4 次）。
    // 片段（放入 mqttClient.on('connect') 内、订阅 SYNC_TOPIC 之后）：
    //   var _reqTries = 0;
    //   var _reqTimer = setInterval(function(){
    //     if(syncReceived || _reqTries >= 4){ clearInterval(_reqTimer); return; }
    //     _reqTries++; requestCurrentPage();
    //   }, 600);
    //   setTimeout(function(){ requestCurrentPage(); }, 300);
  } else {
    showToast('老师控制模式：翻页将自动同步学生端（点 📱 出示答题二维码）', 4000);
    // 教师端绝不出现「跟随老师」开关（学生专属）；提供退出入口便于预览学生视角
    var tb = document.createElement('button');
    tb.id = 'teacherExit';
    tb.style.cssText = 'position:fixed;left:14px;bottom:56px;z-index:250;padding:5px 12px;border:none;border-radius:16px;font-size:12px;background:rgba(0,0,0,.45);color:#fff;cursor:pointer;';
    tb.textContent = '🚪 退出教师模式';
    tb.onclick = function(){ try{ localStorage.removeItem(TEACHER_KEY); }catch(e){} yieldBroadcast(); location.reload(); };
    document.body.appendChild(tb);
  }
  // 【E】学生端导航隐藏（v2026-09-28e 焊死：无自由浏览，永不恢复）
  function setStudentNav(show){
    ['topNav','btnPrev','btnNext'].forEach(function(id){
      var el = document.getElementById(id); if(el) el.style.display = show ? '' : 'none';
    });
  }
  // 【D】焊死纯跟随（v2026-09-28e 定案）：不创建任何「跟随/自由浏览」开关，
  // 学生端导航隐藏且永不恢复；页内"逐步揭示"、答题、仿真交互不受影响。
  if(!IS_TEACHER){ setStudentNav(false); }
  // 【F】教师模式兜底开关：1.5s 内连点三次「页码指示器(如 1/15)」切换教师/学生模式。
  // 不依赖任何 URL 参数——外壳 302/iframe 白名单会丢 query，跨源 iframe 也读不到父页 hash。
  var _piTaps = [];
  var _piEl = document.getElementById('pageIndicator');   // ⚠ 页码指示器元素 id，按课件实际调整
  if (_piEl){
    _piEl.style.cursor = 'default';
    _piEl.addEventListener('click', function(){
      var now = Date.now();
      _piTaps = _piTaps.filter(function(t){ return now - t < 1500; });
      _piTaps.push(now);
      if (_piTaps.length < 3) return;
      _piTaps = [];
      var nextTeacher = !IS_TEACHER, persisted = true;
      try {
        if (nextTeacher) localStorage.setItem(TEACHER_KEY, '1');
        else localStorage.removeItem(TEACHER_KEY);
      } catch(e){ persisted = false; }
      if (persisted && nextTeacher){ location.reload(); return; }   // 存储可用：刷新后按身份重渲染
      // localStorage 不可用（跨源沙箱）：不刷新，就地切换核心 UI
      IS_TEACHER = nextTeacher;
      document.querySelectorAll('.qr-badge').forEach(function(el){ el.style.display = nextTeacher ? '' : 'none'; });
      if (nextTeacher){
        showToast('已切到教师模式（本次会话生效）', 2500);
        showPage((typeof xmnCurIndex === 'function') ? xmnCurIndex() : curPage);
        xmnEnterTeacherRole();   // 【C】探活后持权广播或进入观察态
      } else {
        yieldBroadcast();        // 让权 + 清 retain
        setStudentNav(false);    // 【D】焊死：切回学生模式导航永久隐藏
        showToast('已切回学生模式', 2500);
      }
    });
  }
  console.log('[XMN] teaching-control ready | IS_TEACHER=' + IS_TEACHER + ' | TEACHER_KEY=' + TEACHER_KEY);
})();

/* =====================================================================
 * 三级降级全屏：已抽离为独立 opt-in 模板 references/templates/fullscreen-fallback.js
 *   v2026-09-28e 定案：新课件默认不放全屏按钮、不注入本段；确需时整体复制该文件。
 *   伪全屏 CSS 三条仍需保留在课件 <style>（骨架默认已有），否则回归 S7 FAIL。
 * ===================================================================== */
