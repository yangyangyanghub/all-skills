from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))

from adapters.prog_id_resolver import ProgIdResolver  # noqa: E402


class FakeRegistry:
    def __init__(self, cur_ver=None, registered=None):
        self.cur_ver = cur_ver or {}
        self.registered = registered or []

    def get_cur_ver(self, base_prog_id):
        return self.cur_ver.get(base_prog_id)

    def find_registered(self, base_prog_ids):
        return list(self.registered)


class ProgIdResolverTests(unittest.TestCase):
    def test_discovery_prioritizes_cache_curver_and_registered_versions(self):
        registry = FakeRegistry(
            cur_ver={"AutoCAD.Application": "AutoCAD.Application.24"},
            registered=[
                "AutoCAD.Application",
                "AutoCAD.Application.23.1",
                "AutoCAD.Application.24",
                "AutoCAD.Application.24.1",
            ],
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            resolver = ProgIdResolver(
                cache_path=Path(temp_dir) / "cache.json", registry=registry
            )
            resolver.remember("autocad", "AutoCAD.Application.23")

            candidates = resolver.discover("autocad", "AutoCAD.Application")

        self.assertEqual(
            [candidate.prog_id for candidate in candidates],
            [
                "AutoCAD.Application.23",
                "AutoCAD.Application.24",
                "AutoCAD.Application.24.1",
                "AutoCAD.Application.23.1",
                "AutoCAD.Application",
            ],
        )
        self.assertEqual(candidates[0].source, "cache")
        self.assertEqual(candidates[1].source, "curver")

    def test_cache_can_be_invalidated_conditionally(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            resolver = ProgIdResolver(
                cache_path=Path(temp_dir) / "cache.json", registry=FakeRegistry()
            )
            resolver.remember("autocad", "AutoCAD.Application.24")
            resolver.forget("autocad", "AutoCAD.Application.23")
            self.assertEqual(
                resolver.get_cached("autocad"), "AutoCAD.Application.24"
            )

            resolver.forget("autocad", "AutoCAD.Application.24")
            self.assertIsNone(resolver.get_cached("autocad"))

    def test_invalid_cache_does_not_block_registry_discovery(self):
        registry = FakeRegistry(registered=["AutoCAD.Application.24"])
        for invalid_content in ("not-json", '{"connections": []}'):
            with self.subTest(invalid_content=invalid_content):
                with tempfile.TemporaryDirectory() as temp_dir:
                    cache_path = Path(temp_dir) / "cache.json"
                    cache_path.write_text(invalid_content, encoding="utf-8")
                    resolver = ProgIdResolver(
                        cache_path=cache_path, registry=registry
                    )

                    candidates = resolver.discover(
                        "autocad", "AutoCAD.Application"
                    )

                self.assertEqual(
                    [candidate.prog_id for candidate in candidates],
                    ["AutoCAD.Application.24", "AutoCAD.Application"],
                )


if __name__ == "__main__":
    unittest.main()
