#!/usr/bin/env python3
"""E18 extraction: the self-calibrating tables, the three-way test and the parameters over time (SPEC-SELFCAL v1.0;
session ELO-8, Phase 3; needs data/).

Builds E2's sample (standard) through E10's builder over every broadcast file on disk (2020-01 to 2026-09; no game dated
after 2026-09-30), takes each year's window by SPEC-SELFCAL §4 (analysis/e18_coverage_extract.py's rule, checked against
its aggregate), and for every year with a window:
  - the rule of choice (§5): where the window holds 12 test months after at least 10 months, rolling fits on each test
    month of form E and form P (no colour term by level, no tail), then of the chosen slope with zeta, compared on the
    selection months by the month-block bootstrap interval of the log-loss difference; then v1.1 §4.6's level-pattern
    condition for the draw tail on the selection months; otherwise the previous year's form (the first: E with the tail);
  - the published table: the chosen form fitted on the whole window, within the caps of §6 relative to the previous
    year's table (none for the first), with its covariance;
  - the confirmation months: the chosen form's rolling fits against Layer 0 and against the table in force;
  - the three-way test (§7) on the year's games: table 8.1.2 as FIDE applied it (E2's three-outcome split with the
    window's draw rates), the first table kept frozen, the year's table; log-loss and Brier with month-block intervals,
    overall and by level band; calibration by level band and gap and by level band;
  - the parameters over time (§8) with intervals from 2,000 parametric draws, beside table 8.1.2's values.
Writes analysis/aggregates/E18_selfcal.json: counts, sums, fitted values and test results only. Python standard library
only.

Usage: python3 analysis/e18_selfcal_extract.py > analysis/aggregates/E18_selfcal.json
"""
from __future__ import annotations

import json
import math
import sys
from collections import Counter, defaultdict
from multiprocessing import Pool
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
sys.path.insert(0, str(ROOT / "src"))
import e2_broadcast_extract as e2x  # noqa: E402  (E2's helpers, unchanged)
import e6_rungs_extract as e6  # noqa: E402  (E6's month-block bootstrap and three-outcome split, unchanged)
import e10_guard_extract as e10  # noqa: E402  (E2's sample with the cutoff, unchanged)
import e11_table_by_level_extract as e11  # noqa: E402  (E11's clustered residual and level-pattern test, unchanged)
import e18_coverage_extract as cov  # noqa: E402  (SPEC-SELFCAL §4's windows)
import layer0  # noqa: E402
import selfcal_fit as sf  # noqa: E402
from layer2 import table_v2 as t2  # noqa: E402

TC = "standard"
FREEZE3 = t2.load((ROOT / "params" / "table_fit_2026-10b.yaml").read_text(encoding="utf-8"), TC)
START = dict(zip(t2.NAMES, FREEZE3["par"]), zeta=0.0)          # every fit's deterministic start: Freeze 3's table
FIRST_FORM = {"slope": "E", "colour_by_level": False, "tail": True}   # v1.1's standard form, as E11 chose it
CAPS = {"kappa": 0.05, "lambda": 0.05, "eta": 5.0, "zeta": 5.0, "alpha": 0.20, "beta": 0.10, "gamma": 0.10, "mu": 0.05}
KNOT_CAP = 0.05
TEST, MIN_TRAIN, SELECT = 12, 10, 6
BAND, MIN_CELL, MIN_SHOW, ALPHA = 0.01, 1000, 200, 0.05
FORECASTS = ("l0", "first", "year")


def window_cells(cells_by_month: dict, ms: list[str]) -> list[tuple]:
    agg = Counter()
    for m in ms:
        agg.update(cells_by_month.get(m, {}))
    return [(x, mid, s, float(w)) for (x, mid, s), w in sorted(agg.items())]


def draw_rates(draws_by_month: dict, ms: list[str]) -> dict[int, float]:
    dr, tot = Counter(), Counter()
    for m in ms:
        for (mid, is_draw), n in draws_by_month.get(m, {}).items():
            tot[mid] += n
            dr[mid] += n if is_draw else 0
    return {k: dr[k] / tot[k] for k in tot}


def fit_task(task: tuple) -> dict:
    form, cells, start, caps = task
    return sf.fit(form, cells, start, caps)


def start_for(form: dict, base: dict) -> dict:
    """A deterministic start for a form from a fitted table: P's knots at the base table's kappa(L)."""
    out = dict(base["par"]) if "par" in base else dict(base)
    if form["slope"] == "P":
        tab = base if "par" in base else {"form": {"slope": "E", "colour_by_level": True, "tail": True}, "par": base}
        out.update({f"kappa_{k}": sf.kappa_at(tab, k) for k in sf.KNOTS})
    return out


def caps_for(form: dict, prev: dict | None) -> dict | None:
    """SPEC-SELFCAL §6: each capped quantity within its cap of the previous table's; a dropped term moves toward zero by
    at most its cap and is fixed there."""
    if prev is None:
        return None
    pp = prev["par"]
    out = {}
    if form["slope"] == "E" and prev["form"]["slope"] == "E":
        out["kappa"] = (pp["kappa"] - CAPS["kappa"], pp["kappa"] + CAPS["kappa"])
        out["lambda"] = (pp["lambda"] - CAPS["lambda"], pp["lambda"] + CAPS["lambda"])
    elif form["slope"] == "P":
        for k in sf.KNOTS:
            v = sf.kappa_at(prev, k)
            out[f"kappa_{k}"] = (v - KNOT_CAP, v + KNOT_CAP)
    for k in ("eta", "alpha", "beta", "gamma"):
        out[k] = (pp[k] - CAPS[k], pp[k] + CAPS[k])
    for k, on in (("zeta", form["colour_by_level"]), ("mu", form["tail"])):
        v = pp.get(k, 0.0)
        if on:
            out[k] = (v - CAPS[k], v + CAPS[k])
        else:                                 # dropped (or absent): toward zero by at most the cap, fixed there
            fixed = 0.0 if abs(v) <= CAPS[k] else v - math.copysign(CAPS[k], v)
            out[k] = (fixed, fixed)
    return out


def forecast(table: dict, x: int, mid: int) -> tuple[float, float, float]:
    return sf.probs(table, x, mid)


def ll_of(p: tuple, s: float) -> float:
    return -math.log(p[0] if s == 1.0 else p[1] if s == 0.5 else p[2])


def holm(rows: list[dict]) -> int:
    """Rule (a): cells with at least 1,000 games, one-sided z-tests against the nearer bound of +/-0.01 with the
    clustered standard error, Holm-Bonferroni at a familywise 5 %; the number significantly outside."""
    tested = [r for r in rows if r["n"] >= MIN_CELL and r.get("se")]
    ps = sorted(1.0 - e11.phi((abs(r["mean"]) - BAND) / r["se"]) for r in tested)
    out = 0
    for rank, p in enumerate(ps):
        if p <= ALPHA / (len(ps) - rank):
            out += 1
        else:
            break
    return out


PAIRS = (("year", "first"), ("year", "l0"), ("first", "l0"), ("year_prevform", "first"), ("year", "year_prevform"),
         ("year_prevform", "l0"))


def evaluate(tables: dict[str, dict], games: dict[str, list], rates: dict[int, float]) -> dict:
    """Log-loss, Brier and calibration of the given forecasts on the given months' games."""
    per_month = {m: {f: {"n": 0, "ll": 0.0, "brier": 0.0} for f in tables} for m in games}
    pairs = [pr for pr in PAIRS if pr[0] in tables and pr[1] in tables]
    diffs = {pair: defaultdict(list) for pair in pairs}
    bdiffs = {pair: defaultdict(list) for pair in pairs}
    band_ll = {f: defaultdict(lambda: defaultdict(list)) for f in tables}
    band_diff = {pair: defaultdict(lambda: defaultdict(list)) for pair in diffs}
    cells = {f: defaultdict(lambda: defaultdict(lambda: [0.0, 0, 0.0, 0.0])) for f in tables}
    bands = {f: defaultdict(lambda: defaultdict(lambda: [0.0, 0, 0.0, 0.0])) for f in tables}
    for m, rows in sorted(games.items()):
        for w, b, rw, rb, s, e0 in rows:
            x, mid = rw - rb, e2x.band100_mid((rw + rb) // 2)
            ll, ev = {}, {}
            for f, tab in tables.items():
                if f == "l0":
                    p = e6.three_way(e0, rates.get(mid, 0.3))
                    ev[f] = e0
                else:
                    p = forecast(tab, x, mid)
                    ev[f] = p[0] + p[1] / 2.0
                ll[f] = ll_of(p, s)
                pm = per_month[m][f]
                pm["n"] += 1
                pm["ll"] += ll[f]
                pm["brier"] += (s - ev[f]) ** 2
                band_ll[f][mid][m].append(ll[f])
            for pair in diffs:
                d = ll[pair[0]] - ll[pair[1]]
                diffs[pair][m].append(d)
                band_diff[pair][mid][m].append(d)
                bdiffs[pair][m].append((s - ev[pair[0]]) ** 2 - (s - ev[pair[1]]) ** 2)
            fav_white = x >= 0
            sf_ = s if fav_white else 1.0 - s
            fav = int(w if fav_white else b)
            k = min(abs(x) // 50, e2x.BINS - 1)
            for f in tables:
                ef = ev[f] if fav_white else 1.0 - ev[f]
                for acc in (cells[f][f"{mid}|{k * 50}"][fav], bands[f][mid][fav]):
                    acc[0] += sf_ - ef
                    acc[1] += 1
                    acc[2] += sf_
                    acc[3] += ef
    out = {"months": sorted(games), "per_month": per_month}
    tot = {f: {k: sum(per_month[m][f][k] for m in per_month) for k in ("n", "ll", "brier")} for f in tables}
    out["means"] = {f: {"n": v["n"], "ll": v["ll"] / v["n"], "brier": v["brier"] / v["n"]} for f, v in tot.items() if v["n"]}
    out["differences"] = {f"{a}-{b}": e6.boot(dict(diffs[(a, b)])) for (a, b) in diffs if diffs[(a, b)]}
    out["differences_brier"] = {f"{a}-{b}": e6.boot(dict(bdiffs[(a, b)])) for (a, b) in bdiffs if bdiffs[(a, b)]}
    out["by_band"] = {f: {str(mid): e6.boot(dict(v)) for mid, v in sorted(band_ll[f].items())} for f in tables}
    out["by_band_differences"] = {f"{a}-{b}": {str(mid): e6.boot(dict(v)) for mid, v in sorted(band_diff[(a, b)].items())}
                                  for (a, b) in band_diff if band_diff[(a, b)]}
    out["cells"] = {}
    for f in tables:
        rows = []
        for c, v in sorted(cells[f].items(), key=lambda kv: (int(kv[0].split("|")[0]), int(kv[0].split("|")[1]))):
            st = e11.cr1(v)
            if st["n"] >= MIN_SHOW:
                rows.append({"cell": c, **st})
        out["cells"][f] = {"shown": rows, "tested": sum(1 for r in rows if r["n"] >= MIN_CELL),
                           "outside": holm(rows)}
    out["bands"] = {f: {str(mid): e11.cr1(v) for mid, v in sorted(bands[f].items())} for f in tables}
    out["level_pattern"] = {f: e11.level_pattern(out["bands"][f]) for f in tables}
    return out, {f"{a}-{b}": dict(v) for (a, b), v in diffs.items() if v}, \
        {f"{a}-{b}": dict(v) for (a, b), v in bdiffs.items() if v}


def derived(table: dict) -> dict:
    """SPEC-SELFCAL §8's quantities for one table."""
    return {
        "white_edge_points": {str(m): sf.eta_at(table, m) for m in (2050, 2450, 2750)},
        "white_score_equal": {str(m): (lambda p: p[0] + p[1] / 2.0)(sf.probs(table, 0, m)) for m in (2050, 2450, 2750)},
        "draw_rate_equal": {str(m): sf.nu0(table, m) / (2.0 + sf.nu0(table, m)) for m in sf.BAND_MIDS},
        "slope_even": {str(m): sf.slope_at_zero(table, m) for m in (2050, 2450, 2750)},
        "favourite_100_at_2700": sf.expected_effective(table, 100, 2750),
    }


def cap_dependence(f: dict) -> dict:
    """For each derived quantity, the parameters on a bound that move it (a finite-difference test): a quantity that
    depends on a parameter held at a cap has no honest interval from the draws (review finding ELO8-STAT-4)."""
    base = derived({"form": f["form"], "par": f["par"]})
    deps: dict = {}

    def walk(b, path, bumped):
        if isinstance(b, dict):
            for k, v in b.items():
                walk(v, path + [k], bumped)
            return
        x = bumped
        for k in path:
            x = x[k]
        if abs(x - b) > 1e-12:
            deps.setdefault("/".join(path), []).append(name)
    for name in f["on_bound"]:
        par = dict(f["par"])
        par[name] += 1e-4
        walk(base, [], derived({"form": f["form"], "par": par}))
    return deps


def with_intervals(f: dict) -> dict:
    base = derived({"form": f["form"], "par": f["par"]})
    dr = sf.draws(f)
    ds = [derived({"form": f["form"], "par": d}) for d in dr]
    par_iv = {k: list(sf.interval([d[k] for d in dr])) for k in f["par"]}

    def walk(b, path):
        if isinstance(b, dict):
            return {k: walk(v, path + [k]) for k, v in b.items()}
        vals = []
        for d in ds:
            x = d
            for k in path:
                x = x[k]
            vals.append(x)
        lo, hi = sf.interval(vals)
        return {"value": b, "low": lo, "high": hi}
    return {"parameters": {k: {"value": v, "se": f["se"].get(k), "low": par_iv[k][0], "high": par_iv[k][1],
                               "on_bound": f["on_bound"].get(k)} for k, v in f["par"].items()},
            "derived": walk(base, [])}


def table_812() -> dict:
    return {"white_edge_points": 0, "white_score_equal": 0.5, "draw_rate_equal": None,
            "slope_even": t2.slope_812(), "favourite_100_at_2700": float(layer0.expected_score(100))}


def main() -> int:
    smp, meta = e10.sample()
    games_by_month: dict[str, list] = defaultdict(list)
    cells_by_month: dict[str, Counter] = defaultdict(Counter)
    draws_by_month: dict[str, Counter] = defaultdict(Counter)
    std_month = Counter()
    for m, _tour, w, b, rw, rb, s, e0 in smp[TC]:
        mid = e2x.band100_mid((rw + rb) // 2)
        games_by_month[m].append((w, b, rw, rb, s, e0))
        cells_by_month[m][(rw - rb, mid, s)] += 1
        draws_by_month[m][(mid, s == 0.5)] += 1
        std_month[m] += 1
    covg = json.loads((ROOT / "analysis" / "aggregates" / "E18_coverage.json").read_text(encoding="utf-8"))
    wins = {str(y): cov.window(y, std_month) for y in cov.YEARS}
    assert wins == covg["windows"], "the windows differ from E18_coverage.json"
    years = [y for y in sorted(wins) if wins[y]["table"]]
    out: dict = {"spec": "docs/specs/SPEC-SELFCAL_v1_1.md", "cutoff": meta, "table_years": years, "tables": {},
                 "choice": {}, "confirmation": {}, "three_way": {}, "first_form": FIRST_FORM, "caps": CAPS,
                 "knot_cap": KNOT_CAP, "start": "Freeze 3's standard table (params/table_fit_2026-10b.yaml)"}
    prev = None
    fitted: dict[str, dict] = {}
    with Pool(8) as pool:
        for y in years:
            w = wins[y]
            ms = cov.months(w["from"], w["to"])
            choice = {"window_months": len(ms)}
            if len(ms) >= TEST + MIN_TRAIN:
                test = ms[-TEST:]
                sel, conf = test[:SELECT], test[SELECT:]
                choice.update({"test_months": test, "selection": sel, "confirmation": conf})
                train = {m: [mm for mm in ms if mm < m and mm >= layer0.month_add(m, -36)] for m in test}
                tcells = {m: window_cells(cells_by_month, train[m]) for m in test}
                trates = {m: draw_rates(draws_by_month, train[m]) for m in test}

                def rolling(form: dict, starts: dict) -> dict:
                    res = pool.map(fit_task, [(form, tcells[m], starts[m], None) for m in test], chunksize=1)
                    return dict(zip(test, res))

                def ll_months(fits: dict, form: dict, months: list[str]) -> dict:
                    return {m: [ll_of(forecast({"form": form, "par": fits[m]["par"]}, rw - rb,
                                               e2x.band100_mid((rw + rb) // 2)), s)
                                for _w, _b, rw, rb, s, _e0 in games_by_month[m]] for m in months}

                fe = {"slope": "E", "colour_by_level": False, "tail": False}
                fp = {"slope": "P", "colour_by_level": False, "tail": False}
                rf = {"E": rolling(fe, {m: START for m in test})}
                rf["P"] = rolling(fp, {m: start_for(fp, rf["E"][m]) for m in test})
                lle, llp = ll_months(rf["E"], fe, sel), ll_months(rf["P"], fp, sel)
                slope_test = e6.boot({m: [a - b for a, b in zip(llp[m], lle[m])] for m in sel})
                slope = "P" if slope_test["hi"] < 0 else "E"
                base_form = fp if slope == "P" else fe
                fz = dict(base_form, colour_by_level=True)
                rf["Z"] = rolling(fz, {m: dict(rf[slope][m]["par"]) for m in test})
                llz, llb = ll_months(rf["Z"], fz, sel), (llp if slope == "P" else lle)
                colour_test = e6.boot({m: [a - b for a, b in zip(llz[m], llb[m])] for m in sel})
                colour = colour_test["hi"] < 0
                chosen = fz if colour else base_form
                cfits = rf["Z"] if colour else rf[slope]
                bands = defaultdict(lambda: defaultdict(lambda: [0.0, 0, 0.0, 0.0]))
                for m in sel:
                    tab = {"form": chosen, "par": cfits[m]["par"]}
                    for gw, gb, rw, rb, s, _e0 in games_by_month[m]:
                        x, mid = rw - rb, e2x.band100_mid((rw + rb) // 2)
                        p = forecast(tab, x, mid)
                        e = p[0] + p[1] / 2.0
                        fav_white = x >= 0
                        acc = bands[mid][int(gw if fav_white else gb)]
                        acc[0] += (s if fav_white else 1 - s) - (e if fav_white else 1 - e)
                        acc[1] += 1
                lp = e11.level_pattern({str(mid): e11.cr1(v) for mid, v in bands.items()})
                form = dict(chosen, tail=lp["holds"])
                choice.update({"slope_test": slope_test, "slope": slope, "colour_test": colour_test, "colour": colour,
                               "tail_condition": lp, "chosen": form, "made": True})
                if form["tail"]:
                    rf["T"] = rolling(form, {m: dict(cfits[m]["par"], mu=0.0) for m in test})
                    final_roll = rf["T"]
                else:
                    final_roll = cfits
                # the confirmation months: the chosen form's rolling fits against Layer 0 and the table in force
                conf_games = {m: games_by_month[m] for m in conf}
                c_out = {"months": conf, "per_month": {}}
                diffs = {"chosen-l0": defaultdict(list), "chosen-in_force": defaultdict(list)}
                for m in conf:
                    tab = {"form": form, "par": final_roll[m]["par"]}
                    for _w, _b, rw, rb, s, e0 in conf_games[m]:
                        x, mid = rw - rb, e2x.band100_mid((rw + rb) // 2)
                        a = ll_of(forecast(tab, x, mid), s)
                        l0 = ll_of(e6.three_way(e0, trates[m].get(mid, 0.3)), s)
                        diffs["chosen-l0"][m].append(a - l0)
                        if prev is not None:
                            diffs["chosen-in_force"][m].append(a - ll_of(forecast(prev, x, mid), s))
                c_out["differences"] = {k: e6.boot(dict(v)) for k, v in diffs.items() if v}
                out["confirmation"][y] = c_out
                choice["rolling"] = {k: {m: {"par": v[m]["par"], "n": v[m]["n"], "loglik": v[m]["loglik"]}
                                         for m in test} for k, v in rf.items()}
            else:
                form = dict(prev["form"]) if prev is not None else dict(FIRST_FORM)
                choice.update({"made": False, "chosen": form,
                               "reason": "fewer than 22 months in the window: the previous form is kept"
                                         if prev is not None else "the first table: v1.1's form for standard"})
            caps = caps_for(form, prev)
            start = start_for(form, prev) if prev is not None else start_for(form, START)
            cells_w = window_cells(cells_by_month, ms)
            f = sf.fit(form, cells_w, start, caps)
            tab = {"form": form, "par": f["par"]}
            fitted[y] = tab
            extra = {}
            if prev is not None and form != prev["form"]:
                # the table in the form v1.2's 24 training months would have kept (SPEC-SELFCAL §13), within the caps
                fk = sf.fit(prev["form"], cells_w, start_for(prev["form"], prev), caps_for(prev["form"], prev))
                fitted[f"{y}_prevform"] = {"form": prev["form"], "par": fk["par"]}
                extra["previous_form"] = {"form": prev["form"], "par": fk["par"], "se": fk["se"],
                                          "on_bound": fk["on_bound"], "loglik": fk["loglik"],
                                          "derived": derived({"form": prev["form"], "par": fk["par"]})}
            if f["on_bound"]:
                fu = sf.fit(form, cells_w, start, None)          # the same form without caps, for comparison
                extra["uncapped"] = {"par": fu["par"], "se": fu["se"], "loglik": fu["loglik"],
                                     "derived": derived({"form": form, "par": fu["par"]})}
            out["choice"][y] = choice
            out["tables"][y] = {"window": [ms[0], ms[-1]], "months": len(ms), "games": f["n"], "cells": f["cells"],
                                "form": form, "par": f["par"], "se": f["se"], "free": f["free"], "cov": f["cov"],
                                "on_bound": f["on_bound"],
                                "bounds": {k: [None if math.isinf(v) else v for v in vv] for k, vv in f["bounds"].items()},
                                "caps": caps, "loglik": f["loglik"],
                                "iterations": f["iterations"], "max_abs_score": f["max_abs_score"],
                                "eta_whole": {str(m): sf.eta_whole(tab, m) for m in sf.BAND_MIDS},
                                "kappa_at_band": {str(m): sf.kappa_at(tab, m) for m in sf.BAND_MIDS},
                                "cap_dependence": cap_dependence(f), **extra, **with_intervals(f)}
            prev = tab
    first = years[0]
    pooled_diffs: dict[str, dict] = defaultdict(dict)
    pooled_bdiffs: dict[str, dict] = defaultdict(dict)
    pooled_sums: dict[str, Counter] = defaultdict(Counter)
    for y in years:
        yr_months = sorted(m for m in games_by_month if m[:4] == y)
        w = wins[y]
        rates = draw_rates(draws_by_month, cov.months(w["from"], w["to"]))
        tables = {"l0": None, "first": fitted[first], "year": fitted[y]}
        if f"{y}_prevform" in fitted:
            tables["year_prevform"] = fitted[f"{y}_prevform"]
        res, raw, braw = evaluate(tables, {m: games_by_month[m] for m in yr_months}, rates)
        res["draw_rates"] = {str(k): v for k, v in sorted(rates.items())}
        out["three_way"][y] = res
        for key, per in raw.items():
            if key in ("year-first", "year-l0", "first-l0"):
                pooled_diffs[key].update(per)
        for key, per in braw.items():
            if key in ("year-first", "year-l0", "first-l0"):
                pooled_bdiffs[key].update(per)
        for m, fs in res["per_month"].items():
            for f, v in fs.items():
                if f not in ("l0", "first", "year"):
                    continue
                for k in ("n", "ll", "brier"):
                    pooled_sums[f][k] += v[k]
    out["three_way_pooled"] = {      # every year's games, each forecast by that year's table and draw rates
        "years": years,
        "means": {f: {"n": v["n"], "ll": v["ll"] / v["n"], "brier": v["brier"] / v["n"]} for f, v in pooled_sums.items()},
        "differences": {k: e6.boot(v) for k, v in pooled_diffs.items()},
        "differences_brier": {k: e6.boot(v) for k, v in pooled_bdiffs.items()}}
    out["table_812"] = table_812()
    out["freeze3_reference"] = derived({"form": {"slope": "E", "colour_by_level": False, "tail": True},
                                        "par": dict(START)})
    json.dump(out, sys.stdout, indent=1, sort_keys=True, default=str)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
