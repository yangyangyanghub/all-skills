#!/usr/bin/env node
/**
 * quiz-modify-test.js — 「答题提交前可改、提交后锁定」行为级测试（jsdom）
 *
 * 用法： node quiz-modify-test.js <courseware.html>
 * 依赖： jsdom（NODE_PATH 指向已安装 jsdom 的 node_modules）
 *
 * 检查两层：
 *   A. 源码断言（CSS 锁定语义）——直接扫 HTML 源码，不依赖 jsdom 样式表
 *      （教训：jsdom 的 CSSStylesheet 解析不可靠、getComputedStyle 可能抛
 *       Specificity 异常，CSS 断言一律扫源码；真实渲染另用 playwright 截图核验）
 *   B. 行为断言（JS 闸门语义）——jsdom 加载课件后真实点击：
 *      单选选 A 改 C 生效 / 多选确认后可重选重确认 / 提交后再点不生效 / submitted 类就位
 *
 * ⚠ 已知盲区（必须理解再解读结果）：jsdom 的 element.click() 不受 display:none 拦截，
 *   所以「多选确认按钮被隐藏后能否点到位」行为测试测不出——该语义由 A 层的
 *   `.quiz-q.submitted .opt-confirm{display:none}` 源码断言保证（对应 L4 教训）。
 *
 * 退出码：0 = ALL PASS；1 = 有 FAIL 或课件无法加载。
 */
const fs = require("fs");
const path = require("path");
const { JSDOM } = require("jsdom");

const file = process.argv[2];
if (!file) { console.error("usage: node quiz-modify-test.js <courseware.html>"); process.exit(1); }
const html = fs.readFileSync(file, "utf8");

const results = [];
function check(name, ok, detail) {
  results.push({ name, ok: !!ok, detail: detail || "" });
  console.log((ok ? "PASS" : "FAIL") + " | " + name + (detail ? " | " + detail : ""));
}

const dom = new JSDOM(html, {
  runScripts: "dangerously",
  resources: undefined,           // 不加载外部资源
  url: "https://example.test/courseware.html",
  pretendToBeVisual: true,
  beforeParse(window) {
    // canvas / scrollIntoView 桩（jsdom 缺失会让 showPage 初始化抛错、后半段脚本不执行）
    window.HTMLCanvasElement.prototype.getContext = function () {
      return new Proxy({}, { get: () => () => undefined });
    };
    window.HTMLElement.prototype.scrollIntoView = function () {};
    // submitQuiz 依赖项
    window.studentId = window.studentId || "TEST_SID";
    window.xmnAgg = window.xmnAgg || {};
    window.showToast = window.showToast || function () {};
    window.showConfirmModal = window.showConfirmModal || function (o) { if (o && o.onOk) o.onOk(); };
    window.updateBadgeStats = window.updateBadgeStats || function () {};
    window.xmnPublish = window.xmnPublish || function () {};
    window.addEventListener = window.addEventListener.bind(window);
    window.onerror = function (msg) { console.log("  [window.onerror] " + msg); };
  },
});

const { window } = dom;
const { document } = window;

setTimeout(function () {
  try {
    /* ============ A. 源码断言（CSS 锁定语义） ============ */
    check("A1 选项CSS锁挂submitted前缀", /\.quiz-q\.submitted \.opt\{pointer-events:none/.test(html));
    check("A2 旧answered选项锁已移除", !/\.quiz-q\.answered \.opt\{pointer-events:none/.test(html));
    const hasConfirmCss = /\.quiz-q\.(submitted|answered) \.opt-confirm\{display:none\}/.test(html);
    if (hasConfirmCss) {
      check("A3 确认按钮隐藏挂submitted前缀", /\.quiz-q\.submitted \.opt-confirm\{display:none\}/.test(html));
      check("A4 旧answered确认按钮隐藏已移除", !/\.quiz-q\.answered \.opt-confirm\{display:none\}/.test(html));
    } else {
      check("A3 确认按钮隐藏CSS(无此CSS,跳过)", true);
      check("A4 旧确认按钮隐藏(无此CSS,跳过)", true);
    }
    check("A5 submitQuiz注入submitted类", /classList\.add\('submitted'\)/.test(html));
    const navOk = /#navBtns\{[^}]*position:fixed !important/.test(html)
      && /#navBtns\{[^}]*left:50% !important/.test(html)
      && /#navBtns\{[^}]*transform:translateX\(-50%\) !important/.test(html);
    check("A6 navBtns底部居中!important加固", navOk);

    /* ============ B. 行为断言（JS 闸门语义） ============ */
    if (typeof window.QUIZZES !== "object" || !window.QUIZZES) {
      check("B0 课件含QUIZZES数据", false, "window.QUIZZES 未定义");
      return finish();
    }
    const quizId = Object.keys(window.QUIZZES)[0];
    const container = document.getElementById(quizId);
    if (!container || !container._initialized) {
      check("B0 quiz容器已初始化", false, quizId + " 不存在或 initQuiz 未执行(主脚本可能中断)");
      return finish();
    }
    const qs = container._questions;
    const qqOf = (i) => document.getElementById("qq_" + quizId + "_" + i);
    const multiIdx = qs.findIndex((q) => window.isMultiQ && window.isMultiQ(q));
    const singleIdx = qs.findIndex((q, i) => !(window.isMultiQ && window.isMultiQ(q)));

    // B1 单选：选 A 改 C
    if (singleIdx >= 0) {
      const opts = qqOf(singleIdx).querySelectorAll(".opt");
      opts[0].click();
      const first = container._chosen[singleIdx];
      opts[2].click();
      const second = container._chosen[singleIdx];
      check("B1 单选提交前可改选", first === 0 && second === 2,
        "first=" + first + " second=" + second);
    } else {
      check("B1 单选提交前可改选(无单选题,跳过)", true);
    }

    // B2 多选：确认后可重选、重确认
    if (multiIdx >= 0) {
      const qq = qqOf(multiIdx);
      const opts = qq.querySelectorAll(".opt");
      const btn = qq.querySelector(".opt-confirm");
      opts[0].click(); opts[1].click(); opts[2].click();
      if (btn) btn.click();
      const c1 = JSON.stringify(container._chosen[multiIdx]);
      opts[1].click();                 // 取消中间项 → 重选
      if (btn) btn.click();            // 重新确认
      const c2 = JSON.stringify(container._chosen[multiIdx]);
      check("B2 多选提交前可重选重确认", c1 !== c2, "c1=" + c1 + " c2=" + c2);
    } else {
      check("B2 多选提交前可重选重确认(无多选题,跳过)", true);
    }

    // B3 提交后锁定：填满全部答案 → submitQuiz → 再点不生效
    qs.forEach(function (q, i) {
      if (window.isMultiQ && window.isMultiQ(q)) {
        if (!Array.isArray(container._chosen[i])) container._chosen[i] = [0];
      } else if (container._chosen[i] < 0) {
        const opts = qqOf(i).querySelectorAll(".opt");
        if (opts[0]) opts[0].click();
      }
    });
    const before = JSON.stringify(container._chosen);
    const activity = (window.ACTIVITY_QUIZ_MAP && Object.keys(window.ACTIVITY_QUIZ_MAP)[0]) || "test";
    window.submitQuiz(quizId, activity);
    const subOk = container._submitted === true;
    // 提交后再点击：单选 _chosen 不应变；多选 _picked 可动但 _chosen 不应变
    qs.forEach(function (q, i) {
      const opts = qqOf(i).querySelectorAll(".opt");
      if (opts[1]) opts[1].click();
    });
    const after = JSON.stringify(container._chosen);
    check("B3 提交后_chosen锁定", subOk && before === after, "submitted=" + subOk);
    const hasSubClass = Array.from(container.querySelectorAll(".quiz-q"))
      .every(function (qq) { return qq.classList.contains("submitted"); });
    check("B4 每题都有submitted类", hasSubClass);
  } catch (e) {
    check("EXCEPTION", false, e.message);
  }
  finish();

  function finish() {
    const fails = results.filter(function (r) { return !r.ok; });
    console.log("RESULT: " + (fails.length === 0 ? "ALL PASS (" + results.length + " 项)" : fails.length + " FAIL"));
    process.exit(fails.length === 0 ? 0 : 1);
  }
}, 300);
