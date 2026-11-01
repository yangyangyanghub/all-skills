from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch


SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))

from adapters.adapter_manager import AdapterRegistry  # noqa: E402


class AdapterManagerTests(unittest.TestCase):
    def test_running_instances_are_checked_before_any_launch(self):
        calls = []

        class FakeAdapter:
            def __init__(self, cad_type):
                self.cad_type = cad_type

            def connect(self, only_if_running=False):
                calls.append((self.cad_type, only_if_running))
                return self.cad_type == "autocad" and only_if_running

            def is_connected(self):
                return True

        registry = AdapterRegistry()
        with patch("adapters.AutoCADAdapter", FakeAdapter):
            registry._auto_detect_internal(only_if_running=False)

        self.assertEqual(calls, [("zwcad", True), ("autocad", True)])
        self.assertEqual(registry.get_cad_type(), "autocad")

    def test_launch_phase_starts_only_after_all_running_checks_fail(self):
        calls = []

        class FakeAdapter:
            def __init__(self, cad_type):
                self.cad_type = cad_type

            def connect(self, only_if_running=False):
                calls.append((self.cad_type, only_if_running))
                return self.cad_type == "zwcad" and not only_if_running

            def is_connected(self):
                return True

        registry = AdapterRegistry()
        with patch("adapters.AutoCADAdapter", FakeAdapter):
            registry._auto_detect_internal(only_if_running=False)

        self.assertEqual(
            calls,
            [
                ("zwcad", True),
                ("autocad", True),
                ("bricscad", True),
                ("gcad", True),
                ("zwcad", False),
            ],
        )
        self.assertEqual(registry.get_cad_type(), "zwcad")

    def test_specific_connection_passes_discovered_prog_id_to_adapter(self):
        calls = []

        class FakeAdapter:
            active_prog_id = "AutoCAD.Application.24"

            def __init__(self, cad_type):
                self.cad_type = cad_type

            def connect(self, only_if_running=False, preferred_prog_id=None):
                calls.append((self.cad_type, only_if_running, preferred_prog_id))
                return True

            def is_connected(self):
                return False

        registry = AdapterRegistry()
        with patch("adapters.AutoCADAdapter", FakeAdapter):
            adapter = registry.connect_specific(
                "autocad", "AutoCAD.Application.24"
            )

        self.assertIsInstance(adapter, FakeAdapter)
        self.assertEqual(
            calls,
            [("autocad", False, "AutoCAD.Application.24")],
        )


if __name__ == "__main__":
    unittest.main()
