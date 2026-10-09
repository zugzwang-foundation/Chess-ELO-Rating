# Technical annex to the proposal "Modernising the FIDE Elo Rating System", v0.2

**Status: DRAFT v0.2 — not for publication**
Author: The Zugzwang Authors · Licence: CC BY 4.0 (`docs/LICENSE-docs.md`) · Date: 2026-10-09
Companion to `docs/proposal/ELO-PROPOSAL_v0_2.md`. Architecture as ratified in `docs/decisions/D-0003_architecture-revisions-v0.2.md` (AR-1 to AR-6). Every number in this annex is produced by `analysis/v02_calculations.py` (output in `analysis/OUTPUT_v0_2.md`); every parameter value is PROVISIONAL until estimated from data. Citations: `[R §x]`, `[R n]` the research report `docs/research/ELO-RESEARCH_v1_0.md`; `[V k]` item k of `docs/research/VERIFICATION_2026-10-09.md`. Every FIDE rule quoted is from [V 1] (standard) or [V 2] (rapid and blitz); anything else about FIDE regulations is marked NOT VERIFIED.

Contents: T1 Notation · T2 Layer 1 model · T3 Expected-score function · T4 Layer 2 rules · T5 Properties P1–P6 · T6 Ledger identity · T7 Monthly parameter file · T8 Evaluation pre-registration · T9 Simulator design · T10 Worked examples · T11 Transition.

---

## T1 Notation

Every symbol is defined here once and used with this meaning everywhere in the proposal and the annex.

**Indices.** i, j players; g a game; t a month (a rating period, identified by its list date); tc ∈ {standard, rapid, blitz}; f a federation.

**Published quantities (Layer 2).**

| Symbol | Meaning | Grid |
|---|---|---|
| R_i | published rating of i in time control tc | whole number |
| K_i | published development coefficient of i (AR-2), printed in the list's K column | one decimal |
| S_i | score of i in a game: 1, ½, 0 | exact |
| w_i | colour indicator: +1 White, −1 Black (w_j = −w_i) | — |
| L | level of a game, L = (R_i + R_j)/2 from the two published ratings, without compensation | halves |
| c_j | junior compensation of j (AR-4); 0 unless j is eligible | whole number |
| RX_j | R_j + c_j, the rating used in opponents' expectations; a list column | whole number |
| x_i | effective gap for i: x_i = R_i − RX_j + w_i · η_tc | whole number |
| E(x; tc, L) | expected score from the published table of tc at level band of L (T3) | three decimals |
| P_W, P_D, P_L | the three outcome probabilities behind E | — |
| a_t | global calibration adjustment of month t (AR-3) | one decimal |
| a_{f,t} | federation calibration adjustment (AR-3); 0 while disabled | one decimal |
| ΔR_{i,g} | game term K_i · (S_i − E(x_i)) | exact (at most four decimals) |
| n_i | number of rated games of i in tc on list t | whole number |
| round_FIDE(v) | nearest whole number, 0.5 away from zero (§8.3.4 [V 1]) | — |

**Layer 1 quantities.**

| Symbol | Meaning |
|---|---|
| θ_i(t) | shared latent skill of i at month t, on the Elo scale |
| δ_{i,tc}(t) | time-control offset of i; s_{i,tc}(t) = θ_i(t) + δ_{i,tc}(t) is i's latent strength in tc |
| θ̂_i, σ_i | posterior mean and posterior standard deviation of s_{i,tc} at the list date (per tc). σ_i is the quantity AR-2 uses |
| μ(age, θ) | expected monthly change of θ at a given age and level (drift) |
| σ_θ²(age) | monthly variance of the random walk of θ (process variance; distinct from σ_i) |
| ρ_tc, ω_tc | persistence and innovation standard deviation of δ_{i,tc} |
| μ_0(age, f), s_0 | prior mean and standard deviation of a new player's θ |
| φ_f, s_f | mean miscalibration of federation f relative to the anchor pool, and its posterior SD |
| m_t, m̂_t | published mean and latent (L1) mean of the anchor cohort at month t; d_t = m̂_t − m_t |
| θ̃_i | ŝ_{i,tc} − d_t: the posterior mean brought onto the published scale; the only Layer 1 estimate Layer 2 ever uses (T4.6, T4.7) |
| G, N | number of games and of players in the fit window |

**Derived, ledger and threshold symbols.** E_i⁰ expectation of i without compensation; T_g, C_g^K, C_g^c transfer, unequal-K creation and compensation creation of game g (T6); B_i accrued adjustment balance, A_i the balance posted in month t (T4.5); ρ_i rounding residual (T6); N_anchor minimum anchor-panel size (PROVISIONAL 2,000); n_φ shrinkage constant for φ_f (PROVISIONAL 2,000 cross-pool games); s_max, R_max thresholds on s_f and on the effective resistance for any φ_f-dependent channel (PROVISIONAL, published in T7); σ_seed,max maximum posterior SD for a published seed (PROVISIONAL 120); band width of the published table (PROVISIONAL 200, T7).

**Parameters (per time control unless stated; all PROVISIONAL; annual change caps in T7).**

| Symbol | Meaning | PROVISIONAL (standard / rapid / blitz) |
|---|---|---|
| κ_tc | slope: latent gap per published gap | 1.00 / 1.00 / 1.00 |
| η_tc | colour term, in rating points | 35 / 25 / 25 |
| α_tc, β_tc | draw-term intercept and level slope | −0.50, 0.55 / −0.70, 0.50 / −0.90, 0.45 |
| K_min, K_max | bounds of K_i | 10, 40 |
| σ_new | posterior SD at which K_i reaches K_max | 100 |
| C_period | per-period cap constant (today's 700, unchanged) | 700 |
| a_cap, γ_a | cap on \|a_t\| per month; adjustment gain | 1.5 points; 1/6 |
| τ, c_cap, p_min | compensation threshold, cap, posterior probability | 50, 300, 0.90 |
| R_floor, R_seedmax, N_seed | display floor (§7.2.1), seed maximum (§8.2.3), games to seed (§7.1.4), all today's values | 1400, 2200, 5 |
| band width | width of the level bands of the published table | 200 |

---

## T2 Layer 1 model

Layer 1 is the statistical model. It is re-estimated monthly on a rolling 36-month window of all rated games in all three time controls. It never edits a published rating; its only outputs are the monthly parameter file (T7) and the published diagnostics.

**T2.1 Outcome likelihood.** For a game g in month t and time control tc between White w and Black b, with latent strengths s_w = s_{w,tc}(t), s_b = s_{b,tc}(t):

> x_g = s_w − s_b + η_tc (latent gap, White's view)
> z_g = (ln 10 / 400) · x_g
> ν_g = exp(α_tc + β_tc · (L_g − 2000) / 400), L_g = (R_w + R_b)/2 from the published list in force
> P(White wins) = e^{z_g/2} / D_g, P(draw) = ν_g / D_g, P(Black wins) = e^{−z_g/2} / D_g, D_g = e^{z_g/2} + e^{−z_g/2} + ν_g

This is Davidson's extension of the Bradley–Terry model with a draw term proportional to the geometric mean of the two strengths (dividing by √(π_w π_b), with π = 10^{s/400}, gives the form above; T3.1). The level L_g is taken from the published list, so it is a known covariate and the likelihood stays a function of the gap only. The log-likelihood is Σ_g log P(y_g), y_g the observed result. In latent units the slope is 1; the Layer 2 slope κ_tc (T3) is the regression of the latent gap on the published gap and equals 1 when the published scale is correctly spread.

**T2.2 Dynamics and priors.**

> θ_i(t+1) = θ_i(t) + μ(age_i(t), θ_i(t)) + ε_i(t), ε_i(t) ~ N(0, σ_θ²(age_i(t)))
> δ_{i,tc}(t+1) = ρ_tc · δ_{i,tc}(t) + ξ_{i,tc}(t), ξ ~ N(0, ω_tc²); stationary prior δ_{i,tc} ~ N(0, ω_tc² / (1 − ρ_tc²))
> θ_i(t_0) ~ N(μ_0(age, f), s_0²) for a player first seen at t_0

μ(age, θ) is piecewise linear in age bands (under 12, 12–15, 16–19, 20–24, 25–45, 46–60, over 60; PROVISIONAL) with a linear term in (θ − 2000)/400 inside each band, so that fast improvement is allowed to depend on level; σ_θ(age) is one value per band. The offsets δ are shrunk towards zero: with few games in a time control a player's strength there is essentially θ; with many, the offset is estimated. This is the one framework that diverges by style (proposal §7). The age comes from the year of birth on the FIDE list [V 3]; a player without one is treated as an adult of unknown age (band 25–45) and is never eligible for compensation (T4.6).

**T2.3 Estimation.** Maximum a posteriori over all trajectories {θ_i(·), δ_{i,tc}(·)} given the hyperparameters, by Newton's method one player at a time as in Whole-History Rating [R 11] [R 12]: because consecutive months are linked only by the random walk, the Hessian of one player's trajectory is tridiagonal and a Newton step costs O(n_i) for a player with n_i months in the window; one sweep over all players costs O(G + Σ_i n_i); the fit is warm-started from last month's trajectories and converges in a few dozen sweeps. The posterior standard deviation σ_i is read from the diagonal of the inverse of the tridiagonal Hessian at the list date (Laplace approximation). Two cautions are part of the specification. First, the per-player block Laplace gives the standard deviation conditional on the opponents' estimates and understates the marginal one in small, weakly connected pools; either expectation propagation as in TrueSkill Through Time [R 10] [R 69], which propagates that uncertainty, is used for σ_i, or the block value is calibrated against it by simulation (T9) and σ_new is set on the calibrated scale; the choice is a pre-registered item (T8). Second, a hard window edge would make σ_i and K_i jump in the month a block of games leaves the window, so each player is initialised at the window start with the summarised prior N(ŝ(t − 36), σ²(t − 36) + process variance) taken from the previous fit (fixed-lag smoothing); nothing jumps when the window rolls. With FIDE's roughly 3 to 3.5 million standard games a year [R §7] a 36-month window holds about 10 million games; WHR processed 10.8 million Go games on 2008 hardware [R 11], so the monthly refit is a laptop-scale job.

Hyperparameters (η_tc, α_tc, β_tc, μ(·), σ_θ(·), ρ_tc, ω_tc, μ_0, s_0) are chosen by rolling out-of-sample three-outcome log-loss (T8): fit on months up to t, score month t+1, roll forward, minimise the mean. They change at most once a year, within the caps of T7.

**T2.4 Scale anchoring and identifiability.** The likelihood is invariant to adding one constant to every θ (and to every s), so the level of the latent scale must be fixed by a constraint. The constraint is the anchor cohort: a fixed panel of players aged 25–45 by year of birth on the re-basing date with at least 10 rated games in the time control in each of the three preceding calendar years and a published rating throughout (PROVISIONAL definition). At the reference month t_ref the mean latent strength of the panel equals its mean published rating: mean_{i ∈ anchor} ŝ_{i,tc}(t_ref) = mean_{i ∈ anchor} R_i(t_ref). The panel is re-based every 1 January and chain-linked: the new panel's latent mean at the new reference month is set equal to its value under the previous month's fit, so the latent scale never jumps; the re-basing shift (always zero by construction up to numerical tolerance) is published. The level over time is likewise unidentified by games alone (adding c · t to every θ changes no probability and the age drift μ would absorb it), so a second constraint defines it: the anchor panel's mean drift is zero, Σ_{i ∈ anchor} μ(age_i(t), θ_i(t)) = 0 for every month in the window; juniors' positive drift is identified relative to it. The panel's constancy is therefore the definition of the scale, as in US Chess practice [R 22], not an empirical finding. The drift measurement is taken over current members as a mean of per-player differences, d_t = mean_{i ∈ anchor(t)} (ŝ_{i,tc}(t) − R_i(t)), so that membership churn does not bias it; m̂_t and m_t are its two halves. The monitoring report publishes the panel's size and composition each month.

Within a player, θ_i and the δ_{i,tc} are jointly identified only through the shrinkage prior on δ (adding c to θ_i and −c to every δ_{i,tc} leaves every s unchanged); the prior resolves this softly, and the reported quantity for Layer 2 is always s_{i,tc}, which is identified by the games.

**T2.5 Pool offsets and graph diagnostics.** The miscalibration of federation f is a derived quantity, not a parameter:

> φ_f(t) = mean_{i ∈ f, rated month t} (ŝ_{i,tc}(t) − R_i(t)) − mean_{i ∈ anchor} (ŝ_{i,tc}(t) − R_i(t)),

with posterior SD s_f from the Laplace covariance. The second term equals d_t, so φ_f is net of the global drift by construction. It is identified only through games that cross pools. Two diagnostics are published per federation each month: the connected component of the game graph (players as nodes, games in the window as edges) that contains the federation's players, and the effective resistance between the federation (its players merged into one node) and the anchor pool (merged into one node) in the game graph with unit conductance per game, computed from the graph Laplacian. The effective resistance is the Gaussian-approximation variance of the offset under equal game information, so a large value means the offset is poorly determined whatever the point estimate says. A channel that depends on φ_f acts only when s_f < s_max and the effective resistance is below R_max (both published thresholds, T7); the federation adjustment ships disabled regardless (T4.5).

**T2.6 Outputs.** Per player and time control: ŝ_{i,tc} and σ_i (Layer 2 uses θ̃_i = ŝ_{i,tc} − d_t, T1), and from them K_i; eligibility and c_j for juniors; seeds for newcomers; the anchor statistics m_t, m̂_t, d_t and from them a_t; φ_f, s_f and the graph diagnostics; the fit diagnostics of T7. Nothing else leaves Layer 1.

---

## T3 Expected-score function

**T3.1 Definition and derivation.** For player i against j with effective gap x (T4.2), time control tc and level L:

> z = κ_tc · (ln 10 / 400) · x
> ν = exp(α_tc + β_tc · (L − 2000) / 400)
> P_W = e^{z/2} / (e^{z/2} + e^{−z/2} + ν), P_D = ν / (e^{z/2} + e^{−z/2} + ν), P_L = e^{−z/2} / (e^{z/2} + e^{−z/2} + ν)
> E(x; tc, L) = P_W + P_D / 2 = (e^{z/2} + ν/2) / (e^{z/2} + e^{−z/2} + ν)

Derivation: Davidson's model gives P(i wins) : P(draw) : P(j wins) = π_i : ν √(π_i π_j) : π_j with π = 10^{s/400}; dividing by √(π_i π_j) gives e^{z/2} : ν : e^{−z/2} with z = ln(π_i/π_j) = (ln 10/400)(s_i − s_j). Layer 2 replaces the latent gap by κ_tc times the published gap, so κ_tc is the calibration slope between the published scale and the latent one.

**T3.2 Properties (proofs).**

1. *Symmetry.* E(x) + E(−x) = [(e^{z/2} + ν/2) + (e^{−z/2} + ν/2)] / (e^{z/2} + e^{−z/2} + ν) = 1, because ν depends on L, which is the same for both players. Hence the table needs only x ≥ 0, with E(−x) = 1 − E(x) exactly as table 8.1.2 prints H and L [V 1]. (With compensation, x_i ≠ −x_j and the two expectations do not sum to one; T6 accounts for the difference.)
2. *Continuity and monotonicity.* E is a composition of continuous functions of x. With u = e^{z/2}, E = (u + ν/2)/(u + 1/u + ν) and dE/du = [2/u + ν/2 + ν/(2u²)] / (u + 1/u + ν)² > 0; u is increasing in z and z in x (κ_tc > 0), so E is strictly increasing in x. Numerically (script §2): min E(x+1) − E(x) over x ∈ [−1200, 1200] and all bands = 1.93 × 10⁻⁵ > 0; max |E(x) + E(−x) − 1| = 2.2 × 10⁻¹⁶.
3. *Logistic Elo as the special case ν = 0, κ = 1.* Then E = e^{z/2}/(e^{z/2} + e^{−z/2}) = 1/(1 + e^{−z}) = 1/(1 + 10^{−x/400}), the logistic form of Elo [R §1]; numerically the two agree to 2.2 × 10⁻¹⁶ on the grid (script §2). Davidson's model is therefore a strict generalisation: it adds a draw propensity that grows with level and leaves the Elo odds for decisive results untouched.
4. *Local scale.* dE/dx at x = 0 is κ_tc (ln 10/400) / (2(2 + ν)), so near equal strength the curve behaves like logistic Elo with scale 200(2 + ν)/κ_tc: at ν = 0 that is 400; at ν = 0.4 it is 480, which is Sonas's finding that results behave as if the gap were about 5/6 of the nominal gap [R 44] [R §3.5]. κ and ν are therefore jointly identified only through decisive results against draws, and the calibration fit must report both.
5. *Limits.* E → 1 as x → +∞ and E → 0 as x → −∞; P_D at equal strength is ν/(2 + ν) (0.167 at level 1700, 0.443 at level 2700 with the PROVISIONAL parameters; script §1) and decays like ν e^{−|z|/2} at large gaps. No cap or clamp is needed: there is no x at which the function changes rule, and no result is ever worth exactly nothing.
6. *Colour is self-correcting per game.* Because x_i includes +η_tc for White and −η_tc for Black, the model's expectation already contains the colour. If the model is right, the expected change of i in any single game is K_i · (P_W + P_D/2 − E) = 0 whatever the colour (property P4, T5), so a player who happens to receive more Whites than Blacks gains nothing in expectation and no colour debt accumulates across games or events. Under today's table, which gives .50 to both colours at equal ratings [V 1], a player with one extra White at level 2000 gains about +0.77 points in expectation at K = 20 (script §3), and a short event with an odd number of rounds leaves that imbalance uncorrected.

**T3.3 The published table.** The successor to table 8.1.2 [V 1] is one table per time control, published yearly with the parameter file. Rows: one row for every whole-number x from 0 to 1500 (the QC extends the table whenever a list in force makes a larger gap possible), so that no interpolation is ever needed and the table is normative; the parameter file documents the function that generated it. Columns: level bands of 200 points (below 1600; 1600–1799; …; 2600–2799; 2800 and above), with ν evaluated at the band midpoint (1500 and 2900 for the two open bands). Entries: E to three decimals; a three-decimal entry resolves the top of the scale, where today's two decimals produce the "worth nothing above 735 points" effect [V 1] [R 55]. For negative x the arbiter uses E(−x) = 1 − E(x). The engine uses the same table, so engine and arbiter read identical values. Excerpt for standard (script §1):

| x | <1600 | 1600–1799 | 1800–1999 | 2000–2199 | 2200–2399 | 2400–2599 | 2600–2799 | ≥2800 |
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

Two consequences are stated plainly. First, the level band makes E step at band edges: for a fixed x the entries of two adjacent bands differ by at most 0.0256 (at the top; 0.0096 at the bottom; script §2), that is at most 0.51 points in one game at K = 20. This is a table-resolution effect, not a rule; halving the band width halves it, and the band width is a parameter in T7. Second, with the PROVISIONAL draw parameters the function predicts much lower expectations at large gaps than today's table (0.824, 0.905, 0.949 at x = 400, 600, 800 in the 2200–2399 band against .92, .98, 1.0 [V 1]; script §2), because Davidson's draw probability decays only like e^{−|z|/2}. Whether real draw rates at large gaps fall that slowly is exactly what the calibration-by-gap metric of T8 measures; if they fall faster, the fitted α, β and κ will say so, and the pre-registration records the possibility that the draw term may need a gap-dependent factor as a question for the architect, not a change made here.

---

## T4 Layer 2 rules

Layer 2 is the published rating. Everything in this section is computed from quantities printed on list t and in the parameter file of list t; nothing computed during month t is used before list t+1.

**T4.1 Inputs frozen for the period.** Only games against rated opponents enter Layer 2, exactly as today: §8.3.1 begins "For each game played against a rated player" [V 1], so a rated player's game against an unrated or sub-floor opponent produces no change for either side and no ledger entry; Layer 1 uses every game. For every game of rating period t: R_i and R_j from list t; K_i from list t (one decimal); RX_j = R_j + c_j from list t; the carried adjustment balance B_i from list t (printed, so that a change after an absence is recomputable); the level band of L = (R_i + R_j)/2 (published ratings, without compensation; a half is rounded down before banding); the colour from the tournament report (format NOT VERIFIED; see SPEC-L0 §2.1); η_tc, the table and a_t from the parameter file of list t.

**T4.2 The game term.**

> x_i = R_i − RX_j + w_i · η_tc
> ΔR_{i,g} = K_i · (S_i − E(x_i; tc, L)), which the proposal writes per game as R_i ← R_i + K_i · (S_i − E(x_i)); the game terms are summed and rounded once per period (T4.4)

K_i has one decimal and E three, so each ΔR_{i,g} is exact with at most four decimals. No rounding occurs here.

**T4.3 K from uncertainty.**

> K_i = K_min + (K_max − K_min) · min(1, (σ_i / σ_new)²), rounded to one decimal and printed in the list's K column.

σ_i is the Layer 1 posterior SD of i's strength in tc at the list date. K_i rises with uncertainty and falls as a player's record accumulates; it does not depend on results, only on how much the games so far pin the strength down (T5, P4 remark). The σ² shape is the Bayesian one: a single Gaussian-approximation update moves a posterior mean by σ² · (ln 10/400) · (S − E), that is with an implied K of σ² ln 10/400 (5.2, 11.7, 17.4, 28.2 for σ = 30, 45, 55, 70); σ_new is set so that the published K_i tracks that gain in the range where most players sit and reaches K_max = 40 for a newcomer. PROVISIONAL mapping with σ_new = 100 (script §4): σ_i = 30, 45, 55, 70, 85, 100 give K_i = 12.7, 16.1, 19.1, 24.7, 31.7, 40.0. A newcomer (σ_i ≥ σ_new) starts at K_max = 40, as today's newcomers do [V 1]; an established active adult (σ_i about 55, PROVISIONAL) sits near today's 20; a player who has been inactive for years returns with a higher K_i because σ_i has grown through the random walk (T2.2), and no rating has moved meanwhile (AR-5).

**T4.4 Per-period cap, adjustment, rounding.** Let n_i be the number of rated games of i in tc on list t.

> If K_i × n_i > 700, K_i is replaced for that period by ⌊7000 / n_i⌋ / 10 (700/n_i truncated to one decimal), for every game of the period.
> Period change = round_FIDE( Σ_g ΔR_{i,g} + a_t + a_{f(i),t} ) if i has at least one rated game in tc on list t; otherwise no change.

This restates §8.3.3's rule "K shall be the largest whole number such that K × n does not exceed 700" [V 1] for a one-decimal K. a_t is outside the cap and is added once per rated month, however many games were played (AR-3). The rounding is §8.3.4 [V 1], applied once, to the period total; there is no other rounding anywhere in Layer 2. Example (script §4): K_i = 26.1 and n_i = 40 gives 1044 > 700, so K_i = 17.5 for the period; K_i = 16.5 and n_i = 40 gives 660, no cap.

A *rated month* for i in tc is a month in which i has at least one rated game in tc on list t. It is distinct from the activity flag of §7.2.2 [V 1], which is unchanged.

**T4.5 Calibration adjustments (AR-3).**

> d_t = m̂_t − m_t (latent minus published mean of the anchor cohort, T2.4)
> a_t = clip(γ_a · d_t, −a_cap, +a_cap), rounded to one decimal
> a_{f,t} = clip(γ_a · shrink_f · φ_f(t), −a_cap, +a_cap) with shrink_f = n_f^× / (n_f^× + n_φ) and n_f^× the federation's cross-pool games in the window; SHIPS DISABLED: a_{f,t} = 0 for every f, printed as 0 in every parameter file, until a backtest on FIDE's own game data (T8) shows φ_f stable and predictive out of sample, and then only by Council decision after public comment and consultation with the federation concerned.

a_t is computed from the month just closed and published with the list, never before the games it applies to are rated, so its sign cannot be timed. It is paid per player, never per game, so an extra or an arranged game earns no adjustment. To stop the calendar from mattering (twelve single-game months must not collect twelve payments while one month with twelve games collects one), a_t accrues each month to every player listed as active under §7.2.2 [V 1] (a rated game in the last twelve months) in that time control, into a balance B_i; the balance is posted to R_i only in a rated month, as part of the period total of T4.4; accrual stops while the player is inactive under §7.2.2 and the balance (positive or negative) is carried, not forfeited, so that the activity boundary creates no cliff and no incentive to sit out a liability; it is posted in the first rated month after return. Ratings therefore still change only for players who play, no adjustment is earned while inactive (AR-5), and the posted balance never exceeds 12 · a_cap in magnitude. This accrual rule is a refinement of AR-3 recorded for the architect's confirmation (REDTEAM_v0_1, R-STAT-6, R-EXPLOIT-6). The loop is a proportional controller: with a steady deflationary pressure of 1.3 points a month (the research report's post-reform figure is about −16 a year [R 5]) and γ_a = 1/6, a_t rises to 1.3 and the measured gap settles near 7.8 points (script §7); it is stable because 0 < γ_a < 1, and it can only hold the level if a_cap exceeds the drift, which the monitoring report shows each month. Whether a_t may be negative (a deduction from everyone who played, in an inflating pool) is a policy question the QC can settle by constraining a_t ≥ 0 without touching the mechanism; the architecture allows both signs and this annex records the question as open (REDTEAM_v0_1, R-QC-9). No one-off adjustment is ever made: any gap at adoption closes through capped monthly adjustments to players who play.

Before a_{f,t} may ever be enabled, the following are required in addition to the out-of-sample test (REDTEAM_v0_1, R-EXPLOIT-3): the evidence for φ_f must come from at least 50 distinct players of f with cross-pool games, none contributing more than 5 % of that information; φ_f is a trimmed-mean estimate with a published leave-one-player-out range, and a_{f,t} stays 0 unless the whole range has one sign; players whose published rating is more than 2 s_f from their estimate are excluded from φ_f; and the points a_{f,t} may create per federation per year are capped and printed in the ledger. Separately, because junior compensation creates points deterministically (T6, line 3), the monitoring report compares that line per active player with a_cap each month; if it exceeds a_cap the QC lowers c_cap or raises τ within their annual caps (REDTEAM_v0_1, R-STAT-3).

**T4.6 Junior compensation (AR-4).** j is eligible on list t if (a) the list year minus j's year of birth on the FIDE list is at most 19 (that is, until the end of the calendar year of the 19th birthday, matching the form of §8.3.3's junior rule [V 1]; a player without a year of birth on the list is not eligible), (b) j has at least 10 rated games in that time control within the window, against at least 5 distinct opponents in at least 3 events (PROVISIONAL; so that same-time-control evidence dominates, compensation cannot be manufactured from another time control, and a small circle of club opponents cannot manufacture it within one), and (c) P(s_{j,tc} − d_t − R_j > τ) ≥ p_min under the Layer 1 posterior, which for a Gaussian posterior is θ̃_j − R_j − z_{p_min} σ_j ≥ τ with z_{0.90} = 1.2816, where θ̃_j = ŝ_{j,tc} − d_t is the estimate brought onto the published scale (the latent scale sits d_t above the published one when the pool has drifted; without this netting, compensation would act as a second, uncapped level loop). Then

> c_j = min(round_FIDE(θ̃_j − R_j), c_cap), RX_j = R_j + c_j, printed in the list; otherwise c_j = 0 and RX_j = R_j.

c_j enters only opponents' x; j's own update uses R_i, R_j and the published table like everyone else, so j catches up at full speed while opponents are no longer drained. As R_j rises towards θ̃_j the test fails and c_j returns to 0 by itself. Only RX_j is printed; θ̂_j and σ_j are not published for named players unless the founder decides otherwise (D-0002, item 5). The switch at the threshold is the one discrete element of the design; it moves only opponents' expectations, by at most c_cap, and never within a rating period (T5, P3).

**T4.7 Seeds, inactivity, floor (AR-5).** A player new to the list in tc receives a first published rating once they have at least N_seed = 5 games against rated opponents within 26 consecutive months (§7.1.4 [V 1], unchanged): R_i(t_0) = clip(round_FIDE(θ̃_i), R_floor, R_seedmax) with θ̃_i = ŝ_{i,tc} − d_t the Layer 1 posterior mean of s_{i,tc} on the published scale, drawing on the player's games in all three time controls, and K_i from σ_i (near K_max); the seed's σ_i is published with it, and no seed is published while σ_i exceeds σ_seed,max (PROVISIONAL 120): the player stays unrated and keeps accumulating games. A player re-qualifying after a floor exit is re-published only if round_FIDE(θ̃_i) ≥ R_floor; otherwise they remain unrated while Layer 1 keeps estimating, so the floor no longer manufactures points at the bottom (REDTEAM_v0_2, R2-8). The two hypothetical draws against 1800 of §8.2.2 [V 1] are not used. The 2200 maximum of §8.2.3 is kept, and the five qualifying games must involve at least three distinct opponents in at least two events (both PROVISIONAL; REDTEAM_v0_1, R-EXPLOIT-5). Rapid and blitz keep §7.2.1 of their chapter [V 2] in spirit: a player with a standard rating is seeded in rapid or blitz from the same Layer 1 posterior, which already uses their standard games.

Inactivity: no published rating decays. While i has no rated month, R_i is unchanged, no a_t is paid, and σ_i grows through the random walk (T2.2) so that K_i is higher on return. The activity flag of §7.2.2 [V 1] is unchanged.

Floor: §7.2.1 [V 1] is unchanged as a display rule: a player whose rating drops below 1400 is shown as unrated on the next list and their games are then not rated for opponents, as today. Layer 1 keeps estimating the player from those games, so the pool is still informed by them, and when the player re-qualifies under §7.1.4 the seed is the Layer 1 posterior mean (T4.7), not two phantom draws; the upward re-seeding of today's rule disappears. The ledger (T6) records the rating that left through the floor. (REDTEAM_v0_1 R-QC-1 proposed carrying and printing the sub-1400 rating instead; the architecture's version is kept because it changes no paragraph of §7.2 and no hidden number is ever used to rate an opponent.)

**T4.8 Channel table.** Every channel with its formula, cap and activation threshold.

| Channel | Enters through | Formula | Cap | Activation threshold |
|---|---|---|---|---|
| Expected score (AR-1) | E in every game term | T3.1 with κ_tc, η_tc, α_tc, β_tc | none (no clamp) | always on; parameters change yearly within T7 caps |
| K from uncertainty (AR-2) | K_i | T4.3 | K_min ≤ K_i ≤ K_max; period cap 700 | always on |
| Global adjustment (AR-3) | once per rated month | a_t = clip(γ_a d_t, ±a_cap) | a_cap per month | anchor panel of at least N_anchor players (PROVISIONAL 2,000) |
| Federation adjustment (AR-3) | once per rated month | T4.5 | a_cap per month | DISABLED; later: s_f < s_max, effective resistance < R_max, Council decision |
| Junior compensation (AR-4) | opponents' x only | c_j = min(round_FIDE(θ̃_j − R_j), c_cap), θ̃_j = ŝ_{j,tc} − d_t | c_cap | age rule (list year − birth year ≤ 19), at least 10 rated games in tc, and P(s_{j,tc} − d_t − R_j > τ) ≥ p_min |
| Seed (AR-5) | first published rating | clip(round_FIDE(θ̃_i), R_floor, R_seedmax), θ̃_i = ŝ_{i,tc} − d_t | R_seedmax | N_seed games against at least 3 distinct opponents in at least 2 events within 26 months |
| Ledger (AR-6) | publication only | T6 | — | always |

---

## T5 Properties with proof sketches

**P1 Forward-only.** R_i(t+1) is a function of R_i(t), the games of period t and quantities printed on list t and its parameter file (T4.1). Layer 1 writes nothing into any R. No published list is ever recomputed. Proof: the only operation on a published rating is the period update of T4.4; its inputs are frozen at list t; a published list is a constant thereafter. (The 2024 one-off compression [R §2] has no counterpart here: AR-3 forbids one-off jumps.)

**P2 Bounded change.** Per game |ΔR_{i,g}| ≤ K_i |S_i − E| ≤ K_i ≤ K_max = 40. Per period |Σ_g ΔR_{i,g}| ≤ K_i n_i ≤ 700 after the cap of T4.4, and the posted adjustment balance is at most 12 · a_cap (T4.5), so the published change satisfies |period change| ≤ round_FIDE(700 + 12 · a_cap) = 718 (PROVISIONAL a_cap = 1.5; 702 in a month without accrued balance; the same again for a_{f,t} if it is ever enabled). Today's bound is 700 [V 1].

**P3 Continuity.** E is continuous and strictly increasing in x (T3.2); K_i is continuous in σ_i (a clipped quadratic); the period cap is continuous in n_i (a clipped hyperbola); a_t is continuous in d_t up to its one-decimal rounding (a step of 0.1 point). There is no 400- or 600-point rule, no 2650 exemption, no switch at 30 games, at 2300, at 2400 or at age 18 [V 1] [V 2]. Two discrete elements remain and are stated: (i) the published table steps at level-band edges by at most 0.0256 in E (0.51 points at K = 20; script §2), a resolution effect that shrinks with the band width; (ii) c_j switches on and off at the eligibility test of T4.6, moving opponents' expectations by at most c_cap and never within a period. Neither can be straddled for gain: (i) is symmetric for both players and (ii) is controlled by a posterior, not by a result a player can choose (T9 tests the compensation hunter).

**P4 Unbiasedness.** If the model's probabilities are correct for a game, E[ΔR_{i,g}] = K_i (P_W · 1 + P_D · ½ + P_L · 0 − E) = K_i (E − E) = 0. Hence the expected change from any pairing is zero: a player cannot gain in expectation by choosing weak opponents (farming), strong ones, or a particular colour; the only way to gain is to score more than the calibrated expectation. The result is exact for the model's own probabilities and holds for real games to the extent that the yearly calibration (κ_tc, α_tc, β_tc, η_tc fitted by T8) is right; any residual miscalibration m(x, L) = E_true − E gives an expected gain K_i m per game, which is precisely the quantity the calibration-by-gap metric of T8 reports, and which today's cap converts into a systematic +0.4 points a game for a 2600 against a 2100 if the uncapped table is right (script §6). K_i is a function of σ_i, which depends on the information in the games played (how many, against whom) and on results only through the fitted strength, never on their sign, so a player cannot raise K_i by choosing to lose; playing only far weaker opponents does keep σ_i high (each such game carries little information), which is why the farming index of T8 watches that pattern.

**P5 Ledger completeness.** Every point that enters, leaves or is created in a time control's list in a month appears in exactly one line of the ledger, and the lines sum to the change in the list total. Proof: T6 is an algebraic identity in which every term is one of the published lines; it is checked exactly on a synthetic month in script §8.

**P6 Determinism.** All Layer 2 quantities live on fixed decimal grids (T1) with a single rounding step (T4.4); the table is a published file; the same list, parameter file and tournament reports give the same output on any machine, as SPEC-L0 §5 requires of Layer 0. Layer 1 is an iterative fit in floating point, so bitwise identity across machines is not promised; what is promised is reproducibility at a published tolerance (|Δŝ| ≤ 0.1 and |ΔK_i| ≤ 0.1 between two conforming runs) given the same input ordering (games sorted by date, event and FIDE ids), a fixed sweep order, a fixed iteration cap, a fixed random seed where any stochastic step exists, and the published convergence tolerances; the parameter file and list, once signed, are canonical, and the file carries the hash of its inputs (T7) so that any party can rerun it and compare.

---

## T6 The ledger identity

For a game g between i and j in time control tc, with E_i⁰ = E(R_i − R_j + w_i η_tc) the expectation without compensation (so that E_j⁰ = 1 − E_i⁰ by symmetry), E_i, E_j the expectations actually used (T4.2), and K_i, K_j the period K after the cap:

> Transfer from j to i: T_g = ½ (K_i + K_j) · (S_i − E_i⁰)
> Created by unequal K: C_g^K = (K_i − K_j) · (S_i − E_i⁰), half credited to each player
> Created by compensation: C_g^c = K_i (E_i⁰ − E_i) + K_j (E_j⁰ − E_j)

Then ΔR_{i,g} = T_g + ½ C_g^K + K_i (E_i⁰ − E_i) and ΔR_{j,g} = −T_g + ½ C_g^K + K_j (E_j⁰ − E_j), so ΔR_{i,g} + ΔR_{j,g} = C_g^K + C_g^c: transfers cancel and only the two creation terms remain. With A_i the adjustment balance posted to i in month t (the accrued a_t and a_{f(i),t} of T4.5) if i has a rated month and 0 otherwise, and the rounding residual ρ_i = round_FIDE(Σ_g ΔR_{i,g} + A_i) − (Σ_g ΔR_{i,g} + A_i), the monthly identity per time control is

> Σ_{i ∈ list t+1} R_i(t+1) − Σ_{i ∈ list t} R_i(t) = Σ_g C_g^K + Σ_g C_g^c + Σ_i A_i + Σ_i ρ_i + Σ_{newcomers} R_i(t_0) − Σ_{exits} R_i⁺(t),

where the sums over g, A_i and ρ_i run over every player on list t who played, including those who then leave, and R_i⁺(t) = R_i(t) + (period change of i) is the rating that actually leaves with an exiting player (post-update); writing R_i(t) there would miss the exiting players' own period changes (REDTEAM_v0_2, R2-1). Games against unrated players produce no change for anyone (T4.1), so there are no one-sided terms.

The published ledger lines are therefore: (1) gross points moved between players by results, Σ_g |T_g| (a volume line; it nets to zero); (2) net points created or destroyed by unequal K, Σ_g C_g^K; (3) points created by junior compensation, Σ_g C_g^c; (4) points posted from the global adjustment, Σ_i A_i (global part), with the outstanding accrued balance Σ_i B_i shown as a memo liability; (5) points posted from federation adjustments, Σ_i A_i (federation part; 0 while disabled); (6) rounding residual, Σ_i ρ_i, bounded by 0.5 per player with a rated month; (7) points entering with newcomers, Σ R_i(t_0); (8) points leaving with players removed from the list (below 1400, §7.2.1 [V 1]), at their post-update rating R_i⁺(t); (9) the change in the list total, which must equal (2) + (3) + (4) + (5) + (6) + (7) − (8) exactly; and a memo line (10), the ratings held by players who became inactive this month under §7.2.2, which does not enter the identity because inactive players stay on the list. Lines (2) and (3) are also published per event, so that an event or a club in which unequal-K or compensation creation is concentrated is visible; the monitoring report (T8) flags the top percentile of events on either line for FIDE's existing investigation procedures (REDTEAM_v0_1, R-EXPLOIT-1, R-EXPLOIT-2). The script's synthetic month (script §8: seven listed players, eight rated games, one compensated junior, one game against an unrated player, one floor exit, one newcomer seeded at 1650, a_t = +1.2) gives +322 = +34.9115 + 26.8940 + 8.4 − 1.2055 + 1650 − 1397 exactly; booking the exit at R_i(t) = 1405 instead of R_i⁺(t) = 1397 would leave a residual of 8 points, and the game against the unrated player appears in no line.

In plain language, for the proposal: the ledger is the system's audited monthly accounts, the way a central bank publishes how much money it created and why; nothing is created silently.

---

## T7 Monthly parameter file

One YAML file per time control per list. Layer 1 writes it, the QC signs it, Layer 2 reads nothing else; every published change is recomputable from the game record, the previous list and this file (P6, proved in T5).

### T7.1 Schema

"Measured" fields are outputs of the month's fit, reported, uncapped. "Fixed" fields change only by Council decision (T11 stage 4). Caps are per calendar year, PROVISIONAL (NOTATION.md).

```yaml
schema_version:        string   # "pf-0.2"; fixed, changes only with a new annex version
list_date:             date     # YYYY-MM-01; the list this file governs
time_control:          enum     # standard | rapid | blitz; one file per tc

expected_score:                 # AR-1, published also as the yearly lookup table (T3)
  kappa:  {value: float, unit: dimensionless, cap_per_year: 0.05}    # κ_tc
  eta:    {value: float, unit: rating points, cap_per_year: 5}       # η_tc, colour term
  alpha:  {value: float, unit: log-odds,      cap_per_year: 0.20}    # α_tc, draw intercept
  beta:   {value: float, unit: log-odds per 400 points, cap_per_year: 0.10}  # β_tc

development_coefficient:        # AR-2
  K_min:    {value: float, unit: points per unit score, cap_per_year: 2}
  K_max:    {value: float, unit: points per unit score, cap_per_year: 2}
  sigma_new:{value: float, unit: rating points, cap_per_year: 15}    # σ_new, SD at which K_i = K_max
  C_period: {value: int,   unit: points × games, cap_per_year: fixed} # 700, FIDE's K × n rule restated [V 1]

global_adjustment:              # AR-3, global channel
  a_t:      {value: float, unit: points accrued per active player this month, posted in the current month if rated, otherwise carried (T4.5), cap: "|a_t| ≤ a_cap"}  # one decimal
  band_width: {value: int, unit: rating points, cap_per_year: fixed}   # level-band width of the published table (T3.3)
  a_cap:    {value: float, unit: points per month, cap_per_year: 0.5}
  gamma_a:  {value: float, unit: per month, cap_per_year: 0.0833}    # γ_a, 1/12 cap
  anchor_cohort:
    definition:  string       # fixed text (T2.4); re-based each 1 January, chain-linked
    N_anchor:    int          # minimum panel size for the channel to act (PROVISIONAL 2,000)
    rebased_on:  date
    n_members:   int          # measured
    m_t:         float        # measured, published mean of the cohort, points
    m_hat_t:     float        # measured, L1 latent mean, points
    d_t:         float        # measured, m̂_t − m_t, points

federation_adjustment:          # AR-3, federation channel; SHIPS DISABLED
  enabled:    bool            # false until the FIDE-data backtest passes (T8); change = Council decision
  threshold:  string          # published evidence rule a channel must pass (s_max, R_max, n_phi, 50-player and 5 % conditions of T4.5); cap_per_year: fixed text
  federations_public_aggregate: {share_cross_federation_games_by_band: list}   # the only federation information in the PUBLIC file while enabled = false
  federations:                # QC-ONLY annex while enabled = false (hash below); one entry per federation with ≥ 1 cross-pool game in the window
    - fed:                string   # three-letter FIDE federation code
      phi_f:              float    # φ_f, measured, points
      s_f:                float    # posterior SD of φ_f, measured, points
      component_id:       int      # connected component of the game graph containing f
      eff_resistance:     float    # effective resistance between f and the anchor pool, dimensionless
      passes_threshold:   bool
      a_f_t:              float    # a_{f,t}; always 0.0 while enabled = false

junior_compensation:            # AR-4
  tau:    {value: float, unit: rating points, cap_per_year: 10}      # τ
  c_cap:  {value: float, unit: rating points, cap_per_year: 50}
  p_min:  {value: float, unit: probability,   cap_per_year: fixed}   # 0.90
  eligible:                     # every junior with c_j > 0 this month; PUBLIC copy carries only these three fields
    - fide_id:    int
      R_j:        int           # published rating used in the test
      c_j:         int          # min(round_FIDE(θ̃_j − R_j), c_cap); RX_j = R_j + c_j is the list column; enters opponents' expectations only
  eligible_qc_annex_sha256: string  # hash of the QC-only annex holding, per eligible junior, θ̃_j and σ_j (not public; founder decision 1 may widen this)

seeds_inactivity_floor:         # AR-5
  R_floor:   {value: int, unit: rating points, cap_per_year: fixed}  # display rule only
  R_seedmax: {value: int, unit: rating points, cap_per_year: fixed}  # today's §8.2.3 maximum, kept [V 1] [V 2]
  N_seed:    {value: int, unit: games,         cap_per_year: fixed}  # today's §7.1.4, kept [V 1]

layer1_hyperparameters:         # L1 specification; chosen by rolling out-of-sample log-loss
  window_months:  {value: int, cap_per_year: fixed}                  # 36
  method:         enum          # map_laplace (WHR style) | ep (TrueSkill Through Time style); fixed
  drift_mu_by_age:              # μ(age, θ), points per month, by age band; measured, no cap, reported
    - {age_band: string, mu: float}
  sigma_theta_by_age:           # σ_θ(age), points per month (SD of the random walk); measured
    - {age_band: string, sigma_theta: float}
  rho:    float                 # ρ_tc, persistence of δ_{i,tc}, dimensionless; measured
  omega:  float                 # ω_tc, innovation SD of δ_{i,tc}, points; measured
  rng_seed: int                 # fixed per release so the fit is reproducible
  fit_diagnostics:              # all measured
    oos_log_loss_3way:   float  # nats per game, rolling-origin, last 12 months
    n_games:             int
    n_players:           int
    n_connected_components: int

ledger_totals:                  # AR-6, points to four decimals, the month's totals; lines (1)–(10) of T6
  moved_by_results_gross:  float   # (1) Σ_g |T_g|, gross volume; nets to zero
  created_by_unequal_K:    float   # (2) Σ_g (K_i − K_j)(S_i − E_i⁰)
  junior_compensation:     float   # (3) Σ_g C_g^c
  global_adjustment_posted: float  # (4) Σ_i A_i, global part
  federation_adjustment_posted: float # (5) 0.0 while disabled
  rounding_residual:       float   # (6) Σ_i ρ_i; bounded by 0.5 × players with a rated month
  entering_with_newcomers: float   # (7) Σ of first published ratings
  leaving_below_floor:     float   # (8) Σ of ratings of players removed from the list under §7.2.1
  change_in_list_total:    float   # (9) must equal (2)+(3)+(4)+(5)+(6)+(7)−(8) exactly
  memo_newly_inactive:     float   # (10) ratings held by players flagged inactive this month (not in the identity)
  memo_accrued_balance:    float   # Σ_i B_i outstanding (T4.5)

signatures:
  engine_git_commit:  string    # 40-hex commit of the Layer 0/2 engine that will consume this file
  input_games_sha256: string    # sha256 of the TRF (or test) game file for the period
  previous_file_sha256: string  # chain to last month's file
  approved_by:        string    # QC member(s) signing; role, not a private name, in the public copy
  approved_on:        date
```

### T7.2 Example file: standard chess, list of 1 February 2027

PROVISIONAL / ILLUSTRATIVE: parameter values from NOTATION.md; every measured quantity is invented to show the format.

```yaml
schema_version: "pf-0.2"
list_date: 2027-02-01
time_control: standard
status: "PROVISIONAL / ILLUSTRATIVE"

expected_score:
  kappa:  {value: 1.00,  unit: dimensionless, cap_per_year: 0.05}
  eta:    {value: 35,    unit: rating points, cap_per_year: 5}
  alpha:  {value: -0.50, unit: log-odds, cap_per_year: 0.20}
  beta:   {value: 0.55,  unit: log-odds per 400 points, cap_per_year: 0.10}

development_coefficient:
  K_min:     {value: 10.0, cap_per_year: 2}
  K_max:     {value: 40.0, cap_per_year: 2}
  sigma_new: {value: 100,  cap_per_year: 15}
  C_period:  {value: 700,  cap_per_year: fixed}

global_adjustment:
  a_t: 1.1                      # = clip(γ_a × d_t, ±a_cap) = clip(6.6 / 6, ±1.5), one decimal
  a_cap: 1.5
  gamma_a: 0.1667               # 1/6
  anchor_cohort:
    definition: "Players aged 25-45 by birth year on the re-basing date with at least 10 rated standard games in each of the three preceding calendar years and a published rating throughout; fixed panel, re-based each 1 January, chain-linked."
    rebased_on: 2027-01-01
    n_members: 38412            # illustrative
    m_t: 2041.3                 # illustrative
    m_hat_t: 2047.9             # illustrative
    d_t: 6.6

federation_adjustment:
  enabled: false
  threshold: "PROVISIONAL: |phi_f| / s_f >= 3 and eff_resistance <= 0.05 and >= 1000 cross-pool games in the window; enabled only by Council decision after the FIDE-data backtest (T8)."
  federations_qc_annex_sha256: "0000…0000"   # placeholder; the per-federation block below is in the QC-only annex while enabled = false
  federations:                  # QC-ONLY while disabled; codes and numbers illustrative, not estimates for any real federation
    - {fed: AAA, phi_f: 12.4,  s_f: 9.8,  component_id: 1, eff_resistance: 0.031, passes_threshold: false, a_f_t: 0.0}
    - {fed: BBB, phi_f: -41.0, s_f: 11.2, component_id: 1, eff_resistance: 0.044, passes_threshold: false, a_f_t: 0.0}
    - {fed: CCC, phi_f: 77.5,  s_f: 38.9, component_id: 1, eff_resistance: 0.210, passes_threshold: false, a_f_t: 0.0}

junior_compensation:
  tau:   {value: 50,   cap_per_year: 10}
  c_cap: {value: 300,  cap_per_year: 50}
  p_min: {value: 0.90, cap_per_year: fixed}
  eligible:                     # illustrative identities and values; public copy
    - {fide_id: 900000001, R_j: 1812, c_j: 119}
    - {fide_id: 900000002, R_j: 2105, c_j: 94}
  eligible_qc_annex_sha256: "0000…0000"   # placeholder

seeds_inactivity_floor:
  R_floor:   {value: 1400, cap_per_year: fixed}
  R_seedmax: {value: 2200, cap_per_year: fixed}
  N_seed:    {value: 5,    cap_per_year: fixed}

layer1_hyperparameters:
  window_months: {value: 36, cap_per_year: fixed}
  method: map_laplace
  drift_mu_by_age:              # points per month at θ = 2000, illustrative; bands as in T2.2
    - {age_band: "<12",   mu: 7.5}
    - {age_band: "12-15", mu: 5.0}
    - {age_band: "16-19", mu: 2.5}
    - {age_band: "20-24", mu: 0.8}
    - {age_band: "25-45", mu: 0.0}
    - {age_band: "46-60", mu: -0.3}
    - {age_band: ">60",   mu: -0.8}
  sigma_theta_by_age:           # points per month, illustrative; bands as in T2.2
    - {age_band: "<12",   sigma_theta: 25}
    - {age_band: "12-15", sigma_theta: 25}
    - {age_band: "16-19", sigma_theta: 20}
    - {age_band: "20-24", sigma_theta: 14}
    - {age_band: "25-45", sigma_theta: 12}
    - {age_band: "46-60", sigma_theta: 15}
    - {age_band: ">60",   sigma_theta: 15}
  rho: 0.97
  omega: 8.0
  rng_seed: 20270201
  fit_diagnostics:
    oos_log_loss_3way: 0.9412   # nats per game, illustrative
    n_games: 9871234
    n_players: 611209
    n_connected_components: 3

ledger_totals:                  # points, illustrative
  moved_by_results_gross: 2418766.3
  created_by_unequal_K: -1843.3
  junior_compensation: 2194.4
  global_adjustment_posted: 198176.0   # Σ of the balances posted this month (illustrative)
  federation_adjustment_posted: 0.0
  rounding_residual: 31.2
  entering_with_newcomers: 6121035.0
  leaving_below_floor: 172260.0        # magnitude; subtracted in the identity
  change_in_list_total: 6147333.3      # = (2)+(3)+(4)+(5)+(6)+(7)−(8) = −1843.3 + 2194.4 + 198176.0 + 0.0 + 31.2 + 6121035.0 − 172260.0
  memo_newly_inactive: 4018812.0
  memo_accrued_balance: 61204.1

signatures:
  engine_git_commit: "0000000000000000000000000000000000000000"   # placeholder
  input_games_sha256: "0000…0000"                                 # placeholder
  previous_file_sha256: "0000…0000"                               # placeholder
  approved_by: "FIDE Qualification Commission (two signatories)"
  approved_on: 2027-01-29
```

## T8 Evaluation pre-registration

### T8.1 Baselines

| Baseline | What is fitted | Source |
|---|---|---|
| L0 FIDE-exact | Nothing: today's rules exactly, table 8.1.2, the 400-point rule with the 2650 exemption, K 40/20/10, K × n ≤ 700, two 1800 draws, 1400 floor, as in SPEC-L0 | [V 1] [V 2] |
| Logistic Elo | AR-1 with κ = 1, ν = 0, η = 0 (the reduction proved in T3) and one fixed K chosen on the training months | [R §1] [R 15] |
| Elo++ | Logistic Elo fitted in batch with L2 regularisation weighted by game count, recency and opponents; two global parameters, White's advantage and the regularisation constant | [R §4] [R 60] [R 61] |
| Glicko-2 | Rating, rating deviation and volatility per player, forward-only, one system constant fitted | [R §4] [R 34] [R 64] |
| TrueSkill Through Time | Gaussian skill chain with smoothing and explicit draw margin, fitted by expectation propagation on months ≤ t only | [R §4] [R 10] [R 69] [R 70] |
| WHR | Dynamic Bradley–Terry, MAP by Newton's method over each player's history, fitted on months ≤ t only | [R §4] [R 11] [R 12] |

L0 has no draw model, so for the three-outcome metrics it is scored with an empirical draw split by level band from the training months. TrueSkill Through Time and WHR revise the past; only their estimate at the forecast origin is used.

### T8.2 Protocol

Rolling origin: fit on months ≤ t, forecast every rated game of month t + 1, score, roll one month, over the last 24 months of the data (the first 36 are training only). The match schedule is never a feature: the Kaggle 2011 winner conceded that schedule information drove much of his edge, which is not legitimate for an official rating [R 9] [R §9].

### T8.3 Metrics

Games g = 1 … G in the test month, outcome y_g ∈ {W, D, L} from the player's side, forecasts P_W, P_D, P_L, expected score E_g, score S_g.

| Metric | Definition |
|---|---|
| Three-outcome log-loss | LL = −(1/G) Σ_g Σ_{o ∈ {W,D,L}} 1[y_g = o] · ln P_o(g), nats per game |
| Ranked probability score | RPS = (1/G) Σ_g (1/2) Σ_{k=1}^{2} (F_k(g) − O_k(g))², where F_k and O_k are the cumulative forecast and outcome over the ordered outcomes L < D < W |
| Brier on expected score | B = (1/G) Σ_g (S_g − E_g)² |
| Calibration by bin | For each bin b (gap x in 50-point bins to 1000; level band of 200 points; colour; time control; federation pair): mean residual r_b = mean(S_g − E_g) and the slope of S on E by least squares within b; reported for bins with at least 1,000 games |
| Anchor-cohort drift | D_t = m_{t} − m_{t−12}, the twelve-month change of the published mean of the fixed anchor panel (chain-linked at each re-basing), points per year [R 22] |
| Cross-federation residual | r_f = mean(S_i − E(x_i)) over games with i ∈ f and j ∉ f, in score units, and in points r_f / E′(0; tc, L̄_f) with E′(0) = κ_tc (ln 10/400) / (2(2 + ν)) |
| Monitoring indicators | Published monthly without names: per-event lines (2) and (3) of the ledger with the top percentile flagged; a farming index (share of a player's gain from opponents 300 or more points below, including games against compensated juniors); returns from inactivity whose first-10-game score exceeds the expectation by more than 2 SD (PROVISIONAL threshold); |θ̃_i − R_i| > 2 σ_i for any player (the sandbag indicator); federation offsets moving faster than their cap would allow; Cov(θ, δ_tc) and the cross-time-control correlation as fit diagnostics |
| Newcomer convergence | Real data: mean three-outcome log-loss over a player's games 1–30 against the pool average. Simulation (T9): N_50 = the game count after which |R_i − θ_i| < 50 and stays below for the rest of the run |

### T8.4 Significance

Paired block bootstrap by month: resample the T test months with replacement, recompute each metric for each system on the resampled months, take the paired difference against L0, repeat 2,000 times with a published seed, report the 2.5 and 97.5 percentiles as the 95 % interval. A difference counts only if the interval excludes zero. Months, not games, are the blocks because games in a month share ratings and parameter file.

### T8.5 Success thresholds (all PROVISIONAL; carried from v0.1 §8 unless noted)

| Criterion | PROVISIONAL threshold |
|---|---|
| Three-outcome log-loss, held-out months | at least 2 % better than L0 in every level band, interval excluding zero |
| Ranked probability score and Brier | better than L0 overall, interval excluding zero (new in v0.2) |
| Calibration | slope of S on E within 0.95–1.05 in every gap bin with ≥ 1,000 games, now to 1000 points because AR-1 removes the caps (v0.1 said 800) |
| Anchor-cohort drift | within ±2 points per year (the report's post-reform figure is about −16 per year [R 5]) |
| Cross-federation residual | within ±10 points for every federation with ≥ 1,000 cross-border games in the window; with a_{f,t} = 0 this tests the global channel plus seeds, as shipped |
| Newcomer convergence (simulation) | median N_50 ≤ 15 games |
| Adversarial simulations (T9) | no strategy gains more under L2 than under L0, and farming yields fewer points per game than honest play against equals |
| Hand-checkability | 100 % of a random sample of 1,000 published changes recomputed exactly from the breakdown and the parameter file |

Decision rule: Layer 2 must beat Layer 0 on log-loss, RPS and Brier with intervals excluding zero, meet the drift and calibration thresholds, and keep P1 forward-only, P2 bounded change, P3 continuity, P4 unbiasedness, P5 ledger completeness and P6 determinism, which T5 proves from the rules. A partial result is reported as partial.

### T8.6 Data plan

1. Method development: the Lichess open database, CC0 ("Use them for research, commercial purpose, publication, anything you like" [V 4]), about 28–33 GB and 85–100 million standard games per month in 2024–2026 [V 4]; broadcasts (CC BY-SA 4.0 [V 4]) as the over-the-board slice. Online data calibrates methods, never FIDE parameters.
2. Player panel: FIDE's monthly lists with K, games, birth year and federation [V 3]; no data licence is stated [V 3], so: download, analyse, never redistribute.
3. Formal request: FIDE's TRF archive, the game record submitted under §9.1 [V 1], under a data-sharing agreement (Phase C); the only data on which φ_f can be tested.

### T8.7 What is fixed and what may change

Pre-registered now: baselines, protocol, metric formulas and bins, bootstrap procedure and seed, thresholds, anchor-cohort definition, decision rule, P1–P6. May change until the Lichess backtest is complete, each change dated in the parameter-file history: the PROVISIONAL parameter values, the L1 hyperparameter grid, the federation threshold text. Nothing changes after the first FIDE TRF month is unsealed.

## T9 Simulator design

Phase A work (v0.2 §10), not engine code: it calls the Layer 0 and Layer 2 engines as libraries and nothing in it is published with a list. It measures what no backtest can: recovery of known true skill and the yield of strategies absent from honest data. All values PROVISIONAL.

### T9.1 Data-generating process

| Block | Parameters (PROVISIONAL) |
|---|---|
| Federations | N_F = 6; sizes N_f = 20,000 / 10,000 / 5,000 / 2,000 / 1,000 / 500 players at start |
| Pairing geography | within-federation share π_within = 0.90 of a player's games; cross shares C_{ff′} = (1 − π_within) · N_{f′} / Σ_{f″≠f} N_{f″}; scenario files may overwrite any row of C |
| True skill | s_{i,tc}(0) = θ_i(0) + δ_{i,tc}; θ_i(0) ~ Normal(m_f, 300²) with m_f = 1800 for all f in the baseline; δ_{i,tc} ~ Normal(0, 60²) with ρ = 0.97, ω = 8 |
| Age at start | mixture: 35 % aged 8–17 uniform, 65 % aged 18–65 with density decreasing linearly to zero at 65 |
| Improvement curve μ(age) | +8.0 points per month at age 10, falling linearly to 0 at age 22; 0 from 22 to 45; −0.3 per month 46–60; −0.8 above 60 (large for juniors, near zero for adults) |
| Random walk σ_θ(age) | 25 points per month under 18; 12 for 18–45; 15 above 45 |
| Entries | 0.5 % of the active pool per month (about 3,500 per month at FIDE scale [R §6]); entrant age profile: 60 % aged 8–15, 25 % aged 16–25, 15 % older; entrant θ drawn from Normal(m_f − 150 + 25 · (age − 10)⁺, 250²), truncated at 800 |
| Exits (monthly hazard) | 0.3 % baseline; 2.0 % for ages 18–20 (school leavers); 1.0 % above 60; 1.5 % for players inactive 12 months or more, who first stop playing and then leave |
| Activity | games per player per year ~ lognormal, median 30, 10th percentile 8, 90th percentile 90; a player's year is split into events |
| Event types | 80 % Swiss (9 rounds; 5 or 7 in 15 % of events each): round 1 top half against bottom half by rating, later rounds within score group, top half of the group against its bottom half, odd player floats down; colours alternate, difference never beyond ±2, never three in a row. 20 % round-robin: 10 players, Berger colours. 90 % of an event's entrants from the host federation |
| Outcomes | AR-1 Davidson model with true skills: z = κ (ln 10/400)(s_i − s_j + w_i η), ν = exp(α + β (L_true − 2000)/400), κ = 1.00, η = 35, α = −0.50, β = 0.55 (standard) |
| Rating lists | monthly; L0 exactly as SPEC-L0 (table 8.1.2, 400-point rule with 2650 exemption, K 40/20/10, K × n ≤ 700, two 1800 draws, 2200 maximum, 1400 floor, 5 games, rounding) [V 1]; L2 as T4 with L1 re-fitted monthly, 36-month window |
| Run length | 120 simulated months after a 36-month burn-in; 20 seeds per scenario |

### T9.2 Scenarios

1. Baseline stationary pool: entries equal exits in skill flow, m_f equal.
2. Deflating pool with a junior wave: entry rate doubled, entrant age 60 % under 12, μ(age) 1.5 times the baseline.
3. Two isolated federations: C set so that federations 5 and 6 play 1 % of games outside, with m_5 = +100 and m_6 = −60 relative to the rest; measures whether φ_f is recovered and how the global channel behaves without the federation channel.
4. Farming pool: 50 players rated above 2600 who choose events whose field averages 400 to 800 below them.
5. Mass inactivity and return: 30 % of the pool inactive for 24 months, then returning with true skill moved by their random walk.

### T9.3 Channel ablations

Cumulative against L0: (a) AR-1 expected-score function only, FIDE's K; (b) plus K_i from uncertainty; (c) plus adjustments a_t; (d) plus compensation c_j; (e) plus L1 seeds. Each step reports the T9.5 outputs.

### T9.4 Adversaries

100 agents per strategy, under L0 and under L2, against the same agents playing honestly; measured as points gained per game and per year relative to honest play, with the 20-seed interval.

| Adversary | Behaviour simulated | Quantity measured |
|---|---|---|
| Farmer | plays only events with fields 400–800 below own rating | points per game versus honest play against equals |
| Sandbagger | loses deliberately for 12 months, then plays a target event honestly | points per year and peak-to-trough swing; whether K_i rises reward the dip |
| Colluding pair with unequal K | a K_min and a K_max player arrange results so the high-K partner gains | net points created per arranged game (ledger line "created by unequal K") |
| Arranged-draw ring | 8 players draw every mutual game | points protected per year versus honest play; detection statistic from the draw model |
| Inactivity protector | stops playing at a peak | points retained per year; under L2, growth of σ_i and K_i on return |
| One-game-a-month adjustment collector | plays exactly one rated game each month to collect a_t | points per year from a_t versus a player with the same games in one event (should be equal under the accrual rule of T4.5) |
| Compensation hunter | seeks juniors with c_j > 0 as opponents | points per game versus honest play; c_j enters only the hunter's expectation, so the expected yield is zero |
| Seed manipulator | plays the first N_seed games against chosen opponents | seed error |R_seed − θ| versus the honest seed error |

### T9.5 Outputs and acceptance checks

| Output | Acceptance (PROVISIONAL) |
|---|---|
| Recovery of true skill: RMSE of R_i − θ_i over active players, by level band and age band, per month | L2 RMSE below L0 RMSE in every band in scenarios 1–3 and 5 |
| Drift of the anchor mean: D_t over the run, and the mean of R_i − θ_i over the anchor cohort | within ±2 points per year in scenarios 1 and 2 |
| Newcomer convergence N_50 | median ≤ 15 games |
| Ledger: the T6 identity evaluated each month | closes to zero residual up to rounding: residual ≤ 0.5 × active players, in tenths |
| Adversary table | no strategy gains more under L2 than under L0 |
| Determinism | two runs with the same seed give identical lists and ledgers byte for byte |

## T10 Worked examples by hand

All arithmetic from `analysis/v02_calculations.py` (sections 5–8 of its output) with the PROVISIONAL parameters of T1; rounding to the published change assumes the game is the player's only game of the period. "Today" means the FIDE Rating Regulations as transcribed [V 1].

**T10.1 Example (i): an established 1900 adult against a 1500-listed junior whom Layer 1 rates at 1850.** A (1900, White, σ_A = 55 so K_A = 19.1) meets J (1500, Black, born such that J is eligible by age, σ_J = 100 so K_J = 40.0, ŝ_J = 1850; d_t is taken as 0 here, and in T10.3 as +7.2: either way c_cap binds and the example is unchanged). Eligibility: P(s_J − R_J > 50) = Φ((1850 − 1500 − 50)/100) = Φ(3.000) = 0.9987 ≥ 0.90; c_J = min(1850 − 1500, 300) = 300, so RX_J = 1800 (the cap binds). Level L = 1700, band 1600–1799, ν = 0.4015. A's gap x_A = 1900 − 1800 + 35 = 135, E_A = 0.656 from the table (without compensation x would be 435 and E 0.884). J's gap x_J = 1500 − 1900 − 35 = −435, E_J = 1 − E(435) = 0.116: J's own update uses published ratings only.

Today: D = 400, not "more than 400", so no cap applies; table 8.1.2 row 392–411 gives .92 to A and .08 to J; K = 20 for A and 40 for J (junior under 2300) [V 1].

| Result | A today: 20 × (S − .92) | J today: 40 × (S − .08) | A under Layer 2: 19.1 × (S − 0.656) | J under Layer 2: 40.0 × (S − 0.116) |
|---|---|---|---|---|
| A wins | +1.6 → **+2** | −3.2 → **−3** | +6.5704 → **+7** | −4.6400 → **−5** |
| Draw | −8.4 → **−8** | +16.8 → **+17** | −2.9796 → **−3** | +15.3600 → **+15** |
| J wins | −18.4 → **−18** | +36.8 → **+37** | −12.5296 → **−13** | +35.3600 → **+35** |

The adult is no longer drained for drawing a junior who is really an 1850 player (−3 instead of −8) and is paid for beating one (+7 instead of +2); the junior still climbs at full speed (+15 for a draw, +35 for a win), because the junior's own update never sees c_J. Ledger lines for this game (T6, with E_A⁰ = 0.884):

| Result | transfer J → A, ½(19.1 + 40.0)(S_A − 0.884) | created by unequal K, (19.1 − 40.0)(S_A − 0.884) | created by compensation, 19.1 × (0.884 − 0.656) | sum of the two changes |
|---|---|---|---|---|
| A wins | +3.4278 | −2.4244 | +4.3548 | +1.9304 |
| Draw | −11.3472 | +8.0256 | +4.3548 | +12.3804 |
| J wins | −26.1222 | +18.4756 | +4.3548 | +22.8304 |

In every row the sum of the two players' changes equals the two creation terms exactly; the compensation term, +4.3548 points, is the same whatever the result: it is the deflation the adult used to pay, now printed as a ledger line. E_A + E_J = 0.772, less than one, is the same fact seen from the expectations.

**T10.2 Example (ii): a 2600 against a 2100, and a 2700 against a 2100.** The strong player has White and σ = 45, so K_i = 16.1 (PROVISIONAL). Today both have K = 10 [V 1]. The 2600 is below 2650, so D = 500 is counted as 400 (row 392–411, PD = .92); the 2700 is at or above 2650, so D = 600 is used in full (row 560–619, PD = .98). In rapid and blitz the plain 400-point cap applies to both and, with a player above 2600 and a difference of 600 or more, the second game is not rated at all [V 2].

| Player | Opponent | Today: D used, PD | Today: win / draw / loss | Layer 2: x (with +35 for White), band, E | K_i | Layer 2: win / draw / loss |
|---|---|---|---|---|---|---|
| 2600 | 2100 | 400, .92 | +0.8 / −4.2 / −9.2 | 535, 2200–2399, 0.884 | 16.1 | +1.8676 / −6.1824 / −14.2324 |
| 2700 | 2100 | 600, .98 | +0.2 / −4.8 / −9.8 | 635, 2400–2599, 0.899 | 16.1 | +1.6261 / −6.4239 / −14.4739 |

Why the farming incentive disappears. Under Layer 2 the expected change is K_i (P_W (1 − E) + P_D (½ − E) + P_L (0 − E)) = K_i (E − E) = 0 exactly (P4): the win is worth little and the loss costs much, in the exact ratio of their probabilities, at every gap, with no cap. Today the 2600's expectation is capped at .92 while the table's own uncapped value at D = 500 is .96 (row 485–517 [V 1]); if the uncapped table were right, every game against a 2100 would be worth 10 × (.96 − .92) = +0.4 points in expectation, which is the incentive the October 2025 amendment removed for players rated 2650 and above and left in place below [V 1] [R 55]. The cliff at 2650 today, and its absence under Layer 2 (each player beats a 2200 with White):

| Winner | Today: gap used, PD, gain at K = 10 | Layer 2: x, band, E, gain at K_i = 16.1 |
|---|---|---|
| 2649 | 400, .92, +0.8 | 484, 2400–2599, 0.845, +2.4955 |
| 2651 | 451, .94, +0.6 | 486, 2400–2599, 0.846, +2.4794 |
| 2700 | 500, .96, +0.4 | 535, 2400–2599, 0.866, +2.1574 |
| 2936 | 736, 1.0, +0.0 | 771, 2400–2599, 0.932, +1.0948 |

Today the gain jumps between 2649 and 2651 for the same result against the same opponent and vanishes above a 735-point gap; under Layer 2 it declines smoothly and never reaches zero. The Layer 2 gains are larger than today's because the PROVISIONAL draw parameters make E lower at these gaps than table 8.1.2 (T3.3); whether that is right is what the calibration gate of T8 decides before any table is published.

**T10.3 Example (iii): one month's adjustment for one player.** Standard list; the anchor cohort's published mean is m_t = 2004.6 and its latent mean m̂_t = 2011.8, so d_t = +7.2. a_t = clip(γ_a d_t, −a_cap, a_cap) = clip(7.2/6 = 1.200, −1.5, +1.5) = +1.2 (one decimal); a_{f,t} = 0 (disabled). The player had three rated games with game terms −2.4090, +5.8410, −8.7000 (sum −5.2680) and no accrued balance from earlier months. Period total −5.2680 + 1.2 = −4.0680, rounded under §8.3.4 [V 1] to **−4**. Had the player not played this month, no game terms and no posting: the rating is unchanged, and the month's a_t accrues to the balance to be posted in the next rated month (T4.5). Ledger: +1.2 under line 4 for this player; in aggregate 1.2 × the number of players posted that month. In the stylised pool of script §7, with a steady deflationary pressure of 1.3 points a month, a_t rises over about a year to +1.3 and the measured gap settles near 7.8 points, which is drift/γ_a (T4.5).

**T10.4 The ledger on a synthetic month (script §8).** Seven listed players (ratings 1900, 1500, 2050, 1750, 2300, 1600, 1405; σ 55, 100, 50, 70, 45, 120, 60; the 1500 is a compensated junior with RX = 1800), eight rated games, one further game against an unrated player (not rated for anyone, T4.1), a_t = +1.2 posted to all seven, and one newcomer seeded at 1650. Published changes −10, +72, +11, −22, −1, +27 and −8; the last takes the 1405 player to 1397, below the floor, so that player leaves the list at the post-update rating 1397. List total before 12505, after 12827: change +322. Ledger: created by unequal K +34.9115; created by compensation +26.8940; adjustments posted 7 × 1.2 = +8.4 (the exiting player included); rounding residual −1.2055; newcomers +1650; exits −1397; total +322.0000. Transfers cancel by construction and the identity of T6 closes exactly; booking the exit at the pre-update 1405 would leave a residual of 8 points, which is why T6 books R_i⁺(t).

---
## T11 Transition

Four stages; nothing in stages 1–3 touches the official list.

### Stage 1: Layer 0 replica, now

The reference engine implements the Rating Regulations exactly (docs/specs/SPEC-L0_fide-reference-engine_v0_1.md), test-vector verified against FIDE's calculator and against sampled players' changes between consecutive monthly lists [V 1] [V 3]; the rapid and blitz branches carry the plain 400-point cap and the 600-point exclusion [V 2]. Gate: exact reproduction of every sampled change. Needs nothing from FIDE.

### Stage 2: twelve-month shadow list

Published in parallel with the official list for twelve months, with no effect on titles, norms, pairings or prizes. Precedent: during the 2008–2011 K-factor trial, when top players raised "major concern", FIDE ordered a parallel list so both calculations could be compared before anything changed [R §2] [R 16].

Published each month: the shadow list (rating, K_i, games, RX_j for compensated juniors); the parameter file (T7) per time control; the ledger (T6); a monitoring report with the T8 metrics and the anomaly indicators of v0.2 §9, without names.

Rollback: if any T8.5 threshold is breached two months running, the parameter file reverts to the last compliant file while the QC investigates, and the reversion is published. The QC signs every parameter file (T7 signatures block); the project team proposes, never signs. If the pilot is abandoned, nothing happens to anyone's rating: the official list was never touched; the shadow list stops with a closing report.

### Stage 3: pilot federation

One federation (not named; founder decision, v0.2 §11 decision 2) runs the shadow list as its national list for a defined period, PROVISIONAL twelve months, for domestic purposes. FIDE's official list remains the one used for titles, norms and every FIDE purpose. Publication, rollback and signature as in stage 2. Gate: twelve clean months and a QC report.

### Stage 4: adoption by Council decision

Changes to the Rating Regulations [V 1] and the Rapid and Blitz Regulations [V 2], paragraph numbers as verified on 2026-10-09.

| Paragraph | Today [V 1] [V 2] | Change |
|---|---|---|
| §8.1.2 (and the rapid/blitz equivalent) | one table of D into PD | replaced by the yearly table per time control and level band (T3), published by the QC |
| §8.3.1; §7.3.1 rapid/blitz | 400-point rule with the 2650 exemption; the plain 400-point cap and the 600-point exclusion | deleted; the table has no caps |
| §8.3.2 | "Delta R = score − PD" | wording only: S − E from the yearly table, with x including the colour term and c_j |
| §8.3.3; §7.3.3 | K = 40 / 20 / 10 by games, rating and age; K × n ≤ 700 | K replaced by the published K_i (AR-2); the K × n ≤ 700 sentence kept, restated for K_i with C_period |
| §8.2.2; rapid/blitz §7.2.3 | two hypothetical opponents rated 1800, scored as draws | replaced by the L1 seed (AR-5); §8.2.3's 2200 maximum and §7.1.4's five games kept |
| §7.2.1 | below 1400 shown as unrated, then treated as unrated | unchanged in text; Layer 1 keeps estimating the player, and re-entry under §7.1.4 is seeded from the Layer 1 posterior instead of two phantom draws (T4.7) |
| new paragraph | none | the monthly adjustment a_t (and a_{f,t}, disabled): accrued to active players, posted in a rated month, with its cap and its source in the parameter file (AR-3, T4.5) |
| §7.1.2 | closed list of published fields | add the columns RX (R_j + c_j) and K to one decimal (T4.1) |
| §8.1 | "the two tables are effectively mirror-images" | table 8.1.1 (p into dp) is retained unchanged wherever any regulation refers to it; only 8.1.2 is replaced, so the sentence is deleted |
| new paragraph | none | publication of the parameter file and the ledger with every list (AR-6) |

Paragraphs that do not change: §1 rate of play (and rapid/blitz §1.1); §5 unplayed games; §6 matches; §7.1.3 closing date; §7.1.4 five-game threshold and 26-month pooling; §8.3.4 rounding (and §7.3.4); §9.1 TRF reporting [V 1] [V 2].

Title and norm regulations are not touched by this proposal (they are NOT VERIFIED in this project and will be transcribed before v1.0). Table 8.1.1 is retained wherever they refer to it. The shadow list has no legal status: no title application, norm, pairing, seeding, prize or eligibility rule may refer to it. The interaction of the new expectation table with norm arithmetic is for the QC to assess before stage 4. After adoption Layer 0 keeps running on the same tournament reports for at least 24 months, so that the Council can revert to the Layer 0 list by decision for the following month without any retroactive edit.

No one-off adjustment at adoption: the official list continues from its own values and any gap to the shadow list closes only through the capped monthly adjustments of AR-3 (|a_t| ≤ a_cap, PROVISIONAL 1.5 points per month), so ratings still change only for players who play, visibly in the ledger.

---

*End of DRAFT v0.2 technical annex. Status line repeated: DRAFT v0.2 — not for publication.*
