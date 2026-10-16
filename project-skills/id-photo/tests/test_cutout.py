import os
import sys

from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import cutout


def make_img():
    im = Image.new("RGB", (100, 100), "white")
    for x in range(30, 70):
        for y in range(30, 70):
            im.putpixel((x, y), (200, 0, 0))
    return im


def test_detect_bg_is_white():
    bg = cutout.detect_bg_color(make_img())
    assert all(c > 240 for c in bg)


def test_bg_is_uniform():
    assert cutout.is_bg_uniform(make_img()) is True


def test_replace_bg_blue():
    out = cutout.replace_bg(make_img(), (67, 142, 219))
    assert out.getpixel((0, 0)) == (67, 142, 219)
    assert out.getpixel((50, 50)) == (200, 0, 0)


def test_cutout_auto_returns_rgb():
    out = cutout.cutout_auto(make_img(), (67, 142, 219))
    assert out.mode == "RGB"
    assert out.size == (100, 100)


def test_has_rembg_is_bool():
    assert isinstance(cutout.has_rembg(), bool)
