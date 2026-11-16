# 浏览器转写面板操作细则

字幕接口 429 时，这条路成功率最高。原理：播放器本身会加载字幕，页面的"转写文稿"面板里有全量分段文本，走浏览器等于借用播放器已经拿到的数据。

## 前置

需要 chrome-devtools MCP（提供 `new_page`、`take_snapshot`、`click`、`evaluate_script` 等工具）。

## 完整步骤

### 1. 打开页面

```
new_page("https://www.youtube.com/watch?v=<ID>")
```

### 2. 确认加载完成

```
take_snapshot(pageId)
```

看到标题、时长、章节列表，说明页面已经渲染完。此时留意两处：

- 视频时长（例如"50 分钟 11 秒"），后面用来核对覆盖率
- 描述区是否有"更多"按钮

### 3. 展开描述

点击描述区的"更多"。展开后会出现"内容转文字"按钮，或者直接出现"转写文稿"tab。

**判断是否已经打开**：下一次 `take_snapshot` 里如果出现 `tab "转写文稿" selectable selected`，说明面板已经就位，不需要再点。

### 4. 打开转写面板

优先用真实点击（`click` 传 uid）。如果 uid 拿不到，可以用 `evaluate_script` 找按钮并 `.click()`：

```javascript
() => {
  const btns = [...document.querySelectorAll('button, tp-yt-paper-button')];
  const hit = btns.find(b => /转写文稿|内容转文字|Show transcript/.test(b.innerText || ''));
  if (!hit) return { ok: false };
  hit.click();
  return { ok: true, clicked: hit.innerText.trim() };
}
```

### 5. 快照落盘，不要回传

```
take_snapshot(pageId, filePath = "snap.txt")
```

**这一步很关键**。完整快照动辄几万 token，直接回传会挤掉后续分析的空间。存文件后只读需要的部分，或者直接交给脚本处理。

### 6. 提取

```bash
python scripts/subtitle_to_text.py snap.txt --from-snapshot -o transcript.txt
```

输出会打印段落数、字符数、时间范围。用这三个数核对完整性。

## 判断完整性

| 指标 | 合理范围 | 异常时 |
|---|---|---|
| 首段时间 | 0:00 附近 | 从中间开始说明上半段没渲染 |
| 末段时间 | 与视频时长接近 | 差几分钟说明尾部缺失 |
| 段落数 | 大致每 5 到 10 秒一段（50 分钟约 300 到 600 段） | 明显偏少是虚拟滚动 |
| 中间空洞 | 无超过 2 分钟的跳跃 | 有则重新滚一遍 |

## 虚拟滚动处理

如果段落数明显偏少，面板可能只渲染了可视区域。在容器内滚动到底，再重新取快照：

```javascript
async () => {
  const list = document.querySelector('#segments-container')
    || document.querySelector('ytd-transcript-segment-list-renderer');
  if (!list) return { err: 'no container' };
  for (let i = 0; i < 40; i++) {
    list.scrollTop = list.scrollHeight;
    await new Promise(r => setTimeout(r, 250));
  }
  return { ok: true, height: list.scrollHeight };
}
```

滚动完成后重新 `take_snapshot` 到文件，再跑脚本。

## 快照里的结构

转写面板的每一段是：

```
uid=3_77 button "0秒钟 I think we're going to be able to attract and build the world's best finance organization"
uid=3_78 button "7秒钟 and surrounded by people that want to go and become the best at their craft."
uid=3_79 button "第 1 章：Intro"
```

三种行要区分：

- `0秒钟` / `1分钟2秒钟` — 中文界面时间
- `1:29` / `1:02:03` — 英文界面时间
- `第 1 章：xxx` — 章节标题，没有时间前缀，会被脚本自动跳过

脚本对两种时间格式都做了处理。

## 不要走的三条路

| 做法 | 失败原因 |
|---|---|
| 在页面内 fetch `api/timedtext?...` | 常返回 200 但 `content-length: 0`，因为分段协议需要额外参数 |
| 在页面内 POST `youtubei/v1/get_transcript` | `getTranscriptEndpoint.params` 与 client context 绑定，复用常报 `400 Precondition check failed` |
| 直接 curl 页面找 `captionTracks` | 页面经过签名和混淆，拿到的 URL 多半已被判失效 |

这些路径的失败不代表"没有字幕"，只代表接口被限制。转写面板是绕开限制的最短路径。

## 收尾

用完关掉页面：

```
close_page(pageId)
```

如果只是临时打开，关掉能减少浏览器内存占用，也避免下次 `list_pages` 里堆一堆残留标签。
