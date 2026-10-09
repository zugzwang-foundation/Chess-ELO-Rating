# SPEC-L0 — FIDE reference rating engine, specification v0.1 (skeleton)

**Status: DRAFT v0.1 — skeleton with TODOs; not ratified. No engine code is written until this document carries status RATIFIED.**
Author: The Zugzwang Authors · Licence: CC BY 4.0 (`docs/LICENSE-docs.md`) · Date: 2026-10-09
Language: Python 3.12 (decision D-0001). Tooling: TODO (see §10).

Citations: `[V k]` = item k of `docs/research/VERIFICATION_2026-10-09.md` (the Phase 1 transcription of the FIDE regulations); `[P §x]` = section x of `docs/proposal/ELO-PROPOSAL_v0_1.md`. Every rule below is enumerated from the transcription; where the transcription is silent the rule is marked TODO and must be settled by a test vector, never from memory.

## 1 Purpose

Layer 0 is an exact, deterministic, open-source implementation of the FIDE Rating Regulations effective 1 March 2024 as amended 1 October 2025 [V 1] and of the FIDE Rapid and Blitz Rating Regulations effective 1 March 2024 [V 2]. Given the same inputs FIDE uses (tournament reports and the previous monthly list), it must reproduce FIDE's published rating changes, initial ratings and list status to the point. It is the baseline for every comparison in the proposal [P §4, §8] and the credibility anchor with FIDE. It contains no correction layer and no model.

Out of scope for Layer 0: norms and titles; the pre-2024 regulations (archived versions exist [V 1] and may be added later as separate rule sets for historical backtests); anything in Layers 1 and 2.

## 2 Inputs

### 2.1 Game records (TRF-style)
One record per rated game, derived from the tournament report file (TRF) that arbiters submit under §9.1 [V 1]:
- `tournament_id`, `start_date`, `end_date`, `time_control_class` ∈ {standard, rapid, blitz} with the declared time control (base minutes, increment seconds, moves in the first control if any) so that the classifier (§3.1) can be checked;
- `round`, `white_id`, `black_id` (FIDE ID numbers), `result` ∈ {1-0, ½-½, 0-1, unplayed/forfeit}, `played` flag (§5.1 [V 1]: both players made at least one move);
- `rating_period` the list the tournament is registered for (§7.1.3, §9.1 [V 1]).
TODO: exact TRF field mapping (the TRF format is not in the transcription; the engine reads an internal, documented record format, with a TRF adapter as a separate utility).

### 2.2 Monthly list snapshot
For each player on the list in force for the rating period, per time control: `id`, `rating` (or unrated), `K`, `games_in_period`, `year_of_birth`, `federation`, `sex`, `title`, `inactive_flag`; these are the published fields (§7.1.2 [V 1]) and match the download-list legend (SRTNG/RRTNG/BRTNG, SK/RK/BK, SGM/RGM/BGM, B-day, FED, FLAG) [V 3]. Also required per player: the "games since first listed" count used by the K rule (§8.3.3) and the "has ever been published at 2400+" flag; TODO: neither is a published field, so the engine must carry its own state derived from history (§4.3) and the test-vector plan must confirm FIDE's behaviour.

### 2.3 Newcomer pool
For each unrated player: the pooled results against rated opponents over consecutive rating periods of not more than 26 months (§7.1.4 [V 1]), with dates, so that the pooling window can be applied.

## 3 Rules to implement (enumerated from the transcription)

### 3.1 Game eligibility and time-control class
- R-01 Standard: a game is rateable as standard only if each player has at least 120 minutes (either player rated 2400+), 90 minutes (either player 1800+) or 60 minutes (both below 1800) for 60 moves; a first time control, if any, is at least 30 moves (§1.1, §1.2 [V 1]). TODO: how "time for 60 moves" is computed with increments (the standard chapter does not state the "+ 60 × increment" formula; the rapid/blitz chapter does).
- R-02 Rapid: fixed time, or time plus 60 times the increment, more than 10 and less than 60 minutes per player (§1.1.1 [V 2]).
- R-03 Blitz: more than 3 and not more than 10 minutes per player, same formula (§1.1.2 [V 2]).
- R-04 Games where the players have different playing times are not rated (rapid/blitz §1.2 [V 2]).
- R-05 Unplayed games (forfeit or any other reason) are not counted; a game where both players made at least one move is rated unless force majeure or Fair Play regulations say otherwise (§5.1 [V 1], §4.1 [V 2]).
- R-06 Matches with an unrated player are not rated; in a match over a fixed number of games, games after one player has won are not rated unless waived (§6 [V 1], §5 [V 2]). TODO: match detection from the record format.
- R-07 Rapid/blitz: games with a rating difference of 600 points or more are not rated if at least one player is rated above 2600 on the relevant list, effective 1 December 2024 (§7.3.1 [V 2]). No such rule in standard.

### 3.2 Period handling
- R-08 One list per month; the list incorporates all rated play of the rating period into the previous list (§7.1 [V 1]).
- R-09 Closing date: tournaments ending on or before 3 days before the list date may be rated on that list; official FIDE events may be rated even if they end on the last day before the list date (§7.1.3 [V 1]).
- R-10 A tournament not submitted in time for the third list after it ends is not rated (§9.1 [V 1]).
- R-11 Within a period, a player's rating is fixed at the list value for all games of the period; all changes are summed per period and applied once (§8.3.2 c–d, §8.3.4 [V 1]).
- R-12 A player who receives a published rating before a tournament they played in is rated is rated as a rated player with their current rating, but counts as unrated in their opponents' calculations (§8.2.4 [V 1], §7.2.5 [V 2]). TODO: test vector.

### 3.3 Expected score
- R-13 For each game against a rated player compute D = own rating − opponent rating (§8.3.1 [V 1]).
- R-14 Standard, effective 1 October 2025: if the player is rated below 2650, |D| greater than 400 is treated as 400; if the player is rated 2650 or above, D is used as is (§8.3.1 [V 1]). The rule is evaluated per player (each side of a game may fall under a different branch). TODO: confirm with a test vector whether "players rated 2650 and above" refers to the player whose change is computed (as drafted here) or to either player.
- R-15 Rapid and blitz: |D| greater than 400 is treated as 400 for everyone; no 2650 exemption (§7.3.1 [V 2]).
- R-16 PD is read from table 8.1.2 (§8.3.2 a [V 1]): for D ≥ 0 the H column, for D < 0 the L column of the row containing |D|; |D| above 735 gives 1.0 / .00. The full table is reproduced in §9 and must be encoded verbatim.
- R-17 Per game ΔR = score − PD with score ∈ {1, 0.5, 0} (§8.3.2 b [V 1]).

### 3.4 K (development coefficient), §8.3.3 [V 1] (identical in rapid/blitz §7.3.3 [V 2])
- R-18 K = 40 for a player new to the rating list until they have completed events with at least 30 games.
- R-19 K = 20 as long as the rating remains under 2400.
- R-20 K = 10 once a published rating has reached 2400 and remains at that level subsequently, even if the rating later drops below 2400.
- R-21 K = 40 for all players until the end of the year of their 18th birthday, as long as their rating remains under 2300.
- R-22 Precedence when several lines apply: TODO. The transcription lists the four lines without an explicit order; the engine must reproduce the published K field on the monthly list (test vectors §6.2), and the chosen precedence must be written here before ratification.
- R-23 Cap: if K × n > 700 for a player in a period (n = number of games rated for the player on that list), K is the largest whole number such that K × n ≤ 700.
- R-24 Period change = K × Σ ΔR over the period (§8.3.2 d), using the K after R-23.

### 3.5 Rounding
- R-25 The period change is rounded to the nearest whole number; 0.5 is rounded away from zero (§8.3.4 [V 1], §7.3.4 [V 2]). Implementation note: use decimal arithmetic with an explicit rounding mode; never binary floating point for the final rounding.
- R-26 Ru (initial rating) is rounded to the nearest whole number (§8.2.3 [V 1]). TODO: whether 0.5 rounds away from zero here too (the text says only "nearest whole number"); settle by test vector.

### 3.6 Newcomers (initial rating), §7.1.4 and §8.2 [V 1]
- R-27 Publish a rating only when based on at least 5 games against rated opponents, pooled over consecutive rating periods of not more than 26 months; the rating must be at least 1400.
- R-28 A zero score in the player's first event is disregarded (§8.2.1).
- R-29 Ra = average rating of the rated opponents plus two hypothetical opponents rated 1800, scored as draws (§8.2.2): Ra = (Σ opponent ratings + 3600) / (n + 2); p = (score + 1) / (n + 2).
- R-30 Ru = Ra + dp with dp from table 8.1.1 (§8.2.3); maximum initial rating 2200; Ru rounded (R-26). TODO: rounding of p to two decimals before the lookup (the table is indexed by two-decimal p; the rule for p values between entries is not stated; settle by test vector, see [P Appendix E.2]).
- R-31 Rapid/blitz: an unrated player who has a standard rating at the start of a rapid or blitz tournament uses that standard rating and is treated as rated; R-27 to R-30 do not apply to them (§7.2.1 [V 2]).

### 3.7 Floor and inactivity, §7.2 [V 1] (identical in §6.2 [V 2])
- R-32 A player whose rating drops below 1400 is shown as unrated on the next list and is thereafter treated as any other unrated player (§7.2.1). TODO: whether the sub-1400 value is retained anywhere (not stated; assume discarded; test vector).
- R-33 A player commences inactivity after no rated games in a one-year period; regains activity after at least one rated game in a period and is listed as active on the next list (§7.2.2). Ratings do not change on inactivity.
- R-34 Published fields for a player whose rating is at least 1400 (§7.1.2).

### 3.8 Rapid and blitz differences (summary of the diff in [V 2])
Same tables, same K rules, same rounding and same newcomer arithmetic as standard; differences are R-02, R-03, R-04 (time control), R-07 (600-point exclusion), R-15 (plain 400 cap), R-31 (standard-rating seed), plus registration and rounds-per-day rules that do not affect the arithmetic.

## 4 Interfaces (pure, deterministic functions; signatures only, no bodies)

All functions are pure: no I/O, no global state, no randomness, no wall-clock. Money-style decimal arithmetic (`decimal.Decimal`) for every quantity that is rounded. Each function is documented with the rule ids it implements.

```
classify_time_control(base_minutes, increment_seconds, moves_first_control, rating_a, rating_b) -> TimeControlClass | NotRateable        # R-01..R-04
is_rateable_game(record, list_snapshot) -> bool                                                                                       # R-05..R-07
effective_difference(own_rating, opponent_rating, time_control_class) -> int                                                         # R-13..R-15
expected_score(effective_difference) -> Decimal                                                                                      # R-16 (table 8.1.2)
dp_from_p(p) -> int                                                                                                                  # table 8.1.1 (R-30)
k_factor(player_state, rating, games_in_period) -> int                                                                               # R-18..R-23
period_change(player_state, games_in_period: list[GameVsRated]) -> Decimal                                                           # R-11, R-17, R-24
round_period_change(x: Decimal) -> int                                                                                                # R-25
initial_rating(pooled_games: list[GameVsRated]) -> int | NotYetPublishable                                                           # R-27..R-30
next_list(previous_list, games_of_period, newcomer_pool, list_date) -> ListSnapshot                                                  # R-08..R-12, R-32..R-34
```

### 4.3 Player state carried by the engine (not on the published list)
`games_since_first_listed`, `ever_published_at_2400_plus`, `first_event_zero_disregarded`, `pool_of_unrated_results` (with dates), `last_rated_game_period`. TODO: define how this state is reconstructed from a historical sequence of monthly lists when bootstrapping.

## 5 Determinism and precision
- Identical inputs → identical outputs, byte for byte, on any platform; no dependence on dictionary order, locale, time zone or hardware floating point.
- All rating arithmetic in `Decimal` with a declared context; PD and dp are exact table constants; the only rounding steps are R-25 and R-26.
- Every output row carries a per-game breakdown (D, effective D, PD, ΔR, K, sum, rounded change) so that any change can be checked by hand against the regulations.

## 6 Test-vector plan
### 6.1 FIDE calculator
Source: https://ratings.fide.com/calc.phtml?page=change (reachable at 2026-10-09T14:30:34Z, content not yet transcribed [V +]). Plan: for a grid of (own rating, opponent rating, result, K) covering every row boundary of table 8.1.2 (0–3, 4–10, …, 620–735, >735), both signs of D, the 400 cap on both sides of 2650, and the K × n ≤ 700 cap, record the calculator's output as fixtures. TODO: confirm the calculator implements the 1 October 2025 rule, and capture the initial-rating calculator for R-27..R-30 (including the p-rounding question).
### 6.2 Sampled players across monthly lists
Source: the monthly list archive, February 2015 to date [V 3] (downloaded, never redistributed; see `.gitignore`). Plan: sample players across rating bands, ages (juniors crossing the year of their 18th birthday), the 2300/2400 thresholds, newcomers, players at the floor and returning inactive players; reconstruct each player's games for a period from their public tournament records (TODO: source and terms for per-game data; the TRF archive is the formal request [P §8]); assert that `next_list` reproduces the published rating, K and games fields. Acceptance uses the thresholds in §7.
### 6.3 Regression and property tests
Mirror-image property of the two tables (§8.1 [V 1]); monotonicity of PD in D; K × n ≤ 700 after R-23; rounding symmetry of R-25; rapid/blitz tables identical to standard (verified [V 2]).

## 7 Acceptance criteria
- A-1 Table 8.1.1 and 8.1.2 encoded exactly as transcribed (§9) and unit-tested entry by entry (101 + 51 entries).
- A-2 100 % agreement with FIDE calculator fixtures (§6.1) on rating change, including rounding.
- A-3 100 % agreement on published rating, K and games fields for the sampled players (§6.2), or a documented FIDE-side anomaly for every disagreement.
- A-4 Deterministic: two runs on two platforms produce identical output files (hash-equal).
- A-5 Every TODO in this document resolved and recorded, or moved to a numbered open question with an owner, before status RATIFIED.
- A-6 No function performs I/O; adapters (TRF reader, list parser) are separate and tested separately.

## 8 Open questions for ratification
1. R-14: to whom "players rated 2650 and above" refers (own rating as drafted, or either player).
2. R-22: precedence among the four K lines.
3. R-26, R-30: rounding of Ru and of p.
4. R-32: fate of the sub-1400 value.
5. R-01: increment handling in the standard chapter.
6. §2.1: TRF field mapping and the source of per-game data for §6.2.
7. Whether to implement the archived 2022 and 2017 regulations as additional rule sets for backtests over earlier periods.

## 9 The tables (encoded verbatim)

**Table 8.1.1 (p → dp), 101 entries, from the verified transcription [V 1]:**

| p | dp |
|---|---|
| 1.0 | 800 |
| .99 | 677 |
| .98 | 589 |
| .97 | 538 |
| .96 | 501 |
| .95 | 470 |
| .94 | 444 |
| .93 | 422 |
| .92 | 401 |
| .91 | 383 |
| .90 | 366 |
| .89 | 351 |
| .88 | 336 |
| .87 | 322 |
| .86 | 309 |
| .85 | 296 |
| .84 | 284 |
| .83 | 273 |
| .82 | 262 |
| .81 | 251 |
| .80 | 240 |
| .79 | 230 |
| .78 | 220 |
| .77 | 211 |
| .76 | 202 |
| .75 | 193 |
| .74 | 184 |
| .73 | 175 |
| .72 | 166 |
| .71 | 158 |
| .70 | 149 |
| .69 | 141 |
| .68 | 133 |
| .67 | 125 |
| .66 | 117 |
| .65 | 110 |
| .64 | 102 |
| .63 | 95 |
| .62 | 87 |
| .61 | 80 |
| .60 | 72 |
| .59 | 65 |
| .58 | 57 |
| .57 | 50 |
| .56 | 43 |
| .55 | 36 |
| .54 | 29 |
| .53 | 21 |
| .52 | 14 |
| .51 | 7 |
| .50 | 0 |
| .49 | -7 |
| .48 | -14 |
| .47 | -21 |
| .46 | -29 |
| .45 | -36 |
| .44 | -43 |
| .43 | -50 |
| .42 | -57 |
| .41 | -65 |
| .40 | -72 |
| .39 | -80 |
| .38 | -87 |
| .37 | -95 |
| .36 | -102 |
| .35 | -110 |
| .34 | -117 |
| .33 | -125 |
| .32 | -133 |
| .31 | -141 |
| .30 | -149 |
| .29 | -158 |
| .28 | -166 |
| .27 | -175 |
| .26 | -184 |
| .25 | -193 |
| .24 | -202 |
| .23 | -211 |
| .22 | -220 |
| .21 | -230 |
| .20 | -240 |
| .19 | -251 |
| .18 | -262 |
| .17 | -273 |
| .16 | -284 |
| .15 | -296 |
| .14 | -309 |
| .13 | -322 |
| .12 | -336 |
| .11 | -351 |
| .10 | -366 |
| .09 | -383 |
| .08 | -401 |
| .07 | -422 |
| .06 | -444 |
| .05 | -470 |
| .04 | -501 |
| .03 | -538 |
| .02 | -589 |
| .01 | -677 |
| .00 | -800 |

**Table 8.1.2 (D → PD for the higher-rated player H; the lower-rated player gets 1 − H, as listed in column L), 51 entries, from the verified transcription [V 1]:**

| D | H | L |
|---|---|---|
| 0-3 | .50 | .50 |
| 4-10 | .51 | .49 |
| 11-17 | .52 | .48 |
| 18-25 | .53 | .47 |
| 26-32 | .54 | .46 |
| 33-39 | .55 | .45 |
| 40-46 | .56 | .44 |
| 47-53 | .57 | .43 |
| 54-61 | .58 | .42 |
| 62-68 | .59 | .41 |
| 69-76 | .60 | .40 |
| 77-83 | .61 | .39 |
| 84-91 | .62 | .38 |
| 92-98 | .63 | .37 |
| 99-106 | .64 | .36 |
| 107-113 | .65 | .35 |
| 114-121 | .66 | .34 |
| 122-129 | .67 | .33 |
| 130-137 | .68 | .32 |
| 138-145 | .69 | .31 |
| 146-153 | .70 | .30 |
| 154-162 | .71 | .29 |
| 163-170 | .72 | .28 |
| 171-179 | .73 | .27 |
| 180-188 | .74 | .26 |
| 189-197 | .75 | .25 |
| 198-206 | .76 | .24 |
| 207-215 | .77 | .23 |
| 216-225 | .78 | .22 |
| 226-235 | .79 | .21 |
| 236-245 | .80 | .20 |
| 246-256 | .81 | .19 |
| 257-267 | .82 | .18 |
| 268-278 | .83 | .17 |
| 279-290 | .84 | .16 |
| 291-302 | .85 | .15 |
| 303-315 | .86 | .14 |
| 316-328 | .87 | .13 |
| 329-344 | .88 | .12 |
| 345-357 | .89 | .11 |
| 358-374 | .90 | .10 |
| 375-391 | .91 | .09 |
| 392-411 | .92 | .08 |
| 412-432 | .93 | .07 |
| 433-456 | .94 | .06 |
| 457-484 | .95 | .05 |
| 485-517 | .96 | .04 |
| 518-559 | .97 | .03 |
| 560-619 | .98 | .02 |
| 620-735 | .99 | .01 |
| > 735 | 1.0 | .00 |

## 10 Tooling (TODO)
Python 3.12; package layout, test runner, lint/type-check configuration, fixture format and CI are TODO and will be decided in the first implementation session after ratification. Nothing in this section authorises writing engine code before then.
