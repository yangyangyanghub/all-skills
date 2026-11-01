#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
公文格式提取 / 比对工具

用法：
    python check_format.py 目标.docx               # 打印段落格式表
    python check_format.py 生成.docx 参考.docx      # 逐段比对，标出差异

比对项：页边距、段落数、每段首个有效 run 的（字体, 字号, 加粗）、行距。
"""
import sys

from docx import Document
from docx.oxml.ns import qn

W = qn


def pt(v):
    return None if v is None else round(v / 12700, 2)


def cm(v):
    return None if v is None else round(v / 360000, 3)


def section_sig(doc):
    """完整节属性。docGrid 会改变多倍行距段落的实际行高——红头反线锚定在
    文号段落上，网格不同会让线错位压字，所以必须逐项比。"""
    s = doc.sections[0]
    sect = s._sectPr
    grid = sect.find(qn('w:docGrid'))
    cols = sect.find(qn('w:cols'))
    return {
        'page_cm': (cm(s.page_width), cm(s.page_height)),
        'margin_cm': (cm(s.top_margin), cm(s.bottom_margin),
                      cm(s.left_margin), cm(s.right_margin)),
        'header_pt': round(s.header_distance.pt, 2) if s.header_distance else None,
        'footer_pt': round(s.footer_distance.pt, 2) if s.footer_distance else None,
        'cols': (cols.get(qn('w:space')) if cols is not None else None,
                 cols.get(qn('w:num')) if cols is not None else None),
        'docGrid': (grid.get(qn('w:type')) if grid is not None else None,
                    grid.get(qn('w:linePitch')) if grid is not None else None,
                    grid.get(qn('w:charSpace')) if grid is not None else None),
    }


def normal_align(doc):
    """Normal 样式的对齐值。正文段落不显式设 jc 时，实际效果由它决定。"""
    a = doc.styles['Normal'].paragraph_format.alignment
    return str(a).split(' ')[0] if a is not None else 'LEFT'


def effective_align(doc, p):
    """段落显式 jc 优先，否则继承 Normal。这是肉眼看到的对齐。"""
    if p.alignment is not None:
        return str(p.alignment).split(' ')[0]
    return normal_align(doc)


def shape_count(doc):
    """正文内的浮动形状数量。红头反线是 w:drawing，纯文字比对发现不了。"""
    return len(doc.element.body.findall('.//' + qn('w:drawing')))


def para_sig(p):
    """首个含文字的 run 的字体/字号/加粗 + 行距。"""
    font = size = bold = None
    for r in p.runs:
        if not r.text:
            continue
        rpr = r._element.rPr
        ea = None
        if rpr is not None and rpr.rFonts is not None:
            ea = rpr.rFonts.get(W('w:eastAsia')) or rpr.rFonts.get(W('w:ascii'))
        font = ea or r.font.name
        size = pt(r.font.size)
        bold = bool(r.bold)
        break
    lsp = p.paragraph_format.line_spacing
    if hasattr(lsp, 'pt'):
        lsp = lsp.pt
    return font, size, bold, lsp


def dump(fp):
    doc = Document(fp)
    print('=' * 84)
    print('FILE:', fp)
    for k, v in section_sig(doc).items():
        print('  %-10s %s' % (k, v))
    print('Normal 样式对齐 =', normal_align(doc), '  ← 段落未显式设 jc 时生效')
    print('浮动形状数 =', shape_count(doc))
    print('-' * 84)
    print(' %-4s %-8s %-6s %-6s %-8s %-14s %s' % ('段', '字体', '字号', '加粗', '行距', '对齐', '文字'))
    for i, p in enumerate(doc.paragraphs):
        f, sz, b, ls = para_sig(p)
        print(' P%02d  %-8s %-6s %-6s %-8s %-14s %s'
              % (i, f or '-', sz or '-', b if b is not None else '-',
                 ls or '-', effective_align(doc, p), p.text[:34]))


def compare(target_fp, ref_fp):
    a = Document(ref_fp)
    b = Document(target_fp)
    print('=' * 84)
    print('参考:', ref_fp)
    print('生成:', target_fp)
    print('=' * 84)

    sa, sb = section_sig(a), section_sig(b)
    print('节属性比对：')
    sec_diffs = 0
    for key in sa:
        same = sa[key] == sb[key]
        if not same:
            sec_diffs += 1
        print('  %s %-10s 参考 %-46s 生成 %s'
              % ('OK  ' if same else 'DIF ', key, sa[key], sb[key]))

    na, nb = normal_align(a), normal_align(b)
    print('Normal 样式对齐  参考 %s / 生成 %s  %s'
          % (na, nb, '一致' if na == nb else '不一致（正文实际对齐会不同）'))

    sha, shb = shape_count(a), shape_count(b)
    print('浮动形状数      参考 %d / 生成 %d  %s'
          % (sha, shb, '一致' if sha == shb else '不一致（红头反线等图形缺失或多出）'))

    print('段落数  参考 %d / 生成 %d  %s'
          % (len(a.paragraphs), len(b.paragraphs),
             '一致' if len(a.paragraphs) == len(b.paragraphs) else '不一致'))

    print('-' * 84)
    diffs = 0
    for i in range(min(len(a.paragraphs), len(b.paragraphs))):
        fa, sa_, ba, la = para_sig(a.paragraphs[i])
        fb, sb_, bb, lb = para_sig(b.paragraphs[i])
        if fa is None and fb is None:
            continue
        ja = effective_align(a, a.paragraphs[i])
        jb = effective_align(b, b.paragraphs[i])
        ok = (fa == fb and sa_ == sb_ and ja == jb)
        if not ok:
            diffs += 1
        print(' %s P%02d 参考(%s,%s,%s,%s) L%s | 生成(%s,%s,%s,%s) L%s'
              % ('OK  ' if ok else 'DIF ', i, fa, sa_, ba, ja, la, fb, sb_, bb, jb, lb))
    print('-' * 84)
    print('字体/字号差异段落数：%d' % diffs)
    if diffs == 0:
        print('格式与参考件一致。')


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    if len(sys.argv) >= 3:
        compare(sys.argv[1], sys.argv[2])
    else:
        dump(sys.argv[1])
