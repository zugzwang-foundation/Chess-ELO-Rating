#!/usr/bin/env python3
"""E8 extraction: K from FIDE's complete activity record, rung 4 redesigned (ELO-5, Phase 1; needs data/).

Implements docs/specs/SPEC-K-ACTIVITY_v1_0.md. The certainty σ_i is built from FIDE's monthly lists alone
(src/layer2/kactivity.py: the games field of every list since February 2015, growth by age), and K follows
ruling R16 of D-0009, K_i(n) = clip(q σ² / (κ (1 + n q² σ² v)), 10, 40). The growth scale c_K is chosen per
time control on carry months 2023-01 to 2024-11 (§5), before E6's test months; rung 4 is then tested exactly
as E6 tested it (§6), with E6's harness functions imported unchanged from analysis/e6_rungs_extract.py:
carry each player's rating through month t's broadcast games with FIDE's K and with K_i(n), forecast month
t + 1 from the carried ratings with Layer 0's expected score, on carry months 2025-01 to 2026-08. Also: the
K distribution, the K of established elite players and club adults at the October 2026 list, and the
stability of established ratings. Lists are analysed and never redistributed; broadcast games are the
Lichess archive (CC BY-SA 4.0). Only aggregates leave the script. The data cutoff is enforced in
src/layer1/data.py (broadcast) and src/layer2/kactivity.py (no list after 2026-10).

Usage: python3 analysis/e8_k_activity_extract.py > analysis/aggregates/E8_k_activity.json
"""
from __future__ import annotations

import json
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
sys.path.insert(0, str(ROOT / "src"))
import e6_rungs_extract as e6  # noqa: E402  (E6's harness functions, unchanged: SPEC-K-ACTIVITY §6)
import l1_common as c  # noqa: E402
from layer1 import fit  # noqa: E402
from layer2 import kactivity as ka  # noqa: E402

CHOICE = [fit.month_index(2023, 1) + k for k in range(23)]        # carry months 2023-01 .. 2024-11 (§5)
TEST = e6.TEST                                                      # 2025-01 .. 2026-09; carry months TEST[:-1]
OCT26 = "2026-10"


def quant(v: list[float]) -> dict:
    if not v:
        return {"n": 0}
    s = sorted(v)
    return {"n": len(v), "p10": round(s[int(0.1 * len(s))], 1), "median": round(statistics.median(s), 1),
            "p90": round(s[int(0.9 * len(s)) - 1], 1), "mean": round(statistics.fmean(s), 2)}


def band5(r: int) -> str:
    return ("<1600" if r < 1600 else "1600-1999" if r < 2000 else "2000-2399" if r < 2400 else "2400-2599" if r < 2600
            else "2600+")


def main() -> int:
    S = c.load()
    tp, kappa = S.tp, S.kappa
    by_month: dict[int, list] = defaultdict(list)
    month_players: dict[int, set] = defaultdict(set)
    for g in S.games:
        by_month[g.month].append(g)
        month_players[g.month].update((g.white, g.black))

    def draw_rates(t: int) -> dict:                                 # as E6
        tot, dr = Counter(), Counter()
        for m in range(t - 12, t):
            for g in by_month.get(m, []):
                tot[(g.tc, g.level_mid)] += 1
                dr[(g.tc, g.level_mid)] += g.score == 0.5
        return {k: dr[k] / tot[k] for k in tot}

    def window(t: int) -> set:
        """E6's population: players with a Layer 1 game in months max(2023-01, t − 36) .. t − 1 (layer1.fit.build)."""
        out: set = set()
        for m in range(max(e6.FIRST, t - e6.WINDOW), t):
            out |= month_players.get(m, set())
        return out

    # ---------------------------------------------------------------- FIDE's lists since February 2015 (counts only)
    hist = {}
    for tc in range(3):
        ids = {str(p) for g in S.games if g.tc == tc for p in (g.white, g.black)}
        hist[tc] = ka.read_lists(ROOT, c.TCS[tc], ids)
    months = hist[0][0]
    pos = {m: i for i, m in enumerate(months)}
    years = [int(m[:4]) for m in months]

    def trajectories(tc: int, ck: float) -> dict[int, list]:
        _m, rating, games, birth = hist[tc]
        a, b = tp[tc]["alpha"], tp[tc]["beta"]
        return {int(p): ka.trajectory(rating[p], games[p], years, birth.get(p), ck, a, b) for p in sorted(rating)}

    def k_rung(tc: int, ck: float, traj: dict, p: int, t: int, own: int, n_bcast: int) -> tuple[float, float, int] | None:
        """K_i(n) for player p's games of carry month t (rated on list t + 1, list t in force): (K, σ², n)."""
        lab = fit.month_label(t)
        i = pos[lab]
        arr = traj.get(p)
        if arr is None:
            return None
        j = i
        while j >= 0 and arr[j] is None:
            j -= 1
        if j < 0:
            return None
        by = hist[tc][3].get(str(p))
        age = years[i] - by if by else None
        g = ka.growth(ck, age)
        sigma2 = min(arr[j] + (i - j + 1) * g * g, ka.S0 * ka.S0)
        r_t = hist[tc][1][str(p)][i] or own
        n_list = hist[tc][2][str(p)][i + 1] if i + 1 < len(months) else 0
        n = max(n_list, n_bcast)
        v = ka.score_variance(tp[tc]["alpha"], tp[tc]["beta"], r_t)
        return ka.k_printed(sigma2, n, kappa[tc], v), sigma2, n

    def harness(carry: list[int], cks: dict[int, float], restrict: bool, extras: bool = False) -> dict:
        """E6's rung-4 harness (analysis/e6_rungs_extract.py), K_i(n) of SPEC-K-ACTIVITY §4 in place of R6's."""
        trajs = {tc: trajectories(tc, cks[tc]) for tc in range(3)}
        d_ll, d_br, d_ll_top, d_br_top = defaultdict(list), defaultdict(list), defaultdict(list), defaultdict(list)
        ll_rung = {tc: [0.0, 0] for tc in range(3)}
        ll_tc = {tc: defaultdict(list) for tc in range(3)}
        cal = []
        kcross, k_by_band, k_by_fide = Counter(), defaultdict(list), defaultdict(list)
        k_elite, stab, n_used = [], {"layer0": [], "rung4": []}, []
        for t in carry:
            members = window(t) if restrict else None
            upd: dict = {}
            for g in by_month[t]:
                for p, own, opp, kk, s in ((g.white, g.white_r, g.black_r, g.white_k, g.score),
                                           (g.black, g.black_r, g.white_r, g.black_k, 1.0 - g.score)):
                    if not own or not opp or not kk or (members is not None and p not in members):
                        continue
                    u = upd.setdefault((p, g.tc), {"base": own, "k0": kk, "sum": 0.0, "n": 0})
                    u["base"] = own
                    u["sum"] += s - e6.e0(own, opp, g.tc, g.list_month)
                    u["n"] += 1
            for (p, tc), u in list(upd.items()):
                kr = k_rung(tc, cks[tc], trajs[tc], p, t, u["base"], u["n"])
                if kr is None:                       # not on any list of tc up to t: no certainty (never in practice)
                    del upd[(p, tc)]
                    continue
                u["k6"], u["sigma2"], u["nk"] = kr
            diffs = sorted(abs(u["k6"] - u["k0"]) for u in upd.values())
            top_cut = diffs[int(0.75 * len(diffs))] if diffs else 0.0
            if extras:
                for (p, tc), u in upd.items():
                    kcross[(u["k0"], "<15" if u["k6"] < 15 else "15-25" if u["k6"] < 25 else "25+")] += 1
                    k_by_band[(c.TCS[tc], band5(u["base"]))].append(u["k6"])
                    k_by_fide[(c.TCS[tc], u["k0"])].append(u["k6"])
                    n_used.append(u["nk"])
                    by = S.birth.get(p)
                    age = (t // 12) - by if by else None
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
                ea = e6.e0(round(rw0), round(rb0), g.tc, g.list_month)
                eb = e6.e0(round(rw6), round(rb6), g.tc, g.list_month)
                l_b = e6.ll(e6.three_way(eb, dl), g.score)
                dll = l_b - e6.ll(e6.three_way(ea, dl), g.score)
                dbr = (g.score - eb) ** 2 - (g.score - ea) ** 2
                d_ll[g.month].append(dll)
                d_br[g.month].append(dbr)
                ll_rung[g.tc][0] += l_b
                ll_rung[g.tc][1] += 1
                ll_tc[g.tc][g.month].append(dll)
                cal.append(e6.fav(g.white_r, g.black_r, g.score, ea, eb))
                if (uw and abs(uw["k6"] - uw["k0"]) >= top_cut) or (ub and abs(ub["k6"] - ub["k0"]) >= top_cut):
                    d_ll_top[g.month].append(dll)
                    d_br_top[g.month].append(dbr)
        out = {"mean_log_loss_rung": {c.TCS[tc]: round(v[0] / v[1], 6) if v[1] else None for tc, v in ll_rung.items()},
               "forecast_games": {c.TCS[tc]: v[1] for tc, v in ll_rung.items()}}
        if extras:
            out.update({"log_loss_difference": e6.boot(d_ll), "brier_difference": e6.boot(d_br),
                        "log_loss_difference_top_quartile": e6.boot(d_ll_top),
                        "brier_difference_top_quartile": e6.boot(d_br_top),
                        "log_loss_difference_by_tc": {c.TCS[tc]: e6.boot(ll_tc[tc]) for tc in range(3)},
                        "calibration": e6.calib_mae(cal),
                        "k_cross": {f"{k0}|{k6}": n for (k0, k6), n in sorted(kcross.items())},
                        "k_by_band": {f"{tc}|{b}": quant(v) for (tc, b), v in sorted(k_by_band.items())},
                        "k_by_fide_k": {f"{tc}|{k}": quant(v) for (tc, k), v in sorted(k_by_fide.items())},
                        "k_elite_2600_standard": quant(k_elite),
                        "monthly_change_established": {k: quant(v) for k, v in stab.items()},
                        "n_used": quant([float(x) for x in n_used])})
        return out

    # ---------------------------------------------------------------- §5: c_K chosen on 2023-01 .. 2024-11
    grid = {}
    for ck in ka.GRID:
        r = harness(CHOICE, {0: ck, 1: ck, 2: ck}, restrict=True)
        grid[str(ck)] = r
        print(f"c_K {ck}: {r['mean_log_loss_rung']}", file=sys.stderr, flush=True)
    chosen = {}
    for tc in range(3):
        name = c.TCS[tc]
        best = min(ka.GRID, key=lambda ck: (grid[str(ck)]["mean_log_loss_rung"][name], ck))
        chosen[tc] = best
    out: dict = {"spec": "docs/specs/SPEC-K-ACTIVITY_v1_0.md",
                 "choice_months": [fit.month_label(t) for t in CHOICE],
                 "test_carry_months": [fit.month_label(t) for t in TEST[:-1]],
                 "grid": list(ka.GRID),
                 "choice": {ck: {"mean_log_loss": v["mean_log_loss_rung"], "forecast_games": v["forecast_games"]}
                            for ck, v in grid.items()},
                 "chosen": {c.TCS[tc]: ck for tc, ck in chosen.items()},
                 "chosen_at_grid_edge": {c.TCS[tc]: ck in (ka.GRID[0], ka.GRID[-1]) for tc, ck in chosen.items()}}

    # ---------------------------------------------------------------- §6: the test, as E6
    out["test"] = harness(TEST[:-1], chosen, restrict=True, extras=True)
    out["test_all_rated_players"] = harness(TEST[:-1], chosen, restrict=False, extras=True)
    print("test done", file=sys.stderr, flush=True)

    # ---------------------------------------------------------------- §7: established players at the October 2026 list
    ck0 = chosen[0]
    _m, r26, _g, _b = ka.read_lists(ROOT, "standard", None, OCT26, OCT26)
    cand = {p for p, ra in r26.items() if 1600 <= ra[0] <= 1999 or ra[0] >= 2600}
    published_k = {}
    with (ROOT / "data" / "interim" / "fide" / "standard" / f"{OCT26}.tsv").open() as fh:   # the K column of 2026-10
        next(fh)
        for line in fh:
            pid, _r, _gm, k, _rest = line.split("\t", 4)
            if pid in cand and k.isdigit():
                published_k[pid] = float(k)
    months_s, rating_s, games_s, birth_s = ka.read_lists(ROOT, "standard", cand)
    i26 = months_s.index(OCT26)
    a0, b0 = tp[0]["alpha"], tp[0]["beta"]
    yrs = [int(m[:4]) for m in months_s]
    groups: dict[str, dict[str, list]] = {g: defaultdict(list) for g in ("elite", "club")}
    for pid in sorted(rating_s):
        r = rating_s[pid][i26]
        by = birth_s.get(pid)
        if not r or not by:
            continue
        age = 2026 - by
        gs = games_s[pid]
        if sum(gs) < 30 or sum(gs[i26 - 11:i26 + 1]) < 1:
            continue
        grp = "elite" if r >= 2600 and age >= 20 else "club" if 1600 <= r <= 1999 and 25 <= age <= 60 else None
        if grp is None:
            continue
        traj = ka.trajectory(rating_s[pid], gs, yrs, by, ck0, a0, b0)
        if traj[i26] is None:
            continue
        s2 = ka.period_sigma2(traj[i26], ck0, age)
        v = ka.score_variance(a0, b0, r)
        last_n = next((gs[k] for k in range(i26, -1, -1) if gs[k]), 1)
        _cc, n_eff = ka.published_form(s2, kappa[0], v)
        rec = groups[grp]
        for n in (1, 4, 9):
            rec[f"K_n{n}"].append(ka.k_printed(s2, n, kappa[0], v))
        rec["K_last_period"].append(ka.k_printed(s2, last_n, kappa[0], v))
        rec["last_period_games"].append(float(last_n))
        rec["games_12_lists"].append(float(sum(gs[i26 - 11:i26 + 1])))
        rec["sigma"].append(s2 ** 0.5)
        rec["N_certainty"].append(n_eff)
        if pid in published_k:
            rec["published_k"].append(published_k[pid])
    out["established_oct2026"] = {g: {k: quant(v) for k, v in sorted(d.items())} for g, d in groups.items()}
    out["established_definitions"] = {
        "elite": "standard, rated 2600 or more on the 2026-10 list, aged 20 or more, at least 30 rated standard games on the lists since 2015-02, at least one on the 12 lists up to 2026-10",
        "club": "standard, rated 1600-1999 on the 2026-10 list, aged 25-60, the same activity conditions"}

    # ---------------------------------------------------------------- steady states, standard, adults (25-45) and 12-15
    steady = {}
    for label, age in (("adult_25_45", 30), ("junior_12_15", 13)):
        cgrow = ka.growth(ck0, age)
        for r in (1800, 2300, 2700):
            v = ka.score_variance(a0, b0, r)
            for gm in (1, 2, 4, 8):
                pre = min(ka.steady_state(cgrow, gm, ka.Q * ka.Q * v), ka.S0 * ka.S0)
                steady[f"{label}|{r}|{gm}"] = {"sigma": round(pre ** 0.5, 1), "K": ka.k_printed(pre, gm, kappa[0], v)}
    out["steady_state_standard"] = steady
    json.dump(out, sys.stdout, indent=1, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
