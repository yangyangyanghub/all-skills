# -*- coding: utf-8 -*-
"""
audit_skill_self.py —— 技能自身的严格自审（母技能 · MQTT 路线版）
=====================================================================
改完 SKILL.md / 模板 / 脚本后跑一遍，防止技能「表面完整、内里退化」。
与云变体同名脚本互不通用：本脚本按【MQTT 路线】规约判定（云版按云数据库路线，两者规约相反）。

解决的问题（都是真实踩过的）：
  · 新加的脚本没登记进 SKILL.md → 下次没人知道它存在（2026-09-28 技能被 SkillHub 覆盖即此类事故）
  · TOC 断链 / 重复锚点（复制粘贴遗留；2026-09-29 修过 4 处 CJK 锚点断链）
  · 文档旧数字没跟更新（写「31 项」而实际不符）
  · 「模板引用了 showToast/showConfirmModal 却没人定义」类悬空依赖（2026-09-29 修）
  · 模板里的裸 scrollIntoView / 原生 confirm/alert 回归（2026-09-29 修，本脚本设为回归项）
  · 正则搜「是否实现了 X」被注释命中 → 假 PASS（故一律「限定代码块 + 剥注释」）

用法
----
  python scripts/audit_skill_self.py
  python scripts/audit_skill_self.py --courseware <课件.html> [更多...]   # 顺带跑教学控制回归
  python scripts/audit_skill_self.py --node "C:/path/to/node.exe"

退出码: 0=全过, 1=有 FAIL
"""

import argparse
import io
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)

FAILS = []


def rd(p):
    return io.open(p, encoding='utf-8').read()


def ck(name, ok, detail=''):
    print('  [%s] %s%s' % ('PASS' if ok else 'FAIL', name,
                           ('  -> ' + str(detail)[:180]) if detail else ''))
    if not ok:
        FAILS.append(name)


def strip_line_comments(code):
    """去掉块注释与行内注释，保留 URL 里的 `//`（其前是 ':'）。
    这是「排除注释命中」的关键——注释里写着某实现不代表真实现了。"""
    code = re.sub(r'/\*.*?\*/', '', code, flags=re.S)
    return re.sub(r'(?<![:\'"`])//[^\n]*', '', code)


def gh_anchor(text):
    """GitHub 风格标题锚点。"""
    t = re.sub(r'<a id="[^"]*"></a>', '', text).strip().lower()
    t = re.sub(r'[^\w\u4e00-\u9fff \-]', '', t)
    return t.replace(' ', '-')


def find_node(explicit):
    if explicit:
        return explicit
    env = os.environ.get('NODE_BIN')
    if env and os.path.exists(env):
        return env
    w = shutil.which('node')
    if w:
        return w
    # 兜底：扫描 WorkBuddy 托管 Node 目录（任意版本），不硬编码个人路径
    _wb_node_dir = os.path.join(os.path.expanduser('~'), '.workbuddy', 'binaries', 'node', 'versions')
    if os.path.isdir(_wb_node_dir):
        for ver in sorted(os.listdir(_wb_node_dir), reverse=True):
            for name in ('node.exe', 'node'):
                p = os.path.join(_wb_node_dir, ver, name)
                if os.path.exists(p):
                    return p
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--courseware', nargs='*', default=[],
                    help='顺带对已构建课件跑教学控制回归（page-sync 行为级）')
    ap.add_argument('--node', default=None)
    a = ap.parse_args()

    readme = os.path.join(SKILL, 'SKILL.md')
    if not os.path.exists(readme):
        print('未找到 SKILL.md:', readme)
        return 2
    S = rd(readme)
    S_nc = strip_line_comments(S)
    # v1.4.0 起知识外迁 references/*.md（渐进披露重构）——文档内容类检查改查全集
    DOC = S
    _refdir = os.path.join(SKILL, 'references')
    if os.path.isdir(_refdir):
        for _f in sorted(os.listdir(_refdir)):
            if _f.endswith('.md'):
                DOC += '\n' + rd(os.path.join(_refdir, _f))
    node = find_node(a.node)
    print('技能目录:', SKILL)
    print('node    :', node or '（未找到，跳过 JS 语法检查）')

    # ---------------- A. 文件引用完整性 ----------------
    print('\n' + '=' * 72 + '\nA. SKILL.md 引用的路径是否都存在\n' + '=' * 72)
    refs = set(re.findall(r'`((?:references|scripts)/[\w\-./]+)`', S))
    for m in re.finditer(r'\[([^\]]+)\]\(((?:references|scripts)/[^)]+)\)', S):
        refs.add(m.group(2))
    missing = [r for r in sorted(refs)
               if r.rstrip('/') and not os.path.exists(os.path.join(SKILL, r.replace('/', os.sep)))]
    ck('引用的 %d 个路径全部存在' % len(refs), not missing, missing)

    # ---------------- B. 新文件是否登记 ----------------
    print('\n' + '=' * 72 + '\nB. 目录下每个文件都在 SKILL.md 登记\n' + '=' * 72)
    undoc = []
    for sub in ('scripts', 'references/templates', 'references'):
        d = os.path.join(SKILL, sub)
        if not os.path.isdir(d):
            continue
        for f in sorted(os.listdir(d)):
            fp = os.path.join(d, f)
            if f == '__pycache__' or not os.path.isfile(fp):
                continue
            if f not in DOC:
                undoc.append('%s/%s' % (sub, f))
    ck('scripts/ + references/ 全部已登记', not undoc, undoc)

    # ---------------- C. 脚本可编译 ----------------
    print('\n' + '=' * 72 + '\nC. 脚本编译 / 语法\n' + '=' * 72)
    bad = []
    for sub in ('scripts', 'references/templates'):
        d = os.path.join(SKILL, sub)
        if not os.path.isdir(d):
            continue
        for f in sorted(os.listdir(d)):
            fp = os.path.join(d, f)
            if not os.path.isfile(fp):
                continue
            if f.endswith('.py'):
                # 用 ast.parse 校验（不写 __pycache__，避免自审自身制造构建残留）
                r = subprocess.run(
                    [sys.executable, '-c',
                     'import ast,sys; ast.parse(open(sys.argv[1],encoding="utf-8").read())', fp],
                    capture_output=True)
                if r.returncode:
                    bad.append('%s/%s (py)' % (sub, f))
            elif f.endswith('.js') and node:
                r = subprocess.run([node, '--check', fp], capture_output=True)
                if r.returncode:
                    bad.append('%s/%s (js)' % (sub, f))
    ck('全部 .py / .js 通过编译与语法检查', not bad, bad)

    # ---------------- D. 关键实现「真实存在」（MQTT 路线 · 排除注释） ----------------
    print('\n' + '=' * 72 + '\nD. 关键实现的真实存在性（MQTT 路线 · 排除注释）\n' + '=' * 72)
    T = os.path.join(SKILL, 'references/templates')

    # D1 mqtt-framework.js：确定性选 broker + 内置 UI 反馈 + xmnClear 走模态确认
    mf_p = os.path.join(T, 'mqtt-framework.js')
    if os.path.exists(mf_p):
        mf = rd(mf_p)
        mf_nc = strip_line_comments(mf)
        ck('mqtt-broker 多源 + 确定性哈希（xmnBrokerHash）',
           'MQTT_BROKERS' in mf_nc and 'xmnBrokerHash' in mf_nc)
        ck('内置 showToast + showConfirmModal（UI 反馈标准件）',
           'function showToast' in mf_nc and 'function showConfirmModal' in mf_nc)
        ck('xmnClear 优先 showConfirmModal（typeof 守卫，勿裸 confirm）',
           'typeof showConfirmModal' in mf_nc and 'xmnClearDo' in mf_nc)

    # D2 teaching-control.js：单广播者 + 学生纯跟随闸门
    tc_p = os.path.join(T, 'teaching-control.js')
    if os.path.exists(tc_p):
        tc = strip_line_comments(rd(tc_p))
        for fn in ('startBroadcast', 'stopBroadcast', 'canStudentNavigate', 'publishClaim'):
            ck('teaching-control 含 %s' % fn, ('function ' + fn) in tc)
        # D2b 控制端唯一：onClaim 租约仲裁在位（在位者优先；本地时间判定，不跨设备比 ts，规避时钟漂移）
        #     ⛔ 旧设计「最新 ts 恒赢」在两端各 2s 心跳下必然心跳级易主 → 学生端确定性闪跳（2026-10-12 定案废弃）
        ck('teaching-control 含租约仲裁 onClaim（在位者优先 / CLAIM_TTL）',
           ('function ' + 'onClaim') in tc
           and re.search(r'Date\.now\(\)\s*-\s*activeClaimTs\s*<=\s*CLAIM_TTL', tc) is not None
           and 'xmnDowngradeToObserver' in tc)
        m_req = re.search(r"var\s+(\w+)\s*=\s*JSON\.parse\(raw\)[\s\S]{0,600}?\1\.req\s*===\s*'page'", tc)
        ck('teaching-control 学生 req 分支使用同一声明变量', m_req is not None)
        # D2c 全屏三件套已抽离为 opt-in（与「默认不启用」定案一致）
        ck('teaching-control.js 不含活的全屏三件套（已抽离 opt-in）',
           'fullscreenBtn' not in tc and 'requestFullscreen' not in tc)
        ck('fullscreen-fallback.js 存在（按需复制）',
           os.path.exists(os.path.join(T, 'fullscreen-fallback.js')))

    # D3 page-flip-system.js：scrollIntoView 必须带 typeof 保护（缺则初始化中断，脚本后半段全不执行）
    pf_p = os.path.join(T, 'page-flip-system.js')
    if os.path.exists(pf_p):
        pf = strip_line_comments(rd(pf_p))
        ck('scrollIntoView 带 typeof 保护（防初始化中断回归）',
           'typeof activeChip.scrollIntoView' in pf or
           re.search(r'typeof\s+\w+\.scrollIntoView', pf) is not None)

    # D4 unified-quiz-submit.js：未答提示不得用裸 alert
    uq_p = os.path.join(T, 'unified-quiz-submit.js')
    if os.path.exists(uq_p):
        uq = strip_line_comments(rd(uq_p))
        i = uq.find('hasUnanswered')
        seg = uq[i:i + 260] if i >= 0 else ''
        # 要求「以 showToast 为主」（typeof 守卫）；else 分支里的 alert 是合法兜底，不算违规
        ck('未答提示以 showToast 为主（typeof 守卫，alert 仅兜底）',
           'showToast' in seg and 'typeof showToast' in seg)

    # D5 反向一致性：母技能模板/脚本不得含云数据库运行时代码（与云变体规约相反）
    cloud_runtime = re.compile(r'doUpsert|CLOUD_ORIGINS|cloudClient|workbuddy[_-]cloud|from\s+[\'"].*cloud', re.I)
    hit = []
    for sub in ('scripts', 'references/templates'):
        d = os.path.join(SKILL, sub)
        for f in sorted(os.listdir(d)) if os.path.isdir(d) else []:
            fp = os.path.join(d, f)
            # 跳过本脚本自身：其源码内含检测用的模式串，会自匹配
            if os.path.isfile(fp) and f.endswith(('.js', '.py')) and f != 'audit_skill_self.py':
                if cloud_runtime.search(strip_line_comments(rd(fp))):
                    hit.append('%s/%s' % (sub, f))
    ck('母技能内无云数据库运行时代码（勿被云变体污染）', not hit, hit)

    # ---------------- D6. 2026-09-29 二轮审计修复点（防回归） ----------------
    print('\n' + '=' * 72 + '\nD6. 二轮审计修复点（URL 解析统一 / 全屏三件套 / 索引兼容）\n' + '=' * 72)
    if os.path.exists(pf_p):
        pf_nc2 = strip_line_comments(rd(pf_p))
        ck('page-flip-system.js 定义 getPageParam（URL 参数唯一入口）',
           'function getPageParam' in pf_nc2)
        ck('page-flip-system.js 无 URLSearchParams 直读（外壳剥离 query 即失效）',
           'URLSearchParams' not in pf_nc2)
        ck("page-flip-system.js 初始跳页走 getPageParam('page')",
           "getPageParam('page')" in pf_nc2)
    if os.path.exists(mf_p):
        # 2026-10-02 收紧：不再剥注释——注释里的 DEFAULT-CLASS 字面量同样会
        # 被 verify-library-online.js 全文件 grep 判 FAIL（详见 pitfalls.md）。
        ck('mqtt-framework.js 全文件（含注释）无 DEFAULT-CLASS 字面量',
           'DEFAULT-CLASS' not in rd(mf_p))
    if os.path.exists(tc_p):
        tc_nc2 = strip_line_comments(rd(tc_p))
        ck('teaching-control.js 当前页索引兼容取值（xmnCurIndex 优先，无裸 PAGE_IDS[curPage]）',
           'xmnCurIndex' in tc_nc2 and 'PAGE_IDS[curPage]' not in tc_nc2)
    sk_p = os.path.join(T, 'courseware-skeleton.html')
    if os.path.exists(sk_p):
        ck('骨架无全屏三件套 fullscreenBtn（v2026-09-28e 定案）',
           'fullscreenBtn' not in rd(sk_p))
    pub_p2 = os.path.join(HERE, 'publish_to_library.py')
    if os.path.exists(pub_p2):
        ck('publish_to_library.py 兼容 CLASS_ID 新派生式写法（CLASS_ANY_RE）',
           'CLASS_ANY_RE' in rd(pub_p2))

    # ---------------- D7. 答题可改与导航条居中定案（v2026-09-29，防模板覆盖回退） ----------------
    # 依据 §4.6：提交前可随时修改（单选改选/多选重选重确认），提交后锁定（防刷分）
    print('\n' + '=' * 72 + '\nD7. 答题可改定案（提交前可改 / 提交后锁，防模板回退）\n' + '=' * 72)
    qe_p = os.path.join(T, 'quiz-engine.js')
    if os.path.exists(qe_p):
        qe_nc = strip_line_comments(rd(qe_p))
        ck('quiz-engine.js 单选闸门为 _submitted（无 _chosen[qi]>=0 旧锁）',
           re.search(r'if\s*\(\s*container\._submitted\s*\)\s*return;', qe_nc) is not None
           and re.search(r'_chosen\[qi\]\s*>=\s*0\s*\)\s*return', qe_nc) is None)
        ck('quiz-engine.js 多选闸门为 _submitted（无 !==null 旧锁）',
           re.search(r'if\s*\(\s*container\._submitted\s*\)\s*return;', qe_nc) is not None
           and re.search(r'_chosen\[qi\]\s*!==\s*null\s*\)\s*return', qe_nc) is None)
        ck('quiz-engine.js 确认按钮隐藏挂 submitted 前缀（L4：answered 隐藏=多选确认后无法重确认）',
           '.quiz-q.submitted .opt-confirm{display:none}' in qe_nc
           and '.quiz-q.answered .opt-confirm{display:none}' not in qe_nc)
    if os.path.exists(uq_p):
        uq_nc = strip_line_comments(rd(uq_p))
        ck('unified-quiz-submit.js submitQuiz 补 submitted 类（L5 承接 CSS 锁）',
           "qq.classList.add('submitted')" in uq_nc)
    if os.path.exists(sk_p):
        sk_nc = strip_line_comments(rd(sk_p))
        ck('skeleton 选项 CSS 锁挂 submitted 前缀（L3）',
           '.quiz-q.submitted .opt{pointer-events:none' in sk_nc
           and '.quiz-q.answered .opt{pointer-events:none' not in sk_nc)
        ck('skeleton #navBtns 定位属性 !important 加固（L6 底部居中防挤占）',
           'position:fixed !important' in sk_nc and 'left:50% !important' in sk_nc)

    # ---------------- D9. 2026-09-29 线上实测修复点（防回归） ----------------
    # 依据：认知负荷理论课件三连坑——QR 基址被带成 www 域 / connect 漏订 SYNC 主题 / 骨架缺伪全屏兜底 CSS。
    # 这三处当年都「文档写了、模板没落地」，故一律设为回归项。
    print('\n' + '=' * 72 + '\nD9. 线上实测修复点（QR 基址 / SYNC 订阅 / 骨架伪全屏兜底）\n' + '=' * 72)
    # D9a 骨架必须含三条伪全屏兜底 CSS（缺 → 照骨架生成的课件必踩 pagesync S7 FAIL）
    if os.path.exists(sk_p):
        sk_d9 = rd(sk_p)
        ck('骨架含伪全屏兜底 body.fs-pseudo #topNav{z-index:10001',
           'body.fs-pseudo #topNav{z-index:10001' in sk_d9)
        ck('骨架含伪全屏兜底 #pageContainer + #navBtns 两条',
           'body.fs-pseudo #pageContainer' in sk_d9 and 'body.fs-pseudo #navBtns' in sk_d9)
    # D9b qr-badge-injection.js 必须走 getQrBase() + hash 传参，不得残留旧坏码写法
    qr_p = os.path.join(T, 'qr-badge-injection.js')
    if os.path.exists(qr_p):
        qr_nc = strip_line_comments(rd(qr_p))
        ck('qr-badge 定义 getQrBase()（PUBLISH_BASE 优先，srcdoc/file 不生成坏码）',
           'function getQrBase' in qr_nc)
        ck("qr-badge 用 hash 传参 qrBase + '#page='（非 ?query）",
           "qrBase + '#page='" in qr_nc)
        ck("qr-badge 无旧坏码 location.origin + location.pathname + '?page='",
           "location.origin + location.pathname + '?page='" not in qr_nc)
        ck('qr-badge qrBase 空值守卫（toast 提示先发布）', '请先发布课件' in qr_nc)
    # D9c mqtt-framework.js 必须订阅页码广播与 claim 主题（漏订 → 学生永久停首页）
    if os.path.exists(mf_p):
        mf_d9 = strip_line_comments(rd(mf_p))
        ck('mqtt-framework 订阅 SYNC_TOPIC（页码广播；漏订=学生停首页）',
           re.search(r'subscribe\(\s*SYNC_TOPIC', mf_d9) is not None)
        ck('mqtt-framework 订阅 SYNC_CTL_TOPIC（claim 仲裁）',
           re.search(r'subscribe\(\s*SYNC_CTL_TOPIC', mf_d9) is not None)
    # D9d pagesync-test-mqtt.js 的 S2 必须强断言真实 subscribe 调用（旧版只查字符串 = 漏订仍 PASS 的盲区）
    pst_src_p = os.path.join(HERE, 'pagesync-test-mqtt.js')
    if os.path.exists(pst_src_p):
        pst_src = rd(pst_src_p)
        ck('pagesync S2 强断言真实 subscribe(SYNC_TOPIC) 调用',
           re.search(r'subscribe.{0,12}SYNC_TOPIC', pst_src) is not None)
        ck('pagesync S2 强断言真实 subscribe(SYNC_CTL_TOPIC) 调用',
           re.search(r'subscribe.{0,12}SYNC_CTL_TOPIC', pst_src) is not None)
    # D9e SKILL.md 坑表登记「漏订阅」+ 4A.6 QR 行改 hash（防文档回退到旧 query 写法）
    ck('文档坑表登记「connect 回调漏订阅 SYNC_TOPIC」',
       'connect 回调漏订阅' in DOC)
    ck('文档 4A.6 QR 行用 hash 传参（无旧 ?page=pN 写法）',
       "PUBLISH_BASE + '#page=pN" in DOC and '?page=pN&class=CLASS_ID`' not in DOC)
    # D9f 线上跟随实测脚本存在且带看门狗 + 硬断言（防挂起 / 防断言退化）
    el_p = os.path.join(HERE, 'sync-e2e-live.js')
    ck('scripts/sync-e2e-live.js 存在', os.path.exists(el_p))
    if os.path.exists(el_p):
        el = rd(el_p)
        ck('sync-e2e-live.js 带看门狗（防 playwright/broker 挂起）', 'WATCHDOG' in el)
        ck('sync-e2e-live.js 硬断言 syncReceived + 订阅日志核查',
           'syncReceived' in el and '已订阅' in el)

    # D9g 线上发布态核验脚本存在 + 防挂死三件套 + §5 登记（防回归到 curl 直拉拿不到真身）
    vlo_p = os.path.join(HERE, 'verify-library-online.js')
    ck('scripts/verify-library-online.js 存在', os.path.exists(vlo_p))
    if os.path.exists(vlo_p):
        vlo = rd(vlo_p)
        ck('verify-library-online.js 防挂死：goto 用 commit（外壳 DCL 永久挂起）',
           "waitUntil: 'commit'" in vlo)
        ck('verify-library-online.js 防挂死：看门狗强杀浏览器进程',
           'WATCHDOG' in vlo and 'browser.process' in vlo)
        ck('verify-library-online.js 同步落日志（fs.writeSync，防 SIGTERM 丢输出）',
           'writeSync' in vlo)
        ck('verify-library-online.js 内置通用标记（SYNC_CTL_TOPIC 订阅 + 旧式 URL 直读归零）',
           'subscribe(SYNC_CTL_TOPIC' in vlo and 'new URLSearchParams' in vlo)
    ck('SKILL.md §5 工具链登记 verify-library-online.js',
       'verify-library-online.js' in S)

    # ---------------- E. 关键脚本可运行 ----------------
    print('\n' + '=' * 72 + '\nE. 关键脚本可运行\n' + '=' * 72)
    pub = os.path.join(HERE, 'publish_to_library.py')
    if os.path.exists(pub):
        r = subprocess.run([sys.executable, pub, '--selftest'], capture_output=True)
        out = (r.stdout + r.stderr).decode('utf-8', 'replace')
        ck('publish_to_library.py --selftest PASS', 'PASS' in out and r.returncode == 0,
           out.strip().split('\n')[-1] if out.strip() else '')

    qup = os.path.join(HERE, 'quiz-unlock-patch.py')
    if os.path.exists(qup):
        r = subprocess.run([sys.executable, qup, '--selftest'], capture_output=True)
        out = (r.stdout + r.stderr).decode('utf-8', 'replace')
        ck('quiz-unlock-patch.py --selftest PASS（含反测用例）',
           'ALL PASS' in out and r.returncode == 0,
           out.strip().split('\n')[-1] if out.strip() else '')

    # D8 孤儿 CSS 工具（2026-09-29 大模型课件：孤儿声明块吞掉 #navBtns 规则 → 翻页条挤左下）
    ocf = os.path.join(HERE, 'orphan-css-fix.py')
    ck('orphan-css-fix.py 存在', os.path.exists(ocf))
    if os.path.exists(ocf):
        src = rd(ocf)
        ck('orphan-css-fix.py 含多声明行正则与自测', 'DECL_RE' in src and 'SELFTEST ALL PASS' in src)
        r = subprocess.run([sys.executable, ocf, '--selftest'], capture_output=True)
        out = (r.stdout + r.stderr).decode('utf-8', 'replace')
        ck('orphan-css-fix.py --selftest PASS', 'ALL PASS' in out and r.returncode == 0,
           out.strip().split('\n')[-1] if out.strip() else '')
    ck('文档坑表登记孤儿 CSS 坑', '孤儿 CSS 声明块静默吞掉下一条规则' in DOC)

    pst = os.path.join(HERE, 'pagesync-test-mqtt.js')
    if a.courseware and node and os.path.exists(pst):
        for p in a.courseware:
            if not os.path.exists(p):
                ck('课件存在: %s' % os.path.basename(p), False, p)
                continue
            r = subprocess.run([node, pst, p], capture_output=True)
            out = r.stdout.decode('utf-8', 'replace')
            last = [l for l in out.split('\n') if 'RESULT' in l]
            ck('page-sync 教学控制回归 %s 全过' % os.path.basename(p), 'ALL PASS' in out,
               last[0] if last else out[-120:])

    # ---------------- F. 文档内部一致性 ----------------
    print('\n' + '=' * 72 + '\nF. 文档内部一致性\n' + '=' * 72)
    # F1 重复锚点
    dup = {}
    for m in re.finditer(r'^- \[([^\]]+)\]\(#([^)]+)\)$', S, re.M):
        dup.setdefault(m.group(2), []).append(m.group(1))
    ck('TOC 无重复锚点', not {k: v for k, v in dup.items() if len(v) > 1},
       {k: v for k, v in dup.items() if len(v) > 1})

    # F2 站内链接无断链
    heads = set(gh_anchor(re.match(r'^#{1,6}\s+(.*)$', l).group(1))
                for l in S.split('\n') if re.match(r'^#{1,6}\s', l))
    explicit = set(re.findall(r'<a id="([^"]+)">', S))
    anch = heads | explicit
    broken = []
    for m in re.finditer(r'\]\(#([^)]+)\)', S):
        if m.group(1) not in anch:
            broken.append(m.group(1))
    ck('站内链接无断链', not broken, broken)

    # F3 母技能工具链项数与文档一致（有课件时用真实运行数核对）
    nums = [int(x) for x in re.findall(r'(\d+)\s*项', DOC)]
    if a.courseware and node and os.path.exists(pst):
        p0 = a.courseware[0]
        if os.path.exists(p0):
            out = subprocess.run([node, pst, p0], capture_output=True).stdout.decode('utf-8', 'replace')
            mm = re.search(r'RESULT:\s*[^(]*?\((\d+)\s*项\)', out)
            if mm:
                actual = int(mm.group(1))
                ok_n = ('%d 项' % actual) in DOC
                ck('文档声明的「%d 项」与 pagesync-test-mqtt 实际一致' % actual, ok_n,
                   '' if ok_n else '文档未含「%d 项」' % actual)
    else:
        ck('文档声明项数（未传课件，仅静态核对）',
           re.search(r'共 \d+ 项', DOC) is not None, '未见「共 N 项」')

    # F4 路线声明与勿复制清单
    ck('§4B 资料库强制路线存在（workbuddy.link/p/）', 'workbuddy.link/p/' in S)
    ck('含「勿复制清单」并点名云变体脚本', '勿复制' in DOC and 'audit_courseware_spec.py' in DOC)
    ck('无绝对用户路径残留', 'E:/Users/jowa' not in S and 'C:\\Users\\jowa' not in S)

    # F5 无构建残留
    residue = []
    for sub in ('scripts', 'references', 'references/templates'):
        d = os.path.join(SKILL, sub)
        if not os.path.isdir(d):
            continue
        for f in sorted(os.listdir(d)):
            if f == '__pycache__' or f.endswith('.pyc') or '.bak' in f:
                residue.append('%s/%s' % (sub, f))
    ck('无构建残留（__pycache__ / .pyc / .bak）', not residue, residue)

    # F6 2026-09-29 二轮文档修复点（v1.4.0 起查全集 DOC）
    ck('§4A.5 清空确认走 showConfirmModal（不得只写原生 confirm）',
       'showConfirmModal(msg, onOk)' in DOC)
    ck('A~H 表补入 E 项', '| **E** |' in DOC)
    ck('图片规则「单一事实来源」声明存在', '图片规则的单一事实来源' in DOC)
    ck('全屏规则「单一事实来源」声明存在', '全屏规则的单一事实来源' in DOC)
    ck('四张文件清单表「职责分工」声明存在', '四张「文件清单表」的分工' in DOC)
    ck('§3.7 无「点右上角测全屏」过时自检项', 'Page enters/exits fullscreen' not in S)
    ck('无 §1.3.1 张冠李戴的工具链引用', '见 1.3.1 标准件' not in S)

    # F7 附录 A 无「表格被空行切断」（v1.4.0 起坑表外迁，查全集）
    L = DOC.split('\n')
    i_a = next((i for i, l in enumerate(L) if l.startswith('### A · Common Pitfalls')), None)
    broken = []
    if i_a is not None:
        for i in range(i_a + 1, len(L)):
            if L[i].strip() == '' and L[i - 1].startswith('|') and i + 1 < len(L) and L[i + 1].startswith('|'):
                broken.append(i + 1)
    ck('附录A 无表格被空行切断', not broken, broken)

    print('\n' + '=' * 72)
    if FAILS:
        print('技能自审结论：FAIL %d 项 -> %s' % (len(FAILS), FAILS))
    else:
        print('技能自审结论：全部通过 ✅')
    print('=' * 72)
    return 1 if FAILS else 0


if __name__ == '__main__':
    sys.exit(main())
