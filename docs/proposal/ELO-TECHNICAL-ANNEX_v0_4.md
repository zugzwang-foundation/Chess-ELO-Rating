# Technical annex to the proposal "Modernising the FIDE Elo Rating System", v0.4

**Status: DRAFT v0.4 — not for publication**
Author: The Zugzwang Authors · Licence: CC BY 4.0 (`docs/LICENSE-docs.md`) · Date: 2026-10-10
Companion to `docs/proposal/ELO-PROPOSAL_v0_4.md` and its plain-language brief `docs/proposal/ELO-BRIEF_v0_4.md`. Architecture as ratified in `docs/decisions/D-0003_architecture-revisions-v0.2.md` (AR-1 to AR-6), revised by the architect's decisions D1–D18 (`docs/decisions/D-0005_architect-decisions-v0.3.md`) and, for v0.4, by the rulings R1–R14 (`docs/decisions/D-0008_architect-rulings-elo-4.md`). Every calculated number in this annex is produced by `analysis/v04_calculations.py` (output in `analysis/OUTPUT_v0_4.md`, cited as "script §n") unless it is cited to an evidence report; every parameter value is PROVISIONAL until estimated from data, and the expected-score table's are PROVISIONAL-FITTED (T1). Citations: `[R §x]`, `[R n]` the research report `docs/research/ELO-RESEARCH_v1_0.md`; `[V k]` item k of `docs/research/VERIFICATION_2026-10-09.md`; `[VP k]` item k of `docs/research/VERIFICATION_PRIOR-WORK.md`; `[E n]` evidence report n under `docs/evidence/`, each the output of a committed script (E0 Layer 0 against FIDE, E1 FIDE's monthly lists, E2 the broadcast calibration, E3 the 2026 U.S. Championship, E4 the community register, E5 deflation, E6 the rungs on history, E7 federation residuals). The Layer 1 model is specified in `docs/specs/SPEC-L1_v1_0.md` and fitted on history in `analysis/OUTPUT_L1_history.md`.

Contents: T1 Notation · T2 Layer 1 model · T3 Expected-score function and its calibration fit · T4 Layer 2 rules · T5 Properties P1–P6 · T6 Ledger identity · T7 Monthly parameter file · T8 Evaluation pre-registration · T9 Simulator design · T10 Worked examples · T11 Transition.

---

## T1 Notation

Every symbol is defined here once and used with this meaning everywhere in the proposal, the brief and the annex.

**Indices.** i, j players; g a game; t a month (a rating period, identified by its list date); tc ∈ {standard, rapid, blitz} (and, for T2.7 only, 960); f a federation.

**Published quantities (Layer 2).**

| Symbol | Meaning | Grid |
|---|---|---|
| R_i | published rating of i in time control tc | whole number |
| K_i | published development coefficient of i (rung 4, T4.3), printed in the list's K column | one decimal |
| S_i | score of i in a game: 1, ½, 0 | exact |
| w_i | colour indicator: +1 White, −1 Black (w_j = −w_i) | — |
| L | level of a game, the whole-number part of (R_i + R_j)/2, from the two published ratings without compensation | whole number |
| c_j | junior compensation of j (rung 5, T4.6); 0 unless j is eligible | whole number |
| RX_j | R_j + c_j, the rating used in opponents' expectations; a list column | whole number |
| x_i | effective gap for i: x_i = R_i − RX_j + w_i · η_tc | whole number |
| E(x; tc, L) | expected score from the published table of tc in the level band of L (T3) | three decimals |
| P_W, P_D, P_L | the three outcome probabilities behind E | — |
| a_t | global calibration adjustment of month t (rung 6, T4.5) | one decimal |
| a_{f,t} | federation calibration adjustment (rung 7, T4.5); 0 while disabled | one decimal |
| B_i | accrued, not yet posted adjustment balance of i, printed in the list | one decimal |
| R_i + B_i | settled rating, printed beside R_i for rating-based selections (T4.5) | one decimal |
| ΔR_{i,g} | game term K_i · (S_i − E(x_i)) | exact (at most four decimals) |
| n_i | number of rated games of i in tc in rating period t (the games of the period, for the cap of T4.4) | whole number |
| g_i | number of rated games of i in tc on the twelve lists up to and including list t (the sum of their games fields), for the accrual factor of R3 | whole number |
| round_FIDE(v) | nearest whole number, 0.5 away from zero (§8.3.4 [V 1]) | — |

**Layer 1 quantities.**

| Symbol | Meaning |
|---|---|
| θ_i(t) | shared latent skill of i at month t, on the Elo scale |
| δ_{i,tc}(t) | time-control offset of i; s_{i,tc}(t) = θ_i(t) + δ_{i,tc}(t) is i's latent strength in tc |
| ŝ_{i,tc}, σ_i | posterior mean and posterior standard deviation of s_{i,tc} at the list date (per tc), in latent units; σ_i is the quantity the K rule uses (R6) |
| θ̃_i, σ̃_i | θ̃_i = m_t + (ŝ_{i,tc} − m̂_t)/κ_tc (R2): the posterior mean brought onto the published scale in level and spread (with κ_tc = 1 it is v0.3's ŝ − d_t); σ̃_i = σ_i/κ_tc its standard deviation on that scale. The only Layer 1 estimates Layer 2 uses (T4.6, T4.7) |
| μ(age, θ) | expected monthly change of θ at a given age and level (drift) |
| σ_θ²(age) | monthly variance of the random walk of θ (process variance; distinct from σ_i) |
| ρ_tc, ω_tc | persistence and innovation standard deviation of δ_{i,tc} |
| μ_0(age), s_0 | prior mean (a function of age only, D4) and prior standard deviation of a new player's θ |
| η^L_tc, α^L_tc, β^L_tc, γ^L_tc | Layer 1's own outcome parameters, in latent units (T2.1); distinct from the table's parameters, which are fitted on published ratings (T3.3) |
| φ_f, s_f | mean miscalibration of federation f relative to the anchor pool, and its posterior SD |
| m_t, m̂_t | published mean and latent (Layer 1) mean of the anchor cohort at month t; d_t = m̂_t − m_t |
| G, N | number of games and of players in the fit window |

**Derived, ledger and threshold symbols.** q = ln 10/400 = 0.0057565, a constant (script §0); E_i⁰ expectation of i without compensation; T_g, C_g^K, C_g^c transfer, unequal-K creation and compensation creation of game g, O_g the change of a one-sided game under §8.2.4 [V 1] (T6); A_i the balance posted in month t (T4.5); ρ_i rounding residual (T6); N_anchor minimum anchor-panel size (PROVISIONAL 2,000); n_φ shrinkage constant for φ_f (PROVISIONAL 2,000 cross-pool games); s_max, R_max thresholds on s_f and on the effective resistance for any φ_f-dependent channel (PROVISIONAL, published in T7); σ_seed,max maximum posterior SD for a published seed (PROVISIONAL 120).

**Parameters (per time control unless stated; annual change caps in T7).** The table's κ, η, α, β and γ are PROVISIONAL-FITTED: maximum likelihood on the Lichess broadcast archive against FIDE's lists, 2023-10 to 2026-09 [E2] (`params/table_fit_2026-10.yaml`), η rounded to whole points for the published table. Every other value is PROVISIONAL.

| Symbol | Meaning | Value (standard / rapid / blitz) |
|---|---|---|
| κ_tc | slope of the outcome model on the published gap (T3.3) | 1.2120 / 0.9480 / 0.8735 |
| η_tc | colour term, in whole rating points | 36 / 37 / 27 |
| α_tc, β_tc | draw-term intercept and level slope | 0.2860, 0.4985 / −0.0396, 0.5271 / −0.7796, 0.4432 |
| γ_tc | decay of the draw term with the gap, γ_tc ≥ 0 with no upper bound (R7); a fit on any boundary is a calibration flag for the QC | 0.2915 / 0.2002 / 0.3145 |
| band width | width of the level bands of the published table (D6) | 100 |
| K_min, K_max | bounds of K_i (D3) | 10, 40 |
| C_period | per-period cap constant (today's 700, unchanged) | 700 |
| a_cap, γ_a, d_0 | cap on \|a_t\| per month; adjustment gain; soft deadband (D7) | 1.5 points; 1/6; 2.0 points |
| τ, c_cap, z | compensation margin, cap and posterior quantile (D5; z = 1.2816 is fixed, the 0.90 quantile of the standard normal) | 25, 300, 1.2816 |
| R_floor, R_seedmax, N_seed | display floor (§7.2.1), seed maximum (§8.2.3), games to seed (§7.1.4), all today's values [V 1] | 1400, 2200, 5 |
| v_tc(L) | per-game score variance at x = 0 in level band L, 1/(2(2 + ν_0(L))), read in the player's own band (R6) | standard 0.1681 at 1700, 0.1232 at 2300, 0.0928 at 2700 (script §5) |
| share_min | minimum share of the posterior precision coming from games in the same time control: of a junior's, for compensation (R5); of a newcomer's, for a seed (an executor's addition after REDTEAM_v0_4, V4-EXPLOIT-3, for the architect to confirm) | 0.5 |
| n̄ | the anchor cohort's mean number of rated games on the twelve lists up to t, the denominator of the accrual factor (R3) | measured monthly |
| θ_R1 | review threshold: the calendar-year mean of the noise-corrected spread ratio moving by more than θ_R1 in the same direction two years running (R1) | 0.02 (script §12) |

---

## T2 Layer 1 model

Layer 1 is the statistical model. It is re-estimated monthly on a rolling 36-month window of all rated games in all three time controls. It never edits a published rating; its only outputs are the monthly parameter file (T7) and the published diagnostics. Rungs 3 to 7 of the adoption ladder need it; rungs 1 and 2 do not (T8.1).

**T2.1 Outcome likelihood.** For a game g in month t and time control tc between White w and Black b, with latent strengths s_w = s_{w,tc}(t), s_b = s_{b,tc}(t):

> x_g = s_w − s_b + η^L_tc (latent gap, White's view)
> z_g = q · x_g
> ν_g = exp(α^L_tc + β^L_tc · (L_g − 2000) / 400) · exp(−γ^L_tc · |z_g|), L_g the level from the published list in force
> P(White wins) = e^{z_g/2} / D_g, P(draw) = ν_g / D_g, P(Black wins) = e^{−z_g/2} / D_g, D_g = e^{z_g/2} + e^{−z_g/2} + ν_g

This is the functional form of the published table (T3.1, D1) in latent units, where the slope is 1 by definition. In the specification (`docs/specs/SPEC-L1_v1_0.md` §3.2) its parameters are the published table's in latent units, held fixed: η^L = κ_tc η_tc, α^L = α_tc, β^L = β_tc, γ^L = γ_tc, because z is the log-odds of a decisive result in both models; refitting them jointly with modal strengths, which are shrunk towards their priors, biased them and stopped the sweeps converging on synthetic data (SPEC-L1 §3.2). Estimating them as hyperparameters on held-out games remains open for production; the published table's parameters are fitted separately on published ratings (T3.3, D2). The level L_g is taken from the published list, a known covariate. The log-likelihood is Σ_g log P(y_g), y_g the observed result.

**T2.2 Dynamics and priors.**

> θ_i(t+1) = θ_i(t) + μ(age_i(t), θ_i(t)) + ε_i(t), ε_i(t) ~ N(0, σ_θ²(age_i(t)))
> δ_{i,tc}(t+1) = ρ_tc · δ_{i,tc}(t) + ξ_{i,tc}(t), ξ ~ N(0, ω_tc²); stationary prior δ_{i,tc} ~ N(0, ω_tc² / (1 − ρ_tc²))
> θ_i(t_0) ~ N(μ_0(age_i(t_0)), s_0²) for a player first seen at t_0

Priors use age only (D4): no federation term enters μ_0 or any other seed, prior or default of the system, so a newcomer's starting estimate never depends on the passport. The prior SD s_0 is PROVISIONAL 250 points and is a field of the parameter file (T7). μ(age, θ) is piecewise linear in age bands (under 12, 12–15, 16–19, 20–24, 25–45, 46–60, over 60; PROVISIONAL) with a linear term in (θ − 2000)/400 inside each band, so that fast improvement may depend on level; σ_θ(age) is one value per band. The offsets δ are shrunk towards zero: with few games in a time control a player's strength there is essentially θ; with many, the offset is estimated (proposal §7). The age comes from the year of birth on the FIDE list [V 3]; a player without one is treated as an adult of unknown age (band 25–45) and is never eligible for compensation (T4.6).

**T2.3 Estimation.** Maximum a posteriori over all trajectories {θ_i(·), δ_{i,tc}(·)} given the hyperparameters, by Newton's method one player at a time as in Whole-History Rating [R 11] [R 12]: because consecutive months are linked only by the random walk, the Hessian of one player's trajectory is tridiagonal and a Newton step costs O(n_i) for a player with n_i months in the window; one sweep over all players costs O(G + Σ_i n_i); the fit is warm-started from last month's trajectories. The posterior standard deviation σ_i is read from the diagonal of the inverse of the tridiagonal Hessian at the list date (Laplace approximation). Two cautions are part of the specification. First, the per-player block Laplace gives the standard deviation conditional on the opponents' estimates and understates the marginal one in small, weakly connected pools; either expectation propagation as in TrueSkill Through Time [R 10] [R 69] is used for σ_i, or the block value is calibrated against it by simulation (T9); the choice is a pre-registered item (T8). Second, a hard window edge would make σ_i and K_i jump in the month a block of games leaves the window, so each player is initialised at the window start with the summarised prior N(ŝ(t − 36), σ²(t − 36) + process variance) from the previous fit (fixed-lag smoothing); nothing jumps when the window rolls. With FIDE's roughly 3 to 3.5 million standard games a year [R §7] a 36-month window holds about 10 million games; WHR processed 10.8 million Go games on 2008 hardware [R 11], so the monthly refit is a laptop-scale job.

Hyperparameters (η^L, α^L, β^L, γ^L, μ(·), σ_θ(·), ρ_tc, ω_tc, μ_0(·), s_0) are chosen by rolling out-of-sample three-outcome log-loss: fit on months up to t, score month t+1, roll forward, minimise the mean. They change at most once a year, within the caps of T7.

**T2.3a Fitted on history (ELO-4).** The specification was fitted on every broadcast game with FIDE IDs from January 2023 to September 2026: 776,825 games between 88,253 players, 95 sweeps to a largest move of 0.009 points. c_θ = 2.0 and ω = 4.0 were chosen on held-out games, both at the edges of the grids fixed before the fit, which are not widened after the fact. On held-out games the standard deviation of the standardised residual rises from 0.96 to 1.15 with σ, the plug-in forecast ignoring the players' uncertainty. The fitted drift is +193 points a year under 12, +152 at 12–15, +79 at 16–19, +44 at 20–24, 0 by definition at 25–45, −11 at 46–60 and −21 over 60. A usable estimate (σ̃ ≤ 100) exists for 13,089 of 221,130 active rated standard players: 95 % at 2600 and above, 0.7 % below 1600, 3.3 % of juniors aged 18 or less. Broadcast games are a fraction of each player's rated games, so σ and K_i are larger than a fit on FIDE's record would give (`analysis/OUTPUT_L1_history.md`).

**T2.4 Scale anchoring and identifiability.** The likelihood is invariant to adding one constant to every θ (and to every s), so the level of the latent scale must be fixed by a constraint. The constraint is the anchor cohort: a fixed panel of players aged 25–45 by year of birth on the re-basing date with at least 10 rated games in the time control in each of the three preceding calendar years and a published rating throughout (PROVISIONAL definition). At the reference month t_ref the mean latent strength of the panel equals its mean published rating. The panel is re-based every 1 January and chain-linked: the new panel's latent mean at the new reference month is set equal to its value under the previous month's fit, so the latent scale never jumps; the re-basing shift (zero by construction up to numerical tolerance) is published. The level over time is likewise unidentified by games alone (adding c · t to every θ changes no probability and the age drift μ would absorb it), so a second constraint defines it: the drift is zero in the anchor age band, μ(age, θ) ≡ 0 for ages 25–45, which makes the panel's mean drift zero; juniors' positive drift is identified relative to it. (Written in v0.2 as a monthly sum over the panel, which cannot hold month by month as members age out of the band within a 36-month window; REDTEAM_v0_3, V3-STAT-9.) The panel's constancy is therefore the definition of the scale, as in US Chess practice [R 22], not an empirical finding. The drift measurement is taken over current members as a mean of per-player differences on the settled rating, d_t = mean_{i ∈ anchor(t)} (ŝ_{i,tc}(t) − (R_i(t) + B_i(t))), so that membership churn does not bias it and an accrued but unposted adjustment is not counted as drift; m̂_t and m_t are its two halves. The monitoring report publishes the panel's size and composition each month. The history fit and the rung tests of E6 use SPEC-L1's panel (§3.5): aged 25–45 at t_ref = 2025-01 with at least 10 rated games in each of the two preceding years, fixed and not yet re-based [E6].

Within a player, θ_i and the δ_{i,tc} are jointly identified only through the shrinkage prior on δ (adding c to θ_i and −c to every δ_{i,tc} leaves every s unchanged); the prior resolves this softly, and the reported quantity for Layer 2 is always s_{i,tc}, which is identified by the games. Cov(θ, δ_tc) and the cross-time-control correlation are fit diagnostics in T7.

**T2.5 Pool offsets and graph diagnostics.** The miscalibration of federation f is a derived quantity, not a parameter:

> φ_f(t) = mean_{i ∈ f, rated month t} (ŝ_{i,tc}(t) − R_i(t)) − mean_{i ∈ anchor} (ŝ_{i,tc}(t) − R_i(t)),

with posterior SD s_f from the Laplace covariance. The second term equals d_t, so φ_f is net of the global drift by construction. It is identified only through games that cross pools. Two diagnostics are computed per federation each month: the connected component of the game graph (players as nodes, games in the window as edges) that contains the federation's players, and the effective resistance between the federation (its players merged into one node) and the anchor pool (merged into one node) in the game graph with unit conductance per game, computed from the graph Laplacian. The effective resistance is the Gaussian-approximation variance of the offset under equal game information, so a large value means the offset is poorly determined whatever the point estimate says. A channel that depends on φ_f acts only when s_f < s_max, the effective resistance is below R_max and the selection test of T4.5 passes; the federation adjustment ships disabled regardless (T4.5).

**T2.6 Outputs.** Per player and time control: ŝ_{i,tc} and σ_i (Layer 2 uses θ̃_i and σ̃_i, T1), and from them K_i; the information share of R5, eligibility and c_j for juniors; seeds for newcomers; the anchor statistics m_t, m̂_t, d_t and from them a_t; the spread ratio (R1); φ_f, s_f, the graph diagnostics and the selection test; the fit diagnostics of T7. Nothing else leaves Layer 1. ŝ, θ̃ and σ of named players are visible to the QC only (D17); K_i and RX_j are public. The resulting disclosure is accepted and stated (R4, founder default): K_i rises strictly with σ_i between K_min and K_max, so a published K_i reveals σ_i within a narrow band (K_i = 14.1 at R = 1900 implies 54.80 ≤ σ_i ≤ 55.00), and for a compensated junior with 0 < c_j < c_cap the pair (K_j, RX_j) reveals θ̃_j (K_j = 27.1 at R = 1500 gives θ̃_j = RX_j + 106.3; script §10b). D17's QC-only rule covers the full posterior and everything else.

**T2.7 Chess960 (D14).** FIDE's 2026 General Assembly approved plans for a dedicated Chess960 rating system [R §2] [R 25] [R 26]. The shared skill makes a 960 list a fourth offset, s_{i,960}(t) = θ_i(t) + δ_{i,960}(t), with δ_960 shrunk towards a population mean offset μ_960 (estimated, 0 at the start) with its own ω_960 and ρ_960. On day one every player with a standard, rapid or blitz record has a 960 estimate θ̃_i + μ_960 with an uncertainty that includes the offset's prior variance, so a 960 list can be seeded from existing ratings at once, with K near K_max, and separates from the other lists only as 960 games accumulate. Without Layer 1, the minimal form is the analogue of the rapid and blitz chapter's rule that an unrated player with a standard rating uses it (§7.2.1 of that chapter [V 2]). Whether FIDE's planned system works this way is NOT VERIFIED; this is a design option, not a description of FIDE's plan.

---

## T3 Expected-score function and its calibration fit

**T3.1 Definition (D1).** For player i against j with effective gap x (T4.2), time control tc and level L:

> z = κ_tc · q · x, q = ln 10 / 400
> ν(z) = exp(α_tc + β_tc · (L − 2000) / 400) · exp(−γ_tc · |z|), γ_tc ≥ 0 (R7); write ν_0 = exp(α_tc + β_tc · (L − 2000)/400)
> P_W = e^{z/2} / D, P_D = ν(z) / D, P_L = e^{−z/2} / D, D = e^{z/2} + e^{−z/2} + ν(z)
> E(x; tc, L) = P_W + P_D / 2 = (e^{z/2} + ν(z)/2) / D

Derivation: Davidson's model gives P(i wins) : P(draw) : P(j wins) = π_i : ν √(π_i π_j) : π_j with π = 10^{s/400}; dividing by √(π_i π_j) gives e^{z/2} : ν : e^{−z/2}. The factor exp(−γ |z|) lets the draw propensity decay with the gap. With γ = 0 this is the v0.2 form, in which draws decay only like e^{−|z|/2} and a heavy favourite's expectation stays far below today's table; with γ = ½ the favourite's draws would fade as fast as its losses, P_D/P_L = ν_0 for every z > 0. γ is fitted per time control with the other parameters (T3.3); since R7 it has no upper bound, because E is monotone for every γ ≥ 0 (T3.2), and a fit on any boundary is a calibration flag for the QC. On the broadcast archive of over-the-board games it is 0.2915 in standard, 0.2002 in rapid and 0.3145 in blitz [E2], strictly positive and below ½: the favourite's draws fade more slowly than its losses. At level 2300, P_D/P_L rises from ν_0 = 1.9346 to 3.4616, 6.1942 and 11.0837 at x = 400, 800 and 1200, against 1.9346 throughout with γ = ½ and 7.8087, 31.5196 and 127.2272 with γ = 0 (script §2).

**T3.2 Properties (proofs).**

1. *Symmetry.* ν depends on z only through |z|, and on L, which is the same for both players. Hence E(x) + E(−x) = [(e^{z/2} + ν/2) + (e^{−z/2} + ν/2)] / D = 1, and the table needs only x ≥ 0, with E(−x) = 1 − E(x) exactly as table 8.1.2 prints H and L [V 1]. (With compensation, x_i ≠ −x_j and the two expectations do not sum to one; T6 accounts for the difference.) Numerically (script §3): max |E(x) + E(−x) − 1| over x ∈ [−1500, 1500] and every band is at most 3.3 × 10⁻¹⁶ for γ = 0, ¼, the fitted 0.2915 and ½.
2. *Continuity and monotonicity.* E is a composition of continuous functions of x (|z| is continuous). For z ≥ 0 put u = e^{z/2} ≥ 1 and a = ν_0/2, so ν = 2a u^{−2γ}, E = N/M with N = u + a u^{−2γ}, M = u + u^{−1} + 2a u^{−2γ}. Then N′M − NM′ = 2/u + a(1 + 2γ) u^{−2γ} + a(1 − 2γ) u^{−2γ−2}, and since u ≥ 1, a(1 + 2γ) u^{−2γ} + a(1 − 2γ) u^{−2γ−2} = a u^{−2γ−2} [(1 + 2γ) u² + (1 − 2γ)] ≥ 2a u^{−2γ−2} ≥ 0; so dE/du ≥ (2/u)/M² > 0 and dE/dz = (u/2) dE/du > 0 for every γ ≥ 0. By symmetry E is also strictly increasing for z < 0. ν has a kink at z = 0, but E is differentiable there: the one-sided derivatives are equal because E(−z) = 1 − E(z). Numerically: min E(x + 1) − E(x) over x ∈ [−1500, 1500] and every band = 6.41 × 10⁻⁶, 8.86 × 10⁻⁷, 6.69 × 10⁻⁷ and 2.67 × 10⁻⁷ for γ = 0, ¼, the fitted 0.2915 and ½ (script §3).
3. *Logistic Elo as the special case.* With ν_0 = 0 (any γ) and κ = 1, E = 1/(1 + e^{−z}) = 1/(1 + 10^{−x/400}), the logistic form of Elo [R §1]; numerically the two agree to 2.2 × 10⁻¹⁶ (script §3). The model is a strict generalisation: it adds a draw propensity that grows with level and fades with the gap, and leaves the Elo odds for decisive results untouched.
4. *Local scale.* To first order in z the |z| terms cancel, so dE/dx at x = 0 is κ_tc q / (2(2 + ν_0)) whatever γ: near equal strength the curve behaves like logistic Elo with scale 200(2 + ν_0)/κ_tc, which is 481.2, 649.3 and 855.6 at levels 1700, 2300 and 2700 with the fitted standard parameters, against logistic Elo's 400 (numerical and analytic slopes agree to 10⁻⁹; script §3). κ and ν_0 are therefore jointly identified only through decisive results against draws, and the calibration fit must report both.
5. *Limits and the tail.* P_D at equal strength is ν_0/(2 + ν_0): 0.251 in the bottom band to 0.657 in the top one with the fitted standard parameters (script §1). For the favourite at large gaps, 1 − E = (e^{−z/2} + ν/2)/D; with γ = ½ it behaves like (1 + ν_0/2) e^{−z}, as fast as logistic Elo's tail, and with the fitted γ < ½ the draw term dominates and it decays like e^{−(½ + γ)z}, more slowly. At level 2300 the fitted function gives E = 0.699, 0.868, 0.920 and 0.973 at gaps of 200, 400, 500 and 700, against 0.723, 0.872, 0.917 and 0.966 under Sonas's 5/6-gap rule (logistic Elo on five sixths of the gap [R 44]), 0.718, 0.898, 0.945 and 0.985 with γ = ½ and 0.670, 0.805, 0.854 and 0.922 with γ = 0; today's table gives .76, .92, .96 and .99 [V 1] (script §2). No cap or clamp is needed: there is no x at which the function changes rule, and no result is ever worth exactly nothing.
6. *Colour is self-correcting per game.* Because x_i includes +η_tc for White and −η_tc for Black, the expectation already contains the colour. If the table is calibrated, the expected change of i in any single game is zero whatever the colour (P4, T5), so a player who happens to receive more Whites gains nothing in expectation: an extra White no longer pays. Under today's table, which gives .50 to both colours at equal ratings [V 1], one extra White is worth +0.88, +0.77 and +0.58 points in expectation at K = 20 at levels 1700, 2000 and 2500, where White's expectation with the fitted η = 36 is 0.544, 0.539 and 0.529 (script §4).

**T3.3 The calibration fit (D2).** The published table is fitted on published ratings, separately from Layer 1. For each time control, the parameters (κ_tc, η_tc, α_tc, β_tc, γ_tc) maximise the likelihood of the observed results given the published ratings in force at game time and the colours:

> ℓ(κ, η, α, β, γ) = Σ_g log P(y_g | z_g, L_g), z_g = κ q (R_W − R_B + η), L_g = ⌊(R_W + R_B)/2⌋ taken at the midpoint of its 100-point band, as the published table evaluates it (T3.4; `docs/specs/SPEC-TABLE-FIT_v1_0.md`), γ ≥ 0 (R7)

over the games of a fit window (PROVISIONAL: the last 36 months, refitted once a year, each value moved at most by its annual cap, T7). Once rung 5 is in force, games involving an eligible junior are left out of the fit, so that the table and the compensation do not absorb each other's residuals. With D_g = 1 for a draw, S_g White's score, s_g = sign(z_g), ℓ_g = (L_g − 2000)/400 and E_g, P_D,g the fitted values, the score equations are:

> (α) Σ_g (D_g − P_D,g) = 0 (β) Σ_g ℓ_g (D_g − P_D,g) = 0 (γ, interior) Σ_g |z_g| (D_g − P_D,g) = 0
> (η) Σ_g [(S_g − E_g) − γ s_g (D_g − P_D,g)] = 0 (κ) Σ_g (R_W − R_B + η) [(S_g − E_g) − γ s_g (D_g − P_D,g)] = 0

In words: the fitted draw probability matches the observed draw rate overall, along the level and along the absolute gap; and the score residual S − E, corrected by γ times the signed draw residual, has mean zero from White's side and no linear trend in the gap. (Derivation: ∂ log P(y)/∂z = (S − E) − γ s (D − P_D), ∂ log P(y)/∂α = D − P_D, ∂ log P(y)/∂γ = −|z| (D − P_D).)

**Property P4 for this fit.** *If the fitted table is calibrated on published ratings, that is, if for every published gap, level and colour the expected score equals the table entry, then the expected change of any player in any game, given the opponent's published and compensated rating and the colour, is zero:* E[ΔR_{i,g} | x_i, L] = K_i (E[S_i | x_i, L] − E(x_i; L)) = 0. *Maximum likelihood does not guarantee that calibration: it matches the five moment conditions above (in-sample, within the model family), and with γ at 0 only four of them. Calibration by gap, level and colour is an empirical property, tested out of sample by the calibration rule of T8; a residual m(x, L) = E[S | x, L] − E(x; L) is an expected gain of K_i · m per game from choosing such pairings.* Two limits are stated. First, P4 conditions on the published gap, level and colour only: choosing opponents on other information that predicts results (a federation whose pool is miscalibrated while rung 7 is disabled, under-rated juniors below the compensation gates, activity) is not covered; with E′(0) ≈ 0.0011 a point, a pool over-rated by 64 points is worth about +0.7 a game at K = 10 (REDTEAM_v0_3, V3-EXPLOIT-3), and the monitoring of T8.4 watches it. Second, the statement is about published ratings because that is what a player chooses on: a calibration on latent strengths, as in v0.2, would not guarantee it, since published gaps overstate strength gaps when ratings are too spread out (T3.5).

**T3.4 The published table (D6).** The successor to table 8.1.2 [V 1] is one table per time control, published yearly with the parameter file. Rows: one row for every whole-number x from 0 to 1500 (the QC extends the table whenever a list in force makes a larger gap possible), so no interpolation is needed and the table is normative; the parameter file documents the function that generated it. Columns: level bands of 100 points (below 1500; 1500–1599; …; 2700–2799; 2800 and above), with ν_0 evaluated at the band midpoint (1450 and 2850 for the two open bands); L is the whole-number part of the mean of the two published ratings. Entries: E to three decimals (half up, from a double-precision evaluation); three decimals resolve the top of the scale, where today's two decimals produce the "worth nothing above 735 points" effect [V 1] [R 55]. For negative x the arbiter uses E(−x) = 1 − E(x). The engine uses the same table, so engine and arbiter read identical values. Because the full table has 1,501 rows per band, each band is also published in table 8.1.2's range format (gap range → E), one line per change of the three-decimal value. Excerpt for standard, every other band (script §1):

| x | <1500 | 1600–1699 | 1800–1899 | 2000–2099 | 2200–2299 | 2400–2499 | 2600–2699 | ≥2800 |
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

The level bands make E step at band edges. With 100-point bands and the fitted parameters the largest step between adjacent bands, over every x from 0 to 1500, is 0.0115 (at x = 326, between 2700–2799 and 2800 and above; 0.0051 between the two lowest bands), and 0.012 in the published three-decimal table: at most 0.23 points in one game at K = 20. v0.2's choices (200-point bands, γ = 0) would give 0.0278, or 0.56 points; 200-point bands with the fitted γ would give 0.0231 (script §3.1). This is a table-resolution effect, not a rule, and it is symmetric for both players.

**T3.5 Level versus spread (D8, worded by R9).** A published scale can be wrong in two separate ways: its level (where a given strength sits) and its spread (how many points a given difference in strength is worth). The design gives each its own channel and rescales nothing. The monthly adjustment a_t holds the level: it adds the same amount to every active player in proportion to activity (R3), moves the anchor cohort's published mean towards its latent mean (T4.5), and changes no gap between equally active players. The spread is carried by the fitted table as a whole, κ together with the level-dependent draw term, not by κ alone: in the D1 form the local slope at equal ratings is κ_tc q / (2(2 + ν_0)) (T3.2, item 4), so on the broadcast archive, with κ = 1.21 and draws rising with level, the table behaves near equal ratings like logistic Elo with a scale of 481, 649 and 856 points at levels 1700, 2300 and 2700 against 400 [E2] (script §3). If published gaps overstate strength gaps, which is Sonas's finding that FIDE ratings are "too spread out" [R §3.1] [R 44] [VP 3], the fit returns a flatter table and forecasts accordingly, so no one gains from the excess spread (P4). No rating is ever rescaled: neither channel edits a published rating, and there is no counterpart of the 2024 one-off compression [R §2].

Two dynamics are stated with it (REDTEAM_v0_3, V3-STAT-3), and R1 decides how they are guarded. First, the published update moves ratings towards the table: under a table of slope κ its fixed point is R_i − R_j = (s_i − s_j)/κ, so a flatter table spreads the published ratings further. Second, a slope fitted on noisy published ratings is attenuated, so a yearly refit can ratchet: flatter table, wider spread, flatter table. R1 keeps D2, the table calibrated on published ratings, because property P4 holds only for that fit, and guards against the ratchet in two ways: κ's annual change cap stays (T7), and the monthly spread ratio, the SD of published ratings divided by the SD of Layer 1's estimates for active adults, is a second, published reference for the spread. On history it was 0.794 in standard in January 2023 and 0.747 in September 2026, with a month-to-month SD of change of 0.016; rapid 0.752 and 0.747, blitz 0.810 and 0.749 (`analysis/OUTPUT_L1_history.md`). The measure is the noise-corrected ratio, whose denominator adds the mean posterior variance so that it does not move with activity alone. If its calendar-year mean moves by more than θ_R1 = 0.02 in the same direction two years running, the QC reviews (PROVISIONAL; script §12); nothing is corrected automatically. The threshold lies below the rate a ratchet held to κ's cap would produce, about 0.747 × 0.05 / 1.212 = 0.031 a year in standard, and above every year-on-year change since the March 2024 reset (at most 0.018). The same scale question sits under θ̃, which R2 now defines in spread as well as level: θ̃_i = m_t + (ŝ_{i,tc} − m̂_t)/κ_tc. A correctly rated player whose latent distance from the anchor mean is κ times the published one therefore has θ̃ − R = 0, where v0.3's θ̃ = ŝ − d_t would have shown (κ − 1)(R − m_t): −136, −115 and −94 points at R = 1400, 1500 and 1600 for κ = 1.212 and an anchor mean of 2041.3 (script §10b), which would have under-stated exactly the juniors rung 5 is for. The QC report still shows θ̃ − R by rating band for every eligible junior and every seed, and the targeted residuals of rungs 3 and 5 are broken down by band (T8.1).

---

## T4 Layer 2 rules

Layer 2 is the published rating. Everything in this section is computed from quantities printed on list t and in the parameter file of list t; nothing computed during month t is used before list t+1. Timing, one sentence used everywhere (REDTEAM_v0_3, V3-QC-5): *the parameter file published with list t carries the inputs for rating period t, among them a_t, measured at list t from the games of period t − 1; a_t accrues to the players active in period t and is posted with period t's games.* Each subsection names the rung of the adoption ladder (proposal §9) that introduces it; every rung can be adopted alone, and a rung that is not adopted leaves today's rule in place (for example, without rung 4 every K is today's K).

**T4.1 Inputs frozen for the period.** Only games against rated opponents enter Layer 2, exactly as today: §8.3.1 begins "For each game played against a rated player" [V 1], so a rated player's game against an unrated or sub-floor opponent produces no change for either side and no ledger entry; Layer 1 uses every game. One exception is kept from today at every rung: "If an unrated player receives a published rating before a particular tournament in which they have played is rated, then they are rated as a rated player with their current rating, but in the rating of their opponents they are counted as an unrated player" (§8.2.4 [V 1]). Such a game changes one side only; T6 books it in its own ledger line. For every game of rating period t: R_i and R_j from list t; K_i from list t (one decimal); RX_j = R_j + c_j from list t; the carried adjustment balance B_i from list t (printed, so that a change after an absence is recomputable); the level L (published ratings, without compensation, whole-number part of the mean) and its band; the colour from the tournament report (format NOT VERIFIED; see SPEC-L0 §2.1); η_tc, the table and a_t from the parameter file of list t. "List t" here means the list in force at the start of the game's tournament, as FIDE's published calculations show (SPEC-L0 R-11a [E0]) and as §1.4.6 a) of the Title Regulations states for norms [VT 1]: a tournament that spans two lists uses the earlier one for every input throughout (R, K_i, RX_j, the table and η_tc), and a new table or parameter file applies only to tournaments that start after it.

**T4.2 The game term.**

> x_i = R_i − RX_j + w_i · η_tc if j is an eligible junior (T4.6) and i is not; otherwise x_i = R_i − R_j + w_i · η_tc (R8)
> ΔR_{i,g} = K_i · (S_i − E(x_i; tc, L)), which the proposal writes per game as R_i ← R_i + K_i · (S_i − E(x_i)); the game terms are summed and rounded once per period (T4.4)

K_i has one decimal and E three, so each ΔR_{i,g} is exact with at most four decimals. No rounding occurs here.

**T4.3 K from certainty (rung 4; D3 as revised by R6).**

> K_i = clip(q · σ_i² / (κ_tc · (1 + q² · σ_i² · v_tc)), K_min, K_max), q = ln 10/400, v_tc = 1/(2(2 + ν_0)) in the player's own level band, rounded to one decimal and printed in the list's K column.

σ_i is the Layer 1 posterior SD of i's strength in tc at the list date, in latent units (D-0008, reading 5). The formula is the Kalman gain of one game between equally rated players, carried onto the published scale: in latent units a game at equal strength carries Fisher information q² v_tc about the gap (dE/dz and the score variance at z = 0 both equal v_tc), so a Gaussian posterior with variance σ_i² moves by q σ_i² (S − E)/(1 + q² σ_i² v_tc) latent points, which is κ_tc times a published-scale change; dividing by κ_tc gives K_i (R6). With κ_tc = 1 and no draws (v = ¼) it is v0.3's D3. Values (script §5): at R = 1700, 2300 and 2700, σ_i = 50, 55, 60, 70 and 80 give K_i = 11.7, 14.1, 16.8, 22.7, 29.4 (1700) to 11.8, 14.2, 16.9, 22.9, 29.8 (2700); K_min = 10 binds below σ_i ≈ 46 and K_max = 40 above σ_i ≈ 93–94 (published-scale 38 and 77). The σ values in examples are assumptions, not model outputs. What sets σ_i in practice is activity and the process noise: with a latent process SD of 12 points a month (T7.2, illustrative), the steady state is K ≈ 16.4–22.3 with two standard games a month, 13.4–18.2 with three and 11.6–15.8 with four, at levels 1700–2700, and K_min or close to it with eight; with the 24 points a month fitted on history (c_θ = 2.0 at ages 25–45, T2.3a), K ≈ 31.6–40 with two, 25.8–35.4 with three, 22.2–30.6 with four and 15.5–21.4 with eight (script §10b). Fitted on broadcast games, the model gives established players rated 2600 or more (aged 20 or more, at least 10 standard games) a median K_i of 20.0, from 12.3 to 40.0, at the October 2026 list, against today's 10 (`analysis/OUTPUT_L1_history.md`), and a median of 19.0 over the player-months of the rolling tests [E6]. The broadcast archive holds most of these players' standard games (25,233 player-games at 2600+ against about 59 rated games a year each [E5]), so this is largely what R6 gives with the fitted process noise, not an artefact of the sample; for most players below 2400, whose games the archive covers far less, σ and K_i are too large. In the rung test established adults' monthly changes doubled under K_i (median 7.6 to 16.8 points, p90 25.8 to 55.6) [E6]. R6 applies the gain of one game to every game of a period with σ fixed, which overstates the gain of a period with many games; whether K should fall with the period's games is for the architect. A newcomer starts at K_max = 40, as today's newcomers do [V 1]; a player inactive for years returns with a higher K_i because σ_i has grown (T2.2; 36 idle months take σ from 55 to 90.6 and K from 14.1 to 37.4 at R = 1900). K_i depends on results only through the fitted strength, never on their sign, but it does depend on whom a player meets: games against far weaker opponents carry little information, so a player who plays only them keeps σ_i, and K_i, high (REDTEAM_v0_3, V3-EXPLOIT-5; the farming-region test of T8.4 watches it). There is no switch at 30 games, at 2300, at 2400 or at age 18 [V 1]. On broadcast games rung 4 does not pass its test: forecasts of the next month's games are worse by 0.0024 nats a game for the players whose K changes most, because broadcast-only σ puts most players at K_max [E6].

**T4.4 Per-period cap, adjustment, rounding.** Let n_i be the number of rated games of i in tc on list t.

> If K_i × n_i > 700, K_i is replaced for that period by ⌊7000 / n_i⌋ / 10 (700/n_i truncated to one decimal), for every game of the period.
> Period change = round_FIDE( Σ_g ΔR_{i,g} + A_i ) if i has at least one rated game in tc on list t; otherwise no change, and the month's adjustment accrues to B_i (T4.5).

This restates §8.3.3's rule "K shall be the largest whole number such that K x n does not exceed 700" [V 1] for a one-decimal K. A_i, the posted adjustment balance, is outside the cap and is added once per rated month, however many games were played. The rounding is §8.3.4 [V 1], applied once, to the period total; there is no other rounding anywhere in Layer 2. Example (script §5): K_i = 26.1 and n_i = 40 gives 1044 > 700, so K_i = 17.5 for the period; K_i = 16.5 and n_i = 40 gives 660, no cap. A *rated month* for i in tc is a month in which i has at least one rated game in tc on list t; it is distinct from the activity flag of §7.2.2 [V 1], which is unchanged.

**T4.5 Calibration adjustments (rung 6 global, rung 7 federation; D7, D9, D10).**

> d_t = m̂_t − m_t (latent minus published mean of the anchor cohort, T2.4)
> a_t = clip(γ_a · sign(d_t) · max(0, |d_t| − d_0), −a_cap, +a_cap), rounded to one decimal
> a_{f,t} = clip(γ_a · shrink_f · φ_f(t), −a_cap, +a_cap) with shrink_f = n_f^× / (n_f^× + n_φ) and n_f^× the federation's cross-pool games in the window; SHIPS DISABLED: a_{f,t} = 0 for every f, printed as 0 in every parameter file, until a backtest on FIDE's own game data (T8) shows φ_f stable and predictive out of sample, and then only by Council decision after public comment and consultation with the federation concerned.

*Both signs, soft deadband (D7).* a_t is positive when the pool deflates and negative when it inflates. Within |d_t| ≤ d_0 = 2.0 points nothing is paid, so noise in the anchor estimate does not flip the sign from month to month; beyond it, a_t grows continuously from zero (one point of d_t adds 1/6 of a point), so there is no jump at the deadband edge, and the cap 1.5 bounds it (table in script §9: d_t = 2.5, 5, 7.2 and 12 give +0.1, +0.5, +0.9 and +1.5; d_t = −3 and −8 give −0.2 and −1.0). The loop is a proportional controller with a deadband: with a steady deflationary pressure of 1.3 points a month (illustrative: the research report's −16 a year [R 5] is the active list's median, which falls by composition, while the steady-adult level has not fallen since March 2024 [E5]) a_t rises to +1.3 and the measured gap settles near d_0 + 6 × 1.3 = 9.8 points (9.5 on the one-decimal grid); with an inflationary drift of −1.0 it settles near −8.0 (−7.7 on the grid), with a_t = −1.0 (script §9). The loop is stable because 0 < γ_a < 1, and it can hold the level only while a_cap exceeds the drift, which the monitoring report shows each month. Two consequences are stated, not hidden (REDTEAM_v0_3, V3-STAT-5): the controller keeps a permanent gap of about d_0 + |drift|/γ_a (9.5 points on the grid at a drift of 1.3 a month), which the twelve-month change D_t cannot see; and it needs about a year to reach its steady state, during which the anchor's published mean still falls (by about 8.6 points in the first twelve months of the stylised loop, script §9). Rung 6 is therefore tested on D_t from month 13 of operation, or with the controller started on the stage-1 drift estimate twelve months before the shadow year, together with a level criterion |d_t| ≤ d_0 + |drift|/γ_a + 2 (T8.1). This settles the sign question left open in v0.2 (REDTEAM_v0_1, R-QC-9).

*Accrual and posting (D10, with accrual scaled by activity, R3).* a_t is published with list t, before the games of period t (timing sentence above). It accrues each month to every player listed as active under §7.2.2 [V 1] (a rated game in the last twelve months) in that time control, scaled by the activity factor min(1, g_i ÷ n̄), with g_i the player's rated games on the twelve lists up to and including list t (T1) and n̄ the anchor cohort's mean of the same count (D-0008, reading 3); the factor multiplies a_t before accrual and changes neither a_t nor the deadband nor the cap. The balance B_i is posted to R_i only in a rated month, as part of the period total of T4.4; accrual stops while the player is inactive under §7.2.2, and the balance, positive or negative, is carried, not forfeited, and posted in the first rated month after return. The amount accrued does not depend on the month's games, so knowing a_t in advance is worth nothing; it grows with activity only up to the cohort's mean and never beyond; ratings still change only for players who play; and the posted balance never exceeds 12 · a_cap in magnitude. Two properties are stated plainly. First, the player chooses when the balance lands, by choosing when to play (REDTEAM_v0_3, V3-EXPLOIT-7): the list therefore prints the settled rating R_i + B_i beside R_i, and rating-based selections are recommended to use it. Second, the drift the adjustment offsets is drained per game; with R3 a player with one game a year accrues 0.52 points a year at a steady a_t = +1.3 and n̄ = 30 (illustrative), against 15.6 without the factor, which matches the drift of 0.52 a game (script §10b) (V3-EXPLOIT-2). The published-scale estimate θ̃ is defined in T1 (R2). On broadcast history the controller was replayed at each test month [E6]: the level criterion held in all three time controls, while D_t, the twelve-month change of the fixed panel's published mean, was +2 to +9 points a year, because the panel's members gained, as E5 found for steadily active adults [E5]; the controller follows d_t and paid at most +0.5 a month. Judging rung 6 on D_t assumes a panel of constant strength; whether the rule should be on d_t, or on D_t net of Layer 1's estimate of the panel's change, is for the architect.

*Enabling conditions for a_{f,t}.* Before a_{f,t} may ever be enabled, the following are required in addition to the out-of-sample test (REDTEAM_v0_1, R-EXPLOIT-3): the evidence for φ_f comes from at least 50 distinct players of f with cross-pool games, none contributing more than 5 % of that information; φ_f is a trimmed-mean estimate with a published leave-one-player-out range, and a_{f,t} stays 0 unless the whole range has one sign; players whose published rating is more than 2 s_f from their estimate are excluded from φ_f; the points a_{f,t} may create per federation per year are capped and printed in the ledger; and the selection test (D9) passes: φ_f estimated separately from the federation's junior and adult travellers, and separately from its players' home and away events, must agree within its uncertainty (each pair of estimates within two standard errors of their difference, PROVISIONAL; a field of T7). The test answers the research report's open question whether offsets are artefacts of who travels [R Open questions]: if the juniors who travel differ from the adults who travel, or results at home differ from results abroad, φ_f measures selection, not the pool, and the channel stays off.

*Compensation and the level.* Because junior compensation creates points deterministically (T6, line 3), the monitoring report compares that line per active player with a_cap each month; if it exceeds a_cap the QC lowers c_cap or raises τ within their annual caps (REDTEAM_v0_1, R-STAT-3).

**T4.6 Junior compensation (rung 5; D5, revised by R5 and R8).** j is eligible on list t if (a) the list year minus j's year of birth on the FIDE list is at most 19 (until the end of the calendar year of the 19th birthday, matching the form of §8.3.3's junior rule [V 1]; a player without a year of birth on the list is not eligible), (b) j has at least 10 rated games in that time control within the window, against at least 5 distinct opponents in at least 3 events (PROVISIONAL), and (c) at least half of the posterior precision of s_{j,tc} comes from games in that time control (R5; PROVISIONAL share_min = 0.5): with P_all the precision of s_{j,tc} at the list date, P_tc the precision from the same system without the other time controls' game terms and P_0 with no game terms, (P_tc − P_0)/(P_all − P_0) ≥ 0.5 (SPEC-L1 §4.4). Condition (c) closes the blitz route of REDTEAM_v0_3, V3-EXPLOIT-1: through the shared θ, arranged blitz results could otherwise raise a junior's standard compensation while the donors paid only in blitz. Then

> c_j = min(c_cap, max(0, round_FIDE(θ̃_j − z · σ̃_j − R_j − τ))), z = 1.2816, τ = 25, θ̃_j and σ̃_j from the same-time-control posterior s_{j,tc} on the published scale (R2, R5), RX_j = R_j + c_j, printed in the list;

otherwise c_j = 0 and RX_j = R_j. θ̃_j − z σ̃_j is the lower 10 % quantile of the junior's estimate on the published scale, so a junior is compensated only by the amount the model is 90 % sure of, less the margin τ. There is no posterior-probability switch: c_j is 0 until θ̃_j − R_j exceeds τ + z σ̃_j, then rises one point per point up to c_cap; for σ̃_j = 100 it is positive above a gap of 153.16 and reaches the cap at 453.16, and for σ̃_j = 60 at 101.896 and 401.896 (script §6). The lower quantile also removes the winner's curse of a threshold test (REDTEAM_v0_2, R2-4). c_j enters only the expectation of opponents who are not themselves eligible (R8): a game between two eligible juniors uses published ratings on both sides, so its expectations sum to one and it creates no points (v0.3's rule created 10.4 points a game at c = 100 each and 27.5 at c = 300; script §10b). j's own update uses published ratings like everyone else's. As R_j rises towards θ̃_j, c_j falls continuously to 0. The list flags every eligible junior and prints RX_j for each, c_j = 0 included, because under R8 an eligible junior with c_j = 0 still blocks the opponent's compensation and an arbiter must be able to see it; θ̃_j and σ̃_j go to the QC only (D17), with the disclosure of T2.6. The remaining discrete elements are the eligibility conditions (a) to (c), which act per list and only on opponents' expectations (T5, P3). On broadcast games [E6]: adults scored 0.055 a game below expectation against eligible juniors under today's rules and 0.018 with compensation (56,030 games), and forecasts improved by 0.016 nats a game. Against a matched control, adult pairs in the same months at the same published gap and colour, the junior-specific residual falls from −0.047 to −0.010, inside ±0.01, so table 8.1.2's own error explains little of the drain, and on rung 2's table the result is the same (−0.011). By band it fails in both directions: adults below 2000 still lose (−0.035 to −0.051), and adults rated 2400 or more score above the compensated expectation, +0.026 a game in the games where c_j > 0 on table 8.1.2 and +0.034 on rung 2's table, the compensation hunter's yield (T9.4). The ±0.01 rule of T8.1 is not met; a margin τ that varies with the opponent's level is a question for the architect. The mechanism is the one Chess Scotland applies as "junior additions" by age, which IM Douglas Bryson put to FIDE in the 2023 consultation [VP 4]; here the addition comes from the junior's own evidence.

**T4.7 Seeds, inactivity, floor (rung 3; D4).** A player new to the list in tc receives a first published rating once they have at least N_seed = 5 games against rated opponents within 26 consecutive months (§7.1.4 [V 1], unchanged), and only if round_FIDE(θ̃_i) ≥ R_floor, which keeps §7.1.4's "The rating must be at least 1400" as a publication condition: R_i(t_0) = min(round_FIDE(θ̃_i), R_seedmax), with θ̃_i the Layer 1 posterior mean on the published scale (R2), drawing on the player's games in all three time controls and on a prior that depends on age only (T2.2, D4), and K_i from σ_i (near K_max). A seed is never raised to the floor: v0.3 as reviewed clipped it to 1400, which created up to 150 points for a player estimated at 1250 and differed from the re-entry rule (REDTEAM_v0_3, V3-EXPLOIT-4). The seed's σ̃_i goes with it to the QC, and no seed is published while σ̃_i exceeds σ_seed,max (PROVISIONAL 120): the player stays unrated and keeps accumulating games. The same rule applies to a player re-qualifying after a floor exit: re-published only if round_FIDE(θ̃_i) ≥ R_floor; otherwise they remain unrated while Layer 1 keeps estimating, so the floor no longer manufactures points at the bottom (REDTEAM_v0_2, R2-8; script §10 tests a newcomer and a re-entry on each side of the floor). §8.2.1 [V 1] (a zero score in the first event is disregarded) is kept for the five-game threshold; the Layer 1 estimate uses every game. The two hypothetical draws against 1800 of §8.2.2 [V 1] are not used. The 2200 maximum of §8.2.3 is kept, and the five qualifying games must involve at least three distinct opponents in at least two events (both PROVISIONAL; REDTEAM_v0_1, R-EXPLOIT-5); with the σ̃ condition these are changes to §7.1.4, which lets the five games come from one tournament [V 1] (T11). The σ̃ condition is itself a games requirement in practice: from the prior s_0 = 250, five games against equal opposition in one month leave σ̃ at about 122–126 and six at 114–119, so most newcomers need six to eight games before a seed is published (script §10b). At least half of the seed's posterior precision must come from games in that time control (PROVISIONAL: R5's condition applied to seeds, an executor's addition after REDTEAM_v0_4, V4-EXPLOIT-3, for the architect to confirm): through the shared θ, arranged rated blitz wins would otherwise raise a standard seed, as they could compensation before R5. Rapid and blitz keep §7.2.1 of their chapter [V 2]: an unrated player who has a standard rating is rated from their first rapid or blitz game, as today; under rung 3 the starting value is the Layer 1 estimate in that time control, which already uses their standard games, instead of the standard rating itself. On broadcast games (E6) the seeds of 659 newcomers were closer to their first 30 games' results on average than FIDE's first ratings (residual −0.010 against −0.020) but worse in log-loss by 0.050 a game, because they rest on broadcast games alone while FIDE's first rating uses every rated game; rung 3 does not pass there and is retested on FIDE's data [E6].

Inactivity: no published rating decays. While i has no rated month, R_i is unchanged, nothing is posted, and σ_i grows through the random walk (T2.2) so that K_i is higher on return (T4.3). The activity flag of §7.2.2 [V 1] is unchanged.

Floor: §7.2.1 [V 1] is unchanged as a display rule: a player whose rating drops below 1400 is shown as unrated on the next list and their games are then not rated for opponents, as today. Layer 1 keeps estimating the player from those games, and when the player re-qualifies under §7.1.4 the seed is the Layer 1 estimate, not two phantom draws. The ledger (T6) records the rating that left through the floor.

**T4.8 Channel table.** Every channel with its formula, cap and activation threshold.

| Channel (rung) | Enters through | Formula | Cap | Activation |
|---|---|---|---|---|
| Expected score (2) | E in every game term | T3.1 with κ_tc, η_tc, α_tc, β_tc, γ_tc fitted on published ratings (T3.3) | none (no clamp) | always on once adopted; parameters change yearly within T7 caps |
| Seed (3) | first published rating | min(round_FIDE(θ̃_i), R_seedmax), published only if round_FIDE(θ̃_i) ≥ R_floor | R_seedmax | N_seed games against at least 3 distinct opponents in at least 2 events within 26 months; σ̃_i ≤ σ_seed,max; information share ≥ 0.5 |
| K from certainty (4) | K_i | clip(q σ_i² / (κ_tc (1 + q² σ_i² v_tc)), K_min, K_max) (R6) | K_min ≤ K_i ≤ K_max; period cap 700 | always on once adopted |
| Junior compensation (5) | the x of opponents who are not eligible (R8) | min(c_cap, max(0, round_FIDE(θ̃_j − z σ̃_j − R_j − τ))), same-time-control posterior (R5) | c_cap | age rule (list year − birth year ≤ 19); at least 10 rated games in tc against at least 5 opponents in at least 3 events; information share ≥ 0.5 (R5) |
| Global adjustment (6) | once per rated month, from the accrued balance | clip(γ_a sign(d_t) max(0, \|d_t\| − d_0), ±a_cap), accrued × min(1, n_i/n̄) (R3) | a_cap per month | anchor panel of at least N_anchor players (PROVISIONAL 2,000) |
| Federation adjustment (7) | once per rated month | T4.5 | a_cap per month | DISABLED; later: s_f < s_max, effective resistance < R_max, selection test, Council decision |
| Ledger | publication only | T6 | — | always |

**T4.9 The published per-game breakdown.** Every published change comes with one line per rated game and one line per period (REDTEAM_v0_1, R-QC-2). Per game: event and round; opponent's FIDE ID and eligibility flag; colour w_i; R_i, R_j, c_j and RX_j from list t; x_i; L and its band; E from the table; S_i; K_i for the period (after the cap of T4.4); ΔR_{i,g} to four decimals. A game rated for one side only under §8.2.4 [V 1] is marked as such. Per period: n_i; Σ_g ΔR_{i,g}; the posted balance A_i and the remaining balance B_i; the unrounded total; the rounded change; the new rating and the new settled rating R_i + B_i. Every field is either printed in list t, in the parameter file or the table of list t, or in the tournament report, so the line can be recomputed by hand.

---

## T5 Properties with proof sketches

**P1 Forward-only.** R_i(t+1) is a function of R_i(t), the games of period t and quantities printed on list t and its parameter file (T4.1). Layer 1 writes nothing into any R. No published list is ever recomputed. Proof: the only operation on a published rating is the period update of T4.4; its inputs are frozen at list t; a published list is a constant thereafter. (The 2024 one-off compression [R §2] has no counterpart here: no rating is rescaled, T3.5.)

**P2 Bounded change.** Per game |ΔR_{i,g}| ≤ K_i |S_i − E| ≤ K_i ≤ K_max = 40. Per period |Σ_g ΔR_{i,g}| ≤ K_i n_i ≤ 700 after the cap of T4.4, and the posted balance is at most 12 · a_cap (T4.5), so |period change| ≤ round_FIDE(700 + 12 · a_cap) = 718 (PROVISIONAL a_cap = 1.5; 702 in a month without carried balance; the same again for a_{f,t} if it is ever enabled; script §9). Today's bound is 700 [V 1].

**P3 Continuity.** E is continuous and strictly increasing in x for every γ ≥ 0 (T3.2); K_i is continuous in σ_i (a clipped rational function, T4.3); c_j is continuous in θ̃_j and σ̃_j (a clipped linear function, T4.6, D5); the accrual factor min(1, n_i/n̄) is continuous in n̄ and piecewise linear in the count n_i (R3); a_t is continuous in d_t, the deadband being soft (T4.5, D7); the period cap is continuous in n_i (a clipped hyperbola). There is no 400- or 600-point rule, no 2650 exemption, no switch at 30 games, at 2300, at 2400 or at age 18 [V 1] [V 2]. The discrete elements that remain are stated: (i) the published table steps at level-band edges by at most 0.0115 in E (0.012 in the three-decimal table, 0.23 points at K = 20; script §3.1); (ii) the publication grids (whole-number R, RX and c_j; one-decimal K_i and a_t); (iii) the eligibility conditions of compensation (the calendar-year age rule, the counts of games, opponents and events, and the information share of R5), at which c_j can drop to 0 between two lists; (iv) the activity boundary of §7.2.2 for accrual, which stops accrual but forfeits nothing; (v) the posting time of the carried balance, which the player chooses by choosing when to play. None can be straddled for gain within a period: (i) is symmetric for both players; (iii) acts per list, on opponents' expectations only, by at most c_cap, and is controlled by the calendar and by counts, not by a result a player can choose; (iv) carries the balance; (v) moves at most 12 · a_cap between lists and is visible in the settled rating R_i + B_i (T4.5).

**P4 Unbiasedness.** If the table's probabilities are the true probabilities of the results given the published gap, level and colour, then E[ΔR_{i,g}] = K_i (P_W · 1 + P_D · ½ + P_L · 0 − E) = K_i (E − E) = 0 for every game: given the published gap, level and colour, a player cannot gain in expectation by choosing weak opponents (farming), strong ones or a particular colour; the only way to gain is to score more than the calibrated expectation. The table is fitted on published ratings so that this holds for what players choose on, and its calibration is tested out of sample (T3.3, T8); a residual m(x, L) = E_true − E gives an expected gain K_i m per game, which today's cap converts into a systematic +0.4 points a game for a 2600 against a 2100 if the uncapped table is right (script §8). P4 does not cover choosing opponents on other information that predicts results, such as federation while rung 7 is disabled (T3.3). K_i is a function of σ_i, which depends on the information in the games played (how many, against whom) and on results only through the fitted strength, never on their sign; but games against far weaker opponents, and losses that widen the fitted gaps, keep σ_i, and therefore K_i, higher, which the farming-region calibration test and the farming index of T8 watch (REDTEAM_v0_3, V3-EXPLOIT-5). Pooled as R12 orders, the broadcast games at gaps of 400 or more and levels of 2300 or more show the fitted table under-predicting the favourite by +0.032 in standard and +0.045 in blitz (827 and 1,019 games), outside ±0.01 also with the month-block bootstrap of T8.5 and with player-clustered intervals, while table 8.1.2 with its cap is within ±0.01 there [E6]. If FIDE's games confirm it, rung 2 would give a strong player about 0.3 points a game at K = 10, 0.6 at the K of about 19 that rung 4 gives established 2600+ players in standard and about 1.1 in blitz at K ≈ 25, for farming much weaker opponents. Rung 2 is therefore not recommended in that region until FIDE's data pass it; whether rapid and blitz keep their 600-point exclusion meanwhile is for the architect.

**P5 Ledger completeness.** Every point that enters, leaves or is created in a time control's list in a month appears in exactly one line of the ledger, and the lines sum to the change in the list total. Proof: T6 is an algebraic identity in which every term is one of the published lines; it is checked exactly on a synthetic month in script §10, now with a one-sided game under §8.2.4, a floor exit, a newcomer and a re-entry, and a newcomer and a re-entry refused below the floor.

**P6 Determinism.** All Layer 2 quantities live on fixed decimal grids (T1) with a single rounding step (T4.4); the table is a published file; the same list, parameter file and tournament reports give the same output on any machine, as SPEC-L0 §5 requires of Layer 0. Layer 1 and the calibration fit are iterative computations in floating point, so bitwise identity across machines is not promised for them; what is promised is reproducibility at a published tolerance (|Δŝ| ≤ 0.1 and |ΔK_i| ≤ 0.1 between two conforming runs) given the same input ordering (games sorted by date, event and FIDE ids), a fixed sweep order, a fixed iteration cap, a fixed random seed where any stochastic step exists, and the published convergence tolerances; the parameter file, the table and the list, once signed, are canonical, and the file carries the hash of its inputs (T7) so that any party can rerun it and compare.

---

## T6 The ledger identity

For a game g between i and j in time control tc, with E_i⁰ = E(R_i − R_j + w_i η_tc) the expectation without compensation (so that E_j⁰ = 1 − E_i⁰ by symmetry), E_i, E_j the expectations actually used (T4.2), and K_i, K_j the period K after the cap:

> Transfer from j to i: T_g = ½ (K_i + K_j) · (S_i − E_i⁰)
> Created by unequal K: C_g^K = (K_i − K_j) · (S_i − E_i⁰), half credited to each player
> Created by compensation: C_g^c = K_i (E_i⁰ − E_i) + K_j (E_j⁰ − E_j)

Then ΔR_{i,g} = T_g + ½ C_g^K + K_i (E_i⁰ − E_i) and ΔR_{j,g} = −T_g + ½ C_g^K + K_j (E_j⁰ − E_j), so ΔR_{i,g} + ΔR_{j,g} = C_g^K + C_g^c: transfers cancel and only the two creation terms remain. With A_i the adjustment balance posted to i in month t if i has a rated month and 0 otherwise, and the rounding residual ρ_i = round_FIDE(Σ_g ΔR_{i,g} + A_i) − (Σ_g ΔR_{i,g} + A_i), the monthly identity per time control is

> Σ_{i ∈ list t+1} R_i(t+1) − Σ_{i ∈ list t} R_i(t) = Σ_g C_g^K + Σ_g C_g^c + Σ_i A_i + Σ_i ρ_i + Σ_{entries} R_i(t_0) − Σ_{exits} R_i⁺(t),

where the sums over g, A_i and ρ_i run over every player on list t who played, including those who then leave; entries are newcomers and re-entries after a floor exit (T4.7); and R_i⁺(t) = R_i(t) + (period change of i) is the rating that actually leaves with an exiting player (post-update; REDTEAM_v0_2, R2-1). Games against unrated players produce no change for anyone (T4.1). The one exception is §8.2.4 [V 1]: a game in which a newly rated player is rated against opponents who count that player as unrated changes one side only, by O_g = K_i (S_i − E_i); Σ_g O_g is added to the right-hand side as its own line (REDTEAM_v0_3, V3-STAT-2). Administrative changes to the list (a re-rated or annulled event, merged IDs, removals other than through the floor) are itemised in a further line.

The published ledger lines are: (1) gross points moved between players by results, Σ_g |T_g| (a volume line; it nets to zero); (2) net points created or destroyed by unequal K, Σ_g C_g^K; (3) points created by junior compensation, Σ_g C_g^c; (4) points posted from the global adjustment, Σ_i A_i (global part), with the outstanding accrued balance Σ_i B_i shown as a memo liability; (5) points posted from federation adjustments, Σ_i A_i (federation part; 0 while disabled); (6) rounding residual, Σ_i ρ_i, bounded by 0.5 per player with a rated month; (7) points entering with newcomers and re-entries, Σ R_i(t_0); (8) points leaving with players removed from the list (below 1400, §7.2.1 [V 1]), at their post-update rating R_i⁺(t); (2b) one-sided changes under §8.2.4, Σ_g O_g; (11) administrative corrections, itemised; (9) the change in the list total, which must equal (2) + (2b) + (3) + (4) + (5) + (6) + (7) − (8) + (11) exactly; and a memo line (10), the ratings held by players who became inactive this month under §7.2.2, which does not enter the identity because inactive players stay on the list. A residual that no line explains holds the list until it is itemised; an itemised administrative line does not. Lines (2) and (3) are also published per event, without flags, so that an event or a club in which unequal-K or compensation creation is concentrated is visible; the QC receives a flag for every event whose creation exceeds what its mix of K factors and its pairings predict, and a pair-level monitor of the cumulative line-2 creation of every pair of players over twelve months, across events (REDTEAM_v0_1, R-EXPLOIT-1, R-EXPLOIT-2; REDTEAM_v0_3, V3-QC-7, V3-EXPLOIT-6). There is no per-game cap on the ratio of the two K factors (D11): such a cap would slow exactly the players the design wants to move quickly, juniors with K near 40 meeting established adults near 17, and the collusion it would target, which v0.3 makes possible between more players (a very active player near K_min and a returner near K_max), is visible in line (2) per event and in the pair-level monitor.

The script's synthetic month (script §10: eight listed players, nine rated games, one compensated junior with RX = 1697, one game against an unrated player, one game rated for the newly rated player only under §8.2.4, one floor exit, one newcomer seeded at 1650, one former floor exit re-published at 1452, and a newcomer at θ̃ = 1287.6 and a former floor exit at 1381.2 left unrated, a_t = +0.9) gives +1785 = +39.8134 + 17.5852 + 16.2581 + 7.2 + 0.1433 + 3102 − 1398 exactly; without line (2b) the residual would be 16.2581, booking the exit at R_i(t) = 1405 instead of R_i⁺(t) = 1398 would leave 7 points, and the game against the unrated player and the two refused entries appear in no line. Under R8 no game between two eligible juniors creates points, so line (3) has no junior–junior sub-line. The removal in April 2026 of most of the batch first listed in March 2026 (D-0008, R11) would be booked in line (11).

In plain language, for the proposal: the ledger is the system's audited monthly accounts, the way a central bank publishes how much money it created and why; nothing is created silently.

---

## T7 Monthly parameter file

One YAML file per time control per list. Layer 1 and the calibration fit write it, the QC signs it, Layer 2 reads nothing else; every published change is recomputable from the game record, the previous list and this file (P6, T5). The file published with list t has two parts (REDTEAM_v0_3, V3-QC-5): the inputs for rating period t (table parameters, K bounds, a_t, gates, compensations) and the results of period t − 1 (ledger totals, fit diagnostics), which the QC approves after period t − 1 has been rated.

### T7.1 Schema

"Measured" fields are outputs of the month's fit, reported, uncapped. "Fixed" fields change only by Council decision (T11 stage 4). Caps are per calendar year, PROVISIONAL.

```yaml
schema_version:        string   # "pf-0.4"; fixed, changes only with a new annex version
list_date:             date     # YYYY-MM-01; the list this file governs
time_control:          enum     # standard | rapid | blitz; one file per tc

expected_score:                 # rung 2, published also as the yearly lookup table (T3); fitted on published ratings (T3.3)
  kappa:  {value: float, unit: dimensionless, cap_per_year: 0.05}    # κ_tc
  eta:    {value: int,   unit: rating points, cap_per_year: 5}       # η_tc, colour term, whole points so that x stays on the whole-number grid
  alpha:  {value: float, unit: log-odds,      cap_per_year: 0.20}    # α_tc, draw intercept
  beta:   {value: float, unit: log-odds per 400 points, cap_per_year: 0.10}  # β_tc
  gamma:  {value: float, unit: dimensionless, range: "[0, inf)", cap_per_year: 0.10}  # γ_tc, draw decay (D1); no upper bound (R7)
  band_width: {value: int, unit: rating points, cap_per_year: fixed} # level bands of the table (D6)
  fit:
    method:        string     # "maximum likelihood on published ratings, colours and results (T3.3)"
    window:        string     # first and last month of the games fitted
    n_games:       int        # measured
    excluded:      string     # e.g. "games involving eligible juniors (rung 5 in force)"
    calibration_oos: list     # measured: mean residual per 50-point gap bin and the across-bin slope, held-out months (T8)
    mean_residual_white: float  # measured: Σ(S − E)/G from White's side, in sample
    gamma_at_boundary: bool     # measured: γ fitted at 0 (then only four moment conditions hold); a calibration flag for the QC (R7)
    kappa_attenuation_corrected: float  # measured: κ corrected for rating noise (T3.5), reported beside the ML κ
    sd_ratio_published_to_latent: {anchor: float, pool: float}  # measured monthly (T3.5); the spread ratio of R1
    spread_ratio_review: {threshold: 0.02, rule: "calendar-year mean of the noise-corrected ratio, same direction, two years running", cap_per_year: fixed}  # R1: a QC review, never an automatic correction

development_coefficient:        # rung 4
  q:        {value: "ln(10)/400", cap_per_year: fixed}
  K_min:    {value: float, unit: points per unit score, cap_per_year: 2}
  K_max:    {value: float, unit: points per unit score, cap_per_year: 2}
  C_period: {value: int,   unit: points × games, cap_per_year: fixed} # 700, FIDE's K × n rule restated [V 1]
  rule:     string     # "K_i = clip(q sigma_i^2 / (kappa_tc (1 + q^2 sigma_i^2 v_tc)), K_min, K_max); v_tc = 1/(2(2 + nu0)) in the player's band" (R6)

global_adjustment:              # rung 6
  a_t:      {value: float, unit: points accrued per active player this month, posted in the current month if rated, otherwise carried (T4.5)}  # one decimal
  a_cap:    {value: float, unit: points per month, cap_per_year: 0.5}
  gamma_a:  {value: float, unit: per month, cap_per_year: 0.0833}    # γ_a
  d_0:      {value: float, unit: rating points, cap_per_year: 0.5}   # soft deadband (D7)
  level_criterion: string     # |d_t| <= d_0 + |drift|/gamma_a + 2 (T8.1)
  accrual_factor: {rule: "min(1, n_i / n_bar)", n_bar: float}   # R3; n_bar measured: the anchor cohort's mean rated games on the 12 lists up to t
  anchor_cohort:
    definition:  string       # fixed text (T2.4); re-based each 1 January, chain-linked
    N_anchor:    int          # minimum panel size for the channel to act (PROVISIONAL 2,000)
    rebased_on:  date
    n_members:   int          # measured
    m_t:         float        # measured, published mean of the cohort, points
    m_hat_t:     float        # measured, L1 latent mean, points
    d_t:         float        # measured, m̂_t − m_t, points

federation_adjustment:          # rung 7; SHIPS DISABLED
  enabled:    bool            # false until the FIDE-data backtest passes (T8); change = Council decision
  threshold:  string          # published evidence rule (the 50-player and 5 % conditions of T4.5)
  s_max:      {value: float, unit: rating points, cap_per_year: fixed}
  R_max:      {value: float, unit: dimensionless, cap_per_year: fixed}
  n_phi:      {value: int,   unit: cross-pool games, cap_per_year: fixed}
  selection_tolerance_se: {value: float, unit: standard errors, cap_per_year: fixed}   # D9 test, PROVISIONAL 2
  federations_public_aggregate: {share_cross_federation_games_by_band: list}   # the only federation information in the PUBLIC file while enabled = false
  federations_qc_annex_sha256: string   # hash of the QC-only annex below
  federations:                # QC-ONLY annex while enabled = false; one entry per federation with ≥ 1 cross-pool game in the window
    - fed:                string   # three-letter FIDE federation code
      phi_f:              float    # φ_f, measured, points
      s_f:                float    # posterior SD of φ_f, measured, points
      phi_f_junior_adult: [float, float]  # selection test (D9), measured
      phi_f_home_away:    [float, float]  # selection test (D9), measured
      component_id:       int      # connected component of the game graph containing f
      eff_resistance:     float    # effective resistance between f and the anchor pool, dimensionless
      passes_threshold:   bool
      a_f_t:              float    # a_{f,t}; always 0.0 while enabled = false

junior_compensation:            # rung 5
  tau:    {value: float, unit: rating points, cap_per_year: 10}      # τ
  c_cap:  {value: float, unit: rating points, cap_per_year: 50}
  z:      {value: 1.2816, cap_per_year: fixed}                       # 0.90 quantile of the standard normal
  gates:  {age_limit: 19, min_games: 10, min_opponents: 5, min_events: 3, min_info_share: 0.5, cap_per_year: fixed}   # T4.6 (a)-(c); R5
  eligible:                     # every eligible junior this month, c_j = 0 included (R8 needs the flag); PUBLIC copy carries only these three fields
    - fide_id:    int
      R_j:        int           # published rating used
      c_j:        int           # min(c_cap, max(0, round_FIDE(θ̃_j − z σ̃_j − R_j − τ))); RX_j = R_j + c_j is the list column
  eligible_qc_annex_sha256: string  # hash of the QC-only annex holding, per eligible junior, θ̃_j, σ̃_j and the information share (D17: QC only)

seeds_inactivity_floor:         # rung 3
  R_floor:   {value: int, unit: rating points, cap_per_year: fixed}  # display rule only
  R_seedmax: {value: int, unit: rating points, cap_per_year: fixed}  # today's §8.2.3 maximum, kept [V 1] [V 2]
  N_seed:    {value: int, unit: games,         cap_per_year: fixed}  # today's §7.1.4, kept [V 1]
  sigma_seed_max: {value: float, unit: rating points, cap_per_year: 15}   # on σ̃, the published scale
  seed_min_info_share: {value: 0.5, cap_per_year: fixed}   # PROVISIONAL (T4.7)
  seed_gates: {min_opponents: 3, min_events: 2, cap_per_year: fixed}   # T4.7

layer1_hyperparameters:         # L1 specification; chosen by rolling out-of-sample log-loss
  window_months:  {value: int, cap_per_year: fixed}                  # 36
  method:         enum          # map_laplace (WHR style) | ep (TrueSkill Through Time style); fixed
  outcome_latent: {eta: float, alpha: float, beta: float, gamma: float}   # η^L, α^L, β^L, γ^L; measured
  s_0:    {value: float, unit: rating points, cap_per_year: 25}          # prior SD of a new player's θ (T2.2), PROVISIONAL 250
  prior_mu0_by_age:             # μ_0(age), points; age only (D4)
    - {age_band: string, mu0: float}
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
    cov_theta_delta:     float  # Cov(θ, δ_tc) over players with games in tc
    cross_tc_correlation: float # correlation of ŝ across time controls

ledger_totals:                  # points to four decimals, the month's totals; lines (1)–(10) of T6
  moved_by_results_gross:  float   # (1) Σ_g |T_g|, gross volume; nets to zero
  created_by_unequal_K:    float   # (2) Σ_g (K_i − K_j)(S_i − E_i⁰)
  junior_compensation:     float   # (3) Σ_g C_g^c; no junior–junior games carry compensation (R8)
  one_sided_8_2_4:         float   # (2b) Σ_g O_g, games rated for one side only under §8.2.4 [V 1]
  global_adjustment_posted: float  # (4) Σ_i A_i, global part
  federation_adjustment_posted: float # (5) 0.0 while disabled
  rounding_residual:       float   # (6) Σ_i ρ_i; bounded by 0.5 × players with a rated month
  entering:                float   # (7) Σ of first published ratings of newcomers and re-entries
  leaving_below_floor:     float   # (8) Σ of post-update ratings of players removed under §7.2.1; a positive magnitude, subtracted in (9)
  administrative:          float   # (11) itemised corrections (re-rated or annulled events, merged IDs, removals other than the floor)
  change_in_list_total:    float   # (9) must equal (2)+(2b)+(3)+(4)+(5)+(6)+(7)−(8)+(11) exactly
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

PROVISIONAL / ILLUSTRATIVE: parameter values from T1, the expected-score block from the broadcast fit (`params/table_fit_2026-10.yaml`, [E2]); every other measured quantity is invented to show the format, except a_t, which is computed from the invented d_t by the rule of T4.5 (script §9).

```yaml
schema_version: "pf-0.4"
list_date: 2027-02-01
time_control: standard
status: "PROVISIONAL / ILLUSTRATIVE"

expected_score:                 # PROVISIONAL-FITTED (E2): the broadcast fit, standard
  kappa:  {value: 1.2120, cap_per_year: 0.05}
  eta:    {value: 36,     cap_per_year: 5}      # fitted 35.91, whole points for the table
  alpha:  {value: 0.2860, cap_per_year: 0.20}
  beta:   {value: 0.4985, cap_per_year: 0.10}
  gamma:  {value: 0.2915, range: "[0, inf)", cap_per_year: 0.10}
  band_width: {value: 100, cap_per_year: fixed}
  fit:
    method: "maximum likelihood on published ratings, colours and results (T3.3); docs/specs/SPEC-TABLE-FIT_v1_0.md"
    window: "2023-10 to 2026-09"           # Lichess broadcast archive (CC BY-SA 4.0); FIDE's TRF archive later
    n_games: 339485
    excluded: "none (rung 5 not in force)"
    mean_residual_white: 0.0004            # illustrative
    gamma_at_boundary: false
    kappa_attenuation_corrected: 1.03      # illustrative
    sd_ratio_published_to_latent: {anchor: 0.75, pool: 0.75}   # illustrative; 0.747 measured for active adults, standard, September 2026
    spread_ratio_review: {threshold: 0.02, rule: "calendar-year mean of the noise-corrected ratio, same direction, two years running"}

development_coefficient:
  q:         {value: "ln(10)/400", cap_per_year: fixed}
  K_min:     {value: 10.0, cap_per_year: 2}
  K_max:     {value: 40.0, cap_per_year: 2}
  C_period:  {value: 700,  cap_per_year: fixed}

global_adjustment:
  a_t: 0.8                      # = clip((1/6) x (6.6 - 2.0), ±1.5), one decimal (script §9)
  a_cap: 1.5
  gamma_a: 0.1667               # 1/6
  d_0: 2.0
  level_criterion: "|d_t| <= d_0 + |drift|/gamma_a + 2"
  accrual_factor: {rule: "min(1, g_i / n_bar)", n_bar: 30.0}   # illustrative n_bar
  anchor_cohort:
    definition: "Players aged 25-45 by birth year on the re-basing date with at least 10 rated standard games in each of the three preceding calendar years and a published rating throughout; fixed panel, re-based each 1 January, chain-linked."
    rebased_on: 2027-01-01
    n_members: 38412            # illustrative
    m_t: 2041.3                 # illustrative
    m_hat_t: 2047.9             # illustrative
    d_t: 6.6

federation_adjustment:
  enabled: false
  threshold: "PROVISIONAL: |phi_f| / s_f >= 3 and eff_resistance <= 0.05 and >= 1000 cross-pool games in the window, the 50-player and 5 % conditions, and the selection test (junior v adult travellers, home v away events agree within two standard errors); enabled only by Council decision after the FIDE-data backtest (T8)."
  federations_public_aggregate: {share_cross_federation_games_by_band: [0.31, 0.24, 0.19, 0.15, 0.22, 0.38]}   # illustrative
  federations_qc_annex_sha256: "0000…0000"   # placeholder; the per-federation block is in the QC-only annex while enabled = false
  s_max: {value: 30, cap_per_year: fixed}                # illustrative
  R_max: {value: 0.05, cap_per_year: fixed}              # illustrative
  n_phi: {value: 2000, cap_per_year: fixed}
  selection_tolerance_se: {value: 2, cap_per_year: fixed}

junior_compensation:
  tau:   {value: 25,     cap_per_year: 10}
  c_cap: {value: 300,    cap_per_year: 50}
  z:     {value: 1.2816, cap_per_year: fixed}
  gates: {age_limit: 19, min_games: 10, min_opponents: 5, min_events: 3, min_info_share: 0.5, cap_per_year: fixed}
  eligible:                     # illustrative identities and values; public copy
    - {fide_id: 900000001, R_j: 1812, c_j: 119}
    - {fide_id: 900000002, R_j: 2105, c_j: 94}
  eligible_qc_annex_sha256: "0000…0000"   # placeholder

seeds_inactivity_floor:
  R_floor:   {value: 1400, cap_per_year: fixed}
  R_seedmax: {value: 2200, cap_per_year: fixed}
  N_seed:    {value: 5,    cap_per_year: fixed}
  sigma_seed_max: {value: 120, cap_per_year: 15}
  seed_gates: {min_opponents: 3, min_events: 2, cap_per_year: fixed}

layer1_hyperparameters:
  window_months: {value: 36, cap_per_year: fixed}
  method: map_laplace
  outcome_latent: {eta: 33.0, alpha: -0.42, beta: 0.51, gamma: 0.47}   # illustrative
  s_0: {value: 250, cap_per_year: 25}
  prior_mu0_by_age:             # illustrative; age only (D4)
    - {age_band: "<12",   mu0: 1450}
    - {age_band: "12-15", mu0: 1520}
    - {age_band: "16-19", mu0: 1580}
    - {age_band: "20-24", mu0: 1600}
    - {age_band: "25-45", mu0: 1560}
    - {age_band: "46-60", mu0: 1540}
    - {age_band: ">60",   mu0: 1520}
  drift_mu_by_age:              # points per month at θ = 2000, illustrative
    - {age_band: "<12",   mu: 7.5}
    - {age_band: "12-15", mu: 5.0}
    - {age_band: "16-19", mu: 2.5}
    - {age_band: "20-24", mu: 0.8}
    - {age_band: "25-45", mu: 0.0}
    - {age_band: "46-60", mu: -0.3}
    - {age_band: ">60",   mu: -0.8}
  sigma_theta_by_age:           # points per month, illustrative
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
    cov_theta_delta: -12.4      # illustrative
    cross_tc_correlation: 0.86  # illustrative

ledger_totals:                  # points, illustrative
  moved_by_results_gross: 2418766.3
  created_by_unequal_K: -1843.3
  junior_compensation: 2194.4
  one_sided_8_2_4: 1203.6
  global_adjustment_posted: 198176.0   # Σ of the balances posted this month
  federation_adjustment_posted: 0.0
  rounding_residual: 31.2
  entering: 6121035.0
  leaving_below_floor: 172260.0        # magnitude; subtracted in the identity
  administrative: 0.0
  change_in_list_total: 6148536.9      # = −1843.3 + 1203.6 + 2194.4 + 198176.0 + 0.0 + 31.2 + 6121035.0 − 172260.0 + 0.0
  memo_newly_inactive: 4018812.0
  memo_accrued_balance: 61204.1

signatures:
  engine_git_commit: "0000000000000000000000000000000000000000"   # placeholder
  input_games_sha256: "0000…0000"                                 # placeholder
  previous_file_sha256: "0000…0000"                               # placeholder
  approved_by: "FIDE Qualification Commission (two signatories)"
  approved_on: 2027-01-29
```

---

## T8 Evaluation pre-registration

Rewritten for v0.3 under the operator's decision D12, with the statistical decision rules of the v0.3 review (REDTEAM_v0_3, V3-STAT-1, V3-STAT-10). One baseline, one question per rung, a do-no-harm check for every rung, and decision rules that a correct rung passes with high probability at the stated sample sizes.

### T8.1 Baseline and rungs

The only baseline is Layer 0: today's FIDE rules exactly, as specified in SPEC-L0 (table 8.1.2, the 400-point rule with the 2650 exemption in standard and the plain cap and 600-point exclusion in rapid and blitz, K 40/20/10, K x n ≤ 700, two 1800 draws, 2200 maximum, 1400 floor) [V 1] [V 2]. Glicko-2, TrueSkill Through Time, Whole-History Rating and Elo++ are not baselines; they are cited as prior art and as sources of method [R §4] [R 10] [R 11] [R 60] [R 61] [R 64]. Each rung of the adoption ladder (proposal §9) is tested against Layer 0 on the problem it targets, with everything else held at Layer 0.

| Rung | What changes | Problem targeted | Targeted metric and PROVISIONAL decision rule | Data that tests it now | Data that settles it |
|---|---|---|---|---|---|
| 1 Open replica | nothing in the rules: Layer 0 reproduces today's list | trust and reproducibility | 100 % of fixtures reproduced exactly, and every disagreement with a published list explained by a documented FIDE-side correction | FIDE's published per-player calculations and tournament reports (FIDE's online calculator is out of date: SPEC-L0 §6.1); monthly lists [V 3]; met for every fixture and for the 2025 U.S. Championship [E0] | — |
| 2 Re-fitted table with colour and draws | E from the fitted table (T3) instead of table 8.1.2; same K | expectancy miscalibration (target 4); colour fairness | the calibration rule of T8.2, in all gap bins and separately in the farming region (gap ≥ 400, level ≥ 2300); three-outcome log-loss better than Layer 0 with the interval of T8.5 excluding zero | Lichess broadcast archive of over-the-board games between FIDE-rated players [V 4]: passed in standard, rapid and blitz [E2]; the farming region not testable at the pre-registered bin size, and pooled (R12) the fitted table under-predicts the favourite in standard (+0.032) and blitz (+0.045) [E6] | FIDE TRF archive |
| 3 Newcomer seeds | first rating from Layer 1 (T4.7) instead of two 1800 draws | deflation through newcomers (target 1) | newcomers' mean residual over their first 30 rated games not significantly outside ±0.02, closer to zero than under Layer 0's seeds, reported by rating band | broadcast games: not passed (residual −0.010 against Layer 0's −0.020, but log-loss worse by 0.050 a game, seeds resting on broadcast games alone) [E6]; monthly lists show today's seeds (newcomers' median first rating 1272 in 2023, 1564 in 2025 [E1]) | FIDE TRF archive |
| 4 K from certainty | K_i from σ_i (T4.3) | juniors and returning players lagging; bracket cliffs | log-loss of next-month results for the players whose K_i differs most from Layer 0's K, better than Layer 0 with the interval excluding zero | broadcast games: not passed (log-loss worse by 0.0024 a game for the players whose K changes most; σ from broadcast games puts most players at K_max) [E6] | FIDE TRF archive |
| 5 Junior compensation | opponents' expectations use RX_j (T4.6) | adults drained by under-rated juniors (target 1) | adults' mean residual against eligible juniors not significantly outside ±0.01 (under Layer 0 it is expected to be negative), reported by rating band | broadcast games: not passed: adults' residual −0.055 → −0.018 (outside ±0.01 below 2000), log-loss better by 0.016 a game [E6] | FIDE TRF archive |
| 6 Monthly adjustment | a_t posted in rated months (T4.5) | drift of the level (target 1) | anchor-cohort drift D_t within ±2 points a year, scored from month 13 of operation (T4.5), and the level criterion \|d_t\| ≤ d_0 + \|drift\|/γ_a + 2 | broadcast games with Layer 1 refitted monthly: level criterion met; D_t not within ±2 (the fixed panel's published mean rose 2 to 9 a year; the controller follows d_t) [E6]; the lists show the drift a_t must hold: −6 to −2 points a year before March 2024, +2 to +3 after [E5] | FIDE TRF archive; the simulator for sustained drift (T9) |
| 7 Federation adjustment | a_{f,t} (T4.5), last, after FIDE data | federation isolation (target 2) | for every federation with at least 9,000 cross-border games, the cross-federation residual not significantly outside ±10 points; the selection test of T4.5 | none: monthly lists carry no games | FIDE TRF archive |

### T8.2 Decision rules

*Calibration rule.* A rung passes calibration when (a) no 50-point gap bin with at least 1,000 games has a mean residual S − E significantly outside ±0.01 (one-sided z-tests against the nearer bound, Holm–Bonferroni across bins at a familywise 5 %), and (b) the slope of the bin mean scores on the bin mean expectations, by weighted least squares across all such bins, lies within 0.95–1.05 with a standard error below 0.02; if the standard error is larger the slope test is reported as inconclusive, not as a pass. A bin's residual has a standard error of about 0.014 near x = 0 at 1,000 games, so a bin fails only when the evidence against it is strong; the minimum detectable deviation of each bin is published with the result.

*Do-no-harm check.* Every rung, in addition to its targeted metric, must not make the overall forecast worse than Layer 0's beyond a pre-registered tolerance (PROVISIONAL): the upper end of the 95 % interval of the difference in overall three-outcome log-loss may not exceed 0.002 nats per game, and the game-weighted mean absolute calibration residual over 50-point gap bins may exceed Layer 0's by at most 0.005. A rung that passes its targeted metric and fails this check is not recommended.

*Residual rules.* "Not significantly outside ±b" means that the 95 % interval of the residual overlaps [−b, +b]; with several groups (rating bands, federations) Holm–Bonferroni applies across them. Each result is published with its sample size and minimum detectable deviation.

*The farming region before FIDE's data (R12).* Until bins of 1,000 games exist there, all gaps of 400 or more at levels of 2300 or more are pooled into one bin for a directional test with its interval, labelled low-power; the formal test of rule (a) waits for FIDE's game archive.

### T8.3 Protocol

Rolling origin: fit on months ≤ t, forecast every rated game of month t + 1, score, roll one month, over the test months (the first 24 months of any data source are training only). The match schedule is never a feature: the Kaggle 2011 winner conceded that schedule information drove much of his edge, which is not legitimate for an official rating [R 9] [R §9]. Layer 0 has no draw model, so for the three-outcome metrics it is scored with an empirical draw split by level band from the training months. A decision needs at least 12 test months.

### T8.4 Metrics

Games g = 1 … G in the test month, outcome y_g ∈ {W, D, L} from the player's side, forecasts P_W, P_D, P_L, expected score E_g, score S_g.

| Metric | Definition |
|---|---|
| Three-outcome log-loss | LL = −(1/G) Σ_g Σ_{o ∈ {W,D,L}} 1[y_g = o] · ln P_o(g), nats per game |
| Ranked probability score | RPS = (1/G) Σ_g (1/2) Σ_{k=1}^{2} (F_k(g) − O_k(g))², where F_k and O_k are the cumulative forecast and outcome over the ordered outcomes L < D < W |
| Brier on expected score | B = (1/G) Σ_g (S_g − E_g)² |
| Calibration by bin | For each bin b (gap x in 50-point bins to 1000; level band; colour; time control): mean residual r_b = mean(S_g − E_g) with its standard error, and the across-bin slope of T8.2; reported for bins with at least 1,000 games, and separately for the farming region (gap ≥ 400, level ≥ 2300) |
| Anchor-cohort drift and level | D_t = m_t − m_{t−12}, the twelve-month change of the published mean of the fixed anchor panel (chain-linked at each re-basing), points per year [R 22]; and d_t itself (T4.5) |
| Spread | the ratio of the SD of published ratings to the SD of the Layer 1 estimates, for active adults (R1) and the pool, monthly; its calendar-year mean against θ_R1 (T3.5) |
| Cross-federation residual | r_f = mean(S_i − E(x_i)) over games with i ∈ f and j ∉ f, in score units, and in points r_f / E′(0; tc, L̄_f) with E′(0) = κ_tc q / (2(2 + ν_0)); while rung 7 is disabled, per-federation values and federation-pair bins go to the QC only, and the public report carries only their distribution across federations, without names (REDTEAM_v0_3, V3-QC-1) |
| Newcomer residual | mean(S − E) over a newcomer's first 30 rated games after the first published rating, by rating band |
| Monitoring indicators | Published monthly without names: the compensation hunter's yield, the residual of adults against compensated juniors by the adult's band (T4.6); per-event lines (2) and (3) of the ledger, unflagged; a farming index (share of a player's gain from opponents rated more than 400 points below, including games against compensated juniors); the mean residual S − E by games played in the trailing twelve months (T4.5); an estimate–rating divergence count, \|θ̃_i − R_i\| > 2 σ_i, excluding eligible juniors and players back from inactivity within twelve months; Cov(θ, δ_tc) and the cross-time-control correlation as fit diagnostics. To the QC only: event flags on creation beyond what the K mix and pairings predict, the pair-level line-2 monitor (T6), returns from inactivity whose first-10-game score exceeds the expectation by more than 2 SD (PROVISIONAL), each eligible junior's share of posterior precision from other time controls (T4.6), per-player gains from cross-federation games, and federation estimates moving faster than their cap would allow |

### T8.5 Significance

Paired moving-block bootstrap by month: resample blocks of 3 consecutive test months with replacement, recompute each metric for the rung and for Layer 0 on the resampled months, take the paired difference, repeat 2,000 times with a published seed, report the 2.5 and 97.5 percentiles as the 95 % interval. A difference counts only if the interval excludes zero. Months are the unit because games in a month share ratings and parameter file, and blocks of three because consecutive months share most of their 36-month fit window (REDTEAM_v0_3, V3-STAT-10).

### T8.6 Data (D12)

1. FIDE's monthly lists, standard, rapid and blitz, archived monthly since February 2015 [V 3]: ratings, K, games, year of birth, federation. No data licence is stated [V 3], so the project downloads and analyses them and never redistributes them (D17); only aggregates are published.
2. The Lichess broadcast archive of over-the-board games, CC BY-SA 4.0, attributed [V 4]: the game-level data for the strong, internationally active part of the pool; it carries FIDE ratings and IDs where the broadcaster entered them. Its bias towards stronger players and events is stated with every result.
3. FIDE's TRF archive, the game record submitted under §9.1 [V 1], under a data-sharing agreement (stage 2): the only data on which rungs 3 to 7 can be settled for the whole pool, and the only data on which φ_f can be tested.

List membership is an input to Layer 0: the batch first listed in March 2026 and removed from the April 2026 list (15,712 standard IDs) is excluded from every cohort analysis and from Layer 1's games (D-0008, R11; [E1] [E5]).

Lichess online games are not an evidence source (D12): online ratings and online pools differ from over-the-board play, and the proposal's evidence must come from the games FIDE rates.

### T8.7 Order of work

Real data first, simulation second (D12): the monthly lists (drift, the floor, newcomers, K) and the broadcast archive (calibration, colour, draws) are analysed before the simulator of T9 is built, so that the simulator is calibrated on measured quantities rather than assumed ones.

### T8.8 What is fixed and what may change

Pre-registered now: the baseline, the rungs and their targeted metrics, the decision rules of T8.2, the protocol, metric formulas and bins, the bootstrap procedure and seed, the anchor-cohort definition and P1–P6. The PROVISIONAL parameter values, the Layer 1 hyperparameter grid and the federation threshold text may change, each change dated, but each data source's thresholds are frozen before its first test month is scored, and nothing changes after the first FIDE TRF month is unsealed.

### T8.9 Rollback triggers (closed list)

The parameter file reverts to the last compliant version while the QC investigates if, and only if, one of the following holds two months running: (1) the calibration rule of T8.2 fails on the latest twelve test months; (2) the do-no-harm check fails on the latest twelve test months; (3) the level criterion of rung 6 fails; (4) a monitored channel exceeds its cap (line 3 per active player above a_cap, T4.5). A reversion restores the table parameters, K bounds and a_t of the last compliant file; c_j is recomputed under them. The list is held only when the ledger has a residual that no line explains (T6). Event flags, which mark a fixed share of events by construction, never trigger a rollback (REDTEAM_v0_3, V3-QC-4, V3-QC-7), and neither does the spread ratio: beyond θ_R1 two years running it triggers a QC review (R1).


### T8.10 Status of the evaluation, October 2026

What has been run under these rules (sessions ELO-3 and ELO-4):

- **Rung 1.** Layer 0, specified in `docs/specs/SPEC-L0_fide-reference-engine_v1_1.md` and ratified before any engine code (`docs/decisions/D-0006_spec-l0-ratified.md`), reproduces every fixture of FIDE's published calculations and the 2025 U.S. Championship game by game, player by player and on the November 2025 list [E0]; 58 multi-event periods from FIDE's published calculations were added as fixtures (R10): every game and tournament sum is reproduced, the list change in 56 of the 58 (six after FIDE's own base corrections), two being one point off without explanation; 13 of the 14 periods that discriminate follow rounding once per period, still NOT VERIFIED as a rule, and F-P02 follows rounding per tournament (`analysis/OUTPUT_L0_rounding.md`). Rung 1's criterion, every disagreement explained, is therefore not yet met for three periods.
- **Rung 2.** Evaluated by the protocol of T8.3 on the broadcast archive under `docs/specs/SPEC-TABLE-FIT_v1_0.md`: 21 test months, 2025-01 to 2026-09; it passes rule (a) in all three time controls, where table 8.1.2 fails; slope (b) 0.996, 0.950 and 1.017; it passes the do-no-harm check and improves log-loss with the interval excluding zero (standard −0.048 nats a game) [E2]. Pooled at gaps of 400 or more above 2300 (R12), it under-predicts the favourite in standard (+0.032, interval +0.019 to +0.046, 827 games) and blitz (+0.045, 1,020 games) and is within ±0.01 in rapid; table 8.1.2 is within ±0.01 in standard and blitz and over-predicts in rapid (−0.064) [E6]. The month-block bootstrap of T8.5 and a bootstrap over the favourites (players) both keep the interval outside ±0.01 [E6]. The farming region is part of rung 2's stage-1 gate (T11), so rung 2 has not passed that gate; it is the first test to repeat on FIDE's data.
- **Layer 1.** Specified in `docs/specs/SPEC-L1_v1_0.md` and fitted on history (T2.3a; `analysis/OUTPUT_L1_history.md`).
- **Rungs 3 to 6.** Tested on broadcast games with Layer 1 refitted at each of the 21 test months on the 36 months before it, each rung against Layer 0 with everything else held [E6]. Rung 3 does not pass (do-no-harm: log-loss worse by 0.050 a game; seeds rest on broadcast games alone). Rung 4 does not pass (targeted log-loss worse by 0.0024 a game; broadcast-only σ puts most players at K_max). Rung 5: does not pass the ±0.01 rule by band: the adults' residual against eligible juniors is −0.055 under Layer 0 and −0.018 with compensation, and forecasts improve (log-loss −0.016); against a matched control of adult pairs the junior-specific residual moves from −0.047 to −0.010, but the compensation is too small below 2000 and too large against adults rated 2400 or more (T4.6). Rung 6: meets the level criterion in all three time controls; the D_t rule fails because the fixed panel's published mean rose 2 to 9 points a year (the steady-adult rise of E5) while the controller follows d_t; a design question for the architect. The juniors and newcomers below 2000 that rungs 3 and 5 are meant for are almost absent from broadcast games; FIDE's TRF archive settles them for the pool.
- **Rung 7.** Not testable without FIDE's game archive; the direction of Ghita's federation residuals holds on broadcast games for 21 of the 22 federations he names over 2023–2026, and for all 22 on 2023, 2024 and 2026, which his 2025 extract cannot contain [E7].
- **The deflation question** is settled on FIDE's lists: the level of steadily active adults has stopped falling since March 2024 in standard and rapid; what continues is the transfer from the top implied by table 8.1.2's over-prediction and the composition of the active list [E5].
- **The simulator** (T9) has not been built, as T8.7 orders; it is the next step, with the measured outcome parameters (T9.1).
---

## T9 Simulator design

Built after the real-data tests of T8 (D12), so that its inputs are measured where they can be. Not engine code: it calls the Layer 0 and Layer 2 engines as libraries, and nothing in it is published with a list. It measures what no backtest can: recovery of known true skill and the yield of strategies absent from ordinary data. All values PROVISIONAL, to be replaced by the measurements of the evidence reports where available.

### T9.1 Data-generating process

| Block | Parameters (PROVISIONAL) |
|---|---|
| Federations | N_F = 6; sizes N_f = 20,000 / 10,000 / 5,000 / 2,000 / 1,000 / 500 players at start |
| Pairing geography | within-federation share π_within = 0.90 of a player's games; cross shares C_{ff′} = (1 − π_within) · N_{f′} / Σ_{f″≠f} N_{f″}; scenario files may overwrite any row of C |
| True skill | s_{i,tc}(0) = θ_i(0) + δ_{i,tc}; θ_i(0) ~ Normal(m_f, 300²) with m_f = 1800 for all f in the baseline; δ_{i,tc} ~ Normal(0, 60²) with ρ = 0.97, ω = 8 |
| Age at start | mixture: 35 % aged 8–17 uniform, 65 % aged 18–65 with density decreasing linearly to zero at 65 |
| Improvement curve μ(age) | +8.0 points per month at age 10, falling linearly to 0 at age 22; 0 from 22 to 45; −0.3 per month 46–60; −0.8 above 60 |
| Random walk σ_θ(age) | 25 points per month under 18; 12 for 18–45; 15 above 45 |
| Entries | 0.5 % of the active pool per month (about 3,500 per month at FIDE scale [R §6]); entrant age profile: 60 % aged 8–15, 25 % aged 16–25, 15 % older; entrant θ drawn from Normal(m_f − 150 + 25 · (age − 10)⁺, 250²), truncated at 800 (the truth may differ by federation; the system's priors do not, D4) |
| Exits (monthly hazard) | 0.3 % baseline; 2.0 % for ages 18–20; 1.0 % above 60; 1.5 % for players inactive 12 months or more |
| Activity | games per player per year ~ lognormal, median 30, 10th percentile 8, 90th percentile 90; a player's year is split into events |
| Event types | 80 % Swiss (9 rounds; 5 or 7 in 15 % of events each): round 1 top half against bottom half by rating, later rounds within score group, odd player floats down; colours alternate, difference never beyond ±2, never three in a row. 20 % round-robin: 10 players, Berger colours. 90 % of an event's entrants from the host federation |
| Outcomes | the T3.1 model with true skills: z = q (s_i − s_j + w_i η), ν = exp(α + β (L_true − 2000)/400) exp(−γ\|z\|), η = 36, α = 0.2860, β = 0.4985, γ = 0.2915 (standard: the values fitted on published ratings in [E2], the closest measured ones; PROVISIONAL-FITTED) |
| Rating lists | monthly; Layer 0 exactly as SPEC-L0 [V 1]; Layer 2 as T4 with Layer 1 refitted monthly, 36-month window, and the table fitted on published ratings yearly (T3.3) |
| Run length | 120 simulated months after a 36-month burn-in; 20 seeds per scenario |

### T9.2 Scenarios

1. Baseline stationary pool: entries equal exits in skill flow, m_f equal.
2. Deflating pool with a junior wave: entry rate doubled, entrant age 60 % under 12, μ(age) 1.5 times the baseline.
3. Two isolated federations: C set so that federations 5 and 6 play 1 % of games outside, with m_5 = +100 and m_6 = −60 relative to the rest; measures whether φ_f is recovered, whether the selection test of T4.5 separates true offsets from traveller selection, and how the global channel behaves without the federation channel.
4. Farming pool: 50 players rated above 2600 who choose events whose field averages 400 to 800 below them.
5. Mass inactivity and return: 30 % of the pool inactive for 24 months, then returning with true skill moved by their random walk.

### T9.3 Rung ablations

Against Layer 0, one rung at a time (rungs are adoptable alone) and then cumulatively in ladder order: rung 2 alone; rung 3 alone; rung 4 alone; rung 5 alone; rung 6 alone; then 2, 2–3, 2–4, 2–5, 2–6. Each step reports the T9.5 outputs.

### T9.4 Adversaries

100 agents per strategy, under Layer 0 and under each rung, against the same agents playing ordinarily; measured as points gained per game and per year relative to ordinary play, with the 20-seed interval.

| Adversary | Behaviour simulated | Quantity measured |
|---|---|---|
| Farmer | plays only events with fields 400–800 below own rating | points per game versus ordinary play against equals |
| Sandbagger | loses deliberately for 12 months, then plays a target event normally | points per year and peak-to-trough swing; whether the rise in K_i rewards the dip |
| Colluding pair with unequal K | a K_min and a K_max player arrange results so the high-K partner gains | net points created per arranged game (ledger line 2), and the rate at which the per-event flag of T6 catches it (no K-ratio cap, D11) |
| Arranged-draw ring | 8 players draw every mutual game | points protected per year versus ordinary play; detection statistic from the draw model |
| Inactivity protector | stops playing at a peak | points retained per year; growth of σ_i and K_i on return |
| Minimum-activity adjustment collector | plays one rated game a year, enough to stay active under §7.2.2, and collects the accrued a_t | rating minus true skill after five years, against an active player of the same skill (the accrual windfall, reduced by R3's activity factor, T4.5) |
| Compensation hunter | seeks juniors with c_j > 0 as opponents | points per game versus ordinary play, by the hunter's band; on broadcast games the yield is positive for adults rated 2400 or more (+0.026 a game on table 8.1.2, +0.034 on rung 2's table [E6]), so the lower quantile alone does not stop it |
| Farmer under rungs 2 and 4 | plays fields 400–800 below with rung 2's table and rung 4's K | points per game; the farming-region residual of E6 (+0.032 standard, +0.045 blitz) at K ≈ 19–25 |
| Seed booster | a club arranges rated blitz wins for a newcomer before the newcomer's standard seed | the seed's error and the club adults' points per game; how far the seed's information-share condition (T4.7) limits it |
| Compensation manufacturer | a club arranges wins for its junior, in the same time control or in blitz, to switch c_j on, then plays the junior in standard | points per game to the club's adults; how far the gates, the lower quantile and the information-share condition of R5 (T4.6) limit it |
| K raiser | plays only opponents far below to keep σ_i and K_i high | K_i reached and points per game, against the farming-region calibration test |
| Returner and active donor | a returner near K_max and a very active player near K_min arrange results | net points created (ledger line 2) and the rate at which the pair-level monitor of T6 catches them |
| Seed manipulator | plays the first N_seed games against chosen opponents (including three friends in two events) | seed error \|R_seed − θ\| versus the ordinary seed error |

### T9.5 Outputs and acceptance checks

| Output | Acceptance (PROVISIONAL) |
|---|---|
| Recovery of true skill: RMSE of R_i − θ_i over active players, by level band, age band and activity decile, per month | each rung's RMSE not above Layer 0's in any band or decile in scenarios 1–3 and 5, and below it in the bands the rung targets |
| Spread: κ_tc and the ratio of published to latent SD over the run | no trend beyond ±0.01 a year (T3.5); calendar-year changes of the ratio against θ_R1 (R1) |
| Drift of the anchor mean: D_t over the run | within ±2 points per year in scenarios 1 and 2 with rung 6 |
| Newcomer convergence N_50 (the game count after which \|R_i − θ_i\| < 50 for the rest of the run) | median ≤ 15 games with rung 3 |
| Ledger: the T6 identity evaluated each month | closes exactly (the rounding residual is a ledger line) |
| Adversary table | no strategy gains more under any rung than under Layer 0 |
| Determinism | two runs with the same seed give identical lists and ledgers byte for byte |

---

## T10 Worked examples by hand

All arithmetic from `analysis/v04_calculations.py` (sections 7–10 of its output) with the parameters of T1 (the table's PROVISIONAL-FITTED, the rest PROVISIONAL); the rounding to a published change assumes the game is the player's only game of the period. "Today" means the FIDE Rating Regulations as transcribed [V 1]. All rungs are taken as adopted; K_i follows R6, compensation R5 and R8, accrual R3.

**T10.1 Example (i): an established 1900 adult against a 1500-listed junior whom Layer 1 rates at 1850.** A (1900, White, latent σ_A = 55 so K_A = 14.1 under R6; σ values are assumptions, T4.3) meets J (1500, Black, 16 in the list year and eligible by games and information share, θ̃_J = 1850 and σ̃_J = 100 on the published scale, latent σ_J = 121.2 so K_J = 40.0). A is not eligible, so J's compensation enters A's expectation (R8): c_J = min(300, max(0, round_FIDE(1850 − 1.2816 × 100 − 1500 − 25))) = round_FIDE(196.84) = 197, so RX_J = 1697. Level L = 1700, band 1700–1799 (ν_0 = 0.9748). A's gap x_A = 1900 − 1697 + 36 = 239, E_A = 0.780 (without compensation x would be 436 and E 0.919). J's gap x_J = 1500 − 1900 − 36 = −436, E_J = 1 − E(436) = 0.081: J's own update uses published ratings only.

Today: D = 400, not "more than 400", so no cap applies; table 8.1.2 row 392–411 gives .92 to A and .08 to J; K = 20 for A and 40 for J (16 years old and under 2300) [V 1].

| Result | A today: 20 × (S − .92) | J today: 40 × (S − .08) | A, all rungs: 14.1 × (S − 0.780) | J, all rungs: 40.0 × (S − 0.081) |
|---|---|---|---|---|
| A wins | +1.6 → **+2** | −3.2 → **−3** | +3.1020 → **+3** | −3.2400 → **−3** |
| Draw | −8.4 → **−8** | +16.8 → **+17** | −3.9480 → **−4** | +16.7600 → **+17** |
| J wins | −18.4 → **−18** | +36.8 → **+37** | −10.9980 → **−11** | +36.7600 → **+37** |

The adult is drained less for drawing a junior who is really an 1850 player (−4 instead of −8), loses less when the junior wins (−11 instead of −18) and gains more for winning (+3 instead of +2); the junior's own published changes are today's (−3, +17 and +37), because the junior's update never sees c_J and the fitted table gives the lower-rated player 0.081 at this gap against today's .08. Ledger lines for this game (T6, with E_A⁰ = 0.919):

| Result | transfer J → A, ½(14.1 + 40.0)(S_A − 0.919) | created by unequal K, (14.1 − 40.0)(S_A − 0.919) | created by compensation, 14.1 × (0.919 − 0.780) | sum of the two changes |
|---|---|---|---|---|
| A wins | +2.1910 | −2.0979 | +1.9599 | −0.1380 |
| Draw | −11.3340 | +10.8521 | +1.9599 | +12.8120 |
| J wins | −24.8590 | +23.8021 | +1.9599 | +25.7620 |

In every row the sum of the two players' changes equals the two creation terms exactly; the compensation term, +1.9599 points, is the same whatever the result: it is the deflation the adult used to pay, now printed as a ledger line. E_A + E_J = 0.861, less than one, is the same fact seen from the expectations.

**T10.2 Example (ii): a 2600 against a 2100, and a 2700 against a 2100.** The strong player has White and latent σ = 45, so K_i = 10.0 under R6 (raw 9.55 at 2600 and 9.56 at 2700, clipped to K_min; PROVISIONAL). Today both have K = 10 [V 1]. The 2600 is below 2650, so D = 500 is counted as 400 (row 392–411, PD = .92); the 2700 is at or above 2650, so D = 600 is used in full (row 560–619, PD = .98). In rapid and blitz the plain 400-point cap applies to both and, with a player above 2600 and a difference of 600 or more, the second game is not rated at all [V 2].

| Player | Opponent | Today: D used, PD | Today: win / draw / loss | Rungs 2 and 4: x (with +36 for White), band, E | K_i | Rungs 2 and 4: win / draw / loss |
|---|---|---|---|---|---|---|
| 2600 | 2100 | 400, .92 | +0.8 / −4.2 / −9.2 | 536, 2300–2399, 0.932 | 10.0 | +0.6800 / −4.3200 / −9.3200 |
| 2700 | 2100 | 600, .98 | +0.2 / −4.8 / −9.8 | 636, 2400–2499, 0.957 | 10.0 | +0.4300 / −4.5700 / −9.5700 |

Why the farming incentive disappears. With a calibrated table the expected change is K_i (P_W (1 − E) + P_D (½ − E) + P_L (0 − E)) = K_i (E − E) = 0 exactly (P4): the win is worth little and the loss costs much, in the exact ratio of their probabilities, at every gap, with no cap. Today the 2600's expectation is capped at .92 while the table's own uncapped value at D = 500 is .96 (row 485–517 [V 1]); if the uncapped table were right, every game against a 2100 would be worth 10 × (.96 − .92) = +0.4 points in expectation, the incentive the October 2025 amendment removed for players rated 2650 and above and left in place below [V 1] [R 55]. The cliff at 2650 today, and its absence under rung 2 (each player beats a 2200 with White; K = 10.0 under rung 4):

| Winner | Today: gap used, PD, gain at K = 10 | Rungs 2 and 4: x, band, E, gain at K_i = 10.0 |
|---|---|---|
| 2649 | 400, .92, +0.8 | 485, 2400–2499, 0.905, +0.9500 |
| 2651 | 451, .94, +0.6 | 487, 2400–2499, 0.905, +0.9500 |
| 2700 | 500, .96, +0.4 | 536, 2400–2499, 0.926, +0.7400 |
| 2936 | 736, 1.0, +0.0 | 772, 2500–2599, 0.978, +0.2200 |

Today the gain jumps between 2649 and 2651 for the same result against the same opponent and vanishes above a 735-point gap; under rung 2 it declines smoothly and never reaches zero. With D1's draw decay the fitted table gives the favourite expectations close to the 5/6-gap rule (T3.2), so the gains are close to today's in size; the calibration test of T8 decides whether the table is right before any table is published; on broadcast games the fitted table passes it [E2], except that pooled at gaps of 400 or more above 2300 it under-predicts the favourite (T8.10) [E6], so in this very region these gains would be too large if FIDE's games confirm it.

**T10.3 Example (iii): one month's adjustment for one player.** Standard list; the anchor cohort's published mean is m_t = 2004.6 and its latent mean m̂_t = 2011.8, so d_t = +7.2. a_t = clip((1/6) × (7.2 − 2.0), −1.5, +1.5) = 0.8667, published as +0.9; a_{f,t} = 0 (disabled). The player had three rated games with game terms −2.4090, +5.8410, −8.7000 (sum −5.2680) and no carried balance. With 24 rated games on the twelve lists up to t and an anchor mean of n̄ = 30 (illustrative), the accrual factor is min(1, 24/30) = 0.8 (R3), so the month adds +0.9 × 0.8 = +0.72: period total −5.2680 + 0.7200 = −4.5480, rounded under §8.3.4 [V 1] to **−5** (without R3, −4.3680 → −4). Had the player not played this month, no game terms and no posting: the rating is unchanged and the month's a_t accrues to the balance, to be posted in the next rated month (T4.5). Ledger: +0.72 under line 4 for this player. In the stylised pool of script §9, with a steady deflationary pressure of 1.3 points a month, a_t rises within two years to +1.3 and the measured gap settles at 9.5 points (d_0 + drift/γ_a = 9.8 before the one-decimal grid).

**T10.4 The ledger on a synthetic month (script §10).** Eight listed players (ratings 1900, 1500, 2050, 1750, 2300, 1600, 1405, 1580; latent σ 55, 121.2, 50, 70, 45, 120, 70, 90, so K under R6 14.1, 40.0, 11.7, 22.7, 10.0, 40.0, 22.6, 36.7; the 1500 is a compensated junior with θ̃ = 1850, σ̃ = 100 and RX = 1697; the 1580 received a first rating on list t), nine rated games, one game against an unrated player (not rated for anyone, T4.1), one late-rated game of the 1580 player against the 2050, rated for the 1580 player only under §8.2.4 [V 1] (+16.2581), a_t = +0.9 posted to all eight (the accrual factor taken as 1 here), one newcomer seeded at 1650 and one former floor exit re-published at 1452, while a newcomer at θ̃ = 1287.6 and a former floor exit at 1381.2 stay unrated. Published changes −9, +75, +8, −24, −1, +22, −7 and +17; the −7 takes the 1405 player to 1398, below the floor, so that player leaves the list at the post-update rating 1398. List total before 14085, after 15870: change +1785. Ledger: created by unequal K +39.8134; created by compensation +17.5852; one-sided under §8.2.4 +16.2581; adjustments posted 8 × 0.9 = +7.2; rounding residual +0.1433; entering +3102 (1650 + 1452); exits −1398; total +1785.0000. Transfers cancel by construction and the identity of T6 closes exactly; without line (2b) it would miss 16.2581, and booking the exit at the pre-update 1405 would leave 7 points, which is why T6 books R_i⁺(t).

---

## T11 Transition

Four stages; nothing in stages 1–3 touches the official list. The adoption ladder (proposal §9) runs across them: any subset of rungs can be shadowed in stage 2, piloted in stage 3 and adopted in stage 4, lowest risk first.

### Stage 1: Layer 0 replica and the first real-data tests, now

The reference engine implements the Rating Regulations exactly (`docs/specs/SPEC-L0_fide-reference-engine_v1_1.md`), test-vector verified against FIDE's published calculations, since FIDE's online calculator is out of date (SPEC-L0 §6.1) [V 1] [V 3]; the rapid and blitz branches carry the plain 400-point cap and the 600-point exclusion [V 2]. The first evidence reports measure, on FIDE's monthly lists, the drift of the anchor cohort, the pile-up at the floor, newcomers and the K distribution, and, on the broadcast archive, the calibration of table 8.1.2, White's edge, draw rates and colour imbalance (T8.6). Gate: exact reproduction of every fixture; rung 2's table fitted and tested under T8. Needs nothing from FIDE.

### Stage 2: twelve-month shadow list

Published in parallel with the official list for twelve months, with no effect on titles, norms, pairings or prizes. Precedent: during the 2008–2011 K-factor trial, when top players raised "major concern", FIDE ordered a parallel list so both calculations could be compared before anything changed [R §2] [R 16].

Published each month: the shadow list (rating, K_i, games, RX_j for compensated juniors, carried balance B_i and settled rating R_i + B_i); the parameter file (T7) per time control; the ledger (T6); a monitoring report with the public T8 metrics and indicators, without names and without per-federation figures while rung 7 is disabled (T8.4).

Rollback: on the closed list of triggers of T8.9 only, the parameter file reverts to the last compliant file while the QC investigates, and the reversion is published. The QC signs every parameter file (T7 signatures block); the project team proposes, never signs. If the pilot is abandoned, nothing happens to anyone's rating: the official list was never touched; the shadow list stops with a closing report.

### Stage 3: pilot federation

One federation runs the shadow list as its national list for a defined period, PROVISIONAL twelve months, for domestic purposes; FIDE's official list remains the one used for titles, norms and every FIDE purpose. The choice is deferred to this stage (D17) and made on four criteria: complete game data (every rated game reported in TRF with colours and results); a large junior inflow, so that rungs 3 to 5 are tested where they matter most; real cross-border play, so that the federation's offset is measurable; and willing leadership. Publication, rollback and signature as in stage 2. Gate: twelve clean months and a QC report.

### Stage 4: adoption by Council decision

Changes to the Rating Regulations [V 1] and the Rapid and Blitz Regulations [V 2], paragraph numbers as verified on 2026-10-09, by rung.

| Paragraph | Today [V 1] [V 2] | Change | Rung |
|---|---|---|---|
| §8.1.2 (and the rapid/blitz equivalent) | one table of D into PD | replaced by the yearly table per time control and 100-point level band (T3), fitted on published ratings and published by the QC | 2 |
| §8.3.1; §7.3.1 rapid/blitz | 400-point rule with the 2650 exemption; the plain 400-point cap and the 600-point exclusion | deleted; the table has no caps | 2 |
| §8.3.2 | "Delta R = score - PD" | wording only: S − E from the yearly table, with x including the colour term | 2 |
| §8.3.2 (again) | — | x includes c_j for an eligible junior opponent | 5 |
| §8.2.2; rapid/blitz §7.2.3 | two hypothetical opponents rated 1800, scored as draws | replaced by the Layer 1 seed; §8.2.3's 2200 maximum and §7.1.4's five games kept | 3 |
| §8.2.3 under rung 2 alone | Ru = Ra + dp with dp from table 8.1.1 | kept; table 8.1.1 then no longer inverts the new table: the fitted table reaches p = .75 at gaps 205–267 and p = .92 at 429–520 across band midpoints 1650–2450, where 8.1.1 gives 193 and 401 (script §10b), so newcomers are seeded lower than the new table implies; the QC may instead invert the new table for dp | 2 |
| §8.2.1 | a zero score in the first event is disregarded | kept for the five-game threshold; the Layer 1 estimate uses every game | 3 |
| §8.2.4 | a newly rated player is rated in a late-rated tournament while opponents count them as unrated | kept at every rung; booked in ledger line (2b) (T6) | all |
| §7.1.4, last sentence | "The rating must be at least 1400" | kept as the publication condition of the seed (T4.7) | 3 |
| rapid/blitz §7.2.1, §7.2.2, §7.2.5 | a standard rating is used for an unrated player; the newcomer rules | kept; under rung 3 the starting value is the Layer 1 estimate in that time control (T4.7) | 3 |
| §8.3.3; §7.3.3 | K = 40 / 20 / 10 by games, rating and age; K × n ≤ 700 | K replaced by the published K_i; the K × n ≤ 700 sentence kept, restated for K_i | 4 |
| new paragraph | none | junior compensation c_j and the RX column | 5 |
| new paragraph | none | the monthly adjustment a_t: accrued to active players, posted in a rated month, with its deadband, cap and source in the parameter file | 6 |
| new paragraph | none | the federation adjustment a_{f,t}, disabled until enabled by Council decision | 7 |
| §7.2.1 | below 1400 shown as unrated, then treated as unrated | unchanged in text; Layer 1 keeps estimating the player, and re-entry under §7.1.4 is seeded from Layer 1 instead of two phantom draws | 3 |
| §7.1.2 | closed list of published fields | add the columns RX (R_j + c_j) with an eligibility flag for every eligible junior (RX printed even when c_j = 0), K to one decimal, the carried balance B_i and the settled rating R_i + B_i | 4–6 |
| §8.1 | "the two tables are effectively mirror-images" | table 8.1.1 (p into dp) is retained unchanged wherever any regulation refers to it; only 8.1.2 is replaced, so the sentence is deleted | 2 |
| new paragraph | none | publication of the parameter file and the ledger with every list | all |
| new paragraph | none | delegation: the QC publishes the yearly table and the monthly parameter file within the caps approved by the Council; whether FIDE's rules allow this without a Council decision each year is NOT VERIFIED (table 8.1.2 is part of regulations headed "Approved by FIDE Council on 15/12/2023" [V 1]) | 2–7 |

Paragraphs that do not change: §1 rate of play (and rapid/blitz §1.1); §5 unplayed games; §6 matches; §7.1.3 closing date; §7.1.4's five games and 26-month pooling, to which rung 3 adds its seed conditions (3 opponents in 2 events, σ̃ ≤ 120, the information share; T4.7); §8.3.4 rounding (and §7.3.4); §9.1 TRF reporting [V 1] [V 2].

Title and norm regulations are not touched by this proposal. Their norm arithmetic computes Rp = Ra + dp from table 1.4.9, which is identical to table 8.1.1, and does not use table 8.1.2 [VT 1, 3], so rung 2 leaves it unchanged; any rung that changes published ratings changes the ratings that enter it (the opponents' average, the rating floors of §1.4.6 b, the titles by rating of §1.3, §0.6.2 and §1.5.3) [VT 1], and norms use the published rating R, never RX. Table 8.1.1 is retained wherever they refer to it. The shadow list has no legal status: no title application, norm, pairing, seeding, prize or eligibility rule may refer to it. How the rungs' ratings affect norms is for the QC to assess with the shadow list before stage 4. After adoption Layer 0 keeps running on the same tournament reports for at least 24 months, so that the Council can revert to the Layer 0 list by decision for the following month without any retroactive edit.

No one-off adjustment at adoption: the official list continues from its own values and any gap to the shadow list closes only through the capped monthly adjustments of rung 6 (|a_t| ≤ a_cap, PROVISIONAL 1.5 points per month), so ratings still change only for players who play, visibly in the ledger.

---

*End of DRAFT v0.4 technical annex. Status line repeated: DRAFT v0.4 — not for publication.*
