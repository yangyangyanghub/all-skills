#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Local pre-publish check for courseware (run BEFORE publish_to_library.py).

Mirrors verify-library-online.js marker list so issues are caught LOCALLY
instead of costing one publish + online-verify round trip
(2026-10-02: 'DEFAULT-CLASS' survived in a template comment until the ONLINE
verify flagged it - this check now catches it before any upload).

Usage:
  python prepublish-check.py <courseware.html> [--node-id <id>] [--allow-empty-consts]
Exit code: 0 = PASS, 1 = FAIL (list printed).
"""
import io, re, sys

MUST_NOT_APPEAR = [
    (r'DEFAULT-CLASS', 'DEFAULT-CLASS literal (CLASS_ID tie-breaking rule; comments count too!)'),
    (r'\?teacher=1', 'delivery ban: ?teacher=1 query'),
]
MUST_APPEAR = [
    (r"subscribe\s*\(\s*SYNC_TOPIC", 'SYNC_TOPIC subscription (page sync)'),
    (r"subscribe\s*\(\s*SYNC_CTL_TOPIC", 'SYNC_CTL_TOPIC subscription (claim arbitration)'),
    (r"function\s+startBroadcast", 'startBroadcast'),
    (r"function\s+canStudentNavigate", 'canStudentNavigate'),
    (r"function\s+requestCurrentPage", 'requestCurrentPage (student fast-follow)'),
    (r"getPageParam", 'getPageParam (hash->search param reader)'),
    (r"xmn_teacher_", 'teacher identity localStorage key bound to NODE_ID'),
    (r"onOk\(true\)|onConfirm\(true\)", 'S14 confirm callback passes true'),
    (r"if\s*\(\s*IS_TEACHER\s*\)\s*startBroadcast\s*\(\s*\)\s*;|if\s*\(\s*IS_TEACHER\s*\)\s*\{\s*setTimeout\(\s*function\s*\(\s*\)\s*\{\s*xmnEnterTeacherRole\s*\(", 'G: connect callback broadcaster (startBroadcast 直连 或 xmnEnterTeacherRole 租约入口)'),
    (r"if\s*\(\s*isBroadcaster\s*(?:&&\s*!syncing\s*)?\)\s*xmnBroadcastPage\s*\(\s*\)\s*;", 'showPage end broadcast'),
    (r"lastManualNav\s*=\s*Date\.now\(\)", 'manual-nav timestamp (8s grace guard)'),
    (r"if\s*\(\s*!canStudentNavigate\s*\(\s*\)\s*\)\s*return", 'E: nav gate in nextPage/prevPage'),
]
CONST_PATS = [
    ('NODE_ID',      r"var\s+NODE_ID\s*=\s*'([^']*)'"),
    ('PUBLISH_BASE', r"var\s+PUBLISH_BASE\s*=\s*'([^']*)'"),
]

def main():
    args = sys.argv[1:]
    if not args:
        print('usage: prepublish-check.py <courseware.html> [--node-id <id>] [--allow-empty-consts]')
        return 2
    path = args[0]
    node_id = args[args.index('--node-id') + 1] if '--node-id' in args else None
    allow_empty = '--allow-empty-consts' in args
    src = io.open(path, encoding='utf-8').read()

    fails = []
    print('== prepublish-check:', path, '==')
    for pat, why in MUST_NOT_APPEAR:
        n = len(re.findall(pat, src))
        print('  %-4s x%d  must-not-appear: %s' % ('OK' if n == 0 else 'FAIL', n, why))
        if n:
            for m in re.finditer(pat, src):
                ln = src[:m.start()].count('\n') + 1
                fails.append('line %d: %r (%s)' % (ln, pat, why))
    for pat, why in MUST_APPEAR:
        n = len(re.findall(pat, src))
        print('  %-4s x%d  must-appear: %s' % ('OK' if n else 'FAIL', n, why))
        if not n:
            fails.append('missing: ' + why)
    for name, pat in CONST_PATS:
        m = re.search(pat, src)
        val = m.group(1) if m else None
        if node_id:
            want = node_id if name == 'NODE_ID' else 'https://workbuddy.link/p/%s' % node_id
            okk = (val == want)
        else:
            okk = allow_empty or bool(val)
        print('  %-4s %s = %r' % ('OK' if okk else 'FAIL', name, val))
        if not okk:
            fails.append('%s mismatch (got %r, want %r)' % (name, val, node_id and want or 'non-empty'))
    pm = re.search(r'var\s+PAGE_IDS\s*=\s*\[(.*?)\]\s*;', src, re.S)
    if pm:
        ids = re.findall(r"'([^']+)'", pm.group(1))
        print('  %-4s PAGE_IDS count = %d' % ('OK' if len(set(ids)) == len(ids) and ids else 'FAIL', len(ids)))
        if len(set(ids)) != len(ids):
            fails.append('PAGE_IDS has duplicates')
    else:
        print('  FAIL PAGE_IDS not found')
        fails.append('PAGE_IDS missing')

    # 2026-10-02 新增两条通用判据（抽屉原理课件实战提炼）——
    # 这两类缺陷语法全绿、pagesync 40 项与线上核验均测不出，只能本地结构级拦截。
    # ① 每个 QUIZZES 键必须在 HTML 里有同名 id 容器：容器漏写 id 时 initQuiz 的
    #    getElementById 返回 null 直接 return，整个测验引擎静默失效（页面照常渲染）。
    #    注意 QUIZZES 内层含嵌套花括号，须用平衡计数提取完整对象再找顶层键。
    def _extract_block(s, start_pat):
        m = re.search(start_pat, s)
        if not m:
            return None
        i = m.end() - 1
        depth = 0
        for j in range(i, len(s)):
            if s[j] == '{':
                depth += 1
            elif s[j] == '}':
                depth -= 1
                if depth == 0:
                    return s[i:j + 1]
        return None
    qblk = _extract_block(src, r'var\s+QUIZZES\s*=\s*\{')
    quiz_ids = re.findall(r'(?:^|\n)  (\w+)\s*:\s*\{', qblk) if qblk else []
    quiz_ids = [k for k in quiz_ids if k != 'questions']
    if quiz_ids:
        missing = [k for k in quiz_ids if not re.search(r'id="%s"' % k, src)]
        print('  %-4s QUIZZES keys=%d, 容器 id 齐全' % ('OK' if not missing else 'FAIL', len(quiz_ids))
              + ('' if not missing else '  缺: ' + ','.join(missing)))
        for k in missing:
            fails.append('quiz container id missing: %s (initQuiz will silently skip it)' % k)
    else:
        print('  %-4s QUIZZES 未找到（非测验课件可忽略）' % 'OK')
    # ② 每个 qrPopup_* 弹窗必含 xmnClear：sim_popup 曾缺清空按钮，
    #    导致仿真页提交的数据无法清除（2026-10-02 实战）。
    popup_ids = set(re.findall(r'id="qrPopup_(\w+)"', src))
    if popup_ids:
        no_clear = []
        for a in sorted(popup_ids):
            m = re.search(r'id="qrPopup_%s"' % re.escape(a), src)
            seg = src[m.start():m.start() + 1500] if m else ''
            has_stats = re.search(r'qrPart_|qrAvg_', seg)   # 含统计的弹窗才需清空按钮；无统计的仿真弹窗豁免
            if has_stats and not re.search(r"xmnClear\(\s*['\"]" + re.escape(a), seg):
                no_clear.append(a)
        print('  %-4s qrPopup 弹窗 %d 个, 均含 xmnClear' % ('OK' if not no_clear else 'FAIL', len(popup_ids))
              + ('' if not no_clear else '  缺: ' + ','.join(no_clear)))
        for a in no_clear:
            fails.append('qrPopup_%s has no xmnClear button (submitted data cannot be cleared)' % a)
    else:
        has_badge = '.qr-badge' in src
        print('  %-4s qrPopup %s' % ('FAIL' if has_badge else 'OK', '未找到（但存在 qr-badge，异常）' if has_badge else '未找到（无徽章课件可忽略）'))
        if has_badge:
            fails.append('qr-badge present but qrPopup missing')

    print('RESULT: %s' % ('PASS' if not fails else 'FAIL (%d)' % len(fails)))
    for f in fails:
        print('   -', f)
    return 0 if not fails else 1

if __name__ == '__main__':
    sys.exit(main())
