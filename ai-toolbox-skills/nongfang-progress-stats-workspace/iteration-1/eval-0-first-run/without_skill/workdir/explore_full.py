# -*- coding: utf-8 -*-
import openpyxl
import os

workdir = r'C:\Users\HP\AppData\Roaming\com.ai-toolbox\skills\nongfang-progress-stats-workspace\iteration-1\eval-0-first-run\without_skill\workdir'
files = os.listdir(workdir)
xlsx_files = [f for f in files if f.endswith('.xlsx')]

output = []

# 读取明细表
detail_file = [f for f in xlsx_files if 'NF' in f][0]
wb = openpyxl.load_workbook(os.path.join(workdir, detail_file), data_only=True)
ws = wb.active

# 读取前4行的所有列（包括合并单元格）
output.append('=== 明细表完整表头 ===')
for i in range(1, 5):
    row_data = []
    for j in range(1, ws.max_column + 1):
        cell = ws.cell(row=i, column=j)
        val = cell.value
        if val is not None:
            row_data.append(f'列{j}:{val}')
    output.append(f'行{i}: {row_data}')

# 读取第5行的所有列
output.append('\n=== 第5行完整数据 ===')
row_data = []
for j in range(1, ws.max_column + 1):
    cell = ws.cell(row=5, column=j)
    val = cell.value
    if val is not None:
        row_data.append(f'列{j}:{val}')
output.append(f'行5: {row_data}')

# 检查合并单元格
output.append('\n=== 合并单元格 ===')
for merged_range in ws.merged_cells.ranges:
    output.append(str(merged_range))

wb.close()

# 写入文件
with open(os.path.join(workdir, 'explore_full.txt'), 'w', encoding='utf-8') as f:
    f.write('\n'.join(output))

print('完整探索完成')
