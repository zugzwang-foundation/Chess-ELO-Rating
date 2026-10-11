# Modernising the FIDE Elo Rating System: an exact reference implementation plus an explainable correction layer

**Status: DRAFT v1.0 — not for publication**
Author: The Zugzwang Authors · Licence: CC BY 4.0 (`docs/LICENSE-docs.md`) · Date: 2026-10-11
Audience: FIDE's Qualification Commission (QC) and the chess public. Plain language first; the mathematics is in the technical annex.
Companion documents: the technical annex `docs/proposal/ELO-TECHNICAL-ANNEX_v1_0.md` (sections T1–T11), which holds every formula, proof sketch and worked example and is cross-referenced as [T n]; and a 900-word plain-language brief, `docs/proposal/ELO-BRIEF_v1_0.md`. Version 1.0 applies the architect's rulings R66–R73 (`docs/decisions/D-0016_rulings-on-elo-8-questions.md`: the forecast test's reading confirmed, with Freeze 3d; the rules for choosing and refitting the self-calibrating tables, the caps after a rule change, name matching and what the aggregates keep), R54–R65 (`docs/decisions/D-0014_forecast-test-and-rulings.md`: part A, the forecast test and Freeze 3b; part B, the other questions, with the self-calibrating replays to come; the forecast test's reading in `docs/decisions/D-0015_forecast-test-reading.md`), R43–R53 (`docs/decisions/D-0012_pre-results-amendments.md`, with the reading of R43 in `docs/decisions/D-0013_games-not-counted.md`, confirmed by R57), R24–R42 (`docs/decisions/D-0011_rulings-and-freeze-3.md`) and R15–R23 (`docs/decisions/D-0009_architect-rulings-elo-5.md`) on top of R1–R14 (`docs/decisions/D-0008_architect-rulings-elo-4.md`) and decisions D1–D18 (`docs/decisions/D-0005_architect-decisions-v0.3.md`), and folds in the evidence of sessions ELO-5 and ELO-6: K from FIDE's activity record [E8], the farming guard [E10], the table calibrated by level [E11], the guard re-decided [E12], the amended championship comparison [E13], the simulator rerun on that table [E14], Layer 1's grids widened [E15] and rung 2 under review, restated at today's K [E16]; and of session ELO-7: today's top 100 replayed from January 2020 under FIDE's rules and under rung 2 [E17] (Appendix G); and of session ELO-8: the self-calibrating tables, each year's table fitted only on the games before it (`docs/specs/SPEC-SELFCAL_v1_2.md`) [E18], and today's top 100 under them [E19] (Appendix H), superseding E17's figures (R59); and of session ELO-9: the greats, the players ranked 1st to 3rd on FIDE's lists since 1971, on FIDE's own data (`docs/specs/SPEC-GREATS_v1_0.md`, with the rulings R74–R79 of `docs/decisions/D-0017_rulings-on-the-greats.md`) [E20] (Appendix I).

How to read the citations. `[R §x]` points to a section of the research report `docs/research/ELO-RESEARCH_v1_0.md`; `[R n]` to the report's numbered source n; `[V k]` to item k of the primary-source sweep `docs/research/VERIFICATION_2026-10-09.md`; `[VT k]` to item k of the titles sweep `docs/research/VERIFICATION_TITLES.md`; `[VP k]` to item k of the prior-work sweep `docs/research/VERIFICATION_PRIOR-WORK.md`; `[T n]` to section n of the technical annex; `[E n]` to evidence report n under `docs/evidence/`, each the output of a committed script (E0 Layer 0 against FIDE, E1 FIDE's monthly lists, E2 the broadcast calibration, E3 the 2026 U.S. Championships, E4 the community register, E5 deflation, E6 the rungs on history, E7 federation residuals, E8 K from the activity record, E9 the simulator, E10 the farming guard, E11 the table by level, E12 the guard re-decided, E13 the championships under Freezes 3 to 3d, E14 the simulator on the v2 table, E15 Layer 1's grids widened, E16 rung 2 under review, E17 today's top 100 replayed, with a one-page summary, superseded by E19, E18 the self-calibrating tables, E19 today's top 100 under them, E20 the greats on FIDE's own data). Calculated numbers not cited to an evidence report come from `analysis/v10_calculations.py` (output `analysis/OUTPUT_v1_0.md`, cited as "script §n") and, for the table calibrated by level, from `analysis/elo6_calculations.py` (output `analysis/OUTPUT_ELO6.md`, cited as "script v2 §n"). Every FIDE rule quoted here is transcribed from [V 1] (standard) or [V 2] (rapid and blitz). Every parameter value is PROVISIONAL, a placeholder to be replaced by an estimate from data, except the expected-score table's, which are PROVISIONAL-FITTED on broadcast games [E2] [E11]. The broadcast games behind E2, E6, E7, E8, E10, E11 and E12 are stronger and more international than the rated pool; their results hold for that population until FIDE's game archive tests them. The simulator's pool is synthetic [E9] [E14].

---

## 1 Summary

**What the evidence shows.** Table 8.1.2, which turns a rating gap into an expected score, expects too much of favourites: by 0.02 to 0.05 a game at gaps of 50 to 449 points on 352,737 broadcast standard games, and by up to 0.096 in rapid [E2] [E5]. The higher-rated player is usually the favourite, so the error moves points down the list. At 2400 and above, where every K is 10, it implies a loss of 0.14 to 0.17 points a game, at least what FIDE's lists show these players losing [E5]. Juniors improve faster than their ratings: adults score 0.055 a game below today's expectation against eligible juniors, 0.047 more than against adults at the same gaps [E6]. Federations are priced differently: Ghita's cross-border directions hold on our broadcast sample for 21 of the 22 federations he names [E7]. The level of steadily active adults has not fallen since the March 2024 reform in standard and rapid [E5].

**The proposal.** Publish an exact, open-source reference implementation of FIDE's current rules, so anyone can reproduce every list. Run behind it a statistical model, re-estimated monthly, that learns what Elo assumes away: junior improvement, White's edge, draws, federation drift. Keep the published rating a forward-only Elo number on today's scale, changed per game by a hand-checkable formula, and offer the improvements as seven rungs FIDE can adopt one at a time.

**The verdicts** (section 8). RECOMMENDED NOW: rung 1, the open replica, subject to a check on 1 November; and rung 2, a self-calibrating table, refitted yearly on earlier games, with colour, draws and a slope rising with level, at today's K and guarded in the farming region, in standard: ready for the shadow list today, it changes no official rating until the shadow year confirms its calibration by level band on FIDE's data; rapid and blitz after a re-test on FIDE's games. PILOT: rung 5, junior compensation, Chess Scotland's junior additions made evidence-based. TEST ON FIDE DATA: rungs 3, 4, 6 and 7.

**The ask** (section 9). FIDE's tournament-report (TRF) archive, under a data agreement, to test rungs 3 to 7 on every rated game; a QC review with public comment; a twelve-month shadow list before any pilot. A comparison on the 2026 U.S. Championships was fixed before any result was read and amended four times after round 1 (section 10). Nothing here edits a published rating, amends the title regulations or is a black box.

---

## 2 What the data show

### 2(a) The table drains the top

On broadcast standard games between rated players, the favourite scores below table 8.1.2's expectation in every 50-point gap bin from 50 to 449 points, by 0.022 at 50–99 rising to 0.054 at 350–399; in rapid the shortfall reaches 0.096 and in blitz 0.073 [E2] [E5]. A refitted table with colour and draws passes the calibration rules on held-out months where table 8.1.2 fails, though below 2000 the level-dependent fit misses more than the first [E2] [E11] [E16]. Self-calibrating, refitted each year on earlier games only, it beat table 8.1.2 in 2025 and 2026 and, by 0.0004 nats a game against 0.048, a frozen table in 2026: consistent with self-calibration, not proof [E18].

The favourite pays the error and is usually the higher-rated player, so points move down the list, from 2200 and above to below 2000. At 2400 and above, where everyone's K is 10, the over-prediction alone implies a loss of 0.14 points a game for players rated 2400–2599 and 0.17 for 2600 and above; FIDE's lists show them losing 0.09 and 0.13 a game in 2025–26, about 4 and 7 points a year [E5]. The top has shrunk (standard; active: a rated game in the twelve months to the list) [E5]:

| list | October 2015 | October 2019 | October 2023 | October 2026 |
|---|---|---|---|---|
| active players rated 2600 or more | 225 | 242 | 195 | 150 |
| rating of the 100th active player | 2654 | 2654 | 2642 | 2626 |
| mean of the active top 100 | 2702.7 | 2700.8 | 2693.6 | 2680.5 |

This is a transfer, not a fall of the whole scale: since the March 2024 reform steadily active adults have gained 2 to 3 points a year in standard and 4 to 5 in rapid (blitz −1 to −2), and the active list's median falls, 11 to 16 a year, only because entrants arrive below the players who stop [E5] [R 5]. In a simulated pool whose true model is that table, adults whose true strength is 2400 or more lose 7.9 points a year under today's rules while their strength holds [E14].

### 2(b) Juniors drain the adults who meet them

Juniors improve faster than K = 40 lets their ratings follow: Layer 1's fitted drift is +193 latent points a year under 12 and +79 at 16–19 (`analysis/OUTPUT_L1_history.md`). The adult who meets an under-rated junior pays: on broadcast games adults score 0.055 a game below today's expectation against eligible juniors (56,030 games), 0.047 more than against adults at the same gaps [E6]. Ghita calls it a deflation tax: an adult rated 1900 who draws a junior listed at 1500 loses 8.4 points before rounding, however strong the junior is ([R 5], pp. 13, 18).

The fix is not ours. By Bryson's account in FIDE's 2023 consultation, Chess Scotland adds points to a junior's rating when computing the opponent's expected score, and Sonas named it a possible next step for FIDE [VP 4] [VP 5]. Rung 5 is that mechanism made evidence-based: the addition c_j is the part of the gap the model is 90 % sure of, less a margin τ = 25, from the junior's own games in that time control; it enters only the opponent's expectation, never the junior's own update (section 5). On broadcast games it cuts the adults' shortfall from 0.055 to 0.018 a game and improves forecasts; against a matched control the junior-specific shortfall falls from 0.047 to 0.010 [E6]. By band it gives too little below 2000 and too much against adults rated 2400 or more; τ stays constant and the result stands as measured (R18). Hence PILOT: try it where the junior data are complete.

### 2(c) Federations are priced differently

Ghita's book diagnosed it: in cross-border games players of some federations, mostly Asian, score well above their Elo expectation and players of several European federations below it, measured by a weighted, recursive cross-border index on FIDE's 2025 game extract ([R 5], pp. 23–26, 53, 66–67). We replicated his method on broadcast games: the offsets point his way for 21 of the 22 federations he names over 2023–2026, and for all 22 in years his extract cannot contain [E7]. Sizes are not compared: the sample over-represents strong players. In the simulator rung 7 cannot reach a federation that plays 1 % of its games abroad: its evidence is too thin [E14]. Whether offsets measure the pool or who travels needs FIDE's game record (section 9).

**Dropped or out of scope.** The lists show no pile-up at the 1400 floor: fewer players sit at 1400 than at each of the next nine points [E1]. The 2024 compression itself, online ratings and titles, raised often in the community, are not addressed [E4].

---

## 3 Design principles

One core skill per player, with an offset, table and volatility per time control [T2] [T3]; a forward-only number on today's scale; every change checkable by hand; open, deterministic code; caps on every parameter; a ledger of every point [T5] [T6]. The research report's eight requirements [R §7]:

| # | Requirement | Met by |
|---|---|---|
| 1 | Determinism and reproducibility | Exact decimal arithmetic with one rounding step, today's rounding (§8.3.4 [V 1]), versioned parameters, identical output from identical TRF input [T4] |
| 2 | Transparency | A yearly lookup table and a monthly parameter file, both public and versioned [T7] |
| 3 | Auditability | A per-game breakdown published with every change, and a monthly points ledger [T4] [T6] |
| 4 | Explainability | Model influence enters only through the named rungs of section 8, each a labelled line on the breakdown |
| 5 | Open-source code with test vectors | Apache-2.0 code, CC BY 4.0 documents, test vectors from FIDE's published calculations [E0] |
| 6 | Governance | The QC signs the parameter file; Council approves changes to caps or formula; public comment before changes (section 13) |
| 7 | Fairness and bias monitoring | Residuals by age, sex, rating band and colour reported monthly; by federation to the QC only while rung 7 is disabled [T8] |
| 8 | Manipulation resistance | No cliffs; a guard where farming pays; K from certainty; continuous compensation; adjustments paid per active player, never per game; anomaly monitoring; adversaries simulated [E14] [T9] |

---

## 4 The system: three layers

```
             TRF files from arbiters (monthly, §9.1 [V 1])              Monthly list snapshot
                     │                                                        │
                     ▼                                                        ▼
   ┌──────────────────────────────────────────────────────────────────────────────┐
   │  L0  REFERENCE ENGINE   exact FIDE rules (standard, rapid, blitz):           │
   │      tables 8.1.1 / 8.1.2, 400-point rules, K rules, rounding, newcomers,    │
   │      floor, inactivity. Test-vector verified. Produces today's list exactly. │
   └──────────────────────────────────────────────────────────────────────────────┘
                     │ games and lists (last 36 months)
                     ▼
   ┌──────────────────────────────────────────────────────────────────────────────┐
   │  L1  MODEL [T2]   shared skill θ, offsets δ_tc; Davidson outcome model with  │
   │      colour and draws; age-dependent drift; rolling 36-month fit, monthly.   │
   │      OUTPUTS: posterior mean and SD per player · anchor-cohort drift ·       │
   │      federation miscalibration with its evidence · junior compensations.     │
   │      It never edits a published rating.                                      │
   └──────────────────────────────────────────────────────────────────────────────┘
                     │ yearly table (fitted on published ratings) + monthly parameter file [T7]
                     ▼
   ┌──────────────────────────────────────────────────────────────────────────────┐
   │  L2  PUBLISHED RATING [T4]   forward-only, Elo-style, per game:              │
   │      R_i ← R_i + K_i · (S_i − E(x_i))                                        │
   │      Rungs of the adoption ladder (section 8), each named, capped, published:│
   │        2 table by level, colour, draws, guard 3 newcomer seeds               │
   │        4 K from certainty                      5 junior compensation         │
   │        6 monthly adjustment                    7 federation adjustment (OFF) │
   │      and the points ledger                                                   │
   └──────────────────────────────────────────────────────────────────────────────┘
```

**Layer 0, the reference engine**, is rung 1: an exact implementation of the FIDE Rating Regulations as amended 1 October 2025 [V 1] and of the Rapid and Blitz Rating Regulations [V 2] (`docs/specs/SPEC-L0_fide-reference-engine_v1_5.md`), verified against FIDE's published calculations [E0] (section 8); FIDE's online calculator is out of date (Appendix F).

**Layer 1, the model** [T2], gives each player a shared skill with an age-dependent drift and an offset per time control, refitted monthly on 36 months of games by Whole-History Rating's method [VP 11], with priors by age only, never federation, and a scale anchored to steadily active adults [VP 12] (`docs/specs/SPEC-L1_v1_0.md`). Its estimates of named players are for the QC only. **It never edits a published rating.**

**Layer 2, the published rating** [T4], is forward-only and Elo-style; the model reaches it only through the named, capped rungs of section 8. Each month Layer 0 produces the official list and Layer 2 a shadow list; the QC signs the parameter file.

---

## 5 The published rating in practice

**The update.** For each game a player's rating changes by

> R_i ← R_i + K_i · (S_i − E(x_i))

where S_i is the score (1, ½, 0), E(x_i) the expected score read from the published table for the time control and level band, and K_i the player's K for the period. The game terms are summed over the rating period, with any adjustment balance, and rounded once, as today (§8.3.4 [V 1]) [T4].

**The gap and the table.** x_i is the published rating difference plus the colour term η_tc for White and minus it for Black (36 points in standard, 37 in rapid, 27 in blitz, fitted [E11]), so an extra White no longer pays. Against an eligible junior the opponent's rating for expectation is RX_j = R_j + c_j (rung 5). The table has one block per time control and 100-point level band and a three-decimal value for every gap from 0 to 1500; its slope rises with level, as rating noise flattens it least at the top; draws rise with level and fade with the gap; there is no cap, clamp or exemption [T3] [E11]. The table is fitted on published ratings, so that where it is calibrated no choice of opponent or colour gains in expectation (property P4) [T5]. Where it is not, choosing pays: at gaps of 100 to 399 favourites still score 0.017 above it at levels of 2300 or more and 0.018 at 1500–1999, worth about +0.17 and +0.36 points a game at K = 10 and 20, and at the top White still scores 0.016 above it [E16].

**The farming guard (R17, R24, R46, R47).** The table calibrated by level cuts the favourite's residual in the farming region to +0.004 in standard (rapid +0.007, blitz +0.036) [E11], but R24's rule keeps a guard unless the residual's player-clustered interval lies within ±0.01, which on 827 to 1,020 games no table could achieve [E16]; the same test lifts it, on FIDE's games, where the region holds enough of them (R46). So at a level of 2300 or more and a gap of 400 or more, the favourite's expectation is lifted towards table 8.1.2's uncapped value at the colour-adjusted gap, blended over 50 points and stopped at 735; favourites there score 0.007 below it in standard and 0.041 below in rapid [E12]. Its limits are stated and its shape is left to FIDE's data (R47): no favourite rated below 2500 is guarded, one rating point can move it by up to 0.016, and the stop by 0.080 in rapid [E12] [E16] [T3].

**Rung 2 keeps today's K (R44).** Scaling K by the table's slope ratio (R32) is withdrawn: it raised K by 24 % to 149 %, raised the chance of touching 2500 from 2470 within 27 games from 5 % to 17 %, and forecast worse in standard and blitz [E12] [E16]. The flatter table answers a rating's error more slowly, most at the top [T3].

**K falls with the games of a period (R16, R25).** With rung 4,

> K_i(n) = clip(q · σ_i² / (κ_tc(L) · (1 + n · q² · σ_i² · v_tc(L))), 10, 40), q = ln 10 / 400

where σ_i is the model's uncertainty about the player, κ_tc(L) and v_tc(L) the table's slope and an even game's score variance in the player's band, and n the player's rated games in the period up to the end of the event rated, so each event's K is fixed with it (R25). Equivalently K_i(n) = C / (N_i + n), from printed values: C, a constant of the table in the player's band, and N_i, the model's certainty counted in games (script v2 §4) [T4]. A newcomer has 40; a player back after years away gets more; there is no switch at 30 games, 2300, 2400 or age 18. An event moves a rating at most the larger of C and 700 (R36), so three ten-game events in one period can move a newcomer 1,091 points, against today's 700.

**The monthly adjustment.** Each month the model compares the anchor cohort's published mean with its own estimate; a sixth of the gap's excess over a 2-point deadband, capped at 1.5 points a month (PROVISIONAL), is credited to active players in proportion to their games up to the cohort's average, positive in a deflating pool and negative in an inflating one, until three months after their last rated game (R33), and posted when they next play [T4]. It is judged on that gap, which must not widen by more than 2 points in twelve months (R30); the cohort's own published drift is reported, never scored, because real improvement is not drift (R15).

**The spread.** The table carries the spread; nothing is rescaled. Because a yearly refit could ratchet it, κ's annual cap stays, and the ratio of the published spread to the model's for active adults is published monthly. The QC reviews when its twelve-month mean has moved more than 0.01 since the last review and κ's yearly change was held at its cap, a ratchet's signature; either alone is reported (R31, R40; PROVISIONAL). In the simulator the ratio alone would need 0.015 to keep false alarms below 5 %; the pair caught a ratchet in every run (median 42 months), its false-alarm rate PROVISIONAL until FIDE's data (R51) [E14] [T3].

**The ledger.** Each month a ledger states, by channel, where points were created or destroyed; the identity is exact [T6].

**Worked example** [T10]. An adult, A, rated 1900, has White against a junior, J, listed at 1500 whom the model estimates at 1850 with a standard deviation of 100. J's compensation is 1850 − 1.2816 × 100 − 1500 − 25 = 196.84, so 197: J counts as 1697 in A's expectation, while J's own update uses 1500. A's K is 14.9, J's 40.0 (PROVISIONAL, one game each). Today A expects .92 with K = 20 [V 1].

| Result | A today: 20 × (S − .92) | J today: 40 × (S − .08) | A, all rungs: 14.9 × (S − 0.749) | J, all rungs: 40.0 × (S − 0.111) |
|---|---|---|---|---|
| A wins | +1.6 → **+2** | −3.2 → **−3** | +3.7399 → **+4** | −4.4400 → **−4** |
| Draw | −8.4 → **−8** | +16.8 → **+17** | −3.7101 → **−4** | +15.5600 → **+16** |
| J wins | −18.4 → **−18** | +36.8 → **+37** | −11.1601 → **−11** | +35.5600 → **+36** |

The adult loses 4 instead of 8 for drawing a junior who is really an 1850 player and 11 instead of 18 for losing. The ledger prints the 2.0860 points the compensation creates [T6].

---

## 6 Where points enter and leave

Today's rules are transcribed from [V 1] and [V 2].

| Topic | Today | Proposed | Why |
|---|---|---|---|
| **Newcomers** (rung 3) | Published after at least 5 games against rated opponents, pooled over up to 26 months, and only if at least 1400; Ra = average of rated opponents plus two hypothetical 1800-rated opponents scored as draws; Ru = Ra + dp from table 8.1.1, rounded, maximum 2200 (§7.1.4, §8.2) | Same threshold. The seed is the model's estimate on the published scale from the player's games in all three time controls and an age-only prior, at most 2200, published only if at least 1400, the model's uncertainty is at most 120 points and at least half of the estimate's precision comes from that time control (R20); the five games must involve 3 opponents in 2 events; no hypothetical opponents [T4] | Sonas called the initial-rating formula the main engine of deflation [VP 5]. On broadcast games seeds are closer to newcomers' results on average than FIDE's first ratings but noisier, and fail do-no-harm [E6]. In the simulator they are the most accurate single rung, but remove the points today's newcomers inject, so the level falls 69 points in ten years unless rung 6 runs beside them [E14] |
| **Juniors** (rung 5) | K = 40 until the end of the year of the 18th birthday while rated under 2300 (§8.3.3) | A junior (list year minus year of birth at most 19) with at least 10 rated games in the time control against 5 opponents in 3 events, half of whose estimate's precision comes from that time control (R5), carries c_j = the 90 % lower estimate on the published scale, minus the published rating, minus τ = 25, between 0 and 300 (PROVISIONAL). It enters only the expectation of opponents who are not themselves eligible (R8) and fades as the junior's rating catches up; the list flags every eligible junior (R20) [T4] | Section 2(b). τ stays constant (R18) |
| **Floor** | Below 1400 shown as unrated on the next list, then treated as unrated (§7.2.1) | Unchanged as a display rule; the model keeps estimating the player, and re-entry under §7.1.4 is seeded from that estimate only if it is at least 1400 [T4] | Re-entry through the newcomer rule injects points at the bottom; the ledger books both directions [T6] |
| **Inactivity** (rung 4) | Inactive after a year without a rated game; active again after one game (§7.2.2); no decay | No decay; the model's uncertainty grows while the player is away, so K is higher on return; no adjustment accrues from three months after the last rated game (R33) | About 40 % of listed players have not played since before the pandemic (Ghita's count [R 5]); uncertainty growth with time away is Glicko's remedy [VP 6] |
| **Monthly adjustments** (rungs 6, 7) | No rule | A global adjustment of either sign per time control, 2-point deadband, 1.5-point monthly cap (PROVISIONAL), accrued in proportion to activity up to the anchor cohort's average until three months after the last rated game and posted in a month the player plays (R3, R33); the federation adjustment the same, DISABLED [T4] [T7] | In the simulator it moves the level −2 points in ten years where today's rules move it −28, and −58 where a junior wave moves it −101, paying near its cap [E14]; US Chess holds its level with a bonus [VP 12]; Ghita proposed an activity-linked bonus first ([R 5], p. 55) |

---

## 7 Time controls and Chess960

One shared skill plus a shrunken offset per time control, so a rapid specialist is not a different person; each time control keeps its own table and volatility, because White's edge and draw rates differ by style [E2] [T2]. A rapid game reaches the classical rating only through a newcomer's seed (R5). A Chess960 rating would be one more offset [R 25] [T2]; FIDE's plan is NOT VERIFIED.

---

## 8 The adoption ladder

Seven rungs, lowest risk first, each adoptable alone: a rung not adopted leaves today's rule in place. The verdicts follow the evidence (R22): RECOMMENDED NOW for rungs whose tests support adoption now, under the conditions stated, PILOT for the rung that fixes a measured problem but misses its rule by band, TEST ON FIDE DATA for rungs only FIDE's game record can judge [T8].

| Rung | What changes | Verdict | Evidence |
|---|---|---|---|
| 1 The open replica | Nothing in the rules: an open engine reproduces today's list | **RECOMMENDED NOW**, subject to the 1 November check (R28) | Every game and tournament sum of FIDE's published calculations and the 2025 U.S. Championship reproduced; the list change in 56 of 58 multi-event periods, two one point off unexplained and disclosed [E0] |
| 2 The table calibrated by level, with the narrowed guard | Table 8.1.2 replaced by a self-calibrating table, refitted each year on the games before it within yearly caps (R65) [E18], with colour, draws and a slope rising with level; the narrowed guard at levels of 2300 or more and gaps of 400 or more; today's K (R44) | **RECOMMENDED NOW** in standard: ready for the shadow list today; it changes no official rating until the shadow year confirms calibration by level band on FIDE's data (R49) | Passes the full stage-1 rule in all three time controls, by level band and gap included (standard: 0 of 68 cells outside, Freeze 1's table 10), though the cell test detects only misses of 0.023 to 0.043, and improves log-loss on Freeze 1's table by 0.0015 nats a game in standard on the months on which its form was chosen [E11] [E16]; R24's rule keeps the narrowed guard in all three, with which the full rule passes in standard and blitz, rapid failing slope (b) and the farming region (−0.041) [E12]; below 2000 it misses by more than Freeze 1's table (1500–1599: +0.029), in part because its fit pools games from before the March 2024 compression (refitted after it: +0.023) [E16]; outside the guard's region favourites still score above it, worth up to +0.17 points a game at K = 10, which the simulator, whose truth is the table, cannot show; the region needs a favourite rated 2500 or more, and the simulated farmers mostly play outside it [E16]; R32's K × m, which forecast worse in standard and blitz, is withdrawn (R44) [E12]; in the simulator the farmer's advantage falls from 0.241 to 0.065 points a game and the slide at the top from 7.9 to 4.9 points a year [E14] |
| 3 Newcomer seeds | First rating from the model, not two 1800 draws | **TEST ON FIDE DATA** | Broadcast games: closer on average (−0.010 against −0.020) but log-loss worse by 0.050 a game [E6]; simulator: error against true strength 102 points against 120, the level −69 without rung 6 [E14] |
| 4 K from certainty | K_i(n) from the model's certainty and the period's games, one K per event (R16, R25) | **TEST ON FIDE DATA** | From FIDE's activity record: do-no-harm met overall, not in blitz; targeted rule not met (+0.00042 nats a game, interval −0.00125 to +0.00173) [E8]; simulator: error 116 and 117 (activity record, Layer 1) against 120, and alone it deepens the slide at the top (9.4 and 9.7 a year against 7.9): adopt with rung 2 [E14] |
| 5 Junior compensation | Opponents of under-rated juniors use RX_j (R5, R8) | **PILOT** | Adults' shortfall against eligible juniors 0.055 → 0.018 a game; too small below 2000, too large against adults rated 2400 or more (R18) [E6]; little effect in the simulator, whose model proxy is unsure of juniors (R39) [E14]; a per-player cap on points created through unequal K in the pilot, its size PROVISIONAL until FIDE's data (R29, R51) |
| 6 Monthly adjustment | A capped adjustment of either sign, accrual scaled by activity and ending three months after the last rated game (R33) | **TEST ON FIDE DATA** | Holds the simulated level and meets R30 in 91 % of months, but in no month of a junior wave, where it pays near its cap [E14]; on broadcast months R30 met in rapid, not in standard or blitz [E6] |
| 7 Federation adjustment | The same per federation | **TEST ON FIDE DATA** (disabled) | Direction of Ghita's residuals confirmed [E7]; cannot reach an isolated federation in the simulator [E14]; the selection test needs FIDE's record |

Rung 2 is ready for the shadow list today and changes no official rating until the shadow year confirms its calibration by level band on FIDE's data, needed because below 2000 it misses more than Freeze 1's table (R49) [E11] [E16]; the guard stays until the strict test lifts it there (R46); rapid and blitz are re-tested on FIDE's games before adoption, though on broadcast games the table passes the full rule in both (R35). Rungs 2 to 6 together recover true strength best in the simulator (error 100 points against 120), on an optimistic model proxy [E14]. Appendix H replays today's top 100 self-calibrating, superseding Appendix G [E19] [E17].

---

## 9 The request to FIDE: the tournament-report archive

Everything not recommended now waits on one thing: the games. FIDE's monthly lists record ratings and game counts, not games; the broadcast archive records games, but of the strong, internationally active part of the pool (median rating 2113 against the pool's 1734 in standard) [E2]. The tournament reports arbiters submit for every rated event (TRF, §9.1 [V 1]) hold every rated game. **We ask FIDE for that archive in all three time controls, from February 2015 or as far back as it is kept, and each month's reports during the shadow year, under a data agreement**: FIDE IDs, dates, rounds, colours, results and the uploading federation (§9.1 [V 1]), without names; analysed on FIDE's terms, never redistributed, aggregates only. Each open question then becomes a test pre-registered before the data are opened [T8]:

| The archive settles | Broadcast games cannot, because |
|---|---|
| Rung 2 in the farming region, 1,000 games per 50-point bin, and so whether the guard can lapse; rung 2 by level band, and in rapid and blitz, for the pool | The region holds 827 standard games over 21 test months [E10] |
| Rung 3: seeds for every newcomer from all their rated games | Seeds rest on broadcast games alone (659 newcomers) [E6] |
| Rung 4: certainty from every rated game and opponent | The lists give game counts, not opponents [E8] |
| Rung 5 for juniors below 2000, where the drain is largest | 3.3 % of active juniors aged 18 or less have a usable estimate (`analysis/OUTPUT_L1_history.md`) |
| Rung 6 on the whole pool's anchor cohort | The broadcast panel's gap rests on broadcast estimates [E6] |
| Rung 7: offsets by federation, and the selection test (juniors against adults who travel, home against away events) | The broadcast archive records no host federation and over-represents strong players [E7] |
| The TRF layout itself | NOT VERIFIED here (SPEC-L0 §8 Q-6): its documentation is part of the request |
| Layer 1 for the 221,130 active rated standard players | Broadcast games give 13,089 a usable estimate (`analysis/OUTPUT_L1_history.md`) |

What FIDE receives: the open engine and its test vectors, every evidence report re-run on its data, and a monthly shadow list for the chosen rungs with its parameter file, ledger and monitoring report, at no cost and with no effect on any rating, title or norm (section 14). The computation is laptop-scale [T2].

---

## 10 The 2026 U.S. Championships, pre-registered

The 2026 U.S. Championship and U.S. Women's Championship (Saint Louis, 7 to 23 October 2026; two round robins of 12 players, 66 games each) are rated on FIDE's November list [E3]. The comparison was pre-registered before any result was read and amended four times after round 1. Freeze 1, committed at 19:59 UTC on 9 October, about three hours after round 1 began if the schedule's 12:00 is Saint Louis time, hashed the comparison tool, the engine and the fitted table; Freeze 2 (D-0010, 13:58 UTC on 10 October, after round 1) hashed every file behind a number, with column (b) as rung 2 on Freeze 1's table [E3]. A review then found that table miscalibrated at both fields' levels (section 5), so Freeze 3 (D-0011, 15:22 UTC, before round 2) amended the comparison, keeping the first beside it. Freeze 3a (D-0012, 20:31 UTC, after round 2 began) withdrew R32's factor m, made the table at today's K the main column and settled games not played. Freeze 3b (D-0014, 06:21 UTC on 11 October, after round 2) added a forecast test the results decide and rebased the PILOT on (b′) [E13]. The automated check fails if a frozen file changes; the record is the tags freeze-2 to freeze-3d and GitHub's merge times. No game of either event has been read; the comparison runs once, on all games, after the last round.

**The method, fixed in advance.** For each player: (a) the event's rating change under FIDE's rules, computed by Layer 0; (b′), the main column, rung 2, the table calibrated by level with the narrowed guard at today's K; (b), Freeze 3's column, the same with K × m, and (b0), Freeze 2's, both printed as pre-registered and labelled; and each minus (a). A game §5.1 does not count is left out of every column (R43, D-0013). The guard binds in no pairing of either field (largest gaps 165 and 250) [E12]. Separately, labelled PILOT: rung 5 on top of (b′), with compensations frozen in Freeze 2 from a Layer 1 fit on games to September 2026. Rungs 3, 4, 6 and 7 are not shown. Column (a) must equal FIDE's published calculation of each player's event; a mismatch is a finding, never a reason to edit it. With 132 games, the event illustrates the rungs; it cannot test them. On the 2025 event, with the same definitions [E13] [E16 §7]:

| 2025 U.S. Championship | (a) FIDE's rules | (b′), the main column | (b), Freeze 3, K × m | (b0) |
|---|---|---|---|---|
| mean of \|x\| over the 12 players, points | 6.80 | 7.14 | 11.94 | 7.80 |
| mean of \|x − (a)\| over the 12 players, points | — | 1.94 | 5.49 | 3.33 |
| x − (a) of largest absolute value | — | −4.30 | +12.05 | −7.00 |
| players whose rounded change differs from (a) | — | 10 of 12 | 12 of 12 | 11 of 12 |

**Results, computed after the event** (E13 prints each blank):

| | U.S. Championship | U.S. Women's Championship |
|---|---|---|
| games counted: played games, as §5.1 rates them (D-0013) | {{US26_OPEN_GAMES}} | {{US26_WOMEN_GAMES}} |
| (b′), the main column: mean of \|(b′) − (a)\| over the players, unrounded, points; set by the pairings and the October list's ratings, both known before round 1, since the score cancels from (b′) − (a): results move it only through games not counted; E13 prints the values the pairings fix now, with every game played (R55: open 2.09, women 2.44) | {{US26_OPEN_MEAN_ABS_DIFF}} | {{US26_WOMEN_MEAN_ABS_DIFF}} |
| (b′): (b′) − (a) of largest absolute value, signed, unrounded; set by the pairings likewise (R55: +4.70, −7.58) | {{US26_OPEN_MAX_DIFF}} | {{US26_WOMEN_MAX_DIFF}} |
| (b′): players whose rounded change differs from (a) | {{US26_OPEN_N_DIFFER}} | {{US26_WOMEN_N_DIFFER}} |
| (b), Freeze 3, K × m: mean of \|(b) − (a)\|; not set by the pairings, since m multiplies the score (E13 prints what the pairings fix: each player's value with no point scored and with every game won) | {{US26_OPEN_B_MEAN_ABS_DIFF}} | {{US26_WOMEN_B_MEAN_ABS_DIFF}} |
| (b): (b) − (a) of largest absolute value, signed | {{US26_OPEN_B_MAX_DIFF}} | {{US26_WOMEN_B_MAX_DIFF}} |
| (b): players whose rounded change differs from (a) | {{US26_OPEN_B_N_DIFFER}} | {{US26_WOMEN_B_N_DIFFER}} |
| (b0), first pre-registration, superseded: mean of \|(b0) − (a)\|; set by the pairings likewise (R55: 3.28, 3.47) | {{US26_OPEN_B0_MEAN_ABS_DIFF}} | {{US26_WOMEN_B0_MEAN_ABS_DIFF}} |
| (b0): (b0) − (a) of largest absolute value, signed; set by the pairings likewise (R55: +7.40, −10.10) | {{US26_OPEN_B0_MAX_DIFF}} | {{US26_WOMEN_B0_MAX_DIFF}} |
| (b0): players whose rounded change differs from (a) | {{US26_OPEN_B0_N_DIFFER}} | {{US26_WOMEN_B0_N_DIFFER}} |
| players whose column (a) equals FIDE's published calculation of the event, to 0.01 | {{US26_OPEN_L0_MATCH}} of 12 | {{US26_WOMEN_L0_MATCH}} of 12 |
| PILOT, rung 5 on (b′) at today's K (R56): games of a compensated junior (c_j > 0) against an opponent not eligible (R55: 20, 9) | {{US26_OPEN_R5_GAMES}} | {{US26_WOMEN_R5_GAMES}} |
| PILOT, rung 5 on (b′): those opponents' total change minus column (b′), unrounded, points; set by the pairings likewise (R55: +14.73, +0.61). The PILOT on (b), with K × m, is withdrawn (R56); E13 reports it once, superseded (+24.22, +0.89) | {{US26_OPEN_R5_DIFF}} | {{US26_WOMEN_R5_DIFF}} |

| A forecast test the results decide, pre-registered in Freeze 3b (R54, D-0014), read as Freeze 3c fixes (D-0015) and Freeze 3d confirms (R66, D-0016), each before any result was read; E13 prints each blank: means over the counted games, with 95 % bootstrap intervals over games and over players | U.S. Championship | U.S. Women's Championship | both, pooled |
|---|---|---|---|
| stated in advance: the sample is small (at most 132 games); the difference may favour either column, or neither, and is reported whatever it shows | | | |
| three-outcome log-loss of (a), FIDE's expectation split with the level band's draw rate, nats a game | {{US26_OPEN_LL_A}} | {{US26_WOMEN_LL_A}} | {{US26_POOLED_LL_A}} |
| three-outcome log-loss of (b′), the v2 table with its guard and colour term | {{US26_OPEN_LL_BP}} | {{US26_WOMEN_LL_BP}} | {{US26_POOLED_LL_BP}} |
| log-loss, (b′) − (a): below zero favours (b′) | {{US26_OPEN_LL_DIFF}} | {{US26_WOMEN_LL_DIFF}} | {{US26_POOLED_LL_DIFF}} |
| Brier score of (a)'s expected score, (S − E)² | {{US26_OPEN_BRIER_A}} | {{US26_WOMEN_BRIER_A}} | {{US26_POOLED_BRIER_A}} |
| Brier score of (b′)'s expected score | {{US26_OPEN_BRIER_BP}} | {{US26_WOMEN_BRIER_BP}} | {{US26_POOLED_BRIER_BP}} |
| Brier score, (b′) − (a): below zero favours (b′) | {{US26_OPEN_BRIER_DIFF}} | {{US26_WOMEN_BRIER_DIFF}} | {{US26_POOLED_BRIER_DIFF}} |
| the primary endpoint (D-0015): the pooled Brier difference with its interval over games, which compares the two expectations alone, read with a sentence fixed in advance | | | {{US26_PRIMARY}} |
| how to read the intervals (D-0015, R66): every Brier line, the primary endpoint first, with its interval over games; every log-loss line with the crossed interval over players (games × players), which weights each game by both its players' draws; R54's interval over players counts each game for both its players and is narrower by construction, not a test | | | |
| crossed interval over players, log-loss of (a); of (b′) (R66) | {{US26_OPEN_LL_A_CROSSED}}; {{US26_OPEN_LL_BP_CROSSED}} | {{US26_WOMEN_LL_A_CROSSED}}; {{US26_WOMEN_LL_BP_CROSSED}} | {{US26_POOLED_LL_A_CROSSED}}; {{US26_POOLED_LL_BP_CROSSED}} |
| crossed interval over players, log-loss (b′) − (a) | {{US26_OPEN_LL_DIFF_CROSSED}} | {{US26_WOMEN_LL_DIFF_CROSSED}} | {{US26_POOLED_LL_DIFF_CROSSED}} |
| crossed interval over players, Brier (b′) − (a) | {{US26_OPEN_BRIER_DIFF_CROSSED}} | {{US26_WOMEN_BRIER_DIFF_CROSSED}} | {{US26_POOLED_BRIER_DIFF_CROSSED}} |
| secondary: log-loss (b′) − (a) with one draw model, (a)'s expectation split by (b′)'s draw probability; its crossed interval (R66) | {{US26_OPEN_LL_DIFF_SHARED}}; {{US26_OPEN_LL_DIFF_SHARED_CROSSED}} | {{US26_WOMEN_LL_DIFF_SHARED}}; {{US26_WOMEN_LL_DIFF_SHARED_CROSSED}} | {{US26_POOLED_LL_DIFF_SHARED}}; {{US26_POOLED_LL_DIFF_SHARED_CROSSED}} |
| secondary: rounds 3–11 only, played after the freezes: Brier (b′) − (a); log-loss (b′) − (a); its crossed interval (R66) | {{US26_OPEN_R3_BRIER_DIFF}}; {{US26_OPEN_R3_LL_DIFF}}; {{US26_OPEN_R3_LL_DIFF_CROSSED}} | {{US26_WOMEN_R3_BRIER_DIFF}}; {{US26_WOMEN_R3_LL_DIFF}}; {{US26_WOMEN_R3_LL_DIFF_CROSSED}} | {{US26_POOLED_R3_BRIER_DIFF}}; {{US26_POOLED_R3_LL_DIFF}}; {{US26_POOLED_R3_LL_DIFF_CROSSED}} |
| disclosed (D-0015): by the schedule, rounds 1 and 2, 24 of the 132 games, were played before Freeze 3b; the executor read no result | | | |
| fixed by the pairings: were (b′)'s forecasts exactly right, its expected advantage a game would be, in log-loss as frozen, with one draw model, and in Brier | 0.0358, 0.0173, 0.00215 | 0.0327, 0.0120, 0.00237 | |

{{US26_READING}}

---

## 11 Proof plan

**One baseline**: Layer 0, today's rules exactly; other systems are prior art (section 12). **Protocol**: rolling origin, fitting on months up to t and forecasting month t + 1; the match schedule is never a feature [R 9] [VP 10]. Each rung is scored on its targeted metric and on a do-no-harm check, against thresholds fixed in [T8] before the data were seen, R15's, R17's and R30's apart. **Data**: FIDE's monthly lists since February 2015 [V 3], analysed and never redistributed; the Lichess broadcast archive, CC BY-SA 4.0 [V 4], with its bias stated; online games are not evidence. **The simulator** (`docs/specs/SPEC-SIM_v1_0.md`) adds what no backtest can: known true strengths, ten simulated years a run, every rung on the same games as Layer 0, and adversaries; it was rerun with the table calibrated by level as the true model, rung 2 at today's K [E9] [E14].

**Success criteria (PROVISIONAL; fixed in [T8] before each data source's tests, except rung 6's rule (R15, R30) and rung 2's first guard (R17), set after [E6]; R24's guard rule was fixed before the refit [E12]).**

| Criterion | PROVISIONAL threshold |
|---|---|
| Rung 1 | 100 % of fixtures reproduced exactly; every disagreement with a published list explained by a documented FIDE-side correction |
| Rung 2 | no 50-point gap bin with at least 1,000 games significantly outside ±0.01 (Holm–Bonferroni), and none of level band and gap, across-bin calibration slope within 0.95–1.05, also in the farming region; log-loss better than Layer 0 with a bootstrap interval excluding zero |
| Rungs 3–5 | the targeted residual not significantly outside its threshold of [T8] and closer to zero than under Layer 0, by rating band; for rung 4, forecasts of the players whose K changes most better than Layer 0's |
| Rung 6 | the gap to the model not widening by more than 2 points in twelve months from the controller's thirteenth month (R30), and the level criterion of [T8] |
| Rung 7 | cross-federation residual not significantly outside ±10 points for every federation with at least 9,000 cross-border games, and the selection test passed |
| Do no harm (every rung) | overall log-loss no more than 0.002 nats per game worse than Layer 0's at the upper end of its 95 % interval, and mean absolute calibration residual no more than 0.005 worse |
| Simulator | each rung's error against true strength not above Layer 0's in any band, and no adversary gaining more than under Layer 0 [T9] |
| Hand-checkability and ledger | 100 % of a random sample of published changes recomputed exactly; the identity of [T6] satisfied exactly every month |

---

## 12 Prior work and what this proposal adds

Much of this design was proposed first by others; the full comparison, with page references, is `docs/research/PRIOR-WORK_2026-10-10.md`.

- **Ghita** (book of February 2026) diagnosed federation mispricing with a weighted, recursive cross-border index, whose direction our broadcast games confirm [E7], and proposed a monitored expectancy scale, an activity-linked bonus, safeguards with a sunset and a one-time reset for large federations ([R 5], pp. 49–59). We share the first three in other forms and do not reset: the lists show no level left to reset [E5].
- **Sonas** found the score curve shallower than the table and the ratings too spread out, and proposed the 2024 compression, the floor and the 1800 draws [VP 3] [VP 4] [VP 5]; the compression did what he intended for the level [E5].
- **Chess Scotland's junior additions**, put to FIDE in the 2023 consultation, are rung 5's mechanism [VP 4]. **Glickman**: K from certainty is Glicko's idea [VP 6]; the anchor cohort follows US Chess's monitoring of stable players [VP 12]. **URS** first combined time controls in one strength with age-based priors [VP 8]. **Whole-History Rating** is Layer 1's method [VP 11]. **Elo++** put White's advantage in a rating system in 2010 [VP 9].
- **What this proposal adds**, checked against those sources: an open reproduction of FIDE's current calculation [E0]; each change tested alone against it under rules registered first [E2] [E6] [E8] [E10]; a table with colour, and draws and slope by level, that passes calibration out of sample [E2] [E11]; a model that reaches a forward-only rating only through named, capped channels; the deflation question split into level and composition [E5]; a simulator with adversaries [E9] [E14]; a points ledger; and a comparison pre-registered (section 10).

---

## 13 Governance and the calculator FIDE can run

**Plain statement.** The "AI calculator FIDE can run" is a statistical model, re-estimated monthly, setting the numbers of a published per-game formula within caps, in public; anyone can recompute any change by hand.

**Two published files** [T7]: the yearly table per time control, with its guard, and the monthly parameter file, holding the table's parameters, the K constants, the adjustment and its anchor means, the spread ratio and its threshold, the federation adjustments (zero while disabled) and each eligible junior's compensation. N_i and RX are printed in the list. The model's estimates of named players and, while rung 7 is off, of federations go to the QC only. One disclosure is accepted (R4): a printed N_i reveals the uncertainty behind it, and with RX a compensated junior's estimate [T2].

**Ownership and process.** The QC signs the parameter file; the Council approves changes to caps or formula after public comment, with the 2023 consultation as the model [R 18] [R 19]. No published parameter moves by more than its annual cap; a fit on a boundary is a flag for the QC (R7). Rollback follows a closed list of statistical triggers [T8]; the spread trigger is a QC review, not a rollback (R19, R31). Whether the QC may publish a table yearly without a Council decision is NOT VERIFIED [T11].

**The properties the design guarantees** [T5]. P1 forward-only; P2 bounded change, at most K a game and, under rung 4, at most the larger of the table's constant C and 700 an event (C 954 to 1,327 in standard; R36; script v2 §4), or 700 without it, as today, plus the capped adjustment; P3 continuity, no caps, clamps or bracket switches, the guard's blended edges and its stop apart; P4 unbiasedness where the table is calibrated, with one stated exception, the guard's region (R24); P5 ledger completeness; P6 determinism.

**Cliffs.** Today's rules switch at a 400-point gap below 2650, at 30 games, 2300 and 2400 for K, and through two hypothetical 1800 draws [V 1] [V 2]. What remains discrete is listed in [T5]: the table's bands, the publication grids, compensation's eligibility conditions, and the guard's blended edges and its stop at 735 points. In the simulator, farming gains 0.241 points a game over ordinary play under today's rules and 0.065 with rung 2; arranged junior–adult results create points under every ledger, over ten years 0.8 a game under today's rules against 1.7–3.1 with rungs 4, 5 or 2 to 6: the ledger shows them, and R29 caps them per player in rung 5's pilot and rung 4's test, at a PROVISIONAL size (R51) [E14] [T6].

**Monitoring.** Monthly and without names: improbable mutual results, gains from far weaker opponents, residuals by level and in the guard's region, points created per event and per player; flags go to the QC [T8].

---

## 14 Roadmap

The title and norm regulations keep their text: norm arithmetic uses table 1.4.9, identical to 8.1.1, not 8.1.2 [VT 1, 3], and titles and norms use the published R only, never R + B or RX; under rung 4 an interim rating (§1.5.3 a) [VT 1]) uses each event's own K, and an adjustment counts once posted (R26); under rung 2 it uses today's K (R48); the QC assesses the effect on norms with the shadow list [T11].

| Stage [T11] | Deliverable | Gate to the next stage |
|---|---|---|
| **1. Replica and real-data tests, now** | The reference engine for standard, rapid and blitz [E0]; evidence on FIDE's lists [E1] [E5] [E8] and broadcast games [E2] [E6] [E7] [E10] [E11] [E12]; the simulator [E9] [E14]; the blind comparison on the 2026 U.S. Championships [E3] [E13]; this proposal, for QC and public comment | Layer 0 reproduces every fixture; rung 2 with its guard passes its gate in standard, rapid and blitz in stage 2; comments triaged with no unresolved correctness finding |
| **2. Shadow list, twelve months** | With the TRF archive under a data agreement (section 9): a shadow list for the chosen rungs, computed beside every official list and published with the parameter file, the ledger and the monitoring report; no effect on any rating, title or norm. Precedent, NOT VERIFIED: the parallel list of the 2008–2011 K-factor trial [R 16] | Twelve clean months; each shadowed rung meets its criteria on FIDE data; the QC's assessment of norms |
| **3. Pilot federation** | One federation's players rated under the chosen rungs, rung 5 included, for a domestic list; the official list unchanged; the federation chosen for complete game data, a large junior inflow, real cross-border play and willing leadership | Pilot report; QC recommendation |
| **4. Council decision** | Which rungs to adopt, scope and timing; no one-off jump: any gap between the shadow and official lists closes through the capped monthly adjustments | Council decision |

---

## 15 Open questions and decisions

**Open questions**, with the step that answers each:

1. Can the farming guard lapse (R46), is the table calibrated in every level band (it misses below 2000 and at 2400–2499), and does rung 2 pass in rapid and blitz on the pool? FIDE's games, by level band and gap (R24, R35) [E11] [E12]; the next fit follows SPEC-TABLE-FIT v1.2 (R50).
2. Do rungs 3 to 5 work for the juniors and newcomers below 2000 they are meant for? The TRF archive; broadcast games cover the strong end [E6].
3. Are federation offsets stable and causal, or artefacts of who travels? The TRF archive and the selection test; rung 7 stays disabled until then [E7].
4. Can rung 6 hold the level under a sustained junior wave? Under R30 it fails in standard and blitz on broadcast months and in every month of a simulated wave, paying near its cap [E6] [E14]: a faster controller is for the FIDE-data test.
5. What does R16's bound, the larger of C and 700 an event (R36), do on the pool? The FIDE-data test and the shadow list.
6. Is rounding once per period FIDE's practice? 56 of 58 periods reproduced, two one point off unexplained (SPEC-L0 v1.1); the 1 November check decides rung 1 (R28).

**Decisions taken.** Recorded in `docs/decisions/D-0002_elo-1-decision-triage.md`, `docs/decisions/D-0003_architecture-revisions-v0.2.md`, `docs/decisions/D-0005_architect-decisions-v0.3.md`, `docs/decisions/D-0008_architect-rulings-elo-4.md` (R1–R14) and, for this version, `docs/decisions/D-0009_architect-rulings-elo-5.md` (R15–R23), `docs/decisions/D-0011_rulings-and-freeze-3.md` (R24–R42 and Freeze 3) and `docs/decisions/D-0012_pre-results-amendments.md` (R43–R53 and Freeze 3a). Model estimates of named players are for the QC only, with the disclosure stated (R4); the pilot federation is chosen at stage 3; FIDE's lists are analysed, never redistributed; the out-of-date calculator is reported in Appendix F and nothing has been sent to FIDE (R14).

---

## Appendix A Mathematics

Moved to the technical annex: the notation [T1], the Layer 1 model [T2] and the expected-score function with its calibration fit [T3].
The Layer 2 rules [T4] and the properties P1–P6 [T5].
The ledger identity [T6].

---

## Appendix B Mapping to assumptions A1–A7

The research report tags each problem with the assumptions A1–A7 it breaks ([R §1], [R §3], "Ranked problem table"). The list below is the architect's canonical one (`docs/decisions/D-0003_architecture-revisions-v0.2.md`). "What breaks it" names the report sections; "Handled by" names the rung and the annex section.

| Assumption | Statement | What breaks it (report section) | Handled by (rung and annex section) |
|---|---|---|---|
| A1 | One fixed curve turns any rating gap into a forecast, at every rating level. | §3.5 forecast accuracy across gaps; problem 4 | Rung 2: a table per time control and level band, fitted on published ratings, with a slope rising with level and draws fading with the gap [T3] |
| A2 | A draw is half a win, and colour does not matter. | §3.6 draws; §3.7 colour; problems 8, 9 | Rung 2: colour term η_tc inside the gap and the draw terms [T3]; Layer 1 outcome model [T2] |
| A3 | Every game moves a rating by a fixed step, set by brackets. | §3.4 K-factor and bracket edges; §3.1 deflation; problems 1, 6 | Rung 4: K_i from certainty, no brackets [T4] |
| A4 | Playing strength changes slowly. | §3.3 juniors; §3.11 COVID-era effects; §3.1 deflation; problems 1, 5 | Rung 5: junior compensation [T4]; age-dependent drift in Layer 1 [T2] |
| A5 | The pool is well connected: everyone is indirectly compared with everyone. | §3.2 federation isolation; §3.13 matchmaking; problems 2, 12 | Rung 7: federation adjustment, disabled pending evidence and the selection test, with connectivity diagnostics [T2] [T4]; simulator tests of isolated pools [T9] |
| A6 | Rating points are conserved, so the scale holds steady. | §3.1 deflation; §3.10 inactivity; problems 1, 7 | Rung 6: monthly adjustment from anchor drift [T4]; rung 3: seeds [T4]; the ledger [T6] |
| A7 | Players do not choose their games to protect or game their rating. | §3.8 protection and game selection; §3.9 manipulation; §3.10 inactivity; problems 3, 7, 10 | Rungs 2 and 4 remove the cliffs [T5]; the farming guard where the fitted table under-predicts favourites [T3]; rung 6 paid per active player, never per game [T4]; rung 4 eases inactivity protection after return, nothing prevents it [E14]; anomaly monitoring; adversaries simulated [T9] [E14] |

The report's one-line statement of the model's assumptions, "one latent strength per player, one fixed link curve, no colour or draw structure, and slowly varying strength" [R §1], is covered by A1, A2 and A4; "one latent strength per player" is kept by this design (section 3(a)) and refined by the time-control offsets of section 7.

---

## Appendix C Sources

Every source from the research report's numbered list, with its verification status from the sweep of 2026-10-09 (`docs/research/VERIFICATION_2026-10-09.md`) and, for prior work, the sweep of 2026-10-10 (`docs/research/VERIFICATION_PRIOR-WORK.md`). VERIFIED means the page was fetched on that date and the text relied on was transcribed or paraphrased in the sweep; NOT VERIFIED means the proposal relies on the research report's reading of it. Sources cited in this draft are those that appear as `[R n]` above.

| # | Source (title as listed in the report) | URL | Status |
|---|---|---|---|
| 1 | B. PERMANENT COMMISSIONS / 02. FIDE Rating Regulations (Qualification Commission) / FIDE Rating Regulations effective from 1 March 2024 / FIDE Handbook | https://handbook.fide.com/chapter/B022024 | VERIFIED (handbook chapter fetched 2026-10-09T14:28:34Z; §7, §8 transcribed, [V 1]) |
| 2 | FIDE Adjusts Ratings For 350,000 Players In Massive Change - Chess.com | https://www.chess.com/news/view/fide-adds-rating-points-to-more-than-300-000-players | NOT VERIFIED |
| 3 | FIDE Ratings Revisited • FRBE-KBSB-KSB | https://blog.frbe-kbsb-ksb.be/blog/fide-ratings-revisited/ | VERIFIED (2026-10-10, [VP 2]: the Belgian federation's copy of the revised essay) |
| 4 | FIDE Ratings Revisited - by Vlad Ghita | https://vladchess.substack.com/p/fide-ratings-revisited | VERIFIED (2026-10-10, [VP 2]) |
| 5 | The Rating Revolution — Vlad Ghita | https://vladchess.com/rating-revolution | the book itself read in the operator's purchased copy and cited by page (ELO-4); the web page NOT VERIFIED |
| 6 | Why chess ratings don't mean what they used to | https://vladchess.substack.com/p/why-chess-ratings-dont-mean-what | VERIFIED through the Lichess copy of the same post (2026-10-10, [VP 1]) |
| 7 | FIDE Scraps 400-Point Rule For 2650+ Players, 'Triggered By Nakamura' - Chess.com | https://www.chess.com/news/view/fide-introduces-hikaru-rule-from-october | NOT VERIFIED |
| 8 | Candidates Tournament 2026 | https://en.wikipedia.org/wiki/Candidates_Tournament_2026 | NOT VERIFIED |
| 9 | Tim Salimans: How I won the Deloitte/FIDE Chess Rating Challenge | http://www.chessmetrics.com/KaggleComp/1-TimSalimans.pdf | VERIFIED (2026-10-10, [VP 10]) |
| 10 | \[PDF\] TrueSkill Through Time: Revisiting the History of Chess | https://www.semanticscholar.org/paper/TrueSkill-Through-Time:-Revisiting-the-History-of-Dangauthier-Herbrich/fe8616a7b260472ae1b61d83f3f50fd5662a1dcc | NOT VERIFIED |
| 11 | Whole-History Rating: A Bayesian Rating | https://www.remi-coulom.fr/WHR/WHR.pdf | VERIFIED (2026-10-10, [VP 11]) |
| 12 | Whole-History Rating: A Bayesian Rating System for Players of Time-Varying Strength | https://www.remi-coulom.fr/WHR/ | NOT VERIFIED |
| 13 | Chess rating system | https://en.wikipedia.org/wiki/Chess_rating_system | NOT VERIFIED |
| 14 | how elo ratings actually work | https://zwischenzug.substack.com/p/how-elo-ratings-actually-work | NOT VERIFIED |
| 15 | Elo rating system | https://en.wikipedia.org/wiki/Elo_rating_system | NOT VERIFIED |
| 16 | Rating Regulations - The K-Factor | https://old.fide.com/component/content/article/1-fide-news/3963-rating-regulations-the-k-factor.html | NOT VERIFIED |
| 17 | Changes to FIDE rating regulations - ChessTalk / Parlons Échecs | https://forum.chesstalk.com/forum/chesstalk-canada-s-chess-discussion-board-go-to-www-strategygames-ca-for-your-chess-needs/230682-changes-to-fide-rating-regulations | NOT VERIFIED |
| 18 | Proposals for changes to FIDE ratings regulations | https://en.chessbase.com/post/proposals-for-changes-to-fide-ratings-regulations | NOT VERIFIED |
| 19 | Proposals for changes to FIDE Ratings Regulations | https://www.fide.com/news/2784 | NOT VERIFIED |
| 20 | New FIDE Rating and Title Regulations come into effect | https://www.fide.com/new-fide-rating-and-title-regulations-come-into-effect/ | NOT VERIFIED |
| 21 | Proposals for changes to FIDE Ratings Regulations | https://www.fide.com/proposals-for-changes-to-fide-ratings-regulations/ | NOT VERIFIED |
| 22 | US Chess Ratings Workshop July 18, 2024 Mark E. Glickman, | https://new.uschess.org/sites/default/files/media/documents/7-18-2024-ratings-workshop-2024.pdf | VERIFIED from an archived copy; the live page refused access (2026-10-10, [VP 12]) |
| 23 | FIDE Council approves targeted amendment to Rating Regulation | https://www.fide.com/fide-council-approves-targeted-amendment-to-rating-regulation/ | NOT VERIFIED |
| 24 | FIDE updates rating regulations to include faster time controls for major events | https://www.fide.com/fide-updates-rating-regulations-to-include-faster-time-controls-for-major-events/ | NOT VERIFIED |
| 25 | Main decisions of the FIDE General Assembly 2026 | https://en.chessbase.com/post/decisions-fide-general-assembly-2026 | NOT VERIFIED |
| 26 | Timur Turlov elected President of FIDE | https://www.fide.com/timur-turlov-elected-president-of-fide/ | NOT VERIFIED |
| 27 | Dvorkovich, “It is not Nakamura’s fault, it is our fault for the deficiencies in the rating system” | https://www.chessdom.com/dvorkovich-it-is-not-nakamuras-fault-it-is-our-fault-for-the-deficiencies-in-the-rating-system/ | NOT VERIFIED |
| 28 | Timur Turlov Elected FIDE President, Becomes First Kazakh to Lead World Chess | https://www.prnewswire.com/news-releases/timur-turlov-elected-fide-president-becomes-first-kazakh-to-lead-world-chess-302890770.html | NOT VERIFIED |
| 29 | Ratings Committee Report | https://new.uschess.org/sites/default/files/media/documents/4-15-2024-rc-report-24-mm-eedit.pdf | NOT VERIFIED |
| 30 | FIDE Rating System Changes | https://new.uschess.org/civicrm/mailing/view?reset=1&id=4738&cid= | NOT VERIFIED |
| 31 | Ratings Committee Report | https://new.uschess.org/sites/default/files/media/documents/0001-2025-ratings-committee-report-rc-report-25-rm.pdf | NOT VERIFIED |
| 32 | Change to US Chess Ratings: Bonus Threshold Lowered | https://new.uschess.org/news/change-us-chess-ratings-bonus-threshold-lowered-2025 | NOT VERIFIED |
| 33 | zwischenzug.substack.com | https://zwischenzug.substack.com/p/ratings-are-broken/comments | NOT VERIFIED |
| 34 | Chess rating systems • lichess.org | https://lichess.org/page/rating-systems | NOT VERIFIED |
| 35 | 1 Compression and Calculation Improvements: Supplemental Report | https://www.fide.com/docs/presentations/Sonas%20Supplemental%20Report.pdf | VERIFIED (2026-10-10, [VP 4]) |
| 36 | Universal Rating System | https://en.wikipedia.org/wiki/Universal_Rating_System | VERIFIED, with the system's own site (2026-10-10, [VP 8]) |
| 37 | 1 Sonas Proposal: Repairing the FIDE Standard Elo rating system | https://www.fide.com/docs/presentations/Sonas%20Proposal%20-%20Repairing%20the%20FIDE%20Standard%20Elo%20Rating%20System.pdf | VERIFIED (2026-10-10, [VP 3]) |
| 38 | FIDE Mathematician Proposes Changes To Improve Rating Accuracy - Chess.com | https://www.chess.com/news/view/fide-mathematician-proposes-changes-to-improve-rating-accuracy | NOT VERIFIED |
| 39 | Sonas Proposal - Repairing the FIDE Standard Elo Rating System | https://www.scribd.com/document/668330896/Sonas-Proposal-Repairing-the-FIDE-Standard-Elo-Rating-System | NOT VERIFIED |
| 40 | FIDE ratings - May 2026 | https://en.chessbase.com/post/fide-ratings-may-2026 | NOT VERIFIED |
| 41 | Rating changes coming to FIDE? - ChessTalk / Parlons Échecs | https://forum.chesstalk.com/forum/chesstalk-canada-s-chess-discussion-board-go-to-www-strategygames-ca-for-your-chess-needs/227820-rating-changes-coming-to-fide | NOT VERIFIED |
| 42 | Why chess ratings don't mean what they used to • page 1/9 • Community Blog Discussions • lichess.org | https://lichess.org/forum/community-blog-discussions/ublog-tVDQ1LiL | NOT VERIFIED |
| 43 | FIDE Ratings Revisited • page 4/5 • Community Blog Discussions • lichess.org | https://lichess.org/forum/community-blog-discussions/ublog-BN89yF7d?page=4 | NOT VERIFIED |
| 44 | Jeff Sonas | https://en.wikipedia.org/wiki/Jeff_Sonas | NOT VERIFIED |
| 45 | On the Probability of Magnus Carlsen reaching 2900 | https://arxiv.org/pdf/2208.09563 | NOT VERIFIED |
| 46 | The Elo rating system | https://en.chessbase.com/post/the-elo-rating-system-correcting-the-expectancy-tables | NOT VERIFIED |
| 47 | Why FIDE dropped the 400 point rule | https://en.chessbase.com/post/why-fide-dropped-the-400-point-rule | NOT VERIFIED |
| 48 | Large-scale Analysis of Chess Games with Chess Engines: A Preliminary Report | https://arxiv.org/pdf/1607.04186 | NOT VERIFIED |
| 49 | Computer Gaming | https://herbrich.me/computer-gaming/ | NOT VERIFIED |
| 50 | CheckRaiseMate's Blog • How Elo Ratings Actually Work • lichess.org | https://lichess.org/@/CheckRaiseMate/blog/how-elo-ratings-actually-work/J8UZThlO | NOT VERIFIED |
| 51 | First Move Advantage in Chess - An Antic Disposition | https://www.robweir.com/blog/2014/01/first-move-advantage-in-chess.html | NOT VERIFIED |
| 52 | Fairer Chess: A Reversal of Two Opening Moves in Chess Creates Balance Between White and Black | https://arxiv.org/pdf/2108.02547 | NOT VERIFIED |
| 53 | FIDE Announces New Qualification Path For 2026 Candidates Tournament - Chess.com | https://www.chess.com/news/view/fide-announces-candidates-2026-qualification-changes | NOT VERIFIED |
| 54 | Hikaru Nakamura responds to critics: “I’m not farming for rating at state championships” | https://www.attackingchess.com/hikaru-nakamura-responds-to-critics-im-not-farming-for-rating-at-state-championships/ | NOT VERIFIED |
| 55 | FIDE changes rating regulations | https://en.chessbase.com/post/fide-changes-rating-regulations | NOT VERIFIED |
| 56 | Rating analytics: The number of rated chess players goes up | https://www.fide.com/rating-analytics-the-number-of-rated-chess-players-goes-up/ | NOT VERIFIED |
| 57 | Frequently Asked Questions • lichess.org | https://lichess.org/faq | NOT VERIFIED |
| 58 | FIDE adjusts its ratings to be more in line with Lichess (not really) • Lichess's Blog • lichess.org | https://lichess.org/@/Lichess/blog/fide-adjusts-its-ratings-to-be-more-in-line-with-lichess-not-really/ct5Uwjru | NOT VERIFIED |
| 59 | Matchmaking Ruins Everything | https://medium.com/invokation-games/matchmaking-ruins-everything-053f51527289 | NOT VERIFIED |
| 60 | The Deloitte/FIDE Chess Rating Challenge | https://en.chessbase.com/post/the-deloitte-fide-che-rating-challenge | VERIFIED (2026-10-10, [VP 10]) |
| 61 | How I won the "Chess Ratings - Elo vs the Rest of the World" Competition | https://arxiv.org/pdf/1012.4571 | VERIFIED (2026-10-10, [VP 9]) |
| 62 | Sonas: The Deloitte/FIDE Chess Rating Challenge | https://en.chessbase.com/post/sonas-the-deloitte-fide-che-rating-challenge | VERIFIED (2026-10-10, [VP 10]) |
| 63 | Could World Chess Ratings be decided by the ‘Stephenson System’? | https://medium.com/kaggle-blog/could-world-chess-ratings-be-decided-by-the-stephenson-system-2fba2715cf34 | NOT VERIFIED (HTTP 403 on 2026-10-10, no archived copy, [VP 10]) |
| 64 | Glicko rating system | https://en.wikipedia.org/wiki/Glicko_rating_system | NOT VERIFIED |
| 65 | Whole History Rating (WHR) of Active Gomoku Players - Gomoku Rating | https://gomokurating.renju.net/ | NOT VERIFIED |
| 66 | Whole-History Rating: A Bayesian Rating System for Players of Time-Varying Strength | https://link.springer.com/chapter/10.1007/978-3-540-87608-3_11 | NOT VERIFIED |
| 67 | R%C3%A9mi Coulom | https://en.wikipedia.org/wiki/R%C3%A9mi_Coulom | NOT VERIFIED |
| 68 | Whole-History Rating: A Bayesian Rating System for Players of Time-Varying Strength | https://www.researchgate.net/publication/29621364_Whole-History_Rating_A_Bayesian_Rating_System_for_Players_of_Time-Varying_Strength | NOT VERIFIED |
| 69 | TrueSkill Through Time: Revisiting the History of Chess Pierre Dangauthier | https://www.herbrich.me/papers/ttt.pdf | NOT VERIFIED |
| 70 | TrueSkillThroughTime: Skill Estimation Based on a Single Bayesian Network | https://cran.rstudio.com/web/packages/TrueSkillThroughTime/index.html | NOT VERIFIED |
| 71 | Hikaru Nakamura Accused of "Farming" Ratings at Small Louisiana Tournament | https://www.attackingchess.com/hikaru-nakamura-accused-of-farming-ratings-at-small-louisiana-tournament/ | NOT VERIFIED |
| 72 | Download latest official FIDE Rating list. | https://ratings.fide.com/download_lists.phtml | VERIFIED (fetched 2026-10-09T14:28:44Z, [V 3]) |
| 73 | lichess.org open database | https://database.lichess.org/ | VERIFIED (fetched 2026-10-09T14:28:53Z, [V 4]) |
| 74 | Lichess's Blog • Lichess: End of Year Update 2025 • lichess.org | https://lichess.org/@/Lichess/blog/lichess-end-of-year-update-2025/YRiNKoaQ | NOT VERIFIED |
| 75 | Lichess rating to FIDE Elo : here we go again | https://antoinebfr.medium.com/lichess-rating-to-fide-elo-here-we-go-again-14d6a8fd31dc | NOT VERIFIED |
| 76 | number of games per month • page 1/1 • Lichess Feedback • lichess.org | https://lichess.org/forum/lichess-feedback/number-of-games-per-month | NOT VERIFIED |
| 77 | Lichess/standard-chess-games · Datasets at Hugging Face | https://huggingface.co/datasets/Lichess/standard-chess-games | NOT VERIFIED |
| 78 | GitHub - samuraitruong/fide-ratings-utils: Simple script to broken down fide rating file to smaller by federation, by age division · GitHub | https://github.com/samuraitruong/fide-ratings-utils | NOT VERIFIED |
| 79 | GitHub - rmarabini/player\_info\_from\_fide\_database: Download players information from FIDE Database · GitHub | https://github.com/rmarabini/player_info_from_fide_database | NOT VERIFIED |
| 80 | GitHub - goshrine/whole\_history\_rating: A pure ruby implementation of Rémi Coulom's Whole-History Rating (WHR) algorithm. | https://github.com/goshrine/whole_history_rating | VERIFIED (licence MIT via GitHub API 2026-10-09T14:28:56Z, [V 5]) |
| 81 | Remi-Coulom (Rémi Coulom) · GitHub | https://github.com/Remi-Coulom | VERIFIED for the WHR repository github.com/Remi-Coulom/WHR (licence MIT, [V 5]); the profile page itself was not fetched |
| 82 | GitHub - wind23/whole\_history\_rating: A Python interface incorporating a C++ implementation of the Whole History Rating algorithm · GitHub | https://github.com/wind23/whole_history_rating | VERIFIED (licence MIT via GitHub API 2026-10-09T14:28:56Z, [V 5]) |
| 83 | TrueSkill Through Time: Revisiting the History of Chess | https://www.researchgate.net/publication/221619020_TrueSkill_Through_Time_Revisiting_the_History_of_Chess | NOT VERIFIED |
| 84 | Chess Statistics Today | https://en.chessbase.com/post/chess-statistics-today | NOT VERIFIED |
| 85 | (PDF) FIFA Rankings vs ELO Ratings: Predictive Validity in World Cup Knockout Stages (1994-2022) | https://www.researchgate.net/publication/406281676_FIFA_Rankings_vs_ELO_Ratings_Predictive_Validity_in_World_Cup_Knockout_Stages_1994-2022 | NOT VERIFIED |
| 86 | First-move advantage in chess | https://en.wikipedia.org/wiki/First-move_advantage_in_chess | NOT VERIFIED |
| 87 | Deloitte/FIDE Chess Rating Challenge - Standings - CLIST | https://clist.by/standings/deloittefide-chess-rating-challenge-14828013/ | NOT VERIFIED |

Sources listed: 87. Additional primary sources verified in Phase 1 that are not in the report's numbered list: the FIDE Rapid and Blitz Rating Regulations chapter (https://handbook.fide.com/chapter/B02RBRegulations2024, VERIFIED, [V 2]); the lila repository licence (https://github.com/lichess-org/lila, AGPL-3.0, VERIFIED, [V 5]); FIDE's calculator page (https://ratings.fide.com/calc.phtml?page=change, reachable, HTTP 200, content not transcribed).

---



## Appendix D Illustrations of the provisional parameters, the caps and today's cliffs

Moved to the technical annex: the expected-score function, its calibration fit and its comparison with table 8.1.2 and the 5/6-gap rule [T3]; the Layer 2 rules, caps and channel table [T4].

---

## Appendix E Further worked examples

Moved to the technical annex: all worked examples, hand-checkable against the PROVISIONAL parameters, are in [T10].

---

## Appendix F Findings for the QC (R14, R64)

Two findings from checking Layer 0 against FIDE, reported here for the QC; nothing has been sent to FIDE (founder defaults: D-0008, R14; D-0014, R64).

**F.1 FIDE's online calculator is out of date.** FIDE's online calculator (https://ratings.fide.com/calc.phtml) was probed on 2026-10-09 with 24 rating-change cases and 8 initial-rating cases, recorded as fixtures F-C01 to F-C24 and F-I01 to F-I08 (`tests/fixtures/fide_calculator/`). The rating-change calculator reproduces table 8.1.2 and the multiplication by K, but applies the 400-point cap to every player: it agrees with §8.3.1 as written from 1 October 2025 in 20 of 24 cases and with a plain cap in 24 of 24, the four differences being players rated 2650 or above with a gap over 400 [V 1]. The initial-rating calculator follows the archived rule of 1 January 2022 till 29 February 2024 [VT 2] in 8 of 8 cases and the current rule, with its two hypothetical 1800 draws, in 1 of 8, by coincidence (`analysis/OUTPUT_L0_fixtures.md` §2–3; SPEC-L0 §6.1). Layer 0 therefore takes its test vectors from FIDE's published calculations, not from the calculator: every game and tournament sum of five adults' calculations, one first rating and 58 multi-event periods is reproduced, and the list change in 56 of the 58, six after FIDE's own base corrections; two are one point off without explanation, and one earlier period (F-P02) follows rounding per tournament, not once per period (`analysis/OUTPUT_L0_rounding.md`) [E0].

**F.2 FIDE's lists sometimes depart from FIDE's own calculations.** Replaying today's top 100 from January 2020 with the rules in force at each date, Layer 0 reproduces FIDE's published calculation of 35,620 of 35,621 games and the published change of 3,680 of 3,685 player-periods [E17 §2]. Of the five periods it does not reproduce, four are lists that differ from FIDE's own calculation of the same period: FIDE ID 12923044 on the February 2020 list (published +0 where FIDE's page totals +0.90, which rounds to +1; never made good, so the replay stays one point above the list through October 2026), 44155573 on the December 2022 list (+5 where the page totals +4.40) and on the May 2024 list (−1 where it totals +0.40), and 4107012 on the May 2024 list (+24 where it totals +25.00); the fifth, 35093487 on the May 2022 list, follows rounding per tournament (−9 where the period's −8.40 rounds to −8), and a +1 on the next list, a list without games, reverses it. Four published changes fall on lists on which the player has no rated game, FIDE's corrections outside any calculation: 35093487 (June 2022), 2047640 (April and May 2024) and 4107012 (April 2024), each reversing or reversed by another. In one tournament (30901561, April 2022) FIDE marked two of a favourite's games capped where the 2022 text allows one upgrade; once (4107012, January 2026) FIDE marks as capped a rating 350 points away and computes the game uncapped; and in two tournaments FIDE used the K of the list in force at the tournament's start, not that of the list before the one rating it (SPEC-L0 R-22b, §11) [E17 §2]. Each case and its cause is in E17 §2. None is a reason to edit a published rating, which stays the reference.

---

## Appendix G Today's top 100 under rung 2

> **Superseded before any public use** (ruling R59, D-0014): one table, fitted on broadcast games of October 2023 to September 2026, serves every year of this replay, with FIDE's K. The self-calibrating replay of session ELO-8 [E19], in which each year's table is fitted only on games played before that year and K follows FIDE's rules on each system's own rating, replaces these figures.

*Under this rule, with the same results — not anyone's true strength.*

What the 100 highest-rated active players of FIDE's October 2026 standard list would be rated if every standard game FIDE rated for them from January 2020 had been rated by rung 2 as recommended (section 8: the table calibrated by level, with the narrowed guard, at today's K), with the same results and the same K [E17]. Each player starts from the January 2020 list, and the 100 are replayed together, month by month, from FIDE's published per-player calculations. Layer 0, applying the rules in force at each date, was checked first: given FIDE's own inputs, it reproduces FIDE's calculation in 35,620 of 35,621 games and the published rating on every list for 95 of the 100 players, the October 2026 rating for 99 [E17 §2]. The difference is rung 2's replay minus Layer 0's; the rung-2 rating is the published rating plus the difference. Colours come from broadcast games, 62 % of the games; a game without a known colour carries no colour term [E17 §8].

With the opponents outside the 100 held at their published ratings, in October 2026 the mean difference is +23.3 points (+15.2 to +31.5 with those opponents rated 10 points lower or higher under rung 2, R58; the table +23.7, colour −0.4), from −1 to +45; 93 of the 100 change rank, by at most 19 places; under FIDE's rules 33 are rated 2700 or more and 1 is rated 2800 or more, under rung 2, 42 and 6 [E17 §3–§5].

Read with these caveats [E17 §9]:

- Opponents outside the 100 keep their published ratings, although under rung 2 theirs would differ too, and the group's gain comes from those games: within the 100 the exchange balances (−0.05 points per player, against +24.3 from the games outside it) [E17 §4]. To first order, each point by which those opponents would on average be rated higher or lower moves the mean difference by about 2.4 points; rerun with them 5 or 10 points lower or higher at every date, the mean is +15.2, +19.3, +27.5 and +31.5 (R58) [E17 §9], so the figures, and the counts above 2700 and 2800 most of all, rest on this approximation.
- The difference mixes FIDE's error with rung 2's: on held-out months the v2 table still expects too little of favourites at levels 2300 to 2499 [E16 §1, §5], and the replay cannot separate the two.
- Near equal ratings the v2 table is flatter than table 8.1.2 at the top (annex T3.5), so counts above 2700 and 2800 compare two scales as well as two rules.
- The table was fitted on broadcast games of October 2023 to September 2026, so the replay is in sample from the November 2023 list and out of sample before it.
- The 100 are chosen in October 2026, so players who left the top earlier are not replayed.
- Colours come from broadcasts, 62 % of the games [E17 §8].
- Layer 0 reads the 400-point rule of March 2024 to September 2025 as the plain cap, NOT VERIFIED against the handbook; FIDE's calculations agree with that reading in all 111 tournaments that can tell [E17 §2].
- The figures describe the rule, not the players: who is stronger is not their question.

*Under this rule, with the same results — not anyone's true strength.*

| rank | FIDE ID | October 2026 | rung 2 | difference | the table's effect | colour's effect | games | share as favourite | mean gap | colour balance (matched) | rank under rung 2 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 1503014 | 2823 | 2868 | +45 | +47 | −2 | 230 | 1.00 | +166.3 | +5 of 171 | 1 |
| 2 | 2016192 | 2792 | 2818 | +26 | +27 | −1 | 158 | 0.79 | +133.2 | −2 of 72 | 4 |
| 3 | 2020009 | 2784 | 2829 | +45 | +46 | −1 | 466 | 0.91 | +83.0 | +5 of 281 | 2 |
| 4 | 14205483 | 2782 | 2816 | +34 | +33 | +1 | 379 | 0.68 | +73.0 | +4 of 270 | 5 |
| 5 | 14204118 | 2780 | 2819 | +39 | +40 | −1 | 461 | 0.80 | +88.9 | −2 of 336 | 3 |
| 6 | 5202213 | 2770 | 2802 | +32 | +32 | +0 | 314 | 0.71 | +49.3 | −3 of 195 | 6 |
| 7 | 25059530 | 2763 | 2798 | +35 | +35 | +0 | 509 | 0.68 | +72.3 | −9 of 379 | 8 |
| 8 | 12940690 | 2761 | 2798 | +37 | +39 | −2 | 458 | 0.67 | +42.6 | +9 of 381 | 7 |
| 9 | 8603405 | 2758 | 2786 | +28 | +30 | −2 | 196 | 0.80 | +108.2 | +4 of 124 | 12 |
| 10 | 12573981 | 2757 | 2788 | +31 | +31 | +0 | 276 | 0.69 | +45.6 | +6 of 188 | 11 |
| 11 | 24116068 | 2752 | 2790 | +38 | +38 | +0 | 377 | 0.78 | +65.0 | −4 of 290 | 9 |
| 12 | 35009192 | 2746 | 2789 | +43 | +43 | +0 | 635 | 0.88 | +136.6 | +4 of 456 | 10 |
| 13 | 1170546 | 2741 | 2761 | +20 | +23 | −3 | 218 | 0.65 | +46.1 | +4 of 172 | 14 |
| 14 | 5000017 | 2739 | 2748 | +9 | +11 | −2 | 51 | 0.78 | +67.0 | +2 of 48 | 20 |
| 15 | 3503240 | 2732 | 2750 | +18 | +16 | +2 | 152 | 0.65 | +78.2 | −5 of 51 | 17 |
| 16 | 12401137 | 2732 | 2751 | +19 | +19 | +0 | 86 | 0.87 | +78.4 | −1 of 71 | 15 |
| 17 | 44599790 | 2731 | 2744 | +13 | +12 | +1 | 465 | 0.51 | +64.6 | +6 of 276 | 25 |
| 18 | 12521213 | 2728 | 2762 | +34 | +35 | −1 | 519 | 0.81 | +114.4 | −7 of 357 | 13 |
| 19 | 13300474 | 2725 | 2751 | +26 | +26 | +0 | 288 | 0.70 | +50.2 | −2 of 176 | 16 |
| 20 | 8603677 | 2723 | 2741 | +18 | +21 | −3 | 180 | 0.71 | +72.8 | +3 of 107 | 27 |
| 21 | 4168119 | 2719 | 2750 | +31 | +31 | +0 | 251 | 0.79 | +61.9 | +1 of 133 | 18 |
| 22 | 623539 | 2717 | 2745 | +28 | +30 | −2 | 383 | 0.64 | +64.5 | −1 of 285 | 23 |
| 23 | 2093596 | 2717 | 2749 | +32 | +33 | −1 | 821 | 0.80 | +116.7 | +1 of 409 | 19 |
| 24 | 1039784 | 2716 | 2744 | +28 | +30 | −2 | 605 | 0.77 | +92.2 | +6 of 472 | 24 |
| 25 | 4158814 | 2714 | 2735 | +21 | +21 | +0 | 99 | 0.84 | +94.6 | +2 of 64 | 30 |
| 26 | 14203987 | 2712 | 2734 | +22 | +24 | −2 | 469 | 0.70 | +100.0 | −1 of 301 | 32 |
| 27 | 738590 | 2711 | 2741 | +30 | +33 | −3 | 310 | 0.79 | +75.9 | +1 of 237 | 26 |
| 28 | 13401319 | 2710 | 2746 | +36 | +38 | −2 | 337 | 0.85 | +107.4 | +8 of 284 | 21 |
| 29 | 46616543 | 2710 | 2746 | +36 | +38 | −2 | 588 | 0.78 | +118.9 | +5 of 395 | 22 |
| 30 | 25092340 | 2709 | 2740 | +31 | +33 | −2 | 446 | 0.79 | +115.4 | +8 of 322 | 28 |
| 31 | 2040506 | 2708 | 2727 | +19 | +19 | +0 | 252 | 0.66 | +41.9 | +9 of 127 | 33 |
| 32 | 12539929 | 2705 | 2736 | +31 | +31 | +0 | 470 | 0.82 | +106.7 | +11 of 365 | 29 |
| 33 | 8603820 | 2704 | 2735 | +31 | +34 | −3 | 299 | 0.89 | +121.6 | +12 of 232 | 31 |
| 34 | 2900084 | 2695 | 2703 | +8 | +6 | +2 | 32 | 0.75 | +67.0 | −4 of 20 | 41 |
| 35 | 8602883 | 2694 | 2719 | +25 | +25 | +0 | 136 | 0.84 | +126.8 | −6 of 72 | 36 |
| 36 | 5029465 | 2693 | 2719 | +26 | +26 | +0 | 261 | 0.76 | +64.7 | +1 of 187 | 35 |
| 37 | 24130737 | 2691 | 2723 | +32 | +33 | −1 | 425 | 0.85 | +109.3 | +11 of 331 | 34 |
| 38 | 13400924 | 2689 | 2707 | +18 | +19 | −1 | 76 | 0.68 | +69.2 | −1 of 59 | 39 |
| 39 | 2056437 | 2685 | 2708 | +23 | +25 | −2 | 376 | 0.85 | +237.7 | +4 of 128 | 37 |
| 40 | 24175439 | 2680 | 2708 | +28 | +28 | +0 | 524 | 0.76 | +102.2 | −3 of 279 | 38 |
| 41 | 13413937 | 2679 | 2698 | +19 | +22 | −3 | 567 | 0.68 | +70.0 | −2 of 412 | 44 |
| 42 | 5072786 | 2677 | 2704 | +27 | +29 | −2 | 399 | 0.79 | +140.5 | +7 of 309 | 40 |
| 43 | 25060783 | 2677 | 2699 | +22 | +22 | +0 | 596 | 0.71 | +144.9 | +11 of 357 | 43 |
| 44 | 35028600 | 2674 | 2694 | +20 | +21 | −1 | 566 | 0.76 | +154.0 | +21 of 277 | 45 |
| 45 | 24133795 | 2671 | 2701 | +30 | +28 | +2 | 499 | 0.83 | +116.3 | −4 of 370 | 42 |
| 46 | 24651516 | 2666 | 2687 | +21 | +20 | +1 | 530 | 0.76 | +87.0 | +5 of 397 | 49 |
| 47 | 410608 | 2665 | 2682 | +17 | +17 | +0 | 116 | 0.77 | +122.8 | −6 of 54 | 53 |
| 48 | 14200244 | 2665 | 2685 | +20 | +19 | +1 | 102 | 0.94 | +155.6 | −3 of 75 | 50 |
| 49 | 14102951 | 2664 | 2689 | +25 | +26 | −1 | 315 | 0.88 | +123.4 | −8 of 198 | 47 |
| 50 | 703303 | 2663 | 2672 | +9 | +8 | +1 | 35 | 0.71 | +59.5 | −5 of 31 | 67 |
| 51 | 4152956 | 2663 | 2689 | +26 | +25 | +1 | 298 | 0.87 | +83.7 | +7 of 215 | 46 |
| 52 | 12923044 | 2662 | 2684 | +22 | +22 | +0 | 504 | 0.72 | +94.2 | +18 of 396 | 51 |
| 53 | 13409301 | 2662 | 2680 | +18 | +18 | +0 | 509 | 0.62 | +78.0 | −5 of 301 | 55 |
| 54 | 13306553 | 2661 | 2687 | +26 | +25 | +1 | 567 | 0.80 | +113.6 | +6 of 376 | 48 |
| 55 | 2023970 | 2659 | 2673 | +14 | +15 | −1 | 182 | 0.63 | +36.3 | −5 of 97 | 64 |
| 56 | 1118358 | 2658 | 2680 | +22 | +24 | −2 | 364 | 0.78 | +80.1 | +8 of 290 | 54 |
| 57 | 2047640 | 2656 | 2669 | +13 | +14 | −1 | 215 | 0.78 | +150.5 | +4 of 100 | 69 |
| 58 | 44155573 | 2656 | 2684 | +28 | +25 | +3 | 567 | 0.71 | +93.3 | −5 of 311 | 52 |
| 59 | 1226380 | 2654 | 2679 | +25 | +24 | +1 | 430 | 0.75 | +92.2 | −2 of 378 | 58 |
| 60 | 3805662 | 2654 | 2678 | +24 | +23 | +1 | 368 | 0.92 | +217.4 | −2 of 66 | 59 |
| 61 | 4116992 | 2654 | 2659 | +5 | +5 | +0 | 32 | 1.00 | +368.6 | +0 of 0 | 74 |
| 62 | 24126055 | 2654 | 2680 | +26 | +27 | −1 | 232 | 0.78 | +96.9 | +1 of 79 | 57 |
| 63 | 24101605 | 2653 | 2680 | +27 | +27 | +0 | 306 | 0.86 | +111.5 | −4 of 144 | 56 |
| 64 | 8601445 | 2651 | 2673 | +22 | +22 | +0 | 187 | 0.87 | +146.6 | −1 of 107 | 65 |
| 65 | 14117908 | 2651 | 2673 | +22 | +23 | −1 | 162 | 0.92 | +161.9 | +12 of 108 | 66 |
| 66 | 2285525 | 2650 | 2674 | +24 | +23 | +1 | 495 | 0.79 | +112.6 | −6 of 362 | 62 |
| 67 | 14204223 | 2649 | 2669 | +20 | +21 | −1 | 440 | 0.67 | +100.6 | −3 of 245 | 70 |
| 68 | 5007003 | 2648 | 2678 | +30 | +31 | −1 | 361 | 0.82 | +76.9 | +3 of 275 | 60 |
| 69 | 13306766 | 2648 | 2674 | +26 | +24 | +2 | 529 | 0.82 | +122.3 | +1 of 351 | 63 |
| 70 | 1510045 | 2647 | 2655 | +8 | +7 | +1 | 513 | 0.78 | +222.8 | +7 of 277 | 82 |
| 71 | 5074452 | 2647 | 2675 | +28 | +26 | +2 | 378 | 0.83 | +137.6 | −2 of 234 | 61 |
| 72 | 2004887 | 2646 | 2665 | +19 | +21 | −2 | 304 | 0.61 | +51.3 | −2 of 170 | 72 |
| 73 | 5084423 | 2646 | 2667 | +21 | +21 | +0 | 346 | 0.76 | +114.1 | +3 of 239 | 71 |
| 74 | 35093487 | 2645 | 2671 | +26 | +27 | −1 | 483 | 0.81 | +127.8 | +16 of 310 | 68 |
| 75 | 13302507 | 2642 | 2658 | +16 | +16 | +0 | 313 | 0.71 | +97.7 | +0 of 262 | 77 |
| 76 | 44507356 | 2642 | 2656 | +14 | +14 | +0 | 421 | 0.61 | +78.5 | +15 of 279 | 81 |
| 77 | 2805677 | 2641 | 2657 | +16 | +17 | −1 | 150 | 0.72 | +52.9 | −2 of 92 | 78 |
| 78 | 4135539 | 2640 | 2664 | +24 | +22 | +2 | 315 | 0.86 | +151.8 | +12 of 234 | 73 |
| 79 | 4262875 | 2639 | 2656 | +17 | +19 | −2 | 446 | 0.70 | +82.4 | −1 of 271 | 79 |
| 80 | 14101025 | 2639 | 2644 | +5 | +5 | +0 | 13 | 1.00 | +183.8 | +0 of 0 | 99 |
| 81 | 13306677 | 2638 | 2656 | +18 | +18 | +0 | 423 | 0.69 | +95.2 | +2 of 274 | 80 |
| 82 | 24125890 | 2638 | 2659 | +21 | +21 | +0 | 251 | 0.75 | +109.4 | +2 of 94 | 76 |
| 83 | 4162722 | 2637 | 2651 | +14 | +16 | −2 | 85 | 0.89 | +114.2 | +6 of 50 | 89 |
| 84 | 8603332 | 2637 | 2659 | +22 | +22 | +0 | 197 | 0.84 | +118.0 | +6 of 90 | 75 |
| 85 | 13515110 | 2636 | 2647 | +11 | +10 | +1 | 321 | 0.66 | +101.0 | −2 of 66 | 97 |
| 86 | 30920019 | 2636 | 2655 | +19 | +20 | −1 | 546 | 0.55 | +44.9 | +14 of 304 | 83 |
| 87 | 1512668 | 2633 | 2632 | −1 | −1 | +0 | 509 | 0.96 | +415.1 | −5 of 139 | 100 |
| 88 | 4107012 | 2633 | 2647 | +14 | +13 | +1 | 460 | 0.80 | +180.5 | +0 of 78 | 96 |
| 89 | 13401653 | 2632 | 2650 | +18 | +20 | −2 | 288 | 0.79 | +79.5 | +5 of 215 | 91 |
| 90 | 14103320 | 2632 | 2653 | +21 | +21 | +0 | 222 | 0.77 | +90.4 | −9 of 157 | 86 |
| 91 | 2905540 | 2631 | 2651 | +20 | +20 | +0 | 387 | 0.80 | +103.4 | −1 of 233 | 88 |
| 92 | 409561 | 2630 | 2649 | +19 | +19 | +0 | 267 | 0.82 | +161.6 | +0 of 92 | 94 |
| 93 | 35028561 | 2629 | 2650 | +21 | +23 | −2 | 905 | 0.79 | +132.5 | +17 of 469 | 93 |
| 94 | 4126025 | 2628 | 2654 | +26 | +27 | −1 | 176 | 0.90 | +102.6 | +1 of 65 | 84 |
| 95 | 8608288 | 2628 | 2652 | +24 | +22 | +2 | 378 | 0.77 | +131.1 | −3 of 211 | 87 |
| 96 | 14100010 | 2628 | 2653 | +25 | +23 | +2 | 455 | 0.75 | +111.8 | +2 of 330 | 85 |
| 97 | 1000268 | 2627 | 2646 | +19 | +21 | −2 | 244 | 0.84 | +170.3 | +13 of 125 | 98 |
| 98 | 1444948 | 2627 | 2650 | +23 | +22 | +1 | 507 | 0.71 | +87.6 | +7 of 385 | 90 |
| 99 | 30901561 | 2627 | 2650 | +23 | +23 | +0 | 678 | 0.83 | +162.0 | +10 of 254 | 92 |
| 100 | 2293307 | 2626 | 2648 | +22 | +22 | +0 | 589 | 0.77 | +120.9 | +10 of 458 | 95 |

*Under this rule, with the same results — not anyone's true strength.* Generated by `analysis/e17_summary_report.py --appendix` from E17's aggregate; the table is E17 §3. Mean gap: the player's rating minus the opponent's, both from the list the tournament used; share as favourite: the games against a lower-rated opponent; colour balance: Whites minus Blacks among the games whose colour a broadcast gives. The counts above 2700 and 2800 on every list, each year's split into the table's and colour's effects, the validation and the method are in E17; a one-page summary is `docs/evidence/E17_summary.md`.

---

## Appendix H Self-calibrating: one table a year, and today's top 100 under it

*Under this rule, with the same results — not anyone's true strength.*

Rung 2 as recommended is self-calibrating (R65): each year's table is refitted by SPEC-TABLE-FIT v1.2's rules on the games played before that year only, within annex T7.1's yearly caps, by a method fixed before any table was fitted (`docs/specs/SPEC-SELFCAL_v1_2.md`). Run back in time on the broadcast archive, the data allow two tables: 2016–2019 could not be sourced legitimately, and the archive's games before 2023 carry no FIDE IDs, so the first window is 2024-03 to 2024-12, after the March 2024 compression [E18 §1]. The 2025 table keeps v1.1's form; for 2026 the rule of choice picked a piecewise-linear slope by level and a colour term rising with the level, and the yearly caps held six of its parameters at their bounds [E18 §2].

Forecasting each year's games, the year's table beat table 8.1.2 as FIDE applied it in every year (log-loss −0.0516 in 2025, −0.0477 in 2026, nats a game, intervals below zero), and in 2026 it beat the first table kept frozen (−0.00038; −0.00050 to −0.00030): self-calibration earns its name in 2026, the one year that can tell. The size is small: 0.0004 nats a game, against 0.048 over table 8.1.2, and 0.0001 in the form ruling R68 keeps (a choice of form needs 24 months of games after the last rule change; R68 applies from 2027, and the 10-month figure that allowed the 2026 choice was set after the counts were known); and with one year, against a frozen table fitted on 10 months to the year's 22, the result is consistent with self-calibration and cannot establish it [E18 §3]. Table 8.1.2 expects a 100-point favourite at 2700 to score 0.640; the tables, 0.589 and 0.590; White's edge at 2700–2799 is 35 and 43 rating points (48 without the caps), against none in table 8.1.2 [E18 §4].

Today's top 100 replayed with these tables, FIDE's rules before 2025, and K by FIDE's rules on each system's own rating (R61, which changes no K here): in October 2026 the self-calibrating system rates them +14.5 points higher on average than FIDE's rules (−1 to +29); +10.1 to +18.7 with the opponents outside the 100 rated 10 points lower or higher from 2025 (R58); +11.9 with each table's own residual at levels of 2300 or more removed by level band, and +11.2 by band and gap (R59's two estimates, neither a bound, R71); +14.6 with the 2026 table in the form R68 keeps; 38 and 5 of the 100 at 2700 and 2800, against 33 and 1 [E19]. E17's frozen table gave +23.3 over 2020–2026 (Appendix G); E19 supersedes it (R59).

The five largest differences and the five smallest, with every player tied at the cut, names beside FIDE IDs (R60):

*Under this rule, with the same results — not anyone's true strength.*

| | name | FIDE ID | FIDE's rules, October 2026 | self-calibrating | difference |
|---|---|---|---|---|---|
| largest | Erigaisi Arjun | 35009192 | 2746 | 2775 | +29 |
| largest | Mamedyarov, Shakhriyar | 13401319 | 2710 | 2738 | +28 |
| largest | Caruana, Fabiano | 2020009 | 2784 | 2811 | +27 |
| largest | Tabatabaei, M. Amin | 12521213 | 2728 | 2755 | +27 |
| largest | Abdusattorov, Nodirbek | 14204118 | 2780 | 2807 | +27 |
| largest | Sarana, Alexey | 24133795 | 2671 | 2698 | +27 |
| smallest | Dominguez Perez, Leinier | 3503240 | 2732 | 2731 | −1 |
| smallest | Topalov, Veselin | 2900084 | 2695 | 2695 | +0 |
| smallest | Anand, Viswanathan | 5000017 | 2739 | 2739 | +0 |
| smallest | Howell, David W L | 410608 | 2665 | 2666 | +1 |
| smallest | Christiansen, Johan-Sebastian | 1512668 | 2633 | 2634 | +1 |

Read with these caveats [E18 §5] [E19 §8]:

- Two tables only, so the test of self-calibration rests on 2026; the replay differs from FIDE's rules over 22 lists, not E17's 81.
- Opponents outside the 100 keep their published ratings (R58's range above); a replay of the whole pool needs FIDE's tournament reports (section 9, stage 2).
- The tables' own error at the top is estimated, not removed (R59's two estimates above, R71).
- A flatter table spreads ratings further apart at the top (annex T3.5): counts above 2700 and 2800 compare two scales as well as two rules.
- The tables are fitted on broadcast games, stronger and more international than the rated pool.
- Layer 0 reads the 400-point rule of March 2024 to September 2025 as the plain cap, NOT VERIFIED against the handbook; FIDE's calculations agree in every tournament that can tell [E17 §2].
- The figures describe the rule, not the players: who is stronger is not their question.

*Under this rule, with the same results — not anyone's true strength.*

---

## Appendix I The greats, on FIDE's own data

Outside the body's word count. From E20 (`docs/evidence/E20_greats.md`), under SPEC-GREATS v1.0, fixed before any analysis, the rulings R74 to R79 and the session's review. Every table here, as in E20, reads:

*Under this rule, with the same results — not anyone's true strength. A rating measures strength against one's own era.*

**The data, and their limits.** The study uses FIDE's own data, for analysis only and not redistributed (FIDE reserves all rights, and its written permission has not been sought), and OlimpBase's transcription of FIDE's lists under its terms (`docs/research/DATA-PROBE_greats.md`): FIDE's lists (as OlimpBase transcribes them to 2000, FIDE's own files since 2001), FIDE's printed top lists of 2000–2019 as the Internet Archive keeps them, and FIDE's per-player rating calculations, which give every game only from the list of April 2008. **TWIC and Chessmetrics were not used**, nor ChessBase or any other game collection whose terms need permission. So the greats' lists and their lead over their own era can be shown from 1971, but their games can be replayed only from 2008, and no comparison across eras is possible.

**Who.** The 36 players ranked 1st to 3rd on any FIDE list from July 1971 to December 2019 [E20 §2], from Fischer, Korchnoi and Spassky on the first list (July 1971) to Ding, the last to join (February 2019); six of them only through a share of 3rd place on lists before 1999 whose ratings are multiples of five.

**Their lead over their own era** [E20 §3]: the best three consecutive years by the mean gap to the list's #2, the six largest, each the best of the player's qualifying windows.

*Under this rule, with the same results — not anyone's true strength. A rating measures strength against one's own era.*

| name | best three years | lists | mean gap to #2 | mean gap to #10 | windows |
|---|---|---|---|---|---|
| Fischer, Robert J | July 1972 – January 1975 | 4 | +100.0 | +160.0 | 2 |
| Kasparov, Garry | July 1990 – January 1993 | 6 | +64.2 | +145.0 | 45 |
| Carlsen, Magnus | December 2012 – November 2015 | 36 | +53.7 | +101.2 | 87 |
| Karpov, Anatoly | January 1976 – January 1978 | 3 | +43.3 | +85.0 | 63 |
| Anand, Viswanathan | April 2006 – January 2009 | 12 | +6.0 | +54.5 | 142 |
| Topalov, Veselin | October 2006 – September 2009 | 13 | +4.4 | +47.9 | 134 |

Lists to 2000: OlimpBase's transcription of FIDE's lists, by Wojciech Bartelski (https://www.olimpbase.org/Elo/summary.html), used under its terms: free of charge, citing the source, non-commercial use only (DATA-PROBE §3); only figures derived from it are kept here (R77).

A lead over one's contemporaries, on lists whose frequency and spread change with the era, and a maximum over a different number of windows for each player: not a ranking across eras.

**The replay, 2008–2019** [E20 §4–§5]. Of the 36, 29 have rated games in the window. Given FIDE's own inputs, Layer 0 with the rules in force at each date reproduces FIDE's printed change in 18,490 of 18,490 games; 9 player-periods are thin and carry FIDE's change. In the greats' games FIDE applied the 350-point rule to tournaments starting up to 28 June 2009 and the 400-point rule from 9 July 2009. FIDE's lists rounded a period's half point towards +∞ up to the list of July 2018 (73 of 78 half points before July 2014, every one of the 27 negative ones from July 2014), except on the list of January 2009 (3 of 3 away from zero), and away from zero from the list of November 2018 (every one of the 12 negative ones); Layer 0 rounds as FIDE's lists do, towards +∞ to October 2018 and away from zero from November 2018 (R74 and R80, readings set after FIDE's pages had been seen; the list of the change NOT VERIFIED), and the list of January 2009 keeps its periods thin. Under the 2025 table, **applied backwards, not fitted on that era**, with every opponent outside the 29 held at FIDE's rating (R58), the greats end the window 27.1 points above FIDE's ratings on average (from −9 to +62; +17.9 to +36.6 with those opponents 10 points lower or higher; a replay of the whole pool, in which they would move too, needs FIDE's tournament reports). On these games table 8.1.2 fits the favourites better (mean residual −0.009 against +0.035 for the 2025 table): the difference measures how far the 2025 table sits from 8.1.2 at these players' gaps, and the highest ratings below rest most on levels where the table was fitted on fewest games:

*Under this rule, with the same results — not anyone's true strength. A rating measures strength against one's own era.*

| name | games | highest under FIDE's rules, 2008–2019 | highest under the 2025 table | difference, last list |
|---|---|---|---|---|
| Carlsen, Magnus | 785 | 2882 (May 2014) | 2945 (August 2019) | +62 |
| Caruana, Fabiano | 1,224 | 2844 (October 2014) | 2882 (December 2018) | +55 |
| Aronian, Levon | 899 | 2830 (March 2014) | 2875 (March 2014) | +34 |
| So, Wesley | 1,019 | 2822 (February 2017) | 2857 (February 2017) | +37 |
| Mamedyarov, Shakhriyar | 854 | 2820 (September 2018) | 2858 (September 2018) | +37 |
| Vachier-Lagrave, Maxime | 1,145 | 2819 (August 2016) | 2848 (August 2016) | +35 |
| Anand, Viswanathan | 599 | 2817 (March 2011) | 2847 (July 2015) | +32 |
| Kramnik, Vladimir | 566 | 2817 (October 2016) | 2855 (October 2016) | +41 |
| Ding, Liren | 882 | 2816 (November 2018) | 2854 (September 2019) | +41 |
| Nakamura, Hikaru | 972 | 2816 (October 2015) | 2851 (October 2015) | +33 |

**What permission would add.** With written permission from TWIC, ChessBase or Chessmetrics, the full study becomes possible: the replay could extend to the games those collections hold, across the greats' careers. FIDE's own calculations, against which a replay is checked, exist only from 2008; those collections do not record which games FIDE rated; and any comparison across eras would rest on a model's assumptions. Permission has not been sought.

---

*End of DRAFT v1.0. Status line repeated: DRAFT v1.0 — not for publication.*
