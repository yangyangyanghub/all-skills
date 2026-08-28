# -*- coding: utf-8 -*-
"""
土地执法遥感监测非农违法图斑清单生成脚本
生成包含11列字段的非农违法图斑清单Excel
"""

import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
import sys
import os

def generate_illegal_list(input_file, output_file):
    """
    生成非农违法图斑清单

    参数:
        input_file: 输入的土地执法遥感监测检索明细表Excel文件路径
        output_file: 输出的非农违法图斑清单Excel文件路径
    """

    # 读取数据
    df = pd.read_excel(input_file)

    # 数据筛选：核实后图斑中的非农违法图斑
    verified = df[df['图斑状态'].isna() | (df['图斑状态'] == '拆分')]
    illegal = verified[verified['核实认定意见'].str.contains('非农违法', na=False)].copy()
    # 排序：按县名称升序 + 非农违法耕地面积降序
    illegal = illegal.sort_values(['县级行政区名称', '非农违法耕地面积（亩）'], ascending=[True, False])

    # 从输入文件名或监测批次推断年月，用于标题
    title_suffix = ''
    if len(illegal) > 0 and pd.notna(illegal.iloc[0].get('监测批次')):
        batch = str(illegal.iloc[0]['监测批次'])
        # 尝试从批次名如"七月一批"推断
        month_map = {'一': '1', '二': '2', '三': '3', '四': '4', '五': '5', '六': '6',
                     '七': '7', '八': '8', '九': '9', '十': '10', '十一': '11', '十二': '12'}
        for cn, num in month_map.items():
            if batch.startswith(cn):
                title_suffix = f'{num}月'
                break

    wb = Workbook()
    ws = wb.active
    ws.title = '非农违法清单'

    # 样式
    header_font = Font(name='微软雅黑', size=10, bold=True, color='FFFFFF')
    header_fill = PatternFill(start_color='4472C4', end_color='4472C4', fill_type='solid')
    data_font = Font(name='微软雅黑', size=9)
    total_font = Font(name='微软雅黑', size=9, bold=True)
    total_fill = PatternFill(start_color='FFF2CC', end_color='FFF2CC', fill_type='solid')
    thin_border = Border(
        left=Side(style='thin'), right=Side(style='thin'),
        top=Side(style='thin'), bottom=Side(style='thin')
    )
    center_align = Alignment(horizontal='center', vertical='center', wrap_text=True)
    left_align = Alignment(horizontal='left', vertical='center', wrap_text=True)

    # 标题
    ws.merge_cells('A1:K1')
    title_cell = ws['A1']
    title_cell.value = f'土地执法遥感监测{title_suffix}非农违法图斑清单'
    title_cell.font = Font(name='微软雅黑', size=12, bold=True)
    title_cell.alignment = Alignment(horizontal='center', vertical='center')
    ws.row_dimensions[1].height = 28

    # 表头（11列）
    headers = ['序号', '县名称', '监测批次', '线索编号', '项目名称', '项目主体',
               '非农违法土地用途', '非农违法面积（亩）', '非农违法耕地面积（亩）',
               '非农违法基本农田面积（亩）', '备注']
    for col_idx, val in enumerate(headers, 1):
        cell = ws.cell(row=2, column=col_idx, value=val)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center_align
        cell.border = thin_border

    # 列宽
    col_widths = {'A': 5, 'B': 10, 'C': 10, 'D': 28, 'E': 30, 'F': 18,
                  'G': 16, 'H': 14, 'I': 16, 'J': 18, 'K': 20}
    for col_letter, width in col_widths.items():
        ws.column_dimensions[col_letter].width = width

    # 数据行
    row_num = 3
    for idx, (_, row) in enumerate(illegal.iterrows(), 1):
        # 备注：整改情况（如有）
        remark = ''
        if pd.notna(row.get('整改情况')):
            remark = str(row['整改情况'])

        row_data = [
            idx,
            row['县级行政区名称'],
            row['监测批次'],
            row['线索编号'],
            row['项目名称'] if pd.notna(row.get('项目名称')) else '',
            row['项目主体'] if pd.notna(row.get('项目主体')) else '',
            row['非农违法土地用途'] if pd.notna(row.get('非农违法土地用途')) else '',
            round(row['非农违法面积（亩）'], 2),
            round(row['非农违法耕地面积（亩）'], 2),
            round(row['非农违法永久基本农田面积（亩）'], 2),
            remark
        ]
        for col_idx, val in enumerate(row_data, 1):
            cell = ws.cell(row=row_num, column=col_idx, value=val)
            cell.font = data_font
            cell.border = thin_border
            cell.alignment = left_align if col_idx in [5, 6, 7, 11] else center_align
        row_num += 1

    # 合计行
    total_row = row_num
    ws.cell(row=total_row, column=1, value='合计').font = total_font
    ws.cell(row=total_row, column=8, value=round(illegal['非农违法面积（亩）'].sum(), 2)).font = total_font
    ws.cell(row=total_row, column=9, value=round(illegal['非农违法耕地面积（亩）'].sum(), 2)).font = total_font
    ws.cell(row=total_row, column=10, value=round(illegal['非农违法永久基本农田面积（亩）'].sum(), 2)).font = total_font
    for col_idx in range(1, 12):
        cell = ws.cell(row=total_row, column=col_idx)
        cell.fill = total_fill
        cell.border = thin_border
        cell.alignment = center_align

    ws.freeze_panes = 'A3'

    # A4横向打印设置
    ws.page_setup.paperSize = ws.PAPERSIZE_A4
    ws.page_setup.orientation = 'landscape'
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0

    # 保存
    wb.save(output_file)
    print(f'清单已生成：{output_file}')
    print(f'共 {len(illegal)} 个非农违法图斑')
    print(f'排序：按县名称升序 + 非农违法耕地面积降序')


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print('用法：python generate_illegal_list.py <输入文件> <输出文件>')
        print('示例：python generate_illegal_list.py "遥感检测检索明细表.xlsx" "非农违法图斑清单.xlsx"')
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    if not os.path.exists(input_file):
        print(f'错误：输入文件不存在：{input_file}')
        sys.exit(1)

    generate_illegal_list(input_file, output_file)
