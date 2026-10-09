#!/usr/bin/env python3
"""Download the Lichess broadcast archive (monthly PGN, zstd) into data/raw/lichess_broadcast/ (gitignored).

Broadcast games are released under the Creative Commons Attribution-ShareAlike
4.0 licence [V 4]; the project commits aggregates only, never raw PGN, and
attributes the source in every document that uses them.

Usage:
  python3 tools/data/fetch_lichess_broadcasts.py 2023-01 2026-09

Files: https://database.lichess.org/broadcast/lichess_db_broadcast_YYYY-MM.pgn.zst
(listed on https://database.lichess.org/ on 2026-10-09). Each file is checked
against the published broadcast/sha256sums.txt and recorded in
data/raw/lichess_broadcast/MANIFEST.tsv. Python standard library and curl only.
"""
from __future__ import annotations

import datetime
import hashlib
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "raw" / "lichess_broadcast"
BASE = "https://database.lichess.org/broadcast/"


def months(first: str, last: str):
    y, m = map(int, first.split("-"))
    y1, m1 = map(int, last.split("-"))
    while (y, m) <= (y1, m1):
        yield y, m
        m += 1
        if m == 13:
            y, m = y + 1, 1


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    sums_path = OUT / "sha256sums.txt"
    subprocess.run(["curl", "-s", "-f", "-o", str(sums_path), BASE + "sha256sums.txt"], check=True)
    sums = {}
    for line in sums_path.read_text().splitlines():
        parts = line.split()
        if len(parts) == 2:
            sums[parts[1].lstrip("*")] = parts[0]
    manifest = OUT / "MANIFEST.tsv"
    if not manifest.exists():
        manifest.write_text("month\turl\tfetched_utc\tbytes\tsha256\tmatches_published_sha256\n")
    status = 0
    for y, m in months(sys.argv[1], sys.argv[2]):
        name = f"lichess_db_broadcast_{y:04d}-{m:02d}.pgn.zst"
        dest = OUT / name
        if dest.exists() and dest.stat().st_size > 0:
            continue
        when = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        proc = subprocess.run(["curl", "-s", "-f", "-o", str(dest), BASE + name])
        if proc.returncode != 0:
            print(f"FAILED {name}", flush=True)
            dest.unlink(missing_ok=True)
            status = 1
            continue
        digest = hashlib.sha256(dest.read_bytes()).hexdigest()
        ok = sums.get(name) == digest
        with manifest.open("a") as fh:
            fh.write(f"{y:04d}-{m:02d}\t{BASE + name}\t{when}\t{dest.stat().st_size}\t{digest}\t{ok}\n")
        print(f"ok {name} sha256 {'matches' if ok else 'DOES NOT MATCH'}", flush=True)
        if not ok:
            status = 1
        time.sleep(1)
    return status


if __name__ == "__main__":
    sys.exit(main())
