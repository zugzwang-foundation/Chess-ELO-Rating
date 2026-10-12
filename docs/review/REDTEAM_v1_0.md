# Fifth red-team review: proposal v1.0, technical annex v1.0 and brief v1.0

Status: REVIEW RECORD · Session ELO-5, Phase 5 · Date: 2026-10-10 · Reviewers: three independent subagents working in parallel, read-only, briefed as R-STAT (rating-system statistician), R-QC (Qualification Commission member and arbiter) and R-EXPLOIT (strong player seeking rating without playing better). Each read `docs/proposal/ELO-PROPOSAL_v1_0.md`, `docs/proposal/ELO-TECHNICAL-ANNEX_v1_0.md`, `docs/proposal/ELO-BRIEF_v1_0.md` and `docs/decisions/D-0009_architect-rulings-elo-5.md`, with the script `analysis/v10_calculations.py` and its output, the evidence reports their brief named (R-STAT: E2, E5 to E10; R-QC: E0 to E3, E5 to E10, the verification sweeps and SPEC-L0; R-EXPLOIT: E6, E8 to E10), the specifications and code they needed, and `docs/review/REDTEAM_v0_4.md`. Each returned at most ten findings, ranked, with severity, location and fix. The rulings R15–R23 were given as fixed; ruling-level points were to be listed separately for the architect. The three reports are reproduced below as returned, apart from one path written as plain text (it names a file that is first committed in Phase 6).

## Verification performed by the executor

Every finding was checked against its source before it was fixed; where a finding needed an analysis, the analysis was added to a committed script and run, rather than the claim reworded.

- **The blockers.** V10-EXPLOIT-1 recomputed from `analysis/aggregates/E2_broadcast.json`: at levels of 2300 or more and gaps below 400, rung 2's favourite residual is +0.0299 on 50,722 standard test games (per-game standard error 0.0015), +0.0156 in blitz and +0.0070 in rapid, where Layer 0's is −0.0187, −0.0397 and −0.0604; now printed by `analysis/e10_guard_report.py` (E10 §5). V10-STAT-1's figures confirmed from E10 §2, and the guard's edge steps and colour effect computed (script §13.1). V10-QC-1's points confirmed against E3, SPEC-COMPARE and the commit times (Freeze 1: cb192ba, 2026-10-09T19:59:46Z).
- **The simulator.** V10-STAT-2 confirmed: SPEC-SIM §3.2 drew entrants around the 2023 newcomers' medians on the scale before the March 2024 compression (1120 to 1435); moved by the compression's own formula, R + round(0.4 × (2000 − R)) [E5], they are 1472 to 1661, within 20 points of the 2025 medians [E1]. V10-STAT-5 confirmed in the code: every ledger re-forms its anchor panel each January and measured d_t and the level over the current members. Both fixed (SPEC-SIM §11, revisions 8 and 9), with the guard's 2300 read on the published rating (revision 10, V10-EXPLOIT-6); `analysis/e9_simulator_run.py` was then rerun in full (35 minutes) and reproduced byte for byte by a second run before the aggregate was committed. The rerun moved E9's numbers; the documents carry the new ones (error against true strength: Layer 0 106, rungs 2 to 6 together 92; slide at the top 9.4 a year under Layer 0, 7.6 with rung 2 and its guard; level from the first year to the tenth: Layer 0 −25, rung 6 −1, and under a junior wave −104 and −38; θ_R1 calibrated at 0.01).
- **Other figures.** V10-QC-3's ledger recomputed with the guard (unequal K +42.0227, rounding +0.2764, total +1787), exactly the reviewer's figures. V10-QC-4 checked against SPEC-L0 R-22b and R-11a; V10-QC-5 against [VT 1] (§1.3, §1.4.6 d, §1.5.3 a); V10-QC-8 against [V 3] (SK, RK, BK); V10-QC-9 against [VP 4]. V10-STAT-3 and V10-EXPLOIT-4's lever computed analytically (script §13.2: +1.35 points a decision at σ 70 in band 1700–1799); V10-QC-6's rounding test rerun (script §13.3: 11.4 % of unclipped K values differ by 0.1 when K is computed from the printed C and N_i, 1.2 % with N_i to two decimals); V10-STAT-4's history figures computed (script §13.6); V10-STAT-6's slopes (script §13.4); V10-EXPLOIT-7's windfall (script §13.5); V10-STAT-8 (b) and (c) checked against `analysis/OUTPUT_L1_history.md` and `analysis/e6_rungs_extract.py`.
- **After the fixes:** proposal body 4,435 words by the strict count, brief 897 (check (d)); every reference resolves (check (c)); every script without data reproduces its committed output (check (a)), and the slow simulator run was reproduced byte for byte by hand; 560 tests pass in CI's set (check (b)).

## Disposition

**fixed** (where); **fixed in part** (what remains, and for whom). Ruling-level points go to the architect (below); none of R15–R23 was reopened.

| ID | Sev. | Topic | Status |
|---|---|---|---|
| V10-STAT-1 | blocker | the guard's costs and cliffs unstated | fixed: (a)–(g) stated with their sizes in annex T3.6, P3 (vi), proposal §5, §8, §13 and the brief ("reads today's table without its cap … though the weaker player gains"); the edge steps and the colour effect computed (script §13.1) |
| V10-EXPLOIT-1 | blocker | farming moves below the guard: rung 2 under-predicts favourites at levels of 2300 or more at every gap | fixed in part: the by-level result published (E10 §5) and stated in annex T3.6, P4, T8.1, T8.10, proposal §1, §5, §8, §15 and the brief; a calibration rule by level band and gap pre-registered for FIDE's data, feeding rollback trigger (1) (annex T8.2); the favourite's residual by level band monitored monthly (T8.4); rung 2's verdict now carries a third condition. The guard's region is R17's: for the architect |
| V10-QC-1 | blocker | the pre-registration of §10 not tight enough | fixed in part: every blank of §10 defined in its table row (unrounded, signed, FIDE's published per-event calculation to 0.01, compensated games against opponents not eligible, those opponents' change under rung 5 minus column (b)); Freeze 1's commit time stated and the round's start time marked NOT VERIFIED; Freeze 2 in the future tense, with the check comparing against the hashes D-0010 records; §11 states that R15's and R17's rules were set after E6. The PILOT's tool, its frozen inputs, the hash list (the pilot tool, the rung-5 file and its generator, `src/layer1/`, `src/layer2/`, `tools/set_results.py`, the aggregates) and the forfeit entry are Phase 6's, recorded in D-0010; `{{US26_READING}}` is kept, with its content fixed in D-0010 |
| V10-STAT-2 | major | the simulator's entrants on the pre-2024 scale | fixed: entrants moved to today's scale (SPEC-SIM §3.2, §11 revision 8); E9 rerun and reproduced; every simulator figure restated (proposal §2, §6, §8, §13; annex T3.6, T4.3–T4.7, T8.1, T8.10, T9); E9 states that the pool's true model is E2's fitted table |
| V10-STAT-3 | major | R16: later play sets the K of games already played | fixed in part: the lever stated with its size (script §13.2) in annex T4.3, P4, proposal §5 and §15; a QC-only indicator (T8.4); the strategy added to the simulator's list (T9.4). A K fixed before the games it applies to changes reading 2: for the architect |
| V10-STAT-4 | major | θ_R1's calibration overstated | fixed: recalibrated on the rerun at 0.01 and stated with "one false alarm in 20 runs, exact 95 % upper bound 22 %", the detrended noise and paired detection labelled optimistic, the raw statistic triggering in every baseline run, the history since the reset (script §13.6), the ratchet's rate on the corrected ratio, and the pool about a twentieth of FIDE's active list (E9 §8, annex T3.5, T9.5, proposal §5). Pairing the ratio with κ at its cap: for the architect |
| V10-STAT-5 | major | d_t and the level jump at each January re-basing | fixed: both chain-linked across the re-basing in the simulator (SPEC-SIM §6, §11 revision 9) and in annex T2.4; E9 rerun: rung 6 meets R15 in 91 % of baseline months and 11 % under a junior wave, where it pays near its cap. Scoring only a widening gap (E6: rapid then passes 9 of 9): for the architect |
| V10-QC-2 | major | verdict conditions inconsistent; the brief misstates rung 2 | fixed: proposal §1, §8 (definition of RECOMMENDED NOW and three conditions), §14 (stage-1 gate), the brief (the 400-point rule only; the guard reads today's table without its cap; recommended now in standard; "unevenly by level"); annex T11 splits §8.3.1 and §7.3.1; the guarded farming region's miss on the other side stated (T3.6 (b)) |
| V10-QC-3 | major | the ledger example ignores the guard; T6 books guard effects as compensation | fixed: script §10 guarded with E⁰ guarded; annex T6 defines E⁰ so; T6 and T10.4 restated (+42.0227, +0.2764, total +1787) |
| V10-QC-4 | major | the list in force for K | fixed: annex T4.1 takes K_i and N_i from the list before the one that rates the period (SPEC-L0 R-22b) and states §1.1.4's rule for tournaments over 30 days; T4.3 reads σ_i at that list |
| V10-QC-5 | major | titles and norms: interim ratings under R16 | fixed: proposal §14 rewritten; annex T11 rows for §8.3.2 d), §1.5.3 a) and §1.4.6 d) and its closing paragraph. How an interim rating is computed: for the architect |
| V10-QC-6 | major | K not reproducible from the printed values; band ambiguous | fixed: the printed C (one decimal, in the band of the player's rating) and N_i are normative, and K is computed from them by engine and arbiter alike (annex T4.3, T7.1; script §13.3); T4.4 lists every rounding; proposal §5: "a sixth of the gap's excess", C by band |
| V10-QC-7 | major | the TRF request not actionable | fixed: proposal §9 asks for all three time controls, the monthly reports during the shadow year and the fields of §9.1 [V 1] without names; "the broadcast archive"; a row marks the TRF layout NOT VERIFIED and asks for its documentation; the precedent sentence removed from §9 and marked NOT VERIFIED where it remains (§14, annex T11) |
| V10-EXPLOIT-2 | major | collusion lasts longer under rungs 4 and 5 | fixed in part: the ten-year figures in proposal §13 and annex T9.4, T9.5; E9's T9.5 check now covers every adversary, with margins; a beneficiary monitor beside the pair monitor (T8.4); the low-K donor and a donor ring listed as not yet simulated (T9.4); thresholds for both monitors wait for FIDE's data. A cap on created points: for the architect (D11) |
| V10-EXPLOIT-3 | major | the guard pays the underdog; its edges are cliffs | fixed: (a)–(d) stated with their sizes in annex T3.6, P3 (vi), T3.2 (item 5), proposal §5 and §13 and the brief; the underdog's residual in the region by gap bin, gaps over 735 separately, monitored (T8.4). Stopping the guard at 735: for the architect |
| V10-QC-8 | major | T11 incomplete; guard and accrual wording | fixed: T11 rows for §8.1.2 (kept for the guard, which lapses on the QC's finding), §7.1.4 (rung 3's conditions), rapid and blitz §7.2.1 (starts keep today's rule, R20's share being impossible before the first game: for the architect) and §7.1.2 (N_i in SK, RK and BK [V 3]); the guard's region names RX_j (T7.1, T7.2); the accrual uses g_i (T4.8, P3, T7.1); proposal §6 states the 1400 minimum |
| V10-EXPLOIT-4 | major | R16: n chosen after results | fixed in part: as V10-STAT-3 |
| V10-STAT-6 | minor | rung 2 at today's K slows a rating's response | fixed: stated with the slopes (script §13.4) in annex T3.5; scaling K by the ratio: for the architect |
| V10-STAT-7 | minor | verdict wording overstated | fixed: (a) proposal §1 and the brief; (b) the brief; (c) "overall, not in blitz" (proposal §5, §8; annex T4.3, T8.1); (d) "as much without the guard" (proposal §8, §13; annex T3.6) |
| V10-STAT-8 | minor | units and labels | fixed: (a) latent points (proposal §2(b), annex T2.3a); (b) the corrected ratio (proposal §5, annex T3.5); (c) E10's description of the draw split |
| V10-EXPLOIT-5 | minor | "farming under rungs 3, 4, 6 alone" misread | fixed: E9 §7 prints the farmers' and the controls' changes and drops the misreading; annex T4.3, T9.4 and proposal §8: rung 4 alone deepens the slide at the top (11.6 a year against 9.4), to be adopted with rung 2 |
| V10-EXPLOIT-6 | minor | compensation and the guard; the code passed RX for the 2300 test | fixed in part: the favourite's 2300 read on its published rating in `src/layer2/guard.py` (with a test), the simulator and the PILOT tool, as reading 4 states; annex T6 guards E⁰; the guard's region names RX_j (T7). Testing the region once per game on the published gap would change reading 4: for the architect |
| V10-EXPLOIT-7 | minor | inactivity protection survives every rung; accrual after the last game | fixed: proposal Appendix B (A7); E9 prints the protector's range over seeds; the windfall stated in annex T4.5 (script §13.5); players stopping within three months of their peak monitored (T8.4). Ending accrual sooner: for the architect |
| V10-QC-9 | minor | Bryson details beyond [VP 4]; precedent unverified | fixed: proposal §2(b) and annex T4.6 keep only what [VP 4] supports; the precedent marked NOT VERIFIED (§14, annex T11) and removed from §9 |

## For the architect

Consolidated from the three reports, with the executor's evidence beside each; none is decided here.

1. **R17's region** (R-STAT 1, R-QC 1, R-EXPLOIT 1 and 2; V10-EXPLOIT-6). The under-prediction is tied to the level (rung 2's favourite residual +0.030 at levels of 2300 or more below a 400-point gap, E10 §5), while 4,674 of the guard's 5,501 standard games lie below level 2300, where the table had no measured problem. Should the guard be keyed on level, blended at its edges, stopped at a 735-point gap, kept to standard and blitz, or tested once per game on the published gap?
2. **R16** (R-STAT 2, R-EXPLOIT 3, R-QC 2). One K per period fixed when the period closes lets later play set the K of games already played (+1.35 points a decision at σ 70, script §13.2). Fix K per event or from the previous period? Bound n·K(n) by max(C, 700) beyond the K_min clip?
3. **Interim ratings for titles under rung 4** (R-QC 3): K for the games played so far? Is a posted adjustment included? R or R + B?
4. **Rapid and blitz starts from a standard rating** (R-QC 4): exempt them from R20's information share? Until then they keep today's rule (annex T4.7).
5. **Rung 1's verdict** (R-QC 5): subject to the 1 November check, with three periods unexplained?
6. **Collusion** (R-EXPLOIT 4): with rungs 4 and 5, collusion creates 1.6 to 3.1 points per arranged game over ten years against today's 0.8 (E9 §7). Cap created points per pair or per beneficiary (D11)?
7. **R15 and the controller** (R-STAT 3): score only a widening gap (E6: rapid 9 of 9)? Faster constants or a larger a_cap, given 11 % under a simulated junior wave?
8. **R19** (R-STAT 4): pair the spread ratio with κ sitting at its annual cap, since the raw ratio trips in every simulated baseline run and drifts on history?
9. **Rung 2 at today's K** (R-STAT 5): scale K by the ratio of table 8.1.2's slope to the fitted table's, 14 % to 53 % by level (script §13.4)?
10. **Accrual after the last game** (V10-EXPLOIT-7): end accrual a few months after the last rated game?

---

## The reviewers' reports (verbatim)

### R-STAT

#### Findings

**V10-STAT-1 — blocker — The proposal recommends the guard without its costs or its cliffs.** Location: proposal §5 "The farming guard", §8 rung 2 row, §13 "No exploitable cliffs"; brief step 2; annex T3.6, T5 P3 (vi). (a) Most of the guard's region has no measured problem: in standard 4,674 of its 5,501 games are below level 2300, where rung 2 without the guard is +0.005 (inside ±0.01); the guard makes it −0.032. (b) Across the whole region favourites score below the guarded expectation by 0.030/0.097/0.045 (standard/rapid/blitz), against +0.004/−0.057/−0.001 under Layer 0; rapid's farming region goes from +0.008 to −0.092 [E10 §2]. §5 quotes only −0.021 and −0.030. (c) By R12's own test the guarded table now misses ±0.01 on the other side (standard month blocks −0.027 to −0.012). (d) In the simulator the guard gives back half of rung 2's gain at the top: the top slides 4.5 a year with it, 2.7 without [E9 §4]. (e) The brief says the guard "keeps today's full table"; today, standard favourites rated 2300–2649 read the capped table, as does everyone in rapid and blitz. (f) The edges are cliffs (computed with `src/layer2/table.py` and `guard.py`): from gap 399 to 400 the favourite's E rises by 0.021–0.090 in standard, 0.075–0.147 rapid, 0.056–0.099 blitz; at the 2300 edge by up to 0.057; an underdog with K 40 gains up to 3.6 points a game, so P3 (vi)'s "None can be straddled for gain" is false. (g) The guard ignores colour: at gap 400 it gives 0.92 with either colour, where the fitted table gives 0.899 (White) and 0.856 (Black). Calibration below a gap of 400 is unchanged. **Fix:** state (a), (b), (d), (e) in §5, §8 and the brief; in the brief the guard reads today's table "without its cap, as players rated 2650 or more do"; print the step sizes and the colour effect in T3.6 and P3.

**V10-STAT-2 — major — The simulator's entrants are on the scale before the March 2024 compression.** Location: SPEC-SIM §3.2; E9 §2–§4; proposal §2(a), §6, §8; annex T4.5, T4.7, T8.10, T9.5. Entrants' true strengths are 2023's median first ratings (1120–1435), before FIDE added 0.40 × (2000 − R) to every rating below 2000 in March 2024 [E1] [E5]; the rest of the pool is on today's scale. Transformed, the 2023 medians come within 20 points of 2025's in every age group [E1]. Rerun of E9's baseline with the transformed medians (committed code, three seeds; reruns without the transform reproduce E9): E9 §2's age medians move closer to FIDE's in all five groups (ages 25–45: −2.3 against FIDE's −3; committed +0.2); error against true strength Layer 0 141 → 106, rung 3 98 → 93, rungs 2–6 88 → 87; ten-year level drift Layer 0 +22 → −31, rung 3 −43 → −81, rung 6 −2 → −13. §2(a)'s "without being tuned to it" omits that the simulated truth is E2's table; the slide under table 8.1.2 follows from that assumption. **Fix:** rerun E9 on today's scale (or report both); restate the level and error figures; describe the pool as one "whose true model is the fitted table".

**V10-STAT-3 — major — Under reading 2, R16 rewards stopping after good results.** Location: D-0009 reading 2; annex T4.3 ("never on their sign"), T5 P4; proposal §5. All games of a period use K(n), so a later decision to play sets the K of games already played. Level 1700, σ = 70 (C = 852.8, N = 36.6): K 20.5 after a 5-game event; a further 9-game event makes K(14) = 16.9 for all 14 games. A correctly rated player who stops after a positive residual and plays on after a negative one gains (20.5 − 16.9) × 0.366 ≈ +1.3 per decision, +3.1 with 30 more games. P4's "the only way to gain is to score more than the calibrated expectation" therefore fails; today's K changes with n only at 17–70 games. **Fix:** set K before the games it applies to — per event (cumulatively, restating P2) or from the previous period's n — or disclose and monitor.

**V10-STAT-4 — major — θ_R1's calibration supports neither "at most 5 % false alarms" nor the ratchet figures.** Location: proposal §5 "The spread"; annex T3.5; E9 §8; script §12. (a) 0 of 20 runs: exact 95 % upper bound 14 %. (b) The false-alarm count first removes each run's fitted trend; the raw statistic the QC would watch trips in all 20 baseline runs, median 19 months. (c) Detection is measured on the noise-free paired difference. (d) T3.5 says a ratchet moves the ratio 0.031 a year; E9's response reaches 0.025 only after 57 months, by which κ has fallen from 1.212 to 0.962. (e) On history the corrected standard ratio fell from 0.743 to 0.713 (2024-12 to 2026-08); its trailing mean drifts from its post-reset reference by 0.0017 a month and at that pace trips in 2027 with no ratchet (`L1_history.json`). (f) The simulated active pool is about a twentieth of FIDE's, not a tenth. **Fix:** state "0 of 20, 95 % bound 14 %, on detrended noise"; replace 0.031 with E9's response; calibrate on the raw statistic, with noise.

**V10-STAT-5 — major — E9's d_t and "level" jump every January, when the anchor panel is re-formed.** Location: annex T2.4 ("membership churn does not bias it"), T4.5; E9 §4, §6; proposal §6, §8 rung 6. In three reruns Layer 0's d_t jumps −2.5 to −3.1 each January (±0.3 otherwise); these jumps are most of the "−35 points" E9 credits to the proxy's latent level; without them Layer 0's R15 share rises from 0.12–0.31 to 0.54–0.64. The level series jumps too (two seeds): Layer 0's January jumps give +8 of +11 and +14 of +29; rung 3 −21 of −52 and −18 of −37; rung 6's January jumps of +5 and +11 offset −11 and −9 from the other months. So "rung 6 holds the level" and its 59 % R15 share partly measure who is in the panel. Reading 1 also counts a closing gap as a failure: rapid's only failing month is |d_t| falling from 2.9 to 0.6; scored on the growth of |d_t|, rapid passes 9 of 9 (recomputed from `E6_rungs.json`). **Fix:** chain-link d_t across re-basings, measure the level on a panel fixed at adoption, rerun E9 §4 and §6.

**V10-STAT-6 — minor — Rung 2 at today's K makes ratings respond more slowly; untested and unstated.** Location: proposal §8; annex T3.5, T9.5. Each game corrects a rating error at a rate of K·E′(0). Table 8.1.2's slope near zero is 0.00140; the fitted table's is 0.00117 (1700), 0.00086 (2300), 0.00065 (2700): each game corrects 16 %, 39 %, 54 % less. E2 and E10 test static forecasts and cannot see it; E9 shows it (the inactivity protector +59 a year after return against +39 under Layer 0; adults 2000–2399 −0.052 against juniors, against −0.049). **Fix:** state the effect; test rung 2 with ratings carried forward.

**V10-STAT-7 — minor — The verdict wording overstates.** Location: proposal §1, §5, §8; brief. (a) The guarded rung 2 passes its gate only in standard [E10]; §1 and the brief omit it. (b) The brief's "passes its calibration tests" is true only of the unguarded table. (c) "No longer harms forecasts" is false in blitz: +0.00255 (+0.00062 to +0.00462) [E8]. (d) The simulator's 0.245 → 0.050 is credited to the guard; without the guard it is 0.049.

**V10-STAT-8 — minor — Units and labels.** (a) "+193" and "+79" are latent points; on the published scale 159 and 65. (b) §5 and T3.5 quote the raw spread ratio (0.794 → 0.747); the rule uses the corrected one (0.773 → 0.714). (c) E10 §6 says the fitted draw probability is kept; `three_way` truncates P_D to 2(1 − E) − 0.002, which inflates the guard's cost.

#### For the architect

1. R17's region is defined by the favourite's rating, but the problem was measured by level (827 of the 5,501 standard games). A region by level, or today's capped reading below 2650, would remove most of the cost; a blended edge would remove the cliffs.
2. R16: later play sets the K of games already played. Consider K per event, or from the previous period.
3. R15 with a 2-point deadband fails during the transient of any drift above 2 points a year and penalises a closing gap. Consider scoring the growth of |d_t|.
4. R19: the spread ratio cannot tell a κ ratchet from compression. Pair it with κ sitting at its annual cap.
5. Rung 2 at today's K roughly halves responsiveness at the top. Consider scaling K by E′₈.₁.₂(0)/E′_fit(0) per band.

#### Checked and correct

R16 (T4.3): the derivation is the batch linear-Gaussian update, and C/(N + n) is the same rule; C 852.8 (1700), 1163.5 (2300), 1544.9 (2700) (765.6 lowest band, 1673.9 highest); the P2 bound max(C, 10n), 71 games, K(30) = 25.9 with 777, the steady-state K, σ 55 → 90.6, N 64.9 → σ 55.0. E6's R15 rescoring, recomputed: 5, 8, 0 of 9 months; largest 3.76, 2.27, 3.9; steady state 2 + 6 × drift (9.8, or 9.5 on the grid). E10: 2.9, 4.8, 6.8 %; costs 0.0019, 0.0111, 0.0054; stage-1 outcomes; 2649 and 2651 both at 0.94. E2 and E5: 352,737 games; 0.022–0.054, 0.096, 0.073; 0.14 and 0.17 against 0.09 and 0.13; 242 → 150; 2113 against 1734. E6, E7, E8: 0.055 → 0.018, 0.047 → 0.010; 17/18, 21/22, 22/22; +0.00042, 13.3, 30.3, 23.7. E9 as committed: every figure quoted. Script: T3.4; band steps; 481.2, 649.3, 855.6; colour; T10.1–T10.4 (197, 1.9599, +1787); 718 and 702; seed σ̃.

The reruns used the committed `src/simulator` and `src/layer2`, driven by scratch scripts in the session scratchpad; nothing in the repository was changed.

### R-QC

#### Findings

**V10-QC-1 — blocker — proposal §10, §11; E3; SPEC-COMPARE §2.** Nothing frozen computes the PILOT blanks: SPEC-COMPARE §2 refuses `--rung5 on` and E3 says "Layer 1 does not exist yet"; at b6b1f2c nothing computes `{{US26_*_R5_*}}`, and the PILOT's inputs (which Layer 1 fit, anchor and κ for θ̃; broadcast-only gate counts; whether the guard reads the compensated gap — it can bind there: 250 gap + c_j ≤ 300) are unstated. Ambiguous blanks: "largest (b) − (a)" signed or by magnitude (+6.62 vs −7.00 on 2025's numbers); mean and opponents' total rounded or not; "(a) equal to FIDE's changes" per event or per period (R-11b; R-25 NOT VERIFIED), and what if FIDE rates in December. `{{US26_READING}}` is post-hoc free text. The check fails only "until the page is regenerated" (E3), so a change committed with a regenerated E3 passes. Freeze 2 is described in the past tense; D-0010 does not exist. Round 1's start time is unrecorded, so Freeze 1 (19:59:46 UTC, cb192ba) vs play is unknown. §11's "fixed before the tests were run" is false for R15/R17 (set after E6). `set_results.py` cannot enter a forfeit (§5.1). **Fix:** in §10's table rows (outside the cap) define "mean |(b) − (a)|, unrounded"; "largest |(b) − (a)|, signed"; "PILOT games: c_j > 0 v non-eligible"; "PILOT: Σ K_i(E_b − E_p), unrounded, guarded on the compensated gap"; "(a): K × ΣΔ = FIDE's per-event value to 0.01, and the period change = the list's". Drop `{{US26_READING}}` or fix its template in D-0010. D-0010: hash the pilot tool, its rung-5 file and generator, src/layer1, src/layer2, `L1_history.json`, the 2026 validation script, set_results.py; record the commit SHA, both freeze times and round 1's start; make check (a) compare against D-0010; state that forfeits are entered as "-". §10 prose (+7): "made at a stated UTC time …, listed in D-0010 at a stated commit"; "the check fails if any differs from the hashes D-0010 records". §11 (+12): "…except rung 6's (R15) and rung 2's guard (R17), set after [E6]".

**V10-QC-2 — major — proposal §1, §8, §14; brief; T11 §8.3.1 row.** The verdicts agree across the documents (R22); their conditions do not. §1 and the brief recommend rung 2 now with no conditions. The brief: "The 400- and 600-point special rules go" (the 600-point rule is rapid/blitz only, where rung 2 fails E10); the guard "keeps today's full table" (for favourites rated 2300–2649 it is stricter than today); "needs tuning by level" contradicts R18. "Full gate in standard" omits the farming region, which T8.1 includes: guarded −0.0205 (month blocks −0.0268 to −0.0122), outside ±0.01. §8's "passed their pre-registered test" fits neither rung 1 nor rung 2 in rapid/blitz. §14's stage-1 gate needs FIDE's data, which arrive only at stage 2. **Fix:** §1 (+11): "…guarded where farming pays, in standard; rapid and blitz after a re-test on FIDE's games." §8 (+2): "for rungs whose tests support adoption now, under the conditions stated below"; rung-2 cell: add "the guard over-predicts farming-region favourites (−0.021)". §14 gate: "in standard; rapid and blitz in stage 2". T11: split the row by time control. Brief (net −1): "the 400-point rule goes … a temporary guard reads today's table without its cap … *Recommended now in standard; rapid and blitz after a test on FIDE's games.*"; "unevenly by level"; cut "The FIDE rating is chess's common currency." and "Online games are not evidence."

**V10-QC-3 — major — annex T6, T10.4; script §10.** Game 7 (P5 2300 v P1 1900, gap 400) sits on both inclusive edges of the guard, which T10 says applies, yet uses the unguarded 0.899; guarded it is 0.92 (terms +0.8000/−1.0960, rounding +0.2764; total still +1787). T6's E_i⁰ is unguarded, so with unequal K every guarded game books (K_i − K_j)(E⁰ − E_g) as "created by junior compensation" even with rung 5 off: a 2600 (K 10) drawing a 2100 (K 20) books +0.28. **Fix:** define E_i⁰ as "without compensation, guarded where T3.6 applies" (the unequal-K line then reads +42.0227); apply `guard_E` in script §10 and redo T10.4.

**V10-QC-4 — major — annex T4.1 (T4.3, T4.4).** T4.1 takes "every input throughout (R, K_i, RX_j, the table and η_tc)" from the list in force at the tournament's start. It drops the exception it cites: §1.4.6 a) [VT 1] reads "(see exception 1.1.4)", the over-30-day rule SPEC-L0 R-11a keeps. It contradicts R-22b ("the K published on list t − 1"; in fixture F-P05 one K covers events started in August and in September). Under R16 it breaks one K per period: 8 of SPEC-L0's 13 discriminating periods would get several N_i, against "the same K for every game of the period". **Fix:** "…(R, RX_j, the table, η_tc); a tournament over 30 days uses each game's list (R-11a; §1.1.4 [VT 1]); K_i and N_i come from the list before the one rating the period (R-22b)."

**V10-QC-5 — major — proposal §14; annex T11 closing.** "Nothing here touches the title and norm regulations" overstates. R16 changes interim ratings: titles accept ratings "obtained in the middle of a rating period", disregarding "subsequent results" (§1.3, §1.5.3 a) [VT 1]), and under R16 later games cut the K of earlier games in the same period. Example (σ 90, N_i 30.2): a 2380 scoring +0.75 in nine games is 2402.2 with K(9) = 29.6; a second nine-game event in the period gives K(18) = 24.1 and the same point is 2398.1. Per-tournament changes become provisional until the period closes (§8.3.2 c–d). Unaddressed: whether A_i enters an interim rating, and R versus R + B for titles. Rung 3's σ̃ gate leaves more opponents unrated, so more count at 1400 (§1.4.6 d). **Fix:** §14 (+6): "The title and norm regulations keep their text: … with the published R, never RX; but under rung 4 an interim rating (§1.5.3 a) [VT 1]) depends on the period's later games, a rule the QC must set [T11]." Add T11 rows for §1.5.3 a), §8.3.2 c–d and §1.4.6 d).

**V10-QC-6 — major — proposal §5; annex T1, T4.3, T4.4, T4.9; reading 3.** An arbiter cannot reproduce K: the engine (`k_printed` in src/layer2/kactivity.py; the script's `K_n`) rounds K from σ_i, while the arbiter has C and N_i to one decimal. Measured over σ 40–130, n 1–40 and all bands: 11.8 % of unclipped K values differ by 0.1, changing 1.7 % of rounded period changes; printing N_i to two decimals still leaves 1.3 %. The band is ambiguous: T1's L is the game's level and §5 says "853 at level 1700", but N_i uses the player's own band (T10.1 player A at n = 9: 12.6 against 11.5). T4.4's "no other rounding anywhere in Layer 2" is false. §5's "a sixth of the gap" is wrong (1.2 at d_t = 7.2; T4.5 gives 0.87). **Fix:** make the printed values normative: K = clip(C/(N_i + n)), half up to one decimal, C in the band of R_i, and the engine computes it the same way; T4.4 lists each grid's rounding; §5 (+1): "(853 for players rated 1700–1799, 1164 for 2300–2399)", "a sixth of the excess".

**V10-QC-7 — major — proposal §9.** FIDE cannot act on the request as written. It asks for the archive only, though the shadow list also needs each month's reports; rapid and blitz are not named; no data fields are given. The TRF layout is not transcribed (SPEC-L0 §8 Q-6), so "hold every rated game" and "host federation" are unverified; §9.1 [V 1] gives only the uploading federation. "The archive records no host federation" refers to the broadcast archive, not FIDE's. The precedent sentence rests on [R 16], NOT VERIFIED. **Fix (+4):** delete the precedent sentence; in the bold ask add "in all three time controls" and "each month's reports during the shadow year"; after the colon add "FIDE IDs, dates, rounds, colours, results and the uploading federation (§9.1 [V 1]), without names", then "analysed on FIDE's terms, never redistributed, aggregates only"; add a table row "TRF layout | NOT VERIFIED; documentation requested".

**V10-QC-8 — major — annex T11, T3.6, T4.8, T5 P3, T7.1; proposal §6.** §8.1.2 is marked "replaced" though the guard reads its H column. Rapid/blitz §7.2.1 is marked "kept" though rung 3 changes it, and R20's share gate would block every such start (share zero before any rapid game). §7.1.4 is marked "do not change" though rung 3 adds conditions (residue of V4-QC-5). §7.1.2's K column becomes N_i, changing the SK/RK/BK fields [V 3]. "The guard covers their region" is wrong for favourites below 2300. The `guard.region` text omits RX_j. T4.8, P3 and T7.1 use n_i for the accrual where T1 and T4.5 use g_i (residue of V4-QC-3). §6's "Today" cell omits the 1400 minimum. **Fix:** T11 rows "§8.1.2 retained for the guard until it lapses (state who lifts it)", "rapid/blitz §7.2.1 amended; seed gates exempt", "§7.1.4 gains rung 3's conditions", "§7.1.2: K field holds N_i"; add RX_j to `guard.region`; replace n_i with g_i in the accrual.

**V10-QC-9 — minor — proposal §2(b); annex T4.6; precedent in §9, §14, T11.** [VP 4] supports only "add points to juniors' ratings … as Chess Scotland does (Bryson)"; "IM", "since 1976", "age-dependent", "grade" and "by age" are not transcribed. The parallel-list precedent rests on [R 16], NOT VERIFIED. **Fix:** transcribe Bryson's comment into VP 4, or (−9) "By Bryson's account in FIDE's 2023 consultation, Chess Scotland adds points to a junior's rating when computing the opponent's expected score"; verify the precedent or mark it NOT VERIFIED.

Net effect of all fixes: proposal body +34 words (4,498); brief −1 (898).

#### For the architect

1. R17's scope (E10): rapid's farming region scores +0.008 unguarded and −0.092 guarded; 4,674 of the 5,501 guarded standard games lie below level 2300, at +0.005 unguarded and −0.032 guarded. Apply the guard only at level ≥ 2300, and only in standard and blitz?
2. R16's K_min clip lets a period's change exceed 700 without bound past 70 games (only 10n bounds it); blitz can reach that [V 2]. Cap n·K(n) at max(C, 700)?
3. Interim ratings: use K(m) for the games played so far? Exclude A_i? Count R or R + B?
4. Rapid/blitz §7.2.1: exempt those starts from R20's share gate?
5. Rung 1: make RECOMMENDED NOW subject to the 1 November check, given three unexplained periods and Q-1 still open?

#### Checked and correct

FIDE rules, all correct: the quotes of §8.3.1, §8.3.2 b, the 700 sentence, §8.2.4, §7.1.4 and §8.1; the paraphrases of §7.2.1–7.2.2, §8.2, §8.3.3–8.3.4 and §9.1; the rapid/blitz rules and their numbering; the table readings and the 2650 cliff. Norms: table 1.4.9 equals table 8.1.1, and table 8.1.2 is not used [VT 1, 3]. Also correct: the verdict lists, identical across the documents; the guard, matching reading 4; E3's guard-region check; the numbers spot-checked; status lines; the "Elo" spelling; the word counts.

### R-EXPLOIT

#### Findings

Ranked by value to the attacker. "Computed" means rerun from the committed aggregates (`analysis/aggregates/E2_broadcast.json`, `E9_simulator.json`, `E10_guard.json`) or with `src/layer2`.

**V10-EXPLOIT-1 — blocker — Farming moves below the guard.** Location: annex T3.6, T5 P4, T8.2, T8.4; proposal §1, §3 (row 8), §5; brief step 2; E2, E10. E2's held-out by-level results are computed but never reported: at level ≥ 2300 rung 2 under-predicts the higher-rated player at every gap. In standard the favourite beats the table by +0.030 (per-game SE 0.0015) on the 50,722 test games below a 400 gap — the size of E6's farming region (+0.032, 827 games); by band +0.030, +0.036, +0.024, +0.018 (2300s to 2600s); blitz +0.016; Layer 0 on the same games −0.019. T8.2 pools its gap bins over levels, so the lower levels (−0.005 to −0.010) hide it. The guard is aimed at the wrong games: 85 % of its standard games (4,674 of 5,501, level < 2300) were within ±0.01 without it (+0.005, E10), and 98 % of the under-predicted games lie outside it. The attack: a 2300+ player picks events as the higher-rated, opponents 100–399 below, avoiding gaps of 400+ (where the guard now costs −0.030). Yield +0.30 a game at K 10, +0.60 at K 20, +0.40 at rung 4's elite median K 13.3: the gain R17 removed (+0.32, E10), in 60 times as many games. 40 such games a year: +12 at K 10, where today the same games cost −7.5. The documents claim the guard makes farming lose ("farming does not pay"). **Fix:** report the residual by level band (E2, E10, T3.6, P4); pre-register for FIDE's data (T8.8) calibration rule (a) per 100-point level band × 50-point gap cell, feeding rollback trigger (1); publish the favourite's residual by level band monthly (T8.4). Proposal §5, word-neutral: replace "A 2600 then expects 0.96 … (script §8) [T3]." (30 words) with "At levels of 2300 or more the table under-predicts favourites at every gap, +0.030 below 400 in standard, beyond the guard; it is monitored by level [E2] [T8]." Brief: "so farming far weaker fields does not pay".

**V10-EXPLOIT-2 — major — Collusion lasts longer under rungs 4 and 5; only monitoring stands against it.** Location: proposal §13; annex T6, T9.4, T9.5; E9 §7. Each arranged game creates +9.1 points in year one under Layer 0 (E9), of which the junior keeps K_j/(K_j − K_a) (4/3 at K 40 and 10): about +290 a year at 24 games. E9's all-years figures show the design keeps creating: 0.9 a game under Layer 0 and rung 2, 2.0 under rung 4, 1.6 under rung 5, 3.1 under rungs 2–6 — about 210 against 740 points per pair over ten years, because rung 4 has no K switch at 2300 or age 18. T9.5 says the adversary check fails for farming only; it also fails for collusion under rungs 4, 5 and 2–6. §13 and T9.4 quote year one only. R16 lets a donor cut his own K for the arranged games by playing more that month (σ 55, level 1700: K(2) 13.9 → K(32) 10.0), so a club donor gets the elite donor's 4:1 leverage. The pair monitor has no threshold and was not run on E9's pairs; a ring (several donors, few games each) hides in the noise of honest pairs (SD about 13 points a game). **Fix:** put the all-years figures in §13, T9.4 and T9.5. §13: replace "under today's rules and under every rung, and show in the ledger's per-event lines" with "under every ledger, over three times today's over ten years with rungs 2 to 6; the ledger shows, not stops, them", and cut "and the engine flags, it does not judge". Add a beneficiary monitor (line-2 creation per player, summed over all opponents, twelve months); state thresholds and test both monitors in the simulator on E9's pairs, a donor ring and the R16 low-K donor.

**V10-EXPLOIT-3 — major — The guard pays the underdog; its edges are cliffs.** Location: annex T3.2 (item 5), T3.6, T5 P3 (vi); brief step 2. (a) In the guard's region the underdog scores above its expectation by 0.030/0.097/0.045 in standard/rapid/blitz (E10), against −0.004/+0.057/+0.001 under today's rules: +0.6/+1.9/+0.9 a game at K 20, double at K 40. (b) Above 735 points the underdog's expectation is exactly 0.00, while favourites at gaps of 750+ score 0.952–0.974 (E2): the underdog banks K × 0.03–0.05 a game with no risk, contradicting T3.2's "no result is ever worth exactly nothing". In rapid and blitz, deleting the 600-point exclusion turns today's unrated elite pairings into such games. (c) Edges (computed): one rating point at gap 400 moves a Black favourite from 0.855 to 0.920. A favourite listed at 2300 rather than 2299 (gap 420, Black) steps up +0.054 in standard, +0.108 rapid, +0.081 blitz: 1.1/2.2/1.6 a game at K 20. Players near 2300 will meet weak fields only while listed below it. (d) Colour is unpriced inside the region: an extra White pays again (0.044 at gap 400). P3 (vi) says the edges cannot be straddled for gain; the underdog gains by straddling the gap edge, and the favourite by staying below 2300. **Fix:** state (a)–(d), with sizes, in T3.6, P3 (vi) and the brief ("…does not pay, though the weaker player gains"); add to T8.4 the underdog's residual by gap bin, gaps over 735 separately.

**V10-EXPLOIT-4 — major — R16: n is chosen after the results.** Location: annex T1 (n_i), T4.3, T4.4, T5 P3–P4; D-0009 reading 2; proposal §5, §15 Q5. One K_i(n) covers every game of the period and n is fixed only when it closes: after a bad event a player adds games that month, lowering K for the bad games too; after a good event he stops. Simulated (correctly rated player, level 1700, a 5-game event, a second event only after a negative result; 200,000 months): gain per use +0.36 at σ 55 (K 13), +0.82 at σ 70 (K 20), +1.82 at σ 90 (K 31); with a 9-game second event +0.60/+1.35/+2.89. E8's typical club adult (K(1) 30.3) gains about +1.3 per use; used monthly, 4–35 points a year. Report timing is a second lever (R-09, R-10: an event can be rated on any of three lists). Batching a year's games into one month cuts the year's K-weight by 14–24 % (computed), keeping a declining senior about 11 points higher. The printed N_i lets the player compute every choice exactly. T4.3 and P4 say K depends on results "never on their sign". **Fix:** state the lever and its size in T4.3, P3, P4; §15 Q5 (word-neutral): "Is R16 acceptable? Its period bound passes 700 (853 at level 1700, 1545 at 2700), and n is chosen after results (T4.3): for the QC."; tighten reading 2: an event counts in the n of the period in which it ended, whichever list rates it; add a QC-only indicator of games added after a below-expectation event in the same period; add this dilution strategy to T9.4.

**V10-EXPLOIT-5 — minor — "Farming under rungs 3, 4, 6 alone" is misread.** Location: annex T4.3, T9.4, T9.5; E9 §7; proposal §8 (rung 4 row). Computed from E9: the farmer's own excess barely moves (+0.106 a game under Layer 0; +0.108, +0.104, +0.088 under rungs 4 activity, 6, 3); what changes is that ordinary strong players lose more (−0.139 → −0.182, −0.180, −0.171). Alone, these rungs deepen table 8.1.2's drain: the slide at the top is −7.5, −8.9, −7.5 a year against −6.1. "Let a farmer keep more" is the wrong reading; the right conclusion is an adoption dependency, like rung 3's on rung 6. **Fix:** correct T4.3, E9 §7, T9.5; §8 rung 4 row: "…; alone it deepens the slide at the top (−7.5 a year against −6.1): adopt with rung 2 [E9]", paid for by shortening §8's "on a model proxy that knows the pool's average dynamics, an optimistic assumption" to "on an optimistic model proxy".

**V10-EXPLOIT-6 — minor — Compensation switches the guard off for one side only.** Location: annex T3.6, T6; D-0009 reading 4; `src/simulator/ledger.py`; tools/compare_pilot.py (untracked in the working tree, not mine). The adult's region is tested on R − RX_j, the junior's on the published gap. Computed: adult 2400 v junior 1950, c = 100: the adult's expectation falls from 0.94 to 0.871 (White) or 0.818 (Black), of which 0.017/0.053 is the guard switching off, while the junior stays guarded at 0.06. A 2300+ adult who seeks compensated juniors at published gaps of 400+ swaps the guard's −0.030 (E10) for rung 5's +0.034 at 2400+ (E6). T6 does not say whether E⁰ is guarded, so guard effects land in ledger line 3, which feeds the a_cap test (T8.9 trigger 4). Reading 4 tests "rated 2300 or more" on the published R; the code passes RX. **Fix:** tighten reading 4: test the region once per game on the published gap and read each side's guarded value at the gap it uses; define E⁰ in T6 as the guarded expectation without compensation; align the code on R.

**V10-EXPLOIT-7 — minor — Inactivity protection survives every rung.** Location: proposal Appendix B (A7); annex T4.5, T8.4, T9.4. E9's protector returns 76–83 points above strength under every ledger; rung 4 only speeds the correction after return, yet Appendix B counts inactivity as handled. The "a year later" means (+39/+59/+15) range from −19 to +94 across seeds (computed) and are printed without ranges. Rung 6 adds a windfall: accrual counts the games on the trailing twelve lists, so a player who stops after a busy year keeps accruing up to 11 more months — up to 16.5 points at a_cap, posted on return, for a drain he no longer pays. T8.4's return monitor flags only over-performance. **Fix:** Appendix B: rung 4 eases protection after return, nothing prevents it; print E9's seed ranges; state the windfall in T4.5, or read R3 so accrual stops three months after the last rated game; publish, without names, how many players stop within three months of their peak rating.

#### For the architect

1. R17 ties the guard to a 400-point gap and a 2300 favourite, but the evidence ties the under-prediction to level ≥ 2300 at every gap (V10-EXPLOIT-1): give the table a level-dependent slope, or key the guard on level rather than gap?
2. R17's "table 8.1.2 without the cap" restores an exact 1.0 above 735 (V10-EXPLOIT-3b): stop the guard at 735, or keep the fitted value there?
3. R16 as read gives a period one K fixed only at its close (V10-EXPLOIT-4). An order-dependent n (each event counts the period's games up to its own end) removes the lever but lifts a 30-game newcomer's period bound from 777 to 1,030–1,070: change the reading, or accept and monitor?
4. D11 (no cap on the ratio of K factors): with rungs 4 and 5, collusion creates 1.8–3.4 times today's points over ten years (V10-EXPLOIT-2): cap line-2 creation per pair or per beneficiary per year?

#### Checked and closed

Farming at gaps of 350–399 pooled over levels: −0.006/−0.009/+0.008 (E10). A favourite entering the guard's region gains nothing; the 2650 cliff is gone (script §8); colour outside the guard is priced by η. Two eligible juniors: R8 makes their expectations sum to one. Seeds and re-entry published only from θ̃ ≥ 1400. Compensation hunter: stated and monitored (R18). Compensation and seeds boosted through blitz: closed by the information shares (R5, R20). Minimum-activity collector: 0.52 a year under R3. Knowing a_t early is worthless. Posting the balance when it suits: capped at 12 · a_cap and visible in R + B. Sandbagging: no ledger rewards the dip (E9). K raised by playing weak opponents: the activity record counts games only. R16's period bound above 700 is no lever by itself (stated, §15 Q5). N_i's disclosure is accepted (R4). Federation shopping: stated (P4), monitored by the QC.

---

## Addendum: session ELO-6, Phase 5 — rung 2 v2, the narrowed guard and §10

Status: REVIEW RECORD · Session ELO-6, Phase 5 · Date: 2026-10-10 · Reviewer: one subagent, read-only, briefed with the R-STAT and R-EXPLOIT briefs together, after Freeze 3 and with the documents folded for ELO-6. As the brief orders, it read only rung 2 (the table calibrated by level, with today's K times R32's m), the narrowed guard and the proposal's §10: `docs/proposal/ELO-PROPOSAL_v1_0.md` (§1, §2(a), §5, §8, §10, §11, §13, §15 Q1) and `docs/proposal/ELO-TECHNICAL-ANNEX_v1_0.md` (T3, T5 P2–P4, T8.1, T8.2, T8.10, T10.2, T11), with `docs/decisions/D-0011_rulings-and-freeze-3.md` (the rulings R24–R42 given as fixed; ruling-level points to be listed separately), `docs/decisions/D-0010_freeze-2.md`, the evidence reports E2, E10, E11, E12 and E13 with their aggregates, `docs/specs/SPEC-TABLE-FIT_v1_1.md`, `src/layer2/table_v2.py`, `src/layer2/guard_v2.py`, the two v2 parameter files, `tools/compare_event_v3.py`, `analysis/e13_us_championships_freeze3.py`, `analysis/elo6_calculations.py` with its output, and this file. It returned ten findings, ranked, with severity, location and fix; the report is reproduced verbatim below, after what the executor did with it.

### Verification performed by the executor

- **Every finding was checked against its source, and every number the documents now cite is printed by a committed script.** A new evidence page, E16 (`docs/evidence/E16_rung2-under-review.md`, from `analysis/e16_rung2_review_report.py`), reads the aggregates of E2, E11 and E12 unchanged, runs `tools/compare_event_v3.py` unchanged on the 2025 event and simulates title thresholds; `analysis/e16_post_compression_extract.py` refits the v2 table on games after the March 2024 compression (E16 §5); `analysis/elo6_calculations.py` §8–§9 prints the colour figures and the stake of one game under K × m. Where its setup is the reviewer's, E16 reproduces the reviewer's figures: the residuals and yields of ELO6-EXPLOIT-1 (+0.0179 and +0.0170; +0.25, +0.47), the detectable deviations and rapid's Holm margin of ELO6-STAT-1 (0.023 to 0.043; p = 0.000715 against 0.000714), the sample sizes of ELO6-STAT-3 (1,579 and 4,512 in standard), the 2025 decomposition of ELO6-EXPLOIT-3 (5.49, of which 4.80 from m; +12.05 = +3.56 + 8.49) and the K × m stake of ELO6-STAT-4 (62.0, +60.14). The title simulation of ELO6-EXPLOIT-4 is E16's own design (nine games a month for three months against equal opposition, the interim or the published rating touching the threshold, 40,000 runs with common random numbers) and shows a larger effect than the reviewer's: 2470 to 2500, 0.054 with K and 0.171 with K × m.
- **The compression refit** (ELO6-STAT-2): refitted on games from 2024-03 only, with E11's model, functions and test months (the extraction reproduces E2's monthly sums exactly, and a second run reproduced its aggregate byte for byte), the bottom bands miss less (1500–1599 +0.023 against +0.029) and only 2400–2499 stays outside ±0.01 by level band, log-loss improving by 0.00007 to 0.00037 nats a game (E16 §5). The frozen table is not changed: the refit is shown beside Freeze 3.
- **No frozen file was changed.** Freeze 3's manifest is unchanged (check (a)). Freeze 1's and Freeze 2's files may not be modified in this session (the relay's locks), and changing a Freeze 3 file needs a new decision record that also changes check (a), itself a Freeze 2 file; so the two findings that need such changes, the rule for an unplayed game (ELO6-EXPLOIT-2) and a column without m (ELO6-EXPLOIT-3), are fixed in part and sent to the architect, time-critical. E12 §9's wording, which the reviewer corrects, is in a frozen script; E16 §6 states the correct reason.
- **After the fixes:** proposal body 4,498 words by the strict count and brief 899 (check (d)); every reference resolves (check (c)); every script that needs no data reproduces its committed output and Freeze 3's manifest equals D-0011's (check (a)); the slow simulator run E14 (two runs, byte-identical, md5 81c184e42cfccfcfe7a748fa3ee3a5db) and the data-dependent E16 extraction (two runs, byte-identical) were reproduced by hand, and E15's widened search reproduced the first search's point exactly; 586 tests pass (check (b)).

### Disposition

**fixed** (where); **fixed in part** (what remains, and for whom). Ruling-level points go to the architect (below); none of R24–R42 was reopened.

| ID | Sev. | Topic | Status |
|---|---|---|---|
| ELO6-EXPLOIT-1 | blocker | playing down still pays outside the guard's region, at both ends; colour at the top; the tolerance under K × m | fixed: measured (E16 §1–§3) and stated in annex T3.2 (item 6, with the v2 colour figures of script v2 §8), T3.5, T3.6 ("What remains"), P4, T8.1, T8.10, T10.2 ("what remains outside it"), proposal §5 and §8 and the brief (step 2: "an extra White pays much less"; "against moderately weaker players it still slightly favours the stronger"); the favourite's yield by band and White's residual by band added to T8.4's monthly indicators; the simulator's blindness to these yields stated (P4, T3.6 (g), proposal §8). Rescaling T8.2's tolerance for K × m: for the architect |
| ELO6-STAT-1 | major | "passes in every cell" overstated; below 2000 the v2 table misses by more than Freeze 1's | fixed: the detectable deviations, the untested cells and rapid's Holm margin printed (E16 §4) and stated in annex T3.6, T8.1, T8.10 and proposal §2(a), §8, §15; the bands below 2000 and 2400–2499 named. Making the by-band test on FIDE's data a condition before adoption would change R35's verdict: for the architect |
| ELO6-STAT-2 | major | the fit straddles the March 2024 compression; the held-out claim | fixed: the refit after the compression shown beside Freeze 3 (E16 §5); annex T3.3 states the confound, that the published fit's κ, λ and η lie outside the rolling refits' range and that the model's form was chosen on the test months; a confirmation of the published table on broadcast months from 2026-10 pre-registered (T8.3); proposal §8. Whether SPEC-TABLE-FIT should drop or rescale pre-compression games: for the architect |
| ELO6-EXPLOIT-2 | major | one unplayed game would block every blank of §10 | fixed in part: stated in proposal §10 and annex T8.10; the marker, the completion rule and the changes to `tools/set_results.py`, E13 and check (a) need a decision record changing Freeze 2 and Freeze 3 files, which this session may not make: for the architect, before 22 October |
| ELO6-STAT-3 | major | R24's rule as read could not have removed the guard; rapid's region fails | fixed: the games needed printed (E16 §6) and stated in annex T3.6 and proposal §5; §1 now reads "guarded in the farming region until FIDE's games can calibrate it"; rapid's farming-region failure reported beside slope (b) (annex T3.6 (b), T8.1, T8.10; proposal §5, §8). One test that both imposes and lifts the guard: for the architect |
| ELO6-EXPLOIT-3 | major | §10's (b) will mostly measure R32's m | fixed in part: the 2025 decomposition printed (E16 §7) and set out in proposal §10, as a table, before any result is read, so that the reading can point to it; a pre-registered column without m needs a decision record changing Freeze 3: for the architect, before 22 October |
| ELO6-EXPLOIT-4 | major | K × m raises the chance of touching a title threshold | fixed: the interim rating under rung 2 at today's K specified (each game's K × m term) and its effect measured (E16 §8) and stated in annex T3.5, T11 (§1.5.3 a) row, now rungs 2 and 4) and proposal §14; threshold crossings added to the shadow list's assessment (T3.5). K or K × m for interim ratings under rung 2: for the architect |
| ELO6-EXPLOIT-5 | minor | the guard reaches few favourites; the simulated farmer never tests it | fixed: the reach stated (E16 §6: 193 of 827 standard region games at full weight) in annex T3.6 (g), P4 and proposal §8; a farmer inside the region added to T9.4's list of adversaries not yet run; favourites rated 2500 or more at levels just below 2300 monitored (T8.4) |
| ELO6-EXPLOIT-6 | minor | §1 and §10 overstate how far in advance the comparison was fixed | fixed: proposal §1 ("fixed before any result was read, amended once after round 1") and §10 (Freeze 1's time against D-0011's reading of the schedule; the rung-5 inputs frozen in Freeze 2 after round 1; the tags freeze-2 and freeze-3 with GitHub's merge times as the record); annex T8.10 (the check a tripwire, not a lock) |
| ELO6-STAT-4 | minor | five statements about rung 2 not true as written | fixed: (a) annex T1, P2, T3.4 and P3 (i) (script v2 §9: 62.0 and +60.14; 0.16 with m); (b) annex T11's §8.3.1 row and proposal §5 (the guard lifts towards table 8.1.2, blended); (c) T11's §8.2.3 row (seeds pulled towards the opponents' average); (d) T3.6 (c) and P3 (vi) state that R24's 0.01 condition is missed, by up to 0.006: for the architect; (e) proposal §5 and §8 and annex T8.1 (worse in standard and blitz, the intervals excluding zero) |

### For the architect

Consolidated from the report, with the executor's evidence beside each; none is decided here.

1. **Before 22 October: an unplayed game** (ELO6-EXPLOIT-2). Under Freeze 3 a game not played is entered as "-", which `tools/set_results.py` stores as "no result yet", and E13 then holds both events' tables and every blank as pending. A decision record, before any result is read, should fix a marker for a game not played, the completion rule (every game of rounds 1 to 11 has a result or is marked not played) and the matching changes to `tools/set_results.py`, E13 and check (a); this session's locks forbid changing those files.
2. **Before 22 October: a column without m** (ELO6-EXPLOIT-3). On 2025's games column (b) differs from (a) by 5.49 points on average, 4.80 of them from R32's m; the v2 table at today's K differs by 1.94 and (b0) by 3.33 (E16 §7). Add, by a decision record before any result is read, the v2 table and guard at today's K as a pre-registered column with its three blanks, or rely on §10's 2025 table as the key to reading (b)?
3. **R24, reading 4** (ELO6-STAT-3). The strict reading cannot drop the guard before the region holds about 1,600 games in standard, 2,400 in blitz and 5,300 in rapid (E16 §6), while the guard would lapse on T8.2's "not significantly outside" form, which standard and rapid already meet on broadcast games. One test should both impose and lift the guard.
4. **R24 (ii)** (ELO6-EXPLOIT-5, ELO6-STAT-4 (d)). Keyed on the mean rating, the region guards no favourite rated below 2500, and leaves the largest remaining under-prediction at the top unguarded (+0.017 at gaps of 100 to 399 at levels of 2300 or more, +0.022 at 2400–2499; E16 §1); inside the blend the guarded table steps by 0.011 to 0.016, above the ruling's 0.01 (E12 §2).
5. **R32** (ELO6-EXPLOIT-1, -4, ELO6-STAT-4 (e)). Its only test shows forecasts getting worse in standard and blitz (E12 §6); it multiplies every residual T8.2 tolerates (±0.01 is worth up to 0.18 points a game at K = 10 and 0.73 at K = 40; E16 §3) and those that remain (up to +0.25 a game at K = 10; E16 §1); and it raises title-threshold crossings (E16 §8). Rescale T8.2's tolerance under K × m? K or K × m for interim ratings under rung 2 (R26 covers rung 4 only)?
6. **The March 2024 compression** (ELO6-STAT-2). Refitted on games after it, the bottom bands miss less (1500–1599 +0.023 against +0.029) and one level band stays outside ±0.01 instead of two, with slightly better forecasts in all three time controls (E16 §5). Should SPEC-TABLE-FIT drop or rescale pre-compression games? A refit changes the frozen table, so it would be shown beside Freeze 3, not in it.
7. **Rung 2's verdict and its by-band condition** (ELO6-STAT-1). Below 2000 the v2 table misses by more than Freeze 1's in four of five bands, and the cell test detects only misses of 0.023 to 0.043 (E16 §4). Should the by-band test on FIDE's data be a condition before adoption in standard, which would change R35's RECOMMENDED NOW?
8. **A colour term by level** (ELO6-EXPLOIT-1). White scores 0.016 to 0.021 above the v2 table at 2200 and above (E16 §2): a level-dependent η for the next fit?

### The reviewer's report (verbatim)

The report as returned, with its headings moved three levels down so that it sits under this addendum; nothing else is changed.

#### Red-team review, session ELO-6: rung 2 v2, the narrowed guard and §10 (R-STAT and R-EXPLOIT)

**Method.** I worked read-only and changed no file. Numbers marked "computed" are my own. I produced them from the committed aggregates, or with the committed library code (`src/layer2/table_v2.py`, `src/layer2/guard_v2.py`, `tools/compare_event_v3.py`), and printed them to stdout only. No committed script produces them yet, so the documents must not cite them until one does (CLAUDE.md rule 3).

##### Findings

###### ELO6-EXPLOIT-1 — blocker — Playing down still pays under rung 2 as recommended, now at both ends of the list

**Location:**
- Annex T10.2 ("Why the farming incentive goes"), T3.2 item 6 ("an extra White no longer pays"), T5 P4, T3.6 (g).
- Proposal §5 ("The gap and the table"), §8 rung-2 row, §13 "Cliffs".
- E12 §3.

**Problem.** Below the guard's 400-point gap, favourites still score above the v2 table, and R32's factor m multiplies that residual into a gain. Figures are computed from `analysis/aggregates/E11_table_by_level.json` (rolling test months, standard, level band × gap cells, weighted by games). They cover favourites at gaps of 100–399; yield is expected points a game, K × m × residual:

| Levels | Games | Layer 0 | Freeze 1 | v2 | Yield: Layer 0 / Freeze 1 / v2 with K × m |
|---|---|---|---|---|---|
| 2300–2799 | 28,243 | −0.0233 | +0.0425 | +0.0170 (SE ≈ 0.002) | K = 10: −0.23 / +0.43 / +0.25; K = 20: −0.47 / +0.85 / +0.50 |
| 2400–2499 only | 9,339 | — | +0.0493 | +0.0217 | K = 10: v2 with K × m +0.32 |
| 1500–1999 | 42,516 | −0.0310 | −0.0047 | +0.0179 (SE ≈ 0.002) | K = 20: −0.62 / −0.09 / +0.47; K = 40: −1.24 / −0.19 / +0.94 |

- **At the top.** The residual falls by 60 %, but the yield falls by only about 40 %. In band 2400–2499 the yield is as large as the +0.30 that V10-EXPLOIT-1 reported for Freeze 1's table.
- **Below 2000.** This is a new incentive: Freeze 1's table had none there.
- **The direction of the flow reverses.** Pooled over levels, favourites beat the v2 table in 10 of 11 gap bins (E11 §4: +0.0055 to +0.0121; +0.0079 weighted by games over 189,854 games). Points would flow up the list, the mirror image of §2(a)'s drain.
- **Colour is still under-priced at the top.** E2's descriptive table (all months) has White scoring 0.552, 0.550 and 0.551 in games within 25 points:
  - at 2200–2399 (5,545 games), 2400–2599 (5,140) and 2600 or more (1,912);
  - the v2 table gives White 0.536–0.537, 0.533–0.535 and 0.529–0.532 at equal ratings (computed; script v2 §8 prints 0.533 for 2500–2599);
  - an extra White is therefore still worth about 0.016 × 14.9 ≈ +0.24 points at K = 10.
- **The documents' evidence cannot show any of this.**
  - The simulator's 0.241 → 0.053 takes the v2 table as the truth, so these empirical residuals are absent by construction.
  - E12 §3 computes K × m × residual only inside the guard's region.
- **The tolerance was not rescaled.** T8.2's ±0.01 was set for today's K. Under K × m a residual at that tolerance is worth up to 0.18 points a game at K = 10, and 0.73 at K = 40.

**Fix:**
- Print the favourite's yield K × m × residual by level band and gap outside the region, and White's residual by level band (in E12 or a new report from a committed script).
- Rewrite T10.2's heading and conclusion, P4, §5 and T3.2 item 6 with these figures. The qualifier "where it is calibrated" excludes exactly the common choices.
- Add the favourite's yield by band to T8.4's monthly indicators.
- State in §8 that the simulator cannot show these yields.

###### ELO6-STAT-1 — major — "Passes in every cell" overstates the table's calibration, and below 2000 the v2 table is worse than Freeze 1's

**Location:** proposal §2(a), §8 (rung-2 row and the paragraph after it), §15 Q1; annex T3.6 "What remains", T8.10; E11 §5–§6.

**Problem.**

(a) **Below 2000 the v2 table misses further than the table it replaces.** E11 §6, standard, Freeze 1 → v2 (SE):
- 1500–1599: −0.000 → +0.029 (0.006)
- 1600–1699: −0.010 → +0.018 (0.004)
- 1700–1799: −0.007 → +0.015 (0.003)
- 1800–1899: −0.005 → +0.010 (0.003)
- 1900–1999: +0.003 → +0.011 (0.003)

These five bands hold 68,161 of the 191,878 test games and most of the pool (median 1734, quartiles 1552–1928 [E2]). The proposal names only 1500–1599. It never mentions 2400–2499 (+0.0173, SE 0.0025), which E11's own summary lists as significantly outside ±0.01.

(b) **"0 of 68 cells" comes from a weak test.**
- The tested cells' clustered SEs are 0.0050–0.0133. At 80 % power and a one-sided 5 % test, the smallest detectable deviation is therefore 0.023–0.043. At Holm's first step (z = 3.18) it is 0.030–0.063 (computed).
- T8.2 says "the minimum detectable deviation of each bin is published with the result". E2 printed these deviations; E11 and E12 print none.
- Untested cells reach +0.064 (1500–1599 × 150–199, 904 games) and +0.081 (1500–1599 × 200–249, 473 games).

(c) **Rapid passes by a hair.** Cell 1500–1599 × 200–249 (+0.0458, SE 0.0112, 1,196 games) has p = 0.000715 against Holm's first threshold 0.05/70 = 0.000714 (recomputed with E11's `holm`). With one fewer tested cell, rapid would fail rule (a) by cell, a pass that §8's "by level band and gap included" relies on.

**Fix:**
- Replace "passes them in every cell" with "no cell of 1,000 or more test games misses detectably", giving the smallest detectable deviation.
- Print those deviations in E11 and E12, as T8.2 requires.
- State in §1, §8 and §15 that the v2 table is better at 2200 and above but worse than Freeze 1's in every band from 1500 to 1999, and name 2400–2499.
- Make the by-band test on FIDE's data a condition before adoption, not only "tested".

###### ELO6-STAT-2 — major — The fit straddles the March 2024 compression, and the "held-out" claim covers neither the published table nor its form

**Location:** annex T3.1, T3.3 ("improves held-out log-loss"); proposal §2(a); SPEC-TABLE-FIT v1.1 §2 and §4.6; E11 §2, §8, §11.

**Problem.**

(a) **Two published scales are pooled.**
- The March 2024 list moved every standard rating below 2000 by round(0.4 × (2000 − R)) [E5]. That narrowed published gaps below 2000 by 40 % for the same strengths.
- Every fit pools games on both scales with no indicator. The rolling windows hold 26 pre-compression months (test month 2025-01) down to 6 (2026-09); the published fit holds 5.
- As that share falls, the slope steepens most where the compression acted. Between the 2025-01 and 2026-09 fits, κ(L) rises 5.7 % at 1500–1599, 4.1 % at 2000–2099 and 1.8 % at 2700–2799; κ rises from 1.1227 to 1.1701 and λ falls from 0.2041 to 0.1913 (computed from E11's `per_month`).
- E2 shows the same pattern: its final κ of 1.212 lies above its rolling range of 1.159–1.206.
- The test months are all after the compression, and the v2 table misses below 2000 (STAT-1), where pre-compression games would flatten it.
- E2, E11 and SPEC-TABLE-FIT never mention the compression.

(b) **The published parameters were never tested.** They lie outside the range of all 21 tested refits on κ (1.1771 against 1.1227–1.1701), λ (0.1866 against 0.1913–0.2104) and η (36.47 against 36.61–37.72). E11 §2 prints both without comment.

(c) **The test months chose the model.**
- λ was added because "E2's held-out months show that pattern" (SPEC v1.1 §2).
- The draw tail was added by a condition evaluated on residuals from the test games (§4.6), then scored on the same months.
- The draw tail changed nothing: 2 of 12 bands outside before and after, log-likelihood +2.2, μ 0.076 (SE 0.036), identical log-loss (E11 §8).

**Fix:**
- Refit on post-compression games only (2024-03 to 2026-09), or map pre-compression ratings below 2000 by the compression formula. Report κ(L), λ, the by-band residuals and m beside the frozen table.
- State the confound in T3.3 and E11 §11.
- Write "held out from the fit; the form was chosen on these months".
- Pre-register now a confirmation of the published table on broadcast months from 2026-10.

###### ELO6-EXPLOIT-2 — major — One unplayed game blocks every blank of §10, forcing a change to frozen files after the results are read

**Location:**
- Proposal §10; D-0011 part B, items 1 and 4.
- `analysis/e13_us_championships_freeze3.py` (`complete`, and the per-event and blanks branches).
- `tools/set_results.py` (`ALIASES`); `tools/compare_event.py` (`SCORE`).

**Problem.**
- D-0011 says a game not played is entered as "-" and not counted. `set_results.py` maps "-" to `None`; its docstring calls it "a game not finished", so "not played" and "not yet entered" become the same value.
- `compare_event.compare` skips such a game.
- E13 prints an event's tables only when `counted == scheduled` (66), and the blanks only when both events are complete.
- So a single forfeit or withdrawal leaves both events "pending" for good. Unblocking them means editing frozen files under a new decision record after the results are known, deciding then what "complete" means. That is the after-the-fact choice the freeze exists to prevent.

**Fix:** before any result is read, record in a new decision record:
- a distinct marker for a game not played;
- the completion rule: every game of rounds 1–11 has a result or is marked not played;
- the matching changes to `set_results.py` and E13.

###### ELO6-STAT-3 — major — R24's rule as read could not have removed the guard, yet its outcome is presented as evidence

**Location:** proposal §1 ("guarded where farming pays"), §5 ("which none does on 827 to 1,020 games"); annex T3.6, T8.10; E12 §1, §9; D-0011 reading 4.

**Problem.**
- **No table could have passed.** Reading 4 requires the 95 % interval to lie inside ±0.01, a band 0.020 wide. The region's per-game SEs (E12 aggregate) are 0.00705, 0.01171 and 0.00779 (standard, rapid, blitz). Whatever the table, the intervals are therefore about 0.028, 0.046 and 0.031 wide (by players: 0.026, 0.046, 0.030).
- **The samples needed are far larger** (computed): about 1,580 standard games for a centred residual and 4,540 at the observed +0.0041; blitz 2,380; rapid 5,320.
- **E12 §9 is wrong.** It says the rule "cannot be met ... unless the region's residual is unusually tight". The interval's width does not depend on the residual.
- **"Keeps the guard in all three" says nothing about calibration.** In standard the evidence is +0.0041 (−0.0096 to +0.0168), and the farmer's yield is +0.06 a game (E12 §3). §1's "guarded where farming pays" is not supported in standard.
- **Rapid also fails the farming-region test.** With the guard, rapid's region scores −0.0414 (players −0.0651 to −0.0195; month blocks −0.0525 to −0.0261). That fails the farming-region part of rung 2's targeted metric (T8.1; §11 "also in the farming region"). The documents report only slope (b) as rapid's failure.

**Fix:**
- State in §5, T3.6 and E12 §9 that at these sizes rule (i) keeps the guard whatever the table, and give the sample needed.
- §1: "guarded in the farming region until FIDE's games can calibrate it".
- Report rapid's farming-region failure beside slope (b).

###### ELO6-EXPLOIT-3 — major — §10's statistics will mostly measure R32's multiplier, and (b) against (b0) will read backwards

**Location:** proposal §10 (method and results table); D-0011 part B, items 2, 4 and 5.

**Problem.**
- Column (b) changes two things at once: the table, and K × m (1.63–1.72 in the open field's bands, 1.39–1.49 in the women's). No other column may be computed.
- On the 2025 Championship (computed with `compare_event_v3`, m switched off for comparison):
  - mean |(b) − (a)| is 5.49, of which m alone accounts for 4.80;
  - the v2 table at today's K differs from (a) by 1.94, and Freeze 1's table (b0) by 3.33;
  - the largest (b) − (a), +12.05, is +3.56 from the table and +8.49 from m;
  - rounded changes differ from (a) for 12 of 12 players under (b), 10 under the v2 table alone and 11 under (b0).
- A reader will see (b) further from FIDE's rules than the superseded (b0) and credit the new table, though the new table alone is the closer of the two. The reading paragraph may add no number that would correct this.

**Fix:**
- Before any result is read, add by a new decision record one pre-registered column: the v2 table and guard at today's K, with its three blanks.
- Failing that, fix the reading's template so it states, from a committed script run on 2025, that (b) − (a) is mostly the factor m.

###### ELO6-EXPLOIT-4 — major — K × m raises the chance of touching a title threshold without playing better

**Location:** proposal §14; annex T3.5, T4.4, T11 (§1.5.3 a) row); D-0011 R26, which covers rung 4 only.

**Problem.**
- A title needs a rating "achieved at some time". It "can be obtained in the middle of a rating period, or even in the middle of a tournament", and the player "may then disregard subsequent results" (§1.5.3 a) [VT 1]).
- Rung 2 at today's K multiplies each game's stake by m in standard: +44 % at 2300–2399, +49 % at 2400–2499, up to +82 % at 2800 and above.
- If the interim rating uses K × m, as T1's definition of K_i implies, the effect is sizeable. Computed with 40,000 runs each: the v2 table as the truth, true strength equal to the rating, 27 games over three months against equal opposition.

| Starting rating (= strength) | K | Threshold | Today's K | K × m |
|---|---|---|---|---|
| 2470 | 10 | 2500 | 0.061 | 0.111 (m 1.49) |
| 2480 | 10 | 2500 | 0.175 | 0.282 (m 1.49) |
| 2370 | 20 | 2400 | 0.221 | 0.287 (m 1.44) |

- A K = 40 junior now stakes up to 62 points in one game (see STAT-4).
- The documents state how an interim rating is computed only under rung 4.

**Fix:**
- State the effect and its size in T3.5, in T11's §1.5.3 a) row and in §14.
- Specify the interim rating under rung 2 at today's K.
- Add title-threshold crossings to the shadow list's norms assessment.

###### ELO6-EXPLOIT-5 — minor — The guard reaches few favourites, and the simulator's farmer never tests it

**Location:** annex T3.6 (a) and (g), T5 P4, T9.4; proposal §8 rung-2 row; `src/simulator/run.py` (`agent_games`, lines 312–318).

**Problem.**
- **Few favourites are reached.** Because the region is keyed on the mean rating, it requires the favourite to be rated at least 2500; full weight needs 2575.
  - A 2600 is fully guarded only against opponents rated 2100–2150.
  - Only 193 of the 827 standard region games carry full weight (E12).
- **The simulated farmer never tests the guard.** It is a player rated 2400 or more on the published list, playing fields 400–800 points below. It is outside the region whenever it is rated below 2500.
  - Across the five seeds, the guard changes its advantage by +0.0029, +0.0017, +0.0012, +0.0008 and −0.0024 a game (E14 aggregate, ledgers "2" against "2u").
  - The "+0.053 with or without the guard" therefore says nothing about the guard. The reason is the farmer's construction, not T3.6 (g)'s "the truth is the v2 table".
- **Escaping downwards shows no gain on broadcast games.** In standard, levels 2000–2299 at gaps of 400 or more give +0.0023 over 5,390 games (computed). This is a gap in the evidence, not a measured yield.

**Fix:** say so in T3.6 (g), P4 and §8; simulate a farmer who plays inside the region; monitor favourites rated 2500 or more at levels just below 2300 (T8.4).

###### ELO6-EXPLOIT-6 — minor — §1 and §10 overstate how far in advance the comparison was fixed

**Location:** proposal §1 ("fixed in advance"); §10 ("its start time NOT VERIFIED", "The method, fixed in advance", "frozen before the event"); annex T8.10.

**Problem.**
- **The freezes came after play began.** D-0011 part B reads the official schedule's 12:00 as 17:00 UTC. On that reading:
  - Freeze 1, merged by GitHub at 19:59:46Z on 9 October, came about three hours into round 1;
  - Freezes 2 (13:58:33Z) and 3 (15:22:53Z on 10 October) came after round 1 had been played.
- **The rung-5 inputs were frozen during the event.** `params/rung5_us2026.json`, its extract and `tools/compare_pilot.py` were first committed in Freeze 2 (90ea5ea).
- **What actually protects the comparison:** inputs computed deterministically from games up to 30 September, and the executor's statement that no result was read.
- **Check (a) is a tripwire, not a lock.**
  - It runs the pull request's own copy of the check.
  - It reads the manifest from D-0011, which the same pull request could edit.
  - `.github/workflows/check.yml` is outside the manifest.
  - The external record is the annotated tags plus GitHub's merge times.

**Fix:**
- §1: "fixed before any result was read, amended once after round 1".
- §10: replace "NOT VERIFIED" with D-0011's reading and the resulting order of events. Replace "frozen before the event" with "computed from games to September 2026 and frozen in Freeze 2, after round 1".
- Name the tags and merge times as the record.

###### ELO6-STAT-4 — minor — Five statements about rung 2 are not true as written

**(a) The per-game bound in annex T5 P2 and T1.** P2 says "|ΔR| ≤ … ≤ K_i ≤ K_max = 40", and T1 calls K_min, K_max the "bounds of K_i".
- Under rung 2 at today's K, K_i is K × m. A K = 40 junior rated 2290 who beats a 2780 with Black gains +60.14 (K × m = 62.0; computed with `table_v2` and `guard_v2`).
- T3.4's "at most 0.12 points in one game at K = 20" omits m; with m it is 0.16.

**(b) Annex T11, §8.3.1 row.** It says the guard "keeps the favourite's expectation at least table 8.1.2's". That is false inside the blend: a 2610 with White against a 2190 (gap 420, w = 0.4) reads 0.931, against table 8.1.2's 0.94 (computed). The regulation text must state the blend.

**(c) Annex T11, §8.2.3 row.** "Seeded lower than the new table implies" holds only for newcomers scoring above 50 %.
- Below 50 %, table 8.1.1's dp (−193 at p = .25) is smaller in size than the v2 table's (−231 to −245, from script v2 §7 by symmetry).
- So those newcomers are seeded higher: seeds are pulled towards Ra.

**(d) R24 (ii)'s blend.** The ruling asks for a blend "so that no step exceeds 0.01". Inside the blend, the guarded table steps by up to 0.011 (standard), 0.013 (rapid) and 0.011 (blitz) within a band, and 0.016 (rapid) at a band edge (E12 §2). T3.6 (c) and P3 (vi) print these sizes but do not say the ruling's condition is unmet.

**(e) Proposal §8 rung-2 row and annex T8.1.** "K × m does no harm by the tolerance" omits that its only test shows forecasts getting worse, with the interval excluding zero:
- standard +0.00033 (+0.00018 to +0.00059);
- blitz +0.00130 (+0.00076 to +0.00189) [E12 §6].

That runs against R32's own rationale; §5 mentions only standard.

**Fix:** correct each sentence as indicated, and list (d) and (e) for the architect.

##### For the architect

1. **R24, reading 4.**
   - The strict reading cannot drop the guard until the region holds roughly 1,600 games (standard) to 5,300 (rapid).
   - The guard would lapse on a different statistic: "FIDE's data calibrate its region" (T11, T8.2 rule (a)) is the "not significantly outside" form. Under that form, standard and rapid would already pass on broadcast games.
   - One test should both impose and lift the guard.
2. **R24 (ii).**
   - Keyed on the mean rating, the region guards no favourite below 2500.
   - It leaves the largest remaining under-prediction at the top unguarded: +0.017 at gaps 100–399 at levels of 2300 or more, and +0.022 at 2400–2499.
   - Inside the blend, its "no step exceeds 0.01" is breached (0.011 to 0.016). Reading 6 (f) sent only the stop at 735 to you.
3. **R32.**
   - Its only test shows forecasts getting worse in standard and blitz.
   - It multiplies every residual that T8.2 tolerates: ±0.01 becomes up to ±0.18 points a game at K = 10, and ±0.73 at K = 40.
   - It raises title-threshold crossings. Should interim ratings for titles under rung 2 use K or K × m? R26 covers rung 4 only.
4. **The March 2024 compression.** Should SPEC-TABLE-FIT drop or rescale pre-compression games? A refit changes the frozen table, so it would be shown beside Freeze 3, not in it.
5. **§10.** The rule for unplayed games and a column without m both need a decision record before any result is read. After that, either would be an after-the-fact choice.

##### Checked and correct

- **Reproduction.** E11, E12, E13 and `analysis/OUTPUT_ELO6.md` reproduce byte for byte from their scripts (stdout diff).
- **Freeze 3's manifest.** The live manifest equals D-0011's (`e84f0564…`, 49 entries) and covers the import graph of `compare_event_v3`. `src/layer2/table.py` and `src/layer2/kactivity.py` are not on that path.
- **The 2026 event files** hold no result (0 of 66 each).
  - Largest gaps are 165 and 250; lowest levels 2627.5 and 2240.5.
  - The games fall in bands 2600–2799 and 2200–2499, so m is 1.39–1.72.
  - No pairing lies in the guard's region.
- **The fit.** E11 §2's values and SEs match `params/table_fit_2026-10b.yaml`. κ(L) is 1.048, 1.386 and 1.670, and the local scales are 549, 604 and 721. The m values recompute (E′_8.1.2(0) = 0.001369, giving 1.31–1.82 in standard).
- **Rule (a) by cell,** recomputed with Holm: standard 0 of 68 (Freeze 1 10, Layer 0 23), rapid 0 of 70, blitz 0 of 14.
- **E12's figures** match its aggregate: region counts, residuals and both intervals, the guard's costs, the farmer's yields and R32's test.
- **The guard's code.** `guard_v2.py` implements reading 6:
  - the region is tested on published ratings, with w = w_g · w_L;
  - the guard only ever lifts the favourite, and stops when x_fav exceeds 735;
  - the value is rounded on the favourite's side and mirrored;
  - compensation is read on each side's own gap.
  - T10.2's rows reproduce (0.952 → 0.970 at K × m 14.40; 2649 and 2651 both 0.960; 2936 0.992).
- **E13** implements §10's blanks as D-0011 defines them. The 2025 check reproduces: (b) − (a) from −8.05 to +12.05, and (b0) − (a) from −7.00 to +6.62.
- **The simulator's farming figures,** 0.241 and 0.053, are the five-seed means in E14's aggregate (0.2407, 0.0534).
- **T11's §8.2.3 figures** match script v2 §7 and table 8.1.1 in `src/layer0`.
- **Freeze times.** GitHub merge times are 19:59:46Z on 9 October, then 13:58:33Z and 15:22:53Z on 10 October. Both tags are annotated.

## Addendum: session ELO-7, Phase 4 — D-0012, E17 and the sections changed in ELO-7

Status: REVIEW RECORD · Session ELO-7, Phase 4 · Date: 2026-10-11 · Reviewer: one subagent, read-only, briefed with the R-STAT and R-QC briefs together, after Phases 0 to 3 had merged (main at 586c7d2). It read `docs/decisions/D-0012_pre-results-amendments.md` with its implementation (`tools/set_results.py`, `tools/compare_event_v3a.py`, `analysis/e13_us_championships_freeze3a.py`, `tools/checks/check_outputs.py`, `tests/test_compare_event_v3a.py`, E13, and `analysis/e3_freeze2_record.py` with E3); E17 (`docs/specs/SPEC-TOP100_v1_0.md`, `docs/research/VERIFICATION_RATING-REGULATIONS-ARCHIVE.md`, `src/layer0_history/__init__.py`, the extraction, report and summary scripts with their outputs, the tests and the fixtures); and the sections changed in this session: the proposal's header, §1, §5, §8, §10, §13, §14, §15 and Appendix G, the brief, the annex's sections that carry rung 2 at today's K, E14, E16 and `docs/specs/SPEC-TABLE-FIT_v1_2.md`. The rulings R43–R53 were given as fixed, with ruling-level points to be listed separately. It returned ten findings, ranked, each with severity, location and fix, four points for the architect and a list of what it checked and found correct. The report is reproduced verbatim below, after what the executor did with it.

### Verification performed by the executor

- **ELO7-STAT-1 was checked on the 2025 event with the frozen tool, in memory only.** (b′)'s mean and largest difference (1.94, −4.30) and (b0)'s (3.33, −7.00) come out the same under four sets of results: the real ones, all draws and two random sets. (b)'s move with the results (mean 5.49, 2.22, 8.15 and 8.86), through m. The identity (b′) − (a) = K Σ(PD − E) holds whenever K and the counted games are fixed. The executor computed and printed no 2026 value; the reviewer's are its own (For the architect, item 1).
- **E17's new figures come from the committed extraction, rerun on the cached data:**
  - the first-order sensitivity to the opponents outside the 100: 2.44 points of mean difference for each point those opponents would differ, 0.07 to 7.85 by player;
  - the games beyond 400 points: 2,014, of which 2,013 reproduced;
  - the 85 unidentified capped games: they fall to 30 players, at most 14 for one;
  - the 26 tournaments that straddle a change of rules: all reproduced, only one with a game beyond 400 points;
  - the 2017 rounding reading: 28 of 28 periods.

  Two figures of the review now have their own lines in E17 §9: the reviewer's 1.9 to 2.7 points a point becomes 2.44, and its 14 points a player for each 0.01 of residual is printed as computed. The reassembled fixtures hold the same five cases without IDs.
- **No frozen file changed.** Freeze 3a's manifest still equals D-0012's (check (a)). D-0013 records a reading under R43 before any result is read, as D-0012 provides, and changes no file of any freeze.
- **The checks after the fixes:**
  - (a) every script that needs no data reproduces its committed output, and the manifest holds;
  - (b) 609 tests pass;
  - (c) every reference resolves;
  - (d) the body has 4,496 words and the brief 899.

### Disposition

**fixed** (where); ruling-level points go to the architect (below); none of R43–R53 was reopened.

| ID | Sev. | Topic | Status |
|---|---|---|---|
| ELO7-STAT-1 | major | §10's main blanks are set by the pairings | fixed: §10's table rows (outside the cap) say which blanks the pairings and the October list's ratings set, since the score cancels, and that results move them only through games not played; §1 drops "runs blind"; the brief says "its main figures depend on the pairings, not the results"; the wording for `{{US26_READING}}` is in the steps for 22–23 October (session close-out). Printing the 2026 values now would change how §10 is run: for the architect |
| ELO7-STAT-2 | major | E17's mean and counts rest on opponents held fixed | fixed: E17's brief and §9 give the first-order sensitivity (2.4 points of mean difference a point); the summary and Appendix G open with "with the opponents outside the 100 held at their published ratings" and carry the sensitivity; E17 §9, the summary and Appendix G note beside the counts that they compare two scales (annex T3.5) |
| ELO7-STAT-3 | major | part of the gain is rung 2's own residual at the top | fixed: E17 §9 "Rung 2's own error" (E16 §1 and §5's residuals; 13,996 games as favourite at gaps of 100 to 399, about 14 points a player for each 0.01 at K = 10); the summary's "Why" and "What we did" no longer say "refitted on what players actually score" or "on real results", and both plain-language pages say the replay cannot separate the two errors |
| ELO7-QC-1 | major | the brief misdates the amendments; §10 lost Freeze 2's time | fixed: the brief ("amended it twice after round 1 … all before reading any result"; the replica sentence reordered so that "on broadcast games" qualifies only the table); §10 gives Freeze 2's time again (13:58 UTC on 10 October, after round 1), with Freeze 3's and 3a's times written shorter to stay within the cap |
| ELO7-QC-2 | minor | the marker against §5.1's full test | fixed: `docs/decisions/D-0013_games-not-counted.md` transcribes all of §5.1 [V 1] and sets the marker for every game §5.1 does not count or rate (not played; a player made no move, by the official game score; declared unrated for force majeure or under Fair Play by the time of entry); §10's row is now "games counted" |
| ELO7-QC-3 | minor | E3 and E13 print different values under the same blank names | fixed: `analysis/e3_freeze2_record.py` renames E3's blanks with the prefix F2_ and labels the section as Freeze 2's, superseded, saying that the PILOT there sits on Freeze 2's (b), without m (E3 regenerated); that the PILOT of §10 carries K × m is in the steps for the reading |
| ELO7-STAT-4 | minor | E17's validation covers less than its wording suggests | fixed: "given FIDE's own inputs" in E17's brief, the summary and Appendix G; E17 §2 "What the validation tests" (33,607 games within 400 points test the table and the sums; 2,014 beyond, 85 of them by construction, 30 players, at most 14; 26 tournaments straddle a change of rules, one with a game beyond 400, so the start-date reading is barely tested); the rounding paragraph gives 28 of 28 under the 2017 text; §4's wording corrected |
| ELO7-QC-4 | minor | the plain-language pages drop the NOT VERIFIED rule | fixed: the summary and Appendix G state the reading of March 2024 to September 2025 as NOT VERIFIED, with FIDE's calculations agreeing in all 111 tournaments that can tell; Appendix G now lists every limit of E17 §9 |
| ELO7-QC-5 | minor | real names in a test, IDs in a fixture | fixed: synthetic names in `tests/test_layer0_history.py`; FIDE IDs and event IDs dropped from the fixture (`tools/data/assemble_history_fixtures.py` rerun: the same five cases) |
| ELO7-QC-6 | minor | SPEC-TABLE-FIT v1.2 reimposes γ ≤ ½ | fixed: v1.2 §2 reads γ_tc(L) ≥ 0 with no upper bound, a fit on any boundary a calibration flag for the QC (R7) |

### For the architect

Consolidated from the report, with the executor's evidence beside each; none is decided here.

1. **§10 measures the pairings** (ELO7-STAT-1). (b′)'s and (b0)'s blanks, and the PILOT's difference, do not depend on the results; only the number of games counted, the rounded counts, (b)'s blanks (through m) and L0_MATCH do. Two questions follow. Should §10 also carry a measure that depends on the results, such as the per-game log-loss of (a)'s and (b′)'s expectations? And should the values the pairings fix be printed now from a script outside the freezes? The executor did neither, because §10 runs the comparison once, after the last round.
2. **The PILOT's m** (D-0012, reading 6). The PILOT stays on (b), with K × m. The reviewer computed its open blank from the pairings as +24.22, against +14.73 at today's K; these are the reviewer's figures, and no committed script prints them.
3. **Publishing E17's per-player figures.** E17 and Appendix G print 100 identifiable players' published and hypothetical ratings by FIDE ID. SPEC-TOP100 §8 allows it, but FIDE's list pages reserve reproduction [V 3], so publication is the operator's decision.
4. **K under rung 2 in E17.** The replay holds FIDE's K under rung 2, although a junior's K would follow their rung-2 rating (FIDE ID 44599790 played at K 40 in 2022).

### The reviewer's report (verbatim)

The report as returned; its headings already sit four levels down, and nothing is changed.

#### Red-team review, session ELO-7: D-0012, E17 and the changed sections (R-STAT and R-QC)

Read-only at 586c7d2. "Computed" figures are mine, from committed files under `.venv/bin/python`; hypothetical results were held in memory and no 2026 result was read.

##### Findings

###### ELO7-STAT-1 — major — Most of §10's blanks are set by the pairings, not the results

**Where:** proposal §1 ("runs blind") and §10 ("Results, computed after the event"); the brief's "A test run blind"; D-0012's blanks.
**Problem:** per player, (b′) − (a) = K·Σ(PD − E), and likewise (b0) − (a): the score cancels. The PILOT's opponent difference, K·m·Σ(E_b − E_p), is result-free too. Running `compare_event_v3a` on the frozen 2026 pairings with all draws and with random results gives identical values (computed): open (b′) 2.09 / +4.70, (b0) 3.28 / +7.40, PILOT 20 / +24.22; women's 2.44 / −7.58, 3.47 / −10.10, 9 / +0.89. Only an unplayed game changes them. 2025's 1.94 / −4.30 also survive all-draw results. Only GAMES, N_DIFFER (for players whose difference is under a point), (b)'s blanks (through m) and L0_MATCH depend on results.
**Fix:** say so in §10's table rows, which fall outside the cap ("set by the pairings and ratings frozen before round 1"). Reword §1 and the brief without adding words, and say the same in `{{US26_READING}}`. Optionally, print the values now from a script that is not frozen (E16, for example).

###### ELO7-STAT-2 — major — E17's mean and its 2700/2800 counts depend on opponents held fixed

**Where:** E17's "In brief" and §9; Appendix G, paragraphs 2–3; the summary's "What changes".
**Problem:** the whole gain comes from 24,085 games against opponents frozen at published ratings (+24.32 a player); the −0.05 within the 100 is near zero by construction. At the v2 table's slope there (0.0008–0.0012 a point), each point those opponents would differ on average moves the mean by about 1.9–2.7 points (computed). Their own drift under rung 2 is estimated neither in size nor in direction. The counts also compare two scales, because a flatter table spreads ratings (T3.5). Yet the summary opens with "rung 2 would rate these players 23.3 points higher".
**Fix:** add this sensitivity to E17 §9 and to both plain-language pages. Open with "with opponents outside the 100 held at their published ratings", and note the change of scale beside the counts.

###### ELO7-STAT-3 — major — Part of the gain is rung 2's own residual at the top

**Where:** the summary's "Why"; Appendix G; E17 §9.
**Problem:** the summary credits a table "refitted on what players actually score". On held-out months, favourites at levels 2300–2799 and gaps of 100–399 score +0.0170 above the v2 table (SE 0.0019), +0.0217 at 2400–2499 [E16 §1]. By band, 2300–2499 is +0.0135 and +0.0173, while above 2500 the residual is within ±0.01 but with SE 0.004–0.009 [E16 §5]. The 100 played 13,996 games as favourites at gaps of 100–399 [E17 §4], so each 0.01 of residual is worth about 14 points a player at K = 10 (computed), the order of +23.3. The replay cannot separate FIDE's error from rung 2's.
**Fix:** add this limit to E17 §9, Appendix G and the summary. Replace the phrase with "fitted on broadcast games; at 2300–2499 it still expects too little of favourites [E16]".

###### ELO7-QC-1 — major — The brief misdates the amendments, and §10 lost Freeze 2's time

**Where:** the brief's "A test run blind" and "How we test it"; proposal §10.
**Problem:** the brief says "We amended it twice before any result". In fact round 1 had been played before Freeze 3 (15:22:53 UTC on 10 October) and Freeze 3a (20:31:23 UTC, after round 2 began). The proposal and annex T8.10 say "after round 1". This session also deleted "after round 1" from §10's Freeze 3 and from the rung-5 inputs frozen in Freeze 2 (13:58:33 UTC), reversing the ELO6-EXPLOIT-6 fix: §10 now times every freeze but Freeze 2. The brief's "On broadcast games the replica matches FIDE's published calculations" also miscites E0.
**Fix:** in the brief, write "twice after round 1, before reading any result" and "The replica matches FIDE's published calculations; on broadcast games the new table…". In §10, write "Freeze 2 (D-0010, 13:58 UTC on 10 October, after round 1)", trimming equal words elsewhere (4,499 of 4,500; 899 of 900).

###### ELO7-QC-2 — minor — The marker follows the official page, not §5.1's test

**Where:** D-0012, item 1 and reading 1; §10's row "games rated".
**Problem:** D-0012 quotes only the first sentence of §5.1. [V 1] continues: "Except in case of force majeure, any game where both players have made at least one move will be rated, unless the regulations relating to Fair Play require otherwise." Two cases are left to judgment after the results: a game with a result although one player never moved, and a game annulled under Fair Play or for force majeure. Column (a) would then differ from FIDE.
**Fix:** before any result is read, write a short record that transcribes all of §5.1 and sets `unplayed` for every game §5.1 does not rate, judged from the official game score. No frozen file changes. Rename the row "games counted".

###### ELO7-QC-3 — minor — E3 and E13 will print different values under the same blank names

**Where:** `analysis/e3_freeze2_record.py` (outside Freeze 3a) and E3's section "The blanks of the proposal's §10 (D-0010)"; E13's PILOT table.
**Problem:** on a complete synthetic event (computed, in memory), E3 prints `{{US26_*_MEAN_ABS_DIFF}}`, `MAX_DIFF` and `N_DIFFER` with (b0)'s values, while E13 prints (b′)'s under the same names. E3's `{{US26_*_R5_DIFF}}` is Freeze 2's PILOT: +11.62 for the open against E13's +24.22 (computed from the pairings). D-0012 has both pages regenerated. E13's PILOT table also labels (b) "rung 2 v2", without K × m.
**Fix:** make the record script relabel E3's section "Freeze 2's blanks, superseded: §10's are E13's" and rename the blanks (F2_…). The reading should say the PILOT's (b) carries K × m.

###### ELO7-STAT-4 — minor — E17's validation covers less than its wording suggests

**Where:** E17's "In brief", §2 and §4; Appendix G; the summary ("We checked our copy of FIDE's rules first").
**Problem:**
- Games take FIDE's own Ro, opponent rating and K, so the roughly 33,600 games within 400 points test only the table lookup.
- The rule versions rest on 2,020 games at gaps of 400 or more. 85 of them (capped, opponent unidentified) are reproduced by construction through the ±1,000 device, and in those games rung 2 reads the capped gap and so understates the guard.
- Tournaments straddling a version boundary are not counted.
- The 2017 rounding reading rests on 28 periods, not 167.
- §4's "before the ratings move apart" is wrong: `e_rung2` uses the ratings after they have moved apart.

**Fix:** state these limits, adding "given FIDE's own inputs". Report the boundary cases and each player's share of the 85, and correct §4.

###### ELO7-QC-4 — minor — The plain-language pages drop a rule marked NOT VERIFIED

**Where:** Appendix G, paragraphs 1 and 3 ("four caveats [E17 §9]"); E17_summary.
**Problem:** both apply "the rules in force at each date" without saying that the 400-point rule of March 2024 to September 2025 is a NOT VERIFIED reading (CLAUDE.md rule 3). Appendix G keeps four of E17 §9's six limits.
**Fix:** add "the 400-point rule of March 2024–September 2025 is read as the plain cap, NOT VERIFIED; FIDE's calculations agree in all 111 tournaments that discriminate [E17 §2]". Appendix G is outside the cap.

###### ELO7-QC-5 — minor — Two committed test files depart from SPEC-TOP100 §8

**Where:** `tests/test_layer0_history.py`, lines 112–114; `tests/fixtures/fide_history/published_periods.json`.
**Problem:** SPEC-TOP100 §2 and §8 bar names and FIDE's pages from committed files. Yet the test names three real top players, and the fixture carries FIDE IDs, event IDs, Ro, and each game's rating and chg from five FIDE pages.
**Fix:** use synthetic names in the test. Either drop `fide_id` and `event` from the fixture, or allow verification fixtures in a SPEC-TOP100 v1.1, as SPEC-L0 does.

###### ELO7-QC-6 — minor — SPEC-TABLE-FIT v1.2 reimposes γ ≤ ½, against R7

**Where:** SPEC-TABLE-FIT v1.2, §2.
**Problem:** "0 ≤ γ_tc(L) ≤ ½ at each band midpoint" contradicts R7 (γ ≥ 0, no upper bound; a boundary fit is a flag) and annex T3.1 and T3.3.
**Fix:** write "γ_tc(L) ≥ 0 (R7); a fit on a boundary is a calibration flag for the QC".

##### For the architect

- **§10's main column.** R45's main column compares two tables on fixed pairings. Whether §10 should also carry a measure that depends on the results (for example, the per-game log-loss of (a)'s and (b′)'s expectations) is a matter for a ruling.
- **The PILOT's m (reading 6).** The PILOT on (b) carries m: computed from the pairings, its open blank is +24.22, against +14.73 at today's K.
- **Publishing per-player figures.** E17 and Appendix G publish 100 identifiable players' ratings by FIDE ID, beside hypothetical ones. SPEC-TOP100 §8 allows it, but [V 3]'s footer reserves reproduction, so publication is the operator's call.
- **K under rung 2.** E17 holds FIDE's K under rung 2, although juniors' K would follow their rung-2 ratings (FIDE ID 44599790 was at K 40 in 2022).

##### Checked and correct

- **Freezes:** Freeze 3a's manifest `44954559…` (51 entries) reproduces, and no frozen file has changed since `freeze-3a`. Only `tools/set_results.py` and `tools/checks/check_outputs.py` differ from the hashes at the `freeze-3` and `freeze-2` tags. D-0010's manifest reproduces, and the tag times are as stated (computed).
- **Checks and tests:** check (a) passes (E13 also under Python 3.9). All 609 tests pass, check (c) is clean, and the word counts are 4,499 and 899.
- **The unplayed marker:** unplayed games are excluded from every column and from K × n, and leave the event hash unchanged. E3 and E13 regenerate after a withdrawal (computed, in memory).
- **§10's columns:** (b′) is (b) without m; (b) and (b0) are labelled in E13's main tables; the 2025 figures match E16 §7.
- **E17's figures:**
  - The mean is 23.29, with table 23.68, colour −0.39 and FIDE's colour marks 23.25.
  - The favourite share is 76.7 %, and the gap and opponent splits both sum to 24.27.
  - All 28 old-text half-points were rounded away from zero.
  - The 400-point patterns, the handling of the cap mark and the mismatch causes match the aggregate.
  - The colourless v2 table lies below table 8.1.2 at every gap from 4 to 399 in bands 2250–2850 (computed).
- **The archive:** each transcription gives URL, timestamp and SHA-256, and the readings are coded as transcribed.
- **Rung-2 figures:** those in §5, §8, §13, T3.6, T5 and T8.10 are at today's K and match E14, E16 and OUTPUT_ELO6. E14's rerun changed only rung 2's ledgers (computed). R49 is quoted verbatim. No committed E17 output carries names or monthly rating series.

---

## Addendum: session ELO-8, Phase 6 — D-0014, Freeze 3b, SPEC-SELFCAL, E18, E19 and the changed sections

Status: REVIEW RECORD · Session ELO-8, Phase 6 · Date: 2026-10-11 · Reviewer: one subagent, read-only, briefed with the R-STAT and R-QC briefs together. It reviewed after Phases 0 to 4 had merged and Phase 6's document changes were committed (commit 0684218). It read:

- `docs/decisions/D-0014_forecast-test-and-rulings.md` with Freeze 3b's implementation (`tools/compare_event_v3b.py`, `analysis/e13_us_championships_freeze3b.py`, `analysis/us26_draw_rate_extract.py` and its parameter file, `tools/checks/check_freeze3b.py`, the tests) and E13;
- `docs/specs/SPEC-SELFCAL_v1_0.md` (now v1.1) with SPEC-TABLE-FIT v1.2;
- E18 and E19 with their extractions, the fit module, the reports and the aggregates;
- E17's changes, and §11 of SPEC-L0 v1.2 with its fixture and tests;
- the changed sections of the proposal, the annex and the brief.

The rulings R54–R65 were given as fixed, with points on the rulings themselves to be listed separately. It was told to read no result of either 2026 championship and to use no web access. It returned nine findings (four major, five minor), four points for the architect and a list of what it checked and found correct. Its report is reproduced verbatim below, after what the executor did with it.

### Verification performed by the executor

- **The three findings on the forecast test were checked before any result was read, and answered by a new record.**
  - ELO8-STAT-1 (the interval over players). The executor simulated 200 events on the 2025 U.S. Championship's pairings, with (b′) as the truth (`analysis/elo8_review_checks.py`, output `analysis/OUTPUT_ELO8_review.md`).
    - For the Brier difference, the interval over games covers the true mean in 0.96 of the events, R54's interval over players in 0.78 and the crossed interval in 0.99.
    - For the log-loss difference the three figures are 0.83, 0.69 and 0.94.
  - ELO8-STAT-2 (the draw share). Freeze 3c's tool prints from the pairings what the review computed. If (b′) were exactly right, its expected log-loss advantage would be 0.0358 nats a game in the open event and 0.0327 in the women's, of which the draw split contributes 0.0185 and 0.0208. The mean draw probability in the women's event is 0.374 under (a) against 0.450 under (b′) [E13].
  - ELO8-QC-1 (the timing). By the schedule as D-0011 part B transcribed it, rounds 1 and 2, 24 of the 132 games, were played before Freeze 3b.
  - The answer is `docs/decisions/D-0015_forecast-test-reading.md`, merged at 07:58:10 UTC on 11 October with Freeze 3c and tagged `freeze-3c`, before round 3 and before any result was read.
- **E18's figures were reproduced by rerunning the extraction**, with SPEC-SELFCAL v1.1's restated W3, the previous form, the uncapped fit and the Brier differences added. The tables are unchanged, every window is unchanged (E18 §1), and the reviewer's figures came out exactly:
  - (3) − (2) in 2026: −0.00056 to −0.00017 over months and −0.00077 to +0.00003 over quarters, with the year's table ahead in 8 of 9 months by log-loss and in 9 of 9 by Brier;
  - the 2026 table in 2025's form beats the frozen table by −0.00011 (−0.00018 to −0.00007);
  - the uncapped fit gives ζ = 8.36, κ = 1.605 at 2500 and 1.633 at 2700, White's edge of 48.1 at 2700–2799 and a 100-point favourite at 0.5915.
- **E19 was rerun with R59's correction by level band and gap.** It gives +11.21 against +11.90 by band, as the review computed, and every other figure is unchanged.
- **No frozen file changed.** Freeze 3a's manifest equals D-0012's and Freeze 3b's equals D-0014's; Freeze 3c adds three files.
- **The checks after the fixes:**
  - (a) every script that needs no data reproduces its committed output, and the three freezes hold;
  - (b) 643 tests pass;
  - (c) every reference resolves;
  - (d) the body has 4,499 words and the brief 900.

### Disposition

**fixed** (where); points on the rulings themselves go to the architect (below); none of R54–R65 was reopened.

| ID | Sev. | Topic | Status |
|---|---|---|---|
| ELO8-STAT-1 | major | the interval over players is narrower by construction | fixed before any result was read (D-0015, Freeze 3c): the interval over games is the one to read; R54's interval over players is reported, labelled "narrower by construction, not a test"; a crossed interval over players is added; coverage checked by simulation (above) |
| ELO8-STAT-2 | major | (a)'s draw share tilts the log-loss towards (b′) | fixed (D-0015): the primary endpoint is the Brier difference, which needs no draw model; a secondary log-loss with one draw model; the benchmarks "if (b′) were right" printed now in E13 and §10; D-0014's "decided conservatively" withdrawn |
| ELO8-QC-1 | major | no primary endpoint; the 24 games | fixed (D-0015): the primary endpoint (the pooled Brier difference with its interval over games) and three sentences fixed in advance; a rounds 3–11 line; the 24 games disclosed in D-0015 and §10 |
| ELO8-STAT-3 | major | "earns its name" rests on 0.0004 nats | fixed: the size, and "consistent with self-calibration, cannot establish it", in §2(a), T3.7, T8.10 and Appendix H; E18 §3 prints the monthly and quarterly intervals, the month signs and the 2026 table in the form kept (−0.00011); the verdict, by SPEC-SELFCAL §7's rule, stands as computed |
| ELO8-STAT-4 | minor | intervals at the caps | fixed: E18 §4 gives a quantity that depends on a capped parameter "at a cap", without interval, beside the same form fitted without caps; §2 prints the uncapped parameters; T3.7 says six parameters moved as far as the caps allow |
| ELO8-QC-2 | minor | SPEC-SELFCAL's departures from v1.2; W3 | fixed: SPEC-SELFCAL v1.1 §13 lists the departures and what was set after the counts, for the architect; W3 restated and implemented (`analysis/e18_coverage_extract.py`), no window changing |
| ELO8-STAT-5 | minor | R59's "bound" is an estimate | fixed: E19 §3 prints the correction by band and gap (+11.2) beside the band's (+11.9), both called estimates; the tables' own error could account for 2.6 to 3.3 points; Appendix H and T8.10 likewise |
| ELO8-QC-3 | minor | E18 omits outputs SPEC-SELFCAL §7 promises | fixed: the Brier differences with intervals, per year and pooled; the residual by band and gap, every cell of 200 games, with standard errors |
| ELO8-QC-4 | minor | ties at the cut; §10's heading | fixed: E19 and Appendix H list every player tied at the cut; §10 is headed "pre-registered" (and §12 says so) |

### For the architect

Consolidated from the report, with the executor's evidence beside each; none is decided here.

1. **R54's draw model and intervals** (D-0015's readings). D-0015 makes the Brier difference, which needs no draw model, the primary endpoint and adds a crossed interval over players. The simulation adds a point. For the log-loss, which is skewed, the interval over games covers only 0.83 of the time; the crossed interval covers 0.94. D-0015 names the interval over games "the one to read for every measure". The primary endpoint's interval is unaffected (0.96), but for the log-loss lines the crossed interval is the safer reading. Overrule or confirm.
2. **R65 and SPEC-TABLE-FIT v1.2's 24 training months** (SPEC-SELFCAL v1.1 §13, item 1). After the March 2024 cut, 24 months of training allow no choice of form before 2028. The 10-month minimum that made the 2026 choice possible was set after the counts. With 6 selection months and blocks of 3, the rule of choice's interval rests on few distinct resamples.
3. **R59's "as E16 measured it".** E16 §5 measures by band, the executor's reading; E16 §1 measures at gaps of 100–399. E19 prints both by band and by band and gap.
4. **The caps after a rule change that moved ratings.** SPEC-SELFCAL §6 keeps them. In 2026 six parameters sat on their caps; without the caps ζ would be 8.4, not 5.
5. **Identifying broadcast players by name.** This could recover 2020–2023, whose games carry no FIDE ID, and give tables from 2023 or 2024, at the cost of departing from v1.2's sample rule.
6. **Data (operator).** As the operator's addendum asks, E19's aggregate holds 8,200 of FIDE's published ratings for 100 named players. FIDE's list pages reserve reproduction [V 3]; the operator should confirm, or the aggregate should keep only the differences.

### The reviewer's report (verbatim)

The report as returned; its headings already sit four levels down, and nothing is changed.

#### Red-team review, session ELO-8: D-0014, Freeze 3b, SPEC-SELFCAL, E18, E19 and the changed sections (R-STAT and R-QC)

Read-only at 0684218. Every figure marked "computed" is mine. I produced them from committed files and the local `data/` under `.venv/bin/python`, kept scratch work outside the repository and held hypotheticals in memory. I also read the ELO-8 brief and session log in `~/Downloads`. I read the 2026 event files for pairings only (they hold no result) and looked up no result.

##### Findings

###### ELO8-STAT-1 — major — The forecast test's "over players" interval is too narrow by construction

**Where:** D-0014 part A, item 1 and reading 5; `forecast_test` in `tools/compare_event_v3b.py`; the 2025 illustration in E13.
**Problem:** In a round robin every game belongs to two players. Resampling players therefore counts each game twice and treats twelve overlapping clusters as independent.
- With independent games, the players bootstrap's variance is about 0.42 of the games bootstrap's.
- I simulated 400 events with 2025's pairings. The players interval covered the true mean 78 % of the time; the games interval covered it 95 % of the time (computed).
- In E13's 2025 illustration, the players interval for the log-loss difference (−0.0942 to −0.0038) is half as wide as the games interval (−0.1475 to +0.0250). Only the players interval excludes zero.

**Fix:** Before any result is read, issue a new record that makes the games interval primary. It should label the players interval "narrower by construction; not a test". Alternatively, add a crossed (pigeonhole) bootstrap in code outside the freeze. It weights each game by the product of its two players' resampled multiplicities. In the same simulations it covered 94–100 % (computed).

###### ELO8-STAT-2 — major — Column (a)'s draw share tilts the log-loss towards (b′), so reading 1 is not conservative

**Where:** D-0014 reading 1 ("decided conservatively"); `params/draw_rate_2026-10b.json`; §10.
**Problem:** Column (a) splits its expectation using the level band's draw rate, which ignores the gap. Column (b′) uses a draw probability that rises as the gap narrows. The log-loss therefore compares two draw models as well as two expectations. From the pairings alone (computed):
- In the women's event the mean draw probability is 0.374 under (a) and 0.450 under (b′). In the open event both are 0.582.
- If (b′) were exactly right, its expected advantage would be 0.036 nats a game in the open event and 0.033 in the women's. The draw split alone accounts for 0.019 and 0.021 of that.
- On the 2025 event (in sample), giving (a) the v2 table's draw probability closes 0.029 of the 0.048-nat gap.

**Fix:** Before any result is read, a new record pre-registers one more line: (a)'s expectation split with (b′)'s draw probability. The same record withdraws "decided conservatively". §10 should say that only the Brier difference compares the expectations alone.

###### ELO8-QC-1 — major — The pre-registration fixes the numbers but not how they will be read

**Where:** D-0014, "What will be computed after the event", items 4–5; `{{US26_READING}}`; §10.
**Problem:**
- **No primary endpoint.** Two measures, three scopes and two intervals give twelve intervals, one of them too narrow (STAT-1). Nothing names a primary endpoint or says what counts as favouring (b′). The reading is written by hand after the results.
- **Timing.** By the schedule, rounds 1–2 (24 of the 132 games) were played before Freeze 3b. The brief that set out R54 carries a date but no time. The record's "no result read" covers only the executor. §10 does not say that the test includes those games.

**Fix:** Before any result is read, a new record should:
- name a primary endpoint, for example the pooled Brier difference with its games interval;
- fix the sentence to be used for each outcome;
- add a secondary line covering rounds 3–11 only.

§10 should also disclose the 24 games.

###### ELO8-STAT-3 — major — "Self-calibration earns its name" rests on 0.0004 nats, a comparator with less data and a rule set after the counts

**Where:** proposal §2(a) (in the body) and Appendix H; annex T3.7 and T8.10; E18 §3; SPEC-SELFCAL §5.
**Problem:**
- **Size.** In 2026 the year's table beats the frozen 2025 table by 0.00038 nats a game. That is under 1 % of its gain over table 8.1.2 (0.0477).
- **Interval.** The interval comes from 3-month blocks over 9 months. From E18's monthly sums (computed), a month-level t-interval is twice as wide (−0.00056 to −0.00017). A quarterly interval reaches zero (−0.00077 to +0.00003). The sign holds in 8 of 9 months by log-loss and in 9 of 9 by Brier.
- **Comparator.** The frozen table had 10 months of data and the 2026 table 22, so the test cannot separate refitting from having more data.
- **A rule set after the counts.** Form P with ζ could only be chosen because SPEC-SELFCAL set a 10-month training minimum. That minimum was set once the window lengths were known (22 = 10 + 12). Under v1.0–v1.2's 24 training months no form can be chosen in 2026. Refitted in the form that would then be kept (E with the tail) within the caps, (3) − (2) is −0.00011 (−0.00018 to −0.00007) (computed). The verdict holds, but the size falls by 71 %.

**Fix:**
- In §2(a), T3.7, T8.10 and Appendix H, give the size: "by 0.0004 nats a game, against 0.048 over table 8.1.2".
- Say that one year against a comparator with less data is consistent with self-calibration but cannot establish it.
- Print the form-E variant in E18 §3.

###### ELO8-STAT-4 — minor — The 2026 intervals at the caps exclude the uncapped estimates

**Where:** E18 §4 (the 2026 column); T3.7 ("Its parameters move little").
**Problem:** Six of the 2026 table's thirteen parameters sit on their caps, and the parametric draws hold them fixed. Fitted without caps (computed):
- ζ is 8.36, against its cap of 5;
- κ at 2500 and 2700 is 1.605 and 1.633, against caps of 1.471 and 1.589;
- White's edge at 2700–2799 is 48.1, against E18's printed 43.5 (42.1 to 44.8);
- a 100-point favourite at 2700 is expected to score 0.5915, against the printed 0.590 (0.589 to 0.591).

Both derived values fall outside the printed intervals. E18 §5 says the intervals understate the uncertainty, but not by how much.
**Fix:** Mark every quantity that depends on a capped parameter "at a cap", with no interval, and print the uncapped fit beside it. In T3.7, replace "move little" with "six parameters moved as far as the caps allow".

###### ELO8-QC-2 — minor — SPEC-SELFCAL departs from the rules R65 fixes without saying so

**Where:** SPEC-SELFCAL §4 (W3), §5 and §6; D-0014 part B, reading 8.
**Problem:**
- **Training months.** R65 says each table is fitted "by SPEC-TABLE-FIT v1.2's rules". Through v1.0 §3, that protocol trains on 24 months. SPEC-SELFCAL allows 10. It says the rule was set after the counts, but it does not call this a departure.
- **Dropped terms.** §6's rule for dropped terms is said to predate the fits. It shares their squashed commit, and the session log has no entry between them, so its timing cannot be checked. It makes no difference here, since μ was 0.0009.
- **W3.** A lengthened window still contains the year that was short, so W3 can never rescue a window. This has no effect on E18.

**Fix:** List these as departures for the architect in SPEC-SELFCAL v1.1. Commit future amendments to a specification before fitting, and restate W3.

###### ELO8-STAT-5 — minor — R59's "bound" is a point estimate, not a bound

**Where:** E19 §3 and §8; Appendix H ("bounded, not removed").
**Problem:** The correction pools each band's residual over gaps. That dilutes it where the gain arises: favourites at gaps of 100–399. At those gaps the year's table's residual is larger than the band value (computed from E18's cells):

| year | band | residual at gaps 100–399 | band value |
|---|---|---|---|
| 2025 | 2400–2499 | +0.0315 | +0.0232 |
| 2025 | 2600–2699 | +0.0296 | +0.0051 |
| 2026 | 2300–2399 | +0.0201 | +0.0162 |

Correcting by band and 50-point gap instead turns E19's +11.9 into +11.2 (computed). The tables' own error then accounts for 3.3 points of the headline, not "about 2.6".
**Fix:** Print the correction by band and gap beside the correction by band. Write "estimated" instead of "bounded".

###### ELO8-QC-3 — minor — E18 omits two outputs that SPEC-SELFCAL §7 promises

**Where:** E18 §3; `analysis/e18_selfcal_extract.py`.
**Problem:** §7 promises two outputs that E18 does not print:
- the Brier differences with their intervals: E18 prints only the Brier means, and the extraction bootstraps only the log-loss;
- the residual by band and 50-point gap, with standard errors, for cells of at least 200 games: E18 prints only counts of cells.

**Fix:** Print the cells from the aggregate, and add the Brier differences to the extraction.

###### ELO8-QC-4 — minor — Two slips a reader at FIDE would notice

**Where:** Appendix H; E19's "Largest risers"; the heading of §10.
**Problem:**
- **Ties.** Caruana, Tabatabaei, Abdusattorov and Sarana all tie at +27. "The five largest" silently drops Sarana, because ties are broken by FIDE ID.
- **Heading.** §10 is still headed "run blind", although E13 now prints its main blanks in advance (R55).

**Fix:** List all ties at the cut, or say how they are broken, and head §10 "pre-registered".

##### For the architect

- **R54.** A log-loss "of FIDE's expectation" needs a draw model, and the ruling gives none. Should both columns share one (STAT-2)? In a round robin every game belongs to two players. Should "over players" become a crossed bootstrap, or be dropped (STAT-1)?
- **R65 and SPEC-TABLE-FIT v1.2.** After the March 2024 cut, a 24-month training rule allows no choice of form before 2028, because 2027's window is only 34 months. Is a 10-month minimum acceptable? Annex T8.5's 3-month blocks over 6 selection months make the rule of choice's interval the range of ten block-pair means. For the slope, that range ends at the estimate itself (−0.00033; −0.00068 to −0.00033).
- **R59.** "As E16 measured it" could mean E16 §1 (gaps 100–399) or §5 (by band). The executor took §5.
- **Data (operator).** As the addendum asks, E19's aggregate holds 8,200 of FIDE's published ratings for 100 named players. The brief forbids redistributing FIDE data in bulk, and [V 3] reserves reproduction. The operator should confirm the addendum, or the aggregate should keep only the differences.

##### Checked and correct

- **Freeze 3b.**
  - The manifest recomputes to 48457b94… (56 entries), and checks (a) and (a′) pass.
  - The merge time and the tag match the record.
  - The 2026 files hold no result.
- **R55.**
  - E13's fixed figures do not depend on results: the two runs with placeholder results agree with each other and with the direct sums.
  - C and C + W bound (b) − (a), since m > 1 in every band.
  - The fixed figures quoted in D-0014, §10 and T8.10 match E13.
- **Forecast-test inputs.**
  - The draw rates reproduce E11.
  - The three-way split, the v2 draw formula, the percentile indices and the pairing across columns follow D-0014.
- **E18.**
  - My refit reproduces the 2026 table and its (3) − (2) exactly.
  - The windows follow W1–W5.
  - Every fit, every draw rate and the frozen table use only games from before the year they serve.
  - The Brier difference against table 8.1.2 is negative in all 21 months (computed).
- **E19.**
  - The extraction reruns byte-identical, giving +14.51, R58's +10.14 to +18.71, the bound +11.90 and K reproduced on 8,200 of 8,200 player-lists.
  - Each tournament uses the table for its start list.
  - No year of birth is committed.
  - Appendix H is the script's output verbatim.
- **E17.** R58's range equals E17 §9, and the banners are in place.
- **SPEC-L0 v1.2.**
  - It changes no rule.
  - Its fixtures carry no identifiers.
  - R-14a and R-22b stay NOT VERIFIED.
- **Checks.** 637 tests pass and every reference resolves. The body has 4,498 words and the brief 898.

## Addendum: session ELO-9, Phase 5 — D-0016, the data probe, SPEC-GREATS, E20 and Appendix I

Status: REVIEW RECORD · Session ELO-9, Phase 5 · Date: 2026-10-11 · Reviewer: one subagent, read-only, briefed with the R-STAT and R-QC briefs together. It reviewed after Phases 0 to 4 had merged (main at 4c74425). It read:

- `docs/decisions/D-0016_rulings-on-elo-8-questions.md` and `docs/decisions/D-0017_rulings-on-the-greats.md`;
- the data probe, `docs/research/DATA-PROBE_greats.md`, with its scripts, its aggregate, `tools/data/fetch_probe.py` and `tools/data/politeness.py`;
- `docs/specs/SPEC-GREATS_v1_0.md` with the selection script and its aggregate;
- the rules record `docs/research/VERIFICATION_RATING-REGULATIONS-2001-2017.md` with its script;
- E20 with its two extractions, its report, its aggregates, `src/layer0_greats/`, the fetch and fixture tools, the tests and the fixtures;
- §11 of SPEC-L0 (then v1.3);
- the proposal's Appendix I and front matter.

The rulings R66–R79 were given as fixed, with points on the rulings themselves to be listed separately. It was told to read no result of either 2026 championship and to use no web access. It returned ten findings (six major, four minor), six points for the architect and a list of what it checked and found correct. Its report is reproduced verbatim below, after what the executor did with it.

### Verification performed by the executor

- **ELO9-QC-1 was checked on the cached pages before anything changed.** §10.53 of the 2007 text and §8.57 of the 2010 text stand in "Determining the rating change for a rated player", after K; a new player's Rn is rounded in §10.32 and §8.32. The 2003 text rounds the rated player's Rn in §10.66 ("Rn is rounded off to the nearest 1 or 0"). The rules record now transcribes all six clauses and the §8.5 heading, and its §5 says what they round.
- **ELO9-STAT-1 was recomputed by the extraction** (`calibration` in `analysis/e20_greats_replay_extract.py`): on 9,372 games in which the player of the set was the favourite by 50 to 399 points at FIDE's own ratings, the favourite's mean residual is −0.009 (−0.017 to −0.001) under table 8.1.2 and +0.035 (+0.027 to +0.044) under the 2025 table, intervals clustered over the 29 players. In every level band from 2300 the 2025 table's residual is the larger, by 0.034 to 0.046. The reviewer's own selection gave 9,441 games and −0.008 and +0.036. The replay holds 8,436 and 936 game rows at levels of 2700–2799 and 2800 or more, as the reviewer found; the 2025 table's fit year held 539 and 9 such games [E18 §1].
- **ELO9-STAT-2.** With every outside opponent 10 points lower or higher, the mean difference is +17.79 and +36.34: 0.93 points per point.
- **ELO9-QC-2.** Of the 23 lists before July 2014 that hold a negative half point, 22 rounded every one towards +∞; on the list of January 2009, 3 of 3 went away from zero, and the same list holds one period whose published change is not a rounding of its sum.
- **ELO9-STAT-3.** The six players in only through a shared 3rd place are Polugaevsky (July 1972, January 1976), Mecking (January 1978), Beliavsky (July 1985), Vaganian (January 1986), Sokolov (January and July 1987) and Salov (January 1995). On FIDE's printed lists, Svidler (October 2006) is the one player printed below 3rd on the 3rd's rating who is not among the 36. Kasparov, 1st on the lists before and after, is absent from the lists of January and July 1994, on which Karpov is 1st; Short is absent from the same two lists.
- **ELO9-STAT-5.** The best windows are maxima over 2 (Fischer) to 87 (Carlsen) windows.
- **ELO9-QC-4.** E20 did print `{rdg['R74']['thin_periods']:,}` in its brief, and check (a) passed because the committed page reproduced the slip.
- **The checks after the fixes.**
  - Every script that needs `data/` reproduces its committed output byte for byte (the selection, the probe, the rules record, both E20 extractions, the fixtures).
  - (a) every other script reproduces its committed output, and Freezes 3a to 3d hold.
  - (b) every test passes.
  - (c) every reference resolves.
  - (d) the body has 4,499 words and the brief 900.

### Disposition

**fixed** (where); points on the rulings themselves go to the architect (below); none of R66–R79 was reopened.

| ID | Sev. | Topic | Status |
|---|---|---|---|
| ELO9-STAT-1 | major | the 2025 table misfits the games it is applied to | fixed: E20 §5 prints the check by level band with intervals clustered over players, the fit year's games at 2700–2799 and 2800 or more beside the replay's, and each player's game rows at 2800 or more; E20's brief, §5 and §7 and Appendix I say what the difference measures (the 2025 table's distance from 8.1.2 at these players' gaps, on games 8.1.2 already fits) and that the highest ratings rest most on the levels with least support; whether Appendix I keeps its headline goes to the architect |
| ELO9-QC-1 | major | the 2007 and 2010 texts round the rated player's new rating | fixed: the rules record (passages and §5); SPEC-L0 v1.4 corrects F-H09; E20 §4.2, the era label, `src/layer0_greats/`'s docstrings and the tests; D-0017, a decision record, is not edited: the restated basis goes to the architect |
| ELO9-STAT-2 | major | R58's approximation missing from Appendix I | fixed: Appendix I and E20's brief and §5 state that the outside opponents are held at FIDE's ratings, the range with them 10 points lower or higher, the pass-through of 0.93 points per point and that a replay of the whole pool needs FIDE's tournament reports |
| ELO9-QC-2 | major | Appendix I dates FIDE's change of rounding to July 2014 and hides the January 2009 list | fixed: Appendix I and E20's brief give the rounding up to July 2018, the January 2009 exception and the change of November 2018; E20 §4.2 and F-H09 name the January 2009 list |
| ELO9-STAT-3 | major | six players only through a tie, the change of tie rule in 2000, the two lists of 1994 | fixed: E20 §2 (notes on the selection), §7, the brief and Appendix I ("six of them only through a share of 3rd place"); SPEC-GREATS stays v1.0, its rule fixed (§9): the notes are the rule's consequences, reported in the evidence; one tie rule throughout would be a ruling, for the architect |
| ELO9-QC-3 | major | FIDE's terms held to a laxer standard | fixed: DATA-PROBE §2.6 and a FIDE row in §3 judged by §3's standard (all rights reserved; used for analysis on the brief's instruction, cached locally, not redistributed; written permission not sought); E20's data paragraph and Appendix I reworded; the User-Agent and FIDE's permission go to the operator and the architect |
| ELO9-QC-4 | minor | three slips | fixed: the missing f prefix, with a test that no generated page carries an unrendered placeholder; the April 2003 discrepancy committed as its size (41 points); the fixture README |
| ELO9-STAT-4 | minor | validation and dating claims reach too far | fixed: "given FIDE's own inputs" (E20 §4.1, the brief, Appendix I); "in the greats' games"; the 44 capped games without a found rating under §5's table; the difference "on each player's last list", Korchnoi's being May 2016 |
| ELO9-QC-5 | minor | the permission paragraph promises too much | fixed: Appendix I and E20 §6 keep the brief's statement that permission would allow the full study, with the limits the reviewer names (FIDE's calculations from 2008 only, no record of which games FIDE rated, a model's assumptions across eras); the test updated; SPEC-GREATS §7 keeps the brief's words |
| ELO9-STAT-5 | minor | each best window is a maximum over different numbers of windows | fixed: E20 §3 prints the number of qualifying windows and the median window's mean gap; Appendix I's table gives the number; §3 and §7 note the five-point ratings before 1999 |

2026-10-12 (session ELO-11): ELO9-STAT-1's wording "on games 8.1.2 already fits" no longer stands. E20 §5 reads the check by when the players were chosen, which reverses the order of the two tables for the 14 chosen only on the lists to April 2000, and E20 and Appendix I describe the comparison as made on the same results, which FIDE rated with table 8.1.2 (`docs/DECISIONS.md`, item 9).

### For the architect

1. **R74's premise and scope** (the reviewer's points 1 to 3). The 2003, 2007 and 2010 texts round the rated player's new rating, and §8.57 of 2010 says "0.5 is rounded to 1": R74's outcome has a textual basis that D-0017 does not record, and only a superseding record can restate it. FIDE's lists rounded negative half points towards +∞ to the list of July 2018 (27 of 27) and away from zero from November 2018 (12 of 12); extending R74's reading to July 2018 would leave 9 thin periods instead of 36 (the run "towards +∞ throughout", 21, is 36 − 27 + 12). Decide also whether the list of January 2009 is a list-level exception or its periods stay thin.
2. **The backward table's headline** (point 4). E20 now carries the calibration check, beyond SPEC-GREATS §6; R59's estimate of the table's own error at the top is not computed for E20. Should Appendix I keep "+27.0" as its headline?
3. **Ties** (point 5). One tie rule throughout would change the selection, which SPEC-GREATS §9 bars after results without a ruling.
4. **Terms** (point 6). Should FIDE's written permission be sought before E20 or Appendix I leaves the repository (R73)? R77 puts figures derived from OlimpBase under CC BY 4.0, which allows commercial reuse, while OlimpBase says "non-commercial use only": confirm, or mark those tables with the source's terms. And whether future fetches should name the project in their User-Agent is the operator's decision.

### The reviewer's report (verbatim)

The report is reproduced as returned, its section headings set one level lower to sit under this addendum.

#### Red-team review, session ELO-9: D-0016, the data probe, SPEC-GREATS, E20 and Appendix I (R-STAT and R-QC)

##### Findings

###### ELO9-STAT-1 — major — The 2025 table misfits the games it is applied to, most of all at the top, and E20 does not say so

**Location:** E20 "In brief" ("Under the 2025 table applied backwards"), §5 (closing paragraph), §7; Appendix I, "The replay, 2008–2019", and its table.

**Problem:** E20 says the difference shows "what today's table would have made of the same results". It never checks the table against those results. I ran that check with E18's own measure: the favourite's residual S − E at the list's ratings, on gaps of 50–399. On the 9,441 replayed games in which one of the 29 was the favourite, table 8.1.2 gives −0.008 and the 2025 table +0.036 (computed from FIDE's pages; cluster SE over players 0.004 for each).
- By level band, table 8.1.2 runs from −0.016 to −0.000. The 2025 table runs from +0.026 to +0.046.
- At levels 2700–2750 the 2025 table expects a 100-point favourite to score 0.589. FIDE's table expects 0.64. The slope is 0.00105 a point (computed).
- So the 0.044 between the two curves is worth about 40 points. The +27 mean, and Carlsen's +62, measure the 2025 table's distance from 8.1.2 at the gaps these players played. On these games, 8.1.2 fits better.
- Being selected for success would raise both residuals by the same amount. It does not close the gap between them.

The table also has little data where it matters:
- It was fitted on games of March–December 2024. That window holds at most 9 games at levels of 2800 or more and 539 at 2700–2799 [E18 §1].
- By FIDE's own ratings, the replay holds 936 and 8,436 of its 18,490 game rows at those levels, including 355 of Carlsen's 785 (computed). Under rung 2's higher ratings there would be more.
- One standard error of the table's residual at 2700–2799 is 0.011 [E18 §3]. At this slope that is about 10 points.
- E19 prints R59's estimate of the table's own error at the top. E20 prints none.

**Fix:**
- In E20 §5, print this check as a labelled diagnostic: by band, both tables, with a cluster interval over players. Also print the fit window's game counts at 2700+ and 2800+ beside the replay's.
- In §5, §7 and Appendix I, say what the difference measures: the 2025 table's distance from 8.1.2 at these players' gaps, on games where 8.1.2 fits better.
- Flag Carlsen's and Caruana's rows, and the 2945, as resting on the band with least support.

###### ELO9-QC-1 — major — The rules record misreads the 2007 and 2010 texts: both round the rated player's new rating

**Location:** VERIFICATION_RATING-REGULATIONS-2001-2017.md §5 (the row "Rounding of the change" and "What the texts leave open"). Also:
- SPEC-L0 v1.3 §11, F-H09 ("no clause in the texts of October 2007 and June 2010");
- E20 §4.2 ("The 2007 and 2010 texts have no rounding clause") and its table label "(no clause)";
- the docstring of `src/layer0_greats/__init__.py`;
- Appendix I.

**Problem:** The record says §10.53 (2007) and §8.57 (2010) round "a new player's Rn". The cached archive pages that the script reads say otherwise:
- A new player's Rn is rounded in §10.32 and §8.32, under "The Rating R n which is to be published for a previously unrated player". The 2010 wording is "0.5 is rounded up".
- §10.53 and §8.57 sit inside "Determining the rating change for a rated player", directly after K.
- §8.57 reads: "R n is rounded off to the nearest 1 or 0, 0.5 is rounded to 1."
- Read as the rated player's new rating (a whole Ro plus the change), that means 0.5 towards +∞ for the change. FIDE's lists before July 2014 do exactly this in 73 of 78 half points.

So the texts are not silent. The first reading departed from an existing clause, and the documents deny a textual basis that R74's outcome actually has.

**Fix:**
- Transcribe §10.3/§10.32, §8.3/§8.32 and the §10.5/§8.5 headings into the record.
- Replace "no clause" with this reading, marked NOT VERIFIED.
- Correct F-H09 in SPEC-L0's next version, with its decision record. Correct E20 §4.2, the module docstring and Appendix I.

###### ELO9-STAT-2 — major — Appendix I drops R58's approximation, where it carries almost the whole result

**Location:** Appendix I, "The replay, 2008–2019"; E20 "In brief" and §5's last paragraph.

**Problem:**
- Appendices G and H say that opponents outside the set are held at their published ratings, give R58's range, and note that a whole-pool replay needs FIDE's reports (the ELO7-STAT-2 fix). Appendix I says only "the greats end 2019 27.0 points above FIDE's ratings on average".
- In E20, shifting outside opponents by ±10 moves the mean from +17.8 to +36.3. That is 0.93 a point (computed), against 0.82 in E17 and 0.43 in E19.
- After twelve years the set sits at an equilibrium against opponents frozen at FIDE's ratings. In a whole-pool replay those 2600–2750 opponents would also move. E19 finds today's top 100 (down to 2626) +14.5 after only 22 months of tables, so a move larger than ±10 is plausible.
- Carlsen's 2945 lies on this mixed scale.

**Fix:**
- In Appendix I, write "with every opponent outside the 29 held at FIDE's rating (R58) … +27.0 (+17.8 to +36.3 with them 10 points lower or higher)". Add Appendix H's line on the whole-pool replay.
- In E20's brief and §5, add "against opponents held at FIDE's ratings" and the 0.93 pass-through.

###### ELO9-QC-2 — major — Appendix I misdates FIDE's change of rounding and hides an exception confined to one list

**Location:** Appendix I ("Before July 2014 FIDE rounded a half point towards +∞"); the status column of SPEC-L0 F-H09; E20 §4.2.

**Problem:**
1. The sentence implies a change at July 2014. FIDE's pages show every negative half point rounded towards +∞ up to the list of July 2018 (27 of 27), and away from zero from November 2018 (12 of 12) [E20 §4.2]. Of the 36 thin periods, 27 come from the reading kept from July 2014. The appendix does not say so.
2. All three negative half points rounded away from zero before July 2014 are on one list, January 2009 (3 of 3). Every other list before July 2014 went towards +∞ (30 of 30; computed by rerunning the replay). E20 presents them as scattered exceptions.

**Fix:**
- Appendix I: "FIDE's lists rounded half points towards +∞ to July 2018 (73 of 78 before July 2014; 27 of 27 negative ones after), except the January 2009 list (3 of 3 away from zero), and away from zero from November 2018; 27 of Layer 0's 36 thin periods follow from the reading kept for July 2014–July 2018, which is left to the architect."
- Add the January 2009 cluster to E20 §4.2 and to F-H09.

###### ELO9-STAT-3 — major — Six of the 36 are in only through a tie for 3rd, under a tie rule that changes in 2000; two 1994 lists lack Kasparov

**Location:** SPEC-GREATS §2; `analysis/greats_select.py`, `computed()` (`r >= third`); E20 §2, §3, §7; Appendix I, "Who".

**Problem:** Computed with `greats_select`'s own functions.
- **Tie-only players.** Six players owe their place only to a shared 3rd place, on lists rounded to 0 or 5 (OlimpBase: unrounded only from January 1999):
  - Mecking (1978-01, three tied);
  - Beliavsky (1985-07);
  - Vaganian (1986-01, three tied);
  - Salov (1995-01, three tied);
  - Polugaevsky (1972-07, 1976-01);
  - Sokolov (1987-01, 1987-07).
- **The rule changes in 2000.** From July 2000 FIDE's printed tie-break decides. That excludes Svidler, tied 3rd with Kramnik on 2750 in October 2006, which is SPEC-GREATS §2's own example.
- **Two 1994 lists.** Kasparov and Short are absent from OlimpBase's lists of January and July 1994, and present in July 1993 and January 1995. Those two lists:
  - give Karpov 2 of his 14 lists at #1;
  - give Shirov a best rank of 2 (3rd with Kasparov present);
  - give Kramnik a first top-3 list (4th on 1994-07 with Kasparov present);
  - lower the #2 inside Shirov's and Salov's best windows (July 1992–January 1995) and Ivanchuk's (July 1991–January 1994).

None of this is stated anywhere.

**Fix:**
- Without changing the rule (SPEC-GREATS §9), list in SPEC-GREATS v1.1 and E20 §2 and §7: the six tie-only players, Svidler's exclusion, and what the two 1994 lists change.
- In Appendix I, write "36 players, six only through a tie for 3rd on lists rounded to five points".

###### ELO9-QC-3 — major — FIDE's terms are held to a laxer standard than every other source's, and the appendix tells FIDE otherwise

**Location:** DATA-PROBE §2.6, §3, §4; the E20 header ("as the probe found them legitimately available"); Appendix I ("only what the data probe found legitimately available"); `tools/data/fetch_probe.py` (`UA = "Mozilla/5.0"`, `--ajax`), `fetch_greats_calculations.py`, `fetch_fide_old_lists.py`.

**Problem:**
- §3 marks PGN Mentor, Chessgames.com and 365Chess "needs permission" for "a copyright notice and no licence".
- FIDE's footer goes further: "All Rights Reserved. No part of this site may be reproduced, stored in a retrieval system … without the written permission of FIDE".
- §2.6 quotes that footer but gives FIDE no status. §4 then treats FIDE's calculations as usable.
- The session stored 1,774 calculation pages and 83 list files.
- The fetch tools send a generic browser User-Agent. For the calculations they also send the page's AJAX headers to endpoints which, in the tool's own words, "answer only the headers their own pages send".
- [V 3]'s basis (analysis, no redistribution) may hold. But "legitimately available" claims more than FIDE's terms support.

**Fix:**
- Give FIDE a row in DATA-PROBE §3 by the same standard: rights reserved; storage needs written permission; used for analysis only, on the brief's instruction; not redistributed; permission not sought.
- Use that wording for FIDE's data in E20 and Appendix I.
- Have future fetches identify the project in the User-Agent, as the operator decides.

###### ELO9-QC-4 — minor — Three slips in the generated pages and fixtures

**Location:** E20 "In brief", "Rounding (§4.2, R74)"; `analysis/e20_greats_report.py` line 183; the E20 header; `tests/fixtures/fide_greats/README.md`.

**Problem:**
1. E20 prints `Thin periods: {rdg['R74']['thin_periods']:,} under R74's reading`, because line 183 lacks the `f` prefix. Check (a) passes because the committed page reproduces the bug.
2. The header says every published rating committed is a peak. But §1 and `E20_greats_lists.json` commit two ratings of FIDE ID 1503014 for April 2003.
3. The README calls F-G06 "every period … whose sum ends in exactly a half point". The fixture holds one period (2008-10).

**Fix:**
1. Add the `f`, regenerate (the page should then read 36), and add a test that generated pages contain no unrendered `{x[`-style placeholder.
2. Keep only the size of the April 2003 discrepancy, or reword the header.
3. Correct the README.

###### ELO9-STAT-4 — minor — Validation and dating claims reach further than their basis

**Location:** E20 "In brief", §4.1–§4.2, §5; Appendix I.

**Problem:**
1. "Reproduces FIDE's printed change in 18,490 of 18,490 games" takes FIDE's own Ro, opponent ratings and K. It tests the table and the cap rule only (ELO7-STAT-4 made the same point about E17).
2. "FIDE's pages date the end of the 350-point rule" rests on the greats' games alone.
3. In the 44 capped games whose opponent was not found, rung 2 has no 400-point rule and so reads the capped gap.
4. Korchnoi's +24 is carried from November 2012. He appears on no list after May 2016, yet counts towards "end 2019 … 27.0 above". Without him the mean is +27.14 (computed).

**Fix:**
- Add "given FIDE's own inputs" and "in the greats' games".
- State item 3 under §5's table.
- Write "on each player's last list", or leave Korchnoi out of the end-2019 mean.

###### ELO9-QC-5 — minor — "What permission would add" promises more than any game collection can deliver

**Location:** Appendix I, last paragraph; E20 §6; SPEC-GREATS §7; `tests/test_e20_appendix.py`, which asserts the sentence.

**Problem:** The appendix says "the full study becomes possible: every game of the greats' careers replayed under both systems … and the games that link one era's players to the next". But:
- validation against FIDE is possible only from the April 2008 list (DATA-PROBE §5(iii));
- FIDE's lists begin in 1971, and the rules before 2003 are not transcribed;
- no collection marks which games FIDE rated;
- Chessmetrics's data are ChessBase's (DATA-PROBE §3);
- linking eras gives a comparison only under a model, which the fixed wording ("A rating measures strength against one's own era") disclaims.

**Fix:** Replace the sentence with: "With permission, the replay could extend to the games those collections hold. FIDE's own calculations exist only from 2008, those collections do not record which games FIDE rated, and any comparison across eras would rest on a model's assumptions." Update the test, E20 §6 and SPEC-GREATS §7 to match.

###### ELO9-STAT-5 — minor — Each best window is a maximum taken over very different numbers of windows

**Location:** SPEC-GREATS §5; E20 §3 and "In brief"; Appendix I's first table.

**Problem:** My own code for §5 reproduces E20's best windows exactly. Behind each maximum lie different numbers of qualifying windows: Fischer 2, Kasparov 45, Karpov 63, Carlsen 87 (computed).
- A maximum over many overlapping windows drifts upward more.
- A 1970s window holds 3–4 lists rounded to 5 points, so one list moves its mean by a third.
- E20 discloses only the frequency of the lists.

**Fix:** Print the number of qualifying windows and the median window's mean gap beside each best window. Note the 5-point rounding before 1999 in §3's caveat and in §7.

##### For the architect

1. **R74's premise.** D-0017 calls the 2007 and 2010 texts silent on rounding, and calls towards +∞ "the 2014 text read literally". §8.57 of 2010 ("0.5 is rounded to 1") supports the outcome directly (ELO9-QC-1). A superseding record could restate the basis; D-0017 itself cannot be edited.
2. **R74's scope.** FIDE rounded towards +∞ to July 2018 (27 of 27) and away from zero after (12 of 12). Extending R74 to July 2018 would cut thin periods from 36 to 9. The third reading's count cross-checks this: 21 = 36 − 27 + 12. F-H07's reading of the 2017 words would then hold only from November 2018.
3. **January 2009.** Decide whether this list is a list-level exception (3 of 3 away from zero, plus one period that is not a rounding at all), or whether its periods stay thin.
4. **The backward table.** ELO9-STAT-1's calibration check, and R59's estimate for E20, both lie beyond SPEC-GREATS §6. Decide whether E20 carries them, and whether Appendix I keeps its +27.0 headline if it does.
5. **Ties.** Ties before 2000 bring in six players; FIDE's tie-break after 2000 excludes Svidler. SPEC-GREATS §9 bars a rule change after results, so applying one tie rule throughout needs a ruling.
6. **Terms.** Two questions:
   - Should FIDE's written permission be sought before E20 or Appendix I leaves the repository (R73)?
   - R77 puts OlimpBase-derived figures under CC BY 4.0, which allows commercial reuse, while OlimpBase says "non-commercial use only". Confirm this, or mark those tables as carrying the source's terms.

##### Checked and correct

- **Reproducibility.** Every greats aggregate reproduces byte for byte from local `data/`: the selection, the probe, the rules record, the lists (with the cache redirected to scratch) and the replay (three readings). E20, DATA-PROBE and the appendix reproduce from their scripts. The proposal's Appendix I equals `OUTPUT_E20_appendix.md`. All 671 tests pass, and the tree was left clean.
- **Dominance**, recomputed independently:

  | player | gap to #2 | gap to #10 | lists |
  |---|---|---|---|
  | Fischer | +100.0 | +160.0 | 4 |
  | Kasparov | +64.2 | +145.0 | 6 |
  | Carlsen | +53.7 | +101.2 | 36 |
  | Karpov | +43.3 | +85.0 | 3 |
  | Anand | +6.0 | +54.5 | 12 |

- **Replay counts.** All of these agree with E20:
  - 18,490 games with no mismatch; K reproduced in all 2,680 tournaments (the five at K 15 are two juniors' periods in 2008); 1,774 pages, none missing.
  - Thin periods: 36 = 7 + 17 + 12 by era; 65 and 21 under the other two readings.
  - Half points: 78 = 33 + 45, of which 73 and 46 reproduced; negative half points by year sum to 72 = 57 + 15.
  - Mean difference +27.03 (table +27.31, colour −0.28); ±10 gives +17.79 and +36.34.
  - The 350/400 switch falls between 28 June and 9 July 2009. Colour marks: 9,331 White + 9,159 Black.
- **Sources.**
  - OlimpBase against FIDE's 2001 files: 152,963 of 152,966 ratings equal.
  - FIDE's raw files really do lack Mamedyarov and Ivanchuk (November 2009) and So (January–June 2013), checked by ID and by name.
  - The 12 printed-versus-computed disagreements are 8 ties and 4 activity misfires in 2002–2004. All 12 fall on dates where the printed list decides, so the selection is unaffected.
- **Rules.** Capped ratings are printed unmarked (Ro − 350) before July 2009 and with FIDE's mark after (0 unmarked, 542 marked). The 2007, 2010 and 2014 passages are transcribed verbatim, and their tables equal Layer 0's.
- **Politeness and fixtures.**
  - Since 11:06:18 UTC, no gap to ratings.fide.com is under 4 s (1,933 requests in all).
  - Since 11:27:39 UTC, no gap to the Internet Archive is under 8 s.
  - Both slips are recorded.
  - R79's fixture has 13 player-periods and no names, IDs or events.
  - The fixed wording stands above every table, and the OlimpBase credit is present where it is required.

## Addendum: session ELO-10, Phase 4 — D-0018, SPEC-L0 v1.5, E20, Appendices F and I, annex T1's guard row, README's licence section and DATA-PROBE §3

Status: REVIEW RECORD · Session ELO-10, Phase 4 · Date: 2026-10-11 · Reviewer: one subagent, read-only, briefed with the R-STAT and R-QC briefs together. It reviewed after Phases 0 to 3 had merged (main at e82bb7f). It read:

- `docs/decisions/D-0018_rulings-on-elo-9-questions.md`;
- `docs/specs/SPEC-L0_fide-reference-engine_v1_5.md`, against `docs/specs/SPEC-L0_fide-reference-engine_v1_4.md`;
- E20 with its report and replay scripts, its aggregate, `src/layer0_greats/`, the fixture tool and the fixtures;
- the proposal's front matter, Appendix F and Appendix I, and the annex's front matter and T1's guard row;
- README's licence section and `docs/LICENSE-docs.md`;
- DATA-PROBE §2.6 and §3 with their script;
- for reference, D-0017, the two rules records, SPEC-GREATS, the three aggregates that carry R83's label, `tools/data/politeness.py` with the fetch tools, and the session's tests.

The rulings R80–R89 were given as fixed, with points on the rulings themselves to be listed separately. It was told to read no result of either 2026 championship, to use no web access and to fetch nothing. It changed no file, and every script it ran reproduced the committed outputs byte for byte. It returned eight findings (five major, three minor), seven points for the architect and a list of what it checked and found correct. Its report is reproduced verbatim below, after what the executor did with it.

### Verification performed by the executor

- **ELO10-STAT-1 was recomputed by the extraction** before anything changed in the text. `calibration` in `analysis/e20_greats_replay_extract.py` now also splits the check by how SPEC-GREATS §2 selected the players, and `selection_groups` splits the difference on the last list in the same way. The figures equal the reviewer's to the fourth decimal:
  - the 14 ranked 1st to 3rd only on the lists to April 2000: 3,186 games; −0.0265 (−0.0346 to −0.0184) under table 8.1.2 and +0.0175 (+0.0090 to +0.0261) under the 2025 table; mean difference +17.21;
  - the 15 others: 6,186 games; +0.0000 (−0.0084 to +0.0084) and +0.0445 (+0.0357 to +0.0533); +36.40.
  - The pooled check is unchanged: −0.0090 and +0.0353 on 9,372 games, which do include the thin periods' games.
- **ELO10-QC-1.** The fixtures were counted by script. `tests/fixtures/` holds 1,346 game rows, of which 12 are the synthetic event's, so 1,334 are quoted from FIDE's pages: 79 + 5 + 923 in `fide_calculator/`, 231 in `fide_greats/`, 30 in `fide_history/` and 66 in `validation/`. It also holds 32 cases of FIDE's online calculator. F-N01 records a FIDE ID, a year of birth and an event.
  - 2026-10-12 (session ELO-11): F-N01's FIDE ID, year of birth and event are now placeholders (`docs/DECISIONS.md`, item 7).
- **ELO10-STAT-2.** E20 §4.2's readings table did carry each reading's mean difference and range.
- **ELO10-QC-2.** By `selection_groups`, the 14 players hold 679 of the 1,765 player-periods replayed, 5,673 of the 18,355 games and 5 of the 9 thin periods. Their names are Beliavsky, Gelfand, Huebner, Jussupow, Karpov, Korchnoi, Ljubojevic, Mecking, Portisch, Shirov, Short, Sokolov, Timman and Vaganian.
- **ELO10-QC-3.** This is session ELO-10's Phase 1 measurement: of Freeze 2's 89 entries, 83 equal E3's record and 6 differ.
  - Two of them, `tools/checks/check_outputs.py` and `tools/set_results.py`, were changed as D-0011 part B and D-0012 authorise.
  - The other four were re-pointed to each new version of SPEC-L0, and no decision record authorises those changes:
    - `analysis/l0_ratification_check.py` and its output `analysis/OUTPUT_L0_ratification.md`;
    - `analysis/l0_fixtures_report.py` and its output `analysis/OUTPUT_L0_fixtures.md`.
  - The changes came in commit 5ce9fe5 (PR #44, merged 2026-10-11T06:40:24Z), 4ceeed0 (PR #55, 14:36:49Z) and c0aa1d9 (PR #57, 16:00:41Z).
  - Each changed only the version the files name and the ratification output's status line. That output also gained the test module R63 added, in its rows R-14a, R-22b and R-25.
  - Pointed at v1.5, the frozen script's own code finds the rule met, with only R-12's row changing. A new test does this without editing the frozen script.
- **ELO10-QC-4.** The five places that said "to October 2018" were confirmed: SPEC-L0 v1.5's status line, its §11, F-H07, E20 §4.2 and `round_change_up`.
  - The archive record's §1 is the text of 2017 "with amendments effective from 1 February 2021". The repository therefore holds no text dated 2018.
- **ELO10-STAT-3.** E20's lists aggregate already recorded, on the lists computed without a printed copy, the shares of 3rd place of December 2015 and December 2017; nobody is in the set only through them. SPEC-GREATS' selection aggregate counts 121 printed and 23 computed lists from July 2000.
- **ELO10-QC-5.** Each slip was confirmed. By OlimpBase's list dates, the supplementary lists are July 1978 and July 1979 in the 1970s, and July 1980 in the 1980s.
- **The checks after the fixes.**
  - Every script that needs `data/` and that the fixes touch reproduces its committed output byte for byte: the replay, the rules record, the selection, the lists and the fixtures.
  - (a) every other script reproduces its committed output; Freezes 3a to 3d hold.
  - (b) 685 tests pass.
  - (c) every reference resolves.
  - (d) the body has 4,499 words and the brief 900.

### Disposition

**fixed** (where), **fixed in part** (what remains, and for whom), or **answered**. Points on the rulings themselves go to the architect (below); none of R80–R89 was reopened.

| ID | Sev. | Topic | Status |
|---|---|---|---|
| ELO10-STAT-1 | major | the caveat's premise against the check; the selection effect differs in sign within the sample | fixed: E20 §5 prints, below the check, the same check and the difference on the last list for the players ranked 1st to 3rd only on the lists to April 2000 and for the others, with one sentence that the selection's effect is not common to the sample, so that the order of the two tables depends on the mix; "for the players together" in §5 and §7; "every game of FIDE's 1,774 pages, the thin periods' included" in place of "every replayed game"; R81's caveat kept word for word; its premise to the architect |
| ELO10-QC-1 | major | "only aggregates and differences are committed" | fixed: one wording in DATA-PROBE §2.6 and §3's FIDE row, E20's status line and Appendix I. What is committed of FIDE's material is aggregates and differences, the single published ratings E20 names (R72, R77) and fixed samples of FIDE's calculations kept as test fixtures, quoted value by value for verification (SPEC-L0 §6; R10, R63, R79, R80). The list of every kind, with its counts, is in the operator's inventory for the request. R84's own words go to the architect |
| ELO10-STAT-2 | major | the backward replay's means and ranges in §4.2 | fixed: §4.2's readings table keeps the thin periods, player-periods and games; the mean difference and range under each reading print in §5, under its label, as R80 (iv) and R81 (iii) ask together; the test now checks that they appear in §5 only |
| ELO10-QC-2 | major | 14 of the 29 replayed players selected through OlimpBase's lists | fixed in part. E20 §4 states that the replayed set is SPEC-GREATS §2's selection, resting on OlimpBase's transcription for the 14, with their share of periods, games and thin periods, and labels the selection's figures. Appendix I's replay paragraph and E20 §5's groups carry the label. F.3 no longer calls the replayed players "ranked 1st to 3rd on FIDE's lists". The report and the tests read the selection's names and counts from the aggregates instead of holding them. This addendum carries the label for the ELO-9 addendum, and the test now checks the file. README states the replayed set's footing. Not done: the replay's values (E20 §4 and §5, Appendix I's replay, F.3, `analysis/aggregates/E20_greats_replay.json`), computed on FIDE's pages and files, carry no label. Whether figures computed on FIDE's data for a sample chosen through OlimpBase's lists are "derived" is R83's scope, for the architect |
| ELO10-QC-3 | major | Freeze 2's record out of date; the ratification output describes v1.4 | fixed: the four changes are recorded, with their commits, merge times and what changed, in the sentence `analysis/e3_freeze2_record.py` prints in E3 and in this addendum. SPEC-L0 v1.5 states that check (a)'s ratification output is computed on v1.4. `tests/test_spec_l0_ratification_v1_5.py` applies the rule to v1.5 with the frozen script's own code, and the rule is met; only R-12's row changes. v1.4 is left unchanged, as the file the frozen scripts read. Whether the four files stay as they are is for the architect |
| ELO10-QC-4 | minor | FIDE's 2018 practice stated beyond the evidence | fixed. "To the list of July 2018 (FIDE's output; R80 extends it to October 2018)" now stands in SPEC-L0 v1.5's status line, §11, F-H07 and F-H10, in E20's brief, §4.2 and §7, and in the module's docstrings. The text in force in 2018 is marked NOT VERIFIED in SPEC-L0 §11 and F-H10, E20 §4.2 and §7, the rules record's §5 and the module. F-H07's span is given: November 2018 to December 2019 in the greats' replay, and from February 2020 in E17's (January 2020 read by neither). "And of the 2007 text's half point" is restored to E20's brief |
| ELO10-STAT-3 | minor | from July 2000 a shared place still counts where no printed copy survives | fixed, from the aggregates, which already held these shares: E20's brief, §2's notes and §7, and Appendix I's "Who", now say that from July 2000 FIDE's printed order decides where a printed copy survives (121 of 144 lists). On the other 23 the rank is computed and a share counts (December 2015, December 2017), though no player is in only that way. R82's words go to the architect |
| ELO10-QC-5 | minor | wording slips | fixed: the annex's front matter (the R80–R89 clause after the relative clause); Appendix F's "ruling R86 of D-0018"; Appendix I's "a standard rating period on FIDE's calculations index"; DATA-PROBE §4's supplementary lists by decade (2 in the 1970s, 1 in the 1980s); E20's brief, "as OlimpBase transcribes them" |

### For the architect

1. **R81 (ii), the caveat's premise** (the reviewer's point 1): "their results run ahead of any forecast" asserts the sign of the selection's effect.
   - Table 8.1.2's residual on these games is −0.009 (−0.017 to −0.001).
   - The two groups of players sit 0.027 apart.
   - E20 now prints the split beside the caveat, which keeps R81's words.
2. **R83's scope** (point 2): are figures computed on FIDE's data, for a sample chosen through OlimpBase's lists, themselves derived from its transcription? The executor has labelled the selection's own figures, and not the replay's values.
3. **R84's words** (point 3): "only aggregates and differences are committed" leaves out the fixtures and the single published ratings, which the documents now name. The request "disclosing the use" would list them.
4. **R80 (ii), "while the words did not"** (point 4): the text in force in 2018 is not transcribed, and is now marked NOT VERIFIED wherever the documents say so.
5. **R82, "From July 2000 FIDE's printed order decides"** (point 5): this holds on 121 of the 144 lists from July 2000. On the other 23, shares of 3rd place counted twice, without bringing anyone in.
6. **R86 (2)** (point 6): "the same rounding words … the list of January 2009 is the exception" joins lists under different texts. F.3 keeps the ruling's wording.
7. **Freeze 2** (point 7, and D-0018 reading 5): four of its files were changed after the tag without a record. Decide whether to record the changes, revert them or re-point the files.
   - Reverting the files to the tag would make `analysis/l0_ratification_check.py` read SPEC-L0 v1.1, which the repository no longer holds.

### Errata

**REDTEAM_v0_1's totals and the ELO-4 count** (D-0018, corrections 2 and 3).
- `docs/review/REDTEAM_v0_1.md` is a record and is not edited.
  - Its totals line reads "30 findings; 5 blockers, 17 majors, 8 minors".
  - Its rows give 30 findings: 6 blockers (R-STAT-1, R-STAT-2, R-QC-1, R-QC-2, R-QC-3, R-EXPLOIT-1), 17 majors and 7 minors.
  - The rows are the reference.
- The ELO-4 session log (the operator's files) counts 17 findings in `docs/review/REDTEAM_v0_4.md`.
  - The record lists 15: 6 blockers, 5 majors and 4 minors, in its disposition table and in the reviewer's verbatim report alike.
  - The record is the reference.

### OlimpBase's label for the ELO-9 addendum

Ruling R83; D-0018, reading 11 (d). The ELO-9 addendum above states figures that rest on OlimpBase's transcription of FIDE's lists:
- in the executor's verification: ELO9-STAT-3's players with their lists, and ELO9-STAT-5's numbers of windows;
- in the reviewer's report, which is reproduced verbatim and not edited: ELO9-STAT-3, ELO9-STAT-5 and, under "Checked and correct", the dominance table and the comparison of OlimpBase's lists with FIDE's files of 2001.

This addendum also states such figures: the names of the 14 players and their share of the replay, in the verification above and in the reviewer's report below, which carries its own label lines. For all those figures: Derived from OlimpBase's transcription of FIDE's lists; non-commercial use only; not covered by this repository's CC BY 4.0 or Apache-2.0 licences.

### The reviewer's report (verbatim)

The report is reproduced as returned, from its first heading, its section headings set two levels lower to sit under this addendum. One code span, a test's pytest node ID, is split in two at its "::" so that the reference check (check (c), `tools/checks/check_refs.py`, a file of Freeze 2) can resolve its path; no word is changed.

#### Findings

##### ELO10-STAT-1 — major — The caveat claims a lift that the check itself contradicts, and the selection effect has opposite signs within the sample

**Location:** `docs/evidence/E20_greats.md` §5 (the check's table and the paragraph below it) and §7 (fifth limit); `analysis/e20_greats_report.py` (`fits`, `caveat`). The caveat's words are R81 (ii)'s.

**Problem.** Below the check, E20 prints: "On these games, the favourites' results sit nearer table 8.1.2 than the 2025 table … The players were chosen because they reached the top three, so their results run ahead of any forecast. That lifts both tables' residuals alike; a lift above 0.013 a game would reverse which table sits nearer the results."

The row directly above reads, for table 8.1.2, "−0.009 (−0.017 to −0.001)". On these games the favourites score *below* 8.1.2's forecast, and the interval excludes zero. "Their results run ahead of any forecast" is contradicted by the very check it introduces.

I split the same 9,372 games by when the player entered the set. A scratch script imported `prepare()` and repeated `calibration()`'s selection and player clustering exactly. It reproduces the pooled figures: −0.0090 (−0.0172 to −0.0008) and +0.0353 (+0.0269 to +0.0438).

| players | games | table 8.1.2 | the 2025 table |
|---|---|---|---|
| the 14 replayed players whose every top-3 list is on lists to April 2000 | 3,186 | −0.0265 (−0.0346 to −0.0184) | +0.0175 (+0.0090 to +0.0261) |
| the other 15 | 6,186 | +0.0000 (−0.0084 to +0.0084) | +0.0445 (+0.0357 to +0.0533) |

- **Not a level effect.** In every level band with at least 30 games in each group, the first group sits below the second under 8.1.2: 2300–2399 −0.035 against +0.076; 2400–2499 −0.013 against +0.049; 2500–2599 −0.040 against +0.029; 2600–2699 −0.011 against +0.003; 2700–2799 −0.054 against −0.015.
- **The two groups point opposite ways.**
  - The 14 were chosen long before the window. Their results run behind forecast, and the 2025 table already sits nearer them (|+0.018| < |−0.027|). Their midpoint is −0.0045, which `caveat()` refuses to print.
  - For the 15 others, 8.1.2 fits (0.000).
- **Consequences for the printed sentences.**
  - The lift is not common to the sample. The two groups differ by 0.027 a game under either table, about twice the printed threshold. A single "lift above 0.013" therefore does not describe this sample.
  - "On these games, the favourites' results sit nearer table 8.1.2" is true only for the 29 pooled.
- **The same split runs through §5's comparison.** The mean difference on the last list is +17.21 for the 14 and +36.40 for the 15 (per-player values from `E20_greats_replay.json`; 14 × 17.21 + 15 × 36.40 = 29 × 27.14).
- **The threshold's arithmetic is right.** (−0.0090 + 0.0353) / 2 = 0.01315, printed as 0.013. A common lift δ reverses the order exactly when δ > 0.01315.
- **Separately, "every replayed game" is not quite right.** §5 says "On every replayed game", but `calibration()` reads every game on the 1,774 pages. Of the 9,372 games, 70 lie in the 9 thin periods, which are not replayed.

**Fix.**
- Keep R81's words.
- Below the check, print (from the extraction) the same check and the mean difference split by when the player entered the set: all top-3 lists to April 2000, or a top-3 list from July 2000.
- Add one sentence: the selection's effect differs in sign between players chosen before the window and players chosen in it, so the pooled order of the two tables depends on the mix.
- In §5 and §7, scope "sit nearer table 8.1.2" to "the 29 together".
- Replace "every replayed game" with "every game on FIDE's pages".
- The caveat's premise goes to the architect (below).

For the figures of this finding that rest on the lists to 2000: Derived from OlimpBase's transcription of FIDE's lists; non-commercial use only; not covered by this repository's CC BY 4.0 or Apache-2.0 licences.

##### ELO10-QC-1 — major — "Only aggregates and differences are committed" is not what the repository commits

**Location:** `docs/research/DATA-PROBE_greats.md` §2.6 and §3 (FIDE's row); E20's status line (data paragraph); Appendix I, "The data, and their limits".

**Problem.** The four places say:
- §3's row: "until FIDE answers nothing changes: the pages and files are analysed from the local cache (gitignored) and never redistributed, and only aggregates and differences are committed (R72, R84)".
- §2.6: "FIDE's data are analysed and never redistributed in bulk; only aggregates and differences are committed".
- E20 and Appendix I: "only aggregates and differences are committed".

The repository commits FIDE's per-game values as test fixtures:
- **Game rows.** Counted by script over `tests/fixtures/`, there are 1,334 game rows quoted from FIDE's calculation pages and tournament report, each with the opponent's rating, the score and FIDE's change:
  - fide_calculator: 79 + 5 + 923;
  - fide_greats: 231 in 16 cases (one period appears twice, as F-G03 and F-G11);
  - fide_history: 30;
  - validation: 66.
- **Calculator cases.** There are also 32 cases from FIDE's online calculator.
- **A named player.** `published_initial_rating.json` (F-N01) records a player's FIDE ID, birth year and event.
- **Added this session.** F-G15 (8 games) and F-G16 (19 games) were added in this session (Phase 2), after R84's "Until FIDE answers nothing changes"; R80 (iv) asked for them.

E20 itself also commits single published ratings: the peaks in §2 and §5's "highest under FIDE's rules". Its §4 says "a sample of sixteen cases … is kept as test fixtures", which contradicts its own status line. §2.6 ("in bulk") and §3 ("never redistributed") also disagree with each other.

R84 asks that the permission request disclose the use. The repository's own description of that use leaves out the fixtures.

**Fix.**
- In all four places, say what is committed:
  - aggregates and differences;
  - the single published ratings named by SPEC-GREATS §4 and §6, R72 and R77;
  - the fixed samples of FIDE's per-player calculations kept as test fixtures (R10, R63, R79, R80; `tests/fixtures/`), quoted value by value for verification.
- Use one wording in §2.6 and §3.
- Give the operator that list for the request.
- The ruling's own words go to the architect.

##### ELO10-STAT-2 — major — §4 prints the backward replay's mean and range outside §5 and without its label (R81 (iii))

**Location:** E20 §4.2, the "readings and the thin periods" table; E20's "In brief"; Appendix I; `tests/test_d0018_rulings.py`::`test_r81_the_backward_replay_has_no_headline_and_its_figures_stay_in_section_5`.

**Problem.** R81 (iii) says "+27.0, its range and the per-player figures under the 2025 table appear only in E20 §5, under its label", and R81 (i) makes §4 a headline section.

§4.2's table nonetheless carries the columns "mean difference, last list | range":

| reading | mean difference, last list | range |
|---|---|---|
| R80 | +27.14 | −9 to +62 |
| D-0017 | +27.03 | −9 to +62 |
| rules record | +27.07 | −10 to +62 |
| towards +∞ throughout | +26.69 | −9 to +61 |

The table is introduced only as "The replay under each reading of the rounding, for Layer 0 and rung 2 alike", with no "applied backwards, not fitted on that era" beside it.

As a result, two statements about the page are untrue:
- E20's brief: "Its figures … are in §5 only."
- Appendix I: "its figures, and the caveat on reading them, are in E20 §5 only."

The test checks only the brief and the appendix, not §1–§4 or §6–§7.

**Fix.**
- R80 (iv) asks only that E20 print §5's comparison under both readings. Print the mean difference and range under each reading in §5, under the label.
- Keep the thin periods, player-periods and games in §4.2.
- Extend the test so that the two-decimal means and the ranges appear in no section but §5.

##### ELO10-QC-2 — major — 14 of the replay's 29 players were selected through OlimpBase's lists; the labels and README treat §4–§5 as free of it

**Location:** README's licence section (E20 "(its brief, §1 to §3 and §7)"); D-0018 reading 11 ("The replay of 2008–2019 rests on FIDE's pages and FIDE's own files"); E20 §4 ("What is replayed") and §5; Appendix I, "The replay, 2008–2019"; the opening of F.3; `analysis/aggregates/E20_greats_replay.json` (no `terms`); `tests/test_d0018_rulings.py`; `analysis/e20_greats_report.py`; `docs/review/REDTEAM_v1_0.md`.

**Problem.** The claim is sound for the replay's values but not for its sample.

- **Values: sound.** The only place the replay reads the 1971–2000 series is `reached`, for the K rules' "ever 2400 / ever 2300" flags. No replayed player's flag changes when the lists before 2001 are dropped. I checked all 29: each player's first 2400 on FIDE's own files falls before it is needed, or, for Ding and Giri, the series starts after 2001 anyway.
- **Sample: not sound.** Reading 11 counts "the selection" as derived.
  - 14 of the 29 replayed players have every top-3 list on lists to April 2000, all computed on OlimpBase's transcription: Beliavsky, Gelfand, Huebner, Jussupow, Karpov, Korchnoi, Ljubojevic, Mecking, Portisch, Shirov, Short, Sokolov, Timman and Vaganian.
  - They hold 679 of the 1,765 replayed periods, 5,673 of the 18,355 games, 5 of the 9 thin periods and 3,186 of the calibration check's 9,372 games.
  - Which opponents count as "inside the set" (replayed rather than held at FIDE's ratings) follows from the same selection.
  - §5's mean difference is +17.2 for these 14 and +36.4 for the rest (ELO10-STAT-1).

Whatever the architect decides, some figures are unlabelled under any reading:
- Appendix I's replay paragraph opens "Of the 36, 29 have rated games in the window". It sits after the "Who" label, which covers only "this paragraph".
- E20 §4 names those "who have no FIDE ID" (on OlimpBase's lists).
- `tests/test_d0018_rulings.py` and `analysis/e20_greats_report.py` hard-code R82's names or the count 36, and README does not name either file.
- `REDTEAM_v1_0.md` still carries no label. Reading 11 (d) leaves it to this session's addendum, and `test_r83_every_file_with_olimpbase_derived_figures_carries_the_label_and_readme_names_it` skips the file, so nothing will check the addendum.
- F.3 opens "Replaying the players ranked 1st to 3rd on FIDE's lists". It is 29 of the 36, and for 14 of them the ranks were computed on OlimpBase's transcription, not printed by FIDE.

**Fix.**
- State in E20 §4 and in README that the replayed set is SPEC-GREATS §2's selection, which rests on OlimpBase's lists for 14 of the 29.
- Then do one of the following:
  - **(a) Treat §4–§5 as derived.** Label §4–§5, Appendix I's replay paragraphs, F.3 and `E20_greats_replay.json` (with a `terms` field), and name them in README.
  - **(b) Record a reading.** Record the architect's reading that a sample's membership does not make figures computed on FIDE's data "derived".
- In either case:
  - label "Of the 36" and E20 §4's sentence;
  - name the two code files in README or reword them;
  - carry the label in this session's addendum, and make the test check it.

For the figures of this finding that rest on the lists to 2000: Derived from OlimpBase's transcription of FIDE's lists; non-commercial use only; not covered by this repository's CC BY 4.0 or Apache-2.0 licences.

##### ELO10-QC-3 — major — Freeze 2's record is out of date (six of its files differ from the tag, not two), and the live ratification check reads v1.4

**Location:** `docs/evidence/E3_us-championship-2026.md`, the Freeze 2 static record printed by `analysis/e3_freeze2_record.py`; D-0018 reading 5; `analysis/l0_ratification_check.py` (`SPEC` = v1.4).

**Problem.** E3 says: "As at D-0012, two of the files differ from their hash here: `tools/checks/check_outputs.py` … and `tools/set_results.py`."

I hashed every file path of the record at HEAD. Six of the 87 files differ: the two named, plus:
- `analysis/l0_ratification_check.py`
- `analysis/OUTPUT_L0_ratification.md`
- `analysis/l0_fixtures_report.py`
- `analysis/OUTPUT_L0_fixtures.md`

`git log freeze-2..HEAD` shows these four changed in three commits, each re-pointing SPEC-L0 (v1.1 → v1.2 → v1.3 → v1.4):
- 5ce9fe5 (#44, ELO-8), whose message says "no frozen file changes (checks (a) and (a′) hold)";
- 4ceeed0 (#55);
- c0aa1d9 (#57).

These are exactly the four citations that led reading 5 to keep v1.4. The ELO-10 brief says Freeze 2's files "never change … the rule alone protects them". Reading 5 sends "how those four files came to cite v1.4" to the close-out, which lies outside the repository. No file in the repository records it.

As a consequence, check (a)'s ratification output describes v1.4, not the current specification:
- I pointed the same script at v1.5 in scratch. It meets the rule ("The pre-agreed ratification rule is met: True"); the only change is R-12's NOT VERIFIED column, False → True.
- v1.4 still reads "Status: RATIFIED", with no pointer to v1.5.

None of this touches the championship comparison: Freeze 3a's live manifest of 51 files holds.

**Fix.**
- Record the four changes (commits, dates, what changed) in this session's review addendum and in the sentence `analysis/e3_freeze2_record.py` prints. That script is in no freeze.
- State in v1.5 that check (a)'s ratification output is computed on v1.4.
- Add a non-frozen test that applies the ratification rule to v1.5.
- Whether the four files stay as they are is the architect's call.

##### ELO10-QC-4 — minor — SPEC-L0 v1.5 and E20 state FIDE's 2018 practice beyond the evidence and without the labels it needs

**Location:** SPEC-L0 v1.5's status line, §11's opening paragraph, and the F-H07 and F-H10 rows; E20 §4.2 and its brief; `src/layer0_greats/__init__.py` (`round_change_up`); the rules record §5.

**Problem.**

(a) **FIDE's output is overstated to October 2018.** The texts say:
- status line: F-H10 records "the rounding FIDE's lists followed from July 2014, towards +infinity to October 2018";
- §11: "the rounding the same replay read on FIDE's lists from July 2014, towards +infinity on every list to October 2018";
- F-H07's new clause: "on the lists of July 2017 to October 2018 FIDE rounded the same words towards +infinity";
- E20 §4.2: "Ruling R80 adopts what FIDE's lists show, towards +∞ to October 2018";
- `round_change_up`'s docstring: "FIDE's lists to October 2018 follow it".

FIDE's output shows towards +∞ only up to July 2018. The lists of August to October 2018 hold 24 periods (6 + 13 + 5, from the aggregate) and no negative half point. F-H10 itself rightly marks the list of the switch (August to November 2018) NOT VERIFIED. "To October 2018" is R80's rule for Layer 0, not something observed in FIDE's lists.

F-H07's "it holds on FIDE's lists from November 2018" also covers January 2020, which neither replay reads: E20 ends in December 2019, and E17's first list is February 2020.

(b) **"The words did not change" is unverified.** This appears in F-H10 ("from November 2018 FIDE's arithmetic changed while the words did not"), E20 §4.2 ("while the words did not") and the rules record §5 ("the words unchanged"). The repository transcribes the 2014 text, and the 2017 text only as "Effective from 1 July 2017 (with amendments effective from 1 February 2021)" (archive record §1). The text in force in 2018 is not transcribed, and no NOT VERIFIED label goes with the claim (CLAUDE.md rule 3).

(c) **E20's brief drops part of R80 (i)'s label.** The brief labels only "the reading of Rn as the rated player's new rating". R80 (i) also keeps the 2007 text's half point NOT VERIFIED, as E20 §4.2 and F-H09 do.

**Fix.**
- In the five places, write "towards +infinity to the list of July 2018 (FIDE's output; R80 extends it to October 2018)".
- Mark the 2018 wording NOT VERIFIED: it is known only from the 2014 copy and from the 2017 text as amended from 1 February 2021.
- Restore "and of the 2007 text's half point" to E20's brief.

##### ELO10-STAT-3 — minor — The asymmetry's source is misstated: from July 2000 a shared place still counts on the 23 lists without a printed copy

**Location:** E20's brief, §2 (notes) and §7 (first limit); Appendix I, "Who". These sentences follow R82's wording.

**Problem.** E20 says "from July 2000 FIDE's printed order decides" and "takes from July 2000 the rank FIDE printed". SPEC-GREATS §2 does something narrower. Wherever no printed copy of a list survives, it computes the rank from FIDE's full list, with "players tied sharing a rank". That applies to 23 of the 144 lists from July 2000 (`computed_dates_from_2000_07` in `GREATS_players.json`).

I reran the rule's `computed()` on those 23 lists. It finds two shares of 3rd place:
- December 2015: Anand and Kramnik, both at 2796;
- December 2017: Caruana and Mamedyarov, both at 2799, which is Mamedyarov's first top-3 list.

None of these players is in the set only through a share: each has many other top-3 lists (Mamedyarov 14). So the six names and Svidler stand. On the printed list of October 2006 Svidler is 4th on Kramnik's 2750; the printed lists from July 2000 hold 9 such cases in all.

But the asymmetry's stated source is wrong: it is printed lists against computed ranks, not before and after 2000.

**Fix.**
- Write "from July 2000 FIDE's printed order decides where a printed copy survives (121 of 144 lists); on the other 23 the rank is computed and a share counts, as before 2000 (December 2015, December 2017), though no player is in only that way".
- Compute this in the lists aggregate.

For the figures of this finding that rest on the lists to 2000: Derived from OlimpBase's transcription of FIDE's lists; non-commercial use only; not covered by this repository's CC BY 4.0 or Apache-2.0 licences.

##### ELO10-QC-5 — minor — Wording slips

- **Annex front matter (line 5).** The insertion leaves "…and by the rulings R80–R89 of session ELO-10 (…), whose executor's readings are cited as "D-0009, reading n", "D-0011, reading n" and "D-0012, reading n"". The relative clause now attaches to R80–R89.
  *Fix:* put the R80–R89 clause after the relative clause.
- **Appendix F.** It says "founder defaults: D-0008, R14; D-0014, R64; and D-0018, R86". D-0018 marks only R83, R84, R85 and R89 as founder decisions.
  *Fix:* write "and ruling R86 of D-0018".
- **Appendix I.** "Of the 36, 29 have rated games in the window." E20 §4 shows only that Fischer, Spassky, Kasparov and Salov "have no standard rating period on FIDE's calculations index in the window".
  *Fix:* use E20's words.
- **DATA-PROBE §4, row 1971–1989.** It says "11 lists in the 1970s, 3 of them supplementary, 20 in the 1980s". Counting `PROBE_greats.json`'s list dates from July 1971: 2 of the 11 in the 1970s are supplementary (July 1978, July 1979), and 1 of the 20 in the 1980s (July 1980).
  *Fix:* write "2 of them supplementary, 20 in the 1980s, 1 of them supplementary".
- **E20's brief.** "Kasparov … is absent from FIDE's lists of January 1994 and July 1994 (§2)" drops §2's "as OlimpBase transcribes them", although OlimpBase's transcription is NOT VERIFIED before 2001.
  *Fix:* restore the words.

For the figures of this finding that rest on the lists to 2000: Derived from OlimpBase's transcription of FIDE's lists; non-commercial use only; not covered by this repository's CC BY 4.0 or Apache-2.0 licences.

#### For the architect

1. **R81 (ii), the caveat's premise.** "The players were chosen because they reached the top three, so their results run ahead of any forecast" asserts the sign of the selection effect.
   - Table 8.1.2's own residual on these games is −0.009 (−0.017 to −0.001).
   - The 14 replayed players chosen only on lists to April 2000 run 0.027 behind it, while the 15 others sit at 0.000.
   - A single threshold for a "common" lift (0.013) therefore does not describe this sample.

   Consider a caveat that does not assert the sign, and allowing E20 to print the split (ELO10-STAT-1).
2. **R83's scope.** Are figures computed on FIDE's data, for a sample chosen with OlimpBase-derived ranks, themselves "derived from OlimpBase's transcription"? This covers E20 §4–§5, Appendix I's replay paragraphs, F.3 and `E20_greats_replay.json`.
   - 14 of the 29 replayed players are in the sample only through OlimpBase's lists.
   - Their mean difference is +17.2 against +36.4 for the others.

   Under R83's non-commercial terms, the answer decides what CC BY 4.0 may cover.
3. **R84's words "only aggregates and differences are committed".** These sit against:
   - the fixtures that R10, R63, R79 and R80 (iv) commit: 1,334 game rows quoted from FIDE's pages, and F-N01 with a FIDE ID, birth year and event;
   - the single published ratings that R72 and R77 keep.

   The request "disclosing the use" should list them. The FIDE row also omits "disclosing the use", not only "by the operator" (reading 12 noted only the latter). FIDE's footer requires written permission for storing, and the local cache stores before permission. R84 accepts this, but a reader from the QC will see it.
4. **R80 (ii), "from November 2018 FIDE's arithmetic changed while the words did not".** The repository holds the 2014 text and the 2017 text with the amendments of 1 February 2021, not the text in force in 2018. Consider NOT VERIFIED for the words in force in 2018.
5. **R82, "From July 2000 FIDE's printed order decides".** This holds on the 121 lists with a printed copy. On the other 23, the rule computes ranks with shared places: there are shares of 3rd in December 2015 and December 2017, and no player is in only that way.
6. **R86 (2), "the same rounding words were applied two ways … the list of January 2009 is the exception".** This joins lists under different texts.
   - Before July 2014, the 2007 and 2010 texts round the new rating "to the nearest 1 or 0", and the 2007 text states no half point.
   - The list of January 2009 ran under the 2007 text, not under the 2014/2017 words.

   F.3 reproduces the ruling's wording. Consider: "the 2014 and 2017 words were applied two ways (towards +∞ to July 2018, away from zero from November 2018); before July 2014, under the 2007 and 2010 texts, FIDE's lists rounded negative half points towards +∞ except on the list of January 2009".
7. **Reading 5 and Freeze 2.** Four Freeze 2 files were edited after the tag (#44, #55, #57). Decide whether to record, revert or re-point them. Until then, check (a)'s ratification output describes v1.4.

#### Checked and correct

**Reproduction.**
- Byte-identical regeneration into scratch (repository untouched; `git status` clean throughout):
  - `analysis/aggregates/E20_greats_replay.json` (34 s);
  - `tests/fixtures/fide_greats/published_periods.json`;
  - `GREATS_players.json`;
  - `PROBE_greats.json`;
  - the rules record 2001–2017;
  - E20;
  - `analysis/OUTPUT_E20_appendix.md`;
  - DATA-PROBE.
- Appendix I (proposal lines 663–696) equals `OUTPUT_E20_appendix.md` verbatim.
- Automated checks:
  - (a) passes, with Freeze 3a's 51 files equal to D-0012's manifest;
  - (a′), (a″) and (a‴) pass;
  - (c): 73 files, 0 unresolved;
  - (d): body 4,499 and brief 900.
- 683 tests pass. STATUS.md's figure of 672 is for the close-out to update.
- None of the session's 45 changed paths is in E3's Freeze 1 or Freeze 2 hash tables or in E13's.
- Nothing was fetched: the newest manifest entry is 2026-10-11T14:13:01Z.

**R80 implementation.**
- `round_change` applies `round_change_up` (floor(x + 0.5)) for lists before "2018-11" and `round_change_away` from it.
- `round_change_d0017` keeps D-0017's reading, with its boundary at "2014-07".
- The list of January 2009 gets no exception.

**The four readings.** E20's counts reproduce from the per-era rows (1,766 periods with no gap in FIDE's files, plus 8 periods checked against the next file; 1,774 pages in all):

| reading | periods reproduced (sum of the four era rows) | thin periods |
|---|---|---|
| R80 | 825 + 530 + 215 + 187 | 9 |
| D-0017 | 825 + 513 + 205 + 187 | 36 |
| rules record | 798 + 513 + 205 + 187 | 63, plus a two-period gap stretch = 65 |
| towards +∞ throughout | 825 + 530 + 215 + 175 | 21 (= 36 − 27 + 12) |

- The rules-record reading's own `thin_by_cause` sums to 64 because it counts that stretch once; it is not printed.
- Under R80 and D-0017 the mean differences are +27.14 and +27.03.

**Negative half points.**
- Totals: 33 + 17 + 10 + 12 = 72. By year, 57 went towards +∞ and 15 away from zero.
- From July 2014, 27 went towards +∞ (the last on 2018-07) and 12 away from zero (the first on 2018-11).
- On 2018-07, F-G15's period is the only one. On 2018-11 there are two, and F-G16 is the lower FIDE ID.
- Before July 2014:
  - every negative half point went towards +∞ on 22 of the 23 lists that hold one;
  - on January 2009, 3 of 3 went away from zero;
  - of the 78 half points, towards +∞ reproduces 73 (30 + 43) and away from zero 46 (3 + 43);
  - 2 of the 5 exceptions are exact in floating point.
- The "switch's list NOT VERIFIED" claim is supported: August, September and October 2018 hold 6, 13 and 5 periods, none ending in a negative half point, and positive half points cannot discriminate between the two roundings.
- R80 (iv)'s disclosure is present in E20 (brief, §4.2, §7), Appendix I, F-H10 and §11 of SPEC-L0, the rules record §5 and `layer0_greats`' docstring.

**F-G15 and F-G16.**
- F-G15: list 2018-07, sum −1.50, published −1; one tournament, 8 games.
- F-G16: list 2018-11, sum −1.50, published −2; two tournaments, 19 games.
- Both were chosen by the assembler's code exactly as reading 4 states.
- The sample is 16 cases and 15 player-periods (F-G03 = F-G11), within R79's 30.

**SPEC-L0 v1.5 against v1.4.**
- The diff touches only: the title; the status and author lines; R-12's label; §8's note and Q-12; §11's heading and opening paragraph; and the F-H07, F-H09 and F-H10 rows.
- No rule of §3 changes beyond R-12's label.
- Q-12 is coherent with R-12, and R-12 has its synthetic test.
- F-H10's three quotations match the rules record §4 and the archive record §1 and §2.
- F-H09's counts are correct: 78 / 73 / 46; 22 of 23; 3 of 3; one period not a rounding of its sum.
- v1.5 is named by the proposal, the annex, `pyproject.toml`, STATUS, `tests/l0_helpers.py`, the fixtures READMEs and `assemble_tested_readings.py`. v1.4 is named only by the four Freeze 2 files.

**R81.**
- Calibration: 9,372 games and 29 players; −0.0090 (−0.0172 to −0.0008) for 8.1.2 and +0.0353 (+0.0269 to +0.0438) for the 2025 table. The threshold is 0.01315, printed as 0.013.
- R81 (iv)'s and (v)'s sentences are verbatim. The supporting figures check:
  - 936 game rows at 2800 or more and 8,436 at 2700–2799;
  - the 2024 fit window holds 539 and 9 such games [E18 §1];
  - E19 §3 says "a handful of games".
- The brief and Appendix I hold no +27.1, no 2945 and no per-player table, and Appendix I's backward-replay paragraph is two sentences.
- §5's per-player table checks:
  - differences 787 / 29 = +27.14; the table's effect 794 / 29 = +27.38; colour's −7 / 29 = −0.24;
  - with outside opponents at −10 / +10: +17.93 / +36.55, i.e. 0.93 points per point.

**R82.**
- The six names are in E20 and in Appendix I.
- On the printed list of October 2006, Svidler is 4th on Kramnik's 2750; 8 other printed ties at 3rd from July 2000 concern selected players.

**R83.**
- All 11 rendered instances of the label are exact.
- The three aggregates' `terms` field equals the label.
- README's carve-out and `LICENSE-docs.md`'s sentence are present.
- E20 §1's 152,963 of 152,966 equals the sum of the four 2001 lists.

**R84.** The FIDE row's status and why cells carry no date; the "read" cell's 2026-10-11T10:37:05Z is the footer's retrieval time.

**R85.**
- The User-Agent is exact and carries no email.
- The five tools outside the freezes import `politeness`.
- The three frozen tools keep "Mozilla/5.0".

**R86 (F.3).**
- Every number traces to E20 §4.2 or §1: 28 June 2009, 9 July 2009, July 2018, November 2018, 3 of 3, 41 points.
- The raw APR03FRL.TXT holds 2315 for ID 1503014, as the converted file does.
- F.3 cites E20 only.

**R87.** T1's value cell is exact: "2300, 400, 50, 735 (fixed by ruling, R24; PROVISIONAL until set on FIDE's data, R47)".

**The corrections in D-0018.** All four check against the files:
- **REDTEAM_v0_1.**
  - Rows: 30 findings, 6 blockers / 17 majors / 7 minors (R-STAT 2/6/2, R-QC 3/6/1, R-EXPLOIT 1/5/4).
  - Status cells for the 23 blockers and majors: 18 fixed, 1 justified, 4 with two statuses.
  - Status cells for the 7 minors: 4 fixed, 2 justified, 1 with two statuses.
  - The totals line reads 5 / 17 / 8.
- **REDTEAM_v0_4.** 15 findings (6 / 5 / 4), the same in the disposition table and in the verbatim report. The ELO-4 session log in the operator's files does read "17 findings: 7 blockers, 6 majors, 4 minors".
- **E4.** Lines 266 and 429 carry the NOT VERIFIED wording. [VT 3] gives 101 of 101.
- **"Fixed by ruling".** The quotes from E12 and SPEC-TOP100 are exact.

For the figures of this section that rest on the lists to 2000: Derived from OlimpBase's transcription of FIDE's lists; non-commercial use only; not covered by this repository's CC BY 4.0 or Apache-2.0 licences.
