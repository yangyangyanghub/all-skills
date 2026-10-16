import numpy as np
from PIL import Image


def find_subject_bbox(img, tol=30):
    arr = np.asarray(img.convert("RGB")).astype(np.int32)
    # 用顶部两角估计背景色，再按颜色距离判定前景（适配非白/彩色背景）
    c = 10
    corners = np.concatenate([arr[:c, :c].reshape(-1, 3), arr[:c, -c:].reshape(-1, 3)], axis=0)
    bg = corners.mean(axis=0)
    dist = np.sqrt(((arr - bg) ** 2).sum(axis=2))
    ys, xs = np.where(dist > tol)
    if len(xs) == 0:
        return (0, 0, img.width - 1, img.height - 1)
    return (int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max()))


def crop_to_ratio(img, ratio, head_margin=0.08):
    rw, rh = ratio
    W, H = img.size
    x0, y0, x1, _y1 = find_subject_bbox(img)
    cx = (x0 + x1) / 2
    target = rw / rh

    crop_w = W
    crop_h = crop_w / target
    if crop_h > H:
        crop_h = H
        crop_w = crop_h * target

    top = y0 - head_margin * crop_h
    top = max(0, min(top, H - crop_h))
    left = cx - crop_w / 2
    left = max(0, min(left, W - crop_w))

    return img.crop((round(left), round(top), round(left + crop_w), round(top + crop_h)))


def resize_to_spec(img, px):
    return img.resize((int(px[0]), int(px[1])), Image.LANCZOS)
