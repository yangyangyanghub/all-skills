# -*- coding: utf-8 -*-
"""变更调查新增建设线索 · 分县地类统计一览表

每县一行，列 = 主要地类（个数 + 面积），次要地类归入「其他」：
县名称 | 总线索数 | 农村宅基地 | 工业用地 | 物流仓储用地 | 商业服务业设施用地 | 其他地类 | 未认定

用法：python generate_county_dilei.py <源xlsx> [统计日期YYYY-MM-DD]
输出：<源目录>/变更调查分县地类统计_<日期>.xlsx
"""
import sys
import os
from datetime import datetime

import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dilei_map import DIL_EI_MAP

if len(sys.argv) < 2:
    print('用法: python generate_county_dilei.py <源xlsx> [统计日期YYYY-MM-DD]')
    sys.exit(1)
SRC = sys.argv[1]
OUT_DIR = os.path.dirname(SRC)
TODAY = sys.argv[2] if len(sys.argv) > 2 else datetime.now().strftime('%Y-%m-%d')

# 主要地类（其余归入 其他）
MAIN_DILEI = ['农村宅基地', '工业用地', '物流仓储用地', '商业服务业设施用地']


def main():
    df = pd.read_excel(SRC)
    print(f'源表行数: {len(df)}')

    df['__county'] = df['行政区名称'].fillna(df['县级行政区名称']).fillna('（未分配）')

    def to_name(v):
        if pd.isna(v):
            return '（未认定）'
        return DIL_EI_MAP.get(str(v).strip(), f'{v} (?)')

    df['__dilei'] = df['实地地类'].apply(to_name)
    df['__area'] = pd.to_numeric(df['图斑面积(亩)'], errors='coerce').fillna(0)

    # 每个县的地类分组统计
    rows = []
    for county, g in df.groupby('__county'):
        total = len(g)
        row = {'县名称': county, '总线索数': total}
        for d in MAIN_DILEI:
            sub = g[g['__dilei'] == d]
            row[d] = (len(sub), sub['__area'].sum())
        other = g[~g['__dilei'].isin(MAIN_DILEI) & (g['__dilei'] != '（未认定）')]
        row['其他地类'] = (len(other), other['__area'].sum())
        und = g[g['__dilei'] == '（未认定）']
        row['未认定'] = (len(und), und['__area'].sum())
        rows.append(row)

    out = pd.DataFrame(rows).sort_values('总线索数', ascending=False).reset_index(drop=True)
    print('\n' + out.to_string(index=False))

    # 写 Excel
    wb = Workbook()
    ws = wb.active
    ws.title = '分县地类统计'

    header_font = Font(name='微软雅黑', size=10, bold=True, color='FFFFFF')
    header_fill = PatternFill('solid', fgColor='4472C4')
    cell_font = Font(name='微软雅黑', size=9)
    total_font = Font(name='微软雅黑', size=9, bold=True)
    total_fill = PatternFill('solid', fgColor='FFF2CC')
    thin = Side(border_style='thin', color='B4B4B4')
    border = Border(top=thin, left=thin, right=thin, bottom=thin)
    center = Alignment(horizontal='center', vertical='center', wrap_text=True)
    left = Alignment(horizontal='left', vertical='center', wrap_text=True)

    n_cols = 7
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=n_cols)
    ws.cell(1, 1, f'变更调查新增建设线索·分县地类统计（{TODAY}）').font = Font(name='微软雅黑', size=14, bold=True)
    ws.cell(1, 1).alignment = center
    ws.row_dimensions[1].height = 26

    headers = ['县（区）', '总线索数'] + MAIN_DILEI + ['其他地类', '未认定']
    for col, h in enumerate(headers, 1):
        c = ws.cell(2, col, h)
        c.font = header_font
        c.fill = header_fill
        c.alignment = center
        c.border = border
    ws.row_dimensions[2].height = 24

    def fmt(v):
        n, a = v
        return f'{n}个 {a:.1f}亩' if a else f'{n}个'

    for r, row in enumerate(out.itertuples(index=False), start=3):
        ws.cell(r, 1, row.县名称)
        ws.cell(r, 2, row.总线索数)
        for i, h in enumerate(headers[2:], start=3):
            ws.cell(r, i, fmt(getattr(row, h)))
        ws.row_dimensions[r].height = 20
        for col in range(1, n_cols + 1):
            c = ws.cell(r, col)
            c.font = cell_font
            c.border = border
            c.alignment = left if col == 1 else center

    # 合计行
    tr = 3 + len(out)
    ws.cell(tr, 1, '合计')
    ws.cell(tr, 2, out['总线索数'].sum())
    for i, h in enumerate(headers[2:], start=3):
        n = sum(getattr(r, h)[0] for r in out.itertuples(index=False))
        a = sum(getattr(r, h)[1] for r in out.itertuples(index=False))
        ws.cell(tr, i, fmt((n, a)))
    for col in range(1, n_cols + 1):
        c = ws.cell(tr, col)
        c.font = total_font
        c.fill = total_fill
        c.border = border
        c.alignment = left if col == 1 else center

    widths = [14, 10, 16, 15, 15, 16, 15, 12]
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.freeze_panes = 'B3'
    ws.auto_filter.ref = f'A2:G{2 + len(out)}'

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

    out_path = os.path.join(OUT_DIR, f'变更调查分县地类统计_{TODAY}.xlsx')
    wb.save(out_path)
    print(f'\n输出: {out_path}')


if __name__ == '__main__':
    main()
