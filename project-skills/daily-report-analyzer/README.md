# 日报智能分析器 (daily-report-analyzer)

从钉钉OA审批获取员工日报数据，进行六维度智能评分，生成Markdown和HTML可视化报告。

---

## 一、功能特性

| 能力 | 说明 |
|------|------|
| 数据获取 | 从钉钉OA审批获取日报数据，包含完整审批流程信息 |
| 六维度评分 | 完整度、内容质量、AI应用、及时性、工作量、计划性 |
| 流水账检测 | 自动识别"只写项目名不说具体工作"等敷衍内容 |
| 审批效率分析 | 统计审批耗时、首审延迟、部门完成率 |
| 可视化报告 | 生成HTML图表报告 + Markdown报告 + Excel清单 |

---

## 二、环境要求

- Python 3.8+
- 钉钉企业账号（需有开放平台权限）

---

## 三、安装配置

### 3.1 安装依赖

```bash
pip install requests pandas openpyxl
```

### 3.2 配置钉钉凭证

**方式一：配置文件（推荐）**

创建 `~/.dingtalk/config.json`：

```json
{
  "app_key": "your_app_key",
  "app_secret": "your_app_secret"
}
```

**方式二：环境变量**

```bash
# Linux/macOS
export DINGTALK_APP_KEY="your_app_key"
export DINGTALK_APP_SECRET="your_app_secret"

# Windows PowerShell
$env:DINGTALK_APP_KEY="your_app_key"
$env:DINGTALK_APP_SECRET="your_app_secret"

# Windows CMD
set DINGTALK_APP_KEY=your_app_key
set DINGTALK_APP_SECRET=your_app_secret
```

### 3.3 申请钉钉权限

在钉钉开放平台申请以下权限：

| 权限名称 | 权限代码 | 用途 |
|---------|---------|------|
| 审批实例读权限 | `ProcessInstance.Read` | 获取审批详情、操作记录 |
| 审批流程读权限 | `Workflow.Process.Read` | 获取流程模板信息 |
| 部门列表读权限 | `qyapi_get_department_list` | 获取部门结构（可选） |
| 部门成员读权限 | `qyapi_get_department_member` | 获取部门人数（可选） |

**申请步骤**：
1. 登录 [钉钉开放平台](https://open.dingtalk.com/)
2. 进入应用 → 权限管理
3. 申请上述权限并等待审批

---

## 四、快速使用

### 4.1 一键执行

```bash
# 分析今日日报
python .opencode/skill/daily-report-analyzer/scripts/run_all.py --date=today

# 分析昨日日报
python .opencode/skill/daily-report-analyzer/scripts/run_all.py --date=yesterday

# 分析指定日期
python .opencode/skill/daily-report-analyzer/scripts/run_all.py --date=2026-03-12
```

### 4.2 单独执行各步骤

```bash
# 步骤1: 获取日报数据
python .opencode/skill/daily-report-analyzer/scripts/fetch_oa_reports.py --date=today

# 步骤2: 分析评分
python .opencode/skill/daily-report-analyzer/scripts/analyze_reports.py --date=today

# 步骤3: 生成Markdown报告
python .opencode/skill/daily-report-analyzer/scripts/generate_report.py --date=today

# 步骤4: 生成HTML报告
python .opencode/skill/daily-report-analyzer/scripts/generate_html_report.py --date=today
```

---

## 五、命令行参数

### fetch_oa_reports.py（数据获取）

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--date` | 目标日期，支持 `YYYY-MM-DD` 或 `today`/`yesterday` | `today` |
| `--template` | 审批模板名称 | `员工日报` |
| `--process-code` | 审批模板code（不填则自动获取） | - |
| `--output` | 输出目录 | `daily-reports/` |
| `--status` | 审批状态: `RUNNING`/`TERMINATED`/`COMPLETED` | `COMPLETED` |
| `--fetch-dept-count` | 获取部门人数（需额外权限） | `False` |
| `--dept-config` | 部门人数配置文件（JSON格式） | - |

### run_all.py（一键执行）

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--date` | 目标日期 | `today` |
| `--template` | 审批模板名称 | `员工日报` |
| `--skip-fetch` | 跳过数据获取，直接分析已有数据 | `False` |

---

## 六、输出文件

执行后生成 `daily-reports/YYYY-MM-DD/` 目录：

```
daily-reports/2026-03-12/
├── raw_reports.json      # 原始数据（含审批信息）
├── summary.json          # 数据概要
├── scores.json           # 评分详情
├── analysis.json         # 分析结果
├── daily-report.md       # Markdown分析报告
├── report.html           # HTML可视化报告（推荐）
└── data-list.xlsx        # Excel数据清单
```

### 文件说明

| 文件 | 内容 |
|------|------|
| `raw_reports.json` | 钉钉API返回的原始数据，包含审批流程、操作记录等 |
| `summary.json` | 数据概要统计，包含部门提交率、审批效率等 |
| `scores.json` | 每个员工的六维度评分详情 |
| `analysis.json` | 分析结果，包含AI应用案例、流水账清单等 |
| `daily-report.md` | Markdown格式报告，适合在Obsidian等工具查看 |
| `report.html` | HTML可视化报告，包含图表，浏览器直接打开 |
| `data-list.xlsx` | Excel格式，包含多个Sheet便于二次分析 |

---

## 七、评分体系

### 7.1 六维度评分

| 维度 | 权重 | 评估重点 |
|------|------|----------|
| 完整度 | 20% | 工作内容+复盘+计划是否完整 |
| 内容质量 | 25% | 是否详细描述，是否流水账 |
| AI工具应用 | 20% | 是否用AI解决具体问题 |
| 及时性 | 15% | 提交时间 |
| 工作量 | 10% | 内容丰富程度 |
| 计划性 | 10% | 明日计划和协调事项 |

### 7.2 流水账检测

自动识别以下问题并标记：
- 工作内容少于10字
- 只有项目名，没有具体工作描述
- 没有动作动词（完成、进行、开展等）

### 7.3 AI应用评分标准

| 分值 | 标准 | 示例 |
|------|------|------|
| 5分 | 明确解决具体问题 | "使用AI协助接口开发" |
| 4分 | 有应用场景 | "查询相关规范标准号" |
| 3分 | 只提工具名 | "AI豆包应用" |
| 2分 | 诚实填写未使用 | "无" |
| 1分 | 未填写 | - |

---

## 八、自定义配置

### 8.1 评分权重配置

编辑 `references/scoring_config.json`：

```json
{
  "weights": {
    "completeness": 0.20,
    "content_quality": 0.25,
    "ai_application": 0.20,
    "timeliness": 0.15,
    "workload": 0.10,
    "planning": 0.10
  },
  "ai_keywords": ["ai", "AI", "豆包", "deepseek", "kimi", "chatgpt", "文心", "通义", "讯飞", "智谱"],
  "lazy_report_detection": {
    "rules": [
      "工作内容少于10字",
      "只写项目名没有具体工作描述",
      "没有动词（完成、进行、开展等）"
    ]
  }
}
```

### 8.2 部门人数配置

如果无法获取钉钉部门人数权限，可手动创建配置文件：

```json
{
  "环境艺术所": 15,
  "建筑分院": 20,
  "测绘一队": 10
}
```

使用方式：

```bash
python scripts/fetch_oa_reports.py --date=today --dept-config=dept_config.json
```

---

## 九、常见问题

### Q: 无法获取日报数据？

**检查清单**：
1. 确认 `app_key` 和 `app_secret` 正确
2. 确认权限已申请并生效（审批权限需要管理员审批）
3. 检查API调用次数是否超限（标准版每月1万次）
4. 确认审批模板名称正确（默认为"员工日报"）

### Q: 审批效率数据为空？

- 确保使用 `fetch_oa_reports.py` 获取数据
- 审批效率分析需要 `ProcessInstance.Read` 权限
- 检查日报是否有审批流程

### Q: 如何获取部门人数？

**方式一**：使用 `--fetch-dept-count` 参数自动获取（需要 `qyapi_get_department_member` 权限）

**方式二**：手动创建部门人数配置文件并使用 `--dept-config` 参数

### Q: API调用频率限制？

钉钉API有调用频率限制，建议：
- 不要频繁调用，每次分析只获取一天数据
- 大量数据时分批次获取
- 检查钉钉开放平台的调用统计

---

## 十、注意事项

1. **API限制**：钉钉API标准版每月1万次调用，企业版更高
2. **数据安全**：日报数据包含敏感信息，注意存储安全
3. **权限原则**：仅申请必要权限，遵循最小权限原则
4. **数据处理**：保证数据真实性，必须使用API调用获取，不能虚构数据

---

## 十一、技术架构

```
┌─────────────────────────────────────────────────────────────┐
│                    run_all.py (入口)                        │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│ fetch_oa_     │    │ analyze_      │    │ generate_     │
│ reports.py    │───▶│ reports.py    │───▶│ report.py     │
│               │    │               │    │               │
│ 钉钉API调用    │    │ 六维度评分     │    │ Markdown报告  │
└───────────────┘    └───────────────┘    └───────────────┘
                                                  │
                                                  ▼
                                         ┌───────────────┐
                                         │ generate_     │
                                         │ html_report.py│
                                         │               │
                                         │ HTML可视化    │
                                         └───────────────┘
```

---

## 十二、更新日志

| 版本 | 日期 | 更新内容 |
|------|------|----------|
| 1.0.0 | 2026-03-13 | 初始版本，支持OA审批日报获取、六维度评分、可视化报告生成 |

---

## 十三、License

MIT License