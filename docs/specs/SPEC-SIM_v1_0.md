# SPEC-SIM — The simulator: a synthetic rated pool with known strengths, v1.0

**Status: REVIEW — written before the code (ELO-5 brief, Phase 3), from annex T9 (then of the annex v0.4; now `docs/proposal/ELO-TECHNICAL-ANNEX_v1_0.md`, which cites this specification), with every departure from T9 stated in §10; revised once, after the pilot runs, in §3.2 (the noise, the junior factor, entries and exits), §3.4 (the Swiss pairing), §4.2 and §5 (Layer 1's proxy and θ̃) and §8, each revision listed with its reason in §11.** Author: The Zugzwang Authors · Licence: CC BY 4.0 (`docs/LICENSE-docs.md`) · Date: 2026-10-10. Code: `src/simulator/`; tests: `tests/test_simulator.py`; runs and evidence: `analysis/e9_simulator_run.py` → `analysis/aggregates/E9_simulator.json` → `analysis/e9_simulator_report.py` → E9. Every parameter below is PROVISIONAL; where a value is taken from a measurement, the measurement is named.

## 1 Purpose

The simulator measures what no backtest can: how far each rung brings published ratings to known true strengths, and what strategies absent from ordinary data gain. It runs Layer 0 (today's rules, SPEC-L0) and each rung of the ladder on the same simulated games, over ten simulated years after a burn-in, on several seeds and scenarios, and reports true-strength error by band, the slide at the top, the junior drain, newcomer convergence, federation offsets, the adversaries of T9.4 (farming, sandbagging, collusion, inactivity) and the false-alarm rate and power of R1's spread-ratio review (R19, R20). It is not engine code: nothing in it is published with a list.

## 2 Scales

- **True strength.** Each player has a latent strength θ in latent units (annex T1), the scale on which the outcome model has slope 1.
- **The published-scale truth.** θᴾ = 2000 + (θ − 2000)/κ₀, with κ₀ = 1.2120, the standard table's slope fitted on published ratings [E2]. On this scale the fitted table of rung 2 gives exactly the outcome probabilities of §3.3, so θᴾ is where a calibrated published rating belongs. Errors are R − θᴾ.
- **Level.** The published level can drift (deflation) while gaps stay right, so every error is reported twice: raw, and net of the level offset, the mean of R − θᴾ over the month's anchor cohort (§6.1).

## 3 The data-generating process

### 3.1 Players at the start

- **Pool.** N₀ = 20,000 players (PROVISIONAL; about a tenth of FIDE's active standard pool [E5]) in six federations of relative sizes 20 : 10 : 5 : 2 : 1 : 0.5 (T9.1).
- **Ages.** 35 % juniors aged 8–17 (uniform) and 65 % adults aged 18–65 with a density falling linearly to zero at 65 (T9.1).
- **Strength.** θᴾ ~ Normal(1450, 250²) for players aged 19 or less and Normal(1750, 280²) for adults. The adults' distribution puts about 1 % above 2400 and 0.1 % above 2600, the active list's shares (players rated 2400–2599 and 2600+ among those with a rated game, 2025–26 [E5]).
- **Published ratings at the start.** R = round(θᴾ + ε), ε ~ Normal(0, 50²), plus a federation offset b_f (§3.5); every player starts rated with FIDE's K state of a player with that rating and age (§4.1), adults with 30 or more games.

### 3.2 Dynamics, monthly

- **Drift.** θ moves by μ(a, θ) a month: A_a + B_a·(θ − 2000)/400 with Layer 1's fitted drift by age band (`analysis/OUTPUT_L1_history.md`: A = +16.10, +12.66, +6.60, +3.64, 0, −0.91, −1.79 latent points a month for the bands under 12, 12–15, 16–19, 20–24, 25–45, 46–60, over 60; B = +3.09, +0.90, −0.71, −0.25, 0, +0.11, +0.90). Layer 1 fitted it on broadcast juniors, the strongest improvers; for players under 25 the drift is multiplied by a personal factor τ_i ~ Gamma with mean τ̄ = 0.45 and coefficient of variation 0.5, τ̄ set in the pilot runs so that Layer 0's simulated juniors gain about what FIDE's lists show juniors gaining (median +24 to +38 points a year for players aged 18 or less, 2016–2026 [E5]; the simulated gains are printed beside E5's in E9).
- **Noise.** A random walk with SD c·p(a) a month, p(a) = 12 latent points a month to age 45 and 15 after (the adult values of SPEC-L1 §3.7's profile) and c = 1.0, the scale chosen for standard on held-out months in E8; juniors' greater spread of progress is carried by the factor τ_i, not by the noise (§11). Layer 1's history fit chose c = 2.0 at the edge of its grid; c = 2.0 is run as a sensitivity (§9).
- **Entries.** Each month 2.2 % of the active pool (players with a game in the last 12 months) enters, with E1's age shares of the 2025 newcomers (under 10, 10–14, 15–19, 20–29, 30–49, 50 or more: 8.1, 36.7, 19.4, 12.3, 13.5, 9.8 %) and true strength θᴾ ~ Normal(median, 200²) around the median first rating of the 2023 newcomers of that age (1120, 1156, 1286, 1407, 1406, 1435 [E1]), the last year before the 1400 floor truncated first ratings. Entrants play from their first month and are unrated until a rule of §4 rates them.
- **Exits.** Monthly hazard 0.3 %, 1.0 % for players with fewer than 30 games, doubled for ages 18–20 and above 60, and 3 % for players without a game in the last 12 months (PROVISIONAL, set in the pilot runs so that published newcomers are about a fifth of the active rated pool a year, as on FIDE's lists [E1], with the pool's size near its start; E9 reports the active rated pool year by year).
- **Activity.** Games a year ~ lognormal with median 10·exp(0.002·(θᴾ − 1800)), between 4 and 120, and SD of the log 0.8: about 10 rated games a year for club adults and 50–60 for players rated 2600 or more, as the lists show (E5 §5; E8 §4).

### 3.3 Outcomes

The D1 model in latent units with the standard table's fitted parameters converted as SPEC-L1 §3.2 converts them: z = q·(θ_W − θ_B + η^L), η^L = κ₀·η = 43.52, ν = exp(α + β·(L − 2000)/400 − γ·|z|), α = 0.2860, β = 0.4985, γ = 0.2915, L the midpoint of the 100-point band of the two players' mean θᴾ; P_W : P_D : P_L = e^{z/2} : ν : e^{−z/2} [E2]. White's edge and the draw rates by level are therefore E2's.

### 3.4 Events and pairings (T9.1)

- Each month a player plays Poisson(g/(12·8.5)) events, g the player's games a year.
- 85 % of a player's events are in the own federation, 15 % international (PROVISIONAL: Ghita finds more than 80 % of FIDE's games domestic ([R 5], p. 23); E7 finds 48 % cross-border in broadcast games, which are the international end [E7]).
- Of each month's federation pool, 20 % of the entries are grouped by rating into round-robins of 10 (Berger colours, 9 rounds); the rest are shuffled into Swiss events of 16 to 64 players, 9 rounds (70 %), 7 (15 %) or 5 (15 %).
- **Swiss pairing**, a greedy simplification of the Dutch system: round 1 by rating, top half against bottom half; in later rounds the highest-ranked unpaired player meets the player half its score group below it, else the nearest player it has not met in its group or below, a repeat only when none is left; a bye for the lowest-ranked player without one. Colours: the player with more Blacks gets White; equal histories alternate from the last game; never three of one colour in a row where avoidable.
- **Pairings and seeding use Layer 0's list** (the official list), for every rung: the shadow-list design of stage 2 (annex T11), so that every rung is scored on the same games.

### 3.5 Scenarios (T9.2, adapted)

1. **Baseline.** As above, with federation offsets b_f drawn once per seed from Normal(0, 35²), E7's spread of federation offsets on broadcast games [E7].
2. **Deflation with a junior wave.** Entries doubled, entrants' age shares moved towards the young (under 15: 70 %), the junior drift factor τ̄ × 1.5: a sustained deflationary pressure for rung 6.
3. **Isolated federations.** Federations 5 and 6 play 1 % of their games abroad; their published ratings start 100 points below (federation 5) and 60 above (federation 6) their true strength (T9.2, scenario 3).
4. **Adversaries.** The baseline with the agents of §7.
5. **Ratchet.** The baseline, with rung 2's slope κ lowered by its annual cap, 0.05 a year, from the second year of operation: the spread ratio of R1 must detect it (§8).

### 3.6 Burn-in and adoption

Months 1–36 run Layer 0 only (and Layer 1's proxy). At month 37 each rung's ledger starts from Layer 0's list as it stands, with no one-off adjustment (annex T11, stage 4), and runs for 120 months (ten years).

## 4 The ledgers

Every ledger rates the same games. Ratings, K and expectations are exact: integer arithmetic in thousandths of a point, rounded once per period half away from zero (§8.3.4 [V 1]).

### 4.1 Layer 0 (rung 1): today's rules exactly

SPEC-L0 re-implemented with integers for speed and tested against `src/layer0/` (`tests/test_simulator.py`): table 8.1.2 with the 400-point rule and the 2650 exemption (standard, current regulations); K 40/20/10 by R-18 to R-22 and K × n ≤ 700 (R-23); the period's change rounded once (R-25); games against unrated opponents do not count (R-13); newcomers rated from at least 5 games against rated opponents pooled over 26 periods with two hypothetical draws against 1800, a zero first event disregarded, at most 2200, published only from 1400 (R-26 to R-30); a rating below 1400 leaves the list (R-32) and the player re-qualifies as a newcomer. Not simulated: §8.2.4's one-sided late ratings, base corrections, unplayed games.

### 4.2 The rungs, each alone (everything else Layer 0's)

| Ledger | Rung | Rule (annex section; ruling) |
|---|---|---|
| R2 | 2 with the guard: RECOMMENDED NOW (with rung 1) | the published three-decimal fitted table with colour and draws at the level band of the two published ratings (T3.4), κ₀ and the other standard parameters [E2]; the guard of R17 (`src/layer2/guard.py`); today's K |
| R2U | 2 without the guard | the same, no guard: the guard's effect |
| R3 | 3, seeds | a newcomer's first rating is min(round(θ̃), 2200), published only from 1400, with σ̃ ≤ 120, at least 5 games against rated opponents, 3 opponents and 2 events in 26 months (T4.7); θ̃ from Layer 1's proxy (§5) |
| R4A | 4, K from the activity record | K_i(n) of R16 with σ_i from SPEC-K-ACTIVITY's recursion on the ledger's own list (E8's design and growth for standard) |
| R4L | 4, K from Layer 1's certainty | K_i(n) of R16 with σ_i from Layer 1's proxy |
| R5 | 5, junior compensation | c_j = min(300, max(0, round(θ̃_j − 1.2816 σ̃_j − R_j − 25))) for eligible juniors (aged 19 or less, at least 10 games against 5 opponents in 3 events in the window; one time control, so the information share is 1), in the expectation of opponents who are not eligible (T4.6; R5, R8, R18) |
| R6 | 6, the monthly adjustment | a_t from d_t over the anchor cohort, accrual scaled by activity (R3), posted in rated months (T4.5); judged by R15 |
| R7 | 7, the federation adjustment | a_{f,t} = clip(γ_a · n×/(n× + 2000) · φ_f, ±a_cap), φ_f the mean θ̃ − R − B over the federation's members of the anchor cohort (§11); enabled in the simulator only (T4.5) |
| ALL | 2 (guarded), 3, 4A, 5 and 6 together | the ladder below rung 7 |

## 5 Layer 1 in the simulator: a proxy

SPEC-L1's fit (36 months of games, refitted monthly) is too slow to rerun every month in pure Python. The simulator uses a forward filter with Layer 1's ingredients: per player a Gaussian estimate (mean, variance) in latent units; each month the mean moves by the pool's mean drift at the player's age (Layer 1's profile, times τ̄ under 25: the average a fitted Layer 1 estimates, without the personal factor, which no model can know) and the variance grows by SPEC-L1's noise profile; then the month's games update it by one Newton step of the D1 likelihood with the opponents' estimates held (Glicko-style; the game information of `layer1.model.game_terms`). The level is then fixed as annex T2.4 defines it: the common shift the step gave the anchor cohort is removed from every estimate, so that the cohort's mean latent strength does not drift. A new player starts from N(μ₀(a), 250²), μ₀ the entrants' mean by age (§3.2). θ̃ = m_t + (ŝ − m̂_t)/κ and σ̃ = σ/κ (R2), with m_t and m̂_t the anchor cohort's published and latent means and κ the slope of the D1 model fitted each January on the ledger's own rated games of the year before (annex T3.3 restricted to κ, the other parameters held at E2's). The proxy knows the pool's average dynamics: an optimistic assumption for the rungs that use it (§10).

## 6 Measurements

### 6.1 Every ledger

- **Anchor cohort:** active players aged 25–45 with at least 10 rated games in each of the two preceding years, re-formed every January (T2.4); its mean R − θᴾ is the ledger's level offset, reported monthly (the level drift; D_t is its twelve-month change on the panel).
- **True-strength error by band:** RMSE and mean of R − θᴾ, raw and net of the level offset, by true band (θᴾ below 1600, 1600–1999, 2000–2399, 2400 and above) and by age group, active rated players, over the last 24 months.
- **The slide at the top:** mean change a year of the published ratings of adults aged 25–45 whose θᴾ is 2400 or more at adoption (their strength has no drift), and the count of active players rated 2600 or more against the count whose θᴾ is.
- **The junior drain:** the residual S − E of adults (20 or more) against juniors (19 or less) and the points it moves, K·(S − E) a game, by the adult's band.
- **Newcomer convergence N₅₀:** for players first rated during operation and followed at least 24 months, the rated games after which |R − θᴾ − level offset| stays below 50 for the rest of the run; median and quartiles.
- **Federation offsets:** each federation's mean R − θᴾ minus the pool's, at adoption and after ten years.
- **Spread:** the SD of published ratings over the SD of θᴾ for active adults (the true spread ratio), and R1's measure, the noise-corrected spread ratio against Layer 1's proxy.
- **Ledger identity:** the change of the list total against the sum of its lines (T6), checked every month.

### 6.2 Rung 6 (R15)

d_t over the anchor cohort, its twelve-month change |d_t − d_{t−12}| from month 13 of operation against ±2 points (R15; D-0009, reading 1), and the level criterion |d_t| ≤ d₀ + |drift|/γ_a + 2; D_t reported.

## 7 The adversaries (T9.4), scenario 4

Each strategy is played by agents drawn at adoption from ordinary players of the stated kind; a matched control group of ordinary players of the same true strength is followed alongside. Measured under every ledger on the same games:

| Adversary | Behaviour | Measured |
|---|---|---|
| Farmer (30) | adults with θᴾ ≥ 2400 who, instead of their ordinary events, play monthly 9-round events whose fields are 400 to 800 points below them | points per game against the control's, by ledger |
| Sandbagger (30) | adults rated 2000–2300 who lose every game for 12 months, then play normally | the swing, and the net change after 24 months against the control's |
| Colluding pair (15 pairs) | a junior (K 40 today) and an adult rated 2400 or more (K 10) who play 2 arranged games a month that the junior wins | net points created per arranged game (T6, line 2) |
| Inactivity protector (30) | adults who stop playing when R − θᴾ first exceeds +40 and return 24 months later | R − θᴾ at return against at stop, and K at return |

## 8 R1's review threshold (R19, R20)

On R2's list, the noise-corrected spread ratio for active adults, monthly; its trailing twelve-month mean; the reference is that mean after the first twelve months of operation (D-0009, reading 5). Twenty paired runs (seeds 20262000 to 20262019), each with the baseline and the ratchet on the same games (ledgers L0 and R2 only). For each threshold θ_R1 in {0.005, 0.01, 0.015, 0.02, 0.025, 0.03, 0.04}: the share of baseline runs in which |mean − reference| exceeds θ_R1 at some month of the ten years (raw: the simulated pool's spread does change, so such a review is not false); the false-alarm rate of the noise alone, the same on each baseline series net of its own linear trend; and the months a ratchet at κ's annual cap takes to trigger on its own, from the paired difference (ratchet minus baseline). θ_R1 is calibrated as the smallest threshold whose noise-only false-alarm rate is at most 5 % (D-0009, reading 6), reported with the ratchet's time to trigger.

## 9 Runs

- Seeds: 5 per scenario (20261010 to 20261014); the baseline also with the noise scale c = 2.0 (§3.2).
- Determinism: one `random.Random(seed)` per run; every loop in a fixed order; two runs with the same seed give the same output byte for byte.
- `analysis/e9_simulator_run.py` runs every scenario and seed in parallel processes and prints aggregates only; `analysis/e9_simulator_report.py` writes E9. The run takes minutes, not seconds: check (a) treats it as a slow script, rerun with `--all` (`tools/checks/check_outputs.py`).

## 10 Departures from T9, and assumptions the data could not pin down

- **Scale and time controls.** 20,000 players at the start, not 38,500; standard only; 5 seeds, not 20.
- **Layer 1.** A forward filter with the true hyperparameters (§5), not SPEC-L1's 36-month fit: it cannot smooth, and it knows the dynamics. The table of rung 2 is not refitted yearly; its κ is fixed at κ₀ except in the ratchet scenario.
- **Pairings by Layer 0's list** for every rung (§3.4): a rung's effect on who meets whom is not modelled.
- **The true model is the fitted table.** The outcome model is E2's fit (§3.3), so rung 2's table is exactly right in the simulation, also at large gaps: the farming region's under-prediction measured on broadcast games [E6] is not in the simulated games, and the guard's benefit there cannot show; its cost can.
- **Assumptions the data could not pin down**, each reported with the results it drives: the noise scale c (E8's 1.0 against Layer 1's 2.0); the distribution of junior improvement (Layer 1's profile measured on broadcast juniors, scaled to the lists' junior gains); entrants' true strengths (2023 first ratings, before the floor); the domestic share of games (between E7's broadcast 52 % and Ghita's more than 80 %); the true federation offsets; exits; the activity distribution by level; the event and pairing structure; the adversaries' behaviour.

## 11 Revisions after the pilot runs

Each revision was made after a pilot run showed the first version could not answer its question; none was made after the runs of E9.

1. **The noise and the junior factor (§3.2).** With SPEC-L1's junior noise (25 points a month) and a personal factor of coefficient of variation 0.7 together, a junior's spread of progress was counted twice and the number of players whose true strength exceeds 2600 grew several-fold in ten years, far beyond the share of FIDE's active list [E5]. The noise is now the adult value at every age, and the factor's coefficient of variation 0.5.
2. **τ̄, entries and exits (§3.2)** were set in the pilot runs as §3.2 provides: τ̄ = 0.45, entries 2.2 % a month, the base exit hazard 0.3 %.
3. **The Swiss pairing (§3.4).** The first pairer repeated pairings far more often than a Dutch pairer would; the greedy version repeats a pairing only when a small field leaves no other choice (`tests/test_simulator.py` bounds it).
4. **Layer 1's proxy (§5).** With the full junior drift the proxy over-rated every junior, and without a level constraint its latent level drifted with its own lag; rung 6, which acts on that level, then inflated or deflated the published level by tens of points. The proxy now uses the pool's mean drift and the anchor's zero drift, as SPEC-L1 and annex T2.4 do.
5. **θ̃'s slope (§5).** With κ₀ in θ̃, every rung that uses θ̃ on Layer 0's table read the compression of Layer 0's published scale as a level error; production refits κ yearly on published ratings (annex T3.3), and so does the simulator.
6. **Rung 7's offset (§4.2).** Taken over all of a federation's players, φ_f read the over-rating of newly rated players under today's newcomer rule (E9, sections 2 and 3) as a deflation of every federation, and rung 7 deflated the whole pool. Over the federation's members of the anchor cohort, relative to the anchor as annex T2.5 defines it, it does not.
7. **R1's calibration (§8).** The simulated pool's spread keeps changing for reasons other than a ratchet, so a raw trigger is not a false alarm; the false-alarm rate is measured on the noise net of each run's trend, and the ratchet's detection on paired runs.

