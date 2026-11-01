import openpyxl
from pathlib import Path
from collections import defaultdict
import copy

workdir = r'C:\Users\HP\AppData\Roaming\com.ai-toolbox\skills\nongfang-progress-stats-workspace\iteration-1\eval-2-missing-county\without_skill\workdir'

# 读取文件
files = list(Path(workdir).glob('*.xlsx'))
template_file = None
detail_file = None

for f in files:
    if '修改后' in f.name:
        template_file = f
    elif '10.29' in f.name:
        detail_file = f

print(f"模板文件: {template_file.name}")
print(f"明细文件: {detail_file.name}")

# 读取明细表
wb_detail = openpyxl.load_workbook(detail_file, data_only=True)
ws_detail = wb_detail.active

# 统计每个县的数据
county_stats = defaultdict(lambda: {
    'batches': 0,  # 批次数
    'plots': 0,  # 图斑数
    'completed_plots': 0,  # 已完成图斑
    'unpaid_plots': 0,  # 未缴费图斑
    'paid_plots': 0  # 已缴费图斑
})

current_county = None
for row_idx in range(5, ws_detail.max_row + 1):
    row = [ws_detail.cell(row_idx, col).value for col in range(1, 15)]
    
    # 检查是否是合计行
    if row[0] == '合计':
        break
    
    # 检查是否有县名
    if row[1] is not None:
        current_county = row[1].replace('\n', '')
    
    if current_county is None:
        continue
    
    # 统计该批次
    plots = row[3] if row[3] is not None else 0
    paid = row[5] if row[5] is not None else 0
    unpaid = row[6] if row[6] is not None else 0
    
    county_stats[current_county]['batches'] += 1
    county_stats[current_county]['plots'] += plots
    county_stats[current_county]['paid_plots'] += paid
    county_stats[current_county]['unpaid_plots'] += unpaid

print("\n明细表统计结果:")
for county, stats in sorted(county_stats.items()):
    print(f"{county}: 批次={stats['batches']}, 图斑={stats['plots']}, 已缴费={stats['paid_plots']}, 未缴费={stats['unpaid_plots']}")

# 读取模板
wb_template = openpyxl.load_workbook(template_file)
ws_template = wb_template.active

# 县名映射（模板中的县名 -> 明细表中的县名）
county_mapping = {
    '永年区': '永年区',
    '广平县': '广平县',
    '武安市': '武安市区',
    '临漳县': '临漳县',
    '大名县': '大名县',
    '邯山区': '邯山区',
    '肥乡区': '肥乡区',
    '成安县': '成安县',
    '魏县': '魏县',
    '曲周县': '曲周县',
    '磁县': '磁县',
    '鸡泽县': '鸡泽县',
    '馆陶县': '馆陶县',
    '冀南新区': '冀南新区',
    '涉县': '涉县',
    '峰峰矿区': '峰峰矿区',
    '邱县': '邱县',
    '经开区': '经开区',
    '丛台区': '丛台区',
    '复兴区': '复兴区'
}

# 填充模板
total_batches = 0
total_plots = 0
total_completed_batches = 0
total_completed_plots = 0
total_paid = 0
total_unpaid = 0

for row_idx in range(6, 26):  # 行6-25是县数据
    county_name = ws_template.cell(row_idx, 2).value
    if county_name is None:
        continue
    
    # 获取明细表中的县名
    detail_county = county_mapping.get(county_name, county_name)
    
    if detail_county in county_stats:
        stats = county_stats[detail_county]
        
        # 卷宗总任务
        ws_template.cell(row_idx, 3).value = stats['batches']  # 批次
        ws_template.cell(row_idx, 4).value = stats['plots']  # 图斑
        
        # 累计完成情况
        ws_template.cell(row_idx, 6).value = stats['batches']  # 批次
        ws_template.cell(row_idx, 7).value = stats['paid_plots']  # 图斑
        
        # 剩余任务
        remaining_batches = stats['batches'] - stats['batches']  # 假设所有批次都已处理
        remaining_plots = stats['plots'] - stats['paid_plots']
        ws_template.cell(row_idx, 8).value = remaining_batches  # 批次
        ws_template.cell(row_idx, 9).value = remaining_plots  # 图斑
        
        # 缴费情况
        ws_template.cell(row_idx, 10).value = stats['paid_plots']  # 已缴费
        ws_template.cell(row_idx, 11).value = stats['unpaid_plots']  # 未缴费
        
        # 累计到总计
        total_batches += stats['batches']
        total_plots += stats['plots']
        total_completed_batches += stats['batches']
        total_completed_plots += stats['paid_plots']
        total_paid += stats['paid_plots']
        total_unpaid += stats['unpaid_plots']

# 填充邯郸市总计行（行5）
ws_template.cell(5, 3).value = total_batches
ws_template.cell(5, 4).value = total_plots
ws_template.cell(5, 6).value = total_completed_batches
ws_template.cell(5, 7).value = total_completed_plots
ws_template.cell(5, 8).value = 0  # 剩余批次（假设都已处理）
ws_template.cell(5, 9).value = total_plots - total_completed_plots  # 剩余图斑
ws_template.cell(5, 10).value = total_paid
ws_template.cell(5, 11).value = total_unpaid

# 保存新文件
output_file = Path(workdir) / '农房整治进展统计结果.xlsx'
wb_template.save(output_file)

print(f"\n已保存到: {output_file.name}")
print("\n" + "=" * 60)
print("汇总数据:")
print("=" * 60)
print(f"邯郸市总批次: {total_batches}")
print(f"邯郸市总图斑: {total_plots}")
print(f"累计完成批次: {total_completed_batches}")
print(f"累计完成图斑: {total_completed_plots}")
print(f"剩余批次: 0")
print(f"剩余图斑: {total_plots - total_completed_plots}")
print(f"已缴费: {total_paid}")
print(f"未缴费: {total_unpaid}")

# 检查异常
print("\n" + "=" * 60)
print("异常情况:")
print("=" * 60)

# 检查哪些县在模板中但不在明细表中
template_counties = set()
for row_idx in range(6, 26):
    county = ws_template.cell(row_idx, 2).value
    if county:
        template_counties.add(county)

detail_counties = set(county_stats.keys())
mapped_detail_counties = set(county_mapping.values())

missing_in_detail = template_counties - mapped_detail_counties
if missing_in_detail:
    print(f"以下县在模板中但不在明细表中: {missing_in_detail}")

# 检查哪些县在明细表中但不在模板中
extra_in_detail = detail_counties - set(county_mapping.values())
if extra_in_detail:
    print(f"以下县在明细表中但不在模板中: {extra_in_detail}")

# 检查数据不一致
print("\n需要催办的县（未缴费较多）:")
for county_name in sorted(template_counties):
    detail_county = county_mapping.get(county_name, county_name)
    if detail_county in county_stats:
        stats = county_stats[detail_county]
        if stats['unpaid_plots'] > 50:
            print(f"  {county_name}: 未缴费 {stats['unpaid_plots']} 个图斑")
