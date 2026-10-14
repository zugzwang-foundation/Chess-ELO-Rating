#!/usr/bin/env python3
"""E21, part 1: FIDE's standard lists revisited, totals only (session ELO-D1, step 4; needs data/).

Three measures, each chosen after the lists had been seen and labelled so (the founder's decision of 14 October 2026,
docs/DECISIONS.md item 32), from FIDE's monthly standard lists of February 2015 to October 2026 as converted under
data/interim/fide/standard/ (rating, games, K, birth year, federation, flag; never committed):

1. **Who plays the rated games.** On each list from March 2015 the player-games of the period (FIDE's "games" column:
   each rated game counts once for each rated player in it) by the K of the list before, the K that rated them
   (SPEC-L0 R-22b), with players not rated on the list before counted apart as newly rated; summed by year. Beside it,
   by the K printed on the same list. Ghita's 54.6 % for K = 40 (The Rating Revolution, p. 73) is cited for comparison,
   not taken as a target: his count rests on FIDE's 2025 game extract, ours on the lists.
2. **Juniors' climb against adults'.** Every player rated on the lists of October 2025 and October 2026 with at least
   one rated game in the twelve periods between: the rating change, by age on 2025 (Layer 1's age bands,
   src/layer1/model.py), by 200-point level band of October 2025, and by federation (the 75 of the pilot: at least 1,000
   rated players on the October 2025 list, plus England, Scotland and Wales), juniors (under 20) against adults of 25
   to 45 at the same level, standardised over the level bands by the juniors' numbers.
3. **Newcomers' first ratings and their ratings later.** Every player first rated on a list of April 2024 or later,
   the first list after the one that carried the reform of 1 March 2024 and its one-time compression (first rated: on
   no list before, from February 2015): the rating 12 lists later, for first lists of April 2024 to October 2025, and
   24 lists later, for April to October 2024, among those still listed who played a rated game in between; by age,
   level of the first rating and federation.

A climb is not proof of under-rating: a player who improves climbs under any rule, and a player who stops playing
leaves the measure. Intervals are 95 %, normal, mean ± 1.96 standard errors. Python standard library only.

Usage: python3 analysis/e21_lists_extract.py > analysis/aggregates/E21_lists.json
"""
from __future__ import annotations

import json
import math
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LISTS = ROOT / "data" / "interim" / "fide" / "standard"
FIRST, LAST = "2015-02", "2026-10"
CLIMB_FROM, CLIMB_TO = "2025-10", "2026-10"
NEW_FROM, NEW_12_TO, NEW_24_TO = "2024-04", "2025-10", "2024-10"
MIN_RATED, ADDED_FEDS = 1000, ("ENG", "SCO", "WLS")
AGE_BANDS = ((0, 12, "<12"), (12, 16, "12-15"), (16, 20, "16-19"), (20, 25, "20-24"), (25, 46, "25-45"),
             (46, 61, "46-60"), (61, 200, ">60"))
JUNIOR = ("<12", "12-15", "16-19")
ADULT = "25-45"
LEVELS = ((0, 1400, "below 1400"), (1400, 1600, "1400-1599"), (1600, 1800, "1600-1799"), (1800, 2000, "1800-1999"),
          (2000, 2200, "2000-2199"), (2200, 2400, "2200-2399"), (2400, 9999, "2400+"))
MIN_CELL = 5


def month_add(m: str, k: int) -> str:
    y, mo = int(m[:4]), int(m[5:7]) - 1 + k
    return f"{y + mo // 12:04d}-{mo % 12 + 1:02d}"


def months(a: str, b: str) -> list[str]:
    out = [a]
    while out[-1] < b:
        out.append(month_add(out[-1], 1))
    return out


def age_band(age: int | None) -> str | None:
    if age is None:
        return None
    return next((lab for lo, hi, lab in AGE_BANDS if lo <= age < hi), None)


def level(r: int) -> str:
    return next(lab for lo, hi, lab in LEVELS if lo <= r < hi)


def read(m: str) -> dict[str, tuple]:
    """FIDE ID -> (rating, games, K, birth year or None, federation) of every rated player on list m."""
    out = {}
    with (LISTS / f"{m}.tsv").open(encoding="utf-8") as fh:
        next(fh)
        for line in fh:
            pid, r, g, k, by, _sex, fed, _flag, _title = line.rstrip("\n").split("\t")
            if r.isdigit():
                out[pid] = (int(r), int(g) if g.isdigit() else 0, int(k) if k.isdigit() else 0,
                            int(by) if by.isdigit() and int(by) > 1900 else None, fed)
    return out


class Stat:
    """Count, sum and sum of squares, and the values for the median."""

    def __init__(self) -> None:
        self.v: list[int] = []

    def add(self, x: int) -> None:
        self.v.append(x)

    def summary(self) -> dict:
        n = len(self.v)
        if not n:
            return {"n": 0}
        mean = sum(self.v) / n
        sd = math.sqrt(sum((x - mean) ** 2 for x in self.v) / (n - 1)) if n > 1 else 0.0
        s = sorted(self.v)
        med = s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2
        se = sd / math.sqrt(n)
        return {"n": n, "mean": round(mean, 1), "median": med, "sd": round(sd, 1),
                "lo": round(mean - 1.96 * se, 1), "hi": round(mean + 1.96 * se, 1)}


def standardised(junior: dict[str, Stat], adult: dict[str, Stat]) -> dict | None:
    """Juniors' mean climb minus adults' at the same level, averaged over the level bands where both have at least
    MIN_CELL players, weighted by the juniors' numbers; with its 95 % interval."""
    num, var, w_tot, nj, na = 0.0, 0.0, 0, 0, 0
    for lev, j in junior.items():
        a = adult.get(lev)
        if a is None or len(j.v) < MIN_CELL or len(a.v) < MIN_CELL:
            continue
        sj, sa = j.summary(), a.summary()
        w = sj["n"]
        num += w * (sum(j.v) / sj["n"] - sum(a.v) / sa["n"])
        var += w * w * (sj["sd"] ** 2 / sj["n"] + sa["sd"] ** 2 / sa["n"])
        w_tot += w
        nj += sj["n"]
        na += sa["n"]
    if not w_tot:
        return None
    d, se = num / w_tot, math.sqrt(var) / w_tot
    lo, hi = d - 1.96 * se, d + 1.96 * se
    return {"juniors": nj, "adults": na, "difference": round(d, 1), "lo": round(lo, 1), "hi": round(hi, 1),
            "direction": "juniors climb more" if lo > 0 else "juniors climb less" if hi < 0 else "not settled"}


def main() -> int:
    all_months = months(FIRST, LAST)
    ever: set[str] = set()
    k_by_year: dict[str, dict] = defaultdict(lambda: defaultdict(int))
    k_same_by_year: dict[str, dict] = defaultdict(lambda: defaultdict(int))
    prev = None
    # juniors' climb: October 2025 -> October 2026
    base, played = {}, defaultdict(int)
    climb_by: dict = defaultdict(Stat)
    climb_fed: dict = defaultdict(lambda: defaultdict(Stat))
    # newcomers
    newc: dict[str, dict] = {}
    frame_list = None
    for m in all_months:
        cur = read(m)
        if m == CLIMB_FROM:
            frame_list = cur
        y = m[:4]
        if prev is not None:
            for pid, (_r, g, k, _by, _fed) in cur.items():
                if not g:
                    continue
                p = prev.get(pid)
                key = "newly rated" if p is None else f"K={p[2]}" if p[2] in (10, 20, 40) else "other K"
                k_by_year[y][key] += g
                k_same_by_year[y][f"K={k}" if k in (10, 20, 40) else "other K"] += g
        # newcomers: first rated on m
        if NEW_FROM <= m <= NEW_12_TO:
            for pid, (r, _g, _k, by, fed) in cur.items():
                if pid not in ever:
                    newc[pid] = {"first": m, "r0": r, "age": int(m[:4]) - by if by else None, "fed": fed,
                                 "games12": 0, "games24": 0, "r12": None, "r24": None}
        for pid, d in newc.items():
            if d["first"] < m:
                gap = (int(m[:4]) - int(d["first"][:4])) * 12 + int(m[5:7]) - int(d["first"][5:7])
                c = cur.get(pid)
                if gap <= 12 and c:
                    d["games12"] += c[1]
                if gap <= 24 and c:
                    d["games24"] += c[1]
                if gap == 12:
                    d["r12"] = c[0] if c else None
                if gap == 24:
                    d["r24"] = c[0] if c else None
        if m == CLIMB_FROM:
            base = {pid: (r, by, fed) for pid, (r, _g, _k, by, fed) in cur.items()}
        elif CLIMB_FROM < m <= CLIMB_TO:
            for pid, (_r, g, *_x) in cur.items():
                if pid in base:
                    played[pid] += g
        if m == CLIMB_TO:
            for pid, (r0, by, fed) in base.items():
                c = cur.get(pid)
                if c is None or not played[pid] or by is None:
                    continue
                band = age_band(2025 - by)
                if band is None:
                    continue
                climb_by[(band, level(r0))].add(c[0] - r0)
                climb_fed[fed][(band, level(r0))].add(c[0] - r0)
        ever |= cur.keys()
        prev = cur
    rated = defaultdict(int)
    for _pid, (_r, _g, _k, _by, fed) in frame_list.items():
        rated[fed] += 1
    feds = sorted({f for f, n in rated.items() if n >= MIN_RATED} | set(ADDED_FEDS))

    def shares(tab: dict) -> dict:
        out = {}
        for y, c in sorted(tab.items()):
            tot = sum(c.values())
            out[y] = {"player_games": tot, **{k: v for k, v in sorted(c.items())},
                      **{f"share {k}": round(v / tot, 4) for k, v in sorted(c.items())}}
        return out

    # juniors' climb
    by_age_level = {f"{a}|{lv}": climb_by[(a, lv)].summary() for _l, _h, a in AGE_BANDS for _l2, _h2, lv in LEVELS
                    if climb_by[(a, lv)].v}
    by_age = {}
    for _l, _h, a in AGE_BANDS:
        s = Stat()
        for _l2, _h2, lv in LEVELS:
            s.v += climb_by[(a, lv)].v
        by_age[a] = s.summary()
    std_all = {}
    for a in JUNIOR + ("<20",):
        js = {lv: climb_by[(a, lv)] for _l, _h, lv in LEVELS} if a != "<20" else \
            {lv: merge(climb_by[(b, lv)] for b in JUNIOR) for _l, _h, lv in LEVELS}
        std_all[a] = standardised(js, {lv: climb_by[(ADULT, lv)] for _l, _h, lv in LEVELS})
    fed_rows = {}
    for f in feds:
        js = {lv: merge(climb_fed[f][(b, lv)] for b in JUNIOR) for _l, _h, lv in LEVELS}
        ad = {lv: climb_fed[f][(ADULT, lv)] for _l, _h, lv in LEVELS}
        fed_rows[f] = standardised(js, ad)
    directions = defaultdict(int)
    for v in fed_rows.values():
        directions[v["direction"] if v else "too few players"] += 1

    # newcomers
    def newcomer_tables(horizon: int, last_first: str) -> dict:
        key_r, key_g = f"r{horizon}", f"games{horizon}"
        cohort = [d for d in newc.values() if d["first"] <= last_first]
        listed = [d for d in cohort if d[key_r] is not None]
        active = [d for d in listed if d[key_g] > 0]
        by_a, by_l, by_al, by_f = defaultdict(Stat), defaultdict(Stat), defaultdict(Stat), defaultdict(Stat)
        by_fa = defaultdict(lambda: defaultdict(Stat))
        for d in active:
            a = age_band(d["age"]) or "unknown"
            x = d[key_r] - d["r0"]
            by_a[a].add(x)
            by_l[level(d["r0"])].add(x)
            by_al[(a, level(d["r0"]))].add(x)
            by_f[d["fed"]].add(x)
            by_fa[d["fed"]]["junior" if a in JUNIOR else "adult" if a != "unknown" else "unknown"].add(x)
        allx = merge(by_a.values())
        return {"first_lists": [NEW_FROM, last_first], "newcomers": len(cohort), "still_listed": len(listed),
                "played_in_between": len(active), "all": allx.summary(),
                "by_age": {a: by_a[a].summary() for _l, _h, a in AGE_BANDS if by_a[a].v},
                "by_level": {lv: by_l[lv].summary() for _l, _h, lv in LEVELS if by_l[lv].v},
                "by_age_level": {f"{a}|{lv}": by_al[(a, lv)].summary() for _l, _h, a in AGE_BANDS
                                 for _l2, _h2, lv in LEVELS if by_al[(a, lv)].v},
                "by_federation": {f: {"all": by_f[f].summary(), "under 20": by_fa[f]["junior"].summary(),
                                      "20 and over": by_fa[f]["adult"].summary()} for f in feds},
                "federation_directions": directions_of({f: by_f[f].summary() for f in feds})}

    out = {
        "label": "decided after seeing the data (docs/DECISIONS.md, item 32); a climb, not proof of under-rating",
        "fixed_line": "Under this rule, with the same results — not anyone's true strength.",
        "lists": {"first": FIRST, "last": LAST, "count": len(all_months)},
        "k_shares": {"by_k_of_the_list_before": shares(k_by_year), "by_k_on_the_same_list": shares(k_same_by_year),
                     "note": "player-games: each rated game counts once for each rated player in it; 2015 from March, "
                             "2026 to October",
                     "ghita_cited": {"K=40": 0.546, "K=10": 0.046, "source": "Ghita, The Rating Revolution, p. 73"}},
        "juniors_climb": {"from": CLIMB_FROM, "to": CLIMB_TO, "players": sum(len(s.v) for s in climb_by.values()),
                          "by_age": by_age, "by_age_level": by_age_level,
                          "juniors_minus_adults_25_45_standardised": std_all,
                          "federations": {"list": feds, "by_federation": fed_rows, "directions": dict(directions)}},
        "newcomers": {"12": newcomer_tables(12, NEW_12_TO), "24": newcomer_tables(24, NEW_24_TO),
                      "12_same_cohort_as_24": newcomer_tables(12, NEW_24_TO)}}
    json.dump(out, sys.stdout, indent=1, sort_keys=True)
    sys.stdout.write("\n")
    return 0


def directions_of(rows: dict) -> dict:
    """How many federations' newcomers rise, fall or are not settled, by the 95 % interval of the mean change."""
    out = defaultdict(int)
    for v in rows.values():
        if v["n"] < MIN_CELL:
            out["too few players"] += 1
        else:
            out["rises" if v["lo"] > 0 else "falls" if v["hi"] < 0 else "not settled"] += 1
    return dict(out)


def merge(stats) -> Stat:
    s = Stat()
    for x in stats:
        s.v += x.v
    return s


if __name__ == "__main__":
    sys.exit(main())
