#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
耕地破坏鉴定文书生成器
从 JSON 配置生成《耕地破坏论证意见》和《耕地破坏行政认定意见》两份 docx。

用法：
    python gen_docs.py config.json
    python gen_docs.py config.json --dry-run     # 只校验面积，不出文档

格式基准（河北邯郸既有文书，逐段比对验证）：
    论证意见：A4，上下 2.54cm，左右 3.175cm
    认定意见：A4，上下 2.54cm，左右 2.499cm
    标题 黑体 22pt 加粗 居中 行距精确 30pt
    正文 仿宋 16pt 行距精确 28pt 首行缩进 2 字符
    一级标题 黑体 16pt；（一）（二）楷体 16pt；综上 加粗
    认定意见文头 方正大标宋简体 55pt 红色；文号 14pt 右对齐 2.5 倍行距

依赖：python-docx
"""
import json
import os
import sys
from decimal import Decimal, ROUND_HALF_UP

from docx import Document
from docx.shared import Pt, Cm, RGBColor, Twips
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING, WD_TAB_ALIGNMENT
from docx.oxml import parse_xml
from docx.oxml.ns import qn, nsdecls

D = Decimal
MU_PER_HA = D('15')

BODY_FONT = '仿宋'
HEAD_FONT = '黑体'
SUB_FONT = '楷体'
DOC_HEADER_FONT = '方正大标宋简体'

SIGNATURE_TAB_PT = 344

# 地类汇总顺序与文书用词
LAND_TYPES = [
    ('gengdi', '耕地'),
    ('guoyuan', '果园'),
    ('lindi', '林地'),
    ('nongdao', '农村道路'),
    ('jianshe', '建设用地'),
]

# ============================== 面积工具 ==============================

def q2(x):
    return D(x).quantize(D('0.01'), rounding=ROUND_HALF_UP)


def q4(x):
    return D(x).quantize(D('0.0001'), rounding=ROUND_HALF_UP)


def ha2mu(ha):
    """公顷 → 亩，1 公顷 = 15 亩，四舍五入保留 2 位。禁止截断。"""
    return q2(D(ha) * MU_PER_HA)


def fmt_area(ha):
    """文书标准写法：X.XXXX公顷（合Y.YY亩）"""
    return '%s公顷（合%s亩）' % (q4(ha), ha2mu(ha))


# ============================== 汇总与校验 ==============================

def aggregate(plots):
    """按地块明细汇总各地类公顷数。"""
    agg = {k: D('0') for k, _ in LAND_TYPES}
    agg['area'] = D('0')
    for p in plots:
        agg['area'] += D(str(p['area']))
        agg['gengdi'] += D(str(p.get('gengdi', 0)))
        agg['guoyuan'] += D(str(p.get('guoyuan', 0)))
        agg['lindi'] += D(str(p.get('qiaomu_lindi', 0))) + D(str(p.get('qita_lindi', 0)))
        agg['nongdao'] += D(str(p.get('nongdao', 0)))
        agg['jianshe'] += D(str(p.get('jianshe', 0)))
    return agg


def validate(cfg, plots, agg):
    """六层校验。返回 (errors, warnings)。有 error 则不生成文档。"""
    errors, warnings = [], []
    tol = D('0.00005')

    # 第一层：地块级self-consistency
    for p in plots:
        pid = p.get('id', '?')
        nong = D(str(p.get('gengdi', 0))) + D(str(p.get('guoyuan', 0))) \
            + D(str(p.get('qiaomu_lindi', 0))) + D(str(p.get('qita_lindi', 0))) \
            + D(str(p.get('nongdao', 0)))
        total = nong + D(str(p.get('jianshe', 0)))
        if abs(total - D(str(p['area']))) > tol:
            errors.append('地块 %s 分项之和 %.4f ≠ 地块面积 %.4f'
                          % (pid, total, D(str(p['area']))))

    # 第二层：汇总之和 = 各分项合计
    parts = sum(agg[k] for k, _ in LAND_TYPES)
    if abs(parts - agg['area']) > tol:
        errors.append('分项合计 %.4f ≠ 总面积 %.4f（差 %.4f）'
                      % (parts, agg['area'], parts - agg['area']))

    # 第三层：配置声明的总面积（可选）
    declared = cfg['case'].get('total_area_ha')
    if declared is not None and abs(D(str(declared)) - agg['area']) > tol:
        errors.append('配置声明总面积 %s ≠ 地类汇总 %s' % (declared, agg['area']))

    # 第四层：平方米交叉校验（可选）
    survey = cfg.get('survey_m2') or {}
    if survey:
        m2_total = D(str(survey.get('total', 0)))
        if m2_total:
            if abs(m2_total / D('10000') - agg['area']) > D('0.0001'):
                errors.append('调查报告总面积 %s㎡ (=%s公顷) ≠ 地类汇总 %s 公顷'
                              % (m2_total, m2_total / D('10000'), agg['area']))
        m2_parts = {k: v for k, v in survey.items() if k != 'total'}
        if m2_parts:
            s = sum(D(str(v)) for v in m2_parts.values())
            if m2_total and abs(s - m2_total) > D('0.01'):
                errors.append('调查报告分项㎡之和 %.2f ≠ 总面积 %s' % (s, m2_total))

    # 第五层：亩数分项和 = 合计亩
    mu_parts = sum(ha2mu(agg[k]) for k, _ in LAND_TYPES)
    mu_total = ha2mu(agg['area'])
    if mu_parts != mu_total:
        errors.append('亩数分项之和 %s ≠ 合计亩数 %s（舍入不同步，检查各地类明细）'
                      % (mu_parts, mu_total))

    # 第六层：破坏面积合理性
    dmg = D(str(cfg['case'].get('damage_ha', 0)))
    if dmg <= 0:
        errors.append('未声明 damage_ha（认定破坏的耕地公顷数）')
    elif dmg > agg['gengdi'] + tol:
        errors.append('破坏面积 %s 公顷 > 耕地总面积 %s 公顷' % (dmg, agg['gengdi']))

    pf = cfg['case'].get('permanent_farmland')
    if pf is not None and D(str(pf)) > agg['gengdi'] + tol:
        warnings.append('永久基本农田 %s 公顷 > 耕地 %s 公顷，请复核' % (pf, agg['gengdi']))

    return errors, warnings


# ============================== docx 基础操作 ==============================

def reset_doc_defaults(doc):
    """复刻原件的 docDefaults：空的 pPrDefault，rPr 只留主题字体。

    python-docx 默认模板在 docDefaults 里塞了三样原件没有的东西：
      pPrDefault/w:pPr/spacing after=200 line=276 auto  → 未设 spacing 的段落
          多出 10pt 段后距、行距变 1.15 倍
      rPrDefault/w:rPr/w:sz=22                          → 默认字号 11pt
      rPrDefault/w:rPr/w:lang eastAsia="en-US"          → 中文字体解析错，
          文号会从宋体变成 Arial Unicode MS，行高度量不同

    文头段和文号段都没有显式 spacing，全部受影响，导致文号段与红头反线
    整体下移（实测 23.2pt）。正文段都显式设了行距，不受影响。
    """
    dd = doc.styles.element.find(qn('w:docDefaults'))
    if dd is None:
        return
    ppr_default = dd.find(qn('w:pPrDefault'))
    if ppr_default is not None:
        ppr = ppr_default.find(qn('w:pPr'))
        if ppr is not None:
            ppr_default.remove(ppr)
    rpr_default = dd.find(qn('w:rPrDefault'))
    if rpr_default is not None:
        rpr = rpr_default.find(qn('w:rPr'))
        if rpr is not None:
            for tag in ('w:sz', 'w:szCs', 'w:lang'):
                el = rpr.find(qn(tag))
                if el is not None:
                    rpr.remove(el)


def setup_page(doc, side_margin_cm):
    """设置页面。除边距外还有三项必须与原件一致，否则多倍行距段落（文号段）
    的实际行高会变，锚定在段落上的红线偏移就会落到字上：

      文档网格 docGrid 线间距 312（15.6pt）、按行对齐
      分栏 cols 间距 425、单栏
      页眉 851 / 页脚 992

    同时把 Normal 样式设为两端对齐——原件即如此，正文段落不设 jc，靠样式继承。
    """
    s = doc.sections[0]
    s.page_width = Cm(21.0)
    s.page_height = Cm(29.7)
    s.top_margin = Cm(2.54)
    s.bottom_margin = Cm(2.54)
    s.left_margin = Cm(side_margin_cm)
    s.right_margin = Cm(side_margin_cm)
    s.header_distance = Twips(851)
    s.footer_distance = Twips(992)
    doc.styles['Normal'].paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    reset_doc_defaults(doc)

    sect = s._sectPr
    cols = sect.find(qn('w:cols'))
    if cols is None:
        cols = parse_xml('<w:cols %s/>' % nsdecls('w'))
        grid = sect.find(qn('w:docGrid'))
        if grid is not None:
            grid.addprevious(cols)
        else:
            sect.append(cols)
    cols.set(qn('w:space'), '425')
    cols.set(qn('w:num'), '1')

    grid = sect.find(qn('w:docGrid'))
    if grid is None:
        grid = parse_xml('<w:docGrid %s/>' % nsdecls('w'))
        sect.append(grid)
    grid.set(qn('w:type'), 'lines')
    grid.set(qn('w:linePitch'), '312')
    grid.set(qn('w:charSpace'), '0')


def apply_char_tuning(run, spacing_twips=None, width_pct=None):
    """设置字符间距与横向缩放。w:rPr 子元素有严格顺序（rFonts→b→color→spacing→w→sz），
    append 到末尾会破坏 schema，必须按位置插入。"""
    rpr = run._element.get_or_add_rPr()
    for tag in ('w:spacing', 'w:w'):
        old = rpr.find(qn(tag))
        if old is not None:
            rpr.remove(old)
    anchor = rpr.find(qn('w:color'))
    if anchor is None:
        anchor = rpr.find(qn('w:rFonts'))
    nodes = []
    if spacing_twips is not None:
        nodes.append(parse_xml('<w:spacing %s w:val="%d"/>' % (nsdecls('w'), spacing_twips)))
    if width_pct is not None:
        nodes.append(parse_xml('<w:w %s w:val="%d"/>' % (nsdecls('w'), width_pct)))
    if anchor is not None:
        for node in reversed(nodes):
            anchor.addnext(node)
    else:
        for node in reversed(nodes):
            rpr.insert(0, node)


def set_run(run, font, size, bold=False, color=None, spacing=None, width=None):
    run.font.name = font
    rpr = run._element.get_or_add_rPr()
    rfonts = rpr.find(qn('w:rFonts'))
    if rfonts is None:
        rfonts = rpr.makeelement(qn('w:rFonts'), {})
        rpr.insert(0, rfonts)
    rfonts.set(qn('w:ascii'), font)
    rfonts.set(qn('w:hAnsi'), font)
    rfonts.set(qn('w:eastAsia'), font)
    run.font.size = Pt(size)
    run.bold = bold
    if color:
        run.font.color.rgb = color
    if spacing is not None or width is not None:
        apply_char_tuning(run, spacing, width)


def set_paragraph_mark_rpr(p, source_run=None, size_pt=None):
    """设置段落标记（¶）的字符格式，写入 pPr/rPr。
    段落标记的字号参与行高计算；原件在文头段与文号段都声明了它，
    不声明会让该段行高不同，后续段落（含红头反线）整体位移。"""
    from copy import deepcopy
    ppr = p._element.get_or_add_pPr()
    old = ppr.find(qn('w:rPr'))
    if old is not None:
        ppr.remove(old)
    if source_run is not None:
        rpr = deepcopy(source_run._element.rPr)
    else:
        rpr = parse_xml('<w:rPr %s><w:sz w:val="%d"/><w:szCs w:val="%d"/></w:rPr>'
                        % (nsdecls('w'), int(size_pt * 2), int(size_pt * 2)))
    ppr.append(rpr)


def style_doc_header_run(run, font, size_pt, color, spacing, width, lang='zh-CN'):
    """文头 run 的 rPr，按原件逐项构造。
    python-docx 的 font API 只设 w:sz，不设 szCs；也不设 w:cs 与 w:lang。
    这几项缺失会让字形选择与字距与原件有细微差别。"""
    rpr = run._element.get_or_add_rPr()
    for child in list(rpr):
        rpr.remove(child)

    rfonts = rpr.makeelement(qn('w:rFonts'), {})
    rfonts.set(qn('w:hint'), 'eastAsia')
    for attr in ('w:ascii', 'w:hAnsi', 'w:eastAsia', 'w:cs'):
        rfonts.set(qn(attr), font)
    rpr.append(rfonts)

    rpr.append(rpr.makeelement(qn('w:color'), {qn('w:val'): color}))
    rpr.append(rpr.makeelement(qn('w:spacing'), {qn('w:val'): str(spacing)}))
    rpr.append(rpr.makeelement(qn('w:w'), {qn('w:val'): str(width)}))
    half = str(int(size_pt * 2))
    rpr.append(rpr.makeelement(qn('w:sz'), {qn('w:val'): half}))
    rpr.append(rpr.makeelement(qn('w:szCs'), {qn('w:val'): half}))
    rpr.append(rpr.makeelement(qn('w:lang'), {qn('w:eastAsia'): lang}))


RED_RULE_TEMPLATE = (
    '<w:r {ns}>'
    '<w:rPr><w:sz w:val="28"/></w:rPr>'
    '<mc:AlternateContent>'
    '<mc:Choice Requires="wps">'
    '<w:drawing>'
    '<wp:anchor distT="0" distB="0" distL="114300" distR="114300" simplePos="0" '
    'relativeHeight="251659264" behindDoc="0" locked="0" layoutInCell="1" allowOverlap="1">'
    '<wp:simplePos x="0" y="0"/>'
    '<wp:positionH relativeFrom="column"><wp:posOffset>-187960</wp:posOffset></wp:positionH>'
    '<wp:positionV relativeFrom="paragraph"><wp:posOffset>68580</wp:posOffset></wp:positionV>'
    '<wp:extent cx="6153785" cy="7620"/>'
    '<wp:effectExtent l="0" t="0" r="0" b="0"/>'
    '<wp:wrapNone/>'
    '<wp:docPr id="{id}" name="\u76f4\u63a5\u8fde\u63a5\u7b26 {id}"/>'
    '<wp:cNvGraphicFramePr/>'
    '<a:graphic>'
    '<a:graphicData uri="http://schemas.microsoft.com/office/word/2010/wordprocessingShape">'
    '<wps:wsp>'
    '<wps:cNvCnPr/><wps:spPr>'
    '<a:xfrm flipV="1"><a:off x="0" y="0"/><a:ext cx="6153785" cy="7620"/></a:xfrm>'
    '<a:prstGeom prst="line"><a:avLst/></a:prstGeom>'
    '<a:ln w="28575" cap="flat" cmpd="sng">'
    '<a:solidFill><a:srgbClr val="FF0000"/></a:solidFill>'
    '<a:prstDash val="solid"/><a:miter/>'
    '<a:headEnd type="none" w="med" len="med"/><a:tailEnd type="none" w="med" len="med"/>'
    '</a:ln><a:effectLst/></wps:spPr><wps:bodyPr upright="1"/>'
    '</wps:wsp></a:graphicData></a:graphic>'
    '</wp:anchor></w:drawing>'
    '</mc:Choice>'
    '<mc:Fallback><w:pict>'
    '<v:line id="_x0000_s{id}" o:spid="_x0000_s{id}" o:spt="20" '
    'style="position:absolute;left:0pt;flip:y;margin-left:-14.8pt;margin-top:5.4pt;'
    'height:0.6pt;width:484.55pt;z-index:251659264;mso-width-relative:page;'
    'mso-height-relative:page;" filled="f" stroked="t" coordsize="21600,21600">'
    '<v:fill on="f" focussize="0,0"/>'
    '<v:stroke weight="2.25pt" color="#FF0000" joinstyle="miter"/>'
    '<v:imagedata o:title=""/>'
    '<o:lock v:ext="edit" aspectratio="f"/>'
    '</v:line></w:pict></mc:Fallback>'
    '</mc:AlternateContent></w:r>'
)


def make_red_rule(shape_id):
    """公文红色反线：2.25pt 实线，#FF0000，长 484.55pt，左偏 14.8pt、下偏 5.4pt。
    命名空间手写声明——python-docx 的 nsdecls 不含 mc。"""
    ns = (
        'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
        'xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006" '
        'xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" '
        'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
        'xmlns:wps="http://schemas.microsoft.com/office/word/2010/wordprocessingShape" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
        'xmlns:v="urn:schemas-microsoft-com:vml" '
        'xmlns:o="urn:schemas-microsoft-com:office:office"'
    )
    return parse_xml(RED_RULE_TEMPLATE.format(ns=ns, id=shape_id))


def para(doc, line_pt=28, align=None, first_indent_pt=None):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.line_spacing = Pt(line_pt)
    pf.line_spacing_rule = WD_LINE_SPACING.EXACTLY
    pf.space_before = Pt(0)
    pf.space_after = Pt(0)
    if first_indent_pt:
        pf.first_line_indent = Pt(first_indent_pt)
    if align is not None:
        p.alignment = align
    return p


def add_simple(doc, text, font=BODY_FONT, size=16, bold=False, line=28,
               align=None, indent_chars=2, color=None):
    p = para(doc, line_pt=line, align=align,
             first_indent_pt=size * indent_chars if indent_chars else None)
    r = p.add_run(text)
    set_run(r, font, size, bold, color)
    return p


def add_mixed(doc, parts, line=28, indent_chars=2, base_size=16):
    p = para(doc, line_pt=line, first_indent_pt=base_size * indent_chars if indent_chars else None)
    for text, font, size, bold, color in parts:
        r = p.add_run(text)
        set_run(r, font, size, bold, color)
    return p


def add_title(doc, lines, single=True):
    """论证意见标题为单段落软换行；认定意见标题为多个独立段落。原件如此，勿统一。"""
    if single:
        p = para(doc, line_pt=30, align=WD_ALIGN_PARAGRAPH.CENTER)
        for i, ln in enumerate(lines):
            if i:
                br = p.add_run()
                set_run(br, HEAD_FONT, 22, True)
                br.add_break()
            r = p.add_run(ln)
            set_run(r, HEAD_FONT, 22, True)
    else:
        for ln in lines:
            p = para(doc, line_pt=30, align=WD_ALIGN_PARAGRAPH.CENTER)
            r = p.add_run(ln)
            set_run(r, HEAD_FONT, 22, True)


# ============================== 固定法规条款 ==============================

def law_basis_short(cfg):
    """论证意见用简版依据。"""
    meta = cfg['meta']
    return (
        '依据《邯郸市自然资源和规划局 邯郸市司法局关于做好耕地破坏程度认定鉴定工作的通知》'
        '（%s）和《中华人民共和国土地管理法》《中华人民共和国刑法》'
        '《中华人民共和国刑事诉讼法》等文件精神。' % meta['law_city']
    )


def law_basis_full(cfg):
    """认定意见用完整依据。条款顺序固定，不得改写。"""
    meta = cfg['meta']
    land_year = meta['land_year']
    county = cfg['case'].get('county', meta['county_bureau'].replace('自然资源和规划局', ''))
    return (
        '依据《中华人民共和国土地管理法》《中华人民共和国刑法》《中华人民共和国刑事诉讼法》；'
        '《国土资源部 最高人民检察院 公安部关于国土资源行政主管部门移送涉嫌国土资源犯罪案件若干意见》'
        '（国土资发〔2008〕203号）、《国务院办公厅关于坚决制止耕地“非农化”行为的通知》'
        '（国办发明电〔2020〕24号）、《自然资源部办公厅 司法部办公厅关于进一步加强协作配合做好耕地破坏程度'
        '认定鉴定工作的通知》（自然资办函〔2024〕2253号）、《自然资源部 公安部关于印发涉嫌破坏耕地'
        '犯罪案件移送指引的通知》（自然资发〔2025〕221号）、《河北省自然资源厅 河北省司法厅关于做好'
        '耕地破坏程度认定鉴定工作的通知》（冀自然资函〔2026〕108号）、《邯郸市自然资源和规划局 '
        '邯郸市司法局关于做好耕地破坏程度认定鉴定工作的通知》（%s）文件精神；'
        '%s%s年土地利用现状图、耕地认定书、土地勘测定界技术报告书、勘测定界图、现场照片等'
        '相关资料及专家组论证意见。' % (meta['law_city'], county, land_year)
    )


# ============================== 正文拼装 ==============================

def opt(cfg, key, default=None):
    """可配置措辞项。未配置时退回默认，保证老配置继续可用。"""
    v = cfg['case'].get(key)
    return default if v is None else v


def land_desc_of(agg):
    return '、'.join(
        '%s面积%s' % (name, '%s公顷（合%s亩）' % (q4(agg[k]), ha2mu(agg[k])))
        for k, name in LAND_TYPES)


def pf_desc_of(cfg):
    pf = cfg['case'].get('permanent_farmland')
    return '不涉及永久基本农田' if pf is None else '涉及永久基本农田%s' % fmt_area(pf)


def build_basic(cfg, agg):
    """一、基本情况正文。"""
    c = cfg['case']
    build_part = '建设%s' % c['project']
    if c.get('construction'):
        build_part += '，%s' % c['construction']

    plot_desc = ''
    if opt(cfg, 'include_plot_ids', False) and len(cfg['plots']) > 1:
        ids = '、'.join(x.get('id', '') for x in cfg['plots'])
        plot_desc = '该项目共涉及%d个地块（%s），' % (len(cfg['plots']), ids)

    return ('%s年，%s未经依法批准，擅自占用%s土地%s，%s。%s总占用面积%s，其中%s，%s。'
            % (c['violation_year'], c['subject'], c['location'], fmt_area(agg['area']),
               build_part, plot_desc, fmt_area(agg['area']),
               land_desc_of(agg), pf_desc_of(cfg)))


def build_status(cfg):
    """现状描述。判断句（如「已不具备恢复耕种条件」）只在显式配置时追加——
    这是实质结论，不应由模板默认替专家下。"""
    c = cfg['case']
    status = c.get('status')
    if not status:
        return ''
    judgment = c.get('status_judgment')
    if judgment:
        return '项目建成后，该地块现状为%s，%s。' % (status, judgment)
    return '项目建成后，该地块现状为%s。' % status


def build_conclusion(cfg, agg, with_preface=False):
    """结论段。前半句是「行为短语 + 总面积」，不是固定说法。

    历史样本：
      磁县     磁县人民医院涉嫌违法超占土地总面积……
      冀南新区 成现红在南城乡东陆开村东北取土总面积……
      经开区   尚璧镇西填池村非法倾倒堆放渣土总面积……
      馆陶     馆陶县水利局建设水池水面总面积……
    """
    c = cfg['case']
    phrase = opt(cfg, 'conclusion_subject_phrase', '违法占地')
    if opt(cfg, 'suspect_prefix', True) and '涉嫌' not in phrase:
        phrase = '涉嫌' + phrase
    prefix = '通过现场踏勘核查，' if with_preface else ''
    return ('%s%s%s总面积%s，其中%s，%s。'
            % (prefix, c['subject'], phrase, fmt_area(agg['area']),
               land_desc_of(agg), pf_desc_of(cfg)))


def build_summary(cfg, kind='lunzheng'):
    """综上句。动作词与毁坏程度均可配置，两份文书可用不同用词。"""
    c = cfg['case']
    action = opt(cfg, 'summary_phrase',
                 '%s建设%s' % (opt(cfg, 'action_word', '违法'), c['project']))
    damage = opt(cfg, kind + '_damage_phrase', opt(cfg, 'damage_phrase', '严重毁坏'))
    pf = c.get('permanent_farmland')
    tail = '' if pf is None else '，涉及永久基本农田%s' % fmt_area(pf)
    return ('%s%s共造成%s耕地原耕作层破坏，种植条件%s%s。'
            % (c['subject'], action, fmt_area(D(str(c['damage_ha']))), damage, tail))


# ============================== 两份文书 ==============================

def build_lunzheng(cfg, agg):
    c = cfg['case']
    meta = cfg['meta']
    L = opt(cfg, 'body_line_pt', 28)
    suspect = opt(cfg, 'suspect_prefix', True)
    mark = '涉嫌' if suspect else ''
    doc = Document()
    setup_page(doc, 3.175)   # 论证意见：左右 3.175cm

    lines = c.get('title_lunzheng') or [
        '%s%s违法占地建设%s破坏耕地程度' % (c['subject'], mark, c['project']),
        '专家论证意见',
    ]
    add_title(doc, lines, single=True)
    para(doc, line_pt=L)

    add_simple(doc,
        '%s，%s组织相关专家在%s等有关人员的陪同下，依据《邯郸市自然资源和规划局 '
        '邯郸市司法局关于做好耕地破坏程度认定鉴定工作的通知》（%s）文件要求，对%s%s违法占地'
        '建设%s破坏耕地程度进行了现场踏勘鉴定。'
        % (meta['doc_date'], meta['committee'], meta['county_bureau'],
           meta['law_city'], c['subject'], mark, c['project']), line=L)

    add_simple(doc, '一、基本情况', font=HEAD_FONT, line=L)
    add_simple(doc, build_basic(cfg, agg) + build_status(cfg), line=L)

    add_simple(doc, '二、论证依据', font=HEAD_FONT, line=L)
    add_mixed(doc, [
        ('（一）法律法规依据:', SUB_FONT, 16, False, None),
        (law_basis_short(cfg), BODY_FONT, 16, False, None),
    ], line=L)
    add_mixed(doc, [
        ('（二）地类面积依据：', SUB_FONT, 16, False, None),
        ('依据%s%s年土地利用现状图、耕地认定书、土地勘测定界技术报告书、勘测定界图'
         '以及现场照片等相关资料。' % (c.get('county', ''), meta['land_year']),
         BODY_FONT, 16, False, None),
    ], line=L)

    add_simple(doc, '三、论证结论', font=HEAD_FONT, line=L)
    add_simple(doc, build_conclusion(cfg, agg, with_preface=True), line=L)
    add_mixed(doc, [
        ('综上：', BODY_FONT, 16, True, None),
        (build_summary(cfg, 'lunzheng'), BODY_FONT, 16, False, None),
    ], line=L)

    para(doc, line_pt=L)
    add_simple(doc, '专家组成员：', line=L)
    para(doc, line_pt=L)
    add_simple(doc, meta['doc_date'], align=WD_ALIGN_PARAGRAPH.RIGHT, line=L)

    return doc


def build_rending(cfg, agg):
    c = cfg['case']
    meta = cfg['meta']
    L = opt(cfg, 'rending_line_pt', opt(cfg, 'body_line_pt', 28))
    suspect = opt(cfg, 'suspect_prefix', True)
    mark = '涉嫌' if suspect else ''
    doc = Document()
    setup_page(doc, 2.499)   # 认定意见：左右 2.499cm，与论证意见不同

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run('耕地破坏行政认定意见')
    style_doc_header_run(r, DOC_HEADER_FONT, 55, 'FF0000', spacing=40, width=75)
    set_paragraph_mark_rpr(p, source_run=r)

    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.line_spacing = 2.5
    pf.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    p._p.append(make_red_rule(1))
    r = p.add_run(meta['doc_number'])
    r.font.size = Pt(14)
    # 原件不写字体名，只靠 hint=eastAsia + 主题回退，实测在 LibreOffice 下
    # 会落到 Arial Unicode MS（行高度量差 2pt）。显式指定 eastAsia=宋体，
    # 与原件实际渲染结果一致；ascii 不设，数字仍走主题的 Calibri。
    r._element.get_or_add_rPr().insert(0, parse_xml(
        '<w:rFonts %s w:hint="eastAsia" w:eastAsia="宋体"/>' % nsdecls('w')))
    set_paragraph_mark_rpr(p, size_pt=14)

    lines = c.get('title_rending') or [
        '%s%s违法占地建设%s破坏耕地' % (c['subject'], mark, c['project']),
        '行政认定意见',
    ]
    add_title(doc, lines, single=False)

    add_simple(doc,
        '%s，根据%s破坏耕地申请，我局组织相关人员对%s%s违法占地建设%s破坏耕地情况进行了认定。'
        % (meta['doc_date'], meta['county_bureau'], c['subject'], mark, c['project']), line=L)

    add_simple(doc, '一、基本情况', font=HEAD_FONT, line=L)
    land_type_sentence = ''
    if opt(cfg, 'include_land_type_sentence', True) and c.get('land_type_sentence'):
        land_type_sentence = '按照违法占地发生上一年度地类，为%s。' % c['land_type_sentence']
    add_simple(doc, build_basic(cfg, agg) + land_type_sentence + build_status(cfg), line=L)

    add_simple(doc, '二、认定意见', font=HEAD_FONT, line=L)
    add_mixed(doc, [
        ('（一）认定依据:', SUB_FONT, 16, True, None),
        (law_basis_full(cfg), BODY_FONT, 16, False, None),
    ], line=L)
    add_mixed(doc, [
        ('（二）认定结论：', SUB_FONT, 16, True, None),
        (build_conclusion(cfg, agg), BODY_FONT, 16, False, None),
    ], line=L)
    add_mixed(doc, [
        ('综上：', BODY_FONT, 16, False, None),
        (build_summary(cfg, 'rending'), BODY_FONT, 16, False, None),
    ], line=L)

    add_simple(doc, '附件.现场照片', line=L)

    # 落款：机关名与日期共用同一居中制表位，日期自动居中于机关名下方。
    # 原件用「首行缩进 + 手打空格」对位，实测日期比机关名中心偏 81pt，不可靠。
    para(doc, line_pt=26)
    for text in (meta['issuer'], meta['doc_date']):
        p = para(doc, line_pt=26)
        p.paragraph_format.tab_stops.add_tab_stop(
            Pt(SIGNATURE_TAB_PT), WD_TAB_ALIGNMENT.CENTER)
        r = p.add_run('\t' + text)
        set_run(r, BODY_FONT, 16)

    return doc


# ============================== 入口 ==============================

def safe_save(doc, path):
    """保存 docx。文件被 WPS/Word 占用时给出可操作提示，而不是裸 traceback。"""
    try:
        doc.save(path)
    except PermissionError:
        print('\n[错误] 无法写入：%s' % path)
        print('       该文件正被 WPS / Word 打开，或所在目录只读。')
        print('       请关闭该文档后重新运行。')
        sys.exit(1)


def load_config(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    cfg_path = sys.argv[1]
    dry_run = '--dry-run' in sys.argv

    cfg = load_config(cfg_path)
    plots = cfg['plots']
    agg = aggregate(plots)

    print('=' * 72)
    print('案件：%s — %s' % (cfg['case']['subject'], cfg['case']['project']))
    print('=' * 72)
    for k, name in LAND_TYPES:
        print('  %-6s %10s 公顷 = %8s 亩' % (name, q4(agg[k]), ha2mu(agg[k])))
    print('  %-6s %10s 公顷 = %8s 亩' % ('合计', q4(agg['area']), ha2mu(agg['area'])))

    errors, warnings = validate(cfg, plots, agg)
    for w in warnings:
        print('  [警告] %s' % w)
    if errors:
        print('\n校验失败，未生成文档：')
        for e in errors:
            print('  [错误] %s' % e)
        sys.exit(1)
    print('\n面积校验通过（地块级 / 汇总 / 平方米 / 亩数 / 破坏面积）')

    if dry_run:
        print('--dry-run，跳过文档生成')
        return

    out_dir = cfg['meta']['out_dir']
    os.makedirs(out_dir, exist_ok=True)
    names = cfg['case'].get('filenames', {})
    f1 = os.path.join(out_dir, names.get('lunzheng', '%s耕地破坏论证意见.docx' % cfg['case']['subject']))
    f2 = os.path.join(out_dir, names.get('rending', '%s破坏耕地认定意见.docx' % cfg['case']['subject']))

    # 先构建两份，再统一落盘，避免写坏第一份后第二份失败
    doc1 = build_lunzheng(cfg, agg)
    doc2 = build_rending(cfg, agg)
    safe_save(doc1, f1)
    safe_save(doc2, f2)

    font_src = cfg['meta'].get('font_source')
    if font_src:
        if os.path.exists(font_src):
            import embed_font
            embed_font.embed(f2, font_src, ['方正大标宋简体'])
        else:
            print('[警告] font_source 不存在，红头字体未嵌入：%s' % font_src)

    print('\n已生成：')
    print('  %s' % f1)
    print('  %s' % f2)


if __name__ == '__main__':
    main()
