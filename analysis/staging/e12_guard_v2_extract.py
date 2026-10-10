#!/usr/bin/env python3
"""E12 extraction: the guard re-decided on the v2 table, and R32's scaling of K tested (session ELO-6, Phase 2; needs data/).

The rule is D-0011's (R24, fixed before the v2 table was fitted; readings 4 to 7). This script computes what the rule
and E10's checks need, with the v2 table of each of E2's 21 test months as E11 fitted it
(analysis/staging/aggregates/E11_table_by_level.json; no refit):
 - E2's sample rebuilt through E10's builder (the data cutoff enforced: no broadcast file after 2026-09, no game dated
   after 2026-09-30); the v2 table's monthly sums reproduced exactly from E11 before anything else;
 - the v2 table with and without the narrowed guard (analysis/staging/guard_v2.py) and Layer 0, on the same games:
   log-loss, Brier and RPS sums, calibration bins in E2's format, the favourite's residual by level band x gap cell
   (cluster-robust over favourites), the farming region (= the guard's region: level >= 2300, gap >= 400) with E6's
   month-block and player bootstraps (imported unchanged), and the favourite's and underdog's residuals in it by gap
   bin, gaps over 735 separately; where the guard binds the three-outcome forecast is E6's three_way (E10's choice);
 - R32's test (D-0011, reading 7): Layer 1's game records (src/layer1/data.py, the cutoff enforced there), each
   player's rating carried from the list in force through month t's broadcast games with FIDE's K and with K times
   the month's printed ratio m(L) of the game's level band, and month t + 1's games forecast from the carried ratings
   with month t + 1's v2 table and the narrowed guard (as E6 tested rung 4), the log-loss and Brier differences
   (scaled minus unscaled) by month with E6's month-block bootstrap.
Only aggregates leave the script. Staged under analysis/staging/ until Freeze 3 (D-0011, reading 1).

Usage: python3 analysis/staging/e12_guard_v2_extract.py > analysis/staging/aggregates/E12_guard_v2.json
"""
from __future__ import annotations

import json
import math
import sys
from collections import Counter, defaultdict
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "analysis" / "staging"))
sys.path.insert(0, str(ROOT / "analysis"))
sys.path.insert(0, str(ROOT / "src"))
import e2_broadcast_extract as e2x  # noqa: E402  (E2's model, bins and helpers, unchanged)
import e6_rungs_extract as e6  # noqa: E402  (E6's bootstraps and three-outcome split, unchanged)
import e10_guard_extract as e10  # noqa: E402  (E2's sample with the cutoff, unchanged)
import e11_table_by_level_extract as e11  # noqa: E402  (the cluster-robust mean, unchanged)
import guard_v2 as gv2  # noqa: E402
import table_v2 as t2  # noqa: E402
from layer1 import data as l1data  # noqa: E402

TCS = e2x.TCS
BAND = 0.01
REGION_BINS = (400, 450, 500, 550, 600, 650, 700)           # 700 holds 700-735; gaps over 735 apart (V10-EXPLOIT-3)
DIGITS = {"kappa": 4, "lambda": 4, "eta": 2, "alpha": 4, "beta": 4, "gamma": 4, "mu": 4}


def printed(par: dict) -> tuple:
    """A month's v2 parameters as a parameter file prints them (so its ratio m is the printed one)."""
    return tuple(float(Decimal(repr(par[k])).quantize(Decimal(10) ** -DIGITS[k], rounding=ROUND_HALF_UP)) for k in t2.NAMES)


def guarded(par: tuple, rw: int, rb: int) -> tuple[tuple[float, float, float], float, float, bool]:
    """White's (P_W, P_D, P_L) under the v2 table, its expectation, and the same with the narrowed guard."""
    x = rw - rb
    mid = e2x.band100_mid((rw + rb) // 2)
    vw, vd, vl = t2.probs(par, x, mid)
    ev = vw + vd / 2.0
    w = gv2.weight(rw, rb)
    eg, binds = gv2.guard_own(ev, x + t2.eta_whole(par[2]), x > 0, w)
    return (vw, vd, vl), ev, eg, binds


def region_bin(gap: int, x_fav: int) -> str:
    if x_fav > gv2.X_MAX:
        return "over 735"
    k = max(b for b in REGION_BINS if gap >= b)
    return f"{k}" if k < 700 else "700"


def main() -> int:
    d11 = json.loads((ROOT / "analysis" / "staging" / "aggregates" / "E11_table_by_level.json").read_text(encoding="utf-8"))
    e2 = json.loads((ROOT / "analysis" / "aggregates" / "E2_broadcast.json").read_text(encoding="utf-8"))
    smp, meta = e10.sample()
    out: dict = {"cutoff": meta, "rule": "docs/decisions/D-0011_rulings-and-freeze-3.md (R24; readings 4 to 7)",
                 "region": {"gap_min": gv2.GAP_MIN, "level_min": gv2.LEVEL_MIN, "gap_blend": gv2.GAP_BLEND,
                            "level_blend": gv2.LEVEL_BLEND, "x_max": gv2.X_MAX}, "static": {}, "r32": {}}
    v2_params: dict[str, dict] = {}
    for tc in TCS:
        kind = "tail" if "tail" in d11["rolling"][tc] else "lambda"
        r11 = d11["rolling"][tc][kind]
        rr = e2["rolling"][tc]
        v2_params[tc] = {m: r11["per_month"][m]["params_v2"] for m in rr["test_months"]}
        S = smp[tc]
        months = sorted({row[0] for row in S})
        draws_by_month: dict[str, Counter] = {m: Counter() for m in months}
        games_by_month: dict[str, list[tuple]] = {m: [] for m in months}
        for m, tour, w, b, rw, rb, s, e0 in S:
            mid = e2x.band100_mid((rw + rb) // 2)
            draws_by_month[m][(mid, s == 0.5)] += 1
            games_by_month[m].append((w, b, rw, rb, s, e0))
        per_month, valid = {}, []
        bins_g = [e2x.new_bin() for _ in range(e2x.BINS)]
        cells_g = defaultdict(lambda: defaultdict(lambda: [0.0, 0, 0.0, 0.0]))
        regions = {k: defaultdict(list) for k in ("v2", "guarded", "l0")}
        region_items = {k: [] for k in ("v2", "guarded", "l0")}
        region_cl = {k: defaultdict(lambda: [0.0, 0, 0.0, 0.0]) for k in ("v2", "guarded", "l0")}
        by_bin = {k: defaultdict(lambda: defaultdict(lambda: [0.0, 0, 0.0, 0.0])) for k in ("v2", "guarded", "l0")}
        counts = Counter()
        for m in rr["test_months"]:
            par = tuple(v2_params[tc][m][k] for k in t2.NAMES)
            lo, hi = e2x.month_add(m, -e2x.WINDOW), e2x.month_add(m, -1)
            dr: Counter = Counter()
            tot: Counter = Counter()
            for mm in months:
                if lo <= mm <= hi:
                    for (mid, is_draw), n in draws_by_month[mm].items():
                        tot[mid] += n
                        dr[mid] += n if is_draw else 0
            draw_rate = {k: dr[k] / tot[k] for k in tot}
            sums = dict.fromkeys(("ll_v2", "ll_g", "ll_l0", "brier_v2", "brier_g", "brier_l0", "rps_v2", "rps_g",
                                  "rps_l0"), 0.0)
            n = 0
            for w, b, rw, rb, s, e0 in games_by_month[m]:
                x, level = rw - rb, (rw + rb) // 2
                mid = e2x.band100_mid(level)
                (vw, vd, vl), ev, eg, binds = guarded(par, rw, rb)
                gw, gd, gl = e6.three_way(eg, vd) if binds else (vw, vd, vl)
                e0c = min(max(e0, 0.002), 0.998)
                dd = min(draw_rate.get(mid, 0.3), 2 * e0c - 0.002, 2 * (1 - e0c) - 0.002)
                qw, qd, ql = e0c - dd / 2.0, dd, 1.0 - e0c - dd / 2.0
                n += 1
                pick = (lambda a, dr_, l_: a if s == 1.0 else dr_ if s == 0.5 else l_)
                sums["ll_v2"] -= math.log(pick(vw, vd, vl))
                sums["ll_g"] -= math.log(pick(gw, gd, gl))
                sums["ll_l0"] -= math.log(pick(qw, qd, ql))
                sums["brier_v2"] += (s - ev) ** 2
                sums["brier_g"] += (s - eg) ** 2
                sums["brier_l0"] += (s - e0) ** 2
                sums["rps_v2"] += e2x.rps(vw, vd, vl, s)
                sums["rps_g"] += e2x.rps(gw, gd, gl, s)
                sums["rps_l0"] += e2x.rps(qw, qd, ql, s)
                fav_white = x >= 0
                sf = s if fav_white else 1.0 - s
                ef = {"v2": ev if fav_white else 1.0 - ev, "guarded": eg if fav_white else 1.0 - eg,
                      "l0": e0 if fav_white else 1.0 - e0}
                k = min(abs(x) // 50, e2x.BINS - 1)
                e2x.add_bin(bins_g[k], sf, ef["guarded"], ef["l0"], s == 0.5, gd)
                fav_id = int(w if fav_white else b)
                c = cells_g[f"{mid}|{k * 50}"][fav_id]
                c[0] += sf - ef["guarded"]
                c[1] += 1
                c[2] += sf
                c[3] += ef["guarded"]
                counts["games"] += 1
                if gv2.in_region(rw, rb):
                    counts["region"] += 1
                    counts["region_binds"] += binds
                    wgt = gv2.weight(rw, rb)
                    counts["region_full_weight"] += wgt == 1
                    eta = t2.eta_whole(par[2])
                    x_fav = abs(x) + (eta if fav_white else -eta)
                    counts["region_over_735"] += x_fav > gv2.X_MAX
                    rb_key = region_bin(abs(x), x_fav)
                    for key in ("v2", "guarded", "l0"):
                        r = sf - ef[key]
                        regions[key][m].append(r)
                        region_items[key].append((fav_id, r))
                        rc = region_cl[key][fav_id]
                        rc[0] += r
                        rc[1] += 1
                        rc[2] += sf
                        rc[3] += ef[key]
                        q = by_bin[key][rb_key][fav_id]
                        q[0] += r
                        q[1] += 1
                        q[2] += sf
                        q[3] += ef[key]
            sums["n"] = n
            per_month[m] = sums
            ref = r11["per_month"][m]
            valid.append(max(abs(sums["ll_v2"] - ref["ll_v2"]), abs(sums["brier_v2"] - ref["brier_v2"]),
                             abs(sums["rps_v2"] - ref["rps_v2"]), abs(sums["ll_l0"] - ref["ll_l0"]), abs(n - ref["n"])))
        out["static"][tc] = {
            "model": kind, "test_months": rr["test_months"],
            "reproduces_e11": {"max_abs_difference_of_monthly_sums": max(valid)},
            "per_month": per_month, "bins_guarded_l0": bins_g, "counts": dict(counts),
            "cells_guarded": {cell: e11.cr1(v) for cell, v in sorted(cells_g.items())},
            "region": {key: {**e11.cr1(region_cl[key]),
                             "month_block": e6.boot(regions[key], BAND), "players": e6.boot_cluster(region_items[key])}
                       for key in ("v2", "guarded", "l0")},
            "region_by_gap": {key: {b: e11.cr1(v) for b, v in sorted(by_bin[key].items())} for key in ("v2", "guarded", "l0")},
        }
        print(f"{tc}: reproduces E11 within {max(valid):.2e}; region {counts['region']} games, guard binds "
              f"{counts['region_binds']}", file=sys.stderr, flush=True)

    # ---------------------------------------------------------------- R32: K scaled by m, ratings carried forward
    games, _lists, gmeta = l1data.build_games(ROOT)
    out["r32_data"] = {k: gmeta[k] for k in sorted(gmeta)}
    by_month: dict[tuple[int, str], list] = defaultdict(list)
    for g in games:
        by_month[(g.tc, l1data.month_label_of(g.day))].append(g)
    for tci, tc in enumerate(TCS):
        test = e2["rolling"][tc]["test_months"]
        d_ll, d_br = defaultdict(list), defaultdict(list)
        moved = Counter()
        for t, t1 in zip(test[:-1], test[1:]):
            p_t = tuple(v2_params[tc][t][k] for k in t2.NAMES)
            p_1 = tuple(v2_params[tc][t1][k] for k in t2.NAMES)
            m_t = {mid: float(t2.ratio_printed(printed(v2_params[tc][t]), mid)) for mid in t2.BAND_MIDS}
            upd: dict[int, dict] = {}
            for g in by_month[(tci, t)]:
                if not (g.white_r and g.black_r):
                    continue
                (_vw, _vd, _vl), _ev, eg, _b = guarded(p_t, g.white_r, g.black_r)
                mid = e2x.band100_mid((g.white_r + g.black_r) // 2)
                for p, own, kk, s, e in ((g.white, g.white_r, g.white_k, g.score, eg),
                                         (g.black, g.black_r, g.black_k, 1.0 - g.score, 1.0 - eg)):
                    if not kk:
                        continue
                    u = upd.setdefault(p, {"base": own, "k": kk, "sum": 0.0, "sum_m": 0.0})
                    u["base"] = own
                    u["sum"] += s - e
                    u["sum_m"] += m_t[mid] * (s - e)
            for g in by_month[(tci, t1)]:
                if not (g.white_r and g.black_r):
                    continue
                uw, ub = upd.get(g.white), upd.get(g.black)
                if uw is None and ub is None:
                    continue
                ra = (round(uw["base"] + uw["k"] * uw["sum"]) if uw else g.white_r,
                      round(ub["base"] + ub["k"] * ub["sum"]) if ub else g.black_r)
                rb_ = (round(uw["base"] + uw["k"] * uw["sum_m"]) if uw else g.white_r,
                       round(ub["base"] + ub["k"] * ub["sum_m"]) if ub else g.black_r)
                moved["games"] += 1
                moved["differ"] += ra != rb_
                fa = guarded(p_1, *ra)
                fb = guarded(p_1, *rb_)
                pa = e6.three_way(fa[2], fa[0][1]) if fa[3] else fa[0]
                pb = e6.three_way(fb[2], fb[0][1]) if fb[3] else fb[0]
                d_ll[t1].append(e6.ll(pb, g.score) - e6.ll(pa, g.score))
                d_br[t1].append((g.score - fb[2]) ** 2 - (g.score - fa[2]) ** 2)
        out["r32"][tc] = {"games": moved["games"], "games_where_the_ratings_differ": moved["differ"],
                          "log_loss_difference": e6.boot(d_ll), "brier_difference": e6.boot(d_br)}
        print(f"{tc}: R32 test on {moved['games']} games", file=sys.stderr, flush=True)
    json.dump(out, sys.stdout, indent=1, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
