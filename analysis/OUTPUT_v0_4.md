# OUTPUT of analysis/v04_calculations.py (parameters PROVISIONAL; the table's PROVISIONAL-FITTED)

Generated deterministically by the script; the source of every calculated number in the proposal v0.4, the technical annex v0.4 and the brief v0.4 that is not cited to an evidence report. Rulings R1-R14 (D-0008) applied.

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

## 5 K_i from certainty (R6): K = clip(q sigma^2 / (kappa (1 + q^2 sigma^2 v)), 10, 40), one decimal; v = 1 / (2 (2 + nu0)) in the player's own level band

sigma_i is Layer 1's posterior SD of s_i,tc in latent units (D-0008, reading 5); kappa = 1.2120 (standard). v at the band midpoint of the player's rating: R = 1700: band 1700-1799, nu0 = 0.9748, v = 0.1681, R = 2300: band 2300-2399, nu0 = 2.0589, v = 0.1232, R = 2700: band 2700-2799, nu0 = 3.3895, v = 0.0928.

| sigma_i | 30 | 40 | 45 | 50 | 55 | 60 | 70 | 80 | 90 | 100 | 150 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| R6 raw, R = 1700 | 4.25 | 7.53 | 9.51 | 11.71 | 14.13 | 16.76 | 22.65 | 29.35 | 36.81 | 44.99 | 94.96 |
| K_i, R = 1700 | 10.0 | 10.0 | 10.0 | 11.7 | 14.1 | 16.8 | 22.7 | 29.4 | 36.8 | 40.0 | 40.0 |
| R6 raw, R = 2300 | 4.26 | 7.55 | 9.54 | 11.75 | 14.19 | 16.85 | 22.82 | 29.62 | 37.24 | 45.63 | 97.88 |
| K_i, R = 2300 | 10.0 | 10.0 | 10.0 | 11.8 | 14.2 | 16.9 | 22.8 | 29.6 | 37.2 | 40.0 | 40.0 |
| R6 raw, R = 2700 | 4.26 | 7.56 | 9.56 | 11.78 | 14.24 | 16.91 | 22.93 | 29.81 | 37.54 | 46.08 | 99.95 |
| K_i, R = 2700 | 10.0 | 10.0 | 10.0 | 11.8 | 14.2 | 16.9 | 22.9 | 29.8 | 37.5 | 40.0 | 40.0 |
| v0.3's D3 (kappa = 1, v = 1/4), for comparison | 5.14 | 9.09 | 11.46 | 14.10 | 16.99 | 20.12 | 27.11 | 34.99 | 43.70 | 53.16 | 109.17 |

- R = 1700: K_min binds below sigma = 46.16; K_max binds above sigma = 94.00; the published-scale SD at those points is sigma / kappa = 38.08 and 77.56.
- R = 2300: K_min binds below sigma = 46.08; K_max binds above sigma = 93.39; the published-scale SD at those points is sigma / kappa = 38.02 and 77.05.
- R = 2700: K_min binds below sigma = 46.03; K_max binds above sigma = 92.98; the published-scale SD at those points is sigma / kappa = 37.98 and 76.72.

Per-period cap example: K_i = 26.1 and n = 40 gives 1044.0 > 700, so K_i = 17.5 for the period; K_i = 16.5 and n = 40 gives 660.0 (no cap).

## 6 Continuous junior compensation (D5, R5): c_j = min(c_cap, max(0, theta~ - z sigma~ - R - tau)), z = 1.2816, tau = 25; theta~, sigma~ the same-time-control posterior on the published scale

| sigma~_j | theta~ - R = 0 | theta~ - R = 50 | theta~ - R = 100 | theta~ - R = 150 | theta~ - R = 200 | theta~ - R = 250 | theta~ - R = 300 | theta~ - R = 400 | theta~ - R = 500 | theta~ - R = 600 |
|---|---|---|---|---|---|---|---|---|---|---|
| 60 | 0 | 0 | 0 | 48 | 98 | 148 | 198 | 298 | 300 | 300 |
| 80 | 0 | 0 | 0 | 22 | 72 | 122 | 172 | 272 | 300 | 300 |
| 100 | 0 | 0 | 0 | 0 | 47 | 97 | 147 | 247 | 300 | 300 |

- sigma~_j = 60: c_j is positive once theta~ - R exceeds tau + z sigma~ = 101.8960 and reaches c_cap at 401.8960; it rises one point per point in between, with no jump.
- sigma~_j = 80: c_j is positive once theta~ - R exceeds tau + z sigma~ = 127.5280 and reaches c_cap at 427.5280; it rises one point per point in between, with no jump.
- sigma~_j = 100: c_j is positive once theta~ - R exceeds tau + z sigma~ = 153.1600 and reaches c_cap at 453.1600; it rises one point per point in between, with no jump.
- R8: in a game between two eligible juniors neither compensation enters; both expectations use published ratings.

## 7 Worked example (i): established 1900 adult (White, latent sigma 55) v 1500-listed junior (Black) whom L1 rates at theta~ = 1850 with sigma~ = 100 on the published scale (latent sigma = kappa x 100 = 121.2)

- c_J = min(300, max(0, 1850 - 1.2816 x 100 - 1500 - 25)) = min(300, max(0, 196.8400)) -> 197; RX_J = 1697.
- Level L = 1700, band 1700-1799 (midpoint 1750), nu0 = 0.9748.
- x_A = 1900 - 1697 + 36 = 239, E_A = 0.780; without compensation x = 436, E_A0 = 0.919.
- x_J = 1500 - 1900 - 36 = -436, E_J = 0.081 (J's own update uses published ratings only).
- K_A = 14.1 (latent sigma 55 at R = 1900, R6; v0.3's D3 gave 17.0), K_J = 40.0 (latent sigma 121.2). Today: D = 400, no cap; table 8.1.2 row 392-411: .92 / .08; K = 20 for A, 40 for J [V 1].

| Result | A today: 20 x (S - .92) | J today: 40 x (S - .08) | A under L2: K_A x (S - E_A) | J under L2: K_J x (S - E_J) |
|---|---|---|---|---|
| A wins | +1.6 -> +2 | -3.2 -> -3 | +3.1020 -> +3 | -3.2400 -> -3 |
| Draw | -8.4 -> -8 | +16.8 -> +17 | -3.9480 -> -4 | +16.7600 -> +17 |
| J wins | -18.4 -> -18 | +36.8 -> +37 | -10.9980 -> -11 | +36.7600 -> +37 |

Ledger lines for the game (annex T6):

| Result | transfer J -> A, (K_A + K_J)/2 x (S_A - E_A0) | created by unequal K, (K_A - K_J) x (S_A - E_A0) | created by compensation, K_A x (E_A0 - E_A) | sum of both changes |
|---|---|---|---|---|
| A wins | +2.1910 | -2.0979 | +1.9599 | -0.1380 |
| Draw | -11.3340 | +10.8521 | +1.9599 | +12.8120 |
| J wins | -24.8590 | +23.8021 | +1.9599 | +25.7620 |

E_A + E_J = 0.861; compensation creates K_A x (E_A0 - E_A) = +1.9599 points in this game whatever the result.

## 8 Worked example (ii): 2600 v 2100 and 2700 v 2100 (strong player White, latent sigma 45: K = 10.0 at 2600 and 10.0 at 2700 under R6; raw 9.55 and 9.56)

Today [V 1]: K = 10. 2600 v 2100: D = 500 counted as 400 (player below 2650): row 392-411, .92. 2700 v 2100: D = 600 used in full: row 560-619, .98. Rapid and blitz [V 2]: the plain 400 cap applies to both and, with a player above 2600 and a difference of 600 or more, the game is not rated.

| Player | Opponent | Today: D used, PD | Today: win / draw / loss | L2: x, band, E | L2: K_i | L2: win / draw / loss |
|---|---|---|---|---|---|---|
| 2600 | 2100 | 400, 0.92 | +0.8 / -4.2 / -9.2 | 536, 2300-2399, 0.932 | 10.0 | +0.6800 / -4.3200 / -9.3200 |
| 2700 | 2100 | 600, 0.98 | +0.2 / -4.8 / -9.8 | 636, 2400-2499, 0.957 | 10.0 | +0.4300 / -4.5700 / -9.5700 |

If the uncapped table were right, today's cap gives the 2600 player 10 x (.96 - .92) = +0.4 points per game against a 2100 in expectation (row 485-517 [V 1]); with a calibrated table the expected change of any pairing is zero (P4).

The 2650 cliff today v rung 2 (each beats a 2200 with White; today K = 10 [V 1]; rung 2 here uses K = 10.0):

| Winner | Today: gap used, PD, gain | L2: x, band, E, gain at K = 10.0 |
|---|---|---|
| 2649 | 400, 0.92, +0.8 | 485, 2400-2499, 0.905, +0.9500 |
| 2651 | 451, 0.94, +0.6 | 487, 2400-2499, 0.905, +0.9500 |
| 2700 | 500, 0.96, +0.4 | 536, 2400-2499, 0.926, +0.7400 |
| 2936 | 736, 1.0, +0.0 | 772, 2500-2599, 0.978, +0.2200 |

## 9 Monthly adjustment with a soft deadband (D7): a_t = clip(gamma_a sign(d_t) max(0, |d_t| - d_0), -a_cap, +a_cap), one decimal

| d_t | -12 | -8 | -5 | -3 | -2 | -1 | 0 | 1 | 2 | 2.5 | 3 | 5 | 6.6 | 7.2 | 8 | 11 | 12 | 20 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| a_t | -1.5 | -1.0 | -0.5 | -0.2 | +0.0 | +0.0 | +0.0 | +0.0 | +0.0 | +0.1 | +0.2 | +0.5 | +0.8 | +0.9 | +1.0 | +1.5 | +1.5 | +1.5 |

R3: the accrual of a_t is scaled by min(1, n_i / n_bar), n_i the player's rated games on the 12 lists up to t and n_bar the anchor cohort's mean of the same count (illustrative n_bar = 30): n_i = 1: factor 0.0333, accrual +0.0300 at a_t = +0.9, n_i = 6: factor 0.2000, accrual +0.1800 at a_t = +0.9, n_i = 15: factor 0.5000, accrual +0.4500 at a_t = +0.9, n_i = 30: factor 1.0000, accrual +0.9000 at a_t = +0.9, n_i = 60: factor 1.0000, accrual +0.9000 at a_t = +0.9.

Worked example (iii): m_t = 2004.6, m_hat_t = 2011.8, d_t = +7.2; a_t = (1/6) x (7.2 - 2.0) = 0.8667 -> +0.9. A player with game terms -2.4090, +5.8410, -8.7000 (sum -5.2680) and no carried balance: -5.2680 +0.9 = -4.3680 -> -4. Under R3 the balance accrued in that month is a_t x min(1, n_i / n_bar): with n_i = 24 and n_bar = 30, +0.9 x 0.8 = +0.7200, and the period change is -4.5480 -> -5.

Feedback loop in a stylised pool, d_{t+1} = d_t - a_t + drift (deflation: drift +1.3 points a month, illustrative; inflation: drift -1.0):

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
| 1 | P1 (1900) | P2 (1500) | 0.5 | 1700-1799 | 239 | 0.780 | -436 | 0.081 | -3.9480 | +16.7600 | +10.8521 | +1.9599 | 0 |
| 2 | P3 (2050) | P1 (1900) | 1 | 1900-1999 | 186 | 0.711 | -186 | 0.289 | +3.3813 | -4.0749 | -0.6936 | +0.0000 | 0 |
| 3 | P2 (1500) | P4 (1750) | 1 | 1600-1699 | -214 | 0.240 | 17 | 0.521 | +30.4000 | -11.8267 | +13.1480 | +5.4253 | 0 |
| 4 | P5 (2300) | P3 (2050) | 0.5 | 2100-2199 | 286 | 0.795 | -286 | 0.205 | -2.9500 | +3.4515 | +0.5015 | +0.0000 | 0 |
| 5 | P4 (1750) | P6 (1600) | 0 | 1600-1699 | 186 | 0.730 | -186 | 0.270 | -16.5710 | +29.2000 | +12.6290 | +0.0000 | 0 |
| 6 | P6 (1600) | P2 (1500) | 0 | 1500-1599 | -61 | 0.421 | -136 | 0.324 | -16.8400 | +27.0400 | +0.0000 | +10.2000 | 0 |
| 7 | P5 (2300) | P1 (1900) | 1 | 2100-2199 | 436 | 0.899 | -436 | 0.101 | +1.0100 | -1.4241 | -0.4141 | +0.0000 | 0 |
| 8 | P7 (1405) | P4 (1750) | 0 | 1500-1599 | -309 | 0.147 | 309 | 0.853 | -3.3222 | +3.3369 | +0.0147 | +0.0000 | 0 |
| 9 | P6 (1600) | P7 (1405) | 1 | 1500-1599 | 231 | 0.783 | -231 | 0.217 | +8.6800 | -4.9042 | +3.7758 | +0.0000 | 0 |
| 10 | P3 (2050) | U (unrated) | 1 | — | — | — | — | — | 0 (not rated) | — | 0 | 0 | 0 |
| 11 | P3 (2050) | P8 (1580) | 0.5 | 1800-1899 | 506 | 0.943 | -506 | 0.057 | 0 (counts the newly rated player as unrated) | +16.2581 | 0 | 0 | +16.2581 |

| player | R(t) | sigma | K_i | n | RX | sum of game terms | + a_t | rounded change | R(t+1) | rounding residual | status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| P1 | 1900 | 55 | 14.1 | 3 | 1900 | -9.4470 | -8.5470 | -9 | 1891 | -0.4530 | listed |
| P2 | 1500 | 121.2 | 40.0 | 3 | 1697 | +74.2000 | +75.1000 | +75 | 1575 | -0.1000 | listed |
| P3 | 2050 | 50 | 11.7 | 2 | 2050 | +6.8328 | +7.7328 | +8 | 2058 | +0.2672 | listed |
| P4 | 1750 | 70 | 22.7 | 3 | 1750 | -25.0608 | -24.1608 | -24 | 1726 | +0.1608 | listed |
| P5 | 2300 | 45 | 10.0 | 2 | 2300 | -1.9400 | -1.0400 | -1 | 2299 | +0.0400 | listed |
| P6 | 1600 | 120 | 40.0 | 3 | 1600 | +21.0400 | +21.9400 | +22 | 1622 | +0.0600 | listed |
| P7 | 1405 | 70 | 22.6 | 2 | 1405 | -8.2264 | -7.3264 | -7 | 1398 | +0.3264 | below 1400: shown as unrated (7.2.1 [V 1]); exit booked at R+ = 1398 |
| P8 | 1580 | 90 | 36.7 | 1 | 1580 | +16.2581 | +17.1581 | +17 | 1597 | -0.1581 | listed (first rated on list t; its late-rated game is one-sided, §8.2.4 [V 1]) |
| N1 | — | — | 40.0 | — | — | — | — | — | 1650 | — | newcomer: theta~ = 1650.3, round = 1650 >= 1400, published at 1650 |
| N2 | — | — | — | — | — | — | — | — | — | — | newcomer: theta~ = 1287.6, round = 1288 < 1400, not published (stays unrated; no ledger line) |
| Q1 | — | — | 40.0 | — | — | — | — | — | 1452 | — | former floor exit re-qualifies: theta~ = 1452.4, round = 1452 >= 1400, published at 1452 |
| Q2 | — | — | — | — | — | — | — | — | — | — | former floor exit re-qualifies: theta~ = 1381.2, round = 1381 < 1400, not published (stays unrated; no ledger line) |

Left side: list total after 15870 - before 14085 = +1785.
Right side: unequal K +39.8134 + compensation +17.5852 + one-sided (§8.2.4) +16.2581 + adjustments posted +7.2 (8 x 0.9) + rounding +0.1433 + entering 3102 - exits at post-update rating 1398 = +1785.0000.
Identity closes exactly: True. Without the one-sided line the residual would be +16.2581; booking the exit at R(t) = 1405 instead of R+ = 1398 would leave +7 points.

## 10b Further figures for the review fixes

- Table entry at x = 500 in band 2300-2399 (midpoint 2350): 0.918; the function at L = 2300 gives 0.920.
- R4 disclosure (R6): K_i = 14.1 published to one decimal at R = 1900 implies latent sigma_i between 54.80 and 55.00 (published-scale 45.22 to 45.38); a compensated junior with K_j = 14.1 and 0 < c_j < 300 then has theta~_j = RX_j + 25 + 1.2816 x 45.30 = RX_j + 83.1 (to within the rounding of c_j).
- R4 disclosure (R6): K_i = 27.1 published to one decimal at R = 1500 implies latent sigma_i between 76.79 and 76.94 (published-scale 63.36 to 63.48); a compensated junior with K_j = 27.1 and 0 < c_j < 300 then has theta~_j = RX_j + 25 + 1.2816 x 63.42 = RX_j + 106.3 (to within the rounding of c_j).
- A player at latent sigma 55 and R = 1900 who is inactive for 36 months with a process SD of 12 points a month (T7.2, illustrative) returns at sigma = sqrt(55^2 + 36 x 12^2) = 90.6, K = 37.4 (from 14.1).
- Steady-state K from activity under R6 (Davidson information at equal strength in latent units; one month's games before each list), at two latent process SDs:

  illustrative process SD 12 (T7.2):

| standard games a month | 1 | 2 | 3 | 4 | 5 | 8 |
|---|---|---|---|---|---|---|
| level 1700 | sigma 70.8, K 23.2 | sigma 59.4, K 16.4 | sigma 53.5, K 13.4 | sigma 49.7, K 11.6 | sigma 46.9, K 10.3 | sigma 41.6, K 10.0 |
| level 2300 | sigma 76.6, K 27.2 | sigma 64.3, K 19.3 | sigma 57.9, K 15.7 | sigma 53.8, K 13.6 | sigma 50.8, K 12.2 | sigma 45.0, K 10.0 |
| level 2700 | sigma 82.3, K 31.5 | sigma 69.1, K 22.3 | sigma 62.3, K 18.2 | sigma 57.9, K 15.8 | sigma 54.7, K 14.1 | sigma 48.5, K 11.1 |

  process SD 24, as fitted on history (c_theta = 2.0 times 12 at ages 25-45; SPEC-L1 3.7, analysis/OUTPUT_L1_history.md):

| standard games a month | 1 | 2 | 3 | 4 | 5 | 8 |
|---|---|---|---|---|---|---|
| level 1700 | sigma 99.4, K 40.0 | sigma 83.1, K 31.6 | sigma 74.8, K 25.8 | sigma 69.3, K 22.2 | sigma 65.3, K 19.8 | sigma 57.6, K 15.5 |
| level 2300 | sigma 107.7, K 40.0 | sigma 90.1, K 37.3 | sigma 81.1, K 30.4 | sigma 75.2, K 26.3 | sigma 70.9, K 23.4 | sigma 62.6, K 18.3 |
| level 2700 | sigma 115.8, K 40.0 | sigma 96.9, K 40.0 | sigma 87.3, K 35.4 | sigma 81.0, K 30.6 | sigma 76.4, K 27.2 | sigma 67.5, K 21.4 |

- Seed gate (T4.7, sigma~ <= 120): a newcomer's published-scale SD after n games against opponents of equal strength in one month, from the prior s_0 = 250 (latent), with the same-level information q^2 v per game and the opponents taken as known: level 1500: n = 5: 121.6, n = 6: 114.4, n = 8: 103.1, n = 10: 94.6; level 1800: n = 5: 126.3, n = 6: 119.1, n = 8: 107.7, n = 10: 99.1.

- Table 8.1.1 against the PROVISIONAL-FITTED rung-2 table (rung 2 alone keeps 8.1.1 for initial ratings, §8.2.3 [V 1]): the gap at which the table reaches a score p, at three band midpoints:

| p | 8.1.1 dp [V 1] | band midpoint 1650 | 2050 | 2450 |
|---|---|---|---|---|
| 0.75 | 193 | 205 | 231 | 267 |
| 0.92 | 401 | 429 | 469 | 520 |

- R8: two eligible juniors at equal published ratings use published ratings on both sides, so their expectations sum to one and the game creates no points. For the record, v0.3's rule (each one's compensation in the other's expectation) would have created:
  - (v0.3, superseded) two eligible juniors at equal published ratings (band 1500-1599), each with c = 100, K = 40: expectations 0.417 (White) and 0.324 (Black), sum 0.741; points created per game +10.4, whatever the result.
  - (v0.3, superseded) two eligible juniors at equal published ratings (band 1500-1599), each with c = 300, K = 40: expectations 0.185 (White) and 0.128 (Black), sum 0.313; points created per game +27.5, whatever the result.
- R2: a correctly rated player at R = 1400 whose latent distance from the anchor mean is kappa times the published one (kappa = 1.2120, anchor mean 2041.3, T7.2 illustrative) has theta~ - R = 0 under R2's theta~ = m_t + (s^ - m^_t) / kappa; v0.3's theta~ = s^ - d_t would have shown (kappa - 1)(R - m_t) = -136 points.
- R2: a correctly rated player at R = 1500 whose latent distance from the anchor mean is kappa times the published one (kappa = 1.2120, anchor mean 2041.3, T7.2 illustrative) has theta~ - R = 0 under R2's theta~ = m_t + (s^ - m^_t) / kappa; v0.3's theta~ = s^ - d_t would have shown (kappa - 1)(R - m_t) = -115 points.
- R2: a correctly rated player at R = 1600 whose latent distance from the anchor mean is kappa times the published one (kappa = 1.2120, anchor mean 2041.3, T7.2 illustrative) has theta~ - R = 0 under R2's theta~ = m_t + (s^ - m^_t) / kappa; v0.3's theta~ = s^ - d_t would have shown (kappa - 1)(R - m_t) = -94 points.
- Accrual against activity at a_t = +1.3 a month (R3, illustrative n_bar = 30): a player active under §7.2.2 with one game a year accrues 0.52 points a year (v0.3, without R3: 15.6); with 30 or more games a year, 15.6. A drift of 1.3 points a month spread over 30 games a year is 0.52 a game, so the accrual now matches the drain per game up to the anchor's mean activity.

## 11 Today's initial rating for the Appendix E.2 case of v0.1 (a Layer 0 test vector)

- Ra = (8000 + 2 x 1800)/7 = 1657.14; p = (3 + 1)/7 = 0.5714 -> .57; dp(.57) = 50 [V 1]; Ru = 1707.14 -> 1707. The rounding of p before the lookup is settled in SPEC-L0.

## 12 R1: the monthly spread ratio and the QC-review threshold

The spread ratio is the SD of published ratings divided by the SD of Layer 1's estimates for active adults (aged 25-45, rated, a game of the fit in the 12 months up to the month), measured on history in `analysis/OUTPUT_L1_history.md` (aggregate `analysis/aggregates/L1_history.json`); the corrected ratio adds the mean posterior variance to the latent variance, so that it does not move with activity alone. R1: if the measure moves beyond a published threshold two years running, the QC reviews; no automatic correction.

| time control | SD of the month-to-month change (ratio) | largest 12-month change since 2024-03 (ratio) | calendar-year means, corrected ratio | year-on-year changes, corrected ratio |
|---|---|---|---|---|
| blitz | 0.0105 | 0.027 | 2023: 0.714, 2024: 0.724, 2025: 0.727, 2026: 0.723 | 2023->2024 +0.009, 2024->2025 +0.003, 2025->2026 -0.004 |
| rapid | 0.0078 | 0.011 | 2023: 0.736, 2024: 0.730, 2025: 0.728, 2026: 0.718 | 2023->2024 -0.005, 2024->2025 -0.003, 2025->2026 -0.010 |
| standard | 0.0160 | 0.053 | 2023: 0.787, 2024: 0.739, 2025: 0.735, 2026: 0.717 | 2023->2024 -0.049, 2024->2025 -0.004, 2025->2026 -0.018 |

A ratchet held to kappa's annual cap of 0.05 moves the ratio by about ratio x cap / kappa = 0.747 x 0.05 / 1.212 = 0.031 a year in standard (the ratio varies roughly as 1/kappa), so a threshold on year-on-year changes must lie below that rate to catch it. PROVISIONAL rule: the calendar-year mean of the corrected ratio moves by more than 0.02 in the same direction two years running (a field of the parameter file, T7). On history every year-on-year change since the March 2024 reset is within ±0.02 (the largest, -0.018 in standard into 2026, covers January to September only); the change across 2023-2024 includes the reset itself.

