import openpyxl
from pathlib import Path
from collections import defaultdict

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

# 读取明细表
wb_detail = openpyxl.load_workbook(detail_file, data_only=True)
ws_detail = wb_detail.active

# 统计每个县的数据
county_stats = defaultdict(lambda: {
    'batches': 0,
    'plots': 0,
    'completed_plots': 0,
    'unpaid_plots': 0,
    'paid_plots': 0
})

current_county = None
for row_idx in range(5, ws_detail.max_row + 1):
    row = [ws_detail.cell(row_idx, col).value for col in range(1, 15)]
    
    if row[0] == '合计':
        break
    
    if row[1] is not None:
        current_county = row[1].replace('\n', '')
    
    if current_county is None:
        continue
    
    plots = row[3] if row[3] is not None else 0
    paid = row[5] if row[5] is not None else 0
    unpaid = row[6] if row[6] is not None else 0
    
    county_stats[current_county]['batches'] += 1
    county_stats[current_county]['plots'] += plots
    county_stats[current_county]['paid_plots'] += paid
    county_stats[current_county]['unpaid_plots'] += unpaid

# 读取模板
wb_template = openpyxl.load_workbook(template_file)
ws_template = wb_template.active

# 县名映射
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

output_lines = []
output_lines.append("=" * 80)
output_lines.append("农房整治进展统计结果")
output_lines.append("=" * 80)
output_lines.append("")

for row_idx in range(6, 26):
    county_name = ws_template.cell(row_idx, 2).value
    if county_name is None:
        continue
    
    detail_county = county_mapping.get(county_name, county_name)
    
    if detail_county in county_stats:
        stats = county_stats[detail_county]
        
        ws_template.cell(row_idx, 3).value = stats['batches']
        ws_template.cell(row_idx, 4).value = stats['plots']
        ws_template.cell(row_idx, 6).value = stats['batches']
        ws_template.cell(row_idx, 7).value = stats['paid_plots']
        
        remaining_batches = 0
        remaining_plots = stats['plots'] - stats['paid_plots']
        ws_template.cell(row_idx, 8).value = remaining_batches
        ws_template.cell(row_idx, 9).value = remaining_plots
        
        ws_template.cell(row_idx, 10).value = stats['paid_plots']
        ws_template.cell(row_idx, 11).value = stats['unpaid_plots']
        
        total_batches += stats['batches']
        total_plots += stats['plots']
        total_completed_batches += stats['batches']
        total_completed_plots += stats['paid_plots']
        total_paid += stats['paid_plots']
        total_unpaid += stats['unpaid_plots']
        
        output_lines.append(f"{county_name}:")
        output_lines.append(f"  批次: {stats['batches']}, 图斑: {stats['plots']}")
        output_lines.append(f"  已缴费: {stats['paid_plots']}, 未缴费: {stats['unpaid_plots']}")
        output_lines.append("")

# 填充邯郸市总计行
ws_template.cell(5, 3).value = total_batches
ws_template.cell(5, 4).value = total_plots
ws_template.cell(5, 6).value = total_completed_batches
ws_template.cell(5, 7).value = total_completed_plots
ws_template.cell(5, 8).value = 0
ws_template.cell(5, 9).value = total_plots - total_completed_plots
ws_template.cell(5, 10).value = total_paid
ws_template.cell(5, 11).value = total_unpaid

# 保存新文件
output_file = Path(workdir) / '农房整治进展统计结果.xlsx'
wb_template.save(output_file)

output_lines.append("=" * 80)
output_lines.append("邯郸市汇总数据:")
output_lines.append("=" * 80)
output_lines.append(f"总批次: {total_batches}")
output_lines.append(f"总图斑: {total_plots}")
output_lines.append(f"累计完成批次: {total_completed_batches}")
output_lines.append(f"累计完成图斑: {total_completed_plots}")
output_lines.append(f"剩余批次: 0")
output_lines.append(f"剩余图斑: {total_plots - total_completed_plots}")
output_lines.append(f"已缴费: {total_paid}")
output_lines.append(f"未缴费: {total_unpaid}")

# 检查异常
output_lines.append("")
output_lines.append("=" * 80)
output_lines.append("异常情况:")
output_lines.append("=" * 80)

template_counties = set()
for row_idx in range(6, 26):
    county = ws_template.cell(row_idx, 2).value
    if county:
        template_counties.add(county)

detail_counties = set(county_stats.keys())
mapped_detail_counties = set(county_mapping.values())

missing_in_detail = template_counties - mapped_detail_counties
if missing_in_detail:
    output_lines.append(f"⚠️ 以下县在模板中但不在明细表中: {missing_in_detail}")

extra_in_detail = detail_counties - set(county_mapping.values())
if extra_in_detail:
    output_lines.append(f"⚠️ 以下县在明细表中但不在模板中: {extra_in_detail}")

output_lines.append("")
output_lines.append("需要催办的县（未缴费图斑 > 50）:")
chase_counties = []
for county_name in sorted(template_counties):
    detail_county = county_mapping.get(county_name, county_name)
    if detail_county in county_stats:
        stats = county_stats[detail_county]
        if stats['unpaid_plots'] > 50:
            chase_counties.append((county_name, stats['unpaid_plots']))
            output_lines.append(f"  ⚠️ {county_name}: 未缴费 {stats['unpaid_plots']} 个图斑")

if not chase_counties:
    output_lines.append("  无")

# 保存到文件
with open(Path(workdir) / 'agent_answer.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(output_lines))

print("结果已保存到 agent_answer.txt")
