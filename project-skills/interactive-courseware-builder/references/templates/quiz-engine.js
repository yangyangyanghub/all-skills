// Quiz Engine — 测验系统核心框架（支持单选题 + 多选题）
// 直接复制到课件 <script> 中，只修改 QUIZZES 对象中的题目数据
//
// ================= 题型硬规则 =================
// 1. 前测/中测/后测 **一律只用选择题**（单选或多选）——连线/配对/分类题难以量化计分、
//    不适用于 `.opt`+`qKey` 结构化计分/统计，**禁止出现在任何测验环节**；它们只用于讲授页末尾作及时巩固（见 SKILL.md §1.3.2）
// 2. 单选题数据：{ answer: 0, explain: '...' }                 ← answer 为正确选项索引
//    多选题数据：{ multi: true, answer: [0,2], explain: '...' }  ← answer 为正确索引数组
//    ⚠ 多选题判定：学生选择必须 **100% 与答案一致**（不多选、不漏选）才算正确
// 3. 题干必须标注选择类型（写在 .q-stem 内第一个元素）：
//      单选：<p class="q-stem"><span class="q-type">单选题</span>1. 题干...</p>
//      多选：<p class="q-stem"><span class="q-type multi">多选题</span>2. 题干...</p>
//    （下方 IIFE 自动注入 .q-type 徽章与 .opt-confirm 按钮样式，零额外 CSS）
// 4. 多选题交互：点击选项 = 切换选定/取消；点击「确认本题」记录当前选择。
//    ⚠ 锁定时序（v2026-09-29 定案）：提交模式下「提交前可随时修改」——
//    单选改选、多选重选/重新确认均允许，唯一锁定点是 submitQuiz 提交（container._submitted）。
//    即时模式（Step 3）仍是选完即锁并出解析（showFeedback 内 pointerEvents='none'）。

// ===== 测验数据结构 =====
var QUIZZES = {
  quizPre: {
    questions: [
      { answer: 0, explain: '解析文本...' },
      { multi: true, answer: [0, 2], explain: '解析文本...' }
    ]
  }
};

// ===== 引擎自注入样式（.q-type 徽章 + .opt-confirm 多选确认按钮） =====
(function(){
  if (document.getElementById('quiz-engine-css')) return;
  var st = document.createElement('style');
  st.id = 'quiz-engine-css';
  st.textContent = [
    '.q-type{display:inline-block;font-size:14px;font-weight:700;padding:1px 10px;border-radius:12px;margin-right:8px;vertical-align:2px;background:var(--primary-light);color:#fff;letter-spacing:1px}',
    '.q-type.multi{background:var(--accent)}',
    '.opt-confirm{margin-top:10px;padding:7px 22px;border-radius:18px;font-size:16px;font-weight:600;cursor:pointer;border:2px solid var(--accent);background:var(--paper);color:var(--accent);transition:all .2s}',
    '.opt-confirm:hover{background:var(--accent);color:#fff}',
    '.quiz-q.submitted .opt-confirm{display:none}'
    // ⚠ 必须用 submitted 前缀而非 answered：answered 在多选确认后就会加上，
    //   若用 answered 隐藏确认按钮，学生确认后想重选就点不到「确认本题」→ 无法重新确认。
    //   submitted 只在 submitQuiz 提交后由 unified-quiz-submit.js 加上。
  ].join('\n');
  document.head.appendChild(st);
})();

// ===== 多选判定辅助 =====
function isMultiQ(q){ return !!(q && q.multi && Array.isArray(q.answer)); }
function sameIdxArr(a, b){   // 两个升序索引数组完全一致
  if (!Array.isArray(a) || !Array.isArray(b) || a.length !== b.length) return false;
  for (var i = 0; i < a.length; i++) if (a[i] !== b[i]) return false;
  return true;
}
function ascArr(a){ return a.slice().sort(function(x, y){ return x - y; }); }
// 统一判定入口：chosen 为索引（单选）或升序索引数组（多选）
function isCorrectChoice(q, chosen){
  if (isMultiQ(q)) return sameIdxArr(chosen, ascArr(q.answer));
  return chosen === q.answer;
}
// 选项 j 是否在答案中
function idxInAnswer(q, j){
  return Array.isArray(q.answer) ? q.answer.indexOf(j) >= 0 : j === q.answer;
}
// 选项 j 是否被学生选中（c 为索引或数组）
function idxInChosen(c, j){
  return Array.isArray(c) ? c.indexOf(j) >= 0 : c === j;
}
// ⚠ 分数元素ID — 统一规则：quizId 去掉 "quiz" 前缀、首字母小写 + "Score"
//   （quizPre → preScore；quizMid1 → mid1Score；quizPost → postScore）
//   与 unified-quiz-submit.js 的 submitQuiz 共用此函数，禁止各文件硬编码映射表
function quizScoreId(containerId){
  var s = String(containerId).replace(/^quiz/, '');
  return s.charAt(0).toLowerCase() + s.slice(1) + 'Score';
}

// ===== 测验引擎核心 =====
// ⚠ initQuiz 只负责"选"（选项绑定 + 选择锁定），不负责"交"
//   Step 3: isSubmitMode=false → 选完即反馈（即时模式）
//   Step 4: isSubmitMode=true → 选完只标记，等"提交本页成绩"按钮才评分（提交模式）
//   提交+评分逻辑由 unified-quiz-submit.js 的 submitQuiz() 处理，与本函数不冲突
//   ⚠ Step 4 中所有有 QR 徽章的测验页 isSubmitMode 必须设为 true
function initQuiz(quizId) {
  var container = document.getElementById(quizId);
  if (!container) return;
  if (container._initialized) return;
  container._initialized = true;
  container._questions = QUIZZES[quizId].questions;
  // _chosen: 单选存索引（-1=未答）；多选存升序索引数组（null=未确认）
  container._chosen = container._questions.map(function(q){ return isMultiQ(q) ? null : -1; });
  // _picked: 多选题的暂选池（可增删），单选为 null
  container._picked = container._questions.map(function(q){ return isMultiQ(q) ? [] : null; });

  // ⚠ Step 3: 即时反馈模式 (false)
  // ⚠ Step 4: 提交模式 (true) — 有 QR 徽章的学生互动页必须改为 true
  //    改为 true 后：选完/确认后不即时反馈，等 submitQuiz() 统一处理
  var isSubmitMode = false;

  container.querySelectorAll('.quiz-q').forEach(function(qq, qi) {
    var q = container._questions[qi];
    var opts = qq.querySelectorAll('.opt');
    if (isMultiQ(q)) {
      // —— 多选题：提交前可反复勾选/重新确认；提交后锁定 ——
      opts.forEach(function(opt) {
        opt.addEventListener('click', function() {
          if (container._submitted) return;  // 已提交，锁定（提交前可随时修改）
          var idx = parseInt(this.getAttribute('data-idx'));
          var pos = container._picked[qi].indexOf(idx);
          if (pos >= 0) { container._picked[qi].splice(pos, 1); this.classList.remove('selected'); }
          else { container._picked[qi].push(idx); this.classList.add('selected'); }
        });
      });
      var btn = qq.querySelector('.opt-confirm');
      if (btn) btn.addEventListener('click', function() {
        if (container._submitted) return;  // 已提交，锁定
        if (container._picked[qi].length === 0) return;  // 至少选一项才能确认
        container._chosen[qi] = ascArr(container._picked[qi]);
        qq.classList.add('answered');
        if (!isSubmitMode) { showFeedback(quizId, qi); updateQuizScore(quizId); }
      });
    } else {
      // —— 单选题：点击即选中（提交前可随时改选），提交后锁定 ——
      opts.forEach(function(opt) {
        opt.addEventListener('click', function() {
          if (container._submitted) return; // 已提交，锁定（提交前可随时改选）
          var idx = parseInt(this.getAttribute('data-idx'));
          container._chosen[qi] = idx;
          opts.forEach(function(o) { o.classList.remove('selected'); });
          this.classList.add('selected');
          qq.classList.add('answered');
          if (!isSubmitMode) { showFeedback(quizId, qi); updateQuizScore(quizId); }
        });
      });
    }
  });
}

function showFeedback(quizId, qi) {
  var container = document.getElementById(quizId);
  var q = container._questions[qi];
  var c = container._chosen[qi];
  var qq = document.getElementById('qq_' + quizId + '_' + qi);
  var fb = document.getElementById('fb_' + quizId + '_' + qi);
  if (!qq || !fb) return;
  var isCorrect = isCorrectChoice(q, c);
  fb.innerHTML = '<span class="fb-icon">' + (isCorrect ? '✓' : '✗') + '</span>' +
    (isCorrect ? '回答正确！' : '回答有误。') + q.explain;
  fb.className = 'feedback show ' + (isCorrect ? 'correct-fb' : 'wrong-fb');
  var opts = qq.querySelectorAll('.opt');
  opts.forEach(function(o, j) {
    if (idxInAnswer(q, j)) o.classList.add('correct');
    if (!isCorrect && idxInChosen(c, j) && !idxInAnswer(q, j)) o.classList.add('wrong');
  });
  // 即时模式：选项锁定
  qq.querySelectorAll('.opt').forEach(function(o) { o.style.pointerEvents = 'none'; });
}

function updateQuizScore(quizId) {
  var container = document.getElementById(quizId);
  var total = container._questions.length;
  var done = 0, score = 0;
  container._questions.forEach(function(q, i) {
    var c = container._chosen[i];
    var answered = isMultiQ(q) ? (Array.isArray(c) && c.length > 0) : c >= 0;
    if (answered) {
      done++;
      if (isCorrectChoice(q, c)) score++;
    }
  });
  // 分数元素ID由 quizScoreId() 统一生成（无需项目硬编码映射表，自动适配任意测验页数）
  var scoreEl = document.getElementById(quizScoreId(quizId));
  if (scoreEl) {
    scoreEl.style.display = 'block';
    if (done === total) {
      scoreEl.innerHTML = '得分：' + score + '/' + total + ' &nbsp;&nbsp;' +
        (score === total ? '🌟 全部正确！' : score >= total * 0.6 ? '👍 不错，继续加油！' : '💪 需要加强复习哦');
    } else {
      scoreEl.textContent = '已答：' + done + '/' + total + ' 正确：' + score;
    }
  }
  // localStorage 持久化
  try { localStorage.setItem('xmn_' + quizId, JSON.stringify({ score: score, total: total, done: done })); } catch (e) {}
}

// ⚠ retryQuiz 仅用于 Step 3 即时模式！
// Step 4 提交模式中必须去掉"重做"按钮，改为"提交本页成绩"按钮（用 submitQuiz）
// 搜索 HTML 中的 "retryQuiz" 或 "重做" 确保无残留
function retryQuiz(quizId) {
  var container = document.getElementById(quizId);
  if (!container) return;
  container._chosen = container._questions.map(function(q){ return isMultiQ(q) ? null : -1; });
  container._picked = container._questions.map(function(q){ return isMultiQ(q) ? [] : null; });
  var allQQ = container.querySelectorAll('.quiz-q');
  allQQ.forEach(function(qq) {
    qq.classList.remove('answered');
    qq.querySelectorAll('.opt').forEach(function(o) {
      o.classList.remove('selected', 'correct', 'wrong');
      o.style.pointerEvents = 'auto';
    });
  });
  container.querySelectorAll('.feedback').forEach(function(fb) {
    fb.className = 'feedback'; fb.innerHTML = '';
  });
  // 分数元素ID由 quizScoreId() 统一生成（与 updateQuizScore / submitQuiz 完全一致）
  var el = document.getElementById(quizScoreId(quizId));
  if (el) el.style.display = 'none';
}

// ===== 初始化所有测验 =====
Object.keys(QUIZZES).forEach(function(k) { initQuiz(k); });

// ===== HTML模板（每道题） =====
/*
  —— 单选题 ——
  <div class="quiz-q" id="qq_quizId_N">
    <p class="q-stem"><span class="q-type">单选题</span>N. 题目文本</p>
    <div class="opts">
      <div class="opt" data-idx="0"><span class="badge">A</span>选项A文本</div>
      <div class="opt" data-idx="1"><span class="badge">B</span>选项B文本</div>
      <div class="opt" data-idx="2"><span class="badge">C</span>选项C文本</div>
      <div class="opt" data-idx="3"><span class="badge">D</span>选项D文本</div>
    </div>
    <div class="feedback" id="fb_quizId_N"></div>
  </div>

  —— 多选题（多一个确认按钮） ——
  <div class="quiz-q" id="qq_quizId_M">
    <p class="q-stem"><span class="q-type multi">多选题</span>M. 题目文本</p>
    <div class="opts">…同上…</div>
    <button type="button" class="opt-confirm">确认本题</button>
    <div class="feedback" id="fb_quizId_M"></div>
  </div>

  关键规则：
  - quiz-q的id格式: qq_{quizId}_{questionIndex}
  - feedback的id格式: fb_{quizId}_{questionIndex}
  - 每个opt必须有data-idx属性，值为选项序号(0=A, 1=B, 2=C, 3=D)
  - QUIZZES中answer对应data-idx；多选answer为索引数组
  - 多选题必须包含 .opt-confirm 按钮（否则无法锁定作答）
  - 题干必须含 .q-type 徽章标明「单选题/多选题」
*/
