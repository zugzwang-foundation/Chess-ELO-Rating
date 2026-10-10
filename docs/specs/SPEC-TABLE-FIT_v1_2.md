# SPEC-TABLE-FIT — fitting the expected-score table on the broadcast archive, v1.2: the rules for the next yearly fit

**Status: REVIEW — written under ruling R50 (`docs/decisions/D-0012_pre-results-amendments.md`) in session ELO-7, Phase 0, before any table is fitted under it.** Author: The Zugzwang Authors · Licence: CC BY 4.0 (`docs/LICENSE-docs.md`) · Date: 2026-10-10. Extends `docs/specs/SPEC-TABLE-FIT_v1_1.md`, which stays in place because Freeze 3's parameter file and scripts were fitted and written under it (D-0012, reading 9). Everything v1.1 states holds unless this version changes it. **No table is fitted under this version before the proposal is submitted: Freeze 3's v2 table (`params/table_fit_2026-10b.yaml`, fitted under v1.1 on games of 2023-10 to 2026-09) is this year's table (R50).** The changes are in §1 (the window starts after the last rule change that moved published ratings), §2 (a more flexible slope by level and a colour term by level, as candidates), §3 (the candidates chosen on held-out log-loss, on months that are not then used to test the chosen table) and §4 (R32's slope ratio withdrawn). Every value it will produce is PROVISIONAL-FITTED. The evidence behind each change is E16 [E16].

## 1 Data

As v1.1 §1, with one change.

**The window starts after the last rule change that moved published ratings** (R50). On the March 2024 lists FIDE raised every rating below 2000 by round(0.4 × (2000 − R)), in all three time controls [E5]. Games before that list were played on another published scale, and a fit that pools both scales has no term for the change: refitted on games from 2024-03 only, with v1.1's model and test months, the v2 table misses less in the bottom bands (standard, 1500–1599: +0.023 against +0.029), one level band stays outside ±0.01 instead of two, and held-out log-loss improves by 0.00007 to 0.00037 nats a game in the three time controls [E16 §5]. So:

- every fit, the published one and each rolling fit of §3, uses only games whose list in force (v1.0 §1) is the March 2024 list or a later one, and at most the 36 months before the fit (v1.0 §3);
- if FIDE again changes published ratings by rule (a compression, a re-basing, a change to the initial-rating formula applied retroactively to listed ratings), the window restarts at the first list after that change, and the decision record of the fit names the change;
- while fewer than 36 months have accumulated, the window is shorter and the fit says so; the data cutoff of each fit is the last day of the month before it, enforced in code as v1.1 §1 enforces 2026-09-30.

## 2 Model

v1.1's model (§2) with two extensions. Each enters the published table only by the rule of §3.

1. **The slope by level: a more flexible form.** v1.1's κ_tc(L) = κ_tc · exp(λ_tc ℓ), which fits the top, flattens the bottom: favourites score above the v2 table by +0.029 at 1500–1599 and above it in four of the five bands below 2000, where Freeze 1's single κ was within ±0.01 [E16 §4]. The candidates are:
   - **E** (v1.1): κ_tc(L) = κ_tc · exp(λ_tc ℓ);
   - **P**, piecewise-linear by 200-point band: κ_tc at the knots L = 1500, 1700, 1900, 2100, 2300, 2500 and 2700, linear in L between adjacent knots and constant beyond the end knots, L the midpoint of the game's 100-point level band as in v1.1 (so 1450 takes the value at 1500 and 2850 the value at 2700); seven parameters in place of κ_tc and λ_tc.
   A further form may be added to the candidates only before the fit, in the fit's decision record.
2. **A colour term by level.** White's edge rises with the level while v1.1's η_tc is one number: in games at most 25 points apart White scores 0.530 below 1600 and 0.551 at 2600 or more, 0.016 to 0.021 above the v2 table at 2200 and above [E16 §2]. The candidate is η_tc(L) = η_tc + ζ_tc ℓ, entering z = κ_tc(L) q (x + η_tc(L)); the published table prints η_tc(L) per level band in whole points (annex T3.4).
3. **The draw tail** γ_tc(L) = γ_tc · exp(μ_tc ℓ) stays a candidate under v1.1 §4.6's condition, evaluated on the selection months of §3 only.

The constraint of v1.0 holds in every band (0 ≤ γ_tc(L) ≤ ½ at each band midpoint), and the fit is v1.1's (§2): maximum likelihood over cells of identical (x, band, outcome), a damped Newton method, deterministic starting values (the simpler candidate's fit with the added parameters at zero, or at the value that makes P equal to E at its knots).

## 3 Protocol: candidates chosen on held-out log-loss

As v1.1 §3 (rolling origin; each test month forecast from a fit on the months before it, within the window of §1), with one change, so that the form is not chosen on the months that then test it (REDTEAM_v1_0, ELO6-STAT-2):

- **Selection and confirmation months.** The test months of the window are split in two halves by date; the earlier half (the selection months) chooses among the candidates, the later half (the confirmation months) tests the chosen table and is not used to choose. With an odd number of test months the selection half takes the extra month.
- **The rule of choice**, applied in this order on the selection months: the slope form (E, then P against E); then the colour term by level (with against without); then the draw tail (v1.1 §4.6's condition). A more flexible candidate replaces the simpler one only when the month-block bootstrap interval of its three-outcome log-loss difference (the candidate minus the simpler, annex T8.5: blocks of 3 months, 2,000 resamples, seed 20261009) lies below zero; otherwise the simpler stays. "Improves held-out log-loss" (R50) means exactly this.
- **The published fit** is the chosen model fitted on the whole window up to the month before the fit; the confirmation months report its rolling counterparts.

## 4 Measures and decision rules

As v1.1 §4, with these changes:

1. **On the confirmation months.** E2's measures and rules (v1.1 §4.1–4.2), rule (a) by level band and gap (§4.3), the residual by level band (§4.4) and the farming region (§4.5) are reported on the confirmation months for the chosen table, against Layer 0 and against the table in force; on the selection months only as the record of the choice.
2. **What the cell test can detect.** Every tested cell of rule (a) by level band and gap is published with its minimum detectable deviation at 80 % power, alone and at Holm's first step, and the largest residuals of untested cells with at least 400 games are printed (annex T8.2; as E16 §4 does).
3. **R32's slope ratio is withdrawn** (R44). v1.1 §4.8 no longer applies: rung 2 uses today's K, and the parameter file carries no K scaling. The table's slope at an even gap may be printed for information.
4. **The guard** is not re-decided by the fit: the narrowed guard stays as frozen, and its exact shape is set on FIDE's data (R46, R47).

## 5 Bias statement and outputs

- **Bias.** As v1.1 §5: broadcast events are stronger and more international than the rated pool; a pass supports the table for the broadcast population only, and FIDE's TRF archive settles it for the pool (annex T8.6). A window that starts in March 2024 holds fewer games than v1.1's; the fit prints its games by level band and time control.
- **Outputs**, at the next yearly fit and not before submission: a new parameter file under `params/`, an extraction and a report registered with check (a) and a new evidence report; Freeze 3's files are not changed by it.
