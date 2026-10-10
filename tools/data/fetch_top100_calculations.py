#!/usr/bin/env python3
"""Fetch, once each, FIDE's published per-player rating calculations of the October 2026 top 100 (SPEC-TOP100).

FIDE publishes, for each player and rating period, the calculation behind the change on the list
(https://ratings.fide.com/calculations.phtml; the data come from /a_indv_calculation.php, which answers only requests
that carry the AJAX headers the page itself sends; tools/data/fetch_fide_calculations.py). This tool fetches the
periods in which a player of the top 100 has rated games on FIDE's monthly standard list, from the February 2020 list
to the October 2026 list, under the politeness rules of the ELO-7 brief: ratings.fide.com publishes no robots.txt
(HTTP 404 on 2026-10-10, cached under data/raw/fide_site/); one request at a time, at least DELAY seconds apart; every
response cached once under data/raw/fide_calculations/ and never fetched again; the run stops at the first refusal
(an HTTP error, a timeout or a page that is not a calculation) and records it. Nothing from the November 2026 rating
period is requested. Raw pages are never committed (data/ is gitignored).

Modes:
  plan            print the ID:PERIOD pairs: the top 100 active players of the October 2026 standard list (no
                  inactivity flag; ties at rank 100 broken by FIDE ID), each list from 2020-02 to 2026-10 on which
                  the player has at least one rated game (needs data/interim/fide/standard/)
  fetch FILE      fetch every pair of FILE (one ID:PERIOD a line) that is not cached yet; append one line per request
                  to data/raw/fide_calculations/MANIFEST_top100.tsv (pair, URL, UTC time, HTTP status, bytes, SHA-256)

Python standard library only.
"""
from __future__ import annotations

import csv
import hashlib
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw" / "fide_calculations"
LISTS = ROOT / "data" / "interim" / "fide" / "standard"
MANIFEST = RAW / "MANIFEST_top100.tsv"
URL = "https://ratings.fide.com/a_indv_calculation.php?id_number={id}&rating_period={period}-01&t=0"
REFERER = "https://ratings.fide.com/calculations.phtml?id_number={id}&period={period}-01&rating=0"
DELAY = 3.0
FIRST, LAST, TOP_LIST, N_TOP = "2020-02", "2026-10", "2026-10", 100


def months(first: str, last: str) -> list[str]:
    y, m = map(int, first.split("-"))
    out = []
    while f"{y:04d}-{m:02d}" <= last:
        out.append(f"{y:04d}-{m:02d}")
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out


def load_list(period: str) -> dict[str, tuple[int, int, str]]:
    out = {}
    with (LISTS / f"{period}.tsv").open(encoding="utf-8") as fh:
        rows = csv.reader(fh, delimiter="\t")
        next(rows)
        for pid, rating, games, _k, _by, _sex, _fed, flag, _title in rows:
            if rating.isdigit():
                out[pid] = (int(rating), int(games) if games.isdigit() else 0, flag)
    return out


def top100() -> list[str]:
    lst = load_list(TOP_LIST)
    active = sorted(((r, int(pid)) for pid, (r, _g, flag) in lst.items() if "i" not in flag), key=lambda x: (-x[0], x[1]))
    return [str(pid) for _r, pid in active[:N_TOP]]


def plan() -> list[str]:
    ids = top100()
    pairs = []
    for period in months(FIRST, LAST):
        lst = load_list(period)
        pairs += [f"{pid}:{period}" for pid in ids if pid in lst and lst[pid][1] > 0]
    return sorted(pairs, key=lambda s: (s.split(":")[1], int(s.split(":")[0])))


def cached(pid: str, period: str) -> Path:
    return RAW / f"{pid}_{period}.html"


BLOCKED = ("Technical Info Page", "captcha", "Captcha", "Access Denied", "Access denied", "Too Many Requests",
           "cf-browser-verification", "Attention Required")


def looks_like_calculation(body: bytes) -> bool:
    text = body.decode("utf-8-sig", "replace")
    return "calc_table" in text or "Total change" in text or "rtng_line01" in text


def looks_blocked(body: bytes) -> bool:
    text = body.decode("utf-8-sig", "replace")
    return any(s in text for s in BLOCKED)


def fetch(path: str) -> int:
    RAW.mkdir(parents=True, exist_ok=True)
    pairs = [line.strip() for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]
    todo = [p for p in pairs if not cached(*p.split(":")).exists()]
    print(f"{len(pairs)} pairs, {len(pairs) - len(todo)} cached, {len(todo)} to fetch", flush=True)
    new = not MANIFEST.exists()
    with MANIFEST.open("a", encoding="utf-8") as man:
        if new:
            man.write("pair\turl\tfetched_utc\tstatus\tbytes\tsha256\n")
        odd, run = 0, 0
        for n, pair in enumerate(todo):
            pid, period = pair.split(":")
            if period > LAST:
                raise SystemExit(f"refusing {pair}: after the October 2026 list")
            if n:
                time.sleep(DELAY)
            url = URL.format(id=pid, period=period)
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "X-Requested-With": "XMLHttpRequest",
                                                       "Referer": REFERER.format(id=pid, period=period)})
            stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            try:
                with urllib.request.urlopen(req, timeout=60) as resp:
                    status, body = resp.status, resp.read()
            except urllib.error.HTTPError as exc:
                man.write(f"{pair}\t{url}\t{stamp}\t{exc.code}\t0\t-\n")
                print(f"STOP {pair}: HTTP {exc.code} at {stamp}", flush=True)
                return 1
            except Exception as exc:                          # timeouts, resets: a refusal for this tool's purposes
                man.write(f"{pair}\t{url}\t{stamp}\terror\t0\t-\n")
                print(f"STOP {pair}: {type(exc).__name__}: {exc} at {stamp}", flush=True)
                return 1
            digest = hashlib.sha256(body).hexdigest()
            man.write(f"{pair}\t{url}\t{stamp}\t{status}\t{len(body)}\t{digest}\n")
            man.flush()
            if status != 200 or looks_blocked(body):
                (RAW / f"refused_{pid}_{period}.html").write_bytes(body)
                print(f"STOP {pair}: HTTP {status}, {len(body)} bytes, refused at {stamp}", flush=True)
                return 1
            cached(pid, period).write_bytes(body)                # cached once, never fetched again
            if not looks_like_calculation(body):
                odd, run = odd + 1, run + 1
                print(f"NOTE {pair}: HTTP 200 but no calculation in {len(body)} bytes ({odd} so far)", flush=True)
                if run >= 5:
                    print("STOP: five answers in a row without a calculation", flush=True)
                    return 1
            else:
                run = 0
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
