import os
import sys

from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import layout_sheet


def test_plan_grid_5inch_xiaotwo():
    assert layout_sheet.plan_grid((1050, 1500), (413, 531)) == (2, 2)


def test_make_sheet_5inch_size():
    photo = Image.new("RGB", (413, 531), "white")
    assert layout_sheet.make_sheet(photo, "5inch").size == (1050, 1500)


def test_make_sheet_6inch_size():
    photo = Image.new("RGB", (413, 531), "white")
    assert layout_sheet.make_sheet(photo, "6inch").size == (1500, 1800)
