# Modernising the FIDE Elo Rating System: an exact reference implementation plus an explainable correction layer

**Status: DRAFT v0.1 — not for publication**
Author: The Zugzwang Authors · Licence: CC BY 4.0 (`docs/LICENSE-docs.md`) · Date: 2026-10-09
Audience: FIDE's Qualification Commission (QC) and the chess public. Plain language first; the mathematics is in Appendix A.

How to read the citations. `[R §x]` points to a section of the research report `docs/research/ELO-RESEARCH_v1_0.md`; `[R n]` to the report's numbered source n; `[V k]` to item k of the primary-source verification sweep `docs/research/VERIFICATION_2026-10-09.md`. Every number in this document traces to one of those two files. Every parameter value is marked PROVISIONAL: it is a placeholder to be replaced by an estimate from data.

---

## 1 Summary

**The problem.** The FIDE rating is the world's reference number for chess strength, and it is drifting. After the March 2024 reset the median active player still loses about 16 points a year [R 5]. The same number means different strengths in different countries: one study finds offsets from about +101 (Vietnam) to about −64 (Switzerland, Austria) [R 6]. The 400-point cap created an arbitrage at the top that FIDE patched in October 2025 [R 7] [V 1], and the expectancy table over-predicts favourites at large gaps [R 44]. Every fix so far has been a one-off patch.

**The proposal, in three sentences.** Publish an exact, open-source reference implementation of FIDE's current rules, so anyone can reproduce every list exactly. Run behind it a dynamic statistical model, re-estimated monthly from the last 36 months of games, which learns what Elo assumes away: how fast juniors improve, how far federations have drifted apart, how large White's edge is, how often strong players draw. Keep the published rating a forward-only, Elo-style number on today's scale, updated per game by a formula a player can check by hand, with the model influencing it only through four named, capped, published channels.

**The ask of FIDE.** Review this design through the QC with public comment, as in 2023; provide the tournament-report (TRF) game archive under a data agreement for backtesting; and pilot the correction layer in parallel with one federation's list. Nothing here edits a published rating retroactively, and nothing is a black box.

---

## 2 What the chess world wants fixed

The research report ranks the complaints by community demand, strength of evidence and fixability ("Ranked problem table", [R Recommendations]). The four headline targets, in order:

| Rank | Target | What the evidence says | Pointer |
|---|---|---|---|
| 1 | **Deflation and junior lag** | Sonas (2023, for FIDE) found "extreme rating deflation": players rated 1000 to 2400 spanned only about 1000 points of real strength, because newcomers and juniors enter below their strength and drain points from established players. After the 2024 reform the average rating still fell about 1 point a month, the median active player lost 16 points a year instead of 26, and players pile up at the 1400 floor. FIDE acknowledged the problem in the 2023 consultation and the 2024 reform. | [R §3.1] [R §3.3] [R 3] [R 4] [R 5] [R 37] [R 39] |
| 2 | **Federation isolation** | Most games are domestic, so pools drift apart. Ghita's 2026 study of cross-border games estimates offsets from about +101 (Vietnam) to about −64 (Switzerland, Austria), with gaps that "can exceed 160 Elo"; there is no official fix. Caveat: independent, not peer-reviewed; the "over 80 % domestic" figure is unverified. | [R §3.2] [R 5] [R 6] |
| 3 | **Top-level protection, farming and inactivity** | The 400-point cap let a 2800 player bank points against 2250 opponents; FIDE lifted the cap for 2650+ players from 1 October 2025. Ratings never decay, about 40 % of listed players have not played since before the pandemic, and FIDE's then-president called inactivity the next long-term issue. | [R §3.8] [R §3.9] [R §3.10] [R 7] [R 27] [R 55] [R 56] [V 1] |
| 4 | **Expectancy-curve miscalibration** | On 1.5 million FIDE games, Sonas found results behave as if the gap were about 5/6 of the nominal gap; under the capped table, 700-point favourites scored 98–100 % against an expected 92 %; after the cap was lifted for 2650+ players their expected score "can now be as high as 99 % or even 100 %". | [R §3.5] [R 44] [R 46] [R 47] |

Two things are modelled but are **not headline targets**: the colour advantage (White scores about 54–55 %, worth about 35 rating points in Sonas's 2002 study, but pairing rules keep colour counts near even [R §3.7] [R 51]) and draws (draw rates rise steeply with level; modelling them improves forecasts and manipulation detection but barely moves published ratings [R §3.6] [R 48] [R 49]). Two things are out of scope: the gap between online and over-the-board ratings, a communication problem rather than a FIDE design target [R §3.12], and engine-based "intrinsic" ratings, excluded for cost and transparency [R §4].

---

## 3 Design principles

### 3(a) What stays constant across every style of play

1. **One core skill per player.** A player has one underlying strength, θ, shared across standard, rapid and blitz; style-specific differences are offsets from it (section 7).
2. **A forward-only published number on today's scale.** The rating a player sees moves only forward, only through games, and a 2500 today means what a 2500 meant last month. No retroactive revision, no one-off compressions.
3. **Every correction explainable and hand-checkable.** Each change decomposes into named terms (expected score, K, colour, the four channels) that a player or arbiter can recompute from published inputs with a calculator.
4. **Deterministic and open-source.** Same inputs, same outputs, on any machine; code, test vectors and parameter files are public.
5. **Parameters re-estimated monthly with published annual change caps.** The model is refitted each month, but no published parameter may move by more than a published cap per year.

### 3(b) What diverges by style

- **Per-time-control offsets** δ_tc: a player's rapid or blitz strength is θ plus a shrunken offset (section 7).
- **Colour and draw parameters per time control:** White's edge is smaller in rapid than in classical (about 53 % against 54 % [R §3.7] [R 86]); draw propensity differs by level and style [R §3.6].
- **Volatility per time control:** how fast skill may move month to month is estimated separately for each style.

### 3(c) The eight adoptability requirements

The research report sets eight requirements for an official rating [R §7]; this design meets each as follows.

| # | Requirement | Met by |
|---|---|---|
| 1 | Determinism and reproducibility | Fixed-precision arithmetic, today's rounding (§8.3.4 [V 1]), versioned parameters, identical output from identical TRF input |
| 2 | Transparency | Every parameter in a public, versioned monthly file (section 9) |
| 3 | Auditability | A per-game breakdown published with every change (section 5) |
| 4 | Explainability | Corrections enter only through four named channels, each a labelled line on the breakdown |
| 5 | Open-source code with test vectors | Apache-2.0 code, CC BY 4.0 documents, test vectors from FIDE's calculator and monthly lists |
| 6 | Governance | QC owns the parameters; Council approves; public comment before changes (section 9) |
| 7 | Fairness and bias monitoring | Residuals by federation, age, sex, rating band and colour reported monthly (section 8) |
| 8 | Manipulation resistance | No cliffs; uncertainty-weighted K; anomaly monitoring; adversarial simulations (sections 5, 8, 9) |

---

## 4 The system: three layers

```
             TRF files from arbiters (monthly, §9.1)              Monthly list snapshot
                     │                                                  │
                     ▼                                                  ▼
   ┌──────────────────────────────────────────────────────────────────────────────┐
   │  L0  REFERENCE ENGINE  — exact FIDE rules (standard, rapid, blitz)           │
   │      tables 8.1.1 / 8.1.2, 400-point rule, K rules, rounding, newcomers,     │
   │      floor, inactivity. Test-vector verified. Produces today's list exactly. │
   └──────────────────────────────────────────────────────────────────────────────┘
                     │ games + lists (last 36 months)
                     ▼
   ┌──────────────────────────────────────────────────────────────────────────────┐
   │  L1  MODEL  — Bradley–Terry–Davidson; shared skill θ, offsets δ_tc,          │
   │      colour term, level-dependent draw term; time-varying skill fitted by    │
   │      Kalman smoothing or Whole-History Rating; re-estimated monthly.         │
   │      OUTPUTS: calibrated forecasts · pool and federation offsets ·           │
   │               junior improvement rates · global drift estimate               │
   │      It never edits a published rating.                                      │
   └──────────────────────────────────────────────────────────────────────────────┘
                     │ monthly parameter file (public, versioned, capped)
                     ▼
   ┌──────────────────────────────────────────────────────────────────────────────┐
   │  L2  PUBLISHED RATING  — forward-only, Elo-style, per game:                  │
   │      R += K_eff × (S − E) [+ pool bonus]                                      │
   │      Model influence enters ONLY through four channels:                      │
   │        C1 newcomer seeds   C2 junior-opponent compensation                   │
   │        C3 capped pool drift correction   C4 federation offsets (via E only)  │
   └──────────────────────────────────────────────────────────────────────────────┘
```

**Layer 0, the reference engine.** An exact implementation of the FIDE Rating Regulations effective 1 March 2024 as amended 1 October 2025 [V 1] and of the Rapid and Blitz Regulations [V 2], verified against FIDE's calculator and against sampled players across monthly lists. It is the credibility anchor: before proposing a change, we show we can reproduce today's list to the point, which no repository found so far claims to do [R §5]. Its specification is `docs/specs/SPEC-L0_fide-reference-engine_v0_1.md`.

**Layer 1, the model.** A dynamic paired-comparison model of the Bradley–Terry–Davidson family: each player has a shared skill θ that varies over time and a per-time-control offset δ_tc; the model has a colour term and a draw term whose size depends on the level of the two players. Time-varying skill is fitted by Kalman smoothing or by Whole-History Rating, the method that beat Elo, Glicko and TrueSkill on 10.8 million Go games [R 11] [R 12], on a rolling 36-month window, re-estimated monthly. Outputs: calibrated three-outcome forecasts; pool and federation offsets; junior improvement rates by age; a global drift estimate from an anchor cohort of stable adults, as US Chess does [R 22]. **It never edits a published rating directly.** It is a laptop-scale job: WHR adds a game in under a millisecond, and FIDE rates about 3 to 3.5 million standard games a year [R §7].

**Layer 2, the published rating.** Forward-only and Elo-style, on today's scale, updated per game by R += K_eff × (S − E). E comes from a calibrated logistic curve with a colour term and one consistent, cliff-free clamp replacing the 400-point rule and its 2650 exemption; K_eff is uncertainty-weighted, with smooth decay replacing the 40/20/10 brackets (section 5). Model influence enters only through four named, published channels:

- **C1 Newcomer seeds.** A newcomer's first rating is the model's estimate from their first games, with an age- and pool-informed prior, replacing the two fictitious draws against 1800-rated opponents (§8.2.2 [V 1]).
- **C2 Junior-opponent compensation.** Against a junior whose published rating lags their strength, your expected score is computed against the model's estimate of the junior. Losing to an under-rated junior stops being a tax on adults.
- **C3 Capped monthly pool-level drift correction.** A small per-game bonus, set monthly from the drift estimate and capped, holds the level of the pool. Precedent: the US Chess bonus constant, lowered in 2023 and 2025 because ratings "continue[d] to deflate" [R 29] [R 32].
- **C4 Federation offsets through expectations only.** In a cross-border game each side's expected score uses the other side's rating plus that federation's estimated offset; within a federation the offsets cancel. No rating is ever edited.

**The monthly cycle.** (1) Closing date, three days before the list date (§7.1.3 [V 1]): the TRF files are in. (2) Layer 0 produces the official list exactly as today; during the pilot, Layer 2 produces a shadow list from the same input. (3) Layer 1 refits on the last 36 months and writes next month's parameter file, each value within its annual cap. (4) The QC publishes the list, the shadow list, the parameter file and the monitoring report. (5) Next month's games are rated with the published file; any change can be checked by hand from the file and the breakdown.

---

## 5 The published rating in practice

**The formula.** For each game, a player's rating changes by

> ΔR = K_eff × (S − E) + b

where S is the score (1, ½, 0), E the expected score, K_eff the player's current development coefficient and b this month's pool bonus (channel C3, usually a fraction of a point). Changes are summed over the rating period and rounded exactly as today: nearest whole number, 0.5 away from zero (§8.3.4 [V 1]).

The expected score is a logistic curve on a smoothly clamped gap:

> D = (my rating + my federation offset + κ if I have White) − (opponent's rating for expectation + their federation offset + κ if they have White)
> D_eff = D_max × tanh(D / D_max)
> E = 1 / (1 + 10^(−D_eff / σ))

"Opponent's rating for expectation" is the published rating, except that for a junior whose model estimate is reliable it is the model estimate (channel C2). Federation offsets (channel C4) cancel within a federation. The clamp is the same for every player at every level: almost invisible below 300 points of difference, bending gently above, with no rule that switches on or off (Appendix D compares it with table 8.1.2).

K_eff falls smoothly with experience and rises again with inactivity:

> K_eff = K_floor(R) + (K_max − K_floor(R)) × exp(−n_eff / n_0)
> K_floor(R) = K_top + (K_mid − K_top) / (1 + 10^((R − R_half) / w))

n_eff is an experience count: each month it is multiplied by λ and the month's games are added (a junior's games count w_junior each), with a cap n_cap. A newcomer starts at K_max; an established player settles near K_mid below the top and near K_top above it; a player who stops playing drifts back toward a higher K, so that a return after years is absorbed quickly, as Glicko-style systems do [R §4] [R 64]. There is no switch at 30 games, at 2300, at 2400 or at age 18 (Appendix D tabulates the values).

**Parameter table (every value PROVISIONAL; the Layer 1 fit replaces them).**

| Parameter | Meaning | PROVISIONAL value | Comment |
|---|---|---|---|
| σ | curve scale | 400 | today's convention; Sonas's 5/6 finding suggests the fit will land near 480 [R 44] |
| κ | colour term, added to White's rating for the expectation | 35 | Sonas 2002, 266,000 games [R §3.7]; rapid expected smaller |
| D_max | clamp scale | 800 | replaces the 400-point rule and its 2650 exemption |
| K_max | K for a brand-new player | 40 | today's value for newcomers and juniors |
| K_mid, K_top | K floors below and above the top band | 20, 10 | today's 20 and 10 |
| R_half, w | centre and width of the K transition | 2300, 100 | replaces the permanent switch at 2400 |
| n_0 | experience scale (games) | 20 | K halfway to its floor after about 14 games |
| n_cap | experience cap | 60 | keeps a small residual K and lets inactivity matter |
| λ | monthly retention of experience | 0.97 | one idle year lowers n_eff by about 30 % |
| w_junior | weight of a junior's game | 0.5 | juniors stay "uncertain" longer; replaces the 2300 and age-18 switches |
| α | junior compensation weight (C2) | 1.0 | 0 would reproduce today's behaviour |
| b_max | cap on the pool bonus per game | 0.2 | a few points a year for an active player |
| φ_max, Δφ_max | cap and annual cap on a federation offset | 100, 25 | Ghita's largest estimate is about 101 [R 6] |

**Worked example (hand-checkable).** An established adult, A, rated 1900 with hundreds of games and continuous activity, has White against a junior, J, whose published rating is 1500 but whom the model estimates at 1850 (age prior plus recent results, low variance). J has played 20 rated games, all as a junior. Both belong to the same federation, so offsets cancel. This month's pool bonus is b = +0.1.

*Under FIDE today (standard list, rules as amended 1 October 2025 [V 1]).* The difference is 400, which is not "more than 400", so no cap applies. Table 8.1.2, row 392–411: H = .92, L = .08. K is 20 for A and 40 for J (junior under 2300, fewer than 30 games).

| Result | A: ΔR = 20 × (S − .92) | J: ΔR = 40 × (S − .08) |
|---|---|---|
| A wins | 20 × 0.08 = +1.6 → **+2** | 40 × (−0.08) = −3.2 → **−3** |
| Draw | 20 × (−0.42) = −8.4 → **−8** | 40 × 0.42 = +16.8 → **+17** |
| J wins | 20 × (−0.92) = −18.4 → **−18** | 40 × 0.92 = +36.8 → **+37** |

The draw costs the adult 8.4 points, the figure Ghita uses to explain how under-rated juniors drain established players [R 5].

*Under Layer 2 (PROVISIONAL parameters).*

- A's expectation (channel C2 applies: J's rating for expectation is 1850): D = (1900 + 35) − 1850 = 85; D_eff = 800 × tanh(85/800) = 84.7; E_A = 1 / (1 + 10^(−84.7/400)) = 0.620.
- J's own expectation (J's own published rating is used; A is an adult, so no compensation): D = 1500 − (1900 + 35) = −435; D_eff = 800 × tanh(−435/800) = −396.7; E_J = 1 / (1 + 10^(396.7/400)) = 0.092.
- K for A: n_eff at the cap, 60; K_floor(1900) = 20.0; K_eff = 20.0 + 20.0 × exp(−3) = 21.0.
- K for J: n_eff = 20 games × 0.5 = 10; K_floor(1500) = 20.0; K_eff = 20.0 + 20.0 × exp(−0.5) = 32.1.

| Result | A: ΔR = 21.0 × (S − 0.620) + 0.1 | J: ΔR = 32.1 × (S − 0.092) + 0.1 |
|---|---|---|
| A wins | +8.0 + 0.1 = +8.1 → **+8** | −3.0 + 0.1 = −2.9 → **−3** |
| Draw | −2.5 + 0.1 = −2.4 → **−2** | +13.1 + 0.1 = +13.2 → **+13** |
| J wins | −13.0 + 0.1 = −12.9 → **−13** | +29.2 + 0.1 = +29.3 → **+29** |

Reading the two tables together: the adult is no longer taxed for drawing a junior who is really an 1850 player (−2 instead of −8) and is rewarded for beating one (+8 instead of +2); the junior still climbs quickly (+13 for a draw, +29 for a win), because the junior's own update always uses the junior's published number. The two expectations do not sum to one and points are not conserved in this game; that asymmetry is the point of channel C2, and channel C3 keeps the overall level in check. The breakdown published with A's change would read: "vs J (junior; rated for expectation at 1850 under C2, published 1500) · colour +35 · gap 85 → 84.7 after clamp · expected 0.620 · score ½ · K 21.0 · change −2.5 · pool bonus +0.1 · total −2.4".

---

## 6 Where points enter and leave

| Topic | Today (transcribed [V 1] [V 2]) | Proposed | Why |
|---|---|---|---|
| **Newcomers** | Published after at least 5 games against rated opponents, pooled over up to 26 months; Ra = average of rated opponents plus two hypothetical 1800-rated opponents scored as draws; Ru = Ra + dp from table 8.1.1, rounded, maximum 2200; a zero score in the first event is disregarded (§7.1.4, §8.2) | Same 5-game, 26-month threshold. The seed is the model's estimate from those games with an age- and pool-informed prior (C1), rounded, within the floor and the 2200 cap; no phantom opponents. The newcomer starts at K_max and a high model variance. | The two phantom draws pull every newcomer toward 1800 whatever their age or pool and were a one-off repair for deflation [R 35] [R 39]; a prior that knows a 12-year-old from a 40-year-old seeds closer to the truth, which is the first of the three deflation channels [R Recommendations]. |
| **Juniors** | K = 40 until the end of the year of the 18th birthday while rated under 2300; otherwise standard rules (§8.3.3) | A junior's games count w_junior toward experience, so K_eff stays high smoothly; opponents' expectations use the junior's model estimate when it is reliable (C2); the age-improvement rate is a published model output. | Juniors improve faster than K = 40 can track and were "undervalued by hundreds of points" after the pandemic freeze [R §3.3] [R 4]; the loss to the adult, not the junior's gain, is what deflates the pool [R 5] [R 39]. |
| **Floor** | Ratings below 1400 are shown as unrated on the next list; the player is thereafter treated as any unrated player (§7.2.1) | 1400 stays the publication floor for v0.1 (decision 11.3). The engine carries the rating below the floor; the list shows the player as "below 1400"; on recovery the carried rating is published again. No re-seeding. | Today's rule splits players into rated and unrated, creates an artificial pile-up at 1400 and makes 1400–1600 ratings "highly unreliable" [R 2] [R 4]; re-entry through the newcomer rule injects points at the bottom. |
| **Inactivity** | A player commences inactivity after one year without a rated game and regains activity after one game; ratings do not decay; K unchanged (§7.2.2) | The published rating never decays (forward-only). Experience n_eff decays each idle month, so K_eff is higher on return and the first games move the rating faster. The inactive flag stays. Eligibility rules that depend on rating (for example rating-based tournament spots) are FIDE's to set and are outside these regulations; the model's variance is available to them. | About 40 % of listed players have not played since before the pandemic [R 5] [R 56]; a frozen rating with a frozen K misstates both the level and the uncertainty of a returning player; Glicko-style uncertainty growth is the standard remedy [R §6]. |
| **Retirements** | No rule; a rating stays on the list indefinitely (§7.2.2) | After five years without a rated game (PROVISIONAL), the player moves to an archive list with the rating preserved; return re-activates it. A presentation rule, not a rating change. | Ghost ratings distort pool statistics and the public's reading of the list [R §3.10]; archiving changes no number. |

---

## 7 One framework across time controls

**The structure.** skill_tc = θ + δ_tc. One shared skill per player, θ, plus an offset for each time control, shrunk toward zero with a time-control-specific variance (Appendix A.4). A rapid specialist can be stronger at rapid without the system pretending they are a different person. Each time control keeps its own colour and draw parameters and its own volatility, because White's edge and draw rates differ by style [R §3.7] [R §8].

**Shrinkage.** With few games in a style, δ_tc stays close to zero and the player's strength in that style is essentially θ. With many games, δ_tc is estimated from them. The strength of the shrinkage, ω_tc, is fitted from data; the cross-time-control correlation for FIDE players is one of the first quantities the project will estimate (open question 11.4) [R §8].

**What a rapid game tells the classical rating.** In Layer 1, every game in every style updates θ, so a rapid game moves the model's view of a player's classical strength a little, and moves δ_rapid more. In Layer 2, the classical published rating is touched by a rapid game only through the four channels: the seed of a newcomer to the classical list draws on their rapid history (C1); the compensation for a junior opponent draws on the junior's θ, which rapid games inform (C2). No rapid result ever enters the classical per-game formula directly, and the three published lists remain separate and forward-only.

**What FIDE does today.** Three independent lists with the same tables, K rules and rounding [V 2]. The only cross-link is the seed rule for rapid and blitz: an unrated player who has a standard rating uses it, and is then treated as rated (§7.2.1 of the rapid and blitz regulations [V 2]). The rapid and blitz chapter keeps the plain 400-point cap, without the 2650 exemption, and since 1 December 2024 does not rate games with a 600-point gap when a player is above 2600 [V 2]; from 2026, 45+30 time controls may be rated as standard for approved events [R 24]. This design replaces those cross-list rules with one shared skill and one consistent formula (decision 11.7).

---

## 8 Proof plan

**Backtest protocol.** Rolling-origin evaluation: fit on all games up to month t, forecast every game of month t+1, score, roll forward, for every month in the test range. The match schedule is never a feature; Kaggle 2011's winner admitted that schedule information drove much of the edge, which is not legitimate for an official rating [R 9] [R §9]. Layer 0 (today's rules, exactly) is the baseline on every metric.

**Metrics.**
- Forecast quality: three-outcome log-loss (win, draw, loss, requiring the draw model) and Brier score; calibration plots by rating gap, rating band, colour, time control and federation pair.
- Drift: the mean rating of a stable anchor cohort over time (adults aged about 25–45 with regular activity), as Glickman does for US Chess [R 22]; the score of fixed rating bands against each other across years; rating velocity by age cohort.
- Cross-federation comparability: mean residual (actual minus expected) in cross-border games by federation, which should shrink toward zero; the share of games within each federation.
- Newcomer convergence: games until the error against true strength is below 50 points in simulation; forecast error over a player's first 30 games.
- Manipulation resistance: points gained per unit of effort by simulated adversaries (farmers, sandbaggers, colluding rings, inactive protectors), compared with Layer 0.

**The simulator.** Players with known true strengths: age-dependent improvement curves; federation-clustered pairings with a tunable share of cross-border games; Swiss pairings with top-half-against-bottom-half first rounds, which supply the cross-level mixing that isolated pools lack [R §3.13]; entries and exits with realistic age and pool profiles; colour allocation by pairing rules. Layer 0 and candidate Layer 2 rules run side by side on the same simulated games, so recovery of true strengths, convergence speed and drift can be measured exactly.

**Success criteria (PROVISIONAL thresholds, to be fixed before the Lichess backtest is run).**

| Criterion | PROVISIONAL threshold |
|---|---|
| Three-outcome log-loss on held-out months | at least 2 % better than Layer 0 at every rating band |
| Calibration | slope of actual on expected score within 0.95–1.05 in every gap bin up to 800 points |
| Anchor-cohort drift | within ±2 points per year (the report's post-reform figure is about −16 per year [R 5]) |
| Cross-federation residual | within ±10 points for every federation with at least 1,000 cross-border games in the window |
| Newcomer convergence (simulation) | median absolute error below 50 points within 15 games |
| Adversarial simulations | no strategy gains more than Layer 0 allows, and farming yields fewer points per game than honest play against equals |
| Hand-checkability | 100 % of a random sample of published changes recomputed exactly from the breakdown and the parameter file |

**Data plan.**
1. **Development:** the Lichess open database, CC0 ("Use them for research, commercial purpose, publication, anything you like" [V 4]); monthly standard-game files of about 28–33 GB and 85–100 million games each for 2024–2026 [V 4]; the classical and rapid subsets; the over-the-board broadcast archive (CC BY-SA 4.0 [V 4]) as the OTB slice. Online data calibrates methods, not FIDE parameters.
2. **Player panel:** FIDE's monthly lists, standard, rapid and blitz, with K, games per period, year of birth and federation, archived monthly since February 2015 [V 3]. They carry no licence; the project downloads and analyses them and never redistributes them [V 3].
3. **The formal request:** FIDE's TRF archive, the complete game-level record that arbiters submit under §9.1 [V 1], under a data-sharing agreement (Phase C). It is the only dataset that can settle the federation-offset question [R §5].

## 9 Governance and the calculator FIDE can run

**Plain statement.** This is a statistical model with machine-estimated parameters, re-estimated monthly from games, feeding a published per-game formula. It is not a neural network and not a black box. Anyone with the parameter file and the game record can recompute any rating change by hand; the model's only power is to set the numbers in that file, within caps, once a month, in public.

**Determinism.** Layer 0 and Layer 2 use fixed-precision arithmetic and today's rounding rule (§8.3.4 [V 1]). Identical TRF input and identical parameter file give identical output on any machine. Layer 1 fixes its random seed wherever a stochastic step exists, so its parameter file is reproducible too.

**The monthly parameter file.** Published with every list, versioned, machine- and human-readable. For each time control it holds the curve scale σ and clamp D_max; the colour term κ; the draw-term parameters (forecasts only); the K parameters; the seed prior by age band and pool (C1); the compensation weight α (C2); the pool bonuses b_P (C3); the federation offsets φ_F with sample sizes (C4); and the drift estimate and anchor-cohort definition behind them. Every value carries the date it last changed.

**Annual change caps.** No published parameter moves by more than a published cap per calendar year; the PROVISIONAL caps are tabulated in Appendix D (for example ±10 on σ, ±25 on a federation offset with an absolute cap of 100, ±0.1 per game on the pool bonus with an absolute cap of 0.2).

**Ownership and process.** The QC owns the parameter file and the caps; the FIDE Council approves changes to caps or to the formula; every change to the formula or the caps goes through a public comment period, with the 2023 consultation (over 150 comments [R 18] [R 19]) as the model. The monthly update within the caps is routine and automatic, published with its monitoring report. Rollback rule: if any monitoring threshold (section 8) is breached for two consecutive months, the file reverts to the last compliant version while the QC investigates.

**No exploitable cliffs.** Today's rules contain discontinuities that reward strategy rather than play: the 400-point cap below 2650 and none above it, so that a 2649 and a 2651 player get different expectations against the same 2200 opponent; the K switches at 30 games, at 2300 for juniors and permanently at 2400; the floor rule that turns a 1399 into "unrated" and re-seeds the player through two phantom 1800 draws; and a different cap regime in rapid and blitz [V 1] [V 2] [R 55]. The design removes each of them with one smooth clamp, one smooth K_eff, a carried rating below the floor and a model seed; Appendix D lists cliff and replacement side by side.

**Anomaly monitoring.** Each month the engine publishes, without names, aggregate indicators: clusters of players whose mutual results are far from forecast (collusion and arranged draws, which the draw model makes detectable [R §3.6]); players with large gains concentrated against far-lower-rated opponents (a farming index); returns from inactivity that coincide with unusual results; federations whose residuals move faster than their cap allows. Named cases go to FIDE's existing Tournament Investigation and QC appeal procedures [R §3.9] [V 1]; the engine flags, it does not judge.

---

## 10 Roadmap

| Phase | Deliverable | Gate to the next phase |
|---|---|---|
| **A** | Layer 0 reference engine for standard, rapid and blitz, test-vector verified against FIDE's calculator and sampled monthly lists; the simulator with known true strengths; the Lichess backtest harness (CC0 data [V 4]) and the first rolling-origin results for L1 and L2 | L0 reproduces sampled players' monthly changes exactly; L2 beats L0 on the Lichess backtest on every metric of section 8 |
| **B** | Publish the results: this proposal at v1.0, the code, the test vectors, a short technical report and the monitoring dashboard; invite QC and public comment | Comments triaged; no unresolved correctness finding |
| **C** | Formal request to FIDE for the TRF archive under a data-sharing agreement, pitched to the new administration as a "digital transformation" deliverable [R §2] [R 28]; re-run every backtest on FIDE games; federation offsets become estimable | Backtest on FIDE data meets the section 8 criteria; data agreement respected |
| **D** | Pilot with one federation: a shadow list run in parallel for twelve months, published alongside the official list, with monthly monitoring reports; then a QC decision on adoption, scope and timing | Twelve clean months; QC and Council decision |

---

## 11 Open questions and decisions needed

**Open questions the research could not settle** ([R Open questions], restated with the step that answers each):

1. What share of FIDE-rated games is within one federation, by band and year? Needs the TRF archive (Phase C).
2. Are federation offsets stable and causal, or artefacts of who travels? Needs the TRF archive and a multivariate analysis (Phase C).
3. What were draw rates and White's score in FIDE play in 2024–2026, by level and time control? Lichess broadcasts first (Phase A), FIDE data later.
4. How strongly do classical, rapid and blitz strength correlate for FIDE players today? Estimable from the combined monthly list in Phase A [V 3].
5. How large is per-player colour-count imbalance, and does it move ratings? Phase A on broadcasts; Phase C on FIDE data.
6. Will the QC under the new administration accept a model-driven correction layer, and would title-norm arithmetic need to change? Phase B and C conversations; see decision 6 below.
7. Does any exact reproduction of FIDE's calculator exist? None found [R §5]; Layer 0 is that deliverable.

**Decisions needed from the founder** (numbered for reply):

1. **Assumptions A1–A7.** The research report refers to assumptions A1–A7 but does not list them; Appendix B reconstructs them from the report's usage. Confirm or supply the canonical list.
2. **Junior-opponent compensation scope (C2).** Juniors only, as drafted, or every player whose model estimate exceeds their published rating by more than a threshold? The second is more general and harder to explain.
3. **Floor policy.** Keep 1400 as the publication floor and carry ratings internally below it (as drafted), lower the floor, or keep today's "unrated" rule?
4. **Pool bonus sign (C3).** Allow a negative bonus in an inflating pool, or constrain b ≥ 0 and handle inflation only through seeds?
5. **Publication of model estimates.** Should each player's model estimate θ̂ (used in C1 and C2) be public, visible only to the player, or QC-only? Public is most transparent; it also creates a second number players will compare with.
6. **Curve scale.** Fix σ at 400 for comparability with title-norm tables, or let it move within its cap? Decision 6 interacts with open question 6.
7. **Rapid and blitz consistency.** The rapid/blitz chapter keeps the plain 400-point cap and adds a 600-point "not rated" rule [V 2]; the proposal applies one clamp to all three. Confirm.
8. **Pilot federation.** Which federation to approach for Phase D, and when.
9. **Data handling.** FIDE lists carry no licence [V 3]; confirm the policy "download, analyse, never redistribute" and the wording of the Phase C request.
10. **Repository name.** The operator kept `Chess-ELO-Rating` and public visibility on 2026-10-09 (`docs/decisions/D-0001`). Revisit before v1.0 publication?

---

## Appendix A Mathematics

**A.1 Notation.** Players i, j; months t; time controls tc ∈ {standard, rapid, blitz}; a game g has a White player w(g), a Black player b(g), a time control and a result y_g ∈ {1, ½, 0} for White. R_i(t) is the published rating, θ_i(t) the model's shared skill, δ_{i,tc}(t) the time-control offset, a_i(t) the player's age, F(i) their federation, P(i) their pool (the global pool or a federation pool). All skills live on the Elo scale: 400 points is a factor of 10 in odds.

**A.2 Strength in a time control.** s_{i,tc}(t) = θ_i(t) + δ_{i,tc}(t).

**A.3 Likelihood (Bradley–Terry–Davidson with colour and level-dependent draws).** For a game at time t in time control tc, let

π_w = 10^{(s_{w,tc} + γ_tc)/400}, π_b = 10^{s_{b,tc}/400}, ν = exp(ν0_tc + ν1_tc · (s̄ − 2000)/400), s̄ = (s_{w,tc} + s_{b,tc})/2,

Z = π_w + π_b + ν · √(π_w π_b),

P(White wins) = π_w / Z, P(draw) = ν · √(π_w π_b) / Z, P(Black wins) = π_b / Z.

γ_tc is the colour term (White's advantage in rating points), ν0_tc and ν1_tc set the draw propensity and its growth with level. White's expected score is E_w = P(White wins) + ½ P(draw). The log-likelihood is the sum over games of log P(observed result). Colour and draw structure are what assumption A2 omits (Appendix B).

**A.4 Dynamics.** Skill follows a random walk with an age-dependent drift and volatility:

θ_i(t+1) = θ_i(t) + m(a_i(t)) + ε_i(t), ε_i(t) ~ N(0, τ²(a_i(t))),

where m(a) is the expected monthly improvement at age a (large for juniors, near zero for adults, slightly negative at high age) and τ(a) the monthly volatility. Offsets are shrunk toward zero and move slowly:

δ_{i,tc}(t+1) = ρ_tc · δ_{i,tc}(t) + ξ_{i,tc}(t), ξ ~ N(0, ω²_tc), with stationary prior δ ~ N(0, ω²_tc / (1 − ρ²_tc)).

A new player enters with prior θ_i(t_0) ~ N(μ_0(a, P), s_0²), where μ_0 depends on age band and pool. m(·), τ(·), ρ, ω, γ, ν0, ν1, μ_0 and s_0 are global parameters.

**A.5 Fitting.** Each month, on the games of the last 36 months, maximise the log posterior over all skill trajectories (maximum a posteriori by Newton's method, as in Whole-History Rating [R 11], or a linearised Kalman smoother), warm-started from last month's fit; choose the global parameters by cross-validated three-outcome log-loss on the most recent months. Identification: the mean skill of the anchor cohort (adults aged 25–45 with regular activity in each of the last three years, as in the US Chess practice [R 22]) is held constant over the window.

**A.6 Layer 1 outputs.**
- Posterior mean θ̂_i(t) and variance for every player; forecasts for any pairing.
- Federation offset: φ_F(t) = shrink_F [ mean_{i∈F}(θ̂_i − R_i) − mean_all(θ̂_i − R_i) ], with shrink_F = n_F / (n_F + n_φ) where n_F is the number of cross-border games involving F in the window, then capped at ±φ_max and rate-limited to Δφ_max per year.
- Drift of pool P: d_P(t) = twelve-month change of mean_{i ∈ anchor(P)} [R_i(t) − θ̂_i(t)], in points per year (negative means deflation).
- Junior improvement rates: m̂(a) by age.

**A.7 Layer 2 update rule.** For a game between player i and opponent j, with colour indicator c = 1 for White and 0 for Black:

R̃_j = R_j + α · (θ̂_j − R_j) if j is a junior and the model's variance for j is below a threshold, else R̃_j = R_j (channel C2);

D_i = (R_i + φ_{F(i)} + κ·c_i) − (R̃_j + φ_{F(j)} + κ·c_j) (channel C4 enters here; within a federation φ cancels);

D_eff = D_max · tanh(D_i / D_max) (smooth clamp, same for everyone);

E_i = 1 / (1 + 10^{−D_eff/σ});

ΔR_i = K_eff,i · (S_i − E_i) + b_{P(i)} (channel C3), with S_i ∈ {1, ½, 0};

K_eff,i = K_floor(R_i) + (K_max − K_floor(R_i)) · exp(−n_eff,i / n_0), K_floor(R) = K_top + (K_mid − K_top) / (1 + 10^{(R − R_half)/w});

n_eff,i ← min(n_cap, λ · n_eff,i + Σ_{games this month} w_g), w_g = w_junior if i is a junior at the time of the game, else 1.

The period change is Σ ΔR_i over the player's games in the rating period, rounded to the nearest whole number with 0.5 away from zero (today's §8.3.4 [V 1]).

Channel C1 (seed): a player new to the list receives R_i(t_0) = clamp(round(θ̂_i(t_0)), R_floor, R_seedmax) once they have at least N_min games against rated opponents within 26 consecutive months (today's §7.1.4 [V 1]), with n_eff,i(t_0) = n_seed.

Channel C3 (pool bonus): b_P(t) = clamp(−β · d_P(t) / g_P(t), −b_max, +b_max), where g_P is the mean number of rated games per active player per year in P and β the correction fraction; the total injected per player per year is reported.

**A.8 Symbols (with PROVISIONAL values where the proposal uses one).**

| Symbol | Meaning | PROVISIONAL |
|---|---|---|
| θ_i(t) | shared skill of player i | fitted |
| δ_{i,tc}(t) | time-control offset | fitted, shrunk |
| γ_tc | L1 colour term | fitted (≈ 35 standard [R §3.7]) |
| ν0_tc, ν1_tc | draw propensity and its level slope | fitted |
| m(a), τ(a) | age drift and volatility | fitted |
| ρ_tc, ω_tc | offset persistence and noise | fitted |
| μ_0(a,P), s_0 | newcomer prior mean and sd | fitted |
| σ | L2 curve scale | 400 (fit expected ≈ 480 [R 44]) |
| κ | L2 colour term (points added to White) | 35 |
| D_max | clamp scale | 800 |
| K_max, K_mid, K_top | K ceiling, sub-2300 floor, top floor | 40, 20, 10 |
| R_half, w | centre and width of the K transition | 2300, 100 |
| n_0, n_cap, λ | experience scale, cap, monthly retention | 20, 60, 0.97 |
| w_junior | experience weight of a junior's game | 0.5 |
| α | junior compensation weight | 1.0 |
| φ_F, φ_max, Δφ_max, n_φ | federation offset, cap, annual cap, shrinkage games | fitted, 100, 25, 2000 |
| b_P, b_max, β | pool bonus, cap, correction fraction | fitted, 0.2, 1.0 |
| R_floor, R_seedmax, N_min, n_seed | publication floor, seed cap, games to seed, starting experience | 1400, 2200, 5, 0 |

---

## Appendix B Mapping to assumptions A1–A7

The research report refers to "assumptions A1–A7" [R §1] and tags each problem with them ([R §3], "Ranked problem table"), but version 1.0 of the report does not contain the list itself. The mapping below reconstructs each assumption from the way the report uses it (decision 11.1 asks the founder to confirm). "Breaks" names the problem sections of the report; "Handled by" names the part of this design.

| Assumption (reconstructed) | Statement | Report usage | Handled by |
|---|---|---|---|
| A1 | One fixed link curve converts a rating gap into an expected score | §3.5 forecast accuracy across gaps; problem 4 | Calibrated logistic with fitted scale σ, smooth clamp (section 5); L1 forecasts |
| A2 | No colour and no draw structure: results depend on the gap only | §3.6 draws; §3.7 colour; problems 8, 9 | Colour term κ in L2; colour and level-dependent draw terms in L1 (Appendix A.3) |
| A3 | A fixed step size K, with bracket switches | §3.4 K-factor and bracket edges; §3.1 deflation; problems 1, 6 | Smooth, uncertainty-weighted K_eff (section 5) |
| A4 | Strength varies slowly, at the same rate for everyone | §3.3 juniors; §3.11 COVID-era effects; §3.1 deflation; problems 1, 5 | Age-dependent drift and volatility in L1 (A.4); junior-opponent compensation C2; junior experience weight |
| A5 | One well-mixed pool: everyone eventually plays everyone | §3.2 federation isolation; §3.13 matchmaking; problems 2, 12 | Federation offsets C4 through expectations; pool-level seeds; simulator tests of isolated pools |
| A6 | A closed, conserving pool: points neither enter nor leave, so the scale's level is stable | §3.1 deflation; §3.10 inactivity; problems 1, 7 | Model seeds C1; capped pool drift correction C3; anchor-cohort drift monitoring |
| A7 | Players do not act strategically: they do not choose opponents, time their activity or arrange results to move their rating | §3.8 protection and game selection; §3.9 manipulation; §3.10 inactivity; problems 3, 7, 10 | Cliff-free clamp and K_eff; experience decay on inactivity; anomaly monitoring; adversarial simulations |

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

**D.1 What the PROVISIONAL K parameters imply (section 5).**

| Situation | K_eff | FIDE today [V 1] |
|---|---|---|
| New player, 0 games | 40.0 | 40 |
| 10 games | 32.1 | 40 |
| 20 games | 27.4 | 40 |
| 30 games | 24.5 | 40 → 20 (cliff) |
| 60+ games, rated 1900 | 21.0 | 20 |
| Established, rated 2300 | about 15 | 20 (40 for a junior; cliff at 2300) |
| Established, rated 2400 | about 10.9 | 10, permanently (cliff) |
| Rated 1900, idle 12 / 36 / 60 months | 22.5 / 27.3 / 32.3 | 20 |

**D.2 The smooth clamp against table 8.1.2 (σ = 400, D_max = 800).**

| Gap D | E under Layer 2 | FIDE table 8.1.2 [V 1] |
|---|---|---|
| 100 | 0.639 | .64 |
| 300 | 0.839 | .85 |
| 400 | 0.894 | .92 |
| 600 | 0.949 | .98 (below 2650: capped to .92) |
| 800 | 0.971 | 1.0 (below 2650: capped to .92) |
| 1200 | 0.985 | 1.0 (below 2650: capped to .92) |

**D.3 Annual change caps (all PROVISIONAL; section 9).**

| Parameter | Cap per calendar year | Why |
|---|---|---|
| Curve scale σ | ±10 | Ratings must mean the same thing across years; the curve also feeds title-norm arithmetic (open question 11.6) |
| Colour term κ | ±5 | Small, stable quantity [R §3.7] |
| K parameters | ±2 each (K_max, K_mid, K_top), ±50 (R_half), ±2 (n_0), ±5 (n_cap) | Avoid sudden changes in volatility |
| Federation offset φ_F | ±25, and \|φ_F\| ≤ 100 | Political and statistical caution; offsets are not peer-reviewed yet [R §3.2] |
| Pool bonus b_P | ±0.1 per game, and \|b_P\| ≤ 0.2 per game | A few points a year per active player at most, as with the US Chess bonus constant [R 32] |
| Seed prior | ±25 per age band | Protects the newcomer scale |

**D.4 Today's cliffs and their replacements (section 9).**

| Cliff today [V 1] [V 2] | Effect | Replacement |
|---|---|---|
| 400-point cap for players under 2650; no cap at 2650+ | A 2649 and a 2651 player get different expectations against the same 2200 opponent; the cap created the farming arbitrage [R 55] | One smooth clamp for everyone (section 5) |
| Rapid and blitz keep the plain 400-point cap and add a 600-point "not rated" rule above 2600 | Different incentives by time control | Same clamp in all three |
| K drops 40 → 20 after 30 games; 40 → 20 at 2300 for juniors; 20 → 10 at 2400, permanently | A junior's last game before 2300, or a player's first list at 2400, changes the value of every later game | Smooth K_eff; no permanent switch |
| Floor at 1400: a player dropping below becomes "unrated" and re-enters as a newcomer with two phantom 1800 draws | Artificial pile-up at the floor and re-seeding upward [R 4] [R 2] | Rating carried internally below the floor; re-entry at the carried value (section 6) |
| Two phantom 1800 draws in every initial rating | Pulls every newcomer toward 1800 regardless of age or pool | Model seed with an age- and pool-informed prior (C1) |

---

## Appendix E Further worked examples (all Layer 2 values PROVISIONAL)

Three more hand-checkable cases, computed with the section 5 formula and the parameter table, each next to today's rule [V 1].

**E.1 A cross-federation game (channel C4).** A Spanish player, rated 1900, has White against a Vietnamese player, also rated 1900. Both are established adults (n_eff at the cap, K_eff = 21.0). This month's federation offsets are φ_ESP = 0 and φ_VIE = +100 (Ghita's estimate for Vietnam is about +101 [R 6]).

*Today:* D = 0, table 8.1.2 gives .50 to each; K = 20. A win is worth +10, a loss −10, a draw 0, for either player.

*Layer 2:* Spain's gap D = (1900 + 0 + 35) − (1900 + 100) = −65, D_eff = −64.9, E = 0.408; Vietnam's gap is +65, E = 0.592. The two expectations sum to one, because channel C4 applies symmetrically.

| Result | Spain: 21.0 × (S − 0.408) | Vietnam: 21.0 × (S − 0.592) |
|---|---|---|
| Spain wins | +12.4 → **+12** | −12.4 → **−12** |
| Draw | +1.9 → **+2** | −1.9 → **−2** |
| Vietnam wins | −8.6 → **−9** | +8.6 → **+9** |

The Spanish player is no longer the one who pays for the Vietnamese pool's under-rating: a loss costs 9 instead of 10, a draw earns 2 instead of 0. The Vietnamese player gains less from this game than today, which is deliberate: the catch-up of an under-rated pool comes through the pool's own seeds (C1) and its capped pool bonus (C3), never through draining opponents abroad. No rating was edited; the offset entered only through E.

**E.2 A newcomer's first rating today (a Layer 0 test vector) and how channel C1 differs.** A newcomer plays five games against rated opponents of 1550, 1600, 1650, 1580 and 1620 (average 1600) and scores 3/5. Today's rule (§7.1.4, §8.2 [V 1]): Ra = (5 × 1600 + 2 × 1800) / 7 = 1657.14; p = (3 + 2 × ½) / 7 = 0.5714, taken as .57; table 8.1.1 gives dp = 50 for p = .57; Ru = 1657.14 + 50 = 1707.14, rounded to **1707** (above the 1400 minimum, below the 2200 cap). Whether the newcomer is ten or forty years old makes no difference to this number.

Under channel C1 the same five games feed the model with an age- and pool-informed prior, and the seed is the rounded model estimate within the same floor and cap. The prior, not a pair of phantom 1800 draws, decides where the five games pull from; the age-cohort evidence [R 4] [R 6] implies a higher seed for the ten-year-old than for the forty-year-old with identical results, and a larger model variance, so a higher K_eff, for both. The breakdown would show both numbers: "today's rule 1707; model estimate and its uncertainty; published seed". (The rounding of p before the table lookup is a detail to confirm against FIDE's calculator; the Layer 0 specification lists it as a test case.)

**E.3 The 2650 cliff (channel-free: the clamp alone).** Four players rated 2649, 2651, 2700 and 2936 each beat a 2200-rated opponent with White. Today, all four have K = 10 [V 1].

| Winner's rating | Today: gap used | Today: PD and gain | Layer 2: gap with colour → after clamp | Layer 2: E | Layer 2: K_eff and gain |
|---|---|---|---|---|---|
| 2649 | 400 (capped) | .92 → +0.8 | 484 → 432.5 | 0.923 | 11.5 → +0.88 |
| 2651 | 451 (no cap) | .94 → +0.6 | 486 → 433.9 | 0.924 | 11.5 → +0.87 |
| 2700 | 500 | .96 → +0.4 | 535 → 467.3 | 0.936 | 11.5 → +0.73 |
| 2936 | 736 | 1.0 → +0.0 | 771 → 596.8 | 0.969 | 11.5 → +0.36 |

Today the gain jumps between 2649 and 2651 for the same result against the same opponent, and vanishes entirely above a 735-point gap. Under the clamp it declines smoothly and never reaches zero, so there is no rating at which the rules change and no result that is worth nothing; whether the top end should flatten faster is exactly what the calibration backtest (section 8) will decide.

---

*End of DRAFT v0.1. Status line repeated: DRAFT v0.1 — not for publication.*
