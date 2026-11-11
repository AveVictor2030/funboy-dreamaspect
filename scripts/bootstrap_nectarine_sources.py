#!/usr/bin/env python3
"""Write data/sources/nectarine-q*.json from an MCP SQL export bundle.

Usage (after saving Notion query payloads):
  python3 scripts/bootstrap_nectarine_sources.py path/to/bundle.json

bundle.json shape:
  {"q1": {"results": [...]}, "q2": {...}, "q3": {...}, "q4": {...}}
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "sources"

MAP = {
    "q1": "nectarine-q1-octdec2025.json",
    "q2": "nectarine-q2-janmar2026.json",
    "q3": "nectarine-q3-aprjun2026.json",
    "q4": "nectarine-q4-jul-aug25-2026.json",
}


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__, file=sys.stderr)
        return 2
    bundle = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    OUT.mkdir(parents=True, exist_ok=True)
    for key, name in MAP.items():
        if key not in bundle:
            print(f"Missing key {key!r} in bundle", file=sys.stderr)
            return 1
        path = OUT / name
        path.write_text(json.dumps(bundle[key], indent=2) + "\n", encoding="utf-8")
        n = len(bundle[key].get("results", []))
        print(f"wrote {path.name} ({n} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
