"""Layer 0 for the simulator: SPEC-L0's standard rules in integer arithmetic (docs/specs/SPEC-SIM_v1_0.md §4.1).

The tables are read once from the ratified engine (src/layer0), so that every entry is Layer 0's; the rules
are re-implemented with integers for speed and tested against src/layer0 (tests/test_simulator.py). Scores
are in half points (0, 1, 2) and expectations in hundredths, so a period's change is exact before its one
rounding. Current standard regulations: the 400-point rule with the 2650 exemption (R-14). Standard library only.
"""
from __future__ import annotations

from decimal import Decimal

import layer0

DMAX = 800
_PD = [int(layer0.expected_score(d) * 100) for d in range(DMAX + 1)]          # H column, hundredths, d = 0..800
PD100 = [100 - _PD[-d] for d in range(-DMAX, 0)] + _PD                        # index d + DMAX, d = -800..800
DP = {p: layer0.dp_from_p(Decimal(p) / 100) for p in range(101)}              # table 8.1.1, p in hundredths
CAP, EXEMPT = 400, 2650


def pd100(own: int, opp: int) -> int:
    """R-13 to R-16: PD of `own` in hundredths, the gap capped at 400 unless own is rated 2650 or more."""
    d = own - opp
    if d > CAP and own < EXEMPT:
        d = CAP
    elif d < -CAP and own < EXEMPT:
        d = -CAP
    if d > DMAX:
        d = DMAX
    elif d < -DMAX:
        d = -DMAX
    return PD100[d + DMAX]


def pd100_uncapped(d: int) -> int:
    """Table 8.1.2 at the full difference d (no cap), hundredths: the guard's reading (R17)."""
    d = max(-DMAX, min(DMAX, d))
    return PD100[d + DMAX]


def published_k(rating: int, games_count: int, ever_2400: bool, ever_2300: bool, year: int, birth: int | None) -> int:
    """R-18 to R-22, in the order settled on FIDE's published K (SPEC-L0 R-22)."""
    if ever_2400 or rating >= 2400:
        return 10
    if birth is not None and year - birth <= 18 and not ever_2300 and rating < 2300:
        return 40
    if games_count < 30:
        return 40
    return 20


def k_for_period(k: int, n: int) -> int:
    """R-23: the largest whole K with K × n ≤ 700."""
    if n > 0 and k * n > 700:
        return 700 // n
    return k


def round_half_away(num: int, den: int) -> int:
    """num/den to the nearest whole number, 0.5 away from zero (R-25), exactly."""
    if num >= 0:
        return (2 * num + den) // (2 * den)
    return -((-2 * num + den) // (2 * den))


def initial_rating(events: list) -> int | None:
    """R-26 to R-30. events: [(first_event, [(opponent rating, score in halves), ...]), ...] in time order."""
    results = []
    for first, res in events:
        if first and sum(s for _, s in res) == 0:
            continue                                                        # R-28
        results.extend(res)
    n = len(results)
    if n < 5:                                                               # R-27
        return None
    w2 = sum(s for _, s in results)                                         # score in halves
    p100 = (100 * (w2 + 2) + (n + 2)) // (2 * (n + 2))                      # p = (W + 1)/(n + 2), .005 up (R-30)
    num = sum(r for r, _ in results) + 3600 + DP[p100] * (n + 2)            # Ru = Ra + dp, Ra = (Σ + 3600)/(n + 2)
    ru = min((2 * num + (n + 2)) // (2 * (n + 2)), 2200)                    # R-26: rounded, 0.5 up; at most 2200
    return ru if ru >= 1400 else None
