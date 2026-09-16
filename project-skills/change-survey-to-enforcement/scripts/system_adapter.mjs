// 系统页面适配器：把国土调查云河北分中心的页面结构解析成结构化数据。
// 页面改版只需改本文件，判定逻辑不受影响。
//
// 已修复的三个坑：
//   ① Element Plus 表格拆成「固定列 + 主体 + 操作列」三张表 → 只读含「图斑编号」表头的那张
//   ② 页面状态漂移 → 读前校验当前图斑编号（assertParcel）
//   ③ el-select 下拉框的值不在 input.value 里 → 单独读 .el-select__selected-item
import { evaluate, dumpText, clickByText } from './cdp_client.mjs';

const TAB_NAMES = ['核查填报', '线索详情', '套合结果', '审核复核', '现场照片', '附件资料', '成果复用'];

// 核查填报表单字段（按页面出现顺序）
export const FILL_FIELDS = [
  '核实认定意见', '分类', '用途分类细化', '项目名称', '建设时间', '项目主体',
  '现场核查描述', '地块面积', '占耕地面积', '占基本农田面积',
  '占非耕农用地面积', '占未利用地面积', '占生态红线面积',
];

// ---------- 状态校验（防页面漂移） ----------

/** 读当前详情页的线索编号；不在详情页返回 '' */
export async function currentParcelId(port = 9222) {
  return await evaluate(port, `(() => {
    const m = document.body.innerText.match(/线索编号[:：]\\s*(\\S+)/);
    return m ? m[1] : '';
  })()`);
}

/** 校验当前是否在目标图斑的详情页；不匹配则抛错 */
export async function assertParcel(port = 9222, expectedId = null) {
  const cur = await currentParcelId(port);
  if (!cur) throw new Error('不在详情页（页面未找到「线索编号」）');
  if (expectedId && cur !== expectedId) {
    throw new Error(`图斑不匹配：期望 ${expectedId}，实际 ${cur}（页面可能未刷新或状态漂移）`);
  }
  return cur;
}

// ---------- 列表页 ----------

/** 读列表页（只读含「图斑编号」表头的主表，避开固定列/操作列） */
export async function readListPage(port = 9222) {
  const js = `(() => {
    for (const hw of document.querySelectorAll('.el-table__header-wrapper')) {
      if (!hw.innerText.includes('图斑编号')) continue;
      const heads = [...hw.querySelectorAll('th')].map(th => th.innerText.trim());
      const bw = hw.parentElement.querySelector('.el-table__body-wrapper');
      const rows = bw ? [...bw.querySelectorAll('tr.el-table__row')].map(tr =>
        [...tr.querySelectorAll('td')].map(td => td.innerText.trim())) : [];
      return { heads, rows };
    }
    return { heads: [], rows: [] };
  })()`;
  const raw = await evaluate(port, js);
  const meta = await evaluate(port, `(() => {
    const t = document.body.innerText;
    const total = (t.match(/共\\s*(\\d+)\\s*条/) || [])[1];
    const size = (t.match(/(\\d+)\\s*条\\s*\\/\\s*页/) || [])[1];
    const active = document.querySelector('.el-pager li.is-active');
    const title = (document.body.innerText.split('\\n').map(s => s.trim()).find(s => /线索处置|违法|变更调查/.test(s)) || '').slice(0, 40);
    return { total: total ? Number(total) : null, pageSize: size ? Number(size) : null,
             page: active ? Number(active.innerText.trim()) : null, pageTitle: title };
  })()`);
  // 主表行前面可能夹着固定列的空单元格，用「图斑编号」位置做基准偏移
  const offset = (raw.rows[0] || []).findIndex(c => /SJBG/.test(c));
  const at = (cells, n) => (offset >= 0 ? (cells[offset + n] || '') : '');
  const rows = raw.rows.map((cells, i) => ({
    seq: i + 1,
    id: at(cells, 0),
    county: at(cells, 1),
    type: at(cells, 2),
    issuedAt: at(cells, 3),
    opinion: at(cells, 4),
    areaMu: at(cells, 5),
    dileiCode: at(cells, 6),
    batch: at(cells, 7),
    operator: at(cells, 8),
    status: at(cells, 9),
    submitter: at(cells, 10),
    submitTime: at(cells, 11),
    reportTime: at(cells, 12),
  })).filter(r => r.id);
  // 页面没有「N条/页」时，用本页行数兜底
  const pageSize = meta.pageSize || rows.length || 20;
  return { ...meta, pageSize, heads: raw.heads, rows };
}

/** 翻页读取列表全部数据（自动去重） */
export async function readAllListPages(port = 9222, maxPages = 20) {
  const first = await readListPage(port);
  const seen = new Set();
  const all = [];
  const push = (rows) => {
    for (const r of rows) {
      if (!r.id || seen.has(r.id)) continue;
      seen.add(r.id);
      all.push(r);
    }
  };
  push(first.rows);
  const pageCount = first.total && first.pageSize ? Math.ceil(first.total / first.pageSize) : 1;
  for (let p = 2; p <= Math.min(pageCount, maxPages); p++) {
    const clicked = await evaluate(port, `(() => {
      const btns = [...document.querySelectorAll('.el-pager li')].filter(e => /^\\d+$/.test(e.innerText.trim()));
      const b = btns.find(x => x.innerText.trim() === '${p}');
      if (!b) return false;
      b.click();
      return true;
    })()`);
    if (!clicked) break;
    await new Promise(r => setTimeout(r, 2000));
    push((await readListPage(port)).rows);
  }
  return { total: first.total, pageSize: first.pageSize, count: all.length, rows: all };
}

// ---------- 详情页 ----------

/** 按图斑编号打开详情（推荐：比按索引可靠），并校验打开的是目标图斑 */
export async function openDetailById(port = 9222, id) {
  const r = await evaluate(port, `(() => {
    const rows = [...document.querySelectorAll('tr')].filter(tr => tr.innerText.includes('${id}'));
    if (!rows.length) return 'ROW_NOT_FOUND';
    const btns = [...rows[0].querySelectorAll('button,a,span')].filter(e => e.textContent.trim() === '详情');
    if (!btns.length) return 'BTN_NOT_FOUND';
    btns[0].click();
    return 'CLICKED';
  })()`);
  if (r !== 'CLICKED') throw new Error(`打开详情失败：${r}（图斑 ${id} 可能不在当前页）`);
  await new Promise(res => setTimeout(res, 3000));
  return { clicked: r, id: await assertParcel(port, id), url: await evaluate(port, 'location.href') };
}

/** 打开第 index 行（0 基）的详情（保留旧接口，但不做图斑校验） */
export async function openDetail(port = 9222, index = 0) {
  const js = `(() => {
    const btns = [...document.querySelectorAll('button,a,span')]
      .filter(e => e.textContent.trim() === '详情');
    if (btns.length <= ${index}) return 'NOT_FOUND';
    btns[${index}].click();
    return 'CLICKED';
  })()`;
  const r = await evaluate(port, js);
  await new Promise(res => setTimeout(res, 2500));
  return { clicked: r, id: await currentParcelId(port), url: await evaluate(port, 'location.href') };
}

/** 读「核查填报」表单：按 label 就近取值（修坑③④）
 *  坑③：el-select 的值不在 input.value（单选在 input，多选在 .el-select__selected-item）
 *  坑④：不能按位置硬映射——下拉字段有 el-select DIV + input 两个元素，空值会被过滤导致错位
 */
export async function readFillForm(port = 9222) {
  // 先切到「核查填报」tab（该 tab 内容用 v-if 渲染，不切过去读不到）
  await clickByText(port, '核查填报');
  await new Promise(r => setTimeout(r, 2000));
  const js = `(() => {
    const panes = [...document.querySelectorAll('.el-tab-pane')]
      .filter(p => p.offsetParent !== null && p.innerText.includes('核实认定意见'));
    const p = panes[panes.length - 1];
    if (!p) return { error: '未找到核查填报面板（可能不在该 tab）' };
    // 只取叶子 label（自身不含 label 子元素）
    const labels = [...p.querySelectorAll('label, [class*=label]')]
      .filter(e => !e.querySelector('label, [class*=label]'));
    const form = {};
    for (const lab of labels) {
      const name = lab.innerText.replace(/^[*\\s]+/, '').trim().replace(/[\\s:：]/g, '');
      if (!name || name.length > 20 || name in form) continue;
      // 向上找最近的、含输入元素的祖先（最多 5 层）
      let node = lab.parentElement, field = null, depth = 0;
      while (node && depth < 5 && !field) {
        field = node.querySelector('input:not(.el-upload__input), textarea');
        if (!field) { node = node.parentElement; depth++; }
      }
      form[name] = field ? (field.value || '').trim() : '';
    }
    const t = p.innerText;
    const bi = t.indexOf('批文1信息');
    const batchText = bi >= 0 ? t.slice(bi, bi + 300).replace(/\\n+/g, ' | ') : '';
    return { form, batchText };
  })()`;
  const raw = await evaluate(port, js);
  if (raw.error) return raw;
  return { id: await currentParcelId(port), form: raw.form, batchText: raw.batchText };
}

/** 读详情页所有 tab 的文本（读前校验图斑，防漂移） */
export async function readDetailTabs(port = 9222, expectedId = null) {
  await assertParcel(port, expectedId);
  const out = { id: await currentParcelId(port) };
  for (const tab of TAB_NAMES) {
    const r = await clickByText(port, tab);
    if (r === 'NOT_FOUND') continue;
    await new Promise(res => setTimeout(res, 1500));
    out[tab] = await dumpText(port);
  }
  return out;
}

/** 读当前图斑的举证情况（照片数 / 附件 / 套合 / 表单） */
export async function readParcelEvidence(port = 9222, expectedId = null) {
  const id = await assertParcel(port, expectedId);
  // 核查填报（含 el-select）
  const form = await readFillForm(port);
  // 现场照片
  await clickByText(port, '现场照片');
  await new Promise(res => setTimeout(res, 1800));
  const photos = await evaluate(port, `(() => {
    const m = document.body.innerText.match(/共\\s*(\\d+)\\s*个/);
    return m ? Number(m[1]) : 0;
  })()`);
  // 附件资料
  await clickByText(port, '附件资料');
  await new Promise(res => setTimeout(res, 1800));
  const attachments = await evaluate(port, `(() => {
    const t = document.body.innerText;
    if (t.includes('暂未上传附件材料')) return [];
    return t.split('\\n').map(l => l.trim())
      .filter(l => /\\.(pdf|zip|png|jpg|jpeg|docx?|xlsx?)$/i.test(l));
  })()`);
  // 套合结果（注意：系统在此 tab 展示的是父图斑级数据）
  await clickByText(port, '套合结果');
  await new Promise(res => setTimeout(res, 1800));
  const overlayText = await dumpText(port);
  return {
    id, photos, attachments, overlayText,
    form: form.form || {},
    formRaw: form.values || [],
    overlayScope: 'parent', // ⚠️ 系统「套合结果」tab 是父图斑级
  };
}

// ---------- CLI ----------
import { pathToFileURL } from 'node:url';
import { writeFileSync } from 'node:fs';
const isMain = process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href;
if (isMain) {
  const argv = process.argv.slice(2);
  // 支持 --out <file>：直接写文件，绕开 PowerShell 管道编码问题
  const outIdx = argv.indexOf('--out');
  const outFile = outIdx >= 0 ? argv[outIdx + 1] : null;
  const args = outIdx >= 0 ? argv.filter((_, i) => i !== outIdx && i !== outIdx + 1) : argv;
  const [cmd, arg] = args;
  const port = Number(process.env.CDP_PORT || 9222);
  const emit = (obj) => {
    const s = JSON.stringify(obj, null, 2);
    if (outFile) {
      writeFileSync(outFile, s, 'utf8');
      console.log(`written → ${outFile} (${s.length} chars)`);
    } else {
      console.log(s);
    }
  };
  if (cmd === 'list') emit(await readListPage(port));
  else if (cmd === 'list-all') emit(await readAllListPages(port));
  else if (cmd === 'detail') emit(await openDetail(port, Number(arg || 0)));
  else if (cmd === 'open') emit(await openDetailById(port, arg));
  else if (cmd === 'whoami') emit({ id: await currentParcelId(port) });
  else if (cmd === 'form') emit(await readFillForm(port));
  else if (cmd === 'tabs') emit(await readDetailTabs(port));
  else if (cmd === 'evidence') emit(await readParcelEvidence(port));
  else console.log('usage: node system_adapter.mjs <list|list-all|detail [index]|open <id>|whoami|form|tabs|evidence> [--out <file>]');
}
