// Detail Stats Panel — 每题选项分布条形图（含选项文本内容，便于教师对照）
// 复制到 Step 4 课件 <script> 中，仅需修改 DETAIL_QUIZ_MAP 映射
//
// 依赖：QUIZZES（测验数据）、xmnAgg（MQTT聚合数据）、detailOverlay（HTML面板）
//
// 注意：submitQuiz 中必须先把数据写入本地 xmnAgg（不依赖 MQTT 回环时序），
//       否则教师端可能看不到刚提交的统计。参见 mqtt-framework.js 中的注释。
//
// v2026-10-13 增强：
//   ① 每个选项行展示「选项文本内容」（从 DOM 读取，不依赖 QUIZZES 数据模型，向后兼容已发布课件）；
//   ② 修复多选题统计——chosen 为数组，原 `chosen>=0` 判断恒 false 导致多选统计全 0；
//   ③ 修复多选题正确项标记——原 `oi===q.answer` 对数组恒 false，正确项不显示 ✓/绿色；
//   ④ 题干去除「单选题/多选题」徽章噪声，并去除重复的前导题号。

// ===== 活动→测验名称映射（复用 mqtt-framework.js 的 ACTIVITY_QUIZ_MAP，单一事实来源） =====
// 键值结构与 ACTIVITY_QUIZ_MAP 完全一致（pre→quizPre…），存在时直接复用，不重复定义
var DETAIL_QUIZ_MAP = (typeof ACTIVITY_QUIZ_MAP !== 'undefined')
  ? ACTIVITY_QUIZ_MAP
  : { pre:'quizPre', mid1:'quizMid1', mid2:'quizMid2', mid3:'quizMid3', post:'quizPost' };

// 活动中文标签（复用 ACTIVITY_LABELS；仅当独立引入本文件时使用兜底表）
var DETAIL_LABELS = (typeof ACTIVITY_LABELS !== 'undefined')
  ? ACTIVITY_LABELS
  : { pre:'前测', mid1:'中测1', mid2:'中测2', mid3:'中测3', post:'后测' };

var OPT_LABELS = ['A', 'B', 'C', 'D'];

// 判断某个选项索引是否为正确答案（兼容单选 number / 多选 array）
function _dsIsCorrectIdx(q, idx) {
  if (!q) return false;
  if (Array.isArray(q.answer)) return q.answer.indexOf(idx) >= 0;
  return q.answer === idx;
}

// 从 DOM 读取某题某选项的选项文本内容（剥掉 .badge 字母，仅保留选项文字）
function _dsGetOptText(qEl, idx) {
  if (!qEl) return '';
  var opt = qEl.querySelector('.opt[data-idx="' + idx + '"]');
  if (!opt) return '';
  var clone = opt.cloneNode(true);
  var b = clone.querySelector('.badge');
  if (b) b.parentNode.removeChild(b);
  return (clone.textContent || '').replace(/\s+/g, ' ').trim();
}

function openDetail(activity) {
  var quizId = DETAIL_QUIZ_MAP[activity];
  if (!quizId) return;
  var questions = QUIZZES[quizId] ? QUIZZES[quizId].questions : [];
  var submissions = xmnAgg[activity] || [];
  var totalSubs = submissions.length;

  var html = '<h3 style="font-size:26px;color:var(--primary);margin-bottom:12px">'
    + (DETAIL_LABELS[activity] || activity) + ' — 每题统计</h3>';

  for (var qi = 0; qi < questions.length; qi++) {
    var q = questions[qi];
    var qEl = document.getElementById('qq_' + quizId + '_' + qi);
    var stemText = qEl ? qEl.querySelector('.q-stem').textContent : ('第' + (qi + 1) + '题');
    // 题干清理：剥掉 .q-type 徽章文字，并去掉重复的前导题号（如 "1. "）
    if (qEl) {
      var stClone = qEl.querySelector('.q-stem').cloneNode(true);
      var stBadge = stClone.querySelector('.q-type');
      if (stBadge) stBadge.parentNode.removeChild(stBadge);
      stemText = (stClone.textContent || '').replace(/\s+/g, ' ').trim();
      stemText = stemText.replace(/^\s*\d+[\.、]\s*/, '');
    }
    var optCounts = [0, 0, 0, 0];

    submissions.forEach(function(sub) {
      var a = sub.answers && sub.answers[qi];
      if (!a) return;
      var ch = a.chosen;
      if (Array.isArray(ch)) {
        ch.forEach(function(ix) { if (ix >= 0 && ix < 4) optCounts[ix]++; });
      } else if (ch >= 0 && ch < 4) {
        optCounts[ch]++;
      }
    });

    var maxCount = Math.max.apply(null, optCounts.concat([1]));

    html += '<div class="detail-q-block">';
    html += '<div class="detail-q-title">' + (qi + 1) + '. ' + stemText + '</div>';
    html += '<div class="detail-q-bar">';
    for (var oi = 0; oi < 4; oi++) {
      var isCorrectOpt = _dsIsCorrectIdx(q, oi);
      var barW = totalSubs > 0 ? Math.round(optCounts[oi] / maxCount * 100) : 0;
      var barClass = isCorrectOpt ? 'green'
        : (optCounts[oi] > 0 ? 'orange' : 'gray');
      var tagColor = isCorrectOpt ? 'var(--green)' : 'var(--primary)';
      var optText = _dsGetOptText(qEl, oi);
      html += '<div class="bar-row">';
      // 主视觉：选项标签 + 条形图 + 百分比（选项统计为视觉重点）
      html += '<div class="opt-barline">';
      html += '<span class="opt-tag" style="color:' + tagColor + '">'
        + OPT_LABELS[oi] + (isCorrectOpt ? ' ✓' : '') + '</span>';
      html += '<div class="bar-bg"><div class="bar-fill ' + barClass
        + '" style="width:' + barW + '%">'
        + (optCounts[oi] > 0 ? optCounts[oi] + '人' : '') + '</div></div>';
      html += '<span class="opt-pct">'
        + (totalSubs > 0 ? Math.round(optCounts[oi] / totalSubs * 100) : 0) + '%</span>';
      html += '</div>';
      // 选项文本内容：默认隐藏，悬停整行时以浮窗显示（非重点、省高度）；浮窗文本最前加选项字母(A/B/C/D)便于识别
      html += '<span class="opt-tip"><b>' + OPT_LABELS[oi] + '</b> ' + (optText || '（无选项文本）') + '</span>';
      html += '</div>';
    }
    html += '</div>';
    html += '</div>';
  }

  if (questions.length === 0) {
    html += '<p style="text-align:center;font-size:20px;color:var(--primary-light);padding:40px">该测验无题目数据</p>';
  } else if (totalSubs === 0) {
    html += '<p style="text-align:center;font-size:20px;color:var(--primary-light);padding:40px">暂无提交数据</p>';
  }

  document.getElementById('detailContent').innerHTML = html;
  document.getElementById('detailOverlay').classList.add('show');
}

function closeDetail() {
  document.getElementById('detailOverlay').classList.remove('show');
}

// ===== 需配合的 HTML + CSS =====
// 1) 复制 detail-modal.html 中的 CSS + HTML 到课件中
// 2) 每个 QR 弹窗需加按钮:
//    <a class="qr-detail-link" onclick="openDetail('post');closeQRPopup('post')">查看每题详情 →</a>
// 3) 确保 CSS 中的关闭按钮类名为 .detail-close-btn（与 detail-modal.html 一致）
