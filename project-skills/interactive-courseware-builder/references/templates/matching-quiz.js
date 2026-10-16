// ============================================================
// Matching & Classification Quiz Engine — 连线/配对/分类题交互引擎
// 模板引擎：直接复制到课件 <script> 中，按数据调用即可，零额外 CSS。
//
// 两个入口：
//   1) initMatching(containerId, pairs[, options])
//      连线题 / 配对题：点击左侧项 → 点击右侧项 → SVG 自动连线
//      正确：绿线 + 两侧锁定；错误：红线保留 + 抖动，可重新连线
//      右侧列自动随机打乱，避免答案位置暴露
//      pairs 格式：[['左1','右1'], ['左2','右2'], ...]
//      或 [{left:'左1', right:'右1'}, ...]
//
//   2) initClassification(containerId, items, categories[, options])
//      分类题：拖拽卡片到分类桶（Pointer Events，鼠标+触屏通用）
//      放对：卡片滑入桶 + 变绿；放错：红框抖动弹回
//      同时支持备选交互：点击卡片 → 点击目标桶 也可放置
//      items 格式：      [{id:'a', label:'苹果', cat:'fruit'}, ...]
//      categories 格式： [{id:'fruit', label:'水果 🍎'}, ...]
//
// 【手机端兼容性（已按此设计，勿回退）】
//   - 连线/配对题 = 点击两端，手机浏览器 tap 即可，无兼容风险
//   - 分类题 = Pointer Events 拖拽：move/up 监听挂在 document（不依赖
//     setPointerCapture，兼容 iOS Safari 14.5 以下），卡片 touch-action:none
//     防滚动/缩放手势冲突，另附"点卡片→点桶"点击式兜底（纯点击即可完成）
//   - iOS 9+ / Android 5+ 现代浏览器均可顺畅操作
//
// 通用 options：{ onDone: function(score, total){}, retryLabel:'重试' }
// ⚠ 使用位置硬规则（见 SKILL.md §1.3.2）：
//   连线/配对/分类题 **禁止出现在前测/中测/后测**（难以量化计分、不适用于 `.opt`+`qKey` 结构化计分/统计），
//   仅用于**讲授页（teach page）讲解内容之后**作及时巩固，每页 ≤1 道；
//   巩固题内容不得与该页讲解文字完全一样（须换情境/换例子，防照抄）。
//   巩固题为练习性质，保持即时反馈，不进提交模式、不进结构化统计。
// 调用位置：在 onPageEnter('pN') 中调用（含 _initialized 守卫，重复进入不重建）
// ============================================================

(function(){
  var injected = false;
  function ensureCss(){
    if (injected) return;
    injected = true;
    var css = [
      /* ===== 连线题 ===== */
      '.match-wrap{position:relative;max-width:860px;margin:18px auto 6px;padding:4px 0}',
      '.match-cols{display:flex;gap:40px;justify-content:center;align-items:stretch;position:relative;z-index:2}',
      '.match-col{flex:1;max-width:300px;display:flex;flex-direction:column;gap:12px}',
      '.match-col h4{font-size:19px;color:var(--primary);text-align:center;margin-bottom:2px}',
      '.match-item{background:var(--paper-2);border:2px solid var(--line);border-radius:12px;',
      '  padding:12px 14px;font-size:19px;cursor:pointer;transition:all .2s;user-select:none;-webkit-user-select:none;text-align:center}',
      '.match-item:hover{border-color:var(--accent);transform:translateY(-1px)}',
      '.match-item.sel{border-color:var(--accent);background:var(--accent-soft);box-shadow:0 0 0 3px rgba(255,143,0,.18)}',
      '.match-item.correct{border-color:var(--green);background:#e0f2f1;color:#004d40;cursor:default;pointer-events:none}',
      '.match-item.wrong-flag{border-color:var(--red);background:#fbe9e7}',
      '.match-svg{position:absolute;inset:0;width:100%;height:100%;pointer-events:none;z-index:1}',
      '.match-svg line{stroke-width:3;stroke-linecap:round}',
      '@keyframes mqShake{0%,100%{transform:translateX(0)}20%{transform:translateX(-7px)}40%{transform:translateX(7px)}60%{transform:translateX(-5px)}80%{transform:translateX(5px)}}',
      '.mq-shake{animation:mqShake .45s ease}',
      /* ===== 分类题 ===== */
      '.cls-wrap{max-width:860px;margin:18px auto 6px}',
      '.cls-cards{display:flex;flex-wrap:wrap;gap:12px;justify-content:center;margin-bottom:20px;min-height:64px;padding:10px;border:2px dashed var(--line);border-radius:14px;background:rgba(0,0,0,.02)}',
      '.cls-card{background:var(--paper-2);border:2px solid var(--line);border-radius:12px;',
      '  padding:10px 18px;font-size:19px;cursor:grab;touch-action:none;user-select:none;-webkit-user-select:none;',
      '  transition:transform .2s,box-shadow .2s;position:relative}',
      '.cls-card:active{cursor:grabbing}',
      '.cls-card.dragging{position:fixed;z-index:500;box-shadow:0 8px 24px rgba(0,0,0,.22);transform:scale(1.06);cursor:grabbing;transition:none;pointer-events:none}',
      '.cls-card.pick-src{border-color:var(--accent);background:var(--accent-soft);box-shadow:0 0 0 3px rgba(255,143,0,.18)}',
      '.cls-card.correct{opacity:.35;pointer-events:none}',
      '.cls-buckets{display:flex;gap:16px;justify-content:center;flex-wrap:wrap}',
      '.cls-bucket{flex:1;min-width:150px;max-width:260px;background:var(--paper-2);border:2px solid var(--line);',
      '  border-radius:14px;padding:14px;min-height:120px;text-align:center;transition:all .25s;position:relative}',
      '.cls-bucket.hover{border-color:var(--accent);background:var(--accent-soft);transform:translateY(-3px)}',
      '.cls-bucket h5{font-size:19px;color:var(--primary);margin-bottom:8px;border-bottom:2px dashed var(--line);padding-bottom:6px}',
      '.cls-bucket .chip{display:inline-block;background:#e0f2f1;color:#004d40;border:1px solid var(--green);',
      '  border-radius:8px;padding:4px 12px;margin:4px;font-size:17px;animation:mqFadeUp .3s both}',
      '@keyframes mqFadeUp{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:translateY(0)}}',
      '.cls-bucket .bcount{position:absolute;top:8px;right:10px;font-size:15px;color:var(--primary-light);font-weight:600}',
      '.mq-done{text-align:center;font-size:22px;font-weight:700;color:var(--green);margin-top:16px;display:none}',
      '.mq-actions{text-align:center;margin-top:14px}',
      '.mq-actions button{padding:9px 26px;border-radius:24px;font-size:18px;font-weight:600;cursor:pointer;',
      '  border:2px solid var(--line);background:var(--paper);color:var(--primary);transition:all .2s}',
      '.mq-actions button:hover{border-color:var(--accent);color:var(--accent)}',
      '@media(max-width:768px){.match-cols{gap:18px}.match-item{font-size:17px;padding:10px 10px}.cls-bucket{min-width:120px}}'
    ].join('\n');
    var st = document.createElement('style');
    st.id = 'matching-quiz-css';
    st.textContent = css;
    document.head.appendChild(st);
  }
  ensureCss();

  function shuffle(arr){
    var a = arr.slice();
    for (var i = a.length - 1; i > 0; i--){
      var j = Math.floor(Math.random() * (i + 1));
      var t = a[i]; a[i] = a[j]; a[j] = t;
    }
    return a;
  }

  /* ================= 连线题 / 配对题 ================= */
  // initMatching(containerId, pairs, options)
  // 状态机：state.sel = {side:'L'|'R', idx} 当前高亮项；
  //         state.links[L] = R 当前连线；state.ok[L] = true/false 对错
  // 交互：先点一侧项高亮，再点另一侧项配对；
  //       已连线的未锁定项可重新点击（自动断开旧线）换配。
  function initMatching(containerId, pairs, options){
    options = options || {};
    var c = document.getElementById(containerId);
    if (!c) return;
    if (c._initialized) return;
    c._initialized = true;

    var list = pairs.map(function(p){
      if (Array.isArray(p)) return { left: p[0], right: p[1] };
      return { left: p.left, right: p.right };
    });
    var rightOrder = shuffle(list.map(function(_, i){ return i; }));

    c.innerHTML =
      '<div class="match-wrap">' +
        '<div class="match-cols">' +
          '<div class="match-col"><h4>' + (options.leftTitle || '左侧') + '</h4>' +
            list.map(function(p, i){
              return '<div class="match-item" data-side="L" data-i="' + i + '">' + p.left + '</div>';
            }).join('') +
          '</div>' +
          '<div class="match-col"><h4>' + (options.rightTitle || '右侧') + '</h4>' +
            rightOrder.map(function(i){
              return '<div class="match-item" data-side="R" data-i="' + i + '">' + list[i].right + '</div>';
            }).join('') +
          '</div>' +
        '</div>' +
        '<svg class="match-svg" xmlns="http://www.w3.org/2000/svg"></svg>' +
      '</div>' +
      '<div class="mq-actions"><button type="button" data-act="retry">' + (options.retryLabel || '重试') + '</button></div>' +
      '<div class="mq-done"></div>';

    var wrap = c.querySelector('.match-wrap');
    var svg = c.querySelector('.match-svg');
    var state = { sel: null, links: {}, ok: {} };
    var done = false;

    function itemEl(side, idx){
      return c.querySelector('.match-item[data-side="' + side + '"][data-i="' + idx + '"]');
    }
    // 断开左项 L 的既有连线（解除右侧占用 + 清除标记），供重新配对
    function unlink(L){
      if (state.links[L] === undefined) return;
      var R = state.links[L];
      delete state.links[L];
      delete state.ok[L];
      var lEl = itemEl('L', L), rEl = itemEl('R', R);
      if (lEl) lEl.classList.remove('wrong-flag', 'mq-shake');
      if (rEl) rEl.classList.remove('wrong-flag', 'mq-shake');
    }

    function drawLinks(){
      var svgNS = 'http://www.w3.org/2000/svg';
      while (svg.firstChild) svg.removeChild(svg.firstChild);
      var wr = wrap.getBoundingClientRect();
      svg.setAttribute('viewBox', '0 0 ' + Math.max(1, wr.width) + ' ' + Math.max(1, wr.height));
      Object.keys(state.links).forEach(function(li){
        var R = state.links[li];
        var leftEl = itemEl('L', li), rightEl = itemEl('R', R);
        if (!leftEl || !rightEl) return;
        var lr = leftEl.getBoundingClientRect(), rr = rightEl.getBoundingClientRect();
        var x1 = lr.right - wr.left, y1 = (lr.top + lr.height / 2) - wr.top;
        var x2 = rr.left - wr.left, y2 = (rr.top + rr.height / 2) - wr.top;
        var line = document.createElementNS(svgNS, 'line');
        line.setAttribute('x1', x1); line.setAttribute('y1', y1);
        line.setAttribute('x2', x2); line.setAttribute('y2', y2);
        line.setAttribute('stroke', state.ok[li] ? '#00897B' : '#D84315');
        svg.appendChild(line);
      });
    }

    function checkDone(){
      var total = list.length, correct = 0;
      for (var i = 0; i < total; i++) if (state.ok[i] === true) correct++;
      if (correct === total && total > 0 && !done){
        done = true;
        var el = c.querySelector('.mq-done');
        el.style.display = 'block';
        el.textContent = '🎉 全部配对正确！';
        if (options.onDone) options.onDone(total, total);
      }
    }

    function clearSel(){
      state.sel = null;
      c.querySelectorAll('.match-item').forEach(function(x){ x.classList.remove('sel'); });
    }

    function reset(){
      done = false;
      state = { sel: null, links: {}, ok: {} };
      c.querySelectorAll('.match-item').forEach(function(el){
        el.classList.remove('sel', 'correct', 'wrong-flag', 'mq-shake');
      });
      var el = c.querySelector('.mq-done');
      if (el){ el.style.display = 'none'; el.textContent = ''; }
      drawLinks();
    }

    c.querySelectorAll('.match-item').forEach(function(el){
      el.addEventListener('click', function(){
        if (done) return;
        var side = el.getAttribute('data-side');
        var idx = parseInt(el.getAttribute('data-i'), 10);
        // 已锁定（正确）不可动
        if (side === 'L' && state.ok[idx] === true) return;
        if (side === 'R'){
          var owner = null;
          Object.keys(state.links).forEach(function(k){ if (state.links[k] === idx) owner = k; });
          if (owner !== null && state.ok[owner] === true) return;  // 右项被正确锁定
        }
        // 点击项自身已有未锁定连线 → 先断开重选
        if (side === 'L' && state.links[idx] !== undefined && state.ok[idx] !== true) unlink(idx);

        var sel = state.sel;
        if (sel && sel.side !== side){
          // —— 配对：sel 为已选端，当前点击为另一端 ——
          var L = (side === 'L') ? idx : sel.idx;
          var R = (side === 'R') ? idx : sel.idx;
          // 若右端已被他人占用（未锁定）→ 断开他人
          var otherOwner = null;
          Object.keys(state.links).forEach(function(k){
            if (k !== L && state.links[k] === R) otherOwner = k;
          });
          if (otherOwner !== null) unlink(otherOwner);
          state.links[L] = R;
          var correct = (list[L].right === list[R].right);
          state.ok[L] = correct;
          var lEl = itemEl('L', L), rEl = itemEl('R', R);
          clearSel();
          if (correct){
            if (lEl) lEl.classList.add('correct');
            if (rEl) rEl.classList.add('correct');
          } else {
            if (lEl){ lEl.classList.add('wrong-flag'); lEl.classList.add('mq-shake'); }
            if (rEl){ rEl.classList.add('wrong-flag'); rEl.classList.add('mq-shake'); }
            setTimeout(function(){
              if (lEl) lEl.classList.remove('mq-shake');
              if (rEl) rEl.classList.remove('mq-shake');
            }, 500);
          }
          drawLinks();
          checkDone();
        } else {
          // —— 单选高亮（或换选同侧）——
          clearSel();
          state.sel = { side: side, idx: idx };
          el.classList.add('sel');
        }
      });
    });

    c.querySelector('[data-act="retry"]').addEventListener('click', reset);
    window.addEventListener('resize', function(){ drawLinks(); });
    drawLinks();
  }

  /* ================= 分类题 ================= */
  // initClassification(containerId, items, categories, options)
  function initClassification(containerId, items, categories, options){
    options = options || {};
    var c = document.getElementById(containerId);
    if (!c) return;
    if (c._initialized) return;
    c._initialized = true;

    var itemList = shuffle(items);

    c.innerHTML =
      '<div class="cls-wrap">' +
        '<div class="cls-cards" data-zone="cards">' +
          itemList.map(function(it, i){
            return '<div class="cls-card" data-zone="cards" data-id="' + it.id + '" data-cat="' + it.cat + '" data-i="' + i + '">' + it.label + '</div>';
          }).join('') +
        '</div>' +
        '<div class="cls-buckets">' +
          categories.map(function(cat){
            return '<div class="cls-bucket" data-bucket="' + cat.id + '"><span class="bcount">0/' + itemList.length + '</span><h5>' + cat.label + '</h5><div class="bchips"></div></div>';
          }).join('') +
        '</div>' +
      '</div>' +
      '<div class="mq-actions"><button type="button" data-act="retry">' + (options.retryLabel || '重试') + '</button></div>' +
      '<div class="mq-done"></div>';

    var placed = {};   // itemId -> bucketId
    var done = false;
    var pendingPick = null;

    function updateCounts(){
      c.querySelectorAll('.cls-bucket').forEach(function(bk){
        var bid = bk.getAttribute('data-bucket');
        var n = Object.keys(placed).filter(function(id){ return placed[id] === bid; }).length;
        bk.querySelector('.bcount').textContent = n + '/' + itemList.length;
      });
    }
    function checkDone(){
      var correct = 0, total = itemList.length;
      itemList.forEach(function(it){ if (placed[it.id] === it.cat) correct++; });
      if (correct === total && total > 0 && !done){
        done = true;
        var el = c.querySelector('.mq-done');
        el.style.display = 'block';
        el.textContent = '🎉 全部分类正确！';
        if (options.onDone) options.onDone(total, total);
      }
    }
    function reset(){
      done = false; placed = {}; pendingPick = null;
      c.querySelectorAll('.cls-card').forEach(function(card){
        card.classList.remove('correct', 'pick-src', 'mq-shake', 'dragging');
        card.style.cssText = '';
        c.querySelector('[data-zone="cards"]').appendChild(card);
      });
      c.querySelectorAll('.bchips').forEach(function(bc){ bc.innerHTML = ''; });
      updateCounts();
      var el = c.querySelector('.mq-done');
      if (el){ el.style.display = 'none'; el.textContent = ''; }
    }

    function hitBucket(x, y){
      var hit = null;
      c.querySelectorAll('.cls-bucket').forEach(function(bk){
        var r = bk.getBoundingClientRect();
        if (x >= r.left && x <= r.right && y >= r.top && y <= r.bottom) hit = bk;
      });
      return hit;
    }

    function tryPlace(card, bucket){
      var id = card.getAttribute('data-id');
      var it = null;
      itemList.forEach(function(x){ if (x.id === id) it = x; });
      if (!it || placed[id]) return;
      var bid = bucket.getAttribute('data-bucket');
      if (bid === it.cat){
        placed[id] = bid;
        card.classList.add('correct');
        var chip = document.createElement('span');
        chip.className = 'chip';
        chip.textContent = it.label;
        bucket.querySelector('.bchips').appendChild(chip);
        updateCounts();
        checkDone();
      } else {
        card.classList.add('mq-shake');
        setTimeout(function(){ card.classList.remove('mq-shake'); }, 500);
      }
    }

    // —— 拖拽（Pointer Events，鼠标+触屏统一）——
    // 移动端关键设计：pointermove/pointerup 挂在 document 上（而非卡片上），
    // 不依赖 setPointerCapture（iOS Safari 14.5 以下不支持）——手指拖出卡片边界
    // 后 move 事件仍持续派发，拖拽不中断；touch-action:none 阻止页面滚动/缩放手势。
    var drag = null;
    function onDocMove(e){
      if (!drag) return;
      var card = drag.el;
      if (Math.abs(e.clientX - drag.startX) + Math.abs(e.clientY - drag.startY) > 4) drag.moved = true;
      if (!drag.moved) return;
      card.classList.add('dragging');
      card.style.left = (e.clientX - drag.dx) + 'px';
      card.style.top  = (e.clientY - drag.dy) + 'px';
      c.querySelectorAll('.cls-bucket').forEach(function(bk){
        var r = bk.getBoundingClientRect();
        var hit = e.clientX >= r.left && e.clientX <= r.right && e.clientY >= r.top && e.clientY <= r.bottom;
        bk.classList.toggle('hover', hit);
      });
    }
    function onDocUp(e){
      if (!drag) return;
      var card = drag.el;
      var wasMove = drag.moved;
      var target = null;
      c.querySelectorAll('.cls-bucket').forEach(function(bk){ bk.classList.remove('hover'); });
      if (wasMove){
        target = hitBucket(e.clientX, e.clientY);
        if (target) tryPlace(card, target);
      }
      card.classList.remove('dragging');
      card.style.cssText = '';
      // pointercancel = 系统手势打断（如下拉刷新），不算点击，不进 pick-src
      if (e.type !== 'pointercancel' && !wasMove && !target){
        // 未拖移 → 进入"点击式"待放置（备选交互，触屏友好）
        c.querySelectorAll('.cls-card').forEach(function(x){ x.classList.remove('pick-src'); });
        card.classList.add('pick-src');
        pendingPick = card;
      }
      drag = null;
    }
    document.addEventListener('pointermove', onDocMove);
    document.addEventListener('pointerup', onDocUp);
    document.addEventListener('pointercancel', onDocUp);   // iOS 手势打断时同样收尾

    c.querySelectorAll('.cls-card').forEach(function(card){
      card.addEventListener('pointerdown', function(e){
        if (done || placed[card.getAttribute('data-id')]) return;
        e.preventDefault();
        var rect = card.getBoundingClientRect();
        drag = {
          el: card, dx: e.clientX - rect.left, dy: e.clientY - rect.top,
          startX: e.clientX, startY: e.clientY, moved: false
        };
      });
    });

    // —— 点击式备选：点卡片(pick-src)后再点桶 ——
    c.querySelectorAll('.cls-bucket').forEach(function(bk){
      bk.addEventListener('click', function(){
        if (!pendingPick) return;
        tryPlace(pendingPick, bk);
        pendingPick.classList.remove('pick-src');
        pendingPick = null;
      });
    });

    c.querySelector('[data-act="retry"]').addEventListener('click', reset);
    updateCounts();
  }

  // 全局暴露（供课件 <script> 直接调用）
  window.initMatching = initMatching;
  window.initClassification = initClassification;
})();
