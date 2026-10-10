"""The narrowed farming guard for rung 2 v2 (D-0011: R24's rule (ii) and the executor's reading 6).

Region, tested once per game on the published ratings: the game's level (R_W + R_B)/2 at least 2300 and the
published gap |R_W - R_B| at least 400; the favourite is the player with the higher published rating. Weight
w = w_g * w_L, w_g = min(1, (gap - 400)/50), w_L = min(1, (level - 2300)/50): zero at the region's edges, one from a
gap of 450 and a level of 2350. The favourite's expectation is E_v2 + w * max(0, T - E_v2), T being table 8.1.2's H
entry without the 400-point cap [V 1] read at the favourite's own effective gap x (the colour term included, and c_j
when its opponent is a compensated junior), applied only while x <= 735, the last row of table 8.1.2 below 1.0. The
underdog's is E_v2 - w * max(0, E_v2 - (1 - T)) at its own effective gap, so that without compensation the two sum to
one and the guard creates no points. Works on floats (evaluation, unrounded) and on Decimals (the published entry:
the blended value rounded half up to three decimals). Whether the guard applies in a time control is Phase 2's
outcome, read from the guard parameter file. Staged under analysis/staging/ until Freeze 3 (D-0011, reading 1).
Standard library only.
"""
from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

import layer0

GAP_MIN, LEVEL_MIN, GAP_BLEND, LEVEL_BLEND, X_MAX = 400, 2300, 50, 50, 735


def weight(r_white: int, r_black: int) -> Decimal:
    """The game's weight w = w_g * w_L on the published ratings (exact; 0 outside the region)."""
    gap = abs(r_white - r_black)
    level2 = r_white + r_black                    # twice the level, to keep the half points exact
    if gap < GAP_MIN or level2 < 2 * LEVEL_MIN:
        return Decimal(0)
    w_g = min(Decimal(1), Decimal(gap - GAP_MIN) / GAP_BLEND)
    w_l = min(Decimal(1), Decimal(level2 - 2 * LEVEL_MIN) / (2 * LEVEL_BLEND))
    return w_g * w_l


def in_region(r_white: int, r_black: int) -> bool:
    """The guard's region (published level >= 2300 and published gap >= 400), the edges included."""
    return abs(r_white - r_black) >= GAP_MIN and r_white + r_black >= 2 * LEVEL_MIN


def table_812_full(x: int) -> Decimal:
    """Table 8.1.2's H entry for the higher-rated player at the full difference x >= 0 (no 400-point cap)."""
    if x < 0:
        raise ValueError("x is the favourite's difference, x >= 0")
    return layer0.expected_score(x)


def guard_own(e_fit, x_own: int, own_is_favourite: bool, w):
    """A player's guarded expectation from the fitted value e_fit (float, or the published Decimal), the player's own
    effective gap x_own (own minus the opponent's rating that enters the expectation, plus or minus eta) and the
    game's weight w. Returns (expectation, binds)."""
    if not w:
        return e_fit, False
    x_fav = x_own if own_is_favourite else -x_own
    if x_fav < 0 or x_fav > X_MAX:
        return e_fit, False
    t = table_812_full(x_fav)
    dec = isinstance(e_fit, Decimal)
    if not dec:
        t, w = float(t), float(w)
    e_fav = e_fit if own_is_favourite else 1 - e_fit          # computed on the favourite's side and mirrored, so
    lift = t - e_fav                                            # that the published E(-x) = 1 - E(x) holds exactly
    if lift <= 0:
        return e_fit, False
    e = e_fav + w * lift
    if dec:
        e = e.quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)
    return (e if own_is_favourite else 1 - e), True
