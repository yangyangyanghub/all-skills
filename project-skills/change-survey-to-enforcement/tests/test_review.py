# 审核意见输出测试
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "scripts"))

from review import render_one, render_summary  # noqa: E402

SAMPLE = {
  "id": "130208SJBG26210951",
  "expected": {"top": "农村道路", "category": "", "ruleId": "FARMLAND_ROAD"},
  "filled": {"top": "农村道路", "category": "", "detail": ""},
  "consistent": True,
  "evidence": {"required": ["能证明宽度≤8米的带方位角现场照片"],
               "have": ["带方位角现场照片"], "missing": []},
  "suspicious": False,
  "basis": "规则 FARMLAND_ROAD（农村道路）：依据字段判定为「农村道路」",
}

MISMATCH = dict(SAMPLE, consistent=False,
                filled={"top": "合法", "category": "", "detail": ""},
                expected={"top": "非农违法", "category": "", "ruleId": "ILLEGAL_FALLBACK"})


def test_render_one_contains_id():
  assert "130208SJBG26210951" in render_one(SAMPLE)


def test_render_one_marks_consistent():
  out = render_one(SAMPLE)
  assert "一致" in out


def test_render_one_marks_mismatch():
  out = render_one(MISMATCH)
  assert "不一致" in out


def test_render_one_lists_missing_evidence():
  r = dict(SAMPLE, evidence={"required": ["A", "B"], "have": [], "missing": ["A", "B"]})
  out = render_one(r)
  assert "A" in out and "B" in out


def test_render_summary_counts():
  out = render_summary([SAMPLE, MISMATCH])
  assert "2" in out
  assert "1" in out


if __name__ == "__main__":
  for name, fn in sorted(globals().items()):
    if name.startswith("test_") and callable(fn):
      fn()
      print(f"PASS {name}")
  print("ALL PASS")
