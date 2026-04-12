#!/usr/bin/env python3
"""
Auto-patches dynamic sections of CLAUDE.md from live project state.
Runs as a PostToolUse hook after every Edit/Write.

Updates:
  - casimir-tools version (from casimir_tools/casimir_tools/__init__.py)
  - Physical constants block (from src/lifshitz.py)
  - GitNexus index stats (from .gitnexus/meta.json)
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent
CLAUDE_MD = ROOT / "CLAUDE.md"


def get_casimir_version() -> str | None:
    init_file = ROOT / "casimir_tools" / "casimir_tools" / "__init__.py"
    if not init_file.exists():
        return None
    m = re.search(r'^__version__\s*=\s*"([^"]+)"', init_file.read_text(encoding="utf-8"), re.MULTILINE)
    return m.group(1) if m else None


def get_physical_constants() -> dict[str, str]:
    lifshitz = ROOT / "src" / "lifshitz.py"
    if not lifshitz.exists():
        return {}
    text = lifshitz.read_text(encoding="utf-8")
    constants = {}
    for name in ("HBAR", "KB", "C"):
        m = re.search(rf"^{name}\s*=\s*([0-9eE.+\-]+)", text, re.MULTILINE)
        if m:
            constants[name] = m.group(1)
    return constants


def get_gitnexus_stats() -> dict | None:
    meta = ROOT / ".gitnexus" / "meta.json"
    if not meta.exists():
        return None
    try:
        data = json.loads(meta.read_text(encoding="utf-8"))
        s = data.get("stats", {})
        return {
            "nodes": s.get("nodes", 0),
            "edges": s.get("edges", 0),
            "processes": s.get("processes", 0),
        }
    except (json.JSONDecodeError, KeyError):
        return None


def patch(text: str) -> str:
    # --- 1. casimir-tools version ---
    version = get_casimir_version()
    if version:
        # Checklist line: v0.1.7 live
        text = re.sub(
            r"(\*\*casimir-tools PyPI package\*\* \(v)[0-9a-zA-Z.\-]+",
            rf"\g<1>{version}",
            text,
        )
        # Project structure line: casimir_tools/ ... v0.1.x
        text = re.sub(
            r"(casimir_tools/\s+<-.*?v)[0-9a-zA-Z.\-]+",
            rf"\g<1>{version}",
            text,
        )

    # --- 2. Physical constants block ---
    consts = get_physical_constants()
    if consts:
        hbar = consts.get("HBAR", "1.0545718e-34")
        kb   = consts.get("KB",   "1.380649e-23")
        c    = consts.get("C",    "2.99792458e8")
        new_block = (
            "```python\n"
            f"HBAR = {hbar}   # J·s\n"
            f"KB   = {kb}    # J/K\n"
            f"C    = {c}    # m/s\n"
            "```"
        )
        text = re.sub(
            r"```python\nHBAR = [^\n]+\nKB\s+=\s+[^\n]+\nC\s+=\s+[^\n]+\n```",
            new_block,
            text,
        )

    # --- 3. GitNexus stats ---
    stats = get_gitnexus_stats()
    if stats:
        text = re.sub(
            r"(indexed by GitNexus as \*\*spaceship_bubble\*\* \()\d+ symbols, \d+ relationships, \d+ execution flows(\))",
            rf"\g<1>{stats['nodes']} symbols, {stats['edges']} relationships, {stats['processes']} execution flows\2",
            text,
        )

    return text


def main() -> None:
    if not CLAUDE_MD.exists():
        print("CLAUDE.md not found — skipping", file=sys.stderr)
        return

    original = CLAUDE_MD.read_text(encoding="utf-8")
    updated = patch(original)

    if updated != original:
        CLAUDE_MD.write_text(updated, encoding="utf-8")
        print("CLAUDE.md auto-updated")
    # silent no-op when nothing changed


if __name__ == "__main__":
    main()
