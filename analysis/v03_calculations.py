#!/usr/bin/env python3
"""Calculations for proposal v0.3, technical annex v0.3 and the brief v0.3.

Python standard library only. Deterministic. NOT the rating engine: these are
hand-check-scale calculations, and their output is the source of every number
in docs/proposal/ELO-PROPOSAL_v0_3.md, docs/proposal/ELO-TECHNICAL-ANNEX_v0_3.md
and docs/proposal/ELO-BRIEF_v0_3.md.
Run:  python3 analysis/v03_calculations.py > analysis/OUTPUT_v0_3.md

Every parameter value below is PROVISIONAL (annex T1 and T7). The architect's
decisions D1-D18 are recorded in docs/decisions/D-0005_architect-decisions-v0.3.md.
"""
from __future__ import annotations

import math
from decimal import ROUND_DOWN, ROUND_HALF_UP, Decimal
from fractions import Fraction

Q = math.log(10.0) / 400.0          # q = ln 10 / 400

# ---------------------------------------------------------------- parameters (PROVISIONAL)
PARAMS = {
    "standard": {"kappa": 1.00, "eta": 35, "alpha": -0.50, "beta": 0.55, "gamma": 0.5},
    "rapid":    {"kappa": 1.00, "eta": 25, "alpha": -0.70, "beta": 0.50, "gamma": 0.5},
    "blitz":    {"kappa": 1.00, "eta": 25, "alpha": -0.90, "beta": 0.45, "gamma": 0.5},
}
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


def K_raw(sigma: float) -> float:
    return Q * sigma * sigma / (1.0 + Q * Q * sigma * sigma / 4.0)


def K_of(sigma: float) -> Decimal:
    """D3: K = clip(q sigma^2 / (1 + q^2 sigma^2 / 4), K_min, K_max), one decimal."""
    k = min(K_MAX, max(K_MIN, K_raw(sigma)))
    return Decimal(k).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)


def K_capped(K: Decimal, n: int) -> Decimal:
    """Per-period cap: if K*n > 700, K becomes floor(7000/n)/10."""
    if K * n > C_PERIOD:
        return (Decimal(10 * C_PERIOD) / Decimal(n)).quantize(Decimal("1"), rounding=ROUND_DOWN) / Decimal(10)
    return K


def round_fide(v: Decimal) -> Decimal:
    """Nearest whole number, 0.5 away from zero (FIDE 8.3.4)."""
    return v.quantize(Decimal("1"), rounding=ROUND_HALF_UP)


def comp_raw(theta_tilde: Decimal, sigma: Decimal, R: Decimal) -> Decimal:
    return theta_tilde - Z_Q * sigma - R - TAU


def comp(theta_tilde, sigma, R) -> Decimal:
    """D5: c_j = min(c_cap, max(0, theta~ - z sigma - R - tau)), on the whole-number grid."""
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

P("# OUTPUT of analysis/v03_calculations.py (all parameters PROVISIONAL)\n")
P("Generated deterministically by the script; the source of every number in the proposal v0.3, the technical annex v0.3 and the brief v0.3.\n")

# 0. Parameters
P("## 0 Parameters used (PROVISIONAL)\n")
P("| tc | kappa | eta | alpha | beta | gamma |")
P("|---|---|---|---|---|---|")
for tc, p in PARAMS.items():
    P(f"| {tc} | {p['kappa']:.2f} | {p['eta']} | {p['alpha']:.2f} | {p['beta']:.2f} | {p['gamma']:.2f} |")
P("")
P(f"q = ln 10 / 400 = {Q:.7f}; K_min = {K_MIN:.0f}, K_max = {K_MAX:.0f}; C_period = {C_PERIOD}; a_cap = {A_CAP}, gamma_a = 1/6, d_0 = {D_0}; "
  f"tau = {TAU}, c_cap = {C_CAP}, z = {Z_Q}; level bands of {BAND_WIDTH} points from {BAND_LOW} to {BAND_HIGH}, open below and above "
  f"(midpoints {BAND_LOW - BAND_WIDTH // 2} and {BAND_HIGH + BAND_WIDTH // 2}).\n")

# 1. Table
MIDS, LABELS = mids_of(), labels_of()
P("## 1 Expected-score table, standard (D1 draw decay gamma = 1/2, D6 bands of 100 points; E to three decimals)\n")
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
P("## 2 The forecast tail at level 2300 (standard alpha, beta of v0.2) against the 5/6-gap rule\n")
P(f"nu0 at L = 2300: {nu0('standard', 2300):.4f}. The 5/6-gap rule is logistic Elo on five sixths of the gap, 1/(1 + 10^(-(5x/6)/400)) [R 44]; "
  "today's table 8.1.2 [V 1] is shown for reference.\n")
P("| gap x | D1 (gamma = 1/2): P_W / P_D / P_L | D1: E | v0.2 (gamma = 0): P_D | v0.2: E | 5/6-gap rule | table 8.1.2 |")
P("|---|---|---|---|---|---|---|")
for x in (200, 400, 500, 700):
    pw, pd, pl = probs('standard', x, 2300)
    _, pd0, _ = probs('standard', x, 2300, gamma=0.0)
    P(f"| {x} | {pw:.3f} / {pd:.3f} / {pl:.3f} | {f3(E_exact('standard', x, 2300))} | {pd0:.3f} | "
      f"{f3(E_exact('standard', x, 2300, gamma=0.0))} | {f3(logistic(5 * x / 6))} | {table_812_H(x)} |")
P("")
for x in (400, 800, 1200):
    pw, pd, pl = probs('standard', x, 2300)
    P(f"- x = {x}: P_D / P_L = {pd / pl:.4f} with gamma = 1/2 (equals nu0: draws fade as fast as losses); "
      f"with gamma = 0 it is {probs('standard', x, 2300, gamma=0.0)[1] / probs('standard', x, 2300, gamma=0.0)[2]:.4f}.")
P("")

# 3. Checks
P("## 3 Numerical checks of the D1 form (standard parameters)\n")
grid = range(-1500, 1501)
for g in (0.0, 0.25, 0.5):
    sym = max(abs(E_exact('standard', x, m, gamma=g) + E_exact('standard', -x, m, gamma=g) - 1.0) for x in grid for m in MIDS)
    mono = min(E_exact('standard', x + 1, m, gamma=g) - E_exact('standard', x, m, gamma=g) for x in range(-1500, 1500) for m in MIDS)
    P(f"- gamma = {g}: symmetry max |E(x) + E(-x) - 1| over x in [-1500, 1500], all bands = {sym:.1e}; "
      f"monotonicity min E(x+1) - E(x) = {mono:.2e} (> 0)")
lg = max(abs(E_exact('standard', x, 2000, gamma=0.5, kappa=1.0, nu0_override=0.0) - logistic(x)) for x in grid)
P(f"- Logistic special case (nu0 = 0, kappa = 1, any gamma): max |E(x) - 1/(1 + 10^(-x/400))| = {lg:.1e}")
h = 1e-3
for L in (1700, 2300, 2700):
    num = (E_exact('standard', h, L) - E_exact('standard', -h, L)) / (2 * h)
    ana = Q / (2 * (2 + nu0('standard', L)))
    P(f"- Slope at x = 0, level {L}: numerical {num:.6e}, formula kappa q / (2 (2 + nu0)) = {ana:.6e}; local logistic scale 200 (2 + nu0) / kappa = {200 * (2 + nu0('standard', L)):.1f}")
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
for width, low, high, g, name in ((200, 1600, 2800, 0.0, "200 (v0.2)"), (200, 1600, 2800, 0.5, "200"), (100, BAND_LOW, BAND_HIGH, 0.5, "100 (v0.3)")):
    s, x_at, pair, _ = band_steps(width, low, high, g)
    P(f"| {name} | {g} | {s:.4f} | {x_at} | {pair} | {20 * s:.2f} |")
_, _, _, per = band_steps(100, BAND_LOW, BAND_HIGH, 0.5)
P("")
P("Per adjacent pair, 100-point bands, gamma = 1/2: " + ", ".join(f"{LABELS[b]}/{LABELS[b + 1]}: {per[b]:.4f}" for b in range(len(per))) + "\n")
tbl = max(abs(E_table('standard', x, MIDS[b]) - E_table('standard', x, MIDS[b + 1])) for x in range(0, 1501) for b in range(len(MIDS) - 1))
P(f"Largest step between adjacent bands in the published three-decimal table (100-point bands, gamma = 1/2): {tbl}\n")

# 4. Colour
P("## 4 Colour inside the expectation (standard, eta = 35, gamma = 1/2)\n")
for L in (1700, 2000, 2500):
    ew = E_exact('standard', 35, L)
    P(f"- Equal ratings at level {L}: E(White) = {f3(ew)}, E(Black) = {f3(1 - ew)}; today's table gives .50 to each [V 1]; "
      f"expected gain per extra White today at K = 20: {20 * (ew - 0.5):+.2f} points; with colour in the table: 0.00 by construction.")
P("")

# 5. K from certainty
P("## 5 K_i from certainty (D3): K = clip(q sigma^2 / (1 + q^2 sigma^2 / 4), 10, 40), one decimal\n")
SIGMAS = (30, 40, 45, 50, 55, 60, 70, 80, 90, 100, 150)
P("| sigma_i | " + " | ".join(str(s) for s in SIGMAS) + " |")
P("|---|" + "---|" * len(SIGMAS))
P("| q sigma^2 / (1 + q^2 sigma^2 / 4) | " + " | ".join(f"{K_raw(s):.2f}" for s in SIGMAS) + " |")
P("| K_i (clipped, one decimal) | " + " | ".join(str(K_of(s)) for s in SIGMAS) + " |")
P("")
s_min = math.sqrt(K_MIN / (Q - K_MIN * Q * Q / 4.0))
s_max = math.sqrt(K_MAX / (Q - K_MAX * Q * Q / 4.0))
P(f"K_min binds below sigma = {s_min:.2f}; K_max binds above sigma = {s_max:.2f}.\n")
P(f"Per-period cap example: K_i = 26.1 and n = 40 gives {Decimal('26.1') * 40} > 700, so K_i = {K_capped(Decimal('26.1'), 40)} for the period; "
  f"K_i = 16.5 and n = 40 gives {Decimal('16.5') * 40} (no cap).\n")

# 6. Continuous compensation
P("## 6 Continuous junior compensation (D5): c_j = min(c_cap, max(0, theta~ - z sigma - R - tau)), z = 1.2816, tau = 25\n")
GAPS = (0, 50, 100, 150, 200, 250, 300, 400, 500, 600)
P("| sigma_j | " + " | ".join(f"theta~ - R = {g}" for g in GAPS) + " |")
P("|---|" + "---|" * len(GAPS))
for sg in (60, 80, 100):
    P(f"| {sg} | " + " | ".join(str(comp(1500 + g, sg, 1500)) for g in GAPS) + " |")
P("")
for sg in (60, 80, 100):
    P(f"- sigma_j = {sg}: c_j is positive once theta~ - R exceeds tau + z sigma = {TAU + Z_Q * sg} and reaches c_cap at {C_CAP + TAU + Z_Q * sg}; it rises one point per point in between, with no jump.")
P("")

# 7. Worked example (i)
P("## 7 Worked example (i): established 1900 adult (White, sigma 55) v 1500-listed junior (Black, sigma 100) whom L1 rates at 1850 on the published scale\n")
R_A, R_J, TH_J, SIG_A, SIG_J = 1900, 1500, 1850, 55, 100
c_J = comp(TH_J, SIG_J, R_J)
RX_J = R_J + int(c_J)
K_A, K_J = K_of(SIG_A), K_of(SIG_J)
L = (R_A + R_J) / 2
xA, xJ, xA0 = R_A - RX_J + 35, R_J - R_A - 35, R_A - R_J + 35
EA, EJ, EA0 = E_table('standard', xA, L), E_table('standard', xJ, L), E_table('standard', xA0, L)
P(f"- c_J = min(300, max(0, {TH_J} - 1.2816 x {SIG_J} - {R_J} - 25)) = min(300, max(0, {comp_raw(Decimal(TH_J), Decimal(SIG_J), Decimal(R_J))})) -> {c_J}; RX_J = {RX_J}.")
P(f"- Level L = {L:.0f}, band {band_label(L)} (midpoint {band_mid(L)}), nu0 = {nu0('standard', band_mid(L)):.4f}.")
P(f"- x_A = {R_A} - {RX_J} + 35 = {xA}, E_A = {EA}; without compensation x = {xA0}, E_A0 = {EA0}.")
P(f"- x_J = {R_J} - {R_A} - 35 = {xJ}, E_J = {EJ} (J's own update uses published ratings only).")
P(f"- K_A = {K_A} (sigma 55), K_J = {K_J} (sigma 100). Today: D = 400, no cap; table 8.1.2 row 392-411: .92 / .08; K = 20 for A, 40 for J [V 1].")
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
K45 = K_of(45)
P(f"## 8 Worked example (ii): 2600 v 2100 and 2700 v 2100 (strong player White, sigma 45 so K = {K45})\n")
P("Today [V 1]: K = 10. 2600 v 2100: D = 500 counted as 400 (player below 2650): row 392-411, .92. 2700 v 2100: D = 600 used in full: row 560-619, .98. "
  "Rapid and blitz [V 2]: the plain 400 cap applies to both and, with a player above 2600 and a difference of 600 or more, the game is not rated.\n")
P("| Player | Opponent | Today: D used, PD | Today: win / draw / loss | L2: x, band, E | L2: K_i | L2: win / draw / loss |")
P("|---|---|---|---|---|---|---|")
for Rs, Dused, PD in ((2600, 400, Decimal("0.92")), (2700, 600, Decimal("0.98"))):
    Lg, x = (Rs + 2100) / 2, Rs - 2100 + 35
    E = E_table('standard', x, Lg)
    tw, td, tl = 10 * (1 - PD), 10 * (Decimal("0.5") - PD), 10 * (0 - PD)
    P(f"| {Rs} | 2100 | {Dused}, {PD} | {tw:+.1f} / {td:+.1f} / {tl:+.1f} | {x}, {band_label(Lg)}, {E} | {K45} | "
      f"{K45 * (1 - E):+.4f} / {K45 * (Decimal('0.5') - E):+.4f} / {K45 * (0 - E):+.4f} |")
P("")
P(f"If the uncapped table were right, today's cap gives the 2600 player 10 x (.96 - .92) = {10 * (Decimal('0.96') - Decimal('0.92')):+.1f} points per game against a 2100 in expectation (row 485-517 [V 1]); "
  "with a calibrated table the expected change of any pairing is zero (P4).\n")
P(f"The 2650 cliff today v rung 2 (each beats a 2200 with White; today K = 10 [V 1]; rung 2 here uses K = {K45}):\n")
P(f"| Winner | Today: gap used, PD, gain | L2: x, band, E, gain at K = {K45} |")
P("|---|---|---|")
for Rw, Dused, PD in ((2649, 400, Decimal("0.92")), (2651, 451, Decimal("0.94")), (2700, 500, Decimal("0.96")), (2936, 736, Decimal("1.0"))):
    Lg, x = (Rw + 2200) / 2, Rw - 2200 + 35
    E = E_table('standard', x, Lg)
    P(f"| {Rw} | {Dused}, {PD}, {10 * (1 - PD):+.1f} | {x}, {band_label(Lg)}, {E}, {K45 * (1 - E):+.4f} |")
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
P(f"Worked example (iii): m_t = {m_t}, m_hat_t = {mh_t}, d_t = {d_ex:+}; a_t = (1/6) x ({d_ex} - {D_0}) = {(d_ex - D_0) * GAMMA_A:.4f} -> {a_ex:+.1f}. "
  f"A player with game terms {', '.join(f'{g:+.4f}' for g in games)} (sum {sum(games):+.4f}) and no carried balance: "
  f"{sum(games):+.4f} {a_ex:+.1f} = {sum(games) + a_ex:+.4f} -> {round_fide(sum(games) + a_ex):+}.\n")


def trajectory(drift: Decimal, months: int = 61) -> list[tuple[int, Decimal, Decimal]]:
    d, rows = Decimal(0), []
    for t in range(months):
        a = a_of(d)
        rows.append((t, d, a))
        d = d - a + drift
    return rows


P("Feedback loop in a stylised pool, d_{t+1} = d_t - a_t + drift (deflation: drift +1.3 points a month, the research report's post-reform figure being about -16 a year [R 5]; inflation: drift -1.0):\n")
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
players = {  # id: (R, sigma, theta~ for an eligible junior or None); P8 received its first rating on list t
    "P1": (1900, 55, None), "P2": (1500, 100, 1850), "P3": (2050, 50, None), "P4": (1750, 70, None),
    "P5": (2300, 45, None), "P6": (1600, 120, None), "P7": (1405, 60, None), "P8": (1580, 90, None),
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
    return R + int(comp(th, sg, R)) if th is not None else R


def counts_for(pid: str, g: tuple) -> bool:
    w, b, _, kind = g
    if pid not in (w, b):
        return False
    if kind == "unrated":
        return False
    if kind.startswith("one-sided:"):
        return kind.split(":")[1] == pid
    return True


K = {p: K_of(v[1]) for p, v in players.items()}
nn = {p: sum(1 for g in games_m if counts_for(p, g)) for p in players}
Kc = {p: K_capped(K[p], nn[p]) for p in players}
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
    xw, xb, xw0 = Rw - RX(b) + 35, Rb - RX(w) - 35, Rw - Rb + 35
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
P("| player | R(t) | sigma | K_i | n | RX | sum of game terms | + a_t | rounded change | R(t+1) | rounding residual | status |")
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

# 10b. Figures used by the v0.3 review fixes (REDTEAM_v0_3)
P("## 10b Further figures for the review fixes\n")
P(f"- Table entry at x = 500 in band 2300-2399 (midpoint 2350): {E_table('standard', 500, 2350)}; the function at L = 2300 gives {f3(E_exact('standard', 500, 2300))}.")
for kk in ("17.0", "27.1"):
    k = float(kk)
    lo = math.sqrt((k - 0.05) / (Q - (k - 0.05) * Q * Q / 4))
    hi = math.sqrt((k + 0.05) / (Q - (k + 0.05) * Q * Q / 4))
    mid = math.sqrt(k / (Q - k * Q * Q / 4))
    P(f"- K_i = {kk} published to one decimal implies sigma_i between {lo:.2f} and {hi:.2f}; a compensated junior with K_j = {kk} and 0 < c_j < 300 then has theta~_j = RX_j + 25 + 1.2816 x {mid:.2f} = RX_j + {25 + 1.2816 * mid:.1f} (to within the rounding of c_j).")
sig_ret = math.sqrt(55 ** 2 + 36 * 12 ** 2)
P(f"- A player at sigma 55 who is inactive for 36 months with a process SD of 12 points a month (T7.2, illustrative) returns at sigma = sqrt(55^2 + 36 x 12^2) = {sig_ret:.1f}, K = {K_of(sig_ret)}.")


def steady_k(games: int, level: float, sig_theta: float = 12.0) -> tuple[float, Decimal]:
    """Steady-state posterior SD after a month of `games` games at x = 0 (Davidson information), process SD sig_theta."""
    nu = nu0('standard', level)
    h = 1e-3
    slope = (E_exact('standard', h, level) - E_exact('standard', -h, level)) / (2 * h) / Q     # dE/dz at 0
    pw, pd, pl = probs('standard', 0.0, level)
    var_s = pw * 0.25 + pl * 0.25                         # score variance at x = 0
    info = (Q * slope) ** 2 / var_s if var_s > 0 else 0.0  # Fisher information per game about the gap, per point^2
    v = 100.0 ** 2
    for _ in range(2000):
        v = 1.0 / (1.0 / (v + sig_theta ** 2) + games * info)
    return math.sqrt(v), K_of(math.sqrt(v))


P("- Steady-state K from activity (process SD 12 points a month, T7.2 illustrative; Davidson information at equal strength; one month's games before each list):")
P("")
P("| standard games a month | " + " | ".join(str(g) for g in (1, 2, 3, 4, 5, 8)) + " |")
P("|---|" + "---|" * 6)
for lvl in (1700, 2300, 2700):
    cells = []
    for g in (1, 2, 3, 4, 5, 8):
        s, k = steady_k(g, lvl)
        cells.append(f"sigma {s:.1f}, K {k}")
    P(f"| level {lvl} | " + " | ".join(cells) + " |")
P("")


def inverse_gap(pval: float, level: float) -> int:
    """Smallest whole-number gap x >= 0 at which the PROVISIONAL table (band midpoint `level`) reaches pval."""
    x = 0
    while E_exact('standard', x, level) < pval and x < 2000:
        x += 1
    return x


P("- Table 8.1.1 against the PROVISIONAL rung-2 table (rung 2 alone keeps 8.1.1 for initial ratings, §8.2.3 [V 1]): the gap at which the table reaches a score p, at three band midpoints:")
P("")
P("| p | 8.1.1 dp [V 1] | band midpoint 1650 | 2050 | 2450 |")
P("|---|---|---|---|---|")
for pval, dp in ((0.75, 193), (0.92, 401)):
    P(f"| {pval} | {dp} | " + " | ".join(str(inverse_gap(pval, m)) for m in (1650, 2050, 2450)) + " |")
P("")
for cc in (100, 300):
    Lg = 1550
    x1 = -cc + 0                                         # two eligible juniors at equal published ratings, each compensated by cc
    e_w = E_table('standard', 0 - cc + 35, Lg)          # White's expectation against the opponent's RX
    e_b = E_table('standard', 0 - cc - 35, Lg)
    created = Decimal(40) * (1 - e_w - e_b)
    P(f"- Two eligible juniors at equal published ratings (band 1500-1599), each with c = {cc}, K = 40: expectations {e_w} (White) and {e_b} (Black), sum {e_w + e_b}; points created per game {created:+.1f}, whatever the result.")
for R in (1400, 1500, 1600):
    P(f"- With a table slope kappa = 5/6 and an anchor mean of 2041.3 (T7.2, illustrative), a correctly rated player at R = {R} shows theta~ - R = (1 - kappa)(m_t - R) = {(1 - 5 / 6) * (2041.3 - R):+.0f} points that are spread, not under-rating.")
P(f"- Accrual against activity at a_t = +1.3 a month: a player active under §7.2.2 with one game a year accrues {12 * 1.3:.1f} points a year; the drift it offsets, about 16 points a year for the median active player [R 5], is about {16 / 30:.2f} a game at T9.1's median of 30 games a year.")
P("")

# 11. Layer 0 test vector
P("## 11 Today's initial rating for the Appendix E.2 case of v0.1 (a Layer 0 test vector)\n")
opp = [1550, 1600, 1650, 1580, 1620]
Ra = Fraction(sum(opp) + 3600, 7)
P(f"- Ra = ({sum(opp)} + 2 x 1800)/7 = {float(Ra):.2f}; p = (3 + 1)/7 = {float(Fraction(4, 7)):.4f} -> .57; dp(.57) = 50 [V 1]; Ru = {float(Ra) + 50:.2f} -> 1707. "
  "The rounding of p before the lookup is settled in SPEC-L0.\n")

print("\n".join(out))
