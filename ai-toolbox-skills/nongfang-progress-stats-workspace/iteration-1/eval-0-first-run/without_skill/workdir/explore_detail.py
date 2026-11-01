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

# 读取所有表头（前4行）
output.append('\n=== 明细表表头（前4行，所有列）===')
for i in range(1, 5):
    row_data = []
    for j in range(1, ws.max_column + 1):
        cell = ws.cell(row=i, column=j)
        val = cell.value
        if val is not None:
            row_data.append(f'列{j}:{val}')
    output.append(f'行{i}: {row_data}')

# 读取第5行（第一条数据）的所有列
output.append('\n=== 第5行数据（所有列）===')
row_data = []
for j in range(1, ws.max_column + 1):
    cell = ws.cell(row=5, column=j)
    val = cell.value
    if val is not None:
        row_data.append(f'列{j}:{val}')
output.append(f'行5: {row_data}')

# 统计每个县的数据
output.append('\n=== 按县统计 ===')
county_data = {}
current_county = None
for i in range(5, ws.max_row + 1):
    seq = ws.cell(row=i, column=1).value
    county = ws.cell(row=i, column=2).value
    project = ws.cell(row=i, column=3).value
    tuban = ws.cell(row=i, column=4).value
    
    if county:
        current_county = county
    
    if current_county and project:
        if current_county not in county_data:
            county_data[current_county] = {'count': 0, 'tuban_sum': 0}
        county_data[current_county]['count'] += 1
        if tuban:
            county_data[current_county]['tuban_sum'] += tuban

for county, data in county_data.items():
    output.append(f'{county}: {data["count"]}批次, {data["tuban_sum"]}图斑')

wb.close()

# 写入文件
with open(os.path.join(workdir, 'explore_detail_output.txt'), 'w', encoding='utf-8') as f:
    f.write('\n'.join(output))

print('明细表探索完成')
