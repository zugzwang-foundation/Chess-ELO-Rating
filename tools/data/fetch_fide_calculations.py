#!/usr/bin/env python3
"""Fetch FIDE's published per-player rating calculations and parse them into fixture records.

FIDE publishes, for each player and rating period, the calculation behind the
change on the list (https://ratings.fide.com/calculations.phtml; the data come
from /a_indv_calculation.php, which answers only requests that carry the AJAX
headers the page itself sends). This tool fetches one calculation at a time, at
least DELAY seconds apart, and parses it into the record format of
tests/fixtures/fide_calculator/published_calculations.json: per tournament the
event, place, dates, Rc, Ro, w, n, chg, K and K*chg; per game the colour, the
opponent's rating as FIDE used it, the capped marker, the score, chg, K and
K*chg. Opponents' names are never recorded. Only adults are recorded (year of
birth 2007 or earlier, the rule of the existing fixtures).

Modes:
  select PERIOD [PERIOD ...]   print candidates from the converted lists in
      data/interim/fide/standard/ (needs data/): adults with K 10 or 20 on the
      previous list and at least MIN_GAMES rated games in the period, ordered by
      the SHA-256 of "PERIOD:ID" (a fixed pseudo-random order), PER_PERIOD each.
  fetch ID:PERIOD [ID:PERIOD ...]  fetch and print one JSON record per line
      (raw responses are kept under data/raw/fide_calculations/, never committed).
  select-cross FIRST LAST  print candidates whose period holds an event that
      started under an earlier list (needs data/): players of Lichess broadcast
      tours (data/interim/broadcast/) that start in month A and end in month A+1,
      so that the tour is rated on list A+2 with the list of month A (SPEC-L0
      R-11a), who also played another rated game in that period (more games on
      list A+2 than in the tour), adults with K 10 or 20 on list A+1, periods
      FIRST..LAST, in the SHA-256 order of "PERIOD:ID", at most PER_CROSS.
  assemble FETCHED.jsonl [FETCHED.jsonl ...]  print the fixture file
      tests/fixtures/fide_calculator/published_multi_event_periods.json (needs
      data/): every fetched period with two or more tournaments, with the single
      list values needed to check it (the player's rating on the previous list,
      on the list of the period and on the list in force at each event's start;
      the K of the previous list; the games of the period; the year of birth),
      the period's change rounded once and rounded per tournament, and which of
      the two the published list follows.

Python standard library only.
"""
from __future__ import annotations

import functools
import hashlib
import html
import json
import re
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw" / "fide_calculations"
URL = "https://ratings.fide.com/a_indv_calculation.php?id_number={id}&rating_period={period}-01&t=0"
REFERER = "https://ratings.fide.com/calculations.phtml?id_number={id}&period={period}-01&rating=0"
DELAY = 10.0
MIN_GAMES = 12
PER_PERIOD = 10
PER_CROSS = 40
ADULT_BORN_BY = 2007


def prev_month(period: str) -> str:
    y, m = map(int, period.split("-"))
    return f"{y - 1}-12" if m == 1 else f"{y:04d}-{m - 1:02d}"


@functools.lru_cache(maxsize=None)
def load_list(period: str) -> dict[str, tuple]:
    out = {}
    with (ROOT / "data" / "interim" / "fide" / "standard" / f"{period}.tsv").open() as fh:
        next(fh)
        for line in fh:
            pid, r, g, k, by, *_ = line.rstrip("\n").split("\t")
            if r.isdigit():
                out[pid] = (int(r), int(g) if g.isdigit() else 0, int(k) if k.isdigit() else 0, int(by) if by.isdigit() else 0)
    return out


def select(periods: list[str]) -> None:
    for period in periods:
        cur, prev = load_list(period), load_list(prev_month(period))
        cands = [pid for pid, (r, g, k, by) in cur.items()
                 if g >= MIN_GAMES and pid in prev and prev[pid][2] in (10, 20) and 0 < by <= ADULT_BORN_BY]
        cands.sort(key=lambda pid: hashlib.sha256(f"{period}:{pid}".encode()).hexdigest())
        for pid in cands[:PER_PERIOD]:
            print(f"{pid}:{period}")


def month_shift(period: str, k: int) -> str:
    y, m = map(int, period.split("-"))
    n = y * 12 + m - 1 + k
    return f"{n // 12:04d}-{n % 12 + 1:02d}"


def select_cross(first: str, last: str) -> None:
    tours: dict[str, list] = {}
    for f in sorted((ROOT / "data" / "interim" / "broadcast").glob("*.tsv")):
        with f.open() as fh:
            cols = fh.readline().rstrip("\n").split("\t")
            ix = {c: i for i, c in enumerate(cols)}
            for line in fh:
                v = line.rstrip("\n").split("\t")
                d = v[ix["date"]] if re.fullmatch(r"\d{4}\.\d\d\.\d\d", v[ix["date"]]) else ""
                if not d:
                    continue
                d = d.replace(".", "-")
                tr = tours.setdefault(v[ix["tour"]], [d, d, {}])
                tr[0], tr[1] = min(tr[0], d), max(tr[1], d)
                for pid in (v[ix["white_fide_id"]], v[ix["black_fide_id"]]):
                    if pid.isdigit():
                        tr[2][pid] = tr[2].get(pid, 0) + 1
    cands = set()
    for start, end, players in tours.values():
        a, b = start[:7], end[:7]
        if b != month_shift(a, 1) or (int(end[8:]) + 31 - int(start[8:])) > 30:
            continue
        period = month_shift(a, 2)
        if not (first <= period <= last):
            continue
        cur, base = load_list(period), load_list(month_shift(a, 1))
        for pid, n in players.items():
            if pid in cur and pid in base and base[pid][2] in (10, 20) and 0 < cur[pid][3] <= ADULT_BORN_BY and cur[pid][1] > n:
                cands.add(f"{pid}:{period}")
    for c in sorted(cands, key=lambda c: hashlib.sha256(c.split(":")[1].encode() + b":" + c.split(":")[0].encode()).hexdigest())[:PER_CROSS]:
        print(c)


def cells(row: str) -> list[str]:
    return [html.unescape(re.sub(r"<[^>]+>", "", c)).replace("\xa0", " ").strip()
            for c in re.findall(r"<td[^>]*>(.*?)</td>", row, re.S)]


def parse(text: str) -> dict:
    total = re.search(r"Total change:&nbsp;<b>([^<]*)</b>", text)
    blocks = re.split(r'<div class="rtng_line01"><a href=/report\.phtml\?event=', text)[1:]
    tournaments = []
    for b in blocks:
        event_id = int(re.match(r"(\d+)", b).group(1))
        name = html.unescape(re.search(r"class=head1>(.*?)</a>", b, re.S).group(1)).strip()
        place = html.unescape(re.search(r'<div class="rtng_line02"><strong>(.*?)</strong>', b, re.S).group(1)).strip()
        dates = re.findall(r'<span class="dates_span">([0-9-]+)</span>', b)
        summary = None
        games = []
        for r in re.findall(r"(<tr[^>]*>.*?</tr>)", b, re.S):
            c = cells(r)
            if 'bgcolor=#e6e6e6' in r and len(c) >= 10:
                summary = c
            elif ("white_note" in r or "black_note" in r) and len(c) >= 10:
                rating = c[3]
                games.append({"colour": "white" if "white_note" in r else "black",
                              "opponent_rating_used": rating.replace("*", "").strip(),
                              "capped_marker": "*" in rating,
                              "score": c[5], "chg": c[7], "K": c[8], "K_chg": c[9]})
        if summary is None:
            raise ValueError(f"no summary row in event {event_id}")
        tournaments.append({"event_id": event_id, "event": name, "place": place,
                            "start": dates[0] if dates else None, "end": dates[1] if len(dates) > 1 else None,
                            "Rc": summary[0], "Ro": summary[1], "w": summary[5], "n": summary[6],
                            "chg": summary[7], "K": summary[8], "K_chg": summary[9], "games": games})
    return {"total_change_shown": total.group(1).strip() if total else None, "tournaments": tournaments}


def fetch(pairs: list[str]) -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    for n, pair in enumerate(pairs):
        pid, period = pair.split(":")
        if n:
            time.sleep(DELAY)
        url = URL.format(id=pid, period=period)
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "X-Requested-With": "XMLHttpRequest",
                                                   "Referer": REFERER.format(id=pid, period=period)})
        stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = resp.read()
        (RAW / f"{pid}_{period}.html").write_bytes(body)
        rec = {"fide_id": int(pid), "rating_period": period, "url": url, "fetched_utc": stamp, "bytes": len(body)}
        try:
            rec.update(parse(body.decode("utf-8-sig", "replace")))
        except Exception as exc:                     # recorded, never silently dropped
            rec["parse_error"] = str(exc)
        print(json.dumps(rec, ensure_ascii=False), flush=True)


def round_fide(x: float) -> int:
    """Nearest whole number, 0.5 away from zero (FIDE §8.3.4), on two-decimal values."""
    c = round(abs(x) * 100)
    q, r = divmod(c, 100)
    v = q + (1 if r >= 50 else 0)
    return v if x >= 0 else -v


def list_in_force(day: str) -> str:
    return day[:7]


def assemble(paths: list[str]) -> None:
    lst = load_list
    cases, single = [], 0
    recs = [json.loads(line) for path in paths for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]
    for rec in recs:
        if rec.get("parse_error") or len(rec.get("tournaments", [])) < 2:
            single += 1
            continue
        pid, period = str(rec["fide_id"]), rec["rating_period"]
        prev = prev_month(period)
        months = sorted({prev, period} | {list_in_force(t["start"]) for t in rec["tournaments"]})
        ratings = {m: lst(m)[pid][0] for m in months if pid in lst(m)}
        by = lst(period)[pid][3] if pid in lst(period) else None
        if not by or by > ADULT_BORN_BY:
            single += 1
            continue
        k_chg = [float(t["K_chg"]) for t in rec["tournaments"]]
        per_period = round_fide(sum(k_chg))
        per_tournament = sum(round_fide(x) for x in k_chg)
        change = ratings[period] - ratings[prev]
        base_corr = any(int(t["Ro"]) != ratings.get(list_in_force(t["start"])) for t in rec["tournaments"])
        follows = ("both" if per_period == per_tournament == change else "period" if per_period == change
                   else "tournament" if per_tournament == change else "neither")
        cases.append({"fide_id": int(pid), "birth_year": by, "rating_period": period, "url": rec["url"],
                      "fetched_utc": rec["fetched_utc"], "published_list_ratings": ratings,
                      "published_list_k": {prev: lst(prev)[pid][2]}, "published_list_games": {period: lst(period)[pid][1]},
                      "total_change_shown": rec["total_change_shown"], "tournaments": rec["tournaments"],
                      "change_rounded_per_period": per_period, "change_rounded_per_tournament": per_tournament,
                      "published_change": change, "ro_differs_from_list_in_force": base_corr, "list_follows": follows})
    cases.sort(key=lambda c: (c["rating_period"], c["fide_id"]))
    for n, c in enumerate(cases, 1):
        c["id"] = f"F-M{n:02d}"
    out = {"source": "FIDE's published per-player rating calculations (ratings.fide.com/calculations.phtml, data endpoint "
                     "/a_indv_calculation.php), fetched with tools/data/fetch_fide_calculations.py",
           "fetched": f"{min(c['fetched_utc'] for c in cases)} to {max(c['fetched_utc'] for c in cases)}, one request at a time, "
                      f"at least {DELAY:.0f} s apart; adults only (born {ADULT_BORN_BY} or earlier); opponents identified by the rating "
                      "FIDE used, never by name",
           "selection": "two deterministic selections by tools/data/fetch_fide_calculations.py: 'select 2026-04 2026-06 2026-08 "
                        f"2026-10' (adults with K 10 or 20 on the previous standard list and at least {MIN_GAMES} rated games in the "
                        f"period, the first {PER_PERIOD} per period in the SHA-256 order of 'PERIOD:ID') and 'select-cross 2025-06 2026-09' "
                        "(adults of broadcast tours spanning a month boundary, whose period therefore holds an event that started under "
                        f"an earlier list, at most {PER_CROSS}); every fetched period with two or more tournaments is kept "
                        f"({len(cases)} of {len(recs)}; {single} had one tournament or failed the age check)",
           "list_values_note": "published_list_ratings, published_list_k and published_list_games are single values quoted from "
                               "FIDE's monthly standard lists for verification; the lists themselves are not redistributed",
           "cases": [{"id": c.pop("id"), **c} for c in cases]}
    print(json.dumps(out, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    if len(sys.argv) < 3 or sys.argv[1] not in ("select", "select-cross", "fetch", "assemble"):
        raise SystemExit(__doc__)
    if sys.argv[1] == "assemble":
        assemble(sys.argv[2:])
    elif sys.argv[1] == "select-cross":
        select_cross(sys.argv[2], sys.argv[3])
    else:
        (select if sys.argv[1] == "select" else fetch)(sys.argv[2:])
