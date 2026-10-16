// quiz-answer-check.js — 交互式课件「正确答案位置分布」防呆校验（硬规约 #19）
// 规则：同一测验内正确答案不得全部集中在同一选项位置（防止「全蒙 A 即满分」）。
//   前测/中测/后测各算「一个测验」（即 QUIZZES 的每个 key）。
// 用法：
//   node quiz-answer-check.js <file.html | 目录> [...] [--min-q 3] [--max-ratio 0.8]
//     <file.html | 目录>  单文件或目录（目录递归扫描 *.html）
//     --min-q <n>         触发「全集中」硬判定所需的最少单选题数（默认 3）
//     --max-ratio <r>     触发「高占比告警」的位置占比阈值（默认 0.8，仅对 ≥5 题生效）
// 退出码：0 = PASS（无硬违规）；1 = FAIL（存在测验答案全部集中在同一位置）；2 = 用法/无输入
//
// 判定：
//   FAIL —— 单个测验单选数 ≥ min-q 且某位置占比 = 100%（典型：全 A）
//   WARN —— 单个测验单选数 ≥ 5 且某位置占比 ≥ max-ratio（但未 100%）
//          或多选题 ≥ 3 且每题正确答案都含同一位置（位置偏置信号）
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const POS = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H'];
const posName = (i) => (typeof i === 'number' && i >= 0 && i < POS.length) ? POS[i] : String(i);

function parseArgs(argv) {
  const files = [];
  const opts = { minQ: 3, maxRatio: 0.8 };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--min-q') opts.minQ = parseInt(argv[++i], 10);
    else if (a === '--max-ratio') opts.maxRatio = parseFloat(argv[++i]);
    else files.push(a);
  }
  return { files, opts };
}

function walk(p, out) {
  let st;
  try { st = fs.statSync(p); } catch (e) { return; }
  if (st.isDirectory()) {
    for (const e of fs.readdirSync(p)) walk(path.join(p, e), out);
  } else if (/\.html?$/i.test(p)) {
    out.push(p);
  }
}

// 按「大括号平衡」从源码中提取 `var QUIZZES = {...}` 的对象字面量文本。
// 状态机跳过字符串/模板串/行注释/块注释，避免字符串内的括号干扰平衡计数。
function extractQuizzes(src) {
  const m = /var\s+QUIZZES\s*=\s*\{/.exec(src);
  if (!m) return null;
  const start = src.indexOf('{', m.index);
  let depth = 0, q = null, esc = false, line = false, block = false;
  for (let i = start; i < src.length; i++) {
    const c = src[i], n = src[i + 1];
    if (line) { if (c === '\n') line = false; continue; }
    if (block) { if (c === '*' && n === '/') { block = false; i++; } continue; }
    if (q) {
      if (esc) { esc = false; continue; }
      if (c === '\\') { esc = true; continue; }
      if (c === q) { q = null; }
      continue;
    }
    if (c === '/' && n === '/') { line = true; i++; continue; }
    if (c === '/' && n === '*') { block = true; i++; continue; }
    if (c === '"' || c === "'" || c === '`') { q = c; continue; }
    if (c === '{') depth++;
    else if (c === '}') { depth--; if (depth === 0) return src.slice(start, i + 1); }
  }
  return null;
}

function evalQuizzes(objText) {
  const ctx = {};
  vm.createContext(ctx);
  new vm.Script('__Q__ = ' + objText).runInContext(ctx);
  return ctx.__Q__;
}

function checkFile(f, opts) {
  const src = fs.readFileSync(f, 'utf8');
  const objText = extractQuizzes(src);
  if (!objText) return { skip: true };
  let Q;
  try { Q = evalQuizzes(objText); }
  catch (e) { return { parseErr: e.message }; }

  const reports = [];
  let hardFail = 0, warn = 0;

  for (const key of Object.keys(Q)) {
    const entry = Q[key];
    const arr = (entry && Array.isArray(entry.questions)) ? entry.questions : [];
    const singles = arr.filter(x => x && !x.multi && typeof x.answer === 'number');
    const multis = arr.filter(x => x && x.multi && Array.isArray(x.answer));

    // —— 单选题位置分布 ——
    if (singles.length > 0) {
      const dist = {};
      for (const x of singles) dist[x.answer] = (dist[x.answer] || 0) + 1;
      let maxPos = null, maxN = -1;
      for (const k of Object.keys(dist)) { if (dist[k] > maxN) { maxN = dist[k]; maxPos = k; } }
      const ratio = maxN / singles.length;
      let level = 'OK', note = '';
      if (singles.length >= opts.minQ && ratio >= 1) {
        level = 'FAIL'; hardFail++;
        note = '全集中→' + posName(parseInt(maxPos, 10));
      } else if (singles.length >= 5 && ratio >= opts.maxRatio) {
        level = 'WARN'; warn++;
        note = '高占比 ' + posName(parseInt(maxPos, 10)) + ' ' + Math.round(ratio * 100) + '%';
      }
      const distStr = Object.keys(dist).sort((a, b) => a - b)
        .map(k => posName(parseInt(k, 10)) + dist[k]).join(' ');
      reports.push({ key, n: singles.length, kind: '单选', distStr, level, note });
    }

    // —— 多选题位置偏置（每题正确答案是否都含同一位置）——
    if (multis.length >= 3) {
      let inter = multis[0].answer.slice();
      for (const x of multis.slice(1)) inter = inter.filter(v => x.answer.indexOf(v) >= 0);
      if (inter.length > 0) {
        warn++;
        reports.push({
          key, n: multis.length, kind: '多选',
          distStr: '交集含 ' + inter.map(posName).join('/'),
          level: 'WARN', note: '每题均含同一位置'
        });
      }
    }
  }
  return { reports, hardFail, warn };
}

function main() {
  const { files: inputs, opts } = parseArgs(process.argv.slice(2));
  const targets = [];
  for (const p of inputs) {
    if (!fs.existsSync(p)) { console.error('跳过（不存在）：' + p); continue; }
    walk(p, targets);
  }
  if (targets.length === 0) {
    console.error('用法：node quiz-answer-check.js <file.html | 目录> [...] [--min-q 3] [--max-ratio 0.8]');
    console.error('（未提供有效输入 = 未做任何校验，禁止据此判定通过）');
    process.exit(2);
  }

  let totalFail = 0, totalWarn = 0, scanned = 0, skipped = 0;
  for (const f of targets) {
    const r = checkFile(f, opts);
    if (r.skip) { skipped++; continue; }
    scanned++;
    if (r.parseErr) { console.log('=== ' + f + '\n  [PARSE_ERR] ' + r.parseErr); continue; }
    const flagged = r.reports.filter(x => x.level !== 'OK');
    if (flagged.length === 0) continue; // 正常课件不刷屏
    console.log('=== ' + f);
    for (const rep of r.reports) {
      console.log('  [' + rep.level + '] ' + rep.key + '  ' + rep.kind + rep.n +
        '  分布 ' + rep.distStr + (rep.note ? '  ' + rep.note : ''));
    }
    totalFail += r.hardFail;
    totalWarn += r.warn;
  }

  console.log('---');
  console.log('扫描含 QUIZZES 的课件：' + scanned + '（跳过无 QUIZZES：' + skipped + '）');
  console.log('硬违规（答案全集中）：' + totalFail + '   告警（位置偏置）：' + totalWarn);
  console.log(totalFail > 0 ? 'RESULT: FAIL' : 'RESULT: PASS');
  process.exit(totalFail > 0 ? 1 : 0);
}

main();
