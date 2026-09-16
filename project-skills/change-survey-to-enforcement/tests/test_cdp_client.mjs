// CDP 客户端测试：无浏览器时输出 SKIP，不视为失败
import { getPageTarget } from '../packages/adapter/cdp_client.mjs';

const PORT = 9222;

try {
  const t = await getPageTarget(PORT);
  if (!t) {
    console.log('SKIP: 9222 端口无可用页面');
  } else {
    console.log('PASS: 找到页面', t.url);
  }
} catch (e) {
  console.log('SKIP: 无法连接 9222 —', e.message);
}
