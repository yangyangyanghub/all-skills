import openpyxl
from pathlib import Path

workdir = r'C:\Users\HP\AppData\Roaming\com.ai-toolbox\skills\nongfang-progress-stats-workspace\iteration-1\eval-2-missing-county\without_skill\workdir'
files = list(Path(workdir).glob('*.xlsx'))

output = []

for idx, f in enumerate(files, 1):
    output.append("=" * 80)
    output.append(f"文件{idx}: {f.name}")
    output.append("=" * 80)
    wb = openpyxl.load_workbook(f, data_only=True)
    output.append(f"工作表: {wb.sheetnames}")
    ws = wb.active
    output.append(f"活动工作表: {ws.title}")
    output.append(f"数据范围: {ws.dimensions}")
    output.append(f"最大行: {ws.max_row}, 最大列: {ws.max_column}")
    output.append("\n所有数据:")
    for i, row in enumerate(ws.iter_rows(values_only=True), 1):
        output.append(f"行{i}: {list(row)}")
    output.append("")

# 保存到文件
with open(Path(workdir) / 'file_structure.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(output))

print("已保存到 file_structure.txt")
