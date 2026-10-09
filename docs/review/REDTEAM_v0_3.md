# Third red-team review: proposal v0.3, technical annex v0.3 and brief v0.3

Status: REVIEW RECORD · Session ELO-3, Phase 1 · Date: 2026-10-09 · Reviewer: one subagent briefed with the R-STAT, R-QC and R-EXPLOIT briefs together, reading `docs/proposal/ELO-PROPOSAL_v0_3.md`, `docs/proposal/ELO-TECHNICAL-ANNEX_v0_3.md`, `docs/proposal/ELO-BRIEF_v0_3.md`, `docs/decisions/D-0005_architect-decisions-v0.3.md`, `analysis/OUTPUT_v0_3.md` with its script, `docs/review/REDTEAM_v0_2.md`, `docs/research/VERIFICATION_2026-10-09.md` §1–§2 and `docs/research/ELO-RESEARCH_v1_0.md`. The decisions D1–D18 were given to the reviewer as fixed; decision-level points were to be reported separately for the architect. The reviewer's text is reproduced verbatim in the second half of this file; the first half records what the executor did with it.

## Verification performed by the executor

- `python3 analysis/v03_calculations.py` reproduces `analysis/OUTPUT_v0_3.md` byte for byte, locally (Python 3.12.13, macOS) and in the automated check (Python 3.12, Linux).
- D1: at level 2300 with v0.2's α and β, E = 0.713, 0.878, 0.926 and 0.975 at gaps of 200, 400, 500 and 700, against 0.723, 0.872, 0.917 and 0.966 under the 5/6-gap rule (script §2), as the brief expected. D3: σ = 45 gives K = 11.5 and σ = 55 gives 17.0 (script §5).
- D18 audit, by the executor before the review: every PARTIAL of REDTEAM_v0_2 and the third review's five fixes were searched for in v0.3; the reviewer's Part A below is the independent check. One further inconsistency was found and corrected: v0.2 described its synthetic ledger month as having eight rated games; it had nine (annex T10.4).
- After the fixes below: proposal body 4,391 words and summary 239 by the strict count, brief 839 words (check (d)); every reference resolves (check (c)).

## Disposition

**Part A (D18 audit).** The reviewer found 12 RESOLVED and 4 PARTIAL. Each PARTIAL is closed by a Part B fix: R-STAT-4 by V3-STAT-2; R-QC-8 by V3-QC-2 (the disclosure is now stated; the conflict itself is FA-4); R-EXPLOIT-2 by V3-EXPLOIT-1 (claim corrected, monitoring added; the definitional fix is FA-5); R3-1 by V3-QC-1.

**Part B.** Status: **fixed** (where), **fixed in part** (what remains, and for whom), or **for the architect** (a decision D1–D18 would have to change).

| ID | Sev. | Topic | Status |
|---|---|---|---|
| V3-STAT-1 | blocker | rung tests fail a correct table at the stated sample sizes | fixed: statistical decision rules in annex T8.2 (Holm–Bonferroni across bins, across-bin calibration slope with a standard-error condition, minimum detectable deviation published), rung 7 at 9,000 cross-border games, at least 12 test months per decision (T8.3), closed list of rollback triggers (T8.9); proposal §10, §11 |
| V3-STAT-2 | blocker | no ledger line for §8.2.4 one-sided games or administrative changes | fixed: §8.2.4 kept at every rung and quoted (T4.1); ledger lines (2b) and (11), list held only for an unexplained residual (T6, T7); script §10 now has a one-sided game and closes exactly at +1781 (+17.4800 without the new line); proposal §5 |
| V3-QC-1 | blocker | per-federation residuals in the public report | fixed: per-federation values and federation-pair bins QC-only while rung 7 is disabled, public distribution without names (T8.4, T11 stage 2; proposal §3(c), §11) |
| V3-STAT-3 | major | refitting κ on published ratings can ratchet the spread | fixed in part: fixed-point relation and attenuation stated (T3.5); spread ratio published monthly (T8.4); attenuation-corrected κ and SD ratio in the fit block (T7); simulator check on κ and spread (T9.5). Whether D2 itself should correct for attenuation: FA-1 |
| V3-STAT-4 | major | θ̃ nets out level, not spread | fixed in part: the κ ≈ 1 assumption stated with its size (+107, +90, +74 points at R = 1400, 1500, 1600 for κ = 5/6, script §10b); spread term reported to the QC; rungs 3 and 5 by rating band (T3.5, T8.1). Definition of θ̃: FA-2 |
| V3-STAT-5 | major | rung 6 fails in the controller's transient | fixed: transient and steady-state gap stated; D_t scored from month 13 or with a stage-1 start; level criterion added (T4.5, T8.1, T7; proposal §10) |
| V3-QC-2 | major | public K_i and RX_j reveal σ_i and θ̃_j | fixed in part: the disclosure is stated with its size (K = 17.0 gives 54.94 ≤ σ ≤ 55.10; K = 27.1 gives θ̃ = RX + 114.7, script §10b) in T2.6 and proposal §11, §13. The conflict between D3 and D17: FA-4 (founder) |
| V3-QC-3 | major | paragraph map omits §8.2.1, §8.2.4, §7.1.4's 1400, rapid/blitz §7.2.x; c_j in the rung-2 row; 8.1.1 under rung 2 alone | fixed: rows added, c_j moved to rung 5, the 8.1.1 mismatch recorded with its size (p = .75 at 212–247 and .92 at 452–497 against 193 and 401, script §10b) and the QC's option to invert the new table (T11 stage 4; T4.7) |
| V3-QC-4 | major | delegation of a normative table; rollback triggers; what reverts; list hold | fixed: delegation clause, NOT VERIFIED (T11); closed trigger list and what reverts (T8.9); hold only for an unexplained residual (T6); proposal §11 |
| V3-QC-5 | major | two answers on when a_t is known | fixed: one timing sentence (T4 preamble) used in T4.5, T7 and proposal §4, §5; T7 split into inputs for period t and results of period t − 1 |
| V3-EXPLOIT-1 | major | compensation manufactured through blitz via the shared θ | fixed in part: the T4.6 claim corrected; QC report of each junior's precision share from other time controls and a flag where c_j would be 0 on same-time-control games alone; the blitz route added to T9.4. Same-time-control posterior: FA-5 |
| V3-EXPLOIT-2 | major | accrual per active month, drain per game | fixed in part: the windfall stated with its size (15.6 points a year against about 0.53 a game, script §10b) in T4.5; residual by activity monitored (T8.4); collector measured against true skill and RMSE by activity decile (T9.4, T9.5). Accrual scaled by activity: FA-3 |
| V3-EXPLOIT-3 | major | P4 covers gap, level and colour only | fixed: P4 qualified in T3.3, T5 and proposal §5, §11; federation choice named as the remaining exposure; per-player cross-federation gains monitored, QC-only (T8.4) |
| V3-EXPLOIT-4 | major | newcomer seed clipped up to 1400 creates points and contradicts §7.1.4 | fixed: one rule for newcomers and re-entries, published only if round_FIDE(θ̃) ≥ 1400, seed = min(round_FIDE(θ̃), 2200) (T4.7, T4.8; proposal §6); script §10 now refuses a newcomer at θ̃ = 1287.6 |
| V3-STAT-6 | minor | P4 for the fit overstated | fixed: five moment conditions, four on a γ boundary; calibration an out-of-sample property (T3.3); mean residual and γ-boundary status in the fit block (T7) |
| V3-STAT-7 | minor | Kalman assumptions; asserted σ values; K follows activity | fixed: assumptions stated (T4.3); σ values labelled as assumptions; steady-state K by activity and level computed (script §10b: about 14–22 with two to four games a month, K_min with eight); proposal §5 and brief tie K to activity. The 1/κ factor: FA-6 |
| V3-STAT-8 | minor | junior–junior games create 10–26 points | fixed in part: the case stated with its size (script §10b), its own sub-line of ledger line 3, counted in the a_cap test (T4.6, T7). Rule choice: FA-8 |
| V3-STAT-9 | minor | anchor constraint wording; d_t ignores B_i | fixed: μ ≡ 0 for ages 25–45 (T2.4); d_t on the settled rating R_i + B_i (T2.4) |
| V3-STAT-10 | minor | bootstrap blocks; when thresholds freeze | fixed: moving-block bootstrap with 3-month blocks (T8.5); each source's thresholds frozen before its first test month is scored (T8.8) |
| V3-QC-6 | minor | parameters without fields; η grid | fixed: s_0 (PROVISIONAL 250), the compensation and seed gates, the selection tolerance, n_φ, s_max, R_max added to T7; η a whole number (T1, T7) |
| V3-QC-7 | minor | "sandbag" label; two farming thresholds; public flags; brief wording | fixed: "estimate–rating divergence", excluding eligible juniors and recent returners; one threshold (400); per-event lines published unflagged, flags QC-only (T8.4, T6; proposal §11); brief reworded |
| V3-QC-8 | minor | federation gap, direction of miscalibration, phantom draws, K for top players | fixed: proposal §1 and brief give offsets from about −60 to +100 and gaps over 160 [R 5] [R 6], not peer-reviewed; "expects too much of moderate favourites [R 44]"; "part of the 2024 repair" (§6); K tied to activity |
| V3-QC-9 | minor | hand-check details | fixed: proposal §5 prints the table's 0.925 (script §10b); J is 16 (T10.1); "K x n" quoted verbatim (T4.4); §10 aligned with T8.2; each band also published in table 8.1.2's range format (T3.4) |
| V3-EXPLOIT-5 | minor | σ kept high on purpose | fixed: link between K and opponent gap stated (T4.3, P4); farming-region calibration test (T8.1, T8.4); K-raiser adversary (T9.4) |
| V3-EXPLOIT-6 | minor | more extreme-K pairs for collusion | fixed: QC-only pair-level monitor and event flags on excess creation, not rank (T6, T8.4); returner and active-donor adversary (T9.4) |
| V3-EXPLOIT-7 | minor | the player chooses when the balance lands | fixed: settled rating R_i + B_i printed and recommended for selections (T1, T4.5, T4.9, T11); posting time added to P3 (T5) |

**For the architect.** FA-1 (attenuation in D2), FA-2 (θ̃ in spread as well as level), FA-3 (accrual scaled by activity), FA-4 (D3's public K against D17's QC-only σ; founder), FA-5 (same-time-control posterior for c_j), FA-6 (the 1/κ factor in the Kalman gain), FA-7 (γ ≤ ½ is not needed for monotonicity; boundary fits), FA-8 (compensation in junior–junior games). None is decided here; all are carried to the ELO-3 close-out.

---

## Reviewer's text (verbatim)

# Red-team review of proposal v0.3, technical annex v0.3 and brief v0.3 (R-STAT + R-QC + R-EXPLOIT combined)

Status: REVIEW RECORD (draft) · Date: 2026-10-09

**Inputs read in full:**
- `docs/proposal/ELO-PROPOSAL_v0_3.md`
- `docs/proposal/ELO-TECHNICAL-ANNEX_v0_3.md`
- `docs/proposal/ELO-BRIEF_v0_3.md`
- `docs/decisions/D-0005_architect-decisions-v0.3.md`
- `analysis/OUTPUT_v0_3.md`, with `analysis/v03_calculations.py`
- `docs/review/REDTEAM_v0_2.md`
- `docs/research/VERIFICATION_2026-10-09.md` §1–§2
- `docs/research/ELO-RESEARCH_v1_0.md`

**Read for cross-reference:** `docs/review/REDTEAM_v0_1.md`, `docs/decisions/D-0003_architecture-revisions-v0.2.md` (AR-1 to AR-5) and SPEC-L0 §3.

**Method:**
- No repository file was edited.
- Derivations, arithmetic and three small simulations were rerun in a scratch directory (Python standard library; scripts not committed).
- Every parameter value used below is the documents' own PROVISIONAL value.

**Verdict.**
- The algebra holds. T3.2's derivative and proofs, T3.3's score equations, the K values, the band steps, the deadband steady state and the synthetic ledger month all re-derive.
- Three blockers stop circulation to the QC:
  - The pre-registered rung tests of T8 fail a correct table at the stated sample sizes (V3-STAT-1).
  - The ledger identity has no line for the one-sided games of §8.2.4 [V 1] (V3-STAT-2).
  - The public monthly report would carry per-federation residuals, which R3-1 removed (V3-QC-1).
- Most majors concern four things:
  - spread versus level (D2, D8, D10);
  - cross-time-control evidence feeding compensation (D5);
  - the accrual rule (D10);
  - disclosure of σ through K (D3 against D17).
- Decision-level points are listed once, FOR THE ARCHITECT, at the end of Part B.

**Tally.**

| Part | Result |
|---|---|
| A | 12 RESOLVED, 4 PARTIAL, 0 NOT RESOLVED |
| B | 3 blockers, 11 majors, 12 minors (26 findings) |

---

## Part A — D18 consistency audit

| Item | Verdict | Reason | v0.3 location |
|---|---|---|---|
| R-STAT-2 | RESOLVED | θ̃ = ŝ − d_t is defined once and used for every Layer 2 purpose. D5's lower quantile removes the eligibility cliff (b). Level is netted out; spread is not (V3-STAT-4). | T1, T2.6, T4.6–T4.8, T7.1; proposal §6 |
| R-STAT-3 | RESOLVED | Line 3 is published per event. The farming index includes compensated games. Line 3 per active player is compared with a_cap. | T6, T8.4, T4.5 |
| R-STAT-4 | PARTIAL | Post-update exits, unrated opponents, re-entry and refused re-entry are in the identity and tested in script §10. The one-sided games of §8.2.4 are not (V3-STAT-2). | T4.1, T6; script §10 |
| R-STAT-8 | RESOLVED | Cov(θ, δ_tc) and the cross-time-control correlation are fit diagnostics. | T2.4, T7.1, T8.4 |
| R-STAT-9 | RESOLVED | Band width is registered with a fixed cap; the 100-point steps are measured. | T1, T7.1, T3.4 |
| R-QC-2 | RESOLVED | A dedicated list of per-game and per-period fields now exists. | T4.9 |
| R-QC-8 | PARTIAL | The public file now carries only fide_id, R_j and c_j. But the public K_i and RX_j reveal σ_j and θ̃_j (V3-QC-2). | T7.1, T4.6 |
| R-QC-10 | RESOLVED | "AI" appears only in the §11 denial. There is no "patch" or "arbitrage" in the three documents. The central-bank analogy appears once per document. | proposal §5, §11; annex T6 |
| R-EXPLOIT-1 | RESOLVED | Line 2 is published per event and the top percentile flagged. The ratio cap was decided against with reasons (D11). A colluding-pair adversary is in the simulator. The wider K population is a new point (V3-EXPLOIT-6). | T6, T8.4, T9.4; D-0005 D11; proposal §11 |
| R-EXPLOIT-2 | PARTIAL | Per-event line 3 and flags are in place. The cross-time-control route the finding described is still open through the shared θ (V3-EXPLOIT-1). | T4.6 (b), T6, T8.4 |
| R-EXPLOIT-8 | RESOLVED | The return-from-inactivity indicator has a PROVISIONAL 2 SD threshold. | T8.4 |
| R3-1 | PARTIAL | The parameter file and §11 keep federation estimates QC-only. But §3(c) row 7 and the monthly public report (T8 metrics) publish per-federation residuals (V3-QC-1). | proposal §3(c), §11; T7.1, T8.4, T11 stage 2 |
| R3-2 | RESOLVED | The table has one row per whole-number gap 0–1500, is normative and uses 1 − E for negative gaps; the engine reads the same table. The list prints K_i, RX and B_i. | proposal §5; T3.4, T4.1, T11 (§7.1.2) |
| R3-3 | RESOLVED | "Within a point of today's" matches the example: −4/+16/+36 against −3/+17/+37. | proposal §5; T10.1 |
| R3-4 | RESOLVED | §1 marks the norm question NOT VERIFIED; K = 40/20/10 is cited to §8.3.3 [V 1]. | proposal §1, §5, §12 |
| R3-5 | RESOLVED | The proposal body is neutral. P4 now says "choosing opponents", not "farming". The remaining §2 label is the report's target name, qualified "within the rules", unchanged since the R3-5 fix. New wording in the brief and annex is covered in V3-QC-7. | proposal §2, §5, §11 |

---

## Part B — New findings

### R-STAT

**V3-STAT-1 · blocker · annex T8.1 (rungs 2 and 7), T8.2, T8.4; proposal §10 table and §11 rollback rule.**

*Problem.* The per-bin criteria fail a correct table at the stated minimum bin size of 1,000 games (PROVISIONAL standard parameters, level 2050).

- **Bin mean residual (±0.01).** The standard error of a bin's mean S − E is 0.0138 near x = 0, 0.0125 at x ≈ 225 and 0.0088 at x ≈ 425. A perfectly calibrated bin therefore breaches ±0.01 with probability 0.47, 0.42 and 0.26. All 20 bins from 0 to 1000 pass together with probability 0.005. Holding ±0.01 at 2.5 standard errors needs about 12,000 games per bin.
- **Within-bin slope (0.95–1.05).** Inside one 50-point gap bin, E varies with SD ≈ 0.022 across the 15 level bands. The slope of S on E therefore has a standard error of about 0.60 at 1,000 games, against a tolerance of ±0.05; about 900,000 games would be needed.
- **Rung 7 (±10 points at 1,000 cross-border games).** The standard error is about 12 points.

The consequences:
- Stage 1's gate ("rung 2 passes its test") cannot be met as pre-registered.
- T8.8 freezes the plan once the first TRF month is unsealed.
- §11's rollback ("any monitoring threshold of [T8] … two consecutive months") would fire on noise.

*Fix.*
- Pre-register statistical decision rules. A bin fails only when its residual is significantly outside ±0.01, under a multiplicity rule (Holm, or one χ²/Spiegelhalter statistic across bins).
- Set minimum bin counts by a power calculation.
- Replace the within-bin slope with the slope of bin means on bin expectations, taken across bins.
- For rung 7, require about 9,000 cross-border games, or widen the tolerance.
- Give a closed list of rollback triggers.

**V3-STAT-2 · blocker · annex T4.1, T6, T5 P5, T11; proposal §11 ("the list is held").**

*Problem.* §8.2.4 [V 1] (SPEC-L0 R-12) reads: "If an unrated player receives a published rating before a particular tournament in which they have played is rated, then they are rated as a rated player with their current rating, but in the rating of their opponents they are counted as an unrated player." Such games change one player only.

- T4.1 says games against unrated opponents change "neither side". T6 concludes "there are no one-sided terms". Both are wrong for §8.2.4 games.
- §9.1 allows a tournament to be rated up to the third list after it ends, so a newcomer with a late-rated event is routine.
- Each such game adds K_i(S_i − E_i) to the list total with no ledger line. The identity fails, and §11 holds the list. This is the same class of defect as R2-1.
- The identity also has no line for administrative changes: re-rated or annulled events, ID merges, removals other than the floor.
- Script §10 contains no §8.2.4 game.

*Fix.*
- Decide in T11, per rung, whether §8.2.4 is kept.
- If kept, add a ledger line "(2b) one-sided changes under §8.2.4".
- Add a line "(11) administrative corrections, itemised".
- Put a §8.2.4 game in script §10.
- Hold the list only for an unexplained residual above a stated amount.

**V3-STAT-3 · major · annex T3.5, T3.3, T9.5, T8.4 (dynamics of D2 and D8).**

*Problem.* T3.5 treats κ_tc as a static absorber of excess spread. It omits two effects:
- **The update spreads ratings to match the table.** Under a table of slope κ, the published update's fixed point is R_i − R_j = (s_i − s_j)/κ, so a flatter table spreads the published ratings.
- **The refit flattens the table.** A slope fitted on noisy published ratings is attenuated. This is the errors-in-variables effect behind the 5/6 finding [R 44].

A yearly refit on published ratings therefore ratchets. Reviewer's simulation, set up as follows:
- 3,000 players with fixed true strengths, SD 300.
- K = 20, 24 games a year, binary logistic results, global random pairing.
- Annual cap of ±0.05 on κ.

| Year | κ held at 1: fitted κ | κ held at 1: published SD | Yearly refit: table κ | Yearly refit: published SD |
|---|---|---|---|---|
| 1 | 0.970 | 304 | 1.000 | 304 |
| 10 | 0.938 | 308 | 0.912 | 320 |
| 20 | 0.950 | 309 | 0.857 | 339 |

- With the level held by a_t at the anchor, a player 900 points above the anchor mean gains about 90–100 points over 20 years without playing better, and the bottom of the list drifts towards the floor.
- Noisier ratings (juniors at K = 40) speed this up. The annual cap only slows it.
- T9.1 already refits κ yearly, but T9.5 has no acceptance check on κ or spread, and the monitoring report has no spread metric.

*Fix (within D2 and D8).*
- State the fixed-point relation and the attenuation bias in T3.5.
- Add a T9.5 acceptance check: κ_tc and the ratio of published to latent SD show no trend beyond ±0.01 a year over the 120-month run.
- Publish that ratio monthly, for the anchor cohort and for the pool.
- Report an attenuation-corrected κ beside the maximum-likelihood κ in T7's fit block.
- The design question is FA-1.

**V3-STAT-4 · major · annex T1 (θ̃), T4.6, T4.7, T3.5; proposal §6.**

*Problem.* θ̃ = ŝ − d_t removes the level gap only. T3.5 expects κ_tc ≠ 1. In that case, a correctly rated player (calibrated in the table's sense) has ŝ − m̂_t = κ(R − m_t), so θ̃ − R = (1 − κ)(m_t − R) even with no under-rating.

At κ = 5/6 and the illustrative anchor mean 2041.3 (T7.2), the spurious gap is:

| R | (1 − κ)(m_t − R) |
|---|---|
| 1400 | +107 |
| 1500 | +90 |
| 1600 | +74 |

Consequences:
- The gap is comparable to τ + zσ (101.9 at σ = 60), so correctly rated juniors at the bottom of the list become eligible.
- Ledger line 3 grows for reasons unrelated to junior improvement.
- Seeds enter about 90 points high at 1500, and too low above the anchor mean.
- V3-STAT-3 enlarges the term every year.

*Fix.*
- Wherever θ̃ is called "on the published scale", state the assumption κ ≈ 1.
- Report to the QC the spread term (1/κ − 1)(ŝ − m̂_t) for each eligible junior and each seed.
- Break the rung 3 and rung 5 targeted residuals down by R band.
- The definition itself is FA-2.

**V3-STAT-5 · major · annex T8.1 (rung 6), T4.5; proposal §9, §10; OUTPUT §9.**

*Problem.* With the report's drift of +1.3 a month, OUTPUT §9's own control loop takes d_t from 0 to 8.6 in twelve months.

| Period | Change in the anchor's published mean |
|---|---|
| Months 0–12 | −8.6 |
| Months 12–24 | −0.9 |
| After month 24 | 0 |

- Rung 6's target, "drift of the anchor cohort within ±2 points a year", therefore fails for the whole twelve-month shadow period, by construction.
- The permanent 9.5-point gap that the deadband controller keeps is invisible to D_t, because D_t is a 12-month change.

*Fix (within D7).*
- Pre-register the transient: score D_t from month 13, or start the controller on the stage-1 drift estimate twelve months before the shadow year.
- Add a level criterion |d_t| ≤ d_0 + |drift|/γ_a + tolerance.
- State the steady-state gap as a known property of the controller.

**V3-STAT-6 · minor · annex T3.3 ("P4 for this fit"), T5 P4.**

*Problem.* The sentence "Maximum likelihood on published ratings estimates exactly this conditional expectation within the model family; the score equations are its in-sample form" overstates what the score equations give.
- The η equation gives Σ(S − E) = γ Σ s(D − P_D), not Σ(S − E) = 0.
- The κ equation removes only a linear gap trend in that corrected residual.
- Under misspecification, nothing makes E[S | x, L, colour] equal the table entry bin by bin.
- The PROVISIONAL γ = ½ is the upper end of D1's range. If the data prefer faster draw decay, the fit sits on the boundary, the γ equation holds only as an inequality, and the gap-weighted draw moment is unmatched exactly where large gaps are played.

*Fix.*
- Say that maximum likelihood matches five moment conditions, and that calibration by gap, level and colour is an empirical property tested out of sample (T8).
- Add Σ(S − E)/G and the γ-boundary status to T7's fit block.

**V3-STAT-7 · minor · annex T4.3, T10.2; proposal §5; brief step 4.**

*Problem.*

**(a) The Kalman reading has unstated assumptions.** It assumes κ = 1, logistic information q²/4 and a known opponent, and it treats σ (latent units) as if it were on the published scale. With a fitted κ, the one-game gain on the published scale carries a factor 1/κ: 20 % more at κ = 5/6.

**(b) The example σ values are asserted, not derived.** Take T7.2's σ_θ = 12 a month (ages 25–45) and the Davidson information at x = 0, which is 0.97, 0.90 and 0.80 of the logistic value at levels 1700, 2300 and 2700. Steady-state K at level 2700 is then:

| Standard games a month | 2 | 3 | 4 | 5 |
|---|---|---|---|---|
| K at level 2700 | 18.0 | 14.7 | 12.7 | 11.4 |

- At level 1700, 8 games a month already gives K_min = 10.
- K follows activity, not level. A top player with 24–36 classical games a year sits at 15–18: about half as much again as today's 10, not "11.5, near today's 10".
- A very active club player gets K_min.

*Fix.*
- State the assumptions in T4.3.
- Derive the example σ values from T7.2's σ_θ and a stated activity, or label them as assumptions.
- Report K by level and by games per month in the stage-1 evidence; FIDE's lists carry both K and games [V 3].
- The formula itself is FA-6.

**V3-STAT-8 · minor · annex T4.6 ("c_j enters only opponents' x; j's own update uses R_i, R_j"); proposal §5 ("the junior's update never sees the compensation").**

*Problem.* AR-2 sets x_i = R_i − RX_j + w_i η whenever j qualifies. So in a game between two eligible juniors, each update sees the other's compensation, contrary to AR-4, T4.6 and §5. The game creates points whatever the result. Example at level 1500–1599, K = 40 for both:

| Compensation each | Expectations | Sum | Points created per game |
|---|---|---|---|
| c = 100 | 0.418 / 0.332 | 0.750 | 10.0 |
| c = 300 | 0.196 / 0.142 | 0.338 | 26.5 |

- This is the largest per-game creation in the system.
- It is concentrated in junior events.
- It can trip T4.5's rule that line 3 per active player stay below a_cap. That rule then lowers c_cap for every junior.

*Fix.*
- State the case.
- Report junior–junior line 3 separately, and say whether it counts towards the a_cap test.
- The rule choice is FA-8.

**V3-STAT-9 · minor · annex T2.4, T4.5.**

*Problem.*
- **(a)** "Σ_{i ∈ anchor} μ(age_i(t), θ_i(t)) = 0 for every month in the window" cannot hold month by month. μ is time-invariant with a θ term, and panel members age past 45 within a 36-month window that spans three re-based panels. The rule actually used is μ(25–45) ≡ 0 (T7.2).
- **(b)** d_t = mean(ŝ − R_i) uses R_i without the carried balance B_i. Accrued but unposted adjustment therefore counts as deflation. That adds a posting lag the stylised loop of script §9 ignores, and shifts the steady-state gap by the panel's mean outstanding balance.

*Fix.*
- Write the constraint as μ(25–45, ·) ≡ 0, or as a window mean.
- Compute d_t on R_i + B_i.
- Model the posting lag in the controller analysis and in T9.

**V3-STAT-10 · minor · annex T8.5, T8.8.**

*Problem.*
- Test months are resampled as independent blocks, although consecutive months share 35 of 36 window months and rating errors persist.
- A twelve-month shadow period gives only 12 blocks, too few for percentile intervals.
- T8.8 calls the do-no-harm tolerances "pre-registered now". It also lets "PROVISIONAL parameter values and thresholds" change "until the first evidence on each data source is complete", so thresholds can move while that source's results are being read.

*Fix.*
- Use a moving-block or stationary bootstrap with blocks of at least 3 months, and a stated minimum number of test months per decision.
- Freeze each source's thresholds before its first test month is scored.

### R-QC

**V3-QC-1 · blocker · proposal §3(c) row 7; annex T8.4 (calibration by "federation pair"; r_f "in points"), T11 stage 2 — against proposal §11 and T7.1 (R3-1).**

*Problem.* §11 keeps "federation-level estimates" QC-only while rung 7 is disabled. But:
- §3(c) promises "Residuals by federation … reported monthly".
- The public monthly monitoring report carries "the T8 metrics".
- Those metrics include r_f per federation in rating points, and calibration by federation pair.

These are per-federation miscalibration estimates: exactly the exposure that R3-1, a blocker, removed from the parameter file.

*Fix.*
- While rung 7 is disabled, publish only federation-anonymous aggregates, for example the distribution of r_f across federations.
- Send per-federation r_f and the federation-pair bins to the QC annex.
- Amend §3(c), T8.4 and T11 stage 2 accordingly.

**V3-QC-2 · major · annex T2.6, T4.3, T4.6, T7.1; proposal §11, §13 (D17).**

*Problem.* The list discloses, for named players including minors, the estimate and uncertainty that T2.6, T4.6 and §13 call QC-only.
- **σ_i from K_i.** K_i is printed to one decimal and increases strictly in σ_i between 41.98 and 85.87. So σ_i = √(K/(q − Kq²/4)) is public to ±0.1; for example K = 17.0 gives σ between 54.94 and 55.10.
- **θ̃_j from RX_j.** For a compensated junior with 0 < c_j < 300 and K_j < 40, θ̃_j = RX_j + 25 + 1.2816 σ_j, to within ±0.6. For example K = 27.1 gives θ̃_j = RX_j + 114.7.
- **K_j = 40 hides little.** It censors only σ: σ_j > 85.87 still implies θ̃_j > RX_j + 135.

*Fix.*
- State the disclosure in T2.6, T4.6, §11 and §13, so that the founder decides with it in view.
- The underlying conflict is FA-4.

**V3-QC-3 · major · annex T11 stage 4 (paragraph table and "Paragraphs that do not change"), T4.7.**

*Problem.* The paragraph map omits rules that Layer 2 changes or contradicts:
- **§8.2.1** (a zero score in the first event is disregarded) conflicts with Layer 1 "uses every game" for the seed.
- **§8.2.4** — see V3-STAT-2.
- **Rapid/blitz §7.2.1** ("their standard rating is used … considered to be rated") is kept only "in spirit" (T4.7). An arbiter cannot tell whether such a player is rated from the first rapid game or after five.
- **§7.1.4**, "The rating must be at least 1400", is called unchanged but is contradicted by the seed clip (V3-EXPLOIT-4).

The table also has two smaller problems:
- The §8.3.2 row, assigned to rung 2, mentions c_j, which belongs to rung 5.
- Rung 2 alone keeps table 8.1.1, whose dp no longer inverts the new table. Under rung 2 alone, newcomers are therefore seeded 18–95 points below what the new table implies: a deflationary channel inside a rung offered as self-standing.

| Score p | 8.1.1 dp | Fitted gap at band mid 1650 | at 2050 | at 2450 |
|---|---|---|---|---|
| .75 | 193 | 211 | 225 | 246 |
| .92 | 401 | 452 | 469 | 496 |

*Fix.*
- Add keep/replace rows, per rung, for §8.2.1, §8.2.4, the last sentence of §7.1.4, and rapid/blitz §7.2.1, §7.2.2 and §7.2.5.
- Move c_j to the rung 5 row.
- For rung 2 alone, either invert the fitted table inside Ru = Ra + dp, or record the mismatch with its size.

**V3-QC-4 · major · proposal §11 (ownership, rollback); annex T3.4, T11 stages 2–4.**

*Problem.*
- **(a) Who may change a normative table.** Table 8.1.2 is Council-approved text ("Approved by FIDE Council on 15/12/2023" [V 1]). The proposal has the QC publish a new normative table every year. Whether FIDE's rules let the QC do that without the Council is neither marked NOT VERIFIED nor written into the stage-4 text as an explicit delegation.
- **(b) The rollback trigger fires constantly.** "Any monitoring threshold of [T8]" includes "the top percentile flagged", which is true every month by construction, and per-bin thresholds that fail on noise (V3-STAT-1).
- **(c) "Reverts to the last compliant version" is undefined** for the per-junior c_j, for K_i (printed in the list, not the file) and for a_t.
- **(d) The list-hold rule is too broad.** After adoption, "the list is held" on any ledger mismatch would hold the official list over an unbooked administrative item.

*Fix.*
- Mark (a) NOT VERIFIED and add a delegation clause to the stage-4 text.
- Give a closed list of rollback triggers, each with a statistical rule.
- Define what reverts: table parameters and a_t go back to the last compliant values; c_j is recomputed under them, or set to 0.
- Hold the list only for an unexplained residual.

**V3-QC-5 · major · annex T4 preamble, T4.1, T4.5, T7.1 (a_t comment), T7.2, T10.3; proposal §4 (monthly cycle), §5.**

*Problem.* The documents give two answers to which month's a_t enters a period total.

| Source | What it says | Implication |
|---|---|---|
| T4.1 | freezes "a_t from the parameter file of list t" for period t | a_t is known before the games it is posted with |
| §4 | writes "next month's parameter file" for "next month's games" | same as T4.1 |
| T4.5 | a_t is "published with the list, never before the games it applies to are rated" | a_t is not known in advance |
| §5 | "published with the list after the month it measures, so it cannot be timed" | same as T4.5 |

- T7.2's file for the list of 1 February 2027 is approved on 29 January, the closing date. Yet it carries "the month's" ledger, which needs that list's results, alongside inputs for February's games.
- An arbiter cannot tell which a_t a period total contains, or which file holds it.

*Fix.*
- Write one timing sentence and use it verbatim in T4.1, T4.5, T7.1, T10.3, §4 and §5. For example: "the file published with list t carries a_t computed from period t − 1; it accrues to players active in period t and is posted with period t's games".
- Split T7 into "inputs for period t" and "results of period t − 1", with approval after the results.
- Rest "cannot be timed" on the accrual rule, not on publication order.

**V3-QC-6 · minor · annex T1, T7.1 (schema); proposal §3(a) item 5.**

*Problem.* These quantities set published numbers but have no field, value or cap in the parameter file:
- s_0, the prior SD of a new player. It drives every seed and has no value anywhere.
- The compensation gates: 10 games, 5 opponents, 3 events, and the age limit of 19.
- The seed gates: 3 opponents, 2 events.
- The selection-test tolerance (2 SE).
- n_φ, s_max and R_max, which appear in text only.

§3(a) promises that "No published parameter may move by more than a published cap per year".

A separate grid problem: η is typed float with a cap of 5, yet x must be a whole number for the table lookup, and the grid of a fitted η is not stated.

*Fix.*
- Add the fields, with values, units and caps (or "fixed").
- Put η_tc on the whole-number grid.

**V3-QC-7 · minor · annex T8.4, T6; proposal §11; brief step 6 (wording and tone).**

*Problem.*
- **(a) The "sandbag indicator" mislabels improvement.** It tests |θ̃_i − R_i| > 2σ_i. It fires on any compensated junior with c_j > 0.72σ_j − 25: from 18 points at σ = 60, from 47 at σ = 100. It labels rule-abiding improvement as sandbagging and has no specificity.
- **(b) Two farming thresholds.** The farming index counts opponents "300 or more points below" in T8.4 but "more than 400" in §11.
- **(c) Public flags name innocent events.** Publishing per-event ledger lines with the top percentile "flagged" names about 1 % of events every month by construction, most of them junior-heavy and legitimate.
- **(d) Loaded wording in the brief:** "it cannot be farmed by playing more".

*Fix.*
- Rename the indicator neutrally ("estimate–rating divergence"), and exclude eligible juniors and recent returners.
- Use one farming threshold.
- Keep the flags QC-only and publish the per-event lines unflagged.
- In the brief, write "it does not grow with the number of games".

**V3-QC-8 · minor · proposal §1, §6 (Newcomers, "Why"); brief "What is wrong", step 4.**

*Problem.*
- **(a) Federation gap understated.** "Strengths differing by about 100 points between federations [R 6]": the report gives offsets of +101 (VIE) and −64 (SUI/AUT), so gaps reach about 165, and [R 5] says they "can exceed 160". §2 states this correctly. The brief also drops "not peer-reviewed".
- **(b) Direction of the miscalibration mis-stated.** "Over-predicts favourites at large gaps [R 44]": the 5/6 rule is illustrated at gaps of 180–240. At large gaps under the 400-point cap, favourites were *under*-predicted: 98–100 % scored against 92 % expected [R 46]. Over-prediction at large gaps applies to the uncapped 2650+ regime [R 47].
- **(c) Phantom draws mis-described.** §6 says the 1800 phantom draws "were a one-off repair". The one-off was the compression; the draws are a standing rule (§8.2.2 [V 1]).
- **(d) K for top players.** Brief step 4 says "about 11.5 for a long-standing top player"; see V3-STAT-7.

*Fix.*
- Write "offsets from about −60 to +100, gaps over 160 [R 5] [R 6], not peer-reviewed".
- Write "too high for moderate favourites [R 44], too low under the 400-point cap [R 46]".
- Write "part of the 2024 repair".
- Tie K to activity in the brief.

**V3-QC-9 · minor · proposal §5, §10; annex T10.1, T4.4, T3.4 (hand-check details).**

*Problem.*
- **(a)** §5's "at level 2300 a 500-point favourite expects 0.926" is the function evaluated at L = 2300. The arbiter's table (band 2300–2399, midpoint 2350) gives 0.925, in the paragraph that says every figure is read from the table.
- **(b)** T10.1 uses today's K = 40 for J ("junior under 2300"). That holds only if J is at most 18 in the list year (§8.3.3). Eligibility allows 19, where today's K would be 20.
- **(c)** T4.4 quotes "K × n", where the page reads "K x n" [V 1].
- **(d)** §10's do-no-harm criterion omits "at the upper end of its 95 % interval", which T8.2 includes.
- **(e)** The normative table has 1,501 rows × 15 bands × 3 time controls (67,545 entries), against one page today.

*Fix.*
- Print 0.925, or write "the function gives".
- State J's age.
- Quote verbatim.
- Align §10 with T8.2.
- Also publish each band in table 8.1.2's range format (gap range → E).

### R-EXPLOIT

**V3-EXPLOIT-1 · major · annex T4.6 (b), T2.2, T9.4 ("compensation manufacturer"); R-EXPLOIT-2.**

*Problem.* T4.6 says the 10-game, 5-opponent, 3-event gate exists "so that same-time-control evidence dominates, compensation cannot be manufactured from another time control". It does not achieve that.
- With the shared θ and the PROVISIONAL ρ = 0.97 and ω = 8, the stationary SD of δ_tc is 32.9 points. Blitz results therefore carry into the standard estimate almost one for one.
- Reviewer's Gaussian approximation, for a junior of true strength 1500 with honest standard games at that level plus 60 arranged blitz games at a 1990 performance:

| Honest standard games | ŝ_std | σ | c_j | Club adult's gain per standard game vs the junior |
|---|---|---|---|---|
| 10 | ≈ 1869 | ≈ 58 | 270 | +5.5 |
| 30 | ≈ 1757 | — | 170 | +3.4 |

  (Adult: 1700, K = 17.0, expected gain.)
- The donors pay in blitz rating only, and blitz allows 30 rounds a day [V 2].
- Per-event line 3 marks the standard events, not the blitz event that produced the estimate.
- The same route raises a newcomer's standard seed, within the 2200 maximum.

*Fix (within D5).*
- Correct T4.6's claim and add this route to T9.4.
- For each eligible junior, report to the QC the share of the posterior precision of ŝ_{j,tc} that comes from other time controls. Flag juniors whose c_j would be 0 on same-time-control games alone.
- Run the cluster indicator in all three time controls.
- The definitional fix is FA-5.

**V3-EXPLOIT-2 · major · annex T4.5 (accrual), T5 P3 (iv), T9.4 ("one-game-a-month adjustment collector"), T9.5; proposal §5; brief step 6.**

*Problem.* a_t accrues to every player who is active under §7.2.2, whatever their number of games. The deflation it offsets is drained per game. Take T4.5's steady state, a_t = +1.3: the report's −16 a year [R 5], or about 0.53 a game at T9.1's median of 30 games.

| Player | Accrued per year | Drained per year | Net, relative to strength |
|---|---|---|---|
| 1 rated game every 12 months | 15.6 | ≈ 0.5 | +15.1 |
| 60 games a year | 15.6 | ≈ 32 | −16.4 |

- Play corrects an over-rating e by only K·E′(0)·e ≈ 0.03e a game at K = 25. The minimum-activity player is therefore about 75 points above strength after five years, with no stronger play.
- T9.4 compares the collector with "a player with the same games in one event". That is equal by construction.
- T9.5's RMSE is broken down by level and by age, not by activity.
- Under inflation the sign reverses, and light players lose.

*Fix (within D10 as written).*
- State the windfall in T4.5 and T5.
- In T9.4, measure the collector against true skill.
- Report T9.5's RMSE by activity decile.
- Monitor the mean residual S − E by games played in the trailing 12 months.
- The rule change is FA-3.

**V3-EXPLOIT-3 · major · annex T5 P4, T3.3; proposal §5 ("no choice of opponent or colour gains anything"), §11 ("so choosing opponents earns nothing").**

*Problem.* P4 conditions on gap, level and colour only. Opponents also differ in observables that predict S − E:
- federation: rung 7 is disabled, and [R 6] estimates offsets of −64 to +101;
- uncompensated juniors: below the 10/5/3 gates, or with σ too large;
- activity.

With E′(0) ≈ 0.0011 a point:
- Choosing opponents from a pool over-rated by 64 points is worth +0.7 a game at K = 10. That is nearly twice the +0.4 a game that the October 2025 amendment removed for 2650+ players [T10.2].
- At K = 17 it is +1.2 a game: about 35 a year over a 30-game season.
- Avoiding juniors under-rated by 150 points saves about 3 a game.

All of this is rule-abiding.

*Fix.*
- Qualify P4 everywhere: "given the published gap, level and colour; selection on other information that predicts results is not covered".
- Name federation choice as the remaining opponent-selection exposure until rung 7 is enabled.
- Monitor per-player gains from cross-federation games, QC-only (R3-1).

**V3-EXPLOIT-4 · major · annex T4.7, T4.8 (seed row); proposal §6 (Newcomers); script §10.**

*Problem.* Newcomers are seeded at clip(round_FIDE(θ̃_i), R_floor, R_seedmax).
- A newcomer with θ̃ = 1250 is therefore published at 1400. That creates 150 points, which the newcomer then hands to opponents at about 7 a game (K = 40).
- Re-entrants are published only if round(θ̃) ≥ 1400 (the R2-8 fix), so the two branches disagree.
- The newcomer rule contradicts §7.1.4, "The rating must be at least 1400" [V 1]. T4.7 calls that paragraph unchanged, and SPEC-L0 R-27 reads it as a publication condition.
- It rebuilds at entry the 1400 pile-up that §6 criticises [R 3] [R 4].
- Script §10's newcomer is seeded at 1650, so this branch is untested.

*Fix.*
- Use one rule for both branches: publish only if round_FIDE(θ̃_i) ≥ R_floor, with seed = min(round_FIDE(θ̃_i), R_seedmax).
- Add a sub-1400 newcomer to script §10.

**V3-EXPLOIT-5 · minor · annex T4.3, T5 P4, T8.1 (rung 2 bins), T9.4.**

*Problem.* σ can be kept high on purpose.
- At level 2350, the Davidson information per game at x = 535 is 0.34 of that at x = 0.
- At 4 games a month (σ_θ = 12), a player who meets opponents about 500 points below has σ = 61 rather than 46, and K = 20.6 rather than 12.1.
- The expected gain is zero only if the tail of the table is calibrated; a residual m pays K·m.
- Rung 2's tolerance (±0.01 per 50-point gap bin, levels pooled) admits 0.21 a game at K = 20.6. That is about half of today's +0.4 [T10.2], in bins where elite games are a small share.
- A higher K also raises the chance of touching a peak-rating threshold. Whether any title rule uses one is NOT VERIFIED here.
- P4's "a player cannot raise K_i by choosing to lose" is inexact: losses to much stronger opponents widen the fitted gaps and raise σ.

*Fix.*
- State the link between K and opponent gap in T4.3 and P4.
- Test calibration separately in the farming region (gap ≥ 400 and level ≥ 2300).
- Add a K-raising adversary to T9.4.
- Reword P4.

**V3-EXPLOIT-6 · minor · annex T6 (D11 paragraph), T8.4, T9.4 (colluding pair).**

*Problem.* v0.3 enlarges the pool of extreme-K players.
- K_min = 10 now reaches any very active player: 8 games a month at level 1700 gives σ ≈ 38.
- K_max = 40 now reaches any adult back after about three idle years: σ = √(55² + 36 × 144) = 90.6.
- Today both of these players are adults at K = 20, and their games create nothing.

What a colluding pair can do:
- At equal ratings, an arranged win for the returner creates (40 − 10) × ½ = 15 points: +20 for the returner, −5 for the donor.
- About 27 games pass before the returner's σ falls back to 55, so one return supports about 220 points of creation.

Why the monitoring misses it:
- The per-event flag marks a fixed 1 % of events, and never adds up a pair spread across events.
- The return indicator catches a 10/10 start (3.5 SD) but not 7/10 (1.4 SD).

*Fix (within D11).*
- Add a QC-only pair-level monitor: cumulative line-2 creation per pair over 12 months.
- Flag events on creation in excess of what their K mix and pairings predict, not on rank.
- Add the returner/active-donor pair to T9.4.

**V3-EXPLOIT-7 · minor · annex T4.5 (posting), T5 P3; proposal §5 ("it cannot be timed").**

*Problem.* B_i is printed and posted only in a rated month, so the player chooses when it lands.
- Under inflation (T4.5's steady state is a_t = −1.0), a player who stops playing before a rating-based cut-off keeps up to 12 points of deduction off the published list, or 18 at a_cap.
- Under deflation, one game before the cut-off posts the credit.

The amounts are bounded and visible. But "cannot be timed" holds for accrual only, and P3 does not list posting time among the elements a player can choose.

*Fix.*
- Print R_i + B_i as a "settled rating" column, and recommend it for rating-based selections.
- Add posting time to P3.

### FOR THE ARCHITECT (decision-level; listed once, not counted above)

- **FA-1 (D2, D8).** A yearly maximum-likelihood refit of κ on published ratings is biased towards flatter tables by rating noise, and the published update then re-spreads the ratings to match (V3-STAT-3). D2 needs an errors-in-variables correction, for example de-attenuation using Layer 1's σ, or κ_tc held at 1 unless the calibration test fails. Otherwise D8's "κ absorbs the spread" needs a second reference for spread.
- **FA-2 (D10, θ̃).** Define the published-scale estimate in spread as well as level: θ̃ = m_t + (ŝ − m̂_t)/κ_tc. Compensation and seeds then compare like with like (V3-STAT-4).
- **FA-3 (D10, accrual).** Uniform accrual per active month does not match a drain that occurs per game (V3-EXPLOIT-2). Consider accrual scaled by min(1, n_i over 12 months / the anchor cohort's mean games). It would still never pay more for games beyond the anchor's mean.
- **FA-4 (D3 against D17).** K_i is public and is an invertible function of σ_i; with RX_j it reveals θ̃_j for compensated minors (V3-QC-2). As written, the two decisions cannot both hold. The founder must choose between:
  - accepting and stating the disclosure;
  - publishing K on a coarse grid, at a cost in hand-checkability (whole numbers still reveal σ to ±0.8).
- **FA-5 (D5 with the shared θ).** Compute c_j from a same-time-control posterior, or add an information-share condition to eligibility. Otherwise V3-EXPLOIT-1 stays open.
- **FA-6 (D3).** The one-game gain on the published scale is q σ²/(κ_tc(1 + q²σ² v)), where v is the per-game score variance at x = 0. D3 fixes κ = 1 and v = ¼, which is 20 % low at κ = 5/6.
- **FA-7 (D1).** γ ≤ ½ is not needed for monotonicity: T3.2's bound holds for every γ ≥ 0. With the default on the boundary, either widen the range or treat a boundary fit as a calibration failure (V3-STAT-6).
- **FA-8 (AR-2 against AR-4).** In a game between two eligible juniors, AR-2 puts each one's compensation into the other's expectation, contrary to AR-4's "the junior's own update uses published ratings", and creates 10–26 points a game (V3-STAT-8). Choose one rule:
  - apply c only against non-eligible opponents; or
  - net the two, x_i = RX_i − RX_j + wη, so that the expectations sum to one.

---

## Part C — Checked and found correct

**Reproducibility and checks**
- `python3 analysis/v03_calculations.py` reproduces `analysis/OUTPUT_v0_3.md` byte for byte. Check (a) passes.
- Check (d) passes: body 4,477 words, brief 825.
- check_refs reports one unresolved path, `docs/review/REDTEAM_v0_3.md`. D-0005 D18 names that file, and it does not yet exist.

**Number provenance**
- Every number with two or more decimals in the three documents appears in OUTPUT, VERIFICATION or the research report. The exceptions are PROVISIONAL thresholds and the values in T7.2 marked illustrative.

**T3 — expected-score function and fit**
- T3.2 item 2: N′M − NM′ = 2/u + a(1 + 2γ)u^{−2γ} + a(1 − 2γ)u^{−2γ−2}, re-derived; finite differences agree to 1e−8. The bound N′M − NM′ ≥ 2/u holds for every γ ≥ 0, including γ > ½. Differentiability at the kink follows from E(−z) = 1 − E(z).
- Also re-derived:
  - symmetry;
  - the logistic special case;
  - slope κq/(2(2 + ν₀)), with local scales 480.3, 583.2 and 717.6;
  - the tail (1 + ν₀/2)e^{−z};
  - P_D/P_L = ν₀ at γ = ½;
  - colour gains of +0.85, +0.79 and +0.65.
- T3.3 score equations re-derived term by term on 200 random games; maximum error 7e−10.

**T4 — Layer 2 rules**
- T4.3: K = 11.5, 14.1, 17.0, 20.1, 27.1 and 35.0. K_min binds below σ = 41.98 and K_max above 85.87. The one-game Kalman gain holds under logistic Elo with a known opponent (information q²/4).
- T4.4: the restatement as ⌊7000/n⌋/10, and the 26.1 × 40 example.
- Band steps: 0.0256 (v0.2), 0.0164 (200-point bands, γ = ½), 0.0082 at x = 273 (100-point bands), and 0.009 in the three-decimal table. Within a band the table is off by at most half a step: ≤ 0.0041 in E, or 0.05 points a game at K = 11.5 (0.16 at K = 40). Not exploitable.
- T4.5: the a_t table; the steady state d_0 + drift/γ_a. On the one-decimal grid every d in [9.5, 10.1) is a fixed point at drift +1.3, hence 9.5 and −7.7.
- P2's bounds of 718 and 702.

**T6 — ledger**
- Per-game algebra, using E_j⁰ = 1 − E_i⁰; this is valid because the table is symmetric and L is shared.
- The monthly identity with post-update exits and entries.
- Synthetic month, games 3 and 6 recomputed by hand: 30.1600 / −14.1462 / 9.7266 / 6.2872 and −16.8800 / 26.7200 / 0 / 9.8400.
- Σ C^K = 33.5818 and Σ C^c = 18.4562. List totals go from 12505 to 14268, and the closure of +1763 is exact.

**T10 and FIDE quotations**
- T10.1 and T10.2 tables, and today's rows of table 8.1.2 [V 1]: 392–411 → .92; 433–456 → .94; 485–517 → .96; 560–619 → .98; > 735 → 1.0.
- Proposal §7's two quotations match [V 1] and [V 2] verbatim, including the missing full stop.

**Compensation, colour, fit and floor**
- Compensation thresholds 153.16 / 453.16 and 101.896 / 401.896.
- A compensation hunter has non-positive expectation if θ̃ is unbiased, because RX ≤ θ̃ − zσ − τ.
- The age gate at the calendar-year edge changes only the size of the adult's expected loss.
- Colour inside E leaves no gain from choosing a colour. A 5-point error in η is worth about 0.1 points per White game at K = 17.
- No group can move the fit: 1,000 players × 50 games is about 0.5 % of a 36-month window, and annual caps apply.
- Re-entry after the floor is gated at round(θ̃) ≥ 1400. A dive-and-re-enter re-seeds nearer the truth than today's formula does.
- Three friends can seed a newcomer at 2200 at most, the same as today: 5/5 against 2300s gives Ru = 2466, capped at 2200.

**Decisions, brief and spelling**
- D1–D18: every "Implemented in" cell of D-0005 was spot-checked. D16 (colour in §1) is present, and D14 is marked NOT VERIFIED.
- The brief matches the proposal and OUTPUT on the ladder, the ask, the −8.4 versus −5 example and the 1.5-point cap.
- Spelling is "Elo" throughout. "ELO" appears only in file names, the repository name and the title of [R 85]; D-0005 also uses "ELO-2" and "ELO-3" as session identifiers.

*End of review record.*
