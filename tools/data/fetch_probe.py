#!/usr/bin/env python3
"""Fetch, once each, the pages of the data probe for the greats (session ELO-9, Phase 1; docs/research/DATA-PROBE_greats.md).

The probe asks how far back FIDE's own sources go (the rating-list archive, the top lists, per-player rating histories
and per-player calculations) and on what terms, and what every other candidate source of historical games with ratings
says about its use. Politeness as the ELO-9 brief orders for FIDE's site, and the same for every other host: robots.txt
respected (ratings.fide.com and handbook.fide.com publish none, HTTP 404 on 2026-10-10, cached under
data/raw/fide_site/; for any other host the tool reads its robots.txt first, once, and skips a page it disallows for
every user agent); one request at a time, at least DELAY seconds apart; every page cached once under data/raw/probe/
and never fetched again; a page that is not there (HTTP 404 or 410) is recorded and the run goes on; on FIDE's hosts
the first refusal (any other HTTP error, a timeout) stops the run and is recorded; on other hosts a refusal is recorded
and the run goes on. Each request is logged in data/raw/probe/MANIFEST.tsv (key,
URL, UTC time, HTTP status, bytes, SHA-256). Raw pages are never committed (data/ is gitignored).

Usage: python3 tools/data/fetch_probe.py KEY URL [KEY URL ...]
       python3 tools/data/fetch_probe.py --ajax REFERER KEY URL [...]   (FIDE's AJAX endpoints, which answer only the
                                                                         headers their own pages send)
       python3 tools/data/fetch_probe.py --ajax REFERER --post FORM KEY URL [...]   (the same, sent as the pages send
                                                                         it: a POST with the form FORM, '' for none)
KEY names the cached file (letters, digits, '-', '_', '.').
"""
from __future__ import annotations

import hashlib
import re
import sys
import time
import urllib.error
import urllib.request
import urllib.robotparser
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "raw" / "probe"
MAN = OUT / "MANIFEST.tsv"
DELAY = 3.0
UA = "Mozilla/5.0"
FIDE_HOSTS = {"ratings.fide.com", "handbook.fide.com", "www.fide.com", "fide.com"}
NO_ROBOTS = {"ratings.fide.com", "handbook.fide.com"}      # HTTP 404 on 2026-10-10, cached under data/raw/fide_site/
KEY = re.compile(r"^[A-Za-z0-9._-]+$")
_last: dict[str, float] = {}
_robots: dict[str, urllib.robotparser.RobotFileParser | None] = {}


def log(key: str, url: str, stamp: str, status: str, body: bytes) -> None:
    if not MAN.exists():
        MAN.write_text("key\turl\tfetched_utc\tstatus\tbytes\tsha256\n", encoding="utf-8")
    digest = hashlib.sha256(body).hexdigest() if body else "-"
    with MAN.open("a", encoding="utf-8") as fh:
        fh.write(f"{key}\t{url}\t{stamp}\t{status}\t{len(body)}\t{digest}\n")


def last_request(host: str) -> float:
    """The UTC time of the last request to this host in the manifest, as epoch seconds (any earlier run included)."""
    if not MAN.exists():
        return 0.0
    last = 0.0
    for line in MAN.read_text(encoding="utf-8").splitlines()[1:]:
        parts = line.split("\t")
        if len(parts) > 2 and urlparse(parts[1].split(" ")[0]).netloc == host:
            t = datetime.strptime(parts[2], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp()
            last = max(last, t)
    return last


def wait(host: str) -> None:
    """At least DELAY seconds since the last request to the host, in this run or an earlier one (the manifest's times
    have whole seconds, so one more second is added)."""
    gap = time.monotonic() - _last.get(host, -1e9)
    if gap < DELAY:
        time.sleep(DELAY - gap)
    since = time.time() - last_request(host)
    if since < DELAY + 1:
        time.sleep(DELAY + 1 - since)
    _last[host] = time.monotonic()


def get(url: str, headers: dict[str, str], form: bytes | None = None) -> tuple[str, bytes]:
    if form is not None:
        headers = {**headers, "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}
    req = urllib.request.Request(url, data=form, headers={"User-Agent": UA, **headers})
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return str(resp.status), resp.read()
    except urllib.error.HTTPError as exc:
        return str(exc.code), b""
    except (urllib.error.URLError, TimeoutError) as exc:
        return f"error: {exc}", b""


def allowed(url: str) -> bool:
    """robots.txt, read once per host and cached under data/raw/probe/ (none for FIDE's two rating hosts)."""
    host = urlparse(url).netloc
    if host in NO_ROBOTS:
        return True
    if host not in _robots:
        key = f"robots_{host}"
        cached = OUT / f"{key}.txt"
        if not cached.exists():
            wait(host)
            stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            status, body = get(f"{urlparse(url).scheme}://{host}/robots.txt", {})
            log(key, f"{urlparse(url).scheme}://{host}/robots.txt", stamp, status, body)
            cached.write_bytes(body if status == "200" else b"")
        text = cached.read_text(encoding="utf-8", errors="replace")
        if text.strip():
            rp = urllib.robotparser.RobotFileParser()
            rp.parse(text.splitlines())
            _robots[host] = rp
        else:
            _robots[host] = None
    rp = _robots[host]
    return rp is None or rp.can_fetch(UA, url)


def main(argv: list[str]) -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    headers: dict[str, str] = {}
    if argv and argv[0] == "--ajax":
        headers = {"X-Requested-With": "XMLHttpRequest", "Referer": argv[1],
                   "Accept": "text/html, */*; q=0.01"}
        argv = argv[2:]
    form = None
    if argv and argv[0] == "--post":
        form = argv[1].encode("utf-8")
        argv = argv[2:]
    if len(argv) % 2:
        raise SystemExit(__doc__)
    seen = {line.split("\t", 1)[0] for line in MAN.read_text(encoding="utf-8").splitlines()[1:]} if MAN.exists() else set()
    for key, url in zip(argv[::2], argv[1::2]):
        if not KEY.match(key):
            raise SystemExit(f"bad key {key!r}")
        dest = OUT / f"{key}.html"
        if dest.exists() or key in seen:          # requested once already, answered or refused: never again
            print(f"cached {key}" if dest.exists() else f"requested before {key}", flush=True)
            continue
        host = urlparse(url).netloc
        if not allowed(url):
            stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            log(key, url, stamp, "disallowed by robots.txt", b"")
            print(f"skip {key}: disallowed by robots.txt", flush=True)
            continue
        wait(host)
        stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        status, body = get(url, headers, form)
        log(key, url + (f" POST {form.decode('utf-8')!r}" if form is not None else ""), stamp, status, body)
        if status in ("404", "410"):                 # not there: recorded, not a refusal
            print(f"not found {key}: {status} at {stamp}", flush=True)
            continue
        if status != "200":
            print(f"{'STOP' if host in FIDE_HOSTS else 'refused'} {key}: {status} at {stamp}", flush=True)
            if host in FIDE_HOSTS:
                return 1
            continue
        dest.write_bytes(body)
        print(f"ok {key} {len(body)} bytes at {stamp}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
