# D-0005 — Architect's decisions D1–D18 for proposal v0.3

Date: 2026-10-09 · Session: ELO-3 · Status: DECIDED (by the architect, Web Claude, in the ELO-3 brief; D12 is the operator's decision and D17 applies the founder's decisions, as the brief states); implemented by the executor in `docs/proposal/ELO-PROPOSAL_v0_3.md`, `docs/proposal/ELO-TECHNICAL-ANNEX_v0_3.md` and `docs/proposal/ELO-BRIEF_v0_3.md`

## Context

The ELO-2 close-out left six design questions for the architect (§6: the accrual rule and θ̃ netting, continuous compensation, the draw tail, a K ratio cap, the sign of a_t, the band width) and five founder decisions (§5). The ELO-3 brief fixes them, with further revisions, as decisions D1–D18. They override v0.2 wherever the two differ; AR-1 to AR-6 (`docs/decisions/D-0003_architecture-revisions-v0.2.md`) stand except as revised here. Every number below is produced by `analysis/v03_calculations.py` (output `analysis/OUTPUT_v0_3.md`, "script §n"); every parameter value is PROVISIONAL.

## The decisions and where they are implemented

| # | Decision (abridged from the brief) | Implemented in |
|---|---|---|
| D1 | Forecast tail: ν(z) = exp(α_tc + β_tc (L − 2000)/400) · exp(−γ_tc \|z\|), γ_tc ∈ [0, ½], PROVISIONAL γ = ½, so draws fade as fast as losses at large gaps; γ fitted in Phase 4; symmetry, monotonicity and the logistic special case re-proved. At level 2300 with v0.2's α, β: E = 0.713 / 0.878 / 0.926 / 0.975 at gaps 200 / 400 / 500 / 700 against the 5/6-gap rule's 0.723 / 0.872 / 0.917 / 0.966 (script §2), as the brief expected | annex T3.1, T3.2 (proofs, including monotonicity for every γ ≥ 0), T2.1; script §2, §3 |
| D2 | The published table is fitted on published ratings: κ, η, α, β, γ per time control by maximum likelihood on published ratings at game time, colours and results, separately from Layer 1; property P4 stated for this fit | annex T3.3 (likelihood, score equations, P4 for the fit), T5 P4; proposal §5, §11 |
| D3 | K is the Kalman gain: K_i = clip(q σ_i² / (1 + q² σ_i²/4), K_min, K_max), q = ln 10/400, K_min = 10, K_max = 40; σ_new removed; every example recomputed (σ 45 gives 11.5, σ 55 gives 17.0) | annex T4.3, T10, T7; proposal §5; script §5, §7–§10 |
| D4 | Priors use age only: μ_0(age); the federation term removed from T2.2 and from every seed, prior or default | annex T1, T2.2, T4.7, T7 (`prior_mu0_by_age`); proposal §4, §6 |
| D5 | Continuous junior compensation: c_j = min(c_cap, max(0, θ̃_j − z σ_j − R_j − τ)), z = 1.2816, τ = 25; p_min removed; the conditions on age, games, opponents and events stay | annex T4.6, T4.8, T5 P3, T7; proposal §6; script §6 |
| D6 | Level bands of 100 points; the largest step between adjacent bands is 0.0082 in E (0.009 in the three-decimal table, 0.16 points at K = 20), against 0.0256 under v0.2 | annex T3.4, T5 P3; proposal §5; script §3.1 |
| D7 | Monthly adjustment of both signs with a soft deadband: a_t = clip(γ_a sign(d_t) max(0, \|d_t\| − d_0), −a_cap, +a_cap), d_0 = 2.0; continuous in d_t | annex T4.5, T7; proposal §5, §6; script §9 |
| D8 | Level versus spread: a_t holds the level, κ_tc absorbs the spread, no rating is ever rescaled | annex T3.5; proposal §5 |
| D9 | Federation selection test added to the enabling conditions: φ_f estimated from junior and from adult travellers, and from home and from away events, must agree within its uncertainty | annex T4.5, T7; proposal §11 |
| D10 | The accrual-and-posting rule and θ̃ = ŝ − d_t are confirmed; the accrual rule explained in one plain sentence in the proposal | annex T4.5, T1; proposal §5 ("In plain words: …") |
| D11 | No K-ratio cap: it would slow juniors catching up; collusion is handled by the ledger and monitoring; reasoning recorded | annex T6, T9.4; proposal §11; this record |
| D12 | Evaluation (operator's decision): the only baseline is Layer 0; each rung is tested against Layer 0 on the problem it targets plus a do-no-harm check on overall three-outcome log-loss and calibration within a pre-registered tolerance; Glicko-2, TrueSkill Through Time, Whole-History Rating and Elo++ kept as prior art only; Lichess online games dropped; the real-data sources are FIDE's monthly lists and the Lichess broadcast archive; the simulator comes after the real-data tests | annex T8 (rewritten), T9; proposal §10 |
| D13 | Adoption ladder of seven rungs, each adoptable alone, lowest risk first, each with what changes, its targeted metric and the data that tests it | proposal §9; annex T8.1, T4 (rung per subsection), T11 (paragraphs by rung) |
| D14 | Chess960: the shared skill θ plus a 960 offset seeds a new list from existing ratings on day one; FIDE's 2026 General Assembly approved plans for a Chess960 rating [R §2] [R 25] [R 26] | proposal §8; annex T2.7 |
| D15 | A plain-language brief of at most 900 words | `docs/proposal/ELO-BRIEF_v0_3.md` (825 words by check (d)) |
| D16 | Colour named in the one-page summary as a fairness feature ("an extra White no longer pays"), outside the four headline targets | proposal §1, §2, §5; annex T3.2 item 6 |
| D17 | Founder decisions applied: θ̂ and σ visible to the QC only (K and RX public); pilot federation deferred to stage 3 with criteria (complete game data, a large junior inflow, cross-border play, willing leadership); FIDE lists downloaded and analysed, never redistributed; the repository description stays; removed from the open decisions | proposal §11, §12, §13; annex T2.6, T7, T8.6, T11 stage 3 |
| D18 | Consistency audit: every PARTIAL of REDTEAM_v0_2 and the third review's five fixes re-checked; body at most 4,500 words | `docs/review/REDTEAM_v0_3.md`; check (d) |

## Reasoning recorded for D11

A cap on the ratio of the two players' K factors (for example K_i ≤ 2 K_j, recorded as an option in REDTEAM_v0_1, R-EXPLOIT-1) would act in every game between a junior or newcomer near K = 40 and an established adult near K = 17 or a top player near 11.5. Those are exactly the games in which the design wants the under-rated player to move fast, so a ratio cap would slow juniors catching up, which is the first headline target. The collusion it would prevent, a low-K donor feeding results to a high-K partner, exists today with K of 40 against 10 [V 1] and is bounded by the per-period cap. It is handled by publishing the points created by unequal K per event (ledger line 2, annex T6), by flagging the top percentile of events for FIDE's investigation procedures (annex T8), and by the colluding-pair adversary of the simulator (annex T9.4).

## Executor's implementation choices within the decisions

- c_j lives on the whole-number grid: round_FIDE is applied inside the clip, because RX is a whole-number list column (D5 gives the formula without a grid).
- a_t keeps v0.2's one-decimal grid; with it the deflation steady state is 9.5 rather than d_0 + drift/γ_a = 9.8 (script §9).
- The 100-point bands run from 1500 to 2800, with an open band below 1500 (midpoint 1450) and one from 2800 (midpoint 2850).
- The tolerance of the D9 selection test is two standard errors of each difference; the D12 do-no-harm tolerances are 0.002 nats per game of log-loss and 0.005 of mean absolute calibration residual (all PROVISIONAL, annex T4.5, T8.2).
- Once rung 5 is in force, games involving an eligible junior are left out of the D2 calibration fit, so that the table and the compensation do not absorb each other's residuals (annex T3.3).
- Layer 1's own outcome parameters are written η^L, α^L, β^L, γ^L to keep them distinct from the table's, which D2 fits on published ratings (annex T1, T2.1).
- Check (d) is extended to the brief's 900-word cap (`tools/checks/check_wordcount.py`).

## Consequences

- The six architect questions of the ELO-2 close-out are closed: accrual and θ̃ by D10, continuous compensation by D5, the draw tail by D1, the K ratio cap by D11, the sign of a_t by D7, the band width by D6.
- Founder decisions 1, 2, 3 (the policy half) and 5 of the ELO-2 close-out are applied by D17. Still open for the founder: repository name and visibility before v1.0 (D-0001 stands), and the wording of the stage-2 TRF request.
- Every parameter value remains PROVISIONAL; κ, η, α, β and γ are first fitted on over-the-board data in the evidence work that follows (annex T8.6).
