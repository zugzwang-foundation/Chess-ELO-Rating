#!/usr/bin/env python3
"""E2 extraction: the Lichess broadcast archive against FIDE's published ratings (needs data/).

Implements docs/specs/SPEC-TABLE-FIT_v1_0.md. Reads the game headers of the
Lichess broadcast archive (data/interim/broadcast/, tools/data/convert_broadcasts.py;
CC BY-SA 4.0, attributed wherever the results are used) and FIDE's monthly lists
(data/interim/fide/, analysed, never redistributed), and prints one JSON document
of counts, sums and fitted values; the committed copy is
analysis/aggregates/E2_broadcast.json. analysis/e2_broadcast_report.py applies the
decision rules of annex T8 to it and writes docs/evidence/E2_broadcast-calibration.md
and params/table_fit_2026-10.yaml. Nothing game-level leaves this script.

Usage: python3 analysis/e2_broadcast_extract.py > analysis/aggregates/E2_broadcast.json
"""
from __future__ import annotations

import json
import math
import re
import sys
from collections import Counter
from datetime import date
from multiprocessing import Pool
from pathlib import Path
from typing import NamedTuple

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import layer0  # noqa: E402

Q = math.log(10.0) / 400.0
FIRST_TEST = "2025-01"          # the first 24 months (2023-01 to 2024-12) are training only
WINDOW = 36                     # fit window, months
TCS = ("standard", "rapid", "blitz")
BINS = 21                       # 50-point bins of |x|: 0-49, ..., 950-999, and 1000 or more
START = (0.9, 30.0, -0.5, 0.5, 0.25)


# ------------------------------------------------------------------ months and bands
def to_date(d: str) -> date | None:
    """A PGN date "YYYY.MM.DD", or the forms "YYYY-MM-DD" and "DD.MM.YYYY" that some broadcasts use."""
    m = re.fullmatch(r"(\d{4})[.-](\d\d)[.-](\d\d)", d)
    if m:
        y, mo, dd = m.groups()
    else:
        m = re.fullmatch(r"(\d\d)\.(\d\d)\.(\d{4})", d)
        if not m:
            return None
        dd, mo, y = m.groups()
    try:
        return date(int(y), int(mo), int(dd))
    except ValueError:
        return None


def month_of(d: str) -> str | None:
    x = to_date(d)
    return f"{x.year:04d}-{x.month:02d}" if x else None


def band100_mid(level: int) -> int:
    """Midpoint of the 100-point level band of the published table (annex T3.4)."""
    if level < 1500:
        return 1450
    if level >= 2800:
        return 2850
    return 1500 + 100 * ((level - 1500) // 100) + 50


def band200(level: int) -> int:
    return 1400 if level < 1600 else min(2600, 1600 + 200 * ((level - 1600) // 200))


# ------------------------------------------------------------------ the D1 model
def probs(p: tuple, x: float, mid: float) -> tuple[float, float, float]:
    kappa, eta, alpha, beta, gamma = p
    z = kappa * Q * (x + eta)
    nu = math.exp(alpha + beta * (mid - 2000.0) / 400.0 - gamma * abs(z))
    a = math.exp(z / 2.0)
    b = 1.0 / a
    den = a + b + nu
    return a / den, nu / den, b / den


def loglik_grad(p: tuple, cells: list) -> tuple[float, list[float]]:
    """Log-likelihood and its score (annex T3.3) over cells (x, ell, s, weight)."""
    kappa, eta, alpha, beta, gamma = p
    kq = kappa * Q
    ll = g0 = g1 = g2 = g3 = g4 = 0.0
    for x, ell, s, w in cells:
        z = kq * (x + eta)
        az = abs(z)
        nu = math.exp(alpha + beta * ell - gamma * az)
        a = math.exp(z / 2.0)
        b = 1.0 / a
        den = a + b + nu
        pw, pd, pl = a / den, nu / den, b / den
        if s == 1.0:
            ll += w * math.log(pw)
            dr = 0.0
        elif s == 0.5:
            ll += w * math.log(pd)
            dr = 1.0
        else:
            ll += w * math.log(pl)
            dr = 0.0
        sg = 1.0 if z > 0 else -1.0 if z < 0 else 0.0
        u = w * ((s - (pw + 0.5 * pd)) - gamma * sg * (dr - pd))
        g0 += u * Q * (x + eta)
        g1 += u * kq
        r = w * (dr - pd)
        g2 += r
        g3 += ell * r
        g4 -= az * r
    return ll, [g0, g1, g2, g3, g4]


def _solve(a: list[list[float]], b: list[float]) -> list[float] | None:
    n = len(b)
    m = [row[:] + [b[i]] for i, row in enumerate(a)]
    for c in range(n):
        piv = max(range(c, n), key=lambda r: abs(m[r][c]))
        if abs(m[piv][c]) < 1e-14:
            return None
        m[c], m[piv] = m[piv], m[c]
        for r in range(n):
            if r != c:
                f = m[r][c] / m[c][c]
                for cc in range(c, n + 1):
                    m[r][cc] -= f * m[c][cc]
    return [m[i][n] / m[i][i] for i in range(n)]


def _hessian(p: list[float], cells: list, free: list[int]) -> list[list[float]]:
    h_ = [[0.0] * 5 for _ in range(5)]
    for j in free:
        h = 1e-4 * max(1.0, abs(p[j]))
        pp, pm = list(p), list(p)
        pp[j] += h
        pm[j] -= h
        _, gp = loglik_grad(tuple(pp), cells)
        _, gm = loglik_grad(tuple(pm), cells)
        for i in range(5):
            h_[i][j] = (gp[i] - gm[i]) / (2 * h)
    return h_


def fit(cells: list) -> dict:
    """Maximum likelihood with gamma in [0, 1/2]: damped Newton, finite-difference Hessian, active set for gamma."""
    p = list(START)
    ll, g = loglik_grad(tuple(p), cells)
    it = 0
    for it in range(1, 51):
        free = [0, 1, 2, 3, 4]
        if (p[4] <= 0.0 and g[4] < 0) or (p[4] >= 0.5 and g[4] > 0):
            free = [0, 1, 2, 3]
        h_ = _hessian(p, cells, free)
        step_free = _solve([[-h_[i][j] for j in free] for i in free], [g[i] for i in free])
        if step_free is None:
            break
        step = [0.0] * 5
        for i, j in enumerate(free):
            step[j] = step_free[i]
        t = 1.0
        while True:
            cand = [p[i] + t * step[i] for i in range(5)]
            cand[4] = min(0.5, max(0.0, cand[4]))
            cand[0] = max(0.05, cand[0])
            ll_c, g_c = loglik_grad(tuple(cand), cells)
            if ll_c >= ll - 1e-9 or t < 1e-4:
                break
            t /= 2
        moved = max(abs(cand[i] - p[i]) for i in range(5))
        p, ll, g = cand, ll_c, g_c
        if moved < 1e-7:
            break
    free = [0, 1, 2, 3] if p[4] in (0.0, 0.5) else [0, 1, 2, 3, 4]
    h_ = _hessian(p, cells, free)
    se = {}
    names = ("kappa", "eta", "alpha", "beta", "gamma")
    inv_cols = []
    for k in range(len(free)):
        e = [1.0 if i == k else 0.0 for i in range(len(free))]
        inv_cols.append(_solve([[-h_[i][j] for j in free] for i in free], e))
    for k, j in enumerate(free):
        col = inv_cols[k]
        se[names[j]] = math.sqrt(col[k]) if col is not None and col[k] > 0 else None
    return {"kappa": p[0], "eta": p[1], "alpha": p[2], "beta": p[3], "gamma": p[4], "loglik": ll,
            "n": int(sum(c[3] for c in cells)), "cells": len(cells), "iterations": it, "gamma_at_bound": p[4] in (0.0, 0.5),
            "se": se}


# ------------------------------------------------------------------ time controls
def parse_tc(tag: str) -> float | None:
    m = re.fullmatch(r"(?:\d+/)?(\d+)(?:\+(\d+))?(?::.*)?", tag.strip())
    if m and int(m.group(1)) >= 60:
        return int(m.group(1)) / 60.0 + (int(m.group(2)) if m.group(2) else 0)
    return None


def parse_tc_text(tag: str) -> float | None:
    t = tag.lower()
    m = re.fullmatch(r"\s*g/?(\d+)\s*[+;]\s*(?:inc\s*)?(\d+)\s*", t)
    if m:
        return int(m.group(1)) + int(m.group(2))
    m = re.fullmatch(r"\s*(\d+)\s*(?:min|mins|minutes|m|')\s*\+\s*(\d+)\s*(?:s|sec|secs|seconds|\")\b.*", t)
    if m:
        return int(m.group(1)) + int(m.group(2))
    return None


def by_total(tot: float) -> str | None:
    if tot >= 60:
        return "standard"
    if 10 < tot < 60:
        return "rapid"
    if 3 < tot <= 10:
        return "blitz"
    return None


def classify(tag: str, cw: str, cb: str) -> str | None:
    tot = parse_tc(tag) if tag else None
    if tot is not None:
        return by_total(tot)
    clocks = [int(c) for c in (cw, cb) if c.isdigit()]
    if clocks:
        mins = max(clocks) / 60.0
        return "standard" if mins >= 55 else "rapid" if 13 <= mins < 55 else "blitz" if 2.5 < mins <= 10.5 else None
    tot = parse_tc_text(tag) if tag else None
    return by_total(tot) if tot is not None else None


# ------------------------------------------------------------------ data
class Row(NamedTuple):
    date_used: str
    file_month: str
    tour: str
    round_url: str
    game_url: str
    white: str
    black: str
    white_fide_id: str
    black_fide_id: str
    white_elo: str
    black_elo: str
    result: str
    time_control: str
    clk_white: str
    clk_black: str


def load_games() -> tuple[list[Row], dict]:
    games, raw = [], Counter()
    for f in sorted((ROOT / "data" / "interim" / "broadcast").glob("*.tsv")):
        with f.open() as fh:
            cols = fh.readline().rstrip("\n").split("\t")
            ix = {c: i for i, c in enumerate(cols)}
            for line in fh:
                v = line.rstrip("\n").split("\t")
                raw["games"] += 1
                if v[ix["variant"]] not in ("Standard", ""):
                    continue
                raw["standard_variant"] += 1
                if v[ix["result"]] not in ("1-0", "0-1", "1/2-1/2"):
                    continue
                raw["with_result"] += 1
                d = v[ix["date"]] if to_date(v[ix["date"]]) else v[ix["utc_date"]]
                if to_date(d):
                    raw["dated"] += 1
                    raw["dated_in_file_month"] += month_of(d) == f.stem
                else:                                    # reading: dated by the month of its archive file
                    d = f"{f.stem[:4]}.{f.stem[5:7]}.01"
                    raw["date_from_file_month"] += 1
                w_id, b_id = v[ix["white_fide_id"]], v[ix["black_fide_id"]]
                raw["both_fide_ids"] += w_id.isdigit() and b_id.isdigit()
                games.append(Row(d, f.stem, sys.intern(v[ix["tour"]]), sys.intern(v[ix["round_url"]]), v[ix["game_url"]],
                                 v[ix["white"]], v[ix["black"]], w_id, b_id, v[ix["white_elo"]], v[ix["black_elo"]],
                                 v[ix["result"]], sys.intern(v[ix["time_control"]]), v[ix["clk_white"]],
                                 v[ix["clk_black"]]))
    return games, dict(raw)


def dedupe(games: list[Row]) -> tuple[list[Row], int]:
    """The same game in two tours counts once: per (date, White, Black, result) keep the largest single-tour count."""
    groups: dict[tuple, dict[str, list[Row]]] = {}
    for g in games:
        key = (g.date_used, g.white_fide_id or g.white, g.black_fide_id or g.black, g.result)
        groups.setdefault(key, {}).setdefault(g.tour, []).append(g)
    kept = []
    for key in sorted(groups):
        tours = groups[key]
        best = min(tours, key=lambda t: (-len(tours[t]), t))
        kept.extend(sorted(tours[best], key=lambda g: (g.round_url, g.game_url)))
    return kept, len(games) - len(kept)


def load_lists(months: set[str], ids: set[str], pool_months: set[str]) -> tuple[dict, dict[str, Counter]]:
    """Ratings of the broadcast's players on each needed list, and, per time control, the rating histogram of
    every player with games on the lists of the sample's months (the bias statement)."""
    lists, pool = {}, {tc: Counter() for tc in TCS}
    for tc in TCS:
        for m in sorted(months | pool_months):
            f = ROOT / "data" / "interim" / "fide" / tc / f"{m}.tsv"
            if not f.exists():
                continue
            d = {}
            with f.open() as fh:
                next(fh)
                for line in fh:
                    pid, rating, games, _ = line.split("\t", 3)
                    if not rating.isdigit():
                        continue
                    if pid in ids:
                        d[pid] = int(rating)
                    if m in pool_months and games.isdigit() and int(games) > 0:
                        pool[tc][int(rating)] += 1
            lists[(tc, m)] = d
    return lists, pool


def quantiles_from_hist(hist: Counter) -> dict:
    n = sum(hist.values())
    out, acc = {}, 0
    targets = {"q1": 0.25 * n, "median": 0.5 * n, "q3": 0.75 * n}
    for r in sorted(hist):
        acc += hist[r]
        for k, t in targets.items():
            if k not in out and acc >= t:
                out[k] = r
    out["n"] = n
    out["share_from_2200"] = round(sum(v for r, v in hist.items() if r >= 2200) / n, 4) if n else None
    return out


_E0: dict = {}


def e0_white(rw: int, rb: int, tc: str, start: date) -> float:
    """Layer 0: the expected score FIDE uses for White, from the ratified engine (src/layer0)."""
    key = (rw - rb, rw >= 2650, tc, start >= layer0.rules.AMENDMENT_2650)
    if key not in _E0:
        _E0[key] = float(layer0.expected_score(layer0.effective_difference(rw, rb, tc, start)))
    return _E0[key]


# ------------------------------------------------------------------ evaluation of one test month
def new_bin() -> list[float]:
    return [0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]   # n, S, E2, E0, sum (S-E2)^2, sum (S-E0)^2, draws, P_D rung 2


def add_bin(b: list[float], s: float, e2: float, e0: float, draw: bool, pd2: float) -> None:
    b[0] += 1
    b[1] += s
    b[2] += e2
    b[3] += e0
    b[4] += (s - e2) ** 2
    b[5] += (s - e0) ** 2
    b[6] += draw
    b[7] += pd2


def rps(pw: float, pd: float, pl: float, s: float) -> float:
    o1 = 1.0 if s == 0.0 else 0.0
    o2 = 1.0 if s <= 0.5 else 0.0
    return 0.5 * ((pl - o1) ** 2 + (pl + pd - o2) ** 2)


def evaluate_month(task: tuple) -> dict:
    tc, month, cells, test, draw_rate = task
    params = fit(cells)
    p = tuple(params[k] for k in ("kappa", "eta", "alpha", "beta", "gamma"))
    sums = dict.fromkeys(("ll2", "ll0", "brier2", "brier0", "rps2", "rps0"), 0.0)
    bins = [new_bin() for _ in range(BINS)]
    white_fav = [new_bin() for _ in range(BINS)]
    black_fav = [new_bin() for _ in range(BINS)]
    farming = [new_bin() for _ in range(BINS)]
    levels: dict[int, list[float]] = {}
    for x, level, s, e0 in test:
        mid = band100_mid(level)
        pw, pd, pl = probs(p, x, mid)
        e2 = pw + pd / 2.0
        e0c = min(max(e0, 0.002), 0.998)
        dd = min(draw_rate.get(mid, 0.3), 2 * e0c - 0.002, 2 * (1 - e0c) - 0.002)
        qw, qd, ql = e0c - dd / 2.0, dd, 1.0 - e0c - dd / 2.0
        sums["ll2"] -= math.log(pw if s == 1.0 else pd if s == 0.5 else pl)
        sums["ll0"] -= math.log(qw if s == 1.0 else qd if s == 0.5 else ql)
        sums["brier2"] += (s - e2) ** 2
        sums["brier0"] += (s - e0) ** 2
        sums["rps2"] += rps(pw, pd, pl, s)
        sums["rps0"] += rps(qw, qd, ql, s)
        fav_white = x >= 0
        sf, e2f, e0f = (s, e2, e0) if fav_white else (1.0 - s, 1.0 - e2, 1.0 - e0)
        k = min(abs(x) // 50, BINS - 1)
        add_bin(bins[k], sf, e2f, e0f, s == 0.5, pd)
        add_bin((white_fav if fav_white else black_fav)[k], sf, e2f, e0f, s == 0.5, pd)
        if abs(x) >= 400 and level >= 2300:
            add_bin(farming[k], sf, e2f, e0f, s == 0.5, pd)
        add_bin(levels.setdefault(mid, new_bin()), sf, e2f, e0f, s == 0.5, pd)
    return {"tc": tc, "month": month, "n": len(test), "params": params, "sums": sums, "bins": bins,
            "white_fav": white_fav, "black_fav": black_fav, "farming": farming,
            "levels": {str(k): v for k, v in sorted(levels.items())}}


def merge_bins(rows: list[list[list[float]]]) -> list[list[float]]:
    out = [new_bin() for _ in range(BINS)]
    for r in rows:
        for k in range(BINS):
            out[k] = [a + b for a, b in zip(out[k], r[k])]
    return out


def month_add(m: str, k: int) -> str:
    return layer0.month_add(m, k)


# ------------------------------------------------------------------ main
def main() -> int:
    games, raw = load_games()
    games, duplicates = dedupe(games)
    out: dict = {"source": "Lichess broadcast archive (https://database.lichess.org/broadcast/, CC BY-SA 4.0), "
                           f"monthly files {min(g.file_month for g in games)} to {max(g.file_month for g in games)}",
                 "raw_counts": raw, "duplicates_removed": duplicates, "after_dedupe": len(games)}
    span: dict[str, list[date]] = {}
    votes: dict[str, Counter] = {}
    for g in games:
        d = to_date(g.date_used)
        s = span.setdefault(g.tour, [d, d])
        s[0], s[1] = min(s[0], d), max(s[1], d)
        c = classify(g.time_control, g.clk_white, g.clk_black)
        if c:
            votes.setdefault(g.tour, Counter())[c] += 1
    tour_tc = {t: max(v.items(), key=lambda kv: (kv[1], kv[0]))[0] for t, v in votes.items()}
    game_months = {month_of(g.date_used) for g in games}
    months_needed = game_months | {f"{s[0].year:04d}-{s[0].month:02d}" for s in span.values()}
    ids = {g.white_fide_id for g in games} | {g.black_fide_id for g in games}
    lists, pool_hists = load_lists({m for m in months_needed if m}, ids, {m for m in game_months if m})

    cov = {"classified": Counter(), "both_ids": Counter(), "rated_both": Counter(), "elo_tag_compared": 0,
           "elo_tag_equal": 0}
    sample: dict[str, list[tuple]] = {tc: [] for tc in TCS}
    for g in games:
        tc = tour_tc.get(g.tour)
        if not tc:
            continue
        cov["classified"][tc] += 1
        if not (g.white_fide_id.isdigit() and g.black_fide_id.isdigit()):
            continue
        cov["both_ids"][tc] += 1
        s0, s1 = span[g.tour]
        start = s0 if (s1 - s0).days <= 30 else to_date(g.date_used)
        lst = lists.get((tc, f"{start.year:04d}-{start.month:02d}"))
        if not lst:
            continue
        w, b = lst.get(g.white_fide_id), lst.get(g.black_fide_id)
        if w is None or b is None:
            continue
        cov["rated_both"][tc] += 1
        for tag, rv in ((g.white_elo, w), (g.black_elo, b)):
            if tag.isdigit():
                cov["elo_tag_compared"] += 1
                cov["elo_tag_equal"] += int(tag) == rv
        s = 1.0 if g.result == "1-0" else 0.0 if g.result == "0-1" else 0.5
        sample[tc].append((month_of(g.date_used), g.tour, g.white_fide_id, g.black_fide_id, w, b, s,
                           e0_white(w, b, tc, s0)))
    out["coverage"] = {k: dict(v) if isinstance(v, Counter) else v for k, v in cov.items()}

    # descriptive measures and the bias statement, all months
    desc = {}
    for tc in TCS:
        S = sample[tc]
        if not S:
            continue
        hist = Counter()
        gap: dict[int, list[float]] = {}
        lev: dict[int, list[float]] = {}
        per: dict[tuple, list[int]] = {}
        months = Counter()
        for m, tour, w, b, rw, rb, s, e0 in S:
            months[m] += 1
            hist[rw] += 1
            hist[rb] += 1
            hi_w = rw >= rb
            rh, rl = (rw, rb) if hi_w else (rb, rw)
            sh = s if hi_w else 1.0 - s
            d = rh - rl
            c = gap.setdefault(min(d // 50, BINS - 1), [0, 0.0, 0.0, 0.0, 0])
            c[0] += 1
            c[1] += sh
            c[2] += float(layer0.expected_score(d))
            c[3] += e0 if hi_w else 1.0 - e0
            c[4] += s == 0.5
            lv = lev.setdefault(band200((rw + rb) // 2), [0, 0, 0, 0.0, 0])
            lv[0] += 1
            lv[1] += s == 0.5
            if abs(rw - rb) <= 25:
                lv[2] += 1
                lv[3] += s
                lv[4] += s == 0.5
            for pid, sign in ((w, 1), (b, -1)):
                e = per.setdefault((tour, pid), [0, 0])
                e[0] += 1
                e[1] += sign
        imbalance = Counter()
        for n, imb in per.values():
            if n >= 5:
                imbalance[str(max(-3, min(3, imb)))] += 1
        pool_hist = pool_hists[tc]
        desc[tc] = {
            "n_games": len(S), "n_players": len({row[2] for row in S} | {row[3] for row in S}),
            "n_tours": len({row[1] for row in S}), "games_by_year": dict(sorted(Counter(m[:4] for m in months.elements()).items())),
            "sample_ratings": quantiles_from_hist(hist), "list_players_with_games_same_months": quantiles_from_hist(pool_hist),
            "white_score": round(sum(row[6] for row in S) / len(S), 4),
            "draw_rate": round(sum(row[6] == 0.5 for row in S) / len(S), 4),
            "by_gap_50": {str(k * 50): v for k, v in sorted(gap.items())},
            "by_level_200": {str(k): v for k, v in sorted(lev.items())},
            "colour_imbalance_player_events_5plus": dict(sorted(imbalance.items(), key=lambda kv: int(kv[0]))),
        }
    out["descriptive"] = desc

    # rolling held-out months
    tasks, finals = [], {}
    for tc in TCS:
        S = sample[tc]
        months = sorted({row[0] for row in S})
        if len(S) < 5000:
            continue
        cells_by_month: dict[str, Counter] = {m: Counter() for m in months}
        draws_by_month: dict[str, Counter] = {m: Counter() for m in months}
        games_by_month: dict[str, list[tuple]] = {m: [] for m in months}
        for m, tour, w, b, rw, rb, s, e0 in S:
            mid = band100_mid((rw + rb) // 2)
            cells_by_month[m][(rw - rb, mid, s)] += 1
            draws_by_month[m][(mid, s == 0.5)] += 1
            games_by_month[m].append((rw - rb, (rw + rb) // 2, s, e0))

        def window_cells(lo: str, hi: str) -> list[tuple]:
            agg = Counter()
            for m in months:
                if lo <= m <= hi:
                    agg.update(cells_by_month[m])
            return [(x, (mid - 2000.0) / 400.0, s, float(w)) for (x, mid, s), w in sorted(agg.items())]

        for m in months:
            if m < FIRST_TEST:
                continue
            lo, hi = month_add(m, -WINDOW), month_add(m, -1)
            dr: Counter = Counter()
            tot: Counter = Counter()
            for mm in months:
                if lo <= mm <= hi:
                    for (mid, is_draw), n in draws_by_month[mm].items():
                        tot[mid] += n
                        dr[mid] += n if is_draw else 0
            tasks.append((tc, m, window_cells(lo, hi), games_by_month[m], {k: dr[k] / tot[k] for k in tot}))
        last = months[-1]
        finals[tc] = (month_add(last, -(WINDOW - 1)), last, window_cells(month_add(last, -(WINDOW - 1)), last))
    with Pool(8) as pool:
        rolling = pool.map(evaluate_month, tasks, chunksize=1)
        final_fits = pool.map(fit, [v[2] for v in finals.values()])
    out["rolling"] = {}
    for tc in finals:
        R = [r for r in rolling if r["tc"] == tc]
        out["rolling"][tc] = {
            "window_months": WINDOW, "first_test_month": FIRST_TEST, "test_months": [r["month"] for r in R],
            "per_month": {r["month"]: {"n": r["n"], **r["sums"], "params": {k: r["params"][k] for k in
                                                                             ("kappa", "eta", "alpha", "beta", "gamma")}}
                          for r in R},
            "bins": merge_bins([r["bins"] for r in R]),
            "white_favourite_bins": merge_bins([r["white_fav"] for r in R]),
            "black_favourite_bins": merge_bins([r["black_fav"] for r in R]),
            "farming_bins": merge_bins([r["farming"] for r in R]),
            "levels": {k: [sum(r["levels"].get(k, new_bin())[i] for r in R) for i in range(8)]
                       for k in sorted({k for r in R for k in r["levels"]}, key=int)},
        }
    out["final_fit"] = {tc: {"from": v[0], "to": v[1], **f} for (tc, v), f in zip(finals.items(), final_fits)}
    json.dump(out, sys.stdout, indent=1, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
