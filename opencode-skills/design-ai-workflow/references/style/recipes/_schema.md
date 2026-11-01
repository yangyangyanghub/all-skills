# 配方字段定义

> 配方 = 把"设计判断"变成可执行提示词的结构。**配方里只放结构，不放别人的原文**。
> 别人的原文不进仓库，只记来源链接与「哪一句是 anchor」的判断。见 [_sources.md](_sources.md)。

## 字段

| 字段 | 必填 | 说明 |
|---|---|---|
| `id` | ✅ | 文件名即 id，小写短横线 |
| `title` | ✅ | 中文名，用于日志与交付清单 |
| `drawing` | ✅ | `analysis` / `render` / `masterplan` / `concept`，对应五图纸 |
| `delivery` | ✅ | `deliverable` / `intent-only` / `concept-only`。**这是红线，不是建议** |
| `source` | ✅ | 提炼自哪篇文章（标题 + URL），可追溯 |
| `requires` | ✅ | `base`（satellite/plan/white_model/photo/model/axonometric/none）、`refs`（需要几张参考图）、`view`（视角） |
| `constraint_block` | 视 `delivery` | 保什么不变。`deliverable` 必填 |
| `vars` | ✅ | 骨架里除内置字段外，需要外部给的变量名 |
| `palette_map` / `palette_note` | 二选一 | 色板到功能的映射，或色板说明 |
| `elements` | 建议 | 图元清单（指北针、比例尺、标注模块…） |
| `composition` | 建议 | 构图与排版约束 |
| `anchors` | ✅ 至少 1 条 | **"别人不会这么写"的那句话**。没有 anchor 的配方只是在堆词 |
| `avoid` | ✅ | 负向清单 |
| `prompt_skeleton` | ✅ | 拼装模板，`{变量}` 占位 |

## 内置占位符（不用在 `vars` 里声明）

`{constraint_block}` `{elements}` `{composition}` `{palette_map}` `{palette_note}` `{title}` `{id}`

## 三条硬规矩

1. **`deliverable` 必须有 `constraint_block`。** 没有保真约束的配方不可能产出可交付图。
2. **`concept-only` 不许写"保持…不变"。** 写了就是定位自相矛盾——要么它是概念图，要么它有保真要求。
3. **骨架里的占位符必须在 `vars` 里声明。** 写漏了 `--check` 会报错，避免运行时静默留空。

## 校验

```powershell
python scripts\compose_prompt.py --check
```

它会逐条查：有没有 anchor、占位符能否被解释、交付定位与约束块是否自相矛盾。

## 怎么用

```powershell
python scripts\compose_prompt.py --list
python scripts\compose_prompt.py --recipe render-arch --set style=安藤忠雄 --set materials=清水混凝土 --set env=滨江地块 --set building_type=美术馆
```

缺变量会直接报错并列出该配方声明的变量，不会拼出一个带 `{}` 的半成品。
