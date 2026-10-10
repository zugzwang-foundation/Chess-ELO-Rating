"""K from FIDE's complete activity record: rung 4 redesigned (docs/specs/SPEC-K-ACTIVITY_v1_0.md; R16 of D-0009).

A Glicko-style variance in latent units, built from FIDE's monthly lists alone: it shrinks with each
period's rated games (information per game q²·v_tc from the published table) and grows every month by
c = c_K·p(age), capped at the newcomer's s_0². K follows R16: K_i(n) = clip(q σ² / (κ (1 + n q² σ² v)),
K_min, K_max). Pure functions plus a reader of the converted lists that enforces the data cutoff.
Every parameter is PROVISIONAL. Standard library only.
"""
from __future__ import annotations

import math
from array import array
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

Q = math.log(10.0) / 400.0
K_MIN, K_MAX = 10.0, 40.0
S0, S_LIST = 250.0, 120.0                         # annex T2.2; SPEC-L1 §3.4
N_SEED = 5                                        # §7.1.4 [V 1]: at least 5 games for a first rating
PROFILE = (25.0, 25.0, 20.0, 14.0, 12.0, 15.0, 15.0)   # SPEC-L1 §3.7, points a month by age band
GRID = (0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 4.0, 6.0)  # SPEC-K-ACTIVITY §5, fixed before any fit
FIRST_LIST, LAST_LIST = "2015-02", "2026-10"


def age_band(age: int | None) -> int:
    """SPEC-L1 §3.3's bands: under 12, 12-15, 16-19, 20-24, 25-45, 46-60, over 60; no year of birth counts as 25-45."""
    if age is None:
        return 4
    for i, hi in enumerate((11, 15, 19, 24, 45, 60)):
        if age <= hi:
            return i
    return 6


def band_mid(level: int) -> int:
    """Midpoint of the published table's 100-point level band (annex T3.4)."""
    if level < 1500:
        return 1450
    if level >= 2800:
        return 2850
    return 1500 + 100 * ((level - 1500) // 100) + 50


_V: dict[tuple[float, float, int], float] = {}


def score_variance(alpha: float, beta: float, rating: int) -> float:
    """v_tc(L) = 1/(2(2 + ν_0(L))) in the band of the player's published rating (R6; D-0008, reading 5)."""
    mid = band_mid(rating)
    key = (alpha, beta, mid)
    v = _V.get(key)
    if v is None:
        v = _V[key] = 1.0 / (2.0 * (2.0 + math.exp(alpha + beta * (mid - 2000.0) / 400.0)))
    return v


def growth(c_k: float, age: int | None) -> float:
    """Growth of the latent SD per month, c = c_K · p(age band)."""
    return c_k * PROFILE[age_band(age)]


def newcomer_var(games: int, info: float, s0: float = S0, n_seed: int = N_SEED) -> float:
    """Variance after a first rating (or a re-entry): the prior s_0 and at least N_seed games' information."""
    return 1.0 / (1.0 / (s0 * s0) + max(n_seed, games) * info)


def steady_state(c: float, games: int, info: float) -> float:
    """P⁻ with the same games every month: c²(1 + √(1 + 4/(c² G I)))/2 (SPEC-K-ACTIVITY KA-3)."""
    j = games * info
    return c * c * (1.0 + math.sqrt(1.0 + 4.0 / (c * c * j))) / 2.0


def k_of_n(sigma2: float, n: int, kappa: float, v: float, k_min: float = K_MIN, k_max: float = K_MAX) -> float:
    """R16: K_i(n) = clip(q σ² / (κ (1 + n q² σ² v)), K_min, K_max); n = 1 is R6's K."""
    raw = Q * sigma2 / (kappa * (1.0 + n * Q * Q * sigma2 * v))
    return min(k_max, max(k_min, raw))


def k_printed(sigma2: float, n: int, kappa: float, v: float) -> float:
    """K_i(n) to one decimal, half up, as the per-game breakdown prints it."""
    return float(Decimal(repr(k_of_n(sigma2, n, kappa, v))).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))


def published_form(sigma2: float, kappa: float, v: float) -> tuple[float, float]:
    """D-0009 reading 3: (C, N) with K_i(n) = clip(C/(N + n)); C = 1/(κ q v), N = 1/(q² σ² v)."""
    return 1.0 / (kappa * Q * v), 1.0 / (Q * Q * sigma2 * v)


def trajectory(ratings, games, years, birth: int | None, c_k: float, alpha: float, beta: float,
               first_is_archive_start: bool = True, s0: float = S0, s_list: float = S_LIST) -> list:
    """Posterior variance after each list's games (None where the player is not rated), SPEC-K-ACTIVITY §3.

    ratings[t] is the published rating on list t (0 when not rated), games[t] the list's games field and
    years[t] its calendar year. Index 0 is February 2015, the first archived list, unless stated otherwise."""
    out: list = [None] * len(ratings)
    cap = s0 * s0
    p = None
    prev_r = 0
    for t in range(len(ratings)):
        r = ratings[t]
        if not r:
            p, prev_r = None, 0
            continue
        if p is None:                                           # first appearance or re-entry
            if t == 0 and first_is_archive_start:
                p = s_list * s_list
            else:
                p = newcomer_var(games[t], Q * Q * score_variance(alpha, beta, r), s0)
        else:
            c = growth(c_k, years[t] - birth if birth else None)
            pre = p + c * c
            if pre > cap:
                pre = cap
            g = games[t]
            p = 1.0 / (1.0 / pre + g * Q * Q * score_variance(alpha, beta, prev_r)) if g else pre
        out[t] = p
        prev_r = r
    return out


def period_sigma2(p_post: float, c_k: float, age: int | None, s0: float = S0) -> float:
    """σ_i² for the games of the period rated on the next list: min(P(t) + c², s_0²) (SPEC-K-ACTIVITY §3)."""
    c = growth(c_k, age)
    return min(p_post + c * c, s0 * s0)


def month_labels(first: str, last: str) -> list[str]:
    y, m = int(first[:4]), int(first[5:7])
    out = []
    while f"{y:04d}-{m:02d}" <= last:
        out.append(f"{y:04d}-{m:02d}")
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out


def read_lists(root: Path, tc: str, ids: set[str] | None, first: str = FIRST_LIST, last: str = LAST_LIST):
    """FIDE's converted lists of one time control (data/interim/fide/<tc>/YYYY-MM.tsv), first..last: per player in ids
    (every player when ids is None) an array of ratings (0 when not rated) and of games fields, one entry per list,
    and the latest non-zero year of birth. Refuses a list later than the data cutoff's (2026-10). No federation."""
    if last > LAST_LIST:
        raise ValueError(f"refusing lists later than {LAST_LIST} (data cutoff): {last}")
    months = month_labels(first, last)
    n = len(months)
    rating: dict[str, array] = {}
    games: dict[str, array] = {}
    birth: dict[str, int] = {}
    folder = Path(root) / "data" / "interim" / "fide" / tc
    for t, mm in enumerate(months):
        f = folder / f"{mm}.tsv"
        with f.open() as fh:
            next(fh)
            for line in fh:
                pid, r, g, _k, by, _rest = line.split("\t", 5)
                if not r.isdigit() or (ids is not None and pid not in ids):
                    continue
                ra = rating.get(pid)
                if ra is None:
                    ra = rating[pid] = array("H", bytes(2 * n))
                    games[pid] = array("H", bytes(2 * n))
                ra[t] = int(r)
                if g.isdigit():
                    games[pid][t] = min(int(g), 65535)
                if by.isdigit() and by != "0":
                    birth[pid] = int(by)
    return months, rating, games, birth
