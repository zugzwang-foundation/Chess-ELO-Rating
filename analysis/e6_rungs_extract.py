#!/usr/bin/env python3
"""E6 extraction: rungs 3 to 6 against Layer 0 on history (ELO-4, Phase 4, decision D12; needs data/).

On rolling held-out months (2025-01 to 2026-09) Layer 1 is refitted at each month t
on the 36 months before it (SPEC-L1, warm-started from the previous month's fit,
hyperparameters as chosen in `analysis/aggregates/L1_history.json`), and each rung
is compared with Layer 0 (FIDE's rules, `src/layer0`) on the problem it targets,
with everything else held at Layer 0 (annex T8.1):
 - rung 3, newcomer seeds: players first rated on list t; FIDE's first rating
   against Layer 1's seed (annex T4.7) from the games before list t; the residual
   S − E over each newcomer's first 30 broadcast games from month t, the seed held;
 - rung 4, K from certainty (R6): each player's rating carried through month t's
   broadcast games with FIDE's K and with K_i, then month t + 1's broadcast games
   forecast from the carried ratings; the K distribution, including elite K;
 - rung 5, junior compensation (R5, R8): games of eligible juniors against players
   who are not eligible (R8); the opponent's expectation with R_j and with
   RX_j = R_j + c_j; the pre-registered metric is the adults' residual (opponents
   aged 20 or more, or without a year of birth, annex T2.2); points drained from
   the opponents (Σ K (S − E)); forecast error;
 - rung 6, monthly adjustment (R3): the controller of annex T4.5 replayed on the
   rolling d_t (panel members with a Layer 1 estimate), accrual scaled by activity,
   against the drift D_t of the whole fixed panel, paired over twelve months;
 - and, from the committed E2 aggregates, the pooled farming-region test of R12.
Forecasts of Layer 0's expected score use table 8.1.2 with FIDE's 400-point rule;
three-outcome scores split it with the draw rate of the game's level band in the
12 months before (as E2). Intervals: paired moving-block bootstrap by month, blocks
of 3, 2,000 resamples, seed 20261009 (annex T8.5). Only aggregates leave the script.
For development only, E6_CACHE=<file> keeps the rolling fits' per-month results in a
local pickle and reuses them; check (a) runs without it.

Usage: python3 analysis/e6_rungs_extract.py > analysis/aggregates/E6_rungs.json
"""
from __future__ import annotations

import json
import math
import os
import pickle
import random
import statistics
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
sys.path.insert(0, str(ROOT / "src"))
import l1_common as c  # noqa: E402
import layer0  # noqa: E402
from layer1 import fit, model, outputs  # noqa: E402

TEST = [fit.month_index(2025, 1) + k for k in range(21)]          # 2025-01 .. 2026-09
FIRST = fit.month_index(2023, 1)
WINDOW = 36
SEED = 20261009
BLOCK = 3
RESAMPLES = 2000
NEWCOMER_GAMES = 30
_E0: dict = {}


def e0(own: int, opp: int, tc: int, list_month: str) -> float:
    """Layer 0: FIDE's expected score for `own` against `opp` (table 8.1.2, the 400-point rule, the 2650 exemption)."""
    start = date(int(list_month[:4]), int(list_month[5:7]), 1)
    key = (own - opp, own >= 2650, tc, start >= layer0.rules.AMENDMENT_2650)
    if key not in _E0:
        _E0[key] = float(layer0.expected_score(layer0.effective_difference(own, opp, c.TCS[tc], start)))
    return _E0[key]


def three_way(e: float, draw: float) -> tuple[float, float, float]:
    e = min(max(e, 0.002), 0.998)
    d = min(draw, 2 * e - 0.002, 2 * (1 - e) - 0.002)
    return e - d / 2, d, 1 - e - d / 2


def ll(p: tuple, s: float) -> float:
    return -math.log(p[0] if s == 1.0 else p[1] if s == 0.5 else p[2])


def boot(per_month: dict[int, list[float]], bound: float | None = None) -> dict:
    """Mean of a per-game quantity with a paired moving-block bootstrap by month (blocks of 3). With a bound b, also the
    one-sided bootstrap p-value of "outside ±b" against the nearer bound (annex T8.2's residual rule): the share of
    resamples on the other side of that bound, 1 when the mean lies inside."""
    months = sorted(m for m in per_month if per_month[m])
    if not months:
        return {"n": 0}
    tot = sum(sum(v) for v in per_month.values())
    n = sum(len(v) for v in per_month.values())
    rnd = random.Random(SEED)
    k = len(months)
    nb = math.ceil(k / BLOCK)
    stats = []
    for _ in range(RESAMPLES):
        s = cnt = 0.0
        for _b in range(nb):
            start = rnd.randrange(max(1, k - BLOCK + 1))
            for m in months[start:start + BLOCK]:
                s += sum(per_month[m])
                cnt += len(per_month[m])
        stats.append(s / cnt if cnt else 0.0)
    stats.sort()
    out = {"n": n, "months": k, "mean": round(tot / n, 5), "lo": round(stats[int(0.025 * RESAMPLES)], 5),
           "hi": round(stats[int(0.975 * RESAMPLES) - 1], 5)}
    if bound is not None:
        mean = tot / n
        if mean > bound:
            out["p_outside"] = round(sum(1 for s in stats if s <= bound) / RESAMPLES, 4)
        elif mean < -bound:
            out["p_outside"] = round(sum(1 for s in stats if s >= -bound) / RESAMPLES, 4)
        else:
            out["p_outside"] = 1.0
    return out


def boot_groups(per_group: dict[str, dict[int, list[float]]], bound: float | None = None) -> dict:
    """boot() for each group (rating band), in the groups' sorted order."""
    return {k: boot(v, bound) for k, v in sorted(per_group.items())}


def calib_mae(rows: list[tuple[int, float, float, float]]) -> dict:
    """Do-no-harm calibration (annex T8.2): rows (published gap, favourite's score, E under Layer 0, E under the rung),
    from the side of the player rated higher on the published list; 50-point bins of the gap; the game-weighted mean
    absolute residual of the bins under each, and the difference (rung minus Layer 0)."""
    bins: dict[int, list[float]] = {}
    for x, s, ea, eb in rows:
        b = bins.setdefault(min(abs(x) // 50, 20), [0, 0.0, 0.0])
        b[0] += 1
        b[1] += s - ea
        b[2] += s - eb
    n = sum(b[0] for b in bins.values())
    if not n:
        return {"n": 0}
    ma = sum(abs(b[1]) for b in bins.values()) / n
    mb = sum(abs(b[2]) for b in bins.values()) / n
    return {"n": n, "bins": len(bins), "layer0": round(ma, 5), "rung": round(mb, 5), "difference": round(mb - ma, 5)}


def fav(own: int, opp: int, s: float, e_a: float, e_b: float) -> tuple[int, float, float, float]:
    """A game from the side of the player rated higher on the published list (ties: as given)."""
    return (own - opp, s, e_a, e_b) if own >= opp else (opp - own, 1.0 - s, 1.0 - e_a, 1.0 - e_b)


def main() -> int:
    S = c.load()
    hist = json.loads((ROOT / "analysis" / "aggregates" / "L1_history.json").read_text(encoding="utf-8"))
    ch = hist["fit"]["chosen"]
    hyper = fit.Hyper(c_theta=ch["c_theta"], omega=ch["omega"], max_sweeps=150)
    tp, kappa = S.tp, S.kappa
    by_month: dict[int, list] = defaultdict(list)
    for g in S.games:
        by_month[g.month].append(g)

    def draw_rates(t: int) -> dict:
        tot, dr = Counter(), Counter()
        for m in range(t - 12, t):
            for g in by_month.get(m, []):
                tot[(g.tc, g.level_mid)] += 1
                dr[(g.tc, g.level_mid)] += g.score == 0.5
        return {k: dr[k] / tot[k] for k in tot}

    # per player and time control: months, opponents and tours (for gates)
    played: dict[tuple[int, int], list] = defaultdict(list)
    for g in S.games:
        played[(g.white, g.tc)].append((g.month, g.black, g.tour, g.black_rated))
        played[(g.black, g.tc)].append((g.month, g.white, g.tour, g.white_rated))

    origin: dict[int, dict] = {}
    fitrec = []
    cache = os.environ.get("E6_CACHE")          # development only: check (a) runs without it
    if cache and Path(cache).exists():
        with open(cache, "rb") as fh:
            origin, fitrec = pickle.load(fh)
    prev = None
    for t in ([] if origin else TEST):
        lo = fit.month_label(max(FIRST, t - WINDOW))
        hi = fit.month_label(t - 1)
        f = c.fit_window(S, lo, hi, hyper, warm=prev)
        lab = fit.month_label(t)
        lo_i = max(FIRST, t - WINDOW)
        # anchor at t
        anc, in_fit = {}, {}
        for tc in range(3):
            pres = [(p, f.index[p], S.lists.rating(c.TCS[tc], lab, str(p))) for p in S.panels[tc] if p in f.index]
            pres = [(p, i, r) for p, i, r in pres if r]
            mt = sum(r for _, _, r in pres) / len(pres)
            mh = sum(fit.strength(f, i, tc, t) for _, i, _ in pres) / len(pres)
            anc[tc] = (mt, mh)
            in_fit[tc] = [p for p, _, _ in pres]
        rec: dict = {"anchor": {tc: {"m_t": mt, "m_hat": mh, "d_t": mh - mt, "in_fit": in_fit[tc]} for tc, (mt, mh) in anc.items()}}
        players = {}
        need = {(g.white, g.tc) for g in by_month[t]} | {(g.black, g.tc) for g in by_month[t]}
        first_rated = set()
        for tc in range(3):                                   # newcomers first rated on list t
            prev_lab = fit.month_label(t - 1)
            for (p, t2) in list(played):
                if t2 == tc and S.lists.rating(c.TCS[tc], lab, str(p)) and not S.lists.rating(c.TCS[tc], prev_lab, str(p)):
                    first_rated.add((p, tc))
        for (p, tc) in sorted(need | first_rated):
            i = f.index.get(p)
            if i is None:
                players[(p, tc)] = None
                continue
            mt, mh = anc[tc]
            s_hat = fit.strength(f, i, tc, t)
            sg = fit.sigma_tc(fit.covariance_at(f, i, t), tc)
            th = outputs.theta_tilde(s_hat, mt, mh, kappa[tc])
            sgp = sg / kappa[tc]
            r = S.lists.rating(c.TCS[tc], lab, str(p))
            lvl = r if r else int(th)
            nu0 = math.exp(tp[tc]["alpha"] + tp[tc]["beta"] * model.ell_of(model.band_mid(lvl)))
            k6 = outputs.k_printed(sg, kappa[tc], model.score_variance_at_zero(nu0))
            hist_tc = [x for x in played[(p, tc)] if lo_i <= x[0] <= t - 1]
            by = S.birth.get(p)
            age = (t // 12) - by if by else None
            row = {"theta_tilde": th, "sigma_pub": sgp, "k6": k6, "age": age, "games": len(hist_tc)}
            if age is not None and age <= 19 and r:
                others = tuple(o for o in range(3) if o != tc)
                only = not any(lo_i <= x[0] <= t - 1 for o in others for x in played.get((p, o), []))
                if only:
                    share = 1.0
                else:
                    c_tc = fit.covariance_at(f, i, t, fit.last_cov_variant(f, i, drop_tc=others))
                    c_0 = fit.covariance_at(f, i, t, fit.last_cov_variant(f, i, with_games=False))
                    share = outputs.info_share(1 / sg ** 2, 1 / fit.sigma_tc(c_tc, tc) ** 2, 1 / fit.sigma_tc(c_0, tc) ** 2)
                opp = {x[1] for x in hist_tc}
                tours = {x[2] for x in hist_tc}
                elig = outputs.junior_eligible(age, len(hist_tc), len(opp), len(tours), share)
                row.update({"share": share, "eligible": elig, "c_j": outputs.compensation(th, sgp, r, elig),
                            "gates": outputs.junior_eligible(age, len(hist_tc), len(opp), len(tours), 1.0)})
            if (p, tc) in first_rated:
                w26 = [x for x in played[(p, tc)] if t - 26 <= x[0] <= t - 1]
                rated_g = sum(1 for x in w26 if x[3])
                row["seed"] = outputs.seed(th, sgp, rated_g, len({x[1] for x in w26}), len({x[2] for x in w26}))
                row["first_rating"] = r
            players[(p, tc)] = row
        # activity for R3: games on the 12 lists up to t
        act = {}
        for tc in range(3):
            g12 = {p: sum(S.lists.games(c.TCS[tc], fit.month_label(t - k), str(p)) for k in range(12)) for p in S.panels[tc]}
            act[tc] = g12
        rec["players"] = players
        rec["activity"] = act
        origin[t] = rec
        fitrec.append({"month": lab, "window": [lo, hi], "players": len(f.players), "games": f.games_used, "sweeps": f.sweeps,
                       "max_move": round(f.max_move, 4), "anchor_shift": round(f.shifts[-1], 3)})
        print(f"origin {lab}: window {lo}..{hi}, {f.games_used} games, {f.sweeps} sweeps", file=sys.stderr, flush=True)
        prev = f
    if cache and not Path(cache).exists():
        with open(cache, "wb") as fh:
            pickle.dump((origin, fitrec), fh)

    out: dict = {"test_months": [fit.month_label(t) for t in TEST], "fits": fitrec,
                 "hyperparameters": {"c_theta": hyper.c_theta, "omega": hyper.omega}}

    # ---------------------------------------------------------------- rung 3: newcomer seeds
    seeds = []
    for t in TEST:
        for (p, tc), row in origin[t]["players"].items():
            if row is None or "first_rating" not in row or row["first_rating"] is None:
                continue
            seeds.append((t, p, tc, row["first_rating"], row["seed"], row["sigma_pub"]))
    r3 = {"newcomers_first_rated_with_games_before": len(seeds),
          "seeded_by_rung3": sum(1 for s in seeds if s[4] is not None)}
    res0, res3, br0, br3, ll3 = (defaultdict(list) for _ in range(5))
    band0, band3 = defaultdict(lambda: defaultdict(list)), defaultdict(lambda: defaultdict(list))
    cal3 = []
    for t, p, tc, r_fide, r_l1, _sgp in seeds:
        if r_l1 is None:
            continue
        gl = []
        for g in sorted((g for m in range(t, TEST[-1] + 1) for g in by_month.get(m, []) if g.tc == tc and p in (g.white, g.black)),
                        key=lambda g: (g.day, g.tour)):
            gl.append(g)
            if len(gl) == NEWCOMER_GAMES:
                break
        for g in gl:
            white = g.white == p
            opp_r = g.black_r if white else g.white_r
            if not opp_r:
                continue
            s = g.score if white else 1.0 - g.score
            e_f, e_l = e0(r_fide, opp_r, tc, g.list_month), e0(r_l1, opp_r, tc, g.list_month)
            res0[g.month].append(s - e_f)
            res3[g.month].append(s - e_l)
            br0[g.month].append((s - e_f) ** 2)
            br3[g.month].append((s - e_l) ** 2)
            dl = draw_rates(g.month).get((g.tc, g.level_mid), 0.3)
            ll3[g.month].append(ll(three_way(e_l, dl), s) - ll(three_way(e_f, dl), s))
            b = "<1600" if r_fide < 1600 else "1600-1999" if r_fide < 2000 else "2000+"
            band0[b][g.month].append(s - e_f)
            band3[b][g.month].append(s - e_l)
            cal3.append(fav(r_fide, opp_r, s, e_f, e_l))
    diff_br = {m: [b - a for a, b in zip(br0[m], br3[m])] for m in br0}
    r3.update({"games": sum(len(v) for v in res0.values()), "residual_layer0": boot(res0, 0.02), "residual_rung3": boot(res3, 0.02),
               "brier_difference": boot(diff_br), "log_loss_difference": boot(ll3), "calibration": calib_mae(cal3),
               "seed_difference": statistics.fmean(s[4] - s[3] for s in seeds if s[4] is not None) if r3["seeded_by_rung3"] else None,
               "seed_difference_median": statistics.median(s[4] - s[3] for s in seeds if s[4] is not None) if r3["seeded_by_rung3"] else None,
               "by_band_layer0": boot_groups(band0, 0.02), "by_band_rung3": boot_groups(band3, 0.02)})
    out["rung3"] = r3

    # ---------------------------------------------------------------- rung 4: K from certainty
    d4_ll, d4_br, d4_ll_top, d4_br_top = defaultdict(list), defaultdict(list), defaultdict(list), defaultdict(list)
    kcross = Counter()
    k_elite, k_by_band, k_by_fide = [], defaultdict(list), defaultdict(list)
    stab = {"layer0": [], "rung4": []}
    cal4 = []
    for t in TEST[:-1]:
        upd = {}
        for g in by_month[t]:
            for p, own, opp, kk, s in ((g.white, g.white_r, g.black_r, g.white_k, g.score),
                                       (g.black, g.black_r, g.white_r, g.black_k, 1.0 - g.score)):
                row = origin[t]["players"].get((p, g.tc))
                if not own or not opp or not kk or row is None:
                    continue
                u = upd.setdefault((p, g.tc), {"base": own, "k0": kk, "k6": row["k6"], "sum": 0.0, "n": 0})
                u["base"] = own
                u["sum"] += s - e0(own, opp, g.tc, g.list_month)
                u["n"] += 1
        diffs = sorted(abs(u["k6"] - u["k0"]) for u in upd.values())
        top_cut = diffs[int(0.75 * len(diffs))] if diffs else 0.0
        for (p, tc), u in upd.items():
            kcross[(u["k0"], "<15" if u["k6"] < 15 else "15-25" if u["k6"] < 25 else "25+")] += 1
            b = "<1600" if u["base"] < 1600 else "1600-1999" if u["base"] < 2000 else "2000-2399" if u["base"] < 2400 else "2400-2599" if u["base"] < 2600 else "2600+"
            k_by_band[(c.TCS[tc], b)].append(u["k6"])
            k_by_fide[(c.TCS[tc], u["k0"])].append(u["k6"])
            age = origin[t]["players"][(p, tc)]["age"]
            if tc == 0 and u["base"] >= 2600 and age is not None and age >= 20:
                k_elite.append(u["k6"])
            if u["k0"] in (10, 20) and age is not None and age >= 20:
                stab["layer0"].append(abs(u["k0"] * u["sum"]))
                stab["rung4"].append(abs(u["k6"] * u["sum"]))
        dr = draw_rates(t + 1)
        for g in by_month[t + 1]:
            if not g.white_r or not g.black_r:
                continue
            uw, ub = upd.get((g.white, g.tc)), upd.get((g.black, g.tc))
            if uw is None and ub is None:
                continue
            rw0 = (uw["base"] + uw["k0"] * uw["sum"]) if uw else g.white_r
            rb0 = (ub["base"] + ub["k0"] * ub["sum"]) if ub else g.black_r
            rw6 = (uw["base"] + uw["k6"] * uw["sum"]) if uw else g.white_r
            rb6 = (ub["base"] + ub["k6"] * ub["sum"]) if ub else g.black_r
            dl = dr.get((g.tc, g.level_mid), 0.3)
            ea = e0(round(rw0), round(rb0), g.tc, g.list_month)
            eb = e0(round(rw6), round(rb6), g.tc, g.list_month)
            dll = ll(three_way(eb, dl), g.score) - ll(three_way(ea, dl), g.score)
            dbr = (g.score - eb) ** 2 - (g.score - ea) ** 2
            d4_ll[g.month].append(dll)
            d4_br[g.month].append(dbr)
            cal4.append(fav(g.white_r, g.black_r, g.score, ea, eb))
            if (uw and abs(uw["k6"] - uw["k0"]) >= top_cut) or (ub and abs(ub["k6"] - ub["k0"]) >= top_cut):
                d4_ll_top[g.month].append(dll)
                d4_br_top[g.month].append(dbr)
    q = lambda v: {"n": len(v), "p10": round(sorted(v)[int(0.1 * len(v))], 1), "median": round(statistics.median(v), 1),
                   "p90": round(sorted(v)[int(0.9 * len(v)) - 1], 1), "mean": round(statistics.fmean(v), 2)} if v else {"n": 0}
    out["rung4"] = {"log_loss_difference": boot(d4_ll), "brier_difference": boot(d4_br),
                    "log_loss_difference_top_quartile": boot(d4_ll_top), "brier_difference_top_quartile": boot(d4_br_top),
                    "k_cross": {f"{k0}|{k6}": n for (k0, k6), n in sorted(kcross.items())},
                    "k_by_band": {f"{tc}|{b}": q(v) for (tc, b), v in sorted(k_by_band.items())},
                    "k_by_fide_k": {f"{tc}|{k}": q(v) for (tc, k), v in sorted(k_by_fide.items())},
                    "k_elite_2600_standard": q(k_elite), "calibration": calib_mae(cal4),
                    "monthly_change_established": {k: q(v) for k, v in stab.items()}}

    # ---------------------------------------------------------------- rung 5: junior compensation
    POPS = ("adults", "eligible", "adults_compensated")
    r0, r5, k0d, k5d, lld, brd = ({pop: defaultdict(list) for pop in POPS} for _ in range(6))
    band0_5 = {pop: defaultdict(lambda: defaultdict(list)) for pop in POPS}
    band5_5 = {pop: defaultdict(lambda: defaultdict(list)) for pop in POPS}
    cal5 = {pop: [] for pop in POPS}
    cnt = Counter()
    for t in TEST:
        dr = draw_rates(t)
        for g in by_month[t]:
            if not g.white_r or not g.black_r:
                continue
            pw, pb = origin[t]["players"].get((g.white, g.tc)), origin[t]["players"].get((g.black, g.tc))
            jw, jb = bool(pw and pw.get("eligible")), bool(pb and pb.get("eligible"))
            if jw and jb:
                cnt["eligible_junior_pairs"] += 1          # R8: published ratings on both sides, as Layer 0
                cnt["eligible_junior_pairs_with_c_j"] += pw["c_j"] > 0 or pb["c_j"] > 0
                continue
            if not (jw or jb):
                continue
            if jw:   # the junior is White; the opponent Black
                opp, own, kk, s, cj, jr = g.black, g.black_r, g.black_k, 1.0 - g.score, pw["c_j"], g.white_r
            else:
                opp, own, kk, s, cj, jr = g.white, g.white_r, g.white_k, g.score, pb["c_j"], g.black_r
            if not kk:
                continue
            by = S.birth.get(opp)
            opp_age = (t // 12) - by if by else None
            adult = opp_age is None or opp_age >= 20       # annex T2.2: no year of birth counts as an adult
            pops = ["eligible"] + (["adults"] if adult else []) + (["adults_compensated"] if adult and cj > 0 else [])
            e_0 = e0(own, jr, g.tc, g.list_month)
            e_5 = e0(own, jr + cj, g.tc, g.list_month)
            dl = dr.get((g.tc, g.level_mid), 0.3)
            b = "<1600" if own < 1600 else "1600-1999" if own < 2000 else "2000-2399" if own < 2400 else "2400+"
            for pop in pops:
                cnt[f"games_{pop}"] += 1
                r0[pop][t].append(s - e_0)
                r5[pop][t].append(s - e_5)
                k0d[pop][t].append(kk * (s - e_0))
                k5d[pop][t].append(kk * (s - e_5))
                lld[pop][t].append(ll(three_way(e_5, dl), s) - ll(three_way(e_0, dl), s))
                brd[pop][t].append((s - e_5) ** 2 - (s - e_0) ** 2)
                band0_5[pop][b][t].append(s - e_0)
                band5_5[pop][b][t].append(s - e_5)
                cal5[pop].append(fav(own, jr, s, e_0, e_5))
    elig = Counter()
    for t in TEST:
        for (p, tc), row in origin[t]["players"].items():
            if row and "share" in row:
                elig["junior_rows"] += 1
                elig["pass_gates"] += row["gates"]
                elig["eligible"] += row["eligible"]
                elig["fail_share_only"] += row["gates"] and not row["eligible"]
                elig["compensated"] += row["eligible"] and row["c_j"] > 0
    out["rung5"] = {"counts": dict(cnt), "junior_month_rows": dict(elig),
                    "populations": {pop: {"opponent_residual_layer0": boot(r0[pop], 0.01), "opponent_residual_rung5": boot(r5[pop], 0.01),
                                          "points_per_game_layer0": boot(k0d[pop]), "points_per_game_rung5": boot(k5d[pop]),
                                          "points_total_layer0": round(sum(sum(v) for v in k0d[pop].values()), 1),
                                          "points_total_rung5": round(sum(sum(v) for v in k5d[pop].values()), 1),
                                          "log_loss_difference": boot(lld[pop]), "brier_difference": boot(brd[pop]),
                                          "calibration": calib_mae(cal5[pop]),
                                          "by_opponent_band_layer0": boot_groups(band0_5[pop], 0.01),
                                          "by_opponent_band_rung5": boot_groups(band5_5[pop], 0.01)} for pop in POPS}}

    # ---------------------------------------------------------------- rung 6: the monthly adjustment replayed (R3)
    r6 = {}
    for tc in range(3):
        name = c.TCS[tc]
        rows = []
        bal: dict[int, float] = defaultdict(float)
        settled: dict[int, dict[int, tuple[int, float]]] = {}
        for t in TEST:
            a = origin[t]["anchor"][tc]
            act = origin[t]["activity"][tc]
            lab = fit.month_label(t)
            members = [p for p in S.panels[tc] if S.lists.rating(name, lab, str(p))]      # the whole fixed panel on list t
            mean_games = statistics.fmean(act[p] for p in members) if members else 0.0
            in_fit = a["in_fit"]                                                          # members with a Layer 1 estimate
            d_replay = a["d_t"] - statistics.fmean(bal[p] for p in in_fit)                 # d_t on R + B of the same members
            a_t = outputs.monthly_adjustment(d_replay)
            settled[t] = {p: (S.lists.rating(name, lab, str(p)), bal[p]) for p in members}  # R_t and B_t before a_t accrues
            for p in members:
                if act[p] >= 1:                            # active: a rated game on the 12 lists up to t (§7.2.2)
                    bal[p] += a_t * outputs.accrual_factor(act[p], mean_games)
            rows.append({"month": lab, "members": len(members), "members_in_fit": len(in_fit),
                         "m_t_panel": round(statistics.fmean(settled[t][p][0] for p in members), 2),
                         "d_t_layer0": round(a["d_t"], 2), "d_t_rung6": round(d_replay, 2), "a_t": a_t,
                         "anchor_mean_games_12": round(mean_games, 2),
                         "mean_balance": round(statistics.fmean(settled[t][p][1] for p in members), 3)})
        for k in range(12, len(rows)):
            t, t0 = TEST[k], TEST[k - 12]
            both = [p for p in settled[t] if p in settled[t0]]     # paired over members on both lists
            rows[k]["D_t_members"] = len(both)
            rows[k]["D_t_layer0"] = round(statistics.fmean(settled[t][p][0] - settled[t0][p][0] for p in both), 2)
            rows[k]["D_t_rung6"] = round(statistics.fmean(settled[t][p][0] + settled[t][p][1] - settled[t0][p][0] - settled[t0][p][1]
                                                          for p in both), 2)
        r6[name] = rows
    out["rung6"] = r6

    # ---------------------------------------------------------------- R12: the farming region pooled (E2 aggregates)
    e2 = json.loads((ROOT / "analysis" / "aggregates" / "E2_broadcast.json").read_text(encoding="utf-8"))
    r12 = {}
    for tc, rr in e2["rolling"].items():
        bins = rr["farming_bins"]
        n = sum(b[0] for b in bins[8:])
        if not n:
            continue
        res = {}
        for name_, i_e, i_sq in (("rung2", 2, 4), ("layer0", 3, 5)):
            s = sum(b[1] for b in bins[8:])
            e = sum(b[i_e] for b in bins[8:])
            sq = sum(b[i_sq] for b in bins[8:])
            mean = (s - e) / n
            var = max(sq / n - mean * mean, 0.0)
            se = math.sqrt(var / n)
            res[name_] = {"residual": round(mean, 4), "se": round(se, 4), "lo": round(mean - 1.96 * se, 4), "hi": round(mean + 1.96 * se, 4)}
        r12[tc] = {"games": n, **res}
    out["r12_farming_region"] = r12
    json.dump(out, sys.stdout, indent=1, sort_keys=True, default=str)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
