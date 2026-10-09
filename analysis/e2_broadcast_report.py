#!/usr/bin/env python3
"""E2 report: applies the decision rules of annex T8 to the broadcast aggregates.

Reads analysis/aggregates/E2_broadcast.json (written by analysis/e2_broadcast_extract.py;
games from the Lichess broadcast archive, CC BY-SA 4.0) and prints either the
evidence page docs/evidence/E2_broadcast-calibration.md or, with --yaml, the
parameter file params/table_fit_2026-10.yaml. Implements docs/specs/SPEC-TABLE-FIT_v1_0.md
§4: Holm-Bonferroni tests of the 50-point bins against +/-0.01, the weighted
across-bin slope, the do-no-harm check and the paired moving-block bootstrap by
month (blocks of 3, 2,000 resamples, seed 20261009). Python standard library only.

Usage: python3 analysis/e2_broadcast_report.py > docs/evidence/E2_broadcast-calibration.md
       python3 analysis/e2_broadcast_report.py --yaml > params/table_fit_2026-10.yaml
"""
from __future__ import annotations

import json
import math
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import layer0  # noqa: E402

AGG = ROOT / "analysis" / "aggregates" / "E2_broadcast.json"
TCS = ("standard", "rapid", "blitz")
SEED, RESAMPLES, BLOCK = 20261009, 2000, 3
BAND, MIN_BIN, ALPHA = 0.01, 1000, 0.05
Q = math.log(10.0) / 400.0
ATTRIBUTION = ("Game data: the Lichess broadcast archive (https://database.lichess.org/broadcast/), "
               "CC BY-SA 4.0, attributed; only aggregates are used here.")


def phi(z: float) -> float:
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def f4(x) -> str:
    return "-" if x is None else f"{x:.4f}"


def f3(x) -> str:
    return "-" if x is None else f"{x:.3f}"


def n_(x) -> str:
    return f"{int(x):,}"


def bin_stats(b: list, which: int) -> dict:
    """b = [n, sum S, sum E rung 2, sum E Layer 0, sum (S-E2)^2, sum (S-E0)^2, draws, sum P_D rung 2]."""
    n = b[0]
    s, e, sq = b[1] / n, b[2 + which] / n, b[4 + which] / n
    r = s - e
    var = max(sq - r * r, 1e-12)
    se = math.sqrt(var / n)
    return {"n": n, "score": s, "e": e, "r": r, "se": se}


def calibration(bins: list, which: int) -> dict:
    """T8.2: (a) Holm-Bonferroni one-sided tests against the nearer bound of +/-0.01; (b) the WLS slope."""
    rows = [dict(bin=k * 50, **bin_stats(b, which)) for k, b in enumerate(bins) if b[0] >= MIN_BIN]
    for r in rows:
        z = (abs(r["r"]) - BAND) / r["se"]
        r["p"] = 1.0 - phi(z)
        r["mdd"] = BAND + (1.6449 + 0.8416) * r["se"]          # smallest |residual| detected with 80 % power, 5 % one-sided
    order = sorted(range(len(rows)), key=lambda i: rows[i]["p"])
    m = len(rows)
    stop = False
    for rank, i in enumerate(order):
        rows[i]["outside"] = False
        if not stop and rows[i]["p"] <= ALPHA / (m - rank):
            rows[i]["outside"] = True
        else:
            stop = True
    a_pass = m > 0 and not any(r["outside"] for r in rows)
    slope = se_slope = None
    if m >= 3:
        w = [1.0 / r["se"] ** 2 for r in rows]
        sw = sum(w)
        mx = sum(wi * r["e"] for wi, r in zip(w, rows)) / sw
        my = sum(wi * r["score"] for wi, r in zip(w, rows)) / sw
        sxx = sum(wi * (r["e"] - mx) ** 2 for wi, r in zip(w, rows))
        slope = sum(wi * (r["e"] - mx) * (r["score"] - my) for wi, r in zip(w, rows)) / sxx
        se_slope = math.sqrt(1.0 / sxx)
    if slope is None:
        b_verdict = "inconclusive (fewer than 3 bins)"
    elif se_slope >= 0.02:
        b_verdict = "inconclusive (standard error 0.02 or more)"
    else:
        b_verdict = "pass" if 0.95 <= slope <= 1.05 else "fail"
    mean_abs = (sum(r["n"] * abs(r["r"]) for r in rows) / sum(r["n"] for r in rows)) if rows else None
    return {"rows": rows, "a_pass": a_pass, "slope": slope, "se_slope": se_slope, "b": b_verdict, "mean_abs": mean_abs,
            "m": m}


def all_bins_mean_abs(bins: list, which: int) -> float:
    rows = [bin_stats(b, which) for b in bins if b[0] > 0]
    return sum(r["n"] * abs(r["r"]) for r in rows) / sum(r["n"] for r in rows)


def block_bootstrap(months: list[str], per_month: dict, num: str, den: str = "n") -> tuple[float, float]:
    """Paired moving-block bootstrap by month of sum(num)/sum(den); blocks of 3 consecutive months."""
    rng = random.Random(SEED)
    m = len(months)
    starts = list(range(m - BLOCK + 1))
    blocks = -(-m // BLOCK)
    boots = []
    for _ in range(RESAMPLES):
        picked: list[str] = []
        for _ in range(blocks):
            s = rng.choice(starts)
            picked.extend(months[s:s + BLOCK])
        picked = picked[:m]
        boots.append(sum(per_month[x][num] for x in picked) / sum(per_month[x][den] for x in picked))
    boots.sort()
    return boots[int(math.ceil(0.025 * RESAMPLES)) - 1], boots[int(math.ceil(0.975 * RESAMPLES)) - 1]


def model_e(p: dict, x: float, mid: float) -> float:
    z = p["kappa"] * Q * x
    nu = math.exp(p["alpha"] + p["beta"] * (mid - 2000.0) / 400.0 - p["gamma"] * abs(z))
    a, b = math.exp(z / 2.0), math.exp(-z / 2.0)
    return (a + nu / 2.0) / (a + b + nu)


def yaml_out(d: dict) -> None:
    print("# params/table_fit_2026-10.yaml: generated by analysis/e2_broadcast_report.py --yaml; do not edit by hand.")
    print("status: PROVISIONAL-FITTED")
    print("spec: docs/specs/SPEC-TABLE-FIT_v1_0.md")
    print("model: annex T3.1 and T3.3 (decisions D1, D2); L at the midpoint of the 100-point level band")
    print("source:")
    print('  games: "Lichess broadcast archive, https://database.lichess.org/broadcast/, CC BY-SA 4.0 (attributed)"')
    print('  ratings: "FIDE monthly lists of the game\'s time control, analysed and not redistributed"')
    print(f"  files: \"{d['source']}\"")
    print("evaluation: docs/evidence/E2_broadcast-calibration.md")
    for tc in TCS:
        f = d["final_fit"].get(tc)
        if not f:
            continue
        print(f"{tc}:")
        print(f"  fit_window: {{from: \"{f['from']}\", to: \"{f['to']}\"}}")
        print(f"  games: {f['n']}")
        for k, digits in (("kappa", 4), ("eta", 2), ("alpha", 4), ("beta", 4), ("gamma", 4)):
            se = f["se"].get(k)
            se_txt = f"{se:.{digits}f}" if se else "null"
            print(f"  {k}: {{value: {f[k]:.{digits}f}, se: {se_txt}}}")
        print(f"  gamma_at_bound: {str(f['gamma_at_bound']).lower()}")


def main() -> int:
    d = json.loads(AGG.read_text(encoding="utf-8"))
    if "--yaml" in sys.argv[1:]:
        yaml_out(d)
        return 0
    raw, cov, desc = d["raw_counts"], d["coverage"], d["descriptive"]
    print("# E2 — The expectancy table against the broadcast archive\n")
    print("Status: REVIEW — evidence for rung 2 of the adoption ladder (session ELO-3, Phase 4.2), under "
          "`docs/specs/SPEC-TABLE-FIT_v1_0.md`. Generated by `analysis/e2_broadcast_report.py` from "
          "`analysis/aggregates/E2_broadcast.json` (written by `analysis/e2_broadcast_extract.py`); do not edit by hand. "
          f"Licence: CC BY 4.0 (`docs/LICENSE-docs.md`). {ATTRIBUTION} Ratings: FIDE's monthly lists, analysed and "
          "never redistributed [V 3]. Every fitted value is PROVISIONAL-FITTED.\n")

    print("## Coverage\n")
    print(f"- {d['source']}: {n_(raw['games'])} games, {n_(raw['with_result'])} with a result in standard chess; "
          f"{n_(raw['both_fide_ids'])} carry both players' FIDE IDs; {n_(d['duplicates_removed'])} duplicates across "
          "tours removed.")
    print(f"- Dates: {n_(raw['dated'])} games are dated by their tags, of which {n_(raw['dated_in_file_month'])} "
          f"({raw['dated_in_file_month'] / raw['dated']:.1%}) fall in their file's month; {n_(raw['date_from_file_month'])} "
          "are dated by their file's month (SPEC-TABLE-FIT §1).")
    print(f"- The rating tags of the broadcasts equal the list in force in {cov['elo_tag_equal'] / cov['elo_tag_compared']:.1%} "
          "of comparisons; the analysis uses the lists, not the tags.\n")
    print("| time control | games classified | both FIDE IDs | both rated on the list in force (sample) | share of classified |")
    print("|---|---|---|---|---|")
    for tc in TCS:
        c, b, r = cov["classified"][tc], cov["both_ids"][tc], cov["rated_both"][tc]
        print(f"| {tc} | {n_(c)} | {n_(b)} | {n_(r)} | {r / c:.1%} |")

    print("\n## The sample is stronger than the pool\n")
    print("Ratings in the sample (each game counts both players) against the ratings of every player with rated "
          "games on the same months' lists:\n")
    print("| time control | sample median | quartiles | share 2200 or more | pool median | quartiles | share 2200 or more |")
    print("|---|---|---|---|---|---|---|")
    for tc in TCS:
        s, p = desc[tc]["sample_ratings"], desc[tc]["list_players_with_games_same_months"]
        print(f"| {tc} | {s['median']} | {s['q1']}–{s['q3']} | {s['share_from_2200']:.1%} | {p['median']} | "
              f"{p['q1']}–{p['q3']} | {p['share_from_2200']:.1%} |")
    print("\nA result here holds for broadcast events, which are stronger and more international than the rated "
          "pool; the FIDE TRF archive settles the pool (annex T8.6).\n")

    print("## Descriptive measures, all months\n")
    std = desc["standard"]
    print(f"Standard: {n_(std['n_games'])} games, {n_(std['n_players'])} players, {n_(std['n_tours'])} tours; White "
          f"scores {std['white_score']:.4f} and {std['draw_rate']:.1%} of games are drawn.\n")
    print("**Table 8.1.2 by gap (standard).** The favourite's score against the table's H entry and against the PD "
          "FIDE uses (which caps the gap at 400 except for players rated 2650 or more from 1 October 2025):\n")
    print("| gap | games | favourite's score | table 8.1.2 | PD FIDE uses | score minus PD | draws |")
    print("|---|---|---|---|---|---|---|")
    for k, v in sorted(std["by_gap_50"].items(), key=lambda kv: int(kv[0])):
        n, s, t, pd, dr = v
        label = f"{k}+" if int(k) == 1000 else f"{k}–{int(k) + 49}"
        print(f"| {label} | {n_(n)} | {s / n:.3f} | {t / n:.3f} | {pd / n:.3f} | {s / n - pd / n:+.3f} | {dr / n:.1%} |")
    print("\n**White's edge and draws by level (standard).** Games between players at most 25 points apart, and the "
          "draw rate of all games, by 200-point level band:\n")
    print("| level | games within 25 points | White's score | draws among them | all games | draw rate |")
    print("|---|---|---|---|---|---|")
    for k, v in sorted(std["by_level_200"].items(), key=lambda kv: int(kv[0])):
        n, dr, nc, wc, dc = v
        label = "below 1600" if int(k) == 1400 else ("2600 or more" if int(k) == 2600 else f"{k}–{int(k) + 199}")
        print(f"| {label} | {n_(nc)} | {wc / nc:.3f} | {dc / nc:.1%} | {n_(n)} | {dr / n:.1%} |")
    print("\n**Colour balance per player and event.** Whites minus Blacks for every player with at least 5 games in a "
          "tour (3 means 3 or more):\n")
    print("| time control | ≤ −3 | −2 | −1 | 0 | +1 | +2 | ≥ +3 | share with \\|imbalance\\| ≥ 2 |")
    print("|---|---|---|---|---|---|---|---|---|")
    for tc in TCS:
        c = desc[tc]["colour_imbalance_player_events_5plus"]
        tot = sum(c.values())
        big = sum(v for k, v in c.items() if abs(int(k)) >= 2)
        print(f"| {tc} | " + " | ".join(n_(c.get(str(k), 0)) for k in range(-3, 4)) + f" | {big / tot:.1%} |")

    print("\n## The fit\n")
    print("Maximum likelihood on the last 36 months (SPEC-TABLE-FIT §2–3), with standard errors; these values are "
          "written to `params/table_fit_2026-10.yaml`:\n")
    print("| time control | window | games | κ | η | α | β | γ |")
    print("|---|---|---|---|---|---|---|---|")
    for tc in TCS:
        f = d["final_fit"][tc]
        se = f["se"]
        cell = lambda k, dg: f"{f[k]:.{dg}f} ({se[k]:.{dg}f})" if se.get(k) else f"{f[k]:.{dg}f}"
        print(f"| {tc} | {f['from']} to {f['to']} | {n_(f['n'])} | {cell('kappa', 3)} | {cell('eta', 1)} | "
              f"{cell('alpha', 3)} | {cell('beta', 3)} | {cell('gamma', 3)} |")
    print("\nRange of the monthly refits over the test months:\n")
    print("| time control | κ | η | γ |")
    print("|---|---|---|---|")
    for tc in TCS:
        pm = d["rolling"][tc]["per_month"]
        vals = {k: [v["params"][k] for v in pm.values()] for k in ("kappa", "eta", "gamma")}
        print(f"| {tc} | {min(vals['kappa']):.3f}–{max(vals['kappa']):.3f} | {min(vals['eta']):.1f}–"
              f"{max(vals['eta']):.1f} | {min(vals['gamma']):.3f}–{max(vals['gamma']):.3f} |")
    fs = d["final_fit"]["standard"]
    print("\nThe fitted function for standard (White's expected score at gap x, colour excluded) beside table 8.1.2's "
          "H entry:\n")
    mids = (1650, 2050, 2450, 2650)
    print("| x | " + " | ".join(f"level band {m - 50}–{m + 49}" for m in mids) + " | table 8.1.2 |")
    print("|---|" + "---|" * (len(mids) + 1))
    for x in range(0, 801, 100):
        print(f"| {x} | " + " | ".join(f"{model_e(fs, x, m):.3f}" for m in mids)
              + f" | {layer0.expected_score(x)} |")

    print("\n## Out of sample: rung 2 against Layer 0\n")
    print("Each test month is forecast from a fit on the 36 months before it (2025-01 to 2026-09, 21 months; "
          "SPEC-TABLE-FIT §3). Layer 0 is FIDE's expected score from the ratified engine, split into three outcomes with "
          "the training months' draw rate by level band.\n")
    print("| time control | test games | log-loss rung 2 | Layer 0 | difference (95 % interval) | Brier rung 2 | "
          "Layer 0 | RPS rung 2 | Layer 0 |")
    print("|---|---|---|---|---|---|---|---|---|")
    verdicts = {}
    for tc in TCS:
        r = d["rolling"][tc]
        months = r["test_months"]
        pm = {m: dict(r["per_month"][m]) for m in months}
        for m in months:
            pm[m]["diff"] = pm[m]["ll2"] - pm[m]["ll0"]
        n = sum(pm[m]["n"] for m in months)
        tot = {k: sum(pm[m][k] for m in months) / n for k in ("ll2", "ll0", "brier2", "brier0", "rps2", "rps0")}
        lo, hi = block_bootstrap(months, pm, "diff")
        verdicts[tc] = {"lo": lo, "hi": hi, "diff": tot["ll2"] - tot["ll0"], "months": len(months)}
        print(f"| {tc} | {n_(n)} | {tot['ll2']:.4f} | {tot['ll0']:.4f} | {tot['ll2'] - tot['ll0']:+.4f} "
              f"({lo:+.4f} to {hi:+.4f}) | {tot['brier2']:.4f} | {tot['brier0']:.4f} | {tot['rps2']:.4f} | "
              f"{tot['rps0']:.4f} |")
    print("\n### Calibration by 50-point gap bin (the favourite's side, all test months)\n")
    for tc in TCS:
        r = d["rolling"][tc]
        c2, c0 = calibration(r["bins"], 0), calibration(r["bins"], 1)
        verdicts[tc].update(c2=c2, c0=c0)
        print(f"**{tc.capitalize()}.** Bins with at least {MIN_BIN:,} games; residual = score − expectation; "
              "\"outside\" = significantly outside ±0.01 after Holm–Bonferroni; MDD = the smallest |residual| the "
              "bin detects with 80 % power:\n")
        print("| gap | games | score | rung 2 | residual (SE) | MDD | outside | Layer 0 | residual | outside |")
        print("|---|---|---|---|---|---|---|---|---|---|")
        by0 = {row["bin"]: row for row in c0["rows"]}
        for row in c2["rows"]:
            r0 = by0[row["bin"]]
            print(f"| {row['bin']}–{row['bin'] + 49} | {n_(row['n'])} | {row['score']:.4f} | {row['e']:.4f} | "
                  f"{row['r']:+.4f} ({row['se']:.4f}) | {row['mdd']:.4f} | {'yes' if row['outside'] else 'no'} | "
                  f"{r0['e']:.4f} | {r0['r']:+.4f} | {'yes' if r0['outside'] else 'no'} |")
        sl = lambda c: (f"{c['slope']:.3f} (SE {c['se_slope']:.3f}): {c['b']}" if c["slope"] is not None else c["b"])
        print(f"\nRule (a): rung 2 {'passes' if c2['a_pass'] else 'fails'} ({sum(r['outside'] for r in c2['rows'])} of "
              f"{c2['m']} bins outside); Layer 0 {'passes' if c0['a_pass'] else 'fails'} "
              f"({sum(r['outside'] for r in c0['rows'])} of {c0['m']} bins outside). Rule (b), slope: rung 2 {sl(c2)}; "
              f"Layer 0 {sl(c0)}.")
        fb = [b for b in r["farming_bins"]]
        far_n = sum(b[0] for b in fb)
        cf = calibration(fb, 0)
        verdicts[tc]["farming"] = cf
        res = (sum(b[1] for b in fb) - sum(b[2] for b in fb)) / far_n if far_n else None
        res0 = (sum(b[1] for b in fb) - sum(b[3] for b in fb)) / far_n if far_n else None
        print(f"Farming region (gap 400 or more, level 2300 or more): {n_(far_n)} test games, "
              f"{cf['m']} bins with at least {MIN_BIN:,}; pooled residual rung 2 {f4(res)}, Layer 0 {f4(res0)} "
              f"({'tested' if cf['m'] else 'not testable at the pre-registered bin size: inconclusive'}).")
        for name, key in (("favourite White", "white_favourite_bins"), ("favourite Black", "black_favourite_bins")):
            cb = calibration(r[key], 0)
            worst = max(cb["rows"], key=lambda row: abs(row["r"])) if cb["rows"] else None
            print(f"Colour, {name}: {cb['m']} bins with at least {MIN_BIN:,} games, "
                  f"{sum(row['outside'] for row in cb['rows'])} outside; largest |residual| "
                  f"{f4(abs(worst['r'])) if worst else '-'}.")
        print()
    print("### Decision (annex T8.2, SPEC-TABLE-FIT §4)\n")
    print("| time control | test months | calibration (a) | slope (b) | do-no-harm: log-loss | do-no-harm: mean \\|residual\\| "
          "rung 2 / Layer 0 | log-loss better, interval excludes zero | rung 2 |")
    print("|---|---|---|---|---|---|---|---|")
    for tc in TCS:
        v = verdicts[tc]
        c2, c0 = v["c2"], v["c0"]
        r = d["rolling"][tc]
        ma2, ma0 = all_bins_mean_abs(r["bins"], 0), all_bins_mean_abs(r["bins"], 1)
        harm_ll = v["hi"] <= 0.002
        harm_cal = ma2 <= ma0 + 0.005
        better = v["hi"] < 0
        enough = v["months"] >= 12
        b_ok = c2["b"] == "pass"
        passes = enough and c2["a_pass"] and b_ok and harm_ll and harm_cal and better
        verdict = "passes" if passes else ("inconclusive" if c2["b"].startswith("inconclusive") and c2["a_pass"] else "fails")
        print(f"| {tc} | {v['months']} | {'pass' if c2['a_pass'] else 'fail'} | {c2['b']} | "
              f"{'pass' if harm_ll else 'fail'} (upper {v['hi']:+.4f}) | {'pass' if harm_cal else 'fail'} "
              f"({ma2:.4f} / {ma0:.4f}) | {'yes' if better else 'no'} | {verdict} |")
    print("\nThe farming region and the colour split are reported above; at the pre-registered bin size of 1,000 games "
          "the farming region cannot be tested on this sample.\n")

    print("## Limits\n")
    print("- The sample is broadcast events: stronger and more international than the pool (table above). A pass "
          "here supports rung 2 for that population only.")
    print("- Whether a broadcast game was FIDE-rated is not recorded; a game enters when both players are rated on the "
          "list of its time control in force.")
    print("- Layer 0 has no draw model; its three-outcome forecast uses the training months' draw rate by level band, "
          "and its probabilities are floored so that the log-loss stays finite (SPEC-TABLE-FIT §3). The Brier score on "
          "the expected score needs no draw model and is reported beside it.")
    print("- Rung 2 is fitted and tested on published ratings (decision D2); it says nothing about Layer 1.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
