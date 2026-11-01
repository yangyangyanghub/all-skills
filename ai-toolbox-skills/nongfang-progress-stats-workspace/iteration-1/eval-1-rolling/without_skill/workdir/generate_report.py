# -*- coding: utf-8 -*-
import openpyxl
import json
from copy import copy

# 读取基线数据
with open('.nongfang_baseline.json', 'r', encoding='utf-8') as f:
    baseline = json.load(f)

# 读取今天的数据
with open('today_data.json', 'r', encoding='utf-8') as f:
    today_raw = json.load(f)

# 修复县名中的换行符问题
today_data = {}
for county, data in today_raw['today_data'].items():
    fixed_county = county.replace('\n', '')
    today_data[fixed_county] = data

# 修复delta_counties中的县名
delta_counties = []
for item in today_raw['delta_counties']:
    fixed_county = item['county'].replace('\n', '')
    delta_counties.append({
        'county': fixed_county,
        'delta_batches': item['delta_batches'],
        'delta_patrols': item['delta_patrols']
    })

# 读取模板文件
template_wb = openpyxl.load_workbook('农房整治工作卷宗整改进展统计表(修改后).xlsx')
template_ws = template_wb.active

# 创建新的工作簿
new_wb = openpyxl.Workbook()
new_ws = new_wb.active
new_ws.title = template_ws.title

# 复制模板的格式和内容
for row in template_ws.iter_rows():
    for cell in row:
        new_cell = new_ws.cell(row=cell.row, column=cell.column, value=cell.value)
        # 复制样式
        if cell.has_style:
            new_cell.font = copy(cell.font)
            new_cell.border = copy(cell.border)
            new_cell.fill = copy(cell.fill)
            new_cell.number_format = copy(cell.number_format)
            new_cell.protection = copy(cell.protection)
            new_cell.alignment = copy(cell.alignment)

# 复制列宽
for col in template_ws.column_dimensions:
    if col in template_ws.column_dimensions:
        new_ws.column_dimensions[col].width = template_ws.column_dimensions[col].width

# 复制行高
for row in template_ws.row_dimensions:
    if row in template_ws.row_dimensions:
        new_ws.row_dimensions[row].height = template_ws.row_dimensions[row].height

# 更新标题（第1行第1列）
new_ws['A1'] = '农房整治卷宗整改进展统计表\n（10月30日）'

# 县名映射（模板中的顺序）
county_order = [
    '永年区', '广平县', '武安市', '临漳县', '大名县', '邯山区', '肥乡区', 
    '成安县', '魏县', '曲周县', '磁县', '鸡泽县', '馆陶县', '冀南新区', 
    '涉县', '峰峰矿区', '邱县', '经开区', '丛台区', '复兴区'
]

# 计算每个县的数据
county_stats = {}
for idx, county in enumerate(county_order, start=1):
    today = today_data.get(county, {'batches': 0, 'patrols': 0, 'paid': 0, 'unpaid': 0})
    base = baseline['counties'].get(county, {'cum_batches': 0, 'cum_patrols': 0, 'paid': 0, 'unpaid': 0})
    
    # 当日批次 = 今天的批次 - 基线的累计批次
    daily_batches = today['batches'] - base['cum_batches']
    
    # 累计批次 = 今天的批次
    cum_batches = today['batches']
    
    # 累计图斑 = 今天的图斑
    cum_patrols = today['patrols']
    
    # 总批次和总图斑（从模板读取）
    total_batches = template_ws.cell(row=idx+5, column=3).value or 0
    total_patrols = template_ws.cell(row=idx+5, column=4).value or 0
    
    # 剩余批次 = 总批次 - 累计批次
    remaining_batches = total_batches - cum_batches
    
    # 剩余图斑 = 总图斑 - 累计图斑
    remaining_patrols = total_patrols - cum_patrols
    
    county_stats[county] = {
        'idx': idx,
        'total_batches': total_batches,
        'total_patrols': total_patrols,
        'daily_batches': daily_batches,
        'cum_batches': cum_batches,
        'cum_patrols': cum_patrols,
        'remaining_batches': remaining_batches,
        'remaining_patrols': remaining_patrols,
        'paid': today['paid'],
        'unpaid': today['unpaid']
    }

# 更新每个县的数据（第6-25行）
for county, stats in county_stats.items():
    row = stats['idx'] + 5  # 第6行开始
    
    # E列：当日批次
    new_ws.cell(row=row, column=5, value=stats['daily_batches'] if stats['daily_batches'] > 0 else None)
    
    # F列：累计批次
    new_ws.cell(row=row, column=6, value=stats['cum_batches'])
    
    # G列：累计图斑
    new_ws.cell(row=row, column=7, value=stats['cum_patrols'])
    
    # H列：剩余批次
    new_ws.cell(row=row, column=8, value=stats['remaining_batches'])
    
    # I列：剩余图斑
    new_ws.cell(row=row, column=9, value=stats['remaining_patrols'])
    
    # J列：已缴费
    new_ws.cell(row=row, column=10, value=stats['paid'])
    
    # K列：未缴费
    new_ws.cell(row=row, column=11, value=stats['unpaid'] if stats['unpaid'] > 0 else None)

# 计算总计（第5行）
total_daily_batches = sum(s['daily_batches'] for s in county_stats.values())
total_cum_batches = sum(s['cum_batches'] for s in county_stats.values())
total_cum_patrols = sum(s['cum_patrols'] for s in county_stats.values())
total_remaining_batches = sum(s['remaining_batches'] for s in county_stats.values())
total_remaining_patrols = sum(s['remaining_patrols'] for s in county_stats.values())
total_paid = sum(s['paid'] for s in county_stats.values())
total_unpaid = sum(s['unpaid'] for s in county_stats.values())

# 更新总计行
new_ws.cell(row=5, column=5, value=total_daily_batches)  # E5: 当日批次
new_ws.cell(row=5, column=6, value=total_cum_batches)    # F5: 累计批次
new_ws.cell(row=5, column=7, value=total_cum_patrols)    # G5: 累计图斑
new_ws.cell(row=5, column=8, value=total_remaining_batches)  # H5: 剩余批次
new_ws.cell(row=5, column=9, value=total_remaining_patrols)  # I5: 剩余图斑
new_ws.cell(row=5, column=10, value=total_paid)          # J5: 已缴费
new_ws.cell(row=5, column=11, value=total_unpaid)        # K5: 未缴费

# 保存新文件
output_file = '农房整治卷宗整改进展统计表(10月30日).xlsx'
new_wb.save(output_file)
print(f'新统计表已保存到: {output_file}')
print()

# 输出统计结果
print('=' * 60)
print('邯郸市农房整治卷宗整改进展统计（10月30日）')
print('=' * 60)
print()
print(f'城市总批次: {baseline["total"]["batches"]} 批')
print(f'城市总图斑: {baseline["total"]["patrols"]} 个')
print()
print(f'当日批次: {total_daily_batches} 批')
print(f'累计批次: {total_cum_batches} 批')
print(f'累计图斑: {total_cum_patrols} 个')
print(f'剩余批次: {total_remaining_batches} 批')
print(f'剩余图斑: {total_remaining_patrols} 个')
print()
print(f'已缴费: {total_paid} 万元')
print(f'未缴费: {total_unpaid} 万元')
print()

# 输出有变动的县
print('=' * 60)
print('今日有变动的县（市、区）:')
print('=' * 60)
for item in delta_counties:
    county = item['county']
    delta_b = item['delta_batches']
    delta_p = item['delta_patrols']
    if delta_b > 0 or delta_p > 0:
        print(f'{county}: 新增批次 {delta_b} 批, 新增图斑 {delta_p} 个')

print()
print(f'共有 {len([d for d in delta_counties if d["delta_batches"] > 0 or d["delta_patrols"] > 0])} 个县（市、区）有新增数据')

# 保存统计结果到文件
with open('agent_answer.txt', 'w', encoding='utf-8') as f:
    f.write('=' * 60 + '\n')
    f.write('邯郸市农房整治卷宗整改进展统计（10月30日）\n')
    f.write('=' * 60 + '\n')
    f.write('\n')
    f.write(f'城市总批次: {baseline["total"]["batches"]} 批\n')
    f.write(f'城市总图斑: {baseline["total"]["patrols"]} 个\n')
    f.write('\n')
    f.write(f'当日批次: {total_daily_batches} 批\n')
    f.write(f'累计批次: {total_cum_batches} 批\n')
    f.write(f'累计图斑: {total_cum_patrols} 个\n')
    f.write(f'剩余批次: {total_remaining_batches} 批\n')
    f.write(f'剩余图斑: {total_remaining_patrols} 个\n')
    f.write('\n')
    f.write(f'已缴费: {total_paid} 万元\n')
    f.write(f'未缴费: {total_unpaid} 万元\n')
    f.write('\n')
    f.write('=' * 60 + '\n')
    f.write('今日有变动的县（市、区）:\n')
    f.write('=' * 60 + '\n')
    for item in delta_counties:
        county = item['county']
        delta_b = item['delta_batches']
        delta_p = item['delta_patrols']
        if delta_b > 0 or delta_p > 0:
            f.write(f'{county}: 新增批次 {delta_b} 批, 新增图斑 {delta_p} 个\n')
    f.write('\n')
    f.write(f'共有 {len([d for d in delta_counties if d["delta_batches"] > 0 or d["delta_patrols"] > 0])} 个县（市、区）有新增数据\n')

print()
print(f'统计结果已保存到: agent_answer.txt')
