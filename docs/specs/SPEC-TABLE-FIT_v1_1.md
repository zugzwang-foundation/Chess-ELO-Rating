# SPEC-TABLE-FIT — fitting the expected-score table on the broadcast archive, v1.1: the slope by level

**Status: REVIEW — written before the fit (ELO-6 brief, Phase 1; `docs/decisions/D-0011_rulings-and-freeze-3.md`).** Author: The Zugzwang Authors · Licence: CC BY 4.0 (`docs/LICENSE-docs.md`) · Date: 2026-10-10. Extends `docs/specs/SPEC-TABLE-FIT_v1_0.md`, which stays in place because Freeze 1's table and column (b0) of the championship comparison were fitted under it (D-0011, reading 2). Everything v1.0 states holds unless this version changes it. The changes are in §2 (a slope that depends on the level, and a draw tail that may), §3 (the cutoff in code, the parameter file), §4 (the calibration rule by level band and gap with player-clustered intervals, the comparison with Freeze 1's table, the slope ratio of R32) and §5 (outputs). Every value it produces is PROVISIONAL-FITTED.

## 1 Data

As v1.0 §1: the Lichess broadcast archive [V 4] against FIDE's monthly lists [V 3], with the same sample rules, dates, duplicates and time controls. The sample is built with E2's own functions through E10's builder (`sample` in `analysis/e10_guard_extract.py`, which imports them unchanged from `analysis/e2_broadcast_extract.py`), so that it is E2's sample game for game. The data cutoff is enforced in code (D-0011, reading 3): no broadcast file later than 2026-09 is opened, and games dated after 2026-09-30 are dropped and counted.

## 2 Model and fit

For White against Black, with x = R_W − R_B, q = ln 10/400, L the midpoint of the 100-point level band of ⌊(R_W + R_B)/2⌋ (1450 below 1500, 2850 from 2800) and ℓ = (L − 2000)/400:

- κ_tc(L) = κ_tc · exp(λ_tc · ℓ);
- z = κ_tc(L) q (x + η_tc);
- ν = exp(α_tc + β_tc ℓ − γ_tc(L) |z|), with γ_tc(L) = γ_tc unless the condition of §4.6 adds the draw tail γ_tc(L) = γ_tc · exp(μ_tc · ℓ);
- P_W : P_D : P_L = e^{z/2} : ν : e^{−z/2}.

With λ_tc = 0 (and no tail) this is v1.0's model. The constraint of v1.0 holds in every band: 0 ≤ γ_tc(L) ≤ ½ at each of the fifteen band midpoints.

**Why the slope depends on the level.** A published gap is the gap in strength plus the noise of two ratings, so a slope fitted on published gaps is flattened by the share of the gap's variance that is noise. Players at the top play most, so their ratings carry the least noise and their gaps the least flattening; a single κ fitted over all levels is then too flat at the top and too steep below. E2's held-out months show that pattern: the fitted table under-predicts the favourite at levels of 2300 or more and slightly over-predicts below [E10 §5]. λ_tc lets the slope follow the level, in the same exponential form as the draw term's level dependence.

**The fit.** As v1.0 §2: maximum likelihood summed over cells of identical (x, band, outcome); a damped Newton method with the analytic score and a finite-difference Hessian, the gradient of z being z/κ for κ, ℓ z for λ and κ_tc(L) q for η, and the draw term's ℓ-weighted for μ; a parameter leaves the free set at a bound; it stops when no parameter moves by more than 10⁻⁷, or after 50 iterations; standard errors from the inverse observed information of the free parameters. Each fit starts from v1.0's fit of the same window (E2's parameters, `analysis/aggregates/E2_broadcast.json`) with λ = 0 (and μ = 0), so that the start is fixed and the fit is deterministic. A candidate step that breaks the constraint on γ_tc(L) is halved until it holds.

## 3 Protocol

As v1.0 §3: rolling origin, the first 24 months training only, each test month from 2025-01 to 2026-09 (21 months) forecast from a fit on the 36 months before it, Layer 0's forecast as in v1.0. Freeze 1's table is forecast with the parameters E2 fitted for each month (as E10 does), so that every comparison is on the same games, months and draw rates, and the script first reproduces E2's monthly sums for rung 2 and Layer 0 exactly. The published parameters are the fit on the last 36 months, 2023-10 to 2026-09, written to a new parameter file, params/table_fit_2026-10b.yaml; Freeze 1's file is untouched. Until Freeze 3 the file and the scripts are staged under `analysis/staging/` (D-0011, reading 1).

## 4 Measures and decision rules

1. **E2's measures**, for the v2 table against Layer 0 and against Freeze 1's table, on all test months: three-outcome log-loss, Brier score, ranked probability score; calibration by 50-point gap bin from the favourite's side, pooled over levels, with rules (a) and (b) of annex T8.2 applied by E2's report functions, imported unchanged; the colour split; the farming region (gap ≥ 400, level ≥ 2300) pooled.
2. **Do no harm**, by annex T8.2's rule, against Layer 0 and, by the same rule, against Freeze 1's table: the upper end of the 95 % interval of the log-loss difference (v2 minus the reference) at most 0.002 nats a game, and the game-weighted mean absolute residual over gap bins at most 0.005 above the reference's. "Better" when the interval lies below zero.
3. **Rule (a) by level band and gap** (annex T8.2, "by level band"; D-0011, reading 5): cells of the table's 100-point level band and the 50-point bin of the published gap from the favourite's side; every cell with at least 1,000 test games is tested by a one-sided z-test against the nearer bound of ±0.01, with a cluster-robust standard error over favourites (G/(G − 1) times the sum over the G favourites of their squared sums of deviations from the cell's mean, divided by the cell's games squared), Holm–Bonferroni across the tested cells of a time control at a familywise 5 %. The favourite's residual by level band and gap (REDTEAM_v1_0, V10-EXPLOIT-1) is printed for Freeze 1's table (before), the v2 table (after) and Layer 0, every cell with at least 200 games, with its clustered standard error.
4. **The favourite's residual by level band**, pooled over gaps (E10 §5), for the same three, with clustered standard errors and the month-block interval; and at levels of 2300 or more below a 400-point gap, the games no guard reaches.
5. **The farming region** (gap ≥ 400, level ≥ 2300), pooled: the favourite's residual with the month-block interval and the bootstrap over favourites (E6's `boot` and `boot_cluster`, imported unchanged), for the three. These are the inputs of the rule that re-decides the guard in Phase 2 (D-0011, R24 and reading 4); this specification decides nothing about the guard.
6. **The draw tail, added only on this condition.** After λ, a level pattern remains in a time control when the favourite's residual pooled over gaps in at least one 100-point level band with at least 1,000 test games is significantly outside ±0.01: a one-sided z-test against the nearer bound with the clustered standard error of item 3, Holm–Bonferroni across the bands of the time control at a familywise 5 %. Where it holds, γ_tc(L) of §2 is added in that time control, the rolling and final fits are redone with it, and both versions are reported; that time control's v2 table is then the one with the tail. The condition is evaluated once, on the model with λ, and not iterated.
7. **The stage-1 rule (R35).** The v2 table passes in a time control when E2's gate holds: rules (a) and (b) on the pooled gap bins, the do-no-harm check against Layer 0, and log-loss better than Layer 0's with the interval excluding zero, on at least 12 test months (E10's gate). Rule (a) by level band and gap is reported beside it.
8. **R32's slope ratio.** For each time control and each of the fifteen level bands, m_tc(L) = E′_8.1.2(0) / E′_v2(0), from the published parameters: E′_8.1.2(0) the least-squares slope of table 8.1.2's H entries over D = 0 to 100 [V 1], E′_v2(0) = κ_tc(L) q / (2(2 + ν_0(L))), ν_0(L) = exp(α_tc + β_tc ℓ) (D-0011, reading 7). Printed to two decimals; the verdict per time control is "no scaling" when every band lies within 0.9–1.1, "K scaled by m" otherwise (R32). The parameter file carries the ratios and the verdict.
9. **Intervals.** As v1.0: paired moving-block bootstrap by month, blocks of 3, 2,000 resamples, seed 20261009; the bootstrap over favourites resamples favourites with replacement, 2,000 resamples, the same seed.

## 5 Bias statement and outputs

- **Bias.** As v1.0 §5: broadcast events are stronger and more international than the rated pool, and a pass here supports the v2 table for the broadcast population only; the FIDE TRF archive settles it for the pool (annex T8.6).
- **Outputs**, staged under `analysis/staging/` until Freeze 3 and then moved to their permanent places (D-0011, reading 1):
  - the extraction script (needs `data/`) writes an aggregate of counts, sums and fitted values only;
  - the report script writes `docs/evidence/E11_table-by-level.md` and, with `--yaml`, the parameter file;
  - the table's functions (the published entry, the slope at an even gap, the ratio m) are library code, moved to `src/layer2/` at Freeze 3;
  - check (a) reruns the report and the parameter file; the extraction is rerun with `--all` where the data are.
