"""R17: the temporary farming guard for rung 2 (docs/decisions/D-0009_architect-rulings-elo-5.md, R17 and reading 4).

In all three time controls, when the gap is 400 or more and the favourite is rated 2300 or more, the
favourite's expected score is the larger of the fitted value and table 8.1.2 read without the 400-point cap;
the underdog's is one minus it. The gap is the published rating difference that enters the expectation,
without the colour term (R_i − RX_j when junior compensation applies); "rated 2300 or more" is the
favourite's published rating on the list in force. Table 8.1.2 is read from the ratified Layer-0 engine
(H column at the full difference, 1.0 above 735 points [V 1]). Each player's expectation is guarded on the
gap that player's own expectation uses, so that without compensation the two sum to one. The guard lapses
only when FIDE's game data calibrate the region. Works on floats (evaluation) and on Decimals (the
published three-decimal table). Standard library only.
"""
from __future__ import annotations

from decimal import Decimal

import layer0

GAP_MIN, FAV_MIN = 400, 2300


def in_region(r_fav: int, r_und: int) -> bool:
    """The guard's region: the favourite rated 2300 or more and the gap 400 or more."""
    return r_fav >= FAV_MIN and r_fav - r_und >= GAP_MIN


def table_812_uncapped(d: int) -> Decimal:
    """Table 8.1.2's PD for the higher-rated player at the full difference d ≥ 0, without the 400-point cap."""
    if d < 0:
        raise ValueError("d is the favourite's difference, d >= 0")
    return layer0.expected_score(d)


def guard_own(e_fit, r_own: int, r_opp: int, r_opp_published: int | None = None):
    """A player's expectation under the guard, from the fitted value e_fit and the two ratings that enter it (r_opp is
    RX_j when junior compensation applies). The favourite's "rated 2300 or more" is read on its published rating
    (reading 4): pass r_opp_published when r_opp is a compensated rating. Returns (expectation, binds): binds is True
    when the guard changed the value."""
    own_fav = r_own >= r_opp
    gap = abs(r_own - r_opp)
    fav_published = r_own if own_fav else (r_opp if r_opp_published is None else r_opp_published)
    if not (fav_published >= FAV_MIN and gap >= GAP_MIN):
        return e_fit, False
    fav, und = (r_own, r_opp) if own_fav else (r_opp, r_own)
    t = table_812_uncapped(fav - und)
    if not isinstance(e_fit, Decimal):
        t = float(t)
    if own_fav:
        return (t, True) if t > e_fit else (e_fit, False)
    low = 1 - t
    return (low, True) if low < e_fit else (e_fit, False)
