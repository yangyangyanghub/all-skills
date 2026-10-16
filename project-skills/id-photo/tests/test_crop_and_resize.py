import os
import sys

from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import crop_and_resize as cr


def make_img():
    im = Image.new("RGB", (300, 400), "white")
    for x in range(100, 200):
        for y in range(50, 300):
            im.putpixel((x, y), (200, 0, 0))
    return im


def test_find_subject_bbox():
    assert cr.find_subject_bbox(make_img()) == (100, 50, 199, 299)


def test_crop_to_ratio_has_target_ratio():
    out = cr.crop_to_ratio(make_img(), (35, 45))
    w, h = out.size
    assert abs(w / h - 35 / 45) < 0.01


def test_resize_to_spec_exact():
    out = cr.resize_to_spec(make_img(), (413, 531))
    assert out.size == (413, 531)
