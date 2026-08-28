# 土地执法遥感监测图斑统计校核规则

## 一、校核目的

确保统计数据逻辑一致性，避免数据错误导致决策失误。

---

## 二、校核公式

### 2.1 校核1：总任务 = 已整改 + 未整改

**公式**：
```
总任务个数 = 已整改个数 + 未整改个数
总任务面积 = 已整改面积 + 未整改面积
总任务耕地面积 = 已整改耕地面积 + 未整改耕地面积
```

**逻辑说明**：
- 总任务：所有非农违法（或非粮违法）图斑
- 已整改：完成整改的图斑（剩余未整改面积=0 且 拆分状态="审核结束"）
- 未整改：未完成整改的图斑（剩余未整改面积>0 或 拆分状态≠"审核结束"）

**差异计算**：
```python
差异_个数 = 总任务个数 - (已整改个数 + 未整改个数)
差异_面积 = 总任务面积 - (已整改面积 + 未整改面积)
差异_耕地 = 总任务耕地面积 - (已整改耕地面积 + 未整改耕地面积)
```

**判定标准**：
- 差异 = 0：✅ 校核通过
- 差异 ≠ 0：❌ 校核失败，需检查数据
- 浮点精度误差（|差异| < 1e-10）：✅ 视为0，校核通过

---

### 2.2 校核2：已整改 = 拆除 + 补办

**公式**：
```
已整改个数 = 拆除个数 + 补办个数
已整改面积 = 拆除面积 + 补办面积
已整改耕地面积 = 拆除耕地面积 + 补办耕地面积
```

**逻辑说明**：
- 已整改：完成整改的图斑
- 拆除：整改方式为拆除的图斑（整改情况包含"拆除" 或 拆除面积>0）
- 补办：整改方式为补办的图斑（整改情况包含"补办" 或 补办面积>0）

**差异计算**：
```python
差异_个数 = 已整改个数 - (拆除个数 + 补办个数)
差异_面积 = 已整改面积 - (拆除面积 + 补办面积)
差异_耕地 = 已整改耕地面积 - (拆除耕地面积 + 补办耕地面积)
```

**判定标准**：
- 差异 = 0：✅ 校核通过
- 差异 ≠ 0：❌ 校核失败，需检查数据

---

## 三、校核失败原因分析

### 3.1 校核1失败可能原因

| 原因 | 说明 | 解决方法 |
|-----|------|---------|
| 图斑分类错误 | 图斑被错误分类为已整改或未整改 | 检查剩余未整改面积和拆分状态 |
| 数据缺失 | 部分图斑数据缺失 | 检查原始数据完整性 |
| 计算错误 | 面积计算有误 | 重新计算并四舍五入 |

### 3.2 校核2失败可能原因

| 原因 | 说明 | 解决方法 |
|-----|------|---------|
| 整改方式判定错误 | 拆除/补办判定条件有误 | 检查整改情况文本和面积列 |
| 同时存在拆除和补办 | 一个图斑同时有拆除和补办记录 | 需明确主整改方式或分别统计 |
| 其他整改方式 | 存在既非拆除也非补办的整改方式 | 增加"其他"整改方式分类 |

---

## 四、校核实施步骤

### 4.1 数据准备

```python
# 1. 筛选非农违法图斑
illegal = verified[verified['核实认定意见'].str.contains('非农违法', na=False)]

# 2. 判定整改状态
completed = illegal[(illegal['剩余未整改面积'] == 0) & (illegal['拆分状态'] == '审核结束')]
pending = illegal[(illegal['剩余未整改面积'] > 0) | (illegal['拆分状态'] != '审核结束')]

# 3. 判定整改方式
demolish = completed[completed['整改情况'].str.contains('拆除', na=False) | (completed['拆除面积（亩）'] > 0)]
supplement = completed[completed['整改情况'].str.contains('补办', na=False) | (completed['补办面积（亩）'] > 0)]
```

### 4.2 逐县计算

```python
for county in all_counties:
    ill = illegal[illegal['县级行政区名称'] == county]
    comp = completed[completed['县级行政区名称'] == county]
    dem = demolish[demolish['县级行政区名称'] == county]
    sup = supplement[supplement['县级行政区名称'] == county]
    pend = pending[pending['县级行政区名称'] == county]
    
    # 计算各项指标
    total_count = len(ill)
    total_area = round(ill['非农违法面积（亩）'].sum(), 2)
    total_farmland = round(ill['非农违法耕地面积（亩）'].sum(), 2)
    
    completed_count = len(comp)
    completed_area = round(comp['非农违法面积（亩）'].sum(), 2)
    completed_farmland = round(comp['非农违法耕地面积（亩）'].sum(), 2)
    
    demolish_count = len(dem)
    demolish_area = round(dem['拆除面积（亩）'].sum(), 2)
    demolish_farmland = round(dem['拆除耕地面积（亩）'].sum(), 2)
    
    supplement_count = len(sup)
    supplement_area = round(sup['补办面积（亩）'].sum(), 2)
    supplement_farmland = round(sup['补办耕地面积（亩）'].sum(), 2)
    
    pending_count = len(pend)
    pending_area = round(pend['非农违法面积（亩）'].sum(), 2)
    pending_farmland = round(pend['非农违法耕地面积（亩）'].sum(), 2)
    
    # 校核
    check1_count = total_count - (completed_count + pending_count)
    check1_area = total_area - (completed_area + pending_area)
    check1_farmland = total_farmland - (completed_farmland + pending_farmland)
    
    check2_count = completed_count - (demolish_count + supplement_count)
    check2_area = completed_area - (demolish_area + supplement_area)
    check2_farmland = completed_farmland - (demolish_farmland + supplement_farmland)
```

### 4.3 校核结果展示

```python
print('=== 校核结果 ===')
print(f'校核1（总任务=已整改+未整改）：')
print(f'  个数差异：{check1_count}')
print(f'  面积差异：{check1_area}')
print(f'  耕地差异：{check1_farmland}')
print(f'校核2（已整改=拆除+补办）：')
print(f'  个数差异：{check2_count}')
print(f'  面积差异：{check2_area}')
print(f'  耕地差异：{check2_farmland}')
```

---

## 五、Excel校核列设置

### 5.1 校核列位置

| 列号 | 列名 | 公式 |
|-----|------|------|
| R | 总=已+未 个数 | =C-G-O |
| S | 总=已+未 面积 | =D-H-P |
| T | 总=已+未 耕地 | =E-I-Q |
| U | 已=拆+补 个数 | =G-I-L |

### 5.2 条件格式

- 差异 = 0：正常显示
- 差异 ≠ 0：红色背景(#FFC7CE)，红色字体(#9C0006)

### 5.3 合计行校核

合计行也应进行校核，确保总计数据逻辑一致。

---

## 六、常见问题

### Q1: 为什么校核1面积差异不为0？

**A**: 可能是浮点精度问题。如果差异很小（< 1e-10），可以视为0。如果差异较大，需检查：
- 原始数据是否有误
- 四舍五入是否一致
- 图斑分类是否正确

### Q2: 一个图斑同时有拆除和补办记录怎么办？

**A**: 根据整改情况文本判断主整改方式。如果无法判断，可以：
- 优先按拆除统计（拆除更彻底）
- 或增加"拆除+补办"分类
- 或在备注中说明

### Q3: 待审核图斑算已整改还是未整改？

**A**: 根据规则，只有"审核结束"才算完成整改。待审核图斑（市级待审核、省级待审核）算未整改。

### Q4: 剩余未整改面积=0但拆分状态不是"审核结束"怎么办？

**A**: 算未整改。必须同时满足两个条件：
- 剩余未整改面积 = 0
- 拆分状态 = "审核结束"

---

**文档版本**：1.1  
**更新时间**：2026-08-27
