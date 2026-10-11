#!/usr/bin/env python3
"""Check (a‴): Freeze 3d (docs/decisions/D-0016_rulings-on-elo-8-questions.md) holds.

Freeze 3d extends Freeze 3c (D-0015, which check (a″), tools/checks/check_freeze3c.py, keeps enforcing) with the files
that give every log-loss line of the forecast test its crossed interval over players (ruling R66). The manifest of every
file the championship comparison depends on, computed as E13 prints it (analysis/e13_us_championships_freeze3d.py), must
equal the manifest D-0016 records; a missing record or manifest fails the check. Python standard library only.
"""
from __future__ import annotations

import re
import sys

from _repo import ROOT

FREEZE_RECORD = ROOT / "docs" / "decisions" / "D-0016_rulings-on-elo-8-questions.md"


def main() -> int:
    if not FREEZE_RECORD.exists():
        print(f"FREEZE   {FREEZE_RECORD.relative_to(ROOT)} is missing")
        return 1
    m = re.search(r"Freeze-3d manifest: `([0-9a-f]{64})`", FREEZE_RECORD.read_text(encoding="utf-8"))
    if not m:
        print(f"FREEZE   {FREEZE_RECORD.relative_to(ROOT)} records no Freeze-3d manifest")
        return 1
    sys.path.insert(0, str(ROOT / "analysis"))
    import e13_us_championships_freeze3d as e13d  # noqa: E402  (adds tools/ and src/ to the path itself)
    live = e13d.freeze3d_manifest()
    if live == m.group(1):
        print(f"OK       Freeze 3d: the manifest of the {len(e13d.freeze3d_lines())} frozen entries equals D-0016's")
        return 0
    print(f"FREEZE   Freeze 3d broken: the frozen files' manifest is {live}, D-0016 records {m.group(1)}; "
          "E13 lists every frozen file and its SHA-256")
    return 1


if __name__ == "__main__":
    sys.exit(main())
