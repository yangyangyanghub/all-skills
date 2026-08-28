# 视频生成器

自动生成视频，支持四种模式：
- **新闻简报模式**（口播）：Markdown → 3:4 竖版视频，逐条 TTS 配音（视频号/小红书）
- **简报模式**（合屏）：Markdown → 3:4 竖版视频，同类新闻合屏展示，无配音 BGM 仅 15s
- **技术分享模式**（口播）：调研 Markdown → 3:4 竖版视频，按章节组织，支持表格/代码/GitHub截图
- **系统演示模式**：网页截图 → 16:9 横版视频（B 站/YouTube）

## 触发词

- "生成视频"
- "新闻视频" / "简报视频"
- "系统演示视频" / "操作录屏"
- "视频号视频" / "小红书视频"
- "技术分享视频" / "调研视频" / "调研转视频"

## 通用性说明

本 skill **不是教育系统专用**，所有品牌和内容都是配置驱动的。

**新闻模式**：复制一份 Markdown，改标题和新闻条目即可。
**演示模式**：复制一份 JSON 配置，改 brand + steps + base-url 即可，零代码改动。

| 需要改的 | 不需要改的 |
|---------|-----------|
| 新闻模式：Markdown 文件内容 | 流水线脚本（build_*.py） |
| 演示模式：`config.json` 里的 `brand.*` 和 `steps` | HyperFrames composition 模板 |
| 演示模式：`--base-url` 指向目标系统地址 | 渲染参数（`--workers 2 --page-side-compositing=no`） |

## 执行流程

### Phase 0：准备（通用）

0.1 确认输入文件（Markdown 或 JSON）存在
0.2 校验输入格式：Markdown 需含至少一个 `##` 章节，JSON 需含 `steps` 数组
0.3 确认 HyperFrames 已安装且 ≥0.12.0：`npx hyperframes --version`
0.4 确认 ffmpeg 可用：`ffprobe -version`
0.5 演示模式/技术分享模式需确认 Playwright 已安装：`playwright install chromium`

**检查点 A**：`npx hyperframes --version` 返回版本号

### Phase 1：截图 + 配音（按模式分支）

**演示模式**（walkthrough）：
1.1 Playwright 截图每个 step 的 URL（视口 1920×1080，`fullPage=false`）
1.2 edge-tts 逐 step 生成配音，测量每段时长 → `audio/seg_*.mp3`

**新闻模式**（news）：
1.1 生成 HTML 卡片（`slides/slide_*.html`），视口 1080×1440
1.2 Playwright 截取每张卡片 → `captures/seg_*/screenshot.png`
1.3 edge-tts 逐条生成配音，测量每段时长 → `audio/seg_*.mp3`

**技术分享模式**（tech）：
1.1 生成 HTML 卡片（`slides/slide_*.html`），视口 1080×1440
1.2 Playwright 截取每张本地 HTML 卡片 → `captures/seg_*/screenshot.png`
1.3 对项目主页 URL 远程截图（视口 1280×800，`fullPage=true`，超时 30s，失败跳过）
1.4 edge-tts 逐 slide 生成配音 → `audio/seg_*.mp3`

**简报模式**（brief）：无截图、无配音，跳过 Phase 1

**检查点 B1（截图验证）**：`captures/seg_*/screenshot.png` 数量与 steps/slides 数一致，非空文件
**检查点 B2（技术分享远程截图）**：远程 URL 截图至少成功 1 张，全部失败则提示但不中断
**检查点 C**：`audio/seg_*.mp3` 全部生成

### Phase 2：渲染 + 音轨合成（通用）

2.1 时间线计算 → 生成 `index.html`（含每片段 start/duration）
2.2 HyperFrames 合成无声视频：`npx hyperframes render`
2.3 ffmpeg 合并音轨（TTS adelay + amix，BGM 可选叠加）
2.4 抽帧验证关键位置

**检查点 D**：片头标题 → 内容 → 字幕同步 → TTS 配音 → 片尾感谢
**检查点 E**：`ffprobe final-with-audio.mp4` 显示 `h264,video` + `aac,audio`

## 故障恢复

| 现象 | 原因 | 解决 |
|------|------|------|
| 只有深蓝背景，无截图 | 用了 `--skip-capture` | 去掉 `--skip-capture` 重新跑 |
| 截图全空白 | 登录态过期 | 重新保存 `login-state.json` |
| 远程 URL 截图失败/空白 | 网络不可达或仓库 404 | 检查 URL 是否可访问，或手动截图放入 `captures/` 对应目录 |
| Markdown 解析报错 | 格式不符合要求（缺 `##` 章节、表格行数不一致） | 先通过 `--skip-render` 预览解析结果，调整 Markdown 后重试 |
| 片头/片尾不显示 | 子 composition 缺少 `data-composition-id` | 检查 compositions/*.html 的 root 元素 |
| 字幕不同步 | TTS 时长与时间线不匹配 | 删除 `audio/` 重新生成 TTS |
| render 超时 | HyperFrames 等待子 composition timeline | 确保每个 composition 注册 `window.__timelines[id]` |
| 脚本运行崩溃 | `build_*.py` 未捕获异常（如 CSS 格式化失败） | 贴出报错信息，检查 CSS 字符串中的 `%` 是否已转义为 `%%` |
| 字体回退 | 使用了 HyperFrames 未映射的字体 | 改用 Inter/Roboto 等已映射字体，或添加 `@font-face` |

## 交互流程（对话式）

当用户触发视频生成时，AI 在对话中展示选项，用户回复后执行。

### 第一步：确认模式

```
AI: 请选择视频模式：
    1. 新闻简报 (3:4 竖版, 口播) - 逐条配音
    2. 系统演示 (16:9 横版) - 从网页截图生成
    3. 简报模式 (合屏, 15s) - 无配音, BGM, 同类新闻合屏展示
    4. 技术分享 (3:4 竖版) - 调研笔记分章节转口播
    
    回复数字，或直接提供输入文件
```

### 第二步：模式参数澄清

选择系统演示模式后，先澄清目标信息：

```
用户: 2
AI:  系统演示模式需要以下信息：
     1. 目标系统 URL（如 http://localhost:3000）
     2. 需要演示的操作步骤（如：登录→创建项目→提交）
     3. 是否需要登录（是 → 先执行 save_login.py）
     
     请提供 URL 和操作步骤
```

其他模式直接跳到功能选项。

### 第三步：功能选项

```
AI: 请选择功能选项：
     1. 配音 (TTS)    [开]
     2. 字幕          [开]
     3. 背景音乐      [关]
     
     回复数字切换，或说"开始"
```

### 第四步：执行

```
用户: 1, 3
AI:   → 配音: 关, 背景音乐: 开
      请提供 BGM 文件路径，或说"开始"

用户: 开始
AI:   [执行生成命令]
```

**默认配置**：配音✓ 字幕✓ BGM

### 命令行模式（AI 内部调用）

```bash
# 新闻简报（口播）
python scripts/video_generator.py --mode news --md daily-brief.md --tts --subs

# 简报模式（合屏, 无配音, BGM）
python scripts/video_generator.py --mode brief --md daily-brief.md --bgm music.mp3

# 系统演示
python scripts/video_generator.py --mode walkthrough --config steps.json --base-url http://localhost:3000 --tts --subs

# 技术分享
python scripts/video_generator.py --mode tech --md "E:\code\my-ai-workspace\myk\调研笔记\FunASR-语音识别工具包.md" --tts
```

## 系统演示模式前置准备

演示模式需要登录态才能截图私有系统。首次使用：

```bash
# 1. 保存登录态（打开可见浏览器，手动登录）
python scripts/save_login.py --url "http://your-system.com" --storage-state login-state.json

# 2. 使用登录态生成视频
python scripts/video_generator.py --mode walkthrough --config steps.json --base-url http://your-system.com --storage-state login-state.json
```

**检查点 C**：确认 `login-state.json` 已生成（~1-2KB）

## 文件结构

```
video-generator/
── SKILL.md
── scripts/
    ├── video_generator.py        # 统一入口 → 按 --mode 分发到对应 build_*.py
    ├── build_news_video.py       # 口播模式构建器
    ├── build_news_brief.py       # 简报模式构建器（合屏、无配音、BGM）
    ├── build_tech_share.py       # 技术分享模式构建器（表格/代码/GitHub截图混搭）
    ├── build_walkthrough.py      # 演示模式构建器
    ├── save_login.py             # 保存登录态（演示模式前置脚本）
    ├── example-config.json       # 演示模式配置示例
    ├── audio/                    # 运行时：TTS 配音文件（可清理）
    ├── captures/                 # 运行时：截图文件（可清理）
    ├── slides/                   # 运行时：生成的 HTML 卡片（可清理）
    └── compositions/             # HyperFrames 模板
        ├── intro.html            # 片头
        ├── brief.html            # 简报模式合屏模板
        ├── subtitles.html        # 字幕模板
        └── outro.html            # 片尾
```

### 调用关系
```
video_generator.py ──mode news ──────→ build_news_video.py
                  │──mode brief ──────→ build_news_brief.py
                  │──mode tech ───────→ build_tech_share.py
                  └──mode walkthrough → build_walkthrough.py
```

## 依赖

```bash
# 系统依赖
npx hyperframes                     # 视频渲染引擎（需 ≥0.12.0）
ffmpeg                              # 音轨合成
playwright install chromium         # 截图（仅演示/技术分享模式需要）

# Python 依赖（已内置到各脚本中自动安装的运行时依赖）
pip install edge-tts                # TTS 配音
pip install playwright              # 浏览器截图
```

各脚本自带 `parse_markdown()`、`html.escape`、`re` 等标准库能力，无需额外安装。

## 模式对比

| 特性 | 口播模式 | 简报模式 | 技术分享模式 | 演示模式 |
|------|---------|---------|------------|---------|
| 输入 | Markdown | Markdown | 调研 Markdown | JSON + 网页 URL |
| 画面 | HTML 卡片（逐条） | HTML 列表（合屏） | 表格/代码/GitHub截图 | 网页截图 |
| 比例 | 3:4 竖版 | 3:4 竖版 | 3:4 竖版 | 16:9 横版 |
| 配音 | 可选 | 无 | 可选 | 可选 |
| 字幕 | 可选 | 无 | 可选 | 可选 |
| BGM | 可选 | 必选（预设） | 可选 | 可选 |
| 时长 | TTS 决定（~1-3min） | 固定 < 15s | 章节数量决定 | 截图数量决定 |
| 媒体 | 图片+视频混排 | 纯文本 | URL 自动截图 | 网页截图 |

## 新闻模式：三段式布局 + 媒体可选

### 三段式布局

```
┌─────────────────────┐
│  上区：日期 + 分类   │  ← 固定显示
├─────────────────────┤
│  中区：标题 + 摘要   │  ← 动态内容
│         + 媒体      │     (图片/视频/纯文本)
├─────────────────────┤
│  下区：字幕          │  ← 随配音切换
│  来源 + 进度指示器   │
└─────────────────────┘
```

### 媒体可选

**无媒体**（纯文本卡片）：
```markdown
**1. 新闻标题**
> 摘要内容
> [来源名](url)
```

**带图片**：
```markdown
**2. 带图片的新闻**
> 摘要内容
> ![](pic/screenshot.png)
```

**带视频**：
```markdown
**3. 带视频的新闻**
> 摘要内容
> ![](pic/demo.mp4)
```

**媒体语法**：`![](路径)` 支持 mp4/webm/mov（视频）和 png/jpg/gif（图片）。

**行为**：
- 视频自动播放（muted + loop）
- 视频时长 = 实际时长（用 ffprobe 获取）
- 图片时长 = TTS 配音时长
- 无媒体 = 纯文本卡片（标题 + 摘要）

## 简报模式：合屏展示

### 视觉风格
参考「创见AI实验室」视频号风格：
- 深蓝科技渐变背景 + 微网格装饰线
- 每屏一个分类，最多 5 条新闻
- 编号列表格式（01/02/03...），类黄色/紫色分类色编号
- 公司名/模型名青色高亮，数字绿色高亮
- GSAP 淡入淡出过渡（0.4s），列表项逐个入场动画
- 底部圆点进度指示器

### 合屏逻辑
```
解析 Markdown → 按 Markdown 二级标题分屏，同标题下条目合为同屏 → 每屏最多 5 条
                                                               ↓
                                                          超出的另起一屏
                                ↓
                           生成 HTML slide
                           (无截图, 无TTS)
                                ↓
                          HyperFrames 渲染
                                ↓
                           BGM 合成 → final.mp4
```

### 完整时间线示意
```
[AI 与智能化] 3.5s → [遥感、产品与行业动态] 3.5s → 结束
  fadeIn 0.4s               fadeIn 0.4s
  共 7s（< 15s ✅）
```

### 命令行
```bash
# 直接运行
python scripts/build_news_brief.py --md daily-brief.md --bgm music.mp3

# 通过统一入口
python scripts/video_generator.py --mode brief --md daily-brief.md --bgm music.mp3

# 自定义每屏时长
python scripts/build_news_brief.py --md daily-brief.md --bgm music.mp3 --per-slide 4.0

# 仅生成 HTML（不渲染）
python scripts/build_news_brief.py --md daily-brief.md --skip-render
```

### 参数说明
| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--md` | 必填 | Markdown 新闻简报文件 |
| `--bgm` | 无 | 背景音乐文件路径 |
| `--output` | `brief-final.mp4` | 输出 MP4 路径 |
| `--per-slide` | 3.5 | 每屏时长(秒) |
| `--skip-render` | 关 | 只生成 HTML，跳过渲染 |

## 技术分享模式

从调研 Markdown 自动生成技术分享视频，支持表格/代码/GitHub截图混搭。

### 命令行

```bash
# 直接用 `--skip-render` 预览解析效果
python scripts/video_generator.py --mode tech --md research.md --skip-render

# 用指定调研笔记生成技术分享视频
python scripts/video_generator.py --mode tech --md "E:\code\my-ai-workspace\myk\调研笔记\FunASR-语音识别工具包.md" --tts --subs

# 自定义标题和强调色
python scripts/video_generator.py --mode tech --md research.md --brand-title "我的调研" --brand-accent "#10b981"
```

### 参数说明

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--md` | 必填 | 调研 Markdown 文件路径 |
| `--voice` | zh-CN-YunxiNeural | TTS 语音 |
| `--rate` | +30% | TTS 语速 |
| `--output` | tech-share-final.mp4 | 输出 MP4 路径 |
| `--brand-title` | 自动从文档提取 | 自定义视频标题 |
| `--brand-accent` | #6366f1 | 自定义强调色 |
| `--bgm` | 无 | 背景音乐文件路径 |
| `--skip-capture` | 关 | 跳过截图（复用已有） |
| `--skip-tts` | 关 | 跳过 TTS 配音 |
| `--skip-render` | 关 | 只生成 HTML，跳过渲染 |

### 章节解析规则

每个 `##` 章节自动检测内容类型并生成对应幻灯片：

| 章节内容 | 幻灯片类型 | 素材来源 |
|---------|-----------|---------|
| 概述/要点列表 | 要点卡片 | 本地 HTML 截图 |
| 数据表格（`|` 格式） | 表格卡片 | 本地 HTML 截图 |
| 代码块（`` ``` ``） | 代码卡片 | 本地 HTML 截图，含语法高亮 |
| 项目主页 URL（`> 项目地址`） | GitHub 截图 | Playwright 远程截图（超时 30s，失败时跳过不中断） |
| 总结/结论 | 结论卡片 | 本地 HTML 截图 |

### Markdown 格式要求

```markdown
# 项目名称

> 调研日期：2026-06-12
> 项目地址：https://github.com/xxx/xxx

## 项目概述

- 要点1
- 要点2

## 核心能力

| 功能 | 说明 |
|------|------|

## 代码示例

\`\`\`python
from xxx import X
\`\`\`

## 总结
```

- `> 项目地址` 中的 URL 会自动截图作为素材
- 表格会渲染为可视化表格卡片
- 代码块会渲染为暗色代码卡片带简单语法高亮
- 要点列表渲染为编号条目卡片

## 清理

每次运行会生成临时文件到 `scripts/audio/`、`scripts/captures/`、`scripts/slides/`。如需清理旧构建产物：

```bash
# 删除所有运行时生成的文件（保留目录结构）
rm -rf scripts/audio/* scripts/captures/* scripts/slides/*
```

**可安全删除的目录/文件**（仅在 `scripts/` 根目录出现时）：

| 路径 | 来源 | 说明 |
|------|------|------|
| `scripts/audio/` | TTS 配音 | 每次构建重新生成 |
| `scripts/captures/` | Playwright 截图 | 每次构建重新生成 |
| `scripts/slides/` | HTML 卡片 | 每次构建重新生成 |
| `scripts/index.html` | HyperFrames 入口 | 每次构建重新生成 |
