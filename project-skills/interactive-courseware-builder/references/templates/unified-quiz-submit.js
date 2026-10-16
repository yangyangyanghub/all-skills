// Unified Quiz Submit System — 统一测验提交逻辑
// 复制到 Step 4 课件 <script> 中（与 quiz-engine.js 的 initQuiz 配合使用）
//
// 设计说明：
//   initQuiz（来自 quiz-engine.js）负责选项绑定与选择锁定
//   submitQuiz（本文件）负责提交评分、MQTT 上报、UI 反馈
//   两套逻辑不冲突：initQuiz 只管"选"，submitQuiz 只管"交"
//
// ⚠ Step 4 要求：所有有 QR 徽章的测验页必须使用提交模式
//   initQuiz 中 isSubmitMode 必须设为 true（不再即时反馈）
//   去掉"重做"按钮，改为"提交本页成绩"按钮
// ⚠ 多选题支持：isCorrectChoice / idxInAnswer / idxInChosen 来自 quiz-engine.js；
//   多选题判定 = 学生升序索引数组与答案 100% 一致（不多选不漏选）才算正确
//   ⚠ 发布后（提交模式）：只有点击「提交本页成绩」后才显示每题答案与解析——
//   initQuiz(isSubmitMode=true) 选完不反馈，submitQuiz 统一填充 feedback
// ⚠ 答题可改规约（v2026-09-29 定案）：提交模式下学生可随时改答案（单选改选、多选重选/重确认），
//   唯一锁定点是本函数的 container._submitted——提交前自由修改、提交后立即锁死（防刷分）。
//   initQuiz 侧的选项闸门必须写 if (container._submitted) return; 禁止恢复旧的
//   _chosen[qi]>=0 / !==null 锁定写法（见 SKILL.md 标准件章「答题可改与导航条居中」）。

// ===== activity → containerId 映射 =====
// 单一事实来源：mqtt-framework.js 先定义则直接复用（保持三文件一致，禁止各自重新定义）
// 每个项目根据实际测验页数量修改此处（或 mqtt-framework.js）的映射
var ACTIVITY_QUIZ_MAP = (typeof ACTIVITY_QUIZ_MAP !== 'undefined')
  ? ACTIVITY_QUIZ_MAP
  : {pre:'quizPre', mid1:'quizMid1', mid2:'quizMid2', mid3:'quizMid3', post:'quizPost'};
// 可按需扩展更多中测: mid4, mid5, ...

// ===== 测验容器 HTML 结构要求 =====
// 每个测验容器需包含：
//   1. id="quizXxx" — 对应 ACTIVITY_QUIZ_MAP 中的 containerId
//   2. class="quiz-q" 元素，id="qq_quizXxx_N"（N=题目序号0起）
//   3. class="opt" 元素，data-idx="0/1/2/3"
//   4. class="feedback" 元素，id="fb_quizXxx_N"
//   5. 提交按钮（Step 4 必须有）：
//      <div class="quiz-actions">
//        <button id="quizXxx_submitBtn" class="btn-submit" onclick="submitQuiz('quizXxx','xxx')">提交本页成绩</button>
//      </div>
//      ⚠ Step 4 中不要加"重做"按钮（retryQuiz），只有"提交本页成绩"
//   6. 分数显示：<span id="xxxScore" class="quiz-score"></span>
//      ⚠ 分数元素ID格式：去掉"quiz"前缀 + "Score"，如 quizPre → preScore
// ⚠ Step 4 必须去掉"重做"按钮，避免与提交模式冲突

function submitQuiz(containerId, activity){
  var container = document.getElementById(containerId);
  if(container._submitted) return; // 已提交，阻止重复
  // 未答检查：单选 -1 / 多选 null（未确认）均视为未完成
  var hasUnanswered = container._chosen.some(function(c){ return Array.isArray(c) ? false : (c === null || c < 0); });
  if(hasUnanswered){ if (typeof showToast === 'function') { showToast('请先完成所有题目再提交！'); } else { alert('请先完成所有题目再提交！'); } return; } // iframe 沙箱可能禁原生 alert，优先自建 toast

  container._submitted = true;
  var qs = container._questions;
  var answers = [], score = 0;

  container._chosen.forEach(function(c, i){
    // 判定：单选 = 索引相等；多选 = 升序索引数组与答案 100% 一致（isCorrectChoice 来自 quiz-engine.js）
    var isCorrect = isCorrectChoice(qs[i], c);
    if(isCorrect) score++;
    answers.push({qi:i, chosen:c, correct:qs[i].answer, isCorrect:isCorrect});

    // 显示每题反馈
    var qq = document.getElementById('qq_'+containerId+'_'+i);
    qq.classList.add('answered');
    // ⚠ 必须同步加 submitted 类：v2026-09-29 定案「提交前可随时修改」——
    //   CSS 锁（.opt{pointer-events:none} / .opt-confirm{display:none}）挂在 .submitted 前缀下，
    //   只加 answered 不加 submitted 会导致提交后选项仍可点击（防刷分锁定失效）。
    qq.classList.add('submitted');
    qq.querySelectorAll('.opt').forEach(function(o, j){
      if(idxInAnswer(qs[i], j)) o.classList.add('correct');
      if(!isCorrect && idxInChosen(c, j) && !idxInAnswer(qs[i], j)) o.classList.add('wrong');
    });
    var fb = document.getElementById('fb_'+containerId+'_'+i);
    // ⚠ 反馈格式：✓/✗ 图标 + "回答正确。"/"回答有误。" + 解析文本
    // 正确答案旁只加 ✓，不单独写"正确"标签（详情面板中遵守此规则）
    fb.innerHTML = '<span class="fb-icon">'+(isCorrect?'✓':'✗')+'</span>'+
      (isCorrect?'回答正确。':'回答有误。')+qs[i].explain;
    fb.className = 'feedback show '+(isCorrect?'correct-fb':'wrong-fb');
  });

  // 锁定提交按钮
  var btn = document.getElementById(containerId+'_submitBtn');
  if(btn){ btn.disabled = true; btn.textContent = '已提交 ✓ (不可重复提交)'; }

  // 显示分数
  // 分数元素ID由 quiz-engine.js 的 quizScoreId() 统一生成（quizPre → preScore）
  var scoreEl = document.getElementById(quizScoreId(containerId));
  if(scoreEl){ scoreEl.style.display='block'; scoreEl.textContent = '得分：'+score+'/'+qs.length+' (已提交)'; }

  // 持久化到 localStorage
  try{ localStorage.setItem('xmn_'+activity, JSON.stringify({score:score, total:qs.length, answers:answers})); }catch(e){}

  // ⚠ 关键：先写入本地聚合数据，再 MQTT 上报，不依赖 MQTT 回环时序
  // 否则教师端可能因 broker 延迟/丢包而暂时看不到刚提交的统计
  var msg = {sid:studentId, activity:activity, ts:Date.now(), score:score, total:qs.length, answers:answers};
  if(!xmnAgg[activity]) xmnAgg[activity] = [];
  var oldIdx = xmnAgg[activity].findIndex(function(x){return x.sid===studentId;});
  if(oldIdx>=0) xmnAgg[activity][oldIdx] = msg; else xmnAgg[activity].push(msg);

  // 刷新统计（本地数据已就绪，立即生效，不依赖 MQTT 回环）
  if(typeof updateBadgeStats === 'function') updateBadgeStats(activity);

  // MQTT 上报（如已接入）
  if(typeof xmnPublish === 'function') xmnPublish(activity, {score:score, total:qs.length, answers:answers});
}
