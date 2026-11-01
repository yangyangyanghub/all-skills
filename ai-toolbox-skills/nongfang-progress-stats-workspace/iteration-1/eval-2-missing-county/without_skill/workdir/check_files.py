import openpyxl
from pathlib import Path

workdir = r'C:\Users\HP\AppData\Roaming\com.ai-toolbox\skills\nongfang-progress-stats-workspace\iteration-1\eval-2-missing-county\without_skill\workdir'
files = list(Path(workdir).glob('*.xlsx'))

for idx, f in enumerate(files, 1):
    print("=" * 60)
    print(f"文件{idx}: {f.name}")
    print("=" * 60)
    wb = openpyxl.load_workbook(f)
    print(f"工作表: {wb.sheetnames}")
    ws = wb.active
    print(f"活动工作表: {ws.title}")
    print(f"数据范围: {ws.dimensions}")
    print(f"最大行: {ws.max_row}, 最大列: {ws.max_column}")
    print("\n前15行数据:")
    for i, row in enumerate(ws.iter_rows(min_row=1, max_row=15, values_only=True), 1):
        print(f"行{i}: {row}")
    print()
