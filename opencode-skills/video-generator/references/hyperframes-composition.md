# HyperFrames 合成规范（改本技能必读）

> 来源：2026-10-16 五模式（news/brief/tech/walkthrough/courseware）逐一出片排查后固化。
> 实证版本：HyperFrames 0.8.164 · Chrome Headless Shell v152。
>
> **改任何 `build_*.py` 的 `build_index_html` / composition 生成之前，先读完本文。**
> 违反下述铁律不会报错，只会产出「只有第一屏有画面」或「片尾空白」的**静默错片**。

---

## 铁律 1 · 禁止用 `gsap onUpdate` 手动切片段显隐

**错误的旧写法**（曾遍布全技能）：
```js
HF_ROOT.eventCallback("onUpdate", function(){
  var t = HF_ROOT.time();
  if (t >= st && t <= ed) { el.style.display="block"; } else { el.style.display="none"; }
});
```
root timeline 无 tween 时时长为 0 → `onUpdate` 只在 t=0 触发一次 → 第一屏 block、其余 `display:none`；之后 seek 不再触发，`display:none` 挂着，框架只强制 `opacity`、顶不开 `display` → **其余片段全空白**。

**正确写法**：只写 `data-start`/`data-duration`，框架自动挂载/卸载。
```html
<img id="slide-2" src="..." data-start="24.4" data-duration="21.5" data-track-index="1"
     style="position:absolute;top:0;left:0;width:1920px;height:1080px;object-fit:cover;z-index:1">
```

## 铁律 2 · 元素不要写内联 `opacity:0`

框架自动挂载带 `data-start/duration` 的元素并强制 `opacity:1`。内联 `opacity:0` 未被顶开时该片段**永远不可见** —— 典型症状：**片尾空白**。

## 铁律 3 · root timeline 只留 sentinel

```js
window.__timelines = window.__timelines || {};
var _tl = gsap.timeline({paused:true});
_tl.set({}, {}, TOTAL_DURATION);   // 唯一作用：把 root 时长撑满
window.__timelines["root"] = _tl;
```

## 子 composition（`data-composition-src`）

| 场景 | 规则 |
|------|------|
| 文件本身 | 根元素**必须**带 `data-composition-id`，否则 0.8.164 拒绝渲染 |
| 静态卡（无 timeline） | 宿主加 `data-no-timeline`，否则空等 45s |
| 有动画 | 自己注册 `window.__timelines["<id>"]` |

> **优先内联**：片头/片尾/章节卡直接用内联元素（`data-start/duration`），比子 composition 更稳、更快，且避免多模式共用同名 `compositions/*.html` 导致**内容串台**。

---

## 坑表

| 症状 | 修法 |
|------|------|
| 只有第一屏有画面 | 删 onUpdate，交框架托管（铁律 1） |
| 片尾空白 | 去掉内联 `opacity:0`（铁律 2） |
| `no element with a data-composition-id` | 子 composition 根元素补该属性 |
| 卡 45s + `sub_timeline_readiness_timeout` | 静态 composition 宿主加 `data-no-timeline` |
| 卡在 `Checking browser` | 首次要下载 Chrome Headless Shell（114MB），勿中断 |
| 片头显示别的模式内容 | 停止共用 `compositions/intro.html`，改内联 |
| Playwright「Executable doesn't exist」 | 用 `_launch_browser`（自带chromium→系统Chrome→Edge） |
| `networkidle` 超时 | 改 `wait_until="load"` |
| TTS 403 | `pip install -U edge-tts` |

## 出片 ≠ 完成：必须抽帧验空

按脚本打印的时间线，在各片段**中段**抽帧，用 PIL 判纯色：
```python
from PIL import Image, ImageChops
im = Image.open("frame.png").convert("RGB")
blank = all(lo == hi for lo, hi in im.getextrema())        # True = 疑似空白
same  = ImageChops.difference(a, b).getbbox() is None       # True = 两帧相同
```
判据：**每帧非空白** 且 **相邻帧互异**。纯色帧 RGB 等于背景色即为「片段没显示」。

## 共享助手（勿重复造）

`build_tech_share.py` 的 `_launch_browser`（浏览器回退）与 `get_audio_duration` 为全技能共享，其余 `build_*.py` 从此导入。
