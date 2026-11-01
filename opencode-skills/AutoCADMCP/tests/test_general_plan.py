"""通用图种完整路径和错误拦截回归，不连接 CAD。"""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

from PIL import Image

SKILL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL / "scripts"))
from plan_to_shorthand import convert_plan_to_shorthand
from render_general_plan_preview import render_preview
from render_interior_plan_preview import render_preview as render_interior
from validate_plan import sha256_file, validate_plan_file


class GeneralPlanTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "plan.json"
        self.preview = Path(self.tmp.name) / "preview.png"
        geometries = [
            {"kind": "rect", "rect": [-500, 0, 500, 800]},
            {"kind": "line", "p0": [-500, 400], "p1": [500, 400]},
            {"kind": "polyline", "points": [[-500, 800], [0, 1100], [500, 800]], "closed": False},
            {"kind": "circle", "center": [0, 600], "radius": 100},
            {"kind": "arc", "center": [800, 600], "radius": 100, "angle0": 300, "angle1": 60},
            {"kind": "text", "point": [-500, -200], "height": 80, "text": "立面示意"},
        ]
        self.plan = {"meta": {"drawing_type": "elevation", "units": "mm", "reference_required": False},
                     "entities": [dict(g, id=str(i), layer="A-TEST", confidence="explicit", source="测试尺寸") for i, g in enumerate(geometries)]}

    def write(self, plan=None):
        self.path.write_text(json.dumps(self.plan if plan is None else plan, ensure_ascii=False), encoding="utf-8")

    def test_non_interior_types_complete_without_room_fields(self):
        for kind in ("elevation", "section", "detail", "general", "mechanical"):
            with self.subTest(kind=kind):
                self.plan["meta"]["drawing_type"] = kind
                self.write()
                report = validate_plan_file(self.path)
                self.assertEqual(report["status"], "ok", report)
                self.assertTrue(report["warnings"])
                lines = convert_plan_to_shorthand(self.path).splitlines()
                self.assertEqual([line.split("|")[0] for line in lines], ["rect", "line", "polyline", "circle", "arc", "text"])
                self.assertIn("arc|800,600|100|300|60|white|A-TEST", lines)
                result = render_preview(self.path, self.preview, 900, 700)
                manifest = json.loads(Path(result["manifest"]).read_text(encoding="utf-8"))
                self.assertEqual(manifest["drawing_type"], kind)
                self.assertEqual(manifest["entity_count"], len(lines))
                self.assertEqual(manifest["plan_sha256"], sha256_file(self.path))
                self.assertEqual(manifest["preview_sha256"], sha256_file(self.preview))
                self.assertLess(manifest["bounds_mm"][0], 0)
                with Image.open(self.preview) as image:
                    self.assertEqual(image.size, (900, 700))
                    self.assertLess(image.convert("L").getextrema()[0], 100)

    def test_bad_entities_block_validation_render_and_conversion(self):
        changes = [{"kind": "spline"}, {"radius": -1, "kind": "circle"},
                   {"p0": [float("nan"), 0]}, {"p0": [0, 0, 20]},
                   {"p1": [-500, 400]}, {"rotation": 45}, {"id": "0"},
                   {"layer": "bad|layer"}]
        for change in changes:
            with self.subTest(change=change):
                plan = copy.deepcopy(self.plan)
                plan["entities"][1].update(change)
                self.write(plan)
                self.assertEqual(validate_plan_file(self.path)["status"], "failed")
                with self.assertRaises(ValueError):
                    render_preview(self.path, self.preview)
                with self.assertRaises(ValueError):
                    convert_plan_to_shorthand(self.path)
                self.assertFalse(self.preview.exists())

    def test_invalid_structure_and_mixed_semantics_fail(self):
        for change in ({"meta": []}, {"entities": [None]}, {"entities": []},
                       {"walls": [{"rect": [0, 0, 5, 5]}]},
                       {"meta": {"drawing_type": [], "units": "mm"}}):
            with self.subTest(change=change):
                self.write(dict(self.plan, **change))
                self.assertEqual(validate_plan_file(self.path)["status"], "failed")

    def test_interior_example_and_renderer_routing(self):
        example = SKILL / "assets" / "example_plan.json"
        self.assertEqual(validate_plan_file(example)["status"], "ok")
        self.assertTrue(convert_plan_to_shorthand(example))
        render_interior(example, self.preview)
        with self.assertRaises(ValueError):
            render_preview(example, self.preview)
        self.write()
        with self.assertRaises(ValueError):
            render_interior(self.path, self.preview)


if __name__ == "__main__":
    unittest.main()
