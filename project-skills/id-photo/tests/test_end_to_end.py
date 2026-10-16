import os
import sys

from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import make_idphoto


def make_src(path):
    im = Image.new("RGB", (295, 413), "white")
    for x in range(100, 195):
        for y in range(50, 360):
            im.putpixel((x, y), (180, 60, 60))
    im.save(path)


def test_make_idphoto_outputs(tmp_path):
    src = str(tmp_path / "src.jpg")
    make_src(src)
    out_dir = str(tmp_path / "out")
    result = make_idphoto.make_idphoto(src, "xiaotwo", out_dir, sheets=("5inch", "6inch"))

    assert os.path.exists(result["single"])
    assert Image.open(result["single"]).size == (413, 531)
    assert Image.open(result["sheet_5inch"]).size == (1050, 1500)
    assert Image.open(result["sheet_6inch"]).size == (1500, 1800)
