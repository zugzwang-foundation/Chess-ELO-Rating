# OUTPUT of analysis/v03_calculations.py (parameters PROVISIONAL; the table's PROVISIONAL-FITTED)

Generated deterministically by the script; the source of every number in the proposal v0.3, the technical annex v0.3 and the brief v0.3.

## 0 Parameters used

The table's parameters are PROVISIONAL-FITTED, read from params/table_fit_2026-10.yaml (maximum likelihood on the Lichess broadcast archive, CC BY-SA 4.0, against FIDE's lists; docs/evidence/E2_broadcast-calibration.md), with eta rounded to a whole number; every other value is PROVISIONAL.

| tc | kappa | eta | alpha | beta | gamma |
|---|---|---|---|---|---|
| standard | 1.2120 | 36 | 0.2860 | 0.4985 | 0.2915 |
| rapid | 0.9480 | 37 | -0.0396 | 0.5271 | 0.2002 |
| blitz | 0.8735 | 27 | -0.7796 | 0.4432 | 0.3145 |

q = ln 10 / 400 = 0.0057565; K_min = 10, K_max = 40; C_period = 700; a_cap = 1.5, gamma_a = 1/6, d_0 = 2.0; tau = 25, c_cap = 300, z = 1.2816; level bands of 100 points from 1500 to 2800, open below and above (midpoints 1450 and 2850).

## 1 Expected-score table, standard (D1 draw decay, fitted gamma = 0.2915; D6 bands of 100 points; E to three decimals)

| x | <1500 | 1500-1599 | 1600-1699 | 1700-1799 | 1800-1899 | 1900-1999 | 2000-2099 | 2100-2199 | 2200-2299 | 2300-2399 | 2400-2499 | 2500-2599 | 2600-2699 | 2700-2799 | >=2800 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 0.500 | 0.500 | 0.500 | 0.500 | 0.500 | 0.500 | 0.500 | 0.500 | 0.500 | 0.500 | 0.500 | 0.500 | 0.500 | 0.500 | 0.500 |
| 100 | 0.633 | 0.630 | 0.626 | 0.622 | 0.618 | 0.613 | 0.609 | 0.604 | 0.599 | 0.594 | 0.588 | 0.583 | 0.578 | 0.573 | 0.568 |
| 200 | 0.756 | 0.751 | 0.745 | 0.739 | 0.733 | 0.726 | 0.719 | 0.711 | 0.703 | 0.695 | 0.686 | 0.677 | 0.668 | 0.659 | 0.649 |
| 300 | 0.850 | 0.846 | 0.840 | 0.835 | 0.829 | 0.822 | 0.815 | 0.807 | 0.798 | 0.789 | 0.780 | 0.769 | 0.759 | 0.748 | 0.736 |
| 400 | 0.913 | 0.910 | 0.906 | 0.902 | 0.897 | 0.892 | 0.886 | 0.879 | 0.872 | 0.865 | 0.856 | 0.847 | 0.838 | 0.827 | 0.816 |
| 500 | 0.952 | 0.949 | 0.947 | 0.944 | 0.941 | 0.937 | 0.933 | 0.928 | 0.923 | 0.918 | 0.911 | 0.905 | 0.897 | 0.889 | 0.881 |
| 600 | 0.974 | 0.972 | 0.971 | 0.969 | 0.967 | 0.964 | 0.962 | 0.959 | 0.955 | 0.952 | 0.948 | 0.943 | 0.938 | 0.932 | 0.926 |
| 700 | 0.986 | 0.985 | 0.984 | 0.983 | 0.981 | 0.980 | 0.978 | 0.977 | 0.975 | 0.972 | 0.970 | 0.967 | 0.964 | 0.960 | 0.956 |
| 800 | 0.992 | 0.992 | 0.991 | 0.991 | 0.990 | 0.989 | 0.988 | 0.987 | 0.986 | 0.984 | 0.983 | 0.981 | 0.979 | 0.977 | 0.974 |
| 900 | 0.996 | 0.996 | 0.995 | 0.995 | 0.994 | 0.994 | 0.993 | 0.993 | 0.992 | 0.991 | 0.990 | 0.989 | 0.988 | 0.987 | 0.985 |
| 1000 | 0.998 | 0.998 | 0.997 | 0.997 | 0.997 | 0.997 | 0.996 | 0.996 | 0.995 | 0.995 | 0.994 | 0.994 | 0.993 | 0.992 | 0.992 |

Excerpt printed in annex T3.4 (every other band):

| x | <1500 | 1600-1699 | 1800-1899 | 2000-2099 | 2200-2299 | 2400-2499 | 2600-2699 | >=2800 |
|---|---|---|---|---|---|---|---|---|
| 0 | 0.500 | 0.500 | 0.500 | 0.500 | 0.500 | 0.500 | 0.500 | 0.500 |
| 100 | 0.633 | 0.626 | 0.618 | 0.609 | 0.599 | 0.588 | 0.578 | 0.568 |
| 200 | 0.756 | 0.745 | 0.733 | 0.719 | 0.703 | 0.686 | 0.668 | 0.649 |
| 300 | 0.850 | 0.840 | 0.829 | 0.815 | 0.798 | 0.780 | 0.759 | 0.736 |
| 400 | 0.913 | 0.906 | 0.897 | 0.886 | 0.872 | 0.856 | 0.838 | 0.816 |
| 500 | 0.952 | 0.947 | 0.941 | 0.933 | 0.923 | 0.911 | 0.897 | 0.881 |
| 600 | 0.974 | 0.971 | 0.967 | 0.962 | 0.955 | 0.948 | 0.938 | 0.926 |
| 700 | 0.986 | 0.984 | 0.981 | 0.978 | 0.975 | 0.970 | 0.964 | 0.956 |
| 800 | 0.992 | 0.991 | 0.990 | 0.988 | 0.986 | 0.983 | 0.979 | 0.974 |
| 900 | 0.996 | 0.995 | 0.994 | 0.993 | 0.992 | 0.990 | 0.988 | 0.985 |
| 1000 | 0.998 | 0.997 | 0.997 | 0.996 | 0.995 | 0.994 | 0.993 | 0.992 |

Draw probability at x = 0 by band midpoint, standard: 1450: 0.251, 1550: 0.275, 1650: 0.301, 1750: 0.328, 1850: 0.356, 1950: 0.385, 2050: 0.415, 2150: 0.445, 2250: 0.476, 2350: 0.507, 2450: 0.538, 2550: 0.569, 2650: 0.599, 2750: 0.629, 2850: 0.657

nu0 by band midpoint, standard: 1450: 0.6707, 1550: 0.7597, 1650: 0.8605, 1750: 0.9748, 1850: 1.1041, 1950: 1.2507, 2050: 1.4167, 2150: 1.6047, 2250: 1.8177, 2350: 2.0589, 2450: 2.3322, 2550: 2.6417, 2650: 2.9924, 2750: 3.3895, 2850: 3.8394

## 2 The forecast tail at level 2300 (fitted standard parameters) against the 5/6-gap rule

nu0 at L = 2300: 1.9346. The 5/6-gap rule is logistic Elo on five sixths of the gap, 1/(1 + 10^(-(5x/6)/400)) [R 44]; today's table 8.1.2 [V 1] is shown for reference; the D1 columns with gamma = 1/2 and gamma = 0 keep the other fitted values.

| gap x | D1 (fitted gamma = 0.2915): P_W / P_D / P_L | D1: E | gamma = 1/2: E | gamma = 0: P_D | gamma = 0: E | 5/6-gap rule | table 8.1.2 |
|---|---|---|---|---|---|---|---|
| 200 | 0.529 / 0.339 / 0.131 | 0.699 | 0.718 | 0.436 | 0.670 | 0.723 | 0.76 |
| 400 | 0.785 / 0.167 / 0.048 | 0.868 | 0.898 | 0.311 | 0.805 | 0.872 | 0.92 |
| 500 | 0.867 / 0.106 / 0.026 | 0.920 | 0.945 | 0.247 | 0.854 | 0.917 | 0.96 |
| 700 | 0.954 / 0.039 / 0.007 | 0.973 | 0.985 | 0.143 | 0.922 | 0.966 | 0.99 |

- x = 400: P_D / P_L = 3.4616 with the fitted gamma; 1.9346 with gamma = 1/2 (equals nu0: draws fade as fast as losses); 7.8087 with gamma = 0.
- x = 800: P_D / P_L = 6.1942 with the fitted gamma; 1.9346 with gamma = 1/2 (equals nu0: draws fade as fast as losses); 31.5196 with gamma = 0.
- x = 1200: P_D / P_L = 11.0837 with the fitted gamma; 1.9346 with gamma = 1/2 (equals nu0: draws fade as fast as losses); 127.2272 with gamma = 0.

## 3 Numerical checks of the D1 form (standard parameters)

- gamma = 0: symmetry max |E(x) + E(-x) - 1| over x in [-1500, 1500], all bands = 2.2e-16; monotonicity min E(x+1) - E(x) = 6.41e-06 (> 0)
- gamma = 0.25: symmetry max |E(x) + E(-x) - 1| over x in [-1500, 1500], all bands = 2.2e-16; monotonicity min E(x+1) - E(x) = 8.86e-07 (> 0)
- gamma = 0.2915: symmetry max |E(x) + E(-x) - 1| over x in [-1500, 1500], all bands = 3.3e-16; monotonicity min E(x+1) - E(x) = 6.69e-07 (> 0)
- gamma = 0.5: symmetry max |E(x) + E(-x) - 1| over x in [-1500, 1500], all bands = 2.2e-16; monotonicity min E(x+1) - E(x) = 2.67e-07 (> 0)
- Logistic special case (nu0 = 0, kappa = 1, any gamma): max |E(x) - 1/(1 + 10^(-x/400))| = 2.2e-16
- Slope at x = 0, level 1700: numerical 1.196354e-03, formula kappa q / (2 (2 + nu0)) = 1.196353e-03; local logistic scale 200 (2 + nu0) / kappa = 481.2 (logistic Elo: 400)
- Slope at x = 0, level 2300: numerical 8.866121e-04, formula kappa q / (2 (2 + nu0)) = 8.866112e-04; local logistic scale 200 (2 + nu0) / kappa = 649.3 (logistic Elo: 400)
- Slope at x = 0, level 2700: numerical 6.728228e-04, formula kappa q / (2 (2 + nu0)) = 6.728220e-04; local logistic scale 200 (2 + nu0) / kappa = 855.6 (logistic Elo: 400)

### 3.1 Band-edge steps (D6): max over x in [0, 1500] of |E(x; band b) - E(x; band b+1)|

| bands | gamma | largest step | at x | between | points at K = 20 |
|---|---|---|---|---|---|
| 200 (v0.2) | 0 | 0.0278 | 459 | 2600-2799 / >=2800 | 0.56 |
| 200 | 0.2915 | 0.0231 | 326 | 2600-2799 / >=2800 | 0.46 |
| 100 (v0.3) | 0.2915 | 0.0115 | 326 | 2700-2799 / >=2800 | 0.23 |

Per adjacent pair, 100-point bands, fitted gamma = 0.2915: <1500/1500-1599: 0.0051, 1500-1599/1600-1699: 0.0055, 1600-1699/1700-1799: 0.0060, 1700-1799/1800-1899: 0.0065, 1800-1899/1900-1999: 0.0070, 1900-1999/2000-2099: 0.0076, 2000-2099/2100-2199: 0.0081, 2100-2199/2200-2299: 0.0086, 2200-2299/2300-2399: 0.0091, 2300-2399/2400-2499: 0.0096, 2400-2499/2500-2599: 0.0102, 2500-2599/2600-2699: 0.0106, 2600-2699/2700-2799: 0.0111, 2700-2799/>=2800: 0.0115

Largest step between adjacent bands in the published three-decimal table (100-point bands, fitted parameters): 0.012

## 4 Colour inside the expectation (standard, eta = 36, fitted parameters)

- Equal ratings at level 1700: E(White) = 0.544, E(Black) = 0.456; today's table gives .50 to each [V 1]; expected gain per extra White today at K = 20: +0.88 points; with colour in the table: 0.00 by construction.
- Equal ratings at level 2000: E(White) = 0.539, E(Black) = 0.461; today's table gives .50 to each [V 1]; expected gain per extra White today at K = 20: +0.77 points; with colour in the table: 0.00 by construction.
- Equal ratings at level 2500: E(White) = 0.529, E(Black) = 0.471; today's table gives .50 to each [V 1]; expected gain per extra White today at K = 20: +0.58 points; with colour in the table: 0.00 by construction.

## 5 K_i from certainty (D3): K = clip(q sigma^2 / (1 + q^2 sigma^2 / 4), 10, 40), one decimal

| sigma_i | 30 | 40 | 45 | 50 | 55 | 60 | 70 | 80 | 90 | 100 | 150 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| q sigma^2 / (1 + q^2 sigma^2 / 4) | 5.14 | 9.09 | 11.46 | 14.10 | 16.99 | 20.12 | 27.11 | 34.99 | 43.70 | 53.16 | 109.17 |
| K_i (clipped, one decimal) | 10.0 | 10.0 | 11.5 | 14.1 | 17.0 | 20.1 | 27.1 | 35.0 | 40.0 | 40.0 | 40.0 |

K_min binds below sigma = 41.98; K_max binds above sigma = 85.87.

Per-period cap example: K_i = 26.1 and n = 40 gives 1044.0 > 700, so K_i = 17.5 for the period; K_i = 16.5 and n = 40 gives 660.0 (no cap).

## 6 Continuous junior compensation (D5): c_j = min(c_cap, max(0, theta~ - z sigma - R - tau)), z = 1.2816, tau = 25

| sigma_j | theta~ - R = 0 | theta~ - R = 50 | theta~ - R = 100 | theta~ - R = 150 | theta~ - R = 200 | theta~ - R = 250 | theta~ - R = 300 | theta~ - R = 400 | theta~ - R = 500 | theta~ - R = 600 |
|---|---|---|---|---|---|---|---|---|---|---|
| 60 | 0 | 0 | 0 | 48 | 98 | 148 | 198 | 298 | 300 | 300 |
| 80 | 0 | 0 | 0 | 22 | 72 | 122 | 172 | 272 | 300 | 300 |
| 100 | 0 | 0 | 0 | 0 | 47 | 97 | 147 | 247 | 300 | 300 |

- sigma_j = 60: c_j is positive once theta~ - R exceeds tau + z sigma = 101.8960 and reaches c_cap at 401.8960; it rises one point per point in between, with no jump.
- sigma_j = 80: c_j is positive once theta~ - R exceeds tau + z sigma = 127.5280 and reaches c_cap at 427.5280; it rises one point per point in between, with no jump.
- sigma_j = 100: c_j is positive once theta~ - R exceeds tau + z sigma = 153.1600 and reaches c_cap at 453.1600; it rises one point per point in between, with no jump.

## 7 Worked example (i): established 1900 adult (White, sigma 55) v 1500-listed junior (Black, sigma 100) whom L1 rates at 1850 on the published scale

- c_J = min(300, max(0, 1850 - 1.2816 x 100 - 1500 - 25)) = min(300, max(0, 196.8400)) -> 197; RX_J = 1697.
- Level L = 1700, band 1700-1799 (midpoint 1750), nu0 = 0.9748.
- x_A = 1900 - 1697 + 36 = 239, E_A = 0.780; without compensation x = 436, E_A0 = 0.919.
- x_J = 1500 - 1900 - 36 = -436, E_J = 0.081 (J's own update uses published ratings only).
- K_A = 17.0 (sigma 55), K_J = 40.0 (sigma 100). Today: D = 400, no cap; table 8.1.2 row 392-411: .92 / .08; K = 20 for A, 40 for J [V 1].

| Result | A today: 20 x (S - .92) | J today: 40 x (S - .08) | A under L2: K_A x (S - E_A) | J under L2: K_J x (S - E_J) |
|---|---|---|---|---|
| A wins | +1.6 -> +2 | -3.2 -> -3 | +3.7400 -> +4 | -3.2400 -> -3 |
| Draw | -8.4 -> -8 | +16.8 -> +17 | -4.7600 -> -5 | +16.7600 -> +17 |
| J wins | -18.4 -> -18 | +36.8 -> +37 | -13.2600 -> -13 | +36.7600 -> +37 |

Ledger lines for the game (annex T6):

| Result | transfer J -> A, (K_A + K_J)/2 x (S_A - E_A0) | created by unequal K, (K_A - K_J) x (S_A - E_A0) | created by compensation, K_A x (E_A0 - E_A) | sum of both changes |
|---|---|---|---|---|
| A wins | +2.3085 | -1.8630 | +2.3630 | +0.5000 |
| Draw | -11.9415 | +9.6370 | +2.3630 | +12.0000 |
| J wins | -26.1915 | +21.1370 | +2.3630 | +23.5000 |

E_A + E_J = 0.861; compensation creates K_A x (E_A0 - E_A) = +2.3630 points in this game whatever the result.

## 8 Worked example (ii): 2600 v 2100 and 2700 v 2100 (strong player White, sigma 45 so K = 11.5)

Today [V 1]: K = 10. 2600 v 2100: D = 500 counted as 400 (player below 2650): row 392-411, .92. 2700 v 2100: D = 600 used in full: row 560-619, .98. Rapid and blitz [V 2]: the plain 400 cap applies to both and, with a player above 2600 and a difference of 600 or more, the game is not rated.

| Player | Opponent | Today: D used, PD | Today: win / draw / loss | L2: x, band, E | L2: K_i | L2: win / draw / loss |
|---|---|---|---|---|---|---|
| 2600 | 2100 | 400, 0.92 | +0.8 / -4.2 / -9.2 | 536, 2300-2399, 0.932 | 11.5 | +0.7820 / -4.9680 / -10.7180 |
| 2700 | 2100 | 600, 0.98 | +0.2 / -4.8 / -9.8 | 636, 2400-2499, 0.957 | 11.5 | +0.4945 / -5.2555 / -11.0055 |

If the uncapped table were right, today's cap gives the 2600 player 10 x (.96 - .92) = +0.4 points per game against a 2100 in expectation (row 485-517 [V 1]); with a calibrated table the expected change of any pairing is zero (P4).

The 2650 cliff today v rung 2 (each beats a 2200 with White; today K = 10 [V 1]; rung 2 here uses K = 11.5):

| Winner | Today: gap used, PD, gain | L2: x, band, E, gain at K = 11.5 |
|---|---|---|
| 2649 | 400, 0.92, +0.8 | 485, 2400-2499, 0.905, +1.0925 |
| 2651 | 451, 0.94, +0.6 | 487, 2400-2499, 0.905, +1.0925 |
| 2700 | 500, 0.96, +0.4 | 536, 2400-2499, 0.926, +0.8510 |
| 2936 | 736, 1.0, +0.0 | 772, 2500-2599, 0.978, +0.2530 |

## 9 Monthly adjustment with a soft deadband (D7): a_t = clip(gamma_a sign(d_t) max(0, |d_t| - d_0), -a_cap, +a_cap), one decimal

| d_t | -12 | -8 | -5 | -3 | -2 | -1 | 0 | 1 | 2 | 2.5 | 3 | 5 | 6.6 | 7.2 | 8 | 11 | 12 | 20 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| a_t | -1.5 | -1.0 | -0.5 | -0.2 | +0.0 | +0.0 | +0.0 | +0.0 | +0.0 | +0.1 | +0.2 | +0.5 | +0.8 | +0.9 | +1.0 | +1.5 | +1.5 | +1.5 |

Worked example (iii): m_t = 2004.6, m_hat_t = 2011.8, d_t = +7.2; a_t = (1/6) x (7.2 - 2.0) = 0.8667 -> +0.9. A player with game terms -2.4090, +5.8410, -8.7000 (sum -5.2680) and no carried balance: -5.2680 +0.9 = -4.3680 -> -4.

Feedback loop in a stylised pool, d_{t+1} = d_t - a_t + drift (deflation: drift +1.3 points a month, the research report's post-reform figure being about -16 a year [R 5]; inflation: drift -1.0):

| month | deflation: d_t | a_t | inflation: d_t | a_t |
|---|---|---|---|---|
| 0 | +0.0 | +0.0 | +0.0 | +0.0 |
| 1 | +1.3 | +0.0 | -1.0 | +0.0 |
| 2 | +2.6 | +0.1 | -2.0 | +0.0 |
| 3 | +3.8 | +0.3 | -3.0 | -0.2 |
| 6 | +6.3 | +0.7 | -5.1 | -0.5 |
| 12 | +8.6 | +1.1 | -7.0 | -0.8 |
| 24 | +9.5 | +1.3 | -7.7 | -1.0 |
| 36 | +9.5 | +1.3 | -7.7 | -1.0 |
| 48 | +9.5 | +1.3 | -7.7 | -1.0 |
| 60 | +9.5 | +1.3 | -7.7 | -1.0 |

Steady state: a_t equals the drift and the gap settles near d_0 + drift / gamma_a = 2.0 + 6 x drift (9.8 for +1.3, -8.0 for -1.0). Within |d_t| <= 2.0 nothing is paid, so noise in the anchor estimate does not flip the sign every month; a_t is continuous in d_t except for its one-decimal grid.

Bound on a published change (P2): |period change| <= round(700 + 12 x a_cap) = 718 with a full year of carried balance; round(700 + a_cap) = 702 in a month without one; today's bound is 700 [V 1].

## 10 Ledger identity (annex T6) on a synthetic month: 8 listed players, 9 rated games, one compensated junior, one game against an unrated player, one one-sided game under §8.2.4, one floor exit, one newcomer, one re-entry, one refused newcomer and one refused re-entry, a_t = +0.9

| game | White | Black | S_W | band | x_W | E_W | x_B | E_B | dR_W | dR_B | created by unequal K | created by compensation | one-sided |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | P1 (1900) | P2 (1500) | 0.5 | 1700-1799 | 239 | 0.780 | -436 | 0.081 | -4.7600 | +16.7600 | +9.6370 | +2.3630 | 0 |
| 2 | P3 (2050) | P1 (1900) | 1 | 1900-1999 | 186 | 0.711 | -186 | 0.289 | +4.0749 | -4.9130 | -0.8381 | +0.0000 | 0 |
| 3 | P2 (1500) | P4 (1750) | 1 | 1600-1699 | -214 | 0.240 | 17 | 0.521 | +30.4000 | -14.1191 | +9.8040 | +6.4769 | 0 |
| 4 | P5 (2300) | P3 (2050) | 0.5 | 2100-2199 | 286 | 0.795 | -286 | 0.205 | -3.3925 | +4.1595 | +0.7670 | +0.0000 | 0 |
| 5 | P4 (1750) | P6 (1600) | 0 | 1600-1699 | 186 | 0.730 | -186 | 0.270 | -19.7830 | +29.2000 | +9.4170 | +0.0000 | 0 |
| 6 | P6 (1600) | P2 (1500) | 0 | 1500-1599 | -61 | 0.421 | -136 | 0.324 | -16.8400 | +27.0400 | +0.0000 | +10.2000 | 0 |
| 7 | P5 (2300) | P1 (1900) | 1 | 2100-2199 | 436 | 0.899 | -436 | 0.101 | +1.1615 | -1.7170 | -0.5555 | +0.0000 | 0 |
| 8 | P7 (1405) | P4 (1750) | 0 | 1500-1599 | -309 | 0.147 | 309 | 0.853 | -2.9547 | +3.9837 | +1.0290 | +0.0000 | 0 |
| 9 | P6 (1600) | P7 (1405) | 1 | 1500-1599 | 231 | 0.783 | -231 | 0.217 | +8.6800 | -4.3617 | +4.3183 | +0.0000 | 0 |
| 10 | P3 (2050) | U (unrated) | 1 | — | — | — | — | — | 0 (not rated) | — | 0 | 0 | 0 |
| 11 | P3 (2050) | P8 (1580) | 0.5 | 1800-1899 | 506 | 0.943 | -506 | 0.057 | 0 (counts the newly rated player as unrated) | +17.7200 | 0 | 0 | +17.7200 |

| player | R(t) | sigma | K_i | n | RX | sum of game terms | + a_t | rounded change | R(t+1) | rounding residual | status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| P1 | 1900 | 55 | 17.0 | 3 | 1900 | -11.3900 | -10.4900 | -10 | 1890 | +0.4900 | listed |
| P2 | 1500 | 100 | 40.0 | 3 | 1697 | +74.2000 | +75.1000 | +75 | 1575 | -0.1000 | listed |
| P3 | 2050 | 50 | 14.1 | 2 | 2050 | +8.2344 | +9.1344 | +9 | 2059 | -0.1344 | listed |
| P4 | 1750 | 70 | 27.1 | 3 | 1750 | -29.9184 | -29.0184 | -29 | 1721 | +0.0184 | listed |
| P5 | 2300 | 45 | 11.5 | 2 | 2300 | -2.2310 | -1.3310 | -1 | 2299 | +0.3310 | listed |
| P6 | 1600 | 120 | 40.0 | 3 | 1600 | +21.0400 | +21.9400 | +22 | 1622 | +0.0600 | listed |
| P7 | 1405 | 60 | 20.1 | 2 | 1405 | -7.3164 | -6.4164 | -6 | 1399 | +0.4164 | below 1400: shown as unrated (7.2.1 [V 1]); exit booked at R+ = 1399 |
| P8 | 1580 | 90 | 40.0 | 1 | 1580 | +17.7200 | +18.6200 | +19 | 1599 | +0.3800 | listed (first rated on list t; its late-rated game is one-sided, §8.2.4 [V 1]) |
| N1 | — | — | 40.0 | — | — | — | — | — | 1650 | — | newcomer: theta~ = 1650.3, round = 1650 >= 1400, published at 1650 |
| N2 | — | — | — | — | — | — | — | — | — | — | newcomer: theta~ = 1287.6, round = 1288 < 1400, not published (stays unrated; no ledger line) |
| Q1 | — | — | 40.0 | — | — | — | — | — | 1452 | — | former floor exit re-qualifies: theta~ = 1452.4, round = 1452 >= 1400, published at 1452 |
| Q2 | — | — | — | — | — | — | — | — | — | — | former floor exit re-qualifies: theta~ = 1381.2, round = 1381 < 1400, not published (stays unrated; no ledger line) |

Left side: list total after 15867 - before 14085 = +1782.
Right side: unequal K +33.5787 + compensation +19.0399 + one-sided (§8.2.4) +17.7200 + adjustments posted +7.2 (8 x 0.9) + rounding +1.4614 + entering 3102 - exits at post-update rating 1399 = +1782.0000.
Identity closes exactly: True. Without the one-sided line the residual would be +17.7200; booking the exit at R(t) = 1405 instead of R+ = 1399 would leave +6 points.

## 10b Further figures for the review fixes

- Table entry at x = 500 in band 2300-2399 (midpoint 2350): 0.918; the function at L = 2300 gives 0.920.
- K_i = 17.0 published to one decimal implies sigma_i between 54.94 and 55.10; a compensated junior with K_j = 17.0 and 0 < c_j < 300 then has theta~_j = RX_j + 25 + 1.2816 x 55.02 = RX_j + 95.5 (to within the rounding of c_j).
- K_i = 27.1 published to one decimal implies sigma_i between 69.92 and 70.06; a compensated junior with K_j = 27.1 and 0 < c_j < 300 then has theta~_j = RX_j + 25 + 1.2816 x 69.99 = RX_j + 114.7 (to within the rounding of c_j).
- A player at sigma 55 who is inactive for 36 months with a process SD of 12 points a month (T7.2, illustrative) returns at sigma = sqrt(55^2 + 36 x 12^2) = 90.6, K = 40.0.
- Steady-state K from activity (process SD 12 points a month, T7.2 illustrative; Davidson information at equal strength; one month's games before each list):

| standard games a month | 1 | 2 | 3 | 4 | 5 | 8 |
|---|---|---|---|---|---|---|
| level 1700 | sigma 63.9, K 22.7 | sigma 53.5, K 16.1 | sigma 48.2, K 13.1 | sigma 44.8, K 11.4 | sigma 42.3, K 10.1 | sigma 37.4, K 10.0 |
| level 2300 | sigma 68.9, K 26.3 | sigma 57.8, K 18.7 | sigma 52.1, K 15.3 | sigma 48.4, K 13.2 | sigma 45.7, K 11.8 | sigma 40.4, K 10.0 |
| level 2700 | sigma 73.9, K 30.1 | sigma 62.0, K 21.5 | sigma 55.9, K 17.5 | sigma 51.9, K 15.2 | sigma 49.1, K 13.6 | sigma 43.4, K 10.7 |

- Table 8.1.1 against the PROVISIONAL-FITTED rung-2 table (rung 2 alone keeps 8.1.1 for initial ratings, §8.2.3 [V 1]): the gap at which the table reaches a score p, at three band midpoints:

| p | 8.1.1 dp [V 1] | band midpoint 1650 | 2050 | 2450 |
|---|---|---|---|---|
| 0.75 | 193 | 205 | 231 | 267 |
| 0.92 | 401 | 429 | 469 | 520 |

- Two eligible juniors at equal published ratings (band 1500-1599), each with c = 100, K = 40: expectations 0.417 (White) and 0.324 (Black), sum 0.741; points created per game +10.4, whatever the result.
- Two eligible juniors at equal published ratings (band 1500-1599), each with c = 300, K = 40: expectations 0.185 (White) and 0.128 (Black), sum 0.313; points created per game +27.5, whatever the result.
- With a spread factor of 5/6 (Sonas's rule, illustrative) and an anchor mean of 2041.3 (T7.2, illustrative), a correctly rated player at R = 1400 shows theta~ - R = (1 - 5/6)(m_t - R) = +107 points that are spread, not under-rating.
- With a spread factor of 5/6 (Sonas's rule, illustrative) and an anchor mean of 2041.3 (T7.2, illustrative), a correctly rated player at R = 1500 shows theta~ - R = (1 - 5/6)(m_t - R) = +90 points that are spread, not under-rating.
- With a spread factor of 5/6 (Sonas's rule, illustrative) and an anchor mean of 2041.3 (T7.2, illustrative), a correctly rated player at R = 1600 shows theta~ - R = (1 - 5/6)(m_t - R) = +74 points that are spread, not under-rating.
- Accrual against activity at a_t = +1.3 a month: a player active under §7.2.2 with one game a year accrues 15.6 points a year; the drift it offsets, about 16 points a year for the median active player [R 5], is about 0.53 a game at T9.1's median of 30 games a year.

## 11 Today's initial rating for the Appendix E.2 case of v0.1 (a Layer 0 test vector)

- Ra = (8000 + 2 x 1800)/7 = 1657.14; p = (3 + 1)/7 = 0.5714 -> .57; dp(.57) = 50 [V 1]; Ru = 1707.14 -> 1707. The rounding of p before the lookup is settled in SPEC-L0.

