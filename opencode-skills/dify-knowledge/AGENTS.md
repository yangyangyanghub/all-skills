# DIFY-KNOWLEDGE SKILL KNOWLEDGE

## OVERVIEW
该目录只有一个核心文件：`SKILL.md`。它定义了 dify-knowledge 技能的触发条件、检索流程、文档生成规则与外部依赖。

## WHERE TO LOOK
| 任务 | 位置 | 说明 |
|---|---|---|
| 查看技能元数据 | `SKILL.md` 开头 | name / description / requires |
| 查看知识库分类 | `SKILL.md` “知识库分类” | 两个 dataset 的用途不同 |
| 查看 API 细节 | `SKILL.md` “API 调用” | `curl`、Bearer、`top_k` |
| 查看问答模式 | `SKILL.md` “模式一：简单问答” | 单库/双库检索逻辑 |
| 查看长文模式 | `SKILL.md` “模式二：长文生成” | 三轮检索与文档生成 |
| 查看模板与注意事项 | `SKILL.md` 末尾 | 文档结构模板、限制条件 |

## CONVENTIONS
- `SKILL.md` 是唯一事实来源；修改前先通读相关章节。
- 简单问答与长文生成是两套不同流程，不能混写。
- 长文生成开始前必须先确认目标字数。
- 长文生成仅查知识库 1，且对片段有 `score > 0.15` 过滤。
- 输出要求同时覆盖 Markdown 与 Word 文档。

## ANTI-PATTERNS
- 不要把知识库 2 用于长文生成流程。
- 不要跳过字数确认与阶段性进度通知。
- 不要在未核实服务可用性的情况下改动 Dify 地址、dataset ID、API Key 格式。
- 不要把文档模板当成固定死板结构；应先做内容聚类，再推断章节。

## NOTES
- 当前目录没有源码、测试或构建脚本。
- `.DS_Store` 可忽略，真正重要的只有 `SKILL.md`。
