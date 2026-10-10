# D-0009 — Architect's rulings R15–R23 for ELO-5

Date: 2026-10-10 (UTC) · Session: ELO-5 · Status: DECIDED (by the architect, Web Claude, in the ELO-5 brief; R22 and R23 are founder defaults, as the brief states); recorded by the executor in Phase 0 and applied in Phases 0 to 6 of the session

## Context

The v0.4 review (`docs/review/REDTEAM_v0_4.md`, "For the architect") and the ELO-4 close-out left nine open questions, Q1 to Q9. The ELO-5 brief answers Q1 to Q7 with the rulings R15 to R21 and adds two founder defaults, R22 and R23. The rulings are fixed: the executor implements them and does not reopen them. Where a ruling leaves a detail open, the executor's reading is listed separately below and marked as such; a later record can overrule a reading without reopening the ruling.

Two questions of the close-out are not answered by a ruling: Q8 (Layer 1's grids, where c_θ and ω were chosen at their edges) stays open; Q9 (whether anything can test rung 4 before FIDE's game archive) is answered by the brief's Phase 1, which rebuilds rung 4's certainty from FIDE's monthly lists instead of from broadcast games.

Every parameter introduced or kept by these rulings is PROVISIONAL until estimated from data (CLAUDE.md, rule 7).

## The rulings

The text of each ruling is the brief's, transcribed.

| # | Answers | Ruling (the brief's text) |
|---|---|---|
| R15 | Q1 (judging rung 6) | Rung 6 is judged on the gap to the model: d_t, the published anchor mean minus Layer 1's anchor mean, within ±2 points a year after warm-up. The anchor's absolute drift is reported, never a pass/fail criterion: real improvement is not drift. |
| R16 | Q2 (K and the games of a period) | K falls with the games in a period. Per-game gain K_i(n) = q·σ_i² / (κ_tc·(1 + n·q²·σ_i²·v_tc)), clipped to [K_min, K_max]; it replaces the K × n ≤ 700 cap with a smooth equivalent. Recompute the examples. |
| R17 | Q3 (rung 2 in the farming region) | Temporary farming guard for rung 2, all three time controls: when the gap is 400 or more and the favourite is rated 2300 or more, the favourite's expected score is the larger of the fitted value and table 8.1.2 read without the 400-point cap; the underdog's is one minus it. It lapses only when FIDE's game data calibrate the region. New code only. |
| R18 | Q4 (rung 5 by band) | τ stays constant. Report rung 5's by-band results as they are; the misses track the broadcast sample (the juniors who meet adults rated 2400 or more are the strongest juniors). The simulator and FIDE's data test it. |
| R19 | Q5 (the R1 trigger) | R1's review triggers on the cumulative change in the spread ratio since the last QC review, not on year-on-year moves. |
| R20 | Q6 (the executor's additions) | Confirmed, all PROVISIONAL: the 0.02 R1 threshold (to be calibrated in the simulator); the eligibility flag on the list so arbiters can apply R8; at least half of a seed's evidence from its own time control. |
| R21 | Q7 (SPEC-L0) | Issue SPEC-L0 v1.1 recording the 58-period rounding evidence (56 reproduced, two one point off, unexplained). No change to `src/layer0/` before the championship comparison and the 1 November check. |
| R22 | founder default (the ladder) | The ladder shows three verdicts, from the evidence: RECOMMENDED NOW — rungs 1 and 2 (with R17's guard); PILOT — rung 5; TEST ON FIDE DATA — rungs 3, 6, 7, and 4 unless Phase 1 passes. |
| R23 | founder default (Freeze 2) | Freeze 2 happens at the end of this session, not on 20 October: an earlier freeze is a stronger test. |

## Where each ruling is applied

Planned at Phase 0; the evidence reports E8 and E9, the v1.0 documents and their review record state what was done.

| # | Technical annex (v1.0) | Proposal and brief (v1.0) | Elsewhere in ELO-5 |
|---|---|---|---|
| R15 | T4.5, T8.1, T8.4, T8.9, T8.10 (rung 6's criterion is the twelve-month change of d_t; D_t reported, never scored) | §9, §10 | E6's replay of rung 6 rescored under R15 from its committed aggregates (Phase 4); the controller under sustained drift in the simulator (Phase 3, E9) |
| R16 | T1 (n_i), T4.3, T4.4 (the 700 rule replaced when rung 4 is adopted), T5 (P2, P3), T7, T10 (examples recomputed), T11 (§8.3.3) | §5, brief | Phase 1: the redesigned rung 4 (SPEC-K-ACTIVITY, E8) uses R16; the v1.0 calculations script recomputes the examples (Phase 4) |
| R17 | T3, T4.2, T5 (P4), T8.1, T8.10, T11 (§8.1.2, §8.3.1, §7.3.1 rows) | §5, §9, §12, brief | Phase 2: new code (a new package, planned as src/layer2), rung 2's farming-region and do-no-harm checks rerun with the guard, both 2026 championship fields checked against the guard region; Freeze 1 files untouched |
| R18 | T4.6, T8.1, T8.10, T9.4 | §6, §9 | rung 5's by-band results reported as E6 measured them; the compensation hunter by band in the simulator (Phase 3, E9) |
| R19 | T3.5, T7, T8.4, T8.9, T9.5 | §5 | the trigger's false-alarm rate and power in the simulator (Phase 3, E9) |
| R20 | T1, T3.5, T4.6, T4.7, T4.9, T7, T11 | §5, §6 | θ_R1 calibrated in the simulator (Phase 3, E9) |
| R21 | T8.10 | §4, §9, Appendix F | `docs/specs/SPEC-L0_fide-reference-engine_v1_1.md` (git mv from v1.0) with the evidence of `analysis/OUTPUT_L0_rounding.md`; `src/layer0/` untouched |
| R22 | T8.1, T8.10, T11 | §1, §9, §13, brief | the RECOMMENDED NOW package in the simulator (Phase 3); rung 4's verdict from Phase 1's result |
| R23 | — | §13 ("The 2026 U.S. Championships, run blind") | Phase 6: decision record D-0010 (Freeze 2), the SHA-256 of every file that produces a number in the comparison or the proposal printed in E3 and enforced by check (a), and the git tag `freeze-2` |

## Executor's readings where a ruling leaves a detail open

1. **R15, the sign and the rate.** The brief writes d_t as the published anchor mean minus Layer 1's; the annex defines d_t = m̂_t − m_t, Layer 1's minus the published (T2.4), and its controller is written in that sign (T4.5). The criterion is symmetric, so the annex keeps its sign. "Within ±2 points a year after warm-up" is read as the twelve-month change of the gap: |d_t − d_{t−12}| ≤ 2 points for every month from the thirteenth of operation, the first twelve being the controller's warm-up (T4.5), with d_t measured on the settled ratings R + B of the anchor panel's members (T2.4), as D_t was paired over members on both lists (E6 §5). The level criterion of T8.1, |d_t| ≤ d_0 + |drift|/γ_a + 2, stays beside it. D_t, the panel's twelve-month change of its published mean, is reported every month and is never a pass or fail criterion.
2. **R16, the counts and the clip.** n is n_i of T1, the number of rated games of i in the time control in rating period t, known when the period closes; K_i(n) applies to every game of the period. σ_i and v_tc are those of R6 (D-0008, reading 5), with σ_i taken at the list in force for the period. The clip to [K_min, K_max] applies to K_i(n), after the dependence on n. When rung 4 is adopted, K_i(n) replaces the K × n ≤ 700 rule of T4.4; when it is not, today's K and the 700 rule stay, as every rung not adopted leaves today's rule in place. The bound of a period's change that results (property P2) is computed and published with the examples, not assumed to be 700.
3. **R16, the published form.** Dividing numerator and denominator by q²·σ_i²·v_tc gives the same rule as K_i(n) = clip(C_tc(L) / (N_i + n), K_min, K_max), with C_tc(L) = 1/(κ_tc·q·v_tc(L)), a constant of the published table in each level band, and N_i = 1/(q²·σ_i²·v_tc(L)), the model's certainty about the player in games at equal strength. The list prints N_i to one decimal where it prints K today, and the per-game breakdown prints the period's K_i(n), so that an arbiter recomputes the period's K from n by hand. N_i discloses σ_i exactly as K_i did under R6; R4's accepted disclosure covers it.
4. **R17, the region and the two values.** The gap is the published rating difference that enters the expectation, without the colour term (R_i − R_j; R_i − RX_j when rung 5 applies to the game); the favourite is the player with the higher of the two, and "rated 2300 or more" is that player's published rating on the list in force (SPEC-L0 R-11a). "Table 8.1.2 read without the 400-point cap" is the H column of table 8.1.2 [V 1] at the full difference, 1.0 above 735 points, as a player rated 2650 or more reads it in standard today (SPEC-L0 R-14, R-16). "The fitted value" is rung 2's expectation for the favourite at the effective gap with the colour term, on the published three-decimal table (T3.4). The underdog's expectation is one minus the favourite's, so the guard creates no points. Under rung 2 the 400-point rules and the 600-point exclusion of the rapid and blitz chapter are deleted as T11 states; the guard covers their region. The guard is printed on the per-game breakdown whenever it binds.
5. **R19, the measure.** The ratio is the noise-corrected spread ratio of T3.5 for active adults, taken as its trailing twelve-month mean, so that the month-to-month noise measured on history does not trigger a review; the reference is that mean at the last QC review (at adoption, the first twelve months of operation); the QC reviews when the current value differs from the reference by more than θ_R1 in either direction, and a review resets the reference. The year-on-year rule of v0.4 ("two years running") is withdrawn.
6. **R20, the calibration.** θ_R1 is calibrated in the simulator as the smallest threshold whose false-alarm rate over ten simulated years of a stationary pool is at most 5 %, with the time to trigger under a ratchet held at κ's annual cap reported beside it; the value adopted stays PROVISIONAL.
7. **R21, the version.** SPEC-L0 v1.1 is the v1.0 file moved with `git mv` and amended: its status line records both decisions (D-0006 for v1.0, this record for v1.1), it changes no rule, records the 58 periods' evidence under R-25 and §8 Q-1 and Q-2, and adds their test module as an acceptance criterion; the rounding granularity stays NOT VERIFIED. The docstring of `src/layer0/__init__.py` names v1.0's path, which git history keeps, until the engine may next change, after the 1 November check.
8. **R22, rung 4.** R22 places rung 4 under TEST ON FIDE DATA unless Phase 1 passes, and does not name the verdict a pass would give. The reading: a pass, meaning the targeted rule and the do-no-harm check both met as E6 applied them, places rung 4 under RECOMMENDED NOW, as rung 2's pass on broadcast data placed rung 2; anything else leaves it under TEST ON FIDE DATA. The verdicts replace the "status on the data tested so far" column of the ladder in the proposal, the brief and annex T8.10.
9. **R23, the date.** The 20 October date in the ELO-4 close-out for Freeze 2 is superseded; Freeze 2 is recorded in D-0010 at the end of this session.

## Consequences

- Q1 to Q7 of the ELO-4 close-out are closed by this record; Q8 stays open; Q9 is addressed by Phase 1.
- D-0008 stands except where these rulings revise it: R1's trigger (revised by R19), R6 (revised by R16), R12's region (followed for rung 2 by R17's guard), and the v0.4 executor's additions confirmed by R20.
- Freeze 1 is untouched: `params/table_fit_2026-10.yaml`, `tools/compare_event.py` and `src/layer0/` do not change, and check (a) enforces it through the hashes printed in `docs/evidence/E3_us-championship-2026.md`. R17 is new code; Freeze 2 (R23) adds every file that produces a number in the comparison or the proposal.
- No 2026 U.S. Championship game is read, and every fit keeps the data cutoff of 2026-09-30.
