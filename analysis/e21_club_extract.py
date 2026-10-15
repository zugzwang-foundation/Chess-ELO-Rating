#!/usr/bin/env python3
"""E21, the club-level sample (session ELO-D2, steps 5 and 6; needs data/): the analyses fixed in
docs/specs/SPEC-SOURCING_v1_1.md §7 before the main fetch, totals only.

The pages are the sample's (tools/data/fetch_sourcing.py, modes club-plan and club-run), read by the extended parser,
with opponents identified by name, federation and a rating within 50 points (analysis/e21_club_common.py). First the
pages: fetched and read against the plan, by stratum; game rows, colour marks, rows printed without K, opponents
identified; Layer 0 against FIDE's printed figures on every game (src/layer0_history/); the politeness and the lock from
the session's log (data/fetch_log/ELO-D2.tsv). Then the four analyses, each figure a mean over game rows with a 95 %
interval clustered over pages (the ratio estimator's linearised variance), weighted to the frame by stratum with the
unweighted figure beside it (§7.5):

1. **The fair table** (§7.1): the favourite's score minus table 8.1.2's expectation by 50-point gap, every level pooled
   and by the game's 200-point level band; the same under the 2025 self-calibrating table (E18) and the v2 table (E11's
   rolling fit for the month the tournament started), colour included; E11's rule (a) on cells of 1,000 games or more.
2. **White moves first** (§7.2): White's score at most 25 points apart, by level; White's score minus each fitted
   table's expectation there; and White's edge left by each table over every game, half the difference of the mean
   residual as White and as Black.
3. **Juniors** (§7.3): adults' score minus FIDE's expectation against juniors, from the adult's side on either player's
   page, against adults, and against the matched control of adults' games against adults at the same colour and
   50-point gap, by the adult's band.
4. **Newcomers** (§7.4): first-year score minus FIDE's expectation of players first rated from April 2024, by age when
   first rated.
5. **A sensitivity**, added after the plan and before the sample's results were read, once Tier 0 had shown that the
   ratings FIDE's pages print often differ from the lists as published: the favourite's score minus table 8.1.2 by gap
   with the player's and the identified opponent's ratings as published on the list in force.

With --pilot the same analyses run on the pilot's 2,000 pages, each page post-stratified into the plan's strata (its
weight: the stratum's frame players over the pilot's pages in it, times the player's 2025 pages): the test SPEC-SOURCING
v1.1 asks for, labelled as the pilot's. No player's name, FIDE ID, event or row leaves data/. Python standard library
only.

Usage: python3 analysis/e21_club_extract.py > analysis/aggregates/E21_club.json
       python3 analysis/e21_club_extract.py --pilot > analysis/aggregates/E21_club_pilot.json
"""
from __future__ import annotations

import csv
import json
import math
import re
import sys
from collections import Counter, defaultdict
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
import e21_club_common as cc  # noqa: E402  (the extended parser, the resolver, the groups)
import layer0  # noqa: E402
import layer0_history as lh  # noqa: E402
import selfcal_fit as sc  # noqa: E402  (E18's table model)
from layer2 import table_v2 as t2  # noqa: E402  (E11's table model, Freeze 3; imported, not changed)

fs = cc.fs
AGG = ROOT / "analysis" / "aggregates"
LEVELS = ("1400-1599", "1600-1799", "1800-1999", "2000-2199", "2200+")
GAPS = tuple(f"{lo}-{lo + 49}" for lo in range(0, 400, 50))
BELOW_2000 = LEVELS[:3]
MIN_SHOW = 100                    # a cell is shown from 100 games (SPEC-SOURCING v1.1 §7)
MIN_TEST = 1000                   # E11's rule (a): cells of 1,000 games or more
BOUND = 0.01
NEAR = 25                         # E2: games between players at most 25 points apart
NEWCOMER_FIRST = "2024-04"
FIRST_FIT = "2025-01"             # E11's first rolling fit


def level_of(x: float) -> str:
    """E2's 200-point bands of the game's level, the mean of the two ratings (below 1600 counts as 1400-1599)."""
    return "1400-1599" if x < 1600 else "1600-1799" if x < 1800 else "1800-1999" if x < 2000 else \
        "2000-2199" if x < 2200 else "2200+"


def band_of_rating(r: int) -> str:
    return level_of(r)


def gap_bin(g: int) -> str:
    lo = g // 50 * 50
    return f"{lo}-{lo + 49}"


class Mean:
    """A mean over game rows, weighted or not, with a 95 % interval clustered over pages (linearised ratio)."""

    def __init__(self) -> None:
        self.by_page: dict[str, list[tuple[float, float]]] = defaultdict(list)

    def add(self, page: str, w: float, y: float) -> None:
        self.by_page[page].append((w, y))

    def summary(self, weighted: bool, d: int = 4) -> dict:
        rows = [(w if weighted else 1.0, y) for v in self.by_page.values() for w, y in v]
        n = len(rows)
        if not n:
            return {"games": 0}
        sw = sum(w for w, _y in rows)
        mean = sum(w * y for w, y in rows) / sw
        g = len(self.by_page)
        z = [sum((w if weighted else 1.0) * (y - mean) for w, y in v) for v in self.by_page.values()]
        se = math.sqrt(sum(x * x for x in z) * g / (g - 1)) / sw if g > 1 else 0.0
        return {"games": n, "pages": g, "mean": round(mean, d), "lo": round(mean - 1.96 * se, d),
                "hi": round(mean + 1.96 * se, d), "se": round(se, d + 1)}

    def both(self, d: int = 4) -> dict:
        return {"weighted": self.summary(True, d), "unweighted": self.summary(False, d)}


class Edge:
    """Half the difference of two clustered means (as White minus as Black), with its clustered interval."""

    def __init__(self) -> None:
        self.by_page: dict[str, list[tuple[float, float, int]]] = defaultdict(list)

    def add(self, page: str, w: float, y: float, white: bool) -> None:
        self.by_page[page].append((w, y, 1 if white else 0))

    def summary(self, weighted: bool, d: int = 4) -> dict:
        rows = [(w if weighted else 1.0, y, c) for v in self.by_page.values() for w, y, c in v]
        sw = [sum(w for w, _y, c in rows if c == k) for k in (0, 1)]
        if not all(sw):
            return {"games": len(rows)}
        m = [sum(w * y for w, y, c in rows if c == k) / sw[k] for k in (0, 1)]
        g = len(self.by_page)
        z = [sum((w if weighted else 1.0) * (y - m[c]) / sw[c] * (1 if c else -1) for w, y, c in v)
             for v in self.by_page.values()]
        se = math.sqrt(sum(x * x for x in z) * g / (g - 1)) / 2 if g > 1 else 0.0
        e = (m[1] - m[0]) / 2
        return {"games_white": sum(1 for r in rows if r[2]), "games_black": sum(1 for r in rows if not r[2]),
                "edge": round(e, d), "lo": round(e - 1.96 * se, d), "hi": round(e + 1.96 * se, d)}

    def both(self, d: int = 4) -> dict:
        return {"weighted": self.summary(True, d), "unweighted": self.summary(False, d)}


def rule_a(cells: dict[str, Mean], weighted: bool) -> dict:
    """E11's rule (a): every cell of at least MIN_TEST games, outside when significantly outside +-BOUND (one-sided z
    against the nearer bound, clustered SE), Holm-Bonferroni across the cells at a familywise 5 %."""
    tested = []
    for k, m in sorted(cells.items()):
        s = m.summary(weighted, 6)
        if s.get("games", 0) < MIN_TEST or not s.get("se"):
            continue
        z = (abs(s["mean"]) - BOUND) / s["se"]
        p = 0.5 * math.erfc(z / math.sqrt(2))
        tested.append((p, k, s))
    tested.sort()
    outside, holm_ok = [], True
    for i, (p, k, s) in enumerate(tested):
        if holm_ok and p <= 0.05 / (len(tested) - i):
            outside.append(k)
        else:
            holm_ok = False
    return {"cells_tested": len(tested), "cells_outside": len(outside), "outside": sorted(outside)}


def tables() -> tuple[dict, dict]:
    e18 = json.loads((AGG / "E18_selfcal.json").read_text(encoding="utf-8"))["tables"]["2025"]
    selfcal = {"form": e18["form"], "par": e18["par"]}
    e11 = json.loads((AGG / "E11_table_by_level.json").read_text(encoding="utf-8"))["rolling"]["standard"]["tail"]
    v2 = {m: tuple(v["params_v2"][k] for k in t2.NAMES) for m, v in e11["per_month"].items()}
    return selfcal, v2


def load(pilot: bool) -> dict:
    """The sample: each page with its stratum, its weight and its player's group facts."""
    plan = json.loads(fs.CLUB_PLAN.read_text(encoding="utf-8"))
    cells = plan["cells"]
    if pilot:
        pp = json.loads(fs.PLAN.read_text(encoding="utf-8"))
        first = fs.first_rated()
        oct25 = fs.read_list(fs.FRAME_LIST)
        per = {p["id"]: len(p["periods"]) for st in fs.club_frame()["strata"].values() for p in st}
        sample = []
        for s in pp["sample"]:
            r, _g, _k, by, _f, _fl = oct25[s["id"]]
            band = fs.club_band(r)
            sample.append({"id": s["id"], "stratum": f"{band}|{fs.club_group(by, first.get(s['id']), band)}",
                           "period": s["period"], "periods": per[s["id"]], "first": first.get(s["id"]),
                           "birth": by or None})
    else:
        sample = plan["sample"]
    pages, errors = {}, Counter()
    for s in sample:
        f = fs.CALCS / f"{s['id']}_{s['period']}.html"
        if not f.exists():
            errors["not fetched"] += 1
            continue
        try:
            pages[(s["id"], s["period"])] = cc.parse_page_club(f.read_text(encoding="utf-8-sig", errors="replace"))
        except Exception as exc:                    # recorded, never dropped silently
            errors[type(exc).__name__] += 1
    read = Counter(s["stratum"] for s in sample if (s["id"], s["period"]) in pages)
    weight = {(s["id"], s["period"]): cells[s["stratum"]]["frame_players"] / read[s["stratum"]] * s["periods"]
              for s in sample if (s["id"], s["period"]) in pages}
    return {"sample": sample, "cells": cells, "pages": pages, "errors": errors, "weight": weight, "read": read}


def start_of(t: dict, period: str) -> date:
    return date.fromisoformat(t["start"]) if t["start"] else date.fromisoformat(f"{fs.month_add(period, -1)}-01")


def main() -> int:
    pilot = "--pilot" in sys.argv[1:]
    d = load(pilot)
    sample, pages, weight = d["sample"], d["pages"], d["weight"]
    info = {(s["id"], s["period"]): s for s in sample}
    selfcal, v2 = tables()
    ids, how = cc.resolve_all(pages)
    months = sorted({fs.month_add("2025-12", -k) for k in range(0, 36)}, reverse=True)
    births = cc.births_of({i for i in ids.values() if i}, [fs.FRAME_LIST] + months)
    lists = cc.read_lists(sorted({cc.list_in_force(t["start"], k[1]) for k, pg in pages.items()
                                  for t in pg["tournaments"]}), {k[0] for k in pages} | {i for i in ids.values() if i})
    out: dict = {"label": "pilot pages, post-stratified (the test of the scripts)" if pilot else
                 "the club-level sample; analyses fixed in SPEC-SOURCING v1.1 §7 before the main fetch",
                 "fixed_line": "Under this rule, with the same results — not anyone's true strength."}

    # ---------------------------------------------------------------- the pages
    rows = Counter()
    by_stratum = defaultdict(Counter)
    l0 = Counter()
    for key, pg in pages.items():
        st = info[key]["stratum"]
        by_stratum[st]["pages_read"] += 1
        total = Decimal(0)
        for ti, t in enumerate(pg["tournaments"]):
            rows["tournaments"] += 1
            rows["tournaments_printed_without_k"] += t["unrated"]
            for gi, g in enumerate(t["games"]):
                rows["game_rows"] += 1
                by_stratum[st]["game_rows"] += 1
                rows["colour_mark"] += g["mark"] is not None
                rows["opponent_federation"] += bool(re.fullmatch(r"[A-Z]{3}", g["fed"] or ""))
                rows["capped"] += g["capped"]
                rows["printed_without_k"] += g["k"] is None
                rows["opponent_identified"] += ids[(key, ti, gi)] is not None
            if t["unrated"]:
                continue
            ds = lh.deltas(t["ro"], [(g["rating"], g["score"]) for g in t["games"]], start_of(t, key[1]))
            for g, dl in zip(t["games"], ds):
                l0["games"] += 1
                if dl == g["chg"]:
                    l0["game_change_equal"] += 1
                else:
                    l0["game_change_differs"] += 1
            s = sum(ds, Decimal(0))
            l0["tournaments"] += 1
            l0["tournament_k_sum_equal"] += Decimal(t["k"]) * s == t["k_chg"]
            total += Decimal(t["k"]) * s
        if any(not t["unrated"] for t in pg["tournaments"]):
            l0["pages_with_a_rated_tournament"] += 1
            l0["page_total_equal"] += pg["total"] is not None and total == pg["total"]
        else:
            l0["pages_without_a_rated_tournament"] += 1
    out["pages"] = {"planned": len(sample), "read": len(pages), "errors": dict(d["errors"]), "rows": dict(rows),
                    "opponents": how,
                    "by_stratum": {st: {"planned": d["cells"][st]["sampled"], **dict(by_stratum[st])}
                                   for st in sorted(d["cells"])}}
    out["layer0"] = dict(l0)

    # ---------------------------------------------------------------- the analyses
    fav = {k: defaultdict(Mean) for k in ("812", "selfcal", "v2")}
    fav_level = {k: defaultdict(Mean) for k in ("812", "selfcal", "v2")}
    white_near = defaultdict(Mean)
    white_near_res = {k: defaultdict(Mean) for k in ("selfcal", "v2")}
    edge = {k: defaultdict(Edge) for k in ("812", "selfcal", "v2")}
    aj, aa, ajc, spec = (defaultdict(Mean) for _ in range(4))
    ctrl_rows = []                    # (page, weight, colour, gap bin, residual) of adults against adults
    junior_rows = []                  # (page, weight, colour or None, gap bin, residual, adult's band)
    newc = defaultdict(Mean)
    fav_pub = defaultdict(Mean)
    counts = Counter()
    for key, pg in pages.items():
        pid, period = key
        s = info[key]
        w = weight[key]
        cl = f"{pid}:{period}"
        me_j = cc.is_junior(s["birth"])
        fy = (s["first"] or "") >= NEWCOMER_FIRST and 0 < cc.months_after(s["first"], period) <= 12
        for ti, t in enumerate(pg["tournaments"]):
            if t["unrated"]:
                continue
            mfit = max(FIRST_FIT, (t["start"] or f"{fs.month_add(period, -1)}-01")[:7])
            par = v2.get(mfit)
            for gi, g in enumerate(t["games"]):
                sc_ = float(g["score"])
                chg = float(g["chg"])
                own, opp = t["ro"], g["rating"]
                # newcomers' first year (every rated row; FIDE's printed change before K)
                if fy:
                    age = cc.age_band(int(s["first"][:4]) - s["birth"]) if s["birth"] else "unknown"
                    newc[age].add(cl, w, chg)
                    newc["every age"].add(cl, w, chg)
                    counts["newcomer_first_year_rows"] += 1
                if g["capped"]:
                    continue
                gap = abs(own - opp)
                level = level_of((own + opp) // 2)
                mid = t2.band_mid((own + opp) // 2)
                white = g["mark"] == "white" if g["mark"] else None
                # the fair table (§7.1)
                if gap < 400:
                    if own != opp:
                        fs_score, fav_white = (sc_, white) if own > opp else (1 - sc_, (None if white is None
                                                                                      else not white))
                    elif white is not None:
                        fs_score, fav_white = (sc_ if white else 1 - sc_), True
                    else:
                        fs_score = None
                    if fs_score is not None:
                        gb = gap_bin(gap)
                        r812 = fs_score - float(layer0.expected_score(gap))
                        for k, r in (("812", r812),):
                            fav[k][gb].add(cl, w, r)
                            fav[k][f"{level}|{gb}"].add(cl, w, r)
                            fav_level[k][level].add(cl, w, r)
                        if fav_white is not None:
                            gw = gap if fav_white else -gap       # White's gap
                            ew_sc = sum(sc.probs(selfcal, gw, mid)[i] * (1, 0.5, 0)[i] for i in range(3))
                            e_fav_sc = ew_sc if fav_white else 1 - ew_sc
                            ests = [("selfcal", fs_score - e_fav_sc)]
                            if par:
                                ew_v2 = t2.expected_white(par, gw, mid)
                                ests.append(("v2", fs_score - (ew_v2 if fav_white else 1 - ew_v2)))
                            for k, r in ests:
                                fav[k][gb].add(cl, w, r)
                                fav[k][f"{level}|{gb}"].add(cl, w, r)
                                fav_level[k][level].add(cl, w, r)
                    # the sensitivity, on the same rows: the ratings as published on the list in force
                    m0 = cc.list_in_force(t["start"], period)
                    oid_ = ids[(key, ti, gi)]
                    own_p = lists.get(m0, {}).get(pid, (own,))[0]
                    opp_p = lists.get(m0, {}).get(oid_, (opp,))[0] if oid_ else opp
                    gap_p = abs(own_p - opp_p)
                    counts["sensitivity_rows_with_a_published_rating_moved"] += (own_p, opp_p) != (own, opp)
                    if gap_p < 400 and own_p != opp_p:
                        fsp = sc_ if own_p > opp_p else 1 - sc_
                        fav_pub[gap_bin(gap_p)].add(cl, w, fsp - float(layer0.expected_score(gap_p)))
                    # White's edge from every game (§7.2), each table
                    if white is not None:
                        gw = (own - opp) if white else (opp - own)
                        ew_sc = sum(sc.probs(selfcal, gw, mid)[i] * (1, 0.5, 0)[i] for i in range(3))
                        edge["812"][level].add(cl, w, chg, white)
                        edge["selfcal"][level].add(cl, w, sc_ - (ew_sc if white else 1 - ew_sc), white)
                        if par:
                            ew_v2 = t2.expected_white(par, gw, mid)
                            edge["v2"][level].add(cl, w, sc_ - (ew_v2 if white else 1 - ew_v2), white)
                # White at near-equal ratings (§7.2)
                if gap <= NEAR and white is not None:
                    ws = sc_ if white else 1 - sc_
                    gw = (own - opp) if white else (opp - own)
                    white_near[level].add(cl, w, ws)
                    ew_sc = sum(sc.probs(selfcal, gw, mid)[i] * (1, 0.5, 0)[i] for i in range(3))
                    white_near_res["selfcal"][level].add(cl, w, ws - ew_sc)
                    if par:
                        white_near_res["v2"][level].add(cl, w, ws - t2.expected_white(par, gw, mid))
                # juniors (§7.3)
                oid = ids[(key, ti, gi)]
                if oid is None:
                    continue
                o_j = cc.is_junior(births.get(oid))
                if not me_j and o_j:          # the adult's own page
                    junior_rows.append((cl, w, white, max(-20, min(20, (own - opp) // 50)), chg,
                                        band_of_rating(own)))
                elif me_j and not o_j:        # the junior's page: the adult is the opponent
                    junior_rows.append((cl, w, None if white is None else not white,
                                        max(-20, min(20, (opp - own) // 50)), -chg, band_of_rating(opp)))
                elif not me_j and not o_j:
                    ctrl_rows.append((cl, w, white, max(-20, min(20, (own - opp) // 50)), chg))
                    aa[band_of_rating(own)].add(cl, w, chg)
    # the matched control: the adults' mean residual against adults by colour and gap bin
    ctrl = {"weighted": defaultdict(lambda: [0.0, 0.0]), "unweighted": defaultdict(lambda: [0.0, 0.0])}
    for _cl, w, white, gb, r in ctrl_rows:
        if white is None:
            continue
        for k, ww in (("weighted", w), ("unweighted", 1.0)):
            ctrl[k][(white, gb)][0] += ww
            ctrl[k][(white, gb)][1] += ww * r
    for cl, w, white, gb, r, band in junior_rows:
        aj[band].add(cl, w, r)
        if white is None:
            continue
        cw, cu = ctrl["weighted"].get((white, gb)), ctrl["unweighted"].get((white, gb))
        if not cw or not cw[0]:
            counts["junior_rows_without_a_control_bin"] += 1
            continue
        ajc[band].add(cl, w, cw[1] / cw[0])
        spec[band].add(cl, w, r - cw[1] / cw[0])
        spec[f"{band}|unweighted control"].add(cl, w, r - cu[1] / cu[0])
    counts["junior_rows"] = len(junior_rows)
    counts["control_rows"] = len(ctrl_rows)

    def table_out(dd: dict, keys) -> dict:
        return {k: dd[k].both() for k in keys if k in dd and dd[k].by_page}

    cells_keys = [f"{lv}|{gb}" for lv in LEVELS for gb in GAPS]
    out["fair_table"] = {k: {"by_gap": table_out(fav[k], GAPS), "by_level_gap": table_out(fav[k], cells_keys),
                             "by_level": table_out(fav_level[k], LEVELS),
                             "rule_a": {"weighted": rule_a({c: fav[k][c] for c in cells_keys if c in fav[k]}, True),
                                        "unweighted": rule_a({c: fav[k][c] for c in cells_keys if c in fav[k]},
                                                             False)}}
                         for k in ("812", "selfcal", "v2")}
    out["fair_table_published_ratings"] = table_out(fav_pub, GAPS)
    out["white"] = {"near_equal_score": table_out(white_near, LEVELS),
                    "near_equal_minus_table": {k: table_out(white_near_res[k], LEVELS) for k in ("selfcal", "v2")},
                    "edge_every_game": {k: {lv: edge[k][lv].both() for lv in LEVELS if edge[k][lv].by_page}
                                        for k in ("812", "selfcal", "v2")}}
    out["juniors"] = {"adults_against_juniors": table_out(aj, LEVELS), "adults_against_adults": table_out(aa, LEVELS),
                      "matched_control": table_out(ajc, LEVELS), "junior_specific": table_out(spec, LEVELS),
                      "junior_specific_unweighted_control": {lv: spec[f"{lv}|unweighted control"].both()
                                                             for lv in LEVELS
                                                             if spec[f"{lv}|unweighted control"].by_page}}
    out["newcomers"] = table_out(newc, [a for *_x, a in cc.AGE_BANDS] + ["unknown", "every age"])
    out["counts"] = dict(counts)
    out["thresholds"] = {
        "games_by_band": {b: sum(v.get("game_rows", 0) for st, v in by_stratum.items() if st.startswith(b))
                          for b in LEVELS},
        "adult_junior_games_by_adult_band": {b: aj[b].summary(False).get("games", 0) for b in LEVELS}}
    if not pilot:
        out["politeness"], out["lock"] = politeness_and_lock(sample)
    json.dump(out, sys.stdout, indent=1, sort_keys=True)
    sys.stdout.write("\n")
    return 0


def politeness_and_lock(sample: list[dict]) -> tuple[dict, dict]:
    """From the session's log: requests by host and status, the smallest gap over FIDE's site (whole seconds as
    logged), refusals; the lock: periods requested, URLs and cached pages naming a 2026 U.S. Championship."""
    log = list(csv.DictReader(fs.CLUB_LOG.open(encoding="utf-8"), delimiter="\t"))
    ts = sorted(datetime.strptime(r["fetched_utc"], "%Y-%m-%dT%H:%M:%SZ") for r in log
                if fs.site_of(r["host"]) == "fide.com")
    gaps = [(b - a).total_seconds() for a, b in zip(ts, ts[1:])]
    calc = [r for r in log if r["item"].startswith("calc ")]
    refused = [r for r in log if r["status"] == "429" or r["status"].startswith(("5", "error"))]
    http_refused = [r for r in log if r["status"] == "429" or r["status"].startswith("5")]
    errors = [r for r in log if r["status"].startswith("error")]
    doubled = sum(1 for g in gaps if g >= 8)
    pol = {"requests": len(log), "calc_requests": len(calc), "hosts": dict(Counter(r["host"] for r in log)),
           "statuses": dict(Counter(r["status"] for r in log)), "first": log[0]["fetched_utc"] if log else None,
           "last": log[-1]["fetched_utc"] if log else None, "smallest_gap": min(gaps) if gaps else None,
           "gaps_under_4": sum(1 for g in gaps if g < 4), "refusals": len(refused),
           "http_refusals": len(http_refused), "network_errors": len(errors),
           "network_error_times": [r["fetched_utc"] for r in errors], "gaps_of_8_s_or_more": doubled,
           "largest_gap": max(gaps) if gaps else None,
           "largest_gap_from_to": ([ts[gaps.index(max(gaps))].strftime("%H:%M:%SZ"),
                                    ts[gaps.index(max(gaps)) + 1].strftime("%H:%M:%SZ")] if gaps else None),
           "gaps_of_a_minute_or_more": [[ts[i].strftime("%H:%M:%SZ"), ts[i + 1].strftime("%H:%M:%SZ"), g]
                                        for i, g in enumerate(gaps) if g >= 60],
           "seconds_per_request": round((ts[-1] - ts[0]).total_seconds() / (len(ts) - 1), 2) if len(ts) > 1 else None,
           "bytes": sum(int(r["bytes"]) for r in log)}
    periods = sorted({re.search(r"rating_period=(\d{4}-\d\d)", r["url"]).group(1) for r in calc})
    locked = re.compile(r"2026[^<]{0,80}(U\.?\s?S\.?|United States)[^<]{0,40}Championship|"
                        r"(U\.?\s?S\.?|United States)[^<]{0,40}Championship[^<]{0,80}2026", re.I)
    files = [fs.CALCS / f"{s['id']}_{s['period']}.html" for s in sample]
    files = [f for f in files if f.exists()]
    lock = {"periods_requested": [periods[0], periods[-1]] if periods else None,
            "periods_outside_2025": sum(1 for p in periods if not p.startswith("2025-")),
            "urls_naming_a_2026_us_championship": sum(1 for r in log if locked.search(r["url"])),
            "cached_pages_naming_a_2026_us_championship": sum(
                1 for f in files if locked.search(f.read_text(encoding="utf-8", errors="replace"))),
            "cached_pages_scanned": len(files), "hosts_outside_fide": sorted({r["host"] for r in log
                                                                              if fs.site_of(r["host"]) != "fide.com"})}
    return pol, lock


if __name__ == "__main__":
    sys.exit(main())
