---
name: id-photo
description: 证件照工厂。给一张端正人像，说出证件类型（一寸/二寸/小二寸/护照/各类签证/报名照），自动按官方规格裁切、可换底色（白/蓝/红）、输出电子版并排版到 5寸/6寸相纸。当用户提到"证件照""一寸/二寸/小二寸""护照照片""签证照片""换底色""排相纸"时使用。
---

# id-photo 证件照工厂

给一张端正人像，说出证件类型，输出**合规规格的电子版 + 可打印相纸排版**。

## 能力

- 按规格精确裁切、缩放（px 与 dpi 精确匹配）
- 换底色：白 / 蓝 / 红（默认零依赖色差法；装了 rembg 自动升级为 AI 抠图）
- 5寸 / 6寸相纸自动排版（自动算最优张数）

## 用法

```bash
python .opencode/skills/id-photo/scripts/make_idphoto.py --src <源图路径> --spec <规格> [--bg white|blue|red] [--out <目录>]
```

- `--spec`：规格 id 或别名，如 `xiaotwo` 或 `小二寸`
- `--bg`：不填 = 保留原底色
- `--sheets`：默认 `5inch,6inch`

常见请求 → 规格：`美签`→`meiqian`、`小二寸`→`xiaotwo`、`护照`→`huzhao`、`一寸`→`yicun`。不确定就跑 `scripts/specs.py` 列出全部。

## 查询规格

```bash
python .opencode/skills/id-photo/scripts/specs.py
```

## 规格库

`specs/photo-specs.json` 为唯一权威来源，含国内证件、8 国签证、报名类共 23 条。`variable: true` 的规格因省份/领馆而异，使用前需向用户确认。

## 构图说明

采用「非背景包围盒 + 经验规则」（头顶留白约 8%、水平居中）。对标准证件照原图有效；生活照等非标准图需人工确认。

## 换底色说明

- **色差法**（默认）：仅替换「与图像边缘连通」的近似背景色区域，避免脸部高光被误判为背景；要求背景相对干净
- **rembg**（可选，需独立环境）：rembg 依赖 numpy 2.x，与含 numpy<2 的 conda 环境冲突（本机 base 即为该情况），import 会挂起；如需使用请建独立 venv。未安装时自动回退色差法。

## 故障处理

| 情况 | 处理 |
|------|------|
| 源图路径不存在 | 提示用户核对路径；不要静默失败 |
| `--spec` 报 KeyError | 运行 `python .opencode/skills/id-photo/scripts/specs.py` 列出全部规格，让用户选择 |
| 规格 `variable: true` | 🔴 先向用户确认省份/领馆的具体要求（px、底色、文件大小），确认后再生成 |
| 源图非标准证件照（生活照/侧脸/遮挡/多人） | 🔴 停止自动裁切，请用户先提供端正人像原图 |
| 换底色后边缘发毛或背景有残留 | 色差法仅适用纯色背景；请用户换纯色背景原图，或在独立 venv 装 rembg 后重试 |
| `import rembg` 长时间无响应 | 本机 conda base 与 rembg 冲突（numpy<2）；脚本已用子进程 + 8s 超时探测自动回退色差法，无需干预 |
| 输出比例与预期不符 | 裁切按 `px` 比例、dpi 按规格写入；检查规格 `px` 字段是否正确 |

## 不要做

- ❌ 不要假设所有规格都是 300dpi（身份证 350dpi、申根 400dpi，一律以规格库为准）
- ❌ 不要在 conda base 等含 numpy<2 的环境里 `pip install rembg`（版本冲突，import 会挂起）
- ❌ 不要对非标准照片（生活照、侧脸、遮挡、多人）直接自动裁切
- ❌ 不要用 `mm` 比例裁切——用 `px` 比例（个别规格 mm 与 px 比例不一致）
- ❌ 不要对 `variable: true` 的规格自行假设参数——必须向用户确认
- ❌ 不要为「好看」改动输出 px/dpi——必须精确匹配规格

## 测试

```bash
python -m pytest .opencode/skills/id-photo/tests/ -v
```
