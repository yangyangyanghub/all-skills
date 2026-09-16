# -*- coding: utf-8 -*-
"""变更调查流转表 → 县级处置日报

业务规则（洋哥 2026-09-03 定档）：
- 流转 = 县级行政区名称非空（图斑已下发到县里系统）
- 处置 = 仅审核阶段(系统)=101.0 审核结束
- 在途 = 已打回(90) + 市级待审核(95)
- 未处置 = 状态(系统) ∈ {1,2,4} 或 审核阶段未到 101
- 县分组 = 「行政区名称」列（不是县级行政区名称，860 全非空）
- 地类映射规则：与「三调用地代码名称对照表」(旧表) 不一致以旧表为准，旧表没有的用更正版补充

输出 2 个 Sheet：
- 逐县汇总：10 列（县名称/总线索/审核结束/已打回/市级待审核/省级待审核/已填报/未填报/填报率/差错率），按未填报降序
  - 已填报 = 审核结束(101) + 已打回(90) + 市级待审核(95) + 省级待审核(97)
  - 未填报 = 总线索 - 已填报
  - 填报率 = 已填报 / 总线索数
  - 差错率 = 已打回 / 已填报（分母 0 时留空）
  - 口径定档（洋哥 2026-09-11）：不含「状态=4 已提交但审核阶段空」，该类计入未填报
- 图斑明细：24 列全量
"""
import os
import sys
from datetime import datetime
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

# ===== 配置 =====
BUSINESS_NAME = '变更调查处置'

# 状态机映射
STAGE = {101.0: '审核结束', 90.0: '已打回', 95.0: '市级待审核', 97.0: '省级待审核'}
STATE = {1: '未处理', 2: '未提交', 4: '已提交', 10: '已审核'}
SEND_BACK = {0.0: '市级待审核', 1.0: '已打回'}


def get_stage(row):
    s = row['审核阶段(系统)']
    if pd.notna(s):
        return STAGE.get(s, f'未知({s})')
    return STATE.get(row['状态(系统)'], f'未知({row["状态(系统)"]})')


def get_state_text(row):
    s = row['审核阶段(系统)']
    if pd.notna(s):
        if s == 101.0: return '已审核'
        if s == 90.0: return '已打回'
        if s == 95.0: return '市级待审核'
        if s == 97.0: return '省级待审核'
    return STATE.get(row['状态(系统)'], f'未知({row["状态(系统)"]})')


def get_send_back(row):
    sb = row['打回状态(系统)']
    if pd.isna(sb):
        return ''
    return SEND_BACK.get(sb, f'未知({sb})')


# ===== 地类对照表加载 =====
from dilei_map import DIL_EI_MAP


def load_code_map():
    """使用 v1.5 内置权威对照表（洋哥 2026-09-07 定档）
    来源：附件一 河北省国土变更调查实施细则（2026年度适用）附录 A 表 A.1/A.2
    内置 DIL_EI_MAP 已合并旧表 + 更正版（0602C/K 等），不再依赖外部文件"""
    print(f'地类对照表: 内置 DIL_EI_MAP 共 {len(DIL_EI_MAP)} 项（v1.5 定档）')
    return DIL_EI_MAP


def code_to_name(val, code_map):
    if pd.isna(val):
        return ''
    s = str(val).strip()
    return code_map.get(s, s + ' (?)')


# ===== 主流程 =====
def generate(src, out_dir=None, business_name=BUSINESS_NAME, today=None):
    if today is None:
        today = datetime.now().strftime('%Y-%m-%d')
    if out_dir is None:
        out_dir = os.path.dirname(os.path.abspath(src))

    df = pd.read_excel(src)
    print(f'源表行数: {len(df)}')

    # 地类
    code_map = load_code_map()
    df['__dilei_text'] = df['实地地类'].apply(lambda v: code_to_name(v, code_map))

    # 派生列
    df['__stage'] = df.apply(get_stage, axis=1)
    df['__state'] = df.apply(get_state_text, axis=1)
    df['__send_back'] = df.apply(get_send_back, axis=1)
    df['__done'] = df['审核阶段(系统)'] == 101.0
    df['__transit'] = df['审核阶段(系统)'].isin([90.0, 95.0])
    df['__circulated'] = df['县级行政区名称'].notna()
    # 县名：用「行政区名称」列（860 全非空）
    df['__county'] = df['行政区名称'].fillna(df['县级行政区名称']).fillna('（未分配）')

    # 逐县汇总（5 列：总线索/审核结束/已打回/市级待审核/未填报）
    summary = df.groupby('__county').agg(
        总线索数=('线索编号', 'count'),
        审核结束=('__stage', lambda s: (s == '审核结束').sum()),
        已打回=('__stage', lambda s: (s == '已打回').sum()),
        市级待审核=('__stage', lambda s: (s == '市级待审核').sum()),
        省级待审核=('__stage', lambda s: (s == '省级待审核').sum()),
    ).reset_index().rename(columns={'__county': '县名称'})

    # 已填报 = 县级填报 = 审核结束(101) + 已打回(90) + 市级待审核(95) + 省级待审核(97)
    summary['已填报'] = (
        summary['审核结束'] + summary['已打回'] + summary['市级待审核'] + summary['省级待审核']
    )
    # 未填报 = 总线索 - 已填报（兜底 ≥0）
    summary['未填报'] = (summary['总线索数'] - summary['已填报']).clip(lower=0)
    # 填报率 = 已填报 / 总线索数
    summary['填报率'] = (summary['已填报'] / summary['总线索数']).where(summary['总线索数'] > 0)
    # 差错率 = 已打回 / 已填报（分母 0 时留空）
    summary['差错率'] = (summary['已打回'] / summary['已填报']).where(summary['已填报'] > 0)

    # 按未填报降序
    summary = summary.sort_values(
        by=['未填报', '总线索数', '县名称'],
        ascending=[False, False, True],
    ).reset_index(drop=True)

    print()
    print('逐县汇总:')
    print(summary.to_string(index=False))

    # 公式校验：总线索 = 各阶段 + 未填报（源数据阶段计数与总数是否自洽）
    stage_cols = ['审核结束', '已打回', '市级待审核', '省级待审核', '未填报']
    formula_check = summary[stage_cols].sum(axis=1)
    formula_ok = (formula_check == summary['总线索数']).all()
    print(f'\n公式校验: {"✓ 通过" if formula_ok else "❌ 失败"}')
    if not formula_ok:
        bad = summary.loc[formula_check != summary['总线索数'], ['县名称', '总线索数'] + stage_cols]
        print(bad.to_string(index=False))

    # 明细
    df_sorted = df.sort_values(
        by=['__done', '__transit', '县级行政区名称', '__stage', '图斑编号'],
        ascending=[False, False, True, True, True],
    ).reset_index(drop=True)

    out_cols = [
        ('序号', None, 6),
        ('县级行政区', '__county', 12),
        ('线索编号', '线索编号', 22),
        ('图斑编号', '图斑编号', 22),
        ('监测类型', '监测类型', 12),
        ('图斑面积(亩)', '图斑面积(亩)', 12),
        ('项目名称', '项目名称', 22),
        ('核实认定意见', '核实认定意见', 14),
        ('分类', '分类', 14),
        ('审核阶段', '__stage', 14),
        ('状态', '__state', 10),
        ('打回状态', '__send_back', 12),
        ('整改情况', '整改情况', 14),
        ('处置', '__done', 8),
        ('在途', '__transit', 8),
        ('流转', '__circulated', 8),
        ('图斑特征', '图斑特征', 12),
        ('实地地类(代码)', '实地地类', 10),
        ('实地地类(名称)', '__dilei_text', 18),
        ('外业时间', '外业时间', 18),
        ('核查时间', '核查时间', 18),
        ('核查人', '执行人员(系统)', 10),
        ('图斑名称', '图斑名称', 18),
        ('线索备注', '线索备注', 24),
    ]

    # 写 Excel
    wb = Workbook()
    header_font = Font(name='微软雅黑', size=10, bold=True, color='FFFFFF')
    header_fill = PatternFill('solid', fgColor='4472C4')
    cell_font = Font(name='微软雅黑', size=9)
    total_font = Font(name='微软雅黑', size=9, bold=True)
    total_fill = PatternFill('solid', fgColor='FFF2CC')
    thin = Side(border_style='thin', color='B4B4B4')
    border = Border(top=thin, left=thin, right=thin, bottom=thin)
    center = Alignment(horizontal='center', vertical='center', wrap_text=True)
    left = Alignment(horizontal='left', vertical='center', wrap_text=True)

    # —— Sheet 1: 逐县汇总（10 列）——
    ws1 = wb.active
    ws1.title = '逐县汇总'
    headers = ['县名称', '总线索数', '审核结束', '已打回', '市级待审核', '省级待审核',
               '已填报', '未填报', '填报率', '差错率']
    last_col = get_column_letter(len(headers))
    ws1.merge_cells(f'A1:{last_col}1')
    ws1.cell(1, 1, f'{business_name}逐县汇总（{today}）').font = Font(name='微软雅黑', size=14, bold=True)
    ws1.cell(1, 1).alignment = center
    ws1.merge_cells(f'A2:{last_col}2')
    note = ('公式：已填报 = 审核结束 + 已打回 + 市级待审核 + 省级待审核；'
            '未填报 = 总线索 - 已填报；'
            '填报率 = 已填报 ÷ 总线索；差错率 = 已打回 ÷ 已填报；按未填报降序排列')
    ws1.cell(2, 1, note).font = Font(name='微软雅黑', size=9, italic=True, color='808080')
    ws1.cell(2, 1).alignment = left

    for col, h in enumerate(headers, 1):
        c = ws1.cell(3, col, h)
        c.font = header_font
        c.fill = header_fill
        c.alignment = center
        c.border = border

    rate_cols = {9, 10}  # 填报率 / 差错率，百分比格式
    for r, row in enumerate(summary[headers].itertuples(index=False), start=4):
        for col, val in enumerate(row, start=1):
            if col in rate_cols:
                v = None if pd.isna(val) else float(val)
            elif isinstance(val, (int, float)) and not isinstance(val, bool):
                v = int(val)
            else:
                v = val
            c = ws1.cell(r, col, v)
            c.font = cell_font
            c.alignment = center if col > 1 else left
            c.border = border
            if col in rate_cols:
                c.number_format = '0.0%'

    # 合计行（计数列求和，率列按合计重算）
    total_row = 4 + len(summary)
    count_headers = headers[1:8]
    total_counts = {h: int(summary[h].sum()) for h in count_headers}
    total_vals = ['合计'] + [total_counts[h] for h in count_headers] + [
        total_counts['已填报'] / total_counts['总线索数'] if total_counts['总线索数'] else None,
        total_counts['已打回'] / total_counts['已填报'] if total_counts['已填报'] else None,
    ]
    for col, v in enumerate(total_vals, start=1):
        c = ws1.cell(total_row, col, v)
        c.font = total_font
        c.fill = total_fill
        c.alignment = center
        c.border = border
        if col in rate_cols:
            c.number_format = '0.0%'

    widths = [14, 12, 12, 12, 14, 14, 12, 12, 10, 10]
    for i, w in enumerate(widths, 1):
        ws1.column_dimensions[get_column_letter(i)].width = w

    # —— Sheet 2: 图斑明细 ——
    ws2 = wb.create_sheet('图斑明细')
    ws2.merge_cells(start_row=1, start_column=1, end_row=1, end_column=len(out_cols))
    ws2.cell(1, 1, f'{business_name}图斑明细（{today}）').font = Font(name='微软雅黑', size=14, bold=True)
    ws2.cell(1, 1).alignment = center
    ws2.row_dimensions[1].height = 24
    for col, (label, _, _) in enumerate(out_cols, 1):
        c = ws2.cell(2, col, label)
        c.font = header_font
        c.fill = header_fill
        c.alignment = center
        c.border = border
    ws2.row_dimensions[2].height = 28

    center_cols = {1, 3, 4, 5, 10, 11, 12, 13, 14, 15, 16, 17}

    for r, (_, row) in enumerate(df_sorted.iterrows(), start=3):
        for col, (label, src, _) in enumerate(out_cols, start=1):
            if src is None:
                val = r - 2
            else:
                val = row[src]
                if src in ('__done', '__transit', '__circulated'):
                    val = '是' if val else '否'
                elif pd.isna(val):
                    val = ''
            c = ws2.cell(r, col, val)
            c.font = cell_font
            c.alignment = center if col in center_cols else left
            c.border = border
        ws2.row_dimensions[r].height = 22

    for col, (_, _, width) in enumerate(out_cols, 1):
        ws2.column_dimensions[get_column_letter(col)].width = width

    ws2.freeze_panes = 'C3'
    ws2.auto_filter.ref = f'A2:{get_column_letter(len(out_cols))}{2 + len(df_sorted)}'

    for ws in (ws1, ws2):
        ws.page_setup.orientation = ws.ORIENTATION_LANDSCAPE
        ws.page_setup.paperSize = ws.PAPERSIZE_A4
        ws.page_setup.fitToWidth = 1
        ws.page_setup.fitToHeight = 1
        ws.sheet_properties.pageSetUpPr.fitToPage = True
        ws.print_options.horizontalCentered = True
        ws.page_margins.left = 0.3
        ws.page_margins.right = 0.3
        ws.page_margins.top = 0.4
        ws.page_margins.bottom = 0.4

    out_path = os.path.join(out_dir, f'{business_name}日报_{today}.xlsx')
    wb.save(out_path)
    print(f'\n输出: {out_path}')
    print(f'明细行数: {len(df_sorted)}')
    return out_path


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('用法: python generate_change_survey_daily.py <源xlsx> [统计日期YYYY-MM-DD]')
        sys.exit(1)
    generate(
        src=sys.argv[1],
        today=sys.argv[2] if len(sys.argv) > 2 else None,
    )
