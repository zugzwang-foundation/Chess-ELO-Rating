#!/usr/bin/env python3
"""E12 report: the guard re-decided on the v2 table (R24) and K scaled by the slope ratio (R32).

Reads the E12 aggregate (analysis/staging/aggregates/E12_guard_v2.json, written by
analysis/staging/e12_guard_v2_extract.py), the E11 aggregate for the rule's inputs, the staged v2 parameter file and
the 2026 championship event files (tools/events/; pairings and ratings only); no data/ needed. Applies D-0011's rule
(R24, fixed before the v2 table was fitted) with the executor's readings 4 to 7, E2's decision rules (imported
unchanged from analysis/e2_broadcast_report.py) and E10's stage-1 gate (imported unchanged from
analysis/e10_guard_report.py), and prints either the evidence page docs/evidence/E12_guard-v2.md or, with --yaml, the
guard's parameter file (params/guard_2026-10b.yaml from Freeze 3; staged as analysis/staging/params/guard_2026-10b.yaml
until then, D-0011 reading 1). Python standard library only.

Usage: python3 analysis/staging/e12_guard_v2_report.py > docs/evidence/E12_guard-v2.md
       python3 analysis/staging/e12_guard_v2_report.py --yaml > analysis/staging/params/guard_2026-10b.yaml
"""
from __future__ import annotations

import json
import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "analysis" / "staging"))
sys.path.insert(0, str(ROOT / "analysis"))
sys.path.insert(0, str(ROOT / "src"))
import e2_broadcast_report as r2  # noqa: E402  (E2's decision rules, unchanged)
import e10_guard_report as r10  # noqa: E402  (E10's stage-1 gate, unchanged)
import e11_table_by_level_report as r11  # noqa: E402  (rule (a) by cell, the band labels)
import guard_v2 as gv2  # noqa: E402
import table_v2 as t2  # noqa: E402

STAGE = ROOT / "analysis" / "staging"
AGG = STAGE / "aggregates" / "E12_guard_v2.json"
AGG11 = STAGE / "aggregates" / "E11_table_by_level.json"
TABLE = STAGE / "params" / "table_fit_2026-10b.yaml"
TCS = ("standard", "rapid", "blitz")
BAND = 0.01
EVENTS = (("U.S. Championship", "tools/events/us_championship_2026.json"),
          ("U.S. Women's Championship", "tools/events/us_womens_championship_2026.json"))
WHO = {"v2": "the v2 table", "guarded": "the v2 table with the narrowed guard", "l0": "Layer 0"}
PARAM_FILE = "params/guard_2026-10b.yaml"


def n_(x) -> str:
    return f"{int(x):,}"


def rule(d11: dict, tc: str) -> dict:
    """R24's rule (i) on the v2 table's farming region (D-0011, reading 4): strict and weaker verdicts."""
    kind = "tail" if "tail" in d11["rolling"][tc] else "lambda"
    reg = d11["rolling"][tc][kind]["regions"]["farming"]["v2"]
    pl = reg["players"]
    strict = pl["lo"] >= -BAND and pl["hi"] <= BAND
    weak = pl["hi"] >= -BAND and pl["lo"] <= BAND
    return {"n": reg["n"], "favourites": pl["clusters"], "mean": pl["mean"], "lo": pl["lo"], "hi": pl["hi"],
            "strict": strict, "weak": weak, "guard": not strict}


def steps(par: tuple, eta: int) -> dict:
    """The favourite's published expectation with and without the guard over every pair of published ratings with the
    underdog rated 1500 to 2900 and a gap of 350 to 800, both colours, and the largest change for a one-point move of
    either rating: within a level band and away from the 735-point stop (the guard's blend and table 8.1.2's rows), at
    a level band's edge (where the v2 table itself steps), and across the stop. Returns {kind: (step, where)}."""
    def fav_e(r_fav: int, r_und: int, white: bool) -> tuple[Decimal, Decimal]:
        x = r_fav - r_und + (eta if white else -eta)
        e = t2.published(x, t2.band_mid((r_fav + r_und) // 2), par)
        return e, gv2.guard_own(e, x, True, gv2.weight(r_fav, r_und))[0]

    best = {k: (Decimal(0), None) for k in ("within_g", "within_v2", "band_g", "band_v2", "stop")}
    for white in (True, False):
        side = "White" if white else "Black"
        for r_und in range(1500, 2901):
            row = {gap: fav_e(r_und + gap, r_und, white) for gap in range(350, 802)}
            nxt = {gap: fav_e(r_und + 1 + gap, r_und + 1, white) for gap in range(349, 801)}
            for gap in range(350, 801):
                r_fav = r_und + gap
                e0, g0 = row[gap]
                x0 = gap + (eta if white else -eta)
                for (e1, g1), (a, b) in ((row[gap + 1], (r_fav + 1, r_und)), (nxt[gap - 1], (r_fav, r_und + 1))):
                    x1 = a - b + (eta if white else -eta)
                    where = (r_fav, r_und, side, a, b)
                    if (x0 <= gv2.X_MAX) != (x1 <= gv2.X_MAX):
                        kinds = (("stop", abs(g1 - g0)),)
                    elif t2.band_mid((r_fav + r_und) // 2) != t2.band_mid((a + b) // 2):
                        kinds = (("band_g", abs(g1 - g0)), ("band_v2", abs(e1 - e0)))
                    else:
                        kinds = (("within_g", abs(g1 - g0)), ("within_v2", abs(e1 - e0)))
                    for k, v in kinds:
                        if v > best[k][0]:
                            best[k] = (v, where)
    return best


def yaml_out(d11: dict) -> None:
    print(f"# {PARAM_FILE}: generated by analysis/staging/e12_guard_v2_report.py --yaml; do not edit by hand.")
    print("# Staged as analysis/staging/params/guard_2026-10b.yaml until Freeze 3 (D-0011, reading 1).")
    print("status: PROVISIONAL (the rule, region and blend fixed by the architect, R24; the outcome from broadcast games)")
    print("rule: docs/decisions/D-0011_rulings-and-freeze-3.md (R24; readings 4 and 6)")
    print("table: params/table_fit_2026-10b.yaml")
    print("evaluation: docs/evidence/E12_guard-v2.md")
    print(f"region: {{level_min: {gv2.LEVEL_MIN}, gap_min: {gv2.GAP_MIN}, gap_blend: {gv2.GAP_BLEND}, "
          f"level_blend: {gv2.LEVEL_BLEND}, x_max: {gv2.X_MAX}}}")
    for tc in TCS:
        r = rule(d11, tc)
        print(f"{tc}:")
        print(f"  applies: {str(r['guard']).lower()}")
        print(f"  farming_region_v2: {{games: {r['n']}, residual: {r['mean']:.4f}, players_interval: "
              f"[{r['lo']:.4f}, {r['hi']:.4f}]}}")
        print(f"  rule_i_interval_inside: {str(r['strict']).lower()}")
        print(f"  rule_i_not_significantly_outside: {str(r['weak']).lower()}")


def main() -> int:
    d11 = json.loads(AGG11.read_text(encoding="utf-8"))
    if "--yaml" in sys.argv[1:]:
        yaml_out(d11)
        return 0
    d = json.loads(AGG.read_text(encoding="utf-8"))
    tab = TABLE.read_text(encoding="utf-8")
    V2 = {tc: t2.load(tab, tc) for tc in TCS}
    R = {tc: rule(d11, tc) for tc in TCS}
    out: list[str] = []
    P = out.append

    A = {}
    for tc in TCS:
        st = d["static"][tc]
        months = st["test_months"]
        pm = {m: dict(st["per_month"][m]) for m in months}
        for m in months:
            pm[m]["d_v2_l0"] = pm[m]["ll_v2"] - pm[m]["ll_l0"]
            pm[m]["d_g_l0"] = pm[m]["ll_g"] - pm[m]["ll_l0"]
            pm[m]["d_g_v2"] = pm[m]["ll_g"] - pm[m]["ll_v2"]
        n = sum(pm[m]["n"] for m in months)
        tot = {k: sum(pm[m][k] for m in months) / n for k in ("ll_v2", "ll_g", "ll_l0")}
        iv = {k: r2.block_bootstrap(months, pm, k) for k in ("d_v2_l0", "d_g_l0", "d_g_v2")}
        kind = st["model"]
        bins_v2 = d11["rolling"][tc][kind]["bins_v2_l0"]
        cg = r2.calibration(st["bins_guarded_l0"], 0)
        c2 = r2.calibration(bins_v2, 0)
        ma = {"guarded": r2.all_bins_mean_abs(st["bins_guarded_l0"], 0), "v2": r2.all_bins_mean_abs(bins_v2, 0),
              "l0": r2.all_bins_mean_abs(bins_v2, 1)}
        gate_g, parts_g = r10.gate(cg, iv["d_g_l0"][1], ma["guarded"], ma["l0"], iv["d_g_l0"][1])
        gate_2, parts_2 = r10.gate(c2, iv["d_v2_l0"][1], ma["v2"], ma["l0"], iv["d_v2_l0"][1])
        cells = r11.cell_rule(st["cells_guarded"])
        A[tc] = {"n": n, "tot": tot, "iv": iv, "cg": cg, "c2": c2, "ma": ma, "gate_g": gate_g, "parts_g": parts_g,
                 "gate_2": gate_2, "parts_2": parts_2, "cells": cells, "months": len(months)}
    S = {tc: steps(V2[tc]["par"], t2.eta_whole(V2[tc]["par"][2])) for tc in TCS}

    P("# E12 — The guard re-decided on the v2 table (R24), and K scaled by the slope ratio (R32)\n")
    P("Status: REVIEW — evidence for rung 2 of the adoption ladder (session ELO-6, Phase 2), under "
      "`docs/decisions/D-0011_rulings-and-freeze-3.md` (R24's rule, fixed before the v2 table was fitted; readings 4 to "
      "7) and `docs/specs/SPEC-TABLE-FIT_v1_1.md`. Generated by `analysis/staging/e12_guard_v2_report.py` from "
      "`analysis/staging/aggregates/E12_guard_v2.json` (written by `analysis/staging/e12_guard_v2_extract.py`) and E11's "
      "aggregate; do not edit by hand. Licence: CC BY 4.0 (`docs/LICENSE-docs.md`). " + r2.ATTRIBUTION + " Ratings: "
      "FIDE's monthly lists, analysed and never redistributed [V 3]. The table's parameters are PROVISIONAL-FITTED "
      "[E11]; the guard's region and blend are fixed by ruling (R24). The scripts, aggregate and parameter files are "
      "staged under `analysis/staging/` until Freeze 3 (D-0011, reading 1).\n")

    # ------------------------------------------------------------------ in brief
    guard_tcs = [tc for tc in TCS if R[tc]["guard"]]
    P("**In brief.**\n")
    P("- **The rule** (R24; D-0011, written before the v2 table was fitted): in each time control, if the favourite's "
      "residual in the farming region (gap ≥ 400 at level ≥ 2300) under the v2 table lies within ±0.01 with "
      "player-clustered intervals, no guard; otherwise the narrowed guard. Read strictly (the interval inside ±0.01; "
      "D-0011, reading 4): " + "; ".join(
          f"{tc} {R[tc]['mean']:+.4f} ({R[tc]['lo']:+.4f} to {R[tc]['hi']:+.4f}) on {n_(R[tc]['n'])} games, "
          f"{'inside' if R[tc]['strict'] else 'not inside'}" for tc in TCS) + ". **Outcome: "
      + (f"the narrowed guard in {', '.join(guard_tcs)}" if guard_tcs else "no guard in any time control")
      + (f"; no guard in {', '.join(tc for tc in TCS if tc not in guard_tcs)}" if 0 < len(guard_tcs) < 3 else "") + ".** "
      "Under the weaker reading (not significantly outside ±0.01) the guard would apply in "
      + (", ".join(tc for tc in TCS if not R[tc]["weak"]) or "no time control") + " only; the architect can rule so "
      "without a rerun.")
    for tc in TCS:
        a = A[tc]
        reg = d["static"][tc]["region"]
        c = d["static"][tc]["counts"]
        P(f"- **{tc.capitalize()}.** The region holds {n_(c['region'])} of {n_(c['games'])} test games; the guard binds in "
          f"{n_(c['region_binds'])} ({n_(c['region_full_weight'])} at full weight; {n_(c['region_over_735'])} beyond the "
          f"735-point stop). Favourite's residual in the region: v2 {reg['v2']['mean']:+.4f}, guarded "
          f"{reg['guarded']['mean']:+.4f} (players {reg['guarded']['players']['lo']:+.4f} to "
          f"{reg['guarded']['players']['hi']:+.4f}), Layer 0 {reg['l0']['mean']:+.4f}. The guard's cost in log-loss "
          f"{a['tot']['ll_g'] - a['tot']['ll_v2']:+.5f} nats a game; guarded against Layer 0 "
          f"{a['tot']['ll_g'] - a['tot']['ll_l0']:+.4f} ({a['iv']['d_g_l0'][0]:+.4f} to {a['iv']['d_g_l0'][1]:+.4f}). "
          f"Stage-1 rule with the guard: {'passes' if a['gate_g'] else 'fails'} ({', '.join(a['parts_g'])}); rule (a) by "
          f"level band × gap {len(a['cells']['outside'])} of {a['cells']['m']} cells outside.")
    over_w = [tc for tc in TCS if S[tc]["within_g"][0] > Decimal("0.01")]
    over_s = [tc for tc in TCS if S[tc]["stop"][0] > Decimal("0.01")]
    P("- **Steps** (a one-point move of either published rating; section 2). Within a level band the guarded table moves "
      "by at most " + "; ".join(f"{S[tc]['within_g'][0]} ({tc})" for tc in TCS) + ", the guard's blend riding on table "
      "8.1.2's two-decimal rows" + (f": beyond 0.01 in {', '.join(over_w)}, where a row changes inside the blend" if over_w
                                    else ": no step beyond 0.01, as the rule asks") + ". Across the 735-point stop, which "
      "the brief does not blend, by up to " + "; ".join(f"{S[tc]['stop'][0]} ({tc})" for tc in TCS)
      + (f": beyond 0.01 in {', '.join(over_s)}, reported for the architect and not changed (D-0011, reading 6 (f))"
         if over_s else "") + ".")
    r32 = d["r32"]
    P("- **R32.** K is scaled by the printed ratio m(L) in every time control (E11: m from 1.24 to 2.49). Tested with "
      "ratings carried forward (E6's design for rung 4), scaled minus unscaled log-loss: " + "; ".join(
          f"{tc} {r32[tc]['log_loss_difference']['mean']:+.5f} ({r32[tc]['log_loss_difference']['lo']:+.5f} to "
          f"{r32[tc]['log_loss_difference']['hi']:+.5f}) on {n_(r32[tc]['games'])} games" for tc in TCS)
      + ": " + "; ".join(f"{tc} {verdict32(r32[tc])}" for tc in TCS) + ".")
    P("- **The 2026 championships.** Neither field has a pairing in the region (section 7): the guard cannot change any "
      "expectation in either event; R32's scaling changes every game's K.\n")

    # ------------------------------------------------------------------ 1
    P("## 1 The rule and its inputs\n")
    P("The favourite's residual S − E in the farming region (published gap ≥ 400, level ⌊(R_W + R_B)/2⌋ ≥ 2300) under "
      "the v2 table on E2's 21 held-out months, with the bootstrap over favourites (E6's `boot_cluster`, 2,000 resamples, "
      "seed 20261009) [E11]:\n")
    P("| time control | games | favourites | residual | 95 % interval, players | interval inside ±0.01 (rule (i), as read) | "
      "not significantly outside ±0.01 (the weaker reading) | outcome |")
    P("|---|---|---|---|---|---|---|---|")
    for tc in TCS:
        r = R[tc]
        P(f"| {tc} | {n_(r['n'])} | {n_(r['favourites'])} | {r['mean']:+.4f} | {r['lo']:+.4f} to {r['hi']:+.4f} | "
          f"{'yes' if r['strict'] else 'no'} | {'yes' if r['weak'] else 'no'} | "
          f"{'the narrowed guard' if r['guard'] else 'no guard'} |")
    P("\nThe outcome is written to the guard's parameter file (staged; D-0011, reading 1), which the comparison tool reads.\n")

    # ------------------------------------------------------------------ 2
    P("## 2 The narrowed guard and its steps\n")
    P("- **Region** (R24 (ii); D-0011, reading 6), tested once per game on published ratings: the level (R_W + R_B)/2 "
      "≥ 2300 and the gap |R_W − R_B| ≥ 400 (the farming region of E2, E6 and E10). **Weight** w = min(1, (gap − 400)/50) "
      "· min(1, (level − 2300)/50). **Value**: the favourite's expectation E_v2 + w · max(0, T − E_v2), T table 8.1.2's "
      "H entry [V 1] at the favourite's own effective gap x (colour included), only while x ≤ 735; the underdog's is one "
      "minus it. Published entries are rounded half up to three decimals on the favourite's side and mirrored.")
    P("- **Steps** for a one-point move of either published rating, over underdogs rated 1500 to 2900 and gaps of 350 to "
      "800, both colours, with the published v2 table:\n")
    P("| time control | within a level band: guarded | within a level band: v2 alone | at a band's edge: guarded | at a "
      "band's edge: v2 alone | across the 735-point stop: guarded |")
    P("|---|---|---|---|---|---|")
    for tc in TCS:
        s = S[tc]
        fmt = lambda v: f"{v[0]}" + (f" (favourite {v[1][0]} with {v[1][2]} v {v[1][1]})" if v[1] else "")
        P(f"| {tc} | {fmt(s['within_g'])} | {fmt(s['within_v2'])} | {fmt(s['band_g'])} | {fmt(s['band_v2'])} | "
          f"{fmt(s['stop'])} |")
    P("\nInside the region the blend moves the guard's weight by at most 0.02 a point, so the guarded table steps mainly "
      "where table 8.1.2's two-decimal H entry changes row; at a level band's edge the v2 table steps by itself, as every "
      "published table does (annex T3.4), and the guard, which reads table 8.1.2 by the gap alone, mostly smooths it; "
      "at the stop a favourite one point beyond 735 falls back from table 8.1.2's 0.99 to the v2 table, a step as large "
      "as the guard's lift there, largest where the v2 table is flattest.\n")

    # ------------------------------------------------------------------ 3
    P("## 3 The farming region with and without the guard\n")
    P("The favourite's residual S − E (negative: the favourite scores below the expectation, so farming far weaker "
      "fields costs points), month-block and player intervals:\n")
    P("| time control | games | Layer 0 (table 8.1.2, 400-point rule): players | v2: month-block | v2: players | guarded: "
      "month-block | guarded: players |")
    P("|---|---|---|---|---|---|---|")
    for tc in TCS:
        g = d["static"][tc]["region"]
        P(f"| {tc} | {n_(g['v2']['n'])} | {r11.interval(g['l0']['players'])} | {r11.interval(g['v2']['month_block'])} | "
          f"{r11.interval(g['v2']['players'])} | {r11.interval(g['guarded']['month_block'])} | "
          f"{r11.interval(g['guarded']['players'])} |")
    P("\n**The farmer's yield** a game in the region, K × m(L) times the residual, at K = 10 (every player rated 2400 or "
      "more today [V 1]) and the printed m of the band 2400–2499: " + "; ".join(
          f"{tc}: v2 {10 * float(V2[tc]['k_scale'][2450]) * d['static'][tc]['region']['v2']['mean']:+.2f}, guarded "
          f"{10 * float(V2[tc]['k_scale'][2450]) * d['static'][tc]['region']['guarded']['mean']:+.2f} (m = "
          f"{V2[tc]['k_scale'][2450]})" for tc in TCS) + " points.\n")

    # ------------------------------------------------------------------ 4
    P("## 4 The underdog's residual in the region, by gap\n")
    P("The underdog's residual is minus the favourite's: positive when the underdog scores above its expectation and so "
      "gains points (REDTEAM_v1_0, V10-EXPLOIT-3). Bins of the published gap; \"over 735\" holds the games whose "
      "favourite's effective gap exceeds 735, where the guard stops:\n")
    P("| time control | gap | games | v2 | guarded | Layer 0 |")
    P("|---|---|---|---|---|---|")
    order = ["400", "450", "500", "550", "600", "650", "700", "over 735"]
    for tc in TCS:
        rb = d["static"][tc]["region_by_gap"]
        for b in order:
            if b in rb["v2"]:
                lab = b if b == "over 735" else (f"{b}–{int(b) + 49}" if b != "700" else "700–735")
                P(f"| {tc} | {lab} | {n_(rb['v2'][b]['n'])} | {-rb['v2'][b]['mean']:+.4f} | {-rb['guarded'][b]['mean']:+.4f} | "
                  f"{-rb['l0'][b]['mean']:+.4f} |")
    P("")

    # ------------------------------------------------------------------ 5
    P("## 5 Calibration and do no harm, with and without the guard (E2's rules; E10's checks)\n")
    P("| time control | test games | log-loss: v2 − Layer 0 | guarded − Layer 0 | the guard's cost: guarded − v2 | mean "
      "\\|residual\\| over gap bins: Layer 0 / v2 / guarded |")
    P("|---|---|---|---|---|---|")
    for tc in TCS:
        a = A[tc]
        t = a["tot"]
        P(f"| {tc} | {n_(a['n'])} | {t['ll_v2'] - t['ll_l0']:+.4f} ({a['iv']['d_v2_l0'][0]:+.4f} to "
          f"{a['iv']['d_v2_l0'][1]:+.4f}) | {t['ll_g'] - t['ll_l0']:+.4f} ({a['iv']['d_g_l0'][0]:+.4f} to "
          f"{a['iv']['d_g_l0'][1]:+.4f}) | {t['ll_g'] - t['ll_v2']:+.5f} ({a['iv']['d_g_v2'][0]:+.5f} to "
          f"{a['iv']['d_g_v2'][1]:+.5f}) | {a['ma']['l0']:.4f} / {a['ma']['v2']:.4f} / {a['ma']['guarded']:.4f} |")
    P("\n| time control | rule (a) pooled, v2 / guarded | slope (b), v2 | slope (b), guarded | rule (a) by level band × "
      "gap, guarded | stage-1 rule, v2 | stage-1 rule, guarded |")
    P("|---|---|---|---|---|---|---|")
    for tc in TCS:
        a = A[tc]
        sl = lambda c: f"{c['slope']:.3f} ({c['b']})" if c["slope"] is not None else c["b"]
        P(f"| {tc} | {sum(r['outside'] for r in a['c2']['rows'])} of {a['c2']['m']} / {sum(r['outside'] for r in a['cg']['rows'])} "
          f"of {a['cg']['m']} | {sl(a['c2'])} | {sl(a['cg'])} | {len(a['cells']['outside'])} of {a['cells']['m']} | "
          f"{'pass' if a['gate_2'] else 'fail'} | {'pass' if a['gate_g'] else 'fail'} |")
    P("\nCalibration bins of the guard's gaps, the favourite's side (bins with at least 1,000 test games; \"outside\" after "
      "Holm–Bonferroni):\n")
    P("| time control | gap | games | residual, v2 | residual, guarded | outside, guarded |")
    P("|---|---|---|---|---|---|")
    for tc in TCS:
        a = A[tc]
        by2 = {row["bin"]: row for row in a["c2"]["rows"]}
        for row in a["cg"]["rows"]:
            if row["bin"] >= 350:
                P(f"| {tc} | {row['bin']}–{row['bin'] + 49} | {n_(row['n'])} | {by2[row['bin']]['r']:+.4f} | {row['r']:+.4f} | "
                  f"{'yes' if row['outside'] else 'no'} |")
    rb_ = [tc for tc in ("rapid", "blitz") if A[tc]["gate_g"] and R[tc]["guard"]] + \
          [tc for tc in ("rapid", "blitz") if A[tc]["gate_2"] and not R[tc]["guard"]]
    P("\nR35: rung 2 is RECOMMENDED NOW in standard only; " + (f"the rung as Phase 2 leaves it passes the full stage-1 rule "
                                                               f"on broadcast games in {' and '.join(rb_)} too, reported, "
                                                               "and the condition on FIDE's data stays." if rb_ else
                                                               "in rapid and blitz the rung as Phase 2 leaves it does not "
                                                               "pass the full stage-1 rule on broadcast games, and the "
                                                               "condition on FIDE's data stays.") + "\n")

    # ------------------------------------------------------------------ 6
    P("## 6 R32: K scaled by the slope ratio, and its test\n")
    P("R32 measured E′_8.1.2(0) / E′_v2(0) by level band in E11: outside 0.9–1.1 in every time control (m from "
      + ", ".join(f"{min(V2[tc]['k_scale'].values())} to {max(V2[tc]['k_scale'].values())} in {tc}" for tc in TCS)
      + "), so every game of rung 2 uses K × m(L), L the game's level band, K today's after the 700 rule (D-0011, "
      "reading 7). In the band 2600–2699 of standard, today's K = 10 becomes "
      f"{10 * float(V2['standard']['k_scale'][2650]):.1f}; a period's change can then exceed 700 by the factor m.\n")
    P("**The test** (D-0011, reading 7; E6's design for rung 4): on Layer 1's game records, each player's rating carried "
      "from the list in force through month t's broadcast games with FIDE's K and with K × m (month t's v2 table with the "
      "narrowed guard, its own printed m), and month t + 1's games forecast from the carried ratings with month t + 1's "
      "table; 20 forecast months, 2025-02 to 2026-09; the difference scaled minus unscaled with E6's month-block "
      "bootstrap. The scaling does no harm when the upper end of the log-loss interval is at most 0.002 nats a game, "
      "and helps when the interval lies below zero.\n")
    P("| time control | games forecast | of which the carried ratings differ | log-loss: scaled − unscaled (95 % interval) | "
      "Brier: scaled − unscaled (95 % interval) | verdict |")
    P("|---|---|---|---|---|---|")
    for tc in TCS:
        x = r32[tc]
        ll_, br = x["log_loss_difference"], x["brier_difference"]
        P(f"| {tc} | {n_(x['games'])} | {n_(x['games_where_the_ratings_differ'])} | {ll_['mean']:+.5f} ({ll_['lo']:+.5f} to "
          f"{ll_['hi']:+.5f}) | {br['mean']:+.5f} ({br['lo']:+.5f} to {br['hi']:+.5f}) | {verdict32(x)} |")
    P("\nThe scaling is R32's whatever the test shows (D-0011, reading 7). Broadcast games are a small part of each "
      "player's rated games, so a month's carried change is small and the test has little power (as E6 and E8 found for "
      "rung 4).\n")

    # ------------------------------------------------------------------ 7
    P("## 7 The 2026 U.S. Championships against the region\n")
    P("| event | list in force | games | largest gap | lowest game level | pairings in the region (level ≥ 2300, gap ≥ 400) |")
    P("|---|---|---|---|---|---|")
    for name, path in EVENTS:
        ev = json.loads((ROOT / path).read_text(encoding="utf-8"))
        r = {p["fide_id"]: p["rating"] for p in ev["players"]}
        gaps = [abs(r[g["white"]] - r[g["black"]]) for g in ev["games"]]
        lv = [(r[g["white"]] + r[g["black"]]) / 2 for g in ev["games"]]
        inside = sum(1 for g in ev["games"] if gv2.in_region(r[g["white"]], r[g["black"]]))
        P(f"| {name} | {ev['event']['list_in_force']} | {len(ev['games'])} | {max(gaps)} | {min(lv):g} | {inside} |")
    P("\nThe official pairings of all eleven rounds, with the ratings of FIDE's October 2026 list, as the event files "
      "record them (`tools/events/`); no result is read. No pairing lies in the region, so the guard changes no "
      "expectation in either event.\n")

    # ------------------------------------------------------------------ 8
    P("## 8 Phase 2's outcome\n")
    P("Rung 2 v2 as Phase 2 leaves it, in each time control: the v2 table (E11, "
      "`analysis/staging/params/table_fit_2026-10b.yaml`), " + "; ".join(
          f"{tc}: {'with' if R[tc]['guard'] else 'without'} the narrowed guard, K × m" for tc in TCS)
      + ". Column (b) of the championship comparison is this rung in standard (D-0011, reading 8).\n")

    # ------------------------------------------------------------------ 9
    P("## 9 Limits\n")
    P("- The broadcast games are stronger and more international than the rated pool [E2]; the region's results hold for "
      "them, on 827 to 1,020 games.")
    P("- Where the guard binds, the three-outcome forecast keeps the fitted draw probability, cut where needed (E10's "
      "choice), which raises the guard's log-loss cost; the guard defines the expected score, not the three "
      "probabilities.")
    P("- The rule's strict reading cannot be met on samples of this size unless the region's residual is unusually "
      "tight; FIDE's game archive, with bins of 1,000 games in the region, decides it (annex T8.2).")
    print("\n".join(out))
    return 0


def verdict32(x: dict) -> str:
    ll_ = x["log_loss_difference"]
    if not ll_.get("n"):
        return "no games"
    if ll_["hi"] > 0.002:
        return "harms"
    if ll_["hi"] < 0:
        return "helps"
    if ll_["lo"] > 0:
        return "does no harm by the tolerance, though worse (interval above zero)"
    return "does no harm"


if __name__ == "__main__":
    sys.exit(main())
