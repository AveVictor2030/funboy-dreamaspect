#!/usr/bin/env python3
"""Write a Notion MCP SQL JSON payload to a destination path."""

from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: ingest_notion_json.py DEST.json < payload.json", file=sys.stderr)
        return 2
    dest = Path(sys.argv[1])
    dest.parent.mkdir(parents=True, exist_ok=True)
    data = json.load(sys.stdin)
    dest.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    n = len(data.get("results", []))
    print(f"wrote {dest} ({n} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
