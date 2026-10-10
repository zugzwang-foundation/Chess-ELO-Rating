#!/usr/bin/env python3
"""E6 report: turns analysis/aggregates/E6_rungs.json into docs/evidence/E6_rungs-on-history.md.

Reads only committed aggregates (E6, and the Layer 1 history fit for the
hyperparameters and coverage); no data/ needed. Applies the pre-registered
decision rules of annex T8.1–T8.2 to rungs 3 to 6 and states, for each, what the
broadcast data can and cannot settle.

Usage: python3 analysis/e6_rungs_report.py > docs/evidence/E6_rungs-on-history.md
"""
from __future__ import annotations

import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AGG = ROOT / "analysis" / "aggregates"
D0, GAMMA_A = 2.0, 1.0 / 6.0          # annex T4.5 (PROVISIONAL)
HARM_LL, HARM_CAL = 0.002, 0.005      # annex T8.2 do-no-harm tolerances (PROVISIONAL)
POP_NAMES = {"adults": "adults (aged 20 or more, or without a year of birth) against eligible juniors: the pre-registered metric",
             "eligible": "every opponent who is not eligible, juniors included (where R8 applies the compensation)",
             "adults_compensated": "adults, games in which the junior's c_j is above zero (where the rung changes the expectation)"}


def s1(x: float) -> str:
    """Signed, one decimal, without a negative zero."""
    return f"{round(x, 1) + 0.0:+.1f}"


def n0(x) -> str:
    return "—" if x is None else f"{x:,}"


def ci(b: dict, nd: int = 4) -> str:
    if not b or not b.get("n"):
        return "—"
    return f"{b['mean']:+.{nd}f} ({b['lo']:+.{nd}f} to {b['hi']:+.{nd}f})"


def holm(ps: dict[str, float], alpha: float = 0.025) -> dict[str, bool]:
    """Holm–Bonferroni across groups: True where the group is significantly outside its bound (one-sided p-values; the
    level 0.025 matches a single group's 95 % interval rule of annex T8.2)."""
    order = sorted(ps, key=lambda k: (ps[k], k))
    out, m, stop = {}, len(order), False
    for r, k in enumerate(order):
        sig = not stop and ps[k] < alpha / (m - r)
        stop = stop or not sig
        out[k] = sig
    return out


def residual_rule(rung: dict, base: dict, bands_rung: dict, bands_base: dict, b: float) -> tuple[bool, str]:
    """Annex T8.1/T8.2: the rung's residual not significantly outside ±b (overall and, with Holm, by band) and closer to
    zero than Layer 0's."""
    inside = rung.get("p_outside", 1.0) >= 0.025
    closer = abs(rung["mean"]) < abs(base["mean"])
    sig = holm({k: v.get("p_outside", 1.0) for k, v in bands_rung.items() if v.get("n")})
    bad = [k for k, s in sig.items() if s]
    worse = [k for k, v in bands_rung.items() if v.get("n") and k in bands_base and abs(v["mean"]) >= abs(bands_base[k]["mean"])]
    ok = inside and closer and not bad
    why = (f"overall {'inside' if inside else 'significantly outside'} ±{b}, {'closer to zero' if closer else 'not closer to zero'} "
           f"than Layer 0's; bands significantly outside after Holm: {', '.join(bad) or 'none'}; bands not closer to zero: "
           f"{', '.join(worse) or 'none'}")
    return ok, why


def harm(ll: dict, cal: dict) -> tuple[bool, str]:
    ok_ll = ll.get("n", 0) and ll["hi"] <= HARM_LL
    ok_cal = cal.get("n", 0) and cal["difference"] <= HARM_CAL
    return bool(ok_ll and ok_cal), (f"log-loss difference {ci(ll)} nats a game (upper end at most {HARM_LL}: "
                                    f"{'yes' if ok_ll else 'no'}); calibration residual {cal.get('layer0')} under Layer 0, "
                                    f"{cal.get('rung')} under the rung (difference at most {HARM_CAL}: {'yes' if ok_cal else 'no'})")


def main() -> None:
    d = json.loads((AGG / "E6_rungs.json").read_text(encoding="utf-8"))
    h = json.loads((AGG / "L1_history.json").read_text(encoding="utf-8"))
    P: list[str] = []
    p = P.append
    r3, r4, r5, r6 = d["rung3"], d["rung4"], d["rung5"], d["rung6"]
    months = d["test_months"]

    # ---------------------------------------------------------------- verdicts
    ok3, why3 = (residual_rule(r3["residual_rung3"], r3["residual_layer0"], r3["by_band_rung3"], r3["by_band_layer0"], 0.02)
                 if r3.get("games") else (False, "no games"))
    harm3, hwhy3 = harm(r3.get("log_loss_difference", {}), r3.get("calibration", {}))
    top = r4["log_loss_difference_top_quartile"]
    ok4 = bool(top.get("n")) and top["hi"] < 0
    harm4, hwhy4 = harm(r4["log_loss_difference"], r4["calibration"])
    pe = r5["populations"]["adults"]
    ok5, why5 = (residual_rule(pe["opponent_residual_rung5"], pe["opponent_residual_layer0"], pe["by_opponent_band_rung5"],
                               pe["by_opponent_band_layer0"], 0.01) if pe["opponent_residual_layer0"].get("n") else (False, "no games"))
    harm5, hwhy5 = harm(pe["log_loss_difference"], pe["calibration"])
    r6v = {}
    for tc, rows in r6.items():
        late = [r for r in rows[12:] if "D_t_rung6" in r]
        drift = (rows[-1]["d_t_layer0"] - rows[0]["d_t_layer0"]) / (len(rows) - 1)
        bound = D0 + abs(drift) / GAMMA_A + 2.0
        within = all(abs(r["D_t_rung6"]) <= 2.0 for r in late) if late else None
        level = all(abs(r["d_t_rung6"]) <= bound for r in late) if late else None
        r6v[tc] = {"late": late, "drift": drift, "bound": bound, "within": within, "level": level,
                   "d0_within": all(abs(r["D_t_layer0"]) <= 2.0 for r in late) if late else None}

    def word(ok: bool) -> str:
        return "passes" if ok else "does not pass"

    p("# E6 — Rungs 3 to 6 on history: Layer 1 against Layer 0 on broadcast games")
    p("")
    p("Status: REVIEW — evidence for the proposal (§9, §10) and annex (T4.3–T4.7, T8.1, T8.10), session ELO-4, Phase 4 (decision "
      "D12). Generated by `analysis/e6_rungs_report.py` from `analysis/aggregates/E6_rungs.json`, which "
      "`analysis/e6_rungs_extract.py` computes under `docs/specs/SPEC-L1_v1_0.md` from the Lichess broadcast archive "
      "(https://database.lichess.org/broadcast/, CC BY-SA 4.0, attributed; aggregates only) [V 4] and FIDE's monthly lists "
      "(analysed, never committed or redistributed) [V 3]; Layer 0 is `src/layer0/` (SPEC-L0). Do not edit by hand. Licence: "
      "CC BY 4.0 (`docs/LICENSE-docs.md`). Every parameter is PROVISIONAL; every Layer 1 value is PROVISIONAL-FITTED on broadcast "
      "games, which are stronger and more international than the rated pool [E2].")
    p("")
    p("**In brief.** On rolling held-out months from "
      f"{months[0]} to {months[-1]}, each rung was tested against Layer 0 on the problem it targets, with everything else held at "
      "Layer 0, under the decision rules pre-registered in annex T8 (T8.1–T8.2):")
    p("")
    p(f"- **Rung 3, newcomer seeds:** {word(ok3 and harm3)} on the {n0(r3.get('seeded_by_rung3'))} newcomers the broadcast data "
      f"can seed ({n0(r3.get('games'))} games); residual over their first games {ci(r3.get('residual_layer0'))} with FIDE's first "
      f"rating, {ci(r3.get('residual_rung3'))} with the seed: closer to zero on average"
      + ("" if harm3 else f", but log-loss worse by {r3['log_loss_difference']['mean']:.3f} nats a game, because seeds from broadcast "
         "games alone are noisier than first ratings from every rated game") + ".")
    p(f"- **Rung 4, K from certainty (R6):** {word(ok4 and harm4)}; log-loss of next month's games for the players whose K changes "
      f"most {ci(top, 5)} nats a game (negative is better), overall {ci(r4['log_loss_difference'], 5)}.")
    red = 1 - abs(pe["opponent_residual_rung5"]["mean"]) / abs(pe["opponent_residual_layer0"]["mean"])
    p(f"- **Rung 5, junior compensation (R5, R8):** {word(ok5 and harm5)}; the adults' residual against eligible juniors "
      f"{ci(pe['opponent_residual_layer0'])} under Layer 0 and {ci(pe['opponent_residual_rung5'])} with compensation "
      f"({n0(pe['opponent_residual_layer0'].get('n'))} games): the drain falls by {100 * red:.0f} % and forecasts improve "
      f"(log-loss {pe['log_loss_difference']['mean']:+.4f} nats a game), but"
      + (" the residual stays significantly outside ±0.01" if pe["opponent_residual_rung5"].get("p_outside", 1) < 0.025 else " it fails a band")
      + ", in the bands below 2000 most.")
    p("- **Rung 6, the monthly adjustment (R3):** " + "; ".join(
        f"{tc}: D_t from month 13 {'within' if v['within'] else 'not within'} ±2 points a year, level criterion "
        f"{'met' if v['level'] else 'not met'}" for tc, v in r6v.items() if v["late"]) +
      ". The fixed panel's published mean rose over these months, as E5 found for steadily active adults, while the controller, "
      "which follows the gap to Layer 1 rather than the published mean, paid at most half a point a month (section 5).")
    p("- **What the broadcast data cannot settle:** the juniors and newcomers the rungs are meant for, below 2000 in domestic events, "
      "are almost absent (OUTPUT_L1_history §5); every result here holds for the broadcast population, and FIDE's tournament "
      "reports (the TRF archive) settle it for the pool (annex T8.6).")
    p("")

    # ---------------------------------------------------------------- 1 protocol
    hp = d["hyperparameters"]
    fits = d["fits"]
    p("## 1 Protocol")
    p("")
    p(f"- **Origins.** {len(months)} test months, {months[0]} to {months[-1]}. At each month t, Layer 1 is fitted on the months "
      "before t (36 at most, starting from the archive's first month 2023-01), warm-started from the previous month's fit, with the "
      f"hyperparameters chosen in the history fit (c_θ {hp['c_theta']}, ω {hp['omega']}; `analysis/OUTPUT_L1_history.md`). "
      "Every quantity used at t comes from that fit and from the list of month t; nothing from month t's games or later enters it.")
    p(f"- **Fits.** Games per fit {n0(min(f['games'] for f in fits))} to {n0(max(f['games'] for f in fits))}, players "
      f"{n0(min(f['players'] for f in fits))} to {n0(max(f['players'] for f in fits))}, sweeps {min(f['sweeps'] for f in fits)} to "
      f"{max(f['sweeps'] for f in fits)}; the anchor's final shift at most {max(abs(f['anchor_shift']) for f in fits):.2f} points.")
    p("- **Layer 0.** FIDE's expected score from table 8.1.2 with the 400-point rule and, in standard from October 2025, the 2650 "
      "exemption (`src/layer0/`), on the published ratings and K of the list in force; three-outcome scores split it with the draw "
      "rate of the game's level band in the 12 months before (annex T8.3, as E2).")
    p("- **Intervals.** Paired moving-block bootstrap by month, blocks of 3, 2,000 resamples, seed 20261009 (annex T8.5). "
      "\"Not significantly outside ±b\" means the 95 % interval overlaps [−b, +b]; across rating bands Holm–Bonferroni is applied "
      "to one-sided bootstrap p-values against the nearer bound (T8.2).")
    p("- **Do no harm** (every rung, T8.2): the upper end of the 95 % interval of the log-loss difference at most "
      f"{HARM_LL} nats a game, and the game-weighted mean absolute calibration residual over 50-point gap bins at most {HARM_CAL} "
      "worse than Layer 0's, measured on the games the rung changes (stricter than on all games, where unchanged games add zeros).")
    p("")

    # ---------------------------------------------------------------- 2 rung 3
    p("## 2 Rung 3: newcomer seeds (annex T4.7)")
    p("")
    p(f"- **Who.** Players first rated on list t in a time control who have broadcast games before t: "
      f"{n0(r3.get('newcomers_first_rated_with_games_before'))}; a seed is published for {n0(r3.get('seeded_by_rung3'))} "
      "(at least 5 games against rated opponents in the 26 months before t, 3 opponents, 2 events, σ̃ at most 120 and θ̃ at least "
      "1400, capped at 2200).")
    if r3.get("seed_difference") is not None:
        p(f"- **The seed against FIDE's first rating:** mean {r3['seed_difference']:+.1f} points, median "
          f"{r3['seed_difference_median']:+.1f} (seed minus FIDE).")
    p("- **Test.** Each newcomer's first 30 broadcast games in that time control from month t, against rated opponents, with the "
      "first rating held fixed: S − E with FIDE's first rating (Layer 0) and with the seed.")
    p("")
    p("| band of FIDE's first rating | games | residual, Layer 0 | residual, rung 3 |")
    p("|---|---|---|---|")
    for b in sorted(set(r3.get("by_band_layer0", {})) | set(r3.get("by_band_rung3", {}))):
        a0, a3 = r3["by_band_layer0"].get(b, {}), r3["by_band_rung3"].get(b, {})
        p(f"| {b} | {n0(a0.get('n'))} | {ci(a0)} | {ci(a3)} |")
    p(f"| all | {n0(r3.get('games'))} | {ci(r3.get('residual_layer0'))} | {ci(r3.get('residual_rung3'))} |")
    p("")
    p(f"- **Targeted rule** (residual not significantly outside ±0.02, closer to zero than Layer 0's, by band): {why3}.")
    p(f"- **Do no harm:** {hwhy3}.")
    p(f"- **Verdict on broadcast data:** rung 3 {word(ok3 and harm3)}.")
    p("")

    # ---------------------------------------------------------------- 3 rung 4
    p("## 3 Rung 4: K from certainty (R6; annex T4.3)")
    p("")
    p("- **Test.** Each player's rating is carried through month t's broadcast games, once with FIDE's K and once with K_i of R6 "
      "(from the fit before t), and month t + 1's broadcast games are forecast from the carried ratings, both with Layer 0's "
      "expected score. The targeted group is the games of the players whose |K_i − K| is in the top quarter of the month.")
    p("")
    p("| metric | games | rung 4 minus Layer 0 |")
    p("|---|---|---|")
    p(f"| log-loss, players whose K changes most (targeted) | {n0(top.get('n'))} | {ci(top, 5)} |")
    p(f"| Brier, same games | {n0(r4['brier_difference_top_quartile'].get('n'))} | {ci(r4['brier_difference_top_quartile'], 5)} |")
    p(f"| log-loss, every forecast game | {n0(r4['log_loss_difference'].get('n'))} | {ci(r4['log_loss_difference'], 5)} |")
    p(f"| Brier, every forecast game | {n0(r4['brier_difference'].get('n'))} | {ci(r4['brier_difference'], 5)} |")
    p("")
    p(f"- **Targeted rule** (log-loss better than Layer 0's with the interval excluding zero): {'met' if ok4 else 'not met'}.")
    p(f"- **Do no harm:** {hwhy4}.")
    p(f"- **Verdict on broadcast data:** rung 4 {word(ok4 and harm4)}.")
    p("")
    ke = r4["k_elite_2600_standard"]
    p(f"**The K distribution** (player-months with a broadcast game in the month; K_i to one decimal). Established 2600+ players "
      f"(standard, rated 2600 or more, aged 20 or more): {n0(ke.get('n'))} player-months, K_i p10 {ke.get('p10')}, median "
      f"{ke.get('median')}, p90 {ke.get('p90')} (today's K is 10 for them) (R6).")
    p("")
    p("| time control | band | player-months | p10 | median | p90 | mean |")
    p("|---|---|---|---|---|---|---|")
    order = ["<1600", "1600-1999", "2000-2399", "2400-2599", "2600+"]
    for key in sorted(r4["k_by_band"], key=lambda k: (["standard", "rapid", "blitz"].index(k.split("|")[0]), order.index(k.split("|")[1]))):
        v = r4["k_by_band"][key]
        tc, b = key.split("|")
        p(f"| {tc} | {b} | {n0(v['n'])} | {v['p10']} | {v['median']} | {v['p90']} | {v['mean']} |")
    p("")
    p("| time control | FIDE's K | player-months | K_i p10 | median | p90 |")
    p("|---|---|---|---|---|---|")
    for key in sorted(r4["k_by_fide_k"], key=lambda k: (["standard", "rapid", "blitz"].index(k.split("|")[0]), int(k.split("|")[1]))):
        v = r4["k_by_fide_k"][key]
        tc, k = key.split("|")
        p(f"| {tc} | {k} | {n0(v['n'])} | {v['p10']} | {v['median']} | {v['p90']} |")
    p("")
    st = r4["monthly_change_established"]
    p(f"- **Stability of established ratings** (adults with FIDE's K of 10 or 20, the absolute change from one month's broadcast "
      f"games): median {st['layer0'].get('median')} points with FIDE's K, {st['rung4'].get('median')} with K_i; p90 "
      f"{st['layer0'].get('p90')} and {st['rung4'].get('p90')}.")
    p("- **Why K_i is high here.** σ in the fit comes from broadcast games only, a fraction of each player's rated games, so σ, and "
      "with it K_i, is larger than a fit on FIDE's full record would give; most broadcast players below 2400 sit at K_max = 40 "
      "(OUTPUT_L1_history §4). The K distribution above is an upper bound for the pool, not a forecast of the list.")
    p("")

    # ---------------------------------------------------------------- 4 rung 5
    p("## 4 Rung 5: junior compensation (R5, R8; annex T4.6)")
    p("")
    jm = r5["junior_month_rows"]
    p(f"- **Eligibility** (junior-months of rated juniors aged 19 or less with broadcast games before t): {n0(jm.get('junior_rows'))} "
      f"rows; passing the game, opponent and event gates on broadcast games {n0(jm.get('pass_gates'))}; eligible after R5's "
      f"information share ≥ 0.5 {n0(jm.get('eligible'))} ({n0(jm.get('fail_share_only'))} fail on the share alone); with c_j > 0 "
      f"{n0(jm.get('compensated'))}.")
    cnt = r5["counts"]
    p(f"- **R8.** Games between two eligible juniors use published ratings on both sides: {n0(cnt.get('eligible_junior_pairs', 0))} "
      f"games, {n0(cnt.get('eligible_junior_pairs_with_c_j', 0))} of them with a c_j above zero on one side.")
    p("- **Test.** The opponent's residual S − E against the junior, with the junior's published rating (Layer 0) and with "
      "RX_j = R_j + c_j, and the points the opponents lose, Σ K (S − E), with FIDE's K.")
    p("")
    p("| population | games | opponents' residual, Layer 0 | with compensation | points per game, Layer 0 | with compensation | points, total: Layer 0 / with compensation |")
    p("|---|---|---|---|---|---|---|")
    for pop, v in r5["populations"].items():
        p(f"| {POP_NAMES[pop]} | {n0(v['opponent_residual_layer0'].get('n'))} | {ci(v['opponent_residual_layer0'])} | "
          f"{ci(v['opponent_residual_rung5'])} | {ci(v['points_per_game_layer0'], 3)} | {ci(v['points_per_game_rung5'], 3)} | "
          f"{v['points_total_layer0']:+,.1f} / {v['points_total_rung5']:+,.1f} |")
    p("")
    p("By the adult opponent's band (the pre-registered metric):")
    p("")
    p("| opponent's band | games | residual, Layer 0 | with compensation |")
    p("|---|---|---|---|")
    for b in ["<1600", "1600-1999", "2000-2399", "2400+"]:
        a0, a5 = pe["by_opponent_band_layer0"].get(b), pe["by_opponent_band_rung5"].get(b)
        if a0:
            p(f"| {b} | {n0(a0['n'])} | {ci(a0)} | {ci(a5)} |")
    p("")
    pc, pall = r5["populations"]["adults_compensated"], r5["populations"]["eligible"]
    p(f"- **Where the drain remains.** In the games where c_j is above zero the adults' residual moves from "
      f"{ci(pc['opponent_residual_layer0'])} to {ci(pc['opponent_residual_rung5'])}; the remaining drain comes from eligible juniors "
      "whose c_j is zero, under-rated but not by more than τ plus 1.2816 σ̃ (annex T4.6): the lower-quantile design avoids the "
      "winner's curse by compensating only what the model is 90 % sure of, and leaves the rest. Over every non-eligible opponent, "
      f"juniors included, the residual moves from {ci(pall['opponent_residual_layer0'])} to {ci(pall['opponent_residual_rung5'])}.")
    p(f"- **Targeted rule** (adults' residual not significantly outside ±0.01, by band, closer to zero than Layer 0's): {why5}.")
    p(f"- **Do no harm:** {hwhy5}.")
    p(f"- **Verdict on broadcast data:** rung 5 {word(ok5 and harm5)}.")
    p("")

    # ---------------------------------------------------------------- 5 rung 6
    p("## 5 Rung 6: the monthly adjustment (R3; annex T4.5)")
    p("")
    p("- **Replay.** At each test month the controller of T4.5 is run on that month's rolling d_t = m̂_t − m_t, the mean gap between "
      "Layer 1's estimate and the published rating over the anchor panel's members in that month's fit (the panel fixed at 2025-01, "
      "SPEC-L1 §3.5), net of their carried balances, so that d_t is measured on the settled ratings R + B. a_t accrues to every panel "
      "member active on the lists (a rated game on the 12 lists up to t), scaled by min(1, n_i ÷ the panel's mean games) (R3). "
      "Layer 0 is the same without the adjustment.")
    p("- **Rules** (T8.1): D_t, the twelve-month change of the whole fixed panel's mean, paired over the members on both lists "
      "(published ratings for Layer 0, settled ratings for rung 6), within ±2 points a year from month 13 of operation; and the level "
      "criterion |d_t| ≤ d_0 + |drift| ÷ γ_a + 2, with the drift the mean monthly change of Layer 0's d_t over the test months.")
    p("")
    p("| time control | months scored | monthly drift of d_t | level bound | D_t, Layer 0 (from month 13) | D_t, rung 6 | d_t, rung 6 | mean a_t | criteria |")
    p("|---|---|---|---|---|---|---|---|---|")
    for tc, v in r6v.items():
        rows = r6[tc]
        late = v["late"]
        if not late:
            continue
        d0s = [r["D_t_layer0"] for r in late]
        d6s = [r["D_t_rung6"] for r in late]
        dt6 = [r["d_t_rung6"] for r in late]
        p(f"| {tc} | {len(late)} | {v['drift']:+.2f} | {v['bound']:.1f} | {min(d0s):+.1f} to {max(d0s):+.1f} | "
          f"{min(d6s):+.1f} to {max(d6s):+.1f} | {min(dt6):+.1f} to {max(dt6):+.1f} | "
          f"{statistics.fmean(r['a_t'] for r in rows):+.2f} | D_t: {'met' if v['within'] else 'not met'}; level: {'met' if v['level'] else 'not met'} |")
    p("")
    p("| month | " + " | ".join(f"{tc}: d_t, Layer 0 / rung 6 / a_t" for tc in r6) + " |")
    p("|---|" + "---|" * len(r6))
    for k, m in enumerate(months):
        if k % 3 == 0 or k == len(months) - 1:
            p(f"| {m} | " + " | ".join(f"{s1(r6[tc][k]['d_t_layer0'])} / {s1(r6[tc][k]['d_t_rung6'])} / {s1(r6[tc][k]['a_t'])}"
                                      for tc in r6) + " |")
    p("")
    for tc, v in r6v.items():
        late = v["late"]
        if not late:
            continue
        rows = r6[tc]
        p(f"- **{tc}.** Over twelve months from month 13 the panel's published mean changed by {min(r['D_t_layer0'] for r in late):+.1f} to "
          f"{max(r['D_t_layer0'] for r in late):+.1f} points ({min(r['D_t_rung6'] for r in late):+.1f} to {max(r['D_t_rung6'] for r in late):+.1f} "
          f"with the adjustment); d_t ranged from {s1(min(r['d_t_layer0'] for r in rows))} to {s1(max(r['d_t_layer0'] for r in rows))} and a_t "
          f"from {s1(min(r['a_t'] for r in rows))} to {s1(max(r['a_t'] for r in rows))} a month.")
    p("- **Reading.** The D_t rule fails in every time control because the fixed panel's published mean rose over these months, as "
      "E5 found for steadily active adults since March 2024 [E5]. The controller does not act on D_t but on d_t, the gap between "
      "Layer 1's estimate of the same players and their published ratings, which stayed within a few points; it therefore paid at "
      "most half a point a month, with the sign of d_t: where Layer 1 judged the panel stronger than its published ratings the "
      "payments raised D_t slightly, where weaker they lowered it slightly. The D_t rule assumes the anchor panel's strength is "
      "constant; for a fixed panel of active adults it need not be, and on these months it measured the panel's improvement as much "
      "as any drift of the scale. The level criterion on d_t holds. Whether rung 6 should be judged on D_t, on d_t, or on D_t net of "
      "Layer 1's estimate of the panel's change is a design question for the architect; the controller under sustained drift is for "
      "the simulator of annex T9.")
    p("")

    # ---------------------------------------------------------------- 6 R12
    p("## 6 R12: the farming region, pooled (low power)")
    p("")
    p("Per ruling R12, every gap of 400 points or more at level 2300 or above is pooled into one bin, from the rolling test months of "
      "E2 (`analysis/aggregates/E2_broadcast.json`), for a directional test with its interval. Labelled low-power: the formal test "
      "of annex T8.2 needs 1,000 games per 50-point bin and waits for FIDE's game archive.")
    p("")
    p("| time control | games | residual S − E, rung 2 (fitted table) | Layer 0 (table 8.1.2) |")
    p("|---|---|---|---|")
    for tc, v in d["r12_farming_region"].items():
        p(f"| {tc} | {n0(v['games'])} | {v['rung2']['residual']:+.4f} ({v['rung2']['lo']:+.4f} to {v['rung2']['hi']:+.4f}) | "
          f"{v['layer0']['residual']:+.4f} ({v['layer0']['lo']:+.4f} to {v['layer0']['hi']:+.4f}) |")
    p("")
    p("The residual is the favourite's, so a negative value is the favourite scoring below the expectation; intervals are normal "
      "approximations (± 1.96 standard errors of the per-game residual), not the month bootstrap.")
    p("")

    # ---------------------------------------------------------------- 7 limits
    cov = {(c["band"], c["age"]): c for c in h["at_list"]["standard"]["coverage"]}
    jun_u = sum(c["usable"] for (b, a), c in cov.items() if a == "<=18" and b != "unrated")
    jun_p = sum(c["pool"] for (b, a), c in cov.items() if a == "<=18" and b != "unrated")
    p("## 7 What the data cannot support, and the data that would")
    p("")
    p(f"- **Juniors and newcomers below 2000.** In standard, {n0(jun_u)} of {n0(jun_p)} active rated juniors aged 18 or less have a "
      "usable Layer 1 estimate from broadcast games (OUTPUT_L1_history §5); rungs 3 and 5 are tested on the few strong juniors and "
      "newcomers who play broadcast events. The data that would settle them: FIDE's tournament reports (TRF, §9.1 of the rating "
      "regulations [V 1]), which hold every rated game.")
    p("- **K and the gates.** σ, K_i, the compensation gates and the seed gates are computed on broadcast games only, a fraction of each "
      "player's rated games: σ and K_i are biased upward and fewer juniors pass the gates than FIDE's record would allow.")
    p("- **Rung 6 under drift.** The test months fall in a period with almost no drift of the level; the controller's behaviour "
      "under sustained drift needs the simulator (annex T9) or a longer record.")
    p("- **Rung 7 and the farming region.** Federation offsets are not tested here (Phase 5 of the session tests only the direction of "
      "federation residuals); rung 7 and the formal farming-region test need FIDE's game archive (annex T8.1, R12).")
    print("\n".join(P))


if __name__ == "__main__":
    main()
