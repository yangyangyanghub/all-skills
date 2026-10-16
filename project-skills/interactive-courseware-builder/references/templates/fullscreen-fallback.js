/**
 * fullscreen-fallback.js — 三级降级「真全屏」按需模板（opt-in）
 * =====================================================================
 * ⚠ 默认【不注入】。仅当课件确需保留「全屏按钮」时整体复制本文件，
 *   并在课件补：① HTML 按钮（id="fullscreenBtn"，内含 #fsIcon）② 伪全屏 CSS 三条
 *   （见 SKILL.md「资料库发布 & 教学控制标准件」§3）。
 * 源出：teaching-control.js 抽离（2026-09-29 审计——原文是活代码，与 §3
 *   「默认不放全屏按钮」定案冲突；抽离后二者一致）。
 * 依赖：showToast（mqtt-framework.js 已内置）；无其他本技能私有依赖。
 * ===================================================================== */

/* =====================================================================
 * 三级降级全屏（v2026-09-28e 定案：默认不启用——新课件不放 #fullscreenBtn 按钮，
 *   需要全屏时引导用户按键盘 F11。本段代码仅供"确需全屏按钮"的特殊场景按需复制）
 * 外壳 iframe sandbox 无 allow-fullscreen → requestFullscreen 被静默拒绝，必须逐级降级：
 *   ① 本文档 requestFullscreen（直开 HTML = 真全屏；rejection 自动降级，不得吞错）
 *   ② 同源 iframe 借外壳顶层文档全屏（跨源时 try 读 parent 会抛错 → 自动落 ③）
 *   ③ 伪全屏 body.fs-pseudo（配 CSS，见文件头注释）
 * 注意：isFs 判定与 _exitFullscreen 必须同时覆盖 本文档/父文档/fs-pseudo 三态。
 * ===================================================================== */
var fsBtn = document.getElementById('fullscreenBtn');
var fsPaths = {
  enter: '<path d="M8 3H5a2 2 0 0 0-2 2v3"/><path d="M16 3h3a2 2 0 0 1 2 2v3"/><path d="M8 21H5a2 2 0 0 1-2-2v-3"/><path d="M16 21h3a2 2 0 0 0 2-2v-3"/>',
  exit:  '<path d="M3 8V5a2 2 0 0 1 2-2h3"/><path d="M21 8V5a2 2 0 0 0-2-2h-3"/><path d="M3 16v3a2 2 0 0 0 2 2h3"/><path d="M21 16v3a2 2 0 0 1-2 2h-3"/>'
};
function setFsIcon(mode){
  var ic = document.getElementById('fsIcon');
  if (ic) ic.innerHTML = fsPaths[mode];
  if (fsBtn){ fsBtn.classList.toggle('fs-active', mode === 'exit'); fsBtn.title = (mode === 'exit') ? '退出全屏' : '全屏播放'; }
}
function toggleFullscreen(){
  var isFs = document.fullscreenElement || document.webkitFullscreenElement || document.msFullscreenElement
             || document.body.classList.contains('fs-pseudo')
             || (function(){ try{ return !!window.parent.document.fullscreenElement; }catch(e){ return false; } })();
  if (isFs){ _exitFullscreen(); return; }
  if (_requestOn(document.documentElement)) return;      // ①
  if (_tryParentFullscreen()) return;                    // ②
  _pseudoFullscreen();                                   // ③
}
function _requestOn(el){
  var req = el.requestFullscreen || el.webkitRequestFullscreen || el.msRequestFullscreen;
  if (!req) return false;
  try {
    var p = req.call(el);
    if (p && p.catch) p.catch(function(){ if (el === document.documentElement){ if(!_tryParentFullscreen()) _pseudoFullscreen(); } else { _pseudoFullscreen(); } });
    return true;   // 老 webkit 无 Promise：成功与否由 fullscreenchange 事件纠偏
  } catch(e){ return false; }
}
function _tryParentFullscreen(){
  try {
    var pd = window.parent.document;
    if (pd.fullscreenElement || pd.webkitFullscreenElement) return true;
    if (_requestOn(pd.documentElement)){
      try {
        pd.addEventListener('fullscreenchange', function(){ setFsIcon(pd.fullscreenElement ? 'exit' : 'enter'); });
        pd.addEventListener('webkitfullscreenchange', function(){ setFsIcon(pd.webkitFullscreenElement ? 'exit' : 'enter'); });
      } catch(e){}
      return true;
    }
  } catch(e){}   // 跨源 iframe：读不到外壳文档
  return false;
}
function _exitFullscreen(){
  var doc = document;
  if (doc.fullscreenElement || doc.webkitFullscreenElement || doc.msFullscreenElement){
    (doc.exitFullscreen || doc.webkitExitFullscreen || doc.msExitFullscreen || function(){}).call(doc);
  }
  try { var pd = window.parent.document; if (pd.fullscreenElement || pd.webkitFullscreenElement){ (pd.exitFullscreen || pd.webkitExitFullscreen || function(){}).call(pd); } } catch(e){}
  doc.body.classList.remove('fs-pseudo');
  setFsIcon('enter');
}
function _pseudoFullscreen(){
  document.body.classList.add('fs-pseudo');
  setFsIcon('exit');
  showToast('已铺满页面区域；如需连浏览器界面一起隐藏，请按键盘 F11', 3200);
}
document.addEventListener('fullscreenchange', function(){ setFsIcon(document.fullscreenElement ? 'exit' : 'enter'); });
document.addEventListener('webkitfullscreenchange', function(){ setFsIcon(document.webkitFullscreenElement ? 'exit' : 'enter'); });
if (fsBtn) fsBtn.addEventListener('click', toggleFullscreen);
