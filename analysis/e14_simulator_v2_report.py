#!/usr/bin/env python3
"""E14 report: turns analysis/aggregates/E14_simulator_v2.json into docs/evidence/E14_simulator-v2.md.

E9's report (analysis/e9_simulator_report.py, whose text and tables this script follows) for the simulator rerun with
the v2 table as the pool's true model (analysis/e14_simulator_v2_run.py, src/simulator/v2.py; session ELO-6, Phase 5),
with the sections the rulings add: rung 6 scored under R30, the size of R29's cap, R1's review under R31 and R40, and
E9's headline figures beside the rerun's. Reads only committed aggregates (no data/). Every figure is a mean over the
seeds with the range over them, computed here. FIDE's figures quoted beside the simulated ones for calibration are read
from the committed E1, E5 and E6 aggregates.

Usage: python3 analysis/e14_simulator_v2_report.py > docs/evidence/E14_simulator-v2.md
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AGG = ROOT / "analysis" / "aggregates"
NAMES = {"L0": "Layer 0 (rung 1, today's rules)", "R2": "rung 2 v2 with the narrowed guard at today's K (RECOMMENDED NOW)",
         "R2U": "rung 2 v2 without the guard", "R3": "rung 3, seeds", "R4A": "rung 4, K from the activity record",
         "R4L": "rung 4, K from Layer 1's certainty", "R5": "rung 5, junior compensation", "R6": "rung 6, the monthly adjustment",
         "R7": "rung 7, the federation adjustment", "ALL": "rungs 2 to 6 together"}
ORDER = ("L0", "R2", "R2U", "R3", "R4A", "R4L", "R5", "R6", "R7", "ALL")
BANDS = ("<1600", "1600-1999", "2000-2399", "2400+")
AGES = ("19 or less", "20-24", "25-45", "46 or more")


def mean(v):
    v = [x for x in v if x is not None]
    return sum(v) / len(v) if v else None


def upper95(k: int, n: int) -> float:
    """Exact one-sided 95 % upper bound of a binomial share with k successes in n trials (Clopper–Pearson), by bisection."""
    def cdf(p: float) -> float:
        from math import comb
        return sum(comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(k + 1))
    lo, hi = k / n, 1.0
    for _ in range(60):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if cdf(mid) > 0.05 else (lo, mid)
    return hi


def mr(v, nd: int = 1, sign: bool = False) -> str:
    """Mean over seeds (range)."""
    v = [x for x in v if x is not None]
    if not v:
        return "—"
    f = f"{{:{'+' if sign else ''}.{nd}f}}"
    m = f.format(sum(v) / len(v))
    return m if len(v) == 1 else f"{m} ({f.format(min(v))} to {f.format(max(v))})"


HEADLINE_LABELS = (
    ("rmse", "error against true strength (RMSE, all), by ledger"),
    ("top", "the slide at the top, points a year (L0, R2, R2U, ALL)"),
    ("level", "the level, year 1 to year 10 (L0, R3, R6, ALL)"),
    ("level_deflation", "the level under a junior wave (L0, R6)"),
    ("farming", "farming's advantage a game (L0, R2, R2U, ALL)"),
    ("collusion", "collusion, points created per arranged game, all years (L0, R2, R4A, R5, ALL)"),
    ("drain", "junior drain on adults 2000-2399, a game (L0, R5)"),
    ("r6", "rung 6: share of months passing (E9: R15's reading; E14: R30)"),
    ("theta", "θ_R1 calibrated; false alarms; ratchet's median months"),
)


def headline(d: dict) -> dict:
    """The headline figures of a simulator aggregate (E9's or E14's), as text."""
    sc, seeds = d["scenarios"], d["seeds"]

    def per(s, f):
        return [f(sc[s][str(k)]) for k in seeds]

    def m(v):
        return mean(v)
    led = [x for x in ORDER if x in sc["baseline"][str(seeds[0])]["error"]]
    out = {"rmse": ", ".join(f"{x} {m(per('baseline', lambda r, x=x: r['error'][x]['all']['rmse'])):.0f}" for x in led)}
    top = {x: m(per("baseline", lambda r, x=x: r["series"][x]["top_change"][-1] / len(r["series"][x]["top_change"]))) for x in led}
    out["top"] = ", ".join(f"{x} {top[x]:+.1f}" for x in ("L0", "R2", "R2U", "ALL"))
    lev = lambda s, x: m(per(s, lambda r: r["series"][x]["yearly"]["level"][-1] - r["series"][x]["yearly"]["level"][0]))  # noqa: E731
    out["level"] = ", ".join(f"{x} {lev('baseline', x):+.0f}" for x in ("L0", "R3", "R6", "ALL"))
    out["level_deflation"] = ", ".join(f"{x} {lev('deflation', x):+.0f}" for x in ("L0", "R6"))
    out["farming"] = ", ".join(f"{x} {m(per('adversaries', lambda r, x=x: r['adversaries'][x]['farming_advantage_per_game'])):+.3f}"
                               for x in ("L0", "R2", "R2U", "ALL"))
    out["collusion"] = ", ".join(f"{x} {m(per('adversaries', lambda r, x=x: r['adversaries'][x]['collusion']['created_per_game'])):+.1f}"
                                 for x in ("L0", "R2", "R4A", "R5", "ALL"))
    out["drain"] = ", ".join(f"{x} {m(per('baseline', lambda r, x=x: r['junior_drain'][x].get('2000-2399', [0, 0])[1])) / 1000:+.3f}"
                             for x in ("L0", "R5"))
    key = "r30_share_not_widening_beyond_2" if "r30_share_not_widening_beyond_2" in sc["baseline"][str(seeds[0])]["series"]["R6"] \
        else "r15_share_within_2"
    out["r6"] = (f"baseline {100 * m(per('baseline', lambda r: r['series']['R6'][key])):.0f} %, "
                 f"junior wave {100 * m(per('deflation', lambda r: r['series']['R6'][key])):.0f} %")
    cal = d["r1_calibration"]
    th = cal["calibrated"]
    out["theta"] = (f"{th}; {100 * cal['thresholds'][str(th)]['noise_false_alarm_share']:.0f} %; "
                    f"{cal['thresholds'][str(th)]['ratchet_median_months']}" if th is not None else "none on the grid")
    return out


def main() -> None:
    d = json.loads((AGG / "E14_simulator_v2.json").read_text(encoding="utf-8"))
    d9 = json.loads((AGG / "E9_simulator.json").read_text(encoding="utf-8"))
    e5 = json.loads((AGG / "E5_deflation.json").read_text(encoding="utf-8"))["by_tc"]["standard"]
    e1 = json.loads((AGG / "E1_standard.json").read_text(encoding="utf-8"))
    e6 = json.loads((AGG / "E6_rungs.json").read_text(encoding="utf-8"))
    l1 = json.loads((AGG / "L1_history.json").read_text(encoding="utf-8"))
    n_fide = sum(c["pool"] for c in l1["at_list"]["standard"]["coverage"] if c["band"] != "unrated")
    lon = {w["start"]: w["groups"] for w in e5["longitudinal"]}
    post = ("2024-03", "2025-03")                                   # E5's windows after the 2024 reform
    top_fide = [lon[s][f"band:{b}"]["median"] for s in ("2024-03", "2025-03", "2025-10") for b in ("2200-2399", "2400-2599", "2600+")]
    drain_fide = e6["rung5"]["populations"]["adults"]["by_opponent_band_layer0"]["2400+"]["mean"]
    win = next(w for w in e5["cross_section"]["decomposition"] if w["start"] == "2025-03")
    new_share_fide = e1["newcomers_by_year"]["2025"]["n"] / win["n_start"]
    sc = d["scenarios"]
    seeds = d["seeds"]
    base = sc["baseline"]
    P: list[str] = []
    p = P.append

    def per(s: str, f):
        return [f(sc[s][str(k)]) for k in seeds]

    def err(s, led, key, field):
        return per(s, lambda r: r["error"][led][key][field] if key in r["error"][led] else None)

    def top_rate(s, led):
        return per(s, lambda r: r["series"][led]["top_change"][-1] / len(r["series"][led]["top_change"]))

    def drift(s, led):
        """The level's change from the end of the first year of operation to the end of the tenth."""
        return per(s, lambda r: r["series"][led]["yearly"]["level"][-1] - r["series"][led]["yearly"]["level"][0])

    led_all = [x for x in ORDER if x in base[str(seeds[0])]["error"]]
    # ---------------------------------------------------------------- headline numbers
    rmse_all = {x: mean(err("baseline", x, "all", "rmse")) for x in led_all}
    top = {x: mean(top_rate("baseline", x)) for x in led_all}
    top_true = mean(per("baseline", lambda r: r["series"]["L0"]["top_true_change"][-1] / 10))
    jd = {x: mean(per("baseline", lambda r, x=x: r["junior_drain"][x].get("2000-2399", [0, None])[1])) for x in led_all}
    n50 = {x: mean(per("baseline", lambda r, x=x: r["newcomer_n50"][x]["median"])) for x in led_all}
    adv = sc["adversaries"]
    farm = {x: mean(per("adversaries", lambda r, x=x: r["adversaries"][x]["farming_advantage_per_game"])) for x in led_all}
    cal = d["r1_calibration"]
    cal_rows = per("baseline", lambda r: r["calibration"])
    act_adopt = mean([rs[3]["active_rated"] for rs in cal_rows])
    act_end = mean([rs[-1]["active_rated"] for rs in cal_rows])
    fa_k = round(cal["thresholds"][str(cal["calibrated"])]["noise_false_alarm_share"] * cal["runs"]) if cal["calibrated"] else None

    p("# E14 — The simulator rerun on the v2 table: ten years of each rung against Layer 0")
    p("")
    p("Status: REVIEW — evidence for the proposal and annex (T8.10, T9), session ELO-6, Phase 5, after Freeze 3. Generated "
      "by `analysis/e14_simulator_v2_report.py` from `analysis/aggregates/E14_simulator_v2.json`, which "
      "`analysis/e14_simulator_v2_run.py` computes with `src/simulator/` under `docs/specs/SPEC-SIM_v1_0.md` and the "
      "replacements of `src/simulator/v2.py`. Do not edit by hand. Licence: CC BY 4.0 (`docs/LICENSE-docs.md`). The pool is "
      "synthetic: no player's data is used. It reruns E9's scenarios and seeds (`docs/evidence/E9_simulator.md`) with the "
      "v2 table (E11) as the pool's true outcome model and as Layer 1's proxy's model; rung 2's ledgers read the published "
      "v2 table, with the narrowed guard (R24, E12) at today's K; rung 4's K is fixed per event (R25); accrual ends three "
      "months after the last rated game (R33). The rulings' scores are added: R30 for rung 6, R29's cap, R31 and R40 for R1 "
      "(`docs/decisions/D-0011_rulings-and-freeze-3.md`). Session ELO-6 ran rung 2's ledgers with K times the slope ratio "
      "m(L) of R32; session ELO-7 reran the whole simulation after R44 withdrew it "
      "(`docs/decisions/D-0012_pre-results-amendments.md`), and only rung 2's ledgers changed. Parameters calibrated as in "
      "E9 and PROVISIONAL everywhere; section 9 lists what rests on assumptions.")
    p("")
    p(f"Runs: {len(seeds)} seeds for each of {len(sc)} scenarios, each ten simulated years after a three-year burn-in under "
      f"Layer 0, with about {act_adopt:,.0f} active rated players at adoption and {act_end:,.0f} after ten years, about a "
      f"twentieth of FIDE's {n_fide:,} active rated standard players (`analysis/OUTPUT_L1_history.md`); every rung on the same "
      f"simulated games as Layer 0 (pairings from Layer 0's list). Figures are means over the seeds, with their range in "
      f"brackets. R1's threshold uses {cal['runs']} further paired runs (section 8).")
    p("")
    best = min((x for x in led_all if x not in ("L0", "ALL")), key=lambda x: rmse_all[x])
    best_all = min(led_all, key=lambda x: rmse_all[x])
    p("**In brief.**")
    p("")
    ms = [v / 100 for v in d["v2"]["k_scale"].values()]
    p(f"- **The simulated Layer 0, on a pool whose true outcome model is the v2 table (flatter than table 8.1.2 near equal "
      f"ratings in every level band, its slope at an even gap {min(ms):.2f} to {max(ms):.2f} times smaller, most at the top), "
      f"so that table "
      f"8.1.2's over-prediction of favourites is part of the simulated world:** the adults "
      f"aged 25–45 whose true strength was 2400 or more at adoption lose {abs(top['L0']):.1f} points a year on the list while "
      f"their true strength changes by {top_true:+.1f} (FIDE's lists since the "
      f"2024 reform: players rated 2200 or more lose {abs(max(top_fide)):.0f} to {abs(min(top_fide)):.0f} [E5]), and adults rated "
      f"2400 or more score {abs(mean(per('baseline', lambda r: r['junior_drain']['L0'].get('2400+', [0, None])[1]))) / 1000:.3f} "
      f"a game below today's expectation against juniors (broadcast games: {abs(drain_fide):.3f} [E6]); today's newcomer rule "
      f"publishes newcomers far above their true strength (section 2).")
    p(f"- **Error against true strength** (RMSE over active players, net of the level): Layer 0 {rmse_all['L0']:.0f} points; "
      + ", ".join(f"{NAMES[x].split(',')[0] if x != 'R2' else "rung 2 v2 (guard, today's K)"} {rmse_all[x]:.0f}" for x in ("R2", "R3", "R4A", "R5", "R6", "ALL"))
      + f". The most accurate is {NAMES[best_all]} ({rmse_all[best_all]:.0f}); of the single rungs, {NAMES[best]} "
        f"({rmse_all[best]:.0f}).")
    p(f"- **The slide at the top:** {abs(top['L0']):.1f} points a year under Layer 0, {abs(top['R2']):.1f} with rung 2 v2 "
      f"(the narrowed guard, today's K), {abs(top['R2U']):.1f} without the guard, {abs(top['ALL']):.1f} with rungs 2 to 6 "
      f"together (a negative slide is a rise).")
    dr = {x: mean(drift("baseline", x)) for x in led_all}
    drd = {x: mean(drift("deflation", x)) for x in ("L0", "R6", "ALL")}
    p(f"- **The level:** from the first year to the tenth Layer 0's anchor cohort drifts {dr['L0']:+.0f} points against true "
      f"strength in the baseline and {drd['L0']:+.0f} under a junior wave; rung 6 holds it to {dr['R6']:+.0f} and "
      f"{drd['R6']:+.0f}. Rung 3 alone moves it {dr['R3']:+.0f}: today's newcomer rule injects points that offset the "
      f"junior drain, and accurate seeds remove that offset, which is why rung 3 needs rung 6 beside it.")
    p(f"- **The junior drain** on adults rated 2000–2399: {jd['L0'] / 1000:+.3f} a game under Layer 0, {jd['R5'] / 1000:+.3f} with "
      f"rung 5; newcomers need a median of {n50['L0']:.0f} rated games under Layer 0 and {n50['R3']:.0f} under rung 3 before "
      f"they stay within 50 points of their strength.")
    p(f"- **Farming** gains {farm['L0']:+.3f} points a game over ordinary play under Layer 0, {farm['R2']:+.3f} with rung 2 "
      f"v2 and the narrowed guard and {farm['R2U']:+.3f} without the guard.")
    p(f"- **R1's review threshold:** the noise of the twelve-month mean of the spread ratio has an SD of {cal['noise_sd']:.4f}; "
      + (f"the smallest threshold with at most 5 % false alarms from noise is {cal['calibrated']} ({fa_k} of {cal['runs']} runs; "
         f"exact 95 % upper bound {100 * upper95(fa_k, cal['runs']):.0f} %), which a ratchet at κ's annual cap trips after a "
         f"median of {cal['thresholds'][str(cal['calibrated'])]['ratchet_median_months']} months"
         if cal["calibrated"] is not None else "no threshold on the grid keeps false alarms at 5 % or less")
      + f"; R20's PROVISIONAL 0.02 gives {100 * cal['thresholds']['0.02']['noise_false_alarm_share']:.0f} % false alarms and "
        f"trips on a ratchet after {cal['thresholds']['0.02']['ratchet_median_months']} months. Under R31 and R40 the review "
        f"needs κ at its annual cap as well, which the simulated baseline never reaches; the ratchet then triggers at "
        f"θ_R1 = 0.01 in {100 * d['r1_paired_trigger']['0.01']['detect_share']:.0f} % of runs, after a median of "
        f"{d['r1_paired_trigger']['0.01']['median_months']} months (section 8).")
    p("")

    # ---------------------------------------------------------------- 1 setup
    p("## 1 What is simulated")
    p("")
    df = d["defaults"]
    p(f"- **Pool.** {df['n0']:,} players at the start in six federations (relative sizes 20 : 10 : 5 : 2 : 1 : 0.5), juniors "
      f"35 %, true strengths around 1450 (juniors) and 1750 (adults); entries {100 * df['entry_rate']:.1f} % of the active pool "
      "a month with E1's age shares, their true strengths around the 2023 newcomers' median first ratings moved to today's "
      "scale by the March 2024 compression, R + round(0.4 × (2000 − R)) [E1] [E5]; exits by age, activity and experience.")
    p(f"- **Strength.** A latent strength moving each month by Layer 1's fitted drift by age (`analysis/OUTPUT_L1_history.md`), "
      f"multiplied under 25 by a personal factor of mean {df['junior_factor_mean']} (coefficient of variation "
      f"{df['junior_factor_cv']}), and a random walk of 12 latent points a month (15 after 45), E8's choice for standard; "
      "outcomes from the v2 table [E11] at the true strengths on the published scale, so White's edge, the slope and the "
      "draw rates by level are the v2 table's; Layer 1's proxy uses the same model.")
    p(f"- **Games.** Activity rising with strength (about 10 rated games a year for club adults, 50–60 at 2600 [E5] [E8]); "
      f"{100 * df['domestic_share']:.0f} % of events domestic; Swiss events (9, 7 or 5 rounds) and round-robins of 10.")
    p("- **Ledgers.** Layer 0 exactly (an integer port of SPEC-L0, tested against `src/layer0/`), and each rung alone on the "
      "same games: rung 2 v2 with the narrowed guard and without it, both at today's K (R44); rung 3; rung 4 from the activity "
      "record (E8's design) and from Layer 1's certainty, each with K fixed per event (R25) and with the v2 table's κ(L) "
      "and v(L) in the player's band (annex T4.3); rung 5; rung 6 with accrual "
      "ending three months after the last rated game (R33); rung 7; and rungs 2 to 6 together, whose rung 4 sets K. Rung 1 "
      "is Layer 0 itself, so the RECOMMENDED NOW package is rung 2 v2 with the narrowed guard at today's K. "
      "Rungs 3 to 7 use a forward-filter proxy of Layer 1 that knows the pool's average dynamics (SPEC-SIM §5).")
    p("- **Scenarios.** Baseline; the baseline with twice the noise (Layer 1's history fit, c = 2.0); deflation with a "
      "junior wave; two isolated federations whose ratings start 100 too low and 60 too high; adversaries (section 7); and, "
      "for R1, a ratchet of κ at its annual cap.")
    p("")

    # ---------------------------------------------------------------- 2 calibration
    p("## 2 The simulated Layer 0 against FIDE's lists")
    p("")
    p("Median annual change of published ratings by age (players rated at both ends of a year with a rated game in it), "
      "averaged over the simulated years of operation and the seeds, beside FIDE's standard lists after the 2024 reform [E5]:")
    p("")
    e5_age = {"18 or less": "aged 18 or less", "25-45": "25–45", "46-64": "46–64", "65+": "65 or more"}
    p("| age | simulated Layer 0: median | mean | FIDE's lists, 2024-03 to 2025-03 and 2025-03 to 2026-03: median (mean) [E5] |")
    p("|---|---|---|---|")
    rows = per("baseline", lambda r: r["calibration"])
    key = {"18 or less": "age:<=18", "19-24": "age:19-24", "25-45": "age:25-45", "46-64": "age:46-64", "65+": "age:65+"}
    for ag in ("18 or less", "19-24", "25-45", "46-64", "65+"):
        med = [mean([row["by_age"][ag]["median"] for row in rs if "by_age" in row and ag in row["by_age"]]) for rs in rows]
        mn = [mean([row["by_age"][ag]["mean"] for row in rs if "by_age" in row and ag in row["by_age"]]) for rs in rows]
        fide = ", ".join(f"{lon[s][key[ag]]['median']:+.0f} ({lon[s][key[ag]]['mean']:+.1f})" for s in post)
        p(f"| {ag} | {mr(med, 1, True)} | {mr(mn, 1, True)} | {fide} |")
    p("")
    p("Change per rated game by band of the starting rating (the slide at the top on the lists):")
    p("")
    p("| band | simulated Layer 0 | FIDE's lists, 2024-03 to 2025-03 and 2025-03 to 2026-03 [E5] |")
    p("|---|---|---|")
    for bd in ("<1600", "1600-1999", "2000-2199", "2200-2399", "2400-2599", "2600+"):
        v = [mean([row["by_band"][bd]["per_game"] for row in rs if "by_band" in row and bd in row["by_band"]]) for rs in rows]
        p(f"| {bd} | {mr(v, 3, True)} | " + ", ".join(f"{lon[s]['band:' + bd]['per_game']:+.3f}" for s in post) + " |")
    act = [[row["active_rated"] for row in rs] for rs in rows]
    new = [[row["entering_year"] for row in rs] for rs in rows]
    p("")
    p(f"- **The pool.** Active rated players (Layer 0, a rated game in the last 12 months) at adoption "
      f"{mr([a[3] for a in act], 0)} and after ten years {mr([a[-1] for a in act], 0)}; newly rated players a year "
      f"{mr([mean(n[4:]) for n in new], 0)}, about {100 * mean([mean(n[4:]) for n in new]) / mean([mean(a[3:]) for a in act]):.0f} % "
      f"of the active rated pool (FIDE: {100 * new_share_fide:.0f} % in 2025, E1's newcomers against E5's active list "
      f"[E1] [E5]).")
    p(f"- **Newcomers under today's rule.** The two hypothetical draws against 1800 publish newcomers well above their true "
      f"strength: the points they lose afterwards are the largest inflow of the simulated pool, {mr(per('baseline', lambda r: r['ledger_lines']['L0']['entering'] / 1e6), 1)} "
      f"million rating points entering with newcomers in ten years under Layer 0 against "
      f"{mr(per('baseline', lambda r: r['ledger_lines']['R3']['entering'] / 1e6), 1)} million under rung 3, which publishes "
      "a newcomer only from an estimate of at least 1400 with enough certainty.")
    p("")

    # ---------------------------------------------------------------- 3 error
    p("## 3 Error against true strength, by band and age (baseline)")
    p("")
    p("RMSE of R − θᴾ net of the level (points), active rated players, the last two simulated years:")
    p("")
    p("| ledger | " + " | ".join(BANDS) + " | " + " | ".join(AGES) + " | all |")
    p("|---|" + "---|" * (len(BANDS) + len(AGES) + 1))
    for x in led_all:
        cells = [mr(err("baseline", x, "band|" + b, "rmse"), 0) for b in BANDS]
        cells += [mr(err("baseline", x, "age|" + a, "rmse"), 0) for a in AGES]
        cells.append(mr(err("baseline", x, "all", "rmse"), 0))
        p(f"| {NAMES[x]} | " + " | ".join(cells) + " |")
    p("")
    p("Mean of R − θᴾ net of the level (bias; negative: under-rated):")
    p("")
    p("| ledger | " + " | ".join(BANDS) + " | " + " | ".join(AGES) + " |")
    p("|---|" + "---|" * (len(BANDS) + len(AGES)))
    for x in led_all:
        cells = [mr(err("baseline", x, "band|" + b, "bias"), 0, True) for b in BANDS]
        cells += [mr(err("baseline", x, "age|" + a, "bias"), 0, True) for a in AGES]
        p(f"| {NAMES[x]} | " + " | ".join(cells) + " |")
    worse = {x: [(b, mean(err("baseline", x, "band|" + b, "rmse")) - mean(err("baseline", "L0", "band|" + b, "rmse")))
                 for b in BANDS] for x in led_all if x != "L0"}
    worse = {x: [(b, m) for b, m in v if m > 0] for x, v in worse.items()}
    p("")
    p("T9.5's acceptance check (a rung's RMSE not above Layer 0's in any band; the margin in points where it is above): "
      + "; ".join(f"{x} {'met' if not v else 'not met: ' + ', '.join(f'{b} +{mg:.1f}' for b, mg in v)}" for x, v in worse.items())
      + ". Margins below a point are smaller than the seeds' spread.")
    p("")

    # ---------------------------------------------------------------- 4 top, level, spread
    p("## 4 The top, the level and the spread (baseline)")
    p("")
    p("| ledger | top cohort: change a year | published 2600+ / true 2600+ after ten years | level (anchor's mean R − θᴾ, chain-linked at the January re-basings): end of year 1 → year 10 (change) | true spread ratio: year 1 → year 10 (a year) |")
    p("|---|---|---|---|---|")
    flat = []
    for x in led_all:
        pub = per("baseline", lambda r, x=x: r["series"][x]["yearly"]["n_2600_pub"][-1])
        tru = per("baseline", lambda r, x=x: r["series"][x]["yearly"]["n_2600_true"][-1])
        l0_ = per("baseline", lambda r, x=x: r["series"][x]["yearly"]["level"][0])
        l1_ = per("baseline", lambda r, x=x: r["series"][x]["yearly"]["level"][-1])
        s0 = per("baseline", lambda r, x=x: r["series"][x]["yearly"]["spread_true"][0])
        s1 = per("baseline", lambda r, x=x: r["series"][x]["yearly"]["spread_true"][-1])
        trend = (mean(s1) - mean(s0)) / 9
        if abs(trend) <= 0.01:
            flat.append(x)
        p(f"| {NAMES[x]} | {mr(top_rate('baseline', x), 1, True)} | {mean(pub):.0f} / {mean(tru):.0f} | "
          f"{mean(l0_):+.0f} → {mean(l1_):+.0f} ({mr(drift('baseline', x), 0, True)}) | {mean(s0):.3f} → {mean(s1):.3f} ({trend:+.4f}) |")
    p("")
    p(f"- The top cohort: adults aged 25–45 whose true strength was 2400 or more at adoption; their true strength changed by "
      f"{mr(per('baseline', lambda r: r['series']['L0']['top_true_change'][-1] / 10), 1, True)} points a year.")
    p("- The true spread ratio is the SD of published ratings over the SD of true strength (θᴾ) for active adults aged 25–45; "
      "below 1 the published scale is compressed. T9.5's check (no trend beyond ±0.01 a year) is met by "
      + ", ".join(flat) + "; the other ledgers keep Layer 0's newcomer rule and floor, which compress the scale from below.")
    lv1 = mean(per("baseline", lambda r: r["series"]["L0"]["yearly"]["level"][0]))
    p(f"- The level is the anchor panel's mean R − θᴾ, chain-linked across the panel's January re-basings so that who is in the "
      f"panel does not move it (SPEC-SIM §6). At the end of the first year of operation it stood at {lv1:+.0f} under Layer 0; "
      "the column shows where each ledger takes it from there.")
    p("")

    # ---------------------------------------------------------------- 5 juniors, newcomers
    p("## 5 The junior drain and newcomers (baseline)")
    p("")
    p("Adults' residual S − E against juniors (aged 19 or less), by the adult's band, thousandths of a point a game:")
    p("")
    p("| ledger | " + " | ".join(BANDS) + " | newcomers' N₅₀: median (quartiles) |")
    p("|---|" + "---|" * (len(BANDS) + 1))
    for x in led_all:
        cells = [mr(per("baseline", lambda r, x=x, b=b: r["junior_drain"][x].get(b, [0, None])[1]), 0, True) for b in BANDS]
        q = per("baseline", lambda r, x=x: r["newcomer_n50"][x])
        cells.append(f"{mean([v['median'] for v in q]):.0f} ({mean([v['q1'] for v in q]):.0f} to {mean([v['q3'] for v in q]):.0f})")
        p(f"| {NAMES[x]} | " + " | ".join(cells) + " |")
    p("")
    p("N₅₀ counts the rated games after a player's first rating until |R − θᴾ| (net of the level) stays below 50; T9.5 asks "
      f"for a median of at most 15 with rung 3: {'met' if n50['R3'] <= 15 else 'not met'} ({n50['R3']:.0f}). Two thirds of the "
      "newcomers are juniors, whose ratings keep falling behind their improvement after a first rating however accurate, so "
      "N₅₀ measures the junior lag as much as the seed.")
    p("- **Rung 5 compensates little here.** A junior's c_j is positive only once the model's estimate exceeds the rating by "
      "τ plus 1.28 standard deviations; the proxy carries SPEC-L1's junior uncertainty (25 points a month), so compensation "
      "reaches mostly strong juniors, and the drain on adults below 2400 is almost unchanged. On broadcast games, where "
      "Layer 1 is fitted on the juniors' actual results, it removed most of the junior-specific drain [E6]; in the simulation "
      "its effect rests on the proxy's certainty about juniors (section 9).")
    p("- **Rung 3 and rungs 2–6 together** show a larger residual against juniors: seeded juniors start nearer their "
      "strength (section 3: under-rated where Layer 0's newcomers are over-rated), so the lag that follows their first rating "
      "is no longer offset by an inflated one.")
    p("")

    # ---------------------------------------------------------------- 6 federations, rung 6
    fs = sc["federations"]
    p("## 6 Federations and the monthly adjustment")
    p("")
    p("**Isolated federations** (scenario 3: federations 5 and 6 play 1 % of their games abroad and start 100 points too "
      "low and 60 too high). The federation's mean R − θᴾ against the pool's:")
    p("")
    p("| ledger | federation 5: at adoption → after ten years | federation 6: at adoption → after ten years | federations 1–4, mean absolute offset after ten years |")
    p("|---|---|---|---|")
    for x in led_all:
        a5 = per("federations", lambda r, x=x: r["fed_offsets_at_adoption"][x][4])
        e5_ = per("federations", lambda r, x=x: r["fed_offsets_end"][x][4])
        a6 = per("federations", lambda r, x=x: r["fed_offsets_at_adoption"][x][5])
        e6_ = per("federations", lambda r, x=x: r["fed_offsets_end"][x][5])
        rest = per("federations", lambda r, x=x: mean([abs(v) for v in r["fed_offsets_end"][x][:4]]))
        p(f"| {NAMES[x]} | {mean(a5):+.0f} → {mr(e5_, 0, True)} | {mean(a6):+.0f} → {mr(e6_, 0, True)} | {mr(rest, 0)} |")
    p("")
    p("**Rung 6 judged by R30** (a month from the thirteenth passes when |d_t| has not grown by more than 2 points in "
      "twelve months, a closing gap passing; D-0011, reading 12), beside R15's earlier reading (the twelve-month change of "
      "d_t within ±2 points); D_t reported:")
    p("")
    p("| scenario | ledger | R30: share of months passing | largest twelve-month widening | R15's reading: share within ±2 | mean a_t | level: change from year 1 to year 10 |")
    p("|---|---|---|---|---|---|---|")
    for s in ("baseline", "deflation", "noise2"):
        for x in ("L0", "R6", "ALL"):
            if x not in sc[s][str(seeds[0])]["series"]:
                continue
            s30 = per(s, lambda r, x=x: r["series"][x]["r30_share_not_widening_beyond_2"])
            w30 = per(s, lambda r, x=x: r["series"][x]["r30_largest_widening"])
            sh = per(s, lambda r, x=x: r["series"][x]["r15_share_within_2"])
            at = per(s, lambda r, x=x: r["series"][x]["a_t_mean"])
            p(f"| {s} | {NAMES[x]} | {mr(s30, 2)} | {mr(w30, 1)} | {mr(sh, 2)} | {mr(at, 2, True)} | {mr(drift(s, x), 0, True)} |")
    p("")
    p("Layer 0 has no adjustment; its d_t, the gap a controller would see, is shown for comparison.")
    p("")
    dd = mean(per("baseline", lambda r: r["series"]["L0"]["yearly"]["d_t"][-1] - r["series"]["L0"]["yearly"]["d_t"][0]))
    sh6 = mean(per("baseline", lambda r: r["series"]["R6"]["r30_share_not_widening_beyond_2"]))
    shd = mean(per("deflation", lambda r: r["series"]["R6"]["r30_share_not_widening_beyond_2"]))
    atd = mean(per("deflation", lambda r: r["series"]["R6"]["a_t_mean"]))
    p(f"- **Rung 6 holds the level in the baseline** ({dr['R6']:+.0f} points from the first year to the tenth against Layer 0's "
      f"{dr['L0']:+.0f}) and meets R30's rule there in {100 * sh6:.0f} % of months. Under Layer 0 the gap it answers, d_t, moved "
      f"{dd:+.0f} points over the same years while the true level moved {dr['L0']:+.0f}: with the anchor panel chain-linked, the "
      f"proxy's gap follows the true level. Under a sustained junior wave the controller pays {atd:+.2f} a month on average, "
      f"close to its cap of 1.5, and the level still moves {drd['R6']:+.0f} (Layer 0 {drd['L0']:+.0f}); R30's rule holds in "
      f"{100 * shd:.0f} % of months. The controller holds the level only while its cap exceeds the drift (annex T4.5); whether "
      "Layer 1 holds its own level as well on FIDE's data as this proxy, which knows the pool's dynamics, the full fit must show.")
    p("- **Rung 7 cannot reach isolated federations:** its offset is shrunk by n×/(n× + 2000), and a federation that plays "
      "1 % of its games abroad has too few cross-border games for the shrinkage to let any adjustment through, so its "
      "offset decays at Layer 0's pace. That is the shrinkage working as designed: the evidence for an offset is the "
      "cross-border games themselves (annex T2.5).")
    p("")

    # ---------------------------------------------------------------- 7 adversaries
    p("## 7 The adversaries (scenario 4)")
    p("")
    p("| ledger | farming: advantage a game over the control | sandbaggers after the dumping year / a year later (control) | collusion: points created per arranged game, first year (all years) | inactivity: R − θᴾ at stop → at return → a year later |")
    p("|---|---|---|---|---|")
    for x in led_all:
        fa = per("adversaries", lambda r, x=x: r["adversaries"][x]["farming_advantage_per_game"])
        s12 = per("adversaries", lambda r, x=x: r["adversaries"][x]["checkpoints"].get("sandbagger_12"))
        s24 = per("adversaries", lambda r, x=x: r["adversaries"][x]["checkpoints"].get("sandbagger_24"))
        c12 = per("adversaries", lambda r, x=x: r["adversaries"][x]["checkpoints"].get("sandbagger_control_12"))
        c24 = per("adversaries", lambda r, x=x: r["adversaries"][x]["checkpoints"].get("sandbagger_control_24"))
        co1 = per("adversaries", lambda r, x=x: r["adversaries"][x]["checkpoints"].get("collusion_first_year"))
        coa = per("adversaries", lambda r, x=x: r["adversaries"][x]["collusion"]["created_per_game"])
        ps = per("adversaries", lambda r, x=x: r["adversaries"][x]["protector"]["err_at_stop"])
        pr = per("adversaries", lambda r, x=x: r["adversaries"][x]["protector"]["err_at_return"])
        p1 = per("adversaries", lambda r, x=x: r["adversaries"][x]["protector"]["err_12_months_after_return"])
        p(f"| {NAMES[x]} | {mr(fa, 3, True)} | {mean(s12):+.0f} / {mean(s24):+.0f} ({mean(c12):+.0f} / {mean(c24):+.0f}) | "
          f"{mr(co1, 1, True)} ({mean(coa):+.1f}) | {mean(ps):+.0f} → {mean(pr):+.0f} → {mean(p1):+.0f} |")
    p("")
    p("- **Farming:** 30 strong adults play monthly events against fields 400 to 800 points below them; the advantage is their "
      "change a game net of their true change, minus that of 30 controls of the same strength who play ordinary events.")
    p("- **Sandbagging:** 30 adults rated 2000–2300 lose every game for a year, then play normally; their published change "
      "net of their true change after 12 and 24 months, against controls.")
    p("- **Collusion:** 15 pairs of a junior (K 40 today) and an adult rated 2400 or more (K 10) play two arranged games a "
      "month that the junior wins; the points both changes create together, per arranged game.")
    p("- **Inactivity:** 30 adults stop when their rating first exceeds their strength by 40 points and return two years later.")
    fpg = {x: mean(per("adversaries", lambda r, x=x: r["adversaries"][x]["farmer"]["per_game"])) for x in led_all}
    p(f"- **Farming in points:** the farmers' own change a game net of their true change is {fpg['L0']:+.3f} under Layer 0, "
      f"{fpg['R2']:+.3f} with rung 2 v2 and the narrowed guard and {fpg['R2U']:+.3f} without it; their controls lose under every ledger "
      "(the drain at the top), so the advantage is measured against ordinary play, as T9.4 defines it.")
    fcg = {x: mean(per("adversaries", lambda r, x=x: r["adversaries"][x]["farmer_control"]["per_game"])) for x in led_all}
    p("- **What moves the advantage.** The farmers' own change a game net of their true change, and their controls': "
      + "; ".join(f"{x} {fpg[x]:+.3f} and {fcg[x]:+.3f}" for x in led_all) + ". Where a rung alone raises the advantage "
      "over Layer 0's, it is mostly because ordinary strong players lose more, the drain at the top deepening under today's "
      "capped table, not because the farmer gains more.")
    sb = {x: mean(per("adversaries", lambda r, x=x: r["adversaries"][x]["checkpoints"].get("sandbagger_24")))
          - mean(per("adversaries", lambda r, x=x: r["adversaries"][x]["checkpoints"].get("sandbagger_control_24"))) for x in led_all}
    co = {x: mean(per("adversaries", lambda r, x=x: r["adversaries"][x]["collusion"]["created_per_game"])) for x in led_all}
    pa = {x: mean(per("adversaries", lambda r, x=x: r["adversaries"][x]["protector"]["err_12_months_after_return"])) for x in led_all}
    checks = (("farming (advantage a game)", farm), ("sandbagging (net of the control, a year after the dumping year)", sb),
              ("collusion (points created per arranged game, all years)", co),
              ("inactivity (R − θᴾ a year after return)", pa))
    p("- T9.5's check (no strategy gains more under a rung than under Layer 0), strategy by strategy, with the margin over "
      "Layer 0 where it is not met: " + "; ".join(
        f"{lab}: " + ("met for every rung" if not [x for x in led_all if x != "L0" and vals[x] > vals["L0"]]
                      else "not met for " + ", ".join(f"{x} ({vals[x] - vals['L0']:+.3g})" for x in led_all
                                                      if x != "L0" and vals[x] > vals["L0"]))
        for lab, vals in checks) + ". Margins smaller than the spread over the seeds in the table above are within noise.")
    pr1 = per("adversaries", lambda r: r["adversaries"]["L0"]["protector"]["err_12_months_after_return"])
    p(f"- The inactivity figures are means over the seeds of about {mean(per('adversaries', lambda r: r['adversaries']['L0']['protector']['returned_and_followed_12_months'])):.0f} "
      f"returning players each; a year after return under Layer 0 they range over the seeds from {min(pr1):+.0f} to {max(pr1):+.0f}.")
    p("")
    p("**R29's cap on line-2 creation** (D-0011, reading 11). A player's line-2 creation is the points the player's games "
      "create through unequal K (ledger line 2 of annex T6), attributed to the player with the larger K; for each honest "
      "active player and year of operation, the largest sum over a trailing twelve months, in the baseline (zero where "
      "there is none). The PROVISIONAL size of the cap is the 99.9th percentile, the mean over the seeds rounded up to a "
      "whole point; the colluding juniors of scenario 4 are measured against it, first order (their creation above the "
      "cap, without the feedback the cap would have on their ratings):")
    p("")
    p("| ledger | honest player-years a seed | 99th percentile | 99.9th percentile | largest | the cap's size | colluding juniors' player-years: median (largest) | share of the colluding juniors' creation above the cap |")
    p("|---|---|---|---|---|---|---|---|")
    caps = {}
    for x in ("L0", "R4A", "R4L", "R5", "ALL"):
        if x not in base[str(seeds[0])]["line2"]:
            continue
        ny = per("baseline", lambda r, x=x: r["line2"][x]["honest_player_years"])
        q99 = per("baseline", lambda r, x=x: r["line2"][x]["p99"])
        q999 = per("baseline", lambda r, x=x: r["line2"][x]["p999"])
        mx = per("baseline", lambda r, x=x: r["line2"][x]["max"])
        cap = math.ceil(mean(q999))
        caps[x] = cap
        col = [v for s_ in seeds for v in sc["adversaries"][str(s_)]["line2"][x]["colluding_juniors"]]
        above = sum(max(0.0, v - cap) for v in col) / sum(col) if col and sum(col) > 0 else None
        med = sorted(col)[len(col) // 2] if col else None
        p(f"| {NAMES[x]} | {mean(ny):,.0f} | {mr(q99, 0)} | {mr(q999, 0)} | {mr(mx, 0)} | {cap} | "
          f"{med:.0f} ({max(col):.0f}) | {'—' if above is None else f'{100 * above:.0f} %'} |")
    p("")
    p("The cap binds by construction on one honest player-year in a thousand; it enters rung 5's pilot and rung 4's "
      "FIDE-data test only (R29), where FIDE's data, not the simulator, set its size.")
    p("")

    # ---------------------------------------------------------------- 8 R1
    p("## 8 R1's review threshold (R19, R20, R31, R40)")
    p("")
    p(f"Twenty paired runs; R2's noise-corrected spread ratio for active adults, its trailing twelve-month mean against the "
      f"mean after the first twelve months of operation. The baseline's own trend: {mr(cal['slope_per_year'], 4, True)} a year; "
      f"the SD of the noise around it {cal['noise_sd']:.4f}.")
    p("")
    p("| θ_R1 | baseline runs that trigger (raw) | months to the first raw trigger, median | false alarms from noise alone | ratchet detected | months from the ratchet's start, median |")
    p("|---|---|---|---|---|---|")
    for th, v in cal["thresholds"].items():
        p(f"| {th} | {100 * v['raw_trigger_share']:.0f} % | {v['raw_median_months'] if v['raw_median_months'] is not None else '—'} | "
          f"{100 * v['noise_false_alarm_share']:.0f} % | {100 * v['ratchet_detect_share']:.0f} % | "
          f"{v['ratchet_median_months'] if v['ratchet_median_months'] is not None else '—'} |")
    p("")
    raw_c = cal["thresholds"][str(cal["calibrated"])] if cal["calibrated"] is not None else None
    p(f"- **Calibrated** (the smallest threshold with at most 5 % false alarms from noise; D-0009, reading 6): "
      f"{cal['calibrated']}" + (f", with {fa_k} false alarm(s) in {cal['runs']} runs (exact 95 % upper bound "
                                f"{100 * upper95(fa_k, cal['runs']):.0f} %)" if raw_c else "") + ".")
    p("- **What the calibration measures.** False alarms are counted on the noise around each run's own linear trend, and the "
      "ratchet's detection on the paired difference, ratchet minus baseline on the same seed, which removes the noise both "
      "share; both are therefore optimistic. The raw statistic the QC would watch triggers in "
      + (f"{100 * raw_c['raw_trigger_share']:.0f} % of baseline runs, at a median of {raw_c['raw_median_months']} months, "
         if raw_c else "")
      + "because the simulated published scale keeps compressing against true strength (section 4): a review the QC should "
      "hold, but one the ratio alone cannot tell from a ratchet of κ.")
    p("")
    pt = d["r1_paired_trigger"]
    p("**Under R31 and R40** the review triggers when the spread condition holds AND κ has sat at its annual cap; either "
      "alone is reported (D-0011, reading 13). The simulator holds κ fixed outside the ratchet scenario, so in the stationary "
      f"baseline κ never sits at its cap and the paired trigger cannot fire from noise: 0 false alarms in {cal['runs']} runs "
      "by construction, which the simulator cannot test further. In the ratchet runs κ sits at its cap from the twelfth month "
      "of operation, and the paired trigger is the raw statistic's first crossing from then on:")
    p("")
    p("| θ_R1 | ratchet runs that trigger | months to the trigger, median |")
    p("|---|---|---|")
    for th, v in pt.items():
        p(f"| {th} | {100 * v['detect_share']:.0f} % | {v['median_months'] if v['median_months'] is not None else '—'} |")
    p("")

    # ---------------------------------------------------------------- 9 sensitivity and assumptions
    n2 = {x: mean(err("noise2", x, "all", "rmse")) for x in led_all}
    t2 = {x: mean(top_rate("noise2", x)) for x in led_all}
    p("## 9 What rests on assumptions the data could not pin down")
    p("")
    best2 = min(led_all, key=lambda x: n2[x])
    best1 = min(led_all, key=lambda x: rmse_all[x])
    single2 = min((x for x in led_all if x not in ("L0", "ALL")), key=lambda x: n2[x])
    single1 = min((x for x in led_all if x not in ("L0", "ALL")), key=lambda x: rmse_all[x])
    p("**Twice the noise** (Layer 1's history fit, c = 2.0, against E8's 1.0): RMSE overall "
      + ", ".join(f"{x} {n2[x]:.0f}" for x in ("L0", "R2", "R3", "R4A", "R5", "ALL")) + "; the top cohort's change a year "
      + ", ".join(f"{x} {t2[x]:+.1f}" for x in ("L0", "R2", "ALL")) + ". "
      + f"With twice the noise the most accurate ledger is {NAMES[best2]} and the most accurate single rung is "
        f"{NAMES[single2]}; with E8's noise they are {NAMES[best1]} and {NAMES[single1]}.")
    p("")
    p("| result | rests on |")
    p("|---|---|")
    p("| the junior drain, the slide at the top, the level's drift | how fast juniors improve and how unevenly (Layer 1's profile, measured on broadcast juniors, scaled to the lists' junior gains) |")
    p("| newcomers' over-rating under today's rule, rung 3's effect on the level | entrants' true strengths (2023 first ratings, before the floor, moved to today's scale) |")
    p("| the level and d_t | the anchor panel, re-formed each January and chain-linked across the re-basing (SPEC-SIM §6) |")
    p("| rung 4's K and its effect | the noise scale (E8's 1.0 or Layer 1's 2.0) |")
    p("| federation offsets and their decay | the domestic share of games (between E7's 52 % on broadcast games and Ghita's more than 80 %) and the true offsets |")
    p("| everything that uses Layer 1 (rungs 3 to 7) | a proxy that knows the pool's average dynamics: optimistic |")
    p("| the guard | the true model is the v2 table, the table rung 2 v2 publishes, so the guard's cost shows and its benefit cannot |")
    p("| R1's threshold | the noise of the simulated spread ratio, on a pool about a twentieth of FIDE's active list, and a detrended noise reference |")
    p("")
    p("## 10 E9 beside E14")
    p("")
    p("E9's figures (the pool's true model E2's table, rung 2 with R17's guard at today's K, R16 as read in D-0009, accrual "
      "for eleven months after the last game) beside this rerun's (the v2 table as true model, rung 2 v2 with the narrowed "
      "guard at today's K, R25, R33), on the same scenarios and seeds:")
    p("")
    h9, h14 = headline(d9), headline(d)
    p("| figure | E9 | E14 |")
    p("|---|---|---|")
    for k, lab in HEADLINE_LABELS:
        p(f"| {lab} | {h9.get(k, '—')} | {h14.get(k, '—')} |")
    p("")
    p("## 11 Limits")
    p("")
    p("- A synthetic pool about a twentieth of FIDE's active list, in standard only, five seeds a scenario: differences of a few "
      "points between rungs are within the seeds' range.")
    p("- Pairings follow Layer 0's list for every rung (the shadow-list design), so a rung's effect on who meets whom is not "
      "simulated.")
    p("- The ledger identity of annex T6 is not evaluated line by line; the points entering, leaving through the floor and "
      "posted by adjustments are reported in the aggregates.")
    p("- SPEC-SIM §11 lists the revisions the pilot runs forced and the two the v1.0 red team found (entrants' scale, chain-linking), "
      "each with its reason; the runs reported here follow all of them, and `src/simulator/v2.py` lists what this rerun "
      "replaces.")
    sys.stdout.write("\n".join(P) + "\n")


if __name__ == "__main__":
    main()
