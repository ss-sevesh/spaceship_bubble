"""
conftest.py — pytest configuration for spaceship_bubble test suite.

Adds src/ to sys.path so that lifshitz, optimizer, etc. are importable.
"""

import sys
from pathlib import Path

# Project root is one level above tests/
_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_ROOT / "src"))
