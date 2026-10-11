#!/usr/bin/env python3
"""Fetch, once each, FIDE's standard rating lists of January 2001 to January 2015 (session ELO-9; SPEC-GREATS).

FIDE's download page offers lists from February 2015 only; its page of February 2022 (the Internet Archive's copy,
cached by the data probe under data/raw/probe/wayback_fide_download_2022.html) offered every list from January 2001,
and FIDE's server still serves those files under their old names (docs/research/DATA-PROBE_greats.md §2.1). For each
period of that page from 2001-01 to 2015-01 this tool takes the file from the probe's cache when the probe fetched it,
and otherwise requests, from https://ratings.fide.com/download/, the old name `{mon}{yy}frl.zip` and, if that is not
there (HTTP 404), the later name `standard_{mon}{yy}frl.zip`. Politeness as the ELO-9 brief orders: ratings.fide.com
publishes no robots.txt (HTTP 404 on 2026-10-10, cached under data/raw/fide_site/); one request at a time, at least
DELAY seconds after the last request to ratings.fide.com that data/raw/probe/MANIFEST.tsv or this tool's manifest
records; every file cached once under data/raw/fide_old/standard/ and never fetched again; the first refusal (any HTTP
error but 404, a timeout) stops the run and is recorded. Each request is logged in data/raw/fide_old/MANIFEST.tsv
(period, URL, UTC time, HTTP status, bytes, SHA-256). Raw files are never committed (data/ is gitignored).

Usage: python3 tools/data/fetch_fide_old_lists.py [FIRST LAST]     (default 2001-01 2015-01)
"""
from __future__ import annotations

import csv
import hashlib
import re
import shutil
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "data"))
import politeness  # noqa: E402  (R85: the project's User-Agent)
PROBE = ROOT / "data" / "raw" / "probe"
OUT = ROOT / "data" / "raw" / "fide_old" / "standard"
MAN = ROOT / "data" / "raw" / "fide_old" / "MANIFEST.tsv"
BASE = "https://ratings.fide.com/download/"
DELAY = 3.0
MON = ("jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec")


def periods(first: str, last: str) -> list[str]:
    page = (PROBE / "wayback_fide_download_2022.html").read_text(encoding="utf-8", errors="replace")
    return sorted(p for p in {v[:7] for v in re.findall(r'<option[^>]*value="(\d{4}-\d\d)-\d\d"', page)}
                  if first <= p <= last)


def last_request() -> float:
    """The time of the last request to ratings.fide.com in either manifest, as epoch seconds."""
    last = 0.0
    for path, col in ((PROBE / "MANIFEST.tsv", "url"), (MAN, "url")):
        if not path.exists():
            continue
        with path.open(encoding="utf-8") as fh:
            for r in csv.DictReader(fh, delimiter="\t"):
                if "ratings.fide.com" in r[col]:
                    t = datetime.strptime(r["fetched_utc"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                    last = max(last, t.timestamp())
    return last


def log(period: str, url: str, stamp: str, status: str, body: bytes) -> None:
    if not MAN.exists():
        MAN.write_text("period\turl\tfetched_utc\tstatus\tbytes\tsha256\n", encoding="utf-8")
    digest = hashlib.sha256(body).hexdigest() if body else "-"
    with MAN.open("a", encoding="utf-8") as fh:
        fh.write(f"{period}\t{url}\t{stamp}\t{status}\t{len(body)}\t{digest}\n")


def requested(url: str) -> bool:
    if not MAN.exists():
        return False
    with MAN.open(encoding="utf-8") as fh:
        return any(r["url"] == url for r in csv.DictReader(fh, delimiter="\t"))


def get(url: str) -> tuple[str, str, bytes]:
    """Wait until DELAY + 1 seconds have passed since the last request to the host that a manifest records, then send;
    the time returned, and logged, is the moment of sending (an earlier version logged the time before the wait, so
    that two requests could go out a second apart: fixed in session ELO-9 after 18 requests)."""
    since = time.time() - last_request()
    if since < DELAY + 1:
        time.sleep(DELAY + 1 - since)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    req = urllib.request.Request(url, headers=politeness.headers())
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return stamp, str(resp.status), resp.read()
    except urllib.error.HTTPError as exc:
        return stamp, str(exc.code), b""
    except (urllib.error.URLError, TimeoutError) as exc:
        return stamp, f"error: {exc}", b""


def main(argv: list[str]) -> int:
    first, last = (argv[0], argv[1]) if len(argv) == 2 else ("2001-01", "2015-01")
    OUT.mkdir(parents=True, exist_ok=True)
    for period in periods(first, last):
        dest = OUT / f"{period}.zip"
        if dest.exists():
            print(f"cached {period}", flush=True)
            continue
        tag = f"{MON[int(period[5:]) - 1]}{period[2:4]}"
        names = (f"{tag}frl.zip", f"standard_{tag}frl.zip")
        cached = [PROBE / f"fide_list_{n}.html" for n in names if (PROBE / f"fide_list_{n}.html").exists()]
        if cached:                                   # fetched once by the probe: copied, not fetched again
            shutil.copyfile(cached[0], dest)
            print(f"from the probe's cache {period}", flush=True)
            continue
        for name in names:
            url = BASE + name
            if requested(url):
                continue
            stamp, status, body = get(url)
            log(period, url, stamp, status, body)
            if status == "200" and body[:2] == b"PK":
                dest.write_bytes(body)
                print(f"ok {period} {name} {len(body)} bytes at {stamp}", flush=True)
                break
            if status == "404":
                print(f"not found {period} {name} at {stamp}", flush=True)
                continue
            print(f"STOP {period} {name}: {status} at {stamp}", flush=True)
            return 1
        else:
            print(f"none {period}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
