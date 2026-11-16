# yt-dlp 命令与错误处理

不要求全局安装。用 `uvx` 临时运行，避免污染系统环境：

```bash
uvx yt-dlp --version
```

首次运行会下载几 MB 的包，之后有缓存。

## 列出可用字幕

先看清楚有哪些轨道，不要盲下：

```bash
uvx yt-dlp --skip-download --list-subs --no-warnings "<URL>"
```

输出里会分两块：`Available subtitles`（人工）和 `Available automatic captions`（自动）。人工字幕通常只有少数语言，自动字幕几乎覆盖所有语言。

**选择顺序**：人工 > 自动原文 > 自动译文。自动译文是二次机器翻译，人名和术语失真最严重。

## 下载字幕

```bash
# 只要英文字幕，vtt 格式
uvx yt-dlp --skip-download --write-auto-subs --sub-langs "en" \
  --sub-format "vtt" -o "out/%(id)s.%(ext)s" "<URL>"

# 同时要英文和简体中文
uvx yt-dlp --skip-download --write-auto-subs --sub-langs "en,zh-Hans" \
  --sub-format "vtt" -o "out/%(id)s.%(ext)s" "<URL>"

# json3 格式，结构化更好解析（但更易触发 429）
uvx yt-dlp --skip-download --write-auto-subs --sub-langs "en" \
  --sub-format "json3" -o "out/%(id)s.%(ext)s" "<URL>"
```

## 下载音轨（兜底路径用）

```bash
uvx yt-dlp -f "bestaudio/best" --extract-audio --audio-format mp3 \
  --audio-quality 5 -o "out/audio.%(ext)s" "<URL>"
```

50 分钟视频约 33 MB mp3。相比字幕，音频端点限流概率低很多——实测同一条视频字幕 429 时，音频仍能正常下载。

## 常见输出与错误

| 输出 | 含义 | 处理 |
|---|---|---|
| `WARNING: No supported JavaScript runtime could be found` | 仅警告，字幕仍可下 | 忽略 |
| `WARNING: ... impersonation ... no impersonate target` | 仅警告 | 忽略 |
| `ERROR: Unable to download video subtitles ... HTTP Error 429` | 字幕端点限流 | 重试最多 2 次，然后转浏览器路径 |
| `ERROR: The page needs to be reloaded` | 该 player client 失效 | 换 client 试一次 |
| `ERROR: Video unavailable` | 删除、私享或地区限制 | 告知用户，不猜测内容 |
| 下载成功但文件 0 字节 | 权限或地区问题 | 转浏览器路径 |
| `Some android client https formats have been skipped` | SABR 实验导致部分格式缺失 | 字幕不受影响 |

## 换 player client

```bash
uvx yt-dlp --skip-download --write-auto-subs --sub-langs "en" --sub-format "vtt" \
  --extractor-args "youtube:player_client=android" -o "out/%(id)s.%(ext)s" "<URL>"
```

可选值：`web`、`web_safari`、`android`、`ios`、`tv`、`mweb`。不同 client 命中的接口不同，429 时换一个有机会成功，但实测多数情况下无效——**这一步的价值在于排查，不是主力手段**。

## 限流后的正确姿势

不要在同一个短窗口内连续重试。实测连续三次不同 client 全部 429，而音频下载不受影响。这说明限流针对的是字幕端点而非账号。

正确顺序：

1. 第一次 429 → 等 10 到 15 秒重试一次
2. 仍 429 → 立刻转浏览器转写面板（成功率最高）
3. 不要在这条路上耗超过 1 分钟

## 其他有用的参数

| 参数 | 用途 |
|---|---|
| `--sleep-subtitles 3` | 每个字幕请求间隔 3 秒，降低限流概率（对已限流无效） |
| `--no-warnings` | 减少输出噪音，配合 `--list-subs` 好用 |
| `--print "%(title)s / %(duration_string)s"` | 只要元信息，不下载 |
| `-J` | 输出完整 JSON 元数据，含字幕 URL 列表 |
| `--cookies-from-browser chrome` | 需登录的视频（极少必要，且涉及凭据，用前先确认） |
