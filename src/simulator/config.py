"""The simulator's parameters and scenarios (docs/specs/SPEC-SIM_v1_0.md §3, §3.5, §9). Every value is PROVISIONAL;
where a value comes from a measurement the comment names it. Standard library only."""
from __future__ import annotations

import math
from dataclasses import dataclass, field, replace

Q = math.log(10.0) / 400.0
KAPPA0, ETA, ALPHA, BETA, GAMMA = 1.2120, 35.91, 0.2860, 0.4985, 0.2915      # standard table fit [E2]; Freeze 1 file
ETA_L = KAPPA0 * ETA                                                       # η in latent units (SPEC-L1 §3.2)
# Layer 1's drift by age band (analysis/OUTPUT_L1_history.md): A (points a month at θ = 2000), B (per 400 points)
DRIFT_A = (16.10, 12.66, 6.60, 3.64, 0.0, -0.91, -1.79)
DRIFT_B = (3.09, 0.90, -0.71, -0.25, 0.0, 0.11, 0.90)
PROFILE = (25.0, 25.0, 20.0, 14.0, 12.0, 15.0, 15.0)                       # SPEC-L1 §3.7 (Layer 1's proxy)
DGP_PROFILE = (12.0, 12.0, 12.0, 12.0, 12.0, 15.0, 15.0)                   # the true noise: juniors' spread is in τ
# E1: 2025 newcomers' age shares and 2023 newcomers' median first rating (the last year before the 1400 floor), on the
# scale before the March 2024 compression; moved to today's scale by that compression, R + round(0.4 × (2000 − R))
# below 2000 [E5] (REDTEAM_v1_0, V10-STAT-2): 1472, 1494, 1572, 1644, 1644, 1661
ENTRANT_AGES = ((8, 9), (10, 14), (15, 19), (20, 29), (30, 49), (50, 70))
ENTRANT_SHARE = (0.081, 0.367, 0.194, 0.123, 0.135, 0.098)
ENTRANT_MEDIAN_2023 = (1120.0, 1156.0, 1286.0, 1407.0, 1406.0, 1435.0)
ENTRANT_MEDIAN = tuple(m + round(0.4 * (2000.0 - m)) if m < 2000.0 else m for m in ENTRANT_MEDIAN_2023)
FED_SIZES = (20.0, 10.0, 5.0, 2.0, 1.0, 0.5)                               # T9.1


@dataclass(frozen=True)
class Config:
    name: str = "baseline"
    seed: int = 20261010
    n0: int = 20000
    burn_in: int = 36
    months: int = 120
    start_year: int = 2020
    noise_scale: float = 1.0               # c of §3.2 (E8 chose 1.0 for standard; Layer 1's history fit 2.0)
    dgp_profile: tuple = DGP_PROFILE
    junior_factor_mean: float = 0.45       # τ̄, the junior drift factor (pilot-calibrated to E5's junior gains)
    junior_factor_cv: float = 0.5
    entry_rate: float = 0.022              # entrants a month, share of the active pool (pilot: E1's newcomer flow)
    entrant_share: tuple = ENTRANT_SHARE
    entrant_sd: float = 200.0
    exit_base: float = 0.003
    exit_new: float = 0.010                # fewer than 30 games
    exit_inactive: float = 0.03            # no game in the last 12 months
    activity_median_1800: float = 10.0     # games a year at θᴾ = 1800 (E5 §5, E8 §4)
    activity_slope: float = 0.002
    activity_sd_log: float = 0.8
    rounds_mean: float = 8.5
    domestic_share: float = 0.85           # Ghita: > 80 % domestic ([R 5], p. 23); E7: 52 % on broadcast games
    rr_share: float = 0.20
    fed_offset_sd: float = 35.0            # E7's spread of federation offsets on broadcast games
    fed_offsets: tuple | None = None       # fixed offsets (scenario 3); otherwise drawn with fed_offset_sd
    isolated: tuple = ()                   # federations that play 1 % abroad (scenario 3)
    adversaries: bool = False
    ratchet: bool = False                  # rung 2's κ falls 0.05 a year from the second year of operation
    ledgers: tuple = ("L0", "R2", "R2U", "R3", "R4A", "R4L", "R5", "R6", "R7", "ALL")
    k_activity_ck: float = 1.0             # SPEC-K-ACTIVITY's growth scale for standard, chosen in E8
    extra: dict = field(default_factory=dict)


def scenario(name: str, seed: int, **kw) -> Config:
    base = Config(name=name, seed=seed)
    if name == "baseline":
        cfg = base
    elif name == "noise2":
        cfg = replace(base, noise_scale=2.0)
    elif name == "deflation":
        cfg = replace(base, entry_rate=0.030, junior_factor_mean=base.junior_factor_mean * 1.5,
                      entrant_share=(0.20, 0.50, 0.15, 0.06, 0.05, 0.04))
    elif name == "federations":
        cfg = replace(base, fed_offsets=(0.0, 0.0, 0.0, 0.0, -100.0, 60.0), isolated=(4, 5))
    elif name == "adversaries":
        cfg = replace(base, adversaries=True)
    elif name == "ratchet":
        cfg = replace(base, ratchet=True, ledgers=("L0", "R2"))
    else:
        raise ValueError(name)
    return replace(cfg, **kw)
