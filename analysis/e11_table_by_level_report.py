#!/usr/bin/env python3
"""E11 report: the table calibrated by level (rung 2, version 2), from the E11 aggregate.

Reads analysis/aggregates/E11_table_by_level.json (written by analysis/e11_table_by_level_extract.py;
games from the Lichess broadcast archive, CC BY-SA 4.0) and prints either the evidence page
docs/evidence/E11_table-by-level.md or, with --yaml, the v2 parameter file params/table_fit_2026-10b.yaml. Applies
docs/specs/SPEC-TABLE-FIT_v1_1.md section 4: E2's decision rules (annex T8.2), imported unchanged from
analysis/e2_broadcast_report.py, E10's stage-1 gate, imported unchanged from analysis/e10_guard_report.py, rule (a) by
level band and gap with cluster-robust standard errors over favourites, and R32's slope ratio
(src/layer2/table_v2.py). Python standard library only.

Usage: python3 analysis/e11_table_by_level_report.py > docs/evidence/E11_table-by-level.md
       python3 analysis/e11_table_by_level_report.py --yaml > params/table_fit_2026-10b.yaml
"""
from __future__ import annotations

import json
import math
import sys
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
sys.path.insert(0, str(ROOT / "src"))
import e2_broadcast_report as r2  # noqa: E402  (E2's decision rules, unchanged)
import e10_guard_report as r10  # noqa: E402  (E10's stage-1 gate, unchanged)
from layer2 import table_v2 as t2  # noqa: E402

AGG = ROOT / "analysis" / "aggregates" / "E11_table_by_level.json"
E2AGG = ROOT / "analysis" / "aggregates" / "E2_broadcast.json"
TCS = ("standard", "rapid", "blitz")
BAND, MIN_CELL, ALPHA, PRINT_MIN = 0.01, 1000, 0.05, 200
DIGITS = {"kappa": 4, "lambda": 4, "eta": 2, "alpha": 4, "beta": 4, "gamma": 4, "mu": 4}
PARAM_FILE = "params/table_fit_2026-10b.yaml"
WHO = {"v2": "the v2 table", "v1": "Freeze 1's table", "l0": "Layer 0"}


def n_(x) -> str:
    return f"{int(x):,}"


def s4(x) -> str:
    return "—" if x is None else f"{x:+.4f}"


def s3(x) -> str:
    return "—" if x is None else f"{x:+.3f}"


def band_label(mid: int) -> str:
    if mid == 1450:
        return "below 1500"
    if mid == 2850:
        return "2800 and above"
    return f"{mid - 50}–{mid + 49}"


def chosen(t: dict) -> tuple[str, dict]:
    """The v2 model of a time control: with the draw tail if section 4.6's condition added it, else with lambda."""
    return ("tail", t["tail"]) if "tail" in t else ("lambda", t["lambda"])


def printed(f: dict) -> tuple:
    """The parameters as the parameter file prints them (the published table uses the printed values)."""
    return tuple(float(Decimal(repr(f[k])).quantize(Decimal(10) ** -DIGITS[k], rounding=ROUND_HALF_UP)) for k in t2.NAMES)


def holm(rows: list[dict]) -> list[dict]:
    """One-sided z-tests against the nearer bound of +/-0.01 (clustered SE), Holm-Bonferroni at a familywise 5 %."""
    for r in rows:
        z = (abs(r["mean"]) - BAND) / r["se"]
        r["p"] = 1.0 - r2.phi(z)
    order = sorted(range(len(rows)), key=lambda i: rows[i]["p"])
    stop = False
    for rank, i in enumerate(order):
        rows[i]["outside"] = False
        if not stop and rows[i]["p"] <= ALPHA / (len(rows) - rank):
            rows[i]["outside"] = True
        else:
            stop = True
    return rows


def cell_rule(cells: dict) -> dict:
    """Rule (a) by level band x gap (annex T8.2, "by level band"; D-0011, reading 5)."""
    rows = []
    for key, st in cells.items():
        mid, gap = (int(v) for v in key.split("|"))
        if st["n"] >= MIN_CELL and st.get("se"):
            rows.append({"band": mid, "gap": gap, "n": st["n"], "mean": st["mean"], "se": st["se"]})
    rows.sort(key=lambda r: (r["band"], r["gap"]))
    holm(rows)
    return {"rows": rows, "m": len(rows), "outside": [r for r in rows if r["outside"]],
            "pass": len(rows) > 0 and not any(r["outside"] for r in rows)}


def interval(b: dict) -> str:
    return f"{b['mean']:+.4f} ({b['lo']:+.4f} to {b['hi']:+.4f})" if b.get("n") else "—"


def within(b: dict) -> bool:
    return b["lo"] >= -BAND and b["hi"] <= BAND


def not_outside(b: dict) -> bool:
    """Annex T8.2's "not significantly outside +/-b": the interval overlaps [-b, +b]."""
    return b["hi"] >= -BAND and b["lo"] <= BAND


def analyse(tc: str, res: dict, e2tc: dict) -> dict:
    months = list(res["per_month"])
    pm = {m: dict(res["per_month"][m]) for m in months}
    for m in months:
        pm[m]["d_v2_l0"] = pm[m]["ll_v2"] - pm[m]["ll_l0"]
        pm[m]["d_v2_v1"] = pm[m]["ll_v2"] - pm[m]["ll_v1"]
        pm[m]["d_v1_l0"] = pm[m]["ll_v1"] - pm[m]["ll_l0"]
    n = sum(pm[m]["n"] for m in months)
    tot = {k: sum(pm[m][k] for m in months) / n for k in ("ll_v2", "ll_v1", "ll_l0", "brier_v2", "brier_v1", "brier_l0",
                                                          "rps_v2", "rps_v1", "rps_l0")}
    iv = {k: r2.block_bootstrap(months, pm, k) for k in ("d_v2_l0", "d_v2_v1", "d_v1_l0")}
    c2 = r2.calibration(res["bins_v2_l0"], 0)
    c0 = r2.calibration(res["bins_v2_l0"], 1)
    c1 = r2.calibration(res["bins_v1_l0"], 0)
    ma = {"v2": r2.all_bins_mean_abs(res["bins_v2_l0"], 0), "l0": r2.all_bins_mean_abs(res["bins_v2_l0"], 1),
          "v1": r2.all_bins_mean_abs(res["bins_v1_l0"], 0)}
    gate2, parts2 = r10.gate(c2, iv["d_v2_l0"][1], ma["v2"], ma["l0"], iv["d_v2_l0"][1])
    gate1, parts1 = r10.gate(c1, iv["d_v1_l0"][1], ma["v1"], ma["l0"], iv["d_v1_l0"][1])
    harm_v1 = iv["d_v2_v1"][1] <= 0.002 and ma["v2"] <= ma["v1"] + 0.005
    cells = {k: cell_rule(res["cells"][k]) for k in ("v2", "v1", "l0")}
    return {"n": n, "months": len(months), "tot": tot, "iv": iv, "c2": c2, "c0": c0, "c1": c1, "ma": ma, "gate2": gate2,
            "parts2": parts2, "gate1": gate1, "parts1": parts1, "harm_v1": harm_v1, "cells": cells}


def residual_table(res: dict, P) -> None:
    """The favourite's residual by level band x gap, Freeze 1's table -> the v2 table (cells with 200 games or more)."""
    gaps = list(range(0, 600, 50))
    P("| level band | " + " | ".join(f"{g}–{g + 49}" for g in gaps) + " |")
    P("|---|" + "---|" * len(gaps))
    for mid in t2.BAND_MIDS:
        row = []
        for g in gaps:
            key = f"{mid}|{g}"
            a, b = res["cells"]["v1"].get(key), res["cells"]["v2"].get(key)
            row.append(f"{a['mean']:+.3f} → {b['mean']:+.3f}" if a and a["n"] >= PRINT_MIN else "")
        if any(row):
            P(f"| {band_label(mid)} | " + " | ".join(row) + " |")


def yaml_out(d: dict) -> None:
    print(f"# {PARAM_FILE}: generated by analysis/e11_table_by_level_report.py --yaml; do not edit by hand.")
    print("status: PROVISIONAL-FITTED")
    print("spec: docs/specs/SPEC-TABLE-FIT_v1_1.md")
    print("model: SPEC-TABLE-FIT v1.1 section 2 (annex T3.1, T3.3 with kappa(L) = kappa exp(lambda (L - 2000)/400) and, "
          "where fitted, gamma(L) = gamma exp(mu (L - 2000)/400)); L at the midpoint of the 100-point level band")
    print("source:")
    print('  games: "Lichess broadcast archive, https://database.lichess.org/broadcast/, CC BY-SA 4.0 (attributed)"')
    print('  ratings: "FIDE monthly lists of the game\'s time control, analysed and not redistributed"')
    print('  cutoff: "no broadcast file after 2026-09; games dated after 2026-09-30 dropped"')
    print("evaluation: docs/evidence/E11_table-by-level.md")
    for tc in TCS:
        ff = d["final_fit"][tc]
        kind, f = ("tail", ff["tail"]) if "tail" in ff else ("lambda", ff["lambda"])
        par = printed(f)
        print(f"{tc}:")
        print(f"  fit_window: {{from: \"{ff['from']}\", to: \"{ff['to']}\"}}")
        print(f"  games: {f['n']}")
        for k, v in zip(t2.NAMES, par):
            se = f["se"].get(k)
            se_txt = f"{se:.{DIGITS[k]}f}" if se else "null"
            print(f"  {k}: {{value: {v:.{DIGITS[k]}f}, se: {se_txt}}}")
        print(f"  draw_tail: {str(kind == 'tail').lower()}")
        print(f"  gamma_at_bound: {str(f['gamma_at_bound']).lower()}")
        print("  # R32: m = E'_8.1.2(0) / E'_v2(0) by level band midpoint, two decimals, normative (D-0011, reading 7)")
        print(f"  k_scale_applies: {str(t2.needs_scaling(par)).lower()}")
        print("  k_scale: {" + ", ".join(f"{m}: {t2.ratio_printed(par, m)}" for m in t2.BAND_MIDS) + "}")


def main() -> int:
    d = json.loads(AGG.read_text(encoding="utf-8"))
    if "--yaml" in sys.argv[1:]:
        yaml_out(d)
        return 0
    e2 = json.loads(E2AGG.read_text(encoding="utf-8"))
    out: list[str] = []
    P = out.append
    A, F, K = {}, {}, {}
    for tc in TCS:
        kind, res = chosen(d["rolling"][tc])
        A[tc] = analyse(tc, res, e2["rolling"][tc])
        ff = d["final_fit"][tc]
        F[tc] = ff["tail"] if kind == "tail" else ff["lambda"]
        K[tc] = kind
    s812 = t2.slope_812()

    P("# E11 — The table calibrated by level: rung 2, version 2\n")
    P("Status: REVIEW — evidence for rung 2 of the adoption ladder (session ELO-6, Phase 1), under "
      "`docs/specs/SPEC-TABLE-FIT_v1_1.md` and `docs/decisions/D-0011_rulings-and-freeze-3.md`. Generated by "
      "`analysis/e11_table_by_level_report.py` from `analysis/aggregates/E11_table_by_level.json` "
      "(written by `analysis/e11_table_by_level_extract.py`); do not edit by hand. Licence: CC BY 4.0 "
      f"(`docs/LICENSE-docs.md`). {r2.ATTRIBUTION} Ratings: FIDE's monthly lists, analysed and never redistributed "
      "[V 3]. Every fitted value is PROVISIONAL-FITTED. Frozen in Freeze 3 with the scripts, the aggregate and the "
      "parameter file (D-0011, part B).\n")

    # ------------------------------------------------------------------ in brief
    P("**In brief.**\n")
    lam = "; ".join(f"{tc} {F[tc]['lambda']:.3f} (SE {F[tc]['se']['lambda']:.3f})" for tc in TCS)
    rises = [tc for tc in TCS if F[tc]["lambda"] > 2 * F[tc]["se"]["lambda"]]
    flat = [tc for tc in TCS if abs(F[tc]["lambda"]) <= 2 * F[tc]["se"]["lambda"]]
    P(f"- **The slope by level.** The v2 table replaces the single κ of E2 by κ(L) = κ · exp(λ (L − 2000)/400). Fitted "
      f"on 2023-10 to 2026-09, λ is {lam}: the fitted slope rises with the level in {' and '.join(rises) or 'no time control'}"
      + (f" and does not change with it in {' and '.join(flat)} (λ within two standard errors of zero)" if flat else "")
      + ". " + "; ".join(
          f"{tc}: κ(L) {t2.kappa_at(printed(F[tc]), 1750):.3f} at 1700–1799, {t2.kappa_at(printed(F[tc]), 2350):.3f} at "
          f"2300–2399, {t2.kappa_at(printed(F[tc]), 2750):.3f} at 2700–2799" for tc in TCS) + ".")
    tails = [tc for tc in TCS if K[tc] == "tail"]
    P("- **The draw tail.** " + (f"After λ a level pattern remained in {', '.join(tails)}, so the draw tail γ(L) was "
                                 "added there, as SPEC-TABLE-FIT v1.1 §4.6 orders; the condition is evaluated once and "
                                 "not iterated (section 8)." if tails else
                                 "After λ no level band's residual is significantly outside ±0.01 in any time control, "
                                 "so the draw tail γ(L) is not added (section 8)."))
    for tc in TCS:
        lp = d["rolling"][tc][K[tc]]["level_pattern"]
        out_ = [r for r in lp["bands_tested"] if r["outside"]]
        if out_:
            b1 = d["rolling"][tc][K[tc]]["bands"]["v1"]
            P(f"- **What the slope by level leaves, {tc}.** In {len(out_)} of {len(lp['bands_tested'])} level bands the "
              "favourite's residual, pooled over gaps, stays significantly outside ±0.01 with the v2 table: " + "; ".join(
                  f"{band_label(r['band'])} {r['mean']:+.4f} (SE {r['se']:.4f}; Freeze 1's table "
                  f"{b1[str(r['band'])]['mean']:+.4f})" for r in out_)
              + "." + (" The exponential form that steepens the slope at the top also flattens it at the bottom, where "
                       "Freeze 1's table was within ±0.01 (section 6)." if any(
                           r["band"] < 2000 and abs(b1[str(r["band"])]["mean"]) <= BAND for r in out_) else ""))
    for tc in TCS:
        a = A[tc]
        top = d["rolling"][tc][K[tc]]["regions"]
        P(f"- **{tc.capitalize()}.** Rule (a) by level band × gap (cells of 1,000 test games or more, player-clustered): "
          f"Freeze 1's table {len(a['cells']['v1']['outside'])} of {a['cells']['v1']['m']} cells outside ±0.01, the v2 "
          f"table {len(a['cells']['v2']['outside'])} of {a['cells']['v2']['m']}, Layer 0 {len(a['cells']['l0']['outside'])} "
          f"of {a['cells']['l0']['m']}. At levels of 2300 or more below a 400-point gap the favourite's residual moves "
          f"from {top['top_below_400']['v1']['mean']:+.4f} to {top['top_below_400']['v2']['mean']:+.4f} "
          f"({n_(top['top_below_400']['v2']['n'])} games); in the farming region (gap ≥ 400, level ≥ 2300) from "
          f"{top['farming']['v1']['mean']:+.4f} to {top['farming']['v2']['mean']:+.4f}, player-clustered interval "
          f"{top['farming']['v2']['players']['lo']:+.4f} to {top['farming']['v2']['players']['hi']:+.4f} "
          f"({n_(top['farming']['v2']['n'])} games). Log-loss against Layer 0 {a['tot']['ll_v2'] - a['tot']['ll_l0']:+.4f} "
          f"nats a game (interval {a['iv']['d_v2_l0'][0]:+.4f} to {a['iv']['d_v2_l0'][1]:+.4f}), against Freeze 1's table "
          f"{a['tot']['ll_v2'] - a['tot']['ll_v1']:+.4f} ({a['iv']['d_v2_v1'][0]:+.4f} to {a['iv']['d_v2_v1'][1]:+.4f}). "
          f"Stage-1 rule: {'passes' if a['gate2'] else 'fails'} ({', '.join(a['parts2'])}).")
    scal = [tc for tc in TCS if t2.needs_scaling(printed(F[tc]))]
    rng = "; ".join(f"{tc} {min(t2.ratio_printed(printed(F[tc]), m) for m in t2.BAND_MIDS)} to "
                    f"{max(t2.ratio_printed(printed(F[tc]), m) for m in t2.BAND_MIDS)}" for tc in TCS)
    P(f"- **R32's slope ratio** E′_8.1.2(0) / E′_v2(0) by level band: {rng}. "
      + (f"Outside 0.9–1.1 in at least one band in {', '.join(scal)}, so rung 2 scales K by the printed ratio there "
         "(R32; D-0011, reading 7), tested in Phase 2 (E12)." if scal else "Every band lies within 0.9–1.1: no scaling."))
    P("- **What this page does not decide.** The guard is re-decided in Phase 2 by the rule D-0011 fixed before this "
      "fit (R24); its inputs, the farming region's residuals with their intervals, are in section 7.\n")

    # ------------------------------------------------------------------ 1
    P("## 1 How the table is fitted and tested\n")
    P("- **The model** (SPEC-TABLE-FIT v1.1 §2): E2's D1 model with the slope κ(L) = κ · exp(λ ℓ), ℓ = (L − 2000)/400, "
      "L the midpoint of the game's 100-point level band; η, α, β and γ as in E2. Maximum likelihood over cells of "
      "identical (gap, band, outcome), started from E2's fit of the same window with λ = 0.")
    P("- **The sample and the months** are E2's, rebuilt by E10's builder with E2's own functions, imported unchanged. "
      f"Data cutoff: no broadcast file after 2026-09 is opened; games dated after 2026-09-30: "
      f"{d['cutoff'].get('dropped_after_cutoff', 0)} dropped. Each of E2's 21 test months (2025-01 to 2026-09) is "
      "forecast by the v2 table fitted on the 36 months before it, by Freeze 1's table with the parameters E2 fitted for "
      "that month, and by Layer 0, on the same games with the same draw rates.")
    P("- **E2 reproduced.** Before anything new is computed, the script reproduces E2's monthly sums and calibration bins "
      "for Freeze 1's table and Layer 0: " + "; ".join(
          f"{tc} largest difference {d['rolling'][tc]['lambda']['reproduces_e2']['max_abs_difference_of_monthly_sums']:.1e}, "
          f"bins {'equal' if d['rolling'][tc]['lambda']['reproduces_e2']['bins_equal'] else 'DIFFERENT'}" for tc in TCS) + ".")
    P("- **Decision rules.** E2's (annex T8.2), with E2's report functions imported unchanged: rules (a) and (b) on the "
      "50-point gap bins pooled over levels, the do-no-harm check, log-loss better than Layer 0 with the interval "
      "excluding zero (E10's stage-1 gate); the same do-no-harm rule against Freeze 1's table; and rule (a) by level "
      "band × 50-point gap cell (annex T8.2, \"by level band\"), every cell with at least 1,000 test games tested "
      "against ±0.01 with a cluster-robust standard error over favourites and Holm–Bonferroni across the cells "
      "(D-0011, reading 5). Intervals: the month-block bootstrap of T8.5 (blocks of 3, 2,000 resamples, seed "
      "20261009) and the bootstrap over favourites of E10.\n")

    # ------------------------------------------------------------------ 2
    P("## 2 The fit\n")
    P(f"Maximum likelihood on the last 36 months, with standard errors; written to `{PARAM_FILE}`. Freeze 1's values "
      "(E2) beside them:\n")
    P("| time control | window | games | κ | λ | η | α | β | γ | μ (draw tail) | Freeze 1: κ, η, α, β, γ |")
    P("|---|---|---|---|---|---|---|---|---|---|---|")
    for tc in TCS:
        f, se = F[tc], F[tc]["se"]
        f1 = e2["final_fit"][tc]
        cellv = lambda k, dg: f"{f[k]:.{dg}f} ({se[k]:.{dg}f})" if se.get(k) else f"{f[k]:.{dg}f}"
        P(f"| {tc} | {d['final_fit'][tc]['from']} to {d['final_fit'][tc]['to']} | {n_(f['n'])} | {cellv('kappa', 3)} | "
          f"{cellv('lambda', 3)} | {cellv('eta', 1)} | {cellv('alpha', 3)} | {cellv('beta', 3)} | {cellv('gamma', 3)} | "
          f"{cellv('mu', 3) if K[tc] == 'tail' else '—'} | {f1['kappa']:.3f}, {f1['eta']:.1f}, {f1['alpha']:.3f}, "
          f"{f1['beta']:.3f}, {f1['gamma']:.3f} |")
    P("")
    P("Log-likelihood gained over Freeze 1's model on the same 36 months (twice the gain is the likelihood-ratio "
      "statistic for λ, one degree of freedom" + (", two with the draw tail" if tails else "") + "): " + "; ".join(
          f"{tc} {F[tc]['loglik'] - e2['final_fit'][tc]['loglik']:+.1f}" for tc in TCS) + ".\n")
    P("Range of the monthly refits over the test months:\n")
    P("| time control | κ | λ | η | γ |")
    P("|---|---|---|---|---|")
    for tc in TCS:
        pm = d["rolling"][tc][K[tc]]["per_month"]
        vals = {k: [v["params_v2"][k] for v in pm.values()] for k in ("kappa", "lambda", "eta", "gamma")}
        P(f"| {tc} | {min(vals['kappa']):.3f}–{max(vals['kappa']):.3f} | {min(vals['lambda']):.3f}–{max(vals['lambda']):.3f} | "
          f"{min(vals['eta']):.1f}–{max(vals['eta']):.1f} | {min(vals['gamma']):.3f}–{max(vals['gamma']):.3f} |")
    P("")
    fs = printed(F["standard"])
    P("The fitted function for standard (White's expected score at gap x, colour excluded) by level band, with Freeze "
      "1's (in brackets) and table 8.1.2's H entry:\n")
    mids = (1650, 2050, 2450, 2650)
    f1s = e2["final_fit"]["standard"]
    P("| x | " + " | ".join(f"level band {band_label(m)}" for m in mids) + " | table 8.1.2 |")
    P("|---|" + "---|" * (len(mids) + 1))
    for x in range(0, 801, 100):
        P(f"| {x} | " + " | ".join(f"{t2.expected_effective(x, m, fs):.3f} ({r2.model_e(f1s, x, m):.3f})" for m in mids)
          + f" | {r2.layer0.expected_score(x)} |")

    # ------------------------------------------------------------------ 3
    P("\n## 3 Out of sample: the v2 table against Layer 0 and against Freeze 1's table\n")
    P("| time control | test games | log-loss v2 | Freeze 1 | Layer 0 | v2 − Layer 0 (95 % interval) | v2 − Freeze 1 (95 % "
      "interval) | Brier v2 / Freeze 1 / Layer 0 | RPS v2 / Freeze 1 / Layer 0 |")
    P("|---|---|---|---|---|---|---|---|---|")
    for tc in TCS:
        a = A[tc]
        t = a["tot"]
        P(f"| {tc} | {n_(a['n'])} | {t['ll_v2']:.4f} | {t['ll_v1']:.4f} | {t['ll_l0']:.4f} | "
          f"{t['ll_v2'] - t['ll_l0']:+.4f} ({a['iv']['d_v2_l0'][0]:+.4f} to {a['iv']['d_v2_l0'][1]:+.4f}) | "
          f"{t['ll_v2'] - t['ll_v1']:+.4f} ({a['iv']['d_v2_v1'][0]:+.4f} to {a['iv']['d_v2_v1'][1]:+.4f}) | "
          f"{t['brier_v2']:.4f} / {t['brier_v1']:.4f} / {t['brier_l0']:.4f} | {t['rps_v2']:.4f} / {t['rps_v1']:.4f} / "
          f"{t['rps_l0']:.4f} |")
    P("\n**Do no harm** (annex T8.2: the upper end of the log-loss interval at most 0.002 nats a game and the mean "
      "absolute residual over gap bins at most 0.005 above the reference's):\n")
    P("| time control | against Layer 0 | against Freeze 1's table | mean \\|residual\\| v2 / Freeze 1 / Layer 0 |")
    P("|---|---|---|---|")
    for tc in TCS:
        a = A[tc]
        h0 = a["iv"]["d_v2_l0"][1] <= 0.002 and a["ma"]["v2"] <= a["ma"]["l0"] + 0.005
        P(f"| {tc} | {'pass' if h0 else 'fail'} (upper {a['iv']['d_v2_l0'][1]:+.4f}) | "
          f"{'pass' if a['harm_v1'] else 'fail'} (upper {a['iv']['d_v2_v1'][1]:+.4f}) | {a['ma']['v2']:.4f} / "
          f"{a['ma']['v1']:.4f} / {a['ma']['l0']:.4f} |")

    # ------------------------------------------------------------------ 4
    P("\n## 4 Calibration pooled over levels (E2's rules (a) and (b))\n")
    for tc in TCS:
        a = A[tc]
        c2, c1, c0 = a["c2"], a["c1"], a["c0"]
        P(f"**{tc.capitalize()}.** Bins with at least 1,000 games; residual = score − expectation; \"outside\" = "
          "significantly outside ±0.01 after Holm–Bonferroni (per-game standard errors, as E2):\n")
        P("| gap | games | score | v2 | residual (SE) | outside | Freeze 1: residual | outside | Layer 0: residual | outside |")
        P("|---|---|---|---|---|---|---|---|---|---|")
        by1 = {row["bin"]: row for row in c1["rows"]}
        by0 = {row["bin"]: row for row in c0["rows"]}
        for row in c2["rows"]:
            q1, q0 = by1.get(row["bin"]), by0[row["bin"]]
            P(f"| {row['bin']}–{row['bin'] + 49} | {n_(row['n'])} | {row['score']:.4f} | {row['e']:.4f} | "
              f"{row['r']:+.4f} ({row['se']:.4f}) | {'yes' if row['outside'] else 'no'} | "
              f"{s4(q1['r'] if q1 else None)} | {'yes' if q1 and q1['outside'] else 'no'} | {q0['r']:+.4f} | "
              f"{'yes' if q0['outside'] else 'no'} |")
        sl = lambda c: f"{c['slope']:.3f} (SE {c['se_slope']:.3f}): {c['b']}" if c["slope"] is not None else c["b"]
        P(f"\nRule (a): the v2 table {'passes' if c2['a_pass'] else 'fails'} ({sum(r['outside'] for r in c2['rows'])} of "
          f"{c2['m']} bins outside); Freeze 1's {'passes' if c1['a_pass'] else 'fails'} "
          f"({sum(r['outside'] for r in c1['rows'])} of {c1['m']}); Layer 0 {'passes' if c0['a_pass'] else 'fails'} "
          f"({sum(r['outside'] for r in c0['rows'])} of {c0['m']}). Rule (b), slope: v2 {sl(c2)}; Freeze 1 {sl(c1)}; "
          f"Layer 0 {sl(c0)}.")
        res = d["rolling"][tc][K[tc]]
        for name, key in (("favourite White", "white_favourite_bins_v2"), ("favourite Black", "black_favourite_bins_v2")):
            cb = r2.calibration(res[key], 0)
            worst = max(cb["rows"], key=lambda row: abs(row["r"])) if cb["rows"] else None
            P(f"Colour, {name}: {cb['m']} bins with at least 1,000 games, {sum(row['outside'] for row in cb['rows'])} "
              f"outside; largest |residual| {f'{abs(worst['r']):.4f}' if worst else '—'}.")
        P("")

    # ------------------------------------------------------------------ 5
    P("## 5 Calibration by level band and gap (rule (a) by cell)\n")
    P("Cells of the 100-point level band and the 50-point gap bin from the favourite's side; tested: every cell with at "
      "least 1,000 test games; a cell is outside when its residual is significantly outside ±0.01 (one-sided z-test "
      "against the nearer bound, cluster-robust standard error over favourites, Holm–Bonferroni across the cells of the "
      "time control at a familywise 5 %).\n")
    P("| time control | cells tested | outside: Freeze 1's table | outside: the v2 table | outside: Layer 0 | rule (a) by cell, v2 |")
    P("|---|---|---|---|---|---|")
    for tc in TCS:
        cs = A[tc]["cells"]
        P(f"| {tc} | {cs['v2']['m']} | {len(cs['v1']['outside'])} | {len(cs['v2']['outside'])} | {len(cs['l0']['outside'])} | "
          f"{'pass' if cs['v2']['pass'] else 'fail'} |")
    P("")
    for tc in TCS:
        cs = A[tc]["cells"]
        for key in ("v2", "v1"):
            out_ = cs[key]["outside"]
            if out_:
                P(f"- {tc}, {WHO[key]}: cells outside: " + "; ".join(
                    f"{band_label(r['band'])} × {r['gap']}–{r['gap'] + 49} ({n_(r['n'])} games, {r['mean']:+.4f}, SE "
                    f"{r['se']:.4f})" for r in out_) + ".")
    P("\n**The favourite's residual by level band and gap, before → after** (Freeze 1's table → the v2 table; "
      f"cells with at least {PRINT_MIN} test games; REDTEAM_v1_0, V10-EXPLOIT-1). Standard errors and Layer 0's values "
      "are in the aggregate.\n")
    for tc in TCS:
        P(f"**{tc.capitalize()}.**\n")
        residual_table(d["rolling"][tc][K[tc]], P)
        P("")

    # ------------------------------------------------------------------ 6
    P("## 6 The favourite's residual by level band\n")
    P("All gaps pooled (E10 §5's table), on the 21 test months; standard error clustered over favourites:\n")
    P("| level band | " + " | ".join(f"{tc}: games, Freeze 1, v2 (SE), Layer 0" for tc in TCS) + " |")
    P("|---|---|---|---|")
    for mid in t2.BAND_MIDS:
        cols = []
        for tc in TCS:
            b = d["rolling"][tc][K[tc]]["bands"]
            if str(mid) in b["v2"]:
                v1, v2, v0 = b["v1"][str(mid)], b["v2"][str(mid)], b["l0"][str(mid)]
                cols.append(f"{n_(v2['n'])}, {v1['mean']:+.3f}, {v2['mean']:+.3f} ({v2['se']:.3f}), {v0['mean']:+.3f}"
                            if v2.get("se") else f"{n_(v2['n'])}, {v1['mean']:+.3f}, {v2['mean']:+.3f}, {v0['mean']:+.3f}")
            else:
                cols.append("—")
        P(f"| {band_label(mid)} | " + " | ".join(cols) + " |")
    P("\nAt levels of 2300 or more below a 400-point gap, the games no guard reaches (E10 §5), with the month-block "
      "and the player-clustered intervals:\n")
    P("| time control | games | Freeze 1's table | the v2 table: month-block | the v2 table: players | Layer 0 |")
    P("|---|---|---|---|---|---|")
    for tc in TCS:
        g = d["rolling"][tc][K[tc]]["regions"]["top_below_400"]
        P(f"| {tc} | {n_(g['v2']['n'])} | {g['v1']['mean']:+.4f} | {interval(g['v2']['month_block'])} | "
          f"{interval(g['v2']['players'])} | {g['l0']['mean']:+.4f} |")

    # ------------------------------------------------------------------ 7
    P("\n## 7 The farming region (gap ≥ 400, level ≥ 2300)\n")
    P("The favourite's residual S − E, pooled as R12 orders, with the month-block interval and the interval from the "
      "bootstrap over favourites (E6's functions, imported unchanged). These are the inputs of the rule that re-decides "
      "the guard in Phase 2 (D-0011, R24 and reading 4); nothing is decided here.\n")
    P("| time control | games | favourites | Freeze 1's table: players | the v2 table: month-block | the v2 table: players | "
      "Layer 0: players |")
    P("|---|---|---|---|---|---|---|")
    for tc in TCS:
        g = d["rolling"][tc][K[tc]]["regions"]["farming"]
        P(f"| {tc} | {n_(g['v2']['n'])} | {n_(g['v2']['players']['clusters'])} | {interval(g['v1']['players'])} | "
          f"{interval(g['v2']['month_block'])} | {interval(g['v2']['players'])} | {interval(g['l0']['players'])} |")

    # ------------------------------------------------------------------ 8
    P("\n## 8 The draw tail: is a level pattern left after λ?\n")
    P("SPEC-TABLE-FIT v1.1 §4.6: after λ, a level pattern remains in a time control when the favourite's residual pooled "
      "over gaps in at least one level band with 1,000 test games or more is significantly outside ±0.01 (clustered "
      "standard error, Holm–Bonferroni across the bands); only then is the draw tail γ(L) = γ · exp(μ ℓ) added.\n")
    P("| time control | bands tested | bands outside ±0.01 | largest \\|residual\\| (band) | draw tail added |")
    P("|---|---|---|---|---|")
    for tc in TCS:
        lp = d["rolling"][tc]["lambda"]["level_pattern"]
        rows = lp["bands_tested"]
        worst = max(rows, key=lambda r: abs(r["mean"])) if rows else None
        P(f"| {tc} | {len(rows)} | {sum(r['outside'] for r in rows)} | "
          f"{f'{worst['mean']:+.4f} ({band_label(worst['band'])})' if worst else '—'} | {'yes' if lp['holds'] else 'no'} |")
    for tc in tails:
        lp = d["rolling"][tc]["tail"]["level_pattern"]
        P(f"\nWith the draw tail, {tc}: {sum(r['outside'] for r in lp['bands_tested'])} of {len(lp['bands_tested'])} bands "
          "outside ±0.01; the condition is not evaluated again (§4.6). Both versions, as §4.6 asks:\n")
        P("| " + tc + " | log-likelihood of the published fit | log-loss against Freeze 1's table (95 % interval) | "
          "cells outside (rule (a) by cell) | bands outside ±0.01 | farming region: players | levels ≥ 2300 below 400 |")
        P("|---|---|---|---|---|---|---|")
        for kind in ("lambda", "tail"):
            res = d["rolling"][tc][kind]
            a = A[tc] if kind == K[tc] else analyse(tc, res, e2["rolling"][tc])
            f = d["final_fit"][tc][kind]
            bo = [r for r in res["level_pattern"]["bands_tested"] if r["outside"]]
            P(f"| {'λ' if kind == 'lambda' else 'λ and the draw tail'} | {f['loglik']:.1f} | "
              f"{a['tot']['ll_v2'] - a['tot']['ll_v1']:+.4f} ({a['iv']['d_v2_v1'][0]:+.4f} to {a['iv']['d_v2_v1'][1]:+.4f}) | "
              f"{len(a['cells']['v2']['outside'])} of {a['cells']['v2']['m']} | "
              + (", ".join(f"{band_label(r['band'])} {r['mean']:+.4f}" for r in bo) or "none")
              + f" | {interval(res['regions']['farming']['v2']['players'])} | "
              f"{res['regions']['top_below_400']['v2']['mean']:+.4f} |")

    # ------------------------------------------------------------------ 9
    P("\n## 9 R32: the slope ratio by level band\n")
    P(f"m(L) = E′_8.1.2(0) / E′_v2(0): table 8.1.2's slope near zero, the least-squares slope of its H entries over D = 0 "
      f"to 100, {s812:.5f} a point [V 1] (as `analysis/OUTPUT_v1_0.md` §13.4), over the v2 table's slope at an even gap, "
      "κ(L) q / (2(2 + ν₀(L))) at the band's midpoint, from the parameters as printed. Printed to two decimals, the value "
      "that is normative (D-0011, reading 7):\n")
    P("| level band | " + " | ".join(f"{tc}: E′_v2(0), m" for tc in TCS) + " |")
    P("|---|---|---|---|")
    for mid in t2.BAND_MIDS:
        P(f"| {band_label(mid)} | " + " | ".join(
            f"{t2.slope_at_zero(printed(F[tc]), mid):.5f}, {t2.ratio_printed(printed(F[tc]), mid)}" for tc in TCS) + " |")
    P("\nVerdict (R32): " + "; ".join(
        f"{tc}: {'K scaled by m' if t2.needs_scaling(printed(F[tc])) else 'no scaling'}" for tc in TCS)
      + ". The scaling and its test are Phase 2's (E12).\n")

    # ------------------------------------------------------------------ 10
    P("## 10 Decision (annex T8.2; R35)\n")
    P("| time control | test months | (a) pooled | (b) | do no harm (Layer 0) | better than Layer 0 | stage-1 rule | "
      "(a) by level band × gap | Freeze 1's table: stage-1 rule | do no harm against Freeze 1's table |")
    P("|---|---|---|---|---|---|---|---|---|---|")
    for tc in TCS:
        a = A[tc]
        P(f"| {tc} | {a['months']} | {'pass' if a['c2']['a_pass'] else 'fail'} | {a['c2']['b']} | "
          f"{'pass' if a['iv']['d_v2_l0'][1] <= 0.002 and a['ma']['v2'] <= a['ma']['l0'] + 0.005 else 'fail'} | "
          f"{'yes' if a['iv']['d_v2_l0'][1] < 0 else 'no'} | {'passes' if a['gate2'] else 'fails'} | "
          f"{'pass' if a['cells']['v2']['pass'] else 'fail'} | {'passes' if a['gate1'] else 'fails'} | "
          f"{'pass' if a['harm_v1'] else 'fail'} |")
    rb = [tc for tc in ("rapid", "blitz") if A[tc]["gate2"]]
    P("\nR35: rung 2 is RECOMMENDED NOW in standard only; rapid and blitz stay conditioned on FIDE's data whatever "
      "the broadcast games show. " + (f"The v2 table passes the full stage-1 rule on broadcast games in "
                                      f"{' and '.join(rb)}, reported as R35 asks; the condition stays." if rb else
                                      "The v2 table does not pass the full stage-1 rule on broadcast games in rapid or blitz.")
      + " The guard's outcome, which changes the rule's inputs in its region, is Phase 2's (E12).\n")

    # ------------------------------------------------------------------ 11
    P("## 11 Limits\n")
    P("- The sample is broadcast events, stronger and more international than the pool [E2]: a pass here supports the v2 "
      "table for that population only; FIDE's TRF archive settles it for the pool.")
    P("- λ is fitted on published ratings (decision D2), as κ is: it describes how published gaps predict results by "
      "level, which is what a published table needs (P4), not how strength gaps do.")
    P("- Rule (a) by cell tests only cells with 1,000 test games or more; at the top and at large gaps few cells reach it, "
      "and the farming region is pooled, as R12 orders.")
    P("- The static tests here cannot see how fast a rating answers its error at a given K; R32's scaling of K is tested "
      "with ratings carried forward in Phase 2.")
    print("\n".join(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
