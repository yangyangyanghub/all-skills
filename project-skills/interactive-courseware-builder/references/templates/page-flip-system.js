// Page Flip System — 翻页导航核心框架
// 直接复制到课件 <script> 中，只修改 PAGE_IDS 和 PAGE_LABELS
// ⚠ 加载顺序：本文件必须**最先**复制（getPageParam 在此定义，供 mqtt-framework.js / teaching-control.js 复用）。
// ⚠ 依赖说明：本文件引用 reveal 引擎变量（pageRevealActive / pageRevealQueues / pageRevealIndex /
//   nextReveal / prevReveal），这些由 courseware-skeleton.html 的 reveal 引擎定义；若脱离骨架单独使用，
//   需自行补齐上述变量与函数，否则键盘"揭示优先"分支不生效（回退为纯翻页）。

// ===== URL 参数解析（hash → search → parent）=====
// 资料库外壳会剥离内嵌 iframe 的 query，学生扫码跳页走 hash（#page=..&class=..）；
// 教师身份 / 班级参数同样可能只出现在 hash 或父窗口。故必须按 hash → search → parent 依次解析。
// ⚠ 单一事实来源：全技能所有 URL 参数读取一律调用本函数，
//   **禁止**再用 `new URLSearchParams(location.search)`（外壳下 query 拿不到 → 扫码跳页 / 班级隔离静默失效）。
function getPageParam(k) {
  try {
    var h = location.hash || '';
    if (h.indexOf(k + '=') >= 0) {
      var m1 = new RegExp('[#&]' + k + '=([^&#]*)').exec(h);
      if (m1) return decodeURIComponent(m1[1]);
    }
    var q = location.search || '';
    if (q.indexOf(k + '=') >= 0) {
      var m2 = new RegExp('[?&]' + k + '=([^&#]*)').exec(q);
      if (m2) return decodeURIComponent(m2[1]);
    }
    if (window.parent && window.parent !== window) {
      try {
        var psrc = (window.parent.location.hash || '') + '&' + (window.parent.location.search || '');
        if (psrc.indexOf(k + '=') >= 0) {
          var m3 = new RegExp('[#&?]' + k + '=([^&#]*)').exec(psrc);
          if (m3) return decodeURIComponent(m3[1]);
        }
      } catch (e) { /* 跨源不可读 → 忽略 */ }
    }
  } catch (e) {}
  return null;
}

// ===== 配置块 =====
// ⭐ 下列两个数组**必须按本课件实际页数改写**，此处仅为格式示例（示例 4 页）。
//    PAGE_IDS 的每项 = 一个 <section id="...">；PAGE_LABELS 与之一一对应（导航芯片显示文字）。
var PAGE_IDS = ['p0','p1','p2','p3'];   // 示例：逐页填写，长度 = 课件实际页数
var PAGE_LABELS = ['封面','前测','讲授页1','总结'];
// 图片路径前缀 — 图片统一放 deploy/img/ 子目录，部署后 URL 为 img/xxx.jpg
var IMG_PREFIX = 'img/';

var curPage = 0;

function showPage(i) {
  if (i < 0 || i >= PAGE_IDS.length) return;
  var oldEl = document.querySelector('.page.active');
  if (oldEl) oldEl.classList.remove('active');
  var newEl = document.getElementById(PAGE_IDS[i]);
  if (newEl) {
    newEl.classList.add('active');
    newEl.scrollTop = 0;
  }
  curPage = i;
  // 更新导航芯片
  document.querySelectorAll('#topNav .chip').forEach(function(c, idx) {
    c.classList.toggle('active', idx === i);
  });
  // 更新进度条
  document.getElementById('progressBar').style.width = ((i + 1) / PAGE_IDS.length * 100) + '%';
  // 更新页码指示器
  document.getElementById('pageIndicator').textContent = (i + 1) + '/' + PAGE_IDS.length;
  // 更新按钮状态
  document.getElementById('btnPrev').disabled = (i === 0);
  document.getElementById('btnNext').disabled = (i === PAGE_IDS.length - 1);
  // 触发页面进入回调（用于懒初始化Canvas仿真等）
  onPageEnter(i);
  // 滚动导航使当前芯片可见
  var activeChip = document.querySelector('#topNav .chip.active');
  if (activeChip && typeof activeChip.scrollIntoView === 'function') activeChip.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' }); // typeof 保护：受限环境(jsdom/沙箱 iframe)缺失时跳过，勿中断初始化
}

function nextPage() { if (curPage < PAGE_IDS.length - 1) showPage(curPage + 1); }
function prevPage() { if (curPage > 0) showPage(curPage - 1); }

// 导航芯片点击
document.querySelectorAll('#topNav .chip').forEach(function(chip) {
  chip.addEventListener('click', function() {
    var pageIdx = parseInt(this.getAttribute('data-page'));
    showPage(pageIdx);
  });
});

// 键盘导航 — 揭示优先（PPT演播模式）：
// 右/下/空格 → 优先揭示下一步；全部揭示完 → 翻到下一页
// 左/上 → 优先撤回上一步揭示；已到第0步 → 翻到上一页
// 测验/仿真/封面页（无 reveal 队列）→ 直接翻页
document.addEventListener('keydown', function(e) {
  var pid = PAGE_IDS[curPage];
  if (e.key === 'ArrowRight' || e.key === 'ArrowDown' || e.key === ' ') {
    e.preventDefault();
    // 短路检查：无 reveal 队列则直接翻页（测验/仿真/封面页）
    if (typeof pageRevealActive !== 'undefined' && pageRevealActive[pid] &&
        pageRevealQueues[pid] && pageRevealIndex[pid] < pageRevealQueues[pid].length) {
      nextReveal(pid);
    } else {
      nextPage();
    }
  } else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
    e.preventDefault();
    if (typeof pageRevealQueues !== 'undefined' && pageRevealQueues[pid] && pageRevealIndex[pid] > 0) {
      prevReveal(pid);
    } else {
      prevPage();
    }
  }
});

// 触摸滑动翻页
var touchStartX = 0, touchStartY = 0;
document.addEventListener('touchstart', function(e) {
  touchStartX = e.touches[0].clientX;
  touchStartY = e.touches[0].clientY;
}, { passive: true });
document.addEventListener('touchend', function(e) {
  var dx = e.changedTouches[0].clientX - touchStartX;
  var dy = e.changedTouches[0].clientY - touchStartY;
  if (Math.abs(dx) > Math.abs(dy) && Math.abs(dx) > 60) {
    if (dx < 0) nextPage(); else prevPage();
  }
});

// ===== 页面进入回调系统 =====
// 用于懒初始化：只在第一次进入某页时才初始化Canvas仿真、绘制概念图等
var pageEntered = {};
function onPageEnter(i) {
  var id = PAGE_IDS[i];
  if (pageEntered[id]) return;
  pageEntered[id] = true;
  // 在此处添加各页的懒初始化回调
  // 例: if (id === 'p3') initWaterSim();
  // 例: if (id === 'p8') initTerrainSim();
  // 例: if (id === 'p14') showSummaryComparison();
}

// ===== 初始显示（含 URL 参数跳转，合并执行，避免被覆盖） =====
// ⚠ 关键：URL 跳转必须与初始 showPage 合并，禁止拆成两处（否则末尾的 showPage(0) 会覆盖 URL 跳转）
// 详见 SKILL.md Common Pitfalls「扫码跳转被初始封面覆盖」
var _urlPage = getPageParam('page');
var _initIdx = (_urlPage && PAGE_IDS.indexOf(_urlPage) >= 0) ? PAGE_IDS.indexOf(_urlPage) : 0;
showPage(_initIdx);
