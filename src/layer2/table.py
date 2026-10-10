"""Rung 2: the expected-score function fitted on published ratings (annex T3.1, T3.4; SPEC-TABLE-FIT §2).

Two forms of the same D1 model, White's view, z = κ q (gap + η), ν = exp(α + β (L_mid − 2000)/400 − γ |z|),
P_W : P_D : P_L = e^{z/2} : ν : e^{−z/2}:
  - `probs` and `expected_white`: the evaluation form of E2 and E6 (fractional η, unrounded), so that a test
    reproduces analysis/e2_broadcast_extract.py exactly;
  - `published`: the published table's entry (η rounded to a whole number and added to the gap, E to three
    decimals half up, E(−x) = 1 − E(x)), as tools/compare_event.py computes it (SPEC-COMPARE §3).
`par` is (κ, η, α, β, γ). Standard library only.
"""
from __future__ import annotations

import math
from decimal import ROUND_HALF_UP, Decimal

Q = math.log(10.0) / 400.0


def band_mid(level: int) -> int:
    """Midpoint of the 100-point level band (annex T3.4): 1450 below 1500, 2850 from 2800."""
    if level < 1500:
        return 1450
    if level >= 2800:
        return 2850
    return 1500 + 100 * ((level - 1500) // 100) + 50


def probs(par: tuple, gap_white: float, mid: float) -> tuple[float, float, float]:
    """(P_W, P_D, P_L) at White's published gap (without colour; η is added here) and level band midpoint."""
    kappa, eta, alpha, beta, gamma = par
    z = kappa * Q * (gap_white + eta)
    nu = math.exp(alpha + beta * (mid - 2000.0) / 400.0 - gamma * abs(z))
    a = math.exp(z / 2.0)
    b = 1.0 / a
    den = a + b + nu
    return a / den, nu / den, b / den


def expected_white(par: tuple, gap_white: float, mid: float) -> float:
    pw, pd, _pl = probs(par, gap_white, mid)
    return pw + pd / 2.0


def eta_whole(eta: float) -> int:
    """η rounded half up to a whole number of points (annex T3.4)."""
    return int(Decimal(repr(eta)).quantize(Decimal(1), rounding=ROUND_HALF_UP))


def published(x: int, mid: int, par: tuple) -> Decimal:
    """The published entry at effective gap x (colour included, η whole), three decimals half up; E(−x) = 1 − E(x)."""
    kappa, _eta, alpha, beta, gamma = par
    z = kappa * Q * abs(x)
    nu = math.exp(alpha + beta * (mid - 2000.0) / 400.0 - gamma * z)
    a, b = math.exp(z / 2.0), math.exp(-z / 2.0)
    e = Decimal(repr((a + nu / 2.0) / (a + b + nu))).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)
    return e if x >= 0 else Decimal(1) - e
