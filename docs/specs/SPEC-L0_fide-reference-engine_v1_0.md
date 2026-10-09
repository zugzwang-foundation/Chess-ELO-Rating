# SPEC-L0 — FIDE reference rating engine, specification v1.0

**Status: RATIFIED (`docs/decisions/D-0006_spec-l0-ratified.md`, 2026-10-09). Under the pre-agreed rule of the ELO-3 brief: every rule below carries a verbatim citation of the FIDE text or a fixture of FIDE's own output, and every acceptance criterion of §7 is an executable test, written before the engine. Readings marked NOT VERIFIED are listed in §8. Changing a rule needs a new version and a decision record.**
Author: The Zugzwang Authors · Licence: CC BY 4.0 (`docs/LICENSE-docs.md`) · Date: 2026-10-09 · v0.1, the skeleton, is in git history
Language: Python 3.12 (decision D-0001).

Citations: `[V k]` = item k of `docs/research/VERIFICATION_2026-10-09.md` ([V 1] the FIDE Rating Regulations effective 1 March 2024 as amended 1 October 2025, [V 2] the Rapid and Blitz Rating Regulations effective 1 March 2024, [V 3] the list downloads); `[VT k]` = item k of `docs/research/VERIFICATION_TITLES.md` ([VT 1] the Title Regulations effective 1 January 2024, [VT 2] the archived Rating Regulations of 1 January 2022 till 29 February 2024); `F-xnn` = a fixture in `tests/fixtures/fide_calculator/` (method and findings in its README), every value recomputed in `analysis/OUTPUT_L0_fixtures.md`; the evidence from the monthly lists on K is `analysis/OUTPUT_L0_k_rules.md`; `[P §x]` = section x of `docs/proposal/ELO-PROPOSAL_v0_3.md`.

Evidence classes used in §3: **CIT** — the rule is the quoted FIDE text; **FIX** — a fixture shows FIDE's own output following the rule; **DATA** — aggregates of the published lists agree with the rule; **READ** — the text is silent and the stated reading is adopted. A READ without a fixture is marked **NOT VERIFIED** and listed in §8.

## 1 Purpose

Layer 0 is an exact, deterministic, open-source implementation of the FIDE Rating Regulations effective 1 March 2024 as amended 1 October 2025 [V 1] and of the FIDE Rapid and Blitz Rating Regulations effective 1 March 2024 [V 2]. Given the inputs FIDE uses (tournament results and the monthly lists), it reproduces FIDE's rating changes, initial ratings, K and list status. It is rung 1 of the adoption ladder and the baseline for every comparison in the proposal [P §4, §9, §10]. It contains no model and no correction.

Out of scope: norms and titles (the Title Regulations use table 1.4.9, which equals table 8.1.1 entry by entry [VT 3], and are not implemented); the regulations before 1 March 2024 (separate rule sets may be added for backtests, §8 Q-10); reading TRF files (a separate adapter, §2.1); Layers 1 and 2.

**Changes from v0.1.** R-14 settled (own rating) by FIDE's published calculations; R-22 settled (the precedence of the K lines) by the published lists; R-11a (the list whose ratings a tournament uses), R-11b (base corrections), R-14a (the 1 October 2025 boundary) and R-22b (which list's K applies) added; R-23, R-25, R-29 and R-30 backed by fixtures; R-26, R-30 (ties) and the granularity of R-25 recorded as readings, NOT VERIFIED; FIDE's online calculator found to be out of date (§6.1); acceptance criteria rewritten as executable tests (§7).

## 2 Inputs

### 2.1 Game records

One record per game of a FIDE-rated tournament, in the engine's own documented format (a TRF adapter is a separate utility; the TRF layout is not transcribed, §8 Q-6):
- tournament: `tournament_id`, `start_date`, `end_date`, `rating_period` (the list, YYYY-MM, on which FIDE rates the tournament), `chapter` ∈ {standard, rapid, blitz} and the declared time control (`base_minutes`, `increment_seconds`, `moves_first_control` if any);
- game: `round`, `white_id`, `black_id` (FIDE ID numbers; the colour is the side each ID is on), `result` ∈ {1-0, ½-½, 0-1}, `played` (false for a forfeit or any unplayed game, R-05), `excluded` (true when an arbiter or the Fair Play regulations exclude a played game, R-05);
- for matches (R-06): `match_id` and the scheduled number of games.

### 2.2 Monthly list snapshots

For each month and chapter, the published fields [V 3] (§7.1.2 [V 1]): `id`, `rating` (absent if unrated), `k`, `games` (rated in the period), `birth_year`, `sex`, `federation`, `flag` (inactive), `title`. Layer 0 needs every list from the start of the period it computes back to the list in force when the earliest of its tournaments started (R-11a).

### 2.3 Engine state not on the list (§4.3)

Per player and chapter: `games_count` (rated games counted towards the 30 of R-18), `ever_2400` (a published rating of 2400 or more), `ever_2300` (a published rating of 2300 or more), the newcomer pool (results against rated opponents with their periods, R-27) and the period of the last rated game (R-33).

### 2.4 Corrections

Optional, per list month and player: a corrected rating, such as FIDE's starting rating Ro where it differs from the published list (R-11b). Corrections are inputs, never inferred; every use is printed in the output.

## 3 Rules

### 3.1 Games that count, and their chapter

- **R-01 Standard rate of play.** CIT §1.1–1.2 [V 1]: "For a game to be rated each player must at the start of the game have the following minimum periods in which to complete all the moves, assuming the game lasts 60 moves." 120 minutes "Where at least one of the players in the game has a rating of 2400 or higher", 90 minutes "Where at least one of the players in the game has a rating 1800 or higher", 60 minutes "Where both of the players in the game are rated below 1800"; "Where a certain number of moves is specified in the first time control, it shall be at least 30 moves." READ, NOT VERIFIED: the time for 60 moves is the base time plus 60 times the increment, the formula of the rapid and blitz chapter (R-02); the ratings are those of R-11a, and an unrated player counts as below 1800.
- **R-02 Rapid.** CIT §1.1.1 [V 2]: "for a rapid game all the moves must be made in a fixed time of more than 10 minutes but less than 60 minutes for each player; or the time allotted + 60 times any increment must be more than 10 minutes but less than 60 minutes for each player".
- **R-03 Blitz.** CIT §1.1.2 [V 2]: "for a blitz game all the moves must be made in a fixed time of more than 3 minutes but not more than 10 minutes for each player; or the time allotted + 60 times any increment must be more than 3 minutes but not more than 10 minutes for each player."
- **R-04 Unequal times (rapid and blitz).** CIT §1.2 [V 2]: "Games where the players have different playing times are not rated."
- **R-05 Unplayed games.** CIT §5.1 [V 1] (the same in [V 2]): "Whether these occur because of forfeiture or any other reason, they are not counted. Except in case of force majeure, any game where both players have made at least one move will be rated, unless the regulations relating to Fair Play require otherwise." Force majeure and Fair Play decisions arrive as the `excluded` flag (§2.1).
- **R-06 Matches.** CIT §6.1–6.2 [V 1]: "Matches in which one player is unrated shall not be rated." "Where a match is over a specific number of games, those played after one player has won shall not be rated. This requirement may be waived by prior request." A waiver arrives as an input. READ, NOT VERIFIED: a match is won once one player's score exceeds half the scheduled games.
- **R-07 Rapid and blitz, 600 points.** CIT §7.3.1 [V 2]: "Effective from 1 December 2024: Games played between players with a rating difference of 600 points or more shall not be rated if at least one of the players is rated above 2600 on the relevant list." READ, NOT VERIFIED: "the relevant list" is the list of R-11a. There is no such rule in standard.

### 3.2 Periods and the ratings used

- **R-08 One list a month.** CIT §7.1 [V 1]: "On the first day of each month, FIDE shall prepare a list which incorporates all rated play during the rating period into the previous list. This shall be done using the rating system formula."
- **R-09 Closing date.** CIT §7.1.3 [V 1]: "The closing date for tournaments for a list is 3 days before the date of the list; tournaments ending before or on that day may be rated on the list. Official FIDE events may be rated on the list even if they end on the last day before the list date." The engine takes `rating_period` from FIDE's records and rejects a record whose period is earlier than this rule allows.
- **R-10 Late reports.** CIT §9.1 [V 1]: "If the tournament report is not submitted in time to be included in the third rating list after it ends, the tournament will not be rated." A record whose `rating_period` is later than the third list after `end_date` is rejected. READ, NOT VERIFIED: the third list after the end is the third list dated after `end_date`.
- **R-11 The period's change.** CIT §8.3.2 c–d [V 1]: "Sigma Delta R = the sum of Delta Rs for a tournament or Rating Period." "Sigma Delta R x K = the Rating Change for a tournament or Rating Period." The new rating is the rating on the previous list plus the period's change, rounded (R-25).
- **R-11a Ratings used for a tournament.** Each tournament uses, for the player and for every opponent, the ratings of the list in force on its start date (the list dated the first day of that month), also when it is rated on a later list. CIT §7.1.1 [V 1]: "The rating period (for new players, see 7.1.4) is the period where a certain rating list is valid."; the Title Regulations state the rule for norms, §1.4.6 a) [VT 1]: "The Rating List in effect at the start of the tournament shall be used". FIX F-P02, F-P03: an event from 31 October to 2 November 2025, rated on the December 2025 list, used the October list. READ, NOT VERIFIED: a tournament longer than 30 days uses, for each game, the list in force when it was played, by analogy with §1.1.4 [VT 1].
- **R-11b Base corrections.** FIX F-P04: FIDE's starting rating can differ from the previously published list (Ro 2053 against 2052 on the November 2025 list; the December rating, 2053, follows from 2053). Without a correction (§2.4) the engine starts from the published list; the frequency and cause of corrections are open (§8 Q-2).
- **R-12 A newcomer rated before an earlier event.** CIT §8.2.4 [V 1]: "If an unrated player receives a published rating before a particular tournament in which they have played is rated, then they are rated as a rated player with their current rating, but in the rating of their opponents they are counted as an unrated player." READ: "their current rating" is the rating on the previous list, used when the player is unrated on the list of R-11a.

### 3.3 Expected score

- **R-13 Difference.** CIT §8.3.1 [V 1]: "For each game played against a rated player, determine the difference in rating between the player and their opponent, D."
- **R-14 The 400-point rule, standard.** CIT §8.3.1 [V 1]: "Effective from 1 October 2025: A difference in rating of more than 400 points shall be counted for rating purposes as though it were a difference of 400 points for players rated below 2650. For players rated 2650 and above, the difference between ratings shall be used in all cases". Settled: "players rated" refers to the player whose change is computed, on the list of R-11a. FIX F-P01 and F-P02, two sides of one game: the player rated 2813 uses D = 413 (PD .93); the opponent rated 2400 sees "2800 *", the capped value. Every game with a gap over 400 is capped for a player below 2650, several in one event (F-P02: three); the archived text allowed "only one upgrade" per tournament [VT 2], the current text does not.
- **R-14a Before 1 October 2025.** CIT §8.3.1 [V 1]: "Effective from 1 October 2025:"; the research report dates the exemption to that day, the cap having applied to every player since 1 March 2024 [R §2]. READ, NOT VERIFIED: tournaments starting before 1 October 2025 use the cap for every player, as R-15; the boundary (start date, game date or rating period) was not probed (§8 Q-7).
- **R-15 The 400-point rule, rapid and blitz.** CIT §7.3.1 [V 2]: "A difference in rating of more than 400 points shall be counted for rating purposes as though it were a difference of 400 points." No 2650 exemption.
- **R-16 PD.** CIT §8.3.2 a) [V 1]: "Use table 8.1.2 to determine the player's score probability PD for each game." For D ≥ 0 the H column, for D < 0 the L column, of the row containing |D|; above 735, 1.0 and .00 (§9). FIX F-C01 to F-C13 (row edges on both sides of D) and every game of F-P01 to F-P05 (79 games, each reproduced, `analysis/OUTPUT_L0_fixtures.md` §4).
- **R-17 Per game.** CIT §8.3.2 b) [V 1]: "Delta R = score - PD. For each game, the score is 1, 0.5 or 0."

### 3.4 K

- **R-18 to R-21.** CIT §8.3.3 [V 1], identical in [V 2]: "K = 40 for a player new to the rating list until they have completed events with at least 30 games." "K = 20 as long as a player's rating remains under 2400." "K = 10 once a player's published rating has reached 2400 and remains at that level subsequently, even if the rating drops below 2400." "K = 40 for all players until the end of the year of their 18th birthday, as long as their rating remains under 2300."
- **R-22 Precedence.** CIT §8.3.3 [V 1], the four lines quoted under R-18 to R-21, which state no order; the K = 10 line holds "even if the rating drops below 2400" and the junior line "as long as their rating remains under 2300". Settled on FIDE's published K (DATA): (1) a published rating of 2400 or more at any time → 10; (2) a junior (list year minus year of birth at most 18) never rated 2300 or more → 40; (3) fewer than 30 games counted → 40; (4) otherwise 20. Against the K published for 19,631,361 player-months (players first listed from February 2016, lists from January 2017) this order agrees in 99.21 %; the order junior below 2300, then fewer than 30 games, then 2400, agrees in 99.17 % (`analysis/OUTPUT_L0_k_rules.md` §1). Each step shows in the cells (§4 there): juniors below 2300 with 30 games or more, never rated 2300, K 40 in 2,689,889 player-months and K 20 in 30; juniors below 2300 once rated 2300, K 20 in 6,166 and K 40 in 17; players rated 2400 or more with fewer than 30 games, K 10 in all 1,117. At the turn of the year, juniors in the year after their 18th birthday drop from 40 to 20 on the January list (5,848 against 131 staying at 40 in January 2026, §3 there). READ, NOT VERIFIED: the 30 games include games played before the first published rating. Most disagreements are players published with K 20 while the lists show at most 4 games since their first listing (116,020 of 154,963 player-months); with fewer than 25 games the group (125,080) grows from 250–854 player-months a year in 2017–2023 to 34,365–48,856 a year in 2024–2026 (§2 there), after the floor rose from 1000 to 1400 in March 2024 [R §2]; the lists cannot show games played before a first rating (§8 Q-8).
- **R-22b Which K applies.** The K for the games rated on list t is the K published on list t − 1, "the current value of K for the player" (§7.1.2 [V 1]), reduced under R-23. FIX F-P01 to F-P05 (`analysis/OUTPUT_L0_fixtures.md` §4). READ, NOT VERIFIED where the K changes inside a period (30 games reached, 2400 reached).
- **R-23 Cap.** CIT §8.3.3 [V 1]: "If the number of games (n) for a player on any list for a rating period multiplied by K (as defined above) exceeds 700, then K shall be the largest whole number such that K x n does not exceed 700." FIX F-P05: n = 39, K 20 → 17.
- **R-24 Change.** CIT §8.3.2 d) [V 1]: "Sigma Delta R x K = the Rating Change for a tournament or Rating Period.", with the K of R-22b and R-23. FIX F-P01 to F-P05: K × sum reproduced in all 13 tournaments (`analysis/OUTPUT_L0_fixtures.md` §4).

### 3.5 Rounding

- **R-25 The period's change.** CIT §8.3.4 [V 1], identical in [V 2]: "The Rating Change for a Rating Period is rounded to the nearest whole number. 0.5 is rounded away from zero." FIX F-P01: −2.50 is published as −3. Granularity NOT VERIFIED: F-P05 is reproduced only by rounding the period's change once, as written; F-P02 only by rounding each tournament's change (`analysis/OUTPUT_L0_fixtures.md` §4). The engine rounds per period and also reports the per-tournament result (§4), so that every validation shows which one FIDE's list follows (§8 Q-1).
- **R-26 The initial rating.** CIT §8.2.3 [V 1]: "Ru is rounded to the nearest whole number." READ, NOT VERIFIED: 0.5 is rounded up, as the Title Regulations round the opponents' average (§1.4.7 b) [VT 1]: "The fraction 0.5 is rounded upward."). No fixture falls on a half (F-N01: 1922.43).

### 3.6 Newcomers

- **R-27 Publication.** CIT §7.1.4 [V 1]: "A rating for a player new to the list shall be published when it is based on at least 5 games against rated opponents. This need not be met in one tournament. Results from other tournaments played within consecutive rating periods of not more than 26 months are pooled to obtain the initial rating. The rating must be at least 1400." READ, NOT VERIFIED: the pool keeps the results of the 26 rating periods ending with the one being rated; older results drop out.
- **R-28 A zero start.** CIT §8.2.1 [V 1]: "If an unrated player scores zero in their first event this score is disregarded. Otherwise, their rating is calculated using all their results as in 7.1.4." The first event is the first event of the player that the engine's state records (§2.3).
- **R-29 Ra.** CIT §8.2.2 [V 1]: "Ra is the average rating of the player's rated opponents plus two hypothetical opponents rated 1800. The result against these two hypothetical opponents is considered as a draw." So Ra = (sum of the opponents' ratings + 3600) / (n + 2), and the score is W + 1 out of n + 2. FIX F-N01: 5 games, 3 points, opponents summing to 9507: Ra = 13107 / 7 = 1872.43.
- **R-30 Ru.** CIT §8.2.3 [V 1]: "Ru = Ra + dp" … "The maximum initial rating is 2200." with dp from table 8.1.1 at p = (W + 1) / (n + 2). FIX F-N01: p = 4/7 → .57, dp = 50, Ru = 1922.43 → 1922, the published first rating. READ, NOT VERIFIED: p is rounded to the nearest hundredth with .005 rounded up, as the Title Regulations round percentages before the same table ("All percentages are rounded to the nearest whole number. 0.5% is rounded up." [VT 1]); Ru is rounded (R-26), then limited to 2200, then published only if at least 1400 (R-27). Not references for this rule: FIDE's online calculator, which applies the archived rule [VT 2] (F-I01 to F-I08), and the "Rp" FIDE prints beside a newcomer's result, which does the same (F-N01: 1921).
- **R-31 Rapid and blitz seed.** CIT §7.2.1 [V 2]: "If an unrated player has a standard rating at the beginning of a rapid or blitz tournament, their standard rating is used for rating calculation. Such a player is considered to be rated, and 7.2.2 to 7.2.5 below do not apply." READ, NOT VERIFIED: the player's new rapid or blitz rating is that standard rating plus the period's change, with K as for a player new to that list (R-18).

### 3.7 Floor, inactivity and the published fields

- **R-32 Floor.** CIT §7.2.1 [V 1]: "Players whose ratings drop below 1400 are shown as unrated on the next list. Thereafter they are treated in the same manner as any other unrated player." READ, NOT VERIFIED: the sub-1400 value is not used again and only results obtained while unrated enter the new pool; the games counter of R-18 is kept (§8 Q-9).
- **R-33 Inactivity.** CIT §7.2.2 [V 1]: "A player is considered to commence inactivity if they play no rated games in a one-year period." "A player regains their activity if they play at least one rated game in a period. They are then listed as active on the next list." Ratings do not change with inactivity. READ, NOT VERIFIED: a player is listed as inactive on list t after no rated game in the 12 periods ending with t; without a recorded history the previous list's flag is kept.
- **R-34 Published fields.** CIT §7.1.2 [V 1]: "The following data will be published concerning each player whose rating is at least 1400 as of the current list: FIDE title, Federation, Current Rating, ID Number, Number of games rated in the rating period, Year of Birth, Gender and the current value of K for the player." The engine computes rating, games, K and the inactive flag; title, federation and gender are carried by the caller.

### 3.8 Rapid and blitz

The same tables (verified identical [V 2]), K rules, rounding and newcomer arithmetic as standard; the differences are R-02 to R-04, R-07, R-15 and R-31.

## 4 Interfaces

All functions are pure: no I/O, no global state, no randomness, no clock. Every rounded quantity is a `decimal.Decimal`; PD, dp and K are exact table or integer values, so only R-25, R-26 and R-30 round. Each function names the rules it implements.

```
classify(white_tc, black_tc, rating_white, rating_black)                   -> "standard" | "rapid" | "blitz" | None   # R-01..R-04
rateable(game, tournament, rating_white, rating_black, white_tc, black_tc) -> bool                                    # R-05, R-07
rated_match_games(scores, scheduled, both_rated, waived)                   -> tuple[bool, ...]                        # R-06
list_in_force(start_date)                                                  -> "YYYY-MM"                               # R-11a
earliest_rating_period(end_date, official_fide_event)                      -> "YYYY-MM"                               # R-09
latest_rating_period(end_date)                                             -> "YYYY-MM"                               # R-10
effective_difference(own, opponent, chapter, start_date)                   -> int                                     # R-13..R-15, R-14a
expected_score(d)                                                          -> Decimal                                 # R-16
game_delta(own, opponent, score, chapter, start_date)                      -> Decimal                                 # R-17
published_k(rating, games_count, ever_2400, ever_2300, list_month, birth_year) -> int                                 # R-18..R-22
k_for_period(previous_list_k, n)                                           -> int                                     # R-22b, R-23
period_change(tournament_deltas, k)                                        -> PeriodChange                            # R-11, R-24, R-25
round_change(x), round_initial(x)                                          -> int                                     # R-25, R-26
dp_from_p(p)                                                               -> int                                     # R-30 (table 8.1.1)
initial_rating(pool)                                                       -> int | None                              # R-26..R-30
next_list(period, lists, tournaments, games, state, corrections, birth_years, standard_lists) -> NextList             # R-08..R-12, R-27..R-34
```

`PeriodChange` carries the unrounded change of each tournament and of the period, the rounded period change (R-25) and the per-tournament alternative. `NextList` carries the new list, the new state and, for every player who played, a breakdown: the list used, D, the capped D, PD, Delta R, K, the sums and the rounding, so that every number can be checked by hand against the regulations. Records are frozen dataclasses: `TimeControl`, `Tournament`, `Game`, `ListEntry`, `PlayerState`, `PoolEvent`; `lists` maps a month to a list, and `corrections` maps (month, player) to a corrected rating (R-11b, §2.4).

### 4.3 State and bootstrapping

The state of §2.3 is carried from list to list. To start from history, the engine derives it from the published lists alone: `games_count` is the sum of the games column since the player's first listing, `ever_2400` and `ever_2300` from the published ratings. This reproduces the published K in 99.21 % of player-months (R-22); the residual, games played before a first rating, cannot be recovered from the lists.

## 5 Determinism and precision

- Identical inputs give identical outputs, byte for byte, on any platform: no dependence on dictionary or set order, locale, time zone or hardware floating point; outputs are sorted by FIDE ID, then by tournament start date and ID, then by round.
- Rating arithmetic in `Decimal` with the default context (28 significant digits); binary floating point is never used.
- Every output row carries its per-game breakdown (§4).

## 6 Evidence

### 6.1 FIDE's online calculator: out of date

Fixtures F-C01 to F-C24 and F-I01 to F-I08 (`https://ratings.fide.com/calc.phtml`, 2026-10-09). The rating-change calculator reproduces table 8.1.2 at every row edge probed and the multiplication by K, but applies the 400-point cap to everyone: it agrees with §8.3.1 as written from 1 October 2025 in 20 of 24 cases and with a plain cap in 24 of 24; the four differences are players rated 2650 or above with a gap over 400. The initial-rating calculator follows the archived rule of 2022–24 [VT 2] in 8 of 8 cases and the current rule in 1 of 8, by coincidence (`analysis/OUTPUT_L0_fixtures.md` §2–3). The calculator is therefore a reference for R-16 and R-17 only.

### 6.2 FIDE's published calculations

Fixtures F-P01 to F-P05 (five adults, 13 tournament calculations, 79 games, December 2025 and October 2026 lists) and F-N01 (a first rating). Every game, tournament sum and K × sum is reproduced from table 8.1.2 (`analysis/OUTPUT_L0_fixtures.md` §4). They settle R-11a, R-14, R-22b, R-23, R-25 (the half), R-29 and R-30, and leave open the granularity of R-25 and the base corrections of R-11b.

### 6.3 The published lists

The K rules against 141 standard lists, February 2015 to October 2026 (`analysis/OUTPUT_L0_k_rules.md`, from `analysis/l0_k_rules_extract.py`; the lists are never committed).

### 6.4 Validation events

A complete event, rated on one list, compared player by player with FIDE's per-tournament calculation and with the next list: the 2025 U.S. Championship first (session ELO-3, Phase 3, reported under docs/evidence). Each validation reports the rounding (R-25) and base (R-11b) questions separately from the rule checks.

## 7 Acceptance criteria

Each criterion is one executable test module under `tests/`, written before the engine; the specification is ratified when all of them exist (status line). Raw data are never needed: every test reads committed fixtures or constructs its inputs.

| # | Criterion | Test module |
|---|---|---|
| A-1 | Tables 8.1.1 and 8.1.2 in the engine equal the transcription [V 1] entry by entry (101 and 51 entries, read from the transcription file at test time), with the mirror properties; table 1.4.9 equals 8.1.1 | tests/test_l0_tables.py |
| A-2 | Every rating-change calculator fixture: the engine's single-game change equals the calculator's under the plain cap (R-15), and under R-14 equals the calculator's except exactly F-C16, F-C17, F-C20 and F-C21 | tests/test_l0_calculator.py |
| A-3 | Every published calculation: each game's Delta R, each tournament's sum, K and K × sum equal FIDE's; R-14 on both sides of F-P01/F-P02; K from R-22b and R-23; the new rating equals the published list under R-25 per period for F-P01, F-P03, F-P04 (with its base correction) and F-P05, and under the per-tournament alternative for F-P02 | tests/test_l0_published.py |
| A-4 | Initial rating: F-N01 gives 1922; fewer than 5 games, a result below 1400, a result above 2200 and a zero first event behave as R-27 to R-30; the archived-rule fixtures F-I01 to F-I08 are not reproduced except F-I04 | tests/test_l0_initial.py |
| A-5 | K: each line of R-18 to R-21, the precedence of R-22 on every combination of its four conditions, the turn of the year, R-22b and R-23 at n = 35, 36 and 39 | tests/test_l0_k.py |
| A-6 | Rounding: R-25 at ±0.5, ±1.5, ±2.5 and ±2.49; R-26 at x.5 | tests/test_l0_rounding.py |
| A-7 | Eligibility and chapters: R-01 to R-07 at each boundary (60/90/120 minutes, 30 moves, 10/60 and 3/10 minutes with increments, 600 points with a player above 2600, before and after 1 December 2024) | tests/test_l0_eligibility.py |
| A-8 | Periods and lists: R-08 (every listed player carried over), R-09 and R-10 limits, R-11a (31 October → October list), R-11b corrections, R-12 one-sided rating, R-13 and the R-14a boundary, R-22b, R-27 to R-30 through the list (a newcomer published with K 40; four games kept in the pool), R-31 (the rapid seed), R-32 and R-33 list status, R-34 fields | tests/test_l0_periods.py |
| A-9 | Determinism and purity: runs with different hash seeds give byte-identical output; the order of the input records does not change the result; the engine package performs no I/O | tests/test_l0_determinism.py |
| A-10 | Validation event: the 2025 U.S. Championship reproduced game by game and player by player from a committed fixture of FIDE's per-tournament calculation, and the November 2025 list reproduced allowing for the players' other events in the period | tests/test_l0_validation.py |

## 8 Open questions

Resolved since v0.1: R-14 (own rating, F-P01/F-P02); R-22 (precedence, DATA); R-23 and the half of R-25 (fixtures).

| # | Question | Rules | Default in v1.0 | Owner |
|---|---|---|---|---|
| Q-1 | Is the change rounded once per period, as written, or per tournament? Fixtures disagree (F-P02, F-P05) | R-25 | per period, with the alternative reported | architect; more published calculations or FIDE's answer |
| Q-2 | How often, and why, does FIDE's starting rating differ from the previous list? | R-11b | the published list; corrections as input | executor, next validation |
| Q-3 | Ties in Ru and in p (no fixture falls on a half) | R-26, R-30 | half up | open; a newcomer fixture at a tie |
| Q-4 | Increments in the standard chapter | R-01 | base + 60 × increment | open |
| Q-5 | Tournaments longer than 30 days | R-11a | list in force at each game | open |
| Q-6 | TRF field mapping (the TRF layout is not transcribed) | §2.1 | own record format; adapter separate | executor, when a TRF source exists |
| Q-7 | The boundary of the 1 October 2025 amendment | R-14a | tournament start date | open |
| Q-8 | Do the 30 games of R-18 include games played before the first rating? | R-18, R-22 | as published (lists cannot show them) | open |
| Q-9 | After a drop below 1400, is anything of the old rating or results kept? | R-32 | neither; the games counter is kept | open |
| Q-10 | Rule sets for the archived regulations (2022–24, 2017–21) for backtests | §1 | not implemented | architect |
| Q-11 | FIDE's online calculator is out of date (§6.1); whether to tell FIDE | §6.1 | recorded only; no contact | operator |

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
## 10 Tooling

Python 3.12, standard library only at run time (`decimal`, `dataclasses`, `datetime`); package layer0 under src, Apache-2.0; tests with pytest under `tests/`, configured in pyproject.toml; the automated check (`.github/workflows/check.yml`) runs them on every pull request (D-0004). Fixtures are JSON under `tests/fixtures/`. Nothing in this section authorises engine code before ratification.
