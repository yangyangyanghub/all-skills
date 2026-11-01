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

# 统计每个县的数据
output.append('=== 按县统计明细 ===')
county_data = {}
current_county = None
for i in range(5, ws.max_row + 1):
    seq = ws.cell(row=i, column=1).value
    county = ws.cell(row=i, column=2).value
    project = ws.cell(row=i, column=3).value
    tuban = ws.cell(row=i, column=4).value
    yingjiao = ws.cell(row=i, column=5).value  # 应缴
    shijiao = ws.cell(row=i, column=6).value   # 实缴
    weijiao = ws.cell(row=i, column=7).value   # 未缴
    
    if county:
        current_county = county
    
    if current_county and project:
        if current_county not in county_data:
            county_data[current_county] = {
                'count': 0, 
                'tuban_sum': 0,
                'yingjiao_sum': 0,
                'shijiao_sum': 0,
                'weijiao_sum': 0
            }
        county_data[current_county]['count'] += 1
        if tuban:
            county_data[current_county]['tuban_sum'] += tuban
        if yingjiao:
            county_data[current_county]['yingjiao_sum'] += yingjiao
        if shijiao:
            county_data[current_county]['shijiao_sum'] += shijiao
        if weijiao:
            county_data[current_county]['weijiao_sum'] += weijiao

total_count = 0
total_tuban = 0
total_yingjiao = 0
total_shijiao = 0
total_weijiao = 0

for county, data in sorted(county_data.items()):
    output.append(f'{county}: {data["count"]}批次, {data["tuban_sum"]}图斑, 应缴{data["yingjiao_sum"]}, 实缴{data["shijiao_sum"]}, 未缴{data["weijiao_sum"]}')
    total_count += data['count']
    total_tuban += data['tuban_sum']
    total_yingjiao += data['yingjiao_sum']
    total_shijiao += data['shijiao_sum']
    total_weijiao += data['weijiao_sum']

output.append(f'\n总计: {total_count}批次, {total_tuban}图斑, 应缴{total_yingjiao}, 实缴{total_shijiao}, 未缴{total_weijiao}')

wb.close()

# 写入文件
with open(os.path.join(workdir, 'county_stats.txt'), 'w', encoding='utf-8') as f:
    f.write('\n'.join(output))

print('统计完成')
