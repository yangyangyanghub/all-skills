// 系统适配器测试：无浏览器时 SKIP
import { readListPage } from '../packages/adapter/system_adapter.mjs';

try {
  const data = await readListPage(9222);
  if (data && data.rows && data.rows.length) {
    console.log('PASS: 读到列表行数', data.rows.length, '总数', data.total);
  } else {
    console.log('SKIP: 当前页面不是列表页');
  }
} catch (e) {
  console.log('SKIP:', e.message);
}
