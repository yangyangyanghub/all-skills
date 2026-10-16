// MQTT Data Collection Framework (Robust Edition)
// Copy into <script> of single-file HTML
//
// ⚠ 前置依赖 — CDN 多源 fallback（必须放在 <head> 中，不能与 mqtt-framework.js 合并）：
//   见 SKILL.md 4A.2「MQTT 多源 fallback + 状态指示器」完整代码块。
//   中国网络环境下 unpkg.com 经常超时，手机扫码后 MQTT 库加载失败是教师端看不到数据的首要原因。
//
// ⚠ 状态指示器 — CSS + HTML（必须放在 <style> 和 <body> 中）：
//   见 SKILL.md 4A.2 的 CSS 和 HTML 代码块。左下角绿/红 dot 实时显示 MQTT 连接状态。

// === MQTT 配置 ===
// ⚠ 两端（手机/电脑）必须连到「同一个」broker 才能互相同步。
// ⚠ 关键坑：若两端各自独立 fallback（手机 HiveMQ 慢→切 EMQX，教师端留 HiveMQ），
//   会落到不同 broker，导致"手机提交、电脑收不到"。故 broker 选择必须【确定性】——
//   用 CLASS_ID 哈希选同一个 broker，两端必落同一 broker（见下方 xmnBrokerHash）。
// ⚠ 国内课堂优先 broker-cn.emqx.io（EMQX 中国节点，国内网络可达，避免 HiveMQ 被运营商封 8884）。
var MQTT_BROKERS = ['wss://broker-cn.emqx.io:8084/mqtt', 'wss://broker.emqx.io:8084/mqtt', 'wss://broker.hivemq.com:8884/mqtt'];
var MQTT_BROKER_INDEX = 0;
var MQTT_BROKER = MQTT_BROKERS[0];
var MQTT_TRIES = 0;            // 当前 broker 已尝试次数
var MQTT_MAX_TRIES = 3;        // 同一 broker 最多重试次数，超过才切备用
// ⚠ CLASS_ID 铁律：必须节点级隔离（否则所有课件共享同一话题的 answers → 答题数据跨课件串台）。
//   一律走 getPageParam（hash→search→parent，抗外壳剥离 query），派生 'wb-<NODE_ID>' 兜底；
//   不得在课件任何位置（含注释）留占位类名字面量（发布预检会拦截）。
var CLASS_ID = (typeof getPageParam === 'function' ? getPageParam('class') : null) || ('wb-' + ((typeof NODE_ID !== 'undefined') ? NODE_ID : ''));
var XMN_BASE = 'xmn/'+CLASS_ID+'/answers';
// ⚠ 确定性选 broker：同一 CLASS_ID 的教师端与学生端算出同一个序号 → 必落同一 broker，
// 从根上消除"手机在 EMQX、电脑在 HiveMQ"导致的数据不同步。
function xmnBrokerHash(cid){ var h = 0; for (var i = 0; i < cid.length; i++){ h = (h * 31 + cid.charCodeAt(i)) | 0; } return Math.abs(h) % MQTT_BROKERS.length; }
MQTT_BROKER_INDEX = xmnBrokerHash(CLASS_ID);
MQTT_BROKER = MQTT_BROKERS[MQTT_BROKER_INDEX];
var mqttClient = null, mqttConnected = false, mqttExplicitlyOffline = false;

// === 学生 ID（localStorage 持久化，try/catch 防手机隐私模式） ===
var studentId = (function(){
  try{ var sid = localStorage.getItem('xmnSid'); if(sid) return sid; }catch(e){}
  var sid = Math.random().toString(36).slice(2,10);
  try{ localStorage.setItem('xmnSid', sid); }catch(e){}
  return sid;
})();
var offlineQueue = [];
var xmnAgg = {}; // {activity: [{sid, score, total, answers, ts}]}

// === 连接 ===
function xmnConnect(){
  if(typeof mqtt === 'undefined'){ setTimeout(xmnConnect, 500); return; }
  if(mqttClient){ try{ mqttClient.end(true); }catch(e){} }
  mqttConnected = false;
  mqttExplicitlyOffline = false;
  MQTT_BROKER = MQTT_BROKERS[MQTT_BROKER_INDEX];
  MQTT_TRIES++;
  var _cid = 'xmn_'+studentId+'_'+Date.now();
  myClientId = _cid;   // 【C】回填本端 clientId：claim 需自带 id，否则仲裁判据失效（{id:''} 被全网忽略）
  mqttClient = mqtt.connect(MQTT_BROKER, {
    clientId: _cid,
    clean: true,
    connectTimeout: 4000,
    reconnectPeriod: 3000,
    keepalive: 30,
    // 【C】遗嘱：控制端关页面/崩溃/进程被杀时 broker 代发 bye → 其他端立即释约，无需等 CLAIM_TTL 过期
    will: { topic: SYNC_CTL_TOPIC, payload: JSON.stringify({id:_cid, bye:true, ts:0}), qos:1, retain:true }
  });
  mqttClient.on('connect', function(){
    mqttConnected = true;
    console.log('[MQTT] 已连接:', MQTT_BROKER);
    // 更新状态指示器（需配合 CSS/HTML，见 SKILL.md 4A.2「MQTT 连接状态指示器」）
    var dot = document.getElementById('mqttDot');
    var txt = document.getElementById('mqttText');
    if(dot){ dot.className = 'dot online'; }
    if(txt){ txt.textContent = '数据同步: 已连接 ('+MQTT_BROKER.split('/')[2].split(':')[0]+')'; }
    mqttClient.subscribe(XMN_BASE+'/#', {qos:1}, function(err){
      if(err) console.warn('[MQTT] 订阅失败', err); else console.log('[MQTT] 已订阅:', XMN_BASE+'/#');
    });
    // 【D】页码同步 / 【C】claim 仲裁：必须订阅，否则学生收不到教师翻页广播（漏订=学生停首页）
    mqttClient.subscribe(SYNC_TOPIC, {qos:1}, function(err){ if(err) console.warn('[MQTT] 同步订阅失败', err); else console.log('[MQTT] 已订阅:', SYNC_TOPIC); });
    mqttClient.subscribe(SYNC_CTL_TOPIC, {qos:1}, function(err){ if(err) console.warn('[MQTT] 控制订阅失败', err); else console.log('[MQTT] 已订阅:', SYNC_CTL_TOPIC); });
    // 连接后刷新badge统计（可能收到retained消息）
    Object.keys(ACTIVITY_QUIZ_MAP).forEach(function(act){ updateBadgeStats(act); });
    offlineQueue.forEach(function(q){ mqttClient.publish(q.topic, q.payload, {qos:1, retain:true}); });
    offlineQueue = [];
    // 【C/G】教师：先收集 retain 中的活跃租约，再决定「持权广播 / 进观察态」（函数见 teaching-control.js）
    if(IS_TEACHER){ setTimeout(function(){ xmnEnterTeacherRole(); }, 600); }
    // 【H】学生：进入主动请求当前页（300ms 首发 + 每 600ms 重试直到 syncReceived，≤4 次）
    else {
      var _reqTries = 0;
      var _reqTimer = setInterval(function(){
        if(syncReceived || _reqTries >= 4){ clearInterval(_reqTimer); return; }
        _reqTries++; requestCurrentPage();
      }, 600);
      setTimeout(function(){ requestCurrentPage(); }, 300);
    }
  });
  mqttClient.on('message', function(topic, message){
    var _raw = message.toString();
    // 【C】控制子话题（租约仲裁 + req 回播）/【D】页码同步：交由教学控制标准件处理（集成点②）
    if(topic === SYNC_CTL_TOPIC){ handleControlMessage(_raw); return; }
    if(topic === SYNC_TOPIC){ handleSyncMessage(_raw); return; }
    try{
      var str = _raw;
      if(!str) return; // cleared retained message
      var msg = JSON.parse(str), act = msg.activity;
      if(!act) return;
      console.log('[MQTT] 收到数据:', act, '来自:', msg.sid, '得分:', msg.score);
      if(!xmnAgg[act]) xmnAgg[act] = [];
      var idx = xmnAgg[act].findIndex(function(x){return x.sid===msg.sid;});
      if(idx>=0) xmnAgg[act][idx] = msg; else xmnAgg[act].push(msg);
      updateBadgeStats(act);
    }catch(e){}
  });
  mqttClient.on('offline', function(){
    mqttConnected = false;
    mqttExplicitlyOffline = true;
    console.warn('[MQTT] 连接断开(offline)');
    var dot = document.getElementById('mqttDot');
    var txt = document.getElementById('mqttText');
    if(dot){ dot.className = 'dot offline'; }
    if(txt){ txt.textContent = '数据同步: 已断开'; }
  });
  mqttClient.on('error', function(err){
    mqttConnected = false;
    console.warn('[MQTT] 连接错误('+MQTT_BROKER+'):', err && err.message);
    var dot = document.getElementById('mqttDot');
    var txt = document.getElementById('mqttText');
    if(dot){ dot.className = 'dot offline'; }
    if(txt){ txt.textContent = '数据同步: 连接失败'; }
    xmnRetryOrNextBroker();
  });
}

// 先在当前 broker 指数退避重试；多次失败再切备用，且所有 broker 都失败会重置回主 broker，
// 以保证手机与电脑两端最终收敛到同一 broker（这是跨设备同步能成立的前提）。
function xmnRetryOrNextBroker(){
  if(MQTT_TRIES < MQTT_MAX_TRIES){ setTimeout(xmnConnect, 2000 * MQTT_TRIES); return; }
  // 环形切到下一个 broker：两端起始序号相同(由 CLASS_ID 决定)，失败时也按同一顺序切换，
  // 因此教师端与学生端始终落在同一 broker，不会分叉导致数据不同步。
  MQTT_BROKER_INDEX = (MQTT_BROKER_INDEX + 1) % MQTT_BROKERS.length;
  MQTT_TRIES = 0;
  console.log('Switching to fallback MQTT broker:', MQTT_BROKERS[MQTT_BROKER_INDEX]);
  xmnConnect();
}
setTimeout(function(){
  xmnConnect();
  setTimeout(function(){
    if(!mqttConnected && !mqttExplicitlyOffline) xmnRetryOrNextBroker();
  }, 6500);
}, 800);

// === 发布 ===
function xmnPublish(activity, data){
  var payload = JSON.stringify(Object.assign({sid:studentId, activity:activity, ts:Date.now()}, data));
  var topic = XMN_BASE+'/'+studentId+'/'+activity;
  if(mqttConnected && mqttClient){
    mqttClient.publish(topic, payload, {qos:1, retain:true});
    console.log('[MQTT] 已发布:', activity, '得分:', data.score);
  } else {
    offlineQueue.push({topic:topic, payload:payload});
    console.warn('[MQTT] 离线队列暂存:', activity, '(待连接后自动发送)');
  }
}

// === 清空（含 UI 重置） ===
// ⚠ 此映射必须与 unified-quiz-submit.js 的 ACTIVITY_QUIZ_MAP 和 detail-stats.js 的 DETAIL_QUIZ_MAP 保持一致
// 每个项目根据实际测验页数量修改此映射
var ACTIVITY_QUIZ_MAP = {pre:'quizPre', mid1:'quizMid1', mid2:'quizMid2', mid3:'quizMid3', post:'quizPost'};
// 可按需扩展更多中测: mid4, mid5, ...

var ACTIVITY_LABELS = {pre:'前测', mid1:'中测1', mid2:'中测2', mid3:'中测3', post:'后测'};
// 注意：xmnClear 会清空 ACTIVITY_QUIZ_MAP 中全部活动，不限于传入的 activity 参数。
// 这是为了让教师在任何 QR 弹窗中点击"清空数据"都能一键重置整门课件的所有测验数据。

function xmnClear(activity){
  var allQuizActivities = Object.keys(ACTIVITY_QUIZ_MAP);
  // iframe 沙箱可能禁用原生 confirm —— 优先自建模态 showConfirmModal（teaching-control.js），缺失时才退回原生
  var _msg = '确定要清空本课件中全部测验题的数据吗？此操作不可恢复。';
  if (typeof showConfirmModal === 'function') {
    showConfirmModal(_msg, function(ok){ if (ok) xmnClearDo(allQuizActivities); });
    return;
  }
  if(!confirm(_msg)) return;
  xmnClearDo(allQuizActivities);
}
function xmnClearDo(allQuizActivities){
  // 收集所有已知学生 ID（含本机和其他扫码学生），防止误清后 retained 消息重新弹出旧数据
  var allSids = {};
  allQuizActivities.forEach(function(act){
    (xmnAgg[act] || []).forEach(function(s){ if(s && s.sid) allSids[s.sid] = true; });
    allSids[studentId] = true;
  });
  // 清除全部测验活动的 retained 消息、本地聚合、localStorage，并重置界面
  allQuizActivities.forEach(function(act){
    if(mqttConnected && mqttClient){
      Object.keys(allSids).forEach(function(sid){
        mqttClient.publish(XMN_BASE+'/'+sid+'/'+act, '', {qos:1, retain:true});
      });
    }
    xmnAgg[act] = [];
    try{ localStorage.removeItem('xmn_'+act); }catch(e){}
    var containerId = ACTIVITY_QUIZ_MAP[act];
    if(containerId){
      var c = document.getElementById(containerId);
      if(c){
        c._submitted = false; c._chosen.fill(-1);
        var btn = document.getElementById(containerId+'_submitBtn');
        if(btn){ btn.disabled = false; btn.textContent = '提交本页成绩'; }
        c.querySelectorAll('.quiz-q').forEach(function(qq){
          qq.classList.remove('answered');
          qq.querySelectorAll('.opt').forEach(function(o){ o.classList.remove('selected','correct','wrong'); });
        });
        c.querySelectorAll('.feedback').forEach(function(fb){ fb.className='feedback'; fb.innerHTML=''; });
      }
    }
    updateBadgeStats(act);
  });
}

// === 统计面板刷新（内置通用实现，无需项目再写） ===
// ⚠ avgEl 必须始终更新（含清空时重置为 '-'），否则 xmnClear 后旧值残留
// ⚠ 依赖 detail-stats.js 的 DETAIL_QUIZ_MAP 与 quiz-engine.js 的 QUIZZES（两者均需先复制）
function updateBadgeStats(activity) {
  var subs = xmnAgg[activity] || [];
  var partEl = document.getElementById('qrPart_' + activity);
  if (partEl) partEl.textContent = subs.length;
  var avgEl = document.getElementById('qrAvg_' + activity);
  if (avgEl) {
    if (subs.length > 0) {
      var total = subs.reduce(function(s, x) { return s + x.score; }, 0);
      avgEl.textContent = (total / subs.length).toFixed(1);
    } else {
      avgEl.textContent = '-';
    }
  }
  if (typeof populateMiniStats === 'function') populateMiniStats(activity);
}

// === 内置 UI 反馈：showToast / showConfirmModal（MQTT 版标准件） ===
// 存在理由：unified-quiz-submit.js（未答提示）与 xmnClear（清空确认）会调用它们，
//   而 iframe 沙箱常禁用原生 alert/confirm → 提示/确认会静默失效。
//   云变体把这两个函数放在 cloud-sync-framework.js/page-sync.js；母技能对应放在本文件。
//   function 声明会提升，放在文件末尾不影响上方调用。
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

function showConfirmModal(msg, onOk){
  try{
    var ov = document.createElement('div');
    ov.id = 'xmnConfirm';
    ov.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,.45);z-index:4000;display:flex;align-items:center;justify-content:center';
    var box = document.createElement('div');
    box.style.cssText = 'background:#fff;border-radius:14px;padding:26px 30px;max-width:440px;box-shadow:0 10px 34px rgba(0,0,0,.3)';
    var p = document.createElement('p');
    p.style.cssText = 'font-size:19px;color:#1a3a5c;line-height:1.65;margin:0';
    p.textContent = msg;
    var row = document.createElement('div');
    row.style.cssText = 'margin-top:22px;text-align:right';
    var bc = document.createElement('button');
    bc.textContent = '取消';
    bc.style.cssText = 'font-size:17px;padding:9px 20px;margin-right:10px;border:1px solid #ccc;background:#fff;color:#555;border-radius:8px;cursor:pointer';
    var bo = document.createElement('button');
    bo.textContent = '确定';
    bo.style.cssText = 'font-size:17px;padding:9px 22px;border:none;background:#e8722d;color:#fff;border-radius:8px;cursor:pointer;font-weight:600';
    bc.onclick = function(){ try{ document.body.removeChild(ov); }catch(e){} };
    bo.onclick = function(){ try{ document.body.removeChild(ov); }catch(e){} try{ onOk && onOk(true); }catch(e){ console.warn(e); } };
    row.appendChild(bc); row.appendChild(bo);
    box.appendChild(p); box.appendChild(row); ov.appendChild(box);
    document.body.appendChild(ov);
    return true;
  }catch(e){
    if (window.confirm(msg)) { try{ onOk && onOk(true); }catch(e2){} return true; }
    return false;
  }
}
