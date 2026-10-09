# OUTPUT of analysis/v02_calculations.py (illustrative; all parameters PROVISIONAL)

Generated deterministically by the script; paste-source for the proposal v0.2 and the technical annex v0.2.

## 1 Expected-score table excerpt (standard; E to three decimals; rows x = 0..800 step 100; columns = level bands)

| x | <1600 | 1600-1799 | 1800-1999 | 2000-2199 | 2200-2399 | 2400-2599 | 2600-2799 | >=2800 |
|---|---|---|---|---|---|---|---|---|
| 0 | 0.500 | 0.500 | 0.500 | 0.500 | 0.500 | 0.500 | 0.500 | 0.500 |
| 100 | 0.622 | 0.617 | 0.612 | 0.605 | 0.597 | 0.589 | 0.579 | 0.570 |
| 200 | 0.730 | 0.722 | 0.712 | 0.700 | 0.687 | 0.671 | 0.655 | 0.637 |
| 300 | 0.815 | 0.805 | 0.793 | 0.779 | 0.763 | 0.744 | 0.723 | 0.700 |
| 400 | 0.876 | 0.867 | 0.855 | 0.841 | 0.824 | 0.804 | 0.781 | 0.756 |
| 500 | 0.918 | 0.910 | 0.899 | 0.886 | 0.871 | 0.852 | 0.829 | 0.804 |
| 600 | 0.946 | 0.939 | 0.930 | 0.919 | 0.905 | 0.889 | 0.868 | 0.845 |
| 700 | 0.964 | 0.958 | 0.951 | 0.942 | 0.931 | 0.917 | 0.899 | 0.879 |
| 800 | 0.976 | 0.971 | 0.966 | 0.959 | 0.949 | 0.938 | 0.924 | 0.906 |

Draw probability at equal strength (x = 0) by band midpoint, standard: 1500: 0.132, 1700: 0.167, 1900: 0.209, 2100: 0.258, 2300: 0.314, 2500: 0.376, 2700: 0.443, 2900: 0.511

nu by band midpoint, standard: 1500: 0.3050, 1700: 0.4015, 1900: 0.5286, 2100: 0.6959, 2300: 0.9162, 2500: 1.2062, 2700: 1.5880, 2900: 2.0907

## 2 Numerical checks of the expected-score function (standard parameters)

- Symmetry: max |E(x) + E(-x) - 1| over x in [-1200, 1200], all bands = 2.2e-16
- Monotonicity: min E(x+1) - E(x) over the same grid = 1.93e-05 (> 0)
- Logistic special case (nu = 0, kappa = 1): max |E(x) - 1/(1+10^(-x/400))| = 2.2e-16
- Band-edge step of the published table: max over x of |E(x; band b) - E(x; band b+1)| = 0.0256 (per band pair: 0.0096, 0.0118, 0.0144, 0.0172, 0.0201, 0.0229, 0.0256); at K = 20 that is at most 0.51 points in one game
- E at x = 400, 600, 800 for band 2200-2399 (midpoint 2300): 400: 0.824, 600: 0.905, 800: 0.949  (today's table 8.1.2: .92, .98, 1.0 [V 1])
- Draw probability at x = 0 for band 1600-1799 vs 2600-2799: 0.167 vs 0.443

## 3 Colour inside the expectation (standard, eta = 35 PROVISIONAL)

- Equal ratings at level 1700: E(White) = 0.542, E(Black) = 0.458; today's table gives .50 to each [V 1]. Expected gain per extra White game today at K = 20: +0.84 points; under L2: 0.00 by construction.
- Equal ratings at level 2000: E(White) = 0.539, E(Black) = 0.461; today's table gives .50 to each [V 1]. Expected gain per extra White game today at K = 20: +0.77 points; under L2: 0.00 by construction.
- Equal ratings at level 2500: E(White) = 0.531, E(Black) = 0.469; today's table gives .50 to each [V 1]. Expected gain per extra White game today at K = 20: +0.63 points; under L2: 0.00 by construction.

## 4 K_i from the posterior SD (K_min = 10, K_max = 40, sigma_new = 100, PROVISIONAL; Kalman gain sigma^2 ln10/400 shown for comparison)

| sigma_i | 30 | 45 | 55 | 70 | 85 | 100 | 150 |
|---|---|---|---|---|---|---|---|
| K_i | 12.7 | 16.1 | 19.1 | 24.7 | 31.7 | 40.0 | 40.0 |
| Kalman gain sigma^2 ln10/400 | 5.2 | 11.7 | 17.4 | 28.2 | 41.6 | 57.6 | 129.5 |

Per-period cap example: K_i = 26.1 and n = 40 games gives K_i x n = 1044.0; 700 / 40 truncated to tenths = 17.5; K_i = 16.5 and n = 40 gives 660.0 (no cap).

z_{0.90} = NormalDist().inv_cdf(0.90) = 1.2816 (the Gaussian quantile used in the eligibility test, T4.6); p_min = 0.90.

## 5 Worked example (i): established 1900 adult (White, sigma = 55) v 1500-listed junior (Black, sigma = 100) whom L1 rates at 1850

- Eligibility (AR-4): P(theta_J - R_J > tau) = Phi((1850 - 1500 - 50) / 100) = Phi(3.000) = 0.9987 >= 0.9: eligible. c_J = min(1850 - 1500, 300) = 300; RX_J = 1800.
- Level L = (1900 + 1500)/2 = 1700, band 1600-1799 (midpoint 1700), nu = 0.4015.
- A's gap x_A = 1900 - 1800 + 35 = 135; E_A = 0.656 (table). Without compensation x = 435, E = 0.884.
- J's gap x_J = 1500 - 1900 - 35 = -435; E_J = 0.116 (table; J's own update uses published ratings).
- K_A = 19.1 (sigma 55), K_J = 40.0 (sigma 100).

Today (standard list, rules as amended 1 October 2025 [V 1]): D = 400, not 'more than 400', so no cap; table 8.1.2 row 392-411: H = .92, L = .08; K = 20 for A, 40 for J.

| Result | A today: 20 x (S - .92) | J today: 40 x (S - .08) | A under L2: K_A x (S - E_A) | J under L2: K_J x (S - E_J) |
|---|---|---|---|---|
| A wins | +1.6 -> +2 | -3.2 -> -3 | +6.5704 -> +7 | -4.6400 -> -5 |
| Draw | -8.4 -> -8 | +16.8 -> +17 | -2.9796 -> -3 | +15.3600 -> +15 |
| J wins | -18.4 -> -18 | +36.8 -> +37 | -12.5296 -> -13 | +35.3600 -> +35 |

Ledger lines for the game (T6 decomposition; E_A0 = E_A without compensation):

| Result | transfer J -> A, (K_A+K_J)/2 x (S_A - E_A0) | created by unequal K, (K_A - K_J) x (S_A - E_A0) | created by compensation, K_A x (E_A0 - E_A) | sum of both changes |
|---|---|---|---|---|
| A wins | +3.4278 | -2.4244 | +4.3548 | +1.9304 = -2.4244 + +4.3548 |
| Draw | -11.3472 | +8.0256 | +4.3548 | +12.3804 = +8.0256 + +4.3548 |
| J wins | -26.1222 | +18.4756 | +4.3548 | +22.8304 = +18.4756 + +4.3548 |

Check: sum of changes - (creation by unequal K + creation by compensation) = +0.0000, +0.0000, +0.0000 (zero in every case).

Points created by compensation in expectation over A's own E_A: E_A + E_J = 0.772 (less than 1), expected creation per game = K_A x (E_A0 - E_A) = +4.3548.

## 6 Worked example (ii): 2600 v 2100 and 2700 v 2100 (strong player White, sigma = 45 so K = 16.1); today v L2

Today [V 1]: K = 10 (rating at or above 2400). 2600 v 2100: D = 500 > 400 and the player is below 2650, so D is counted as 400: table row 392-411, PD = .92. 2700 v 2100: D = 600, player at or above 2650, no cap: row 560-619, PD = .98. Rapid and blitz [V 2]: the plain 400 cap applies to both (PD = .92), and at 600 points or more with a player above 2600 the game is not rated.

| Player | Opponent | Today: D used, PD | Today: win / draw / loss | L2: x (with +35 colour), band, E | L2: K_i | L2: win / draw / loss |
|---|---|---|---|---|---|---|
| 2600 | 2100 | 400, 0.92 | +0.8 / -4.2 / -9.2 | 535, 2200-2399, 0.884 | 16.1 | +1.8676 / -6.1824 / -14.2324 |
| 2700 | 2100 | 600, 0.98 | +0.2 / -4.8 / -9.8 | 635, 2400-2599, 0.899 | 16.1 | +1.6261 / -6.4239 / -14.4739 |

Expected change under L2 = K x (P_W x (1 - E) + P_D x (0.5 - E) + P_L x (0 - E)) = K x (E - E) = 0 exactly (property P4). Today, the 2600 player's expectation is capped at .92 while the table's own uncapped value at D = 500 is .96 (row 485-517 [V 1]): if the uncapped table were right, each game against a 2100 would be worth 10 x (.96 - .92) = +0.4 points in expectation, which is the farming incentive; under L2 there is no cap and the incentive is zero.

The 2650 cliff today v L2 (each beats a 2200 with White; today K = 10 [V 1]):

| Winner | Today: gap used, PD, gain | L2: x, band, E, gain at K = 16.1 |
|---|---|---|
| 2649 | 400, 0.92, +0.8 | 484, 2400-2599, 0.845, +2.4955 |
| 2651 | 451, 0.94, +0.6 | 486, 2400-2599, 0.846, +2.4794 |
| 2700 | 500, 0.96, +0.4 | 535, 2400-2599, 0.866, +2.1574 |
| 2936 | 736, 1.0, +0.0 | 771, 2400-2599, 0.932, +1.0948 |

## 7 Worked example (iii): one month's global adjustment for one player (standard; a_cap = 1.5, gamma_a = 1/6, PROVISIONAL)

- Anchor cohort this month: published mean m_t = 2004.6, L1 latent mean m_hat_t = 2011.8, gap d_t = +7.2 points.
- a_t = clip(gamma_a x d_t, -a_cap, +a_cap) = clip(7.2/6 = 1.200, -1.5, +1.5) -> +1.2 (one decimal). a_{f,t} = 0 (disabled).
- Player's game terms this month: -2.4090, +5.8410, -8.7000; sum = -5.2680; plus a_t +1.2 = -4.0680; rounded (8.3.4) = -4.
- Had the player not played this month: no game terms, no a_t, rating unchanged (AR-5).

Feedback loop (AR-3) in a stylised pool: gap evolves as d_{t+1} = d_t - a_t + drift, drift = -(-1.3) = +1.3 points per month of deflation pressure on the gap (the research report's post-reform figure is about -16 points a year [R 5]):

| month | gap d_t | a_t |
|---|---|---|
| 0 | +0.0 | +0.0 |
| 1 | +1.3 | +0.2 |
| 2 | +2.4 | +0.4 |
| 3 | +3.3 | +0.6 |
| 6 | +5.1 | +0.9 |
| 12 | +6.9 | +1.2 |
| 24 | +7.5 | +1.3 |
| 36 | +7.5 | +1.3 |

Steady state: a_t -> +1.3 = the drift, gap -> about 7.8 points (= drift / gamma_a); the loop is stable because 0 < gamma_a < 1 and the cap 1.5 exceeds the drift 1.3. If the drift exceeded a_cap the gap would grow linearly and the monitoring report would show it.

## 8 Ledger identity (T6) checked on a synthetic month: 7 listed players, 8 rated games, one compensated junior, one game against an unrated player (not rated), one floor exit, one newcomer, a_t = +1.2

| game | White | Black | S_W | x_W | E_W | x_B | E_B | dR_W | dR_B | created by unequal K | created by compensation |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | P1 (1900) | P2 (1500) | 0.5 | 135 | 0.656 | -435 | 0.116 | -2.9796 | +15.3600 | +8.0256 | +4.3548 |
| 2 | P3 (2050) | P1 (1900) | 1 | 185 | 0.698 | -185 | 0.302 | +5.2850 | -5.7682 | -0.4832 | +0.0000 |
| 3 | P2 (1500) | P4 (1750) | 1 | -215 | 0.264 | -85 | 0.400 | +29.4400 | -9.8800 | +11.2608 | +8.2992 |
| 4 | P5 (2300) | P3 (2050) | 0.5 | 285 | 0.769 | -285 | 0.231 | -4.3309 | +4.7075 | +0.3766 | +0.0000 |
| 5 | P4 (1750) | P6 (1600) | 0 | 185 | 0.707 | -185 | 0.293 | -17.4629 | +28.2800 | +10.8171 | +0.0000 |
| 6 | P6 (1600) | P2 (1500) | 0 | -165 | 0.306 | -135 | 0.338 | -12.2400 | +26.4800 | -0.0000 | +14.2400 |
| 7 | P5 (2300) | P1 (1900) | 1 | 435 | 0.858 | -435 | 0.142 | +2.2862 | -2.7122 | -0.4260 | +0.0000 |
| 8 | P7 (1405) | P4 (1750) | 0 | -310 | 0.178 | 310 | 0.822 | -3.7024 | +4.3966 | +0.6942 | +0.0000 |
| 9 | P6 (1600) | P7 (1405) | 1 | 230 | 0.758 | -230 | 0.242 | +9.6800 | -5.0336 | +4.6464 | +0.0000 |
| 10 | P3 (2050) | U (unrated) | 1 | — | — | — | — | 0 (not rated) | — | 0 | 0 |

| player | R(t) | K_i | n | sum of game terms | + a_t | rounded change | R(t+1) | rounding residual | status |
|---|---|---|---|---|---|---|---|---|---|
| P1 | 1900 | 19.1 | 3 | -11.4600 | -10.2600 | -10 | 1890 | +0.2600 | listed |
| P2 | 1500 | 40.0 | 3 | +71.2800 | +72.4800 | +72 | 1572 | -0.4800 | listed |
| P3 | 2050 | 17.5 | 2 | +9.9925 | +11.1925 | +11 | 2061 | -0.1925 | listed |
| P4 | 1750 | 24.7 | 3 | -22.9463 | -21.7463 | -22 | 1728 | -0.2537 | listed |
| P5 | 2300 | 16.1 | 2 | -2.0447 | -0.8447 | -1 | 2299 | -0.1553 | listed |
| P6 | 1600 | 40.0 | 3 | +25.7200 | +26.9200 | +27 | 1627 | +0.0800 | listed |
| P7 | 1405 | 20.8 | 2 | -8.7360 | -7.5360 | -8 | 1397 | -0.4640 | below 1400: shown as unrated (7.2.1 [V 1]); EXIT at R+ = 1397 |
| N1 | — | 40.0 | 5 | — | — | — | 1650 | — | newcomer: first published rating (seed, T4.7) |

Left side: list total after = 12827, list total before = 12505, change = +322.
Right side: created by unequal K +34.9115 + created by compensation +26.8940 + adjustments posted +8.4 (7 x 1.2, including the exiting player) + rounding residuals -1.2055 + newcomers +1650 - exits at post-update rating 1397 = +322.0000.
Identity closes exactly: True. Note the exit is booked at R+ = R(t) + period change (1397); booking R(t) = 1405 instead would leave a residual of +8 points. The game against the unrated player changed nothing and appears in no line (T4.1).

## 9 Today's initial rating for the Appendix E.2 case of v0.1 (Layer 0 test vector, unchanged)

- Ra = (8000 + 2 x 1800)/7 = 1657.14; p = (3 + 1)/7 = 0.5714 -> .57; dp(.57) = 50 [V 1]; Ru = 1707.14 -> 1707. The rounding of p before the lookup is NOT VERIFIED (SPEC-L0 R-30).
- Under AR-5 the seed is the L1 posterior mean over all three time controls after the same five games; it is an output of the monthly fit and is not reproduced by this script.

