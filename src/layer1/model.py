"""Layer 1 outcome model and dynamics (SPEC-L1 §3; annex T2.1, T2.2).

Latent units: the slope is 1, so a latent gap x gives z = q·x with q = ln 10 / 400.
For White's view of a game: P_W : P_D : P_L = e^{z/2} : ν : e^{-z/2},
ν = exp(α + β·ℓ − γ·|z|). Pure functions, standard library only.
"""
from __future__ import annotations

import math

Q = math.log(10.0) / 400.0
TCS = ("standard", "rapid", "blitz")
AGE_BANDS = ("<12", "12-15", "16-19", "20-24", "25-45", "46-60", ">60")
ANCHOR_BAND = 4                       # ages 25-45: drift fixed at zero (annex T2.4)


def age_band(age: int | None) -> int:
    """Index into AGE_BANDS; a player without a year of birth counts as 25-45 (T2.2)."""
    if age is None:
        return ANCHOR_BAND
    if age < 12:
        return 0
    if age <= 15:
        return 1
    if age <= 19:
        return 2
    if age <= 24:
        return 3
    if age <= 45:
        return 4
    if age <= 60:
        return 5
    return 6


def band_mid(level: int) -> int:
    """Midpoint of the 100-point level band of the published table (annex T3.4)."""
    if level < 1500:
        return 1450
    if level >= 2800:
        return 2850
    return 1500 + 100 * ((level - 1500) // 100) + 50


def ell_of(level_mid: float) -> float:
    return (level_mid - 2000.0) / 400.0


def probs(z: float, nu0: float, gamma: float) -> tuple[float, float, float]:
    """(P_W, P_D, P_L) for White at z, with ν = nu0·exp(−γ|z|)."""
    nu = nu0 * math.exp(-gamma * abs(z))
    a = math.exp(0.5 * z)
    b = 1.0 / a
    d = a + b + nu
    return a / d, nu / d, b / d


def game_terms(z: float, nu0: float, gamma: float, s_white: float) -> tuple[float, float, float]:
    """For one game seen from White: log P(result), u = d log P / dz and the Fisher information E[u^2].

    s_white is White's score (1, 0.5, 0). u = (S − E) − γ·sign(z)·(D − P_D) (annex T3.3)."""
    pw, pd, pl = probs(z, nu0, gamma)
    e = pw + 0.5 * pd
    sg = 1.0 if z > 0 else -1.0 if z < 0 else 0.0
    gs = gamma * sg
    u_w = (1.0 - e) + gs * pd
    u_d = (0.5 - e) - gs * (1.0 - pd)
    u_l = -e + gs * pd
    info = pw * u_w * u_w + pd * u_d * u_d + pl * u_l * u_l
    if s_white == 1.0:
        return math.log(pw), u_w, info
    if s_white == 0.5:
        return math.log(pd), u_d, info
    return math.log(pl), u_l, info


def expected_white(z: float, nu0: float, gamma: float) -> float:
    pw, pd, _ = probs(z, nu0, gamma)
    return pw + 0.5 * pd


def score_variance_at_zero(nu0: float) -> float:
    """Var(S) at z = 0: 1/(2(2 + ν0)); ¼ without draws (SPEC-L1 §5.1, R6's v_tc)."""
    return 1.0 / (2.0 * (2.0 + nu0))
