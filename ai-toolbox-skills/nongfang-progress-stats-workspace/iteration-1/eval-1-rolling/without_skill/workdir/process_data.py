# -*- coding: utf-8 -*-
import openpyxl
import json
from collections import defaultdict
from copy import copy

# 读取基线数据
with open('.nongfang_baseline.json', 'r', encoding='utf-8') as f:
    baseline = json.load(f)

print('基线数据日期:', baseline['data_date'])
print('基线总批次:', baseline['total']['batches'])
print('基线总图斑:', baseline['total']['patrols'])
print()

# 读取今天的新明细表
wb = openpyxl.load_workbook('邯郸市NF整改进展情况统计表10.30.xlsx', data_only=True)
ws = wb.active

# 提取数据
counties_data = defaultdict(lambda: {'batches': 0, 'patrols': 0, 'paid': 0, 'unpaid': 0})

# 县市区名称列表
county_names = ['磁县', '曲周县', '冀南新区', '武安市', '馆陶县', '永年区', '涉县', '邱县', 
                '复兴区', '邯山区', '峰峰矿区', '成安县', '鸡泽县', '魏县', '临漳县', 
                '广平县', '肥乡区', '丛台区', '大名县', '经开区']

# 读取所有数据行
for row_idx, row in enumerate(ws.iter_rows(min_row=5, values_only=True), start=5):
    # 跳过空行
    if not row or all(cell is None for cell in row[:5]):
        continue
    
    # 提取县市区名称（第2列，索引1）
    county = row[1] if len(row) > 1 else None
    
    # 如果县市区为空，尝试从项目名称中提取
    if not county and len(row) > 2 and row[2]:
        project_name = str(row[2])
        for name in county_names:
            if name in project_name:
                county = name
                break
    
    if not county:
        continue
    
    # 提取图斑数量（第4列，索引3）
    patrols = row[3] if len(row) > 3 and row[3] is not None else 0
    
    # 提取应缴费（第5列，索引4）和实缴费（第6列，索引5）
    paid = row[5] if len(row) > 5 and row[5] is not None else 0
    unpaid = row[6] if len(row) > 6 and row[6] is not None else 0
    
    # 累加数据
    counties_data[county]['batches'] += 1
    counties_data[county]['patrols'] += patrols
    counties_data[county]['paid'] += paid
    counties_data[county]['unpaid'] += unpaid

# 打印今天的数据
print('=== 今天（10月30日）的数据 ===')
total_batches = 0
total_patrols = 0
total_paid = 0
total_unpaid = 0

for county in sorted(counties_data.keys()):
    data = counties_data[county]
    print(f"{county}: 批次={data['batches']}, 图斑={data['patrols']}, 已缴费={data['paid']}, 未缴费={data['unpaid']}")
    total_batches += data['batches']
    total_patrols += data['patrols']
    total_paid += data['paid']
    total_unpaid += data['unpaid']

print()
print(f"总计: 批次={total_batches}, 图斑={total_patrols}, 已缴费={total_paid}, 未缴费={total_unpaid}")
print()

# 计算增量
print('=== 与基线对比的增量 ===')
new_counties_with_delta = []

for county in sorted(counties_data.keys()):
    today_data = counties_data[county]
    baseline_data = baseline['counties'].get(county, {'cum_batches': 0, 'cum_patrols': 0, 'paid': 0, 'unpaid': 0})
    
    delta_batches = today_data['batches'] - baseline_data['cum_batches']
    delta_patrols = today_data['patrols'] - baseline_data['cum_patrols']
    
    if delta_batches > 0 or delta_patrols > 0:
        new_counties_with_delta.append({
            'county': county,
            'delta_batches': delta_batches,
            'delta_patrols': delta_patrols
        })
        print(f"{county}: 新增批次={delta_batches}, 新增图斑={delta_patrols}")

print()
print(f"有变动的县数量: {len(new_counties_with_delta)}")

# 保存结果供后续使用
result = {
    'today_data': dict(counties_data),
    'total': {
        'batches': total_batches,
        'patrols': total_patrols,
        'paid': total_paid,
        'unpaid': total_unpaid
    },
    'delta_counties': new_counties_with_delta
}

with open('today_data.json', 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print()
print('数据已保存到 today_data.json')
