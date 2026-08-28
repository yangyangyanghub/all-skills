// runtime.js - HTML Presentation Keyboard Navigation & Speaker Mode
// Pure vanilla JS, no external dependencies, no ES modules
// Compatible with Chromium-based browsers

(function () {
  'use strict';

  // ─── STATE ───────────────────────────────────────────────
  var currentSlide = 0;
  var totalSlides = 0;
  var slides = [];
  var themes = [];
  var currentTheme = 0;
  var isPreview = false;
  var previewSlide = 0;
  var speakerWindow = null;
  var animationLoop = false;
  var animationTimer = null;
  var timerRunning = true;
  var timerStart = Date.now();
  var perSlideTimers = {};
  var currentElapsed = 0;
  var timerInterval = null;
  var overviewOpen = false;
  var notesOpen = false;
  var bc; // BroadcastChannel

  // ─── INIT ────────────────────────────────────────────────
  function init() {
    // Parse URL
    var hash = window.location.hash;
    var previewMatch = window.location.search.match(/[?&]preview=(\d+)/);
    var themeMatch = /[?&]theme=([^&]+)/.exec(window.location.search);

    if (previewMatch) {
      isPreview = true;
      previewSlide = parseInt(previewMatch[1], 10) - 1;
    } else if (hash && /^#\d+$/.test(hash)) {
      currentSlide = parseInt(hash.replace('#', ''), 10) - 1;
    }

    // Apply URL theme parameter
    if (themeMatch) {
      var urlTheme = decodeURIComponent(themeMatch[1]);
      // Will be applied after themes are collected
    }

    // Collect slides
    slides = Array.prototype.slice.call(document.querySelectorAll('.slide'));
    totalSlides = slides.length;

    // Collect themes from data-themes attribute on <body> or root
    var themesAttr = document.body.getAttribute('data-themes');
    if (themesAttr) {
      themes = themesAttr.split(',').map(function (t) { return t.trim(); });
      // URL theme parameter takes precedence
      if (themeMatch) {
        var urlTheme = decodeURIComponent(themeMatch[1]);
        var urlThemeIdx = themes.indexOf(urlTheme);
        if (urlThemeIdx !== -1) {
          currentTheme = urlThemeIdx;
        }
      }
      // Check for saved theme (lower priority than URL)
      if (!themeMatch) {
        var savedTheme = localStorage.getItem('ppt-theme');
        if (savedTheme) {
          var idx = themes.indexOf(savedTheme);
          if (idx !== -1) currentTheme = idx;
        }
      }
    }

    // Load saved slide
    var savedSlide = parseInt(localStorage.getItem('ppt-slide'), 10);
    if (!isNaN(savedSlide) && !hash && !previewMatch) {
      currentSlide = savedSlide;
    }

    // Clamp
    if (currentSlide < 0) currentSlide = 0;
    if (currentSlide >= totalSlides) currentSlide = totalSlides - 1;
    if (previewSlide < 0) previewSlide = 0;
    if (previewSlide >= totalSlides) previewSlide = totalSlides - 1;

    // BroadcastChannel
    try {
      bc = new BroadcastChannel('ppt-deck-sync');
      bc.onmessage = onBroadcastMessage;
    } catch (e) {
      // Fallback for older browsers
    }

    applySlide();
    applyTheme();
    initTimer();
    bindEvents();
  }

  // ─── SLIDE NAVIGATION ────────────────────────────────────
  function goToSlide(index, skipBroadcast) {
    if (index < 0 || index >= totalSlides) return;
    currentSlide = index;
    applySlide();
    if (!skipBroadcast && bc) {
      bc.postMessage({ type: 'goto', slide: currentSlide });
    }
    // Update hash
    if (!isPreview) {
      window.location.hash = (currentSlide + 1);
    }
    saveState();
    notifySpeakerIframe();
  }

  function applySlide() {
    for (var i = 0; i < slides.length; i++) {
      // Remove all state classes
      slides[i].classList.remove('is-active');
      // Hide all
      slides[i].style.display = 'none';
    }
    // Show current
    if (slides[currentSlide]) {
      slides[currentSlide].style.display = '';
      slides[currentSlide].classList.add('is-active');
    }
    // Preview mode: hide all non-preview slides
    if (isPreview) {
      for (var j = 0; j < slides.length; j++) {
        if (j !== previewSlide) {
          slides[j].style.display = 'none';
        }
      }
    }
    // Notify parent frame if inside iframe
    notifyParent();
    // Update progress
    updateProgress();
    // Update timer
    onSlideChange();
  }

  function nextSlide() { if (currentSlide < totalSlides - 1) goToSlide(currentSlide + 1); }
  function prevSlide() { if (currentSlide > 0) goToSlide(currentSlide - 1); }
  function firstSlide() { goToSlide(0); }
  function lastSlide() { goToSlide(totalSlides - 1); }

  // ─── PROGRESS BAR ────────────────────────────────────────
  function updateProgress() {
    var bar = document.getElementById('ppt-progress-bar');
    if (!bar) {
      bar = document.createElement('div');
      bar.id = 'ppt-progress-bar';
      bar.style.cssText = 'position:fixed;bottom:0;left:0;height:4px;background:var(--ppt-primary,#3b82f6);z-index:10000;transition:width 0.2s;';
      document.body.appendChild(bar);
    }
    var pct = totalSlides > 1 ? ((currentSlide + 1) / totalSlides * 100) : 100;
    bar.style.width = pct + '%';
  }

  // ─── KEYBOARD NAVIGATION ─────────────────────────────────
  function isSpeakerWindow() {
    // Detect if we're running inside a speaker window (has draggable cards)
    return document.querySelectorAll('.card').length > 0;
  }

  function bindEvents() {
    document.addEventListener('keydown', onKeyDown, true);
    document.addEventListener('message', onIframeMessage, false);
  }

  function onKeyDown(e) {
    // Ignore if typing in input/textarea
    var tag = e.target.tagName;
    if (tag === 'INPUT' || tag === 'TEXTAREA' || e.target.isContentEditable) return;

    // Speaker window: only handle R (reset timer) and Esc
    if (isSpeakerWindow()) {
      if (e.key === 'r' || e.key === 'R') {
        e.preventDefault();
        resetTimer();
        return;
      }
      if (e.key === 'Escape') {
        window.close();
        e.preventDefault();
        return;
      }
      // Don't process other keys in speaker window
      return;
    }

    // Preview mode: don't handle keyboard chrome
    if (isPreview) return;

    // Esc - close all overlays
    if (e.key === 'Escape') {
      closeAllOverlays();
      return;
    }

    switch (e.key) {
      case 'ArrowLeft': case 'PageUp':
        e.preventDefault(); prevSlide(); break;
      case 'ArrowRight': case 'PageDown':
        e.preventDefault(); nextSlide(); break;
      case ' ':
        if (!e.shiftKey) {
          e.preventDefault();
          if (!animationLoop) { nextSlide(); }
        } else { e.preventDefault(); prevSlide(); }
        break;
      case 'Home': e.preventDefault(); firstSlide(); break;
      case 'End': e.preventDefault(); lastSlide(); break;
      case 'f': case 'F': toggleFullscreen(); break;
      case 's': case 'S': openSpeakerMode(); break;
      case 'n': case 'N': toggleNotes(); break;
      case 'r': case 'R': resetTimer(); break;
      case 'o': case 'O': toggleOverview(); break;
      case 't': case 'T': cycleTheme(); break;
      case 'a': case 'A': toggleAnimationLoop(); break;
    }
  }

  function closeAllOverlays() {
    if (overviewOpen) { toggleOverview(); }
    if (notesOpen) { toggleNotes(); }
    if (animationLoop) { toggleAnimationLoop(); }
    if (document.fullscreenElement) {
      document.exitFullscreen().catch(function () {});
    }
  }

  // ─── FULLSCREEN ──────────────────────────────────────────
  function toggleFullscreen() {
    if (!document.fullscreenElement) {
      (document.documentElement.requestFullscreen ||
       document.documentElement.webkitRequestFullscreen ||
       function () {}).call(document.documentElement);
    } else {
      (document.exitFullscreen ||
       document.webkitExitFullscreen ||
       function () {}).call(document);
    }
  }

  // ─── THEME CYCLE ─────────────────────────────────────────
  function cycleTheme() {
    if (themes.length < 2) return;
    currentTheme = (currentTheme + 1) % themes.length;
    applyTheme();
    saveState();
    // Broadcast to speaker window
    if (bc) {
      bc.postMessage({ type: 'theme', theme: themes[currentTheme] });
    }
    localStorage.setItem('ppt-theme', themes[currentTheme]);
  }

  function applyTheme() {
    if (themes.length === 0) return;
    document.body.className = '';
    document.body.classList.add(themes[currentTheme]);
  }

  // ─── NOTES DRAWER ────────────────────────────────────────
  function toggleNotes() {
    notesOpen = !notesOpen;
    var drawer = document.getElementById('ppt-notes-drawer');
    if (!drawer) {
      drawer = document.createElement('div');
      drawer.id = 'ppt-notes-drawer';
      var activeSlide = slides[currentSlide];
      var notes = activeSlide ? (activeSlide.querySelector('.notes') || null) : null;
      var notesContent = notes ? notes.textContent || notes.innerHTML : 'No notes for this slide.';
      drawer.innerHTML = '<div class="ppt-notes-inner">' + notesContent + '</div>';
      drawer.style.cssText = 'position:fixed;bottom:0;left:0;right:0;height:200px;background:#1e1e1e;color:#e8e8e8;z-index:9999;overflow-y:auto;transform:translateY(100%);transition:transform 0.3s ease;'
        + 'border-top:2px solid #3b82f6;padding:16px;font-size:14px;line-height:1.6;';
      document.body.appendChild(drawer);
    }
    // Update content
    var activeSlide = slides[currentSlide];
    var notes = activeSlide ? (activeSlide.querySelector('.notes') || null) : null;
    var notesContent = notes ? notes.textContent || notes.innerHTML : 'No notes for this slide.';
    var inner = drawer.querySelector('.ppt-notes-inner');
    if (inner) inner.innerHTML = notesContent;

    if (notesOpen) {
      drawer.style.transform = 'translateY(0)';
    } else {
      drawer.style.transform = 'translateY(100%)';
    }
  }

  // ─── OVERVIEW GRID ───────────────────────────────────────
  function toggleOverview() {
    overviewOpen = !overviewOpen;
    var overlay = document.getElementById('ppt-overview');

    if (overviewOpen) {
      if (!overlay) {
        overlay = document.createElement('div');
        overlay.id = 'ppt-overview';
        overlay.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,0.85);z-index:9998;overflow-y:auto;padding:40px;';

        var grid = document.createElement('div');
        grid.style.cssText = 'display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:20px;max-width:1400px;margin:0 auto;';

        for (var i = 0; i < slides.length; i++) {
          var thumb = document.createElement('div');
          var clone = slides[i].cloneNode(true);
          // Reset styles for thumbnail
          clone.style.display = '';
          clone.style.position = 'relative';
          clone.style.transform = 'scale(0.15)';
          clone.style.transformOrigin = 'top left';
          clone.style.width = '600%';
          clone.style.height = 'auto';
          clone.style.border = 'none';
          clone.style.fontSize = '16px';
          clone.style.overflow = 'hidden';
          // Wrap for clickable area
          var wrap = document.createElement('div');
          wrap.style.cssText = 'background:#fff;border-radius:8px;overflow:hidden;cursor:pointer;aspect-ratio:16/9;position:relative;'
            + (i === currentSlide ? 'border:3px solid #3b82f6;box-shadow:0 0 12px rgba(59,130,246,0.6);' : 'border:2px solid #444;');
          var innerWrap = document.createElement('div');
          innerWrap.style.cssText = 'position:relative;width:100%;height:100%;overflow:hidden;';
          innerWrap.appendChild(clone);
          wrap.appendChild(innerWrap);

          // Label
          var label = document.createElement('div');
          label.style.cssText = 'text-align:center;margin-top:8px;color:#ccc;font-size:13px;font-family:sans-serif;';
          label.textContent = 'Slide ' + (i + 1);
          wrap.appendChild(label);

          wrap.addEventListener('click', (function (idx) {
            return function () {
              goToSlide(idx);
              toggleOverview();
            };
          })(i));

          grid.appendChild(wrap);
        }

        overlay.appendChild(grid);
        document.body.appendChild(overlay);

        // Close on click outside
        overlay.addEventListener('click', function (e) {
          if (e.target === overlay) { toggleOverview(); }
        });
      }
    } else {
      if (overlay) {
        overlay.remove();
      }
    }
  }

  // ─── ANIMATION LOOP ──────────────────────────────────────
  function toggleAnimationLoop() {
    animationLoop = !animationLoop;
    if (animationLoop) {
      // Loop animations on current slide
      var activeSlide = slides[currentSlide];
      if (activeSlide) {
        // Find animated elements (elements with data-animate or .animate class)
        var animated = activeSlide.querySelectorAll('[data-animate], .animate');
        if (animated.length === 0) {
          // If no animated elements, just pulse the slide
          activeSlide.style.animation = 'ppt-pulse 2s ease-in-out infinite';
          if (!document.getElementById('ppt-pulse-keyframes')) {
            var style = document.createElement('style');
            style.id = 'ppt-pulse-keyframes';
            style.textContent = '@keyframes ppt-pulse{0%,100%{opacity:1}50%{opacity:0.5}}';
            document.head.appendChild(style);
          }
        } else {
          // Restart animations
          for (var i = 0; i < animated.length; i++) {
            animated[i].style.animation = 'none';
            // Force reflow
            void animated[i].offsetHeight;
            animated[i].style.animation = '';
          }
        }
      }
      // Auto-advance loop every 5s
      animationTimer = setInterval(function () {
        var next = (currentSlide + 1) % totalSlides;
        goToSlide(next);
      }, 5000);
    } else {
      clearInterval(animationTimer);
      var activeSlide = slides[currentSlide];
      if (activeSlide) {
        activeSlide.style.animation = '';
        var animated = activeSlide.querySelectorAll('[data-animate], .animate');
        for (var i = 0; i < animated.length; i++) {
          animated[i].style.animation = '';
        }
      }
    }
  }

  // ─── TIMER ───────────────────────────────────────────────
  function initTimer() {
    perSlideTimers = JSON.parse(localStorage.getItem('ppt-timers') || '{}');
    currentElapsed = parseInt(perSlideTimers[currentSlide] || '0', 10) * 1000;
    timerStart = Date.now() - currentElapsed;
    timerInterval = setInterval(tickTimer, 1000);
    tickTimer();
  }

  function tickTimer() {
    currentElapsed = Date.now() - timerStart;
    // Update timer display (for speaker window)
    var timerDisplay = document.getElementById('ppt-timer');
    if (timerDisplay) {
      timerDisplay.textContent = formatTime(currentElapsed);
    }
    var timerDisplaySmall = document.getElementById('ppt-timer-small');
    if (timerDisplaySmall) {
      timerDisplaySmall.textContent = formatTime(currentElapsed);
    }
    // Notify speaker
    if (bc) {
      bc.postMessage({ type: 'timer', elapsed: currentElapsed, slide: currentSlide });
    }
  }

  function resetTimer() {
    timerStart = Date.now();
    currentElapsed = 0;
    perSlideTimers[currentSlide] = '0';
    localStorage.setItem('ppt-timers', JSON.stringify(perSlideTimers));
    tickTimer();
  }

  function onSlideChange() {
    // Save previous slide time
    var prevKey = perSlideTimers;
    perSlideTimers[currentSlide] = String(Math.floor(currentElapsed / 1000));
    localStorage.setItem('ppt-timers', JSON.stringify(perSlideTimers));
    // Start fresh for new slide
    timerStart = Date.now();
    currentElapsed = 0;
    tickTimer();

    // Update notes drawer if open
    if (notesOpen) { toggleNotes(); } // Refresh
  }

  function formatTime(ms) {
    var totalSec = Math.floor(ms / 1000);
    var mm = Math.floor(totalSec / 60);
    var ss = totalSec % 60;
    return (mm < 10 ? '0' : '') + mm + ':' + (ss < 10 ? '0' : '') + ss;
  }

  // ─── SPEAKER MODE ────────────────────────────────────────
  function openSpeakerMode() {
    if (speakerWindow && !speakerWindow.closed) {
      speakerWindow.focus();
      return;
    }

    speakerWindow = window.open('', '_blank', 'width=1400,height=900,noopener,noreferrer');
    speakerWindow.document.write(buildSpeakerHTML());
    speakerWindow.document.close();

    // Notify after document ready
    setTimeout(function () {
      notifySpeakerWindow();
    }, 500);

    // Handle close
    var closeCheck = setInterval(function () {
      if (speakerWindow.closed) {
        speakerWindow = null;
        clearInterval(closeCheck);
      }
    }, 2000);
  }

  function buildSpeakerHTML() {
    var baseUrl = window.location.href.split('?')[0].split('#')[0];

    // Load card positions from localStorage
    var cardPositions = JSON.parse(localStorage.getItem('ppt-cards') || 'null');

    function cardStyle(id, defaultPos) {
      if (cardPositions && cardPositions[id]) {
        var p = cardPositions[id];
        return 'left:' + p.left + 'px;top:' + p.top + 'px;width:' + p.width + 'px;height:' + p.height + 'px;';
      }
      return 'left:' + defaultPos[0] + 'px;top:' + defaultPos[1] + 'px;width:' + defaultPos[2] + 'px;height:' + defaultPos[3] + 'px;';
    }

    function cardIframe(id, slideIdx, extra) {
      var idx = typeof slideIdx === 'number' ? slideIdx : currentSlide;
      return '<iframe id="' + id + '" src="' + baseUrl + '?preview=' + (idx + 1) + (extra || '') + '" '
        + 'style="border:none;width:100%;height:calc(100% - 32px);margin-top:32px;border-radius:6px;background:#000;"'
        + 'allowfullscreen></iframe>';
    }

    var notesEl = slides[currentSlide] ? slides[currentSlide].querySelector('.notes') : null;
    var notesText = notesEl ? notesEl.textContent || notesEl.innerHTML : 'No notes for this slide.';

    return '<!DOCTYPE html>'
      + '<html lang="zh-CN">'
      + '<head>'
      + '<meta charset="UTF-8">'
      + '<title>Speaker Mode</title>'
      + '<style>'
      + 'body{margin:0;padding:0;background:#1a1a2e;font-family:system-ui,-apple-system,sans-serif;overflow:hidden;width:100vw;height:100vh;}'
      + '.card{position:absolute;background:#16213e;border-radius:12px;box-shadow:0 4px 24px rgba(0,0,0,0.4);overflow:hidden;cursor:move;resize:both;min-width:200px;min-height:150px;}'
      + '.card-header{position:absolute;top:0;left:0;right:0;height:32px;background:linear-gradient(135deg,#0f3460,#16213e);display:flex;align-items:center;padding:0 12px;color:#e8e8e8;font-size:12px;font-weight:600;letter-spacing:0.5px;text-transform:uppercase;z-index:10;}'
      + '.card-header .close{margin-left:auto;cursor:pointer;opacity:0.6;font-size:16px;}'
      + '.card-header .close:hover{opacity:1;}'
      + '#timer-display{position:absolute;top:32px;left:0;right:0;height:calc(100% - 32px);display:flex;flex-direction:column;align-items:center;justify-content:center;color:#e8e8e8;font-family:monospace;z-index:5;}'
      + '#timer-display .time{font-size:72px;font-weight:700;letter-spacing:4px;color:#4fc3f7;text-shadow:0 0 20px rgba(79,195,247,0.3);}'
      + '#timer-display .label{font-size:14px;color:#666;margin-top:12px;}'
      + '#script-content{position:absolute;top:32px;left:0;right:0;bottom:0;padding:16px;color:#d0d0d0;font-size:14px;line-height:1.7;overflow-y:auto;z-index:5;}'
      + '</style>'
      + '</head>'
      + '<body>'

      // CURRENT card
      + '<div class="card" id="card-current" style="' + cardStyle('card-current', [20, 20, 600, 400]) + '">'
      + '<div class="card-header">Current Slide<span class="close" onclick="window.close()">&times;</span></div>'
      + cardIframe('iframe-current', currentSlide)
      + '</div>'

      // NEXT card
      + '<div class="card" id="card-next" style="' + cardStyle('card-next', [640, 20, 600, 400]) + '">'
      + '<div class="card-header">Next Slide</div>'
      + cardIframe('iframe-next', Math.min(currentSlide + 1, totalSlides - 1))
      + '</div>'

      // SCRIPT card
      + '<div class="card" id="card-script" style="' + cardStyle('card-script', [20, 440, 600, 300]) + '">'
      + '<div class="card-header">Speaker Notes</div>'
      + '<div id="script-content">' + escapeHtml(notesText) + '</div>'
      + '</div>'

      // TIMER card
      + '<div class="card" id="card-timer" style="' + cardStyle('card-timer', [640, 440, 600, 300]) + '">'
      + '<div class="card-header" style="cursor:move;">Timer <span style="margin-left:12px;font-size:11px;opacity:0.5;">Press R to reset</span><span class="close" onclick="window.close()">&times;</span></div>'
      + '<div id="timer-display"><div class="time" id="speaker-timer">' + formatTime(currentElapsed) + '</div><div class="label">Press R to reset timer</div></div>'
      + '</div>'

      + '<script>'
      + '(function() {'
      // Drag logic
      + 'var dragTarget = null, dragOffX = 0, dragOffY = 0;'
      + 'document.addEventListener("mousedown", function(e) {'
      + '  var card = e.target.closest(".card");'
      + '  if (card && !e.target.classList.contains("close")) {'
      + '    dragTarget = card;'
      + '    var rect = card.getBoundingClientRect();'
      + '    dragOffX = e.clientX - rect.left;'
      + '    dragOffY = e.clientY - rect.top;'
      + '    card.style.zIndex = 100;'
      + '    e.preventDefault();'
      + '  }'
      + '});'
      + 'document.addEventListener("mousemove", function(e) {'
      + '  if (dragTarget) {'
      + '    dragTarget.style.left = (e.clientX - dragOffX) + "px";'
      + '    dragTarget.style.top = (e.clientY - dragOffY) + "px";'
      + '    savePositions();'
      + '  }'
      + '});'
      + 'document.addEventListener("mouseup", function() {'
      + '  if (dragTarget) {'
      + '    dragTarget.style.zIndex = "";'
      + '    dragTarget = null;'
      + '  }'
      + '});'
      // Resize observation
      + 'try {'
      + '  var ro = new ResizeObserver(function() { savePositions(); });'
      + '  document.querySelectorAll(".card").forEach(function(c) { ro.observe(c); });'
      + '} catch(e) {}'
      // Save positions
      + 'function savePositions() {'
      + '  try {'
      + '    var pos = {};'
      + '    document.querySelectorAll(".card").forEach(function(c) {'
      + '      pos[c.id] = { left: parseInt(c.style.left), top: parseInt(c.style.top), width: c.offsetWidth, height: c.offsetHeight };'
      + '    });'
      + '    localStorage.setItem("ppt-cards", JSON.stringify(pos));'
      + '  } catch(e) {}'
      + '}'
      // BroadcastChannel listener in speaker window
      + 'try {'
      + '  var speakerBc = new BroadcastChannel("ppt-deck-sync");'
      + '  speakerBc.onmessage = function(e) {'
      + '    var data = e.data;'
      + '    if (data.type === "goto") {'
      + '      updateIframes(data.slide);'
      + '    }'
      + '    if (data.type === "theme") {'
      + '      updateIframes(speakerCurrentSlide);'
      + '    }'
      + '    if (data.type === "timer") {'
      + '      var totalTime = Math.floor(data.elapsed / 1000);'
      + '      var mm = Math.floor(totalTime / 60);'
      + '      var ss = totalTime % 60;'
      + '      var timeStr = (mm < 10 ? "0" : "") + mm + ":" + (ss < 10 ? "0" : "") + ss;'
      + '      var el = document.getElementById("speaker-timer");'
      + '      if (el) el.textContent = timeStr;'
      + '    }'
      + '  };'
      + '} catch(e) {}'
      + 'var speakerCurrentSlide = 0;'
      + 'function updateIframes(slideIdx) {'
      + '  speakerCurrentSlide = slideIdx;'
      + '  var baseUrl = window.location.href.split("?")[0].split("#")[0];'
      + '  var cur = document.getElementById("iframe-current");'
      + '  var nxt = document.getElementById("iframe-next");'
      + '  if (cur) cur.src = baseUrl + "?preview=" + (speakerCurrentSlide + 1) + "&theme=" + encodeURIComponent("' + (themes[currentTheme] || '') + '");'
      + '  if (nxt) nxt.src = baseUrl + "?preview=" + (Math.min(speakerCurrentSlide + 1, ' + totalSlides + ' - 1) + 1) + "&theme=" + encodeURIComponent("' + (themes[currentTheme] || '') + '");'
      + '}'
      + 'speakerCurrentSlide = ' + currentSlide + ';'
      + 'function formatTime(ms) {'
      + '  var t = Math.floor(ms / 1000);'
      + '  var mm = Math.floor(t / 60);'
      + '  var ss = t % 60;'
      + '  return (mm < 10 ? "0" : "") + mm + ":" + (ss < 10 ? "0" : "") + ss;'
      + '}'
      + '})();'
      + '</script>'
      + '</body></html>';
  }

  function notifySpeakerWindow() {
    if (bc && speakerWindow && !speakerWindow.closed) {
      bc.postMessage({ type: 'goto', slide: currentSlide });
    }
  }

  function notifySpeakerIframe() {
    // postMessage to iframes in this window (used in preview mode / speaker window)
    // This is handled by the iframe listeners
  }

  // ─── BROADCAST CHANNEL ───────────────────────────────────
  function onBroadcastMessage(e) {
    var data = e.data;
    if (!data) return;

    if (data.type === 'goto' && data.slide !== undefined) {
      goToSlide(data.slide, true); // skip re-broadcast
    }
    if (data.type === 'theme' && data.theme) {
      var idx = themes.indexOf(data.theme);
      if (idx !== -1) {
        currentTheme = idx;
        applyTheme();
      }
    }
  }

  // ─── IFRAME COMMUNICATION ────────────────────────────────
  function notifyParent() {
    // If we're inside a speaker window iframe, notify parent
    try {
      if (window.parent !== window) {
        window.parent.postMessage({
          type: 'ppt-slide',
          slide: currentSlide
        }, '*');
      }
    } catch (e) {}
  }

  function onIframeMessage(e) {
    if (!e.data) return;
    if (e.data.type === 'ppt-slide') {
      // Iframe is requesting slide info
    }
  }

  // ─── STATE PERSISTENCE ───────────────────────────────────
  function saveState() {
    try {
      localStorage.setItem('ppt-slide', String(currentSlide));
    } catch (e) {}
  }

  // ─── UTILITY ─────────────────────────────────────────────
  function escapeHtml(str) {
    return str
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  // ─── BOOT ────────────────────────────────────────────────
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

})();
