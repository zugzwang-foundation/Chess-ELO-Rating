# Fourth red-team review: proposal v0.4, technical annex v0.4 and brief v0.4

Status: REVIEW RECORD · Session ELO-4, Phase 6 · Date: 2026-10-10 · Reviewer: one subagent briefed with the R-STAT, R-QC and R-EXPLOIT briefs together, reading `docs/proposal/ELO-PROPOSAL_v0_4.md`, `docs/proposal/ELO-TECHNICAL-ANNEX_v0_4.md`, `docs/proposal/ELO-BRIEF_v0_4.md`, `docs/decisions/D-0008_architect-rulings-elo-4.md`, `analysis/OUTPUT_v0_4.md` with its script, the evidence reports E2 and E4 to E7, `analysis/OUTPUT_L1_history.md`, `docs/specs/SPEC-L1_v1_0.md`, `docs/research/PRIOR-WORK_2026-10-10.md`, `docs/research/VERIFICATION_PRIOR-WORK.md` and `docs/review/REDTEAM_v0_3.md`. The rulings R1–R14 were given as fixed; decision-level points were to be listed separately for the architect. The reviewer's text is reproduced verbatim in the second half of this file, with one citation normalised to the checker's form ([VT 1, 3]); the first half records what the executor did with it.

## Verification performed by the executor

- `python3 analysis/v04_calculations.py` reproduces `analysis/OUTPUT_v0_4.md` byte for byte; check (a) reruns every script without data, and the data-dependent extracts changed in this phase (E6, E7) were rerun under check (a)'s environment.
- New analyses run for the review, from the rolling fits of E6 (cached; every earlier section of `analysis/aggregates/E6_rungs.json` unchanged by the rerun): a matched control for rung 5 (169,508 games between two adults, binned by time control, colour and 50-point gap), rung 5 on rung 2's fitted table, the compensation hunter's yield by band, and the farming region at game level with the month-block bootstrap of annex T8.5 and a bootstrap over players (`docs/evidence/E6_rungs-on-history.md` §4, §6). E7 gained the years Ghita's 2025 extract cannot contain (2023, 2024 and 2026; `docs/evidence/E7_cross-border.md`).
- The reviewer's numbers were checked against their sources before each fix; where a finding needed an analysis, the analysis was run rather than the claim reworded.
- After the fixes: proposal body 4,479 words and summary 377 by the strict count, brief 886 words (check (d)); every reference resolves (check (c), which now also resolves `[VP k]` and treats documents marked RATIFIED as records); 541 tests pass (check (b)).

## Disposition

**Part A (D-0008 audit).** The reviewer found twelve rulings APPLIED and two PARTIAL (R7, R8), and listed gaps under several APPLIED ones. Each is closed: the example file of T7.2 now carries γ's open range (R7), the accrual factor (R3), the information-share gate (R5), the spread-ratio review (R1) and schema "pf-0.4"; T7.1's c_j comment uses σ̃_j (R2); eligibility is visible on the list (R8, V4-QC-2); the farming interval is recomputed (R12, V4-EXPLOIT-1); the citation guide defines `[VT k]` (R14); the rung-1 and calculator claims are stated exactly (R10, R14, V4-QC-1). The re-ranking's evidence column is corrected (V4-STAT-3); the floor theme (27 items) is now addressed in §2; rank 4 is labelled as resting on Ghita's count and FIDE's rules, since our own data say less about it. SPEC-L0 §8 Q-1 still cites the earlier fixtures only: a new SPEC-L0 version is needed and is listed for the architect.

**Part B.** Status: **fixed** (where), **fixed in part** (what remains, and for whom).

| ID | Sev. | Topic | Status |
|---|---|---|---|
| V4-STAT-1 | blocker | "outside ±0.01 below 2000" is false: three bands fail | fixed: "in every band below 2400", with the matched control and the band pattern (proposal §1, §6, §9, §10; annex T4.6, T8.1, T8.10; E6) |
| V4-QC-1 | blocker | rung 1 and Appendix F claim every period reproduced | fixed: every game and tournament sum reproduced; the list change in 56 of 58 periods (six after FIDE's base corrections), two one point off unexplained, F-P02 per tournament; rung 1's criterion not yet met for three periods (proposal §1, §4, §9, Appendix F; annex T8.10) |
| V4-QC-2 | blocker | under R8 an arbiter cannot see which juniors are eligible | fixed: an eligibility flag and RX for every eligible junior, c_j = 0 included, in the list, the public file and the per-game breakdown (annex T4.6, T4.9, T7.1, T11 §7.1.2 row; proposal §5, §12) |
| V4-EXPLOIT-1 | blocker | farming under rung 2 understated; interval unclustered; rung 2's gate | fixed in part: P4 restated at rung 4's K (about 0.6 points a game in standard, 1.1 in blitz); intervals recomputed with month blocks and players, still outside ±0.01 (E6 §6); rung 2 stated as not having passed the farming part of its stage-1 gate and not recommended there; the combined rung 2 and 4 farmer added to T9.4. Keeping the 600-point exclusion in rapid and blitz meanwhile: for the architect |
| V4-EXPLOIT-2 | blocker | compensation hunter gains; rung 5 may absorb table 8.1.2's error | fixed in part: matched control run (the table's own error is about a seventh of the drain; junior-specific −0.047 → −0.010 with compensation); rung 5 on rung 2's table run (−0.011 overall); the hunter's yield published by band (+0.026 a game at 2400+ on table 8.1.2, +0.034 on rung 2's) and monitored (T8.4); T9.4 corrected. A margin τ that rises with the opponent's level: for the architect |
| V4-STAT-2 | blocker | K at the fitted process SD; elite K is not a sample artefact; stability result omitted | fixed: K at 24 points a month shown beside 12 (script §10b; about 22–40 with two to four games a month); the elite explanation corrected (the archive holds most elite standard games, E5); the doubling of established adults' monthly changes reported (proposal §5, annex T4.3, E6 §3). K falling with a period's games: for the architect |
| V4-STAT-3 | major | headline claims beyond E5 and E1 | fixed: 2200–2399 about a third of the implied transfer (also in E5's own summary, now computed); the elite's fall dated after 2019 and not attributed to the table; the newcomers' median rise labelled as truncation; "40 %" labelled as Ghita's count; "in standard and rapid" (proposal §1, §2; brief) |
| V4-STAT-4 | major | the R1 threshold cannot catch a cap-limited ratchet | fixed: θ_R1 = 0.02, same direction, two years running, on the noise-corrected ratio, below the 0.031 a year a ratchet at κ's cap would give and above every change since the reset (script §12; annex T1, T3.5, T7; proposal §5) |
| V4-EXPLOIT-3 | major | blitz wins can raise a standard seed through the shared θ | fixed (an executor's addition, for the architect to confirm): a seed needs at least half of its precision from games in that time control (annex T1, T4.7, T4.8, T7.1; proposal §6); the seed booster added to T9.4 |
| V4-QC-3 | major | which list's inputs apply to cross-period events; n_i used for two counts | fixed: every Layer 2 input from the list in force at the tournament's start (SPEC-L0 R-11a), new tables only for tournaments starting after them (annex T4.1); g_i for the twelve-list count (T1, T4.5) |
| V4-QC-4 | major | the norm question is narrower than "NOT VERIFIED" | fixed: norms use table 1.4.9, identical to 8.1.1, never 8.1.2 [VT 1, 3]; what remains is which ratings enter them (R, never RX) (proposal §13, §14; annex T11; brief) |
| V4-QC-5 | minor | seed gates change §7.1.4; σ̃ gate implies more games; T4.8 notation | fixed: listed as changes to §7.1.4 (annex T4.7, T11; proposal §6); six to eight games in practice, computed (script §10b); T4.8 uses σ̃ |
| V4-QC-6 | minor | the T7.2 example and the T7.1 comment out of date | fixed (annex T7.1, T7.2) |
| V4-STAT-5 | minor | "independent sample" | fixed: "a different sample"; on 2023, 2024 and 2026, which Ghita's 2025 extract cannot contain, 22 of 22 directions agree (E7; proposal §1, §2; annex T8.10) |
| V4-QC-7 | minor | credits for Ghita's activity bonus and URS | fixed (brief; proposal §6 adjustment row, §11) |

**For the architect** (the reviewer's five, carried to the close-out):

1. Rung 6: judge it on d_t, on D_t, or on D_t net of Layer 1's estimate of the panel's own change? (E6 §5.)
2. R6 applies the gain of one game to every game of a period with σ fixed; should K fall with the number of games in the period, or have an activity-linked floor? (It also doubles the elite's K.)
3. Rung 2 in the farming region: keep a temporary guard, or rapid and blitz's 600-point exclusion, until FIDE's archive allows the formal test?
4. Rung 5: judge it on top of rung 2's table, and let τ rise with the opponent's level, given the over-compensation against adults rated 2400 or more?
5. R1: should the review trigger on cumulative drift since adoption rather than on year-on-year moves?

And from the executor: confirm or reject the seed's information-share condition (V4-EXPLOIT-3), which goes beyond R5's text; and issue SPEC-L0 v1.1 to record the 58 periods under Q-1.

---

## The reviewer's report (verbatim)

PART A: the D-0008 audit

R1 APPLIED. Where: annex T3.5, T7.1 (sd_ratio, spread_ratio_review 0.05), T8.4, T8.9, T9.5; proposal §5 and §12. Gaps: the T7.2 example file has no review field, and its "illustrative" ratio of 1.01/1.04 sits far from the measured 0.747. The threshold cannot fire on the ratchet it is meant to catch (V4-STAT-4).

R2 APPLIED. Where: T1, T2.6, T3.5, T4.6, T4.7, T10; proposal §6; SPEC-L1 §3.6. One leftover: the c_j comment in T7.1 uses σ_j where it should use σ̃_j (V4-QC-6).

R3 APPLIED. Where: T4.5, T5 P3, T7.1 accrual_factor, T9.4, T10.3; proposal §5 and §6; brief step 6. The T7.2 example file has no accrual_factor field.

R4 APPLIED. Where: T2.6, with the sizes given; proposal §12 and §14.

R5 APPLIED. Where: T4.6(c) with SPEC-L1 §4.4's formula, T4.8, T7.1 gates, T8.4; proposal §6. The T7.2 gates have no min_info_share. Seeds are not covered, which is outside R5's text (V4-EXPLOIT-3).

R6 APPLIED. Where: T4.3, T4.8, T7.1, T10; proposal §5; brief step 4. The elite K is reported (median 20.0, and 19.0 in E6), but the documents read it wrongly (V4-STAT-2).

R7 PARTIAL. Applied in T1, T3.1–T3.3, T7.1 ("[0, inf)") and proposal §12. Missing: the T7.2 example file still prints the γ range as "[0, 0.5]".

R8 PARTIAL. Stated in T4.2, T4.6, T6, T10 and proposal §5–6. Missing: the list does not show which juniors are eligible, so an arbiter cannot apply the rule (V4-QC-2).

R9 APPLIED. Where: T3.5 and proposal §5, using the wording of D-0007 item 6.

R10 APPLIED. 58 multi-event periods added (analysis/OUTPUT_L0_rounding.md, tests/test_l0_rounding_periods.py); src/layer0/ untouched; still NOT VERIFIED (T8.10, §14 Q5). The Q-1 row in SPEC-L0 §8 still cites only F-P02 and F-P05; changing it needs a new spec version. How the result is reported is wrong (V4-QC-1).

R11 APPLIED. Where: T8.6 and T6 line 11. E1, E5, E7 and the Layer 1 fit all exclude the batch.

R12 APPLIED. Where: T8.1, T8.2, T8.10; proposal §9, §10, §14 Q3; E6 §6. The interval, though, is a per-game normal approximation, not the T8.5 bootstrap (V4-EXPLOIT-1).

R13 APPLIED. CLAUDE.md hard rule 3.

R14 APPLIED. Appendix F; nothing was sent to FIDE. Two problems: it claims all 58 periods are reproduced (V4-QC-1), and it cites [VT 2], a key the citation guide never defines.

The session brief's other v0.4 requirements:
- Re-ranking by E1, E2, E5 and E4: PARTIAL. The new table is in §2, but:
  - its evidence column overstates (V4-STAT-3);
  - rank 4 rests on [R 5] and [V 1], not on our own data;
  - FLOOR, the third most raised theme (27 items), is missing from the table.
- The 1400 pile-up claim: removed (§2, the §6 floor row; E1 cited).
- E4–E7 and the prior-work section: folded in (§2, §9, §11; T2.3a, T4.3–T4.7, T8.10).
- Body within 4,500 words: not counted; the automated check counts it.

PART B: findings

V4-STAT-1 · blocker · proposal §1 ("does not meet its ±0.01 rule below 2000"), §9 rung 5 row, annex T8.1 rung 5 row.
- Problem: E6 §4 shows that after Holm the adults' residual is significantly outside ±0.01 in three bands: <1600, 1600–1999 and 2000–2399. The last is the largest band (27,814 games) and sits at −0.0170 (interval −0.0228 to −0.0107). Only the 2400+ band is inside. "Below 2000" is therefore false.
- Fix: write "outside ±0.01 in every band below 2400".

V4-QC-1 · blocker · proposal §1 ("reproduces FIDE exactly"), §9 rung 1, Appendix F ("58 multi-event periods is reproduced").
- Problem: OUTPUT_L0_rounding.md shows every game (923) and every tournament sum reproduced. The published list change is not:
  - F-M09 and F-M18 are one point off, with no explanation;
  - F-P02 matches only per-tournament rounding, which Layer 0 does not use.
- §10's own rung-1 criterion requires every disagreement to be explained by a documented FIDE-side correction. That is not met.
- Fix: say that games and tournament sums are reproduced, and the list change in 56 of 58 periods (6 of them after FIDE's base corrections), with 2 unexplained. Record rung 1 as met except for three open periods.

V4-QC-2 · blocker · annex T4.2, T4.9, T7.1 (eligible list = "every junior with c_j > 0"), T11 (§7.1.2 row); proposal §5.
- Problem: under R8, an eligible junior with c_j = 0 blocks the opponent's compensation. But no published record shows eligibility: not the list, not the public parameter file, not the per-game breakdown. On the list, RX = R looks the same for an eligible junior and a non-eligible one.
- Scale: in E6, 10,359 of the 21,631 junior–junior games have c_j > 0 on one side, which is exactly this case. An arbiter cannot apply the rule.
- Fix: print an eligibility flag (or print RX for every eligible junior, c_j = 0 included) in the list, the public file and the T4.9 breakdown, and add it to the §7.1.2 row of T11.

V4-EXPLOIT-1 · blocker · annex T5 P4, T10.2, T11 stage 4 (§7.3.1 row); proposal §1, §9, §13 stage 1.
- The evidence: pooled at gaps of 400 or more above 2300, the fitted table under-predicts favourites by +0.032 in standard and +0.045 in blitz (E6 §6).
- The understatement: P4 prices this at "about 0.3 a game at K = 10". Under rung 4, though, established 2600+ players get K of about 19 in standard and 25 in blitz (E6 §3). That makes the gain about +0.6 and +1.1 points a game, and farming keeps σ, and so K, high.
- The deleted rule: T11 deletes the rapid and blitz exclusion of games 600 or more points apart when a player is above 2600, in force since 1 December 2024 [V 2], which reopens exactly these games.
- The interval: E6's interval is a per-game normal approximation without clustering by player, so "intervals excluding ±0.01" overstates.
- The gate: §13 makes the farming region part of the stage-1 gate, so rung 2 has not passed it, yet §1 says it "passes".
- Fix:
  - restate P4 with the K that rung 4 gives;
  - recompute the interval by T8.5, clustered by player;
  - say that rung 2 has not passed its stage-1 gate;
  - keep the 600-point exclusion until FIDE's data clear the region;
  - add the combined rung 2 and 4 farmer to T9.4.

V4-EXPLOIT-2 · blocker · annex T9.4 (compensation hunter: yield "should be zero or negative"), T4.6; proposal §1, §6.
- Problem: in games where c_j > 0, adults already score above the compensated expectation. The figures (E6 aggregates, rung5/adults_compensated):
  - +0.0072 overall (+0.0012 to +0.0137);
  - +0.026 for adults rated 2400 or more (+0.016 to +0.036, 7,385 games).
- The gain: a strong player who seeks out compensated juniors earns about 0.26 points a game at K = 10, and more at rung-4 K.
- Likely cause: rung 5 was tested on table 8.1.2, and the compensation absorbs that table's own over-prediction of favourites (0.02–0.05, E2). E6 has no control (adults against adults at the same gaps), so part of the "0.055 drain" is the table's. With rung 2's table in place, the over-compensation would grow.
- Fix: add the matched control, test rung 5 on top of rung 2, publish the hunter's yield by band, and correct T9.4.

V4-STAT-2 · blocker · proposal §5 ("about 12 to 22 … 10 to 14 with five"; elite K "high because it sees only their broadcast games"); brief step 4; annex T4.3; script §10b.
- Problem 1, the process SD: the steady-state K figures assume a process SD of 12 points a month. The history fit chose c_θ = 2, which means 24 for ages 25–45 (SPEC-L1 §3.7), and that value sits at the edge of its grid. With 24, the script's own method gives about 22–40 with two to four games a month, and 15–21 with eight (my recomputation).
- Problem 2, the elite: the broadcast archive already holds most elite standard games. E5 §5 counts 25,233 broadcast player-games at 2600+, against roughly 36,000 rated games over the same months (about 163 players × 59 a year). So a K about twice today's 10 is what R6 gives the elite; it is not an artefact of the sample.
- Problem 3, an omitted result: E6 §3 found the monthly rating changes of established adults doubling (median 7.6 → 16.8, p90 25.8 → 55.6). The proposal does not mention it.
- Fix: show K under the fitted process SD, report the stability result, and drop the broadcast-only explanation.

V4-STAT-3 · major · proposal §1, §2; brief "What is wrong".
- (a) "Largely what still drains players rated 2200+": for 2200–2399, which is 6,304 of the 8,026 players concerned, the implied transfer is 0.07–0.09 a game against 0.16–0.19 lost on the lists in 2025–26. That is about half or less (E5 §5).
- (b) The table is blamed for the shrinking elite, but the active 2600+ count rose from 225 to 242 between 2015 and 2019 under the same table. It fell after 2020, when activity collapsed (E5 §4).
- (c) The rise in newcomers' median first rating, 1272 to 1564, is mostly truncation at the new floor. In 2023, 23,676 of 35,187 newcomers were below 1400; in 2025 none can be (E1).
- (d) Rank 4's "40 %" is [R 5]'s figure, not ours.
- (e) "Stopped falling" needs "in standard and rapid": blitz is still −2, −1, −1.
- Fix: restate each claim only as far as E5 and E1 support it.

V4-STAT-4 · major · annex T3.5, T7.1; proposal §5; script §12.
- Problem: the spread ratio is about 0.91/κ. If κ falls at its annual cap of 0.05, the ratio moves only about 0.03 a year, and less while ratings converge. A threshold of 0.05 on year-on-year changes therefore never trips on a ratchet held to the cap, however long it runs.
- At the same time, the largest 12-month change in standard since March 2024 is already 0.053 (OUTPUT_L1 §3), which the script's justification leaves out.
- Also: "moves" has no defined direction, and the uncorrected ratio shifts with shrinkage whenever activity changes.
- Fix: a same-sign threshold below the cap-implied rate (for example 0.02), backed by a power calculation, applied to the posterior-corrected ratio.

V4-EXPLOIT-3 · major · annex T4.7, T9.4 (seed manipulator).
- Problem: seeds draw on all three time controls. With ω = 4 at the edge of its grid, the fitted ŝ correlates 0.9999 between standard and blitz (OUTPUT_L1 §1), so blitz results carry over in full.
- R5's share condition protects compensation but not seeds. A club can therefore raise a newcomer's standard seed with arranged rated blitz wins, then collect points as the over-rated newcomer plays standard. This is the V3-EXPLOIT-1 route, moved to rung 3.
- Fix: require at least half of a seed's precision to come from games in that time control, and add this route to T9.4.

V4-QC-3 · major · annex T4.1, T4.4, T1 (n_i).
- Problem 1: T4.1 takes R, K_i, RX_j, B_i and the table from list t for every game of period t. But an event that started under an earlier list is rated with that list's ratings (SPEC-L0 R-11a, fixtures F-P02 and F-P03). Eight of the 13 periods that follow rounding once contain such events.
- Nothing says which list's inputs apply to late-rated or cross-period events, or what happens when the yearly table changes in the middle of an event.
- Problem 2: n_i means "games on list t" for the 700 cap, which needs period t's games, and a twelve-list count for R3.
- Fix: adopt R-11a for every Layer 2 input, and give the two counts separate symbols.

V4-QC-4 · major · proposal §13; annex T11 (closing paragraphs); brief "What stays the same".
- Problem: all three call the norm question NOT VERIFIED. But docs/research/VERIFICATION_TITLES.md has verified that norm arithmetic uses table 1.4.9, which is identical to 8.1.1, and never 8.1.2 [VT 1, 3].
- What remains open is narrower: which ratings enter norms (§1.4.6 b, §1.3, §0.6.2, §1.5.3), and whether a compensated junior counts at R or RX there.
- Fix: cite VT, narrow the open question, state that norms use R, and add [VT] to the citation guide.

V4-QC-5 · minor · annex T4.7, T4.8, T11; proposal §6.
- Problem 1: "at least two events" contradicts §7.1.4's "This need not be met in one tournament" [V 1]. Yet §6 says "same 5-game threshold" and T11 lists §7.1.4 as unchanged.
- Problem 2: the σ̃ ≤ 120 gate, with s_0 = 250, gives σ̃ ≈ 117 for five equal-strength games in one month. It goes over 120 when opponents are 300 latent points away, or, for a junior, when a month passes before the list. In practice six to eight games become the minimum.
- Problem 3: T4.8 writes latent σ_i where T4.7 writes σ̃, which would mean about 9–10 games.
- Fix: list both conditions as changes to §7.1.4, and correct T4.8.

V4-QC-6 · minor · annex T7.1, T7.2.
- Problem: the T7.2 example file is out of date:
  - it prints γ range "[0, 0.5]", against R7;
  - its schema is "pf-0.3" where T7.1 says "pf-0.4";
  - it has no min_info_share (R5), accrual_factor (R3) or spread_ratio_review (R1);
  - its spread ratio of 1.01/1.04 contradicts the measured 0.747.
- The c_j comment in T7.1 uses σ_j instead of σ̃_j, which is 27 points in example (i).
- Fix: bring T7.2 and the comment into line with R1, R3, R5 and R7.

V4-STAT-5 · minor · proposal §1 ("our independent sample"); E7 "games he did not use".
- Problem: Ghita used FIDE's 2025 extract of standard games (E7 §2). Broadcast games from 2025 are FIDE-rated games and may well be in it, so independence is shown neither for 2025 nor for the 2023–2026 pool that contains it.
- Fix: report 2023–24 plus 2026 separately, and call it a different sample, not an independent one.

V4-QC-7 · minor · brief (the credits paragraph); proposal §6 monthly-adjustment row, §11.
- Problem: Ghita proposed an activity-linked bonus first, and R3 moved rung 6 towards it (PRIOR-WORK G5).
  - The brief omits this, and also omits URS for seeds built from all time controls with age priors.
  - The §6 row credits only US Chess.
  - §11's "we share the first three in other forms" never says plainly that he came first.
- Fix: add one plain clause in each place.

For the architect

1. Rung 6: should it be judged on d_t, on D_t, or on D_t net of Layer 1's estimate of how much the panel itself improved? E6 §5 shows D_t failing only because the panel got stronger.
2. R6 (a ruling that looks wrong in one respect): it is the gain of one game, but it is applied to every game in a period with σ held fixed. Against the n-game gain qσ²/(κ(1 + nq²σ²v)), that overstates a nine-game period by about 13 % at σ = 55 and 35 % at σ = 90. It also doubles the elite's K. Should K depend on n, or have a floor tied to activity?
3. D1 says no caps or clamps, but the farming evidence (E6 §6) says the fitted table under-predicts big favourites. Should rung 2 keep a temporary guard in that region, or the 600-point exclusion, until FIDE's archive allows the formal test?
4. Rung 5: should it be judged on top of rung 2's table, and may τ rise with the opponent's level, given the over-compensation at 2400+?
5. R1: a "moves beyond a threshold two years running" rule cannot catch a ratchet slower than about 0.03 a year. Should the review instead trigger on cumulative drift from the value at adoption?
