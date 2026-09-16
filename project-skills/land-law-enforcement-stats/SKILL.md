---
name: land-law-enforcement-stats
description: 土地执法遥感监测统计技能 · **入口路由**。专门处理土地执法遥感监测图斑 Excel 数据。本技能是**入口**，只负责「识别数据子类型 → 路由到对应子技能」。**子类型 A（卫片检索明细表，字段图斑状态/拆分状态）请转 land-law-enforcement-stats-weipian 子技能；子类型 B（业务表多阶段审核，字段状态(系统)+审核阶段(系统)+打回状态(系统)，如大运河排查/专项整治/变更调查）请转 land-law-enforcement-stats-biz 子技能。** 触发词包括"图斑统计"、"违法线索统计"、"非农违法统计"、"非粮违法统计"、"整改统计"、"图斑汇总"、"图斑核实统计"、"土地执法统计"、"土地违法统计"、"遥感图斑统计"、"遥感图斑汇报"、"土地执法遥感统计"、"土地执法遥感汇报"、"对县区发函"、"发提示函"、"县区提示函"、"整改提示函"、"给县里发函"、"业务表"、"大运河排查"、"变更调查"、"变更调查日报"、"专项整治"、"多阶段审核"、"状态机审核"、"流程进度"、"排查清单"、"县级填报"、"审核阶段"、"打回状态"、"卫片执法流转"，或看到 Sheet 名是"图斑列表"（需判断入口字段是"图斑状态"还是"状态(系统)"）。注意：不带"图斑/违法/土地执法"限定的"遥感统计"、"遥感汇报"需结合土地执法上下文；通用"生成汇报"、"写汇报"需结合土地执法遥感监测上下文才触发本技能。
---

# 土地执法遥感监测统计 · 入口路由

本技能是**入口**，职责：①识别数据子类型 ②路由到对应子技能。**不处理具体业务逻辑**——具体统计/报表/汇报逻辑在各子技能中。

## 一、数据子类型识别（首要步骤）

> 🔴 **STOP · 这一步决定走哪条子技能，识别错了整套统计全错**。读源数据后**必须**先看入口字段，再路由。

读源数据后按入口字段判定：

```
if 列名包含 '图斑状态' and 列名包含 '拆分状态':
    → 子类型 A：卫片检索明细表 → 转 land-law-enforcement-stats-weipian
elif 列名包含 '状态(系统)' and 列名包含 '审核阶段(系统)':
    → 子类型 B：业务表（多阶段审核）→ 转 land-law-enforcement-stats-biz
else:
    → 问用户提供更多字段样本
```

| 判断依据 | 子类型 | 路由 |
|---------|:---:|------|
| `图斑状态` + `拆分状态` | A（卫片） | → **weipian** |
| `状态(系统)` + `审核阶段(系统)` | B（业务表） | → **biz** |
| 其它 | — | 问用户 |

> **注意**：看到 Sheet 名"图斑列表"**不能直接判断**——必须看入口字段是 `图斑状态`（A）还是 `状态(系统)`（B）。

## 二、两份子技能

| 子技能 | 业务 | 入口字段 | 脚本 |
|:---:|------|---------|------|
| **land-law-enforcement-stats-weipian** | 卫片检索明细表（原始下发/核实后/非农违法/非粮违法/整改 + 汇报 + 提示函） | `图斑状态` | `generate_county_stats/illegal_stats/illegal_list.py` |
| **land-law-enforcement-stats-biz** | 业务表（多阶段审核 + 大运河排查 + 变更调查日报） | `状态(系统)+审核阶段(系统)` | `generate_business_checklist/change_survey_daily.py` |

## 三、触发词分流（按用户说法）

| 用户说法 | 子类型 | 路由 |
|---------|:---:|------|
| 卫片统计、遥感图斑统计、违法线索统计、非农违法统计、逐县统计表、情况汇报、对县区发函 | A | 转 **weipian** |
| 排查清单、专项整治、大运河排查、变更调查、变更调查日报、多阶段审核、状态机审核、流程进度、县级填报 | B | 转 **biz** |
| 图斑清单、图斑排查（无前置词） | 不确定 | **先看入口字段** |

## 四、共享资源

脚本和参考文档保留在本技能目录（`.opencode/skills/land-law-enforcement-stats/`），两个子技能通过相对路径 `../scripts/...`、`../references/...` 引用（子技能在 `weipian/` 或 `biz/` 下，向上到父目录即 `../`）。

| 资源 | 归属 |
|------|------|
| `scripts/generate_county_stats.py` | A（卫片） |
| `scripts/generate_illegal_stats.py` | A（卫片） |
| `scripts/generate_illegal_list.py` | A（卫片） |
| `scripts/generate_business_checklist.py` | B（业务表） |
| `scripts/generate_change_survey_daily.py` | B（业务表） |
| `scripts/generate_county_dilei.py` | B（业务表） |
| `scripts/generate_dilei_flow.py` | B（业务表） |
| `scripts/generate_dilei_summary.py` | B（业务表） |
| `scripts/generate_county_dilei.py` | B（业务表·分县地类） |
| `scripts/generate_dilei_flow.py` | B（业务表·地类流向） |
| `references/field_specification.md` | A |
| `references/validation_rules.md` | A |
| `references/business_table_field_spec.md` | B |

## 五、通用约定（两子技能共用）

- **违面积专用列**：违法统计用"非农违法面积（亩）"等专用列，勿用图斑面积
- **校核**：核算公式必须校验，差异标红
- **打印**：A4 横向、1页宽×1页高、边距 0.3-0.4 英寸
- **样式**：微软雅黑、蓝色表头(#4472C4)、黄色合计行(#FFF2CC)
- **改源表必须备份**：`_backup_YYYY-MM-DD` 后缀

**技能版本**：1.5 · 拆分为入口路由 + 双子技能（weipian / biz）
