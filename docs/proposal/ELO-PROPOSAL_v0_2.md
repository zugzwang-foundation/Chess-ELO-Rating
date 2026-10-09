# Modernising the FIDE Elo Rating System: an exact reference implementation plus an explainable correction layer

**Status: DRAFT v0.2 — not for publication**
Author: The Zugzwang Authors · Licence: CC BY 4.0 (`docs/LICENSE-docs.md`) · Date: 2026-10-09
Audience: FIDE's Qualification Commission (QC) and the chess public. Plain language first; the mathematics is in the technical annex.
Companion document: the technical annex `docs/proposal/ELO-TECHNICAL-ANNEX_v0_2.md` (sections T1–T11) holds every formula, proof sketch and worked example; this document cross-references it as [T n].

How to read the citations. `[R §x]` points to a section of the research report `docs/research/ELO-RESEARCH_v1_0.md`; `[R n]` to the report's numbered source n; `[V k]` to item k of the primary-source verification sweep `docs/research/VERIFICATION_2026-10-09.md`; `[T n]` to section n of the technical annex. Every FIDE rule quoted here is transcribed from [V 1] (standard) or [V 2] (rapid and blitz). Every parameter value is PROVISIONAL: a placeholder to be replaced by an estimate from data.

---

## 1 Summary

**The problem.** The FIDE rating is the world's reference number for chess strength, and it is drifting. After the March 2024 reset the median active player still loses about 16 points a year [R 5]. One independent, not peer-reviewed study finds that the same number can mean strengths differing by about 100 points between federations [R 6]. FIDE corrected the 400-point cap's top-level incentive by amendment in October 2025 [R 7] [V 1]; the expectancy table over-predicts favourites at large gaps [R 44]; each correction so far has been a separate amendment.

**The proposal, in three sentences.** Publish an exact, open-source reference implementation of FIDE's current rules, so anyone can reproduce every list. Run behind it a statistical model, re-estimated monthly from the last 36 months of games, which learns what Elo assumes away: junior improvement, federation drift, White's edge, draw rates. Keep the published rating a forward-only, Elo-style number on today's scale, updated per game by a hand-checkable formula from a published table; the model reaches it only through six named, capped, published channels and a monthly ledger.

**The ask of FIDE.** Review this design through the QC with public comment, as in 2023; provide the tournament-report (TRF) archive under a data agreement; and run a twelve-month shadow list before any pilot. Nothing here edits a published rating retroactively or amends the title and norm regulations; whether their arithmetic is affected by the new table is NOT VERIFIED and is what the shadow list answers (section 10). Nothing here is a black box.

---

## 2 What the chess world wants fixed

The research report ranks the complaints by community demand, strength of evidence and fixability ("Ranked problem table", [R Recommendations]). The four headline targets, in order:

| Rank | Target | What the evidence says | Pointer |
|---|---|---|---|
| 1 | **Deflation and junior lag** | Sonas (2023, hosted by FIDE) found "extreme rating deflation": players rated 1000 to 2400 spanned only about 1000 points of real strength, because newcomers and juniors enter below their strength and drain points from established players. After the 2024 reform the average rating still fell about 1 point a month, the median active player lost 16 points a year instead of 26, and players pile up at the 1400 floor. FIDE acknowledged the problem in the 2023 consultation and the 2024 reform. | [R §3.1] [R §3.3] [R 3] [R 4] [R 5] [R 37] [R 39] |
| 2 | **Federation isolation** | Most games are domestic, so pools drift apart. Ghita's 2026 study of cross-border games estimates offsets between federations of the order of plus 100 to minus 60 points, with gaps that "can exceed 160 Elo"; there is no official fix. Caveat: independent, not peer-reviewed; the "over 80 % domestic" figure is unverified. | [R §3.2] [R 5] [R 6] |
| 3 | **Top-level protection, farming and inactivity** | The 400-point cap allowed a 2800-rated player to gain points, within the rules, against 2250-rated opponents; FIDE lifted the cap for 2650+ players from 1 October 2025. Ratings never decay, about 40 % of listed players have not played since before the pandemic, and FIDE's then-president called inactivity the next long-term issue. | [R §3.8] [R §3.9] [R §3.10] [R 7] [R 27] [R 55] [R 56] [V 1] |
| 4 | **Expectancy-curve miscalibration** | On 1.5 million FIDE games, Sonas found results behave as if the gap were about 5/6 of the nominal gap; under the capped table, 700-point favourites scored 98–100 % against an expected 92 %; after the cap was lifted for 2650+ players their expected score "can now be as high as 99 % or even 100 %". | [R §3.5] [R 44] [R 46] [R 47] |

Two things are modelled but are **not headline targets**: the colour advantage (White scores about 54–55 %, worth about 35 rating points in Sonas's 2002 study, but pairing rules keep colour counts near even [R §3.7] [R 51]) and draws (draw rates rise steeply with level; modelling them improves forecasts and manipulation detection but barely moves published ratings [R §3.6] [R 48] [R 49]). Out of scope: the gap between online and over-the-board ratings [R §3.12] and engine-based "intrinsic" ratings [R §4].

---

## 3 Design principles

### 3(a) What stays constant across every style of play

1. **One core skill per player.** A player has one underlying strength, θ, shared across standard, rapid and blitz; style-specific differences are offsets from it (section 7).
2. **A forward-only published number on today's scale.** The rating a player sees moves only forward, only in months in which the player plays, and a 2500 today means what a 2500 meant last month. No retroactive revision, no one-off compressions, no jump at adoption.
3. **Every change explainable and hand-checkable.** Each change decomposes into named terms (expected score read from a published table, the player's printed K_i, colour, any junior compensation, the month's adjustment) that a player or arbiter can recompute from published inputs with a calculator.
4. **Deterministic and open-source.** Same inputs, same outputs, on any machine; code, test vectors, the yearly table and the monthly parameter file are public.
5. **Parameters re-estimated with published annual change caps.** The model is refitted each month, but no published parameter may move by more than a published cap per year.
6. **Every point accounted for.** A monthly ledger states where rating points were created, destroyed and moved (section 5) [T6].

### 3(b) What diverges by style

- **Per-time-control offsets** δ_tc: a player's rapid or blitz strength is θ plus a shrunken offset (section 7).
- **An expected-score function per time control:** its slope κ_tc, its colour term η_tc and its draw parameters α_tc and β_tc are estimated separately for standard, rapid and blitz, because White's edge is smaller in rapid than in classical (about 53 % against 54 % [R §3.7] [R 86]) and draw propensity differs by level and style [R §3.6] [T3].
- **Volatility per time control:** how fast skill may move month to month is estimated separately for each style [T2].

### 3(c) The eight adoptability requirements

The research report sets eight requirements for an official rating [R §7]; this design meets each as follows.

| # | Requirement | Met by |
|---|---|---|
| 1 | Determinism and reproducibility | Exact decimal arithmetic with one rounding step, today's rounding (§8.3.4 [V 1]), versioned parameters, identical output from identical TRF input [T4] |
| 2 | Transparency | A yearly lookup table and a monthly parameter file, both public and versioned [T7] |
| 3 | Auditability | A per-game breakdown published with every change, and a monthly points ledger [T6] |
| 4 | Explainability | Model influence enters only through six named channels (section 4), each a labelled line on the breakdown |
| 5 | Open-source code with test vectors | Apache-2.0 code, CC BY 4.0 documents, test vectors from FIDE's calculator and monthly lists |
| 6 | Governance | The QC signs the parameter file; Council approves changes to caps or formula; public comment before changes (section 9) |
| 7 | Fairness and bias monitoring | Residuals by federation, age, sex, rating band and colour reported monthly [T8] |
| 8 | Manipulation resistance | No cliffs; K from uncertainty; adjustments paid per active player, never per game; anomaly monitoring; adversarial simulations [T9] |

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
   │      colour and level-dependent draws; age-dependent drift; rolling 36-month │
   │      fit, re-estimated monthly.                                              │
   │      OUTPUTS: posterior mean and SD per player · anchor-cohort drift ·       │
   │      federation miscalibration with its evidence · junior compensations.     │
   │      It never edits a published rating.                                      │
   └──────────────────────────────────────────────────────────────────────────────┘
                     │ yearly lookup table + monthly parameter file [T7] (public, versioned, capped)
                     ▼
   ┌──────────────────────────────────────────────────────────────────────────────┐
   │  L2  PUBLISHED RATING [T4]   forward-only, Elo-style, per game:              │
   │      R_i ← R_i + K_i · (S_i − E(x_i))                                        │
   │      Channels, each named, capped and published:                             │
   │        expected score (AR-1)             K from uncertainty (AR-2)           │
   │        monthly calibration adjustments (AR-3): global ON,                    │
   │          federation adjustment DISABLED pending evidence                     │
   │        junior compensation (AR-4)        seeds and inactivity (AR-5)         │
   │        the points ledger (AR-6)                                              │
   └──────────────────────────────────────────────────────────────────────────────┘
```

**Layer 0, the reference engine.** An exact implementation of the FIDE Rating Regulations effective 1 March 2024 as amended 1 October 2025 [V 1] and of the Rapid and Blitz Rating Regulations [V 2], verified against FIDE's calculator and sampled monthly lists. It is the credibility anchor: no repository found so far claims to reproduce today's list to the point [R §5]. Its specification is `docs/specs/SPEC-L0_fide-reference-engine_v0_1.md`.

**Layer 1, the model** [T2]. A dynamic paired-comparison model: each player has a shared skill θ that moves over time with an age-dependent drift, and a per-time-control offset δ_tc shrunk towards zero. Outcomes follow a Davidson-type model with a colour term and a draw term whose size depends on the level of the two players. It is refitted monthly on a rolling 36-month window in the style of Whole-History Rating, which beat Elo, Glicko and TrueSkill on 10.8 million Go games [R 11] [R 12], or of TrueSkill Through Time [R 10]. The scale is anchored to the published mean of an anchor cohort of stable adults, as US Chess does [R 22]. Outputs: a posterior mean θ̂_i and standard deviation σ_i for every player in every time control; the anchor-cohort drift; federation miscalibration estimates with their evidence; the compensation of each eligible junior. **It never edits a published rating.** The monthly refit is a laptop-scale job [R §7].

**Layer 2, the published rating** [T4]. Forward-only and Elo-style, on today's scale, updated per game by R_i ← R_i + K_i · (S_i − E(x_i)). Model influence enters only through six named channels, each published and capped:

- **Expected score (AR-1).** One calibrated function per time control turns the gap into an expected score, published yearly as a lookup table per level band, the successor to table 8.1.2 [V 1]. Colour is inside the gap. There are no 400- or 600-point caps and no clamps [T3].
- **K from uncertainty (AR-2).** A player's K_i is set by how uncertain the model is about that player, mapped onto today's range of K = 10, 20 and 40 (§8.3.3 [V 1]), and printed beside the rating in the monthly list, which already carries a K column (§7.1.2 [V 1]).
- **Monthly calibration adjustments (AR-3).** A small, capped global adjustment a_t is credited each month to every active player in that time control and posted to the rating in a month in which the player plays; it is derived from the drift of the anchor cohort. A federation adjustment a_{f,t} uses the same mechanism per federation and ships DISABLED (a_{f,t} = 0) until a backtest on FIDE's own game data shows that federation miscalibration is stable and predictive out of sample.
- **Junior compensation (AR-4).** Against a junior whom the model rates well above their published number, the opponent's expectation uses a compensated rating. The junior's own update uses published ratings only.
- **Seeds and inactivity (AR-5).** A newcomer's first rating is the model's estimate from their first games in all three time controls, replacing the two fictitious draws against 1800-rated opponents (§8.2.2 [V 1]). An inactive player's rating never decays; the model's uncertainty grows instead, so K_i is higher on return.
- **The points ledger (AR-6).** Every month, for each time control, a public statement of where points were created, destroyed and moved [T6].

**Why adjustments, not offsets inside the expectation.** Version 0.1 put the federation offset inside the expected score; the architect's review removed it, because an offset inside the expectation freezes the gap it measures: if the formula already credits an under-rated pool with 100 points, its players stop gaining from the wins that would lift them, and the list never converges. A capped monthly adjustment to players who play closes the measured gap over time, appears in the ledger and switches itself off. The per-game pool bonus of v0.1 went too: anything paid per game rewards extra or arranged games.

**The monthly cycle.** (1) Closing date, three days before the list date (§7.1.3 [V 1]): the TRF files are in. (2) Layer 0 produces the official list exactly as today; during the shadow period, Layer 2 produces a shadow list from the same input. (3) Layer 1 refits on the last 36 months and writes next month's parameter file, each value within its annual cap, with the ledger and the monitoring report. (4) The QC signs and publishes the list, the shadow list, the parameter file, the ledger and the report. (5) Next month's games are rated with the published file and the current table, hand-checkable from them.

---

## 5 The published rating in practice

**The update.** For each game, a player's rating changes by

> R_i ← R_i + K_i · (S_i − E(x_i))

where S_i is the score (1, ½, 0), E(x_i) the expected score read from the published table for the time control and level band, and K_i the player's printed development coefficient. Each game term is computed exactly from the printed K_i (one decimal) and the table value (three decimals); the terms are summed over the rating period together with the month's adjustment and rounded once, exactly as today: nearest whole number, 0.5 away from zero (§8.3.4 [V 1]). The exact rules are in [T4].

**The gap.** x_i is the player's rating minus the opponent's rating for expectation, plus the colour term η_tc for White and minus it for Black (PROVISIONAL η_tc: 35 points standard, 25 rapid, 25 blitz). Colour is inside the expectation and nowhere else, so a surplus of Whites is charged game by game and never accumulates [T3]. The opponent's rating for expectation is the published rating, plus the published compensation c_j when the opponent is an eligible junior (section 6). There is no cap on the gap, no clamp and no exemption at any level; the function is continuous, and the two players' expectations sum to one whenever no compensation applies [T5].

**The table arbiters use.** The expected-score function is published once a year as a lookup table per time control, with one block per level band of 200 points (the level being the whole-number part of the mean of the two published ratings) and one three-decimal value for every whole-number gap from 0 to 1500; for a negative gap the arbiter uses 1 − E [T3] [T7]. The table is normative and the parameter file documents the function that generated it; the QC extends the table whenever a list in force makes a larger gap possible. It is the successor to table 8.1.2 [V 1], and every figure in the worked examples is read from it. Bands exist because strong players draw more [R §3.6] [R 48]. PROVISIONAL slope κ_tc = 1.00 for all three time controls; the draw parameters α_tc and β_tc are tabulated in [T7].

**K from uncertainty.** K_i maps the model's posterior standard deviation σ_i for the player in that time control onto today's range:

> K_i = K_min + (K_max − K_min) · min(1, (σ_i / σ_new)²)

with PROVISIONAL K_min = 10, K_max = 40 and σ_new = 100 points. A newcomer has K_i = 40; an established, active adult settles near today's K = 20 (PROVISIONAL σ_i about 55); a player at the top with a long record sits a little above today's K = 10 (today's values: §8.3.3 [V 1]); a player returning from years away has a higher K_i than when they left, because the model's uncertainty about them has grown. There is no switch at 30 games, at 2300, at 2400 or at age 18. K_i is published to one decimal beside the rating, in the K column the list already carries (§7.1.2 [V 1]), together with the compensated rating RX and the carried adjustment balance, so that any change, including one after an absence, is recomputable from the list, the table and the parameter file alone. One cap carries over from today: if K_i times the number of games n in the period exceeds 700, K_i is replaced for that period by the largest one-decimal value with K_i × n ≤ 700, in the spirit of today's rule (§8.3.3 [V 1]) [T4].

**The monthly adjustment.** Each month, every active player in a time control is credited with the same adjustment a_t for that time control, PROVISIONALLY capped at 1.5 points per month, derived from the gap between the anchor cohort's published mean and the model's estimate of it and closed at a PROVISIONAL gain of one sixth per month [T4] [T7]. The credit is posted to the rating only in a month in which the player plays a rated game, stops accruing while the player is inactive and is carried until their return, so a player who plays twelve games in one month and one who plays one game in each of twelve months receive the same amount. It is paid per player and never per game, so playing more games, or arranging them, earns nothing extra; a_t is computed from the month just closed and published with the list, so it cannot be timed. The federation adjustment a_{f,t} has the same structure and is DISABLED (set to zero) until the evidence test of section 9 is passed. Players who do not play receive nothing, so ratings still change only for players who play.

**The ledger.** Unequal K factors, newcomers, the floor and departures all create or destroy points, which is how the scale drifts [R §3.1] [R 5]. Layer 2 therefore publishes each month, per time control, where the points went: moved between players by results; created or destroyed by unequal K; paid as adjustments; created by junior compensation; entering with newcomers; leaving with players removed from the list below the floor. The analogy is a central bank publishing how much money it created and why. The exact accounting identity, which the published figures must satisfy to the tenth, is [T6].

**Worked example (hand-checkable).** The annex works through four cases [T10]; the first is reproduced here. An established adult, A, rated 1900, has White against a junior, J, whose published rating is 1500 but whom Layer 1 rates at 1850 confidently enough to pass the eligibility test of section 6, so J's rating for A's expectation is 1800 (the 350-point difference is capped at the PROVISIONAL c_cap of 300) while J's own expectation uses the published 1500 and 1900. A's printed K_i is 19.1 and J's is 40.0 (PROVISIONAL, from posterior standard deviations of 55 and 100). Under today's rules [V 1] the difference is 400, which is not "more than 400", so no cap applies; table 8.1.2 gives A an expectation of .92 with K = 20 and J an expectation of .08 with K = 40, and a draw costs A 8.4 points before rounding, the figure Ghita uses to explain how under-rated juniors drain established players [R 5]. The table below sets today's figures beside the Layer 2 figures for each result, computed from the PROVISIONAL parameters by the reference script.

| Result | A today: 20 × (S − .92) | J today: 40 × (S − .08) | A under Layer 2: 19.1 × (S − 0.656) | J under Layer 2: 40.0 × (S − 0.116) |
|---|---|---|---|---|
| A wins | +1.6 → **+2** | −3.2 → **−3** | +6.6 → **+7** | −4.6 → **−5** |
| Draw | −8.4 → **−8** | +16.8 → **+17** | −3.0 → **−3** | +15.4 → **+15** |
| J wins | −18.4 → **−18** | +36.8 → **+37** | −12.5 → **−13** | +35.4 → **+35** |

The adult is no longer drained for drawing a junior who is really an 1850 player (−3 instead of −8) and is paid for beating one (+7 instead of +2); the junior's own update keeps today's form, K = 40 on published ratings: +15 for a draw and +35 for a win against +17 and +37 under today's table, because the calibrated function gives the lower-rated player a higher expectation at this gap (0.116 against .08); whether that trade is right is what the calibration backtest decides. The two expectations, 0.656 and 0.116, do not sum to one; the difference is the compensation, and the ledger prints it as 19.1 × (0.884 − 0.656) = 4.4 points created in this game whatever the result [T6] [T10].

---

## 6 Where points enter and leave

| Topic | Today (transcribed [V 1] [V 2]) | Proposed | Why |
|---|---|---|---|
| **Newcomers** | Published after at least 5 games against rated opponents, pooled over up to 26 months; Ra = average of rated opponents plus two hypothetical 1800-rated opponents scored as draws; Ru = Ra + dp from table 8.1.1, rounded, maximum 2200; a zero score in the first event is disregarded (§7.1.4, §8.2) | Same 5-game, 26-month threshold. The seed is the Layer 1 estimate for the player on the published scale, drawing on their games in all three time controls, rounded, within the 1400 floor and the 2200 maximum (AR-5) [T4]; no phantom opponents. The newcomer starts with the model's uncertainty, hence K_i near 40, and the ledger records the points that enter with them. | The two phantom draws pull every newcomer towards 1800 whatever their age or pool and were a one-off repair for deflation [R 35] [R 39]; a seed that uses everything known about the player, including rapid and blitz games, enters closer to the truth, which is the first of the three deflation channels [R Recommendations]. |
| **Juniors** | K = 40 until the end of the year of the 18th birthday while rated under 2300; otherwise standard rules (§8.3.3) | A junior (list year minus year of birth on the FIDE list at most 19) with at least 10 rated games in the time control, against at least 5 opponents in at least 3 events (PROVISIONAL), whom Layer 1 rates, on the published scale, above their published rating by more than τ (PROVISIONAL 50 points) with posterior probability at least 0.90 carries a published compensation c_j, capped at c_cap (PROVISIONAL 300 points); the list prints the compensated rating beside the published one. It enters the opponent's expectation only; the junior's own update uses published ratings, so the compensation itself neither speeds nor slows the junior. It switches off by itself as the junior's rating catches up (AR-4) [T4]. | Juniors improve faster than K = 40 can track and were "undervalued by hundreds of points" after the pandemic freeze [R §3.3] [R 4]; the loss to the adult, not the junior's gain, is what deflates the pool [R 5] [R 39]. |
| **Floor** | Ratings below 1400 are shown as unrated on the next list; the player is thereafter treated as any unrated player (§7.2.1) | §7.2.1 is unchanged as a display rule: the list shows the player as unrated and their games are not rated for opponents, as today. Layer 1 keeps estimating the player, so their games still inform the pool, and when the player re-qualifies under §7.1.4 the seed is the Layer 1 estimate, not two phantom draws. The ledger records the points leaving through the floor (AR-5) [T4]. | Today's rule splits players into rated and unrated, creates an artificial pile-up at 1400 and makes 1400–1600 ratings "highly unreliable" [R 2] [R 4]; re-entry through the newcomer rule injects points at the bottom. |
| **Inactivity** | A player commences inactivity after one year without a rated game and regains activity after one game (§7.2.2); ratings do not decay | No rating decays. The model's uncertainty about an inactive player grows, so K_i is higher on return and the first games move the rating faster. No adjustment is earned while inactive (AR-5). The inactive flag stays; eligibility rules that depend on rating are FIDE's to set and are outside these regulations. | About 40 % of listed players have not played since before the pandemic [R 5] [R 56]; a frozen rating with a frozen K misstates the uncertainty of a returning player; Glicko-style uncertainty growth is the standard remedy [R §6] [R 64]. |
| **Monthly adjustments** | No rule; the level of the scale is left to the arithmetic of K factors and seeds | A global adjustment a_t per time control, credited to every active player and posted in a month in which the player plays, capped (PROVISIONAL 1.5 points per month), derived from the anchor cohort's drift and signed in either direction (whether a negative a_t should be allowed is an open policy question for the QC). A federation adjustment a_{f,t} with the same structure, DISABLED until the evidence test of section 9 is passed (AR-3) [T4] [T7]. | The median active player still loses about 16 points a year after the 2024 reform [R 5]; US Chess holds its level with a bonus mechanism it re-tuned in 2023 and 2025 because ratings "continue[d] to deflate" [R 29] [R 32]; a per-player monthly payment does the same job without rewarding extra games. |

---

## 7 One framework across time controls

**The structure.** skill_tc = θ + δ_tc. One shared skill per player, θ, plus an offset for each time control, shrunk towards zero with a time-control-specific variance [T2]. A rapid specialist can be stronger at rapid without the system pretending they are a different person. Each time control keeps its own expected-score function, colour term, draw parameters and volatility, because White's edge and draw rates differ by style [R §3.7] [R §8].

**Shrinkage.** With few games in a style, δ_tc stays near zero and the player's strength there is essentially θ; with many, δ_tc is estimated from them. The strength of the shrinkage, ω_tc, is fitted from data (open question 11.4) [R §8].

**What a rapid game tells the classical rating.** In Layer 1 every game in every style updates θ and moves δ_rapid more. In Layer 2, the classical published rating is touched by a rapid game only through the channels: the seed of a newcomer to the classical list draws on their rapid history (AR-5); the compensation for a junior opponent draws on the junior's θ, which rapid games inform (AR-4). No rapid result ever enters the classical per-game formula directly, and the three published lists remain separate and forward-only.

**What FIDE does today, and why it argues for one framework.** FIDE's two rating chapters share tables, K rules and rounding [V 2] but have drifted apart on the rule that matters most at the top. The standard chapter reads: "Effective from 1 October 2025: A difference in rating of more than 400 points shall be counted for rating purposes as though it were a difference of 400 points for players rated below 2650. For players rated 2650 and above, the difference between ratings shall be used in all cases" [V 1]. The rapid and blitz chapter reads: "A difference in rating of more than 400 points shall be counted for rating purposes as though it were a difference of 400 points." It has no 2650 exemption, and continues: "Effective from 1 December 2024: Games played between players with a rating difference of 600 points or more shall not be rated if at least one of the players is rated above 2600 on the relevant list." [V 2]. The same top-level pairing is rated on the full gap in standard, on a capped gap in rapid and blitz, and beyond 600 points not at all. Each rule answered a real problem, but separately amended rule sets drift apart and every amendment adds a threshold. The remedy is one expected-score function in all three time controls, with no caps or exclusions, whose parameters differ by style only where the data say so [T3]. The one cross-list rule in today's chapters, that an unrated player with a standard rating uses it in rapid and blitz (§7.2.1 of the rapid and blitz chapter [V 2]), becomes a special case of the shared skill θ.

---

## 8 Proof plan

**Protocol.** Rolling-origin evaluation: fit on games up to month t, forecast month t+1, score, roll forward. The match schedule is never a feature, since schedule information drove much of the 2011 Kaggle winner's edge, which is not legitimate for an official rating [R 9] [R §9]. Layer 0 (today's rules, exactly) is the baseline on every metric. Metrics, holdout design, anchor-cohort definition and success thresholds are pre-registered in [T8] before any FIDE data is seen.

**Metrics** [T8]. Three-outcome log-loss, ranked probability score and Brier score, with calibration by gap, band, colour, time control and federation pair; anchor-cohort drift, as Glickman does for US Chess [R 22]; cross-federation residuals; newcomer convergence; points gained per unit of effort by simulated adversaries; hand-checkability of published changes; the ledger identity.

**The simulator** [T9]. Players with known true strengths, age-dependent improvement, federation-clustered pairings, Swiss and round-robin events [R §3.13], entries and exits; Layer 0 and Layer 2 run side by side on the same simulated games, so recovery of true strengths, drift and the yield of every adversary strategy are measured exactly.

**Success criteria (PROVISIONAL thresholds, fixed in [T8] before the backtest is run).**

| Criterion | PROVISIONAL threshold |
|---|---|
| Three-outcome log-loss, ranked probability score and Brier score on held-out months | log-loss at least 2 % better than Layer 0 in every rating band; all three better than Layer 0 with a bootstrap interval excluding zero |
| Calibration | slope of actual on expected score within 0.95–1.05 in every gap bin up to 1000 points; the yearly table is published only if this holds |
| Anchor-cohort drift | within ±2 points per year (the report's post-reform figure is about −16 per year [R 5]) |
| Cross-federation residual | within ±10 points for every federation with at least 1,000 cross-border games in the window |
| Newcomer convergence (simulation) | median absolute error below 50 points within 15 games |
| Adversarial simulations | no strategy gains more than Layer 0 allows, and results against much lower-rated opponents yield no more points per game than results against equally rated opponents |
| Hand-checkability | 100 % of a random sample of published changes recomputed exactly from the breakdown, the table and the parameter file |
| Ledger | the published ledger satisfies the identity of [T6] to the tenth in every month |

**Data plan.** (1) Development: the Lichess open database, CC0 [V 4], about 85–100 million games a month for 2024–2026 [V 4], with the broadcast archive (CC BY-SA 4.0 [V 4]) as the over-the-board slice; online data calibrates methods, not FIDE parameters. (2) Player panel: FIDE's monthly lists, standard, rapid and blitz, archived monthly since February 2015 [V 3]; they carry no licence, so the project downloads and analyses them and never redistributes them [V 3]. (3) The formal request: FIDE's TRF archive, the game-level record that arbiters submit under §9.1 [V 1], under a data-sharing agreement (stage 2); the only dataset that can settle the federation question [R §5].

---

## 9 Governance and the calculator FIDE can run

**Plain statement.** This is the "AI calculator FIDE can run" only in this sense: a statistical model with machine-estimated parameters, re-estimated monthly from games, feeding a published per-game formula; it is not a neural network and not a black box. Anyone with the yearly table, the monthly parameter file and the game record can recompute any rating change by hand; the model's only power is to set the numbers in those two files, within caps, in public.

**Two published files** [T7]. The yearly lookup table per time control succeeds table 8.1.2 and changes at most once a year. The monthly parameter file, published with every list and versioned, holds per time control the function parameters behind the table (κ_tc, η_tc, α_tc, β_tc), the K mapping, the adjustment a_t with its gain, cap and anchor-cohort means, the federation adjustments a_{f,t} (all zero while disabled) and every eligible junior's compensation c_j. While the federation adjustment is disabled, federation-level estimates go to the QC only, and the public file carries aggregate connectivity diagnostics without per-federation figures. Each player's K_i and compensated rating RX are printed in the list itself.

**Annual change caps.** No published parameter moves by more than a published cap per calendar year; the PROVISIONAL caps are listed beside the values in [T7] (for example ±0.05 on the slope κ_tc, ±5 on the colour term, ±2 on K_min and K_max, ±0.5 on the adjustment cap).

**Ownership and process.** The QC owns and signs the parameter file and the caps; the FIDE Council approves changes to caps or to the formula; every change to the formula or the caps goes through a public comment period, with the 2023 consultation (over 150 comments [R 18] [R 19]) as the model. Rollback rule: if any monitoring threshold of [T8] is breached for two consecutive months, the file reverts to the last compliant version while the QC investigates; if the ledger identity of [T6] fails in any month, the list is held until it is reconciled. The federation adjustment is enabled only by Council decision, after public comment, consultation with the federation concerned and a backtest on FIDE's own game data showing federation miscalibration stable and predictive out of sample; it uses cross-federation games only, attaches to a federation's pool, not to any player, and stays capped and reversible.

**The properties the design guarantees** [T5]. P1 Forward-only: a published rating depends only on earlier lists and the games of the period, and no list is ever recomputed. P2 Bounded change: at most K_i per game, and per period at most 700 points plus the capped adjustment. P3 Continuity: no caps, clamps or bracket switches; the expected score and K_i are continuous in their inputs. P4 Unbiasedness: when ratings are accurate the expected change from any pairing is zero, so farming earns nothing. P5 Ledger completeness: every point created, moved or lost appears in one ledger line and the lines sum exactly. P6 Determinism: exact decimal arithmetic and today's rounding give identical published output on any machine; the model fit behind the parameter file is reproducible to a published tolerance.

**No exploitable cliffs.** Today's rules contain discontinuities: the 400-point cap below 2650 and none above it; the K switches at 30 games, at 2300 for juniors and permanently at 2400; the floor rule that re-seeds a player through two phantom 1800 draws; and a different cap regime in rapid and blitz [V 1] [V 2] [R 55]. The design contains no caps, clamps or bracket switches. Its only thresholds, the junior eligibility test and the activity test for the monthly adjustment, enter through capped, published quantities (c_j and a_t), so crossing one changes a published number by a bounded, visible amount and never changes the value of every later game.

**Anomaly monitoring.** Each month the engine publishes, without names, aggregate indicators: clusters of players whose mutual results are far from forecast (collusion and arranged draws, which the draw model makes detectable [R §3.6]); a concentration index, the share of a player's gains from opponents rated more than 400 points below them; returns from inactivity that coincide with unusual results; and, reported to the QC only while the federation adjustment is disabled, federation-level estimates that move faster than their cap would allow. Named cases go to FIDE's existing investigation and appeal procedures [R §3.9] (NOT VERIFIED in this project); the engine flags, it does not judge.

---

## 10 Roadmap

Nothing in this proposal touches the title and norm regulations. Whether any norm arithmetic that relies on table 8.1.2 would need to change is NOT VERIFIED and is for the QC to assess; the shadow list answers it with numbers before any decision [T11].

| Stage [T11] | Deliverable | Gate to the next stage |
|---|---|---|
| **1. Layer 0 replica, now** | The reference engine for standard, rapid and blitz, test-vector verified against FIDE's calculator and sampled monthly lists; the simulator [T9]; the Lichess backtest harness (CC0 data [V 4]) and the first rolling-origin results [T8]; this proposal at v1.0 with code and test vectors, for QC and public comment | L0 reproduces sampled players' monthly changes exactly; L2 beats L0 on the Lichess backtest on every metric of [T8]; comments triaged with no unresolved correctness finding |
| **2. Shadow list, twelve months** | With the TRF archive under a data-sharing agreement, pitched as a digital-transformation deliverable [R §2] [R 28]: a shadow list computed in parallel with every official list and published beside it, with the parameter file, the ledger and the monitoring report; no effect on any rating, title or norm. Precedent: the parallel list during the 2008–2011 K-factor trial [R §2] [R 16] | Twelve clean months; the pre-registered criteria of [T8] met on FIDE data; the QC's assessment of the title and norm question |
| **3. Pilot federation** | One federation's players rated under Layer 2 for a domestic list, with the official list unchanged; monthly reports; the federation adjustment still disabled | Pilot report; QC recommendation |
| **4. Council decision** | QC recommendation to the FIDE Council on adoption, scope and timing; adoption, if any, with no one-off jump: any gap between the shadow and official lists closes through the capped monthly adjustments | Council decision |

---

## 11 Open questions and decisions needed

**Open questions the research could not settle** ([R Open questions], restated with the step that answers each):

1. What share of FIDE-rated games is within one federation, by band and year? Needs the TRF archive (stage 2).
2. Are federation offsets stable and causal, or artefacts of who travels? Needs the TRF archive and a multivariate analysis (stage 2); the federation adjustment stays disabled until this is answered.
3. What were draw rates and White's score in FIDE play in 2024–2026, by level and time control? Lichess broadcasts first (stage 1), FIDE data later.
4. How strongly do classical, rapid and blitz strength correlate for FIDE players today? Estimable from the combined monthly list in stage 1 [V 3].
5. How large is per-player colour-count imbalance, and does it move ratings? Stage 1 on broadcasts; stage 2 on FIDE data.
6. Will the QC under the new administration accept a model-driven correction layer, and would title-norm arithmetic need to change? The shadow list answers the second with numbers; the first is for the QC (section 10).
7. Does any exact reproduction of FIDE's calculator exist? None found [R §5]; Layer 0 is that deliverable.

**Decisions needed from the founder** (numbered for reply). The technical decisions of v0.1 are resolved in `docs/decisions/D-0002_elo-1-decision-triage.md` and `docs/decisions/D-0003_architecture-revisions-v0.2.md`; only these remain.

1. **Publication of model estimates beyond the technical minimum.** The minimum is fixed: every eligible junior's compensation c_j and every player's K_i are published, because arbiters need them to recompute an expectation. Whether each player's θ̂_i and σ_i are public, visible only to the player, or QC-only remains open.
2. **Pilot federation.** Which federation to approach for stage 3, and when.
3. **Data handling and the TRF request.** FIDE lists carry no licence [V 3]; confirm the policy "download, analyse, never redistribute" and the wording of the stage 2 request.
4. **Repository name and visibility.** The operator kept `Chess-ELO-Rating` and public visibility on 2026-10-09 (`docs/decisions/D-0001_repo-licence-visibility-language.md`). Revisit before v1.0 publication?
5. **Repository description.** Confirm the current description text or revert it.

---

## Appendix A Mathematics

Moved to the technical annex: the notation [T1], the Layer 1 model [T2] and the expected-score function [T3].
The Layer 2 rules [T4] and the properties P1–P6 [T5].
The ledger identity [T6].

---

## Appendix B Mapping to assumptions A1–A7

The research report tags each problem with the assumptions A1–A7 it breaks ([R §1], [R §3], "Ranked problem table"). The list below is the architect's canonical one (`docs/decisions/D-0003_architecture-revisions-v0.2.md`). "What breaks it" names the report sections; "Handled by" names the architecture revision and the annex section.

| Assumption | Statement | What breaks it (report section) | Handled by (AR-n and annex section) |
|---|---|---|---|
| A1 | One fixed curve turns any rating gap into a forecast, at every rating level. | §3.5 forecast accuracy across gaps; problem 4 | AR-1 calibrated expected-score function per time control and level band [T3] |
| A2 | A draw is half a win, and colour does not matter. | §3.6 draws; §3.7 colour; problems 8, 9 | AR-1 colour term η_tc inside the gap and level-dependent draw term [T3]; L1 outcome model [T2] |
| A3 | Every game moves a rating by a fixed step, set by brackets. | §3.4 K-factor and bracket edges; §3.1 deflation; problems 1, 6 | AR-2 K_i from the posterior uncertainty, no brackets [T4] |
| A4 | Playing strength changes slowly. | §3.3 juniors; §3.11 COVID-era effects; §3.1 deflation; problems 1, 5 | AR-4 junior compensation [T4]; age-dependent drift in L1 [T2] |
| A5 | The pool is well connected: everyone is indirectly compared with everyone. | §3.2 federation isolation; §3.13 matchmaking; problems 2, 12 | AR-3 federation adjustment, disabled pending evidence, with connectivity diagnostics [T2] [T4]; simulator tests of isolated pools [T9] |
| A6 | Rating points are conserved, so the scale holds steady. | §3.1 deflation; §3.10 inactivity; problems 1, 7 | AR-3 global adjustment from anchor drift [T4]; AR-5 seeds [T4]; AR-6 ledger [T6] |
| A7 | Players do not choose their games to protect or game their rating. | §3.8 protection and game selection; §3.9 manipulation; §3.10 inactivity; problems 3, 7, 10 | AR-1 and AR-2 remove the cliffs [T5]; AR-3 paid per active player, never per game [T4]; AR-5 uncertainty growth on inactivity [T4]; anomaly monitoring and adversarial simulations [T9] |

The report's one-line statement of the model's assumptions, "one latent strength per player, one fixed link curve, no colour or draw structure, and slowly varying strength" [R §1], is covered by A1, A2 and A4; "one latent strength per player" is kept by this design (section 3(a)) and refined by the time-control offsets of section 7.

---

## Appendix C Sources

Every source from the research report's numbered list, with its verification status from the Phase 1 sweep of 2026-10-09 (`docs/research/VERIFICATION_2026-10-09.md`). VERIFIED means the page was fetched on that date and the text relied on was transcribed; NOT VERIFIED means the proposal relies on the research report's reading of it. Sources cited in this draft are those that appear as `[R n]` above.

| # | Source (title as listed in the report) | URL | Status |
|---|---|---|---|
| 1 | B. PERMANENT COMMISSIONS / 02. FIDE Rating Regulations (Qualification Commission) / FIDE Rating Regulations effective from 1 March 2024 / FIDE Handbook | https://handbook.fide.com/chapter/B022024 | VERIFIED (handbook chapter fetched 2026-10-09T14:28:34Z; §7, §8 transcribed, [V 1]) |
| 2 | FIDE Adjusts Ratings For 350,000 Players In Massive Change - Chess.com | https://www.chess.com/news/view/fide-adds-rating-points-to-more-than-300-000-players | NOT VERIFIED |
| 3 | FIDE Ratings Revisited • FRBE-KBSB-KSB | https://blog.frbe-kbsb-ksb.be/blog/fide-ratings-revisited/ | NOT VERIFIED |
| 4 | FIDE Ratings Revisited - by Vlad Ghita | https://vladchess.substack.com/p/fide-ratings-revisited | NOT VERIFIED |
| 5 | The Rating Revolution — Vlad Ghita | https://vladchess.com/rating-revolution | NOT VERIFIED |
| 6 | Why chess ratings don't mean what they used to | https://vladchess.substack.com/p/why-chess-ratings-dont-mean-what | NOT VERIFIED |
| 7 | FIDE Scraps 400-Point Rule For 2650+ Players, 'Triggered By Nakamura' - Chess.com | https://www.chess.com/news/view/fide-introduces-hikaru-rule-from-october | NOT VERIFIED |
| 8 | Candidates Tournament 2026 | https://en.wikipedia.org/wiki/Candidates_Tournament_2026 | NOT VERIFIED |
| 9 | Tim Salimans: How I won the Deloitte/FIDE Chess Rating Challenge | http://www.chessmetrics.com/KaggleComp/1-TimSalimans.pdf | NOT VERIFIED |
| 10 | \[PDF\] TrueSkill Through Time: Revisiting the History of Chess | https://www.semanticscholar.org/paper/TrueSkill-Through-Time:-Revisiting-the-History-of-Dangauthier-Herbrich/fe8616a7b260472ae1b61d83f3f50fd5662a1dcc | NOT VERIFIED |
| 11 | Whole-History Rating: A Bayesian Rating | https://www.remi-coulom.fr/WHR/WHR.pdf | NOT VERIFIED |
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
| 22 | US Chess Ratings Workshop July 18, 2024 Mark E. Glickman, | https://new.uschess.org/sites/default/files/media/documents/7-18-2024-ratings-workshop-2024.pdf | NOT VERIFIED |
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
| 35 | 1 Compression and Calculation Improvements: Supplemental Report | https://www.fide.com/docs/presentations/Sonas%20Supplemental%20Report.pdf | NOT VERIFIED |
| 36 | Universal Rating System | https://en.wikipedia.org/wiki/Universal_Rating_System | NOT VERIFIED |
| 37 | 1 Sonas Proposal: Repairing the FIDE Standard Elo rating system | https://www.fide.com/docs/presentations/Sonas%20Proposal%20-%20Repairing%20the%20FIDE%20Standard%20Elo%20Rating%20System.pdf | NOT VERIFIED |
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
| 60 | The Deloitte/FIDE Chess Rating Challenge | https://en.chessbase.com/post/the-deloitte-fide-che-rating-challenge | NOT VERIFIED |
| 61 | How I won the "Chess Ratings - Elo vs the Rest of the World" Competition | https://arxiv.org/pdf/1012.4571 | NOT VERIFIED |
| 62 | Sonas: The Deloitte/FIDE Chess Rating Challenge | https://en.chessbase.com/post/sonas-the-deloitte-fide-che-rating-challenge | NOT VERIFIED |
| 63 | Could World Chess Ratings be decided by the ‘Stephenson System’? | https://medium.com/kaggle-blog/could-world-chess-ratings-be-decided-by-the-stephenson-system-2fba2715cf34 | NOT VERIFIED |
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

Moved to the technical annex: the expected-score function and its comparison with table 8.1.2 [T3]; the Layer 2 rules, caps and the cliff-by-cliff replacement table [T4].

---

## Appendix E Further worked examples

Moved to the technical annex: all worked examples, hand-checkable against the PROVISIONAL parameters, are in [T10].

---

*End of DRAFT v0.2. Status line repeated: DRAFT v0.2 — not for publication.*
