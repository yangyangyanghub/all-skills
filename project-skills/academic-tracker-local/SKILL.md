---
name: academic-tracker-local
description: >
  在本地或 OpenCode 生态中从零搭建一个全自动、多维度的学术追踪器，完全脱离第三方平台。
  当用户要求"本地搭建学术追踪器"、"脱离 Coze 做论文追踪"、"Semantic Scholar 追踪"、"GitHub 趋势追踪"、
  "GeoAI 项目监控"时使用此技能。
  基于 Python + RSS/学术 API/GitHub API 多源抓取 + LLM 智能分析 + 推送，实现端到端自动化。
---

# 本地化学术追踪器 (Multi-Source)

## 架构升级

本次升级采用**"陆地 + 海洋 + 空中"三维数据源架构**，确保信息无死角：
| RSS (陆地) | 基础盘 | 稳定追踪知网、核心订阅源。 |
| Semantic Scholar (海洋) | 深水区 | API 覆盖全球 2 亿+论文，获取引用数据。 |
| GitHub (空中) | 风向标 | 捕捉尚未发表论文的最新开源工具。 |

## 部署步骤
### 1. 初始化项目
mkdir -p ~/academic-tracker/{data,reports}
pip install feedparser requests python-dotenv

### 2. 配置 .env
LLM_BASE_URL=http://localhost:11434/v1
LLM_MODEL=qwen2.5:7b
RESEARCH_TOPIC="我主要关注地理信息系统（GIS）、空间智能、遥感 AI..."
RSS_LIMIT=20
SEMANTIC_LIMIT=10
GITHUB_MIN_STARS=50
