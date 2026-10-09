#!/usr/bin/env python3
"""E1 extraction: aggregates from FIDE's monthly rating lists (needs data/, never committed).

Reads data/interim/fide/<tc>/YYYY-MM.tsv (tools/data/convert_fide_lists.py) and
prints one JSON document of aggregates to standard output; the committed copy is
analysis/aggregates/E1_<tc>.json, and analysis/e1_fide_lists_report.py turns it
into analysis/OUTPUT_E1.md. FIDE lists are analysed, never redistributed: only
counts, medians and shares leave this script.

Definitions (all PROVISIONAL, stated in docs/evidence/E1_fide-lists.md):
  anchor cohort for a 12-month window s -> s+12: aged 25-45 in the calendar year
    of s (by year of birth), rated on both lists, not flagged inactive on either,
    at least MIN_GAMES rated games in the window (sum of the list "Gms" fields of
    months s+1..s+12) and at least MIN_GAMES in the 12 lists up to s;
  annual change: R(s+12) - R(s); median and mean, overall and for players rated
    below and from 2000 at s (the March 2024 compression moved only ratings
    below 2000);
  floor pile-up: rated players per 10-point bin from 1400 to 1599, and per
    1-point bin over the 20 points above the floor in force (1000 before March
    2024, 1400 from then [V 1] [R §2]), per list;
  exit: an ID on list m that is absent from list m+1, by its last rating, and
    how many exits had first been listed on list m itself;
  newcomer: an ID on list m that is on no earlier list since February 2015
    (counted from February 2016, a one-year burn-in); re-entry: an ID seen
    before but absent from list m-1; also summed by calendar year: counts and
    median first rating by age band (age in the list year) and counts by
    100-point band of the first rating;
  K distribution: counts of each K value per list, for all players, for players
    with at least one rated game in that period, and for such players aged 18 or
    less in the list year.

Usage: python3 analysis/e1_fide_lists_extract.py standard > analysis/aggregates/E1_standard.json
"""
from __future__ import annotations

import json
import statistics
import sys
from array import array
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MIN_GAMES = 10
AGE_BANDS = [(0, 9, "<10"), (10, 14, "10-14"), (15, 19, "15-19"), (20, 29, "20-29"), (30, 49, "30-49"), (50, 200, "50+")]


def band_of(age: int | None) -> str:
    if age is None:
        return "unknown"
    for lo, hi, name in AGE_BANDS:
        if lo <= age <= hi:
            return name
    return "unknown"


def shift(period: str, months: int) -> str:
    y, m = map(int, period.split("-"))
    m0 = y * 12 + (m - 1) + months
    return f"{m0 // 12:04d}-{m0 % 12 + 1:02d}"


def summ(v: list[int]) -> dict:
    return {"n": len(v), "median": statistics.median(v) if v else None,
            "mean": round(statistics.fmean(v), 2) if v else None}


def main() -> int:
    tc = sys.argv[1]
    files = sorted((ROOT / "data" / "interim" / "fide" / tc).glob("*.tsv"))
    periods = [f.stem for f in files]
    T = len(periods)
    index: dict[str, int] = {}
    for f in files:                                   # pass 1: every ID
        with f.open() as fh:
            next(fh)
            for line in fh:
                pid = line[:line.index("\t")]
                if pid not in index:
                    index[pid] = len(index)
    N = len(index)
    rating = [array("H", bytes(2 * N)) for _ in range(T)]       # 0 = not on the list
    games = [array("H", bytes(2 * N)) for _ in range(T)]
    inactive = [bytearray(N) for _ in range(T)]
    kval = [bytearray(N) for _ in range(T)]
    birth = array("H", bytes(2 * N))
    for t, f in enumerate(files):                      # pass 2: fill arrays
        R, G, I, K = rating[t], games[t], inactive[t], kval[t]
        with f.open() as fh:
            next(fh)
            for line in fh:
                pid, r, g, k, by, sex, fed, flag, title = line.rstrip("\n").split("\t")
                if not r.isdigit():
                    continue
                i = index[pid]
                R[i] = int(r)
                G[i] = int(g) if g.isdigit() else 0
                I[i] = 1 if "i" in flag else 0
                K[i] = int(k) if k.isdigit() else 255
                if by.isdigit():
                    birth[i] = int(by)
    pos = {p: t for t, p in enumerate(periods)}
    out: dict = {"time_control": tc, "first_list": periods[0], "last_list": periods[-1], "n_lists": T,
                 "n_ids": N, "min_games": MIN_GAMES}

    # rolling 12-list sums of rated games per player: W[t] = games on lists t-11 .. t
    W: list[array] = []
    run = array("l", bytes(8 * N))
    for t in range(T):
        Gt = games[t]
        Go = games[t - 12] if t >= 12 else None
        for i in range(N):
            v = Gt[i] - (Go[i] if Go is not None else 0)
            if v:
                run[i] += v
        W.append(array("H", (min(x, 65535) for x in run)))

    # (i) anchor-cohort drift over 12-month windows
    drift = []
    for s in periods:
        e, b = shift(s, 12), shift(s, -11)
        if e not in pos or b not in pos:
            continue
        ts, te = pos[s], pos[e]
        g_before, g_in = W[ts], W[te]
        year = int(s[:4])
        Rs, Re, Is, Ie = rating[ts], rating[te], inactive[ts], inactive[te]
        ch_all, ch_lo, ch_hi = [], [], []
        for i in range(N):
            r0, r1, by = Rs[i], Re[i], birth[i]
            if not r0 or not r1 or not by or Is[i] or Ie[i]:
                continue
            if not (25 <= year - by <= 45) or g_in[i] < MIN_GAMES or g_before[i] < MIN_GAMES:
                continue
            c = r1 - r0
            ch_all.append(c)
            (ch_lo if r0 < 2000 else ch_hi).append(c)
        drift.append({"start": s, "end": e, "all": summ(ch_all), "below_2000": summ(ch_lo), "from_2000": summ(ch_hi)})
    out["anchor_drift"] = drift

    # first list on which each ID is rated
    first_t = array("h", [-1]) * N
    for t in range(T):
        Rt = rating[t]
        for i in range(N):
            if Rt[i] and first_t[i] < 0:
                first_t[i] = t

    # (ii) floor pile-up and (exits)
    floor, exits = [], []
    for t, p in enumerate(periods):
        bins, act = [0] * 20, [0] * 20
        fine = [0] * 20                                   # 1-point bins at the floor in force
        floor_at = 1400 if p >= "2024-03" else 1000       # §7.2.1 [V 1]; 1000 before the March 2024 reform [R §2]
        Rt, It = rating[t], inactive[t]
        n_rated, rmin = 0, 9999
        for i in range(N):
            r = Rt[i]
            if not r:
                continue
            n_rated += 1
            rmin = min(rmin, r)
            if floor_at <= r < floor_at + 20:
                fine[r - floor_at] += 1
            if 1400 <= r < 1600:
                bins[(r - 1400) // 10] += 1
                if not It[i]:
                    act[(r - 1400) // 10] += 1
        floor.append({"list": p, "n_rated": n_rated, "min_rating": rmin, "floor": floor_at,
                      "one_point_bins_from_floor_20": fine,
                      "bins_1400_1599": bins, "not_inactive_bins_1400_1599": act})
        if t + 1 < T:
            Rn = rating[t + 1]
            cnt = {"<1450": 0, "1450-1599": 0, "1600+": 0}
            first_here = 0
            for i in range(N):
                r = Rt[i]
                if r and not Rn[i]:
                    cnt["<1450" if r < 1450 else "1450-1599" if r < 1600 else "1600+"] += 1
                    first_here += first_t[i] == t
            exits.append({"list": periods[t + 1], "exits_by_last_rating": cnt,
                          "exits_first_listed_on_previous_list": first_here})
    out["floor"] = floor
    out["exits"] = exits

    # (iii) newcomers and re-entries
    seen = bytearray(N)
    newc = []
    yearly: dict[str, dict[str, list[int]]] = {}
    for t, p in enumerate(periods):
        Rt = rating[t]
        Rp = rating[t - 1] if t else None
        if p >= "2016-02":
            by_age: dict[str, list[int]] = {}
            re_entries = []
            for i in range(N):
                r = Rt[i]
                if not r:
                    continue
                if not seen[i]:
                    by = birth[i]
                    band = band_of(int(p[:4]) - by if by else None)
                    by_age.setdefault(band, []).append(r)
                    yearly.setdefault(p[:4], {}).setdefault(band, []).append(r)
                elif Rp is not None and not Rp[i]:
                    re_entries.append(r)
            all_r = [r for v in by_age.values() for r in v]
            newc.append({
                "list": p, "n_new": len(all_r), "n_reentry": len(re_entries),
                "new_median_rating": statistics.median(all_r) if all_r else None,
                "new_below_1400": sum(1 for r in all_r if r < 1400),
                "new_1400_1409": sum(1 for r in all_r if 1400 <= r < 1410),
                "new_at_1400": sum(1 for r in all_r if r == 1400),
                "new_from_1800": sum(1 for r in all_r if r >= 1800),
                "new_by_age": {k: summ(v) for k, v in sorted(by_age.items())},
                "reentry_median_rating": statistics.median(re_entries) if re_entries else None,
            })
        for i in range(N):
            if Rt[i]:
                seen[i] = 1
    out["newcomers"] = newc
    out["newcomers_by_year"] = {
        y: {"n": sum(len(v) for v in d.values()),
            "median_rating": statistics.median([r for v in d.values() for r in v]),
            "below_1400": sum(1 for v in d.values() for r in v if r < 1400),
            "by_age": {k: summ(v) for k, v in sorted(d.items())},
            "by_rating_band": {f"{b}-{b + 99}": sum(1 for v in d.values() for r in v if b <= r < b + 100)
                               for b in range(1000, 2600, 100)},
            "lists": sum(1 for x in newc if x["list"][:4] == y)}
        for y, d in sorted(yearly.items())}

    # (iv) K distribution
    kd = []
    for t, p in enumerate(periods):
        year = int(p[:4])
        a: dict[str, int] = {}
        played: dict[str, int] = {}
        jun: dict[str, int] = {}
        Rt, Gt, Kt = rating[t], games[t], kval[t]
        for i in range(N):
            if not Rt[i]:
                continue
            k = str(Kt[i]) if Kt[i] != 255 else "?"
            a[k] = a.get(k, 0) + 1
            if Gt[i]:
                played[k] = played.get(k, 0) + 1
                if birth[i] and year - birth[i] <= 18:
                    jun[k] = jun.get(k, 0) + 1
        kd.append({"list": p, "all": dict(sorted(a.items())), "played_this_period": dict(sorted(played.items())),
                   "juniors_played_this_period": dict(sorted(jun.items()))})
    out["k_distribution"] = kd

    json.dump(out, sys.stdout, indent=1, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
