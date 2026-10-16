// syntax-check.js — 校验单文件 HTML 中全部内联 <script> 的 JS 语法
// 用法：node syntax-check.js <file.html> [...]
const fs = require('fs');
const vm = require('vm');

let bad = 0;
const files = process.argv.slice(2);
if (files.length === 0) {
  console.error('用法：node syntax-check.js <file.html> [...]');
  console.error('（未提供文件 = 未做任何校验，禁止据此判定通过）');
  process.exit(2);
}
for (const f of files) {
  const h = fs.readFileSync(f, 'utf8');
  const re = /<script(?![^>]*\bsrc=)[^>]*>([\s\S]*?)<\/script>/g;
  let m, blocks = [];
  while ((m = re.exec(h)) !== null) blocks.push(m[1]);
  console.log('=== ' + f);
  blocks.forEach((s, i) => {
    try {
      new vm.Script(s);
      console.log('  block ' + i + '  OK   len=' + s.length);
    } catch (e) {
      console.log('  block ' + i + '  ERR  ' + e.message + '  len=' + s.length);
      bad = 1;
    }
  });
}
console.log(bad ? 'RESULT: SYNTAX_ERR' : 'RESULT: SYNTAX_OK');
process.exit(bad);
