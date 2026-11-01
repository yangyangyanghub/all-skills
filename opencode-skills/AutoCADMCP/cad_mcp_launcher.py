#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Launch the AutoCADMCP server (AutoCADMCP backend) over stdio.

The bundled `src/server.py` uses absolute imports (``from core import ...``,
``from adapters import ...``), so the ``src`` directory must be placed on
``sys.path`` explicitly here — the host's embedded Python locks ``sys.path`` via
its ``._pth`` file and neither injects the working directory nor honors
``PYTHONPATH``.

Connection to CAD is done by the AutoCADMCP adapter (pywin32 COM): it attaches to a
running AutoCAD/ZWCAD/GstarCAD/BricsCAD instance via ``GetActiveObject`` or
launches one via ``Dispatch``. ProgIDs are resolved from the verified user cache,
registry ``CurVer``, and registered versioned entries. CAD types are detected in
order zwcad → autocad → bricscad → gcad (see ``src/adapters/adapter_manager.py``).
"""
from __future__ import annotations

import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent
CAD_MCP_SRC = SKILL_DIR / "src"

sys.path.insert(0, str(CAD_MCP_SRC))

# Importing the server module registers all MCP tools at module load; the FastMCP
# instance `mcp` is then ready to serve stdio.
from server import mcp  # noqa: E402


if __name__ == "__main__":
    mcp.run(transport="stdio")
