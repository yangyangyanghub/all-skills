from __future__ import annotations

import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))

from adapters.mixins.connection_mixin import ConnectionMixin  # noqa: E402
from adapters.prog_id_resolver import ProgIdCandidate  # noqa: E402
from core import CADConnectionError  # noqa: E402


class FakeResolver:
    def __init__(self):
        self.remembered = None

    def discover(self, cad_type, configured_prog_id):
        return [
            ProgIdCandidate("AutoCAD.Application", "config"),
            ProgIdCandidate("AutoCAD.Application.24", "registry"),
        ]

    def remember(self, cad_type, prog_id):
        self.remembered = (cad_type, prog_id)

    def forget(self, cad_type, expected_prog_id=None):
        return None


class FakeDocuments:
    Count = 1

    def Add(self):
        raise AssertionError("An existing document should be used")


class FakeApplication:
    def __init__(self):
        self.Documents = FakeDocuments()
        self.ActiveDocument = SimpleNamespace(Name="Drawing1.dwg")


class FakeAdapter(ConnectionMixin):
    def __init__(self):
        self.cad_type = "autocad"
        self.config = SimpleNamespace(
            prog_id="AutoCAD.Application", startup_wait_time=1.0
        )
        self.application = None
        self.document = None
        self.active_prog_id = None

    def _wait_for(self, condition, timeout=20.0, interval=0.1):
        return condition()


class ConnectionMixinTests(unittest.TestCase):
    def test_connect_uses_discovered_versioned_prog_id(self):
        resolver = FakeResolver()
        attempted = []

        def get_active_object(prog_id):
            attempted.append(prog_id)
            if prog_id == "AutoCAD.Application.24":
                return FakeApplication()
            raise RuntimeError("not registered")

        with patch(
            "adapters.mixins.connection_mixin.get_prog_id_resolver",
            return_value=resolver,
        ), patch(
            "adapters.mixins.connection_mixin.pythoncom.CoInitialize"
        ), patch(
            "adapters.mixins.connection_mixin.win32com.client.GetActiveObject",
            side_effect=get_active_object,
        ):
            adapter = FakeAdapter()
            connected = adapter.connect(only_if_running=True)

        self.assertTrue(connected)
        self.assertEqual(adapter.active_prog_id, "AutoCAD.Application.24")
        self.assertEqual(adapter.document.Name, "Drawing1.dwg")
        self.assertEqual(
            resolver.remembered, ("autocad", "AutoCAD.Application.24")
        )
        self.assertEqual(
            attempted,
            ["AutoCAD.Application", "AutoCAD.Application.24"],
        )

    def test_explicit_prog_id_must_be_in_discovery_allowlist(self):
        adapter = FakeAdapter()
        candidates = FakeResolver().discover("autocad", "AutoCAD.Application")

        with self.assertRaises(CADConnectionError):
            adapter._prioritize_candidate(
                candidates, "Unrelated.Application"
            )

    def test_explicit_discovered_prog_id_is_tried_first(self):
        adapter = FakeAdapter()
        candidates = FakeResolver().discover("autocad", "AutoCAD.Application")

        prioritized = adapter._prioritize_candidate(
            candidates, "AutoCAD.Application.24"
        )

        self.assertEqual(prioritized[0].prog_id, "AutoCAD.Application.24")


if __name__ == "__main__":
    unittest.main()
