#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Step 4 (4A) generic injection driver for interactive courseware.

Replaces per-course hand-written inject scripts. Courseware-independent parts
(template mods, head/body/JS blocks) are built-in; courseware-specific parts
come from a small JSON config.

Usage:
  python step4_inject.py --config step4.json --html <courseware.html> --probe
  python step4_inject.py --config step4.json --html <courseware.html> --apply

Config schema (JSON):
{
  "quizzes": [ {"act": "pre",  "quizId": "quizPre",  "page": "p1", "hasAvg": false} ],
  "sims":    [ {"act": "sim1", "page": "p3"} ],
  "extraReps": [ {"old": "...", "new": "...", "count": 1, "label": "..."} ]
}

Safety gates (2026-10-02 lessons baked in):
  * idempotency marker: refuses to run twice on the same file
  * every rep(): count assertion + brace-delta assertion (OLD/NEW net braces
    must match - this kills the "rep() ate onPageEnter's closing brace" bug)
  * function-end insertions located via scan_braces.function_span (immune to
    braces inside strings/comments/regex), never via fragile text anchors
  * after writing: full brace re-scan; any imbalance auto-rolls back to .bak
Exit code: 0 = ok, 1 = probe/apply failure.
"""
import io, os, re, sys, json, shutil

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scan_braces as sb

SKILL = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
TMPL = os.path.join(SKILL, 'references', 'templates')
MARKER = '4A_INTERACTION_STANDARD_BLOCK'
FAILS = []

def rep(text, old, new, count, label):
    """Count-asserted + brace-delta-asserted replace. Collects failures."""
    n = text.count(old)
    if n != count:
        FAILS.append('[%s] expected count %d, got %d' % (label, count, n))
        return text
    if (old.count('{') - old.count('}')) != (new.count('{') - new.count('}')):
        FAILS.append('[%s] brace-delta mismatch OLD vs NEW (net braces differ)' % label)
        return text
    return text.replace(old, new)

def quiz_default_id(act):
    return 'quiz' + act[:1].upper() + act[1:]

# ---------------- template loading + fixed mods ----------------

def load_templates():
    mqtt = io.open(os.path.join(TMPL, 'mqtt-framework.js'), encoding='utf-8').read()
    uni  = io.open(os.path.join(TMPL, 'unified-quiz-submit.js'), encoding='utf-8').read()
    qr   = io.open(os.path.join(TMPL, 'qr-badge-injection.js'), encoding='utf-8').read()
    det  = io.open(os.path.join(TMPL, 'detail-stats.js'), encoding='utf-8').read()
    tc   = io.open(os.path.join(TMPL, 'teaching-control.js'), encoding='utf-8').read()
    return mqtt, uni, qr, det, tc

def patch_mqtt(mqtt):
    # 2026-10-13：mqtt-framework.js 模板已升级，C/D 路由与 G/H 连接逻辑可能已内置。
    # 先检测再补丁（幂等），避免「模板已内置 → 锚点失配 → apply 直接失败」。
    # G: broadcaster on connect + H: student requests current page
    if 'xmnEnterTeacherRole' in mqtt:
        print('[step4_inject] mqtt 模板已内置 G/H 连接逻辑，跳过 connect 补丁')
    else:
        mqtt = rep(mqtt,
          "    // 连接后刷新badge统计（可能收到retained消息）\n    Object.keys(ACTIVITY_QUIZ_MAP).forEach(function(act){ updateBadgeStats(act); });",
          "    // 连接后刷新badge统计（可能收到retained消息）\n    Object.keys(ACTIVITY_QUIZ_MAP).forEach(function(act){ updateBadgeStats(act); });\n"
          "    // 【G】广播权随教师模式常驻：教师端连上即持权广播\n"
          "    if (IS_TEACHER) startBroadcast();\n"
          "    // 【H】学生端进入主动请求当前页（摆脱对 2s 心跳/retain 的被动等待）\n"
          "    if (!IS_TEACHER) {\n"
          "      var _reqTries = 0;\n"
          "      var _reqTimer = setInterval(function(){\n"
          "        if ((typeof syncReceived !== 'undefined' && syncReceived) || _reqTries >= 4){ clearInterval(_reqTimer); return; }\n"
          "        _reqTries++; requestCurrentPage();\n"
          "      }, 600);\n"
          "      setTimeout(function(){ requestCurrentPage(); }, 300);\n"
          "    }",
          1, 'mqtt connect G+H')
    # C/D: SYNC message routing branch
    if 'handleSyncMessage' in mqtt:
        print('[step4_inject] mqtt 模板已内置 C/D 消息路由，跳过 message routing 补丁')
    else:
        mqtt = rep(mqtt,
          "  mqttClient.on('message', function(topic, message){\n    try{\n      var str = message.toString();\n      if(!str) return; // cleared retained message\n      var msg = JSON.parse(str), act = msg.activity;",
          "  mqttClient.on('message', function(topic, message){\n    try{\n      var raw = message.toString();\n      if(!raw) return; // cleared retained message\n"
          "      // 【C】【D】页码同步 / 广播权仲裁：SYNC 消息走独立分支，不与答题数据混淆\n"
          "      if (topic === SYNC_TOPIC) { handleSyncMessage(raw); return; }\n"
          "      if (topic === SYNC_CTL_TOPIC) { handleControlMessage(raw); return; }\n"
          "      var str = raw;\n"
          "      var msg = JSON.parse(str), act = msg.activity;",
          1, 'mqtt message routing')
    # xmnClearDo: per-type reset (NEVER _chosen.fill(-1) - corrupts multi-select)
    if 'c._chosen = c._questions.map' in mqtt:
        print('[step4_inject] mqtt 模板 xmnClearDo 已是 per-type reset，跳过 reset 补丁')
    else:
        mqtt = rep(mqtt,
          "        c._submitted = false; c._chosen.fill(-1);",
          "        c._submitted = false;\n"
          "        // per-type reset; NEVER _chosen.fill(-1) (corrupts multi-select)\n"
          "        c._chosen = c._questions.map(function(q){ return isMultiQ(q) ? null : -1; });\n"
          "        c._picked = c._questions.map(function(q){ return isMultiQ(q) ? [] : null; });",
          1, 'mqtt xmnClearDo reset')
    if "qq.classList.remove('answered','submitted')" in mqtt:
        print('[step4_inject] mqtt 模板 xmnClearDo 已含 submitted 清理，跳过 submitted 补丁')
    else:
        mqtt = rep(mqtt,
          "        c.querySelectorAll('.quiz-q').forEach(function(qq){\n          qq.classList.remove('answered');\n          qq.querySelectorAll('.opt').forEach(function(o){ o.classList.remove('selected','correct','wrong'); });\n        });",
          "        c.querySelectorAll('.quiz-q').forEach(function(qq){\n          qq.classList.remove('answered','submitted');\n          qq.querySelectorAll('.opt').forEach(function(o){ o.classList.remove('selected','correct','wrong'); o.style.pointerEvents=''; });\n        });",
          1, 'mqtt xmnClearDo submitted')
    return mqtt

def patch_qr(qr):
    # A: student closes popup -> defensive stopBroadcast
    qr = rep(qr,
      "function closeQRPopup(activity) {\n  var popup = document.getElementById('qrPopup_' + activity);\n  if (popup) popup.classList.remove('show');\n}",
      "function closeQRPopup(activity) {\n  var popup = document.getElementById('qrPopup_' + activity);\n  if (popup) popup.classList.remove('show');\n"
      "  // 【A】student closes popup: defensive stopBroadcast; teacher keeps broadcasting\n"
      "  if (!IS_TEACHER) stopBroadcast();\n}",
      1, 'qr closeQRPopup A')
    return qr

def patch_tc(tc):
    tc2, n = re.subn(r"// ===== 内置 UI 反馈标准件.*?// ---- 状态变量",
                     "// （showToast / showConfirmModal 由 mqtt-framework.js 统一提供，此处不再重复定义）\n// ---- 状态变量",
                     tc, count=1, flags=re.S)
    if n == 1 and 'function showToast(msg, ms){' not in tc2 and 'function showConfirmModal' not in tc2:
        tc = tc2
    else:
        FAILS.append('[tc dedupe] showToast/showConfirmModal block not removed cleanly')
    if 'var syncReceived' in tc:
        print('[step4_inject] teaching-control 模板已内置 syncReceived，跳过该补丁')
    else:
        tc = rep(tc,
          "var syncing = false;",
          "var syncing = false;\nvar syncReceived = false;                        // 【H】student has received teacher page",
          1, 'tc syncReceived')
    return tc

# ---------------- HTML block builders ----------------

HEAD_ADD = (
'<script>\n'
'(function(){\n'
"  var mqttSources = [\n"
"    'https://cdn.jsdelivr.net/npm/mqtt@4.3.7/dist/mqtt.min.js',\n"
"    'https://fastly.jsdelivr.net/npm/mqtt@4.3.7/dist/mqtt.min.js',\n"
"    'https://unpkg.com/mqtt@4.3.7/dist/mqtt.min.js'\n"
"  ];\n"
"  var mIdx = 0;\n"
"  function tryLoadMqtt() {\n"
"    if (mIdx >= mqttSources.length) { console.warn('[MQTT] 所有CDN源均加载失败'); return; }\n"
"    var s = document.createElement('script');\n"
"    s.src = mqttSources[mIdx];\n"
"    s.async = true;\n"
"    s.onload = function() { console.log('[MQTT] 加载成功，源:', mqttSources[mIdx]); };\n"
"    s.onerror = function() { console.warn('[MQTT] 加载失败:', mqttSources[mIdx]); mIdx++; tryLoadMqtt(); };\n"
"    document.head.appendChild(s);\n"
"  }\n"
"  tryLoadMqtt();\n"
"})();\n"
'</script>\n'
'<script async src="https://cdn.jsdelivr.net/npm/qrcode-generator@1.4.4/qrcode.min.js"\n'
'        onerror="console.warn(\'QR generator CDN failed\')"></script>\n'
'<style>\n'
'#mqttStatus{position:fixed;left:14px;bottom:14px;z-index:250;display:flex;align-items:center;gap:7px;background:rgba(26,58,92,.82);color:#fff;padding:6px 12px;border-radius:18px;font-size:14px;font-weight:600;box-shadow:0 4px 14px rgba(0,0,0,.2)}\n'
'#mqttStatus .dot{width:10px;height:10px;border-radius:50%;background:#f44336;display:inline-block}\n'
'#mqttStatus .dot.online{background:#4CAF50}\n'
'#mqttStatus .dot.offline{background:#f44336}\n'
'/* v2026-10-13 页码导航置于顶层（教师唯一入口，勿被通信状态/背景图盖住）：\n'
'   注入式覆盖，令存量课件（旧骨架 z-index:150）重新注入后也能拿到顶层导航层 */\n'
'#navBtns{z-index:500 !important}\n'
'.qr-badge{position:fixed;bottom:28px;right:28px;z-index:500;width:48px;height:48px;border-radius:50%;background:var(--accent,#E8871E);color:#fff;font-size:24px;cursor:pointer;display:none;align-items:center;justify-content:center;box-shadow:0 4px 12px rgba(232,135,30,.4);transition:transform .2s}\n'
'body.deployed .qr-badge.on{display:flex}\n'
'.qr-badge:hover{transform:scale(1.1)}\n'
'.qr-popup{display:none;position:fixed;inset:0;z-index:999;background:rgba(0,0,0,.5);justify-content:center;align-items:center}\n'
'.qr-popup.show{display:flex}\n'
'.qr-popup-inner{position:relative;background:#fff;border-radius:16px;padding:28px 32px;max-width:360px;width:90%;text-align:center;box-shadow:0 12px 48px rgba(0,0,0,.25)}\n'
'.qr-close-x{position:absolute;top:12px;right:12px;width:32px;height:32px;border:none;border-radius:50%;background:transparent;color:var(--primary,#1A3A5C);font-size:20px;cursor:pointer;line-height:32px;padding:0}\n'
'.qr-close-x:hover{background:var(--red,#D93025);color:#fff}\n'
'.qr-img-wrap{margin:8px 0 16px}\n'
'.qr-img-wrap img{max-width:200px;height:auto;border-radius:8px}\n'
'.qr-stat-row{font-size:20px;margin:6px 0;font-weight:600}\n'
'.qr-stat-row span{color:var(--accent,#E8871E);font-weight:700}\n'
'.qr-mini-bars{margin:12px 0;min-height:20px}\n'
'.qr-mini-row{display:flex;align-items:center;gap:8px;margin:4px 0;font-size:14px}\n'
'.qr-mini-row .qlabel{width:28px;color:var(--primary,#1A3A5C);font-weight:700}\n'
'.qr-mini-row .qbar-bg{flex:1;height:14px;background:#e9ecef;border-radius:7px;overflow:hidden}\n'
'.qr-mini-row .qbar-fill{height:100%;border-radius:7px;transition:width .3s}\n'
'.qr-mini-row .qbar-fill.green{background:var(--green,#4CAF50)}\n'
'.qr-mini-row .qbar-fill.orange{background:var(--accent,#E8871E)}\n'
'.qr-mini-row .qpct{width:36px;text-align:right;color:var(--primary,#1A3A5C);font-weight:600}\n'
'.qr-detail-link{display:inline-block;margin:8px 0;padding:8px 18px;border-radius:20px;background:var(--primary,#1A3A5C);color:#fff;font-size:16px;cursor:pointer;text-decoration:none;font-weight:600}\n'
'.qr-detail-link:hover{background:var(--accent,#E8871E)}\n'
'.qr-clear-btn{margin-top:14px;padding:0;background:transparent;border:none;color:#999;font-size:14px;cursor:pointer;text-decoration:underline}\n'
'.qr-clear-btn:hover{color:var(--red,#D93025)}\n'
'.detail-overlay{display:none;position:fixed;inset:0;z-index:999;background:rgba(0,0,0,.55);justify-content:center;align-items:flex-start;padding-top:40px}\n'
'.detail-overlay.show{display:flex}\n'
'.detail-panel{background:#fff;border-radius:16px;width:min(92vw,700px);max-height:88vh;overflow-y:auto;box-shadow:0 12px 48px rgba(0,0,0,.25);padding:28px 32px 32px;position:relative}\n'
'.detail-close-btn{position:absolute;top:16px;right:20px;width:36px;height:36px;border-radius:50%;border:2px solid var(--line,#ddd);background:#fff;font-size:20px;cursor:pointer;display:flex;align-items:center;justify-content:center;color:var(--primary,#1A3A5C);transition:background .2s}\n'
'.detail-close-btn:hover{background:var(--red,#D93025);color:#fff;border-color:var(--red,#D93025)}\n'
'.detail-q-block{border:1px solid var(--line,#ddd);border-radius:12px;padding:12px 18px;margin-bottom:12px;background:var(--paper,#fff)}\n'
'.detail-q-title{font-size:16px;font-weight:700;color:var(--primary,#1A3A5C);margin-bottom:6px}\n'
'.detail-q-bar .bar-row{position:relative;display:block;padding:5px 0;border-bottom:1px dashed var(--line,#ddd)}\n'
'.detail-q-bar .bar-row:last-child{border-bottom:none}\n'
'.detail-q-bar .opt-barline{display:flex;align-items:center;gap:10px}\n'
'.detail-q-bar .opt-tag{font-weight:800;font-size:18px;min-width:44px;flex:none;white-space:nowrap}\n'
'.detail-q-bar .bar-bg{flex:1;height:18px;background:var(--paper-2,#f2f2f2);border-radius:5px;overflow:hidden}\n'
'.detail-q-bar .bar-fill{height:100%;border-radius:5px;display:flex;align-items:center;justify-content:flex-end;padding-right:8px;font-size:13px;color:#fff;font-weight:700}\n'
'.detail-q-bar .bar-fill.green{background:var(--green,#4CAF50)}\n'
'.detail-q-bar .bar-fill.orange{background:var(--accent,#E8871E)}\n'
'.detail-q-bar .bar-fill.gray{background:#b8bcc2}\n'
'.detail-q-bar .opt-pct{width:56px;text-align:right;font-size:20px;font-weight:800;color:var(--primary,#1A3A5C);flex:none}\n'
'.detail-q-bar .opt-tip{position:absolute;bottom:100%;left:0;right:0;margin-bottom:6px;z-index:20;background:var(--primary,#1A3A5C);color:#fff;font-size:13px;line-height:1.45;padding:7px 11px;border-radius:8px;box-shadow:0 6px 18px rgba(30,58,95,.28);opacity:0;visibility:hidden;transform:translateY(4px);transition:opacity .12s ease,transform .12s ease;pointer-events:none;word-break:break-word}\n'
'.detail-q-bar .bar-row:hover .opt-tip{opacity:1;visibility:visible;transform:translateY(0)}\n'
'.qr-join-title{font-size:20px;font-weight:700;color:var(--primary,#1A3A5C);margin:6px 0 2px}\n'
'.qr-join-hint{font-size:15px;color:#666;margin:2px 0 0;line-height:1.5}\n'
'/* v2026-10-13 移动端避让：通信状态条/退出教师按钮上移至导航行（bottom:20px）之上，\n'
'   revealHint 由骨架媒体查询上移至 124px——保证底部页码区只属于导航层（z-index:500） */\n'
'@media(max-width:768px){\n'
'  #mqttStatus{bottom:84px}\n'
'  #teacherExit{left:auto !important;right:14px !important;bottom:84px !important}\n'
'}\n'
'</style>\n'
)

def quiz_popup(act, has_avg):
    avg = ('&nbsp;&nbsp;平均得分: <span id="qrAvg_%s">-</span>' % act) if has_avg else ''
    return (
'<div class="qr-popup" id="qrPopup_%s">\n'
'  <div class="qr-popup-inner">\n'
'    <button class="qr-close-x" onclick="closeQRPopup(\'%s\')">✕</button>\n'
'    <div class="qr-img-wrap"><img id="qrImg_%s" src="" alt="扫码参与%s"></div>\n'
'    <p class="qr-stat-row">参与人数: <span id="qrPart_%s">0</span>%s</p>\n'
'    <div class="qr-mini-bars" id="qrMiniBars_%s"></div>\n'
'    <a class="qr-detail-link" onclick="openDetail(\'%s\');closeQRPopup(\'%s\')">查看每题详情 →</a>\n'
'    <button class="qr-clear-btn" onclick="xmnClear(\'%s\')">清空数据</button>\n'
'  </div>\n'
'</div>\n'
    ) % (act, act, act, act, act, avg, act, act, act, act)

def sim_popup(act):
    # 2026-10-02 修复：仿真页弹窗原缺「参与人数 + 清空数据」，
    # 导致学生在仿真页提交后教师无法清除该活动数据（xmnClear 覆盖不全）。
    # 与 quiz_popup 对齐：给出参与人数读数与清空按钮；不挂 openDetail
    # （仿真活动无题目分布，openDetail 对无映射活动本就安全 return）。
    return (
'<div class="qr-popup" id="qrPopup_%s">\n'
'  <div class="qr-popup-inner">\n'
'    <button class="qr-close-x" onclick="closeQRPopup(\'%s\')">✕</button>\n'
'    <div class="qr-img-wrap"><img id="qrImg_%s" src="" alt="扫码进入仿真页"></div>\n'
'    <p class="qr-stat-row">参与人数: <span id="qrPart_%s">0</span></p>\n'
'    <button class="qr-clear-btn" onclick="xmnClear(\'%s\')">清空数据</button>\n'
'  </div>\n'
'</div>\n'
    ) % (act, act, act, act, act)

def page_ids(html):
    # 从课件 HTML 提取全部页面 section 的 id（含非活动页：封面/讲授/总结）
    # v2026-10-13：每页都要有 QR 徽章（含首页「加入」徽章），活动页用带 data-activity 的徽章，
    # 其余页用无 data-activity 的加入徽章（toggleQRPopup 识别走 openJoinPopup 分支）。
    ids = []
    for m in re.finditer(r'<(section|div)\b[^>]*>', html):
        tag = m.group(0)
        cm = re.search(r'class="([^"]*)"', tag)
        if not cm or not re.search(r'(?:^|\s)page(?:\s|$)', cm.group(1)):
            continue
        idm = re.search(r'\bid="([^"]+)"', tag)
        if idm:
            ids.append(idm.group(1))
    return ids

def join_popup():
    # 2026-10-13：非活动页（封面/讲授/总结等）共用的「加入课堂」弹窗。
    # QR  URL 由 openJoinPopup 按徽章 data-page 动态重建（不同页不同 URL），
    # 无统计数据故不需要 xmnClear（prepublish-check 按 qrPart_/qrAvg_ 豁免）。
    return (
'<div class="qr-popup" id="qrPopup_join">\n'
'  <div class="qr-popup-inner">\n'
'    <button class="qr-close-x" onclick="closeQRPopup(\'join\')">✕</button>\n'
'    <div class="qr-img-wrap"><img id="qrImg_join" src="" alt="扫码加入课堂"></div>\n'
'    <p class="qr-join-title">学生扫码加入本节课</p>\n'
'    <p class="qr-join-hint">扫码后进入当前页，并自动跟随教师端同步</p>\n'
'  </div>\n'
'</div>\n'
    )

def build_body(html, quizzes, sims):
    body = (
'<div id="mqttStatus"><span class="dot" id="mqttDot"></span><span id="mqttText">数据同步: 等待连接</span></div>\n'
'<div class="detail-overlay" id="detailOverlay">\n'
'  <div class="detail-panel" id="detailPanel">\n'
'    <button class="detail-close-btn" onclick="closeDetail()">✕</button>\n'
'    <div id="detailContent"></div>\n'
'  </div>\n'
'</div>\n'
    )
    for q in (quizzes or []):
        body += '<div class="qr-badge" data-activity="%s" data-page="%s" onclick="toggleQRPopup(this)">📱</div>\n' % (q['act'], q['page'])
    for s in (sims or []):
        body += '<div class="qr-badge" data-activity="%s" data-page="%s" onclick="toggleQRPopup(this)">📱</div>\n' % (s['act'], s['page'])
    # v2026-10-13：非活动页补「加入」徽章（无 data-activity），实现每页可扫码
    covered = set(q['page'] for q in (quizzes or [])) | set(s['page'] for s in (sims or []))
    join_pages = [p for p in page_ids(html) if p not in covered]
    for p in join_pages:
        body += '<div class="qr-badge" data-page="%s" onclick="toggleQRPopup(this)">📱</div>\n' % p
    if join_pages:
        body += join_popup()
    for q in (quizzes or []):
        body += quiz_popup(q['act'], q.get('hasAvg', False))
    for s in (sims or []):
        body += sim_popup(s['act'])
    return body

def build_js_block(mqtt, uni, qr, det, tc, quizzes):
    js = '\n/* %s: MQTT + submit-mode + QR badge + teaching control A-H */\n' % MARKER
    js += mqtt + '\n\n'
    js += '/* constants: NODE_ID/PUBLISH_BASE rewritten by publish_to_library.py */\n'
    js += "var NODE_ID = '';\nvar PUBLISH_BASE = '';\n"
    js += "var SYNC_TOPIC = 'xmn-sync/' + (NODE_ID || CLASS_ID);\n"
    js += "var SYNC_CTL_TOPIC = SYNC_TOPIC + '/ctl';\n"
    js += r"var IS_DEPLOYED = (function(){ try { return location.protocol !== 'file:' && /^https?:\/\//.test(PUBLISH_BASE || ''); } catch(e){ return false; } })();" + '\n'
    js += "try { document.body.classList.toggle('deployed', IS_DEPLOYED); } catch(e){}\n"
    # v2026-10-13：徽章 HTML 追加在 </body> 之前（晚于本 JS 块与初始 showPage），
    #   故此处立即遍历徽章必然查空 → 首屏（含首页）徽章永不显示。
    #   处方：DOMContentLoaded 后再「当前页上架、其余下架」（此刻 curPage 已由初始 showPage 定好）。
    js += (
      "/* per-page QR badge init: badges appended at end of <body>, so sync AFTER DOM ready (v2026-10-13) */\n"
      "(function(){ function _xmnBadgeSync(){\n"
      "  if (typeof IS_DEPLOYED === 'undefined' || !IS_DEPLOYED) return;\n"
      "  try {\n"
      "    var _i = (typeof xmnCurIndex === 'function') ? xmnCurIndex() : ((typeof curPage === 'number') ? curPage : 0);\n"
      "    var _id = (typeof PAGE_IDS !== 'undefined' && PAGE_IDS[_i]) ? PAGE_IDS[_i] : null;\n"
      "    document.querySelectorAll('.qr-badge').forEach(function(b){ b.classList.remove('on'); });\n"
      "    var _nb = _id ? document.querySelector('.qr-badge[data-page=\"' + _id + '\"]') : null;\n"
      "    if (_nb) _nb.classList.add('on');\n"
      "  } catch(e){}\n"
      "} if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', _xmnBadgeSync); else _xmnBadgeSync(); })();\n\n"
    )
    js += uni + '\n\n' + qr + '\n\n' + det + '\n\n' + tc + '\n'
    # ACTIVITY_QUIZ_MAP：一律按配置精确发射（2026-10-13）
    # 旧逻辑仅当 quizId 偏离命名约定时才覆盖——但模板默认映射含 mid3，对只有 4 套测验的课件
    # 会残留不存在的 mid3 条目（冒烟测试误报 + xmnClear 清空不存在的容器）。
    # 现在无论命名是否约定，都用配置清单替换模板默认字面量；unified-quiz-submit.js 与
    # detail-stats.js 均经 typeof 守卫复用本映射，无需各自改动。
    if quizzes:
        lit = '{' + ', '.join("%s:'%s'" % (q['act'], q['quizId']) for q in quizzes) + '}'
        js = rep(js, "ACTIVITY_QUIZ_MAP = {pre:'quizPre', mid1:'quizMid1', mid2:'quizMid2', mid3:'quizMid3', post:'quizPost'};",
                 'ACTIVITY_QUIZ_MAP = ' + lit + ';', 1, 'ACTIVITY_QUIZ_MAP emit')
    return js

# ---------------- courseware integration points ----------------

def fn_insert_before_close(text, fname, snippet, label):
    span = sb.function_span(text, fname)
    if span is None:
        FAILS.append('[%s] function %s not found' % (label, fname))
        return text
    pos = span[1] - 1
    if text[pos] != '}':
        FAILS.append('[%s] span end is not a brace' % label)
        return text
    return text[:pos] + snippet + text[pos:]

def fn_insert_after_open(text, fname, snippet, label):
    span = sb.function_span(text, fname)
    if span is None:
        FAILS.append('[%s] function %s not found' % (label, fname))
        return text
    return text[:span[0]+1] + snippet + text[span[0]+1:]

def apply_integration(html, quizzes):
    # 3) showPage end: broadcast + manual-nav timestamp
    # ⚠ 2026-10-13：必须用合体守卫 if (isBroadcaster && !syncing) —— 与 teaching-control.js
    #    模板注释③及 pagesync-test-mqtt.js S3 断言一致；分体写法会挂 S3 门禁。
    html = fn_insert_before_close(html, 'showPage',
      "\n  if (isBroadcaster && !syncing) xmnBroadcastPage();\n  if (!syncing) lastManualNav = Date.now();",
      'showPage D')
    # 4) nav gate (E) - insert right after the opening brace of one-line fns
    html = fn_insert_after_open(html, 'nextPage', ' if (!canStudentNavigate()) return;', 'nextPage E')
    html = fn_insert_after_open(html, 'prevPage', ' if (!canStudentNavigate()) return;', 'prevPage E')
    # onPageEnter: per-page QR badge (param-derived id, immune to inner var names)
    # ⚠ v2026-10-13：必须插在函数【开头】（守卫之前）——若插在函数末尾，会被
    #   `if (pageEntered[id]) return;` 拦截：回访某页时守卫提前 return，徽章停在上一页（错显/不切换）。
    m = re.search(r'function\s+onPageEnter\s*\(\s*([A-Za-z_$][\w$]*)\s*\)', html)
    if m:
        p = m.group(1)
        snippet = (
          "\n  /* [4A] per-page QR badge display（每次进入都切徽章，不可放进 pageEntered 守卫内） */\n"
          "  if (typeof IS_DEPLOYED !== 'undefined' && IS_DEPLOYED) {\n"
          "    try { document.querySelectorAll('.qr-badge').forEach(function(b){ b.classList.remove('on'); }); } catch(e){}\n"
          "    var _qrId = PAGE_IDS[" + p + "];\n"
          "    var _b = (typeof _qrId === 'string') ? document.querySelector('.qr-badge[data-page=\"' + _qrId + '\"]') : null;\n"
          "    if (_b) _b.classList.add('on');\n"
          "  }\n"
        )
        html = fn_insert_after_open(html, 'onPageEnter', snippet, 'onPageEnter QR')
    else:
        FAILS.append('[onPageEnter QR] function onPageEnter(param) not found')
    # submit mode
    html, n = re.subn(r'var\s+isSubmitMode\s*=\s*false\s*;', 'var isSubmitMode = true;', html, count=1)
    if n != 1:
        FAILS.append('[isSubmitMode] var isSubmitMode = false; not found')
    # retry -> submit buttons
    # 2026-10-02 正则放宽：按钮属性顺序/额外属性（如 type="button"）不再导致锚点失配——
    #   旧正则要求 class 与 onclick 紧邻，课件多写一个属性就 4 连 MISS（抽屉原理课件实战踩坑）。
    #   正确方向是注入器迁就 HTML，而非 HTML 迁就注入器。
    RETRY_BTN_PAT = (r'<button[^>]*class="[^"]*btn-retry[^"]*"[^>]*'
                     r'onclick="retryQuiz\(\'{qid}\'\)"[^>]*>[^<]*</button>')
    for q in (quizzes or []):
        pat = RETRY_BTN_PAT.replace('{qid}', re.escape(q['quizId']))
        newbtn = "<button id=\"%s_submitBtn\" class=\"btn-submit\" onclick=\"submitQuiz('%s','%s')\">提交本页成绩</button>" % (q['quizId'], q['quizId'], q['act'])
        html, n = re.subn(pat, newbtn, html, count=1)
        if n != 1:
            FAILS.append('[submit %s] retry button not found' % q['act'])
    return html

# ---------------- probe / apply ----------------

def probe(html, cfg):
    print('== 4A probe ==')
    checks = []
    checks.append(('already-injected guard', MARKER not in html))
    checks.append(('</head> x1', html.count('</head>') == 1))
    checks.append(('</body> x1', html.count('</body>') == 1))
    checks.append(('showPage( defined', re.search(r'function\s+showPage\s*\(', html) is not None))
    checks.append(('showPage(init) call present', bool(re.findall(r'showPage\([^()]{1,40}\)\s*;', html))))
    checks.append(('nextPage( defined', re.search(r'function\s+nextPage\s*\(', html) is not None))
    checks.append(('prevPage( defined', re.search(r'function\s+prevPage\s*\(', html) is not None))
    checks.append(('onPageEnter( defined', re.search(r'function\s+onPageEnter\s*\(', html) is not None))
    checks.append(('PAGE_IDS array present', re.search(r'var\s+PAGE_IDS\s*=\s*\[', html) is not None))
    checks.append(('isSubmitMode=false present', re.search(r'var\s+isSubmitMode\s*=\s*false\s*;', html) is not None))
    for q in cfg.get('quizzes', []):
        pat = (r'<button[^>]*class="[^"]*btn-retry[^"]*"[^>]*'
               r'onclick="retryQuiz\(\'{qid}\'\)"').replace('{qid}', re.escape(q['quizId']))
        checks.append(("retry btn %s" % q['quizId'], re.search(pat, html) is not None))
    for label, okk in checks:
        print('  %-4s %s' % ('OK' if okk else 'MISS', label))
    bal = sb.balance_ok(sb.extract_main_script(html))
    print('  %-4s %s' % ('OK' if bal else 'FAIL', 'source JS currently balanced'))
    bad = [l for l, okk in checks if not okk]
    print('RESULT: %s' % ('ALL OK - safe to --apply' if (not bad and bal) else 'PROBLEMS: %d (fix anchors first)' % len(bad)))
    return 0 if (not bad and bal) else 1

def main():
    args = sys.argv[1:]
    def opt(name):
        return args[args.index(name) + 1] if name in args else None
    cfg_path = opt('--config')
    html_path = opt('--html')
    mode = 'apply' if '--apply' in args else ('probe' if '--probe' in args else None)
    if not (cfg_path and html_path and mode):
        print('usage: step4_inject.py --config <json> --html <file> --probe|--apply')
        return 2
    cfg = json.load(io.open(cfg_path, encoding='utf-8'))
    html = io.open(html_path, encoding='utf-8').read()
    quizzes = cfg.get('quizzes', [])
    sims = cfg.get('sims', [])

    if mode == 'probe':
        return probe(html, cfg)

    # ---- apply ----
    if MARKER in html:
        print('[ERR] already injected (marker found). Refusing to run twice.')
        return 1
    mqtt, uni, qr, det, tc = load_templates()
    mqtt = patch_mqtt(mqtt)
    qr = patch_qr(qr)
    tc = patch_tc(tc)
    if FAILS:
        print('[ERR] template patch failures:')
        for f in FAILS:
            print('  ', f)
        return 1

    orig = html
    # head
    html = rep(html, '</head>', HEAD_ADD + '</head>', 1, 'head inject')
    # js block before last showPage(...) call
    calls = list(re.finditer(r'showPage\([^()]{1,40}\)\s*;', html))
    if not calls:
        FAILS.append('[js inject] no showPage(...) call found')
    else:
        m = calls[-1]
        js_block = build_js_block(mqtt, uni, qr, det, tc, quizzes)
        html = html[:m.start()] + js_block + '\n' + html[m.start():]
    # body before </body>
    html = rep(html, '</body>', build_body(html, quizzes, sims) + '</body>', 1, 'body inject')
    # integration points
    html = apply_integration(html, quizzes)
    # extra courseware-specific reps
    for r in cfg.get('extraReps', []):
        html = rep(html, r['old'], r['new'], r.get('count', 1), r.get('label', 'extra'))

    if FAILS or html == orig:
        print('[ERR] apply failed, file NOT modified:')
        for f in FAILS:
            print('  ', f)
        if html == orig and not FAILS:
            print('   (no change produced)')
        return 1

    # post gate: brace balance on the new main script
    if not sb.balance_ok(sb.extract_main_script(html)):
        print('[ERR] post-apply brace scan UNBALANCED - rolling back to .bak')
        bak = html_path + '.bak_step4'
        io.open(bak, 'w', encoding='utf-8').write(orig)
        return 1

    bak = html_path + '.bak_step4'
    io.open(bak, 'w', encoding='utf-8').write(orig)
    io.open(html_path, 'w', encoding='utf-8').write(html)
    print('[OK] injected. bytes %d -> %d  (backup: %s)' % (
        len(orig.encode('utf-8')), len(html.encode('utf-8')), bak))
    print('[OK] brace scan: BALANCED')
    print('next: node scripts/syntax-check.js %s && node scripts/pagesync-test-mqtt.js %s' % (html_path, html_path))
    return 0

if __name__ == '__main__':
    sys.exit(main())
