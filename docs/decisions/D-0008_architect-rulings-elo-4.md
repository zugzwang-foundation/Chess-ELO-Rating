# D-0008 — Architect's rulings R1–R14 for ELO-4

Date: 2026-10-09 (UTC; the brief is dated 2026-10-10) · Session: ELO-4 · Status: DECIDED (by the architect, Web Claude, in the ELO-4 brief; R4 and R14 are founder defaults, as the brief states); recorded by the executor in Phase 0, applied to the technical annex and the proposal in Phase 6 (v0.4)

## Context

The v0.3 review left eight decision-level questions for the architect, FA-1 to FA-8 (`docs/review/REDTEAM_v0_3.md`, "For the architect"). The ELO-3 close-out added six more: the wording of the spread finding, SPEC-L0 Q-1 (rounding granularity), the April 2026 list event, the farming region, CLAUDE.md hard rule 3, and SPEC-L0 Q-11 (FIDE's online calculator). The ELO-4 brief answers all fourteen. The rulings are fixed: the executor implements them and does not reopen them. Where a ruling leaves a detail open, the executor's reading is listed separately below and marked as such; it can be overruled by a later record without reopening the ruling.

Every parameter introduced or kept by these rulings is PROVISIONAL until estimated from data (CLAUDE.md, rule 7).

## The rulings

The text of each ruling is the brief's, transcribed.

| # | Answers | Ruling (the brief's text) |
|---|---|---|
| R1 | FA-1 (attenuation in D2) | Keep D2: the table is calibrated on published ratings, because P4 holds only for that fit. Guard against the ratchet instead: κ's annual change cap stays; the monthly spread ratio (SD of published ratings ÷ SD of Layer 1 strengths, active adults) is the second reference for spread; if it moves beyond a published threshold two years running, the QC reviews — no automatic correction. |
| R2 | FA-2 (θ̃ in spread as well as level) | Adopt θ̃ = m_t + (ŝ − m̂_t)/κ_tc. |
| R3 | FA-3 (accrual scaled by activity) | Adopt accrual scaled by min(1, n_i over 12 months ÷ the anchor cohort's mean games). |
| R4 | FA-4 (D3's public K against D17's QC-only σ) | Founder default: accept and state the disclosure — K and RX together reveal part of Layer 1's estimate for compensated juniors; D17's QC-only rule covers the full posterior and everything else. |
| R5 | FA-5 (same-time-control posterior for c_j) | c_j uses the same-time-control posterior s_{j,tc}; eligibility adds an information-share condition: at least half of that posterior's precision comes from games in the same time control (PROVISIONAL 0.5). |
| R6 | FA-6 (the 1/κ factor in the Kalman gain) | Adopt the published-scale gain: K_i = clip(q·σ_i² / (κ_tc·(1 + q²·σ_i²·v_tc)), K_min, K_max), v_tc = the fitted per-game score variance at x = 0. Recompute the examples and report the K an established 2600+ player gets. |
| R7 | FA-7 (γ's upper bound; boundary fits) | γ ≥ 0 with no upper bound; a fit on any boundary is a calibration flag for the QC. |
| R8 | FA-8 (compensation in junior–junior games) | Compensation applies only against opponents who are not themselves eligible; a game between two eligible juniors uses published ratings on both sides. |
| R9 | ELO-3 close-out, question 2 (spread language) | Spread wording: the fitted table as a whole — κ together with the level-dependent draw term — carries the spread (local scale 481/649/856 against 400); κ alone does not. Use D-0007's wording. |
| R10 | SPEC-L0 Q-1 (rounding granularity) | Keep rounding once per period (the regulation text and E0's 12 of 12), still NOT VERIFIED; add at least five more multi-event periods from FIDE's published calculations to settle it. Fixtures only — `src/layer0/` stays untouched. |
| R11 | ELO-3 close-out, question 4 (the April 2026 list event) | List membership is an input to Layer 0; exclude the batch first listed in March 2026 and removed in April from cohort analyses, and say so. |
| R12 | ELO-3 close-out, question 5 (the farming region) | Pool all gaps of 400 or more into one bin for a directional test with its interval, labelled low-power; the formal test waits for FIDE's game archive. |
| R13 | ELO-3 close-out, question 6 (CLAUDE.md hard rule 3) | The evidence base is `docs/research/` and `docs/evidence/` ([E n]). |
| R14 | SPEC-L0 Q-11 (FIDE's online calculator) | Founder default: FIDE's out-of-date online calculator is reported as a finding in a proposal appendix; nothing is sent to FIDE. |

## Where each ruling is applied

Planned at Phase 0; the v0.4 documents and their review record (Phase 6) state what was done.

| # | Technical annex (v0.4) | Proposal and brief (v0.4) | Elsewhere in ELO-4 |
|---|---|---|---|
| R1 | T3.5 (the ratchet and its guard), T7 (the spread ratio and its threshold as fields), T8.4 (the spread metric), T8.9 (a QC review, not a rollback trigger), T9.5 | §5 (level and spread), §11 | Phase 3: the spread ratio measured on history with Layer 1, so that the threshold can be set from its observed variation |
| R2 | T1 (θ̃), T2.6, T3.5, T4.6, T4.7, T10 | §6 | Phase 3: the Layer 1 specification and outputs; Phase 4: rungs 3 and 5 |
| R3 | T4.5, T5 (P3), T7, T9.4, T10.3 | §5, brief step 6 | Phase 4: rung 6 |
| R4 | T2.6 | §11, §13 | — |
| R5 | T4.6, T7 (gates), T8.4 | §6 | Phase 3: the information share as a Layer 1 output; Phase 4: rung 5 |
| R6 | T4.3, T7, T10 | §5, brief step 4 | Phase 4: rung 4, the K distribution including the K of established 2600+ players |
| R7 | T1, T3.1, T3.2, T3.3, T7 | §5 | The frozen parameter file (Freeze 1) was fitted under γ ∈ [0, ½]; its γ is interior in all three time controls (0.2915, 0.2002, 0.3145 [E2]), so the upper bound never bound and the frozen values stand under R7 |
| R8 | T4.2, T4.6, T6, T10 | §5, §6 | Phase 4: rung 5 |
| R9 | T3.5 | §5 | — |
| R10 | SPEC-L0 §8 Q-1 (the evidence added, the reading unchanged) | — | New fixtures and tests under `tests/`; the engine is not edited |
| R11 | T8.6, T6 (line 11, administrative changes) | — | Phase 1 (deflation, every cohort analysis); Phase 3 (Layer 1 inputs) |
| R12 | T8.1, T8.2 | §10 | The pooled directional test computed from the E2 aggregates and reported with the rung tests (Phase 4) |
| R13 | — | — | CLAUDE.md hard rule 3, changed in this record's pull request |
| R14 | — | a new appendix: the finding, its evidence (SPEC-L0 §6.1, `analysis/OUTPUT_L0_fixtures.md`) and the statement that nothing has been sent to FIDE | — |

## Executor's readings where a ruling leaves a detail open

1. **R1, the threshold.** The ruling asks for a published threshold and does not give its value. It is set in Phase 6 as a PROVISIONAL field of the parameter file, from the month-to-month variation of the spread ratio measured on history in Phase 3; the comparison is calendar year on calendar year, for active adults (the anchor-cohort age band), in each time control.
2. **R2, the means.** m_t and m̂_t are the published and Layer 1 means of the anchor cohort at the list date (annex T2.4), so θ̃ − m_t is a latent deviation from the anchor mean divided by κ_tc. With κ_tc = 1 it reduces to v0.3's θ̃ = ŝ − d_t.
3. **R3, the counts.** n_i is the number of rated games of i in the time control on the twelve lists up to and including list t (the sum of the lists' games fields); the anchor cohort's mean games is the mean of the same count over the cohort's members at list t. The factor multiplies a_t before accrual; it does not change a_t itself, the deadband or the cap.
4. **R5, precision.** The precision share is the share of the posterior precision of s_{j,tc} at the list date that comes from games in time control tc, measured as the Laplace precision contributed by those games (Phase 3 specifies it).
5. **R6, v_tc.** The per-game score variance at x = 0 is read from the fitted table, v_tc(L) = P_W + P_D/4 − ¼ at x = 0, which is 1/(2(2 + ν_0(L))), evaluated in the player's own level band (at x = 0 the game's level is the player's rating). With ν_0 = 0 it is ¼, D3's value, so R6 reduces to D3 when κ_tc = 1 and there are no draws. σ_i is Layer 1's posterior SD of s_{i,tc} in latent units.
6. **R10, fixtures.** A multi-event period is one rating period in which FIDE's published calculation for one player shows two or more tournaments. For each, the fixture records the published per-tournament changes and the published list change, so that rounding per period and rounding per tournament can be compared without the engine.
7. **R11, the batch.** The batch is identified from the lists themselves: every standard ID whose first rated appearance since February 2015 is the March 2026 list and which is absent from the April 2026 list (15,712 IDs [E1]). The same rule is applied to the rapid and blitz lists, and the count found in each is reported.
8. **R12, the region.** The pooled bin covers the farming region of annex T8.1, gaps of 400 or more at levels of 2300 or more, over E2's test months; the residual and its interval are computed for rung 2 and for Layer 0 from the committed E2 aggregates.

## Consequences

- FA-1 to FA-8 of REDTEAM_v0_3 and the six open questions of the ELO-3 close-out listed above are closed by this record.
- R13 changes CLAUDE.md hard rule 3 in the pull request that adds this record.
- Freeze 1 is untouched: `params/table_fit_2026-10.yaml`, `tools/compare_event.py` and `src/layer0/` do not change, and check (a) enforces it through the hashes printed in `docs/evidence/E3_us-championship-2026.md`.
- D-0005 and D-0007 stand except where these rulings revise them: D2 (kept, with the guard of R1), D3 (K, revised by R6), D5 (compensation, revised by R5 and R8), D8 (spread, worded by R9), D10 (θ̃ revised by R2, accrual revised by R3) and D1's range for γ (widened by R7).
