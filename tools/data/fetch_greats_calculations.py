#!/usr/bin/env python3
"""Fetch, once each, FIDE's published per-player rating calculations of the greats, April 2008 to December 2019
(SPEC-GREATS v1.0 §6; session ELO-9, Phase 3).

The players are SPEC-GREATS §2's (analysis/aggregates/GREATS_players.json); a player's standard rating periods are those
FIDE's calculations index lists for the player (the profile's "Check more periods", fetched once each by
tools/data/fetch_probe.py into data/raw/probe/fide_calcs_more_<ID>.html); the window is the lists of April 2008, the
first whose calculations give every game (docs/research/DATA-PROBE_greats.md §2.4), to December 2019. The page is the
AJAX answer the calculations page itself requests (/a_indv_calculation.php, with the headers the page sends), as
tools/data/fetch_top100_calculations.py fetched the top 100's. Politeness as the ELO-9 brief and ruling R75 order:
ratings.fide.com publishes no robots.txt (HTTP 404 on 2026-10-10, cached under data/raw/fide_site/); one request at a
time, sent at least four seconds after the last request to ratings.fide.com in this run or in any manifest of the
session's fetches (tools/data/politeness.py; the time logged is the moment of sending; the run of 11 October 2026 kept
four seconds within the run, three plus the log's rounding across runs, before R75); every page cached once under
data/raw/fide_calculations_greats/ and never fetched again (a page the probe fetched is copied); the first refusal (an
HTTP error, a timeout, a page that looks like a block) stops the run and is recorded. Raw pages are never committed (data/ is gitignored).

Modes:
  plan            print the ID:PERIOD pairs
  fetch FILE      fetch every pair of FILE (one ID:PERIOD a line) not cached yet; one line per request in
                  data/raw/fide_calculations_greats/MANIFEST.tsv (pair, URL, UTC time, HTTP status, bytes, SHA-256)

Python standard library only.
"""
from __future__ import annotations

import hashlib
import json
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
import politeness  # noqa: E402  (R75: four seconds to ratings.fide.com, across runs and tools)

PROBE = ROOT / "data" / "raw" / "probe"
RAW = ROOT / "data" / "raw" / "fide_calculations_greats"
MANIFEST = RAW / "MANIFEST.tsv"
SELECTED = ROOT / "analysis" / "aggregates" / "GREATS_players.json"
URL = "https://ratings.fide.com/a_indv_calculation.php?id_number={id}&rating_period={period}-01&t=0"
REFERER = "https://ratings.fide.com/calculations.phtml?id_number={id}&period={period}-01&rating=0"
FIRST, LAST = "2008-04", "2019-12"
BLOCKED = ("Technical Info Page", "captcha", "Captcha", "Access Denied", "Access denied", "Too Many Requests",
           "cf-browser-verification", "Attention Required")


def plan() -> list[str]:
    players = json.loads(SELECTED.read_text(encoding="utf-8"))["players"]
    pairs = []
    for p in players:
        if not p["fide_id"]:
            continue
        index = (PROBE / f"fide_calcs_more_{p['fide_id']}.html").read_text(encoding="utf-8", errors="replace")
        periods = sorted(set(re.findall(r"period=(\d{4}-\d\d)-\d\d&rating=0", index)))
        pairs += [f"{p['fide_id']}:{x}" for x in periods if FIRST <= x <= LAST]
    return sorted(pairs, key=lambda s: (s.split(":")[1], int(s.split(":")[0])))


def cached(pid: str, period: str) -> Path:
    return RAW / f"{pid}_{period}.html"


def fetch(path: str) -> int:
    RAW.mkdir(parents=True, exist_ok=True)
    pairs = [line.strip() for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]
    for pair in pairs:                                   # pages the probe fetched once: copied, not fetched again
        pid, period = pair.split(":")
        probe = PROBE / f"fide_calc_{pid}_{period}.html"
        if probe.exists() and not cached(pid, period).exists():
            shutil.copyfile(probe, cached(pid, period))
    todo = [p for p in pairs if not cached(*p.split(":")).exists()]
    print(f"{len(pairs)} pairs, {len(pairs) - len(todo)} cached, {len(todo)} to fetch", flush=True)
    if not MANIFEST.exists():
        MANIFEST.write_text("pair\turl\tfetched_utc\tstatus\tbytes\tsha256\n", encoding="utf-8")
    last = None
    for n, pair in enumerate(todo):
        pid, period = pair.split(":")
        if not FIRST <= period <= LAST:
            raise SystemExit(f"refusing {pair}: outside {FIRST} to {LAST}")
        politeness.wait("ratings.fide.com", last)
        url = URL.format(id=pid, period=period)
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "X-Requested-With": "XMLHttpRequest",
                                                   "Referer": REFERER.format(id=pid, period=period)})
        stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        last = time.time()
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                status, body = resp.status, resp.read()
        except urllib.error.HTTPError as exc:
            with MANIFEST.open("a", encoding="utf-8") as man:
                man.write(f"{pair}\t{url}\t{stamp}\t{exc.code}\t0\t-\n")
            print(f"STOP {pair}: HTTP {exc.code} at {stamp}", flush=True)
            return 1
        except Exception as exc:                          # timeouts, resets: a refusal for this tool's purposes
            with MANIFEST.open("a", encoding="utf-8") as man:
                man.write(f"{pair}\t{url}\t{stamp}\terror\t0\t-\n")
            print(f"STOP {pair}: {type(exc).__name__}: {exc} at {stamp}", flush=True)
            return 1
        with MANIFEST.open("a", encoding="utf-8") as man:
            man.write(f"{pair}\t{url}\t{stamp}\t{status}\t{len(body)}\t{hashlib.sha256(body).hexdigest()}\n")
        text = body.decode("utf-8-sig", "replace")
        if status != 200 or any(s in text for s in BLOCKED):
            (RAW / f"refused_{pid}_{period}.html").write_bytes(body)
            print(f"STOP {pair}: HTTP {status}, {len(body)} bytes, refused at {stamp}", flush=True)
            return 1
        cached(pid, period).write_bytes(body)                # cached once, never fetched again
        if (n + 1) % 100 == 0:
            print(f"{n + 1} of {len(todo)} fetched, last {pair} at {stamp}", flush=True)
    print("done", flush=True)
    return 0


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "plan":
        print("\n".join(plan()))
    elif len(sys.argv) == 3 and sys.argv[1] == "fetch":
        sys.exit(fetch(sys.argv[2]))
    else:
        raise SystemExit(__doc__)
