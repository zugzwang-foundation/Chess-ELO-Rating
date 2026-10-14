#!/usr/bin/env python3
"""Session ELO-D1's fetches: robots.txt and published terms, Sonas's reports, the pilot of 2,000 per-player calculation
pages for 2025 standard periods, and the probe of FIDE's tournament reports.

The calculation pages are fetched as the repository's fetcher fetches them (tools/data/fetch_fide_calculations.py: the
AJAX answer the calculations page itself requests, /a_indv_calculation.php, with the headers that page sends) and read by
E17's parser (analysis/e17_top100_extract.py, parse_page), unchanged. Politeness (the ELO-D1 relay): robots.txt read
first on every host and obeyed; at least four seconds between requests to any FIDE host, measured across runs and tools
(tools/data/politeness.py, which reads this session's log as well; from 09:34 UTC on 14 October 2026 every host of
fide.com counts as one site); every file cached once and never fetched again; on
HTTP 429 or 5xx, or a timeout, the gap is doubled, and after three refusals in a row the route stops; a page that looks
like a block (403, a captcha, "Access Denied") stops it at once; the client always identifies itself with the project's
User-Agent (R85). Every request is logged, one line each, to data/fetch_log/ELO-D1.tsv (UTC time of sending, host, path,
status, bytes, SHA-256, URL, item). The championship lock: no rating period after the October 2026 list, no tournament
report of an event that ended on or after 1 October 2026 or whose name refers to a 2026 U.S. Championship. Nothing
fetched is committed (data/ is gitignored).

Modes:
  robots HOST          fetch https://HOST/robots.txt once (data/raw/sourcing/robots/)
  get URL NAME         fetch one page once (terms, reports) into data/raw/sourcing/pages/NAME, after the host's robots.txt
  plan                 draw the pilot's sample from the October 2025 standard list and write its queue,
                       data/raw/sourcing/pilot_queue.txt, and its plan, data/raw/sourcing/pilot_plan.json (both local)
  run QUEUE            work through a queue, one item a line, "calc ID:PERIOD", "report EVENT_ID" or "get URL NAME"; the priority queue
                       data/raw/sourcing/queue_priority.txt is read first and both are re-read after every request, so
                       that items appended later are taken in turn by the one process
  report-events N      print N tournament-report items for the probe: the events of the pilot's pages of the January 2025
                       period (all of them ended before 1 October 2026; none of a 2026 U.S. Championship), in the SHA-256
                       order of "ELO-D1-report:EVENT", the first N, for the priority queue

Session ELO-D2 (the club-level sample, docs/specs/SPEC-SOURCING_v1_1.md), with the same endpoint, headers, cache,
politeness and parser, its requests logged to data/fetch_log/ELO-D2.tsv:
  club-robots          fetch https://ratings.fide.com/robots.txt once more, logged in the session's log
  club-plan            draw the sample from the frame with the allocation committed in
                       analysis/aggregates/E21_club_plan.json (totals only) and write its queue,
                       data/raw/sourcing/club_queue.txt, and its plan, data/raw/sourcing/club_plan.json (both local)
  club-run QUEUE STATUS
                       work through the queue as run does, calculation pages of 2025 periods only, and stop at
                       CLUB_CAP requests in the session's log; write the run's status to STATUS (outside the
                       repository) at the start, every hour and at the end, its last line COMPLETE when the queue is done

Python standard library only.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "data"))
import politeness  # noqa: E402  (R75's gaps across runs and tools; R85's User-Agent)

LOG = ROOT / "data" / "fetch_log" / "ELO-D1.tsv"
BASE = ROOT / "data" / "raw" / "sourcing"
ROBOTS = BASE / "robots"
PAGES = BASE / "pages"
CALCS = BASE / "calculations"
REPORTS = BASE / "reports"
QUEUE_PRIORITY = BASE / "queue_priority.txt"
PLAN = BASE / "pilot_plan.json"
QUEUE = BASE / "pilot_queue.txt"
LISTS = ROOT / "data" / "interim" / "fide" / "standard"
# the calculation page, as tools/data/fetch_fide_calculations.py requests it
CALC_URL = "https://ratings.fide.com/a_indv_calculation.php?id_number={id}&rating_period={period}-01&t=0"
CALC_REFERER = "https://ratings.fide.com/calculations.phtml?id_number={id}&period={period}-01&rating=0"
REPORT_URL = "https://ratings.fide.com/report.phtml?event={event}&t=0"
LAST_LIST = "2026-10"                    # the championship lock: no rating period after the October 2026 list
LOCK_END = "2026-10-01"                  # no tournament that ended on or after 1 October 2026
LOCKED_NAME = re.compile(r"(U\.?\s?S\.?|United States)\b.*Championship", re.I)
BLOCKED = ("Technical Info Page", "captcha", "Captcha", "Access Denied", "Access denied", "Too Many Requests",
           "cf-browser-verification", "Attention Required")
MAX_REFUSALS = 3                         # refusals in a row before the route stops
MAX_GAP = 300.0

# ------------------------------------------------------------------ the pilot's sample (the ELO-D1 relay, step 2)
FRAME_LIST = "2025-10"                   # "drawn from the October 2025 list's active players"
PERIODS = [f"2025-{m:02d}" for m in range(1, 13)]
TOTAL = 2000
MIN_RATED = 1000                         # federations with at least 1,000 rated players on the frame list
ADDED_FEDS = ("ENG", "SCO", "WLS")       # plus England, Scotland and Wales
JUNIOR_BORN_FROM = 2007                  # juniors: born 2007 or later
NEWCOMER_FROM = "2023-01"                # newcomers: first rated 2023 or later
OVERSAMPLE = 3.0                         # a junior's or newcomer's weight in the draw, against 1 for others
BANDS = ((0, 1400, "below 1400"), (1400, 1600, "1400-1599"), (1600, 1800, "1600-1799"), (1800, 2000, "1800-1999"),
         (2000, 2200, "2000-2199"), (2200, 2400, "2200-2399"), (2400, 9999, "2400+"))
SEED = "ELO-D1"


def band_of(r: int) -> str:
    return next(lab for lo, hi, lab in BANDS if lo <= r < hi)


def month_add(m: str, k: int) -> str:
    y, mo = int(m[:4]), int(m[5:7]) - 1 + k
    return f"{y + mo // 12:04d}-{mo % 12 + 1:02d}"


def u01(tag: str) -> float:
    """A fixed pseudo-random number in (0, 1) from the SHA-256 of `tag`."""
    h = int(hashlib.sha256(tag.encode()).hexdigest()[:15], 16)
    return (h + 0.5) / 16 ** 15


def read_list(month: str) -> dict[str, tuple]:
    """FIDE ID -> (rating, games, K, birth year, federation, flag) of every rated player of a converted standard list."""
    out = {}
    with (LISTS / f"{month}.tsv").open(encoding="utf-8") as fh:
        next(fh)
        for line in fh:
            pid, r, g, k, by, _sex, fed, flag, _title = line.rstrip("\n").split("\t")
            if r.isdigit():
                out[pid] = (int(r), int(g) if g.isdigit() else 0, int(k) if k.isdigit() else 0,
                            int(by) if by.isdigit() else 0, fed, flag)
    return out


def rated_before(month: str) -> set[str]:
    """Every FIDE ID rated on a converted standard list before `month` (February 2015 onwards)."""
    seen: set[str] = set()
    for f in sorted(LISTS.glob("*.tsv")):
        if f.stem >= month:
            break
        with f.open(encoding="utf-8") as fh:
            next(fh)
            for line in fh:
                pid, r = line.split("\t", 2)[:2]
                if r.isdigit():
                    seen.add(pid)
    return seen


def plan() -> dict:
    frame_list = read_list(FRAME_LIST)
    lists = {m: read_list(m) for m in [month_add(PERIODS[0], -1)] + PERIODS}
    earlier = rated_before(NEWCOMER_FROM)
    rated = defaultdict(int)
    for pid, (_r, _g, _k, _by, fed, _flag) in frame_list.items():
        rated[fed] += 1
    feds = sorted({f for f, n in rated.items() if n >= MIN_RATED} | set(ADDED_FEDS))
    frame: dict[tuple, list] = defaultdict(list)
    for pid, (r, _g, _k, by, fed, flag) in frame_list.items():
        if fed not in feds or "i" in flag:
            continue
        periods = [p for p in PERIODS if pid in lists[p] and lists[p][pid][1] > 0 and pid in lists[month_add(p, -1)]]
        if not periods:
            continue
        junior = by >= JUNIOR_BORN_FROM
        newcomer = pid not in earlier
        frame[(fed, band_of(r))].append({"id": pid, "junior": junior, "newcomer": newcomer, "periods": periods})
    # equal shares by federation, the remainder to the largest frames
    size = {f: sum(len(v) for (ff, _b), v in frame.items() if ff == f) for f in feds}
    base, extra = divmod(TOTAL, len(feds))
    per_fed = {f: base for f in feds}
    for f in sorted(feds, key=lambda f: (-size[f], f))[:extra]:
        per_fed[f] += 1
    sample, cells = [], {}
    for f in feds:
        bands = [b for _lo, _hi, b in BANDS if frame.get((f, b))]
        alloc = allocate(per_fed[f], {b: len(frame[(f, b)]) for b in bands})
        for b in bands:
            pool = frame[(f, b)]
            w = {p["id"]: OVERSAMPLE if (p["junior"] or p["newcomer"]) else 1.0 for p in pool}
            # weighted sampling without replacement, the exponential race on fixed pseudo-random numbers
            order = sorted(pool, key=lambda p: (-math.log(u01(f"{SEED}:{p['id']}")) / w[p["id"]], p["id"]))
            chosen = order[:alloc[b]]
            for p in chosen:
                k = int(u01(f"{SEED}-period:{p['id']}") * len(p["periods"]))
                sample.append({"id": p["id"], "fed": f, "band": b, "junior": p["junior"], "newcomer": p["newcomer"],
                               "period": p["periods"][k], "weight": w[p["id"]]})
            cells[f"{f}|{b}"] = {
                "frame": len(pool), "frame_junior": sum(p["junior"] for p in pool),
                "frame_newcomer": sum(p["newcomer"] for p in pool),
                "frame_junior_or_newcomer": sum(p["junior"] or p["newcomer"] for p in pool),
                "frame_pages": sum(len(p["periods"]) for p in pool),
                "frame_pages_junior_or_newcomer": sum(len(p["periods"]) for p in pool if p["junior"] or p["newcomer"]),
                "sampled": len(chosen), "sampled_junior_or_newcomer": sum(p["junior"] or p["newcomer"] for p in chosen)}
    sample.sort(key=lambda s: (s["period"], int(s["id"])))
    return {"frame_list": FRAME_LIST, "periods": [PERIODS[0], PERIODS[-1]], "total": TOTAL, "federations": feds,
            "rated_by_federation": {f: rated[f] for f in feds}, "per_federation": per_fed, "oversample": OVERSAMPLE,
            "junior_born_from": JUNIOR_BORN_FROM, "newcomer_from": NEWCOMER_FROM, "bands": [b for *_x, b in BANDS],
            "cells": cells, "sample": sample}


def allocate(n: int, sizes: dict[str, int]) -> dict[str, int]:
    """n draws across a federation's level bands: in proportion to the square root of each band's frame, at least one
    in every band while n allows, never more than the band holds; largest remainders, ties by band order."""
    out = {b: 0 for b in sizes}
    left = n
    for b in sizes:                                   # one in every band first, from the floor up
        if left and sizes[b]:
            out[b], left = 1, left - 1
    while left:
        room = {b: sizes[b] - out[b] for b in sizes if sizes[b] > out[b]}
        if not room:
            break
        root = {b: math.sqrt(sizes[b]) for b in room}
        tot = sum(root.values())
        want = {b: left * root[b] / tot for b in room}
        add = {b: min(room[b], int(want[b])) for b in room}
        if not sum(add.values()):                     # the remainders, largest first
            for b in sorted(room, key=lambda b: (-(want[b] - int(want[b])), list(sizes).index(b)))[:left]:
                add[b] = 1
        for b, k in add.items():
            out[b] += k
            left -= k
    return out


# ------------------------------------------------------------------ fetching
def log_line(stamp: str, url: str, status: str, body: bytes, item: str) -> None:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    new = not LOG.exists()
    p = urllib.parse.urlparse(url)
    with LOG.open("a", encoding="utf-8") as fh:
        if new:
            fh.write("fetched_utc\thost\tpath\tstatus\tbytes\tsha256\turl\titem\n")
        path = p.path + (f"?{p.query}" if p.query else "")
        digest = hashlib.sha256(body).hexdigest() if body else "-"
        fh.write(f"{stamp}\t{p.netloc}\t{path}\t{status}\t{len(body)}\t{digest}\t{url}\t{item}\n")


def robots_read(host: str) -> Path | None:
    hits = sorted(ROBOTS.glob(f"robots_{host}_*.txt"))
    return hits[-1] if hits else None


def allowed(url: str) -> bool:
    """The host's robots.txt, read this session, obeyed (a 404 or an HTML error page means no rules)."""
    host = politeness.host_of(url)
    f = robots_read(host)
    if f is None:
        raise SystemExit(f"refusing {url}: robots.txt of {host} not read yet (mode robots)")
    status = f.stem.rsplit("_", 1)[-1]
    if not status.isdigit() or int(status) >= 500:    # robots.txt unreachable: nothing is fetched from the host
        return False
    text = f.read_text(encoding="utf-8", errors="replace")
    if int(status) >= 400 or "<html" in text.lower():  # no robots.txt (a 4xx or an HTML error page): no rules
        return True
    path = urllib.parse.urlparse(url).path or "/"
    rules, applies = [], False
    for line in text.splitlines():
        line = line.split("#")[0].strip()
        if not line or ":" not in line:
            continue
        key, val = (s.strip() for s in line.split(":", 1))
        if key.lower() == "user-agent":
            applies = val == "*" or val.lower() in politeness.USER_AGENT.lower()
        elif applies and key.lower() in ("disallow", "allow") and val:
            rules.append((key.lower(), val))
    best = ("allow", "")
    for kind, val in rules:
        pat = re.escape(val).replace(r"\*", ".*").replace(r"\$", "$")
        if re.match(pat, path) and len(val) > len(best[1]):
            best = (kind, val)
    return best[0] == "allow"


class Refused(Exception):
    pass


def site_of(host: str) -> str:
    """FIDE's hosts count as one site for the gap (from 09:34 UTC on 14 October 2026): fide.com and every *.fide.com."""
    return "fide.com" if host == "fide.com" or host.endswith(".fide.com") else host


def last_on_site(site: str) -> float:
    """An upper bound, as epoch seconds, of the last request to any host of `site` that any manifest or log records."""
    last = 0.0
    for path in politeness.MANIFESTS:
        if not path.exists():
            continue
        with path.open(encoding="utf-8") as fh:
            for r in csv.DictReader(fh, delimiter="\t"):
                if site_of(politeness.host_of(r.get("url") or "")) == site:
                    t = datetime.strptime(r["fetched_utc"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                    last = max(last, t.timestamp() + 1)
    return last


def request(url: str, item: str, gap: float, headers: dict | None = None, last: float | None = None) -> tuple:
    """One request, sent no sooner than `gap` seconds (at least the host's gap, four seconds for FIDE) after the last
    request to the same site in this run or in any manifest or log."""
    host = politeness.host_of(url)
    before = max(last_on_site(site_of(host)), last or 0.0)
    delay = before + max(gap, politeness.gap_for(host)) - time.time()
    if delay > 0:
        time.sleep(delay)
    req = urllib.request.Request(url, headers=politeness.headers(headers))
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    sent = time.time()
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            status, body = resp.status, resp.read()
    except urllib.error.HTTPError as exc:
        body = exc.read() if hasattr(exc, "read") else b""
        log_line(stamp, url, str(exc.code), body, item)
        return exc.code, body, sent, stamp
    except Exception as exc:                          # timeouts, resets
        log_line(stamp, url, f"error:{type(exc).__name__}", b"", item)
        return None, b"", sent, stamp
    log_line(stamp, url, str(status), body, item)
    return status, body, sent, stamp


def robots(host: str) -> int:
    ROBOTS.mkdir(parents=True, exist_ok=True)
    url = f"https://{host}/robots.txt"
    status, body, _sent, stamp = request(url, f"robots {host}", politeness.gap_for(host))
    out = ROBOTS / f"robots_{host}_{stamp.replace(':', '').replace('-', '')}_{status}.txt"
    out.write_bytes(body)
    print(f"{host}: HTTP {status}, {len(body)} bytes at {stamp} -> {out.relative_to(ROOT)}")
    return 0


def get(url: str, name: str) -> int:
    PAGES.mkdir(parents=True, exist_ok=True)
    out = PAGES / name
    if out.exists():
        print(f"cached: {out.relative_to(ROOT)}")
        return 0
    if not allowed(url):
        print(f"DISALLOWED by robots.txt: {url}")
        return 1
    status, body, _sent, stamp = request(url, f"get {name}", politeness.gap_for(politeness.host_of(url)))
    if status == 200:
        out.write_bytes(body)
    else:
        (PAGES / f"refused_{name}").write_bytes(body)
    print(f"{url}: HTTP {status}, {len(body)} bytes at {stamp}")
    return 0 if status == 200 else 1


def cached_path(kind: str, arg: str) -> Path:
    if kind == "calc":
        pid, period = arg.split(":")
        return CALCS / f"{pid}_{period}.html"
    if kind == "get":
        return PAGES / arg.split(" ", 1)[1]
    return REPORTS / f"{arg}.html"


def check_lock(kind: str, arg: str) -> None:
    if kind == "calc":
        period = arg.split(":")[1]
        if period > LAST_LIST:
            raise SystemExit(f"refusing calc {arg}: after the October 2026 list")
    elif kind == "get":
        if LOCKED_NAME.search(urllib.parse.unquote(arg)):
            raise SystemExit(f"refusing get {arg}: a 2026 U.S. Championship")
    elif kind == "report":
        meta = report_events_known().get(arg)
        if meta is None or meta["end"] >= LOCK_END or LOCKED_NAME.search(meta["name"]):
            raise SystemExit(f"refusing report {arg}: not an event of the pilot's pages ended before {LOCK_END}, or "
                             "a 2026 U.S. Championship")


def next_item(done: set[str]) -> str | None:
    for q in (QUEUE_PRIORITY, QUEUE_FILE[0]):
        if q is None or not q.exists():
            continue
        for line in q.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and line not in done:
                return line
    return None


QUEUE_FILE: list[Path | None] = [None]


def run(queue: str, club: bool = False, status: Path | None = None) -> int:
    QUEUE_FILE[0] = Path(queue)
    CALCS.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    gap, refusals, streak, last, n, done = 4.0, 0, 0, None, 0, set()
    t0 = time.time()
    next_status = t0 + 3600
    if status:
        write_status(status, queue, t0, n, "running")
    while True:
        if status and time.time() >= next_status:
            write_status(status, queue, t0, n, "running")
            next_status += 3600
        line = next_item(done)
        if line is None:
            break
        kind, arg = line.split(" ", 1)
        if kind not in ("calc", "report", "get"):
            raise SystemExit(f"unknown item {line!r}")
        out = cached_path(kind, arg)
        if out.exists():                              # cached once, never fetched again
            done.add(line)
            continue
        if club:
            check_lock_club(kind, arg)
            if requests_logged() >= CLUB_CAP:
                print(f"STOP: the cap of {CLUB_CAP} requests in {LOG.name} is reached", flush=True)
                if status:
                    write_status(status, queue, t0, n, f"STOPPED: the cap of {CLUB_CAP} requests is reached")
                return 1
        check_lock(kind, arg)
        if kind == "calc":
            pid, period = arg.split(":")
            url = CALC_URL.format(id=pid, period=period)
            headers = {"X-Requested-With": "XMLHttpRequest", "Referer": CALC_REFERER.format(id=pid, period=period)}
        elif kind == "get":
            url, headers = arg.split(" ", 1)[0], None
        else:
            url, headers = REPORT_URL.format(event=arg), None
        if not allowed(url):
            print(f"DISALLOWED by robots.txt: {url}", flush=True)
            done.add(line)
            continue
        status, body, last, stamp = request(url, line, gap, headers, last)
        n += 1
        text = body.decode("utf-8-sig", "replace")
        if status == 403 or (status == 200 and any(s in text for s in BLOCKED)):
            (BASE / f"refused_{kind}_{arg.replace(':', '_')}.html").write_bytes(body)
            print(f"STOP {line}: HTTP {status}, {len(body)} bytes, looks like a block, at {stamp}", flush=True)
            if status:
                write_status(status, queue, t0, n, f"STOPPED: HTTP {status} at {stamp}, a page that looks like a block")
            return 1
        if status is None or status == 429 or status >= 500:
            refusals += 1
            streak = 0
            gap = min(gap * 2, MAX_GAP)
            print(f"REFUSED {line}: HTTP {status} at {stamp}; gap now {gap:.0f} s ({refusals} in a row)", flush=True)
            if refusals >= MAX_REFUSALS:
                print(f"STOP: {refusals} refusals in a row; the route is stopped", flush=True)
                if status:
                    write_status(status, queue, t0, n, f"STOPPED: {refusals} refusals in a row, the last at {stamp}")
                return 1
            continue
        refusals = 0
        if status != 200:                             # a page not served (404 and the like): recorded, not retried
            (BASE / f"status{status}_{kind}_{arg.replace(':', '_')}.html").write_bytes(body)
            done.add(line)
            print(f"NOTE {line}: HTTP {status} at {stamp}", flush=True)
            continue
        out.write_bytes(body)
        done.add(line)
        streak += 1
        if gap > 4.0 and streak >= 100:               # after 100 answers in a row the doubled gap is halved again
            gap, streak = max(4.0, gap / 2), 0
        if n % 50 == 0:
            print(f"{n} requests, last {line} at {stamp}, {(time.time() - t0) / n:.2f} s a request", flush=True)
    print(f"done: {n} requests in {time.time() - t0:.0f} s", flush=True)
    if status:
        write_status(status, queue, t0, n, "done")
    return 0


# ------------------------------------------------------------------ the probe's events
def report_events_known(period: str | None = None) -> dict[str, dict]:
    """Every event of the pilot's cached pages (of one rating period, if given): its name and dates as printed."""
    out = {}
    for f in sorted(CALCS.glob(f"*_{period}.html" if period else "*.html")):
        text = f.read_text(encoding="utf-8-sig", errors="replace")
        for b in re.split(r'<div class="rtng_line01"><a href=/report\.phtml\?event=', text)[1:]:
            ev = re.match(r"(\d+)", b).group(1)
            name = re.search(r"class=head1>(.*?)</a>", b, re.S)
            dates = re.findall(r'<span class="dates_span">([0-9-]+)</span>', b)
            out[ev] = {"name": name.group(1).strip() if name else "", "start": dates[0] if dates else "",
                       "end": dates[1] if len(dates) > 1 else (dates[0] if dates else "9999")}
    return out


PROBE_PERIOD = "2025-01"                 # the probe draws its events from the pilot's pages of the January 2025 period


def report_events(n: int) -> None:
    known = report_events_known(PROBE_PERIOD)
    ok = [e for e, m in known.items() if m["end"] < LOCK_END and not LOCKED_NAME.search(m["name"])]
    ok.sort(key=lambda e: hashlib.sha256(f"{SEED}-report:{e}".encode()).hexdigest())
    for e in ok[:n]:
        print(f"report {e}")


# ------------------------------------------------------------------ session ELO-D2: the club-level sample
CLUB_LOG = ROOT / "data" / "fetch_log" / "ELO-D2.tsv"
CLUB_PLAN = BASE / "club_plan.json"
CLUB_QUEUE = BASE / "club_queue.txt"
CLUB_ALLOCATION = ROOT / "analysis" / "aggregates" / "E21_club_plan.json"     # committed before the fetch, totals only
CLUB_SEED = "ELO-D2"
CLUB_YEAR = 2025                         # 2025 rating periods only (the ELO-D2 relay)
CLUB_JUNIOR_MAX_AGE = 19                 # juniors as E6 defines them: list year minus year of birth at most 19
CLUB_NEWCOMER_FROM = "2023-01"           # newcomers: first rated on a list from January 2023
CLUB_BANDS = ((1400, 1600, "1400-1599"), (1600, 1800, "1600-1799"), (1800, 2000, "1800-1999"),
              (2000, 2200, "2000-2199"), (2200, 9999, "2200+"))
CLUB_GROUPS = ("junior", "newcomer", "other")
CLUB_CAP = 5500                          # the hard cap on requests in the session's log


def club_band(r: int) -> str | None:
    """The level band of the October 2025 list's rating, or None below 1400."""
    return next((lab for lo, hi, lab in CLUB_BANDS if lo <= r < hi), None)


def club_group(birth_year: int, first: str | None, band: str) -> str:
    """Junior (E6: list year minus year of birth at most 19), else newcomer (first rated from January 2023), else
    other; at 2200 or more newcomers are too few to stand apart and are drawn with the others."""
    if birth_year and CLUB_YEAR - birth_year <= CLUB_JUNIOR_MAX_AGE:
        return "junior"
    if first is not None and first >= CLUB_NEWCOMER_FROM and band != "2200+":
        return "newcomer"
    return "other"


def first_rated() -> dict[str, str]:
    """FIDE ID -> the first converted standard list (from February 2015) that rates the player."""
    first: dict[str, str] = {}
    for f in sorted(LISTS.glob("*.tsv")):
        with f.open(encoding="utf-8") as fh:
            next(fh)
            for line in fh:
                pid, r = line.split("\t", 2)[:2]
                if r.isdigit() and pid not in first:
                    first[pid] = f.stem
    return first


def club_frame() -> dict:
    """The frame of SPEC-SOURCING v1.1 §2, as the pilot's: the October 2025 list's active players of the pilot's 75
    federations (every federation with at least 1,000 rated players on that list, plus England, Scotland and Wales),
    each with the 2025 periods in which the list shows games and the player was rated on the list before. Returns the
    federations and, per stratum (level band, group), the players with their periods, first list and year of birth."""
    frame_list = read_list(FRAME_LIST)
    lists = {m: read_list(m) for m in [month_add(PERIODS[0], -1)] + PERIODS}
    first = first_rated()
    rated: dict[str, int] = defaultdict(int)
    for _pid, (_r, _g, _k, _by, fed, _flag) in frame_list.items():
        rated[fed] += 1
    feds = sorted({f for f, n in rated.items() if n >= MIN_RATED} | set(ADDED_FEDS))
    strata: dict[str, list] = defaultdict(list)
    for pid, (r, _g, _k, by, fed, flag) in frame_list.items():
        if fed not in feds or "i" in flag:
            continue
        periods = [p for p in PERIODS if pid in lists[p] and lists[p][pid][1] > 0 and pid in lists[month_add(p, -1)]]
        band = club_band(r)
        if not periods or band is None:
            continue
        group = club_group(by, first.get(pid), band)
        strata[f"{band}|{group}"].append({"id": pid, "fed": fed, "periods": periods, "first": first.get(pid),
                                          "birth": by or None,
                                          "games": [lists[p][pid][1] for p in periods]})
    return {"federations": feds, "strata": dict(strata)}


def club_plan() -> dict:
    """The sample: in each stratum, the committed number of players drawn without replacement, all with equal chance
    (the exponential race on fixed pseudo-random numbers, seed ELO-D2), each with one of the player's 2025 periods
    drawn at random among them; one page per player."""
    alloc = json.loads(CLUB_ALLOCATION.read_text(encoding="utf-8"))["allocation"]["pages"]
    fr = club_frame()
    sample, cells = [], {}
    for st in sorted(fr["strata"]):
        pool = fr["strata"][st]
        take = alloc.get(st, 0)
        if take > len(pool):
            raise SystemExit(f"stratum {st}: {take} pages allocated, {len(pool)} players in the frame")
        order = sorted(pool, key=lambda p: (-math.log(u01(f"{CLUB_SEED}:{p['id']}")), p["id"]))
        for p in order[:take]:
            k = int(u01(f"{CLUB_SEED}-period:{p['id']}") * len(p["periods"]))
            sample.append({"id": p["id"], "fed": p["fed"], "stratum": st, "period": p["periods"][k],
                           "periods": len(p["periods"]), "first": p["first"], "birth": p["birth"]})
        cells[st] = {"frame_players": len(pool), "frame_pages": sum(len(p["periods"]) for p in pool),
                     "frame_player_games": sum(sum(p["games"]) for p in pool), "sampled": take}
    sample.sort(key=lambda s: (s["period"], int(s["id"])))
    return {"seed": CLUB_SEED, "frame_list": FRAME_LIST, "federations": fr["federations"], "cells": cells,
            "sample": sample}


def check_lock_club(kind: str, arg: str) -> None:
    """The ELO-D2 lock: calculation pages of 2025 rating periods only."""
    if kind != "calc" or not arg.split(":")[1].startswith(f"{CLUB_YEAR}-"):
        raise SystemExit(f"refusing {kind} {arg}: the club-level run takes calculation pages of 2025 periods only")


def requests_logged() -> int:
    """Requests in the session's log so far."""
    if not LOG.exists():
        return 0
    with LOG.open(encoding="utf-8") as fh:
        return max(0, sum(1 for _ in fh) - 1)


def write_status(path: Path, queue: str, t0: float, n: int, state: str) -> None:
    """The run's status for the operator: pages done, games on them, errors, the smallest gap between requests to
    FIDE's site in the session's log (whole seconds, as logged) and the estimated finish; COMPLETE as the last line
    once the queue is done. Counts only: no player is named."""
    items = [x.strip() for x in Path(queue).read_text(encoding="utf-8").splitlines() if x.strip()]
    done = [x for x in items if cached_path(*x.split(" ", 1)).exists()]
    games = 0
    for x in done:
        text = cached_path(*x.split(" ", 1)).read_text(encoding="utf-8-sig", errors="replace")
        games += len(re.findall(r'<tr bgcolor=#efefef>', text))
    rows = list(csv.DictReader(LOG.open(encoding="utf-8"), delimiter="\t")) if LOG.exists() else []
    stamps = sorted(datetime.strptime(r["fetched_utc"], "%Y-%m-%dT%H:%M:%SZ") for r in rows
                    if site_of(r["host"]) == "fide.com")
    gaps = [(b - a).total_seconds() for a, b in zip(stamps, stamps[1:])]
    errors = sum(1 for r in rows if r["status"] != "200")
    pace = (time.time() - t0) / n if n else None
    left = len(items) - len(done)
    eta = (datetime.now(timezone.utc).timestamp() + left * pace) if pace else None
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    lines = ["Status: DRAFT (session ELO-D2, the club-level fetch; counts only, no player named)", "",
             f"# ELO-D2 fetch status — {now}", "",
             f"- State: {state}",
             f"- Pages done: {len(done):,} of {len(items):,} in the queue ({left:,} left)",
             f"- Game rows on the pages done: {games:,}",
             f"- Requests in {LOG.name}: {len(rows):,} (cap {CLUB_CAP:,}); not HTTP 200: {errors}",
             f"- Smallest gap between requests to FIDE's site in the log: "
             f"{min(gaps):.0f} s; gaps under 4 s: {sum(1 for g in gaps if g < 4)}" if gaps else
             "- Smallest gap: — (fewer than two requests)",
             f"- Pace this run: {pace:.2f} s a request" if pace else "- Pace this run: —",
             "- Estimated finish: " + (datetime.fromtimestamp(eta, timezone.utc).strftime("%Y-%m-%dT%H:%MZ")
                                       if eta and left else "—")]
    if state == "done" and not left:
        lines.append("")
        lines.append("COMPLETE")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1].startswith("club-"):
        LOG = CLUB_LOG
    if len(sys.argv) == 2 and sys.argv[1] == "club-robots":
        sys.exit(robots("ratings.fide.com"))
    elif len(sys.argv) == 2 and sys.argv[1] == "club-plan":
        p = club_plan()
        BASE.mkdir(parents=True, exist_ok=True)
        CLUB_PLAN.write_text(json.dumps(p, indent=1, sort_keys=True), encoding="utf-8")
        CLUB_QUEUE.write_text("".join(f"calc {s['id']}:{s['period']}\n" for s in p["sample"]), encoding="utf-8")
        print(f"{len(p['sample'])} pages planned in {len(p['cells'])} strata -> {CLUB_QUEUE.relative_to(ROOT)}")
    elif len(sys.argv) == 4 and sys.argv[1] == "club-run":
        sys.exit(run(sys.argv[2], club=True, status=Path(sys.argv[3]).expanduser()))
    elif len(sys.argv) >= 2 and sys.argv[1] == "plan":
        p = plan()
        BASE.mkdir(parents=True, exist_ok=True)
        PLAN.write_text(json.dumps(p, indent=1, sort_keys=True), encoding="utf-8")
        QUEUE.write_text("".join(f"calc {s['id']}:{s['period']}\n" for s in p["sample"]), encoding="utf-8")
        print(f"{len(p['sample'])} pages planned, {len(p['federations'])} federations -> {QUEUE.relative_to(ROOT)}")
    elif len(sys.argv) == 3 and sys.argv[1] == "robots":
        sys.exit(robots(sys.argv[2]))
    elif len(sys.argv) == 4 and sys.argv[1] == "get":
        sys.exit(get(sys.argv[2], sys.argv[3]))
    elif len(sys.argv) == 3 and sys.argv[1] == "run":
        sys.exit(run(sys.argv[2]))
    elif len(sys.argv) == 3 and sys.argv[1] == "report-events":
        report_events(int(sys.argv[2]))
    else:
        raise SystemExit(__doc__)
