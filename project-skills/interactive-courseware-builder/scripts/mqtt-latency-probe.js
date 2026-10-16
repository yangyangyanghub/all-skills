#!/usr/bin/env node
/**
 * mqtt-latency-probe.js — MQTT 教学同步链路「分层诊断」探针（第四代课件）
 * =====================================================================
 * 用途：当用户报「学生扫码后跳页要等 5 秒以上」时，**先判断是代码 bug 还是 broker 基础设施延迟**，
 *       不要在浏览器端反复改代码。本探针用 Node 直连同一个 broker，模拟
 *       「学生发 req:'page' → 教师即时回播当前页 → 学生收到」链路，测真实往返耗时。
 *
 * 判读口径：
 *   往返 < 2.5s  → **broker 层正常**（公共 broker 本身有波动，实测 0.6~1.7s 都算正常），
 *                  端到端慢 = 浏览器侧 connect(4.9~5.9s) / 跨节点消息(5~7s)
 *                  → 属公共 emqx 基础设施延迟，代码已最优，治本只能换低延迟 broker。
 *   往返 > 2.5s 或收不到 → 换 broker 节点 / 自建单节点 emqx，或核查两端 CLASS_ID 是否一致。
 *
 * 用法（必须能 require('mqtt')，用托管 workspace 的 node_modules）：
 *   NODE_PATH="<含 mqtt 包的 node_modules 目录>" \
 *     node mqtt-latency-probe.js --class <CLASS_ID>   # 本课件节点派生值 wb-<node_id>
 *   # 或从课件 HTML 自动抓 MQTT_BROKERS：
 *   NODE_PATH=... node mqtt-latency-probe.js --html E:/.../deploy/index.html --class <CLASS_ID>
 *
 * 参数：--class <CLASS_ID>（决定话题与 broker 选择，必填）
 *       --html <path>    （可选，抓取课件里的 MQTT_BROKERS 池，保持与课件一致）
 *       --brokers <a,b>  （可选，直接给 broker 池，优先于 --html）
 *       --timeout <ms>   （可选，默认 8000）
 * ===================================================================== */
'use strict';
const fs = require('fs');
const mqtt = require('mqtt');

const argv = process.argv.slice(2);
const getArg = (k, d) => { const i = argv.indexOf(k); return i >= 0 ? argv[i + 1] : d; };

const CLASS_ID = getArg('--class', '');
const HTML = getArg('--html', '');
const BROKERS_ARG = getArg('--brokers', '');
const TIMEOUT = parseInt(getArg('--timeout', '8000'), 10);

if (!CLASS_ID) { console.error('缺少 --class <CLASS_ID>（本课件节点派生值 wb-<node_id>，或自定义班级 id）'); process.exit(2); }

// ---- broker 池：优先命令行，其次从课件 HTML 抓（与课件保持同一池，才能同 broker 对比）----
let BROKERS = ['wss://broker-cn.emqx.io:8084/mqtt', 'wss://broker.emqx.io:8084/mqtt'];
if (BROKERS_ARG) {
  BROKERS = BROKERS_ARG.split(',').map(s => s.trim()).filter(Boolean);
} else if (HTML && fs.existsSync(HTML)) {
  const html = fs.readFileSync(HTML, 'utf8');
  const m = html.match(/MQTT_BROKERS\s*=\s*\[([^\]]*)\]/);
  if (m) {
    const list = m[1].match(/['"]([^'"]+)['"]/g);
    if (list && list.length) { BROKERS = list.map(s => s.replace(/^['"]|['"]$/g, '')); }
  }
}

// ---- 与课件一致的确定性 broker 选择（*31 哈希 % 池长；勿用 %2，池长可变）----
function xmnBrokerHash(cid) { let h = 0; for (let i = 0; i < cid.length; i++) { h = (h * 31 + cid.charCodeAt(i)) | 0; } return Math.abs(h) % BROKERS.length; }

const idx = xmnBrokerHash(CLASS_ID);
const BROKER = BROKERS[idx];
const SYNC_TOPIC = 'xmn-sync/' + CLASS_ID;
const CTL = SYNC_TOPIC + '/ctl';

console.log('CLASS_ID    :', CLASS_ID);
console.log('broker pool :', BROKERS.length, '→ idx', idx);
console.log('broker      :', BROKER);
console.log('SYNC_TOPIC  :', SYNC_TOPIC);
console.log('CTL topic   :', CTL);
console.log('---------------------------------------------');

const teacher = mqtt.connect(BROKER, { clientId: 'probe_t_' + Date.now(), clean: true, connectTimeout: 6000 });
const student = mqtt.connect(BROKER, { clientId: 'probe_s_' + Date.now(), clean: true, connectTimeout: 6000 });

let t0 = 0, tReqRecv = 0, tPageRecv = 0, connT = 0, connS = 0;
const startedAt = Date.now();
const mark = (who) => { if (who === 't') connT = Date.now() - startedAt; else connS = Date.now() - startedAt; console.log('[' + who + '] connected +' + (Date.now() - startedAt) + 'ms'); };

teacher.on('connect', () => {
  mark('t');
  teacher.subscribe(CTL, { qos: 1 }, (err) => {
    if (err) { console.error('[teacher] subscribe CTL 失败', err.message); return; }
    teacher.on('message', (topic, msg) => {
      if (topic !== CTL) return;
      try {
        const o = JSON.parse(msg.toString());
        if (o && o.req === 'page') {
          tReqRecv = Date.now();
          // 模拟课件：持权教师收到 req 即时回播当前页
          teacher.publish(SYNC_TOPIC, JSON.stringify({ page: 'PAGE7', idx: 7, ts: Date.now() }), { qos: 1, retain: true });
        }
      } catch (e) {}
    });
    student.emit('teacherReady');
  });
});

student.on('connect', () => {
  mark('s');
  student.subscribe(SYNC_TOPIC, { qos: 1 }, () => {
    student.on('message', (topic) => { if (topic === SYNC_TOPIC) tPageRecv = Date.now(); });
  });
});

student.on('teacherReady', () => {
  setTimeout(() => {
    t0 = Date.now();
    student.publish(CTL, JSON.stringify({ req: 'page', from: 'probe', ts: t0 }), { qos: 1 });
    console.log('[student] req 已发 +' + (t0 - startedAt) + 'ms');
  }, 800);
});

teacher.on('error', e => console.error('[teacher] err', e.message));
student.on('error', e => console.error('[student] err', e.message));

setTimeout(() => {
  const r = {
    连接耗时_教师ms: connT || null,
    连接耗时_学生ms: connS || null,
    教师收到req_ms: tReqRecv ? (tReqRecv - t0) : null,
    学生收到回播_ms: tPageRecv ? (tPageRecv - t0) : null,
    teacherGotReq: !!tReqRecv,
    studentGotPage: !!tPageRecv
  };
  console.log('---------------------------------------------');
  console.log(JSON.stringify(r, null, 2));
  const rt = r.学生收到回播_ms;
  if (rt != null && rt < 2500) {
    console.log('结论：broker 层正常（往返 ' + rt + 'ms）。若端到端仍 >3s，瓶颈在浏览器侧 connect / 跨节点消息 —— 换低延迟 broker 才能根治。');
  } else if (rt != null) {
    console.log('结论：本链路往返 ' + rt + 'ms，偏慢 —— 考虑换 broker 节点 / 自建单节点 emqx。');
  } else {
    console.log('结论：未收到回播 —— 检查两端 CLASS_ID 是否一致（话题是否同一个）/ broker 是否可达。');
  }
  teacher.end(true); student.end(true);
  process.exit(0);
}, TIMEOUT);
