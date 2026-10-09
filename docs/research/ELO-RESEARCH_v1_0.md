# How the Elo Rating System for Chess Should Be Modified: Evidence Base for Zugzwang's Open-Source FIDE Proposal (status as of 9 October 2026)

The chess world's strongest, best-evidenced and most fixable complaint is **structural deflation driven by fast-improving juniors and by federations that rarely play each other**, so Zugzwang's proposal should target it first. Second come **top-level rating protection and "farming"** and **forecast miscalibration across rating gaps**. Colour and draws should be modelled inside the engine, but community demand for them is low and their effect on published ratings is small. The evidence supports the working hypothesis (c): a dynamic statistical model running behind the scenes, publishing a familiar, forward-only Elo-style number. The shipping product should be a transparent, deterministic, open-source "reference implementation" of FIDE's current rules, with a documented correction layer on top. It should not be a black-box AI.

## TL;DR

- **What to fix, ranked by demand × evidence × fixability:** (1) deflation and junior lag; (2) federation and geographic isolation, i.e. the same number meaning different strength in different countries; (3) top-level rating protection and farming, plus inactivity; (4) the expectancy curve being miscalibrated across rating gaps. FIDE has officially acknowledged #1 and #3, through the March 2024 reform and the October 2025 "400-point rule" amendment. #2 is the fastest-rising issue in 2025–2026 analyses but has no official fix. Colour advantage is real: Jeff Sonas's 2002 ChessBase analysis of 266,000 games valued the White pieces at 35 rating points. But it matters more for forecasting than for fairness, because pairing rules largely balance colours.
- **How to fix it:** a two-layer system. Underneath, a dynamic paired-comparison model (Bradley–Terry/Davidson with draw, colour and time-control terms, time-varying skill, Kalman/Whole-History-style smoothing, and pool-level offsets) is re-estimated monthly on the last 2–3 years of games. On top, the published Elo number is updated by an explainable per-game formula whose parameters (K, curve, colour term, newcomer seeds, junior boosts, pool corrections) are set by that model and published. Precedents: US Chess's Glickman-designed system with periodic "bonus" recalibration, Go's WHR ratings, FIFA's Elo-based "SUM" switch (approved by the FIFA Council on 10 June 2018 and first used on 16 August 2018), and the Sonas–Glickman Universal Rating System.
- **What to build first:** a GitHub repository that reproduces FIDE's current regulations exactly, using the FIDE Rating Regulations effective 1 March 2024 as amended 1 October 2025 and the monthly rating-list downloads. Add a simulator with known true strengths and a Lichess (CC0) backtest harness, then request FIDE's game-level archive. That archive is the only dataset that can settle the federation-offset question. Measure every change with rolling-origin log-loss and calibration, drift metrics, cross-federation residuals and manipulation tests.

## Key Findings

1. **FIDE's current system is still classic Elo plus patches.** It uses a fixed normal-curve lookup table (§8.1.2), K = 40/20/10 with a junior K = 40 rule, a 400-point cap (now lifted for players rated 2650+), a 1400 floor, and performance-based initial ratings that include two fictitious draws against 1800-rated opponents.\[1\] FIDE's QC chair is quoted as saying the 2024 one-off compression would "reset the current deflation… however it will not stop the deflation for the future". That quote is in fact from Danish critic Christian Milvang, but the reform's own design concedes the same point.\[2\]
2. **Deflation continued after the 2024 reset.** An independent analysis of March 2024–June 2025 lists found the average rating falling by about 1 Elo per month, with players piling up at the 1400 floor.\[3\]\[4\] A February 2026 study of 954,805 FIDE games found the median active player losing 26 Elo a year before the reform and 16 a year after it. The reform slowed the drift but did not stop it.\[5\]
3. **Geography is the new frontier.** The same study estimates that Vietnamese players outperform their ratings by 101 Elo, while Swiss and Austrian players underperform by 64.\[6\] The gap between federations "can exceed 160 Elo".\[5\] Elo has no mechanism to detect or correct pools that drift apart.\[3\]\[4\]
4. **FIDE fixes things reactively, case by case.** The October 2025 amendment followed Hikaru Nakamura's rating gains against low-rated opponents.\[7\]\[8\] In an hour-long interview with ChessBase India, FIDE's then-president Arkady Dvorkovich said Nakamura "used deficiencies in our rules… it is not his fault, it is our fault that we allowed for those deficiencies". He flagged inactivity as the next long-term issue.
5. **Better algorithms have existed for 15+ years, and FIDE has not adopted them.** Kaggle 2010 was won by Yannis Sismanis's Elo++ (arXiv:1012.4571), which used "only two global parameters (white's advantage and regularization constant)"; the Elo benchmark finished 141st of 258. Kaggle/Deloitte 2011 was won by a TrueSkill-inspired model.\[9\] TrueSkill Through Time showed that modelling draws "provides significantly better predictive power".\[10\] WHR outperformed Elo, Glicko and TrueSkill on 10.8 million Go games.\[11\]\[12\] The barrier is governance and explainability, not compute.

---

## 1. What Elo is

**Plain-language takeaway:** Elo is a prediction machine. It guesses your score against an opponent from the rating gap, then moves your rating up or down by a fixed step times how much you beat or missed that guess. The 400-point scale is just a convention.

**Origin.** Arpad Elo, a Hungarian-American physics professor, devised the system. The US Chess Federation (USCF) switched to the Elo rating system in 1960, and FIDE adopted it in 1970.\[13\] FIDE's first published list (1971) had about 600 players, led by Fischer, with a rating floor of 2200.\[4\] A February 2026 analysis puts the inaugural list at 592 players, all above 2200, compared with 528,064 by December 2025.\[5\]

**Mathematics.**
- Expected score for player A against B, in the common logistic form: E_A = 1 / (1 + 10^((R_B − R_A)/400)). A 400-point gap gives 10:1 odds in expected points, about 91%. A 200-point gap gives roughly 3:1, about 75%.\[14\]
- **FIDE does not use the logistic formula.** It uses Elo's original **normal-curve table**, printed in §8.1.2 of the regulations.\[15\] For example, a gap of 0–3 points gives .50, 92–98 gives .63, 198–206 gives .76, 345–357 gives .89, and anything above 735 gives 1.0. The class interval is set at 200 points.\[1\] Any reproduction of FIDE must use this table, not the logistic approximation.
- Update: ΔR = K × Σ(score − P_D). Scores are 1, ½ or 0, summed over a tournament or rating period, and the result is rounded (0.5 rounds away from zero).\[1\]

**Statistical interpretation.** Elo is an online stochastic-gradient step on a paired-comparison (Bradley–Terry/Thurstone) model. Each game nudges the rating in the direction that would have made the observed result more likely. K is the learning rate. The model assumes one latent strength per player, one fixed link curve, no colour or draw structure, and slowly varying strength. Those are assumptions A1–A7 below.

---

## 2. How it has changed: timeline to October 2026

**Plain-language takeaway:** FIDE's system has been adjusted dozens of times, mostly by moving the floor, the K-factor and the 400-point cap. These are blunt instruments, and each one shifts the balance between inflation and deflation without fixing the mechanism behind it.

| Date | Change | Source/notes |
|---|---|---|
| 1960 | USCF adopts Elo | Wikipedia (secondary)\[13\] |
| 1970–71 | FIDE adopts Elo; first list ~600 players, floor 2200 | Ghita 2025/2026\[4\] |
| 1981 → 2000 → 2009 → 2012 | Publication: annual → semiannual (1981) → quarterly (2000) → bi-monthly (2009) → monthly (since 2012) | Ghita, "FIDE Ratings Revisited" (June 2025)\[4\] |
| 1993 → 2010s | Floor lowered 2200 → 2000 (1993) → 1800 → 1600 → 1400 → 1200 → 1000 | Ghita 2025\[4\] |
| 2008–2011 | FIDE trial of higher K (30/20 instead of 25/15/10); top players raised "major concern"; parallel list ordered | Old FIDE news page, "Rating Regulations – The K-Factor"\[16\] |
| pre-2011 | "350-point rule" | Ghita 2025\[4\] |
| 1 July 2014 | K = 40 for new players and for juniors under 18 rated below 2300; K = 20 below 2400; K = 10 at 2400+ (previously 30/15/10) | FIDE Handbook regulation archive; Ghita 2025\[4\] |
| 2012 onward | Monthly lists; Rapid and Blitz rating lists exist (Rapid & Blitz regulations have their own chapters, revised 2018, Jan 2022, Oct 2022, Mar 2024) | FIDE Handbook |
| 1 Jan 2022 | 400-point rule restricted (applied only once per tournament) | Ghita 2025; ChessTalk forum\[17\] |
| Mar–Jul 2023 | QC public consultation; Sonas proposal published 20 July 2023; "over 150 comments" received | FIDE news 2784; ChessBase\[18\]\[19\] |
| 14/15 Dec 2023 | FIDE Council approves reform (FIDE news says 14 Dec; the Handbook header says "Approved by FIDE Council on 15/12/2023") | FIDE\[1\]\[20\] |
| **1 Mar 2024** | **One-off compression**: for ratings < 2000, new = old + 0.40 × (2000 − old) (1500→1700, 1700→1820, 1000→1400); **floor 1000 → 1400**; **initial rating** = performance against rated opponents plus **two hypothetical draws against 1800-rated opponents**, capped at 2200; **400-point rule restored with no limit**; same changes applied to Rapid & Blitz;\[1\]\[17\]\[20\]\[21\] ~350,000 players adjusted | FIDE Handbook B.02 2024; Chess.com, 1 Mar 2024\[2\]\[22\] |
| **1 Oct 2025** | **400-point cap no longer applies to players rated 2650+** ("the difference between ratings shall be used in all cases") | FIDE Council, 29 Sep 2025; Handbook §8.3.1\[1\]\[23\] |
| 2026 calendar | 45+30 (and 60+30) time controls may be rated as **standard** for QC-approved major/traditional events, continuing a late-2025 pilot | FIDE news, 2026\[24\] |
| 26–27 Sep 2026 | FIDE General Assembly, Samarkand: **Timur Turlov elected President** (110–85 over Wadim Rosenstein in the run-off), **Viswanathan Anand Deputy President**; GA approved plans for a **dedicated Chess960 rating system** | FIDE; ChessBase 4 Oct 2026; Chess.com\[25\]\[26\] |

**Rules in force today (FIDE Rating Regulations effective 1 March 2024, with the 1 Oct 2025 amendment):**
- **Rate of play (§1):** at least 120 min per player if either player is rated 2400+; at least 90 min if either is 1800+; at least 60 min if both are below 1800.\[1\]
- **Newcomers (§7.1.4, §8.2):** a rating is published after at least 5 games against rated opponents, pooled over up to 26 months, and it must be at least 1400. A zero score in a player's first event is disregarded. Ra is the average of the rated opponents plus two hypothetical 1800-rated opponents, scored as draws. Ru = Ra + dp, with a maximum of 2200.\[1\]
- **Floor (§7.2.1):** a player whose rating drops below 1400 is shown as unrated on the next list.\[1\]
- **Inactivity (§7.2.2):** a player becomes inactive after one year with no rated games and becomes active again after one game.\[1\] Ratings do not decay.
- **K (§8.3.3):** 40 for a new player until 30 games; 20 below 2400; 10 once a published rating reaches 2400, permanently; 40 for juniors until the end of the year they turn 18, while rated below 2300. If K × n > 700 in a period, K is reduced so that K × n ≤ 700.\[1\]

**2025–2026 proposals and elections.** FIDE CEO Emil Sutovsky, quoted by Chess.com when the October 2025 change was introduced, said there were "at least five players more of 2650+ level who, in 2024-25 regularly played events with a string of very low-rated opponents, abusing 400-points rule." Dvorkovich said in 2025 that FIDE must "think in the long term… not only with farming the rating, but also the whole subject of the inactivity".\[27\] I found **no published rating-reform plank** in the 2026 election platforms of Turlov/Anand, Rosenstein/Tang or Buettner/Pein. Turlov's press release promised "digital transformation".\[28\] This is an open lobbying opportunity: Anand, now Deputy President, is a former world champion with credibility on the topic.

**Other systems for comparison.**

| System | Method | Recent changes |
|---|---|---|
| US Chess | Glickman/Doan system: Elo-like with Glicko-style uncertainty logic, bonus points, a "special" algorithm for new players | B (bonus threshold) lowered 14→12 in 2023 and 12→10 retroactive to 1 Jan 2025, because "ratings on average continue[d] to deflate over time and are well below rating levels at the end of 1997"; FIDE→US Chess conversion revised Mar 2024,\[29\]\[30\] then an error found that made converted ratings about 200 points too high for FIDE < 2000; a rating-variance proposal (Feb 2024) is under Executive Board review; the rating infrastructure is being rebuilt\[31\]\[32\] |
| Lichess | Glicko-2,\[33\] start 1500, rating deviation (RD) shown | Median rating stable near 1500\[34\] |
| Chess.com | Glicko (Glicko-1, per community sources)\[34\] | Not verified from a primary source |
| Universal Rating System (URS) | Sonas, Glickman, Miller, Rischard; one rating combining classical, rapid and blitz | Used for Grand Chess Tour 2017 seeding; Sonas's 2023 supplemental report notes QC considering URS as an "auxiliary rating"\[35\]\[36\] |

---

## 3. Existing problems: evidence, demand and the assumption each one breaks

**Plain-language takeaway:** Most complaints trace back to two facts. Some players' real strength changes faster than their rating can follow, mainly juniors. And many player pools barely mix, mainly countries. Everything else is second-order.

### 3.1 Deflation and inflation (A3, A4, A6): demand very high, evidence strong
- **Evidence.** Sonas (July 2023, hosted by FIDE) wrote: "the past decade has brought extreme rating deflation to the FIDE Standard Elo".\[37\] He found that strength differences between players rated 1000 and 2400, about 99% of players, actually span only about 1000 Elo, not 1400. A 600-point gap "isn't as large a difference in performance as it was 10 years ago".\[38\] The mechanism: large numbers of newcomers enter with low ratings, outperform them, and drain points from established players.\[39\] His supplemental report concluded that deflation "has almost certainly reached the top 1,000".\[35\]
- **After the reform.** Ghita (June 2025) found about 3,500 new standard-rated players a month, the average falling about 1 Elo a month, deflation at every percentile including the top 1%, the 1800–1999 band "slowly being replaced by the 1400–1599 band", and an artificial pile-up at 1400.\[3\]\[4\] Ghita (Feb 2026) reported a −26 Elo per year median loss before the reform and −16 after, 165k+ newcomers in 2021–2025 (a 47% expansion), and a 37% shrinkage of the 2600–2699 band between 2021 and 2025.\[5\] ChessBase (May 2026) noted that Carlsen (2840) was the only 2800+ player and that "Elo deflation… perhaps… has already reached the elite level".\[40\]
- **Critiques.** Christian Milvang argued in a 12-page response that the 1400 floor splits players into rated and unrated, that ratings in the 1400–1600 range are "highly unreliable", and that "there are no mechanisms to prevent deflation".\[2\] A Canadian commenter objected that compression breaks the principle that a rating "can be changed only at the chess board".\[41\]
- **Demand indicators.** Official FIDE acknowledgement (2023 consultation, 2024 reform); 150+ consultation comments;\[18\]\[19\] recurring Lichess, Chess.com and ChessBase threads; US Chess facing the same problem.\[29\]

### 3.2 Federation and geographic isolation (A5): demand high and rising, evidence moderate to strong, no official fix
- **Evidence.** Ghita's 2026 study used about 189k cross-border games in 2025, excluded federations with fewer than 1,000 such games, and applied a recursive travel-adjusted correction. It found Vietnam +101 and Switzerland/Austria −64.\[6\] It says "In some events, a player's federation is a better predictor of the result than their rating", and calls modern chess "a single global currency across partially disconnected local markets."\[6\] Ghita's 2025 essay gave the example of the Sunway Sitges 2024 open, where of about 20 Indian players rated below 2000, only one finished below their starting rank.\[4\]
- **Caveat.** The brief's "over 80% of rated games are within one federation" figure is **not verified**. The only support is an inference: 189k cross-border games out of a sample of about 955k would imply roughly 80% domestic, but the sample spans 2021–2025. Ghita's offsets come from a book published with a foreword by GM Levon Aronian.\[6\] They are not peer-reviewed, and the full method is paywalled.
- **Mechanism (Ghita).** A draw between a Spanish 1900 and an Indian junior listed at 1500 but playing at 1900 strength costs the Spaniard 8.4 points.\[5\] Commenters add that FIDE-rated events are far more common in some countries than others, so isolation is amplified.\[42\]

### 3.3 Juniors (A4): demand very high, evidence strong
Juniors improve faster than K = 40 can track. Ghita's age-cohort data (2021–2025) show that U16 players gain consistently even after accounting for the K asymmetry, and that juniors who trained during the pandemic freeze were "undervalued by hundreds of points once they resumed play".\[4\]\[6\] Community proposal: a "junior addition", meaning opponents of juniors are rated as if the junior had a higher rating than published.\[43\]

### 3.4 K-factor and bracket edges (A3): demand medium, evidence moderate
In 2002 Sonas argued K = 24 would predict better than K = 10 at the top;\[44\] John Nunn disputed this ("show me the proof", 2009).\[45\] The 2008–2011 trial of higher K drew "major concern especially among the top players".\[16\] Bracket cliffs exist at 30 games, at 2300 for juniors, and at 2400 (a permanent K = 10 switch), and the 700-point cap per period reduces K for very active players.\[1\] None of these has an evidential basis beyond convention.

### 3.5 Forecast accuracy across rating gaps (A1): demand medium (mostly experts), evidence strong
In 2011, after analysing 1.5 million FIDE games, Sonas found that actual results for a rating gap X behave like a gap of about 5/6 X.\[44\] Examples: a 240-point favourite scores about 76% rather than 80%, and a 180-point favourite about 70% rather than 73%. Under the then-capped table, players with 700+ point advantages scored 98–100% against an expected 92%.\[46\] That is the 400-point cap distorting the curve. Sonas warned in October 2025 that after the cap was lifted for players rated 2650+, "their Elo expected score can now be as high as 99% or even 100%".\[47\]

### 3.6 Draws (A2): demand low to medium, evidence strong
Draw rates rise steeply with level: they rarely happen at low ratings and occur in about half of games among strong players (large-database study, arXiv 1607.04186).\[48\] TrueSkill Through Time found that modelling a player's "ability to force a draw provides significantly better predictive power".\[49\] Elo predicts only expected score, not draw probability.\[50\] That matters for calibration metrics and for detecting manipulation, such as pre-arranged draws.

### 3.7 Colour advantage and colour-count imbalance (A2): demand low, evidence strong for the advantage, weak for the imbalance
- White scores about 54–55% overall (Chessgames.com, 2015: 37.5% wins, 34.9% draws, 27.6% losses, a 54.95% score). In a ChessBase article of 22 October 2002 based on 266,000 games from 1994–2001, Sonas valued the White pieces at 35 rating points, so White is expected to score 54% when ratings are identical. He also found White's edge smaller in rapid (53%). A 2014 analysis found White's excess over Elo expectation to be about 3.4%.\[51\] Among decisive elite games (2700+), White wins about 64%.\[52\]
- **Assessment.** Pairing rules (Swiss colour allocation, round-robin balance) keep most players' colour counts near even, so the cumulative effect on any one player's rating is small. A colour term mostly improves per-game forecasts and fairness in short events and odd-round Swisses. The user's hypothesis, that a player who gets more Whites gets an advantage, is plausible at the margin, but **I found no published quantification of per-player colour imbalance in FIDE data**. This is a cheap, testable item for the repo.

### 3.8 Rating protection and strategic game selection (A7): demand high at elite level, evidence strong, partly fixed
The rating-based Candidates spot rewards sitting on a rating. FIDE's 2026 cycle used a six-month average and a 40-game minimum: Nakamura qualified at 2810.5 average with 40 games, while Carlsen did not qualify on rating with 16 games.\[8\] Maxime Vachier-Lagrave proposed using performance rating instead, and Caruana agreed; FIDE did not adopt it.\[53\] Sutovsky: "No more farming. If you are a 2650+ player, do prove your skill vs opponents of comparable strength."\[7\] Nakamura: "it's not about farming".\[54\]

### 3.9 Manipulation: sandbagging, fixed games, rating farming (A7): demand medium, evidence anecdotal
The 400-point cap created a measurable arbitrage: each win against a 2250-rated opponent earned Nakamura 0.8 points, totalling 9 points across 11 games.\[55\] According to Wikipedia's "Candidates Tournament 2026" entry, since 1 October 2025 a 2650+ player who beats an opponent 400 points lower gains only 0.1 points, and nothing at all at a 735-point gap. Below the elite level, evidence is mostly anecdotal. FIDE has a Tournament Investigation Form and QC appeal rules,\[1\] which suggests that suspicious tournaments do occur. The repo should include anomaly detection, such as clusters of players with unusual win/loss graphs.

### 3.10 Inactivity: demand medium, evidence moderate
Ratings never decay, and about 40% of listed players "haven't played since before the pandemic" (Ghita 2026).\[5\]\[56\] Dvorkovich named inactivity as a long-term issue in 2025.\[27\]

### 3.11 COVID-era effects (A4): demand medium, evidence moderate
The 2020 near-shutdown froze ratings while juniors trained online. FIDE OTB activity rebounded strongly: 2024 was the most active year on record, with about 3.5 million rated games projected for 2025 (Ghita).\[3\]\[4\]

### 3.12 Online vs OTB divergence: demand very high in forums, low relevance
The Lichess FAQ calls Elo "dated" and stresses that cross-system comparisons are meaningless.\[34\]\[57\] Lichess satirised the 2024 compression on April Fools' Day.\[58\] This is a communication issue, not a FIDE design target. Out of scope, except as a data source.

### 3.13 Matchmaking and selection effects: the "Matchmaking Ruins Everything" claim
- **Claim (Charlie Olson, Medium, Oct 2023).** With perfect skill-based matchmaking (SBMM), equal-skill players' ratings spread into a uniform distribution, and Elo "will continue expanding indefinitely" under SBMM. TrueSkill expands less. The article links this to FIDE's statement that ratings are "spread out too widely".\[59\]
- **Assessment.** The core mechanism is sound. Elo corrects an over-rated player only when that player meets correctly rated opponents. If over-rated players meet only similarly over-rated players, the errors cancel and nothing corrects. However: (a) the ASCII example uses fixed ±1 steps, not Elo's expectation-weighted steps, so it exaggerates; (b) the effect is about **spread**, while FIDE's main problem is the **level** (deflation from underrated entrants), although Sonas's finding that FIDE ratings are "too spread out" fits both; (c) OTB Swiss events are the opposite of tight SBMM. Round 1 pairs the top half against the bottom half, producing many 200–600-point gaps, which supply exactly the cross-level mixing Elo needs. **Verdict:** the argument matters for online pools and for **isolated federations**, where domestic-only play is the chess analogue of SBMM. It does not apply to well-mixed OTB opens. The repo's simulator should test it directly.

---

## 4. Proposals by players and experts

**Plain-language takeaway:** Statisticians have repeatedly built systems that predict results better than Elo. FIDE has adopted only the simple, explainable pieces: floors, K values, initial-rating tweaks and one-off compressions.

| Proposal | What it changes | Evidence it works | Main objection | Adoption |
|---|---|---|---|---|
| **Sonas 2023 "Repairing the FIDE Standard Elo"** + Supplemental Report | One-off compression below 2000; floor 1400; two fictitious 1800 draws for newcomers; "mild inflationary effects"; supplemental report weighed a lesser "Compression to 1200" and URS as an auxiliary rating\[35\]\[39\] | Simulation of the FIDE pool; residual analysis of 2008–2023 data | Milvang: resets but doesn't stop deflation; breaks "only at the board" principle\[2\]\[41\] | **Adopted (core), Mar 2024** |
| **Sonas linear expectancy / "Sonas formula" (2002) & 5/6-gap correction (2011)** | Replace normal table with flatter/linear curve; K ≈ 24 | Better fit on 1.5M FIDE games\[44\] | Nunn: insufficient proof; changes norm/title arithmetic | Not adopted |
| **Elo++ (Sismanis, Kaggle 2010)** | Logistic Elo with L2 regularisation weighting games by count, recency and opponents; only two global parameters, **White's advantage** and the regularisation constant | Won "Elo vs the Rest of the World"; Elo benchmark 141st of 258\[60\]\[61\] | Batch fitting, not a simple per-game update | Not adopted |
| **Salimans (Kaggle/Deloitte 2011, $10,000 winner)** | TrueSkill-inspired Bayesian model with shrinkage toward opponents | Won on 1.84M games, 54,000 players, 11 years | Winner admitted much of the edge came from "information in the match schedule", which is not legitimate for an official rating\[9\]\[60\]\[62\] | Not adopted |
| **Stephenson system (2011 FIDE Prize)** | Glicko plus Sismanis ideas plus data-driven tweaks | Judged "most promising practical" system; presented to FIDE\[63\] | Complexity | Not adopted |
| **Glicko / Glicko-2 (Glickman)** | Adds rating deviation (RD) and volatility (σ), so step size adapts | Basis of Lichess, US Chess logic, Australian CF | RD is less intuitive; vulnerable to strategic inactivity | Not FIDE\[64\] |
| **URS (Sonas, Glickman, Miller, Rischard, 2017)** | Single rating across classical, rapid and blitz, with global re-estimation | Used for GCT seeding\[36\] | Opaque to players; one rating can't capture time-control differences | GCT only; QC "considered" as auxiliary |
| **Whole-History Rating (Coulom, 2008)** | Dynamic Bradley–Terry fitted over a player's whole history (MAP via Newton's method) | Beat Elo, Glicko, TrueSkill on KGS (10.8M games); new game in < 0.001 s; used by goratings.org and the Renju federation | Past ratings revise retroactively | Go/Renju (unofficial or federation)\[11\]\[12\]\[65\]\[66\]\[67\]\[68\] |
| **TrueSkill Through Time (Dangauthier, Herbrich, Minka, Graepel, NIPS 2007)** | Smoothing instead of filtering; explicit draw-ability | 3,505,366 games, 206,059 players (1850–2006); draw modelling improved prediction | Retroactive revision | Research; open packages (Julia/Python/R, JSS 2025)\[69\]\[70\] |
| **Ken Regan's intrinsic performance ratings** | Ratings from move quality versus an engine | Strong for anti-cheating | Excluded by user (compute and transparency) | Anti-cheating context only |
| **Ghita 2025–2026 ("FIDE Ratings Revisited"; "Why chess ratings don't mean what they used to"; book *The Rating Revolution*)** | Two-layer repair: a global deflation mechanism plus federation-divergence correction, with "safeguards, monitoring conditions, and rollback criteria" | Federation offsets (CBPI/FDI) over 73 federations\[5\] | Paywalled method; political viability of country offsets, which commenter NoseKnowsAll doubts\[42\] | Not adopted\[3\] |
| **Community: asymmetric K for cross-federation games** | e.g., K_winner × 1.25, K_loser × 0.8\[42\] | None (forum idea) | Injects points arbitrarily | — |
| **MVL/Caruana: performance-based Candidates rating spot** | Selection rule, not rating rule | — | — | Not adopted\[53\] |
| **Milvang (Norway)** | Revise the formula; remove the floor; adjust for games played | Norway ran a national system down to 600 until 2017\[2\] | — | Not adopted |

**On-record views of players and officials.** Dvorkovich (2025) took the blame for the rating system's "deficiencies".\[27\] Sutovsky called for "no more farming".\[7\] Nakamura denied farming.\[54\] Nepomniachtchi said FIDE "literally doesn't care about the rating spot", though that quote comes from a secondary aggregator.\[71\] I could **not verify** recent on-record statements on deflation from Carlsen, Caruana (beyond agreeing with MVL), Anand, Gukesh or Kramnik. Treat any such claims as unverified until a primary interview is found. Levon Aronian wrote the foreword to Ghita's 2026 book,\[5\] which signals elite sympathy for reform.

---

## 5. Where the current system lives, and the code and data landscape

**Plain-language takeaway:** The rules are public and short enough to code exactly. Player-level monthly lists can be downloaded. The game-by-game data you need is the gap: FIDE has it, so ask for it.

- **Rules:** "FIDE Rating Regulations effective from 1 March 2024" (Handbook B.02, https://handbook.fide.com/chapter/B022024). The calculation is defined in §7 (lists, newcomers, floor, inactivity) and §8 (tables 8.1.1 and 8.1.2, initial rating 8.2, rating change 8.3, K in 8.3.3, rounding in 8.3.4). The 1 October 2025 amendment is embedded in §8.3.1. Rapid & Blitz rules are in a separate chapter, also effective 1 March 2024. Older versions (2014, 2017, 2022) are archived, which helps back-test historical periods.\[1\]
- **Official calculators:** https://ratings.fide.com/calc.phtml (rating change, etc.), linked from the Handbook.\[1\]
- **Monthly lists:** https://ratings.fide.com/download_lists.phtml. The October 2026 list (dated 07 Oct 2026) comes as TXT and XML: a combined standard/rapid/blitz file of about 42.6 MB TXT, separate standard (12.7 MB), rapid (10.7 MB) and blitz (7.3 MB) files, and a legacy file that includes unrated players. Fields include ID, name, federation, sex, title, rating, games per period (SGM/RGM/BGM), K (SK/RK/BK) and year of birth.\[72\] I found no explicit licence on the page. Treat it as publicly downloadable but ask FIDE for written permission to redistribute.
- **Game-level data:** individual calculation pages on ratings.fide.com show per-opponent results, but I did not verify their terms of use, and scraping them at scale is legally and ethically unclear. Tournament reports are submitted to FIDE as TRF files (§9.1),\[1\] so **FIDE holds a complete, machine-readable game archive.** That is the "eventual ask". The 2011 Kaggle dataset (1.84M games, prepared by Sonas from FIDE archives)\[60\]\[62\] may still be on Kaggle's competition page, but I did not verify that it is still available.
- **Lichess open database:** https://database.lichess.org, released under **CC0** (broadcast games under CC BY-SA 4.0). It holds 8,220,312,882 standard rated games in monthly PGN files\[73\]\[74\] and about 100 million games per month.\[75\]\[76\] A Hugging Face parquet mirror (Lichess/standard-chess-games) totals about 4.94 TB.\[77\] It includes over 900,000 OTB broadcast games since 2020, which is a useful OTB slice.\[74\]
- **Other OTB sources:** The Week in Chess (weekly PGN of elite and open events), the US Chess member services and ratings archive, the English Chess Federation rating database, and chess-results.com (tournament pairings and results for most FIDE-rated events). **I did not verify the terms of use for automated collection for any of these.** Assume permission is required before scraping chess-results.com.
- **Open-source code:**

| Component | Repo / source | Language | Notes |
|---|---|---|---|
| FIDE list utilities | github.com/samuraitruong/fide-ratings-utils; github.com/rmarabini/player_info_from_fide_database | Python | Parse and split official lists; not calculators\[78\]\[79\] |
| WHR | github.com/Remi-Coulom/WHR (C++, the paper's code); github.com/goshrine/whole_history_rating (Ruby, 85 stars); github.com/wind23/whole_history_rating (Python/C++) | C++/Ruby/Python | Licence not verified\[80\]\[81\]\[82\] |
| TrueSkill Through Time | CRAN "TrueSkillThroughTime" (+ Julia/Python), JSS doi:10.18637/jss.v112.i06 | R/Julia/Python | Peer-reviewed implementation\[70\] |
| BayesElo | remi-coulom.fr (Coulom 2005) | C++ | Batch MLE with draw and White-advantage terms\[11\] |
| Lichess Glicko-2 / database exporter | github.com/lichess-org (lila, database) | Scala | lila licence believed AGPL (verify) |
| Ordo, Glicko-2 libraries, TrueSkill | various | — | **Not verified this session**; check licences |

  **No repository I found claims to reproduce FIDE's official calculations exactly**, including the §8.1.2 table, the 400/2650 rule, the K × n ≤ 700 cap, rounding, the newcomer pooling window and the floor removal. That gap is the repo's first deliverable.

---

## 6. Dynamic, self-evolving rating systems

**Plain-language takeaway:** The engine should re-learn its own settings every month from the last few years of games, such as how big White's edge is, how often strong players draw and how fast juniors improve. It should then change the published rating only through small, announced, rule-based adjustments.

- **Methods.** State-space models treat skill as a random walk: a Kalman filter for forward updates and a smoother (TrueSkill Through Time, WHR) for re-estimation.\[83\] Glicko's RD and Glicko-2's volatility give adaptive step sizes. Time-varying global parameters (colour offset, draw parameter, time-control offsets) can be re-estimated on a rolling 24–36-month window. Drift correction can use anchor sets of stable adult players, a measure Glickman uses at US Chess: "mean ratings of stable players", with the stated "goal is to maintain rating" level.\[22\]
- **Adaptivity vs stability.** Smoothing models revise the past, which is unacceptable for an official, forward-only list. The two-layer design solves this. The back end may revise its estimates freely, while the front end only moves forward. US Chess is the precedent for controlled recalibration through a published constant (the bonus threshold B, 14→12→10).\[32\] FIDE's 2024 compression is the precedent for a one-off level reset.
- **How chess changed, 2023–2026 (data found).** Rated-player growth: 165k+ newcomers to the standard pool in 2021–2025 (+47%), about 3,500 new standard-rated players a month, and 1,643,067 players on FIDE lists in May 2025 (502,209 with a standard rating).\[4\]\[5\]\[84\] Activity: 2024 was the busiest year on record, with about 3.5 million standard-rated games projected for 2025.\[4\] Geography: India and other Asian federations are growing, and the leading federations by player count include Russia (about 34,800 rated players in May 2025).\[84\] Online-to-OTB: the Lichess broadcast archive and Ghita's age data show a pandemic-trained junior cohort entering OTB underrated. Format: from 2026, 45+30 can count as standard for approved events,\[24\] which slightly blurs the line between classical and rapid. **Draw rates and colour advantage for 2024–2026 specifically were not found.** The repo should compute them from Lichess and FIDE data.

---

## 7. An AI or computational rating calculator FIDE can use

**Plain-language takeaway:** The computation is trivially cheap. The real requirements are trust: anyone must be able to rerun the calculation and get the same number, and understand why it moved.

- **Compute.** FIDE handles about 3–3.5 million standard games a year plus rapid and blitz. WHR adds a game in under 0.001 seconds and processed 10.8 million Go games on a 2008 single-thread CPU.\[11\]\[12\] A monthly full re-fit of a few million games is a laptop-scale job. **Cost is not a constraint.**
- **Precedents.** FIFA replaced its custom ranking with the Elo-based "SUM" method, approved by the FIFA Council in Moscow on 10 June 2018 and used from 16 August 2018. ChessBase quoted its stated aims as "simplifying and refining the formula, eliminating opportunities to manipulate the rankings and giving all teams the same opportunity to improve their ranking". FIFA's women's ranking has been Elo-based since 2003. A retrospective found that the switch narrowed FIFA's predictive gap against independent Elo from 6.0 to 3.2 percentage points (ResearchGate preprint, not peer-reviewed).\[85\] Go uses WHR (goratings.org, unofficial).\[67\] Microsoft's TrueSkill/TrueSkill 2 power Xbox matchmaking, which is commercial and opaque. UTR (tennis) and esports MMR systems are mostly proprietary; I did not research them in depth this session. The lesson: **official sports bodies have accepted simple, published Elo variants, while black-box ML ratings remain confined to commercial matchmaking.** Olson's Medium article itself notes that TrueSkill's shrinking step size makes it "ripe for smurfing" and "problematic for player-facing MMR".\[59\]
- **Requirements for an official rating:**
  1. **Determinism and reproducibility:** fixed-precision arithmetic, rounding as in §8.3.4, versioned parameters, identical output from identical TRF input.
  2. **Transparency:** every published parameter (K, curve, colour term, offsets) in a public file per list.
  3. **Auditability:** a per-game breakdown a player or arbiter can check by hand. Players must still be able to calculate their own norm requirements; Ghita notes FIDE leadership's belief that only Elo allows this.\[4\]
  4. **Explainability:** corrections attributable to named rules (for example "junior-opponent adjustment +X").
  5. **Open-source code** under an OSI licence, with test vectors matching FIDE's calculator.
  6. **Governance:** QC owns the parameters, changes are approved by Council, with a public comment period (the 2023 consultation is the model).
  7. **Fairness and bias:** monitor residuals by federation, age, sex and rating band.
  8. **Manipulation resistance:** no exploitable cliffs like the old 400-point cap; anomaly detection; avoid incentives to stay inactive.
- **The "AI" framing.** Present it as a **statistical model with machine-learned parameters**, re-estimated monthly, rather than a neural network. That meets the user's goal of a cheap per-game calculator FIDE can run, while staying inside the trust requirements.

---

## 8. One framework across time controls

**Plain-language takeaway:** Use one core skill per player, with a separate offset for each style. A rapid specialist can then be stronger at rapid without the system pretending it's a different person.

- **Prior work.** URS combined classical, rapid and blitz into one list, from August 2016 onward.\[36\] FIDE runs three independent lists, each with its own K, floor and newcomer rules, all aligned since March 2024.\[20\]\[36\] TrueSkill-family and WHR models extend naturally to multi-dimensional skill, for example a shared latent skill plus a correlated deviation for each time control.
- **Recommended structure.** skill_tc(player, t) = θ(player, t) + δ_tc(player, t). θ is shared across time controls. Each δ is shrunk toward zero with time-control-specific variance, and each time control has its own colour and draw parameters (White's edge is smaller in rapid, 53% according to Sonas)\[86\] and its own random-walk volatility. Games in one time control then inform priors in the others. This is especially valuable for newcomers and for players with few classical games.
- **Evidence gap.** I did not retrieve a quantified cross-time-control correlation for FIDE players in this session. Estimating it from FIDE's combined list (players rated in all three) and from Lichess is a first-week repo task.

---

## 9. How to prove an improvement

**Plain-language takeaway:** Freeze the past, predict next month, score the predictions, and repeat. Then show in a simulation that the new system recovers known "true" strengths better and resists cheating.

- **Forecast metrics.** Log-loss over the three outcomes (win/draw/loss; requires a draw model), Brier score, and calibration plots by rating gap, rating band, colour, time control and federation pair. The Kaggle contests used similar binomial-deviance-style scoring, with leaderboard values around 0.25 in 2011.\[87\]
- **Backtest protocol.** Rolling-origin evaluation: train on months up to t, predict month t+1, roll forward. Never use the match schedule as a feature, which Salimans noted dominated Kaggle 2011.\[9\]
- **Drift metrics.** Mean rating of a stable anchor cohort (adults aged about 25–45 with consistent activity) over time, as Glickman does. Score of fixed rating bands against each other over years. Rating velocity by age cohort.
- **Cross-federation comparability.** Mean residual (actual − expected) in cross-border games by federation, which should shrink toward zero. Network connectivity statistics, such as the share of games within each federation.
- **Newcomer convergence.** Games until the error is below 50 Elo in simulation. Prediction error over a player's first 30 games.
- **Manipulation resistance.** Simulated adversaries (farmers, sandbaggers, colluding rings, inactive protectors) measuring points gained per unit of effort.
- **Simulation with known truth.** Generate players with age-dependent improvement curves, federation-clustered pairings, Swiss pairings (top half against bottom half in round 1), and entry and exit flows. Run FIDE-exact rules and candidate rules side by side.

---

## Recommendations

**Design (hypothesis (c), refined):**
1. **Layer 0, the reference engine.** An exact, test-vector-verified implementation of FIDE's 2024 rules as amended in 2025, for standard, rapid and blitz. This alone is a contribution, and it is the credibility anchor with FIDE.
2. **Layer 1, the behind-the-scenes model.** A dynamic Bradley–Terry–Davidson model with skill θ, time-control offsets δ, a colour term and a level-dependent draw term. Fit it by Kalman smoothing or WHR on a rolling 36-month window and re-estimate monthly. Outputs: calibrated forecasts, federation and pool offsets, junior improvement rates, and the global drift estimate.
3. **Layer 2, the published rating.** Forward-only and Elo-style on today's scale, updated per game by an explainable formula: R += K_eff × (S − E). E uses a calibrated logistic curve with a colour term and the 400-point clamp handled consistently. K_eff depends on uncertainty (Glicko-style) with smooth, cliff-free decay instead of 40/20/10 brackets. Point flows from the model enter only through named, published channels:
   - newcomer seeds from the model's posterior, replacing the fixed 1800 phantom draws;
   - junior-opponent compensation, so that losing to an underrated junior costs less;
   - a monthly pool-level drift correction, capped at a few points, as with US Chess's bonus constant;
   - a slow federation-offset correction applied only through cross-border game expectations, never by editing ratings directly.
4. **Parameters.** Publish them each month in a versioned file, with a rule that no parameter moves more than a set amount per year, to protect comparability across years.

**Process:** build Layer 0 and the simulator first. Backtest on Lichess and the OTB broadcasts. Publish results. Then formally request FIDE's TRF archive under a data-sharing agreement, pitched to the new Turlov/Anand administration as a "digital transformation" deliverable.

### Ranked problem table

| Rank | Problem | Maps to | Community demand | Evidence strength | Fixability | Target? |
|---|---|---|---|---|---|---|
| 1 | Deflation (junior and newcomer driven) | A3, A4, A6 | Very high (FIDE acknowledged; 2024 reform) | Strong (Sonas 2023; Ghita 2025–26; US Chess parallel) | High (seed, junior and drift channels) | **TOP** |
| 2 | Federation/geographic isolation | A5 | High, rising (2025–26) | Moderate–strong (not peer-reviewed) | Medium (needs FIDE game data; politically sensitive) | **TOP** |
| 3 | Top-level protection/farming; rating-spot gaming | A7 | High at elite level; FIDE acted Oct 2025 | Strong (documented cases) | High (consistent curve, uncertainty-weighted K) | **TOP** |
| 4 | Expectancy-curve miscalibration | A1 | Medium (experts) | Strong (Sonas 2011; Kaggle) | High (re-fit curve) | **TOP (technical)** |
| 5 | Juniors underrated | A4 | Very high | Strong | High (part of #1) | Folded into #1 |
| 6 | K-factor brackets/cliffs | A3 | Medium | Moderate | High | Yes, via K_eff |
| 7 | Inactivity/ghost ratings | A6, A7 | Medium (Dvorkovich) | Moderate (~40% ghosts) | Medium (RD growth, no decay of published rating) | Secondary |
| 8 | Draws not modelled | A2 | Low–medium | Strong | High (inside Layer 1) | Inside model |
| 9 | Colour advantage/imbalance | A2 | Low (user priority) | Strong for advantage, weak for imbalance | High | Inside model; quantify imbalance |
| 10 | Manipulation (lower levels) | A7 | Medium | Anecdotal | Medium | Monitoring |
| 11 | Online vs OTB divergence | — | Very high (forums) | N/A | Low (not FIDE's job) | No |
| 12 | Matchmaking flattening | A5 | Low | Theoretical, plausible for isolated pools | — | Test in simulator |

### Candidate fixes for the top problems

| Problem | Candidate fix | Mechanism | Evidence it works | Who backs it | Strongest objection | Data to test |
|---|---|---|---|---|---|---|
| Deflation | Model-based newcomer seeds | Seed = posterior from early games plus age prior | Sonas simulation supported the 1800-draw seed; Bayesian priors standard in Glicko/TTT | Sonas; Glickman (US Chess "special" algorithm) | Seeds could inflate if the prior is biased | FIDE TRF; simulation |
| Deflation | Junior-opponent compensation | Opponents' expectation uses the junior's model skill, not their published rating | Ghita cohort data show systematic junior over-performance | Forum proposals; Ghita | Points not conserved | FIDE games with birth years (lists include B-day) |
| Deflation | Capped monthly drift correction | Inject points to hold an anchor cohort's mean level | US Chess bonus constant B lowered 2023 and 2025 | Glickman/US Chess RC | "Artificial" points; Milvang-type critique | Anchor cohort from FIDE lists |
| Federation isolation | Cross-border offset learning | Estimate pool offsets from cross-border games; apply through expectations only | Ghita: +101 (VIE) to −64 (SUI/AUT) | Ghita; URS idea; Aronian (foreword) | Political: "country penalties"; small samples | ~189k cross-border games/year; FIDE TRF |
| Federation isolation | Global re-estimation (URS/WHR-style) | Joint fit across all games propagates information through bridge players | URS used in GCT; WHR on 10.8M games | Sonas, Glickman | Bridges may themselves be unrepresentative (Lichess forum objection) | FIDE TRF |
| Farming/protection | Consistent calibrated curve; no clamp cliffs | Removes arbitrage from capped expectations | Sonas: 98–100% actual vs 92% expected under the cap | FIDE (Oct 2025 partial fix); Sutovsky | Elite players fear rating losses from weak events | FIDE elite games |
| Farming/protection | Uncertainty-weighted K (Glicko RD) | Inactive players' K grows when they return; small steps when active | Glicko/Glicko-2 adoption; Kaggle | Glickman | "Rating holders" lose stability | Simulation; FIDE |
| Curve | Re-fit expectancy (logistic, flatter, level-dependent draw) | Fit P(win/draw/loss) by gap, level and colour | Sonas 5/6-gap; TTT draw model; Elo++ White term | Sonas; Kaggle winners | Breaks title-norm arithmetic tables | Lichess + FIDE; rolling backtest |

### Code and data sources

| Source | URL | Licence/terms | Suitability |
|---|---|---|---|
| FIDE Rating Regulations (2024, amended 2025) | handbook.fide.com/chapter/B022024 | Public document | Spec for Layer 0 (essential) |
| FIDE Rapid & Blitz Regulations 2024 | handbook.fide.com/chapter/B02RBRegulations2024 | Public | Spec for the rapid/blitz branches |
| FIDE calculators | ratings.fide.com/calc.phtml | Public web tool | Test vectors |
| FIDE monthly lists | ratings.fide.com/download_lists.phtml | Downloadable; no explicit licence found | Player-level panel (ratings, K, games, birth year, federation) |
| FIDE TRF archive | via FIDE QC/Ratings Office | Requires agreement | Gold standard (the ask) |
| Lichess open database | database.lichess.org | CC0 (broadcasts CC BY-SA 4.0) | Backtests, colour/draw/time-control parameters, simulator calibration |
| Lichess parquet mirror | huggingface.co/datasets/Lichess/standard-chess-games | CC0 | Fast analytics |
| Kaggle 2011 FIDE dataset | kaggle.com (ChessRatings2) | Competition rules; availability unverified | Historical benchmark |
| TWIC, chess-results.com, US Chess, ECF | respective sites | Terms not verified; get permission | OTB supplements |
| WHR code | github.com/Remi-Coulom/WHR; goshrine; wind23 | Verify | Layer 1 prototype |
| TrueSkillThroughTime | CRAN / JSS v112 i06 | Open-source package | Layer 1 alternative |
| FIDE list parsers | github.com/samuraitruong/fide-ratings-utils | Verify | Ingest utilities |

## Caveats

- **Unverified or secondary claims:** the >80% same-federation share; Ghita's offsets and deflation rates (independent, non-peer-reviewed, method partly paywalled); Chess.com's use of Glicko-1; licences of several repositories; terms of use of TWIC, chess-results.com, US Chess and ECF; availability of the Kaggle 2011 data; Nepomniachtchi's and Nakamura's quotes (secondary aggregator).
- **Projections, not facts:** "about 3.5 million games by end-2025" was Ghita's projection made in mid-2025.\[3\]
- **Date conflict:** FIDE's news says the Council approved the 2024 reform on 14 December 2023, while the Handbook says 15 December 2023.
- **Elections:** no rating-reform commitments by the 2026 tickets were found. Absence of evidence, not evidence of absence.

## Open questions the research could not settle

1. What share of FIDE-rated games is within one federation, by rating band and year? This needs FIDE TRF data.
2. Are federation offsets stable and causal (junior share, event scarcity, GDP), or artefacts of who travels? Ghita himself calls for multivariate analysis.\[3\]
3. What were draw rates and White's score in FIDE OTB play in 2024–2026, by level and time control?
4. How strongly do classical, rapid and blitz strength correlate for FIDE players today?
5. How large is per-player colour-count imbalance in FIDE events, and does it measurably move ratings?
6. Will FIDE's QC under the new Turlov/Anand administration accept a model-driven correction layer, and would title-norm arithmetic need to change?
7. Is there an exact, published reproduction of FIDE's calculator outputs anywhere? None was found, which is the repo's first deliverable.

## Sources

1. [B. PERMANENT COMMISSIONS / 02. FIDE Rating Regulations (Qualification Commission) / FIDE Rating Regulations effective from 1 March 2024 / FIDE Handbook](https://handbook.fide.com/chapter/B022024)
2. [FIDE Adjusts Ratings For 350,000 Players In Massive Change - Chess.com](https://www.chess.com/news/view/fide-adds-rating-points-to-more-than-300-000-players)
3. [FIDE Ratings Revisited • FRBE-KBSB-KSB](https://blog.frbe-kbsb-ksb.be/blog/fide-ratings-revisited/)
4. [FIDE Ratings Revisited - by Vlad Ghita](https://vladchess.substack.com/p/fide-ratings-revisited)
5. [The Rating Revolution — Vlad Ghita](https://vladchess.com/rating-revolution)
6. [Why chess ratings don't mean what they used to](https://vladchess.substack.com/p/why-chess-ratings-dont-mean-what)
7. [FIDE Scraps 400-Point Rule For 2650+ Players, 'Triggered By Nakamura' - Chess.com](https://www.chess.com/news/view/fide-introduces-hikaru-rule-from-october)
8. [Candidates Tournament 2026](https://en.wikipedia.org/wiki/Candidates_Tournament_2026)
9. [Tim Salimans: How I won the Deloitte/FIDE Chess Rating Challenge](http://www.chessmetrics.com/KaggleComp/1-TimSalimans.pdf)
10. [\[PDF\] TrueSkill Through Time: Revisiting the History of Chess](https://www.semanticscholar.org/paper/TrueSkill-Through-Time:-Revisiting-the-History-of-Dangauthier-Herbrich/fe8616a7b260472ae1b61d83f3f50fd5662a1dcc)
11. [Whole-History Rating: A Bayesian Rating](https://www.remi-coulom.fr/WHR/WHR.pdf)
12. [Whole-History Rating: A Bayesian Rating System for Players of Time-Varying Strength](https://www.remi-coulom.fr/WHR/)
13. [Chess rating system](https://en.wikipedia.org/wiki/Chess_rating_system)
14. [how elo ratings actually work](https://zwischenzug.substack.com/p/how-elo-ratings-actually-work)
15. [Elo rating system](https://en.wikipedia.org/wiki/Elo_rating_system)
16. [Rating Regulations - The K-Factor](https://old.fide.com/component/content/article/1-fide-news/3963-rating-regulations-the-k-factor.html)
17. [Changes to FIDE rating regulations - ChessTalk / Parlons Échecs](https://forum.chesstalk.com/forum/chesstalk-canada-s-chess-discussion-board-go-to-www-strategygames-ca-for-your-chess-needs/230682-changes-to-fide-rating-regulations)
18. [Proposals for changes to FIDE ratings regulations](https://en.chessbase.com/post/proposals-for-changes-to-fide-ratings-regulations)
19. [Proposals for changes to FIDE Ratings Regulations](https://www.fide.com/news/2784)
20. [New FIDE Rating and Title Regulations come into effect](https://www.fide.com/new-fide-rating-and-title-regulations-come-into-effect/)
21. [Proposals for changes to FIDE Ratings Regulations](https://www.fide.com/proposals-for-changes-to-fide-ratings-regulations/)
22. [US Chess Ratings Workshop July 18, 2024 Mark E. Glickman,](https://new.uschess.org/sites/default/files/media/documents/7-18-2024-ratings-workshop-2024.pdf)
23. [FIDE Council approves targeted amendment to Rating Regulation](https://www.fide.com/fide-council-approves-targeted-amendment-to-rating-regulation/)
24. [FIDE updates rating regulations to include faster time controls for major events](https://www.fide.com/fide-updates-rating-regulations-to-include-faster-time-controls-for-major-events/)
25. [Main decisions of the FIDE General Assembly 2026](https://en.chessbase.com/post/decisions-fide-general-assembly-2026)
26. [Timur Turlov elected President of FIDE](https://www.fide.com/timur-turlov-elected-president-of-fide/)
27. [Dvorkovich, “It is not Nakamura’s fault, it is our fault for the deficiencies in the rating system”](https://www.chessdom.com/dvorkovich-it-is-not-nakamuras-fault-it-is-our-fault-for-the-deficiencies-in-the-rating-system/)
28. [Timur Turlov Elected FIDE President, Becomes First Kazakh to Lead World Chess](https://www.prnewswire.com/news-releases/timur-turlov-elected-fide-president-becomes-first-kazakh-to-lead-world-chess-302890770.html)
29. [Ratings Committee Report](https://new.uschess.org/sites/default/files/media/documents/4-15-2024-rc-report-24-mm-eedit.pdf)
30. [FIDE Rating System Changes](https://new.uschess.org/civicrm/mailing/view?reset=1&id=4738&cid=)
31. [Ratings Committee Report](https://new.uschess.org/sites/default/files/media/documents/0001-2025-ratings-committee-report-rc-report-25-rm.pdf)
32. [Change to US Chess Ratings: Bonus Threshold Lowered](https://new.uschess.org/news/change-us-chess-ratings-bonus-threshold-lowered-2025)
33. [zwischenzug.substack.com](https://zwischenzug.substack.com/p/ratings-are-broken/comments)
34. [Chess rating systems • lichess.org](https://lichess.org/page/rating-systems)
35. [1 Compression and Calculation Improvements: Supplemental Report](https://www.fide.com/docs/presentations/Sonas%20Supplemental%20Report.pdf)
36. [Universal Rating System](https://en.wikipedia.org/wiki/Universal_Rating_System)
37. [1 Sonas Proposal: Repairing the FIDE Standard Elo rating system](https://www.fide.com/docs/presentations/Sonas%20Proposal%20-%20Repairing%20the%20FIDE%20Standard%20Elo%20Rating%20System.pdf)
38. [FIDE Mathematician Proposes Changes To Improve Rating Accuracy - Chess.com](https://www.chess.com/news/view/fide-mathematician-proposes-changes-to-improve-rating-accuracy)
39. [Sonas Proposal - Repairing the FIDE Standard Elo Rating System](https://www.scribd.com/document/668330896/Sonas-Proposal-Repairing-the-FIDE-Standard-Elo-Rating-System)
40. [FIDE ratings - May 2026](https://en.chessbase.com/post/fide-ratings-may-2026)
41. [Rating changes coming to FIDE? - ChessTalk / Parlons Échecs](https://forum.chesstalk.com/forum/chesstalk-canada-s-chess-discussion-board-go-to-www-strategygames-ca-for-your-chess-needs/227820-rating-changes-coming-to-fide)
42. [Why chess ratings don't mean what they used to • page 1/9 • Community Blog Discussions • lichess.org](https://lichess.org/forum/community-blog-discussions/ublog-tVDQ1LiL)
43. [FIDE Ratings Revisited • page 4/5 • Community Blog Discussions • lichess.org](https://lichess.org/forum/community-blog-discussions/ublog-BN89yF7d?page=4)
44. [Jeff Sonas](https://en.wikipedia.org/wiki/Jeff_Sonas)
45. [On the Probability of Magnus Carlsen reaching 2900](https://arxiv.org/pdf/2208.09563)
46. [The Elo rating system](https://en.chessbase.com/post/the-elo-rating-system-correcting-the-expectancy-tables)
47. [Why FIDE dropped the 400 point rule](https://en.chessbase.com/post/why-fide-dropped-the-400-point-rule)
48. [Large-scale Analysis of Chess Games with Chess Engines: A Preliminary Report](https://arxiv.org/pdf/1607.04186)
49. [Computer Gaming](https://herbrich.me/computer-gaming/)
50. [CheckRaiseMate's Blog • How Elo Ratings Actually Work • lichess.org](https://lichess.org/@/CheckRaiseMate/blog/how-elo-ratings-actually-work/J8UZThlO)
51. [First Move Advantage in Chess - An Antic Disposition](https://www.robweir.com/blog/2014/01/first-move-advantage-in-chess.html)
52. [Fairer Chess: A Reversal of Two Opening Moves in Chess Creates Balance Between White and Black](https://arxiv.org/pdf/2108.02547)
53. [FIDE Announces New Qualification Path For 2026 Candidates Tournament - Chess.com](https://www.chess.com/news/view/fide-announces-candidates-2026-qualification-changes)
54. [Hikaru Nakamura responds to critics: “I’m not farming for rating at state championships”](https://www.attackingchess.com/hikaru-nakamura-responds-to-critics-im-not-farming-for-rating-at-state-championships/)
55. [FIDE changes rating regulations](https://en.chessbase.com/post/fide-changes-rating-regulations)
56. [Rating analytics: The number of rated chess players goes up](https://www.fide.com/rating-analytics-the-number-of-rated-chess-players-goes-up/)
57. [Frequently Asked Questions • lichess.org](https://lichess.org/faq)
58. [FIDE adjusts its ratings to be more in line with Lichess (not really) • Lichess's Blog • lichess.org](https://lichess.org/@/Lichess/blog/fide-adjusts-its-ratings-to-be-more-in-line-with-lichess-not-really/ct5Uwjru)
59. [Matchmaking Ruins Everything](https://medium.com/invokation-games/matchmaking-ruins-everything-053f51527289)
60. [The Deloitte/FIDE Chess Rating Challenge](https://en.chessbase.com/post/the-deloitte-fide-che-rating-challenge)
61. [How I won the "Chess Ratings - Elo vs the Rest of the World" Competition](https://arxiv.org/pdf/1012.4571)
62. [Sonas: The Deloitte/FIDE Chess Rating Challenge](https://en.chessbase.com/post/sonas-the-deloitte-fide-che-rating-challenge)
63. [Could World Chess Ratings be decided by the ‘Stephenson System’?](https://medium.com/kaggle-blog/could-world-chess-ratings-be-decided-by-the-stephenson-system-2fba2715cf34)
64. [Glicko rating system](https://en.wikipedia.org/wiki/Glicko_rating_system)
65. [Whole History Rating (WHR) of Active Gomoku Players - Gomoku Rating](https://gomokurating.renju.net/)
66. [Whole-History Rating: A Bayesian Rating System for Players of Time-Varying Strength](https://link.springer.com/chapter/10.1007/978-3-540-87608-3_11)
67. [R%C3%A9mi Coulom](https://en.wikipedia.org/wiki/R%C3%A9mi_Coulom)
68. [Whole-History Rating: A Bayesian Rating System for Players of Time-Varying Strength](https://www.researchgate.net/publication/29621364_Whole-History_Rating_A_Bayesian_Rating_System_for_Players_of_Time-Varying_Strength)
69. [TrueSkill Through Time: Revisiting the History of Chess Pierre Dangauthier](https://www.herbrich.me/papers/ttt.pdf)
70. [TrueSkillThroughTime: Skill Estimation Based on a Single Bayesian Network](https://cran.rstudio.com/web/packages/TrueSkillThroughTime/index.html)
71. [Hikaru Nakamura Accused of "Farming" Ratings at Small Louisiana Tournament](https://www.attackingchess.com/hikaru-nakamura-accused-of-farming-ratings-at-small-louisiana-tournament/)
72. [Download latest official FIDE Rating list.](https://ratings.fide.com/download_lists.phtml)
73. [lichess.org open database](https://database.lichess.org/)
74. [Lichess's Blog • Lichess: End of Year Update 2025 • lichess.org](https://lichess.org/@/Lichess/blog/lichess-end-of-year-update-2025/YRiNKoaQ)
75. [Lichess rating to FIDE Elo : here we go again](https://antoinebfr.medium.com/lichess-rating-to-fide-elo-here-we-go-again-14d6a8fd31dc)
76. [number of games per month • page 1/1 • Lichess Feedback • lichess.org](https://lichess.org/forum/lichess-feedback/number-of-games-per-month)
77. [Lichess/standard-chess-games · Datasets at Hugging Face](https://huggingface.co/datasets/Lichess/standard-chess-games)
78. [GitHub - samuraitruong/fide-ratings-utils: Simple script to broken down fide rating file to smaller by federation, by age division · GitHub](https://github.com/samuraitruong/fide-ratings-utils)
79. [GitHub - rmarabini/player\_info\_from\_fide\_database: Download players information from FIDE Database · GitHub](https://github.com/rmarabini/player_info_from_fide_database)
80. [GitHub - goshrine/whole\_history\_rating: A pure ruby implementation of Rémi Coulom's Whole-History Rating (WHR) algorithm.](https://github.com/goshrine/whole_history_rating)
81. [Remi-Coulom (Rémi Coulom) · GitHub](https://github.com/Remi-Coulom)
82. [GitHub - wind23/whole\_history\_rating: A Python interface incorporating a C++ implementation of the Whole History Rating algorithm · GitHub](https://github.com/wind23/whole_history_rating)
83. [TrueSkill Through Time: Revisiting the History of Chess](https://www.researchgate.net/publication/221619020_TrueSkill_Through_Time_Revisiting_the_History_of_Chess)
84. [Chess Statistics Today](https://en.chessbase.com/post/chess-statistics-today)
85. [(PDF) FIFA Rankings vs ELO Ratings: Predictive Validity in World Cup Knockout Stages (1994-2022)](https://www.researchgate.net/publication/406281676_FIFA_Rankings_vs_ELO_Ratings_Predictive_Validity_in_World_Cup_Knockout_Stages_1994-2022)
86. [First-move advantage in chess](https://en.wikipedia.org/wiki/First-move_advantage_in_chess)
87. [Deloitte/FIDE Chess Rating Challenge - Standings - CLIST](https://clist.by/standings/deloittefide-chess-rating-challenge-14828013/)
