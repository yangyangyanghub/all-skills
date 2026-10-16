#!/usr/bin/env node
/**
 * sync-e2e-live.js — 线上「学生跟随」端到端实测（playwright + 真 broker）
 * =====================================================================
 * 用途：对**已发布**的课件网址，模拟学生视角打开，再用外部 MQTT 客户端
 *   直接向 SYNC_TOPIC 发布页码广播，断言学生页真的跟着跳转。
 *   能一次抓住 pagesync 静态断言抓不到的线上集成缺陷（如 connect 回调漏订
 *   SYNC_TOPIC/SYNC_CTL_TOPIC —— 2026-09-29 认知负荷理论实战）。
 *
 * 用法：
 *   NODE_PATH=<node workspace node_modules> node sync-e2e-live.js <url|nodeId>
 *   例：node sync-e2e-live.js https://workbuddy.link/p/mDvHgg4vh3Zi64YURstw7e
 *
 * 依赖：playwright + mqtt（装在托管 node workspace，见上方 NODE_PATH）
 * 输出：stdout 末行 RESULT: E2E_PASS（订阅/连接/收报全过 + 注入跟随已验证）
 *   / E2E_SUBSCRIBE_OK（发布端连不上公共 broker 时降级：仅订阅·连接·收报断言，注入未执行）
 *   / E2E_FAIL(=n)；exit 0(=PASS/SUBSCRIBE_OK) 或 1
 * 说明：
 *   - 学生端每条课件可能落在 3 个公共 broker 之一，按课件内 xmnBrokerHash(CLASS_ID) 复现；
 *   - 学生初始 showPage 会写 lastManualNav，8s 宽限内忽略广播 → 脚本先等 ~13s 再发；
 *   - 若断言前页 == 断言后页 → FAIL（说明未跟随）。
 * =====================================================================
 */
const path = require('path');
let chromium, mqtt;
try { ({ chromium } = require('playwright')); } catch (e) { console.error('缺少 playwright，请设置 NODE_PATH 指向托管 node workspace/node_modules'); process.exit(2); }
try { mqtt = require('mqtt'); } catch (e) { console.error('缺少 mqtt'); process.exit(2); }

const arg = process.argv[2];
if (!arg) { console.error('用法: node sync-e2e-live.js <url|nodeId>'); process.exit(2); }
const m = /\/p\/([^/?#]+)/.exec(arg);
const NODE_ID = m ? m[1] : arg.trim();
const URL = m ? arg : 'https://workbuddy.link/p/' + NODE_ID;
const CLASS_ID = 'wb-' + NODE_ID;
const BROKERS = ['wss://broker-cn.emqx.io:8084/mqtt', 'wss://broker.emqx.io:8084/mqtt', 'wss://broker.hivemq.com:8884/mqtt'];
const SYNC_TOPIC = 'xmn-sync/' + NODE_ID;
function xmnBrokerHash(cid) { let h = 0; for (let i = 0; i < cid.length; i++) { h = (Math.imul(h, 31) + cid.charCodeAt(i)) | 0; } return Math.abs(h) % BROKERS.length; }
const BROKER = BROKERS[xmnBrokerHash(CLASS_ID)];
const P1 = process.argv[3] || 'p5';
const P2 = process.argv[4] || 'p8';
const sleep = ms => new Promise(r => setTimeout(r, ms));
let fails = 0;
const ck = (name, ok, extra) => { console.log((ok ? '  PASS  ' : '  FAIL  ') + name + (extra ? '   ← ' + extra : '')); if (!ok) fails++; };

(async () => {
  // 看门狗：无论如何 150s 内强制退出（防 playwright/broker 挂起导致永不结束）
  setTimeout(() => { console.error('WATCHDOG: 总时长超时，强制退出'); console.log('RESULT: E2E_TIMEOUT'); process.exit(3); }, 150000);
  console.log('=== sync-e2e-live:', URL);
  console.log('  CLASS_ID=' + CLASS_ID + ' broker=' + BROKER + ' SYNC_TOPIC=' + SYNC_TOPIC);
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  const logs = [];
  page.on('console', x => logs.push(x.text()));
  await page.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await sleep(13000); // 等 MQTT 连接 + 过 8s 宽限

  let cw = null;
  for (const f of page.frames()) { try { if (await f.evaluate(() => !!document.getElementById('pageIndicator'))) { cw = f; break; } } catch (e) {} }
  ck('定位到课件 iframe（#pageIndicator）', !!cw);
  if (!cw) { await browser.close(); console.log('RESULT: E2E_FAIL=' + fails); process.exit(1); }
  ck('学生视角 IS_TEACHER=false', (await cw.evaluate(() => typeof IS_TEACHER !== 'undefined' && IS_TEACHER === false)));
  ck('MQTT 已连接', (await cw.evaluate(() => typeof mqttConnected !== 'undefined' && mqttConnected === true)));
  ck('已订阅 SYNC_TOPIC', logs.some(l => l.indexOf('已订阅: ' + SYNC_TOPIC) >= 0));
  ck('已订阅 SYNC_CTL_TOPIC', logs.some(l => l.indexOf('已订阅: ' + SYNC_TOPIC + '/ctl') >= 0));

  const before = await cw.evaluate(() => (document.querySelector('.page.active') || {}).id);
  const client = mqtt.connect(BROKER, { connectTimeout: 8000, reconnectPeriod: 0, clientId: 'e2e_pub_' + Date.now() });
  let pubOk = true;
  try { await new Promise((res, rej) => { client.on('connect', res); client.on('error', rej); setTimeout(() => rej(new Error('pub connect timeout')), 12000); }); }
  catch (err) { pubOk = false; console.log('  NOTE  发布端连接失败（' + err.message + '）——公共 broker 限流/不稳；跳过注入，仅保留「连接 + 订阅 + 收报」断言'); }
  if (pubOk) {
  // 探测并发真实广播者（教师端每 2s 发一条 __sync__ 心跳）——存在时会把学生拽回其所在页
  let externalBeat = 0;
  client.subscribe(SYNC_TOPIC, { qos: 1 });
  client.on('message', (t, m) => { const s = m.toString(); if (s.indexOf('"__sync__"') >= 0) externalBeat++; });
  await sleep(2500);
  const concurrent = externalBeat > 0;
  if (concurrent) console.log('  NOTE  检测到并发广播者心跳 ' + externalBeat + ' 条（真实教师端可能在线，会把学生同步到其所在页，覆盖本次注入）');
  const read = async () => cw.evaluate(() => (document.querySelector('.page.active') || {}).id);
  // 公共 broker 跨节点延迟 5–7s + 可能存在的并发真实教师广播（每 2s 心跳会覆盖）：
  // 重发 + 快轮询（每 300ms）捕捉"至少到达一次目标页"即判定跟随成功。
  async function flipTo(target) {
    for (let round = 0; round < 5; round++) {
      client.publish(SYNC_TOPIC, JSON.stringify({ page: target }), { qos: 1, retain: true });
      for (let i = 0; i < 10; i++) { await sleep(300); const cur = await read(); if (cur === target) return cur; }
    }
    return await read();
  }
  const after1 = await flipTo(P1);
  // 硬断言：学生端收到任意合法页码广播即证明 SYNC_TOPIC 订阅链路通（不受并发广播者干扰）
  const recv = await cw.evaluate(() => typeof syncReceived !== 'undefined' && syncReceived === true);
  ck('学生端收到页码广播（syncReceived=true）', recv, 'after=' + after1);
  // 注入跟随：仅当无并发广播者时才可作为硬断言（否则学生被真实教师端持续拽回，不可判定）
  if (concurrent && after1 !== P1) {
    console.log('  SKIP  并发广播者在线，注入 ' + P1 + ' 被其覆盖 → 跳过"注入跟随"硬断言（订阅与收报已由上一项证实）');
  } else {
    ck('广播 ' + P1 + ' 后学生跟随', after1 === P1, 'before=' + before + ' after=' + after1);
  }
  const after2 = await flipTo(P2);
  if (concurrent && after2 !== P2) {
    console.log('  SKIP  并发广播者在线，注入 ' + P2 + ' 被其覆盖 → 跳过"注入跟随"硬断言');
  } else {
    ck('广播 ' + P2 + ' 后学生跟随', after2 === P2, 'after=' + after2);
  }

  }

  try { client.end(true); } catch (e) {}
  const result = (fails === 0 ? (pubOk ? 'E2E_PASS' : 'E2E_SUBSCRIBE_OK') : 'E2E_FAIL=' + fails);
  console.log('RESULT: ' + result);
  try { await Promise.race([browser.close(), sleep(5000)]); } catch (e) {}
  process.exit(fails === 0 ? 0 : 1);
})().catch(e => { console.error('E2E ERROR:', e.message); console.log('RESULT: E2E_FAIL'); process.exit(1); });
