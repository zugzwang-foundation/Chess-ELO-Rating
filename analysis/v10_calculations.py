#!/usr/bin/env python3
"""Calculations for proposal v1.0, technical annex v1.0 and the brief v1.0.

Python standard library only. Deterministic. NOT the rating engine: these are
hand-check-scale calculations, and their output is the source of every number
in docs/proposal/ELO-PROPOSAL_v1_0.md, docs/proposal/ELO-TECHNICAL-ANNEX_v1_0.md
and docs/proposal/ELO-BRIEF_v1_0.md that is not cited to an evidence report.
Run:  python3 analysis/v10_calculations.py > analysis/OUTPUT_v1_0.md

Every parameter value below is PROVISIONAL (annex T1 and T7), except the
expected-score table's (kappa, eta, alpha, beta, gamma), which are
PROVISIONAL-FITTED: read from params/table_fit_2026-10.yaml (docs/evidence/
E2_broadcast-calibration.md), with eta rounded to a whole number because the
published table has one row per whole-number gap (annex T3.4). The architect's
decisions D1-D18 are recorded in docs/decisions/D-0005_architect-decisions-v0.3.md and
the rulings R1-R14 in docs/decisions/D-0008_architect-rulings-elo-4.md: K from the
published-scale gain (R6), theta~ in spread as well as level (R2), compensation from the
published-scale posterior (R5) and only against non-eligible opponents (R8), accrual
scaled by activity (R3), gamma >= 0 without an upper bound (R7). Version 1.0 applies the rulings
R15-R23 (docs/decisions/D-0009_architect-rulings-elo-5.md): K falls with the period's games (R16;
section 5 and the ledger of section 10 recomputed), the farming guard of rung 2 (R17; section 8), and
the R1 review on the cumulative change of the spread ratio with the threshold calibrated in the
simulator (R19, R20; section 12, read from analysis/aggregates/E9_simulator.json).
"""
from __future__ import annotations

import math
import re
from decimal import ROUND_DOWN, ROUND_HALF_UP, Decimal
from fractions import Fraction
from pathlib import Path

Q = math.log(10.0) / 400.0          # q = ln 10 / 400
PARAM_FILE = "params/table_fit_2026-10.yaml"


def read_params(path: str) -> dict:
    """The fitted table parameters of every time control in a params/table_fit_*.yaml file."""
    text = (Path(__file__).resolve().parents[1] / path).read_text(encoding="utf-8")
    out = {}
    for tc in ("standard", "rapid", "blitz"):
        block = re.search(rf"^{tc}:\n((?:  .*\n?)+)", text, re.M).group(1)
        v = {k: float(re.search(rf"^  {k}: {{value: (-?[\d.]+)", block, re.M).group(1))
             for k in ("kappa", "eta", "alpha", "beta", "gamma")}
        v["eta"] = int(Decimal(repr(v["eta"])).quantize(Decimal(1), rounding=ROUND_HALF_UP))
        out[tc] = v
    return out


# ---------------------------------------------------------------- parameters
PARAMS = read_params(PARAM_FILE)    # PROVISIONAL-FITTED (E2)
ETA = PARAMS["standard"]["eta"]     # White's edge in standard, whole points
GAMMA = PARAMS["standard"]["gamma"]
K_MIN, K_MAX = 10.0, 40.0
C_PERIOD = 700
A_CAP, GAMMA_A, D_0 = Decimal("1.5"), Decimal(1) / Decimal(6), Decimal("2.0")
TAU, C_CAP, Z_Q = Decimal(25), Decimal(300), Decimal("1.2816")
BAND_WIDTH, BAND_LOW, BAND_HIGH = 100, 1500, 2800    # open bands below 1500 and from 2800


# ---------------------------------------------------------------- core functions
def band_lo(L: float, width: int = BAND_WIDTH, low: int = BAND_LOW, high: int = BAND_HIGH) -> int | None:
    """Lower edge of the level band of L (whole-number part of the mean); None for the open bands."""
    Li = math.floor(L)
    if Li < low or Li >= high:
        return None
    return low + width * ((Li - low) // width)


def band_mid(L: float, width: int = BAND_WIDTH, low: int = BAND_LOW, high: int = BAND_HIGH) -> int:
    Li = math.floor(L)
    if Li < low:
        return low - width // 2
    if Li >= high:
        return high + width // 2
    return band_lo(L, width, low, high) + width // 2


def band_label(L: float, width: int = BAND_WIDTH, low: int = BAND_LOW, high: int = BAND_HIGH) -> str:
    Li = math.floor(L)
    if Li < low:
        return f"<{low}"
    if Li >= high:
        return f">={high}"
    lo = band_lo(L, width, low, high)
    return f"{lo}-{lo + width - 1}"


def mids_of(width: int = BAND_WIDTH, low: int = BAND_LOW, high: int = BAND_HIGH) -> list[int]:
    return [low - width // 2] + list(range(low + width // 2, high, width)) + [high + width // 2]


def labels_of(width: int = BAND_WIDTH, low: int = BAND_LOW, high: int = BAND_HIGH) -> list[str]:
    return [f"<{low}"] + [f"{lo}-{lo + width - 1}" for lo in range(low, high, width)] + [f">={high}"]


def nu0(tc: str, L: float) -> float:
    p = PARAMS[tc]
    return math.exp(p["alpha"] + p["beta"] * (L - 2000.0) / 400.0)


def probs(tc: str, x: float, L: float, gamma: float | None = None, kappa: float | None = None,
          nu0_override: float | None = None) -> tuple[float, float, float]:
    """P_W, P_D, P_L for effective gap x at level L (D1: nu(z) = nu0 * exp(-gamma |z|))."""
    p = PARAMS[tc]
    g = p["gamma"] if gamma is None else gamma
    k = p["kappa"] if kappa is None else kappa
    n0 = nu0(tc, L) if nu0_override is None else nu0_override
    z = k * Q * x
    nu = n0 * math.exp(-g * abs(z))
    a, b = math.exp(z / 2.0), math.exp(-z / 2.0)
    den = a + b + nu
    return a / den, nu / den, b / den


def E_exact(tc: str, x: float, L: float, **kw) -> float:
    pw, pd, _ = probs(tc, x, L, **kw)
    return pw + pd / 2.0


def E_table(tc: str, x: int, L: float) -> Decimal:
    """The published table entry: E at the band midpoint, three decimals; negative x by 1 - E."""
    if x < 0:
        return Decimal(1) - E_table(tc, -x, L)
    return Decimal(E_exact(tc, x, band_mid(L))).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)


def v_of(R: float, tc: str = "standard") -> float:
    """R6 (D-0008 reading 5): the per-game score variance at x = 0 in the player's own level band, 1 / (2 (2 + nu0))."""
    return 1.0 / (2.0 * (2.0 + nu0(tc, band_mid(R))))


def K_raw(sigma: float, R: float, tc: str = "standard") -> float:
    """R6: q sigma^2 / (kappa (1 + q^2 sigma^2 v)), sigma the Layer 1 posterior SD in latent units."""
    return Q * sigma * sigma / (PARAMS[tc]["kappa"] * (1.0 + Q * Q * sigma * sigma * v_of(R, tc)))


def K_D3(sigma: float) -> float:
    """v0.3's D3 gain (kappa = 1, v = 1/4), for comparison only."""
    return Q * sigma * sigma / (1.0 + Q * Q * sigma * sigma / 4.0)


def K_of(sigma: float, R: float, tc: str = "standard") -> Decimal:
    """R6: K = clip(q sigma^2 / (kappa (1 + q^2 sigma^2 v)), K_min, K_max), one decimal."""
    k = min(K_MAX, max(K_MIN, K_raw(sigma, R, tc)))
    return Decimal(k).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)


def sigma_for_K(K: float, R: float, tc: str = "standard") -> float:
    """The sigma at which K_raw equals K (inverse of R6 at the player's level)."""
    kap, v = PARAMS[tc]["kappa"], v_of(R, tc)
    return math.sqrt(K * kap / (Q - K * kap * Q * Q * v))


def K_capped(K: Decimal, n: int) -> Decimal:
    """Per-period cap: if K*n > 700, K becomes floor(7000/n)/10."""
    if K * n > C_PERIOD:
        return (Decimal(10 * C_PERIOD) / Decimal(n)).quantize(Decimal("1"), rounding=ROUND_DOWN) / Decimal(10)
    return K


def K_n_raw(sigma: float, R: float, n: int, tc: str = "standard") -> float:
    """R16: the per-game gain of a period with n games, q sigma^2 / (kappa (1 + n q^2 sigma^2 v)), before the clip."""
    return Q * sigma * sigma / (PARAMS[tc]["kappa"] * (1.0 + n * Q * Q * sigma * sigma * v_of(R, tc)))


def K_n(sigma: float, R: float, n: int, tc: str = "standard") -> Decimal:
    """R16: K_i(n) = clip(q sigma^2 / (kappa (1 + n q^2 sigma^2 v)), K_min, K_max), one decimal; n = 1 is R6."""
    k = min(K_MAX, max(K_MIN, K_n_raw(sigma, R, n, tc)))
    return Decimal(k).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)


def published_form(sigma: float, R: float, tc: str = "standard") -> tuple[float, float]:
    """D-0009 reading 3: K_i(n) = clip(C / (N_i + n)) with C = 1 / (kappa q v) and N_i = 1 / (q^2 sigma^2 v)."""
    v = v_of(R, tc)
    return 1.0 / (PARAMS[tc]["kappa"] * Q * v), 1.0 / (Q * Q * sigma * sigma * v)


def guard_E(E: Decimal, own: int, opp: int) -> Decimal:
    """R17 (D-0009 reading 4): for a favourite rated 2300 or more at a gap of 400 or more, the larger of the fitted value and
    table 8.1.2 read without the cap; the underdog's is one minus it. Gap without the colour term."""
    if own - opp >= 400 and own >= 2300:
        return max(E, table_812_H(own - opp))
    if opp - own >= 400 and opp >= 2300:
        return min(E, Decimal(1) - table_812_H(opp - own))
    return E


def round_fide(v: Decimal) -> Decimal:
    """Nearest whole number, 0.5 away from zero (FIDE 8.3.4)."""
    return v.quantize(Decimal("1"), rounding=ROUND_HALF_UP)


def comp_raw(theta_tilde: Decimal, sigma: Decimal, R: Decimal) -> Decimal:
    return theta_tilde - Z_Q * sigma - R - TAU


def comp(theta_tilde, sigma, R) -> Decimal:
    """D5 with R5: c_j = min(c_cap, max(0, theta~ - z sigma~ - R - tau)), on the whole-number grid; theta~ and sigma~
    are the same-time-control posterior on the published scale (sigma~ = sigma / kappa)."""
    v = round_fide(comp_raw(Decimal(theta_tilde), Decimal(sigma), Decimal(R)))
    return min(C_CAP, max(Decimal(0), v))


def a_of(d: Decimal) -> Decimal:
    """D7: a_t = clip(gamma_a * sign(d) * max(0, |d| - d_0), -a_cap, +a_cap), one decimal."""
    mag = max(Decimal(0), abs(d) - D_0) * GAMMA_A
    raw = mag if d >= 0 else -mag
    return max(-A_CAP, min(A_CAP, raw)).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)


def logistic(x: float) -> float:
    return 1.0 / (1.0 + 10.0 ** (-x / 400.0))


def table_812_H(D: int) -> Decimal:
    """Today's table 8.1.2, H column, for D >= 0 [V 1]."""
    rows = [(3, ".50"), (10, ".51"), (17, ".52"), (25, ".53"), (32, ".54"), (39, ".55"), (46, ".56"), (53, ".57"),
            (61, ".58"), (68, ".59"), (76, ".60"), (83, ".61"), (91, ".62"), (98, ".63"), (106, ".64"), (113, ".65"),
            (121, ".66"), (129, ".67"), (137, ".68"), (145, ".69"), (153, ".70"), (162, ".71"), (170, ".72"),
            (179, ".73"), (188, ".74"), (197, ".75"), (206, ".76"), (215, ".77"), (225, ".78"), (235, ".79"),
            (245, ".80"), (256, ".81"), (267, ".82"), (278, ".83"), (290, ".84"), (302, ".85"), (315, ".86"),
            (328, ".87"), (344, ".88"), (357, ".89"), (374, ".90"), (391, ".91"), (411, ".92"), (432, ".93"),
            (456, ".94"), (484, ".95"), (517, ".96"), (559, ".97"), (619, ".98"), (735, ".99")]
    for hi, h in rows:
        if D <= hi:
            return Decimal(h)
    return Decimal("1.0")


def phi(z: float) -> float:
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def f3(v) -> str:
    return f"{v:.3f}"


# ---------------------------------------------------------------- report
out: list[str] = []
P = out.append

P("# OUTPUT of analysis/v10_calculations.py (parameters PROVISIONAL; the table's PROVISIONAL-FITTED)\n")
P("Generated deterministically by the script; the source of every calculated number in the proposal v1.0, the technical annex v1.0 and the brief v1.0 "
  "that is not cited to an evidence report. Rulings R1-R14 (D-0008) and R15-R23 (D-0009) applied.\n")

# 0. Parameters
P("## 0 Parameters used\n")
P(f"The table's parameters are PROVISIONAL-FITTED, read from {PARAM_FILE} (maximum likelihood on the Lichess broadcast "
  "archive, CC BY-SA 4.0, against FIDE's lists; docs/evidence/E2_broadcast-calibration.md), with eta rounded to a "
  "whole number; every other value is PROVISIONAL.\n")
P("| tc | kappa | eta | alpha | beta | gamma |")
P("|---|---|---|---|---|---|")
for tc, p in PARAMS.items():
    P(f"| {tc} | {p['kappa']:.4f} | {p['eta']} | {p['alpha']:.4f} | {p['beta']:.4f} | {p['gamma']:.4f} |")
P("")
P(f"q = ln 10 / 400 = {Q:.7f}; K_min = {K_MIN:.0f}, K_max = {K_MAX:.0f}; C_period = {C_PERIOD}; a_cap = {A_CAP}, gamma_a = 1/6, d_0 = {D_0}; "
  f"tau = {TAU}, c_cap = {C_CAP}, z = {Z_Q}; level bands of {BAND_WIDTH} points from {BAND_LOW} to {BAND_HIGH}, open below and above "
  f"(midpoints {BAND_LOW - BAND_WIDTH // 2} and {BAND_HIGH + BAND_WIDTH // 2}).\n")

# 1. Table
MIDS, LABELS = mids_of(), labels_of()
P(f"## 1 Expected-score table, standard (D1 draw decay, fitted gamma = {GAMMA:.4f}; D6 bands of 100 points; E to three decimals)\n")
P("| x | " + " | ".join(LABELS) + " |")
P("|---|" + "---|" * len(LABELS))
for x in range(0, 1001, 100):
    P(f"| {x} | " + " | ".join(f3(E_exact('standard', x, m)) for m in MIDS) + " |")
P("")
SEL = [0, 2, 4, 6, 8, 10, 12, 14]
P("Excerpt printed in annex T3.4 (every other band):\n")
P("| x | " + " | ".join(LABELS[i] for i in SEL) + " |")
P("|---|" + "---|" * len(SEL))
for x in range(0, 1001, 100):
    P(f"| {x} | " + " | ".join(f3(E_exact('standard', x, MIDS[i])) for i in SEL) + " |")
P("")
P("Draw probability at x = 0 by band midpoint, standard: " + ", ".join(f"{m}: {f3(probs('standard', 0, m)[1])}" for m in MIDS) + "\n")
P("nu0 by band midpoint, standard: " + ", ".join(f"{m}: {nu0('standard', m):.4f}" for m in MIDS) + "\n")

# 2. Tail against the 5/6-gap rule
P("## 2 The forecast tail at level 2300 (fitted standard parameters) against the 5/6-gap rule\n")
P(f"nu0 at L = 2300: {nu0('standard', 2300):.4f}. The 5/6-gap rule is logistic Elo on five sixths of the gap, 1/(1 + 10^(-(5x/6)/400)) [R 44]; "
  "today's table 8.1.2 [V 1] is shown for reference; the D1 columns with gamma = 1/2 and gamma = 0 keep the other fitted values.\n")
P(f"| gap x | D1 (fitted gamma = {GAMMA:.4f}): P_W / P_D / P_L | D1: E | gamma = 1/2: E | gamma = 0: P_D | gamma = 0: E | 5/6-gap rule | table 8.1.2 |")
P("|---|---|---|---|---|---|---|---|")
for x in (200, 400, 500, 700):
    pw, pd, pl = probs('standard', x, 2300)
    _, pd0, _ = probs('standard', x, 2300, gamma=0.0)
    P(f"| {x} | {pw:.3f} / {pd:.3f} / {pl:.3f} | {f3(E_exact('standard', x, 2300))} | {f3(E_exact('standard', x, 2300, gamma=0.5))} | {pd0:.3f} | "
      f"{f3(E_exact('standard', x, 2300, gamma=0.0))} | {f3(logistic(5 * x / 6))} | {table_812_H(x)} |")
P("")
for x in (400, 800, 1200):
    rat = lambda g: probs('standard', x, 2300, gamma=g)[1] / probs('standard', x, 2300, gamma=g)[2]
    P(f"- x = {x}: P_D / P_L = {rat(GAMMA):.4f} with the fitted gamma; {rat(0.5):.4f} with gamma = 1/2 (equals nu0: draws fade as fast as losses); "
      f"{rat(0.0):.4f} with gamma = 0.")
P("")

# 3. Checks
P("## 3 Numerical checks of the D1 form (standard parameters)\n")
grid = range(-1500, 1501)
for g in (0.0, 0.25, GAMMA, 0.5):
    sym = max(abs(E_exact('standard', x, m, gamma=g) + E_exact('standard', -x, m, gamma=g) - 1.0) for x in grid for m in MIDS)
    mono = min(E_exact('standard', x + 1, m, gamma=g) - E_exact('standard', x, m, gamma=g) for x in range(-1500, 1500) for m in MIDS)
    P(f"- gamma = {g:g}: symmetry max |E(x) + E(-x) - 1| over x in [-1500, 1500], all bands = {sym:.1e}; "
      f"monotonicity min E(x+1) - E(x) = {mono:.2e} (> 0)")
lg = max(abs(E_exact('standard', x, 2000, gamma=0.5, kappa=1.0, nu0_override=0.0) - logistic(x)) for x in grid)
P(f"- Logistic special case (nu0 = 0, kappa = 1, any gamma): max |E(x) - 1/(1 + 10^(-x/400))| = {lg:.1e}")
h = 1e-3
for L in (1700, 2300, 2700):
    num = (E_exact('standard', h, L) - E_exact('standard', -h, L)) / (2 * h)
    kap = PARAMS['standard']['kappa']
    ana = kap * Q / (2 * (2 + nu0('standard', L)))
    P(f"- Slope at x = 0, level {L}: numerical {num:.6e}, formula kappa q / (2 (2 + nu0)) = {ana:.6e}; local logistic scale 200 (2 + nu0) / kappa = {200 * (2 + nu0('standard', L)) / kap:.1f} (logistic Elo: 400)")
P("")


def band_steps(width: int, low: int, high: int, gamma: float) -> tuple[float, int, str, list[float]]:
    mids, labels = mids_of(width, low, high), labels_of(width, low, high)
    per_pair, best = [], (0.0, 0, "")
    for b in range(len(mids) - 1):
        m = 0.0
        for x in range(0, 1501):
            d = abs(E_exact('standard', x, mids[b], gamma=gamma) - E_exact('standard', x, mids[b + 1], gamma=gamma))
            if d > m:
                m = d
            if d > best[0]:
                best = (d, x, f"{labels[b]} / {labels[b + 1]}")
        per_pair.append(m)
    return best[0], best[1], best[2], per_pair


P("### 3.1 Band-edge steps (D6): max over x in [0, 1500] of |E(x; band b) - E(x; band b+1)|\n")
P("| bands | gamma | largest step | at x | between | points at K = 20 |")
P("|---|---|---|---|---|---|")
for width, low, high, g, name in ((200, 1600, 2800, 0.0, "200 (v0.2)"), (200, 1600, 2800, GAMMA, "200"), (100, BAND_LOW, BAND_HIGH, GAMMA, "100 (v0.3)")):
    s, x_at, pair, _ = band_steps(width, low, high, g)
    P(f"| {name} | {g:.4g} | {s:.4f} | {x_at} | {pair} | {20 * s:.2f} |")
_, _, _, per = band_steps(100, BAND_LOW, BAND_HIGH, GAMMA)
P("")
P(f"Per adjacent pair, 100-point bands, fitted gamma = {GAMMA:.4f}: " + ", ".join(f"{LABELS[b]}/{LABELS[b + 1]}: {per[b]:.4f}" for b in range(len(per))) + "\n")
tbl = max(abs(E_table('standard', x, MIDS[b]) - E_table('standard', x, MIDS[b + 1])) for x in range(0, 1501) for b in range(len(MIDS) - 1))
P(f"Largest step between adjacent bands in the published three-decimal table (100-point bands, fitted parameters): {tbl}\n")

# 4. Colour
P(f"## 4 Colour inside the expectation (standard, eta = {ETA}, fitted parameters)\n")
for L in (1700, 2000, 2500):
    ew = E_exact('standard', ETA, L)
    P(f"- Equal ratings at level {L}: E(White) = {f3(ew)}, E(Black) = {f3(1 - ew)}; today's table gives .50 to each [V 1]; "
      f"expected gain per extra White today at K = 20: {20 * (ew - 0.5):+.2f} points; with colour in the table: 0.00 by construction.")
P("")

# 5. K from certainty
LEVELS_K = (1700, 2300, 2700)
P("## 5 K_i from certainty (R6): K = clip(q sigma^2 / (kappa (1 + q^2 sigma^2 v)), 10, 40), one decimal; v = 1 / (2 (2 + nu0)) in the player's own level band\n")
P(f"sigma_i is Layer 1's posterior SD of s_i,tc in latent units (D-0008, reading 5); kappa = {PARAMS['standard']['kappa']:.4f} (standard). "
  "v at the band midpoint of the player's rating: " + ", ".join(f"R = {R}: band {band_label(R)}, nu0 = {nu0('standard', band_mid(R)):.4f}, v = {v_of(R):.4f}" for R in LEVELS_K) + ".\n")
SIGMAS = (30, 40, 45, 50, 55, 60, 70, 80, 90, 100, 150)
P("| sigma_i | " + " | ".join(str(s) for s in SIGMAS) + " |")
P("|---|" + "---|" * len(SIGMAS))
for R in LEVELS_K:
    P(f"| R6 raw, R = {R} | " + " | ".join(f"{K_raw(s, R):.2f}" for s in SIGMAS) + " |")
    P(f"| K_i, R = {R} | " + " | ".join(str(K_of(s, R)) for s in SIGMAS) + " |")
P("| v0.3's D3 (kappa = 1, v = 1/4), for comparison | " + " | ".join(f"{K_D3(s):.2f}" for s in SIGMAS) + " |")
P("")
for R in LEVELS_K:
    P(f"- R = {R}: K_min binds below sigma = {sigma_for_K(K_MIN, R):.2f}; K_max binds above sigma = {sigma_for_K(K_MAX, R):.2f}; "
      f"the published-scale SD at those points is sigma / kappa = {sigma_for_K(K_MIN, R) / PARAMS['standard']['kappa']:.2f} and "
      f"{sigma_for_K(K_MAX, R) / PARAMS['standard']['kappa']:.2f}.")
P("")
P("### 5b R16: K falls with the period's games, K_i(n) = clip(q sigma^2 / (kappa (1 + n q^2 sigma^2 v)), 10, 40)\n")
P("n is the player's rated games in the time control in the rating period; K_i(n) applies to every game of the period (D-0009, reading 2). "
  "With n = 1 it is the R6 value of the table above. Published form (D-0009, reading 3): K_i(n) = clip(C / (N_i + n)), C = 1 / (kappa q v) a "
  "constant of the table in each level band and N_i = 1 / (q^2 sigma^2 v), the player's certainty in games at equal strength.\n")
NS = (1, 2, 4, 9, 20, 30)
SIG_R16 = (45, 55, 70, 90, 120, 150, 250)
for R in (1700, 2300):
    C_, _N = published_form(55, R)
    P(f"Level {R} (C = {C_:.1f}):\n")
    P("| sigma_i | N_i | " + " | ".join(f"K(n = {n})" for n in NS) + " | n x K(n) at n = 30 |")
    P("|---|---|" + "---|" * len(NS) + "---|")
    for s in SIG_R16:
        P(f"| {s} | {published_form(s, R)[1]:.1f} | " + " | ".join(str(K_n(s, R, n)) for n in NS) + f" | {30 * K_n(s, R, 30)} |")
    P("")
P("- The bound of a period's change (property P2) under R16, with rung 4 adopted: unclipped, n x K(n) < C, which is "
  + ", ".join(f"{published_form(55, R)[0]:.0f} at level {R}" for R in (1700, 2300, 2700))
  + "; clipped at K_min, n x K_min, above 700 only from 71 games in a period; clipped at K_max, 40 n. Today's bound is 700 [V 1].")
k30 = K_n(250, 1700, 30)
P(f"- A newcomer at the prior's sigma (250, latent) with 30 games in a period at level 1700: K(30) = {k30}, n x K = {30 * k30}; "
  f"today a newcomer's K = 40 is cut to 700 // 30 = {700 // 30} by K x n <= 700, n x K = {30 * (700 // 30)} [V 1].")
P(f"- Without rung 4 today's K and the 700 rule stay (every rung not adopted leaves today's rule): K_i = 26.1 and n = 40 would give "
  f"{Decimal('26.1') * 40} > 700, so {K_capped(Decimal('26.1'), 40)} for the period; that restatement for a one-decimal K applies only "
  "to rung 4 under R6, which R16 replaces.\n")

# 6. Continuous compensation
P("## 6 Continuous junior compensation (D5, R5): c_j = min(c_cap, max(0, theta~ - z sigma~ - R - tau)), z = 1.2816, tau = 25; theta~, sigma~ the same-time-control posterior on the published scale\n")
GAPS = (0, 50, 100, 150, 200, 250, 300, 400, 500, 600)
P("| sigma~_j | " + " | ".join(f"theta~ - R = {g}" for g in GAPS) + " |")
P("|---|" + "---|" * len(GAPS))
for sg in (60, 80, 100):
    P(f"| {sg} | " + " | ".join(str(comp(1500 + g, sg, 1500)) for g in GAPS) + " |")
P("")
for sg in (60, 80, 100):
    P(f"- sigma~_j = {sg}: c_j is positive once theta~ - R exceeds tau + z sigma~ = {TAU + Z_Q * sg} and reaches c_cap at {C_CAP + TAU + Z_Q * sg}; it rises one point per point in between, with no jump.")
P("- R8: in a game between two eligible juniors neither compensation enters; both expectations use published ratings.\n")

# 7. Worked example (i)
KAPPA_S = PARAMS["standard"]["kappa"]
P(f"## 7 Worked example (i): established 1900 adult (White, latent sigma 55) v 1500-listed junior (Black) whom L1 rates at theta~ = 1850 with sigma~ = 100 on the published scale (latent sigma = kappa x 100 = {KAPPA_S * 100:.1f})\n")
R_A, R_J, TH_J, SIG_A, SIG_J = 1900, 1500, 1850, 55, 100
c_J = comp(TH_J, SIG_J, R_J)
RX_J = R_J + int(c_J)
K_A, K_J = K_of(SIG_A, R_A), K_of(KAPPA_S * SIG_J, R_J)
L = (R_A + R_J) / 2
xA, xJ, xA0 = R_A - RX_J + ETA, R_J - R_A - ETA, R_A - R_J + ETA
EA, EJ, EA0 = E_table('standard', xA, L), E_table('standard', xJ, L), E_table('standard', xA0, L)
P(f"- c_J = min(300, max(0, {TH_J} - 1.2816 x {SIG_J} - {R_J} - 25)) = min(300, max(0, {comp_raw(Decimal(TH_J), Decimal(SIG_J), Decimal(R_J))})) -> {c_J}; RX_J = {RX_J}.")
P(f"- Level L = {L:.0f}, band {band_label(L)} (midpoint {band_mid(L)}), nu0 = {nu0('standard', band_mid(L)):.4f}.")
P(f"- x_A = {R_A} - {RX_J} + {ETA} = {xA}, E_A = {EA}; without compensation x = {xA0}, E_A0 = {EA0}.")
P(f"- x_J = {R_J} - {R_A} - {ETA} = {xJ}, E_J = {EJ} (J's own update uses published ratings only).")
P(f"- K_A = {K_A} (latent sigma 55 at R = {R_A}, R6; v0.3's D3 gave {K_D3(SIG_A):.1f}), K_J = {K_J} (latent sigma {KAPPA_S * SIG_J:.1f}). Today: D = 400, no cap; table 8.1.2 row 392-411: .92 / .08; K = 20 for A, 40 for J [V 1].")
P("")
P("| Result | A today: 20 x (S - .92) | J today: 40 x (S - .08) | A under L2: K_A x (S - E_A) | J under L2: K_J x (S - E_J) |")
P("|---|---|---|---|---|")
led = []
for name, SA in (("A wins", Decimal(1)), ("Draw", Decimal("0.5")), ("J wins", Decimal(0))):
    SJ = 1 - SA
    tA, tJ = 20 * (SA - Decimal("0.92")), 40 * (SJ - Decimal("0.08"))
    dA, dJ = K_A * (SA - EA), K_J * (SJ - EJ)
    P(f"| {name} | {tA:+.1f} -> {round_fide(tA):+} | {tJ:+.1f} -> {round_fide(tJ):+} | {dA:+.4f} -> {round_fide(dA):+} | {dJ:+.4f} -> {round_fide(dJ):+} |")
    led.append((name, (K_A + K_J) / 2 * (SA - EA0), (K_A - K_J) * (SA - EA0), K_A * (EA0 - EA), dA + dJ))
P("")
P("Ledger lines for the game (annex T6):\n")
P("| Result | transfer J -> A, (K_A + K_J)/2 x (S_A - E_A0) | created by unequal K, (K_A - K_J) x (S_A - E_A0) | created by compensation, K_A x (E_A0 - E_A) | sum of both changes |")
P("|---|---|---|---|---|")
for name, T, CK, CC, tot in led:
    assert tot == CK + CC
    P(f"| {name} | {T:+.4f} | {CK:+.4f} | {CC:+.4f} | {tot:+.4f} |")
P(f"\nE_A + E_J = {EA + EJ}; compensation creates K_A x (E_A0 - E_A) = {K_A * (EA0 - EA):+.4f} points in this game whatever the result.\n")

# 8. Worked example (ii)
K45 = K_of(45, 2600)
P(f"## 8 Worked example (ii): 2600 v 2100 and 2700 v 2100 (strong player White, latent sigma 45: K = {K45} at 2600 and {K_of(45, 2700)} at 2700 under R6; raw {K_raw(45, 2600):.2f} and {K_raw(45, 2700):.2f})\n")
P("Today [V 1]: K = 10. 2600 v 2100: D = 500 counted as 400 (player below 2650): row 392-411, .92. 2700 v 2100: D = 600 used in full: row 560-619, .98. "
  "Rapid and blitz [V 2]: the plain 400 cap applies to both and, with a player above 2600 and a difference of 600 or more, the game is not rated.\n")
P("| Player | Opponent | Today: D used, PD | Today: win / draw / loss | L2: x, band, E | with R17's guard: E | L2: K_i | L2 with the guard: win / draw / loss |")
P("|---|---|---|---|---|---|---|---|")
for Rs, Dused, PD in ((2600, 400, Decimal("0.92")), (2700, 600, Decimal("0.98"))):
    Lg, x = (Rs + 2100) / 2, Rs - 2100 + ETA
    E = E_table('standard', x, Lg)
    Eg = guard_E(E, Rs, 2100)
    tw, td, tl = 10 * (1 - PD), 10 * (Decimal("0.5") - PD), 10 * (0 - PD)
    P(f"| {Rs} | 2100 | {Dused}, {PD} | {tw:+.1f} / {td:+.1f} / {tl:+.1f} | {x}, {band_label(Lg)}, {E} | {Eg} | {K45} | "
      f"{K45 * (1 - Eg):+.4f} / {K45 * (Decimal('0.5') - Eg):+.4f} / {K45 * (0 - Eg):+.4f} |")
P("")
P(f"If the uncapped table were right, today's cap gives the 2600 player 10 x (.96 - .92) = {10 * (Decimal('0.96') - Decimal('0.92')):+.1f} points per game against a 2100 in expectation (row 485-517 [V 1]); "
  "with a calibrated table the expected change of any pairing is zero (P4).\n")
P(f"The 2650 cliff today v rung 2 (each beats a 2200 with White; today K = 10 [V 1]; rung 2 here uses K = {K45}):\n")
P(f"| Winner | Today: gap used, PD, gain | L2: x, band, E, gain at K = {K45} | with R17's guard: E, gain |")
P("|---|---|---|---|")
for Rw, Dused, PD in ((2649, 400, Decimal("0.92")), (2651, 451, Decimal("0.94")), (2700, 500, Decimal("0.96")), (2936, 736, Decimal("1.0"))):
    Lg, x = (Rw + 2200) / 2, Rw - 2200 + ETA
    E = E_table('standard', x, Lg)
    Eg = guard_E(E, Rw, 2200)
    P(f"| {Rw} | {Dused}, {PD}, {10 * (1 - PD):+.1f} | {x}, {band_label(Lg)}, {E}, {K45 * (1 - E):+.4f} | {Eg}, {K45 * (1 - Eg):+.4f} |")
P("")
P("R17 (D-0009, reading 4): where the gap is 400 or more and the favourite is rated 2300 or more, the favourite's expectation is the larger of "
  "the fitted value and table 8.1.2's H entry at the full gap, the underdog's one minus it. In every row above the guard binds: rung 2 with the "
  "guard reads table 8.1.2 in full for these pairings, as today's rule does for players rated 2650 or more, and the 2650 cliff disappears "
  "because the cap no longer depends on the favourite's rating.")
P("")

# 9. Monthly adjustment with soft deadband
P("## 9 Monthly adjustment with a soft deadband (D7): a_t = clip(gamma_a sign(d_t) max(0, |d_t| - d_0), -a_cap, +a_cap), one decimal\n")
DS = [Decimal(v) for v in ("-12", "-8", "-5", "-3", "-2", "-1", "0", "1", "2", "2.5", "3", "5", "6.6", "7.2", "8", "11", "12", "20")]
P("| d_t | " + " | ".join(str(d) for d in DS) + " |")
P("|---|" + "---|" * len(DS))
P("| a_t | " + " | ".join(f"{a_of(d):+.1f}" for d in DS) + " |")
P("")
m_t, mh_t = Decimal("2004.6"), Decimal("2011.8")
d_ex = mh_t - m_t
a_ex = a_of(d_ex)
games = [Decimal("-2.4090"), Decimal("5.8410"), Decimal("-8.7000")]
N_ANCHOR_MEAN = Decimal(30)        # the anchor cohort's mean games in 12 months (illustrative: T9.1's median of 30)
P(f"R3: the accrual of a_t is scaled by min(1, n_i / n_bar), n_i the player's rated games on the 12 lists up to t and n_bar the anchor cohort's mean of the same count "
  f"(illustrative n_bar = {N_ANCHOR_MEAN}): " + ", ".join(f"n_i = {n}: factor {min(Decimal(1), Decimal(n) / N_ANCHOR_MEAN):.4f}, accrual {a_of(Decimal('7.2')) * min(Decimal(1), Decimal(n) / N_ANCHOR_MEAN):+.4f} at a_t = {a_of(Decimal('7.2')):+.1f}" for n in (1, 6, 15, 30, 60)) + ".\n")
P(f"Worked example (iii): m_t = {m_t}, m_hat_t = {mh_t}, d_t = {d_ex:+}; a_t = (1/6) x ({d_ex} - {D_0}) = {(d_ex - D_0) * GAMMA_A:.4f} -> {a_ex:+.1f}. "
  f"A player with game terms {', '.join(f'{g:+.4f}' for g in games)} (sum {sum(games):+.4f}) and no carried balance: "
  f"{sum(games):+.4f} {a_ex:+.1f} = {sum(games) + a_ex:+.4f} -> {round_fide(sum(games) + a_ex):+}. "
  f"Under R3 the balance accrued in that month is a_t x min(1, n_i / n_bar): with n_i = 24 and n_bar = {N_ANCHOR_MEAN}, "
  f"{a_ex:+.1f} x {min(Decimal(1), Decimal(24) / N_ANCHOR_MEAN)} = {a_ex * min(Decimal(1), Decimal(24) / N_ANCHOR_MEAN):+.4f}, and the period change is "
  f"{sum(games) + a_ex * min(Decimal(1), Decimal(24) / N_ANCHOR_MEAN):+.4f} -> {round_fide(sum(games) + a_ex * min(Decimal(1), Decimal(24) / N_ANCHOR_MEAN)):+}.\n")


def trajectory(drift: Decimal, months: int = 61) -> list[tuple[int, Decimal, Decimal]]:
    d, rows = Decimal(0), []
    for t in range(months):
        a = a_of(d)
        rows.append((t, d, a))
        d = d - a + drift
    return rows


P("Feedback loop in a stylised pool, d_{t+1} = d_t - a_t + drift (deflation: drift +1.3 points a month, illustrative; inflation: drift -1.0):\n")
P("| month | deflation: d_t | a_t | inflation: d_t | a_t |")
P("|---|---|---|---|---|")
tr_up, tr_dn = trajectory(Decimal("1.3")), trajectory(Decimal("-1.0"))
for t in (0, 1, 2, 3, 6, 12, 24, 36, 48, 60):
    P(f"| {t} | {tr_up[t][1]:+.1f} | {tr_up[t][2]:+.1f} | {tr_dn[t][1]:+.1f} | {tr_dn[t][2]:+.1f} |")
P("")
P(f"Steady state: a_t equals the drift and the gap settles near d_0 + drift / gamma_a = {D_0} + 6 x drift ({D_0 + 6 * Decimal('1.3')} for +1.3, "
  f"{-(D_0 + 6 * Decimal('1.0'))} for -1.0). Within |d_t| <= {D_0} nothing is paid, so noise in the anchor estimate does not flip the sign every month; "
  "a_t is continuous in d_t except for its one-decimal grid.\n")
P(f"Bound on a published change (P2): |period change| <= round(700 + 12 x a_cap) = {round_fide(C_PERIOD + 12 * A_CAP)} with a full year of carried balance; "
  f"round(700 + a_cap) = {round_fide(C_PERIOD + A_CAP)} in a month without one; today's bound is 700 [V 1].\n")

# 10. Ledger identity
P("## 10 Ledger identity (annex T6) on a synthetic month: 8 listed players, 9 rated games, one compensated junior, one game against an unrated player, one one-sided game under §8.2.4, one floor exit, one newcomer, one re-entry, one refused newcomer and one refused re-entry, a_t = +0.9\n")
players = {  # id: (R, latent sigma, theta~ for an eligible junior or None); P8 received its first rating on list t
    "P1": (1900, 55, None), "P2": (1500, 121.2, 1850), "P3": (2050, 50, None), "P4": (1750, 70, None),
    "P5": (2300, 45, None), "P6": (1600, 120, None), "P7": (1405, 70, None), "P8": (1580, 90, None),
}
games_m = [  # (White, Black, White's score, kind); kind "both" | "unrated" (U) | "one-sided:<id>" (§8.2.4 [V 1])
    ("P1", "P2", Decimal("0.5"), "both"), ("P3", "P1", Decimal(1), "both"), ("P2", "P4", Decimal(1), "both"),
    ("P5", "P3", Decimal("0.5"), "both"), ("P4", "P6", Decimal(0), "both"), ("P6", "P2", Decimal(0), "both"),
    ("P5", "P1", Decimal(1), "both"), ("P7", "P4", Decimal(0), "both"), ("P6", "P7", Decimal(1), "both"),
    ("P3", "U", Decimal(1), "unrated"), ("P3", "P8", Decimal("0.5"), "one-sided:P8"),
]
A_T = a_of(d_ex)
SEED_N1 = Decimal("1650.3")         # newcomer N1: theta~ (L1 estimate on the published scale)
SEED_N2 = Decimal("1287.6")         # newcomer N2: theta~ below the floor
REENTRY = {"Q1": Decimal("1452.4"), "Q2": Decimal("1381.2")}   # theta~ of two former floor exits who re-qualify


def RX(p: str) -> int:
    R, sg, th = players[p]
    return R + int(comp(th, Decimal(repr(sg)) / Decimal(repr(KAPPA_S)), R)) if th is not None else R


def counts_for(pid: str, g: tuple) -> bool:
    w, b, _, kind = g
    if pid not in (w, b):
        return False
    if kind == "unrated":
        return False
    if kind.startswith("one-sided:"):
        return kind.split(":")[1] == pid
    return True


nn = {p: sum(1 for g in games_m if counts_for(p, g)) for p in players}
Kc = {p: K_n(v[1], v[0], nn[p]) for p, v in players.items()}          # R16: K for the period's n games
tot = {p: Decimal(0) for p in players}
sumCK = sumCC = sum1 = Decimal(0)
P("| game | White | Black | S_W | band | x_W | E_W | x_B | E_B | dR_W | dR_B | created by unequal K | created by compensation | one-sided |")
P("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
for n_, (w, b, Sw, kind) in enumerate(games_m, 1):
    if kind == "unrated":
        P(f"| {n_} | {w} ({players[w][0]}) | U (unrated) | {Sw} | — | — | — | — | — | 0 (not rated) | — | 0 | 0 | 0 |")
        continue
    Rw, Rb = players[w][0], players[b][0]
    Lg = (Rw + Rb) / 2
    xw, xb, xw0 = Rw - RX(b) + ETA, Rb - RX(w) - ETA, Rw - Rb + ETA
    Ew, Eb, Ew0 = E_table('standard', xw, Lg), E_table('standard', xb, Lg), E_table('standard', xw0, Lg)
    if kind.startswith("one-sided:"):
        side = kind.split(":")[1]
        d1 = Kc[side] * ((Sw if side == w else 1 - Sw) - (Ew if side == w else Eb))
        tot[side] += d1
        sum1 += d1
        dws = f"{d1:+.4f}" if side == w else "0 (counts the newly rated player as unrated)"
        dbs = f"{d1:+.4f}" if side == b else "0 (counts the newly rated player as unrated)"
        P(f"| {n_} | {w} ({Rw}) | {b} ({Rb}) | {Sw} | {band_label(Lg)} | {xw} | {Ew} | {xb} | {Eb} | {dws} | {dbs} | 0 | 0 | {d1:+.4f} |")
        continue
    dw, db = Kc[w] * (Sw - Ew), Kc[b] * ((1 - Sw) - Eb)
    CK = (Kc[w] - Kc[b]) * (Sw - Ew0) + 0          # + 0 normalises a signed zero
    CC = Kc[w] * (Ew0 - Ew) + Kc[b] * ((1 - Ew0) - Eb) + 0
    assert dw + db - CK - CC == 0
    tot[w] += dw
    tot[b] += db
    sumCK += CK
    sumCC += CC
    P(f"| {n_} | {w} ({Rw}) | {b} ({Rb}) | {Sw} | {band_label(Lg)} | {xw} | {Ew} | {xb} | {Eb} | {dw:+.4f} | {db:+.4f} | {CK:+.4f} | {CC:+.4f} | 0 |")
P("")
P("| player | R(t) | sigma | K_i(n) (R16) | n | RX | sum of game terms | + a_t | rounded change | R(t+1) | rounding residual | status |")
P("|---|---|---|---|---|---|---|---|---|---|---|---|")
sum_res = Decimal(0)
list_t = sum(v[0] for v in players.values())
list_t1 = Decimal(0)
exits = Decimal(0)
for p in players:
    pre = tot[p] + A_T
    r = round_fide(pre)
    sum_res += r - pre
    post = players[p][0] + r
    if post < 1400:
        status = f"below 1400: shown as unrated (7.2.1 [V 1]); exit booked at R+ = {post}"
        exits += post
    else:
        status = "listed" if p != "P8" else "listed (first rated on list t; its late-rated game is one-sided, §8.2.4 [V 1])"
        list_t1 += post
    P(f"| {p} | {players[p][0]} | {players[p][1]} | {Kc[p]} | {nn[p]} | {RX(p)} | {tot[p]:+.4f} | {pre:+.4f} | {int(r):+d} | {post} | {r - pre:+.4f} | {status} |")
entering = Decimal(0)
for q, th, what in (("N1", SEED_N1, "newcomer"), ("N2", SEED_N2, "newcomer"),
                    ("Q1", REENTRY["Q1"], "former floor exit re-qualifies"), ("Q2", REENTRY["Q2"], "former floor exit re-qualifies")):
    seed = min(round_fide(th), Decimal(2200))
    if round_fide(th) >= 1400:
        entering += seed
        P(f"| {q} | — | — | 40.0 | — | — | — | — | — | {seed} | — | {what}: theta~ = {th}, round = {round_fide(th)} >= 1400, published at {seed} |")
    else:
        P(f"| {q} | — | — | — | — | — | — | — | — | — | — | {what}: theta~ = {th}, round = {round_fide(th)} < 1400, not published (stays unrated; no ledger line) |")
list_t1 += entering
P("")
lhs = list_t1 - list_t
rhs = sumCK + sumCC + sum1 + A_T * len(players) + sum_res + entering - exits
P(f"Left side: list total after {list_t1} - before {list_t} = {lhs:+}.")
P(f"Right side: unequal K {sumCK:+.4f} + compensation {sumCC:+.4f} + one-sided (§8.2.4) {sum1:+.4f} + adjustments posted {A_T * len(players):+.1f} ({len(players)} x {A_T}) "
  f"+ rounding {sum_res:+.4f} + entering {entering} - exits at post-update rating {exits} = {rhs:+.4f}.")
P(f"Identity closes exactly: {lhs == rhs}. Without the one-sided line the residual would be {sum1:+.4f}; booking the exit at R(t) = {players['P7'][0]} instead of R+ = {exits} would leave {players['P7'][0] - exits:+} points.\n")
assert lhs == rhs

# 10b. Figures used by the review fixes (REDTEAM_v0_3) and the rulings R1-R14 (D-0008)
P("## 10b Further figures for the review fixes\n")
P(f"- Table entry at x = 500 in band 2300-2399 (midpoint 2350): {E_table('standard', 500, 2350)}; the function at L = 2300 gives {f3(E_exact('standard', 500, 2300))}.")
for kk, Rk in (("14.1", 1900), ("27.1", 1500)):
    k = float(kk)
    lo, hi, mid = sigma_for_K(k - 0.05, Rk), sigma_for_K(k + 0.05, Rk), sigma_for_K(k, Rk)
    P(f"- R4 disclosure (R6): K_i = {kk} published to one decimal at R = {Rk} implies latent sigma_i between {lo:.2f} and {hi:.2f} (published-scale "
      f"{lo / KAPPA_S:.2f} to {hi / KAPPA_S:.2f}); a compensated junior with K_j = {kk} and 0 < c_j < 300 then has theta~_j = RX_j + 25 + 1.2816 x {mid / KAPPA_S:.2f} "
      f"= RX_j + {25 + 1.2816 * mid / KAPPA_S:.1f} (to within the rounding of c_j).")
for s_, Rk in ((55.0, 1900), (121.2, 1500)):
    C_, N_ = published_form(s_, Rk)
    P(f"- R16's published form at R = {Rk}, latent sigma {s_}: C = {C_:.1f}, N_i = {N_:.1f}; the list prints N_i to one decimal, from which "
      f"sigma_i = 1 / (q sqrt(N_i v)) = {1 / (Q * math.sqrt(N_ * v_of(Rk))):.1f}: the same disclosure as K_i under R6 (R4).")
sig_ret = math.sqrt(55 ** 2 + 36 * 12 ** 2)
P(f"- A player at latent sigma 55 and R = 1900 who is inactive for 36 months with a process SD of 12 points a month (T7.2, illustrative) returns at sigma = sqrt(55^2 + 36 x 12^2) = {sig_ret:.1f}, "
  f"K(1) = {K_n(sig_ret, 1900, 1)} and K(4) = {K_n(sig_ret, 1900, 4)} (from {K_n(55, 1900, 1)} and {K_n(55, 1900, 4)}).")


def steady_k(games: int, level: float, sig_theta: float = 12.0) -> tuple[float, Decimal]:
    """Steady-state latent posterior SD after a month of `games` games at x = 0, process SD sig_theta (latent units).
    In latent units (slope 1) the Davidson information per game about the gap at x = 0 is q^2 v, v = 1/(2(2 + nu0)),
    because dE/dz and the score variance at z = 0 both equal v."""
    info = Q * Q * v_of(level)
    v = 100.0 ** 2
    for _ in range(2000):
        v = 1.0 / (1.0 / (v + sig_theta ** 2) + games * info)
    pre = math.sqrt(v + sig_theta ** 2)                    # the certainty for the next period (R16 uses it with n = games)
    return math.sqrt(v), K_n(pre, level, games)


P("- Steady-state K from activity under R16 (Davidson information at equal strength in latent units; the same number of games every month; "
  "K_i(n) for that month's n games from the certainty before them), at two latent process SDs:")
P("")
for sig_th, label in ((12.0, "illustrative process SD 12 (T7.2)"), (24.0, "process SD 24, as fitted on history (c_theta = 2.0 times 12 at ages 25-45; SPEC-L1 3.7, analysis/OUTPUT_L1_history.md)")):
    P(f"  {label}:")
    P("")
    P("| standard games a month | " + " | ".join(str(g) for g in (1, 2, 3, 4, 5, 8)) + " |")
    P("|---|" + "---|" * 6)
    for lvl in (1700, 2300, 2700):
        cells = []
        for g in (1, 2, 3, 4, 5, 8):
            s, k = steady_k(g, lvl, sig_th)
            cells.append(f"sigma {s:.1f}, K {k}")
        P(f"| level {lvl} | " + " | ".join(cells) + " |")
    P("")


S0_LATENT = 250.0      # s_0, the newcomer's prior SD (T7.2, PROVISIONAL)
P("- Seed gate (T4.7, sigma~ <= 120): a newcomer's published-scale SD after n games against opponents of equal strength in one month, from the "
  f"prior s_0 = {S0_LATENT:.0f} (latent), with the same-level information q^2 v per game and the opponents taken as known: " +
  "; ".join(f"level {lvl}: " + ", ".join(f"n = {n}: {math.sqrt(1.0 / (1.0 / S0_LATENT ** 2 + n * Q * Q * v_of(lvl))) / KAPPA_S:.1f}" for n in (5, 6, 8, 10))
            for lvl in (1500, 1800)) + ".")
P("")


def inverse_gap(pval: float, level: float) -> int:
    """Smallest whole-number gap x >= 0 at which the fitted table (band midpoint `level`) reaches pval."""
    x = 0
    while E_exact('standard', x, level) < pval and x < 2000:
        x += 1
    return x


P("- Table 8.1.1 against the PROVISIONAL-FITTED rung-2 table (rung 2 alone keeps 8.1.1 for initial ratings, §8.2.3 [V 1]): the gap at which the table reaches a score p, at three band midpoints:")
P("")
P("| p | 8.1.1 dp [V 1] | band midpoint 1650 | 2050 | 2450 |")
P("|---|---|---|---|---|")
for pval, dp in ((0.75, 193), (0.92, 401)):
    P(f"| {pval} | {dp} | " + " | ".join(str(inverse_gap(pval, m)) for m in (1650, 2050, 2450)) + " |")
P("")
P("- R8: two eligible juniors at equal published ratings use published ratings on both sides, so their expectations sum to one and the game creates no points. "
  "For the record, v0.3's rule (each one's compensation in the other's expectation) would have created:")
for cc in (100, 300):
    Lg = 1550
    x1 = -cc + 0                                         # two eligible juniors at equal published ratings, each compensated by cc
    e_w = E_table('standard', 0 - cc + ETA, Lg)         # White's expectation against the opponent's RX
    e_b = E_table('standard', 0 - cc - ETA, Lg)
    created = Decimal(40) * (1 - e_w - e_b)
    P(f"  - (v0.3, superseded) two eligible juniors at equal published ratings (band 1500-1599), each with c = {cc}, K = 40: expectations {e_w} (White) and {e_b} (Black), sum {e_w + e_b}; points created per game {created:+.1f}, whatever the result.")
for R in (1400, 1500, 1600):
    P(f"- R2: a correctly rated player at R = {R} whose latent distance from the anchor mean is kappa times the published one (kappa = {KAPPA_S:.4f}, anchor mean 2041.3, T7.2 illustrative) "
      f"has theta~ - R = 0 under R2's theta~ = m_t + (s^ - m^_t) / kappa; v0.3's theta~ = s^ - d_t would have shown (kappa - 1)(R - m_t) = {(KAPPA_S - 1) * (R - 2041.3):+.0f} points.")
P(f"- Accrual against activity at a_t = +1.3 a month (R3, illustrative n_bar = {N_ANCHOR_MEAN}): a player active under §7.2.2 with one game a year accrues {12 * 1.3 / float(N_ANCHOR_MEAN):.2f} points a year "
  f"(v0.3, without R3: {12 * 1.3:.1f}); with {int(N_ANCHOR_MEAN)} or more games a year, {12 * 1.3:.1f}. A drift of 1.3 points a month spread over {int(N_ANCHOR_MEAN)} games a year is {12 * 1.3 / float(N_ANCHOR_MEAN):.2f} a game, so the accrual now matches the drain per game up to the anchor's mean activity.")
P("")

# 11. Layer 0 test vector
P("## 11 Today's initial rating for the Appendix E.2 case of v0.1 (a Layer 0 test vector)\n")
opp = [1550, 1600, 1650, 1580, 1620]
Ra = Fraction(sum(opp) + 3600, 7)
P(f"- Ra = ({sum(opp)} + 2 x 1800)/7 = {float(Ra):.2f}; p = (3 + 1)/7 = {float(Fraction(4, 7)):.4f} -> .57; dp(.57) = 50 [V 1]; Ru = {float(Ra) + 50:.2f} -> 1707. "
  "The rounding of p before the lookup is settled in SPEC-L0.\n")

# 12. R1: the spread ratio and its review threshold
import json  # noqa: E402
L1 = json.loads((Path(__file__).resolve().parents[1] / "analysis" / "aggregates" / "L1_history.json").read_text(encoding="utf-8"))
E9 = json.loads((Path(__file__).resolve().parents[1] / "analysis" / "aggregates" / "E9_simulator.json").read_text(encoding="utf-8"))
CAL = E9["r1_calibration"]
R1_THRESHOLD = CAL["calibrated"]     # PROVISIONAL: calibrated in the simulator (R20; D-0009 reading 6; E9)
P("## 12 R1: the monthly spread ratio and the QC-review threshold (R1 as revised by R19 and R20)\n")
P("The spread ratio is the SD of published ratings divided by the SD of Layer 1's estimates for active adults (aged 25-45, rated, a game of the "
  "fit in the 12 months up to the month), measured on history in `analysis/OUTPUT_L1_history.md` (aggregate `analysis/aggregates/L1_history.json`); "
  "the corrected ratio adds the mean posterior variance to the latent variance, so that it does not move with activity alone. In v0.4, if the measure "
  "moved beyond a published threshold two years running, the QC reviewed (R1, D-0008); R19 (D-0009) makes the trigger the cumulative change since "
  "the last review. No automatic correction either way.\n")
P("| time control | SD of the month-to-month change (ratio) | largest 12-month change since 2024-03 (ratio) | calendar-year means, corrected ratio | year-on-year changes, corrected ratio |")
P("|---|---|---|---|---|")
for tc, rows in L1["spread_series"].items():
    r = [x["ratio"] for x in rows]
    dif = [b - a for a, b in zip(r, r[1:])]
    mean_d = sum(dif) / len(dif)
    sd = math.sqrt(sum((d - mean_d) ** 2 for d in dif) / len(dif))
    d12 = [abs(r[k + 12] - r[k]) for k in range(len(r) - 12) if rows[k]["month"] >= "2024-03"]
    years = sorted({x["month"][:4] for x in rows})
    means = {y: sum(x["ratio_noise_corrected"] for x in rows if x["month"][:4] == y) / sum(1 for x in rows if x["month"][:4] == y) for y in years}
    yoy = [(f"{a}->{b}", means[b] - means[a]) for a, b in zip(years, years[1:])]
    P(f"| {tc} | {sd:.4f} | {max(d12):.3f} | " + ", ".join(f"{y}: {means[y]:.3f}" for y in years) + " | "
      + ", ".join(f"{k} {v:+.3f}" for k, v in yoy) + " |")
P("")
kap = PARAMS["standard"]["kappa"]
cap = 0.05
P(f"A ratchet held to kappa's annual cap of {cap} moves the ratio by about ratio x cap / kappa = 0.747 x {cap} / {kap:.3f} = {0.747 * cap / kap:.3f} a year "
  "in standard (the ratio varies roughly as 1/kappa). R19 replaces v0.4's year-on-year rule: the QC reviews when the trailing twelve-month mean of the "
  "noise-corrected ratio differs from its value at the last QC review (at adoption, the mean of the first twelve months of operation) by more than "
  "theta_R1, in either direction; a review resets the reference (D-0009, reading 5). A cumulative rule catches a ratchet however slowly it runs.\n")
th = CAL["thresholds"]
P(f"theta_R1 calibrated in the simulator ({CAL['runs']} paired runs, E9; D-0009, reading 6): the smallest threshold whose false-alarm rate from noise "
  f"alone over ten simulated years is at most 5 % is {R1_THRESHOLD} (PROVISIONAL); a ratchet at kappa's cap trips it after a median of "
  f"{th[str(R1_THRESHOLD)]['ratchet_median_months']} months. R20's earlier PROVISIONAL 0.02: {100 * th['0.02']['noise_false_alarm_share']:.0f} % false "
  f"alarms from noise, the ratchet tripping it after {th['0.02']['ratchet_median_months']} months. On history since the March 2024 reset the "
  "year-on-year changes of the corrected ratio's calendar-year means are within ±0.02 (table above).\n")

print("\n".join(out))
