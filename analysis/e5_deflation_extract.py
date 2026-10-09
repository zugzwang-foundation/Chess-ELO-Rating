#!/usr/bin/env python3
"""E5 extraction: the deflation question, from FIDE's lists and the broadcast archive (needs data/).

Prints one JSON document of aggregates (counts, medians, means, percentiles,
slopes and sums; nothing player-level); the committed copy is
analysis/aggregates/E5_deflation.json and analysis/e5_deflation_report.py turns
it into docs/evidence/E5_deflation.md. FIDE's lists are analysed, never
redistributed [V 3]; the Lichess broadcast archive is CC BY-SA 4.0, attributed
wherever its results are used.

What it measures (definitions stated again in the report; all PROVISIONAL):
 A. Per-player annual change of published ratings, R(s+12) - R(s), for players
    rated on both lists ("survivors"), over E1's windows, by group: all players
    with at least one rated game in the window; without K 40 (K on list s); adults
    25-45 (age in the calendar year of s); E1's anchor cohort; six bands of R(s);
    age groups. Banding by R(s) carries regression to the mean, so a variant bands
    by the rating a year earlier, R(s-12).
 B. The cross-section: the distribution of ratings of players active in the 12
    months up to a list (at least one rated game on the 12 lists up to it), at
    each window's ends, with the change of the mean, the median and percentiles
    split into a within-player part and a composition part (entries and exits).
 C. Ghita's measures, as his book defines them (The Rating Revolution, 2026: the
    percentile rates p.21, the data p.63, "active" p.65, rating velocity p.20):
    percentiles of the active pool on every standard list 2021-01 to 2025-12,
    with yearly slopes before (2021-01 to 2024-02) and after (2024-03 to
    2025-12) the March 2024 reform, under three readings of "active"; and the
    mean rating change per game by age cohort.
 D. The top and the spread: players rated 2600, 2700 and 2800 or more on every
    list; ratings at ranks 10, 100 and 1000 of the active pool; the SD and
    percentiles of active adults aged 25-45.
 E. The mechanism: on broadcast games between two players rated on the list in
    force (the E2 sample, SPEC-TABLE-FIT §1), FIDE's expected score from Layer 0,
    each player's K from that list, and the realised K(S - E) by the player's
    band and year; the part implied by the favourite's over-prediction alone,
    K x (the mean residual of the game's 50-point gap bin, all years); Ghita's
    Deflation Index (sum E - sum S)/N x 100 from the favourite's side, domestic
    and cross-border (federations on the list in force); and the logistic scale
    S that minimises the squared error of the expected score.
 F. The April 2026 list event (D-0008, R11): the batch first listed in March 2026
    and absent in April, described in aggregate and excluded from A-E.

Data cutoff (ELO-4): no broadcast game dated after 2026-09-30 is used, and no
broadcast file later than 2026-09 is opened.

Usage: python3 analysis/e5_deflation_extract.py > analysis/aggregates/E5_deflation.json
"""
from __future__ import annotations

import json
import math
import statistics
import sys
from array import array
from collections import Counter
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
sys.path.insert(0, str(ROOT / "src"))
import fide_panel as fp  # noqa: E402
import e2_broadcast_extract as e2  # noqa: E402
import layer0  # noqa: E402

CUTOFF = date(2026, 9, 30)
LAST_FILE = "2026-09"
TCS = ("standard", "rapid", "blitz")
WINDOWS = [(f"{y}-02", f"{y + 1}-02") for y in range(2016, 2024)] + [
    ("2024-03", "2025-03"), ("2025-03", "2026-03"), ("2025-10", "2026-10")]
BANDS = [(0, 1599, "<1600"), (1600, 1999, "1600-1999"), (2000, 2199, "2000-2199"),
         (2200, 2399, "2200-2399"), (2400, 2599, "2400-2599"), (2600, 9999, "2600+")]
AGES = [(0, 18, "<=18"), (19, 24, "19-24"), (25, 45, "25-45"), (46, 64, "46-64"), (65, 200, "65+")]
GHITA_AGES = [(0, 18, "<=18"), (19, 34, "19-34"), (35, 49, "35-49"), (50, 200, "50+")]
PCTS = (1, 10, 25, 50, 75, 90, 99, 99.9)
MIN_GAMES = 10


def band(r: int) -> str:
    for lo, hi, name in BANDS:
        if lo <= r <= hi:
            return name
    return "?"


def age_group(age: int | None, groups=AGES) -> str:
    if age is None:
        return "unknown"
    for lo, hi, name in groups:
        if lo <= age <= hi:
            return name
    return "unknown"


def games_group(g: int) -> str:
    return "1-4" if g < 5 else "5-9" if g < 10 else "10-19" if g < 20 else "20-49" if g < 50 else "50+"


def pct(sorted_vals: list[int], p: float) -> int | None:
    """Nearest-rank percentile of a sorted list."""
    if not sorted_vals:
        return None
    k = max(1, math.ceil(p / 100.0 * len(sorted_vals)))
    return sorted_vals[k - 1]


def summ(changes: list[int], games: int | None = None) -> dict:
    if not changes:
        return {"n": 0}
    s = sorted(changes)
    out = {"n": len(s), "median": statistics.median(s), "mean": round(statistics.fmean(s), 2),
           "p25": pct(s, 25), "p75": pct(s, 75), "sum": sum(s)}
    if games is not None:
        out["games"] = games
        out["per_game"] = round(sum(s) / games, 4) if games else None
    return out


def dist(vals: list[int]) -> dict:
    if not vals:
        return {"n": 0}
    s = sorted(vals)
    return {"n": len(s), "mean": round(statistics.fmean(s), 2), "sd": round(statistics.pstdev(s), 2),
            **{f"p{p:g}": pct(s, p) for p in PCTS}}


def ols_slope_per_year(ys: list[float]) -> float | None:
    n = len(ys)
    if n < 3:
        return None
    xs = [i / 12.0 for i in range(n)]
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    return round(sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx, 2)


# ----------------------------------------------------------------------------- lists: A-D, F
def rolling_games(pan: fp.Panel) -> list[array]:
    """W[t] = rated games on lists t-11 .. t, per player."""
    W, run = [], array("l", bytes(8 * pan.n))
    for t in range(len(pan.periods)):
        Gt, Go = pan.games[t], (pan.games[t - 12] if t >= 12 else None)
        for i in range(pan.n):
            v = Gt[i] - (Go[i] if Go is not None else 0)
            if v:
                run[i] += v
        W.append(array("l", run))
    return W


def describe_batch(pan: fp.Panel, batch: set[int]) -> dict:
    if not batch:
        return {"n": 0}
    tm = pan.pos["2026-03"]
    R, G, F = pan.rating[tm], pan.games[tm], pan.fed[tm]
    feds = Counter(pan.feds[F[i]] for i in batch)
    ages = Counter(age_group(pan.age(i, 2026)) for i in batch)
    bands = Counter(band(R[i]) for i in batch)
    games = Counter(min(G[i], 10) for i in batch)
    later = sum(1 for i in batch if any(pan.rating[t][i] for t in range(tm + 1, len(pan.periods))))
    return {"n": len(batch), "top_federations": feds.most_common(8), "n_federations": len(feds),
            "share_top_federation": round(feds.most_common(1)[0][1] / len(batch), 4),
            "by_age": dict(sorted(ages.items())), "by_band": dict(sorted(bands.items())),
            "games_on_march_list_capped_10": dict(sorted(games.items())),
            "median_rating": statistics.median(R[i] for i in batch),
            "rated_again_on_a_later_list": later}


def compression_check(pan: fp.Panel, batch: set[int]) -> dict:
    """The March 2024 list against R + 0.4 (2000 - R) for players with no rated game in that period [R §2]."""
    if "2024-02" not in pan.pos or "2024-03" not in pan.pos:
        return {}
    t2, t3 = pan.pos["2024-02"], pan.pos["2024-03"]
    R2, R3, G3 = pan.rating[t2], pan.rating[t3], pan.games[t3]
    below = exact = above = unchanged = 0
    for i in range(pan.n):
        r0, r1 = R2[i], R3[i]
        if not r0 or not r1 or G3[i] or i in batch:
            continue
        if r0 < 2000:
            below += 1
            exact += r1 == r0 + (4 * (2000 - r0) + 5) // 10
        else:
            above += 1
            unchanged += r1 == r0
    return {"no_game_below_2000": below, "equal_to_formula": exact,
            "no_game_from_2000": above, "unchanged": unchanged}


def longitudinal(pan: fp.Panel, W: list[array], batch: set[int]) -> list[dict]:
    out = []
    for s, e in WINDOWS:
        if s not in pan.pos or e not in pan.pos:
            continue
        ts, te = pan.pos[s], pan.pos[e]
        tb = pan.pos.get(fp.shift(s, -12))
        year = int(s[:4])
        Rs, Re, Ks, Is, Ie = pan.rating[ts], pan.rating[te], pan.k[ts], pan.inactive[ts], pan.inactive[te]
        Rb = pan.rating[tb] if tb is not None else None
        g_in, g_before = W[te], W[ts]
        groups: dict[str, list[int]] = {}
        gsum: Counter = Counter()

        def add(key: str, c: int, g: int) -> None:
            groups.setdefault(key, []).append(c)
            gsum[key] += g

        for i in range(pan.n):
            r0, r1 = Rs[i], Re[i]
            if not r0 or not r1 or i in batch:
                continue
            g = g_in[i]
            if g < 1:
                continue
            c = r1 - r0
            age = pan.age(i, year)
            k40 = Ks[i] == 40
            b = band(r0)
            add("all_active", c, g)
            add(f"band:{b}", c, g)
            if not k40:
                add("all_active_no_k40", c, g)
                add(f"band_no_k40:{b}", c, g)
            add(f"age:{age_group(age)}", c, g)
            if age is not None and 25 <= age <= 45:
                add("adults_25_45", c, g)
                add(f"adult_band:{b}", c, g)
                add(f"adult_games:{games_group(g)}", c, g)
                if not k40:
                    add("adults_25_45_no_k40", c, g)
                if not Is[i] and not Ie[i] and g >= MIN_GAMES and g_before[i] >= MIN_GAMES:
                    add("anchor_e1", c, g)
                    add(f"anchor_band:{b}", c, g)
            if Rb is not None and Rb[i]:
                add(f"band_prev_year:{band(Rb[i])}", c, g)
        out.append({"start": s, "end": e, "groups": {k: summ(v, gsum[k]) for k, v in sorted(groups.items())}})
    return out


def cross_section(pan: fp.Panel, W: list[array], batch: set[int]) -> dict:
    """The active pool (>= 1 rated game on the 12 lists up to t) at window ends, with a decomposition."""
    lists = sorted({p for w in WINDOWS for p in w if p in pan.pos})
    snap = {}
    for p in lists:
        t = pan.pos[p]
        R, Wt = pan.rating[t], W[t]
        year = int(p[:4])
        allv, adults = [], []
        for i in range(pan.n):
            if R[i] and Wt[i] >= 1 and i not in batch:
                allv.append(R[i])
                a = pan.age(i, year)
                if a is not None and 25 <= a <= 45:
                    adults.append(R[i])
        snap[p] = {"active": dist(allv), "active_adults_25_45": dist(adults)}
    decomp = []
    for s, e in WINDOWS:
        if s not in pan.pos or e not in pan.pos:
            continue
        ts, te = pan.pos[s], pan.pos[e]
        Rs, Re, Ws, We = pan.rating[ts], pan.rating[te], W[ts], W[te]
        A_s = [i for i in range(pan.n) if Rs[i] and Ws[i] >= 1 and i not in batch]
        A_e_set = {i for i in range(pan.n) if Re[i] and We[i] >= 1 and i not in batch}
        A_s_set = set(A_s)
        stay = [i for i in A_s if i in A_e_set]
        entrants = [i for i in A_e_set if i not in A_s_set]
        leavers = [i for i in A_s if i not in A_e_set]
        n_s, n_e = len(A_s), len(A_e_set)
        mean_s = sum(Rs[i] for i in A_s) / n_s
        mean_e = sum(Re[i] for i in A_e_set) / n_e
        within = sum(Re[i] - Rs[i] for i in stay) / len(stay)
        start_vals = sorted(Rs[i] for i in A_s)
        end_vals = sorted(Re[i] for i in A_e_set)
        counterfactual = sorted([Rs[i] for i in stay] + [Re[i] for i in entrants])
        pcts = {}
        for p in (10, 50, 90, 99):
            a, b, c = pct(start_vals, p), pct(end_vals, p), pct(counterfactual, p)
            pcts[f"p{p}"] = {"start": a, "end": b, "change": b - a, "composition": c - a, "within": b - c}
        decomp.append({"start": s, "end": e, "n_start": n_s, "n_end": n_e, "stayers": len(stay),
                       "entrants": len(entrants), "leavers": len(leavers),
                       "entrants_mean_rating": round(sum(Re[i] for i in entrants) / len(entrants), 1) if entrants else None,
                       "leavers_mean_rating": round(sum(Rs[i] for i in leavers) / len(leavers), 1) if leavers else None,
                       "mean_change": round(mean_e - mean_s, 2),
                       "mean_within_stayers": round(within, 2),
                       "mean_within_weighted": round(len(stay) / n_e * within, 2),
                       "mean_composition": round(mean_e - mean_s - len(stay) / n_e * within, 2),
                       "percentiles": pcts})
    return {"snapshots": snap, "decomposition": decomp}


def ghita(pan: fp.Panel, W: list[array], batch: set[int]) -> dict:
    """Percentiles of the active pool on every list 2021-01 .. 2025-12, three readings of 'active'; velocity by age."""
    months = [p for p in pan.periods if "2021-01" <= p <= "2025-12"]
    year_games: dict[int, array] = {}
    for y in range(2021, 2026):
        acc = array("l", bytes(8 * pan.n))
        for p in pan.periods:
            if p[:4] == str(y):
                g = pan.games[pan.pos[p]]
                for i in range(pan.n):
                    if g[i]:
                        acc[i] += g[i]
        year_games[y] = acc
    readings = {"month": {}, "trailing_12": {}, "calendar_year": {}}
    for p in months:
        t = pan.pos[p]
        R, G, Wt, Y = pan.rating[t], pan.games[t], W[t], year_games[int(p[:4])]
        vals = {"month": [], "trailing_12": [], "calendar_year": []}
        for i in range(pan.n):
            r = R[i]
            if not r or i in batch:
                continue
            if G[i]:
                vals["month"].append(r)
            if Wt[i]:
                vals["trailing_12"].append(r)
            if Y[i]:
                vals["calendar_year"].append(r)
        for k, v in vals.items():
            v.sort()
            readings[k][p] = {"n": len(v), "mean": round(sum(v) / len(v), 2),
                              **{f"p{q:g}": pct(v, q) for q in (10, 25, 50, 75, 90, 99, 99.9)}}
    slopes = {}
    for k, series in readings.items():
        pre = [p for p in months if p <= "2024-02"]
        post = [p for p in months if p >= "2024-03"]
        slopes[k] = {}
        for stat in ("mean", "p10", "p25", "p50", "p75", "p90", "p99", "p99.9"):
            slopes[k][stat] = {"pre": ols_slope_per_year([series[p][stat] for p in pre]),
                               "post": ols_slope_per_year([series[p][stat] for p in post]),
                               "dec_to_dec": {f"{y}-12 to {y + 1}-12": series[f"{y + 1}-12"][stat] - series[f"{y}-12"][stat]
                                              for y in range(2021, 2025)}}
    # rating velocity: mean change per game by age cohort, months with games, March 2024 excluded
    vel: dict[str, dict[str, list[float]]] = {"pre": {}, "post": {}}
    for p in months:
        if p == "2021-01" or p == "2024-03":
            continue
        t = pan.pos[p]
        R0, R1, G = pan.rating[t - 1], pan.rating[t], pan.games[t]
        year = int(p[:4])
        era = "pre" if p <= "2024-02" else "post"
        for i in range(pan.n):
            g = G[i]
            if not g or not R0[i] or not R1[i] or i in batch:
                continue
            key = age_group(pan.age(i, year), GHITA_AGES)
            acc = vel[era].setdefault(key, [0, 0, 0])
            acc[0] += R1[i] - R0[i]
            acc[1] += g
            acc[2] += 1
    velocity = {era: {k: {"points": v[0], "games": v[1], "player_months": v[2],
                          "per_game": round(v[0] / v[1], 4)} for k, v in sorted(d.items())}
                for era, d in vel.items()}
    return {"months": months, "series": readings, "slopes": slopes, "velocity": velocity}


def top_and_spread(pan: fp.Panel, W: list[array], batch: set[int]) -> dict:
    rows = {}
    for t, p in enumerate(pan.periods):
        R, Wt = pan.rating[t], W[t]
        year = int(p[:4])
        c = Counter()
        active, adults = [], []
        for i in range(pan.n):
            r = R[i]
            if not r or i in batch:
                continue
            if r >= 2600:
                c["2600"] += 1
                if r >= 2700:
                    c["2700"] += 1
                    if r >= 2800:
                        c["2800"] += 1
            if Wt[i] >= 1:
                active.append(r)
                if r >= 2600:
                    c["active_2600"] += 1
                    if r >= 2700:
                        c["active_2700"] += 1
                        if r >= 2800:
                            c["active_2800"] += 1
                a = pan.age(i, year)
                if a is not None and 25 <= a <= 45:
                    adults.append(r)
        active.sort(reverse=True)
        rows[p] = {"n_2600": c["2600"], "n_2700": c["2700"], "n_2800": c["2800"],
                   "active_2600": c["active_2600"], "active_2700": c["active_2700"], "active_2800": c["active_2800"],
                   "active_rank_10": active[9] if len(active) >= 10 else None,
                   "active_rank_100": active[99] if len(active) >= 100 else None,
                   "active_rank_1000": active[999] if len(active) >= 1000 else None,
                   "active_top100_mean": round(sum(active[:100]) / 100, 1) if len(active) >= 100 else None,
                   "active_adults_25_45": dist(adults)}
    return rows


# ----------------------------------------------------------------------------- broadcasts: E
def broadcast_games() -> tuple[dict, dict[str, list[tuple]]]:
    """The E2 sample construction (SPEC-TABLE-FIT §1), keeping ids, dates and tours; cutoff enforced."""
    for f in (ROOT / "data" / "interim" / "broadcast").glob("*.tsv"):
        if f.stem > LAST_FILE:
            raise SystemExit(f"refusing to read {f.name}: later than the ELO-4 data cutoff ({LAST_FILE})")
    games, raw = e2.load_games()
    games, duplicates = e2.dedupe(games)
    after_cutoff = [g for g in games if e2.to_date(g.date_used) > CUTOFF]
    games = [g for g in games if e2.to_date(g.date_used) <= CUTOFF]
    span: dict[str, list[date]] = {}
    votes: dict[str, Counter] = {}
    for g in games:
        d = e2.to_date(g.date_used)
        s = span.setdefault(g.tour, [d, d])
        s[0], s[1] = min(s[0], d), max(s[1], d)
        c = e2.classify(g.time_control, g.clk_white, g.clk_black)
        if c:
            votes.setdefault(g.tour, Counter())[c] += 1
    tour_tc = {t: max(v.items(), key=lambda kv: (kv[1], kv[0]))[0] for t, v in votes.items()}
    by_tc: dict[str, list[tuple]] = {tc: [] for tc in TCS}
    for g in games:
        tc = tour_tc.get(g.tour)
        if not tc or not (g.white_fide_id.isdigit() and g.black_fide_id.isdigit()):
            continue
        s0, s1 = span[g.tour]
        start = s0 if (s1 - s0).days <= 30 else e2.to_date(g.date_used)
        score = 1.0 if g.result == "1-0" else 0.0 if g.result == "0-1" else 0.5
        by_tc[tc].append((e2.to_date(g.date_used), f"{start.year:04d}-{start.month:02d}", s0, g.tour,
                          g.white_fide_id, g.black_fide_id, score))
    meta = {"raw_games": raw.get("games"), "duplicates_removed": duplicates,
            "dropped_after_cutoff": len(after_cutoff), "cutoff": CUTOFF.isoformat()}
    return meta, by_tc


def gap_bin(d: int) -> int:
    return min(abs(d) // 50, 20)


def mechanism(pan: fp.Panel, games: list[tuple], batch_ids: set[str]) -> dict:
    tc = pan.tc
    rows = []                        # (year, rw, rb, kw, kb, fw, fb, s, e0w)
    skipped = Counter()
    for d, lst, s0, tour, w, b, s in games:
        if w in batch_ids or b in batch_ids:
            skipped["r11_batch"] += 1
            continue
        t = pan.pos.get(lst)
        iw, ib = pan.index.get(w), pan.index.get(b)
        if t is None or iw is None or ib is None:
            skipped["not_on_list"] += 1
            continue
        rw, rb = pan.rating[t][iw], pan.rating[t][ib]
        if not rw or not rb:
            skipped["not_rated_on_list_in_force"] += 1
            continue
        kw, kb = pan.k[t][iw], pan.k[t][ib]
        if kw not in (10, 20, 40) or kb not in (10, 20, 40):
            skipped["k_not_10_20_40"] += 1
            continue
        e0w = e2.e0_white(rw, rb, tc, s0)
        rows.append((d.year, rw, rb, kw, kb, pan.feds[pan.fed[t][iw]], pan.feds[pan.fed[t][ib]], s, e0w))
    # mean residual of the favourite by 50-point gap bin, all years (E2's measure, recomputed on this sample)
    fav = [[0, 0.0] for _ in range(21)]
    for _y, rw, rb, _kw, _kb, _fw, _fb, s, e0w in rows:
        k = gap_bin(rw - rb)
        sf, ef = (s, e0w) if rw >= rb else (1 - s, 1 - e0w)
        fav[k][0] += 1
        fav[k][1] += sf - ef
    m = [(c[1] / c[0]) if c[0] else 0.0 for c in fav]
    # per player-game, by the player's band and year: realised K(S-E) and the part implied by m alone
    cells: dict[tuple, list[float]] = {}
    for y, rw, rb, kw, kb, _fw, _fb, s, e0w in rows:
        mk = m[gap_bin(rw - rb)]
        for r, k, sc, ex, is_fav in ((rw, kw, s, e0w, rw >= rb), (rb, kb, 1 - s, 1 - e0w, rb > rw)):
            implied = k * (mk if is_fav else -mk)
            for key in ((band(r), y), (band(r), "all")):
                c = cells.setdefault(key, [0, 0.0, 0.0, 0.0])
                c[0] += 1
                c[1] += k * (sc - ex)
                c[2] += implied
                c[3] += k
    by_band_year = {f"{b}|{y}": {"player_games": int(c[0]), "realised_per_game": round(c[1] / c[0], 4),
                                 "implied_per_game": round(c[2] / c[0], 4), "mean_k": round(c[3] / c[0], 2)}
                    for (b, y), c in sorted(cells.items(), key=lambda kv: (kv[0][0], str(kv[0][1])))}
    # Ghita's Deflation Index from the favourite's side, by year, domestic / cross-border, by favourite's band
    di: dict[str, list[float]] = {}
    for y, rw, rb, _kw, _kb, fw, fb, s, e0w in rows:
        if rw == rb:
            continue
        ef, sf, rf = (e0w, s, rw) if rw > rb else (1 - e0w, 1 - s, rb)
        el = 1.0 / (1.0 + 10 ** (-abs(rw - rb) / 400.0))
        kind = "domestic" if fw and fw == fb else "cross_border" if fw and fb else "unknown_fed"
        for key in (f"{y}|all|all", f"{y}|{kind}|all", f"{y}|{kind}|{band(rf)}", f"all|{kind}|all", "all|all|all"):
            c = di.setdefault(key, [0, 0.0, 0.0, 0.0])
            c[0] += 1
            c[1] += ef
            c[2] += sf
            c[3] += el
    deflation_index = {k: {"games": int(c[0]), "di_table": round(100 * (c[1] - c[2]) / c[0], 3),
                           "di_logistic_400": round(100 * (c[3] - c[2]) / c[0], 3)}
                       for k, c in sorted(di.items())}
    # logistic scale S minimising sum (S_obs - 1/(1+10^(-x/S)))^2, White's view, colour ignored, uncapped gap
    def best_scale(sub: list[tuple]) -> float | None:
        if len(sub) < 1000:
            return None
        cells_s = Counter((rw - rb, s) for _y, rw, rb, *_r, s, _e in sub)
        items = sorted(cells_s.items())

        def sse(scale: float) -> float:
            return sum(n * (s - 1.0 / (1.0 + 10 ** (-x / scale))) ** 2 for (x, s), n in items)
        lo, hi = 300.0, 900.0
        for _ in range(60):                       # golden-section search
            a, b = lo + 0.382 * (hi - lo), lo + 0.618 * (hi - lo)
            if sse(a) < sse(b):
                hi = b
            else:
                lo = a
        return round((lo + hi) / 2, 1)
    scales = {str(y): best_scale([r for r in rows if r[0] == y]) for y in sorted({r[0] for r in rows})}
    scales["all"] = best_scale(rows)
    return {"games_used": len(rows), "skipped": dict(skipped), "favourite_residual_by_gap_bin": [round(x, 4) for x in m],
            "favourite_games_by_gap_bin": [c[0] for c in fav], "by_band_year": by_band_year,
            "deflation_index": deflation_index, "logistic_scale_least_squares": scales,
            "games_by_year": dict(sorted(Counter(r[0] for r in rows).items()))}


# ----------------------------------------------------------------------------- main
def main() -> int:
    meta, bgames = broadcast_games()
    out: dict = {"broadcast": meta, "windows": WINDOWS, "bands": [b[2] for b in BANDS], "by_tc": {}}
    batch_ids_all: set[str] = set()
    for tc in TCS:
        pan = fp.load_panel(tc)
        batch = fp.batch_r11(pan)
        batch_ids = {pan.ids[i] for i in batch}
        batch_ids_all |= batch_ids
        W = rolling_games(pan)
        res = {"first_list": pan.periods[0], "last_list": pan.periods[-1], "n_ids": pan.n,
               "r11_batch": describe_batch(pan, batch),
               "march_2024": compression_check(pan, batch),
               "longitudinal": longitudinal(pan, W, batch),
               "cross_section": cross_section(pan, W, batch),
               "top_and_spread": top_and_spread(pan, W, batch),
               "mechanism": mechanism(pan, bgames[tc], batch_ids)}
        if tc == "standard":
            res["ghita"] = ghita(pan, W, batch)
        out["by_tc"][tc] = res
        del pan, W
    json.dump(out, sys.stdout, indent=1, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
