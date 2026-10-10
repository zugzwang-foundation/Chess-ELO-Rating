# Modernising the FIDE Elo Rating System: an exact reference implementation plus an explainable correction layer

**Status: DRAFT v0.4 — not for publication**
Author: The Zugzwang Authors · Licence: CC BY 4.0 (`docs/LICENSE-docs.md`) · Date: 2026-10-10
Audience: FIDE's Qualification Commission (QC) and the chess public. Plain language first; the mathematics is in the technical annex.
Companion documents: the technical annex `docs/proposal/ELO-TECHNICAL-ANNEX_v0_4.md` (sections T1–T11), which holds every formula, proof sketch and worked example and is cross-referenced as [T n]; and a 900-word plain-language brief, `docs/proposal/ELO-BRIEF_v0_4.md`. Version 0.4 applies the architect's rulings R1–R14 (`docs/decisions/D-0008_architect-rulings-elo-4.md`) on top of decisions D1–D18 (`docs/decisions/D-0005_architect-decisions-v0.3.md`), and folds in the evidence of session ELO-4: the community register [E4], the deflation question [E5], the rungs tested on history [E6], the federation residuals [E7], the Layer 1 fit on history (`analysis/OUTPUT_L1_history.md`, under `docs/specs/SPEC-L1_v1_0.md`) and the prior-work record `docs/research/PRIOR-WORK_2026-10-10.md`.

How to read the citations. `[R §x]` points to a section of the research report `docs/research/ELO-RESEARCH_v1_0.md`; `[R n]` to the report's numbered source n; `[V k]` to item k of the primary-source sweep `docs/research/VERIFICATION_2026-10-09.md`; `[VT k]` to item k of the titles sweep `docs/research/VERIFICATION_TITLES.md`; `[VP k]` to item k of the prior-work sweep `docs/research/VERIFICATION_PRIOR-WORK.md`; `[T n]` to section n of the technical annex; `[E n]` to evidence report n under `docs/evidence/`, each the output of a committed script (E0 Layer 0 against FIDE, E1 FIDE's monthly lists, E2 the broadcast calibration, E3 the 2026 U.S. Championship, E4 the community register, E5 deflation, E6 the rungs on history, E7 federation residuals). Every FIDE rule quoted here is transcribed from [V 1] (standard) or [V 2] (rapid and blitz). Every parameter value is PROVISIONAL, a placeholder to be replaced by an estimate from data, except the expected-score table's, which are PROVISIONAL-FITTED on broadcast games [E2]. The broadcast games behind E2, E6 and E7 are stronger and more international than the rated pool; their results hold for that population until FIDE's game archive tests them.

---

## 1 Summary

**The problem.** Table 8.1.2 expects too much of favourites, by 0.02 to 0.05 at gaps of 50 to 449 points on 352,737 broadcast games [E2]; for players rated 2400 or more that over-prediction implies as large a loss as their lists show since the 2024 reset, for 2200–2399 about a third of it [E5]. Juniors improve faster than their ratings follow, and the adults who meet them score 0.055 a game below today's expectation, 0.047 more than against other adults at the same gaps [E6]. Federations are priced differently: Ghita's cross-border directions hold on a different sample for 21 of the 22 federations he names, and for all 22 on the years his data cannot contain [E7]. The fall of the level itself has stopped for steadily active adults in standard and rapid since March 2024 (blitz −1 to −2 a year); the active list's median still falls, through who enters and leaves it [E5].

**The proposal, in three sentences.** Publish an exact, open-source reference implementation of FIDE's current rules, so anyone can reproduce every list. Run behind it a statistical model, re-estimated monthly from 36 months of games, which learns what Elo assumes away: junior improvement, White's edge, draw rates, federation drift. Keep the published rating a forward-only, Elo-style number on today's scale, updated per game by a hand-checkable formula, and offer the improvements as seven rungs FIDE can adopt one at a time, each tested against today's rules first.

**What the tests show so far.** Rung 1 reproduces every game and tournament sum of FIDE's published calculations, and the list change in all but three periods [E0]; rung 2, the refitted table, passes its calibration rules on broadcast games but not yet the farming region of its gate, where it under-predicts big favourites [E2] [E6]; rung 5, junior compensation, removes most of the junior-specific drain but gives too little below 2000 and too much against adults rated 2400 or more; rungs 3 and 4 fail on broadcast data [E6].

**The ask of FIDE.** Review this design through the QC with public comment; provide the tournament-report (TRF) archive under a data agreement; run a twelve-month shadow list before any pilot. Nothing here edits a published rating retroactively, amends the title regulations or is a black box.

---

## 2 What the chess world wants fixed

v0.3 ranked four headline problems from the research report. v0.4 re-ranks them by our own evidence on FIDE's lists [E1] [E5] and broadcast games [E2] [E6] [E7], and by how often the community raises them [E4] (items raising the theme, January 2023 to September 2026).

| Rank | Problem | Our evidence | Community [E4] |
|---|---|---|---|
| 1 (was 4) | **The expected-score table, and the drain from the top** | Table 8.1.2 over-predicts favourites by 0.02–0.05 at gaps of 50–449; a fitted table passes out of sample [E2]. The implied transfer matches what players rated 2400+ still lose since 2024 and is about a third of the loss at 2200–2399 [E5]. Under the fitted table the farming region (gaps ≥ 400 above 2300) leans the other way in standard and blitz (+0.032 and +0.045, outside ±0.01 with player-clustered intervals) [E6] | the 400-point rule and farming 22; the curve 14 |
| 2 (from 1) | **Juniors and newcomers entering below strength** | Layer 1's age drift is +193 points a year under 12 and +79 at 16–19 (`analysis/OUTPUT_L1_history.md`); adults score 0.055 a game below expectation against eligible juniors, 0.047 more than against adults at the same gaps [E6]; since the 2024 floor no first rating is below 1400, so the newcomers' median first rating rose mostly by truncation [E1] | juniors 21; newcomers 21 |
| 3 (was 2) | **Federation isolation** | Ghita's directions hold for 17 of 18 federations in 2025, 21 of 22 over 2023–2026 and 22 of 22 on 2023, 2024 and 2026, years his 2025 extract cannot contain (one-sided p ≤ 0.0001); sizes not comparable, the sample being strong-player-heavy [E7] | federations 17 |
| 4 (was 3) | **Top-level protection, inactivity and K** | FIDE lifted the 400-point cap for 2650+ players in October 2025 [V 1]; about 40 % of listed players have not played since before the pandemic (Ghita's count [R 5]); today's K switches at 30 games, 2300 and 2400 [V 1]; the elite shrank after 2019, from 242 active players rated 2600+ to 150 [E5] | inactivity 21; K 17 |

**Corrected or dropped.** *Deflation of the level* is no longer a headline: since March 2024 the published level of steadily active adults has stopped falling in standard and rapid, and the often-quoted −16 points a year [R 5] is the active list's cross-sectional median, which falls because entrants arrive below the players who stop [E5]; rung 6 stays as a guard. *The pile-up at the 1400 floor* goes: the lists show fewer players at 1400 than at each of the next nine points [E1]; the floor itself (27 items) is handled by the seeds of rung 3 and the ledger's floor lines. Three popular themes are not addressed: the 2024 compression itself (30 items; the design never rescales), online ratings (16) and titles (14), both out of scope [E4]. Colour and draws are modelled as fairness features [E2].

---

## 3 Design principles

### 3(a) What stays constant across every style of play

1. **One core skill per player.** A player has one underlying strength, θ, shared across standard, rapid and blitz (and, if FIDE adds it, Chess960); style-specific differences are offsets from it (sections 7 and 8).
2. **A forward-only published number on today's scale.** The rating a player sees moves only forward, only in months in which the player plays, and a 2500 today means what a 2500 meant last month. No retroactive revision, no rescaling, no jump at adoption.
3. **Every change explainable and hand-checkable.** Each change decomposes into named terms a player or arbiter can recompute with a calculator.
4. **Deterministic and open-source.** Same inputs, same outputs, on any machine; code, test vectors, the yearly table and the monthly parameter file are public.
5. **Parameters re-estimated with published annual change caps.** No published parameter may move by more than a published cap per year.
6. **Every point accounted for.** A monthly ledger states where rating points were created, destroyed and moved (section 5) [T6].

### 3(b) What diverges by style

- **Per-time-control offsets** δ_tc: a player's rapid or blitz strength is θ plus a shrunken offset (section 7).
- **An expected-score function per time control:** its slope κ_tc, colour term η_tc and draw parameters α_tc, β_tc and γ_tc are fitted separately for standard, rapid and blitz, because White's edge and draw propensity differ by style and level [E2] [T3].
- **Volatility per time control:** how fast skill may move month to month is estimated separately for each style [T2].

### 3(c) The eight adoptability requirements

The research report sets eight requirements for an official rating [R §7]; this design meets each as follows.

| # | Requirement | Met by |
|---|---|---|
| 1 | Determinism and reproducibility | Exact decimal arithmetic with one rounding step, today's rounding (§8.3.4 [V 1]), versioned parameters, identical output from identical TRF input [T4] |
| 2 | Transparency | A yearly lookup table and a monthly parameter file, both public and versioned [T7] |
| 3 | Auditability | A per-game breakdown published with every change, and a monthly points ledger [T4] [T6] |
| 4 | Explainability | Model influence enters only through the named rungs of section 9, each a labelled line on the breakdown |
| 5 | Open-source code with test vectors | Apache-2.0 code, CC BY 4.0 documents, test vectors from FIDE's published calculations [E0] |
| 6 | Governance | The QC signs the parameter file; Council approves changes to caps or formula; public comment before changes (section 12) |
| 7 | Fairness and bias monitoring | Residuals by age, sex, rating band and colour reported monthly; by federation to the QC only while rung 7 is disabled [T8] |
| 8 | Manipulation resistance | No cliffs; K from certainty; continuous compensation; adjustments paid per active player, never per game; anomaly monitoring; adversarial simulations [T9] |

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
   │      Rungs of the adoption ladder (section 9), each named, capped, published:│
   │        2 fitted table with colour and draws    3 newcomer seeds              │
   │        4 K from certainty                      5 junior compensation         │
   │        6 monthly adjustment                    7 federation adjustment (OFF) │
   │      and the points ledger                                                   │
   └──────────────────────────────────────────────────────────────────────────────┘
```

**Layer 0, the reference engine.** An exact implementation of the FIDE Rating Regulations as amended 1 October 2025 [V 1] and of the Rapid and Blitz Rating Regulations [V 2], specified in `docs/specs/SPEC-L0_fide-reference-engine_v1_0.md` and verified against FIDE's published calculations game by game [E0] and on 58 more multi-event periods, where every game and tournament sum is reproduced and the list change in 56, two being one point off without explanation (`analysis/OUTPUT_L0_rounding.md`); FIDE's online calculator is out of date (Appendix F). It is rung 1 and the baseline for every other rung; no other repository found claims to reproduce today's list [R §5].

**Layer 1, the model** [T2]. Each player has a shared skill θ that moves with an age-dependent drift and a per-time-control offset δ_tc shrunk towards zero; outcomes follow the published table's form, with colour and draws. It is refitted monthly on a rolling 36-month window by the method of Whole-History Rating [VP 11]; priors depend on age only, never on federation; the scale is anchored to steadily active adults, as US Chess does [VP 12]. Specified in `docs/specs/SPEC-L1_v1_0.md`, it has been fitted on 776,825 broadcast games between 88,253 players with FIDE IDs, 2023 to September 2026, and gives a usable estimate for 95 % of active players rated 2600 or more but 0.7 % of those below 1600 (`analysis/OUTPUT_L1_history.md`). Its estimates of named players are for the QC only. **It never edits a published rating.**

**Layer 2, the published rating** [T4]. Forward-only and Elo-style, on today's scale, updated per game by R_i ← R_i + K_i · (S_i − E(x_i)). Model influence enters only through named, published, capped channels, each a rung of the ladder of section 9:

- **Expected score (rung 2).** One function per time control, fitted on published ratings, colours and results and published yearly as a lookup table per 100-point level band, succeeds table 8.1.2 [V 1]; colour is inside the gap, draws fade with it, and there are no caps or clamps [T3].
- **Newcomer seeds (rung 3).** A newcomer's first rating is the model's estimate from their first games in all three time controls, replacing the two hypothetical draws against 1800-rated opponents (§8.2.2 [V 1]).
- **K from certainty (rung 4).** K_i, between 10 and 40 as today (§8.3.3 [V 1]), follows the model's certainty about the player; an inactive player's rating never decays, but K_i is higher on return.
- **Junior compensation (rung 5).** Against a junior whom the model rates well above their published number, the opponent's expectation uses a compensated rating that rises smoothly with the evidence in that time control; the junior's own update, and any game between two eligible juniors, use published ratings.
- **Monthly adjustment (rung 6).** A small, capped adjustment of either sign, from the anchor cohort's drift, credited to active players in proportion to their activity up to the cohort's average.
- **Federation adjustment (rung 7).** The same per federation, DISABLED until FIDE's own game data show federation miscalibration stable, predictive and not an artefact of who travels. An adjustment, unlike an offset inside the expectation, closes a gap over time instead of freezing it.

**The monthly cycle.** After the closing date (§7.1.3 [V 1]), Layer 0 produces the official list as today and Layer 2 a shadow list; Layer 1 writes the coming month's parameter file within its caps; the QC signs and publishes them.

---

## 5 The published rating in practice

**The update.** For each game, a player's rating changes by

> R_i ← R_i + K_i · (S_i − E(x_i))

where S_i is the score (1, ½, 0), E(x_i) the expected score read from the published table for the time control and level band, and K_i the player's printed development coefficient. Each game term is computed exactly from the printed K_i (one decimal) and the table value (three decimals); the terms are summed over the rating period together with any adjustment balance and rounded once, exactly as today: nearest whole number, 0.5 away from zero (§8.3.4 [V 1]) [T4].

**The gap.** x_i is the player's rating minus the opponent's rating for expectation, plus the colour term η_tc for White and minus it for Black (η_tc fitted on broadcast games: 36 points standard, 37 rapid, 27 blitz [E2]). Colour is inside the expectation, so a surplus of Whites is charged game by game: an extra White no longer pays [T3]. The opponent's rating for expectation is the published rating, plus the published compensation c_j when the opponent is an eligible junior and the player is not (section 6); the list flags every eligible junior, with RX printed even when c_j is 0, so that an arbiter can apply the rule. There is no cap on the gap, no clamp and no exemption at any level; the function is continuous, and the two players' expectations sum to one whenever no compensation applies [T5].

**The table arbiters use.** One block per time control and 100-point level band (the level from the mean of the two published ratings), a three-decimal value for every gap from 0 to 1500, and 1 − E for a negative gap [T3] [T7]. Bands exist because strong players draw more [R 48]; neighbouring bands differ by at most 0.012. In band 2300–2399 a 500-point favourite expects 0.918, close to Sonas's 5/6-gap rule (0.917) [R 44] [T3].

**Fitted on published ratings; level and spread.** The table is fitted on the ratings players see and choose opponents by, so that if it is right no choice of opponent's rating or colour gains anything in expectation (property P4, section 12); choosing on other information, such as federation, is not covered while rung 7 is off [T3]. The monthly adjustment holds the level. The spread is carried by the fitted table as a whole, its slope κ together with the draw term that rises with level, not by κ alone: near equal ratings the standard table behaves like logistic Elo with a scale of 481 points at level 1700, 649 at 2300 and 856 at 2700, against 400 [E2] [T3]. Because a yearly refit could ratchet the spread, κ's annual cap stays and a second reference is published monthly: the ratio of the spread of published ratings to that of the model's estimates for active adults (0.794 in January 2023, 0.747 in September 2026 in standard; `analysis/OUTPUT_L1_history.md`). If the calendar-year mean of the noise-corrected ratio moves by more than 0.02 in the same direction two years running (PROVISIONAL; a ratchet held to κ's cap would move it about 0.03 a year), the QC reviews; nothing corrects automatically, and no rating is rescaled [T3].

**K from certainty.** K_i is the Kalman gain of one game on the published scale, given the model's certainty about the player:

> K_i = clip(q · σ_i² / (κ_tc · (1 + q² · σ_i² · v_tc)), K_min, K_max), q = ln 10 / 400

where σ_i is the model's standard deviation for the player in that time control, v_tc the score variance of one game at equal ratings in the player's level band of the fitted table, and K_min = 10, K_max = 40 (PROVISIONAL). A newcomer has 40; K then follows activity and the model's process noise: with an illustrative 12 points a month, about 12 to 22 with two to four standard games a month, but with the 24 fitted on history, about 22 to 40, against today's 40, 20 and 10 [T4]. Established players rated 2600 or more get a median K_i of 20.0 on broadcast games (`analysis/OUTPUT_L1_history.md`); the archive holds most of their standard games [E5], so that is largely what the rule gives, and in the rung test established adults' monthly changes doubled (median 7.6 to 16.8 points) [E6]. Whether K should fall with the number of games in a period is for the architect. There is no switch at 30 games, 2300, 2400 or age 18. The list prints K_i, the compensated rating RX and the carried adjustment balance, so any change is recomputable; today's cap K_i × n ≤ 700 carries over [T4].

**The monthly adjustment.** Each month the model compares the anchor cohort's published mean with its own estimate; when the difference d_t exceeds 2 points either way, a sixth of the excess, capped at 1.5 points a month (PROVISIONAL), is credited to active players, positive in a deflating pool and negative in an inflating one, in proportion to their rated games over twelve months up to the cohort's average (R3) [T4]. It is published before the month it applies to, added when the player next plays and never grows with games beyond the average; the list prints the settled rating, R plus the carried balance, for rating-based selections.

**The ledger.** Unequal K factors, newcomers, the floor and departures create or destroy points, which is how a scale drifts. Each month the ledger states, per time control, where the points went, by channel, like a central bank publishing how much money it created and why; the identity is exact [T6].

**Worked example (hand-checkable)** [T10]. An adult, A, rated 1900, has White against a junior, J, published at 1500 but estimated by Layer 1 at 1850 on the published scale with a standard deviation of 100. J's compensation is the part of the gap the model is 90 % sure of, less 25: 1850 − 1.2816 × 100 − 1500 − 25 = 196.84, so 197, and J counts as 1697 in A's expectation, while J's own uses 1500 and 1900. A's K_i is 14.1 and J's 40.0 (PROVISIONAL, from model standard deviations of 55 and 121.2). Today table 8.1.2 gives A .92 with K = 20 and J .08 with K = 40 [V 1], and a draw costs A 8.4 points before rounding, Ghita's example of how under-rated juniors drain adults ([R 5], pp. 13, 18).

| Result | A today: 20 × (S − .92) | J today: 40 × (S − .08) | A, all rungs: 14.1 × (S − 0.780) | J, all rungs: 40.0 × (S − 0.081) |
|---|---|---|---|---|
| A wins | +1.6 → **+2** | −3.2 → **−3** | +3.1020 → **+3** | −3.2400 → **−3** |
| Draw | −8.4 → **−8** | +16.8 → **+17** | −3.9480 → **−4** | +16.7600 → **+17** |
| J wins | −18.4 → **−18** | +36.8 → **+37** | −10.9980 → **−11** | +36.7600 → **+37** |

The adult loses less for drawing a junior who is really an 1850 player (−4 instead of −8) or losing to one (−11 instead of −18) and gains more for winning (+3 instead of +2); the junior's changes are today's. The expectations, 0.780 and 0.081, do not sum to one; the ledger prints the difference as 14.1 × (0.919 − 0.780) = 1.9599 points created by compensation [T6].

---

## 6 Where points enter and leave

| Topic | Today (transcribed [V 1] [V 2]) | Proposed | Why |
|---|---|---|---|
| **Newcomers** (rung 3) | Published after at least 5 games against rated opponents, pooled over up to 26 months; Ra = average of rated opponents plus two hypothetical 1800-rated opponents scored as draws; Ru = Ra + dp from table 8.1.1, rounded, maximum 2200; a zero score in the first event is disregarded (§7.1.4, §8.2) | Same 5-game, 26-month threshold. The seed is the Layer 1 estimate for the player on the published scale, θ̃ = m_t + (ŝ − m̂_t)/κ_tc (R2), drawing on their games in all three time controls and on a prior that depends on age only, rounded, at most 2200, published only if it is at least 1400, the model's uncertainty is at most 120 points and at least half of the estimate's precision comes from games in that time control (PROVISIONAL, as R5 requires of compensation) [T4]; the five games must involve 3 opponents in 2 events, a change to §7.1.4; no hypothetical opponents. The newcomer starts with the model's uncertainty, hence K_i near 40, and the ledger records the points that enter with them | The two hypothetical draws pull every newcomer towards 1800 whatever their age and were part of the 2024 repair [VP 3] [VP 4]; Sonas called the initial-rating formula the main engine of deflation [VP 5]. A passport is not evidence of strength, so the prior ignores federation. On broadcast games the seeds are closer to newcomers' results on average than FIDE's first ratings but noisier game by game, so the rung fails its do-no-harm check there [E6] |
| **Juniors** (rung 5) | K = 40 until the end of the year of the 18th birthday while rated under 2300; otherwise standard rules (§8.3.3) | A junior (list year minus year of birth at most 19) with at least 10 rated games in the time control against at least 5 opponents in at least 3 events, at least half of whose estimate's precision comes from games in that time control (R5, PROVISIONAL 0.5), carries c_j = the 90 % lower estimate on the published scale, minus the published rating, minus τ = 25, between 0 and 300 (PROVISIONAL), from the same-time-control posterior. It enters only the expectation of opponents who are not themselves eligible (R8) and fades to zero as the junior's rating catches up [T4] | Juniors improve faster than K = 40 can track [R §3.3]; the adult's loss, not the junior's gain, is what drains the pool [R 5] [VP 3]. On broadcast games adults score 0.055 a game below today's expectation against eligible juniors, 0.047 more than against adults at the same gaps, and 0.018 below with compensation; the compensation is too small below 2000 and too large against adults rated 2400 or more [E6]. The mechanism is Chess Scotland's "junior additions", applied since 1976 by its account, made evidence-based [VP 4] (section 11) |
| **Floor** | Ratings below 1400 are shown as unrated on the next list; the player is thereafter treated as any unrated player (§7.2.1) | §7.2.1 is unchanged as a display rule. Layer 1 keeps estimating the player; on re-qualifying under §7.1.4 the player is re-published only if the Layer 1 estimate is at least 1400, and the seed is that estimate. The ledger records the points leaving through the floor and re-entering [T4] | Re-entry through the newcomer rule injects points at the bottom. The published lists show no pile-up at 1400 (fewer players at 1400 than at each of the next nine points); players below the floor leave the list [E1] |
| **Inactivity** (rung 4) | A player commences inactivity after one year without a rated game and regains activity after one game (§7.2.2); ratings do not decay | No rating decays. The model's uncertainty about an inactive player grows, so K_i is higher on return. No adjustment accrues while inactive. The inactive flag stays | About 40 % of listed players have not played since before the pandemic [R 5]; uncertainty growth with time away is Glicko's remedy [VP 6] |
| **Monthly adjustments** (rungs 6, 7) | No rule; the level of the scale is left to the arithmetic of K factors and seeds | A global adjustment a_t per time control, of either sign, with a 2-point deadband and a 1.5-point monthly cap (PROVISIONAL), accrued to active players scaled by min(1, their rated games over 12 months ÷ the anchor cohort's average) (R3) and posted in a month in which the player plays [T4] [T7]. A federation adjustment with the same structure, DISABLED until the evidence test of section 12 is passed | The level of steadily active adults fell 2 to 6 points a year before March 2024 and has held since [E5]: the adjustment guards against a return. US Chess holds its level with a bonus it re-tuned as ratings continued to deflate [VP 12]; scaling by activity matches the payment to a drain that occurs per game (R3) and moves it towards the activity-linked bonus Ghita proposed first ([R 5], p. 55) |

---

## 7 One framework across time controls

**The structure.** skill_tc = θ + δ_tc: one shared skill per player plus an offset for each time control, shrunk towards zero, so a rapid specialist can be stronger at rapid without being treated as a different person [T2]. Each time control keeps its own expected-score function and volatility, because White's edge and draw rates differ by style [E2]. One strength informed by every time control is the Universal Rating System's idea [VP 8]; here the three lists stay separate and forward-only. With few games in a style, δ_tc stays near zero; the shrinkage ω is chosen on held-out games (4 points a month on broadcast history, `analysis/OUTPUT_L1_history.md`).

**What a rapid game tells the classical rating.** In Layer 1 every game updates θ. In Layer 2 a rapid game reaches the classical rating only through a newcomer's seed; compensation uses the same time control's evidence (R5), and no rapid result enters the classical per-game formula.

**What FIDE does today.** FIDE's two rating chapters share tables, K rules and rounding but differ at the top: since 1 October 2025 the standard chapter uses the full difference for players rated 2650 and above [V 1]; the rapid and blitz chapter keeps the plain 400-point cap and, since 1 December 2024, does not rate games 600 or more points apart involving a player above 2600 [V 2]. Separately amended rule sets drift apart; one expected-score function in all three time controls, without caps or exclusions, removes the difference [T3].

---

## 8 Chess960

FIDE's 2026 General Assembly approved plans for a Chess960 rating system [R §2] [R 25] [R 26]. With a shared skill, a Chess960 list is one more offset on θ, seeded on day one from existing estimates with K near 40 [T2]. FIDE's plan is NOT VERIFIED; this is an option.

---

## 9 The adoption ladder

Seven rungs, lowest risk first, each adoptable alone: a rung not adopted leaves today's rule in place. Each is tested against Layer 0 on its problem and must not make the overall forecast worse (section 10) [T8].

| Rung | What changes | Targeted metric | Status on the data tested so far |
|---|---|---|---|
| 1 The open replica | Nothing in the rules: an open engine reproduces today's list exactly | 100 % of the fixtures of FIDE's published calculations reproduced | Met for every game and tournament sum, every fixture and the 2025 U.S. Championship [E0]; of 58 multi-event periods, the list change is reproduced in 56 and two are one point off unexplained, so the criterion is not yet met for them (Appendix F) |
| 2 The re-fitted table with colour and draws | Table 8.1.2 replaced by a yearly table fitted on published ratings, with colour, draws and 100-point level bands; same K | Calibration by gap, level and colour; three-outcome log-loss against Layer 0 | Passes rules (a) and (b) in standard, rapid and blitz on broadcast games [E2]; the farming region of its gate is not passed: at gaps ≥ 400 above 2300 it under-predicts favourites in standard (+0.032) and blitz (+0.045), outside ±0.01 with player-clustered intervals [E6]; to be repeated on FIDE's data before adoption |
| 3 Newcomer seeds | First rating from the model, not two 1800 draws | Newcomers' results against expectation over their first 30 games | Does not pass on broadcast games: residual −0.010 with seeds against −0.020 with FIDE's first ratings, but log-loss worse by 0.050 a game; seeds come from broadcast games only [E6] |
| 4 K from certainty | K_i from the model's uncertainty, 10 to 40 (R6) | Forecast accuracy for the players whose K changes most | Does not pass on broadcast games: log-loss worse by 0.0024 a game, and established adults' monthly changes double; most broadcast players sit at K = 40 [E6] |
| 5 Junior compensation | Opponents of under-rated juniors use the compensated rating (R5, R8) | Adults' results against juniors relative to expectation | Does not pass on broadcast games: adults' residual against eligible juniors from −0.055 to −0.018 a game and log-loss better by 0.016; against a matched control the junior-specific residual falls from −0.047 to −0.010, inside ±0.01, but by band the compensation is too small below 2000 and too large against adults rated 2400 or more (+0.026 in the games where it applies) [E6] |
| 6 The monthly adjustment | A capped monthly adjustment of either sign, accrual scaled by activity (R3) | Drift of the anchor cohort within ±2 points a year | Level criterion met; the D_t rule not met, because the fixed anchor panel's published mean rose 2 to 9 points a year while the controller follows the gap to Layer 1, a design question for the architect [E6] |
| 7 The federation adjustment, last | The same per federation, after FIDE data | Cross-federation residuals; the selection test | Not testable without FIDE's game archive; the direction of federation residuals is confirmed on broadcast games [E7] |

Rungs 1 and 2 need no model; rungs 3 to 6 need Layer 1; rung 7 comes last because only FIDE's game record can test it. The broadcast tests are the strongest available before FIDE's data, and they are biased: for rungs 3 to 5 they cover the strong juniors and newcomers who play broadcast events, not the improving players below 2000 the rungs are meant for, and Layer 1 sees only part of each player's games (`analysis/OUTPUT_L1_history.md` §5) [E6].

---

## 10 Proof plan

**One baseline.** Layer 0, today's rules exactly; other systems are prior art (section 11).

**Protocol.** Rolling-origin evaluation: fit on games up to month t, forecast month t+1, score, roll forward; the match schedule is never a feature [R 9] [VP 10]. Each rung is scored on its targeted metric and on a do-no-harm check against tolerances fixed in [T8] before any FIDE game data are seen.

**Data.** FIDE's monthly lists since February 2015 [V 3], analysed and never redistributed; the Lichess broadcast archive of over-the-board games, CC BY-SA 4.0 [V 4], with its bias towards strong players stated. Online games are not evidence. FIDE's TRF archive (§9.1 [V 1]) is the only data that can settle rungs 3 to 7 for the whole pool [R §5].

**Results so far** (section 9): rung 1 met but for three periods [E0]; rung 2 passes its calibration rules on broadcast games but not the farming region of its gate [E2] [E6]; rung 5 removes most of the junior-specific drain but is miscalibrated by level; rungs 3 and 4 fail on broadcast data for reasons the data explain; rung 6 was tested in months with almost no drift [E6]. The deflation question that v0.3 led with is settled on FIDE's lists [E5]. **The simulator** [T9] comes next: known true strengths, federation-clustered pairings and Swiss events, so that recovery, the controller under sustained drift and every adversary strategy are measured exactly.

**Success criteria (PROVISIONAL, fixed in [T8] before the tests are run).**

| Criterion | PROVISIONAL threshold |
|---|---|
| Rung 1 | 100 % of fixtures reproduced exactly; every disagreement with a published list explained by a documented FIDE-side correction |
| Rung 2 | no 50-point gap bin with at least 1,000 games significantly outside ±0.01 (Holm–Bonferroni), across-bin calibration slope within 0.95–1.05, also in the farming region; log-loss better than Layer 0 with a bootstrap interval excluding zero |
| Rungs 3–5 | the targeted residual not significantly outside its threshold of [T8] and closer to zero than under Layer 0, by rating band |
| Rung 6 | anchor-cohort drift within ±2 points per year from the controller's thirteenth month, and the level criterion of [T8] |
| Rung 7 | cross-federation residual not significantly outside ±10 points for every federation with at least 9,000 cross-border games, and the selection test passed |
| Do no harm (every rung) | overall log-loss no more than 0.002 nats per game worse than Layer 0's at the upper end of its 95 % interval, and mean absolute calibration residual no more than 0.005 worse |
| Hand-checkability | 100 % of a random sample of published changes recomputed exactly from the breakdown, the table and the parameter file |
| Ledger | the identity of [T6] satisfied exactly every month |

---

## 11 Prior work and what this proposal adds

Much of this design was proposed first by others, and it says so; the full comparison, with page references and the claims checked, is `docs/research/PRIOR-WORK_2026-10-10.md`.

- **Ghita** (book of February 2026 and posts) diagnosed federation mispricing with a weighted, recursive cross-border index, which we credit and whose direction our broadcast games confirm [E7]; proposed treating the expectancy scale as a monitored quantity (S = 459), an activity-linked bonus, safeguards with a sunset, and a one-time calibrated reset for large federations ([R 5], pp. 49–59). He proposed the first three before us; we share them in other forms (rungs 2 and 6, the caps and rollback list) and do not reset: our lists show no level left to reset for steadily active adults [E5], federation sizes need FIDE's data, and under-rated juniors are handled through their opponents' expectations. His "deflation tax" framing of the junior drain is the one our worked example uses.
- **Sonas** (2023 proposal and reports hosted by FIDE) found the score curve shallower than the table and the ratings too spread out, and proposed the 2024 compression, the 1400 floor and the hypothetical 1800 draws [VP 3] [VP 4] [VP 5]. Our lists show the compression did what he intended for the level [E5]; our table carries the spread instead of rescaling.
- **Glickman**: K from certainty is Glicko's idea, the gain following the rating deviation, which grows with time away [VP 6]; the anchor cohort follows US Chess's monitoring of stable players [VP 12]. **URS** (Sonas, Glickman, Miller, Rischard) first combined time controls in one strength with age-based priors [VP 8]. **Whole-History Rating** is Layer 1's fitting method [VP 11]. **Elo++**, the 2010 Kaggle winner, already put White's advantage in a rating system [VP 9]. **Chess Scotland's junior additions**, put to FIDE in the 2023 consultation, are rung 5's mechanism [VP 4].
- **What this proposal adds**, checked against those sources: an open reproduction of FIDE's current calculation with fixtures from FIDE's own published calculations [E0]; each change tested alone against it on held-out months under rules registered first [E2] [E6]; a normative table with colour and level-dependent draws that passes calibration out of sample [E2]; a model that sits behind a forward-only published rating and enters it only through named, capped channels; the deflation question separated into level and composition on FIDE's lists [E5]; and a monthly points ledger.

---

## 12 Governance and the calculator FIDE can run

**Plain statement.** The "AI calculator FIDE can run" is a statistical model, re-estimated monthly, setting the numbers of a published per-game formula within caps, in public; anyone can recompute any change by hand.

**Two published files** [T7]. The yearly table per time control, and the monthly parameter file: the table's parameters, the K bounds, the adjustment and its anchor means, the spread ratio and its threshold, the federation adjustments (zero while disabled) and each eligible junior's compensation. K_i and RX are printed in the list; the model's estimates of named players and, while rung 7 is off, of federations go to the QC only. One disclosure is accepted and stated (R4): a printed K_i reveals the uncertainty behind it, and with RX a compensated junior's estimate; the QC-only rule covers the full posterior and everything else [T2].

**Caps and flags.** No published parameter moves by more than its annual cap [T7]; γ has no upper bound, and a fit on any boundary is a flag for the QC (R7).

**Ownership and process.** The QC signs the parameter file; the Council approves changes to caps or formula after public comment, with the 2023 consultation as the model [R 18] [R 19]. Rollback follows a closed list of statistical triggers [T8]; a spread ratio beyond its threshold two years running is a QC review, not a rollback (R1). Whether the QC may publish a normative table yearly without a Council decision is NOT VERIFIED [T11]. The federation adjustment is enabled only by Council decision, after public comment, consultation with the federation, a backtest on FIDE's data and a selection test: offsets estimated from junior and adult travellers, and from home and away events, must agree, so that it measures the pool, not who travels [T4].

**The properties the design guarantees** [T5]. P1 forward-only; P2 bounded change, at most K_i per game and 700 points plus the capped adjustment per period; P3 continuity, no caps, clamps or bracket switches; P4 unbiasedness: if the table is right, no pairing or colour gains in expectation, and where it is not, as the farming region shows for big favourites above 2300 in standard and blitz [E6], the residual is a gain of about 0.6 points a game in standard at the K that rung 4 gives established 2600+ players, more in blitz; rung 2 is not recommended there until FIDE's data clear the region, and whether rapid and blitz keep their 600-point exclusion meanwhile is for the architect; P5 ledger completeness; P6 determinism, the model fit reproducible to a published tolerance.

**No exploitable cliffs.** Today's rules switch at a 400-point gap below 2650, at 30 games, 2300 and 2400 for K, and through two hypothetical 1800 draws at the floor, with a different regime in rapid and blitz [V 1] [V 2]. The design has none; what remains discrete is listed in [T5]: the table's bands, the publication grids and the eligibility conditions for compensation, which the list makes visible with a flag for every eligible junior. There is no cap on the ratio of K factors, which would slow exactly the players who should move fast; arranged results show in the per-event ledger lines and the monitoring report [T6].

**Anomaly monitoring.** Monthly, without names: clusters of improbable mutual results, the share of gains from opponents more than 400 below, per-event ledger lines. Flags go to the QC and named cases to FIDE's procedures (NOT VERIFIED here); the engine flags, it does not judge.

---

## 13 Roadmap

Nothing in this proposal touches the title and norm regulations. Norm arithmetic uses table 1.4.9, identical to table 8.1.1, and not table 8.1.2 [VT 1, 3], so rung 2 leaves the norm formula unchanged; what any rung changes is the ratings that enter it, which the proposal leaves as published ratings R, never RX. How that affects norms is for the QC to assess with the shadow list's numbers [T11].

| Stage [T11] | Deliverable | Gate to the next stage |
|---|---|---|
| **1. Layer 0 replica and real-data tests, now** | The reference engine for standard, rapid and blitz, verified against FIDE's published calculations [E0]; evidence on FIDE's monthly lists (drift, floor, newcomers, K) [E1] [E5] and on the broadcast archive (calibration, colour, draws; Layer 1; the rung tests) [E2] [E6] [E7]; the simulator next [T9]; this proposal at v1.0 with code and test vectors, for QC and public comment | Layer 0 reproduces every fixture exactly; rung 2 passes its test and the do-no-harm check [T8], the farming region included; comments triaged with no unresolved correctness finding |
| **2. Shadow list, twelve months** | With the TRF archive under a data-sharing agreement, pitched as a digital-transformation deliverable [R §2] [R 28]: a shadow list for the chosen rungs, computed in parallel with every official list and published beside it, with the parameter file, the ledger and the monitoring report; no effect on any rating, title or norm. Precedent: the parallel list during the 2008–2011 K-factor trial [R §2] [R 16] | Twelve clean months; each shadowed rung meets its criteria of [T8] on FIDE data; the QC's assessment of the title and norm question |
| **3. Pilot federation** | One federation's players rated under the chosen rungs for a domestic list, with the official list unchanged; monthly reports; the federation adjustment still disabled. The federation is chosen at this stage for complete game data, a large junior inflow, real cross-border play and willing leadership | Pilot report; QC recommendation |
| **4. Council decision** | QC recommendation to the FIDE Council on which rungs to adopt, scope and timing; adoption, if any, with no one-off jump: any gap between the shadow and official lists closes through the capped monthly adjustments | Council decision |

---

## 14 Open questions and decisions

**Open questions** (restated with the step that answers each):

1. Are federation offsets stable and causal, or artefacts of who travels? Needs the TRF archive and the selection test; rung 7 stays disabled until then [E7].
2. Do rungs 3 to 5 work for the juniors and newcomers below 2000 they are meant for? Needs the TRF archive; the broadcast tests cover the strong end [E6].
3. Does the fitted table under-predict big favourites above 2300 in FIDE's own games, as the pooled broadcast test suggests in standard and blitz? The formal test needs FIDE's data (R12) [E6].
4. How does the monthly controller behave under sustained drift? The simulator answers it [T9].
5. Is rounding once per period FIDE's practice? 13 of 14 discriminating periods say so (`analysis/OUTPUT_L0_rounding.md`); a new SPEC-L0 version would reclassify it.
6. Will the QC accept a model-driven correction layer, and how do the rungs' ratings feed the norm tables? The shadow list answers the second.

**Decisions taken.** Recorded in `docs/decisions/D-0002_elo-1-decision-triage.md`, `docs/decisions/D-0003_architecture-revisions-v0.2.md`, `docs/decisions/D-0005_architect-decisions-v0.3.md` and, for this version, `docs/decisions/D-0008_architect-rulings-elo-4.md` (R1–R14). The founder's decisions are applied: model estimates of named players are for the QC only, with the K–RX disclosure stated (R4); the pilot federation is chosen at stage 3; FIDE's lists are analysed, never redistributed; the out-of-date calculator is reported in Appendix F and nothing has been sent to FIDE (R14).

**Still open for the founder.** (1) Repository name and visibility: kept as `Chess-ELO-Rating`, public (`docs/decisions/D-0001_repo-licence-visibility-language.md`); revisit before v1.0? (2) The wording of the stage 2 request to FIDE for the TRF archive.

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
| A7 | Players do not choose their games to protect or game their rating. | §3.8 protection and game selection; §3.9 manipulation; §3.10 inactivity; problems 3, 7, 10 | Rungs 2 and 4 remove the cliffs [T5]; rung 6 paid per active player, never per game [T4]; uncertainty growth on inactivity [T4]; anomaly monitoring and adversarial simulations [T9] |

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

*End of DRAFT v0.4. Status line repeated: DRAFT v0.4 — not for publication.*
