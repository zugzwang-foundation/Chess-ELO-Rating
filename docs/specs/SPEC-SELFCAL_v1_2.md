# SPEC-SELFCAL — the self-calibrating table: one table a year, each fitted only on the games before it, v1.2

**Status: REVIEW — v1.0 written before any yearly table was fitted and before any self-calibrating replay was run (ELO-8 brief, Phase 2; rulings R61 and R65, `docs/decisions/D-0014_forecast-test-and-rulings.md`, part B); v1.1, after the session's review, records the departures from SPEC-TABLE-FIT v1.2 and the amendments made after the counts (§13) and restates W3 (§4), changing no window, table or result; v1.2 applies the architect's rulings R68 to R72 (`docs/decisions/D-0016_rulings-on-elo-8-questions.md`, session ELO-9): when a form may be chosen and when only refitted (§5), when the caps may be lifted (§6), name matching as a labelled sensitivity (§2), R59's two estimates and what E19's aggregate keeps (§10), changing no table and no headline result.** Author: The Zugzwang Authors · Licence: CC BY 4.0 (`docs/LICENSE-docs.md`) · Date: 2026-10-11 · v1.0 and v1.1 are in git history; E18 and E19 were produced under them, and their ELO-9 additions under v1.2. It applies `docs/specs/SPEC-TABLE-FIT_v1_2.md` (the rules for a yearly fit) year by year, back in time, and fixes what v1.2 leaves to the fit's decision record: the window when data are short, the yearly change caps for the forms v1.2 adds, and how the yearly tables enter the replays. Every value it produces is PROVISIONAL-FITTED. Nothing in it changes the championship comparison: the 2026 U.S. Championships keep Freeze 3's table as frozen (Freezes 3 to 3d).

## 1 What "self-calibrating" means here

Rung 2's table (annex T3) is refitted each year on the games played before that year, by SPEC-TABLE-FIT v1.2's rules, within the yearly change caps of annex T7.1; the method is fixed here and never changes because of results (R65). The public name is "self-calibrating". It is evaluated in two places:

- **E18** (`docs/evidence/E18_self-calibration.md`): the yearly tables, the three-way test of §7 and the parameters over time (§8);
- **E19** (docs/evidence/E19_top100-selfcal.md, to be written in Phase 4): today's top 100 replayed as in E17, rung 2 taking each year's table and K following FIDE's K rules on each system's own rating (R61; §9, §10).

Standard chess only. Rapid and blitz are reported for coverage (§2) and are not fitted: their earlier rules are not transcribed (`docs/research/VERIFICATION_RATING-REGULATIONS-ARCHIVE.md` covers standard), so the three-way test could not be run for them.

## 2 Data

- **Games: the Lichess broadcast archive**, monthly files 2020-01 to 2026-09 (https://database.lichess.org/broadcast/, CC BY-SA 4.0, attributed; aggregates only) [V 4], with E2's sample rules unchanged (SPEC-TABLE-FIT v1.0 §1, which v1.1 and v1.2 keep): standard variant and a result; both FIDE IDs; both players rated on the list of the time control in force (the list dated the first day of the month in which the broadcast tour starts, or of the game's month when the tour spans more than 30 days); dates, duplicates and the time-control class as E2 reads them. The sample is built with E2's functions through E10's builder (`analysis/e10_guard_extract.py`), which enforces the cutoff of §3.
- **Colours**: the PGN's White and Black. **Ratings**: FIDE's monthly lists [V 3], analysed and never redistributed.
- **2016 to 2019: no legitimate free source.** The brief asks for free historical databases for 2016–2019, licences checked first. Checked on 2026-10-11:
  - The Week in Chess (https://theweekinchess.com/twic): "TWIC magazine is free for personal use only. All rights are reserved." A project of this kind would need the owner's permission, and this session may contact no one.
  - PGN Mentor (https://www.pgnmentor.com/files.html): no licence or terms for the files, only "Copyright © 2025 64 Squares."
  - KingBase (Internet Archive copies of 2018 and 2019): discontinued, with no licence stated; compiled from sources that include TWIC.
  The Lichess broadcast archive holds no file before 2020-01 (its published checksum list, `data/raw/lichess_broadcast/sha256sums.txt`, fetched in session ELO-7, begins with 2020-01). **So the data start in January 2020, and, by the window rule of §4, the first table is the earliest year whose window the data allow (§4, W5).**
- **The archive's files before 2023 carry no FIDE ID.** Their PGN headers hold names, often Elo tags, and no WhiteFideId or BlackFideId tag (none in the 6,629 games of 2021-06, for example), so E2's sample, which needs both FIDE IDs, finds almost no standard game before 2023 and few before March 2024 (E18 §1 counts them). The rules of SPEC-TABLE-FIT v1.2, which R65 fixes, keep that requirement, and the headline keeps it (R65's sample rule).
- **Name matching (R70), a labelled sensitivity only.** A player of a game of 2020 to 2023 without a FIDE ID is matched when exactly one player on the standard list in force (the list E2 reads for the game) has the same name, the same federation and a rating within 10 points of the game's Elo tag; a game counts when both players match, and every other game is dropped. If the matched games give a table for 2023 or 2024, the three-way test and E19 are reported with it beside the headline. The archive's games of 2020 to 2023 carry no federation tag (counted by `analysis/e18_name_match_extract.py`, E18 §1), so no game matches and no table results; no looser match is tried (D-0016, reading 11).
- **Coverage** is reported by year, 100-point level band and time control (E18 §1).

## 3 "The games before that year"

- **The table of year Y** is the table in force for every tournament that uses a list dated in year Y (the list in force at the tournament's start, SPEC-L0 R-11a), as the published table is issued once a year with the January list's parameter file (annex T3.4, T7).
- **It is fitted only on games played before year Y**: games dated in the months of its window (§4), every one of them on or before 31 December of year Y − 1; the cutoff is the last day of the month before the fit, enforced in code, and no game dated after 30 September 2026, and no archive file later than 2026-09, is ever read (the brief's locks).
- **A game's month** is the month of its date as E2 reads it (the Date tag, else the UTCDate tag, else the archive file's month).

## 4 The window rule

For each year Y from 2020 to 2026:

- **W1.** The window is the 36 months before Y: January of Y − 3 to December of Y − 1.
- **W2. A rule change that moved published ratings cuts it** (SPEC-TABLE-FIT v1.2 §1): no game whose list in force precedes the first list after the change enters the window. The one change in the period is the compression of the March 2024 lists [E5], so a window that would reach before 2024-03 starts at 2024-03.
- **W3. A year with too few games lengthens it.** If a calendar year inside the window holds fewer than G = 20,000 standard sample games (pro rata, G × m / 12, for a year with only m months inside the window), the window adds the 12 months before its start, repeatedly, until it holds G games for every 12 of the months W1 and W2 gave it (3G for a 36-month window, pro rata for a cut one), never before the first month of data (2020-01) and never across a cut of W2. (v1.0 tested each year again after lengthening, which could never succeed, since a lengthened window keeps its short year; review finding ELO8-QC-2. No window changes.)
- **W4. No table without a window.** If, after W3, the window still holds fewer games than W3 asks, no table is fitted for Y and the previous year's table stays in force; before the first table, the self-calibrating system has no table of its own and uses table 8.1.2 as FIDE applies it.
- **W5. The first table** is therefore the earliest year whose window meets W1 to W3. With data from 2020-01 and no extension possible before it, that is 2023 at the earliest (window 2020-01 to 2022-12), and later if a year of 2020 to 2022 has too few games; with the sample of E18 §1 it is 2025 (window 2024-03 to 2024-12, cut by W2).
- **G = 20,000** is fixed here before any count is seen: about a quarter of a year of the broadcast archive's standard sample at its 2023–2025 rate (352,737 games in 45 months [E2]), enough for each of a window's years to hold a share of the fit's information; it is PROVISIONAL.

## 5 The fit of each year's table

As SPEC-TABLE-FIT v1.2 (§2, §3), with these details fixed here.

- **The model.** For White against Black, x = R_W − R_B, L the midpoint of the 100-point level band of ⌊(R_W + R_B)/2⌋ (1450 below 1500, 2850 from 2800), ℓ = (L − 2000)/400, q = ln 10/400: z = κ(L) q (x + η(L)); ν = exp(α + β ℓ − γ(L) |z|); P_W : P_D : P_L = e^{z/2} : ν : e^{−z/2}; with κ(L) of form E, κ exp(λ ℓ), or form P, piecewise-linear between the knots L = 1500, 1700, …, 2700 and constant beyond them; η(L) = η + ζ ℓ (ζ = 0 without the colour term by level); γ(L) = γ exp(μ ℓ) (μ = 0 without the draw tail).
- **Maximum likelihood** over cells of identical (x, band, outcome), a damped Newton method with the analytic score and a finite-difference Hessian, deterministic starts (the simpler candidate's fit with the added parameters at zero, or at the values that make P equal to E at its knots), κ(L) ≥ 0.05, γ(L) ≥ 0 at every band midpoint with no upper bound (R7), the caps of §6 as bounds; it stops when no parameter moves by more than 10⁻⁷, or after 50 iterations; standard errors and the covariance from the inverse observed information of the free parameters. A fit on a bound is reported.
- **The candidates and the rule of choice** (v1.2 §3), applied in this order on the selection months: the slope form (P against E), then the colour term by level (ζ free against ζ = 0), then the draw tail (μ free, by v1.1 §4.6's condition: a level band with at least 1,000 selection games whose favourite's residual pooled over gaps lies significantly outside ±0.01, one-sided, cluster-robust over favourites, Holm–Bonferroni at a familywise 5 %). A more flexible slope or colour form replaces the simpler only when the month-block bootstrap interval of its three-outcome log-loss difference (candidate minus simpler; blocks of 3 months, 2,000 resamples, seed 20261009) lies below zero.
- **Choosing a form, and refitting it (R68).** A table's form is chosen only when its window holds at least 24 months of games after the last rule change that moved ratings, counted as the window's months from the first list after the change (W2), test months included; refitting the parameters of the form in force needs at least 10 months (D-0016, readings 7 and 8). **The 10-month figure was set after the counts were known**: v1.0 set it once E18 §1's counts had fixed the windows at 10 and 22 months, and before any table was fitted; the first table, 2025's, exists only because of it.
- **Test months.** Within a window that may choose, rolling origin as v1.0 §3: the test months are the window's last 12 months, split into selection months (the earlier six) and confirmation months (the later six), each forecast by a fit on the months of the window before it (at most 36), so that at least 12 months of training precede them; in a 36-month window this is v1.0's protocol (24 months training only, 12 test months). A window of 10 to 23 months makes no choice: the form of the previous year's table is kept and its parameters refitted on the whole window; a first table without a choice takes v1.1's form for standard, form E with the draw tail, as E11 chose it [E11].
- **When R68 applies.** From the 2027 table, the first fitted after the ruling (D-0016, reading 6), so that no table is changed after its result was seen. The 2026 table's form was chosen under SPEC-SELFCAL v1.1's rule, which asked for 10 months of training before 12 test months (a 22-month window); E18 and E19 keep it in their headlines and print beside them the 2026 table in the form R68 keeps: form E with the draw tail, refitted on the 2026 window within the caps ("R68 applied to 2026").
- **The published table of year Y** is the chosen form fitted on the whole window, within the caps of §6.

## 6 The yearly change caps

Annex T7.1's caps per calendar year, PROVISIONAL, relative to the previous year's published table: κ 0.05; λ 0.05; η 5 rating points; α 0.20; β 0.10; γ 0.10; μ 0.05. For what v1.2 adds and T7.1 does not list:

- **form P:** each knot's κ within 0.05 of the previous table's κ(L) at that knot (whatever the previous form);
- **ζ:** within 5 rating points per unit of ℓ of the previous table's ζ (0 if it had none);
- **a form or term added in a year** (P after E, ζ or μ after none): capped against the previous table's value of the same quantity (κ(L) at the knots; ζ = 0; μ = 0);
- **a term the rule of choice drops** (ζ or μ): it moves toward zero by at most its cap and is fixed there, so that the table's change stays within the cap (added in session ELO-8, Phase 3, before any table was fitted).

The caps are box bounds of the fit: a capped parameter that would move further sits at its bound, and the fit says so. The first table has no predecessor and is fitted without caps. **The caps hold (R69)**: after a rule change that moved ratings the QC may lift them for the first refit only, the first table fitted with a predecessor after the change, by a recorded decision; otherwise they hold, a year whose window W2 cuts included. No decision lifts them for 2026, the first refit after the March 2024 compression, so E18's tables and E19 keep them; E18 prints, as a sensitivity and not as the headline, the three-way test with the 2026 table fitted without caps in its chosen form (D-0016, reading 10).

## 7 The three-way test (E18)

For every year Y from the first table's year to 2026, every standard sample game dated in Y (2026: January to September), each scored from White's side:

1. **Table 8.1.2 as FIDE applied it**: Layer 0 with the rules in force at the tournament's start (`src/layer0_history/`: the plain cap to 2021, one upgrade per tournament from 2022, applied to each player's games in the broadcast tour, the plain cap from March 2024, NOT VERIFIED, the 2650 exemption from 1 October 2025); its three outcomes split White's expected score with the draw rate of the game's 100-point level band in Y's window (E2's construction, E6's floor);
2. **the first year's table, kept frozen**: the published table of the first year, fitted on its window, used unchanged in every later year;
3. **Y's own table**.

Forecasts (2) and (3) use the table's model probabilities at the game's band midpoint (as E11 evaluates a table); the narrowed guard is not applied, so that the test compares tables. Reported, per year and pooled over the years:

- the three-outcome log-loss and the expected-score Brier score of each forecast, and the differences (3) − (2), (3) − (1) and (2) − (1), with month-block bootstrap 95 % intervals over the year's months (blocks of 3 months, 2,000 resamples, seed 20261009), overall and by 100-point level band;
- calibration: the favourite's residual S − E by level band and 50-point gap cell (cells with at least 200 games printed with their cluster-robust standard errors over favourites; cells with at least 1,000 games tested against ±0.01 as annex T8.2's rule (a), one-sided, Holm–Bonferroni at a familywise 5 %), and by level band pooled over gaps.

**The verdict, year by year:** self-calibration earns its name in year Y when (3)'s log-loss is below (2)'s with the interval of (3) − (2) below zero, and both (2) and (3) are below (1) with their intervals below zero. In the first year (2) and (3) are the same table. The verdict is reported whatever it shows.

**Beside the verdict, never in it:** where Y's table changed form, the same comparisons with Y's table in the form in force before it (for 2026, R68's form: D-0016, reading 6); where a parameter of Y's table sits on a cap, the same comparisons with Y's table fitted without caps (R69). Each is labelled a sensitivity.

## 8 The parameters over time (E18)

For each year's table, with 95 % intervals from the fit's covariance (2,000 parametric draws from its normal approximation, seed 20261009; the cap's bound where a parameter sits on it), beside table 8.1.2's constant values where they are comparable:

- **White's edge**: η(L) at L = 2050, 2450 and 2750 (the band midpoints nearest 2000, 2400 and 2700), in rating points, and White's expected score at equal ratings there; table 8.1.2: 0 points, 0.50;
- **the draw rate at equal ratings by level**: ν₀(L) / (2 + ν₀(L)), ν₀(L) = exp(α + β ℓ), at every band midpoint; table 8.1.2 has no draw model (not comparable);
- **the slope at an even gap** at 2000, 2400 and 2700: κ(L) q / (2 (2 + ν₀(L))) per rating point, at the band midpoints 2050, 2450 and 2750; table 8.1.2: the least-squares slope of its H entries over D = 0 to 100 [V 1] (`src/layer2/table_v2.py`, `slope_812`);
- **a 100-point favourite's expected score at 2700**, without colour: the model's E at x = 100 in band 2700–2799; table 8.1.2: the H entry at D = 100 [V 1].

E18's committed aggregate holds every year's parameters, standard errors, covariance-based intervals, cap flags and these quantities with their intervals, beside table 8.1.2's values, so that the video session the operator deferred (D-0014, R62) needs no refit.

## 9 K in the replays (R61)

Same rules, different rating. FIDE's K rules in the version in force (SPEC-L0 R-18 to R-22, the order settled on FIDE's published K; the junior clause "until their 18th birthday" in the 2017 regulations, "until the end of the year of their 18th birthday" from 2022, `docs/research/VERIFICATION_RATING-REGULATIONS-ARCHIVE.md`), with K × n ≤ 700 (R-23):

- **Layer 0's replay** keeps FIDE's K as FIDE's calculation pages print it: FIDE's rules applied to FIDE's ratings (E17 reproduces it in 4,938 of 4,940 tournaments).
- **The self-calibrating replay** applies the same rules to its own ratings: "a published rating of 2400 or more at any time" and "never rated 2300 or more" are read on the self-calibrating rating from January 2020 (before 2020 the two systems share FIDE's history); the inputs that do not depend on the rating (the year of birth, the games counted, the list in force, n) are FIDE's. Before the replay, the rule is applied to FIDE's own ratings and must give FIDE's printed K; on any player-list where it does not, the self-calibrating K is FIDE's K there, and the case is listed.

## 10 Today's top 100, self-calibrating (E19)

As `docs/specs/SPEC-TOP100_v1_0.md` (E17): the same 100 players, games, validation and Layer 0, the 100 replayed together month by month, the opponents outside the 100 at their published ratings, the difference the self-calibrating replay minus Layer 0's replay, the fixed wording "under this rule, with the same results — not anyone's true strength" with every table; with these changes:

- **rung 2 is self-calibrating**: each tournament uses the table of the year of the list in force at its start (§3), with η(L) rounded to whole points in each band and the published entry to three decimals (annex T3.4), the narrowed guard as frozen (R46, R47) on top of it, and no 400-point rule; before the first table, table 8.1.2 as FIDE applies it, so that the two systems agree until then;
- **K** as §9;
- **beside the headline**: R58's range (the replay rerun with every opponent outside the 100 rated 10 and 5 points lower and higher under the self-calibrating system); R59's estimate of the table's own error at the top, in its two readings, both called estimates, not bounds (R71): the replay rerun with each year's table corrected, at levels of 2300 or more, by its favourite's residual by 100-point level band pooled over gaps (E16 §5's measure; the reading the headline sentence uses) and by band and 50-point gap (cells of 200 games or more, the band's value elsewhere), on that year's games (§7), added to the favourite's expectation and taken from the underdog's; the replay with the 2026 table in the form R68 keeps (§5); and E17's frozen-table figures for comparison;
- **per player**: names beside FIDE IDs (R60), FIDE's rating and the self-calibrating rating in October 2026 (kept for E19 §2 and Appendix H, R72), the difference split into the table's effect and colour's, and, on every list from January 2020 to October 2026, **only the difference between the two systems** in E19's committed aggregate (R72); both systems' ratings on every list stay in the local cache under `data/` (gitignored), where the deferred video session can read them without a refit. FIDE's lists are otherwise not redistributed [V 3], and no year of birth is committed.

## 11 Outputs

- `analysis/e18_coverage_extract.py` (needs `data/`) writes `analysis/aggregates/E18_coverage.json` (Phase 2: the games and the windows); `analysis/e18_name_match_extract.py` (needs `data/`, ELO-9) writes `analysis/aggregates/E18_name_match.json` (R70's counts); analysis/e18_selfcal_extract.py (needs `data/`, Phase 3) writes analysis/aggregates/E18_selfcal.json: counts, sums, fitted values and test results only; `analysis/e18_selfcal_report.py` writes `docs/evidence/E18_self-calibration.md` from both.
- analysis/e19_top100_selfcal_extract.py (needs `data/`, Phase 4) writes analysis/aggregates/E19_top100_selfcal.json; analysis/e19_top100_selfcal_report.py writes docs/evidence/E19_top100-selfcal.md.
- The fit's code is a module of the extraction, new (Freeze 3's `analysis/table_v2_fit.py` keeps v1.1's bound on γ and stays unchanged).
- Check (a) reruns the reports; the extractions are rerun with `--all` where the data are.

## 12 Bias statement

As SPEC-TABLE-FIT v1.0 §5: broadcast events are stronger and more international than the rated pool, and the archive covers fewer games in 2020 to 2022 than later; the yearly tables describe the broadcast population. FIDE's tournament reports would settle the method for the pool (annex T8.6).

## 13 Departures from SPEC-TABLE-FIT v1.2, and what was set after the counts (v1.1)

Listed for the architect after the session's review (`docs/review/REDTEAM_v1_0.md`, ELO-8 addendum, ELO8-QC-2 and ELO8-STAT-3). R65 fixes each year's table "by SPEC-TABLE-FIT v1.2's rules"; this specification departs from them, or fixed a detail only after the counts of E18 §1 were known, in four places:

1. **The training months.** v1.2 keeps v1.0 §3's protocol: 24 months of training before the first test month. §5 asks for 10, a rule set after E18 §1's counts had fixed the windows at 10 and 22 months and before any table was fitted. Under 24 months no form could be chosen for 2026 (the first window after the March 2024 cut long enough for that would be 2028's), and the 2026 table would keep 2025's form, E with the draw tail. E18 §3 prints that table beside the chosen one, so that the effect of the departure is measured. **Settled by R68** (this version, §5): a choice of form needs 24 months of games after the last rule change, a refit 10; the 10-month figure was set after the counts were known; the rule applies from 2027, and the 2026 table in R68's form is printed beside the headline in E18 and E19.
2. **The first table's form when no choice can be made** (v1.1's form for standard, E with the draw tail, §5), set in Phase 2 after the counts and before any fit.
3. **The rule for a term the rule of choice drops** (§6) was written in Phase 3 before the fits but committed with them, so its timing cannot be checked from the history. It changed nothing: 2025's μ was 0.0009, inside its cap.
4. **W3** as v1.0 worded it could never lengthen a window into one that passes; §4 restates it. No window changes (E18 §1).

None changes a table or a result of E18 or E19; the first changes which form the 2026 table takes, and E18 §3 reports both. The caps after a rule change, left to the architect in SPEC-SELFCAL v1.1 §6, are settled by R69 (§6).

