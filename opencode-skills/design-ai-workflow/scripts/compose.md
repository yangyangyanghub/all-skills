# 生成后合成：只取重绘图的局部，其余保留原图像素

结构保真的唯一硬办法。mask 外的区域一个像素都不动。

## 用法

```powershell
python compose.py --base 原图.png --edit 重绘.png --mask mask.png --out 交付.png [--feather 2]
```

- `--base`：原始底图（结构依据）
- `--edit`：AI 重绘结果（必须与 base 同尺寸）
- `--mask`：白色=使用 edit，黑色=保留 base；灰度按灰度值线性混合
- `--feather`：mask 边缘羽化像素数，默认 2，接缝明显时加到 4~6
- `--dump-mask`：把处理后的 mask 另存，便于复查

## mask 怎么来

见 `references/zoning-mask.md`：
- 手绘纯红涂鸦 → `mask_from_zoning.py`
- 或 CAD 闭合区域导出填充

## 输出

- `--out` 指定路径的合成图（PNG，无损）
- 标准输出打印实际替换像素占比，用于核对

## 限制

- base 与 edit 尺寸必须一致；不一致直接报错，不自动缩放（缩放会破坏结构保真）
- 不做透视对齐；edit 的透视必须与 base 一致（用同一底图作 ref 出图即可）
- 不做色调匹配；色差明显时先统一 edit 的白平衡再合成
