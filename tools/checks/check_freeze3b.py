#!/usr/bin/env python3
"""Check (a′): Freeze 3b (docs/decisions/D-0014_forecast-test-and-rulings.md, part A) holds.

Freeze 3b extends Freeze 3a (D-0012, which check (a), tools/checks/check_outputs.py, keeps enforcing) with the files of
the pre-registered forecast test (R54), the figures the pairings fix (R55) and the PILOT on (b′) (R56). The manifest of
every file the championship comparison depends on, computed as E13 prints it
(analysis/e13_us_championships_freeze3b.py), must equal the manifest D-0014 records, so that a change to a frozen file
fails this check even after E13 is regenerated; a missing record or manifest fails it too. Python standard library only.
"""
from __future__ import annotations

import re
import sys

from _repo import ROOT

FREEZE_RECORD = ROOT / "docs" / "decisions" / "D-0014_forecast-test-and-rulings.md"


def main() -> int:
    if not FREEZE_RECORD.exists():
        print(f"FREEZE   {FREEZE_RECORD.relative_to(ROOT)} is missing")
        return 1
    m = re.search(r"Freeze-3b manifest: `([0-9a-f]{64})`", FREEZE_RECORD.read_text(encoding="utf-8"))
    if not m:
        print(f"FREEZE   {FREEZE_RECORD.relative_to(ROOT)} records no Freeze-3b manifest")
        return 1
    sys.path.insert(0, str(ROOT / "analysis"))
    import e13_us_championships_freeze3b as e13b  # noqa: E402  (adds tools/ and src/ to the path itself)
    live = e13b.freeze3b_manifest()
    if live == m.group(1):
        print(f"OK       Freeze 3b: the manifest of the {len(e13b.freeze3b_lines())} frozen entries equals D-0014's")
        return 0
    print(f"FREEZE   Freeze 3b broken: the frozen files' manifest is {live}, D-0014 records {m.group(1)}; "
          "E13 lists every frozen file and its SHA-256")
    return 1


if __name__ == "__main__":
    sys.exit(main())
