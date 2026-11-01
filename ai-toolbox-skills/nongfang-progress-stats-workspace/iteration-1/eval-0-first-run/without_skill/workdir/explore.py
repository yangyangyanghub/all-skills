# -*- coding: utf-8 -*-
import openpyxl
import os

workdir = r'C:\Users\HP\AppData\Roaming\com.ai-toolbox\skills\nongfang-progress-stats-workspace\iteration-1\eval-0-first-run\without_skill\workdir'
files = os.listdir(workdir)
xlsx_files = [f for f in files if f.endswith('.xlsx')]

output = []

# 读取明细表
detail_file = [f for f in xlsx_files if 'NF' in f][0]
output.append(f'明细表: {detail_file}')
wb = openpyxl.load_workbook(os.path.join(workdir, detail_file), data_only=True)
ws = wb.active
output.append(f'工作表名: {ws.title}')
output.append(f'总行数: {ws.max_row}, 总列数: {ws.max_column}')
output.append('\n前15行数据:')
for i in range(1, min(16, ws.max_row + 1)):
    row_data = []
    for j in range(1, min(12, ws.max_column + 1)):
        cell = ws.cell(row=i, column=j)
        val = cell.value
        if val is not None:
            row_data.append(f'{j}:{val}')
    output.append(f'行{i}: {row_data}')
wb.close()

# 读取模板
template_file = [f for f in xlsx_files if '农房' in f or '整改' in f][0]
output.append(f'\n模板表: {template_file}')
wb = openpyxl.load_workbook(os.path.join(workdir, template_file), data_only=True)
ws = wb.active
output.append(f'工作表名: {ws.title}')
output.append(f'总行数: {ws.max_row}, 总列数: {ws.max_column}')
output.append('\n前25行数据:')
for i in range(1, min(26, ws.max_row + 1)):
    row_data = []
    for j in range(1, min(13, ws.max_column + 1)):
        cell = ws.cell(row=i, column=j)
        val = cell.value
        if val is not None:
            row_data.append(f'{j}:{val}')
    output.append(f'行{i}: {row_data}')
wb.close()

# 写入文件
with open(os.path.join(workdir, 'explore_output.txt'), 'w', encoding='utf-8') as f:
    f.write('\n'.join(output))

print('探索完成，结果已写入 explore_output.txt')
