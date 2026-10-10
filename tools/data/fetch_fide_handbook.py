#!/usr/bin/env python3
"""Fetch, once each, chapters of FIDE's handbook (https://handbook.fide.com/chapter/<CODE>) for transcription.

Used to transcribe the earlier versions of the FIDE Rating Regulations that applied to rating periods from February
2020 (SPEC-TOP100; docs/research/VERIFICATION_RATING-REGULATIONS-ARCHIVE.md). Politeness as the ELO-7 brief orders:
handbook.fide.com publishes no robots.txt (HTTP 404 on 2026-10-10, cached under data/raw/fide_site/); one request at
a time, at least DELAY seconds apart; every page cached once under data/raw/fide_site/handbook/ and never fetched
again; the first refusal stops the run and is recorded. Each request is logged in data/raw/fide_site/handbook/
MANIFEST.tsv (code, URL, UTC time, HTTP status, bytes, SHA-256). Raw pages are never committed (data/ is gitignored).

Usage: python3 tools/data/fetch_fide_handbook.py B022024 B022022 ...
"""
from __future__ import annotations

import hashlib
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "raw" / "fide_site" / "handbook"
URL = "https://handbook.fide.com/chapter/{code}"
DELAY = 3.0


def main(codes: list[str]) -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    man = OUT / "MANIFEST.tsv"
    if not man.exists():
        man.write_text("code\turl\tfetched_utc\tstatus\tbytes\tsha256\n", encoding="utf-8")
    first = True
    for code in codes:
        dest = OUT / f"{code}.html"
        if dest.exists():
            print(f"cached {code}", flush=True)
            continue
        if not first:
            time.sleep(DELAY)
        first = False
        url = URL.format(code=code)
        stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                status, body = resp.status, resp.read()
        except urllib.error.HTTPError as exc:
            with man.open("a", encoding="utf-8") as fh:
                fh.write(f"{code}\t{url}\t{stamp}\t{exc.code}\t0\t-\n")
            print(f"STOP {code}: HTTP {exc.code} at {stamp}", flush=True)
            return 1
        digest = hashlib.sha256(body).hexdigest()
        with man.open("a", encoding="utf-8") as fh:
            fh.write(f"{code}\t{url}\t{stamp}\t{status}\t{len(body)}\t{digest}\n")
        if status != 200:
            print(f"STOP {code}: HTTP {status} at {stamp}", flush=True)
            return 1
        dest.write_bytes(body)
        print(f"ok {code} {len(body)} bytes {digest[:12]} at {stamp}", flush=True)
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    sys.exit(main(sys.argv[1:]))
