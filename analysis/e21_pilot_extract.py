#!/usr/bin/env python3
"""E21, part 2: the pilot of FIDE's per-player game pages and the probe of FIDE's tournament reports, totals only
(session ELO-D1, step 6; needs data/).

The pages are the pilot's (tools/data/fetch_sourcing.py: 2,000 per-player calculation pages of 2025 standard periods,
drawn from the October 2025 list's active players of 75 federations, juniors and newcomers drawn three times as often),
read by E17's parser unchanged (analysis/e17_top100_extract.py, parse_page). Nothing about a sampled player leaves
data/: this script writes totals by federation, level band, age group and colour only, and no name, FIDE ID, event or
page. Every measure below was chosen after the pilot's first pages had been seen, and is labelled "pilot".

1. **The pages.** Pages planned, fetched and parsed; tournaments and games per page; game rows with a colour mark, an
   opponent's federation and an opponent's rating; the games on the page against the games column of FIDE's list for
   the same player and period; seconds per page, from the session's log (data/fetch_log/ELO-D1.tsv).
2. **Layer 0 against FIDE's printed figures**, on every page (FIDE's own inputs: the player's Ro, the opponent's rating
   as printed, K as printed; the rules in force at each tournament's start, src/layer0_history/): each game's change,
   each tournament's K x sum, the page's total, and the published change on the list (the rating of the period's list
   minus the list before), rounded once per period.
3. **Cross-border games**: the share of game rows whose opponent's federation differs from the player's, by federation
   and level, and overall with the design weights.
4. **First looks** (labelled "pilot"): White's score at near-equal ratings and White's edge from every game, by level;
   the favourite's score against table 8.1.2 by gap and level; adults' results against juniors (opponents identified
   by name, federation and rating on the list in force, as E17 identifies them, for their year of birth).
5. **The yield of a full fetch**: per federation and level, the pages and the player-games a fetch of every frame page
   of 2025 would bring (from FIDE's lists, checked against the pages), the cross-border player-games (the pilot's share
   applied), and the distinct games after the double count of games between two frame players is removed.
6. **The probe**: what FIDE's tournament reports give per request.

Weights: a sampled page stands for frame players / sampled players of its federation, level band and group (juniors
or newcomers, others), times the player's 2025 pages (the page was drawn at random among them). Intervals: 95 %,
clustered over pages (one page per player). Python standard library only.

Usage: python3 analysis/e21_pilot_extract.py > analysis/aggregates/E21_pilot.json
"""
from __future__ import annotations

import csv
import json
import math
import re
import sys
import zipfile
from collections import Counter, defaultdict
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for _sub in ("analysis", "tools", "tools/data", "src"):
    sys.path.insert(0, str(ROOT / _sub))
import convert_fide_lists as cfl  # noqa: E402  (the lists' fixed-width columns, for names)
import e17_top100_extract as ex  # noqa: E402  (FIDE's page parser and the name key, unchanged)
import fetch_sourcing as fs  # noqa: E402  (the pilot's plan, cache and log: one rule for fetch and analysis)
import layer0  # noqa: E402
import layer0_history as lh  # noqa: E402

RAW_LISTS = ROOT / "data" / "raw" / "fide" / "standard"
LABEL = "pilot"
GAP_BINS = ((0, 50, "0-49"), (50, 100, "50-99"), (100, 150, "100-149"), (150, 200, "150-199"), (200, 300, "200-299"),
            (300, 400, "300-399"), (400, 10000, "400+"))
LEVELS = tuple(lab for *_x, lab in fs.BANDS)
NEAR_EQUAL = 50
TARGET_CROSS = 300           # a smaller run's target: cross-border games per federation (E7's threshold)
FLOOR_PAGES = 200            # and at least this many pages per federation, raised in steps of 100 pages until the
TARGET_JUNIOR = 1000         # projected games of adults against juniors reach this in each level band below 2000
BELOW_2000 = ("1400-1599", "1600-1799", "1800-1999")      # the level bands from the floor to 2000
CAP_PAGES = 2000             # and at most this many: a federation whose games stay at home is not chased page by page
JUNIOR_BORN_FROM = fs.JUNIOR_BORN_FROM


def band_mid_level(r: float) -> str:
    return fs.band_of(int(r))


def gap_bin(g: int) -> str:
    return next(lab for lo, hi, lab in GAP_BINS if lo <= g < hi)


class Clustered:
    """A mean over game rows with a 95 % interval clustered over pages (sum of cluster residuals, as E20 does)."""

    def __init__(self) -> None:
        self.rows: dict[str, list[float]] = defaultdict(list)

    def add(self, cluster: str, x: float) -> None:
        self.rows[cluster].append(x)

    def summary(self, digits: int = 4) -> dict:
        n = sum(len(v) for v in self.rows.values())
        if not n:
            return {"games": 0}
        mean = sum(sum(v) for v in self.rows.values()) / n
        g = len(self.rows)
        resid = [sum(x - mean for x in v) for v in self.rows.values()]
        se = (sum(r * r for r in resid) * g / (g - 1)) ** 0.5 / n if g > 1 else 0.0
        return {"games": n, "pages": g, "mean": round(mean, digits), "lo": round(mean - 1.96 * se, digits),
                "hi": round(mean + 1.96 * se, digits)}


# ------------------------------------------------------------------ the plan, the pages, the lists
def load() -> dict:
    plan = json.loads(fs.PLAN.read_text(encoding="utf-8"))
    pages, errors = {}, Counter()
    for s in plan["sample"]:
        f = fs.CALCS / f"{s['id']}_{s['period']}.html"
        if not f.exists():
            continue
        text = f.read_text(encoding="utf-8-sig", errors="replace")
        try:
            pages[(s["id"], s["period"])] = ex.parse_page(text)
        except Exception as exc:                    # recorded, never dropped silently
            no_k = any(("white_note" in r or "black_note" in r) and len(ex.cells(r)) >= 10 and not ex.cells(r)[8]
                       for r in re.findall(r"(<tr[^>]*>.*?</tr>)", text, re.S))
            errors["game rows printed without K" if no_k else type(exc).__name__] += 1
    return {"plan": plan, "pages": pages, "parse_errors": errors}


def read_lists(months: list[str], want: set[str] | None) -> dict[str, dict]:
    out = {}
    for m in months:
        d = {}
        with (fs.LISTS / f"{m}.tsv").open(encoding="utf-8") as fh:
            next(fh)
            for line in fh:
                pid, r, g, k, by, _sex, fed, flag, _title = line.rstrip("\n").split("\t")
                if r.isdigit() and (want is None or pid in want):
                    d[pid] = (int(r), int(g) if g.isdigit() else 0, int(k) if k.isdigit() else 0,
                              int(by) if by.isdigit() and int(by) > 1900 else None, fed, flag)
        out[m] = d
    return out


def names_of(m: str, keys: set[str]) -> dict[str, list[tuple]]:
    """Name key -> [(FIDE ID, federation, rating)] on FIDE's list m, for the wanted keys (E20's index, one list)."""
    ratings = {}
    with (fs.LISTS / f"{m}.tsv").open(encoding="utf-8") as fh:
        next(fh)
        for line in fh:
            pid, r = line.split("\t", 2)[:2]
            if r.isdigit():
                ratings[pid] = int(r)
    tag = f"{cfl.MONTHS[int(m[5:]) - 1]}{m[2:4]}"
    with zipfile.ZipFile(RAW_LISTS / f"standard_{tag}frl.zip") as zf:
        raw = zf.read(zf.namelist()[0]).decode("latin-1").splitlines()
    sp = cfl.spans(raw[0], tag.upper())
    (ia, ib), (na, nb), (fa, fb) = sp["ID Number"], sp["Name"], sp["Fed"]
    idx: dict[str, list] = defaultdict(list)
    memo: dict[str, str] = {}
    for line in raw[1:]:
        pid = line[ia:ib].strip()
        if pid not in ratings:
            continue
        name = line[na:nb].strip()
        k = memo.get(name)
        if k is None:
            k = memo[name] = ex.norm(name)
        if k in keys:
            idx[k].append((pid, line[fa:fb].strip(), ratings[pid]))
    return idx


def list_in_force(start: str | None, period: str) -> str:
    """As E17: the list in force at the tournament's start, at most the list before the one that rates it."""
    prev = fs.month_add(period, -1)
    if not start:
        return prev
    return min(start[:7], prev)


def resolve(g: dict, ro: int, idx: dict) -> str | None:
    """The opponent's FIDE ID: the one player of the printed name key (with the printed federation, else any) whose
    rating on the list in force equals the printed one, or lies beyond it on the same side where FIDE marks a cap."""
    cands = idx.get(ex.norm(g["name"]), [])
    for pool in ([c for c in cands if c[1] == g["fed"]], cands):
        ok = {pid for pid, _f, r in pool
              if r == g["rating"] or (g["capped"] and ((r < g["rating"]) if g["rating"] < ro else (r > g["rating"])))}
        if len(ok) == 1:
            return next(iter(ok))
        if len(ok) > 1:
            return None
    return None


# ------------------------------------------------------------------ the frame, from FIDE's lists
def frame_totals(plan: dict) -> dict:
    """Per federation and level band of the frame (as the plan draws it): players, pages (player-periods with games in
    2025) and player-games, by group; and the same for every player of every federation with a 2025 page."""
    months = [fs.month_add(fs.PERIODS[0], -1)] + fs.PERIODS
    lists = read_lists(months + [fs.FRAME_LIST], None)
    earlier = fs.rated_before(fs.NEWCOMER_FROM)
    feds = set(plan["federations"])
    frame_list = lists[fs.FRAME_LIST]
    cell: dict = defaultdict(lambda: Counter())
    every = Counter()
    periods_of: dict[str, int] = {}
    for p in fs.PERIODS:
        prev = lists[fs.month_add(p, -1)]
        for pid, (_r, g, *_x) in lists[p].items():
            if g > 0 and pid in prev:
                every["pages"] += 1
                every["player_games"] += g
    for pid, (r, _g, _k, by, fed, flag) in frame_list.items():
        if fed not in feds or "i" in flag:
            continue
        per = [p for p in fs.PERIODS if pid in lists[p] and lists[p][pid][1] > 0 and pid in lists[fs.month_add(p, -1)]]
        if not per:
            continue
        periods_of[pid] = len(per)
        grp = "junior_or_newcomer" if ((by or 0) >= JUNIOR_BORN_FROM or pid not in earlier) else "other"
        c = cell[(fed, fs.band_of(r))]
        c[f"players_{grp}"] += 1
        c[f"pages_{grp}"] += len(per)
        c[f"player_games_{grp}"] += sum(lists[p][pid][1] for p in per)
    return {"cells": cell, "every": every, "periods_of": periods_of, "lists": lists}


# ------------------------------------------------------------------ the analysis
def main() -> int:
    c = load()
    plan, pages = c["plan"], c["pages"]
    sample = {(s["id"], s["period"]): s for s in plan["sample"]}
    fr = frame_totals(plan)
    lists = fr["lists"]
    out: dict = {"label": LABEL, "decided": "after seeing the pilot's first pages (docs/DECISIONS.md, item 32)",
                 "fixed_line": "Under this rule, with the same results — not anyone's true strength."}

    # weights: frame players over sampled players of the cell and group, times the player's 2025 pages
    sampled_n = Counter()
    for s in plan["sample"]:
        grp = "junior_or_newcomer" if (s["junior"] or s["newcomer"]) else "other"
        sampled_n[(s["fed"], s["band"], grp)] += 1
    weight = {}
    for key, s in sample.items():
        grp = "junior_or_newcomer" if (s["junior"] or s["newcomer"]) else "other"
        players = fr["cells"][(s["fed"], s["band"])][f"players_{grp}"]
        weight[key] = players / sampled_n[(s["fed"], s["band"], grp)] * fr["periods_of"].get(s["id"], 1)

    # 1. the pages
    log = list(csv.DictReader((fs.LOG).open(encoding="utf-8"), delimiter="\t"))
    calc_log = [r for r in log if r["item"].startswith("calc ")]
    times = sorted(datetime.strptime(r["fetched_utc"], "%Y-%m-%dT%H:%M:%SZ") for r in calc_log)
    per_page_games = []
    rows = Counter()
    list_match = Counter()
    for key, pg in pages.items():
        s = sample[key]
        g = sum(len(t["games"]) for t in pg["tournaments"])
        per_page_games.append(g)
        rows["tournaments"] += len(pg["tournaments"])
        rows["games"] += g
        rows["n_printed"] += sum(t["n"] for t in pg["tournaments"])
        rows["tournaments_games_equal_n"] += sum(1 for t in pg["tournaments"] if t["n"] == len(t["games"]))
        for t in pg["tournaments"]:
            for gm in t["games"]:
                rows["colour_mark"] += gm["mark"] in ("white", "black")
                rows["opponent_federation"] += bool(re.fullmatch(r"[A-Z]{3}", gm["fed"] or ""))
                rows["opponent_rating"] += gm["rating"] > 0
                rows["capped_mark"] += gm["capped"]
        lst = lists[s["period"]].get(s["id"])
        listed = lst[1] if lst else None
        list_match["pages"] += 1
        list_match["equal"] += listed == g
        list_match["page_more"] += listed is not None and g > listed
        list_match["page_fewer"] += listed is not None and g < listed
        list_match["games_on_pages"] += g
        list_match["games_on_lists"] += listed or 0
    srt = sorted(per_page_games)
    q = (lambda p: srt[min(len(srt) - 1, int(p * len(srt)))]) if srt else (lambda p: None)
    out["pages"] = {
        "planned": len(plan["sample"]), "fetched": sum(1 for s in plan["sample"]
                                                     if (fs.CALCS / f"{s['id']}_{s['period']}.html").exists()),
        "parsed": len(pages), "parse_errors": dict(c["parse_errors"]),
        "with_a_game": sum(1 for g in per_page_games if g), "tournaments": rows["tournaments"], "games": rows["games"],
        "games_per_page": {"mean": round(rows["games"] / len(pages), 2) if pages else None, "median": q(0.5),
                           "p90": q(0.9), "max": srt[-1] if srt else None},
        "game_rows": {k: rows[k] for k in ("colour_mark", "opponent_federation", "opponent_rating", "capped_mark",
                                           "n_printed", "tournaments_games_equal_n")},
        "page_against_list_games": dict(list_match),
        "requests": {"calc": len(calc_log), "statuses": dict(Counter(r["status"] for r in calc_log)),
                     # the runner's pace: every request of its to ratings.fide.com from its first page to its last
                     "seconds_per_request": round((times[-1] - times[0]).total_seconds() /
                                                  (sum(1 for r in log if r["host"] == "ratings.fide.com" and
                                                       times[0] <= datetime.strptime(r["fetched_utc"], "%Y-%m-%dT%H:%M:%SZ")
                                                       <= times[-1]) - 1), 2) if len(times) > 1 else None,
                     "bytes_per_page": round(sum(int(r["bytes"]) for r in calc_log) / len(calc_log)) if calc_log else None}}
    by_cell_games = defaultdict(list)
    for key, pg in pages.items():
        s = sample[key]
        by_cell_games[(s["fed"], s["band"])].append(sum(len(t["games"]) for t in pg["tournaments"]))
    out["pages"]["games_per_page_by_level"] = {
        lv: round(sum(sum(v) for (f, b), v in by_cell_games.items() if b == lv) /
                  max(1, sum(len(v) for (f, b), v in by_cell_games.items() if b == lv)), 2) for lv in LEVELS
        if any(b == lv for (f, b) in by_cell_games)}

    # 2. Layer 0 against FIDE's printed figures
    l0 = Counter()
    versions = Counter()
    for key, pg in pages.items():
        s = sample[key]
        total = Decimal(0)
        game_ok = True
        short_page = False
        for t in pg["tournaments"]:
            start = ex.d_of(t["start"]) if t["start"] else date.fromisoformat(f"{fs.month_add(s['period'], -1)}-01")
            versions[lh.version(start)] += 1
            d = lh.deltas(t["ro"], [(g["rating"], g["score"]) for g in t["games"]], start)
            for g, dl in zip(t["games"], d):
                l0["games"] += 1
                l0["game_change_equal"] += dl == g["chg"]
                game_ok &= dl == g["chg"]
            ts = sum(d, Decimal(0))
            l0["tournaments"] += 1
            l0["tournament_k_sum_equal"] += Decimal(t["k"]) * ts == t["k_chg"]
            if Decimal(t["k"]) * ts != t["k_chg"] and len(t["games"]) < t["n"]:
                l0["tournament_differs_a_row_unmarked"] += 1          # a game row without a colour mark is not read
                short_page = True
            total += Decimal(t["k"]) * ts
        l0["pages"] += 1
        if pg["tournaments"]:
            l0["pages_with_a_tournament"] += 1
            l0["page_total_equal"] += pg["total"] is not None and total == pg["total"]
            l0["page_total_differs_a_row_unmarked"] += short_page and total != pg["total"]
        else:
            l0["pages_without_a_tournament"] += 1
        prev, cur = lists[fs.month_add(s["period"], -1)].get(s["id"]), lists[s["period"]].get(s["id"])
        if prev and cur:
            l0["pages_on_both_lists"] += 1
            ok = prev[0] + layer0.round_change(total) == cur[0]
            l0["list_change_equal"] += ok
            if not ok:          # why the published change differs from the page's rounded total
                page_games = sum(len(t["games"]) for t in pg["tournaments"])
                if any(t["ro"] != prev[0] for t in pg["tournaments"]):
                    l0["list_differs_ro_not_previous_list"] += 1
                elif page_games != cur[1]:
                    l0["list_differs_page_games_not_list_games"] += 1
                else:
                    l0["list_differs_unexplained"] += 1
                    l0["list_differs_unexplained_k40"] += prev[2] == 40
                    l0["list_differs_unexplained_by_one"] += abs(cur[0] - prev[0] - layer0.round_change(total)) == 1
                    l0["list_differs_unexplained_junior_or_newcomer"] += s["junior"] or s["newcomer"]
    out["layer0"] = {**dict(l0), "rules_by_tournament_start": dict(versions)}

    # 3 and 4: opponents identified, cross-border shares, first looks
    needed: dict[str, set] = defaultdict(set)
    for key, pg in pages.items():
        for t in pg["tournaments"]:
            m = list_in_force(t["start"], key[1])
            for g in t["games"]:
                needed[m].add(ex.norm(g["name"]))
    index = {m: names_of(m, keys) for m, keys in sorted(needed.items())}
    opp_ids: dict[tuple, str | None] = {}
    for key, pg in pages.items():
        for ti, t in enumerate(pg["tournaments"]):
            m = list_in_force(t["start"], key[1])
            for gi, g in enumerate(t["games"]):
                opp_ids[(key, ti, gi)] = resolve(g, t["ro"], index[m])
    want = {i for i in opp_ids.values() if i}
    births = {}
    for m in sorted(set(index) | {fs.FRAME_LIST}):
        for pid, v in read_lists([m], want)[m].items():
            if v[3]:
                births.setdefault(pid, v[3])
    own_birth = {s["id"]: (lists[fs.FRAME_LIST].get(s["id"]) or (0, 0, 0, None))[3] for s in plan["sample"]}
    frame_ids = fr["periods_of"]

    xb_fed, xb_level, xb_cell = defaultdict(Counter), defaultdict(Counter), defaultdict(Counter)
    proj_cal, proj_near, proj_aj = Counter(), Counter(), Counter()     # for the smaller run's projections
    xb_w = Counter()
    white_near = defaultdict(Clustered)
    edge = defaultdict(lambda: {"white": Clustered(), "black": Clustered()})
    fav = defaultdict(Clustered)
    vs = defaultdict(Clustered)
    ident = Counter()
    for key, pg in pages.items():
        s = sample[key]
        cl = f"{key[0]}:{key[1]}"
        by = own_birth.get(s["id"])
        me = "junior" if by and by >= JUNIOR_BORN_FROM else "adult" if by else "unknown"
        for ti, t in enumerate(pg["tournaments"]):
            for gi, g in enumerate(t["games"]):
                oid = opp_ids[(key, ti, gi)]
                ident["games"] += 1
                ident["opponent_identified"] += oid is not None
                ident["opponent_in_frame_with_that_period"] += bool(oid and oid in frame_ids and
                                                                    lists[key[1]].get(oid, (0, 0))[1] > 0 and
                                                                    oid in lists[fs.month_add(key[1], -1)])
                cross = g["fed"] != s["fed"]
                xb_cell[(s["fed"], s["band"])]["games"] += 1
                xb_cell[(s["fed"], s["band"])]["cross"] += cross
                xb_fed[s["fed"]]["games"] += 1
                xb_fed[s["fed"]]["cross"] += cross
                xb_level[s["band"]]["games"] += 1
                xb_level[s["band"]]["cross"] += cross
                xb_w["games"] += weight[key]
                xb_w["cross"] += weight[key] * cross
                sc = float(g["score"])
                own, opp = t["ro"], g["rating"]
                lev = band_mid_level((own + opp) / 2)
                white_score = sc if g["mark"] == "white" else 1 - sc
                if abs(own - opp) <= NEAR_EQUAL and not g["capped"]:
                    white_near[lev].add(cl, white_score)
                edge[s["band"]][g["mark"]].add(cl, float(g["chg"]))
                if not g["capped"]:
                    gap = abs(own - opp)
                    fav_score = sc if own > opp else 1 - sc if own < opp else 0.5 + (sc - 0.5) * 0  # equal: no favourite
                    if own != opp:
                        h = float(layer0.expected_score(gap))
                        fav[(lev, gap_bin(gap))].add(cl, fav_score - h)
                        fav[("every level", gap_bin(gap))].add(cl, fav_score - h)
                if not g["capped"] and abs(own - opp) < 400 and (own + opp) / 2 < 2000:
                    proj_cal[(s["fed"], f"{int((own + opp) / 2) // 100 * 100}|{abs(own - opp) // 50 * 50}")] += 1
                if abs(own - opp) <= NEAR_EQUAL and not g["capped"]:
                    proj_near[(s["fed"], lev)] += 1
                ob = births.get(oid) if oid else None
                them = "junior" if ob and ob >= JUNIOR_BORN_FROM else "adult" if ob else "unknown"
                if me == "adult" and them == "junior":
                    proj_aj[(s["fed"], s["band"])] += 1
                if me != "unknown" and them != "unknown":
                    vs[(me, them, s["band"])].add(cl, float(g["chg"]))
                    vs[(me, them, "every level")].add(cl, float(g["chg"]))
    out["opponents"] = dict(ident)
    out["cross_border"] = {
        "weighted_share": round(xb_w["cross"] / xb_w["games"], 4) if xb_w["games"] else None,
        "by_level": {lv: {"games": v["games"], "share": round(v["cross"] / v["games"], 4)}
                     for lv, v in sorted(xb_level.items())},
        "by_federation": {f: {"games": v["games"], "cross": v["cross"], "share": round(v["cross"] / v["games"], 4)}
                          for f, v in sorted(xb_fed.items())}}
    out["first_looks"] = {
        "white_score_near_equal": {"within_points": NEAR_EQUAL,
                                   **{lv: white_near[lv].summary() for lv in LEVELS if white_near[lv].rows}},
        "white_edge_every_game": {lv: white_edge(edge[lv]) for lv in LEVELS if edge[lv]["white"].rows},
        "favourite_minus_table_812": {f"{lev}|{gb}": v.summary() for (lev, gb), v in sorted(fav.items())},
        "results_by_age": {f"{a}|{b}|{lv}": v.summary() for (a, b, lv), v in sorted(vs.items())}}

    # 5. the yield of a full fetch of 2025, from the lists, with the pilot's shares: the cross-border share of each
    # federation and level band from a two-way model, additive in federation and level on the log-odds scale, fitted
    # to the pilot's game rows (every cell's rows, half a pseudo-row each way per federation)
    cells = fr["cells"]
    a, c = two_way(xb_cell, sorted({f for f, _b in cells}), LEVELS)
    share_cell = {(f, b): expit(a[f] + c.get(b, 0.0)) for (f, b) in cells}
    yield_fed, yield_level = defaultdict(Counter), defaultdict(Counter)
    for (f, b), v in cells.items():
        pages_n = v["pages_junior_or_newcomer"] + v["pages_other"]
        games_n = v["player_games_junior_or_newcomer"] + v["player_games_other"]
        for agg, k in ((yield_fed, f), (yield_level, b)):
            agg[k]["players"] += v["players_junior_or_newcomer"] + v["players_other"]
            agg[k]["pages"] += pages_n
            agg[k]["player_games"] += games_n
            agg[k]["cross_border_player_games"] += games_n * share_cell[(f, b)]
    both = ident["opponent_in_frame_with_that_period"] / ident["games"] if ident["games"] else 0.0
    ratio = list_match["games_on_pages"] / list_match["games_on_lists"] if list_match["games_on_lists"] else 1.0

    def finish(v: Counter) -> dict:
        # the counts are FIDE's; the cross-border and distinct games are estimates, given to the nearest hundred
        return {"players": v["players"], "pages": v["pages"], "player_games": v["player_games"],
                "cross_border_player_games": round(v["cross_border_player_games"], -2),
                "distinct_games": round(v["player_games"] * ratio * (1 - both / 2), -2)}
    tot = Counter()
    for v in yield_fed.values():
        tot.update(v)
    model_share = (sum(v["cross_border_player_games"] for v in yield_fed.values()) /
                   sum(v["player_games"] for v in yield_fed.values()))
    out["full_fetch_2025"] = {
        "cross_border_share_model": round(model_share, 4),
        "page_to_list_games_ratio": round(ratio, 4), "share_rows_with_opponent_also_in_frame": round(both, 4),
        "frame": finish(tot), "by_federation": {f: finish(v) for f, v in sorted(yield_fed.items())},
        "by_level": {lv: finish(yield_level[lv]) for lv in LEVELS if lv in yield_level},
        "every_rated_player": {"pages": fr["every"]["pages"], "player_games": fr["every"]["player_games"]}}

    # a smaller run: per federation, the pages that bring TARGET_CROSS cross-border player-games at the pilot's rate
    # (games per page and cross-border share of the federation's own pages), at most every frame page of 2025
    rate = defaultdict(lambda: [0, 0])
    for key, pg in pages.items():
        rate[sample[key]["fed"]][0] += 1
    def plan_for(floor: int) -> dict:
        out_ = {}
        for f, v in sorted(yield_fed.items()):
            n_pages = rate[f][0]
            per_page = xb_fed[f]["cross"] / n_pages if n_pages else 0.0
            games_page = xb_fed[f]["games"] / n_pages if n_pages else 0.0
            need = math.ceil(TARGET_CROSS / per_page) if per_page else CAP_PAGES
            take = min(max(need, floor), CAP_PAGES, v["pages"])
            out_[f] = {"cross_border_per_page": round(per_page, 3), "pages": take,
                       "player_games": round(take * games_page, -1),
                       "cross_border_player_games": round(take * per_page, -1),
                       "reaches_target": take * per_page >= TARGET_CROSS, "reaches_1000": take * per_page >= 1000}
        return out_

    def adults_juniors(plan_: dict) -> Counter:
        aj_ = Counter()
        for (f, b), k in proj_aj.items():
            aj_[b] += k * plan_[f]["pages"] / rate[f][0] if rate[f][0] else 0
        return aj_
    floors = {}
    for floor in range(FLOOR_PAGES, CAP_PAGES + 1, 100):
        pl_ = plan_for(floor)
        aj_ = adults_juniors(pl_)
        floors[floor] = {"pages": sum(x["pages"] for x in pl_.values()),
                         "adult_junior_below_2000": [round(aj_[b]) for b in BELOW_2000]}
        if all(aj_[b] >= TARGET_JUNIOR for b in BELOW_2000):
            break
    floor = max(floors)
    smaller = plan_for(floor)
    scale = {f: smaller[f]["pages"] / rate[f][0] for f in smaller if rate[f][0]}
    cal = Counter()
    for (f, cell), k in proj_cal.items():
        cal[cell] += k * scale.get(f, 0)
    aj, near = Counter(), Counter()
    for (f, b), k in proj_aj.items():
        aj[b] += k * scale.get(f, 0)
    for (f, b), k in proj_near.items():
        near[b] += k * scale.get(f, 0)
    # the cells the rating floor allows: a game's lower player is rated at least 1400, so its gap is at most twice the
    # distance of the game's level from 1400
    cal_cells = [f"{lv}|{gp}" for lv in range(1400, 2000, 100) for gp in range(0, 400, 50) if gp <= 2 * (lv + 99 - 1400)]
    projection = {"calibration_cells_below_2000": len(cal_cells),
                  "calibration_cells_with_1000": sum(1 for c_ in cal_cells if cal[c_] >= 1000),
                  "calibration_smallest_cell": round(min(cal[c_] for c_ in cal_cells)),
                  "adult_junior_games_by_adult_level": {b: round(aj[b]) for b in LEVELS if aj[b]},
                  "white_near_equal_games_by_level": {b: round(near[b]) for b in LEVELS if near[b]}}
    out["smaller_run_projection"] = projection
    out["smaller_run"] = {"target_cross_border_games_per_federation": TARGET_CROSS, "floor_pages": floor,
                          "floors_tried": {str(k): v for k, v in floors.items()},
                          "target_adult_junior_games_per_level_below_2000": TARGET_JUNIOR,
                          "cap_pages": CAP_PAGES,
                          "pages": sum(x["pages"] for x in smaller.values()),
                          "player_games": sum(x["player_games"] for x in smaller.values()),
                          "cross_border_player_games": sum(x["cross_border_player_games"] for x in smaller.values()),
                          "federations_reaching_target": sum(x["reaches_target"] for x in smaller.values()),
                          "federations_reaching_1000": sum(x["reaches_1000"] for x in smaller.values()),
                          "by_federation": smaller}
    out["plan"] = {"frame_list": plan["frame_list"], "federations": len(plan["federations"]),
                   "per_federation": sorted(set(plan["per_federation"].values())),
                   "oversample": plan["oversample"], "junior_born_from": plan["junior_born_from"],
                   "newcomer_from": plan["newcomer_from"],
                   "sampled_by_level": dict(Counter(x["band"] for x in plan["sample"])),
                   "sampled_junior_or_newcomer": sum(1 for x in plan["sample"] if x["junior"] or x["newcomer"]),
                   "sampled_junior": sum(1 for x in plan["sample"] if x["junior"]),
                   "sampled_newcomer": sum(1 for x in plan["sample"] if x["newcomer"]),
                   "frame_players": sum(v["frame"] for v in plan["cells"].values()),
                   "frame_junior_or_newcomer": sum(v["frame_junior_or_newcomer"] for v in plan["cells"].values()),
                   "frame_pages": sum(v["frame_pages"] for v in plan["cells"].values()),
                   "cells": {k: {"frame": v["frame"], "sampled": v["sampled"]} for k, v in sorted(plan["cells"].items())}}

    # 6. the probe of FIDE's tournament reports
    out["probe"] = probe(log)
    out["politeness"] = politeness(log)
    out["lock"] = lock(log)
    json.dump(out, sys.stdout, indent=1, sort_keys=True)
    sys.stdout.write("\n")
    return 0


def expit(x: float) -> float:
    return 1 / (1 + math.exp(-x))


def two_way(cell: dict, feds: list[str], levels: tuple, sweeps: int = 200) -> tuple[dict, dict]:
    """logit P(cross-border) = a_f + c_b, by maximum likelihood on the pilot's rows: each parameter in turn solved by
    Newton's method so that the model's expected cross-border rows equal the observed ones; half a pseudo-row each way
    per federation keeps a federation with no cross-border row finite. Level bands without rows get c = 0."""
    rows = {k: (v["games"], v["cross"]) for k, v in cell.items() if v["games"]}
    a = {f: 0.0 for f in feds}
    c = {b: 0.0 for b in levels if any(k[1] == b for k in rows)}

    def solve(x0: float, terms: list[tuple[int, float]], target: float) -> float:
        x = x0
        for _ in range(50):
            ps = [(n_, expit(x + off)) for n_, off in terms]
            g = sum(n_ * p_ for n_, p_ in ps) - target
            h = sum(n_ * p_ * (1 - p_) for n_, p_ in ps)
            if h <= 0:
                break
            step = g / h
            x -= max(-5.0, min(5.0, step))
            if abs(step) < 1e-10:
                break
        return x
    for _ in range(sweeps):
        old = dict(a), dict(c)
        for f in feds:
            terms = [(n_, c[b]) for (ff, b), (n_, _x) in rows.items() if ff == f] + [(1, 0.0)]
            target = sum(x_ for (ff, _b), (_n, x_) in rows.items() if ff == f) + 0.5
            a[f] = solve(a[f], terms, target)
        for b in c:
            terms = [(n_, a[f]) for (f, bb), (n_, _x) in rows.items() if bb == b]
            target = sum(x_ for (_f, bb), (_n, x_) in rows.items() if bb == b)
            c[b] = solve(c[b], terms, target)
        if max(max(abs(a[k] - old[0][k]) for k in a), max(abs(c[k] - old[1][k]) for k in c)) < 1e-9:
            break
    return a, c


def white_edge(e: dict) -> dict:
    """White's edge in score points from every game: half the difference of the mean residual (score minus FIDE's
    expectation, the printed change before K) as White and as Black."""
    w, b = e["white"].summary(), e["black"].summary()
    if not w.get("games") or not b.get("games"):
        return {"white": w, "black": b}
    edge = (w["mean"] - b["mean"]) / 2
    half = ((w["hi"] - w["lo"]) ** 2 + (b["hi"] - b["lo"]) ** 2) ** 0.5 / 4
    return {"games_white": w["games"], "games_black": b["games"], "edge": round(edge, 4),
            "lo": round(edge - half, 4), "hi": round(edge + half, 4)}


def politeness(log: list[dict]) -> dict:
    """Requests by host and status, and the smallest gap between consecutive requests, as logged (whole seconds): per
    host, and over every host of fide.com from 09:34Z on 14 October 2026, when the tool began to count them as one
    site."""
    by_host: dict[str, list] = defaultdict(list)
    for r in log:
        by_host[r["host"]].append(datetime.strptime(r["fetched_utc"], "%Y-%m-%dT%H:%M:%SZ"))
    out = {}
    for h, ts in sorted(by_host.items()):
        ts.sort()
        gaps = [(b - a).total_seconds() for a, b in zip(ts, ts[1:])]
        out[h] = {"requests": len(ts), "first": ts[0].strftime("%H:%M:%SZ"), "last": ts[-1].strftime("%H:%M:%SZ"),
                  "statuses": dict(Counter(r["status"] for r in log if r["host"] == h)),
                  "smallest_gap": min(gaps) if gaps else None, "gaps_under_4": sum(1 for g in gaps if g < 4)}
    site = sorted(datetime.strptime(r["fetched_utc"], "%Y-%m-%dT%H:%M:%SZ") for r in log
                  if fs.site_of(r["host"]) == "fide.com")
    after = [t for t in site if t >= datetime(2026, 10, 14, 9, 34)]
    gaps = [(b - a).total_seconds() for a, b in zip(after, after[1:])]
    refused = [r for r in log if r["status"] == "429" or r["status"].startswith("5") or r["status"].startswith("error")]
    return {"by_host": out, "fide_site_from_0934": {"requests": len(after), "smallest_gap": min(gaps) if gaps else None,
                                                    "gaps_under_4": sum(1 for g in gaps if g < 4)},
            "refusals": len(refused), "robots": {r["host"]: r["status"] for r in log if r["item"].startswith("robots ")},
            "hosts_outside_fide": sorted({r["host"] for r in log if fs.site_of(r["host"]) != "fide.com"}),
            "requests_in_all": len(log), "first": log[0]["fetched_utc"] if log else None,
            "last": log[-1]["fetched_utc"] if log else None}


def lock(log: list[dict]) -> dict:
    """The championship lock: the latest rating period requested, the latest end of an event whose report was
    requested, and requests or cached files that name a 2026 U.S. Championship."""
    periods = [re.search(r"rating_period=(\d{4}-\d\d)", r["url"]).group(1) for r in log if "rating_period=" in r["url"]]
    known = fs.report_events_known()
    ends = [known[r["item"].split()[1]]["end"] for r in log if r["item"].startswith("report ")
            and r["item"].split()[1] in known]
    locked = re.compile(r"2026[^<]{0,80}(U\.?\s?S\.?|United States)[^<]{0,40}Championship|"
                        r"(U\.?\s?S\.?|United States)[^<]{0,40}Championship[^<]{0,80}2026", re.I)
    files = [f for d in (fs.CALCS, fs.REPORTS) for f in d.glob("*.html")]
    hits = sum(1 for f in files if locked.search(f.read_text(encoding="utf-8", errors="replace")))
    return {"latest_period_requested": max(periods) if periods else None,
            "latest_report_event_end": max(ends) if ends else None,
            "urls_naming_a_2026_us_championship": sum(1 for r in log if locked.search(r["url"])),
            "cached_pages_naming_a_2026_us_championship": hits, "cached_pages_scanned": len(files)}


def probe(log: list[dict]) -> dict:
    items = [r for r in log if r["item"].startswith("report ")]
    reports = []
    for r in items:
        f = fs.REPORTS / f"{r['item'].split()[1]}.html"
        if not f.exists():
            continue
        t = f.read_text(encoding="utf-8", errors="replace")
        table = t[t.find('<table class="table2"'):]
        table = table[:table.find("</table>")]
        trs = re.findall(r"<tr>(.*?)</tr>", table, re.S)
        players = [ex.cells(x) for x in trs[1:]]
        players = [p for p in players if p and p[0].isdigit()]
        n = sum(int(p[7]) for p in players if len(p) > 7 and p[7].isdigit())
        reports.append({"bytes": int(r["bytes"]), "players": len(players), "player_games": n,
                        "ids_given": all(p[0].isdigit() for p in players),
                        "colour_marks": t.count("white_note") + t.count("black_note"),
                        "links_to_player_pages": len(re.findall(r"/calculations\.phtml\?id_number=", table))})
    if not reports:
        return {"requests": len(items), "reports": 0}
    pl = sorted(x["players"] for x in reports)
    return {"requests": len(items), "statuses": dict(Counter(r["status"] for r in items)), "reports": len(reports),
            "players_per_report": {"median": pl[len(pl) // 2], "min": pl[0], "max": pl[-1],
                                   "total": sum(pl)},
            "player_games_per_report_median": sorted(x["player_games"] for x in reports)[len(reports) // 2],
            "individual_games_given": 0, "colour_marks": sum(x["colour_marks"] for x in reports),
            "player_ids_given_in_every_report": all(x["ids_given"] for x in reports),
            "player_pages_linked": sum(x["links_to_player_pages"] for x in reports)}


if __name__ == "__main__":
    sys.exit(main())
