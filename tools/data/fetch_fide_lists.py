#!/usr/bin/env python3
"""Download FIDE's monthly rating lists (TXT format) into data/raw/fide/ (gitignored).

FIDE's lists carry no data licence [V 3]: they are downloaded and analysed,
never committed or redistributed (D-0005, D17). Only aggregates are published.

Usage:
  python3 tools/data/fetch_fide_lists.py standard 2015-02 2026-10
  python3 tools/data/fetch_fide_lists.py rapid 2015-02 2026-10

Archive URLs follow the pattern verified on ratings.fide.com/download_lists.phtml
(via its a_download.php?period=YYYY-MM-01 endpoint) on 2026-10-09:
  https://ratings.fide.com/download/<tc>_<mon><yy>frl.zip
Requests are sequential with a pause between files. Each file is recorded in
data/raw/fide/MANIFEST.tsv (period, time control, URL, UTC time, bytes, sha256).
Python standard library and the curl command only.
"""
from __future__ import annotations

import datetime
import hashlib
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "raw" / "fide"
MONTHS = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]


def periods(first: str, last: str):
    y, m = map(int, first.split("-"))
    y1, m1 = map(int, last.split("-"))
    while (y, m) <= (y1, m1):
        yield y, m
        m += 1
        if m == 13:
            y, m = y + 1, 1


def main() -> int:
    tc, first, last = sys.argv[1], sys.argv[2], sys.argv[3]
    (OUT / tc).mkdir(parents=True, exist_ok=True)
    manifest = OUT / "MANIFEST.tsv"
    if not manifest.exists():
        manifest.write_text("period\ttc\turl\tfetched_utc\tbytes\tsha256\n")
    for y, m in periods(first, last):
        name = f"{tc}_{MONTHS[m - 1]}{y % 100:02d}frl.zip"
        dest = OUT / tc / name
        if dest.exists() and dest.stat().st_size > 0:
            continue
        url = f"https://ratings.fide.com/download/{name}"
        when = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        tmp = dest.with_suffix(".part")
        proc = subprocess.run(["curl", "-s", "-f", "-A", "Mozilla/5.0", "-o", str(tmp), url])
        if proc.returncode != 0 or not tmp.exists():
            print(f"FAILED {url} (curl exit {proc.returncode})", flush=True)
            tmp.unlink(missing_ok=True)
            time.sleep(5)
            continue
        tmp.rename(dest)
        data = dest.read_bytes()
        with manifest.open("a") as fh:
            fh.write(f"{y:04d}-{m:02d}\t{tc}\t{url}\t{when}\t{len(data)}\t{hashlib.sha256(data).hexdigest()}\n")
        print(f"ok {name} {len(data)} bytes", flush=True)
        time.sleep(2)
    return 0


if __name__ == "__main__":
    sys.exit(main())
