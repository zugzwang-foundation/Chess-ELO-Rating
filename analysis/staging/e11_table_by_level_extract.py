#!/usr/bin/env python3
"""E11 extraction: the table calibrated by level, rung 2 version 2 (session ELO-6, Phase 1; needs data/).

Implements docs/specs/SPEC-TABLE-FIT_v1_1.md. Builds E2's sample with E2's own functions through E10's builder
(analysis/e10_guard_extract.py, which enforces the data cutoff: no broadcast file after 2026-09, no game dated after
2026-09-30), refits the table with the level-dependent slope kappa(L) = kappa exp(lambda (L - 2000)/400) on E2's 21
rolling test months (2025-01 to 2026-09, each from the 36 months before it) and on the last 36 months (the published
fit), and evaluates on the same games, months and draw rates three forecasts: the v2 table, Freeze 1's table (rung 2
as E2 fitted it for each month) and Layer 0. It first reproduces E2's monthly sums and calibration bins for Freeze
1's table and Layer 0. Then: E2's sums and bins for the v2 table; the favourite's residual by level band x 50-point
gap cell and by level band, with cluster-robust standard errors over favourites; the farming region (gap >= 400,
level >= 2300) and the games at levels >= 2300 below a 400-point gap, with E6's month-block and player bootstraps
imported unchanged. If, after lambda, a level pattern remains in a time control (SPEC-TABLE-FIT v1.1 section 4.6),
the draw tail gamma(L) = gamma exp(mu (L - 2000)/400) is added there and everything is redone with it. Only
aggregates leave the script. Staged under analysis/staging/ until Freeze 3 (D-0011, reading 1).

Usage: python3 analysis/staging/e11_table_by_level_extract.py > analysis/staging/aggregates/E11_table_by_level.json
"""
from __future__ import annotations

import json
import math
import sys
from collections import Counter, defaultdict
from multiprocessing import Pool
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "analysis" / "staging"))
sys.path.insert(0, str(ROOT / "analysis"))
sys.path.insert(0, str(ROOT / "src"))
import e2_broadcast_extract as e2x  # noqa: E402  (E2's model, bins and helpers, unchanged)
import e6_rungs_extract as e6  # noqa: E402  (E6's bootstraps, unchanged)
import e10_guard_extract as e10  # noqa: E402  (E2's sample with the cutoff, unchanged)
import table_v2 as t2  # noqa: E402
import table_v2_fit as tf  # noqa: E402

TCS = e2x.TCS
BAND, MIN_CELL, ALPHA = 0.01, 1000, 0.05
MODELS = ("v2", "v1", "l0")


def phi(z: float) -> float:
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def cr1(clusters: dict) -> dict:
    """Mean of a per-game residual with its cluster-robust standard error over favourites (CR1), from per-cluster
    [sum of residuals, games, sum of scores, sum of expectations]."""
    n = sum(v[1] for v in clusters.values())
    if not n:
        return {"n": 0}
    tot = sum(v[0] for v in clusters.values())
    mean = tot / n
    g = len(clusters)
    ss = sum((v[0] - v[1] * mean) ** 2 for v in clusters.values())
    se = math.sqrt(ss * g / (g - 1)) / n if g > 1 else None
    return {"n": n, "clusters": g, "mean": mean, "se": se, "score": sum(v[2] for v in clusters.values()) / n,
            "e": sum(v[3] for v in clusters.values()) / n}


def level_pattern(bands: dict) -> dict:
    """SPEC-TABLE-FIT v1.1 section 4.6: bands with at least 1,000 test games; one-sided z-tests of the pooled residual
    against the nearer bound of +/-0.01 with the clustered standard error; Holm-Bonferroni at a familywise 5 %."""
    rows = []
    for mid, st in sorted(bands.items(), key=lambda kv: int(kv[0])):
        if st["n"] >= MIN_CELL and st["se"]:
            z = (abs(st["mean"]) - BAND) / st["se"]
            rows.append({"band": int(mid), "n": st["n"], "mean": st["mean"], "se": st["se"], "p": 1.0 - phi(z)})
    order = sorted(range(len(rows)), key=lambda i: rows[i]["p"])
    stop = False
    for rank, i in enumerate(order):
        rows[i]["outside"] = False
        if not stop and rows[i]["p"] <= ALPHA / (len(rows) - rank):
            rows[i]["outside"] = True
        else:
            stop = True
    return {"bands_tested": rows, "holds": any(r["outside"] for r in rows)}


def fit_task(task: tuple) -> dict:
    cells, start, tail = task
    return tf.fit(cells, start, tail)


def evaluate(rr: dict, months: list[str], fits: dict, games_by_month: dict, draws_by_month: dict) -> dict:
    """The three forecasts on every test month; sums, bins (E2's format) and the residual groups."""
    per_month, valid = {}, []
    bins = {"v2": [e2x.new_bin() for _ in range(e2x.BINS)], "v1": [e2x.new_bin() for _ in range(e2x.BINS)]}
    colour = {"white": [e2x.new_bin() for _ in range(e2x.BINS)], "black": [e2x.new_bin() for _ in range(e2x.BINS)]}
    farming = [e2x.new_bin() for _ in range(e2x.BINS)]
    cells = {k: defaultdict(lambda: defaultdict(lambda: [0.0, 0, 0.0, 0.0])) for k in MODELS}
    bands = {k: defaultdict(lambda: defaultdict(lambda: [0.0, 0, 0.0, 0.0])) for k in MODELS}
    band_months = {k: defaultdict(lambda: defaultdict(list)) for k in MODELS}
    regions = {name: {k: defaultdict(list) for k in MODELS} for name in ("farming", "top_below_400")}
    region_items = {name: {k: [] for k in MODELS} for name in regions}
    region_clusters = {name: {k: defaultdict(lambda: [0.0, 0, 0.0, 0.0]) for k in MODELS} for name in regions}
    for m in rr["test_months"]:
        p1 = tuple(rr["per_month"][m]["params"][k] for k in ("kappa", "eta", "alpha", "beta", "gamma"))
        p2 = tf.par_of(fits[m])
        lo, hi = e2x.month_add(m, -e2x.WINDOW), e2x.month_add(m, -1)
        dr: Counter = Counter()
        tot: Counter = Counter()
        for mm in months:
            if lo <= mm <= hi:
                for (mid, is_draw), n in draws_by_month[mm].items():
                    tot[mid] += n
                    dr[mid] += n if is_draw else 0
        draw_rate = {k: dr[k] / tot[k] for k in tot}
        sums = dict.fromkeys(("ll_v2", "ll_v1", "ll_l0", "brier_v2", "brier_v1", "brier_l0", "rps_v2", "rps_v1",
                              "rps_l0"), 0.0)
        n = 0
        for w, b, rw, rb, s, e0 in games_by_month[m]:
            x, level = rw - rb, (rw + rb) // 2
            mid = e2x.band100_mid(level)
            vw, vd, vl = t2.probs(p2, x, mid)
            ev2 = vw + vd / 2.0
            pw, pd, pl = e2x.probs(p1, x, mid)
            ev1 = pw + pd / 2.0
            e0c = min(max(e0, 0.002), 0.998)
            dd = min(draw_rate.get(mid, 0.3), 2 * e0c - 0.002, 2 * (1 - e0c) - 0.002)
            qw, qd, ql = e0c - dd / 2.0, dd, 1.0 - e0c - dd / 2.0
            n += 1
            pick = (lambda a, d, l_: a if s == 1.0 else d if s == 0.5 else l_)
            sums["ll_v2"] -= math.log(pick(vw, vd, vl))
            sums["ll_v1"] -= math.log(pick(pw, pd, pl))
            sums["ll_l0"] -= math.log(pick(qw, qd, ql))
            sums["brier_v2"] += (s - ev2) ** 2
            sums["brier_v1"] += (s - ev1) ** 2
            sums["brier_l0"] += (s - e0) ** 2
            sums["rps_v2"] += e2x.rps(vw, vd, vl, s)
            sums["rps_v1"] += e2x.rps(pw, pd, pl, s)
            sums["rps_l0"] += e2x.rps(qw, qd, ql, s)
            fav_white = x >= 0
            sf = s if fav_white else 1.0 - s
            ef = {"v2": ev2 if fav_white else 1.0 - ev2, "v1": ev1 if fav_white else 1.0 - ev1,
                  "l0": e0 if fav_white else 1.0 - e0}
            k = min(abs(x) // 50, e2x.BINS - 1)
            e2x.add_bin(bins["v2"][k], sf, ef["v2"], ef["l0"], s == 0.5, vd)
            e2x.add_bin(bins["v1"][k], sf, ef["v1"], ef["l0"], s == 0.5, pd)
            e2x.add_bin((colour["white"] if fav_white else colour["black"])[k], sf, ef["v2"], ef["l0"], s == 0.5, vd)
            fav_id = int(w if fav_white else b)
            in_farming = abs(x) >= 400 and level >= 2300
            if in_farming:
                e2x.add_bin(farming[k], sf, ef["v2"], ef["l0"], s == 0.5, vd)
            cell = f"{mid}|{k * 50}"
            for key in MODELS:
                r = sf - ef[key]
                c = cells[key][cell][fav_id]
                c[0] += r
                c[1] += 1
                c[2] += sf
                c[3] += ef[key]
                bnd = bands[key][mid][fav_id]
                bnd[0] += r
                bnd[1] += 1
                bnd[2] += sf
                bnd[3] += ef[key]
                band_months[key][mid][m].append(r)
                for name, inside in (("farming", in_farming), ("top_below_400", level >= 2300 and abs(x) < 400)):
                    if inside:
                        regions[name][key][m].append(r)
                        region_items[name][key].append((fav_id, r))
                        rc = region_clusters[name][key][fav_id]
                        rc[0] += r
                        rc[1] += 1
                        rc[2] += sf
                        rc[3] += ef[key]
        sums["n"] = n
        per_month[m] = {**sums, "params_v2": {name: fits[m][name] for name in t2.NAMES}}
        ref = rr["per_month"][m]
        valid.append(max(abs(sums["ll_v1"] - ref["ll2"]), abs(sums["ll_l0"] - ref["ll0"]), abs(sums["brier_v1"] - ref["brier2"]),
                         abs(sums["brier_l0"] - ref["brier0"]), abs(sums["rps_v1"] - ref["rps2"]), abs(sums["rps_l0"] - ref["rps0"]),
                         abs(n - ref["n"])))
    bins_equal = all(abs(a - b) < 1e-6 for r1, r2 in zip(bins["v1"], rr["bins"]) for a, b in zip(r1, r2))
    return {
        "reproduces_e2": {"max_abs_difference_of_monthly_sums": max(valid), "bins_equal": bins_equal},
        "per_month": per_month,
        "bins_v2_l0": bins["v2"], "bins_v1_l0": bins["v1"],
        "white_favourite_bins_v2": colour["white"], "black_favourite_bins_v2": colour["black"], "farming_bins_v2": farming,
        "cells": {key: {c: cr1(v) for c, v in sorted(cells[key].items())} for key in MODELS},
        "bands": {key: {str(mid): {**cr1(bands[key][mid]), "month_block": e6.boot(band_months[key][mid], BAND)}
                        for mid in sorted(bands[key])} for key in MODELS},
        "regions": {name: {key: {**cr1(region_clusters[name][key]), "month_block": e6.boot(regions[name][key], BAND),
                                 "players": e6.boot_cluster(region_items[name][key])} for key in MODELS}
                    for name in regions},
    }


def main() -> int:
    e2 = json.loads((ROOT / "analysis" / "aggregates" / "E2_broadcast.json").read_text(encoding="utf-8"))
    smp, meta = e10.sample()
    out: dict = {"cutoff": meta, "spec": "docs/specs/SPEC-TABLE-FIT_v1_1.md", "band_mids": list(t2.BAND_MIDS),
                 "min_cell": MIN_CELL, "tolerance": BAND, "rolling": {}, "final_fit": {}}
    with Pool(8) as pool:
        for tc in TCS:
            rr = e2["rolling"][tc]
            S = smp[tc]
            months = sorted({row[0] for row in S})
            cells_by_month: dict[str, Counter] = {m: Counter() for m in months}
            draws_by_month: dict[str, Counter] = {m: Counter() for m in months}
            games_by_month: dict[str, list[tuple]] = {m: [] for m in months}
            for m, tour, w, b, rw, rb, s, e0 in S:
                mid = e2x.band100_mid((rw + rb) // 2)
                cells_by_month[m][(rw - rb, mid, s)] += 1
                draws_by_month[m][(mid, s == 0.5)] += 1
                games_by_month[m].append((w, b, rw, rb, s, e0))

            def window_cells(lo: str, hi: str) -> list[tuple]:
                agg = Counter()
                for mm in months:
                    if lo <= mm <= hi:
                        agg.update(cells_by_month[mm])
                return [(x, (mid - 2000.0) / 400.0, s, float(wt)) for (x, mid, s), wt in sorted(agg.items())]

            test = rr["test_months"]
            starts = {m: tuple(rr["per_month"][m]["params"][k] for k in ("kappa", "eta", "alpha", "beta", "gamma"))
                      for m in test}
            wins = {m: window_cells(e2x.month_add(m, -e2x.WINDOW), e2x.month_add(m, -1)) for m in test}
            f1 = e2["final_fit"][tc]
            final_start = tuple(f1[k] for k in ("kappa", "eta", "alpha", "beta", "gamma"))
            final_cells = window_cells(f1["from"], f1["to"])
            lam_fits = dict(zip(test, pool.map(fit_task, [(wins[m], starts[m], False) for m in test], chunksize=1)))
            res = evaluate(rr, months, lam_fits, games_by_month, draws_by_month)
            res["level_pattern"] = level_pattern(res["bands"]["v2"])
            out["rolling"][tc] = {"test_months": test, "window_months": e2x.WINDOW, "lambda": res}
            out["final_fit"][tc] = {"from": f1["from"], "to": f1["to"], "lambda": tf.fit(final_cells, final_start, False)}
            print(f"{tc}: reproduces E2 within {res['reproduces_e2']['max_abs_difference_of_monthly_sums']:.2e}, bins "
                  f"equal {res['reproduces_e2']['bins_equal']}; level pattern after lambda: {res['level_pattern']['holds']}",
                  file=sys.stderr, flush=True)
            if res["level_pattern"]["holds"]:
                tail_fits = dict(zip(test, pool.map(fit_task, [(wins[m], starts[m], True) for m in test], chunksize=1)))
                tres = evaluate(rr, months, tail_fits, games_by_month, draws_by_month)
                tres["level_pattern"] = level_pattern(tres["bands"]["v2"])
                out["rolling"][tc]["tail"] = tres
                out["final_fit"][tc]["tail"] = tf.fit(final_cells, final_start, True)
                print(f"{tc}: draw tail fitted; level pattern after it: {tres['level_pattern']['holds']}", file=sys.stderr,
                      flush=True)
    json.dump(out, sys.stdout, indent=1, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
