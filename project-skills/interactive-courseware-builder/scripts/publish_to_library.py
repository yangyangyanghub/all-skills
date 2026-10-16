#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
一键发布交互式课件到资料库（生成 https://workbuddy.link/p/<node_id>）。

这是「第四代交互式课件」技能的核心发布工具。因技能目录会被 SkillHub 同步覆盖，
本脚本刻意放在课件工作区 scripts/ 下持久化。

修复/固化要点（均来自实战坑）：
  * CLASS_ID 默认 'DEFAULT-CLASS' 自动派生为节点级唯一值 'wb-<node_id>'，
    关闭跨课件答题数据串台（XMN_BASE = 'xmn/'+CLASS_ID+'/answers'）。
  * NODE_ID / PUBLISH_BASE 回写（二维码与 MQTT 同步依赖）。
  * SYNC_TOPIC 是派生式（'xmn-sync/'+(NODE_ID||CLASS_ID)），绝不改写成字面量。
  * 打包自动排除 _backup*/.bak/.md/_docs/.__pycache__ 等中间产物。
  * 发布前备份写系统临时目录，不污染发布根目录。
  * 先 encode 后 open('wb')，避免异常截断源文件。
  * 解析 import_html.py 成功信号 KS_IMPORT_OK（失败也 exit 0，须解析 stdout）。

用法：
  python publish_to_library.py --dir <课件根目录> --token <op_xxx> [--node-id <已存在节点>] [--title <显示名>]
  python publish_to_library.py --dir <...> --dry-run        # 只体检，不联网
  python publish_to_library.py --selftest                   # 自检常量回写逻辑
"""
import argparse
import base64
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile

def _find_library_skill():
    """定位 library 技能目录（发布依赖其 page/import_html.py 与 page/publish_page.py）。
    查找顺序：环境变量 → 内置技能目录 → 用户级技能目录 → 本技能同级目录。"""
    env = os.environ.get('WB_LIBRARY_SKILL_DIR')
    if env and os.path.isdir(env):
        return env
    home = os.path.expanduser('~')
    cands = [
        os.path.join(home, 'AppData', 'Local', 'Programs', 'WorkBuddy', 'resources',
                     'app.asar.unpacked', 'resources', 'plugins', 'workbuddy-builtin',
                     'skills', 'library'),
        os.path.join(home, '.workbuddy', 'skills', 'library'),
        os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                      '..', '..', 'library')),
    ]
    for c in cands:
        if os.path.isdir(c):
            return c
    return None


LIB = _find_library_skill()

EXCLUDE_DIR_PREFIXES = (".", "_backup", "_docs", "__pycache__")
EXCLUDE_SUFFIXES = (".zip", ".bak", ".pyc")

NODE_RE = re.compile(r"var\s+NODE_ID\s*=\s*'([^']*)'")
PUBLISH_RE = re.compile(r"var\s+PUBLISH_BASE\s*=\s*'([^']*)'")
# 旧写法：捕获 "var CLASS_ID = <表达式> || 'DEFAULT-CLASS'" 中的整段，便于派生
CLASS_RE = re.compile(r"(var\s+CLASS_ID\s*=\s*.+?)\|\|\s*'DEFAULT-CLASS'", re.S)
# 新写法兼容：CLASS_ID 已是派生式（'wb-' + NODE_ID）或其它形态时，整行重写为显式字面量 'wb-<node_id>'，
# 使其不依赖运行期 NODE_ID 变量（更稳）。模板自 2026-09-29 起默认产出新写法，故必须兼容。
CLASS_ANY_RE = re.compile(r"var\s+CLASS_ID\s*=\s*[^\n;]+;")
# SYNC_TOPIC 派生式：只动 NODE_ID/PUBLISH_BASE，不动它
SYNC_RE = re.compile(r"var\s+SYNC_TOPIC\s*=")


def patch_constants(src, node_id):
    """回写 NODE_ID / PUBLISH_BASE；把 DEFAULT-CLASS 派生为 wb-<node_id>。返回 (新源码, 改动列表)。"""
    changed = []
    m = NODE_RE.search(src)
    if m and m.group(1) != node_id:
        src = NODE_RE.sub("var NODE_ID = '%s'" % node_id, src, count=1)
        changed.append("NODE_ID")

    pm = PUBLISH_RE.search(src)
    want_pub = "https://workbuddy.link/p/%s" % node_id
    if pm and pm.group(1) != want_pub:
        src = PUBLISH_RE.sub("var PUBLISH_BASE = '%s'" % want_pub, src, count=1)
        changed.append("PUBLISH_BASE")

    cm = CLASS_RE.search(src)
    if cm:
        derived = "var CLASS_ID = getPageParam('class') || 'wb-%s'" % node_id
        src = CLASS_RE.sub(derived, src, count=1)
        changed.append("CLASS_ID(DEFAULT-CLASS->wb-)")
    else:
        # 新写法：已是派生式（'wb-' + NODE_ID）→ 显式化为 'wb-<node_id>' 字面量（幂等：已显式则跳过）
        am = CLASS_ANY_RE.search(src)
        if am and 'wb-' in am.group(0) and ("'wb-%s'" % node_id) not in am.group(0):
            derived = "var CLASS_ID = getPageParam('class') || 'wb-%s';" % node_id
            src = src[:am.start()] + derived + src[am.end():]
            changed.append("CLASS_ID(derive->literal)")

    return src, changed


def build_zip(root, zip_path):
    if os.path.exists(zip_path):
        os.remove(zip_path)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for dp, dns, fns in os.walk(root):
            dns[:] = [d for d in dns if not d.startswith(EXCLUDE_DIR_PREFIXES)]
            for fn in fns:
                fp = os.path.join(dp, fn)
                if fn.lower().endswith(EXCLUDE_SUFFIXES):
                    continue
                rel_parts = os.path.relpath(fp, root).split(os.sep)
                if any(seg.startswith(EXCLUDE_DIR_PREFIXES) for seg in rel_parts):
                    continue
                z.write(fp, os.path.relpath(fp, root))
    return os.path.getsize(zip_path)


def run_capture(cmd, token):
    return subprocess.run(cmd, input=(token + "\n"), capture_output=True, text=True)


# ⚠ 2026-10-02 实测坑（孟德尔课件）：后端把 .zip 分流到网盘上传后，本脚本回退「单文件 index.html 导入」，
#   而单文件导入【只上传 HTML 本身】，img/ 目录不会随包上传 → 线上所有图片 404
#   （playwright 实测：9 张配图全部 404、naturalWidth=0）。
#   故回退时必须用「图片已内联为 data URI 的自包含 HTML」，保证单文件即可完整呈现。
_MIME_BY_EXT = {
    '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png',
    '.gif': 'image/gif', '.webp': 'image/webp', '.svg': 'image/svg+xml', '.bmp': 'image/bmp',
}
_IMG_SRC_RE = re.compile(r'(<img\b[^>]*?\ssrc\s*=\s*")([^"]+)(")', re.I)
_CSS_URL_RE = re.compile(r'(url\(\s*[\'"]?)([^\'")]+)([\'"]?\s*\))')


def _as_data_uri(root, ref):
    if not ref or ref.startswith(('data:', 'http://', 'https://', '//', '#')):
        return None
    ref_wo_q = ref.split('?')[0]
    fp = os.path.join(root, ref_wo_q.replace('/', os.sep))
    if not os.path.isfile(fp):
        return None
    mime = _MIME_BY_EXT.get(os.path.splitext(fp)[1].lower())
    if not mime:
        return None
    with open(fp, 'rb') as fh:
        return 'data:%s;base64,%s' % (mime, base64.b64encode(fh.read()).decode('ascii'))


def inline_images(src_html, root, out_html=None):
    """把 HTML 内指向本地相对路径的图片（<img src> 与 CSS url()）内联为 data URI，产出自包含单文件。"""
    with open(src_html, 'rb') as fh:
        text = fh.read().decode('utf-8')
    n = {'img': 0, 'css': 0}

    def r_img(m):
        uri = _as_data_uri(root, m.group(2))
        if not uri:
            return m.group(0)
        n['img'] += 1
        return m.group(1) + uri + m.group(3)

    def r_css(m):
        uri = _as_data_uri(root, m.group(2))
        if not uri:
            return m.group(0)
        n['css'] += 1
        return m.group(1) + uri + m.group(3)

    text = _IMG_SRC_RE.sub(r_img, text)
    text = _CSS_URL_RE.sub(r_css, text)
    out = out_html or os.path.join(tempfile.gettempdir(),
                                   'cw_publish_inlined_%s.html' % os.path.basename(root))
    with open(out, 'wb') as fh:
        fh.write(text.encode('utf-8'))
    return out, n


def publish(dir_path, token, node_id=None, title=None, dry_run=False):
    root = os.path.abspath(dir_path)
    html_path = os.path.join(root, "index.html")
    if not os.path.isfile(html_path):
        print("[ERR] 发布目录缺少 index.html：", html_path)
        return 2
    title = title or (os.path.basename(root) + ".html")

    src = io.open(html_path, encoding="utf-8").read()
    # 体检：是否含中间产物目录
    bad = [d for d in os.listdir(root)
           if os.path.isdir(os.path.join(root, d)) and d.startswith(("_backup", "_docs"))]
    if bad:
        print("[WARN] 发布目录含中间产物目录（将自动排除）：", bad)

    if dry_run:
        print("[DRY-RUN] 发布目录：", root)
        print("[DRY-RUN] index.html 字节数：", len(src.encode("utf-8")))
        print("[DRY-RUN] 若提供 --node-id 将覆盖同节点；否则新建节点。")
        print("[DRY-RUN] 常量回写预览：", patch_constants(src, node_id or "NODE_PLACEHOLDER")[1])
        print("[DRY-RUN] 未联网，结束。")
        return 0

    # 1) 写回常量（先编码后写盘，避免截断）
    new_src, changed = patch_constants(src, node_id) if node_id else (src, [])
    if node_id and changed:
        data = new_src.encode("utf-8")
        backup = os.path.join(tempfile.gettempdir(),
                              "cw_publish_bak_%s.html" % os.path.basename(root))
        try:
            shutil.copy2(html_path, backup)
        except Exception:
            pass
        with open(html_path, "wb") as fh:
            fh.write(data)
        print("[OK] 常量回写：", changed, "（备份→", backup, "）")

    def _import_once(src_path, node, file_name=None):
        argv = [sys.executable, os.path.join(LIB, "page", "import_html.py"), src_path]
        if file_name:
            argv += ["--file-name", file_name]
        if node:
            argv += ["--node-block-id", node]
        argv += ["--token-stdin"]
        return run_capture(argv, token)

    # 2026-10-02 提速：后端把 .zip 分流为网盘上传，import_html.py 必失败，
    # 回退恒为单文件。故先探测 index.html 是否引用本地图片/CSS 资源：
    #   无本地资源 → 直接内联单文件导入（省一次注定失败的网络往返）；
    #   有本地资源 → 仍先试 zip（img/ 随包上传），失败再回退内联单文件。
    def _has_local_assets(s):
        for m in _IMG_SRC_RE.finditer(s):
            if _as_data_uri(root, m.group(2)) is not None:
                return True
        for m in _CSS_URL_RE.finditer(s):
            if _as_data_uri(root, m.group(2)) is not None:
                return True
        return False

    final_src = new_src if (node_id and changed) else src
    if not _has_local_assets(final_src):
        print("[OK] 无本地图片引用 → 跳过 zip 尝试，直接单文件导入")
        inlined, n_img = inline_images(html_path, root)
        print("[OK] 自包含单文件（<img> %d 张 / CSS url %d 处，%s 字节）"
              % (n_img['img'], n_img['css'], os.path.getsize(inlined)))
        p = _import_once(inlined, node_id)
    else:
        zip_path = os.path.join(tempfile.gettempdir(),
                                "cw_publish_%s.zip" % os.path.basename(root))
        zb = build_zip(root, zip_path)
        print("[OK] 打包 zip 字节数：", zb)
        p = _import_once(zip_path, node_id)
        if "KS_IMPORT_OK" not in p.stdout and "缺少 uploadUrl 或 cosKey" in p.stdout:
            print("[WARN] zip 路线被后端分流为网盘上传（import_html.py 不支持）→ 自动回退单文件 .html 导入")
            inlined, n_img = inline_images(html_path, root)
            print("[OK] 已内联本地图片 → 自包含单文件（<img> %d 张 / CSS url %d 处，%s 字节）"
                  % (n_img['img'], n_img['css'], os.path.getsize(inlined)))
            p = _import_once(inlined, node_id)
    print("IMPORT:", p.stdout.strip()[-500:])
    if "KS_IMPORT_OK" not in p.stdout:
        print("[ERR] 导入失败：", p.stderr.strip()[-300:])
        return 3
    if not node_id:
        m = re.search(r'"node_block_id"\s*:\s*"([^"]+)"', p.stdout)
        node_id = m.group(1) if m else None
        if not node_id:
            print("[ERR] 未能从返回结果解析 node_block_id")
            return 3
        print("[OK] 新建节点：", node_id)
    else:
        print("[OK] 覆盖节点：", node_id)

    # 4) 发布
    q = run_capture([sys.executable, os.path.join(LIB, "page", "publish_page.py"),
                     "--token-stdin", "--node-id", node_id], token)
    print("PUBLISH:", q.stdout.strip()[-400:])
    if q.returncode != 0 and '"code":0' not in q.stdout:
        print("[ERR] 发布失败：", q.stderr.strip()[-300:])
        return 4

    print("\n==== 发布完成 ====")
    print("链接：https://workbuddy.link/p/%s" % node_id)
    print("教师控制端：进入 https://workbuddy.link/p/%s 后，在底部页码指示器（如 1/13）处 1.5 秒内连点 3 次切教师模式。" % node_id)
    print("  （⛔ 勿对外发带 URL 参数形式的链接：资料库外壳 iframe 会剥离 query，壳内必失效；教师入口只能是连点底部页码三次。）")
    return 0


def selftest():
    html = (
        "<!doctype html><html><head><script>\n"
        "var NODE_ID = '';\n"
        "var PUBLISH_BASE = '';\n"
        "var SYNC_TOPIC = 'xmn-sync/' + (NODE_ID || CLASS_ID);\n"
        "var CLASS_ID = getPageParam('class') || 'DEFAULT-CLASS';\n"
        "var XMN_BASE = 'xmn/'+CLASS_ID+'/answers';\n"
        "</script></head><body></body></html>\n"
    )
    node_id = "TESTNODE123"
    new, changed = patch_constants(html, node_id)
    assert sorted(changed) == ["CLASS_ID(DEFAULT-CLASS->wb-)", "NODE_ID", "PUBLISH_BASE"], changed
    assert "var NODE_ID = 'TESTNODE123'" in new
    assert "var PUBLISH_BASE = 'https://workbuddy.link/p/TESTNODE123'" in new
    assert "var CLASS_ID = getPageParam('class') || 'wb-TESTNODE123'" in new
    # SYNC_TOPIC 派生式必须保留
    assert "var SYNC_TOPIC = 'xmn-sync/' + (NODE_ID || CLASS_ID)" in new, "SYNC_TOPIC 派生式被破坏"
    # XMN_BASE 不被误改
    assert "var XMN_BASE = 'xmn/'+CLASS_ID+'/answers'" in new
    # 已填写则不重复改
    html2 = html.replace("var NODE_ID = '';", "var NODE_ID = 'TESTNODE123';")
    new2, changed2 = patch_constants(html2, node_id)
    assert "NODE_ID" not in changed2

    # 新写法（2026-09-29 起模板/骨架默认产出）：CLASS_ID 已是派生式 → 必须显式化为字面量
    html3 = (
        "<!doctype html><html><head><script>\n"
        "var NODE_ID = '';\n"
        "var PUBLISH_BASE = '';\n"
        "var SYNC_TOPIC = 'xmn-sync/' + (NODE_ID || CLASS_ID);\n"
        "var CLASS_ID = (typeof getPageParam === 'function' ? getPageParam('class') : null) "
        "|| ('wb-' + ((typeof NODE_ID !== 'undefined') ? NODE_ID : ''));\n"
        "var XMN_BASE = 'xmn/'+CLASS_ID+'/answers';\n"
        "</script></head><body></body></html>\n"
    )
    new3, changed3 = patch_constants(html3, node_id)
    assert "CLASS_ID(derive->literal)" in changed3, changed3
    assert "var CLASS_ID = getPageParam('class') || 'wb-TESTNODE123';" in new3, new3
    # 幂等：再跑一次不再改 CLASS_ID
    new3b, changed3b = patch_constants(new3, node_id)
    assert "CLASS_ID(derive->literal)" not in changed3b, changed3b
    assert "var CLASS_ID = getPageParam('class') || 'wb-TESTNODE123';" in new3b
    print("[SELFTEST] PASS — 常量回写 + CLASS_ID 派生（旧 DEFAULT-CLASS / 新派生式 双写法） + SYNC_TOPIC 派生式守卫 全部通过")
    return 0


def main():
    ap = argparse.ArgumentParser(description="一键发布交互式课件到资料库（workbuddy.link/p/<id>）")
    ap.add_argument("--dir", help="发布目录（根部含 index.html）")
    ap.add_argument("--token", help="资料库 open platform token（op_ 开头）")
    ap.add_argument("--node-id", help="已存在的发布节点 id（覆盖更新，链接不变）")
    ap.add_argument("--title", help="资料库显示名（默认用目录名）")
    ap.add_argument("--dry-run", action="store_true", help="只体检，不联网")
    ap.add_argument("--selftest", action="store_true", help="自检常量回写逻辑")
    args = ap.parse_args()

    if args.selftest:
        return selftest()
    if not args.dir:
        ap.error("缺少 --dir")
    if not args.dry_run and not args.token:
        ap.error("非 dry-run 必须提供 --token")
    if LIB is None:
        print("[ERR] 未找到 library 技能目录（发布依赖其 page/import_html.py 与 page/publish_page.py）。")
        print("      请设置环境变量 WB_LIBRARY_SKILL_DIR 指向 library 技能目录后重试。")
        return 5

    return publish(args.dir, args.token, args.node_id, args.title, args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
