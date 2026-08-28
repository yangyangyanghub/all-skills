---
name: token-usage-report
description: 统计 HDPD 或 new-api 的 API key/token 使用量，并自动生成按昨日增量对比的 Markdown 报告。当用户提到“统计 key 消耗”“看下 token 使用”“API key 用量”“生成 token 报告”“对比昨日消耗”“HDPD 使用量”这类需求时，必须优先使用此技能。它会查询当前用量、自动选择日期合法的最近历史快照作为基准，并把结果写入 assets/tokens/YYYY-MM-DD.md。
---

# Token Usage Report

用于生成 HDPD API key 使用量日报。

## 适用场景

- 用户要看 HDPD / new-api 的 key 消耗排行
- 用户要统计今日 token 使用量
- 用户要生成“较昨日新增”对比报告
- 用户要把结果落盘到 `assets/tokens/`

## 默认流程

直接运行：

```bash
python .opencode/skill/token-usage-report/scripts/generate_token_report.py
```

脚本会自动完成这些事：

1. 调用 `temp/query_tokens_detail.py` 获取当前使用量
2. 读取系统今天日期
3. 在 `assets/tokens/` 中选择日期严格小于今天的最新快照作为基准
4. 计算每个 key 的较昨日新增量
5. 生成 Markdown 报告到 `assets/tokens/YYYY-MM-DD.md`

## 输出要求

报告必须包含：

- `## 统计摘要`
- `## 排行榜`
- 表头：`排名 | 名称 | 总消耗（M) | **较昨日新增（M)**`

排序规则：

- 按总消耗降序排列

## 使用说明

### 标准执行

```bash
python .opencode/skill/token-usage-report/scripts/generate_token_report.py
```

### 执行完成后

你应该：

1. 告诉用户生成的文件路径
2. 说明本次使用的基准快照是哪一天
3. 说明今日新增总量
4. 如果没有历史快照，明确说明本次是首份快照，新增量按当前总量处理

## 异常处理

- 如果 `temp/query_tokens_detail.py` 不存在，直接报错并说明缺少查询脚本
- 如果 `assets/tokens/` 中存在未来日期快照，忽略它们
- 如果今天的报告文件已存在，允许覆盖，但基准仍然只能选“严格早于今天”的快照，避免把今天自己当基准

## 说明

- 这个技能只负责当前这条固定流程，不扩展成通用数据库查询技能
- 底层数据库连接与 SSH 查询能力复用现有 `temp/query_tokens_detail.py`
