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
