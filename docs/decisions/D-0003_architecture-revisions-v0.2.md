# D-0003 — Architecture revisions AR-1 to AR-6 for proposal v0.2

Date: 2026-10-09 · Session: ELO-2 · Status: RATIFIED by the architect (Web Claude) in the ELO-2 brief of 2026-10-09; implemented by the executor in proposal v0.2 and the technical annex v0.2

## Context

Proposal v0.1 (`docs/proposal/ELO-PROPOSAL_v0_1.md`) described a three-layer design with four correction channels. The architect reviewed it and fixed six revisions. They override v0.1 wherever the two differ. They are recorded here verbatim in substance; the exact formulas live in the technical annex (`docs/proposal/ELO-TECHNICAL-ANNEX_v0_2.md`, sections T2–T6).

## The revisions

**AR-1 Expected score (assumptions A1, A2).** Each time control tc has a calibrated Davidson-type expected-score function. For player i against j with effective gap x (AR-2): z = κ_tc · (ln 10 / 400) · x; ν = exp(α_tc + β_tc · (L − 2000)/400) with L the mean of the two published ratings; P(win) = e^{z/2} / (e^{z/2} + e^{−z/2} + ν); P(draw) = ν / (e^{z/2} + e^{−z/2} + ν); E = P(win) + P(draw)/2. E is continuous and monotone in x, E(x) + E(−x) = 1, and with ν = 0 and κ = 1 it is exactly logistic Elo (proved in annex T3). No 400- or 600-point caps and no clamps. Published yearly as a lookup table per time control and level band, the successor to §8.1.2, so arbiters keep working from a table. Colour enters the expectation only: x includes +η_tc for White and −η_tc for Black; this makes colour imbalance self-correcting per game (annex T3).

**AR-2 Published update (Layer 2).** x_i = R_i − R̃_j + w_i · η_tc with w_i = +1 for White, −1 for Black; R̃_j = R_j + c_j with c_j = 0 unless j qualifies under AR-4; R_i ← R_i + K_i · (S_i − E(x_i)); K_i = K_min + (K_max − K_min) · min(1, (σ_i/σ_new)²), σ_i being the L1 posterior SD of i in that time control. K_i is printed beside the rating in the monthly list, which already carries a K column. A per-period cap on total change in the spirit of FIDE's K × n ≤ 700 rule, restated for K_i. Fixed-point arithmetic in tenths; rounding exactly as FIDE §8.3.4; fully deterministic.

**AR-3 Monthly calibration adjustments** replace v0.1's per-game pool bonus (C3) and v0.1's federation offsets applied through expectations (C4). Architect's correction: an offset inside the expectation freezes the gap it measures; if E already credits an under-rated pool with +100, its players stop gaining from wins and the published list never converges. Therefore: a global adjustment a_t, paid each month to every player with at least one rated game in that time control that month, derived from the drift of a precisely defined anchor cohort (stable adults, roughly 25–45, regularly active): published anchor mean versus L1 latent mean, with |a_t| ≤ a_cap; a federation adjustment a_{f,t} by the same mechanism from the L1 estimate of the federation's mean miscalibration φ_f, shrunk by its evidence and capped, which SHIPS DISABLED (a_{f,t} = 0) until a backtest on FIDE's own game data shows φ_f stable and predictive out of sample; paid per player per active month, never per game; no one-off jumps, so any gap at adoption closes gradually and ratings still change only for players who play.

**AR-4 Junior-opponent compensation (A4).** Eligible when j is under 20 (birth year from the FIDE list) and L1 rates j above R_j by more than τ with posterior probability at least 0.9; then c_j = min(θ̂_j − R_j, c_cap). It enters only the opponent's expectation; the junior's own update uses published ratings, so the junior catches up at full speed while opponents are not drained. It switches off by itself as the junior's rating catches up.

**AR-5 Seeds, inactivity, floor.** A newcomer's first published rating (still after at least 5 games) is the L1 posterior mean, drawing on games in all three time controls; it replaces the two 1800 phantom draws. No rating decays with inactivity: the L1 uncertainty grows instead, so K rises on return, and no adjustment is earned while inactive. The 1400 floor may remain as a display rule, but L1 keeps estimating players below it so their games still inform the pool; the ledger records points leaving through the floor.

**AR-6 The points ledger.** Published monthly per time control: points moved between players by results; points created or destroyed by unequal K; points from each adjustment and from junior compensation; points entering with newcomers; points leaving with players who drop off the active list or below the floor. Plain-language analogy for the proposal: a central bank publishing how much money it created and why. The exact accounting identity is annex T6.

**L1 specification (stated exactly in annex T2).** Outcomes: the AR-1 Davidson model with η_tc, α_tc, β_tc, κ_tc. Skill: s_{i,tc}(t) = θ_i(t) + δ_{i,tc}(t); θ follows a random walk with age-dependent drift μ(age, θ) and variance σ²(age); δ is shrunk towards 0; this is the one framework that diverges by style. Fit: rolling 36-month window, re-estimated monthly; MAP with a Laplace approximation (Whole-History-Rating style) or expectation propagation (TrueSkill Through Time); hyperparameters by rolling out-of-sample log-loss. Scale: anchored to the anchor cohort's published mean at a reference date; pool offsets identified only through games that cross pools, each reported with its posterior SD and graph diagnostics (connected components; effective resistance between the federation and the anchor pool); a channel acts only when its evidence passes a published threshold. L1 never edits a published rating; its only outputs are the monthly parameter file and the published diagnostics.

## What this supersedes in v0.1

| v0.1 element | Superseded by |
|---|---|
| Logistic curve with scale σ and tanh clamp D_max (§5, A.7) | AR-1 Davidson function per time control, no clamp |
| K_eff with exponential experience decay, K_floor(R) transition at R_half (§5, A.7, D.1) | AR-2 K_i from the L1 posterior SD |
| C3 per-game pool bonus b (§5, A.7) | AR-3 monthly global adjustment a_t per active player |
| C4 federation offsets inside the expectation (§5, A.7, E.1) | AR-3 federation adjustment a_{f,t}, shipped disabled |
| C2 with weight α and a variance threshold (A.7) | AR-4 eligibility test and cap c_cap |
| C1 seed with age- and pool-informed prior (§6, A.7) | AR-5 L1 posterior mean over all three time controls |
| Retirement archive after five years (§6) | Dropped from the rating rules; a presentation matter for FIDE |
| No ledger | AR-6 points ledger with exact identity |

## Consequences

- The channel names C1–C4 are retired. v0.2 names the channels by what they do: expected score (AR-1), K from uncertainty (AR-2), calibration adjustments (AR-3), junior compensation (AR-4), seeds (AR-5), ledger (AR-6).
- Every parameter value remains PROVISIONAL until estimated from data.
