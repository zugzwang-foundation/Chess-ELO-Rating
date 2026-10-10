# SPEC-TABLE-FIT — fitting the expected-score table on the broadcast archive, v1.0

**Status: REVIEW — written before the fit (ELO-3 brief, Phase 4.2).** Author: The Zugzwang Authors · Licence: CC BY 4.0 (`docs/LICENSE-docs.md`) · Date: 2026-10-09. Implements decisions D1, D2 and D12 (`docs/decisions/D-0005_architect-decisions-v0.3.md`), annex T3 and T8 (of v0.3, now `docs/proposal/ELO-TECHNICAL-ANNEX_v0_4.md`). Every value it produces is PROVISIONAL-FITTED.

## 1 Data

- **Games.** The Lichess broadcast archive of over-the-board games, monthly files January 2023 to September 2026 [V 4]; CC BY-SA 4.0, attributed wherever a result is used. Game headers only (`tools/data/convert_broadcasts.py`); nothing game-level is committed.
- **Ratings.** FIDE's monthly lists of the game's time control [V 3], analysed and never redistributed.
- **The sample.** A game enters when all of the following hold:
  - its variant is standard chess and its result is 1-0, ½-½ or 0-1;
  - both players carry a FIDE ID;
  - both are rated on the list of that time control in force for the game: the list dated the first day of the month in which the broadcast tour starts, or of the game's month when the tour spans more than 30 days (SPEC-L0 R-11a; Title Regulations §1.1.4 [VT 1]).
- **Dates.** A game is dated by its Date tag, or by its UTCDate tag (forms YYYY.MM.DD, YYYY-MM-DD and DD.MM.YYYY are read). A game with neither is dated by the month of the monthly file it comes from. That is a reading, NOT VERIFIED: the page states one-month files for the standard-game exports [V 4], not for broadcasts; the share of dated games that fall in their file's month is reported.
- **Duplicates.** The same game broadcast in two tours counts once: within one (date, White, Black, result) key, the larger count of any one tour is kept.
- **Time control.** The tour's majority class over its games. Each game is classified from its TimeControl tag in PGN form, else from the first clock readings, else from free text, using base + 60 × increment [V 1] [V 2]:
  - standard: at least 60 minutes;
  - rapid: more than 10 and less than 60;
  - blitz: more than 3 and at most 10;
  - from clocks alone: 55 minutes or more is standard, 13 to 55 rapid, 2.5 to 10.5 blitz.

## 2 Model and fit (annex T3.1, T3.3)

For White against Black, with x = R_W − R_B and q = ln 10/400:
- z = κ q (x + η);
- ν = exp(α + β (L − 2000)/400 − γ |z|);
- P_W : P_D : P_L = e^{z/2} : ν : e^{−z/2}.

Here L is the midpoint of the 100-point level band of ⌊(R_W + R_B)/2⌋, the value at which the published table is evaluated (T3.4). The parameters (κ, η, α, β, γ) of each time control maximise the likelihood, with γ ∈ [0, ½]:
- the likelihood is summed over cells of identical (x, band, outcome);
- the method is a damped Newton method with the analytic score of T3.3 and a finite-difference Hessian; γ leaves the free set at a bound;
- it stops when no parameter moves by more than 10⁻⁷, or after 50 iterations;
- standard errors come from the inverse observed information of the free parameters.

## 3 Protocol (annex T8.3, D12)

- **Rolling origin.**
  - The first 24 months, 2023-01 to 2024-12, are training only.
  - For every test month m from 2025-01 to 2026-09, the fit uses months m − 36 to m − 1 and forecasts every game of m.
  - A decision needs at least 12 test months.
- **Layer 0 forecast.**
  - FIDE's own expected score for White, computed by the ratified engine (`src/layer0`: table 8.1.2, the 400-point rule with the 2650 exemption in standard from 1 October 2025, the plain cap in rapid and blitz).
  - It is split into three outcomes with the draw rate of the game's 100-point level band in the training months.
  - E is clipped to [0.002, 0.998] and the draw share is capped so that no outcome falls below 0.001, keeping the log-loss finite where the table prints 1.0 or .00.
- **Published parameters.** The fit on the last 36 months, 2023-10 to 2026-09, written to `params/table_fit_2026-10.yaml` with source, dates and game counts, labelled PROVISIONAL-FITTED.

## 4 Measures and decision rules (annex T8.2, T8.4, T8.5)

- **Descriptive measures.** On every sample game of each time control, all months:
  - coverage: the share with both FIDE IDs, and with both ratings found;
  - the time-control mix;
  - table 8.1.2's calibration by 50-point gap: the favourite's score against the table entry and against the PD FIDE uses;
  - White's score at equal ratings (|x| ≤ 25) by 200-point level band;
  - the draw rate by level band;
  - per-player colour imbalance per event: Whites minus Blacks for every player with at least 5 games in a tour.
- **Out-of-sample scores** (rung 2 against Layer 0, over all test months):
  - three-outcome log-loss;
  - Brier score on the expected score;
  - ranked probability score;
  - calibration by 50-point bins of |x| to 1000, from the favourite's side, separately by colour and in the farming region (|x| ≥ 400, L ≥ 2300).
- **Calibration rule.** It holds when both of these hold:
  - (a) no bin with at least 1,000 games has a mean residual S − E significantly outside ±0.01 (one-sided z-tests against the nearer bound, Holm–Bonferroni at a familywise 5 %);
  - (b) the weighted least-squares slope of bin mean scores on bin mean expectations lies in 0.95–1.05, with standard error below 0.02; otherwise (b) is inconclusive.
- **Do-no-harm check.** It holds when both of these hold:
  - the upper end of the 95 % interval of the log-loss difference (rung 2 minus Layer 0) is at most 0.002 nats a game;
  - the game-weighted mean absolute calibration residual exceeds Layer 0's by at most 0.005.
- **Rung 2 passes** when, in addition, its log-loss is better than Layer 0's with the interval excluding zero.
- **Intervals.** Paired moving-block bootstrap by month: blocks of 3 consecutive test months, 2,000 resamples, seed 20261009.
- **Reporting.** Every bin carries its game count and minimum detectable deviation.

## 5 Bias statement and outputs

- **Bias.** Broadcast events are stronger and more international than the rated pool. Every result is reported beside the sample's rating distribution and that of the players with games on the same months' lists. A pass here supports rung 2 for the broadcast population only; the FIDE TRF archive settles it for the pool (T8.6).
- **Outputs.**
  - `analysis/e2_broadcast_extract.py` (needs `data/`) writes `analysis/aggregates/E2_broadcast.json` (counts and fitted values only).
  - `analysis/e2_broadcast_report.py` writes `docs/evidence/E2_broadcast-calibration.md` and `params/table_fit_2026-10.yaml`.
  - Check (a) reruns both.
