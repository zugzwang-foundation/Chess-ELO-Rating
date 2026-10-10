# SPEC-L1 — Layer 1, the model, fitted on history, v1.0

**Status: REVIEW — written before the code was committed (ELO-4 brief, Phase 3.1), and revised once, after the synthetic tests of §7, in §3.2 (the outcome parameters) and §4.2 (the anchor imposed at the end; the drift refit bounded).** Author: The Zugzwang Authors · Licence: CC BY 4.0 (`docs/LICENSE-docs.md`) · Date: 2026-10-10. Implements annex T2 (written against v0.3, now `docs/proposal/ELO-TECHNICAL-ANNEX_v1_0.md`, which cites this specification) with the architect's rulings R2, R5 and R6 (`docs/decisions/D-0008_architect-rulings-elo-4.md`). Code: `src/layer1/`; tests: `tests/test_l1_model.py`, `tests/test_l1_solver.py`, `tests/test_l1_fit.py`, `tests/test_l1_data.py`, `tests/test_l1_outputs.py` (written first, pull request 3a); the history fit: `analysis/l1_history_extract.py`, reported in `analysis/OUTPUT_L1_history.md`. Every hyperparameter below is PROVISIONAL; every fitted value it produces is PROVISIONAL-FITTED on broadcast games.

## 1 Purpose and scope

Layer 1 estimates, for every player, a latent strength in each time control and its uncertainty, month by month. The annex's production Layer 1 is fitted on FIDE's tournament reports (TRF archive). This specification fits it on what is public now: the Lichess broadcast archive of over-the-board games between players with FIDE IDs, January 2023 to September 2026 [V 4], with FIDE's monthly lists for years of birth and published ratings [V 3]. Its outputs feed the tests of rungs 3 to 6 on history (E6) and the spread ratio of R1. Nothing it produces edits a published rating. §9 lists where it differs from the production model.

## 2 Inputs

### 2.1 Games

From the converted broadcast files `data/interim/broadcast/YYYY-MM.tsv` (`tools/data/convert_broadcasts.py`). A game enters when all of these hold:
- its variant is standard chess and its result is 1-0, ½-½ or 0-1;
- both players carry a FIDE ID;
- its tour's time control is classified standard, rapid or blitz by the rules of SPEC-TABLE-FIT §1 (the tour's majority class);
- its date (Date tag, else UTCDate, else the file's month, as SPEC-TABLE-FIT §1) is on or before 2026-09-30;
- it is not a duplicate (SPEC-TABLE-FIT §1: per date, players and result, the largest single-tour count is kept; a player without a FIDE ID is keyed by name);
- neither player belongs to the April 2026 batch (D-0008, R11; `analysis/fide_panel.py`).

Unlike the table fit, a player need not be rated on the list in force: Layer 1 uses every game (annex T4.1), and players with a FIDE ID but no published rating are the newcomers of rung 3.

### 2.2 Lists

FIDE's monthly standard, rapid and blitz lists (`data/interim/fide/<tc>/`): the year of birth, the published rating in each time control on the list in force for the game (the list of the tour's first month, or of the game's month for a tour longer than 30 days: SPEC-L0 R-11a), and the games fields (for the anchor panel). The federation field is not read (decision D4).

### 2.3 The published table

κ_tc and the draw parameters of the published table are read from `params/table_fit_2026-10.yaml` (read only; Freeze 1). κ_tc maps between the latent and the published scale (R2, R6, §3.6) and ν_0(L) gives the per-game score variance of R6.

### 2.4 The data cutoff

No broadcast file later than 2026-09 is opened, every game dated after 2026-09-30 is dropped by the loader and counted, and the fitting functions raise an error if any game dated after 2026-09-30 reaches them. No game of the 2026 U.S. Championships, which begin on 9 October 2026, can be read.

## 3 Model (annex T2.1, T2.2, T2.4, T2.7)

### 3.1 Strengths

s_{i,tc}(t) = θ_i(t) + μ_tc + δ_{i,tc}(t), for tc in {standard, rapid, blitz} and t a calendar month. θ_i is the shared skill; δ_{i,tc} the player's offset in tc. μ_standard ≡ 0; μ_rapid and μ_blitz are location constants fixed by the anchor constraint of each time control (§3.5), as annex T2.7 gives Chess960 a population offset. They cancel in every game's gap, so they affect no probability.

### 3.2 Outcomes (T2.1)

For a game in month t and time control tc between White w and Black b:
- x = s_{w,tc}(t) − s_{b,tc}(t) + η^L_tc, z = q·x, q = ln 10/400;
- ν = exp(α^L_tc + β^L_tc·ℓ − γ^L_tc·|z|), ℓ = (L − 2000)/400;
- P_W : P_D : P_L = e^{z/2} : ν : e^{−z/2}.

L is the midpoint of the 100-point level band (annex T3.4) of ⌊(R_w + R_b)/2⌋ from the list in force; when one player is unrated, the rated player's rating; when neither is rated, 1450. The slope in latent units is 1 by definition.

The outcome parameters are the published table's (§2.3) in latent units, held fixed during the fit: η^L_tc = κ_tc·η_tc, α^L_tc = α_tc, β^L_tc = β_tc, γ^L_tc = γ_tc. z is the log-odds of a decisive result in both models, so the table's draw term applies unchanged and only the colour term converts by κ. They are hyperparameters in the sense of T2.3, checked on held-out games (§4.6), not refitted: refitting them jointly with modal strengths, which are shrunk towards their priors, biases them and stops the sweeps converging (on the synthetic pool of A1-4 it moved blitz η from 25 to 10).

### 3.3 Dynamics (T2.2)

A player's states are kept at the months in which they have at least one game in the window (Whole-History Rating's time points [R 11]). Between consecutive time points k and k + 1, Δ months apart, with a the player's age band at k:
- θ_{k+1} = θ_k + Δ·μ(a, θ_k) + ε, ε ~ N(0, Δ·σ_θ(a)²), with μ(a, θ) = A_a + B_a·(θ − 2000)/400 and A_a = B_a = 0 for ages 25–45 (T2.4);
- δ_{tc,k+1} = ρ_tc^Δ·δ_{tc,k} + ξ, ξ ~ N(0, ω_tc²·(1 − ρ_tc^{2Δ})/(1 − ρ_tc²)).

Age bands: under 12, 12–15, 16–19, 20–24, 25–45, 46–60, over 60 (T2.2); the age is the month's calendar year minus the year of birth; a player without a year of birth is treated as aged 25–45 (T2.2).

### 3.4 Priors at a player's first time point

- **No federation.** No prior, seed or default depends on the federation (D4).
- **A newcomer** (not rated in any time control on the list in force at the first game): θ ~ N(μ_0(a), s_0²), s_0 = 250 (T2.2). μ_0(a) by age band is the median first published rating of the 2025 newcomers of that age [E1], mapped to the latent scale by §3.6 (PROVISIONAL).
- **A rated player.** The annex starts each player at the window's start from the summary of the previous month's fit (T2.3, fixed-lag smoothing). A history fit has no previous fit, so the published rating stands in for it: θ ~ N(θ_list, s_list²), θ_list = m_ref,tc + κ_tc·(R_tc − m_ref,tc) − μ_tc, with tc standard if the player is rated in standard on the list in force, else rapid, else blitz; m_ref,tc the anchor panel's published mean at t_ref; s_list = 120 (PROVISIONAL). Before the fit μ_tc is not known; the prior uses m_ref,tc − m_ref,standard in its place. This is a stated substitution, not a feature of the production model.
- **Offsets.** δ_{tc} ~ N(0, ω_tc²/(1 − ρ_tc²)), the stationary prior (T2.2).

### 3.5 Anchoring (T2.4)

The panel of time control tc: players aged 25–45 in the calendar year of t_ref, rated in tc on the list at t_ref and on the list 24 months earlier, with at least 10 rated games in tc in each of the two 12-month periods before t_ref (the games fields of the lists; E1's anchor cohort, PROVISIONAL), and with at least one game of the fit in tc. The annex's three calendar years would put the 2020–21 pandemic years into the panel's history. t_ref = 2025-01, the January re-basing date nearest the middle of the window (PROVISIONAL); a single historical fit needs no chain-linking.

Constraint: the panel's mean ŝ_{i,tc}(t_ref) equals its mean published rating on the list of t_ref. In standard it fixes the location of θ (a common shift of every θ); in rapid and blitz it fixes μ_tc. The drift constraint μ ≡ 0 for ages 25–45 fixes the level over time.

### 3.6 Scales (R2)

The published-scale estimate is θ̃_{i,tc}(t) = m_tc(t) + (ŝ_{i,tc}(t) − m̂_tc(t))/κ_tc, where m_tc(t) and m̂_tc(t) are the panel's published and latent means at month t over the members present (R2). Its standard deviation on the published scale is σ̃ = σ/κ_tc. The inverse map, ŝ = m̂ + κ_tc·(R − m), is used for initial values and for μ_0; at t_ref, m̂ = m.

### 3.7 Hyperparameters

| Symbol | Meaning | Value (PROVISIONAL) |
|---|---|---|
| σ_θ(a) | monthly SD of the random walk of θ by age band | c_θ × (25, 25, 20, 14, 12, 15, 15) points |
| c_θ | scale of σ_θ | chosen from {0.5, 1, 2} by §4.6 |
| ρ_tc | persistence of δ_tc a month | 0.97 |
| ω_tc | innovation SD of δ_tc | chosen from {4, 8, 16} points by §4.6 (one value for the three time controls) |
| s_0, s_list | prior SD of a newcomer's and of a rated player's first θ | 250, 120 points |
| window | months fitted | the history fit of §8: every month of the archive, 2023-01 to 2026-09, as the ELO-4 brief asks; the rolling fits of the rung tests: 36 months ending with the last month before the list (fewer at the start of the archive), annex T2.3 |
| ridge on A_a, B_a | prior SDs of the drift parameters | 10 points a month; 2 points a month per 400 points |

The values of σ_θ's profile are the annex's illustrative T7.2 values; c_θ and ω are chosen on held-out games, as T2.3 asks, from the grids above, fixed here before any fit.

## 4 Estimation (T2.3)

### 4.1 Objective

Maximum a posteriori over every player's states and the drift parameters, given the hyperparameters and the outcome parameters of §3.2.

### 4.2 Sweeps

- Players are visited in ascending FIDE ID. For each, one Newton step on all its states (θ, δ_standard, δ_rapid, δ_blitz at each time point; 4 numbers each), with the opponents' current strengths fixed.
- The gradient is exact. The Hessian is exact for the prior and dynamics terms and uses the expected (Fisher) information for the game terms, so it is positive definite. The block-tridiagonal system (4 × 4 blocks) is solved exactly by block elimination. A step that raises the player's negative log posterior is halved, at most five times, and otherwise skipped.
- After each sweep, one exact Newton step along the common shift of every θ, the one direction the likelihood cannot see; only the priors and the level-dependent drift act on it, so the step lowers the negative log posterior and removes the slowest mode of the sweeps.
- Every fifth sweep, the drift parameters (A_a, B_a for the six age bands other than 25–45) are refitted by weighted least squares on the modal increments of θ between consecutive time points, with weights Δ/σ_θ(a)² and weak ridge priors A_a ~ N(0, 10²) and B_a ~ N(0, 2²) (points a month; PROVISIONAL); an expectation–maximisation step that ignores the posterior covariance of the increments, stated as an approximation. The refits stop when neither parameter changes by more than 0.05, or after six rounds.
- The sweeps stop when no strength moves by more than 0.1 point in a sweep after the last drift refit, or after 150 sweeps; the tolerance reached is reported.
- The anchor constraint (§3.5) is then imposed once, exactly: a common shift of every θ and of every prior mean, which leaves the posterior unchanged except through the small level-dependent drift term, and μ_rapid, μ_blitz set from their panels. Imposing it after every sweep instead fights the priors, which pull every θ back each sweep, and the sweeps never settle.

### 4.3 Posterior standard deviation (Laplace)

The covariance of a player's last state is the inverse of the last eliminated block of its system at the mode. At a later month the dynamics of §3.3 propagate it (drift slope, random-walk variance, the offsets' decay). σ_{i,tc} is the SD of s_{i,tc} = θ + δ_tc. Two cautions of T2.3 hold: σ is conditional on the opponents' estimates, so it understates the marginal SD in small, weakly connected pools; and its calibration is measured on held-out games (§5.5), not corrected.

### 4.4 Information share (R5)

For player j and time control tc at a list date: P_all = 1/σ_{j,tc}² from §4.3; P_tc from the same system with the game terms of the other two time controls removed; P_0 with no game terms (priors and dynamics only). The share is (P_tc − P_0)/(P_all − P_0), clipped to [0, 1], and 1 when j has games in tc only.

### 4.5 Forecasts

For a month after the fit, each player's state at the last time point is propagated by §3.3 and the probabilities of §3.2 are computed at the propagated means (plug-in; the posterior SDs are not integrated over). A player first seen in the forecast month has the prior of §3.4.

### 4.6 Choosing c_θ and ω

Fit on 2023-01 to 2024-09 and score every game of 2024-10 to 2024-12 by the three-outcome log-loss of §4.5. First c_θ in {0.5, 1, 2} with ω = 8, then ω in {4, 16} with the best c_θ; keep the lowest mean log-loss. These months precede every test month of E6, which starts in 2025-01.

## 5 Outputs, for a list date (the first day of month t + 1, from games up to the end of month t)

### 5.1 Per player and time control

- ŝ, σ (latent units), θ̃ and σ̃ (published scale, §3.6);
- games, distinct opponents and distinct tours in the window in that time control, and the information share (§4.4);
- K_i by R6: K_i = clip(q·σ_i²/(κ_tc·(1 + q²·σ_i²·v_tc)), K_min, K_max), K_min = 10, K_max = 40, with σ_i in latent units and v_tc = 1/(2(2 + ν_0(L))), the table's per-game score variance at x = 0 in the band of the player's published rating (of θ̃ for an unrated player) (D-0008, reading 5);
- for a junior (list year minus year of birth at most 19): the gates of annex T4.6 (at least 10 games in tc, against at least 5 opponents, in at least 3 tours, all counted on broadcast games) and of R5 (information share at least 0.5); c_j = min(c_cap, max(0, round_FIDE(θ̃ − z·σ̃ − R_j − τ))), z = 1.2816, τ = 25, c_cap = 300, R_j the published rating; 0 when a gate fails or the junior is unrated;
- for an unrated player: the seed of annex T4.7, min(round_FIDE(θ̃), 2200), published only if round_FIDE(θ̃) ≥ 1400, σ̃ ≤ 120 and the player has at least 5 games against rated opponents, with at least 3 opponents in at least 2 tours, within 26 months.

### 5.2 Anchor and adjustment, per time control and month

The panel's size, m_t, m̂_t, d_t = m̂_t − m_t, and a_t = clip(γ_a·sign(d_t)·max(0, |d_t| − d_0), ±a_cap), one decimal, d_0 = 2, γ_a = 1/6, a_cap = 1.5 (annex T4.5; all PROVISIONAL).

### 5.3 Spread ratio (R1), per time control and month

For active adults (aged 25–45, rated on the list, at least one game of the fit in the 12 months up to the month): SD of published ratings ÷ SD of ŝ (latent units); and the same with the denominator sqrt(Var(ŝ) + mean σ²), an estimate of the SD of the latent strengths themselves.

### 5.4 Fit record

The hyperparameters, the outcome and drift parameters, μ_rapid and μ_blitz, sweeps and the tolerance reached, the log posterior, the in-sample log-loss, the number of games and players, the connected components of the game graph, Cov(θ, δ_tc) and the correlation of ŝ across time controls for players with at least 10 games in both (T2.4, T7).

### 5.5 Calibration of σ

On held-out games: the SD of the standardised forecast residual (S − E)/sqrt(Var(S)) by decile of the players' σ; a value near 1 means σ adds no unexplained noise.

## 6 Determinism

Games are sorted by date, tour and the two players' FIDE IDs (duplicates resolved first, ties keeping the order of round and game URL); players are swept in ascending FIDE ID; no step is random; the stopping rule and iteration caps are fixed. The same input gives the same output byte for byte on the same machine, and within |Δŝ| ≤ 0.1 point across machines (annex T5, P6). The committed outputs are reproduced by check (a) with `--all`.

## 7 Acceptance tests (written before the code; standard library and pytest only, synthetic data, run by check (b))

| Test | Criterion | Module |
|---|---|---|
| A1-1 | Outcome model: the probabilities equal SPEC-TABLE-FIT §2's form with κ = 1, sum to 1, E(x) + E(−x) = 1 when η = 0, and dE/dz at z = 0 equals the score variance there | `tests/test_l1_model.py` |
| A1-2 | A player's analytic gradient equals central finite differences (relative 1e-6); the game information is positive | `tests/test_l1_model.py` |
| A1-3 | The block solver equals dense Gaussian elimination on random symmetric positive definite block-tridiagonal systems (1e-9), its last block inverse equals the dense inverse's, and the smoothed covariances of every state (§5.3) equal the dense inverse's diagonal blocks | `tests/test_l1_solver.py` |
| A1-4 | Recovery on a synthetic pool drawn from the model (known parameters, three time controls): correlation of ŝ with the true strength at least 0.9 for players with at least 20 games; SD of (ŝ − s)/σ between 0.7 and 1.4 | `tests/test_l1_fit.py` |
| A1-5 | After a fit the panel's mean ŝ at t_ref equals its published mean within 1e-6 in each time control; A = B = 0 for ages 25–45 | `tests/test_l1_fit.py` |
| A1-6 | Two fits of the same input are identical | `tests/test_l1_fit.py` |
| A1-7 | The loader refuses a broadcast file later than 2026-09 and drops games dated after 2026-09-30; the fitter raises on such a game | `tests/test_l1_data.py` |
| A1-8 | No federation: the game records carry no federation and no function takes one | `tests/test_l1_data.py` |
| A1-9 | R6: K is non-decreasing in σ, lies in [K_min, K_max], equals D3's formula when κ = 1 and ν_0 = 0, and carries the factor 1/κ before clipping | `tests/test_l1_outputs.py` |
| A1-10 | R2: θ̃ = m + (ŝ − m̂)/κ, which is ŝ − d_t when κ = 1 | `tests/test_l1_outputs.py` |
| A1-11 | R5: the information share lies in [0, 1] and is 1 for a player with games in one time control; c_j is 0 when the share is below 0.5 or a gate fails; c_j follows annex T4.6 | `tests/test_l1_outputs.py` |
| A1-12 | Seeds follow annex T4.7: none below 1400 or with σ̃ above 120; at most 2200 | `tests/test_l1_outputs.py` |

## 8 Coverage (Phase 3.3)

The coverage report counts, at the list of October 2026 and by the bands of E5 and the age groups of E5, the players with a usable estimate (σ̃ ≤ 100, PROVISIONAL) against the active rated players on that list (at least one rated game in the 12 months up to it), and the juniors who pass the gates of §5.1 and the newcomers with a seed. It states what the strong-player bias of the broadcast sample [E2] means for juniors and newcomers.

## 9 Differences from the production model, and limits

- Broadcast games only: stronger and more international than the pool [E2]; most of a player's FIDE-rated games are missing, so gates counted on broadcast games understate them.
- Published ratings stand in for the previous fit's summary at the window start (§3.4).
- σ is conditional on the opponents (§4.3); the expectation-propagation alternative of T2.3 is not implemented.
- The drift step ignores posterior covariances (§4.2); c_θ and ω come from small grids (§4.6); μ_0 is fixed from E1.
- A per-time-control location μ_tc is added (§3.1) so that each time control's anchor can hold; the annex states it only for Chess960 (T2.7).
- NOT VERIFIED: the classification of broadcast games as FIDE-rated (a broadcast game is not marked as rated); dating undated games by their file's month (SPEC-TABLE-FIT §1).
