# -*- coding: utf-8 -*-
"""大运河排查 / 专项整治 业务表 → 流程进度清单

子类型 B：以"状态(系统)+审核阶段(系统)+打回状态(系统)"为主轴
输出 2 个 Sheet：逐县汇总（15 列）+ 图斑明细（23 列）
"""
import os
import sys
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

# 状态机映射
STAGE = {101.0: '审核结束', 90.0: '已打回', 95.0: '市级待审核', 97.0: '省级待审核'}
STATE = {1: '未处理', 2: '未提交', 4: '已提交', 10: '已审核'}
SEND_BACK = {0.0: '市级待审核', 1.0: '已打回'}


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


def get_passed(row):
    s = row['审核阶段(系统)']
    if s in (101.0, 97.0): return '通过'
    if pd.isna(s): return '待填报'
    return '未通过'


def county_filled(row):
    s = row['审核阶段(系统)']
    return pd.notna(s) and s in (101.0, 90.0, 95.0, 97.0)


def city_reviewed(row):
    s = row['审核阶段(系统)']
    return pd.notna(s) and s in (101.0, 90.0, 97.0)


def prov_returned(row):
    s = row['审核阶段(系统)']
    sb = row['打回状态(系统)']
    return s == 95.0 and sb == 1.0


def generate(src_xlsx, out_xlsx=None, business_name='业务'):
    if out_xlsx is None:
        base, ext = os.path.splitext(src_xlsx)
        from datetime import datetime
        date_str = datetime.now().strftime('%Y-%m-%d')
        out_xlsx = f"{os.path.dirname(base)}\\{business_name}图斑清单_{date_str}{ext}"

    df = pd.read_excel(src_xlsx)
    # 县分组：优先「行政区名称」（完整），回退「县级行政区名称」——县级行政区名称可能大面积缺失
    df['__county'] = df['行政区名称'].fillna(df['县级行政区名称']).fillna('（未分配）')
    # 计算派生列
    df['__stage'] = df.apply(get_stage, axis=1)
    df['__state'] = df.apply(get_state_text, axis=1)
    df['__send_back'] = df.apply(get_send_back, axis=1)
    df['__passed'] = df.apply(get_passed, axis=1)
    df['__county_filled'] = df.apply(county_filled, axis=1)
    df['__city_reviewed'] = df.apply(city_reviewed, axis=1)
    df['__prov_returned'] = df.apply(prov_returned, axis=1)

    # 逐县汇总
    summary = df.groupby('__county').agg(
        总数=('线索编号', 'count'),
        县级填报=('__county_filled', lambda s: s.sum()),
        市级已审核=('__city_reviewed', lambda s: s.sum()),
        审核结束=('__stage', lambda s: (s == '审核结束').sum()),
        已打回=('__stage', lambda s: (s == '已打回').sum()),
        市级待审核=('__stage', lambda s: (s == '市级待审核').sum()),
        省级退回=('__prov_returned', lambda s: s.sum()),
        通过=('__passed', lambda s: (s == '通过').sum()),
        未通过=('__passed', lambda s: (s == '未通过').sum()),
        待填报=('__passed', lambda s: (s == '待填报').sum()),
        未处理=('__stage', lambda s: (s == '未处理').sum()),
        未提交=('__stage', lambda s: (s == '未提交').sum()),
        已提交=('__stage', lambda s: (s == '已提交').sum()),
        面积合计=('图斑面积(亩)', 'sum'),
    ).reset_index()

    # 排序
    df_sorted = df.sort_values(
        by=['__county_filled', '__passed', '__county', '乡镇行政区名称', '__stage', '图斑编号'],
        ascending=[False, False, True, True, True, True],
    ).reset_index(drop=True)

    # 写 Excel
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

    # —— Sheet 1: 逐县汇总 ——
    ws1 = wb.active
    ws1.title = '逐县汇总'
    ws1.merge_cells('A1:O1')
    ws1.cell(1, 1, f'{business_name}逐县汇总').font = Font(name='微软雅黑', size=14, bold=True)
    ws1.cell(1, 1).alignment = center
    ws1.merge_cells('A2:O2')
    ws1.cell(2, 1, '业务规则：县级填报=审核结束+已打回+市级待审核+省级待审核；市级已审核=审核结束+已打回+省级待审核；省级退回=市级待审核且打回状态=已打回').font = Font(name='微软雅黑', size=9, italic=True, color='808080')

    headers = ['县(区)', '总数', '县级填报', '市级已审核', '审核结束', '已打回',
               '市级待审核', '省级退回', '通过', '未通过', '待填报',
               '未处理', '未提交', '已提交', '面积合计(亩)']
    for col, h in enumerate(headers, 1):
        c = ws1.cell(3, col, h)
        c.font = header_font
        c.fill = header_fill
        c.alignment = center
        c.border = border

    for r, row in enumerate(summary.itertuples(index=False), start=4):
        for col, val in enumerate(row, start=1):
            v = round(val, 2) if isinstance(val, float) and pd.notna(val) else (int(val) if isinstance(val, bool) else val)
            c = ws1.cell(r, col, v)
            c.font = cell_font
            c.alignment = center if col > 1 else left
            c.border = border

    # 合计行
    total_row = 4 + len(summary)
    ws1.cell(total_row, 1, '合计').font = total_font
    ws1.cell(total_row, 1).fill = total_fill
    ws1.cell(total_row, 1).alignment = center
    ws1.cell(total_row, 1).border = border
    for col in range(2, len(headers) + 1):
        col_name = summary.columns[col - 2 + 1]  # 跳过第 1 列县级行政区名称
        if col_name == '面积合计':
            v = round(summary[col_name].sum(), 2)
        else:
            v = int(summary[col_name].sum())
        c = ws1.cell(total_row, col, v)
        c.font = total_font
        c.fill = total_fill
        c.alignment = center
        c.border = border

    widths = [12, 8, 10, 12, 10, 10, 12, 10, 8, 10, 10, 10, 10, 10, 14]
    for i, w in enumerate(widths, 1):
        ws1.column_dimensions[get_column_letter(i)].width = w

    # —— Sheet 2: 图斑明细 ——
    ws2 = wb.create_sheet('图斑明细')
    out_cols = [
        ('序号', None, 6),
        ('县级行政区', '__county', 10),
        ('乡镇', '乡镇行政区名称', 14),
        ('线索编号', '线索编号', 18),
        ('图斑编号', '图斑编号', 18),
        ('项目名称', '项目名称', 22),
        ('项目主体', '项目主体', 14),
        ('图斑面积(亩)', '图斑面积(亩)', 12),
        ('现场核查描述', '现场核查描述', 30),
        ('核实认定意见', '核实认定意见', 14),
        ('审核阶段', '__stage', 14),
        ('状态', '__state', 10),
        ('打回状态', '__send_back', 12),
        ('是否通过审核', '__passed', 12),
        ('县级填报', '__county_filled', 10),
        ('市级已审核', '__city_reviewed', 10),
        ('省级退回', '__prov_returned', 10),
        ('核查人', '执行人员(系统)', 10),
        ('核查时间', '核查时间', 18),
        ('备注', '备注说明', 24),
    ]
    ws2.merge_cells(start_row=1, start_column=1, end_row=1, end_column=len(out_cols))
    ws2.cell(1, 1, f'{business_name}图斑清单').font = Font(name='微软雅黑', size=14, bold=True)
    ws2.cell(1, 1).alignment = center
    ws2.row_dimensions[1].height = 24
    for col, (label, _, _) in enumerate(out_cols, 1):
        c = ws2.cell(2, col, label)
        c.font = header_font
        c.fill = header_fill
        c.alignment = center
        c.border = border
    ws2.row_dimensions[2].height = 28

    # 转换布尔为 是/否
    for r, (_, row) in enumerate(df_sorted.iterrows(), start=3):
        for col, (label, src, _) in enumerate(out_cols, start=1):
            if src is None:
                val = r - 2
            else:
                val = row[src]
                if src in ('__county_filled', '__city_reviewed', '__prov_returned'):
                    val = '是' if val else '否'
                elif pd.isna(val):
                    val = ''
            c = ws2.cell(r, col, val)
            c.font = cell_font
            c.alignment = center if col in (1, 4, 5, 11, 12, 13, 14, 15, 16, 17, 18) else left
            c.border = border
        ws2.row_dimensions[r].height = 22

    for col, (_, _, width) in enumerate(out_cols, 1):
        ws2.column_dimensions[get_column_letter(col)].width = width

    ws2.freeze_panes = 'C3'
    ws2.auto_filter.ref = f'A2:{get_column_letter(len(out_cols))}{2 + len(df_sorted)}'

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

    wb.save(out_xlsx)
    print(f'输出: {out_xlsx}')
    print(f'明细行数: {len(df_sorted)}')
    print('\n逐县汇总:')
    print(summary.to_string(index=False))
    return out_xlsx


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('用法: python generate_business_checklist.py <源xlsx> [业务名] [输出xlsx]')
        sys.exit(1)
    src = sys.argv[1]
    name = sys.argv[2] if len(sys.argv) > 2 else '业务'
    out = sys.argv[3] if len(sys.argv) > 3 else None
    generate(src, out, name)
