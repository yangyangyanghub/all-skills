import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage


def detect_bg_color(img, corner=10):
    arr = np.asarray(img.convert("RGB"))
    h, w, _ = arr.shape
    # 只采样顶部与上半侧边，避开底部（人像衣服常占据底角）
    patches = [
        arr[:corner, :corner],
        arr[:corner, -corner:],
        arr[:corner, :],
        arr[: h // 2, :corner],
        arr[: h // 2, -corner:],
    ]
    px = np.concatenate([p.reshape(-1, 3) for p in patches], axis=0)
    return tuple(int(v) for v in px.mean(axis=0))


def is_bg_uniform(img, thresh=12):
    arr = np.asarray(img.convert("RGB"))
    h, w, _ = arr.shape
    c = 10
    patches = [
        arr[:c, :c],
        arr[:c, -c:],
        arr[:c, :],
        arr[: h // 2, :c],
        arr[: h // 2, -c:],
    ]
    px = np.concatenate([p.reshape(-1, 3) for p in patches], axis=0)
    return float(px.std(axis=0).mean()) < thresh


def cutout_alpha(img, bg_color, tol=40, feather=1):
    arr = np.asarray(img.convert("RGB")).astype(np.int32)
    bg = np.array(bg_color, dtype=np.int32)
    dist = np.sqrt(((arr - bg) ** 2).sum(axis=2))

    # 仅把「与图像边缘连通」的近似背景色区域判为背景，
    # 避免脸部高光等内部浅色区域被误判成背景。
    candidate = dist < tol
    labeled, n = ndimage.label(candidate)
    if n > 0:
        border = np.zeros(n + 1, dtype=bool)
        border[labeled[0, :]] = True
        border[labeled[-1, :]] = True
        border[labeled[:, 0]] = True
        border[labeled[:, -1]] = True
        border[0] = False
        bg_mask = border[labeled]
    else:
        bg_mask = np.zeros(arr.shape[:2], dtype=bool)

    alpha = np.full(arr.shape[:2], 255, dtype=np.uint8)
    alpha[bg_mask] = 0
    alpha_img = Image.fromarray(alpha, "L")
    if feather:
        alpha_img = alpha_img.filter(ImageFilter.GaussianBlur(feather))
    rgba = img.convert("RGBA")
    rgba.putalpha(alpha_img)
    return rgba


def replace_bg(img, color):
    bg = detect_bg_color(img)
    rgba = cutout_alpha(img, bg)
    base = Image.new("RGB", img.size, tuple(color))
    base.paste(rgba, (0, 0), rgba)
    return base


def has_rembg(timeout=8):
    import subprocess
    import sys
    # 用子进程探测，避免 import rembg 在本机环境挂起阻塞整个脚本
    try:
        r = subprocess.run(
            [sys.executable, "-c", "import rembg"],
            timeout=timeout, capture_output=True,
        )
        return r.returncode == 0
    except Exception:
        return False


def cutout_auto(img, target_color):
    # 背景均匀 → 色差法（快、零依赖）；背景杂乱 → 交给 rembg（若可用）
    if not is_bg_uniform(img) and has_rembg():
        from rembg import remove
        rgba = remove(img.convert("RGB")).convert("RGBA")
        base = Image.new("RGB", img.size, tuple(target_color))
        base.paste(rgba, (0, 0), rgba)
        return base
    return replace_bg(img, target_color)
