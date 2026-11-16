---
name: youtube-transcript
description: 取用 YouTube 视频与同类网页的长内容正文（字幕/逐字稿 transcript），用于总结、解读、翻译、观点提炼、对比分析。当用户给 youtube.com/watch 或 youtu.be 链接并要求"解读/总结/讲了什么/观点是什么/翻译这个视频"，或给 YC Library、a16z、播客节目页要求提炼内容，或说"把字幕拿下来""转写这个视频""这个视频能分析吗"时使用。不要因为手里没有直接的字幕工具就放弃或只凭标题猜测——本技能给出四层降级路径，多数情况下能拿到完整正文。不适用：B 站、小红书、抖音等需要登录态或专用接口的平台，以及纯音乐/MV。
---

# YouTube 与长视频内容取用

目标：把视频内容变成可引用的文字，且能说清"这段文字从哪来、有多少、可不可靠"。

绝大多数失败不是"拿不到"，而是**拿了一半就当全文**，或者**拿不到字幕就凭标题写总结**。这个技能的核心是四层降级 + 一个覆盖率自检。

文中的 `python` 指系统 Python 3 解释器（Windows 上通常就是 `python`，macOS/Linux 可能是 `python3`）。两个脚本只依赖标准库，不需要安装任何第三方包。

## 先判断来源类型

| 来源特征 | 走哪条路径 | 典型代表 |
|---|---|---|
| 视频页，有 `youtube.com/watch?v=` 或 `youtu.be/` | 路径 B 优先，C 兜底 | YouTube |
| 文章/课程/播客页，正文由 JS 渲染但页面源码里带内嵌 JSON | 路径 A | YC Library、部分播客站 |
| 页面源码里搜不到 transcript，也没有视频流 | 路径 A 反查，找不到就告知用户 | 付费墙、登录墙 |
| 上面都失败，但有音视频流 | 路径 D | 兜底 |

判断方法：先 `curl -sL` 抓一次页面，看返回里有没有 `transcript`、`captionTracks`、`&quot;transcript&quot;` 这类字段。有就是路径 A 的候选。没有就按路径 B 处理。

## 路径 A：从页面内嵌数据提取（最快）

适用：页面用服务端渲染或注入了完整 props，正文藏在 HTML 里的 JSON 字符串中。

```bash
# 1. 抓页面（带 UA，很多站对默认 curl UA 返回精简页）
curl -sL -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36" \
  "<URL>" -o page.html

# 2. 用脚本提取并还原转义
python scripts/extract_embedded.py page.html -o transcript.txt
```

`extract_embedded.py` 会自动找 `transcript` / `caption` / `subtitles` / `content` 这几类字段，做 HTML 实体解码（`&quot;` `&#39;` `&amp;` `&lt;` `&gt;`）和 `\n` 还原，输出纯文本。

**为什么先试这条**：一次请求就有全文，不用装依赖、不触发限流。YC Library 的完整逐字稿就是这样拿到的（一篇 3.8 万到 5.2 万字符不等），而直接对这类页面做正文抽取只能拿到标题。

**注意**：如果提取结果只有标题或摘要，说明正文在客户端异步加载，直接转路径 B/C，不要在这条路上反复试正则。

## 路径 B：yt-dlp 拉字幕（YouTube 标准路径）

```bash
# 1. 先看有哪些字幕轨道，不要盲下
uvx yt-dlp --skip-download --list-subs --no-warnings "<URL>"

# 2. 有 en 就下 en（原文最准，避免中译二次失真）
uvx yt-dlp --skip-download --write-auto-subs --sub-langs "en" --sub-format "vtt" \
  -o "out/%(id)s.%(ext)s" "<URL>"

# 3. 转成带时间戳的纯文本
python scripts/subtitle_to_text.py out/*.en.vtt -o transcript.txt
```

优先选原文语言：自动字幕的翻译版是机器二次转译，人名和术语更容易错，做观点提炼时偏差会放大。

### 这条路径常见的四种失败

| 现象 | 含义 | 处理 |
|---|---|---|
| `HTTP Error 429: Too Many Requests` | 字幕端点被限流，换 client 参数通常无效 | 别重试超过 2 次，直接转 C |
| `No supported JavaScript runtime could be found` | 只是警告，字幕仍可下载 | 忽略 |
| `The page needs to be reloaded` | 该 player client 失效 | 换 `--extractor-args "youtube:player_client=android"` 试一次 |
| 下载成功但文件为空 | 极少见，多为权限或地区限制 | 转 C |

## 路径 C：浏览器转写面板（429 时的主力）

这是今天实测最可靠的一条：YouTube 播放器自己会加载字幕，而页面的"转写文稿"面板里有全量分段文本。走浏览器相当于借用播放器已经拿到的数据，绕开独立字幕接口的限流。

用 chrome-devtools MCP：

1. `new_page` 打开 `https://www.youtube.com/watch?v=<ID>`
2. `take_snapshot` 先确认页面加载完（看得到标题、时长、章节）
3. 点开描述区的"更多"，再点"内容转文字"（或"转写文稿"tab）。如果 `take_snapshot` 返回的 uid 里已经有 `tab "转写文稿"` 且为 selected，说明面板已经打开，跳过这一步
4. `take_snapshot` 时**指定 `filePath` 存到临时文件**，不要直接回传。完整快照动辄几万 token，直接输出会挤掉后续分析所需的空间
5. 用脚本从快照里抽字幕：

```bash
python scripts/subtitle_to_text.py snap.txt --from-snapshot -o transcript.txt
```

6. 核对覆盖率：首段时间应接近 0，末段时间应接近视频总时长。中间时间戳不应出现大跳跃。

### 细节坑

- 面板里的分段是 `button "<时间> <正文>"` 结构，章节标题也长这样（`第 1 章：Intro`），脚本按"以时间开头"过滤掉章节。
- 面板可能是虚拟滚动。如果抽出来的段数明显少于预期（比如 50 分钟视频少于 300 段），先在容器内滚到底再重新取快照。
- 不要依赖页面内的 `youtubei/v1/get_transcript` 接口：`getTranscriptEndpoint.params` 与当前 client context 绑定，直接复用常返回 `400 Precondition check failed`。
- `api/timedtext` 可能返回 200 但 `content-length: 0`。这是正常现象（分段协议），不代表字幕不存在，不要据此判断"没有字幕"。

## 路径 D：音频转写（最后兜底）

只有在 A/B/C 全失败时才用。代价是下载体积和转写时间。

```bash
# 只下音轨
uvx yt-dlp -f "bestaudio/best" --extract-audio --audio-format mp3 --audio-quality 5 \
  -o "out/audio.%(ext)s" "<URL>"
```

然后用本地或云端 ASR 转写。注意：本机若无现成 ASR 环境，安装即意味着数 GB 依赖，属于需要先跟用户确认的动作，不要默认执行。

## 输出规范

拿到正文后，交付时至少包含三样：

1. **正文**（带时间戳，便于回头核对原片位置）
2. **来源与规模**：平台、标题、时长、段落数、覆盖时间区间
3. **可靠性标注**：官方字幕 / 自动字幕 / 人工转写，以及已知识别错误

自动字幕一定有专名错误。今天的实例：CFO 名字被识别成 `Pier Milwani`（实为 Praveer Melwani）、`Navan` 被识别成 `Non`、`Codex` 写成 `codeex`。所以：

- 引用人名、公司名、产品名前，先用上下文交叉验证
- 数字类结论（比例、金额、人数）不要直接对外引用，标注"以原片为准"
- 在交付物里写一句"字幕为自动生成，专名可能有误"，比事后被指出要好

## 自检清单

交付前过一遍：

- [ ] 首段接近 0:00，末段接近视频时长（覆盖完整）
- [ ] 段落数是否合理（大致每 5-10 秒一段）
- [ ] 中间无超过 2 分钟的空洞
- [ ] 已标注字幕类型与专名风险
- [ ] 没有把"演示跑通"写成"内容已验证"（拿到的是文本，不是我的理解）

## 与其他技能的分工

- 要**深度调研一个主题**（多源、要结论）：用 `deep-research`
- 只是**把一条视频变成可读文本**：本技能
- 要**转成中文长文**：拿到正文后用 `space-intel-writer` 或 `khazix-writer`
- 网页正文抽取（非视频）：优先 `defuddle`

## 参考

- 命令全集与错误码：`references/yt-dlp-recipes.md`
- 浏览器面板操作细则：`references/browser-panel.md`
