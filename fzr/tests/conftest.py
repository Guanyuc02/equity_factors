"""Test configuration to ensure the project package is importable."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

# Allow tests to import the package using the src/ layout.
src_path = str(SRC)
if src_path not in sys.path:
    sys.path.insert(0, src_path)
