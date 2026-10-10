#!/usr/bin/env python3
"""Layer 1 on history (ELO-4, Phase 3): hyperparameters, the history fit and its coverage (needs data/).

Implements docs/specs/SPEC-L1_v1_0.md: §4.6 (c_θ and ω chosen on held-out games),
the fit on every broadcast game with FIDE IDs from January 2023 to September 2026
(the ELO-4 brief), and the outputs of §5 at the list of October 2026, reduced to
aggregates: the fit record, the anchor and spread series of every month, the
distributions of K (R6), the information share and compensation (R5) and seeds,
and the coverage of §8 by rating band and age. No player-level value leaves this
script (D17: estimates of named players are for the QC only; FIDE's lists are not
redistributed). The ELO-4 data cutoff is enforced by `layer1.data` and
`layer1.fit`. Standard library only.

Usage: python3 analysis/l1_history_extract.py > analysis/aggregates/L1_history.json
"""
from __future__ import annotations

import json
import math
import multiprocessing as mp
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
sys.path.insert(0, str(ROOT / "src"))
import l1_common as c  # noqa: E402
from layer1 import fit, forecast, model, outputs  # noqa: E402

GRID_FIT = ("2023-01", "2024-09")
GRID_TEST = ("2024-10", "2024-12")
HISTORY = ("2023-01", "2026-09")
LIST = "2026-10"
BANDS = [(0, 1599, "<1600"), (1600, 1999, "1600-1999"), (2000, 2199, "2000-2199"),
         (2200, 2399, "2200-2399"), (2400, 2599, "2400-2599"), (2600, 9999, "2600+")]
AGES = [(0, 18, "<=18"), (19, 24, "19-24"), (25, 45, "25-45"), (46, 64, "46-64"), (65, 200, "65+")]
USABLE = 100.0              # SPEC-L1 §8: σ̃ at most 100 points (PROVISIONAL)
S: c.Setup | None = None


def band(r: int | None) -> str:
    if r is None:
        return "unrated"
    return next(n for lo, hi, n in BANDS if lo <= r <= hi)


def age_group(age: int | None) -> str:
    if age is None:
        return "unknown"
    return next((n for lo, hi, n in AGES if lo <= age <= hi), "unknown")


def q(vals: list[float], nd: int = 1) -> dict:
    if not vals:
        return {"n": 0}
    s = sorted(vals)
    pick = lambda p: s[min(len(s) - 1, max(0, math.ceil(p * len(s)) - 1))]
    return {"n": len(s), "min": round(s[0], nd), "p10": round(pick(0.1), nd), "p25": round(pick(0.25), nd),
            "median": round(statistics.median(s), nd), "p75": round(pick(0.75), nd), "p90": round(pick(0.9), nd),
            "max": round(s[-1], nd), "mean": round(statistics.fmean(s), nd)}


def grid_job(args: tuple) -> dict:
    c_theta, omega = args
    f = c.fit_window(S, *GRID_FIT, fit.Hyper(c_theta=c_theta, omega=omega, max_sweeps=150))
    test = [g for g in S.games if GRID_TEST[0] <= fit.month_label(g.month) <= GRID_TEST[1]]
    ll, n = forecast.log_loss(f, test, c.prior_factory(S))
    return {"c_theta": c_theta, "omega": omega, "log_loss": round(ll, 6), "games": n, "sweeps": f.sweeps,
            "max_move": round(f.max_move, 4)}


def calibration(f: fit.Fit, games: list, prior_of) -> tuple[list[dict], list[dict]]:
    """SPEC-L1 §5.5: SD of (S − E)/sqrt(Var S) on held-out games, by decile of the pair's combined σ (standard), and by the
    number of players outside the fit (their σ is the prior's, s_0). Deciles are cut on σ alone; pairs with equal σ (two
    players outside the fit) keep the games' order, so that no decile is cut on the outcome."""
    rows = []
    for g in games:
        if g.tc != 0:
            continue
        pw, pd, pl = forecast.probabilities(f, g, prior_of)
        e = pw + 0.5 * pd
        var = pw + 0.25 * pd - e * e
        sig, outside = [], 0
        for p in (g.white, g.black):
            i = f.index.get(p)
            sig.append(fit.sigma_tc(fit.covariance_at(f, i, g.month), 0) if i is not None else c.S_0)
            outside += i is None
        rows.append((math.sqrt(sig[0] ** 2 + sig[1] ** 2), (g.score - e) / math.sqrt(var), outside))
    rows.sort(key=lambda r: r[0])

    def summary(part: list) -> dict:
        z = [r[1] for r in part]
        return {"games": len(part), "sigma_pair_median": round(statistics.median(r[0] for r in part), 1),
                "z_mean": round(statistics.fmean(z), 4), "z_sd": round(statistics.pstdev(z), 4),
                "outside_fit_share": round(sum(1 for r in part if r[2]) / len(part), 4)}
    deciles = []
    for d in range(10):
        part = rows[d * len(rows) // 10:(d + 1) * len(rows) // 10]
        if part:
            deciles.append({"decile": d + 1, **summary(part)})
    by_outside = [{"players_outside_fit": k, **summary(part)} for k in (0, 1, 2) if (part := [r for r in rows if r[2] == k])]
    return deciles, by_outside


def main() -> int:
    global S
    S = c.load()
    ctx = mp.get_context("fork")
    with ctx.Pool(3) as pool:
        first = pool.map(grid_job, [(0.5, 8.0), (1.0, 8.0), (2.0, 8.0)])
    best_c = min(first, key=lambda r: (r["log_loss"], r["c_theta"]))["c_theta"]
    with ctx.Pool(2) as pool:
        second = pool.map(grid_job, [(best_c, 4.0), (best_c, 16.0)])
    grid = first + second
    best = min(grid, key=lambda r: (r["log_loss"], r["c_theta"], r["omega"]))
    hyper = fit.Hyper(c_theta=best["c_theta"], omega=best["omega"], max_sweeps=150)
    prior_of = c.prior_factory(S)

    # calibration of σ on the grid's held-out months, with the chosen hyperparameters
    fg = c.fit_window(S, *GRID_FIT, hyper)
    held = [g for g in S.games if GRID_TEST[0] <= fit.month_label(g.month) <= GRID_TEST[1]]
    calib, calib_outside = calibration(fg, held, prior_of)
    del fg

    f = c.fit_window(S, *HISTORY, hyper)
    m_list = fit.month_index(int(LIST[:4]), int(LIST[5:7]))
    tp, kappa = S.tp, S.kappa

    # per player and time control: games, opponents, tours, months
    stats: dict[tuple[int, int], dict] = defaultdict(lambda: {"games": 0, "opp": set(), "tours": set(), "rated_games": 0,
                                                               "recent": 0, "months": set()})
    first26 = fit.month_index(2024, 8)
    for g in S.games:
        if not (HISTORY[0] <= fit.month_label(g.month) <= HISTORY[1]):
            continue
        for p, o, o_rated in ((g.white, g.black, g.black_rated), (g.black, g.white, g.white_rated)):
            st = stats[(p, g.tc)]
            st["games"] += 1
            st["opp"].add(o)
            st["tours"].add(g.tour)
            st["months"].add(g.month)
            if g.month >= first26 and o_rated:
                st["rated_games"] += 1
            if g.month >= m_list - 12:
                st["recent"] += 1

    def published(tc: int, month_label: str, p: int) -> int | None:
        return S.lists.rating(c.TCS[tc], month_label, str(p))

    # anchor series and spread ratio, every month of the fit
    cov_all = {i: fit.smoothed_covariances(f, i) for i in range(len(f.players))}

    def var_at(i: int, tc: int, month: int) -> float:
        ms = f.months[i]
        k = min(range(len(ms)), key=lambda kk: (abs(ms[kk] - month), kk))
        cv = cov_all[i][k] if month <= ms[-1] else fit.covariance_at(f, i, month)
        return fit.sigma_tc(cv, tc) ** 2

    months = [fit.month_index(2023, 1) + k for k in range(45)]
    anchor, spread = {}, {}
    for tc in range(3):
        pan = [(f.index[p], p) for p in S.panels[tc] if p in f.index]
        rows, srows = [], []
        for m in months:
            lab = fit.month_label(m)
            pres = [(i, published(tc, lab, p)) for i, p in pan]
            pres = [(i, r) for i, r in pres if r]
            mt = sum(r for _, r in pres) / len(pres)
            mh = sum(fit.strength(f, i, tc, m) for i, _ in pres) / len(pres)
            d = mh - mt
            rows.append({"month": lab, "members": len(pres), "m_t": round(mt, 2), "m_hat_t": round(mh, 2), "d_t": round(d, 2),
                         "a_t": outputs.monthly_adjustment(d)})
            act = []
            for (p, t), st in stats.items():
                if t != tc or not any(m - 11 <= mm <= m for mm in st["months"]):
                    continue
                by = S.birth.get(p)
                r = published(tc, lab, p)
                if by is None or not (25 <= (m // 12) - by <= 45) or r is None:
                    continue
                i = f.index[p]
                act.append((r, fit.strength(f, i, tc, m), var_at(i, tc, m)))
            if len(act) >= 30:
                sd_r = statistics.pstdev(a[0] for a in act)
                sd_s = statistics.pstdev(a[1] for a in act)
                mv = statistics.fmean(a[2] for a in act)
                srows.append({"month": lab, "players": len(act), "sd_published": round(sd_r, 2), "sd_latent": round(sd_s, 2),
                              "ratio": round(sd_r / sd_s, 4), "ratio_noise_corrected": round(sd_r / math.sqrt(sd_s ** 2 + mv), 4)})
        anchor[c.TCS[tc]] = rows
        spread[c.TCS[tc]] = srows

    # outputs at the list of October 2026
    out_tc = {}
    for tc in range(3):
        name = c.TCS[tc]
        pan = [(f.index[p], p) for p in S.panels[tc] if p in f.index]
        pres = [(i, published(tc, LIST, p)) for i, p in pan]
        pres = [(i, r) for i, r in pres if r]
        m_t = sum(r for _, r in pres) / len(pres)
        m_hat = sum(fit.strength(f, i, tc, m_list) for i, _ in pres) / len(pres)
        pool, active12 = pool_counts(name, m_list)
        cov_cells: dict[tuple[str, str], list[int]] = defaultdict(lambda: [0, 0])
        k_by_band: dict[str, list[float]] = defaultdict(list)
        k_elite, shares, comp, seeds = [], [], [], []
        juniors = Counter()
        sig_pub = []
        n_in_fit = 0
        for (p, t), st in sorted(stats.items()):
            if t != tc:
                continue
            i = f.index[p]
            s_hat = fit.strength(f, i, tc, m_list)
            sg = fit.sigma_tc(fit.covariance_at(f, i, m_list), tc)
            th = outputs.theta_tilde(s_hat, m_t, m_hat, kappa[tc])
            sgp = sg / kappa[tc]
            sig_pub.append(sgp)
            n_in_fit += 1
            r = published(tc, LIST, p)
            by = S.birth.get(p)
            age = 2026 - by if by else None
            if r is None or active12[str(p)] >= 1:
                cell = cov_cells[(band(r), age_group(age))]
                cell[0] += 1
                cell[1] += sgp <= USABLE
            lvl = r if r is not None else int(th)
            nu0 = math.exp(tp[tc]["alpha"] + tp[tc]["beta"] * model.ell_of(model.band_mid(lvl)))
            k = outputs.k_printed(sg, kappa[tc], model.score_variance_at_zero(nu0))
            if r is not None and st["recent"] > 0:
                k_by_band[band(r)].append(k)
                if tc == 0 and r >= 2600 and age is not None and age >= 20 and st["games"] >= 10:
                    k_elite.append(k)
            if age is not None and age <= 19 and r is not None:
                only = not any((p, o) in stats for o in range(3) if o != tc)
                if only:
                    share = 1.0
                else:
                    others = tuple(o for o in range(3) if o != tc)
                    c_tc = fit.covariance_at(f, i, m_list, fit.last_cov_variant(f, i, drop_tc=others))
                    c_0 = fit.covariance_at(f, i, m_list, fit.last_cov_variant(f, i, with_games=False))
                    share = outputs.info_share(1 / sg ** 2, 1 / fit.sigma_tc(c_tc, tc) ** 2, 1 / fit.sigma_tc(c_0, tc) ** 2)
                shares.append(share)
                elig = outputs.junior_eligible(age, st["games"], len(st["opp"]), len(st["tours"]), share)
                gates = outputs.junior_eligible(age, st["games"], len(st["opp"]), len(st["tours"]), 1.0)
                juniors["juniors"] += 1
                juniors["pass_game_gates"] += gates
                juniors["eligible"] += elig
                juniors["fail_share_only"] += gates and not elig
                cj = outputs.compensation(th, sgp, r, elig)
                if elig:
                    comp.append(cj)
                    juniors["compensated"] += cj > 0
            if r is None:
                sd = outputs.seed(th, sgp, st["rated_games"], len(st["opp"]), len(st["tours"]))
                seeds.append(sd)
        coverage = []
        for b in [n for _, _, n in BANDS] + ["unrated"]:
            for a in [n for _, _, n in AGES] + ["unknown"]:
                n_fit, n_use = cov_cells.get((b, a), [0, 0])
                n_pool = pool.get((b, a), 0)
                if n_fit or n_pool:
                    coverage.append({"band": b, "age": a, "in_fit": n_fit, "usable": n_use, "pool": n_pool})
        out_tc[name] = {"anchor_at_list": {"members": len(pres), "m_t": round(m_t, 2), "m_hat_t": round(m_hat, 2),
                                           "d_t": round(m_hat - m_t, 2)},
                        "players_in_fit": n_in_fit,
                        "sigma_published": q(sig_pub), "coverage": coverage,
                        "k_by_band": {b: q(v) for b, v in sorted(k_by_band.items())}, "k_elite_2600": q(k_elite),
                        "juniors": dict(juniors), "info_share": q(shares, 3), "compensation_eligible": q([float(x) for x in comp]),
                        "seeds": {"unrated_in_fit": len(seeds), "published": sum(1 for x in seeds if x is not None),
                                  "values": q([float(x) for x in seeds if x is not None], 0)}}

    # fit record
    parent = list(range(len(f.players)))

    def find(a: int) -> int:
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a
    for i, gl in enumerate(f.glist):
        for _k, _tc, j, *_r in gl:
            ra, rb = find(i), find(j)
            if ra != rb:
                parent[max(ra, rb)] = min(ra, rb)
    comps = Counter(find(i) for i in range(len(f.players)))
    ins = defaultdict(lambda: [0.0, 0])
    for i, gl in enumerate(f.glist):
        X = f.x[i]
        for k, tc, j, jk, sign, s_w, ell in gl:
            if sign < 0:
                continue
            cc = 1 + tc
            Xj = f.x[j]
            z = model.Q * ((X[4 * k] + X[4 * k + cc]) - (Xj[4 * jk] + Xj[4 * jk + cc]) + f.eta[tc])
            pw, pd, pl = model.probs(z, math.exp(f.alpha[tc] + f.beta[tc] * ell), f.gamma[tc])
            ins[tc][0] -= math.log(pw if s_w == 1.0 else pd if s_w == 0.5 else pl)
            ins[tc][1] += 1
    cov_td, cross = {}, {}
    for tc in range(3):
        pts = [(f.x[f.index[p]][4 * (len(f.months[f.index[p]]) - 1)], f.x[f.index[p]][4 * (len(f.months[f.index[p]]) - 1) + 1 + tc])
               for (p, t) in stats if t == tc]
        mt, md = statistics.fmean(a for a, _ in pts), statistics.fmean(b for _, b in pts)
        cov_td[c.TCS[tc]] = round(statistics.fmean((a - mt) * (b - md) for a, b in pts), 2)
    for o in (1, 2):
        both = [p for (p, t), st in stats.items() if t == 0 and st["games"] >= 10 and stats.get((p, o), {"games": 0})["games"] >= 10]
        xs = [fit.strength(f, f.index[p], 0, m_list) for p in both]
        ys = [fit.strength(f, f.index[p], o, m_list) for p in both]
        cross[f"standard_{c.TCS[o]}"] = {"players": len(both), "correlation": round(statistics.correlation(xs, ys), 4) if len(both) > 2 else None}
    record = {"hyperparameters": {"c_theta": hyper.c_theta, "omega": hyper.omega, "rho": hyper.rho, "s_0": c.S_0, "s_list": c.S_LIST,
                                  "sigma_profile": list(hyper.sigma_profile), "t_ref": c.T_REF},
              "grid": grid, "chosen": best, "calibration_held_out": calib, "calibration_by_players_outside_fit": calib_outside,
              "outcome_latent": {k: [round(v, 4) for v in vals] for k, vals in c.outcome_latent(tp).items()},
              "kappa": list(kappa), "games": f.games_used, "players": len(f.players),
              "sweeps": f.sweeps, "max_move": round(f.max_move, 4), "drift_rounds": f.drift_rounds,
              "anchor_shift_final": round(f.shifts[-1], 3), "mu": [round(v, 2) for v in f.mu],
              "drift_A": [round(v, 3) for v in f.A], "drift_B": [round(v, 3) for v in f.B],
              "log_posterior": round(f.log_post, 1),
              "in_sample_log_loss": {c.TCS[t]: round(v[0] / v[1], 5) for t, v in sorted(ins.items())},
              "components": {"n": len(comps), "largest_share": round(max(comps.values()) / len(f.players), 4)},
              "cov_theta_delta": cov_td, "cross_tc_correlation": cross,
              "panels": {c.TCS[tc]: len(v) for tc, v in S.panels.items()}, "m_ref": {c.TCS[tc]: round(v, 2) for tc, v in S.m_ref.items()},
              "data": S.meta}
    out = {"spec": "docs/specs/SPEC-L1_v1_0.md", "window": HISTORY, "list": LIST, "fit": record,
           "anchor_series": anchor, "spread_series": spread, "at_list": out_tc}
    json.dump(out, sys.stdout, indent=1, sort_keys=True)
    sys.stdout.write("\n")
    return 0


def pool_counts(tc: str, m_list: int) -> tuple[Counter, Counter]:
    """The pool for coverage (SPEC-L1 §8): rated players on the list with at least one rated game on the 12 lists up to
    it, by band and age group, and every player's rated games on those 12 lists; streamed, no full list is kept."""
    games12: Counter = Counter()
    for k in range(12):
        with (ROOT / "data" / "interim" / "fide" / tc / f"{fit.month_label(m_list - k)}.tsv").open() as fh:
            next(fh)
            for line in fh:
                pid, r, g, _rest = line.split("\t", 3)
                if r.isdigit() and g.isdigit() and g != "0":
                    games12[pid] += int(g)
    pool: Counter = Counter()
    with (ROOT / "data" / "interim" / "fide" / tc / f"{fit.month_label(m_list)}.tsv").open() as fh:
        next(fh)
        for line in fh:
            pid, r, _g, _k, by, _rest = line.split("\t", 5)
            if r.isdigit() and games12[pid] >= 1:
                age = 2026 - int(by) if by.isdigit() and by != "0" else None
                pool[(band(int(r)), age_group(age))] += 1
    return pool, games12


if __name__ == "__main__":
    sys.exit(main())
