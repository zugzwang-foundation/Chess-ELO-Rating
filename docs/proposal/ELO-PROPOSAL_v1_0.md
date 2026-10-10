# Modernising the FIDE Elo Rating System: an exact reference implementation plus an explainable correction layer

**Status: DRAFT v1.0 — not for publication**
Author: The Zugzwang Authors · Licence: CC BY 4.0 (`docs/LICENSE-docs.md`) · Date: 2026-10-10
Audience: FIDE's Qualification Commission (QC) and the chess public. Plain language first; the mathematics is in the technical annex.
Companion documents: the technical annex `docs/proposal/ELO-TECHNICAL-ANNEX_v1_0.md` (sections T1–T11), which holds every formula, proof sketch and worked example and is cross-referenced as [T n]; and a 900-word plain-language brief, `docs/proposal/ELO-BRIEF_v1_0.md`. Version 1.0 applies the architect's rulings R15–R23 (`docs/decisions/D-0009_architect-rulings-elo-5.md`) on top of R1–R14 (`docs/decisions/D-0008_architect-rulings-elo-4.md`) and decisions D1–D18 (`docs/decisions/D-0005_architect-decisions-v0.3.md`), and folds in the evidence of session ELO-5: K from FIDE's activity record [E8], the simulator [E9] and the farming guard [E10], with rung 6 rescored under R15 in [E6].

How to read the citations. `[R §x]` points to a section of the research report `docs/research/ELO-RESEARCH_v1_0.md`; `[R n]` to the report's numbered source n; `[V k]` to item k of the primary-source sweep `docs/research/VERIFICATION_2026-10-09.md`; `[VT k]` to item k of the titles sweep `docs/research/VERIFICATION_TITLES.md`; `[VP k]` to item k of the prior-work sweep `docs/research/VERIFICATION_PRIOR-WORK.md`; `[T n]` to section n of the technical annex; `[E n]` to evidence report n under `docs/evidence/`, each the output of a committed script (E0 Layer 0 against FIDE, E1 FIDE's monthly lists, E2 the broadcast calibration, E3 the 2026 U.S. Championships, E4 the community register, E5 deflation, E6 the rungs on history, E7 federation residuals, E8 K from the activity record, E9 the simulator, E10 the farming guard). Calculated numbers not cited to an evidence report come from `analysis/v10_calculations.py` (output `analysis/OUTPUT_v1_0.md`, cited as "script §n"). Every FIDE rule quoted here is transcribed from [V 1] (standard) or [V 2] (rapid and blitz). Every parameter value is PROVISIONAL, a placeholder to be replaced by an estimate from data, except the expected-score table's, which are PROVISIONAL-FITTED on broadcast games [E2]. The broadcast games behind E2, E6, E7, E8 and E10 are stronger and more international than the rated pool; their results hold for that population until FIDE's game archive tests them. The simulator's pool is synthetic [E9].

---

## 1 Summary

**What the evidence shows.** Table 8.1.2, which turns a rating gap into an expected score, expects too much of favourites: by 0.02 to 0.05 a game at gaps of 50 to 449 points on 352,737 broadcast standard games, and by up to 0.096 in rapid [E2] [E5]. The higher-rated player is usually the favourite, so the error moves points down the list. At 2400 and above, where every K is 10, it implies a loss of 0.14 to 0.17 points a game, at least what FIDE's lists show these players losing, and the active players rated 2600 or more fell from 242 in October 2019 to 150 in October 2026 [E5]. Juniors improve faster than their ratings: adults score 0.055 a game below today's expectation against eligible juniors, 0.047 more than against adults at the same gaps [E6]. Federations are priced differently: Ghita's cross-border directions hold on our broadcast sample for 21 of the 22 federations he names, and for all 22 in the years his data cannot contain [E7]. The level of steadily active adults, by contrast, has not fallen since the March 2024 reform in standard and rapid [E5].

**The proposal.** Publish an exact, open-source reference implementation of FIDE's current rules, so anyone can reproduce every list. Run behind it a statistical model, re-estimated monthly, that learns what Elo assumes away: junior improvement, White's edge, draws, federation drift. Keep the published rating a forward-only Elo number on today's scale, changed per game by a hand-checkable formula, and offer the improvements as seven rungs FIDE can adopt one at a time.

**The verdicts** (section 8). RECOMMENDED NOW: rung 1, the open replica, and rung 2, a refitted table with colour and draws, guarded where farming pays. PILOT: rung 5, junior compensation, Chess Scotland's junior additions made evidence-based. TEST ON FIDE DATA: rungs 3, 4, 6 and 7.

**The ask** (section 9). FIDE's tournament-report (TRF) archive, under a data agreement, to test rungs 3 to 7 on every rated game; a QC review with public comment; a twelve-month shadow list before any pilot. A comparison on the 2026 U.S. Championships was fixed in advance and runs blind (section 10). Nothing here edits a published rating, amends the title regulations or is a black box.

---

## 2 What the data show

### 2(a) The table drains the top

On broadcast standard games between players rated on FIDE's list in force, the favourite scores below table 8.1.2's expectation in every 50-point gap bin from 50 to 449 points, by 0.022 at 50–99 rising to 0.054 at 350–399; in rapid the shortfall reaches 0.096 and in blitz 0.073 [E2] [E5]. A refitted table with colour and draws passes the calibration rules on held-out months where table 8.1.2 fails [E2].

Whoever is the favourite pays the error, and the favourite is usually the higher-rated player, so points move down the list, from 2200 and above to below 2000. At 2400 and above, where everyone's K is 10, the over-prediction alone implies a loss of 0.14 points a game for players rated 2400–2599 and 0.17 for 2600 and above; FIDE's lists show them losing 0.09 and 0.13 a game in 2025–26, about 4 and 7 points a year [E5]. The top has shrunk (standard; active means a rated game in the twelve months up to the list) [E5]:

| list | October 2015 | October 2019 | October 2023 | October 2026 |
|---|---|---|---|---|
| active players rated 2600 or more | 225 | 242 | 195 | 150 |
| rating of the 100th active player | 2654 | 2654 | 2642 | 2626 |
| mean of the active top 100 | 2702.7 | 2700.8 | 2693.6 | 2680.5 |

This is a transfer, not a fall of the whole scale. Since the March 2024 reform the published ratings of steadily active adults have risen 2 to 3 points a year in standard and 4 to 5 in rapid (blitz −1 to −2); the active list's median still falls, 11 to 16 points a year, because entrants arrive below the players who stop, which is what the often-quoted −16 a year measures [E5] [R 5]. A simulated pool with known true strengths reproduces the slide without being tuned to it: under today's rules, adults whose true strength is 2400 or more lose 6.1 points a year on the list while their strength falls 1.5 [E9].

### 2(b) Juniors drain the adults who meet them

Juniors improve faster than K = 40 lets their ratings follow: Layer 1's fitted drift is +193 points a year under 12 and +79 at 16–19 (`analysis/OUTPUT_L1_history.md`). The adult who meets an under-rated junior pays: on broadcast games adults score 0.055 a game below today's expectation against eligible juniors (56,030 games), 0.047 more than against adults at the same gaps [E6]. Ghita calls it a deflation tax: an adult rated 1900 who draws a junior listed at 1500 loses 8.4 points before rounding, however strong the junior is ([R 5], pp. 13, 18). In the simulated pool adults rated 2400 or more score 0.050 a game below expectation against juniors [E9].

The fix is not ours. By IM Douglas Bryson's account in FIDE's 2023 consultation, Chess Scotland has since 1976 added an age-dependent number of points to a junior's grade when computing the opponent's expected score, and Sonas named it a possible next step for FIDE [VP 4] [VP 5]. Rung 5 is that mechanism made evidence-based: the addition c_j is the part of the gap the model is 90 % sure of, less a margin τ = 25, from the junior's own games in that time control; it enters only the opponent's expectation, never the junior's own update (section 5). On broadcast games it cuts the adults' shortfall from 0.055 to 0.018 a game and improves forecasts; against a matched control the junior-specific shortfall falls from 0.047 to 0.010 [E6]. By band it gives too little below 2000 and too much against adults rated 2400 or more, whose junior opponents are the strongest juniors; τ stays constant and the result stands as measured (R18). Hence PILOT: try it where the junior data are complete.

### 2(c) Federations are priced differently

Vlad Ghita's book diagnosed it: in cross-border games players of some federations, mostly Asian, score well above their Elo expectation and players of several European federations below it, measured by a weighted, recursive cross-border index on FIDE's 2025 game extract ([R 5], pp. 23–26, 53, 66–67). We replicated his method on broadcast games: the federation offsets point his way for 17 of the 18 named federations with enough games in 2025 and 21 of 22 over 2023–2026; on 2023, 2024 and 2026, years his extract cannot contain, 22 of 22 agree [E7]. Sizes are not compared: the sample over-represents strong players. In the simulator, a federation that plays 1 % of its games abroad and is 64 points under-rated at adoption is still 47 under-rated ten years later under today's rules, and rung 7 cannot reach it: its evidence, the cross-border games, is too thin [E9]. Whether offsets measure the pool or who travels needs FIDE's game record (section 9).

**Dropped or out of scope.** The lists show no pile-up at the 1400 floor: fewer players sit at 1400 than at each of the next nine points [E1]. The 2024 compression itself, online ratings and titles, raised often in the community, are not addressed [E4].

---

## 3 Design principles

Constant across styles: one core skill per player; a forward-only published number on today's scale that moves only when the player plays; every change explainable by hand; deterministic open-source code; parameters re-estimated within published annual caps; a monthly ledger of every point [T5] [T6]. Per time control: an offset from the core skill, an expected-score function with its own colour and draw terms, and a volatility [T2] [T3]. The research report's eight adoptability requirements [R §7]:

| # | Requirement | Met by |
|---|---|---|
| 1 | Determinism and reproducibility | Exact decimal arithmetic with one rounding step, today's rounding (§8.3.4 [V 1]), versioned parameters, identical output from identical TRF input [T4] |
| 2 | Transparency | A yearly lookup table and a monthly parameter file, both public and versioned [T7] |
| 3 | Auditability | A per-game breakdown published with every change, and a monthly points ledger [T4] [T6] |
| 4 | Explainability | Model influence enters only through the named rungs of section 8, each a labelled line on the breakdown |
| 5 | Open-source code with test vectors | Apache-2.0 code, CC BY 4.0 documents, test vectors from FIDE's published calculations [E0] |
| 6 | Governance | The QC signs the parameter file; Council approves changes to caps or formula; public comment before changes (section 13) |
| 7 | Fairness and bias monitoring | Residuals by age, sex, rating band and colour reported monthly; by federation to the QC only while rung 7 is disabled [T8] |
| 8 | Manipulation resistance | No cliffs; a guard where farming pays; K from certainty; continuous compensation; adjustments paid per active player, never per game; anomaly monitoring; adversaries simulated [E9] [T9] |

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
   │        2 fitted table, colour, draws, guard   3 newcomer seeds               │
   │        4 K from certainty                      5 junior compensation         │
   │        6 monthly adjustment                    7 federation adjustment (OFF) │
   │      and the points ledger                                                   │
   └──────────────────────────────────────────────────────────────────────────────┘
```

**Layer 0, the reference engine**, is rung 1: an exact implementation of the FIDE Rating Regulations as amended 1 October 2025 [V 1] and of the Rapid and Blitz Rating Regulations [V 2] (`docs/specs/SPEC-L0_fide-reference-engine_v1_1.md`), verified against FIDE's published calculations [E0] (section 8); FIDE's online calculator is out of date (Appendix F).

**Layer 1, the model** [T2], gives each player a shared skill that moves with an age-dependent drift and a shrunken offset per time control; outcomes follow the published table's form, with colour and draws. It is refitted monthly on 36 months of games by the method of Whole-History Rating [VP 11], with priors that depend on age only, never on federation, and a scale anchored to steadily active adults, as US Chess monitors its level [VP 12] (`docs/specs/SPEC-L1_v1_0.md`). Fitted on 776,825 broadcast games, it gives a usable estimate for 95 % of active players rated 2600 or more but 0.7 % of those below 1600 (`analysis/OUTPUT_L1_history.md`): broadcast games cover the top, not the pool. Its estimates of named players are for the QC only. **It never edits a published rating.**

**Layer 2, the published rating** [T4], is forward-only and Elo-style, on today's scale. Model influence enters only through named, published, capped channels, the rungs of section 8. After each closing date (§7.1.3 [V 1]) Layer 0 produces the official list as today and Layer 2 a shadow list; Layer 1 writes the coming month's parameter file within its caps, and the QC signs it.

---

## 5 The published rating in practice

**The update.** For each game a player's rating changes by

> R_i ← R_i + K_i · (S_i − E(x_i))

where S_i is the score (1, ½, 0), E(x_i) the expected score read from the published table for the time control and level band, and K_i the player's K for the period. The game terms are summed over the rating period, with any adjustment balance, and rounded once, as today (§8.3.4 [V 1]) [T4].

**The gap and the table.** x_i is the published rating difference plus the colour term η_tc for White and minus it for Black (36 points in standard, 37 in rapid, 27 in blitz, fitted [E2]), so an extra White no longer pays. Against an eligible junior the opponent's rating for expectation is RX_j = R_j + c_j (rung 5). The table has one block per time control and 100-point level band and a three-decimal value for every gap from 0 to 1500; draws rise with level and fade with the gap, and there is no cap, clamp or exemption [T3]. The table is fitted on published ratings, so that where it is calibrated no choice of opponent or colour gains in expectation (property P4) [T5].

**The farming guard (R17).** Pooled on broadcast games, the fitted table under-predicts favourites at gaps of 400 or more above level 2300 in standard (+0.032) and blitz (+0.045), so a strong player farming much weaker fields would gain [E6]. Until FIDE's games calibrate that region, a temporary guard applies in all three time controls: when the gap is 400 or more and the favourite is rated 2300 or more, the favourite's expectation is the larger of the fitted value and table 8.1.2 read without its 400-point cap, and the underdog's is one minus it. On broadcast games the guard binds in every game of the region and turns the farming gain into a loss (standard −0.021, blitz −0.030); rung 2 with the guard still forecasts better than table 8.1.2 and passes the do-no-harm check in all three time controls, but its full calibration gate only in standard [E10]. A 2600 then expects 0.96 against a 2100, as today's rule gives a player rated 2650 or more at that gap, so today's cliff at 2650 disappears (script §8) [T3].

**K falls with the games of a period (R16).** With rung 4,

> K_i(n) = clip(q · σ_i² / (κ_tc · (1 + n · q² · σ_i² · v_tc)), 10, 40), q = ln 10 / 400

where σ_i is the model's uncertainty about the player, v_tc the score variance of an even game in the player's band and n the player's rated games in the period. Equivalently K_i(n) = C / (N_i + n): C is a constant of the published table (853 at level 1700, 1164 at 2300) and N_i, printed in the list, is the model's certainty about the player counted in games (script §5b) [T4]. A newcomer has 40; a player back after years away gets more; there is no switch at 30 games, 2300, 2400 or age 18. The rule replaces K × n ≤ 700 with a smooth equivalent: a newcomer with 30 games in one period at level 1700 receives K 25.9, a range of 777 points against today's 23 and 690. Built from FIDE's own monthly activity record, it gives established players rated 2600 or more a median K of 13.3 and club adults rated 1600–1999 about 30 for a one-game month and 24 for nine games, against today's 10 and 20; it no longer harms forecasts, but does not yet improve them measurably [E8].

**The monthly adjustment.** Each month the model compares the anchor cohort's published mean with its own estimate; beyond a 2-point deadband a sixth of the gap, capped at 1.5 points a month (PROVISIONAL), is credited to active players in proportion to their games up to the cohort's average, positive in a deflating pool and negative in an inflating one, and posted when they next play [T4]. It is judged on that gap, within ±2 points a year; the cohort's own published drift is reported, never scored, because real improvement is not drift (R15).

**The spread.** The table carries the spread; nothing is rescaled. Because a yearly refit could ratchet it, κ's annual cap stays, and the ratio of the published spread to the model's for active adults is published monthly (standard: 0.794 in January 2023, 0.747 in September 2026; `analysis/OUTPUT_L1_history.md`). When its twelve-month mean has moved more than 0.025 (PROVISIONAL) since the last review, the QC reviews (R19); calibrated in the simulator, that threshold gives at most 5 % false alarms and catches a ratchet at κ's cap after a median of 57 months [E9] [T3].

**The ledger.** Unequal K factors, compensation, newcomers, the floor and departures create or destroy points. Each month a ledger states where the points went, as a central bank publishes how much money it created and why; the identity is exact [T6].

**Worked example** [T10]. An adult, A, rated 1900, has White against a junior, J, listed at 1500 whom the model estimates at 1850 with a standard deviation of 100. J's compensation is 1850 − 1.2816 × 100 − 1500 − 25 = 196.84, so 197: J counts as 1697 in A's expectation, while J's own update uses 1500. A's K is 14.1 and J's 40.0 (PROVISIONAL, one game each). Today table 8.1.2 gives A .92 with K = 20 [V 1], and a draw costs A 8.4 points, Ghita's example ([R 5], pp. 13, 18).

| Result | A today: 20 × (S − .92) | J today: 40 × (S − .08) | A, all rungs: 14.1 × (S − 0.780) | J, all rungs: 40.0 × (S − 0.081) |
|---|---|---|---|---|
| A wins | +1.6 → **+2** | −3.2 → **−3** | +3.1020 → **+3** | −3.2400 → **−3** |
| Draw | −8.4 → **−8** | +16.8 → **+17** | −3.9480 → **−4** | +16.7600 → **+17** |
| J wins | −18.4 → **−18** | +36.8 → **+37** | −10.9980 → **−11** | +36.7600 → **+37** |

The adult loses 4 instead of 8 for drawing a junior who is really an 1850 player and 11 instead of 18 for losing; the junior's changes are today's. The ledger prints the 1.9599 points the compensation creates [T6].

---

## 6 Where points enter and leave

Today's rules are transcribed from [V 1] and [V 2].

| Topic | Today | Proposed | Why |
|---|---|---|---|
| **Newcomers** (rung 3) | Published after at least 5 games against rated opponents, pooled over up to 26 months; Ra = average of rated opponents plus two hypothetical 1800-rated opponents scored as draws; Ru = Ra + dp from table 8.1.1, rounded, maximum 2200 (§7.1.4, §8.2) | Same threshold. The seed is the model's estimate on the published scale from the player's games in all three time controls and an age-only prior, at most 2200, published only if at least 1400, the model's uncertainty is at most 120 points and at least half of the estimate's precision comes from that time control (R20); the five games must involve 3 opponents in 2 events; no hypothetical opponents [T4] | Sonas called the initial-rating formula the main engine of deflation [VP 5]. On broadcast games seeds are closer to newcomers' results on average than FIDE's first ratings but noisier, and fail do-no-harm [E6]. In the simulator they are the most accurate single rung, but remove the points today's newcomers inject, so the level falls 44 points in ten years unless rung 6 runs beside them [E9] |
| **Juniors** (rung 5) | K = 40 until the end of the year of the 18th birthday while rated under 2300 (§8.3.3) | A junior (list year minus year of birth at most 19) with at least 10 rated games in the time control against 5 opponents in 3 events, half of whose estimate's precision comes from that time control (R5), carries c_j = the 90 % lower estimate on the published scale, minus the published rating, minus τ = 25, between 0 and 300 (PROVISIONAL). It enters only the expectation of opponents who are not themselves eligible (R8) and fades as the junior's rating catches up; the list flags every eligible junior (R20) [T4] | Section 2(b). τ stays constant (R18) |
| **Floor** | Below 1400 shown as unrated on the next list, then treated as unrated (§7.2.1) | Unchanged as a display rule; the model keeps estimating the player, and re-entry under §7.1.4 is seeded from that estimate only if it is at least 1400 [T4] | Re-entry through the newcomer rule injects points at the bottom; the ledger books both directions [T6] |
| **Inactivity** (rung 4) | Inactive after a year without a rated game; active again after one game (§7.2.2); no decay | No decay; the model's uncertainty grows while the player is away, so K is higher on return; no adjustment accrues while inactive | About 40 % of listed players have not played since before the pandemic (Ghita's count [R 5]); uncertainty growth with time away is Glicko's remedy [VP 6] |
| **Monthly adjustments** (rungs 6, 7) | No rule | A global adjustment of either sign per time control, 2-point deadband, 1.5-point monthly cap (PROVISIONAL), accrued in proportion to activity up to the anchor cohort's average and posted in a month the player plays (R3); the federation adjustment the same, DISABLED [T4] [T7] | In the simulator it moves the level −2 points in ten years where today's rules move it +21, and −6 where a junior wave moves it −38 [E9]; US Chess holds its level with a bonus [VP 12]; Ghita proposed an activity-linked bonus first ([R 5], p. 55) |

---

## 7 Time controls and Chess960

One shared skill plus a shrunken offset per time control, so that a rapid specialist is not treated as a different person; each time control keeps its own table and volatility, because White's edge and draw rates differ by style [E2] [T2]. In Layer 2 a rapid game reaches the classical rating only through a newcomer's seed, and compensation uses the same time control's evidence (R5). Today's two chapters differ at the top: standard uses the full difference for players rated 2650 and above since 1 October 2025 [V 1]; rapid and blitz keep the plain 400-point cap and, since 1 December 2024, do not rate games 600 or more points apart involving a player above 2600 [V 2]. One table and one guard in all three remove the difference. FIDE's planned Chess960 rating would be one more offset, seeded from existing estimates [R 25] [T2]; FIDE's plan is NOT VERIFIED.

---

## 8 The adoption ladder

Seven rungs, lowest risk first, each adoptable alone: a rung not adopted leaves today's rule in place. The verdicts follow the evidence (R22): RECOMMENDED NOW for rungs that passed their pre-registered test against Layer 0, PILOT for the rung that fixes a measured problem but misses its rule by band, TEST ON FIDE DATA for rungs only FIDE's game record can judge [T8].

| Rung | What changes | Verdict | Evidence |
|---|---|---|---|
| 1 The open replica | Nothing in the rules: an open engine reproduces today's list | **RECOMMENDED NOW** | Every game and tournament sum of FIDE's published calculations and the 2025 U.S. Championship reproduced; the list change in 56 of 58 multi-event periods, two one point off unexplained [E0] |
| 2 The refitted table, with the farming guard | Table 8.1.2 replaced by a yearly table with colour, draws and level bands; R17's guard at gaps of 400 or more with a favourite rated 2300 or more; same K | **RECOMMENDED NOW** | Passes calibration rules (a) and (b) in all three time controls and improves forecasts [E2]; with the guard, do-no-harm in all three and the full gate in standard, while rapid misses rules (a) and (b) and blitz rule (b) [E10]; in the simulator the farmer's advantage falls from 0.245 to 0.050 points a game [E9] |
| 3 Newcomer seeds | First rating from the model, not two 1800 draws | **TEST ON FIDE DATA** | Broadcast games: closer on average (−0.010 against −0.020) but log-loss worse by 0.050 a game [E6]; simulator: error against true strength 98 points against 143, the level −44 without rung 6 [E9] |
| 4 K from certainty | K_i(n) from the model's certainty and the period's games (R16) | **TEST ON FIDE DATA** | From FIDE's activity record: do-no-harm met, targeted rule not (+0.00042 nats a game, interval −0.00125 to +0.00173) [E8]; simulator: error 140 against 143, and a farmer keeps more (+0.290 a game) [E9] |
| 5 Junior compensation | Opponents of under-rated juniors use RX_j (R5, R8) | **PILOT** | Adults' shortfall against eligible juniors 0.055 → 0.018 a game; too small below 2000, too large against adults rated 2400 or more (R18) [E6]; little effect in the simulator, whose model proxy is unsure of juniors [E9] |
| 6 Monthly adjustment | A capped adjustment of either sign, accrual scaled by activity | **TEST ON FIDE DATA** | Holds the simulated level (above); R15's ±2-a-year rule not met on broadcast months or in the simulator, where the model's own level moves [E6] [E9] |
| 7 Federation adjustment | The same per federation | **TEST ON FIDE DATA** (disabled) | Direction of Ghita's residuals confirmed [E7]; cannot reach an isolated federation in the simulator [E9]; the selection test needs FIDE's record |

Rung 2's verdict carries two conditions: the guard stays until FIDE's games calibrate the farming region, and rapid and blitz are re-tested on FIDE's games before adoption there. Rungs 2 to 6 together recover true strength best in the simulator (error 88 points against 143), on a model proxy that knows the pool's average dynamics, an optimistic assumption [E9].

---

## 9 The request to FIDE: the tournament-report archive

Everything not recommended now waits on one thing: the games. FIDE's monthly lists record ratings and game counts, not games; the broadcast archive records games, but of the strong, internationally active part of the pool (median rating 2113 against the pool's 1734 in standard) [E2]. The tournament reports arbiters submit for every rated event (TRF, §9.1 [V 1]) hold every rated game. **We ask FIDE for that archive, from February 2015 or as far back as it is kept, under a data agreement**: analysed on FIDE's terms, never redistributed, results published as aggregates only, as we already treat FIDE's lists. Each open question then becomes a test pre-registered before the data are opened [T8]:

| The archive settles | Broadcast games cannot, because |
|---|---|
| Rung 2 in the farming region, 1,000 games per 50-point bin, and so whether the guard can lapse; rung 2 in rapid and blitz for the pool | The region holds 827 standard games over 21 test months [E10] |
| Rung 3: seeds for every newcomer from all their rated games | Seeds rest on broadcast games alone (659 newcomers) [E6] |
| Rung 4: certainty from every rated game and opponent | The lists give game counts, not opponents [E8] |
| Rung 5 for juniors below 2000, where the drain is largest | 3.3 % of active juniors aged 18 or less have a usable estimate (`analysis/OUTPUT_L1_history.md`) |
| Rung 6 on the whole pool's anchor cohort | The broadcast panel's gap rests on broadcast estimates [E6] |
| Rung 7: offsets with each event's host federation, and the selection test (juniors against adults who travel, home against away events) | The archive records no host federation and over-represents strong players [E7] |
| Layer 1 for the 221,130 active rated standard players | Broadcast games give 13,089 a usable estimate (`analysis/OUTPUT_L1_history.md`) |

What FIDE receives: the open engine and its test vectors, every evidence report re-run on its data, and a monthly shadow list for the chosen rungs with its parameter file, ledger and monitoring report, at no cost and with no effect on any rating, title or norm (section 14). The computation is laptop-scale [T2]. Precedent: FIDE ran a parallel list during the 2008–2011 K-factor trial [R §2] [R 16].

---

## 10 The 2026 U.S. Championships, run blind

The 2026 U.S. Championship and U.S. Women's Championship (Saint Louis, 7 to 23 October 2026; two round robins of 12 players, 66 games each) are rated on FIDE's November list [E3]. The comparison was fixed before any result was read. Freeze 1, on 9 October, the day of the first round, hashed the comparison tool, the engine and the fitted table, and the repository's automated check fails if any of them changes [E3]. Freeze 2 (R23), also made before any result was read, hashed every other file that produces a number in the comparison or this proposal, recorded in decision record D-0010 and tagged freeze-2. No game of either event has been read; the comparison runs once, on all games, after the last round.

**The method, fixed in advance.** For each player: (a) the event's rating change under FIDE's rules, computed by Layer 0; (b) the change under rung 2 with its guard and the same K; and (b) − (a). The guard binds in no pairing of either field (largest gaps 165 and 250), so column (b) is Freeze 1's [E3]. Separately, labelled PILOT: rung 5 for the games against eligible juniors, with compensations from a Layer 1 fit on games to September 2026, frozen before the event's results are read. Rungs 3, 4, 6 and 7 are not shown. After the November list, column (a) must equal FIDE's official changes once each player's other October games are added; a mismatch is a finding about Layer 0 or FIDE's data, never a reason to edit it. With 132 games, the event illustrates the rungs; it cannot test them.

**Results, computed after the event** (blanks until then):

| | U.S. Championship | U.S. Women's Championship |
|---|---|---|
| games rated | {{US26_OPEN_GAMES}} | {{US26_WOMEN_GAMES}} |
| mean absolute (b) − (a) per player, points | {{US26_OPEN_MEAN_ABS_DIFF}} | {{US26_WOMEN_MEAN_ABS_DIFF}} |
| largest (b) − (a), points | {{US26_OPEN_MAX_DIFF}} | {{US26_WOMEN_MAX_DIFF}} |
| players whose rounded change differs under (b) | {{US26_OPEN_N_DIFFER}} of 12 | {{US26_WOMEN_N_DIFFER}} of 12 |
| column (a) equal to FIDE's 1 November 2026 changes | {{US26_OPEN_L0_MATCH}} of 12 | {{US26_WOMEN_L0_MATCH}} of 12 |
| PILOT, rung 5: games with a compensated junior | {{US26_OPEN_R5_GAMES}} | {{US26_WOMEN_R5_GAMES}} |
| PILOT, rung 5: the juniors' opponents' total change, minus column (b), points | {{US26_OPEN_R5_DIFF}} | {{US26_WOMEN_R5_DIFF}} |

{{US26_READING}}

---

## 11 Proof plan

**One baseline**: Layer 0, today's rules exactly; other systems are prior art (section 12). **Protocol**: rolling origin, fitting on months up to t, forecasting month t + 1 and rolling forward; the match schedule is never a feature [R 9] [VP 10]. Each rung is scored on its targeted metric and on a do-no-harm check, against thresholds fixed in [T8] before the data were seen. **Data**: FIDE's monthly lists since February 2015 [V 3], analysed and never redistributed; the Lichess broadcast archive, CC BY-SA 4.0 [V 4], with its bias stated; online games are not evidence. **The simulator** (`docs/specs/SPEC-SIM_v1_0.md`) adds what no backtest can: known true strengths, ten simulated years a run, every rung on the same games as Layer 0, and the adversaries, farming, sandbagging, collusion and inactivity [E9]. Its pool is calibrated on our measurements where they exist; the results that rest on assumptions the data could not pin down are listed with them [E9].

**Success criteria (PROVISIONAL, fixed in [T8] before the tests were run).**

| Criterion | PROVISIONAL threshold |
|---|---|
| Rung 1 | 100 % of fixtures reproduced exactly; every disagreement with a published list explained by a documented FIDE-side correction |
| Rung 2 | no 50-point gap bin with at least 1,000 games significantly outside ±0.01 (Holm–Bonferroni), across-bin calibration slope within 0.95–1.05, also in the farming region; log-loss better than Layer 0 with a bootstrap interval excluding zero |
| Rungs 3–5 | the targeted residual not significantly outside its threshold of [T8] and closer to zero than under Layer 0, by rating band; for rung 4, forecasts of the players whose K changes most better than Layer 0's |
| Rung 6 | the twelve-month change of the gap to the model within ±2 points from the controller's thirteenth month (R15), and the level criterion of [T8] |
| Rung 7 | cross-federation residual not significantly outside ±10 points for every federation with at least 9,000 cross-border games, and the selection test passed |
| Do no harm (every rung) | overall log-loss no more than 0.002 nats per game worse than Layer 0's at the upper end of its 95 % interval, and mean absolute calibration residual no more than 0.005 worse |
| Simulator | each rung's error against true strength not above Layer 0's in any band, and no adversary gaining more than under Layer 0 [T9] |
| Hand-checkability and ledger | 100 % of a random sample of published changes recomputed exactly; the identity of [T6] satisfied exactly every month |

---

## 12 Prior work and what this proposal adds

Much of this design was proposed first by others, and it says so; the full comparison, with page references and the claims checked, is `docs/research/PRIOR-WORK_2026-10-10.md`.

- **Ghita** (book of February 2026 and posts) diagnosed federation mispricing with a weighted, recursive cross-border index, which we credit and whose direction our broadcast games confirm [E7]; he proposed treating the expectancy scale as a monitored quantity, an activity-linked bonus, safeguards with a sunset and a one-time calibrated reset for large federations ([R 5], pp. 49–59). We share the first three in other forms (rungs 2 and 6, the caps and rollback list) and do not reset: the lists show no level left to reset for steadily active adults [E5], and federation sizes need FIDE's data. His "deflation tax" is the framing of our worked example.
- **Sonas** found the score curve shallower than the table and the ratings too spread out, and proposed the 2024 compression, the 1400 floor and the hypothetical 1800 draws [VP 3] [VP 4] [VP 5]. The lists show the compression did what he intended for the level [E5]; our table carries the spread instead of rescaling.
- **Chess Scotland's junior additions**, put to FIDE in the 2023 consultation, are rung 5's mechanism [VP 4]. **Glickman**: K from certainty is Glicko's idea [VP 6]; the anchor cohort follows US Chess's monitoring of stable players [VP 12]. **URS** first combined time controls in one strength with age-based priors [VP 8]. **Whole-History Rating** is Layer 1's method [VP 11]. **Elo++** put White's advantage in a rating system in 2010 [VP 9].
- **What this proposal adds**, checked against those sources: an open reproduction of FIDE's current calculation [E0]; each change tested alone against it under rules registered first [E2] [E6] [E8] [E10]; a table with colour and level-dependent draws that passes calibration out of sample [E2]; a model that reaches a forward-only rating only through named, capped channels; the deflation question split into level and composition [E5]; a simulator with adversaries [E9]; a points ledger; and a comparison run blind (section 10).

---

## 13 Governance and the calculator FIDE can run

**Plain statement.** The "AI calculator FIDE can run" is a statistical model, re-estimated monthly, setting the numbers of a published per-game formula within caps, in public; anyone can recompute any change by hand.

**Two published files** [T7]: the yearly table per time control, with its guard, and the monthly parameter file, holding the table's parameters, the K constants, the adjustment and its anchor means, the spread ratio and its threshold, the federation adjustments (zero while disabled) and each eligible junior's compensation. N_i and RX are printed in the list. The model's estimates of named players and, while rung 7 is off, of federations go to the QC only. One disclosure is accepted (R4): a printed N_i reveals the uncertainty behind it, and with RX a compensated junior's estimate [T2].

**Ownership and process.** The QC signs the parameter file; the Council approves changes to caps or formula after public comment, with the 2023 consultation as the model [R 18] [R 19]. No published parameter moves by more than its annual cap; a fit on a boundary is a flag for the QC (R7). Rollback follows a closed list of statistical triggers [T8]; the spread ratio past its threshold is a QC review, not a rollback (R19). Whether the QC may publish a table yearly without a Council decision is NOT VERIFIED [T11]. The federation adjustment is enabled only by Council decision after public comment, consultation with the federation, a backtest on FIDE's data and the selection test [T4].

**The properties the design guarantees** [T5]. P1 forward-only; P2 bounded change, at most 40 a game and, under R16, at most the larger of the table's constant C and 10 points a game in a period (C is 853 at level 1700, 1164 at 2300 and 1545 at 2700, against today's 700; script §5b), plus the capped adjustment; P3 continuity, no caps, clamps or bracket switches, the guard's region apart; P4 unbiasedness where the table is calibrated, the guard covering the farming region where it is not; P5 ledger completeness; P6 determinism.

**No exploitable cliffs.** Today's rules switch at a 400-point gap below 2650, at 30 games, 2300 and 2400 for K, and through two hypothetical 1800 draws, with a different regime in rapid and blitz [V 1] [V 2]. What remains discrete here is listed in [T5]: the table's bands, the guard's edges at a 400-point gap and a 2300 favourite, the publication grids and the eligibility conditions for compensation. In the simulator, farming gains 0.245 points a game over ordinary play under today's rules and 0.050 with rung 2 and its guard; arranged results between a junior and a strong adult create 9 to 11 points a game in their first year under today's rules and under every rung, and show in the ledger's per-event lines [E9] [T6].

**Anomaly monitoring.** Monthly and without names: improbable mutual results, gains from far weaker opponents, per-event ledger lines; flags go to the QC, and the engine flags, it does not judge [T8].

---

## 14 Roadmap

Nothing here touches the title and norm regulations: norm arithmetic uses table 1.4.9, identical to table 8.1.1, not table 8.1.2 [VT 1, 3]; the ratings that enter it stay the published R, never RX, and the QC assesses the effect on norms with the shadow list [T11].

| Stage [T11] | Deliverable | Gate to the next stage |
|---|---|---|
| **1. Replica and real-data tests, now** | The reference engine for standard, rapid and blitz [E0]; evidence on FIDE's lists [E1] [E5] [E8] and broadcast games [E2] [E6] [E7] [E10]; the simulator [E9]; the blind comparison on the 2026 U.S. Championships [E3]; this proposal, for QC and public comment | Layer 0 reproduces every fixture; rung 2 with its guard passes its gate, in rapid and blitz on FIDE's data; comments triaged with no unresolved correctness finding |
| **2. Shadow list, twelve months** | With the TRF archive under a data agreement (section 9): a shadow list for the chosen rungs, computed beside every official list and published with the parameter file, the ledger and the monitoring report; no effect on any rating, title or norm. Precedent: the parallel list of the 2008–2011 K-factor trial [R 16] | Twelve clean months; each shadowed rung meets its criteria on FIDE data; the QC's assessment of norms |
| **3. Pilot federation** | One federation's players rated under the chosen rungs, rung 5 included, for a domestic list; the official list unchanged; the federation chosen for complete game data, a large junior inflow, real cross-border play and willing leadership | Pilot report; QC recommendation |
| **4. Council decision** | Which rungs to adopt, scope and timing; no one-off jump: any gap between the shadow and official lists closes through the capped monthly adjustments | Council decision |

---

## 15 Open questions and decisions

**Open questions**, with the step that answers each:

1. Can the farming guard lapse, and does rung 2 pass in rapid and blitz on the pool? FIDE's games, 1,000 per bin in the region (R17) [E10].
2. Do rungs 3 to 5 work for the juniors and newcomers below 2000 they are meant for? The TRF archive; broadcast games cover the strong end [E6].
3. Are federation offsets stable and causal, or artefacts of who travels? The TRF archive and the selection test; rung 7 stays disabled until then [E7].
4. Can rung 6 meet R15? The PROVISIONAL controller lets the gap pass ±2 a year while it catches up, on broadcast months and in the simulator [E6] [E9]: a faster controller or a criterion on the settled gap is for the architect.
5. Is R16's period bound acceptable? It rises above today's 700, to 853 at level 1700 and 1545 at 2700 (script §5b): for the QC.
6. Is rounding once per period FIDE's practice? 56 of 58 periods reproduced, two one point off unexplained (SPEC-L0 v1.1).

**Decisions taken.** Recorded in `docs/decisions/D-0002_elo-1-decision-triage.md`, `docs/decisions/D-0003_architecture-revisions-v0.2.md`, `docs/decisions/D-0005_architect-decisions-v0.3.md`, `docs/decisions/D-0008_architect-rulings-elo-4.md` (R1–R14) and, for this version, `docs/decisions/D-0009_architect-rulings-elo-5.md` (R15–R23). Model estimates of named players are for the QC only, with the disclosure stated (R4); the pilot federation is chosen at stage 3; FIDE's lists are analysed, never redistributed; the out-of-date calculator is reported in Appendix F and nothing has been sent to FIDE (R14).

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
| A1 | One fixed curve turns any rating gap into a forecast, at every rating level. | §3.5 forecast accuracy across gaps; problem 4 | Rung 2: a table per time control and level band, fitted on published ratings, with draws fading with the gap [T3] |
| A2 | A draw is half a win, and colour does not matter. | §3.6 draws; §3.7 colour; problems 8, 9 | Rung 2: colour term η_tc inside the gap and the draw terms [T3]; Layer 1 outcome model [T2] |
| A3 | Every game moves a rating by a fixed step, set by brackets. | §3.4 K-factor and bracket edges; §3.1 deflation; problems 1, 6 | Rung 4: K_i from certainty, no brackets [T4] |
| A4 | Playing strength changes slowly. | §3.3 juniors; §3.11 COVID-era effects; §3.1 deflation; problems 1, 5 | Rung 5: junior compensation [T4]; age-dependent drift in Layer 1 [T2] |
| A5 | The pool is well connected: everyone is indirectly compared with everyone. | §3.2 federation isolation; §3.13 matchmaking; problems 2, 12 | Rung 7: federation adjustment, disabled pending evidence and the selection test, with connectivity diagnostics [T2] [T4]; simulator tests of isolated pools [T9] |
| A6 | Rating points are conserved, so the scale holds steady. | §3.1 deflation; §3.10 inactivity; problems 1, 7 | Rung 6: monthly adjustment from anchor drift [T4]; rung 3: seeds [T4]; the ledger [T6] |
| A7 | Players do not choose their games to protect or game their rating. | §3.8 protection and game selection; §3.9 manipulation; §3.10 inactivity; problems 3, 7, 10 | Rungs 2 and 4 remove the cliffs [T5]; the farming guard where the fitted table under-predicts favourites [T3]; rung 6 paid per active player, never per game [T4]; uncertainty growth on inactivity [T4]; anomaly monitoring; adversaries simulated [T9] [E9] |

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

## Appendix F FIDE's online calculator is out of date (a finding; R14)

FIDE's online calculator (https://ratings.fide.com/calc.phtml) was probed on 2026-10-09 with 24 rating-change cases and 8 initial-rating cases, recorded as fixtures F-C01 to F-C24 and F-I01 to F-I08 (`tests/fixtures/fide_calculator/`). The rating-change calculator reproduces table 8.1.2 and the multiplication by K, but applies the 400-point cap to every player: it agrees with §8.3.1 as written from 1 October 2025 in 20 of 24 cases and with a plain cap in 24 of 24, the four differences being players rated 2650 or above with a gap over 400 [V 1]. The initial-rating calculator follows the archived rule of 1 January 2022 till 29 February 2024 [VT 2] in 8 of 8 cases and the current rule, with its two hypothetical 1800 draws, in 1 of 8, by coincidence (`analysis/OUTPUT_L0_fixtures.md` §2–3; SPEC-L0 §6.1). Layer 0 therefore takes its test vectors from FIDE's published calculations, not from the calculator: every game and tournament sum of five adults' calculations, one first rating and 58 multi-event periods is reproduced, and the list change in 56 of the 58, six after FIDE's own base corrections; two are one point off without explanation, and one earlier period (F-P02) follows rounding per tournament, not once per period (`analysis/OUTPUT_L0_rounding.md`) [E0]. This is reported here as a finding for the QC; nothing has been sent to FIDE (founder default, D-0008, R14).

---

*End of DRAFT v1.0. Status line repeated: DRAFT v1.0 — not for publication.*
