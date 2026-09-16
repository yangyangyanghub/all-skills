---
name: change-survey-to-enforcement
description: 变更调查流向执法地类判定审核助手（市局侧）。读国土调查云河北分中心（http://121.29.50.223:8085/hbgty/）的图斑举证（套合结果 / 现场照片 / 附件资料 / 核查填报），按《全省土地执法与一体化调查监测衔接工作培训》+《一体化执法填报明白纸》规则判定，输出审核意见（该定哪类 + 依据哪条 + 举证缺什么）。触发词包括"变更流向执法判定"、"图斑判定审核"、"合法性判定核查"、"举证核查"、"地类判定审核"、"审核意见"、"这个图斑该定哪类"、"变更调查审核"。注意：纯统计/报表需求走 land-law-enforcement-stats 技能；本技能只做判定审核。
---

# 变更调查流向执法地类判定审核助手

## 定位

**市局审核助手**：读系统举证 → 给判定依据。**不重判、不自动定性**。

## 铁律

1. **只读系统**——绝不点「提报 / 退回 / 保存 / 标为典型问题 / 一键提报」
2. **不下定性结论**——只输出「与填报不一致」和「举证缺失」，最终定性由人签
3. **规则可追溯**——每条结论必须能指到规则 id + 字段值
4. **无法核实标「存疑」**——导出表缺该类举证字段时只能标存疑，**不得误报「不一致」**

## 使用流程

### 前置：打开调试浏览器

```powershell
# 独立配置，不影响日常 Chrome
& "C:\Program Files\Google\Chrome\Application\chrome.exe" `
  --remote-debugging-port=9222 `
  --user-data-dir="$env:TEMP\chrome-debug" `
  "http://121.29.50.223:8085/hbgty/"
# 在弹出的窗口里登录系统
```

### 方式一：审系统里的图斑（浏览器取数）

```bash
# 1. 看列表
node scripts/system_adapter.mjs list

# 2. 打开第 1 条详情并读举证
node scripts/system_adapter.mjs detail 0
node scripts/system_adapter.mjs evidence
```

### 方式二：审导出的图斑表（离线批量）

```bash
# 1. 导出表 → 结构化
python scripts/load_parcels.py "图斑列表.xlsx" -o out/parcels.json

# 2. 规则判定
python scripts/judge.py out/parcels.json -o out/results.json

# 3. 屏幕看审核意见
python scripts/review.py out/results.json
python scripts/review.py out/results.json --only-mismatch   # 只看不一致
python scripts/review.py out/results.json --id 130208SJBG26210951
```

## 规则来源

| 来源 | 文件 | 作用 |
|---|---|---|
| 政策口径 | 《全省土地执法与一体化调查监测衔接工作培训》2026-08-25 第 4–24 页 | 判定情形、举证要求 |
| 系统枚举 | 《一体化执法填报明白纸》 | 系统字段取值（**冲突时以此为准**） |

规则字典：`data/rule-dictionary.json`

## 关键判定要点

1. 非农违法有前置条件：**非农整改到位才能认定通过**
2. 出入口地块量化门槛（>2 亩：套合≥95% 且未套合耕地<0.5 亩；≤2 亩：套合主体建筑≥90% 且未套合耕地<0.5 亩）
3. 设施农用地省级放宽口径（上图入库信息范围内 + 用途不明确但不能确定为建设用地 → 提交县级说明 + 承包流转合同 + 采购合同 + 发票 → 调查为设施农用地，纳入跟踪）
4. 农村道路硬门槛：北方宽 2.0–8.0 米、国家公路网之外
5. 违法类须按建设年份分新增 / 存量

## 实测踩坑（务必知悉）

| 坑 | 说明 |
|---|---|
| `203` 值落在 `城镇村属性` 列 | 不在 `城镇村属性码` 列，两列都要读 |
| 系统枚举 ≠ 明白纸文本 | `203范围` vs `203范围及开天窗`、`边坡治理地块` vs `边坡治理`；见 `aliases` |
| 导出表举证字段全空 | 全部「占比(%)」与「批准文号」列 0% 填报；举证只在系统页面里 |
| `伪变化` / `实地为设施` | 系统实际存在、明白纸没有的取值，已入 `top_level_extra` / `aliases` |

## 系统页面结构（2026-09-15 实测）

- 系统：国土调查云河北分中心工作平台 3.0
- 详情页 6 tab：线索详情 / 套合结果 / 审核复核 / 现场照片 / 附件资料 / 成果复用
- 左侧导航：项目清单（未提报 / 判定合法 / 判定违法 / 判定其它 / 判定农村道路 / 判定设施农用地 / 变更退回整改 / 异议清单）+ 审核清单（待审核 / 已审核 / 变更退回整改 / 异议清单）

## 测试

```bash
python tests/test_rule_dictionary.py
python tests/test_load_parcels.py
python tests/test_judge.py
python tests/test_review.py
node tests/test_cdp_client.mjs
node tests/test_system_adapter.mjs
```
