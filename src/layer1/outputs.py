"""Layer 1 outputs for Layer 2 (SPEC-L1 §5; annex T4.3, T4.5–T4.7; rulings R2, R5, R6 of D-0008).

Pure functions of the fitted quantities. Every parameter default is the annex's
PROVISIONAL value. Standard library only.
"""
from __future__ import annotations

import math
from decimal import ROUND_HALF_UP, Decimal

Q = math.log(10.0) / 400.0
K_MIN, K_MAX = 10.0, 40.0
Z90 = 1.2816
TAU, C_CAP = 25, 300
R_FLOOR, R_SEEDMAX, SIGMA_SEED_MAX = 1400, 2200, 120.0
D0, GAMMA_A, A_CAP = 2.0, 1.0 / 6.0, 1.5


def round_fide(v: float) -> int:
    """Nearest whole number, 0.5 away from zero (§8.3.4)."""
    d = Decimal(repr(v)).copy_abs().quantize(Decimal(1), rounding=ROUND_HALF_UP)
    return int(d) if v >= 0 else -int(d)


def theta_tilde(s_hat: float, m_pub: float, m_lat: float, kappa: float) -> float:
    """R2: θ̃ = m_t + (ŝ − m̂_t)/κ_tc; with κ = 1 it is ŝ − d_t."""
    return m_pub + (s_hat - m_lat) / kappa


def k_from_sigma(sigma: float, kappa: float, v: float, k_min: float = K_MIN, k_max: float = K_MAX) -> float:
    """R6: K = clip(q σ² / (κ (1 + q² σ² v)), K_min, K_max); D3 when κ = 1 and v = 1/4."""
    raw = Q * sigma * sigma / (kappa * (1.0 + Q * Q * sigma * sigma * v))
    return min(k_max, max(k_min, raw))


def k_printed(sigma: float, kappa: float, v: float) -> float:
    """K_i to one decimal, as the list prints it (annex T4.3)."""
    k = k_from_sigma(sigma, kappa, v)
    return float(Decimal(repr(k)).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))


def info_share(p_all: float, p_tc: float, p_0: float, only_tc: bool = False) -> float:
    """R5: share of the posterior precision of s_{j,tc} that comes from games in tc, in [0, 1]."""
    if only_tc:
        return 1.0
    denom = p_all - p_0
    if denom <= 0.0:
        return 0.0
    return min(1.0, max(0.0, (p_tc - p_0) / denom))


def compensation(theta_t: float, sigma_pub: float, r_j: int | None, eligible: bool, tau: int = TAU,
                 c_cap: int = C_CAP, z: float = Z90) -> int:
    """Annex T4.6 with R5's posterior: c_j = min(c_cap, max(0, round_FIDE(θ̃ − z σ̃ − R_j − τ))); 0 if not eligible."""
    if not eligible or r_j is None:
        return 0
    return min(c_cap, max(0, round_fide(theta_t - z * sigma_pub - r_j - tau)))


def junior_eligible(age: int | None, games: int, opponents: int, events: int, share: float,
                    max_age: int = 19, min_games: int = 10, min_opp: int = 5, min_events: int = 3,
                    min_share: float = 0.5) -> bool:
    """Annex T4.6 gates and R5's information-share condition (PROVISIONAL 0.5)."""
    return (age is not None and age <= max_age and games >= min_games and opponents >= min_opp
            and events >= min_events and share >= min_share)


def seed(theta_t: float, sigma_pub: float, rated_games: int, opponents: int, events: int,
         n_seed: int = 5, min_opp: int = 3, min_events: int = 2) -> int | None:
    """Annex T4.7: min(round_FIDE(θ̃), 2200), published only if round_FIDE(θ̃) ≥ 1400 and σ̃ ≤ 120 with the gates."""
    if rated_games < n_seed or opponents < min_opp or events < min_events or sigma_pub > SIGMA_SEED_MAX:
        return None
    r = round_fide(theta_t)
    if r < R_FLOOR:
        return None
    return min(r, R_SEEDMAX)


def monthly_adjustment(d_t: float, d0: float = D0, gamma_a: float = GAMMA_A, cap: float = A_CAP) -> float:
    """Annex T4.5: a_t = clip(γ_a sign(d_t) max(0, |d_t| − d_0), ±cap), one decimal."""
    raw = gamma_a * (1.0 if d_t > 0 else -1.0 if d_t < 0 else 0.0) * max(0.0, abs(d_t) - d0)
    a = min(cap, max(-cap, raw))
    return float(Decimal(repr(a)).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))


def accrual_factor(games_12: int, anchor_mean_games: float) -> float:
    """R3: accrual scaled by min(1, n_i over 12 months / the anchor cohort's mean games)."""
    if anchor_mean_games <= 0:
        return 1.0
    return min(1.0, games_12 / anchor_mean_games)
