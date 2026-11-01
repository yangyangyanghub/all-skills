# -*- coding: utf-8 -*-
"""变更调查流转表 → 县级处置日报（台账县名称版 · 参数化）

基于 generate_change_survey_daily.py（v1.6）口径，唯一差异：
县分组按台账 xlsx 的「图斑编号→县名称」映射替换（邯郸 20 县口径，含冀南新区/经开区）；
未命中的图斑兜底源表「行政区名称」。业务口径与原版完全一致：
- 已填报 = 审核结束(101) + 已打回(90) + 市级待审核(95) + 省级待审核(97)
- 未填报 = 总线索 - 已填报（97 计入已填报，洋哥 2026-09-11 定档）
- 状态=4 已提交但审核阶段空 → 计入未填报
- 按未填报降序

用法：
    python generate_change_survey_daily_tz.py <源xlsx> <统计日期YYYY-MM-DD> [台账xlsx]

台账默认：E:\\2026卫片执法专项\\2026年变更调查\\进度\\20261015\\...\\fixed_..._4650个.xlsx
输出：源文件同目录「变更调查处置日报_<日期>_台账县名称.xlsx」
Sheet1 逐县汇总（10列）+ Sheet2 图斑明细（24列）
"""
import os
import sys
from datetime import datetime
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

BUSINESS_NAME = '变更调查处置'
DEFAULT_TAIZHANG = (r"E:\2026卫片执法专项\2026年变更调查\进度\20261015"
                    r"\2026年上半年变更调查新增建设线索处置(4650个)0026681329736776"
                    r"\fixed_2026年上半年变更调查新增建设线索处置_4650个.xlsx")
SUFFIX = '_台账县名称'

STAGE = {101.0: '审核结束', 90.0: '已打回', 95.0: '市级待审核', 97.0: '省级待审核'}
STATE = {1: '未处理', 2: '未提交', 4: '已提交', 10: '已审核'}
SEND_BACK = {0.0: '市级待审核', 1.0: '已打回'}

from dilei_map import DIL_EI_MAP


def get_stage(row):
    s = row['审核阶段(系统)']
    if pd.notna(s):
        return STAGE.get(s, f'未知({s})')
    return STATE.get(row['状态(系统)'], f'未知({row["状态(系统)"]})')


def get_state_text(row):
    s = row['审核阶段(系统)']
    if pd.notna(s):
        if s == 101.0: return '已审核'
        if s == 90.0: return '已打回'
        if s == 95.0: return '市级待审核'
        if s == 97.0: return '省级待审核'
    return STATE.get(row['状态(系统)'], f'未知({row["状态(系统)"]})')


def get_send_back(row):
    sb = row['打回状态(系统)']
    if pd.isna(sb):
        return ''
    return SEND_BACK.get(sb, f'未知({sb})')


def code_to_name(val, code_map):
    if pd.isna(val):
        return ''
    s = str(val).strip()
    return code_map.get(s, s + ' (?)')


def load_county_map(taizhang):
    tz = pd.read_excel(taizhang)
    tz['k'] = tz['图斑编号'].astype(str).str.strip()
    bad = []
    for k, g in tz.groupby('k'):
        names = set(g['县名称'].astype(str).str.strip())
        if len(names) > 1:
            bad.append((k, sorted(names)))
    if bad:
        print('❌ 台账重复图斑编号县名称不一致，中止:')
        for b in bad:
            print(' ', b)
        sys.exit(1)
    print(f'台账: {len(tz)} 行, 唯一图斑编号 {tz["k"].nunique()}, 县名称 {tz["县名称"].nunique()} 个')
    return dict(zip(tz['k'], tz['县名称'].astype(str).str.strip()))


def generate(src, today, taizhang=DEFAULT_TAIZHANG, out_dir=None):
    if today is None:
        today = datetime.now().strftime('%Y-%m-%d')
    if out_dir is None:
        out_dir = os.path.dirname(os.path.abspath(src))

    df = pd.read_excel(src)
    print(f'源表行数: {len(df)}')

    county_map = load_county_map(taizhang)
    keys = df['图斑编号'].astype(str).str.strip()
    df['__county_tz'] = keys.map(county_map)
    hit = df['__county_tz'].notna().sum()
    print(f'台账命中: {hit}/{len(df)} ({hit/len(df)*100:.1f}%)')

    print(f'地类对照表: 内置 DIL_EI_MAP 共 {len(DIL_EI_MAP)} 项（v1.5 定档）')
    df['__dilei_text'] = df['实地地类'].apply(lambda v: code_to_name(v, DIL_EI_MAP))

    df['__stage'] = df.apply(get_stage, axis=1)
    df['__state'] = df.apply(get_state_text, axis=1)
    df['__send_back'] = df.apply(get_send_back, axis=1)
    df['__done'] = df['审核阶段(系统)'] == 101.0
    df['__transit'] = df['审核阶段(系统)'].isin([90.0, 95.0])
    df['__circulated'] = df['县级行政区名称'].notna()
    df['__county'] = (df['__county_tz']
                      .fillna(df['行政区名称'])
                      .fillna(df['县级行政区名称'])
                      .fillna('（未分配）'))

    summary = df.groupby('__county').agg(
        总线索数=('线索编号', 'count'),
        审核结束=('__stage', lambda s: (s == '审核结束').sum()),
        已打回=('__stage', lambda s: (s == '已打回').sum()),
        市级待审核=('__stage', lambda s: (s == '市级待审核').sum()),
        省级待审核=('__stage', lambda s: (s == '省级待审核').sum()),
    ).reset_index().rename(columns={'__county': '县名称'})

    summary['已填报'] = (summary['审核结束'] + summary['已打回']
                        + summary['市级待审核'] + summary['省级待审核'])
    summary['未填报'] = (summary['总线索数'] - summary['已填报']).clip(lower=0)
    summary['填报率'] = (summary['已填报'] / summary['总线索数']).where(summary['总线索数'] > 0)
    summary['差错率'] = (summary['已打回'] / summary['已填报']).where(summary['已填报'] > 0)

    summary = summary.sort_values(
        by=['未填报', '总线索数', '县名称'], ascending=[False, False, True],
    ).reset_index(drop=True)

    print()
    print('逐县汇总（台账县名称）:')
    print(summary.to_string(index=False))

    stage_cols = ['审核结束', '已打回', '市级待审核', '省级待审核', '未填报']
    formula_check = summary[stage_cols].sum(axis=1)
    formula_ok = (formula_check == summary['总线索数']).all()
    print(f'\n公式校验: {"✓ 通过" if formula_ok else "❌ 失败"}')
    if not formula_ok:
        bad = summary.loc[formula_check != summary['总线索数'], ['县名称', '总线索数'] + stage_cols]
        print(bad.to_string(index=False))

    df_sorted = df.sort_values(
        by=['__done', '__transit', '县级行政区名称', '__stage', '图斑编号'],
        ascending=[False, False, True, True, True],
    ).reset_index(drop=True)

    out_cols = [
        ('序号', None, 6),
        ('县级行政区', '__county', 12),
        ('线索编号', '线索编号', 22),
        ('图斑编号', '图斑编号', 22),
        ('监测类型', '监测类型', 12),
        ('图斑面积(亩)', '图斑面积(亩)', 12),
        ('项目名称', '项目名称', 22),
        ('核实认定意见', '核实认定意见', 14),
        ('分类', '分类', 14),
        ('审核阶段', '__stage', 14),
        ('状态', '__state', 10),
        ('打回状态', '__send_back', 12),
        ('整改情况', '整改情况', 14),
        ('处置', '__done', 8),
        ('在途', '__transit', 8),
        ('流转', '__circulated', 8),
        ('图斑特征', '图斑特征', 12),
        ('实地地类(代码)', '实地地类', 10),
        ('实地地类(名称)', '__dilei_text', 18),
        ('外业时间', '外业时间', 18),
        ('核查时间', '核查时间', 18),
        ('核查人', '执行人员(系统)', 10),
        ('图斑名称', '图斑名称', 18),
        ('线索备注', '线索备注', 24),
    ]

    wb = Workbook()
    header_font = Font(name='微软雅黑', size=10, bold=True, color='FFFFFF')
    header_fill = PatternFill('solid', fgColor='4472C4')
    cell_font = Font(name='微软雅黑', size=9)
    total_font = Font(name='微软雅黑', size=9, bold=True)
    total_fill = PatternFill('solid', fgColor='FFF2CC')
    thin = Side(border_style='thin', color='B4B4B4')
    border = Border(top=thin, left=thin, right=thin, bottom=thin)
    center = Alignment(horizontal='center', vertical='center', wrap_text=True)
    left = Alignment(horizontal='left', vertical='center', wrap_text=True)

    ws1 = wb.active
    ws1.title = '逐县汇总'
    headers = ['县名称', '总线索数', '审核结束', '已打回', '市级待审核', '省级待审核',
               '已填报', '未填报', '填报率', '差错率']
    last_col = get_column_letter(len(headers))
    ws1.merge_cells(f'A1:{last_col}1')
    ws1.cell(1, 1, f'{BUSINESS_NAME}逐县汇总·台账县名称（{today}）').font = Font(name='微软雅黑', size=14, bold=True)
    ws1.cell(1, 1).alignment = center
    ws1.merge_cells(f'A2:{last_col}2')
    note = ('公式：已填报 = 审核结束 + 已打回 + 市级待审核 + 省级待审核；'
            '未填报 = 总线索 - 已填报；填报率 = 已填报 ÷ 总线索；差错率 = 已打回 ÷ 已填报；按未填报降序排列；'
            '县名称按台账「图斑编号→县名称」修正')
    ws1.cell(2, 1, note).font = Font(name='微软雅黑', size=9, italic=True, color='808080')
    ws1.cell(2, 1).alignment = center
    for c, h in enumerate(headers, 1):
        cell = ws1.cell(3, c, h)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center
        cell.border = border
    for r, row in summary.iterrows():
        excel_r = 4 + r
        ws1.cell(excel_r, 1, row['县名称'])
        for c, h in enumerate(headers[1:8], 2):
            ws1.cell(excel_r, c, int(row[h]))
        pc = ws1.cell(excel_r, 9, row['填报率'] if pd.notna(row['填报率']) else None)
        pc.number_format = '0.0%'
        ec = ws1.cell(excel_r, 10, row['差错率'] if pd.notna(row['差错率']) else None)
        ec.number_format = '0.0%'
    total_r = 4 + len(summary)
    ws1.cell(total_r, 1, '合计')
    for c, h in enumerate(['总线索数', '审核结束', '已打回', '市级待审核', '省级待审核', '已填报', '未填报'], 2):
        ws1.cell(total_r, c, int(summary[h].sum()))
    tp = ws1.cell(total_r, 9, summary['已填报'].sum() / summary['总线索数'].sum())
    tp.number_format = '0.0%'
    te = ws1.cell(total_r, 10, summary['已打回'].sum() / summary['已填报'].sum() if summary['已填报'].sum() else None)
    te.number_format = '0.0%'
    for c in range(1, len(headers) + 1):
        cell = ws1.cell(total_r, c)
        cell.font = total_font
        cell.fill = total_fill
        cell.border = border
        cell.alignment = center
    for r in range(4, total_r):
        for c in range(1, len(headers) + 1):
            cell = ws1.cell(r, c)
            cell.font = cell_font
            cell.border = border
            cell.alignment = center if c > 1 else left
    for i, w in enumerate([14, 10, 10, 10, 12, 12, 10, 10, 10, 10], 1):
        ws1.column_dimensions[get_column_letter(i)].width = w
    ws1.freeze_panes = 'B4'
    ws1.auto_filter.ref = f'A3:{get_column_letter(len(headers))}{total_r - 1}'

    ws2 = wb.create_sheet('图斑明细')
    for c, (h, col, w) in enumerate(out_cols, 1):
        cell = ws2.cell(1, c, h)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center
        cell.border = border
        ws2.column_dimensions[get_column_letter(c)].width = w
    for r_idx, (_, row) in enumerate(df_sorted.iterrows(), 2):
        for c, (h, col, w) in enumerate(out_cols, 1):
            if col is None or col not in row.index:
                v = r_idx - 1 if col is None else None
            else:
                v = row[col]
                if type(v).__name__ in ('bool', 'bool_'):
                    v = '是' if v else '否'
                elif pd.isna(v):
                    v = None
            cell = ws2.cell(r_idx, c, v)
            cell.font = cell_font
            cell.border = border
            cell.alignment = left if c in (7, 8, 9, 13, 17, 24) else center
    ws2.freeze_panes = 'C2'
    ws2.auto_filter.ref = f'A1:{get_column_letter(len(out_cols))}{1 + len(df_sorted)}'

    for ws in (ws1, ws2):
        ws.page_setup.orientation = ws.ORIENTATION_LANDSCAPE
        ws.page_setup.paperSize = ws.PAPERSIZE_A4
        ws.page_setup.fitToWidth = 1
        ws.page_setup.fitToHeight = 1
        ws.sheet_properties.pageSetUpPr.fitToPage = True
        ws.print_options.horizontalCentered = True
        ws.page_margins.left = 0.3
        ws.page_margins.right = 0.3
        ws.page_margins.top = 0.4
        ws.page_margins.bottom = 0.4

    out_path = os.path.join(out_dir, f'{BUSINESS_NAME}日报_{today}{SUFFIX}.xlsx')
    wb.save(out_path)
    print(f'\n输出: {out_path}')
    print(f'明细行数: {len(df_sorted)}')
    return out_path


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print('用法: python generate_change_survey_daily_tz.py <源xlsx> <统计日期YYYY-MM-DD> [台账xlsx]')
        sys.exit(1)
    generate(
        src=sys.argv[1],
        today=sys.argv[2],
        taizhang=sys.argv[3] if len(sys.argv) > 3 else DEFAULT_TAIZHANG,
    )
