# -*- coding: utf-8 -*-
import openpyxl
import os
import shutil

workdir = r'C:\Users\HP\AppData\Roaming\com.ai-toolbox\skills\nongfang-progress-stats-workspace\iteration-1\eval-0-first-run\without_skill\workdir'
files = os.listdir(workdir)
xlsx_files = [f for f in files if f.endswith('.xlsx')]

# 文件名
detail_file = [f for f in xlsx_files if 'NF' in f][0]
template_file = [f for f in xlsx_files if '农房' in f or '整改' in f][0]
output_file = '农房整治工作卷宗整改进展统计表_已填写.xlsx'

print(f'明细表: {detail_file}')
print(f'模板表: {template_file}')
print(f'输出文件: {output_file}')

# 1. 复制模板
shutil.copy2(os.path.join(workdir, template_file), os.path.join(workdir, output_file))
print('模板已复制')

# 2. 读取明细表，按县统计
wb_detail = openpyxl.load_workbook(os.path.join(workdir, detail_file), data_only=True)
ws_detail = wb_detail.active

county_data = {}
current_county = None
for i in range(5, ws_detail.max_row + 1):
    seq = ws_detail.cell(row=i, column=1).value
    county = ws_detail.cell(row=i, column=2).value
    project = ws_detail.cell(row=i, column=3).value
    tuban = ws_detail.cell(row=i, column=4).value
    yingjiao = ws_detail.cell(row=i, column=5).value
    shijiao = ws_detail.cell(row=i, column=6).value
    weijiao = ws_detail.cell(row=i, column=7).value
    
    if county:
        current_county = county
    
    if current_county and project:
        if current_county not in county_data:
            county_data[current_county] = {
                'count': 0, 
                'tuban_sum': 0,
                'shijiao_sum': 0,
                'weijiao_sum': 0
            }
        county_data[current_county]['count'] += 1
        if tuban:
            county_data[current_county]['tuban_sum'] += tuban
        if shijiao:
            county_data[current_county]['shijiao_sum'] += shijiao
        if weijiao:
            county_data[current_county]['weijiao_sum'] += weijiao

wb_detail.close()
print(f'明细表读取完成，共{len(county_data)}个县')

# 3. 读取模板，填充数据
wb_template = openpyxl.load_workbook(os.path.join(workdir, output_file))
ws_template = wb_template.active

# 模板结构：
# 行5: 邯郸市（汇总行）
# 行6-25: 20个县（序号1-20）

# 县名映射（模板中的县名 -> 明细表中的县名）
county_mapping = {
    '永年区': '永年区',
    '广平县': '广平县',
    '武安市': '武安市',
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

# 计算邯郸市汇总
total_count = sum(d['count'] for d in county_data.values())
total_tuban = sum(d['tuban_sum'] for d in county_data.values())
total_shijiao = sum(d['shijiao_sum'] for d in county_data.values())
total_weijiao = sum(d['weijiao_sum'] for d in county_data.values())

# 填充邯郸市（行5）
# 列3: 总批次, 列4: 总图斑
# 列6: 累计批次, 列7: 累计图斑
# 列8: 剩余批次, 列9: 剩余图斑
# 列10: 已缴费, 列11: 未缴费

# 注意：模板中已有部分数据，我们需要更新
# 根据模板结构，当日批次(列5)是当天完成的，这里我们假设为0或保留原值
# 累计批次 = 总批次 - 剩余批次
# 剩余批次 = 总批次 - 累计批次

# 从明细表我们只能得到总批次和总图斑，以及缴费情况
# 当日批次、累计批次、剩余批次需要从其他来源获取或假设为0

# 这里我们只填充能从明细表得到的数据：
# - 总批次（列3）
# - 总图斑（列4）
# - 已缴费（列10）= 实缴
# - 未缴费（列11）= 未缴

ws_template.cell(row=5, column=3).value = total_count  # 总批次
ws_template.cell(row=5, column=4).value = total_tuban  # 总图斑
ws_template.cell(row=5, column=10).value = total_shijiao  # 已缴费
ws_template.cell(row=5, column=11).value = total_weijiao  # 未缴费

print(f'邯郸市: 总批次{total_count}, 总图斑{total_tuban}, 已缴费{total_shijiao}, 未缴费{total_weijiao}')

# 填充20个县（行6-25）
for row in range(6, 26):
    seq = ws_template.cell(row=row, column=1).value
    county_name = ws_template.cell(row=row, column=2).value
    
    if county_name and county_name in county_mapping:
        detail_county = county_mapping[county_name]
        if detail_county in county_data:
            data = county_data[detail_county]
            # 列3: 总批次
            ws_template.cell(row=row, column=3).value = data['count']
            # 列4: 总图斑
            ws_template.cell(row=row, column=4).value = data['tuban_sum']
            # 列10: 已缴费（实缴）
            ws_template.cell(row=row, column=10).value = data['shijiao_sum']
            # 列11: 未缴费（未缴）
            ws_template.cell(row=row, column=11).value = data['weijiao_sum']
            print(f'{county_name}: 总批次{data["count"]}, 总图斑{data["tuban_sum"]}, 已缴费{data["shijiao_sum"]}, 未缴费{data["weijiao_sum"]}')

# 保存
wb_template.save(os.path.join(workdir, output_file))
wb_template.close()

print(f'\n完成！输出文件: {output_file}')
