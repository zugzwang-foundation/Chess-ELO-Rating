#!/usr/bin/env python3
"""E10 extraction: R17's farming guard on rung 2, rerun on E2's and E6's checks (ELO-5, Phase 2; needs data/).

Ruling R17 of D-0009 (reading 4): in the region where the gap is 400 or more and the favourite is rated 2300
or more, the favourite's expected score is the larger of rung 2's fitted value and table 8.1.2 read without
the 400-point cap (src/layer2/guard.py). This script rebuilds E2's sample with E2's own functions, imported
unchanged from analysis/e2_broadcast_extract.py, and re-evaluates E2's 21 rolling test months (2025-01 to
2026-09) with the parameters E2 fitted for each month (analysis/aggregates/E2_broadcast.json), three ways:
Layer 0 (table 8.1.2 with FIDE's 400-point rule), rung 2 as E2 evaluated it, and rung 2 with the guard.
It first reproduces E2's per-month sums for Layer 0 and rung 2 (a check that the sample and the parameters
are E2's), then computes the guarded sums, calibration bins, and the region residuals of E6 §6 (the farming
region, gap 400 or more at level 2300 or more) and of R17 (gap 400 or more, favourite 2300 or more), with
E6's month-block and player bootstraps imported unchanged. Where the guard binds, the three-outcome forecast
keeps the fitted draw probability and moves the win and loss probabilities to the guarded expectation
(E6's three_way). The data cutoff holds: no broadcast file after 2026-09, no game dated after 2026-09-30.
Only aggregates leave the script.

Usage: python3 analysis/e10_guard_extract.py > analysis/aggregates/E10_guard.json
"""
from __future__ import annotations

import json
import math
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
sys.path.insert(0, str(ROOT / "src"))
import e2_broadcast_extract as e2x  # noqa: E402  (E2's sample and model functions, unchanged)
import e6_rungs_extract as e6  # noqa: E402  (E6's bootstraps and three-outcome split, unchanged)
from layer2 import guard  # noqa: E402

TCS = e2x.TCS
CUTOFF, LAST_FILE = date(2026, 9, 30), "2026-09"


def sample() -> tuple[dict[str, list[tuple]], dict]:
    """E2's sample (analysis/e2_broadcast_extract.py main(), the same steps in the same order), with the cutoff."""
    late = [f.stem for f in (ROOT / "data" / "interim" / "broadcast").glob("*.tsv") if f.stem > LAST_FILE]
    if late:
        raise ValueError(f"refusing broadcast files later than {LAST_FILE}: {sorted(late)}")
    games, _raw = e2x.load_games()
    games, _dup = e2x.dedupe(games)
    meta = Counter()
    kept = []
    for g in games:
        if e2x.to_date(g.date_used) > CUTOFF:
            meta["dropped_after_cutoff"] += 1
            continue
        kept.append(g)
    games = kept
    span: dict[str, list[date]] = {}
    votes: dict[str, Counter] = {}
    for g in games:
        d = e2x.to_date(g.date_used)
        s = span.setdefault(g.tour, [d, d])
        s[0], s[1] = min(s[0], d), max(s[1], d)
        c = e2x.classify(g.time_control, g.clk_white, g.clk_black)
        if c:
            votes.setdefault(g.tour, Counter())[c] += 1
    tour_tc = {t: max(v.items(), key=lambda kv: (kv[1], kv[0]))[0] for t, v in votes.items()}
    game_months = {e2x.month_of(g.date_used) for g in games}
    months_needed = game_months | {f"{s[0].year:04d}-{s[0].month:02d}" for s in span.values()}
    ids = {g.white_fide_id for g in games} | {g.black_fide_id for g in games}
    lists, _pool = e2x.load_lists({m for m in months_needed if m}, ids, set())
    out: dict[str, list[tuple]] = {tc: [] for tc in TCS}
    for g in games:
        tc = tour_tc.get(g.tour)
        if not tc or not (g.white_fide_id.isdigit() and g.black_fide_id.isdigit()):
            continue
        s0, s1 = span[g.tour]
        start = s0 if (s1 - s0).days <= 30 else e2x.to_date(g.date_used)
        lst = lists.get((tc, f"{start.year:04d}-{start.month:02d}"))
        if not lst:
            continue
        w, b = lst.get(g.white_fide_id), lst.get(g.black_fide_id)
        if w is None or b is None:
            continue
        s = 1.0 if g.result == "1-0" else 0.0 if g.result == "0-1" else 0.5
        out[tc].append((e2x.month_of(g.date_used), g.tour, g.white_fide_id, g.black_fide_id, w, b, s,
                        e2x.e0_white(w, b, tc, s0)))
    return out, dict(meta)


def main() -> int:
    e2 = json.loads((ROOT / "analysis" / "aggregates" / "E2_broadcast.json").read_text(encoding="utf-8"))
    smp, meta = sample()
    result: dict = {"cutoff": meta, "guard": {"gap_min": guard.GAP_MIN, "favourite_min": guard.FAV_MIN}}
    for tc in TCS:
        rr = e2["rolling"][tc]
        S = smp[tc]
        months = sorted({row[0] for row in S})
        draws_by_month: dict[str, Counter] = {m: Counter() for m in months}
        games_by_month: dict[str, list[tuple]] = {m: [] for m in months}
        for m, tour, w, b, rw, rb, s, e0 in S:
            mid = e2x.band100_mid((rw + rb) // 2)
            draws_by_month[m][(mid, s == 0.5)] += 1
            games_by_month[m].append((w, b, rw, rb, s, e0))
        per_month, valid = {}, []
        bins = {k: [e2x.new_bin() for _ in range(e2x.BINS)] for k in ("rung2", "guarded")}
        regions = {name: {k: defaultdict(list) for k in ("layer0", "rung2", "guarded")}
                   for name in ("farming", "r17", "r17_level_below_2300")}
        clusters = {name: {k: [] for k in ("layer0", "rung2", "guarded")} for name in regions}
        counts = Counter()
        cal6 = []
        for m in rr["test_months"]:
            par = tuple(rr["per_month"][m]["params"][k] for k in ("kappa", "eta", "alpha", "beta", "gamma"))
            lo, hi = e2x.month_add(m, -e2x.WINDOW), e2x.month_add(m, -1)
            dr: Counter = Counter()
            tot: Counter = Counter()
            for mm in months:
                if lo <= mm <= hi:
                    for (mid, is_draw), n in draws_by_month[mm].items():
                        tot[mid] += n
                        dr[mid] += n if is_draw else 0
            draw_rate = {k: dr[k] / tot[k] for k in tot}
            sums = dict.fromkeys(("ll2", "ll0", "ll2g", "brier2", "brier0", "brier2g", "rps2", "rps0", "rps2g"), 0.0)
            n = 0
            for w, b, rw, rb, s, e0 in games_by_month[m]:
                x, level = rw - rb, (rw + rb) // 2
                mid = e2x.band100_mid(level)
                pw, pd, pl = e2x.probs(par, x, mid)
                e2v = pw + pd / 2.0
                e0c = min(max(e0, 0.002), 0.998)
                dd = min(draw_rate.get(mid, 0.3), 2 * e0c - 0.002, 2 * (1 - e0c) - 0.002)
                qw, qd, ql = e0c - dd / 2.0, dd, 1.0 - e0c - dd / 2.0
                eg, binds = guard.guard_own(e2v, rw, rb)
                gw, gd, gl = e6.three_way(eg, pd) if binds else (pw, pd, pl)
                n += 1
                sums["ll2"] -= math.log(pw if s == 1.0 else pd if s == 0.5 else pl)
                sums["ll0"] -= math.log(qw if s == 1.0 else qd if s == 0.5 else ql)
                sums["ll2g"] -= math.log(gw if s == 1.0 else gd if s == 0.5 else gl)
                sums["brier2"] += (s - e2v) ** 2
                sums["brier0"] += (s - e0) ** 2
                sums["brier2g"] += (s - eg) ** 2
                sums["rps2"] += e2x.rps(pw, pd, pl, s)
                sums["rps0"] += e2x.rps(qw, qd, ql, s)
                sums["rps2g"] += e2x.rps(gw, gd, gl, s)
                fav_white = x >= 0
                sf = s if fav_white else 1.0 - s
                e2f, e0f, egf = (e2v, e0, eg) if fav_white else (1.0 - e2v, 1.0 - e0, 1.0 - eg)
                k = min(abs(x) // 50, e2x.BINS - 1)
                e2x.add_bin(bins["rung2"][k], sf, e2f, e0f, s == 0.5, pd)
                e2x.add_bin(bins["guarded"][k], sf, egf, e0f, s == 0.5, pd)
                cal6.append((abs(x), sf, e0f, egf))
                fav_id, r_fav = (w, rw) if fav_white else (b, rb)
                in_r17 = guard.in_region(r_fav, r_fav - abs(x))
                counts["games"] += 1
                if in_r17:
                    counts["r17_games"] += 1
                    counts["r17_binds"] += binds
                    if level < 2300:
                        counts["r17_level_below_2300"] += 1
                for name, inside in (("farming", abs(x) >= 400 and level >= 2300), ("r17", in_r17),
                                     ("r17_level_below_2300", in_r17 and level < 2300)):
                    if not inside:
                        continue
                    for key, e in (("layer0", e0f), ("rung2", e2f), ("guarded", egf)):
                        regions[name][key][m].append(sf - e)
                        clusters[name][key].append((int(fav_id), sf - e))
            sums["n"] = n
            per_month[m] = sums
            ref = rr["per_month"][m]
            valid.append(max(abs(sums[k] - ref[k]) for k in ("ll2", "ll0", "brier2", "brier0", "rps2", "rps0")))
            valid.append(abs(n - ref["n"]))
        bins_ok = all(abs(a - b) < 1e-6 for r1, r2 in zip(bins["rung2"], rr["bins"]) for a, b in zip(r1, r2))
        result[tc] = {
            "test_months": rr["test_months"],
            "reproduces_e2": {"max_abs_difference_of_monthly_sums": max(valid), "bins_equal": bins_ok},
            "per_month": per_month,
            "bins_guarded": bins["guarded"],
            "counts": dict(counts),
            "calibration_e6_rule": e6.calib_mae([(x, s, a, b) for x, s, a, b in cal6]),
            "regions": {name: {key: e6.boot(v, 0.01) for key, v in r.items()} for name, r in regions.items()},
            "regions_players": {name: {key: e6.boot_cluster(v) for key, v in r.items()} for name, r in clusters.items()},
        }
        print(f"{tc}: reproduces E2 within {max(valid):.2e}, bins equal {bins_ok}; R17 games {counts['r17_games']}, "
              f"guard binds {counts['r17_binds']}", file=sys.stderr, flush=True)
    json.dump(result, sys.stdout, indent=1, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
