// QR Badge Injection — 交互页QR徽章注入模板（Robust Edition）
// 在Step 4（学生交互模式）中，为每个测验/仿真页注入QR徽章

// ===== 依赖脚本 =====
// 课件 <head> 中需放入（本模板自带注释，勿在此处写 script 结束标签字面量）：
//   qrcode-generator CDN：cdn.jsdelivr.net/npm/qrcode-generator@1.4.4/qrcode.min.js（async）
// ⚠ 坑：JS 注释里出现 script 结束标签字面量会提前截断所在 script 元素，
//      导致其后整段标准件失效（syntax-check 报 Invalid or unexpected token）。

// ===== HTML模板 =====
/*
  在每个交互页的section末尾添加:
  <div class="qr-badge" data-activity="pre" data-page="p1" onclick="toggleQRPopup(this)">📱</div>

  弹窗模板（新布局：关闭叉在右上角，QR图下方依次是人数/迷你条形图/查看详情/清空数据）:
  注意：清空数据按钮的 onclick 只调 xmnClear，【不要】追加 closeQRPopup——
  否则点清空后弹窗被关闭，用户会"离开二维码页面"（已在《价格理论》课件踩坑）。
  <div class="qr-popup" id="qrPopup_pre">
    <div class="qr-popup-inner">
      <button class="qr-close-x" onclick="closeQRPopup('pre')">✕</button>
      <div class="qr-img-wrap"><img id="qrImg_pre" src="" alt="扫码参与前测"></div>
      <p class="qr-stat-row">参与人数: <span id="qrPart_pre">0</span></p>
      <div class="qr-mini-bars" id="qrMiniBars_pre"></div>
      <a class="qr-detail-link" onclick="openDetail('pre');closeQRPopup('pre')">查看每题详情 →</a>
      <button class="qr-clear-btn" onclick="xmnClear('pre')">清空数据</button>
    </div>
  </div>

  后测弹窗可额外显示平均得分:
  <p class="qr-stat-row">参与人数: <span id="qrPart_post">0</span>&nbsp;&nbsp;平均得分: <span id="qrAvg_post">-</span></p>

  ⚠ 每页徽章制（v2026-10-13）：非活动页（封面/讲授/总结）也必须有徽章——
  无 data-activity 的「加入」徽章，点击走 openJoinPopup 分支（共用加入弹窗，二维码按页动态生成）。
  加入弹窗由 step4_inject.py 的 build_body 自动注入，无需手写：
  <div class="qr-popup" id="qrPopup_join">
    <div class="qr-popup-inner">
      <button class="qr-close-x" onclick="closeQRPopup('join')">✕</button>
      <div class="qr-img-wrap"><img id="qrImg_join" src="" alt="扫码加入课堂"></div>
      <p class="qr-join-title">学生扫码加入本节课</p>
      <p class="qr-join-hint">扫码后进入当前页，并自动跟随教师端同步</p>
    </div>
  </div>
*/

// ===== CSS =====
/*
.qr-badge{
  position:fixed;bottom:28px;right:28px;z-index:500;
  width:48px;height:48px;border-radius:50%;
  background:var(--accent);color:#fff;font-size:24px;
  cursor:pointer;display:none;align-items:center;justify-content:center;
  box-shadow:0 4px 12px rgba(255,143,0,.4);transition:transform .2s;
}
body.deployed .qr-badge.on{display:flex}
.qr-badge:hover{transform:scale(1.1)}
.qr-popup{
  display:none;position:fixed;inset:0;z-index:999;
  background:rgba(0,0,0,.5);justify-content:center;align-items:center;
}
.qr-popup.show{display:flex}
.qr-popup-inner{
  position:relative;background:#fff;border-radius:16px;padding:28px 32px;
  max-width:360px;width:90%;text-align:center;box-shadow:0 12px 48px rgba(0,0,0,.25);
}
.qr-close-x{
  position:absolute;top:12px;right:12px;width:32px;height:32px;
  border:none;border-radius:50%;background:transparent;color:var(--primary);
  font-size:20px;cursor:pointer;line-height:32px;padding:0;
}
.qr-close-x:hover{background:var(--red);color:#fff}
.qr-img-wrap{margin:8px 0 16px}
.qr-img-wrap img{max-width:200px;height:auto;border-radius:8px}
.qr-stat-row{font-size:20px;margin:6px 0;font-weight:600}
.qr-stat-row span{color:var(--accent);font-weight:700}
.qr-mini-bars{margin:12px 0;min-height:20px}
.qr-mini-row{display:flex;align-items:center;gap:8px;margin:4px 0;font-size:14px}
.qr-mini-row .qlabel{width:28px;color:var(--primary);font-weight:700}
.qr-mini-row .qbar-bg{flex:1;height:14px;background:#e9ecef;border-radius:7px;overflow:hidden}
.qr-mini-row .qbar-fill{height:100%;border-radius:7px;transition:width .3s}
.qr-mini-row .qbar-fill.green{background:var(--green)}
.qr-mini-row .qbar-fill.orange{background:var(--accent)}
.qr-mini-row .qpct{width:36px;text-align:right;color:var(--primary);font-weight:600}
.qr-detail-link{
  display:inline-block;margin:8px 0;padding:8px 18px;border-radius:20px;
  background:var(--primary-light);color:#fff;font-size:16px;cursor:pointer;
  text-decoration:none;font-weight:600;
}
.qr-detail-link:hover{background:var(--accent)}
.qr-clear-btn{
  margin-top:14px;padding:0;background:transparent;border:none;
  color:#999;font-size:14px;cursor:pointer;text-decoration:underline;
}
.qr-clear-btn:hover{color:var(--red)}
.qr-join-title{font-size:20px;font-weight:700;color:var(--primary);margin:6px 0 2px}
.qr-join-hint{font-size:15px;color:#666;margin:2px 0 0;line-height:1.5}
*/

// ===== JS逻辑 =====
// ⚠ CLASS_ID 由 mqtt-framework.js 定义（唯一来源），此处直接复用，不得重复声明
//   （若本文件先于 mqtt-framework.js 复制，可在课件 <script> 顶部补：
//    var CLASS_ID = getPageParam('class') || ('wb-' + NODE_ID);）

// ===== QR 基址（坑表「nullsrcdoc 坏码」处方）：PUBLISH_BASE 优先；srcdoc/file 场景绝不生成坏码 =====
function getQrBase() {
  if (typeof PUBLISH_BASE !== 'undefined' && PUBLISH_BASE && PUBLISH_BASE.indexOf('https://') === 0) return PUBLISH_BASE;
  if ((location.protocol === 'https:' || location.protocol === 'http:') && location.origin && location.origin !== 'null') {
    return location.origin + location.pathname;
  }
  return null;
}

// 本地优先生成 QR dataURI（v2026-10-13 提为模块级：加入弹窗 openJoinPopup 复用）
function _xmnLocalQr(img, url) {
  if (typeof qrcode === 'undefined') return false;
  try { var q = qrcode(0, 'L'); q.addData(url); q.make(); img.src = q.createDataURL(4, 0); return true; }
  catch (e) { return false; }
}

// v2026-10-13 每页徽章制：非活动页（封面/讲授/总结）的「加入」徽章 → 共用加入弹窗。
// QR URL 按徽章 data-page 动态重建——每次打开都重新生成（禁用 src 缓存，不同页不同 URL）。
function openJoinPopup(pageId) {
  var popup = document.getElementById('qrPopup_join');
  if (!popup) return;
  var qrBase = getQrBase();
  if (!qrBase) { if (typeof showToast === 'function') showToast('请先发布课件后再使用扫码功能', 3000); return; }
  var qrUrl = qrBase + '#page=' + pageId + '&class=' + CLASS_ID;
  var qrImg = document.getElementById('qrImg_join');
  if (qrImg) {
    qrImg.removeAttribute('data-qrdone');
    if (!_xmnLocalQr(qrImg, qrUrl)) {
      qrImg.src = 'https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=' + encodeURIComponent(qrUrl);
    }
  }
  popup.classList.add('show');
}

function toggleQRPopup(badge) {
  var activity = badge.getAttribute('data-activity');
  var pageId = badge.getAttribute('data-page');
  // 无 data-activity = 非活动页加入徽章（v2026-10-13 每页徽章制）→ 加入弹窗分支
  if (!activity) { openJoinPopup(pageId); return; }
  var popup = document.getElementById('qrPopup_' + activity);
  if (!popup) return;

  var qrBase = getQrBase();
  if (!qrBase) { if (typeof showToast === 'function') showToast('请先发布课件后再使用扫码功能', 3000); return; }
  var qrUrl = qrBase + '#page=' + pageId + '&class=' + CLASS_ID;
  var qrImg = document.getElementById('qrImg_' + activity);
  // ⚠ 必须用 getAttribute('src') 判断，因为 element.src 在属性为空时会返回当前页URL
  // ⚠ 本地优先（v2026-10-02 定案）：qrcode-generator 以 async 引入，同步调用时库未就绪
  //   → 旧写法恒走远端 qrserver（国内慢/不可达），且库就绪后 src 非空、本地生成永不执行。
  //   处方：首次先试本地，失败挂远端占位；已挂远端的，轮询（≤6s）等库就绪换本地 data URI，data-qrdone 防重复。
  if (qrImg) {
    if (!qrImg.getAttribute('src')) {
      if (!_xmnLocalQr(qrImg, qrUrl)) {
        qrImg.src = 'https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=' + encodeURIComponent(qrUrl);
      }
    } else if (qrImg.getAttribute('src').indexOf('data:image') !== 0 && !qrImg.getAttribute('data-qrdone')) {
      var _t0 = Date.now();
      var _iv = setInterval(function () {
        if (_xmnLocalQr(qrImg, qrUrl)) { qrImg.setAttribute('data-qrdone', '1'); clearInterval(_iv); }
        else if (Date.now() - _t0 > 6000) { clearInterval(_iv); }
      }, 250);
    }
  }

  popup.classList.toggle('show');
  if (popup.classList.contains('show')) populateMiniStats(activity);
}

function closeQRPopup(activity) {
  var popup = document.getElementById('qrPopup_' + activity);
  if (popup) popup.classList.remove('show');
}

// 弹窗内迷你条形图（每题正确率）
// ⚠ 依赖 DETAIL_QUIZ_MAP（来自 detail-stats.js）和 QUIZZES（来自 quiz-engine.js）
// 确保这两个变量在调用 populateMiniStats 之前已定义（detail-stats.js 和 quiz-engine.js 需先复制到 <script>）
function populateMiniStats(activity) {
  var quizId = DETAIL_QUIZ_MAP ? DETAIL_QUIZ_MAP[activity] : null;
  var barsEl = document.getElementById('qrMiniBars_' + activity);
  if (!barsEl) return;
  var questions = quizId && QUIZZES[quizId] ? QUIZZES[quizId].questions : [];
  var submissions = xmnAgg[activity] || [];
  var totalSubs = submissions.length;
  if (totalSubs === 0 || questions.length === 0) { barsEl.innerHTML = ''; return; }
  var html = '';
  for (var qi = 0; qi < questions.length; qi++) {
    var correctCount = 0;
    submissions.forEach(function(sub) {
      if (sub.answers && sub.answers[qi] && sub.answers[qi].isCorrect) correctCount++;
    });
    var pct = Math.round(correctCount / totalSubs * 100);
    html += '<div class="qr-mini-row">';
    html += '<span class="qlabel">Q' + (qi+1) + '</span>';
    html += '<div class="qbar-bg"><div class="qbar-fill ' + (pct >= 60 ? 'green' : 'orange') + '" style="width:' + Math.max(pct, 2) + '%"></div></div>';
    html += '<span class="qpct">' + pct + '%</span>';
    html += '</div>';
  }
  barsEl.innerHTML = html;
}

// 需在页面进入时显示对应QR徽章
// onPageEnter 示例（⚠ 必须加 IS_DEPLOYED 闸门：未部署的静态文件绝不显示徽章，否则误导用户以为可扫码互动）：
// var IS_DEPLOYED = (function(){ try { return location.protocol!=='file:' && /^https?:\/\//.test(PUBLISH_BASE||''); } catch(e){ return false; } })();
//
// ⚠ v2026-10-13 每页徽章制：build_body 为每个页面 section 都注入一枚徽章
//   （活动页带 data-activity，其余页为加入徽章）——「全部下架+当前页上架」天然实现
//   「每页都有且只有一枚可见徽章（含首页）」。
//
// ⚠⚠ 徽章切换有【两个必守点位】（step4_inject.py 已按此注入，勿手改回退）：
//   ① onPageEnter 开头的 toggle 必须插在函数【开头】（`if (pageEntered[id]) return;` 守卫【之前】）——
//      插在函数末尾会被守卫拦截：回访某页时守卫提前 return，徽章停在上一页（「回访错显」）。
//   ② 徽章 HTML 追加在文档末尾、body 收尾标签之前（晚于初始 showPage 与 JS 块），故加载时 onPageEnter 查不到徽章 →
//      必须在 DOMContentLoaded 后再同步一次「当前页徽章」（build_js_block 注入的 _xmnBadgeSync），
//      否则首屏（含首页）徽章永不显示（「首屏无徽章」）。
