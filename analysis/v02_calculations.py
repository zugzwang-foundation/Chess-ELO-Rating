#!/usr/bin/env python3
"""Illustrative calculations for proposal v0.2 and technical annex v0.2.

Python standard library only. Deterministic. NOT the rating engine: these are
hand-check-scale calculations whose output is pasted into the documents.
Run:  python3 analysis/v02_calculations.py > analysis/OUTPUT_v0_2.md

Every parameter value below is PROVISIONAL (see docs/proposal/ELO-TECHNICAL-ANNEX_v0_2.md, T1/T7).
"""
from __future__ import annotations

import math
from decimal import Decimal, ROUND_HALF_UP, ROUND_DOWN
from fractions import Fraction

LN10_400 = math.log(10.0) / 400.0

# ---------------------------------------------------------------- parameters (PROVISIONAL)
PARAMS = {
    "standard": {"kappa": 1.00, "eta": 35, "alpha": -0.50, "beta": 0.55},
    "rapid":    {"kappa": 1.00, "eta": 25, "alpha": -0.70, "beta": 0.50},
    "blitz":    {"kappa": 1.00, "eta": 25, "alpha": -0.90, "beta": 0.45},
}
K_MIN, K_MAX, SIGMA_NEW = 10.0, 40.0, 100.0
C_PERIOD = 700
A_CAP, GAMMA_A = 1.5, 1.0 / 6.0
TAU, C_CAP, P_MIN = 50, 300, 0.90
BAND_WIDTH = 200
BAND_LOW, BAND_HIGH = 1600, 2800   # open bands below 1600 and from 2800; midpoints 1500 ... 2900

# ---------------------------------------------------------------- core functions
def band_midpoint(L: float) -> int:
    """Level band of a game from L = (R_i + R_j)/2; returns the midpoint used for nu."""
    if L < BAND_LOW:
        return BAND_LOW - BAND_WIDTH // 2
    if L >= BAND_HIGH:
        return BAND_HIGH + BAND_WIDTH // 2
    lo = BAND_LOW + BAND_WIDTH * int((L - BAND_LOW) // BAND_WIDTH)
    return lo + BAND_WIDTH // 2

def band_label(L: float) -> str:
    if L < BAND_LOW:
        return f"<{BAND_LOW}"
    if L >= BAND_HIGH:
        return f">={BAND_HIGH}"
    lo = BAND_LOW + BAND_WIDTH * int((L - BAND_LOW) // BAND_WIDTH)
    return f"{lo}-{lo + BAND_WIDTH - 1}"

def nu_of(tc: str, Lmid: float) -> float:
    p = PARAMS[tc]
    return math.exp(p["alpha"] + p["beta"] * (Lmid - 2000.0) / 400.0)

def probs(tc: str, x: float, Lmid: float, nu_override: float | None = None, kappa_override: float | None = None):
    p = PARAMS[tc]
    kappa = p["kappa"] if kappa_override is None else kappa_override
    nu = nu_of(tc, Lmid) if nu_override is None else nu_override
    z = kappa * LN10_400 * x
    a, b = math.exp(z / 2.0), math.exp(-z / 2.0)
    den = a + b + nu
    return a / den, nu / den, b / den          # P_W, P_D, P_L

def E_exact(tc: str, x: float, Lmid: float, **kw) -> float:
    pw, pd, _ = probs(tc, x, Lmid, **kw)
    return pw + pd / 2.0

def E_table(tc: str, x: int, L: float) -> Decimal:
    """What the published table prints: E to three decimals, negative x by symmetry."""
    mid = band_midpoint(L)
    if x >= 0:
        return Decimal(repr(round(E_exact(tc, x, mid), 3))).quantize(Decimal("0.001"))
    return (Decimal(1) - E_table(tc, -x, L)).quantize(Decimal("0.001"))

def K_of(sigma: float) -> Decimal:
    k = K_MIN + (K_MAX - K_MIN) * min(1.0, (sigma / SIGMA_NEW) ** 2)
    return Decimal(repr(round(k, 1))).quantize(Decimal("0.1"))

def K_capped(K: Decimal, n: int) -> Decimal:
    """Per-period cap: if K*n > 700, K becomes floor(7000/n)/10."""
    if K * n > C_PERIOD:
        return (Decimal(10 * C_PERIOD) / Decimal(n)).quantize(Decimal("1"), rounding=ROUND_DOWN) / Decimal(10)
    return K

def round_fide(v: Decimal) -> Decimal:
    """Nearest whole number, 0.5 away from zero (FIDE 8.3.4)."""
    return v.quantize(Decimal("1"), rounding=ROUND_HALF_UP)

def phi(z: float) -> float:
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))

def fmt(v, nd=3):
    return f"{v:.{nd}f}"

# ---------------------------------------------------------------- report
out: list[str] = []
P = out.append

P("# OUTPUT of analysis/v02_calculations.py (illustrative; all parameters PROVISIONAL)\n")
P("Generated deterministically by the script; paste-source for the proposal v0.2 and the technical annex v0.2.\n")

# 1. Table excerpt
P("## 1 Expected-score table excerpt (standard; E to three decimals; rows x = 0..800 step 100; columns = level bands)\n")
mids = [1500] + list(range(BAND_LOW + BAND_WIDTH // 2, BAND_HIGH, BAND_WIDTH)) + [2900]
labels = [f"<{BAND_LOW}"] + [f"{lo}-{lo+BAND_WIDTH-1}" for lo in range(BAND_LOW, BAND_HIGH, BAND_WIDTH)] + [f">={BAND_HIGH}"]
P("| x | " + " | ".join(labels) + " |")
P("|---|" + "---|" * len(labels))
for x in list(range(0, 801, 100)):
    P(f"| {x} | " + " | ".join(fmt(E_exact('standard', x, m)) for m in mids) + " |")
P("")
P("Draw probability at equal strength (x = 0) by band midpoint, standard: " +
  ", ".join(f"{m}: {fmt(probs('standard', 0, m)[1])}" for m in mids) + "\n")
P("nu by band midpoint, standard: " + ", ".join(f"{m}: {fmt(nu_of('standard', m), 4)}" for m in mids) + "\n")

# 2. Property checks
P("## 2 Numerical checks of the expected-score function (standard parameters)\n")
grid = list(range(-1200, 1201, 1))
max_sym = max(abs(E_exact('standard', x, m) + E_exact('standard', -x, m) - 1.0) for x in grid for m in mids)
min_step = min(E_exact('standard', x + 1, m) - E_exact('standard', x, m) for x in grid[:-1] for m in mids)
max_logistic_dev = max(abs(E_exact('standard', x, 2000, nu_override=0.0, kappa_override=1.0) - 1.0 / (1.0 + 10 ** (-x / 400.0))) for x in grid)
band_steps = []
for b in range(len(mids) - 1):
    band_steps.append(max(abs(E_exact('standard', x, mids[b]) - E_exact('standard', x, mids[b + 1])) for x in range(0, 1001)))
P(f"- Symmetry: max |E(x) + E(-x) - 1| over x in [-1200, 1200], all bands = {max_sym:.1e}")
P(f"- Monotonicity: min E(x+1) - E(x) over the same grid = {min_step:.2e} (> 0)")
P(f"- Logistic special case (nu = 0, kappa = 1): max |E(x) - 1/(1+10^(-x/400))| = {max_logistic_dev:.1e}")
P(f"- Band-edge step of the published table: max over x of |E(x; band b) - E(x; band b+1)| = {max(band_steps):.4f} "
  f"(per band pair: {', '.join(f'{s:.4f}' for s in band_steps)}); at K = 20 that is at most {20*max(band_steps):.2f} points in one game")
P(f"- E at x = 400, 600, 800 for band 2200-2399 (midpoint 2300): "
  + ", ".join(f"{x}: {fmt(E_exact('standard', x, 2300))}" for x in (400, 600, 800)) + "  (today's table 8.1.2: .92, .98, 1.0 [V 1])")
P(f"- Draw probability at x = 0 for band 1600-1799 vs 2600-2799: {fmt(probs('standard',0,1700)[1])} vs {fmt(probs('standard',0,2700)[1])}")
P("")

# 3. Colour
P("## 3 Colour inside the expectation (standard, eta = 35 PROVISIONAL)\n")
for L in (1700, 2000, 2500):
    ew = E_exact('standard', 35, L)
    P(f"- Equal ratings at level {L}: E(White) = {fmt(ew)}, E(Black) = {fmt(1-ew)}; today's table gives .50 to each [V 1]. "
      f"Expected gain per extra White game today at K = 20: {20*(ew-0.5):+.2f} points; under L2: 0.00 by construction.")
P("")

# 4. K mapping
P("## 4 K_i from the posterior SD (K_min = 10, K_max = 40, sigma_new = 100, PROVISIONAL; Kalman gain sigma^2 ln10/400 shown for comparison)\n")
P("| sigma_i | 30 | 45 | 55 | 70 | 85 | 100 | 150 |")
P("|---|" + "---|" * 7)
P("| K_i | " + " | ".join(str(K_of(s)) for s in (30, 45, 55, 70, 85, 100, 150)) + " |")
P("| Kalman gain sigma^2 ln10/400 | " + " | ".join(f"{s*s*LN10_400:.1f}" for s in (30, 45, 55, 70, 85, 100, 150)) + " |")
P("")
P(f"Per-period cap example: K_i = 26.1 and n = 40 games gives K_i x n = {Decimal('26.1')*40}; 700 / 40 truncated to tenths = {K_capped(Decimal('26.1'), 40)}; "
  f"K_i = 16.5 and n = 40 gives {Decimal('16.5')*40} (no cap).\n")

# 5. Worked example (i)
from statistics import NormalDist
P(f"z_{{0.90}} = NormalDist().inv_cdf(0.90) = {NormalDist().inv_cdf(0.90):.4f} (the Gaussian quantile used in the eligibility test, T4.6); p_min = 0.90.\n")
P("## 5 Worked example (i): established 1900 adult (White, sigma = 55) v 1500-listed junior (Black, sigma = 100) whom L1 rates at 1850\n")
R_A, R_J, THETA_J, SIG_A, SIG_J = 1900, 1500, 1850, 55, 100
p_elig = phi((THETA_J - R_J - TAU) / SIG_J)
c_J = min(THETA_J - R_J, C_CAP)
RX_J = R_J + c_J
K_A, K_J = K_of(SIG_A), K_of(SIG_J)
L = (R_A + R_J) / 2
xA = R_A - RX_J + PARAMS['standard']['eta']
xJ = R_J - R_A - PARAMS['standard']['eta']
EA, EJ = E_table('standard', xA, L), E_table('standard', xJ, L)
EA0 = E_table('standard', R_A - R_J + PARAMS['standard']['eta'], L)   # without compensation
P(f"- Eligibility (AR-4): P(theta_J - R_J > tau) = Phi(({THETA_J} - {R_J} - {TAU}) / {SIG_J}) = Phi({(THETA_J-R_J-TAU)/SIG_J:.3f}) = {p_elig:.4f} >= {P_MIN}: eligible. "
  f"c_J = min({THETA_J} - {R_J}, {C_CAP}) = {c_J}; RX_J = {RX_J}.")
P(f"- Level L = ({R_A} + {R_J})/2 = {L:.0f}, band {band_label(L)} (midpoint {band_midpoint(L)}), nu = {nu_of('standard', band_midpoint(L)):.4f}.")
P(f"- A's gap x_A = {R_A} - {RX_J} + 35 = {xA}; E_A = {EA} (table). Without compensation x = {R_A - R_J + 35}, E = {EA0}.")
P(f"- J's gap x_J = {R_J} - {R_A} - 35 = {xJ}; E_J = {EJ} (table; J's own update uses published ratings).")
P(f"- K_A = {K_A} (sigma 55), K_J = {K_J} (sigma 100).")
P("")
P("Today (standard list, rules as amended 1 October 2025 [V 1]): D = 400, not 'more than 400', so no cap; table 8.1.2 row 392-411: H = .92, L = .08; K = 20 for A, 40 for J.\n")
P("| Result | A today: 20 x (S - .92) | J today: 40 x (S - .08) | A under L2: K_A x (S - E_A) | J under L2: K_J x (S - E_J) |")
P("|---|---|---|---|---|")
led = []
for name, SA in (("A wins", Decimal(1)), ("Draw", Decimal("0.5")), ("J wins", Decimal(0))):
    SJ = Decimal(1) - SA
    tA, tJ = Decimal(20) * (SA - Decimal("0.92")), Decimal(40) * (SJ - Decimal("0.08"))
    dA, dJ = K_A * (SA - EA), K_J * (SJ - EJ)
    P(f"| {name} | {tA:+.1f} -> {round_fide(tA):+} | {tJ:+.1f} -> {round_fide(tJ):+} | {dA:+.4f} -> {round_fide(dA):+} | {dJ:+.4f} -> {round_fide(dJ):+} |")
    # ledger decomposition (T6): transfer, creation by unequal K, creation by compensation
    T = (K_A + K_J) / 2 * (SA - EA0)
    CK = (K_A - K_J) * (SA - EA0)
    CC = K_A * (EA0 - EA)
    led.append((name, T, CK, CC, dA + dJ))
P("")
P("Ledger lines for the game (T6 decomposition; E_A0 = E_A without compensation):\n")
P("| Result | transfer J -> A, (K_A+K_J)/2 x (S_A - E_A0) | created by unequal K, (K_A - K_J) x (S_A - E_A0) | created by compensation, K_A x (E_A0 - E_A) | sum of both changes |")
P("|---|---|---|---|---|")
for name, T, CK, CC, tot in led:
    P(f"| {name} | {T:+.4f} | {CK:+.4f} | {CC:+.4f} | {tot:+.4f} = {CK:+.4f} + {CC:+.4f} |")
P(f"\nCheck: sum of changes - (creation by unequal K + creation by compensation) = "
  + ", ".join(f"{(tot - CK - CC):+.4f}" for _, T, CK, CC, tot in led) + " (zero in every case).\n")
P(f"Points created by compensation in expectation over A's own E_A: E_A + E_J = {EA + EJ} (less than 1), expected creation per game = K_A x (E_A0 - E_A) = {K_A*(EA0-EA):+.4f}.\n")

# 6. Worked example (ii)
P("## 6 Worked example (ii): 2600 v 2100 and 2700 v 2100 (strong player White, sigma = 45 so K = " + str(K_of(45)) + "); today v L2\n")
P("Today [V 1]: K = 10 (rating at or above 2400). 2600 v 2100: D = 500 > 400 and the player is below 2650, so D is counted as 400: table row 392-411, PD = .92. "
  "2700 v 2100: D = 600, player at or above 2650, no cap: row 560-619, PD = .98. Rapid and blitz [V 2]: the plain 400 cap applies to both (PD = .92), and at 600 points or more with a player above 2600 the game is not rated.\n")
P("| Player | Opponent | Today: D used, PD | Today: win / draw / loss | L2: x (with +35 colour), band, E | L2: K_i | L2: win / draw / loss |")
P("|---|---|---|---|---|---|---|")
for Rs, Dused, PD in ((2600, 400, Decimal("0.92")), (2700, 600, Decimal("0.98"))):
    Ro = 2100
    Lg = (Rs + Ro) / 2
    x = Rs - Ro + 35
    E = E_table('standard', x, Lg)
    K = K_of(45)
    tw, td, tl = Decimal(10) * (1 - PD), Decimal(10) * (Decimal("0.5") - PD), Decimal(10) * (0 - PD)
    lw, ld, ll = K * (1 - E), K * (Decimal("0.5") - E), K * (0 - E)
    P(f"| {Rs} | {Ro} | {Dused}, {PD} | {tw:+.1f} / {td:+.1f} / {tl:+.1f} | {x}, {band_label(Lg)}, {E} | {K} | {lw:+.4f} / {ld:+.4f} / {ll:+.4f} |")
P("")
E500 = E_table('standard', 500, 2350)
P(f"Expected change under L2 = K x (P_W x (1 - E) + P_D x (0.5 - E) + P_L x (0 - E)) = K x (E - E) = 0 exactly (property P4). "
  f"Today, the 2600 player's expectation is capped at .92 while the table's own uncapped value at D = 500 is .96 (row 485-517 [V 1]): "
  f"if the uncapped table were right, each game against a 2100 would be worth 10 x (.96 - .92) = {Decimal(10)*(Decimal('0.96')-Decimal('0.92')):+.1f} points in expectation, which is the farming incentive; under L2 there is no cap and the incentive is zero.\n")
P("The 2650 cliff today v L2 (each beats a 2200 with White; today K = 10 [V 1]):\n")
P("| Winner | Today: gap used, PD, gain | L2: x, band, E, gain at K = " + str(K_of(45)) + " |")
P("|---|---|---|")
for Rw, Dused, PD in ((2649, 400, Decimal("0.92")), (2651, 451, Decimal("0.94")), (2700, 500, Decimal("0.96")), (2936, 736, Decimal("1.0"))):
    Lg = (Rw + 2200) / 2
    x = Rw - 2200 + 35
    E = E_table('standard', x, Lg)
    P(f"| {Rw} | {Dused}, {PD}, {Decimal(10)*(1-PD):+.1f} | {x}, {band_label(Lg)}, {E}, {K_of(45)*(1-E):+.4f} |")
P("")

# 7. Worked example (iii): one month's adjustment
P("## 7 Worked example (iii): one month's global adjustment for one player (standard; a_cap = 1.5, gamma_a = 1/6, PROVISIONAL)\n")
m_t, mhat_t = Decimal("2004.6"), Decimal("2011.8")
d_t = mhat_t - m_t
a_raw = d_t / Decimal(6)
a_t = max(-Decimal(repr(A_CAP)), min(Decimal(repr(A_CAP)), a_raw.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)))
P(f"- Anchor cohort this month: published mean m_t = {m_t}, L1 latent mean m_hat_t = {mhat_t}, gap d_t = {d_t:+.1f} points.")
P(f"- a_t = clip(gamma_a x d_t, -a_cap, +a_cap) = clip({d_t}/6 = {a_raw:.3f}, -1.5, +1.5) -> {a_t:+.1f} (one decimal). a_{{f,t}} = 0 (disabled).")
games = [Decimal("-2.4090"), Decimal("+5.8410"), Decimal("-8.7000")]
s = sum(games)
P(f"- Player's game terms this month: {', '.join(f'{g:+.4f}' for g in games)}; sum = {s:+.4f}; plus a_t {a_t:+.1f} = {s + a_t:+.4f}; rounded (8.3.4) = {round_fide(s + a_t):+}.")
P(f"- Had the player not played this month: no game terms, no a_t, rating unchanged (AR-5).")
P("")
P("Feedback loop (AR-3) in a stylised pool: gap evolves as d_{t+1} = d_t - a_t + drift, drift = -(-1.3) = +1.3 points per month of deflation pressure on the gap "
  "(the research report's post-reform figure is about -16 points a year [R 5]):\n")
d = Decimal("0.0")
traj = []
for t in range(37):
    a = max(-Decimal(repr(A_CAP)), min(Decimal(repr(A_CAP)), (d / Decimal(6)).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)))
    traj.append((t, d, a))
    d = d - a + Decimal("1.3")
P("| month | gap d_t | a_t |")
P("|---|---|---|")
for t, dd, a in traj:
    if t in (0, 1, 2, 3, 6, 12, 24, 36):
        P(f"| {t} | {dd:+.1f} | {a:+.1f} |")
P(f"\nSteady state: a_t -> +1.3 = the drift, gap -> about {6*1.3:.1f} points (= drift / gamma_a); the loop is stable because 0 < gamma_a < 1 and the cap 1.5 exceeds the drift 1.3. "
  "If the drift exceeded a_cap the gap would grow linearly and the monitoring report would show it.\n")

# 8. Ledger identity on a synthetic month
P("## 8 Ledger identity (T6) checked on a synthetic month of 6 players, 7 games, one compensated junior, a_t = +1.2\n")
players = {  # id: (R, sigma, is_eligible_junior, theta_hat)
    "P1": (1900, 55, False, None), "P2": (1500, 100, True, 1850), "P3": (2050, 50, False, None),
    "P4": (1750, 70, False, None), "P5": (2300, 45, False, None), "P6": (1600, 120, False, None),
}
games_m = [  # (white, black, score_white)
    ("P1", "P2", Decimal("0.5")), ("P3", "P1", Decimal(1)), ("P2", "P4", Decimal(1)), ("P5", "P3", Decimal("0.5")),
    ("P4", "P6", Decimal(0)), ("P6", "P2", Decimal(0)), ("P5", "P1", Decimal(1)),
]
A_T = Decimal("1.2")
K = {p: K_of(v[1]) for p, v in players.items()}
nn = {p: sum(1 for g in games_m if p in g[:2]) for p in players}
Kc = {p: K_capped(K[p], nn[p]) for p in players}
def RX(p):
    R, sig, jun, th = players[p]
    if jun and phi((th - R - TAU) / sig) >= P_MIN:
        return R + min(th - R, C_CAP)
    return R
tot = {p: Decimal(0) for p in players}
sumCK = sumCC = Decimal(0)
P("| game | White | Black | S_W | x_W | E_W | x_B | E_B | dR_W | dR_B | created by unequal K | created by compensation |")
P("|---|---|---|---|---|---|---|---|---|---|---|---|")
for n_, (w, b, Sw) in enumerate(games_m, 1):
    Rw, Rb = players[w][0], players[b][0]
    Lg = (Rw + Rb) / 2
    xw, xb = Rw - RX(b) + 35, Rb - RX(w) - 35
    xw0 = Rw - Rb + 35
    Ew, Eb, Ew0 = E_table('standard', xw, Lg), E_table('standard', xb, Lg), E_table('standard', xw0, Lg)
    Eb0 = Decimal(1) - Ew0
    dw, db = Kc[w] * (Sw - Ew), Kc[b] * ((1 - Sw) - Eb)
    CK = (Kc[w] - Kc[b]) * (Sw - Ew0)
    CC = Kc[w] * (Ew0 - Ew) + Kc[b] * (Eb0 - Eb)
    assert (dw + db - CK - CC) == 0, (dw + db, CK, CC)
    tot[w] += dw; tot[b] += db; sumCK += CK; sumCC += CC
    P(f"| {n_} | {w} ({Rw}) | {b} ({Rb}) | {Sw} | {xw} | {Ew} | {xb} | {Eb} | {dw:+.4f} | {db:+.4f} | {CK:+.4f} | {CC:+.4f} |")
P("")
P("| player | R | K_i | n | sum of game terms | + a_t | rounded change | rounding residual |")
P("|---|---|---|---|---|---|---|---|")
sum_round = sum_res = Decimal(0)
for p in players:
    pre = tot[p] + A_T
    r = round_fide(pre)
    res = r - pre
    sum_round += r; sum_res += res
    P(f"| {p} | {players[p][0]} | {Kc[p]} | {nn[p]} | {tot[p]:+.4f} | {pre:+.4f} | {int(r):+d} | {res:+.4f} |")
P("")
P(f"Identity: sum of published changes {int(sum_round):+d} = created by unequal K {sumCK:+.4f} + created by compensation {sumCC:+.4f} + adjustments {A_T*len(players):+.1f} (6 x 1.2) + rounding residuals {sum_res:+.4f} + newcomers 0 - exits 0 = {sumCK + sumCC + A_T*len(players) + sum_res:+.4f}. "
  f"Transfers cancel by construction. Closes exactly: {sum_round == sumCK + sumCC + A_T*len(players) + sum_res}.\n")

# 9. Newcomer seed comparison (today's rule, as a Layer-0 test vector; the L2 seed is an L1 output and cannot be computed here)
P("## 9 Today's initial rating for the Appendix E.2 case of v0.1 (Layer 0 test vector, unchanged)\n")
opp = [1550, 1600, 1650, 1580, 1620]
Ra = Fraction(sum(opp) + 3600, 7)
p_ = Fraction(3 * 2 + 2, 14)  # (3 + 2*0.5)/7
P(f"- Ra = ({sum(opp)} + 2 x 1800)/7 = {float(Ra):.2f}; p = (3 + 1)/7 = {float(p_):.4f} -> .57; dp(.57) = 50 [V 1]; Ru = {float(Ra)+50:.2f} -> 1707. The rounding of p before the lookup is NOT VERIFIED (SPEC-L0 R-30).")
P("- Under AR-5 the seed is the L1 posterior mean over all three time controls after the same five games; it is an output of the monthly fit and is not reproduced by this script.\n")

print("\n".join(out))
