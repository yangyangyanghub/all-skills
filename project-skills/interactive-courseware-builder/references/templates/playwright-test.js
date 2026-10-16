// Playwright Automated Test for Interactive Courseware
// 使用方法: node playwright-test.js <path-to-html-file>
// 需先安装: npm install playwright

// ===== 测试项 =====
// 1. 页面翻页: 验证所有页面可正常切换
// 2. 测验逻辑: 验证选项选择和评分
// 3. Canvas仿真: 验证Canvas元素存在且尺寸正确
// 4. 响应式: 验证移动端390×844视口下无溢出
// 5. JS错误: 捕获页面运行时的JS错误

const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const htmlPath = process.argv[2];
if (!htmlPath) {
  console.error('Usage: node playwright-test.js <path-to-html-file>');
  process.exit(1);
}
if (!fs.existsSync(htmlPath)) {
  console.error('File not found: ' + htmlPath);
  process.exit(1);
}

const fileUrl = 'file://' + path.resolve(htmlPath);

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 390, height: 844 } });
  const errors = [];
  page.on('pageerror', e => errors.push(e.message));

  console.log('--- Testing: ' + htmlPath + ' ---');

  // 1. 加载页面
  await page.goto(fileUrl, { waitUntil: 'networkidle' });
  console.log('1. Page loaded. JS errors so far: ' + errors.length);
  if (errors.length > 0) errors.forEach(e => console.log('   ERROR: ' + e));

  // 2. 翻页测试
  const navChips = await page.$$('#topNav .chip');
  const totalPages = navChips.length;
  console.log('2. Total pages: ' + totalPages);

  for (let i = 0; i < totalPages; i++) {
    await navChips[i].click();
    await page.waitForTimeout(300);
    const activePage = await page.$('.page.active');
    const pageId = await activePage.getAttribute('id');
    console.log('   Page ' + i + ': ' + pageId);
  }

  // 3. 测验测试 — 定位第一个测验页（.quiz-page 是测验页容器类，测验题目为 .quiz-q）
  //    先经导航芯片激活该页（隐藏页点击无效），再点击第一题的第一个选项并验证 answered 状态
  const quizPages = await page.$$('.quiz-page');
  console.log('3. Quiz pages found: ' + quizPages.length);
  if (quizPages.length > 0) {
    const idx = await page.evaluate(function(sec) {
      return (typeof PAGE_IDS !== 'undefined') ? PAGE_IDS.indexOf(sec.id) : -1;
    }, quizPages[0]);
    if (idx >= 0) {
      const chip = await page.$('#topNav .chip[data-page="' + idx + '"]');
      if (chip) { await chip.click(); await page.waitForTimeout(300); }
    }
    const opts = await quizPages[0].$$('.opt');
    console.log('   First quiz page options: ' + opts.length);
    if (opts.length > 0) {
      await opts[0].click();
      await page.waitForTimeout(200);
      const answered = await quizPages[0].evaluate(function(sec) {
        var qq = sec.querySelector('.quiz-q');
        return qq ? qq.classList.contains('answered') : false;
      });
      console.log('   First question answered: ' + answered);
    }
  } else {
    console.log('   No quiz pages found (skipped)');
  }

  // 4. Canvas测试
  const canvases = await page.$$('canvas');
  console.log('4. Canvas elements found: ' + canvases.length);
  for (let i = 0; i < canvases.length; i++) {
    const w = await canvases[i].evaluate(el => el.width);
    const h = await canvases[i].evaluate(el => el.height);
    console.log('   Canvas ' + i + ': ' + w + 'x' + h);
  }

  // 5. 响应式溢出检查
  const bodyWidth = await page.evaluate(() => document.body.scrollWidth);
  const viewportWidth = await page.evaluate(() => window.innerWidth);
  console.log('5. Mobile viewport: ' + viewportWidth + 'px, body scroll: ' + bodyWidth + 'px');
  if (bodyWidth > viewportWidth + 10) {
    console.log('   WARNING: Possible horizontal overflow on mobile!');
  }

  // 结果汇总
  console.log('\n--- Summary ---');
  console.log('Pages: ' + totalPages);
  console.log('Quiz pages: ' + quizPages.length);
  console.log('Canvases: ' + canvases.length);
  console.log('JS errors: ' + errors.length);
  if (errors.length > 0) {
    console.log('FAIL: JS errors detected');
    errors.forEach(e => console.log('  - ' + e));
  } else {
    console.log('PASS: No JS errors');
  }

  await browser.close();
})();
