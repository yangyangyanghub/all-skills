# -*- coding: utf-8 -*-
import openpyxl
import os

workdir = r'C:\Users\HP\AppData\Roaming\com.ai-toolbox\skills\nongfang-progress-stats-workspace\iteration-1\eval-0-first-run\without_skill\workdir'
output_file = '农房整治工作卷宗整改进展统计表_已填写.xlsx'

wb = openpyxl.load_workbook(os.path.join(workdir, output_file), data_only=True)
ws = wb.active

output = []
output.append('=== 生成的统计表内容 ===\n')

# 读取行5（邯郸市）和行6-25（20个县）
output.append('邯郸市（汇总行）:')
row5_data = []
for j in range(1, 12):
    val = ws.cell(row=5, column=j).value
    if val is not None:
        row5_data.append(f'列{j}:{val}')
output.append(f'  行5: {row5_data}')

output.append('\n20个县（行6-25）:')
for i in range(6, 26):
    row_data = []
    for j in range(1, 12):
        val = ws.cell(row=i, column=j).value
        if val is not None:
            row_data.append(f'{val}')
        else:
            row_data.append('')
    output.append(f'  行{i}: {row_data}')

wb.close()

# 写入文件
with open(os.path.join(workdir, 'verify_output.txt'), 'w', encoding='utf-8') as f:
    f.write('\n'.join(output))

print('验证完成')
