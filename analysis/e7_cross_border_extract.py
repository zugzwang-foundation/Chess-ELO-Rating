#!/usr/bin/env python3
"""E7 extraction: the direction of Ghita's federation residuals on broadcast games (ELO-4, Phase 5.3; needs data/).

Follows the method as Ghita's book describes it (The Rating Revolution, 2026 [R 5]:
the cross-border performance index, p. 24; its weighted, recursive form, pp. 25,
51, 67) and as his blog of 17 February 2026 details it (per-game weight E(1 − E)
with the odds capped at 90/10; recursion to a change below 0.1 point): on
broadcast standard games between two players rated on the list in force whose
federations on that list differ (the E2 sample), each federation's offset is
estimated jointly from its cross-border games. Expectations use the logistic
curve with the 400 scale and, as the book's Part V does, with 459 (p. 49).

Per-federation magnitudes are not printed by name (annex T8.4: federation
estimates are for the QC only while rung 7 is disabled). The script prints the
direction test against the federations the book names with a direction (its
tables of cross-border residuals and of qualifying federations, pp. 26 and 53;
only the direction is used here, none of the book's figures), the distribution
of the offsets without names, and the sample. Aggregates only.

Usage: python3 analysis/e7_cross_border_extract.py > analysis/aggregates/E7_cross_border.json
"""
from __future__ import annotations

import json
import math
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
sys.path.insert(0, str(ROOT / "src"))
import fide_panel as fp  # noqa: E402
import e5_deflation_extract as e5  # noqa: E402

# Directions only, from the book: under-rated (+) in the tables of pp. 26 and 53; over-rated (−) in the table of p. 26.
GHITA_PLUS = ("VIE", "CHN", "UZB", "TUR", "RUS", "KAZ", "BLR", "IND", "SRI", "MAS", "AZE", "KGZ", "SGP", "IRI", "PER", "ECU")
GHITA_MINUS = ("SUI", "AUT", "CRO", "NED", "GER", "ESP")
MIN_GAMES = 300              # our threshold for an estimate; the book's is 1,000 cross-border games (p. 24)
CAP = 0.9                    # odds cap of the weight E(1 − E): E within [0.1, 0.9]
TOL = 0.1
MAX_IT = 500


def expected(d: float, scale: float) -> float:
    return 1.0 / (1.0 + 10.0 ** (-d / scale))


def recursive_offsets(games: list[tuple], scale: float, feds: set[str]) -> tuple[dict[str, float], dict[str, float], int]:
    """Joint federation offsets (points), the fixed point of o_f = o_f + Σ w (S − E) / Σ w E′ over f's cross-border
    games, with w = E(1 − E) and E capped to [0.1, 0.9] for the weight; federations are updated one at a time in a fixed
    order (Gauss–Seidel; the simultaneous update cycles on this sample), games against federations outside `feds` count
    against an offset of 0, which fixes the level during the passes, and the converged offsets are centred on the
    game-weighted mean for reporting. Returns the offsets,
    the unweighted base index (S − E)/N × 100 per federation and the passes used (negative if not converged)."""
    off = {f: 0.0 for f in feds}
    k = math.log(10.0) / scale
    mine: dict[str, list] = defaultdict(list)
    for rw, rb, fw, fb, s in games:
        if fw in off:
            mine[fw].append((rw, rb, fb, s))
        if fb in off:
            mine[fb].append((rb, rw, fw, 1.0 - s))
    weight = {f: len(v) for f, v in mine.items()}
    it, last = 0, 0.0
    for it in range(1, MAX_IT + 1):
        last = 0.0
        for f in sorted(off):
            num = den = 0.0
            of = off[f]
            for r_own, r_opp, g, s in mine[f]:
                e = expected(r_own + of - r_opp - off.get(g, 0.0), scale)
                ec = min(CAP, max(1 - CAP, e))
                w = ec * (1 - ec)
                num += w * (s - e)
                den += w * k * e * (1 - e)
            step = num / den if den > 0 else 0.0
            off[f] += step
            last = max(last, abs(step))
        if last < TOL:
            break
    mean = sum(off[f] * weight[f] for f in sorted(off)) / sum(weight[f] for f in sorted(off))
    for f in off:
        off[f] -= mean
    base = {}
    for f, lst in mine.items():
        base[f] = 100.0 * sum(s - expected(r_own - r_opp, scale) for r_own, r_opp, _g, s in lst) / len(lst)
    return off, base, it if last < TOL else -it


PROFILE_BANDS = ((0, 1599, "<1600"), (1600, 1999, "1600-1999"), (2000, 2199, "2000-2199"), (2200, 2399, "2200-2399"),
                 (2400, 9999, "2400+"))


def band_of(r: int) -> str:
    return next(n for lo, hi, n in PROFILE_BANDS if lo <= r <= hi)


def profile(ratings: list[int]) -> dict:
    """Share of player-games (or players) by rating band, and the median rating: the sample's bias (aggregates only)."""
    c = Counter(band_of(r) for r in ratings)
    return {"n": len(ratings), "median": statistics.median(ratings),
            "share": {n: round(c[n] / len(ratings), 4) for _, _, n in PROFILE_BANDS}}


def direction_test(off: dict[str, float]) -> dict:
    rows = []
    for f, sign in [(x, 1) for x in GHITA_PLUS] + [(x, -1) for x in GHITA_MINUS]:
        if f in off:
            rows.append((f, sign, off[f]))
    agree = [f for f, s, v in rows if (v > 0) == (s > 0)]
    disagree = [f for f, s, v in rows if (v > 0) != (s > 0)]
    n, k = len(rows), len(agree)
    p_one_sided = sum(math.comb(n, j) for j in range(k, n + 1)) / 2 ** n if n else None
    return {"named_and_estimable": n, "agree": k, "agree_feds": sorted(agree), "disagree_feds": sorted(disagree),
            "binomial_p_one_sided": round(p_one_sided, 5) if p_one_sided is not None else None,
            "not_estimable": sorted(f for f in GHITA_PLUS + GHITA_MINUS if f not in off)}


def main() -> int:
    meta, bgames = e5.broadcast_games()
    pan = fp.load_panel("standard")
    batch = {pan.ids[i] for i in fp.batch_r11(pan)}
    rows = []                                   # (year, rw, rb, fw, fb, s)
    skipped = Counter()
    for d, lst, s0, tour, w, b, s in bgames["standard"]:
        if w in batch or b in batch:
            skipped["r11_batch"] += 1
            continue
        t = pan.pos.get(lst)
        iw, ib = pan.index.get(w), pan.index.get(b)
        if t is None or iw is None or ib is None or not pan.rating[t][iw] or not pan.rating[t][ib]:
            skipped["not_rated_on_list_in_force"] += 1
            continue
        fw, fb = pan.feds[pan.fed[t][iw]], pan.feds[pan.fed[t][ib]]
        if not fw or not fb:
            skipped["no_federation"] += 1
            continue
        rows.append((d.year, pan.rating[t][iw], pan.rating[t][ib], fw, fb, s))
    out = {"sample": {"standard_games": len(rows), "skipped": dict(skipped), "broadcast": meta,
                      "cross_border_by_year": dict(sorted(Counter(r[0] for r in rows if r[3] != r[4]).items())),
                      "domestic_by_year": dict(sorted(Counter(r[0] for r in rows if r[3] == r[4]).items()))}}
    for label, years in (("2025", {2025}), ("2023-2024 and 2026", {2023, 2024, 2026}), ("2023-2026", {2023, 2024, 2025, 2026})):
        cross = [(rw, rb, fw, fb, s) for y, rw, rb, fw, fb, s in rows if y in years and fw != fb]
        per_fed = Counter()
        for rw, rb, fw, fb, s in cross:
            per_fed[fw] += 1
            per_fed[fb] += 1
        feds = {f for f, n in per_fed.items() if n >= MIN_GAMES}
        res = {"cross_border_games": len(cross), "federations_with_min_games": len(feds),
               "player_games_profile": profile([r for rw, rb, _fw, _fb, _s in cross for r in (rw, rb)]),
               "federations_with_1000": sum(1 for f, n in per_fed.items() if n >= 1000),
               "share_of_games_in_estimated_feds": round(sum(1 for g in cross if g[2] in feds or g[3] in feds) / len(cross), 4)}
        for scale in (400.0, 459.0):
            off, base, it = recursive_offsets(cross, scale, feds)
            vals = sorted(off.values())
            res[f"scale_{int(scale)}"] = {
                "iterations": it, "converged": it > 0, "direction_test": direction_test(off),
                "offsets_distribution": {"n": len(vals), "min": round(vals[0], 1), "p10": round(vals[len(vals) // 10], 1),
                                         "median": round(statistics.median(vals), 1), "p90": round(vals[-len(vals) // 10 - 1], 1),
                                         "max": round(vals[-1], 1), "sd": round(statistics.pstdev(vals), 1)},
                "base_index_vs_recursive_sign_agreement": round(sum(1 for f in off if (off[f] > 0) == (base[f] > 0)) / len(off), 4),
                "games_named_feds": {f: per_fed[f] for f in GHITA_PLUS + GHITA_MINUS if f in per_fed}}
        out[label] = res
    # the pool for comparison: players rated on the December 2025 list with a rated game on the twelve lists of 2025
    t25 = pan.pos["2025-12"]
    g12 = pan.window_games(t25, 12)
    out["pool_2025_profile"] = profile([pan.rating[t25][i] for i in range(pan.n)
                                        if pan.rating[t25][i] and g12[i] > 0 and pan.ids[i] not in batch])
    json.dump(out, sys.stdout, indent=1, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
