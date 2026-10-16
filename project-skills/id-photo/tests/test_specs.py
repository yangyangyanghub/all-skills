import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import specs


def test_load_specs_returns_list():
    items = specs.load_specs()
    assert isinstance(items, list)
    assert len(items) >= 20


def test_get_spec_by_id():
    s = specs.get_spec("xiaotwo")
    assert s["mm"] == [35, 45]
    assert s["px"] == [413, 531]
    assert s["dpi"] == 300


def test_get_spec_by_alias():
    assert specs.get_spec("小二寸")["id"] == "xiaotwo"


def test_idcard_is_350dpi():
    s = specs.get_spec("shenfenzheng")
    assert s["dpi"] == 350
    assert s["px"] == [358, 441]


def test_unknown_spec_raises():
    import pytest
    with pytest.raises(KeyError):
        specs.get_spec("__nope__")
