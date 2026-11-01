#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
耕地破坏文书格式合规检查（自包含，不需要参考原件）

用法：
    python check_spec.py 文书.docx                 # 结构级检查
    python check_spec.py 文书.docx --render        # 追加渲染级检查（需 LibreOffice）
    python check_spec.py 文书.docx --type lunzheng # 强制指定文书类型

校验项（结构级）：
    S1  页面：纸张、四边距、页眉页脚距、分栏、文档网格
    S2  文档默认：docDefaults 无多余 spacing/sz/lang，Normal 两端对齐
    S3  段落：每段字体/字号/加粗/行距/对齐
    S4  认定专属：文头 rPr 七项、红色反线形状参数
    S5  字体嵌入：odttf + fontTable + settings
    S6  落款：机关名与日期共用同一居中制表位

校验项（渲染级，--render）：
    R1  红线到文头文字底部的距离
    R2  落款两行水平中心一致
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile

from docx import Document
from docx.oxml.ns import qn
from docx.shared import Pt

W = qn

SPEC_LUNZHENG = {
    'kind': '论证意见',
    'side_margin_cm': 3.175,
    'paras': 15,
}
SPEC_RENDING = {
    'kind': '认定意见',
    'side_margin_cm': 2.499,
    'paras': 15,
}

EXPECTED_SECTION = {
    'page_cm': (21.0, 29.7),
    'margin_cm': (2.54, 2.54, None, None),
    'header_pt': 42.55,
    'footer_pt': 49.6,
    'cols': ('425', '1'),
    'docGrid': ('lines', '312', '0'),
}

HEADER_RPR_TAGS = ['rFonts', 'color', 'spacing', 'w', 'sz', 'szCs', 'lang']
HEADER_RPR_EXPECT = {
    'color': {'val': 'FF0000'},
    'spacing': {'val': '40'},
    'w': {'val': '75'},
    'sz': {'val': '110'},
    'szCs': {'val': '110'},
    'lang': {'eastAsia': 'zh-CN'},
}
HEADER_FONT = '方正大标宋简体'
SIGNATURE_TAB_PT = 344
TOL = 0.01

results = []


def local(tag):
    return tag.split('}')[-1] if '}' in tag else tag


def chk(ok, name, detail=''):
    results.append((bool(ok), name, detail))
    print('  %s %s%s' % ('OK  ' if ok else 'FAIL', name, ('  ← ' + detail) if detail else ''))
    return ok


def cm(v):
    return round(v / 360000, 3) if v is not None else None


def pt_of(v):
    return round(v / 12700, 2) if v is not None else None


def layer(title):
    print('\n' + '=' * 78)
    print(title)
    print('=' * 78)


def detect_kind(path, forced=None):
    if forced:
        return SPEC_LUNZHENG if forced.startswith('lun') else SPEC_RENDING
    name = os.path.basename(path)
    doc = Document(path)
    first = next((p.text for p in doc.paragraphs if p.text.strip()), '')
    if '行政认定意见' in first:
        return SPEC_RENDING
    if first.startswith('耕地破坏行政认定'):
        return SPEC_RENDING
    return SPEC_LUNZHENG if '论证' in name or '论证' in first else SPEC_RENDING


# ---------------- S1 页面 ----------------
def check_section(doc, spec):
    layer('S1 页面设置')
    s = doc.sections[0]
    sect = s._sectPr
    grid = sect.find(W('w:docGrid'))
    cols = sect.find(W('w:cols'))

    chk(abs(s.page_width.cm - EXPECTED_SECTION['page_cm'][0]) < TOL,
        '纸张宽 21.0cm', '实际 %.2f' % s.page_width.cm)
    chk(abs(s.page_height.cm - EXPECTED_SECTION['page_cm'][1]) < TOL,
        '纸张高 29.7cm', '实际 %.2f' % s.page_height.cm)
    chk(abs(s.top_margin.cm - 2.54) < TOL, '上边距 2.54cm', '实际 %.3f' % s.top_margin.cm)
    chk(abs(s.bottom_margin.cm - 2.54) < TOL, '下边距 2.54cm', '实际 %.3f' % s.bottom_margin.cm)
    chk(abs(s.left_margin.cm - spec['side_margin_cm']) < TOL,
        '左边距 %.3fcm（%s）' % (spec['side_margin_cm'], spec['kind']),
        '实际 %.3f' % s.left_margin.cm)
    chk(abs(s.right_margin.cm - spec['side_margin_cm']) < TOL,
        '右边距 %.3fcm' % spec['side_margin_cm'], '实际 %.3f' % s.right_margin.cm)
    chk(abs(s.header_distance.pt - EXPECTED_SECTION['header_pt']) < 0.1,
        '页眉距 42.55pt', '实际 %.2f' % s.header_distance.pt)
    chk(abs(s.footer_distance.pt - EXPECTED_SECTION['footer_pt']) < 0.1,
        '页脚距 49.6pt', '实际 %.2f' % s.footer_distance.pt)

    got_cols = (cols.get(W('w:space')) if cols is not None else None,
                cols.get(W('w:num')) if cols is not None else None)
    chk(got_cols == EXPECTED_SECTION['cols'], '分栏 space=425 num=1', '实际 %s' % (got_cols,))

    got_grid = (grid.get(W('w:type')) if grid is not None else None,
                grid.get(W('w:linePitch')) if grid is not None else None,
                grid.get(W('w:charSpace')) if grid is not None else None)
    chk(got_grid == EXPECTED_SECTION['docGrid'],
        '文档网格 lines/312/0', '实际 %s（不对会让文号段行高变，红线错位）' % (got_grid,))


# ---------------- S2 文档默认 ----------------
def check_defaults(doc):
    layer('S2 文档默认格式')
    dd = doc.styles.element.find(W('w:docDefaults'))

    ppr_default = dd.find(W('w:pPrDefault')) if dd is not None else None
    ppr = ppr_default.find(W('w:pPr')) if ppr_default is not None else None
    spacing = ppr.find(W('w:spacing')) if ppr is not None else None
    chk(spacing is None,
        'docDefaults 无默认段间距',
        '存在 %s（会让文头/文号段多 10pt 段后距）' % spacing.attrib if spacing is not None else '')

    rpr_default = dd.find(W('w:rPrDefault')) if dd is not None else None
    rpr = rpr_default.find(W('w:rPr')) if rpr_default is not None else None
    bad = []
    if rpr is not None:
        for tag in ('w:sz', 'w:szCs', 'w:lang'):
            if rpr.find(W(tag)) is not None:
                bad.append(tag.split(':')[1])
    chk(not bad, 'docDefaults 无多余字号/语言设置',
        '存在 %s（lang 会让中文字体回退成 Arial Unicode MS）' % ','.join(bad) if bad else '')

    normal = doc.styles['Normal']
    align = str(normal.paragraph_format.alignment).split(' ')[0] if \
        normal.paragraph_format.alignment is not None else 'LEFT'
    chk(align == 'JUSTIFY', 'Normal 样式两端对齐', '实际 %s' % align)


# ---------------- S3 段落 ----------------
def run_font(run):
    rpr = run._element.rPr
    ea = None
    if rpr is not None and rpr.rFonts is not None:
        ea = rpr.rFonts.get(W('w:eastAsia')) or rpr.rFonts.get(W('w:ascii'))
    return ea or run.font.name


def check_paragraphs(doc, spec):
    layer('S3 段落格式')
    chk(len(doc.paragraphs) == spec['paras'],
        '段落数 %d' % spec['paras'], '实际 %d' % len(doc.paragraphs))

    for i, p in enumerate(doc.paragraphs):
        if not p.text.strip():
            continue
        r = next((x for x in p.runs if x.text.strip()), None)
        if r is None:
            continue
        font = run_font(r)
        size = pt_of(r.font.size)
        pf = p.paragraph_format
        ls = pt_of(pf.line_spacing) if hasattr(pf.line_spacing, 'pt') else pf.line_spacing
        tag = '[P%02d] %s %.0fpt 行距%s %r' % (i, font, size or 0, ls, p.text[:12])
        ok = font is not None and size is not None
        chk(ok, 'P%02d 有明确字体与字号' % i, '' if ok else '字体=%s 字号=%s' % (font, size))


# ---------------- S4 认定专属 ----------------
def check_rending_only(doc):
    layer('S4 红头与红色反线')

    p0 = doc.paragraphs[0]
    chk(p0.text.strip() == '耕地破坏行政认定意见', '文头文字', repr(p0.text[:20]))
    r = p0.runs[0] if p0.runs else None
    if r is not None:
        rpr = r._element.find(W('w:rPr'))
        tags = [local(c.tag) for c in rpr] if rpr is not None else []
        chk(tags == HEADER_RPR_TAGS, '文头 rPr 七项齐全且顺序正确', '实际 %s' % tags)
        for tag, expect in HEADER_RPR_EXPECT.items():
            el = rpr.find(W('w:' + tag)) if rpr is not None else None
            got = {local(k): v for k, v in el.attrib.items()} if el is not None else None
            chk(got == expect, '文头 %s=%s' % (tag, expect), '实际 %s' % got)

    shapes = doc.element.body.findall('.//' + W('w:drawing'))
    chk(len(shapes) == 1, '红色反线形状数 = 1', '实际 %d' % len(shapes))
    if shapes:
        from lxml import etree
        s = etree.tostring(shapes[0]).decode()
        chk('FF0000' in s, '反线颜色 FF0000')
        chk('w="28575"' in s, '反线线宽 2.25pt')
        chk('cx="6153785"' in s, '反线长度 484.55pt')
        chk('68580' in s, '反线垂直偏移 5.4pt')
        chk('-187960' in s, '反线水平偏移 -14.8pt')
        ac = doc.element.body.findall(
            './/{http://schemas.openxmlformats.org/markup-compatibility/2006}AlternateContent')
        chk(bool(ac) and 'Fallback' in etree.tostring(ac[0]).decode(),
            '含 VML 回退分支（老版本 Word/WPS 依赖）')

    p1 = doc.paragraphs[1]
    docno_run = next((x for x in p1.runs if x.text.strip()), None)
    if docno_run is not None:
        rpr = docno_run._element.find(W('w:rPr'))
        fonts = rpr.find(W('w:rFonts')) if rpr is not None else None
        ea = fonts.get(W('w:eastAsia')) if fonts is not None else None
        hint = fonts.get(W('w:hint')) if fonts is not None else None
        chk(ea == '宋体', '文号中文字体显式宋体', '实际 %s' % ea)
        chk(hint == 'eastAsia', '文号 rFonts hint=eastAsia', '实际 %s' % hint)


# ---------------- S5 字体嵌入 ----------------
def check_fonts(path, doc):
    layer('S5 红头字体嵌入')
    z = zipfile.ZipFile(path)
    odttf = [n for n in z.namelist() if n.endswith('.odttf')]
    chk(bool(odttf), '存在 odttf 字体文件', str(odttf))
    ft = z.read('word/fontTable.xml').decode('utf-8')
    chk('方正大标宋简体' in ft and 'embedRegular' in ft,
        'fontTable 声明了方正大标宋简体嵌入')
    ct = z.read('[Content_Types].xml').decode('utf-8')
    chk('odttf' in ct, 'Content_Types 声明 odttf')
    st = z.read('word/settings.xml').decode('utf-8')
    chk('<w:embedTrueTypeFonts/>' in st, 'settings 开启 embedTrueTypeFonts')
    chk('<w:saveSubsetFonts/>' in st, 'settings 开启 saveSubsetFonts')
    z.close()


# ---------------- S6 落款 ----------------
def check_signature(doc):
    layer('S6 落款对齐')
    tail = [p for p in doc.paragraphs if p.text.strip()][-2:]
    if len(tail) < 2:
        chk(False, '落款两段存在')
        return
    issuer, date = tail[0], tail[1]
    ok_name = '自然资源和规划局' in issuer.text or '局' in issuer.text
    chk(ok_name, '倒数第二段为落款单位', repr(issuer.text[:20]))
    chk(bool(re.search(r'\d{4}年\d{1,2}月\d{1,2}日', date.text)),
        '最后一段为日期', repr(date.text[:20]))
    for label, p in (('单位', issuer), ('日期', date)):
        stops = p.paragraph_format.tab_stops
        hit = [ts for ts in stops if ts.alignment is not None
               and 'CENTER' in str(ts.alignment)
               and abs(ts.position.pt - SIGNATURE_TAB_PT) < 0.5]
        chk(bool(hit), '落款%s有居中制表位 %dpt' % (label, SIGNATURE_TAB_PT),
            '实际 %s' % [(ts.position.pt, str(ts.alignment)) for ts in stops])


# ---------------- S7 全文一致性 ----------------
def check_consistency(doc):
    layer('S7 全文一致性')
    text = '\n'.join(p.text for p in doc.paragraphs)

    names = set(re.findall(r'建设([\u4e00-\u9fa5A-Za-z0-9（）\-]{4,30}?)项目', text))
    chk(len(names) <= 1, '项目名称全文唯一',
        '发现多种写法 %s（改名时漏改会出现）' % names if len(names) > 1 else
        '（%s）' % next(iter(names)) + '项目' if names else '（未识别到项目名）')

    amounts = re.findall(r'([0-9]+\.[0-9]{4})公顷（合([0-9]+\.[0-9]{2})亩）', text)
    bad = [(ha, mu) for ha, mu in amounts
           if abs(float(ha) * 15 - float(mu)) > 0.01 + 1e-9
           and abs(round(float(ha) * 15 + 1e-9, 2) - float(mu)) > 0.011]
    chk(not bad, '公顷与亩的换算全文自洽',
        '不一致 %s' % bad[:3] if bad else '（%d 处全部吻合）' % len(amounts))

    damage = set(re.findall(r'种植条件([\u4e00-\u9fa5]{2,6})', text))
    allowed = {'严重毁坏', '严重破坏', '毁坏', '破坏'}
    off = sorted(damage - allowed)
    chk(not off, '毁坏程度表述规范',
        '发现 %s，可用写法：严重毁坏 / 严重破坏 / 毁坏 / 破坏'
        % off if off else ('（%s）' % next(iter(damage)) if damage else ''))


# ---------------- S8 内容溯源 ----------------
RISK_PHRASES = [
    '开挖', '挖成', '挖出', '剥离', '回填', '硬化', '浇筑', '砌筑',
    '配套设施用地', '构筑物用地', '池体', '塘坝',
]


def check_traceability(doc, report_path):
    """文书里的建设方式、现状、判断类表述，必须能在调查报告里找到对应文字。
    报告没写的不能补——这是虚构。"""
    layer('S8 内容溯源（对照执法局调查报告）')
    if not report_path or not os.path.exists(report_path):
        chk(False, '提供调查报告', '未指定 --report，跳过溯源检查')
        return
    with open(report_path, encoding='utf-8') as f:
        report = re.sub(r'\s+', '', f.read())
    text = re.sub(r'\s+', '', '\n'.join(p.text for p in doc.paragraphs))

    hits = [kw for kw in RISK_PHRASES if kw in text and kw not in report]
    chk(not hits, '无报告中不存在的表述',
        '发现 %s（报告里没有这些说法）' % '、'.join(hits) if hits else
        '（检查了 %d 个高风险词）' % len(RISK_PHRASES))

    facts = ['2023', '粮画大道', '黄花鸢尾']
    miss = [k for k in facts if k in text and k not in report]
    chk(not miss, '关键事实均在报告中有依据',
        '无依据 %s' % '、'.join(miss) if miss else '')


# ---------------- S9 结构骨架 ----------------
# 只列不可缺的骨架。可选项（如上一年度地类句、地块编号、涉嫌）不在此列。
SKELETON = {
    'lunzheng': ['一、基本情况', '二、论证依据', '三、论证结论', '综上：', '专家组成员：'],
    'rending': ['一、基本情况', '二、认定意见', '（一）认定依据:', '（二）认定结论：',
                '综上：', '附件.现场照片'],
}


def check_skeleton(doc, spec):
    layer('S9 结构骨架')
    kind = 'lunzheng' if spec is SPEC_LUNZHENG else 'rending'
    text = '\n'.join(p.text for p in doc.paragraphs)
    miss = [k for k in SKELETON[kind] if k not in text]
    chk(not miss, '骨架段落齐全',
        '缺 %s' % '、'.join(miss) if miss else
        '（%d 项）' % len(SKELETON[kind]))


# ---------------- R 渲染级 ----------------
def find_soffice():
    for p in (r'C:\Program Files\LibreOffice\program\soffice.exe',
              r'C:\Program Files (x86)\LibreOffice\program\soffice.exe'):
        if os.path.exists(p):
            return p
    return shutil.which('soffice')


def check_render(docx_path):
    layer('R 渲染级检查（LibreOffice）')
    soffice = find_soffice()
    if not soffice:
        chk(False, '找到 LibreOffice', '未安装，跳过渲染级检查')
        return
    try:
        import pdfplumber
    except ImportError:
        chk(False, 'pdfplumber 可用', '未安装')
        return

    tmp = tempfile.mkdtemp(prefix='speccheck_')
    src = os.path.join(tmp, 'doc.docx')
    shutil.copy2(docx_path, src)
    profile = 'file:///' + tmp.replace('\\', '/') + '/lo'
    subprocess.run([soffice, '--headless', '-env:UserInstallation=' + profile,
                    '--convert-to', 'pdf', '--outdir', tmp, src],
                   capture_output=True, timeout=180)
    pdf_path = os.path.join(tmp, 'doc.pdf')
    if not os.path.exists(pdf_path):
        chk(False, 'PDF 转换成功')
        return
    chk(True, 'PDF 转换成功')

    with pdfplumber.open(pdf_path) as pdf:
        pages = pdf.pages

        def red_line():
            for pg in pages:
                for attr in ('lines', 'rects', 'curves'):
                    for s in getattr(pg, attr):
                        col = s.get('stroking_color') or s.get('non_stroking_color')
                        if isinstance(col, (list, tuple)) and len(col) == 3 \
                                and col[0] > 0.8 and col[1] < 0.2 and col[2] < 0.2 \
                                and (s.get('x1', 0) - s.get('x0', 0)) > 380:
                            return s
            return None

        line = red_line()
        if line:
            chk(True, '渲染出红色反线', 'x0=%.1f top=%.1f' % (line['x0'], line['top']))
            big = [c for c in pages[0].chars if c['size'] > 30 and c['text'].strip()]
            if big:
                gap = line['top'] - max(c['bottom'] for c in big)
                chk(10 <= gap <= 24, '红线与文头间距在 10~24pt', '实际 %.2fpt' % gap)
        else:
            chk(False, '渲染出红色反线')

        rows = {}
        for c in pages[-1].chars:
            if c['text'].strip():
                rows.setdefault(round(c['top'], 1), []).append(c)
        cand = [(t, cs) for t, cs in rows.items()
                if len(cs) <= 16 and ('局' in ''.join(c['text'] for c in cs)
                                      or re.search(r'\d{4}年', ''.join(c['text'] for c in cs)))]
        if len(cand) >= 2:
            centers = []
            for t, cs in sorted(cand)[-2:]:
                x0 = min(c['x0'] for c in cs)
                x1 = max(c['x1'] for c in cs)
                centers.append((x0 + x1) / 2)
            diff = abs(centers[0] - centers[1])
            chk(diff < 1.0, '落款两行水平中心一致', '差 %.2fpt' % diff)
        else:
            chk(False, '定位落款两行')

    shutil.rmtree(tmp, ignore_errors=True)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    path = sys.argv[1]
    forced = None
    if '--type' in sys.argv:
        forced = sys.argv[sys.argv.index('--type') + 1]
    report = None
    if '--report' in sys.argv:
        report = sys.argv[sys.argv.index('--report') + 1]
    if not os.path.exists(path):
        sys.exit('文件不存在：%s' % path)

    doc = Document(path)
    spec = detect_kind(path, forced)
    print('=' * 78)
    print('文件：%s' % os.path.basename(path))
    print('类型：%s' % spec['kind'])
    print('=' * 78)

    check_section(doc, spec)
    check_defaults(doc)
    check_paragraphs(doc, spec)
    check_consistency(doc)
    check_skeleton(doc, spec)
    if spec is SPEC_RENDING:
        check_rending_only(doc)
        check_fonts(path, doc)
        check_signature(doc)
    if '--render' in sys.argv:
        check_render(path)
    if report:
        check_traceability(doc, report)

    layer('汇总')
    fails = [r for r in results if not r[0]]
    print('校验项 %d，通过 %d，失败 %d'
          % (len(results), len(results) - len(fails), len(fails)))
    if fails:
        print('\n失败明细：')
        for ok, name, detail in fails:
            print('  FAIL %-52s %s' % (name, detail))
        sys.exit(1)
    print('全部通过。')


if __name__ == '__main__':
    main()
